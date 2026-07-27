// State + actions behind the experiment-results page (sub-step 5.2).
// All computation lives in experimentResultsTransforms.js (pure,
// unit-testable); this composable owns the refs and the interactions the
// children emit back to.
import { ref, computed } from 'vue';
import { marked } from 'marked';
import { experimentService } from '@/services/generatorService';
import {
  buildDetailedGroups,
  computeChunksSummary,
  splitSummaryResults,
} from '@/composables/experimentResultsTransforms';

// marked-based formatters, shared with the presentational children.
export const markdownToHtml = (text) => {
  return marked(text);
};

export const formatAnswer = (text) => {
  const formattedText = text.replace(/([:.)\]])(nn?)/g, (match, p1, p2) => {
    return p1 + (p2 === 'nn' ? '<br><br>' : '<br>');
  });
  return marked(formattedText);
};

export function useExperimentResults() {
  const mainResults = ref([]);
  const chunkResults = ref([]);
  const fullEvaluation = ref([]);
  const loading = ref(true);
  const error = ref(null);
  const experimentName = ref('');
  const showChunksSummary = ref(false);
  const selectedModel = ref('');
  const chunksSummary = ref({
    llm: { hallucinations: 0, missings: 0, combined: 0, wholeTest: 0 },
    chunks: { hallucinations: 0, missings: 0, combined: 0, wholeTest: 0 }
  });

  const filters = ref({
    ok: true,
    hallu: true,
    missing: true,
    extra: true
  });

  const hasChunkEvaluations = computed(() => chunkResults.value.length > 0);
  const groupedDetailedResults = ref([]);

  const filteredDetailedResults = computed(() => {
    return groupedDetailedResults.value
      .map((group, idx) => ({
        ...group,
        originalIndex: idx + 1,
        show: (filters.value.ok && group.mainResult.ok > 0) ||
              (filters.value.hallu && group.mainResult.hallu > 0) ||
              (filters.value.missing && group.mainResult.missing > 0) ||
              (filters.value.extra && group.mainResult.extra > 0)
      }))
      .filter(group => group.show);
  });

  // `resultsSource` is the results name (post-experiment redirect) or a
  // legacy full path (old bookmarks); the backend accepts both.
  const fetchResults = async (resultsSource) => {
    if (resultsSource) {
      try {
        loading.value = true;
        error.value = null;
        const data = await experimentService.getExperimentResults(resultsSource);
        const summary = splitSummaryResults(data.summary);
        mainResults.value = summary.main;
        chunkResults.value = summary.chunks;
        groupedDetailedResults.value = buildDetailedGroups(data.detailed, data.full);
        fullEvaluation.value = data.full;
        experimentName.value = resultsSource.split('/').pop().replace('.json', '');
      } catch (err) {
        console.error('Error fetching experiment results:', err);
        error.value = 'Error fetching experiment results: ' + err.message;
      } finally {
        loading.value = false;
      }
    } else {
      error.value = 'No results name provided';
      loading.value = false;
    }
  };

  const toggleExpandedDetails = (group) => {
    const originalGroup = groupedDetailedResults.value.find(g => g.question === group.question);
    if (originalGroup) {
      originalGroup.showExpanded = !originalGroup.showExpanded;
    }
  };

  const showChunkContent = (group, chunkIndex) => {
    group.chunks[chunkIndex].isVisible = !group.chunks[chunkIndex].isVisible;
  };

  const showChunk = (group, factIndex, chunkNumber) => {
    const fact = group.facts[factIndex];
    if (fact) {
      const button = fact.chunkButtons.find(b => b.number === chunkNumber);
      if (button) {
        button.isVisible = !button.isVisible;
      }
    }
  };

  const toggleChunksSummary = (modelName) => {
    if (selectedModel.value === modelName && showChunksSummary.value) {
      showChunksSummary.value = false;
    } else {
      selectedModel.value = modelName;
      chunksSummary.value = computeChunksSummary(fullEvaluation.value, modelName);
      showChunksSummary.value = true;
    }
  };

  const closeChunksSummary = () => {
    showChunksSummary.value = false;
    setTimeout(() => {
      selectedModel.value = '';
    }, 150);
  };

  return {
    mainResults,
    chunkResults,
    fullEvaluation,
    loading,
    error,
    experimentName,
    showChunksSummary,
    selectedModel,
    chunksSummary,
    hasChunkEvaluations,
    groupedDetailedResults,
    filteredDetailedResults,
    filters,
    fetchResults,
    toggleExpandedDetails,
    showChunk,
    showChunkContent,
    toggleChunksSummary,
    closeChunksSummary,
  };
}
