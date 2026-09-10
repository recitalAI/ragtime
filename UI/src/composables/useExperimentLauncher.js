// Job launch + polling + config assembly for the experiment page
// (sub-step 5.3). Moved verbatim from ExperimentSetup.vue; the experiment
// runs as a backend job (POST /api/jobs) and the job id is kept in
// sessionStorage so closing/reopening the tab re-attaches to the running
// experiment. Completion comes from the job status.
//
// `form` is the bag of refs/computeds owned by the view; `showMessage` is
// the view's snackbar helper. Log auto-scrolling lives in LiveLogPanel
// (it owns the DOM container); this composable only appends to `liveLogs`.
import { onUnmounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { experimentService } from '@/services/generatorService';
import { formatDateForBackend } from '@/utils/dateFormatter';
import { useConnectivityGuard } from '@/composables/useConnectivityGuard';

const JOB_STORAGE_KEY = 'ragtime_running_job_id';

export function useExperimentLauncher(form, showMessage) {
  const router = useRouter();
  const { showOfflineDialog, ensureOnline, handleOfflineError } = useConnectivityGuard();

  const isExperimentRunning = ref(false);
  const liveLogs = ref([]);
  const isShowingLogs = ref(false);
  const autoScroll = ref(true);
  const activeJobId = ref(null);
  // Search checkpoint: when phase 1 (retrieval) finishes, the job pauses at
  // `awaiting_review`; we fetch the retrieved answers+chunks and show them for
  // approval before any evaluation runs.
  const isAwaitingReview = ref(false);
  const reviewItems = ref([]);        // [{question, answer, chunks:[...]}]
  const reviewName = ref('');
  const isEvaluating = ref(false);    // phase-2 launch in flight
  // Once the user approves the checkpoint we must not fall back into the
  // awaiting_review branch while the worker is still flipping the status from
  // awaiting_review -> running (that would kill polling and reopen the review).
  let reviewApproved = false;
  let jobLogOffset = 0;
  let logPollingInterval = null;

  const finishJobPolling = () => {
    stopLogPolling();
    isExperimentRunning.value = false;
    sessionStorage.removeItem(JOB_STORAGE_KEY);
  };

  const pollJob = async () => {
    if (!activeJobId.value) return;
    try {
      const job = await experimentService.getExperimentJob(activeJobId.value, jobLogOffset);

      if (Array.isArray(job.logs) && job.logs.length > 0) {
        liveLogs.value = [...liveLogs.value, ...job.logs];
        jobLogOffset = job.next_offset;
      }

      if (job.status === 'done') {
        finishJobPolling();
        showMessage('Experiment completed successfully.', 'success');
        router.push({ name: 'ExperimentResults', query: { name: job.results_name } });
      } else if (job.status === 'failed') {
        finishJobPolling();
        showMessage(`Experiment failed: ${job.error || 'Unknown error'}`, 'error');
      } else if (job.status === 'awaiting_review' && !reviewApproved) {
        // Phase 1 done: stop polling and load the retrieved answers+chunks so
        // the user can review before evaluation. The job id stays in
        // sessionStorage so a tab reopen re-attaches to the checkpoint.
        // Skip this once the user has approved (reviewApproved) — otherwise a
        // stale awaiting_review read during the phase-2 startup would reopen
        // the checkpoint and stop the eval logs.
        stopLogPolling();
        isExperimentRunning.value = false;
        await loadReview();
      }
    } catch (error) {
      console.error('Failed to poll experiment job:', error);
      if (error.response?.status === 404) {
        // Job files were cleaned up server-side — stop polling.
        finishJobPolling();
      }
    }
  };

  const startLogPolling = () => {
    if (!logPollingInterval) {
      pollJob();
      logPollingInterval = setInterval(pollJob, 1000);
    }
  };

  const stopLogPolling = () => {
    if (logPollingInterval) {
      clearInterval(logPollingInterval);
      logPollingInterval = null;
    }
  };

  const attachToJob = (jobId) => {
    activeJobId.value = jobId;
    jobLogOffset = 0;
    liveLogs.value = [];
    reviewApproved = false;   // fresh job: checkpoint is live again
    isExperimentRunning.value = true;
    isShowingLogs.value = true;
    sessionStorage.setItem(JOB_STORAGE_KEY, jobId);
    stopLogPolling();
    startLogPolling();
  };

  const resumeRunningJob = async () => {
    const savedJobId = sessionStorage.getItem(JOB_STORAGE_KEY);
    if (!savedJobId) return;
    try {
      const job = await experimentService.getExperimentJob(savedJobId, 0);
      if (job.status === 'queued' || job.status === 'running') {
        attachToJob(savedJobId);
      } else {
        sessionStorage.removeItem(JOB_STORAGE_KEY);
      }
    } catch (error) {
      sessionStorage.removeItem(JOB_STORAGE_KEY);
    }
  };

  const startExperiment = async () => {
    // Re-entrancy guard: form submit, double clicks, or Enter presses must
    // never create a second job while one is being submitted or running.
    if (isExperimentRunning.value) return;
    // Offline guard: block the launch and show the popup when the browser
    // reports no connection (the experiment runs generation + evaluation,
    // which need the network).
    if (!ensureOnline()) return;
    if (!form.validationSetData.value) {
      showMessage('Validation set data is not loaded. Please select a validation set.', 'error');
      return;
    }
    isExperimentRunning.value = true;
    // Search retriever supplies both answers and chunks, so no answer model is
    // chosen; selectedModel stays undefined and answerGenerationModels is
    // ignored by the backend for this path.
    const isSearch = (form.selectedRetriever?.value || '').toLowerCase() === 'search'
      && (form.useRetriever?.value || false);
    const selectedModel = isSearch
      ? null
      : (form.fileName.value
        ? form.selectedModels.value[0]
        : [...form.selectedLLMs.value, ...form.selectedCustomLLMs.value][0]);

    if (form.matchedQuestions.value.length > 0) {
      form.validationSetData.value.items = form.matchedQuestions.value.map(item => ({
        question: { text: item.question },
        facts: {
          items: item.facts.map(fact => ({ text: fact }))
        },
        answers: {
          items: [
            {
              llm_answer: {
                meta: {},
                text: item.answer,
                prompt: {
                  meta: {},
                  user: item.question,
                  system: "",
                  prompter: "AnsPrompterBase"
                },
                name: selectedModel,
                full_name: selectedModel,
                timestamp: formatDateForBackend(new Date()),
                duration: 0,
                chunks: item.chunks
              },
              meta: {},
              text: item.answer
            }
          ]
        },
        chunks: {
          meta: {},
          items: item.chunks.map(chunk => ({ text: chunk }))
        },
        timestamp: formatDateForBackend(new Date())
      }));
    }
    const experimentConfig = {
      name: form.experimentName.value,
      test: form.fullValidationSetName.value,
      validationSet: form.fullValidationSetName.value || form.selectedValidationSet.value,
      evaluationModel: form.evaluationModel.value,
      answerGenerationModels: selectedModel ? [selectedModel] : [],
      evaluateAnswers: form.evaluateAnswers.value,
      evaluateChunks: form.evaluateChunks.value,
      useRetriever: form.useRetriever.value || form.isAlbertSelected.value,
      retrieverType: form.selectedRetriever.value,
      validationSetData: form.validationSetData.value,
      withCSV: form.withCSV.value,
      // Per-model reasoning choice (default off) for the selected model;
      // only meaningful for reasoning-capable models, ignored otherwise.
      reasoning: (form.reasoningChoices?.value || {})[selectedModel] ?? null,
      // Per-model reasoning effort ('low'|'medium'|'high'); only applied to
      // effort-capable reasoning models, ignored otherwise.
      reasoningEffort: (form.reasoningEffortChoices?.value || {})[selectedModel] ?? null,
    };

    try {
      const job = await experimentService.createExperimentJob(experimentConfig);
      attachToJob(job.job_id);
    } catch (error) {
      console.error('Error starting experiment:', error);
      isExperimentRunning.value = false;
      if (handleOfflineError(error)) return;
      let errorMessage = 'An unexpected error occurred.';
      if (error.response && error.response.data && error.response.data.error) {
        errorMessage = error.response.data.error;
      }
      showMessage(`Error starting experiment: ${errorMessage}`, 'error');
    }
  };

  // ── Search checkpoint actions ─────────────────────────────────────────
  const loadReview = async () => {
    if (!activeJobId.value) return;
    try {
      const data = await experimentService.getReviewedJob(activeJobId.value);
      reviewItems.value = Array.isArray(data.items) ? data.items : [];
      reviewName.value = data.name || '';
      isAwaitingReview.value = true;
    } catch (error) {
      console.error('Failed to load review data:', error);
      showMessage('Could not load the retrieved answers to review.', 'error');
    }
  };

  const launchEvaluation = async () => {
    if (!activeJobId.value || isEvaluating.value) return;
    if (!ensureOnline()) return;
    isEvaluating.value = true;
    try {
      await experimentService.evaluateReviewedJob(activeJobId.value);
      // Back to the running/logs view; polling resumes and will route to
      // results when phase 2 finishes. Mark approved so pollJob won't reopen
      // the checkpoint on a stale awaiting_review read during startup.
      reviewApproved = true;
      isAwaitingReview.value = false;
      reviewItems.value = [];
      isExperimentRunning.value = true;
      isShowingLogs.value = true;
      // Restart polling cleanly: stop any stale interval first, then start.
      // Keep jobLogOffset as-is — phase-2 logs are appended to the same job log,
      // so we continue reading from where phase 1 left off.
      stopLogPolling();
      startLogPolling();
    } catch (error) {
      console.error('Failed to launch evaluation:', error);
      isEvaluating.value = false;
      if (handleOfflineError(error)) return;
      const msg = error.response?.data?.error || 'An unexpected error occurred.';
      showMessage(`Could not start evaluation: ${msg}`, 'error');
    }
  };

  const stopExperiment = async () => {
    if (!activeJobId.value) return;
    try {
      // Downloads the debug .xlsx (question/answer/chunks) then clears the
      // pending data server-side.
      await experimentService.discardReviewedJob(
        activeJobId.value,
        `${reviewName.value || 'experiment'}_search_debug.xlsx`,
      );
      showMessage('Experiment stopped. A debug file with the answers and chunks was downloaded.', 'success');
    } catch (error) {
      console.error('Failed to discard experiment:', error);
      showMessage('Could not download the debug file.', 'error');
    } finally {
      // Clean the session either way.
      isAwaitingReview.value = false;
      reviewItems.value = [];
      reviewName.value = '';
      isEvaluating.value = false;
      reviewApproved = false;
      activeJobId.value = null;
      sessionStorage.removeItem(JOB_STORAGE_KEY);
    }
  };

  onUnmounted(() => {
    if (logPollingInterval) {
      clearInterval(logPollingInterval);
    }
  });

  return {
    isExperimentRunning,
    liveLogs,
    isShowingLogs,
    autoScroll,
    showOfflineDialog,
    startExperiment,
    resumeRunningJob,
    // Search checkpoint
    isAwaitingReview,
    reviewItems,
    reviewName,
    isEvaluating,
    launchEvaluation,
    stopExperiment,
  };
}
