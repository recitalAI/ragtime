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

const JOB_STORAGE_KEY = 'ragtime_running_job_id';

export function useExperimentLauncher(form, showMessage) {
  const router = useRouter();

  const isExperimentRunning = ref(false);
  const liveLogs = ref([]);
  const isShowingLogs = ref(false);
  const autoScroll = ref(true);
  const activeJobId = ref(null);
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
    if (!form.validationSetData.value) {
      showMessage('Validation set data is not loaded. Please select a validation set.', 'error');
      return;
    }
    isExperimentRunning.value = true;
    const selectedModel = form.fileName.value
      ? form.selectedModels.value[0]
      : [...form.selectedLLMs.value, ...form.selectedCustomLLMs.value][0];

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
      answerGenerationModels: [selectedModel],
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
      let errorMessage = 'An unexpected error occurred.';
      if (error.response && error.response.data && error.response.data.error) {
        errorMessage = error.response.data.error;
      }
      showMessage(`Error starting experiment: ${errorMessage}`, 'error');
      isExperimentRunning.value = false;
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
    startExperiment,
    resumeRunningJob,
  };
}
