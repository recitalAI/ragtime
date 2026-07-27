<template>
  <div class="experiment-results page-padding py-7">
    <div v-if="loading">Loading results...</div>
    <div v-else-if="error" class="error-message">{{ error }}</div>
    <h2
      v-else
      class="h2-text mb-7"
    >
      <span>{{ experimentName }}</span>
      <DownloadReport 
        v-if="hasChunkEvaluations && fullEvaluation && fullEvaluation.length > 0"
        :experiment-data="{ items: fullEvaluation }" 
      />
      <DownloadSimpleReport
        v-else-if="fullEvaluation && fullEvaluation.length > 0"
        :experiment-data="{ items: fullEvaluation }" 
      />
    </h2>
    <!-- Main Summary table -->
    <h3 class="h3-text black--text mb-4">
      Summary
    </h3>
    <ResultsSummaryTable
      :items="mainResults"
      :loading="loading"
      :has-chunk-evaluations="hasChunkEvaluations"
      @model-click="toggleChunksSummary"
    />
    <ChunksPanel
      v-model="showChunksSummary"
      :model="selectedModel"
      :summary="chunksSummary"
      @close="closeChunksSummary"
    />

    <!-- Detailed question-by-question results -->
    <div class="detailed-results">
      <div class="results-header">
        <h3 class="h3-text black--text">
          Question results
        </h3>
        <ResultFilters v-model:filters="filters" />
      </div>
      <DetailedResultsTable
        :items="filteredDetailedResults"
        @toggle-expand="toggleExpandedDetails"
        @toggle-fact-chunk="showChunk"
        @toggle-chunk="showChunkContent"
      />
    </div>
  </div>
</template>

<script>
import { onMounted } from 'vue';
import DownloadReport from '@/components/DownloadReport.vue';
import DownloadSimpleReport from '@/components/DownloadSimpleReport.vue';
import ResultsSummaryTable from '@/components/results/ResultsSummaryTable.vue';
import DetailedResultsTable from '@/components/results/DetailedResultsTable.vue';
import ChunksPanel from '@/components/results/ChunksPanel.vue';
import ResultFilters from '@/components/results/ResultFilters.vue';
import { useExperimentResults } from '@/composables/useExperimentResults';

export default {
  name: 'ExperimentResultsView',
  props: {
    // Results name (post-experiment redirect and the Home table). `path` is
    // kept for old bookmarks; the backend reduces it to its basename.
    name: String,
    path: String,
  },

  components: {
    DownloadReport,
    DownloadSimpleReport,
    ResultsSummaryTable,
    DetailedResultsTable,
    ChunksPanel,
    ResultFilters,
  },

  setup(props) {
    const {
      mainResults,
      fullEvaluation,
      loading,
      error,
      experimentName,
      showChunksSummary,
      selectedModel,
      chunksSummary,
      hasChunkEvaluations,
      filteredDetailedResults,
      filters,
      fetchResults,
      toggleExpandedDetails,
      showChunk,
      showChunkContent,
      toggleChunksSummary,
      closeChunksSummary,
    } = useExperimentResults();

    onMounted(() => fetchResults(props.name || props.path));

    return {
      mainResults,
      fullEvaluation,
      loading,
      error,
      experimentName,
      showChunksSummary,
      selectedModel,
      chunksSummary,
      hasChunkEvaluations,
      filteredDetailedResults,
      filters,
      toggleExpandedDetails,
      showChunk,
      showChunkContent,
      toggleChunksSummary,
      closeChunksSummary,
    };
  }
};
</script>

<style scoped>
.experiment-results {
  max-width: 2000px;
}

.error-message {
  color: #721c24;
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
  padding: 10px;
  margin-top: 20px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
</style>
