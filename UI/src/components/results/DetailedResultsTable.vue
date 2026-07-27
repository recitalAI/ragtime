<template>
  <TableWithFooter
    :items="paginatedItems"
    :paginated-items-length="paginatedItems.length"
    :loading="false"
    :current-page="currentPage"
    :items-per-page="itemsPerPage"
    :total="items.length"
    :show-footer="items.length > itemsPerPage"
    :include-footer-in-table-card="true"
    @change-page="onPageChange"
    @change-items-per-page="onItemsPerPageChange"
  >
    <template #header>
      <v-col
        class="justify-center"
        cols="1"
      >
        #
      </v-col>
      <v-col>
        Question
      </v-col>
      <v-col class="justify-center">
        Model
      </v-col>
      <v-col class="justify-center" cols="1">
        Facts
      </v-col>
      <v-col class="justify-center" cols="1">
        Ok
        <CustomTooltip text="Number of facts that exist in the answer." />
      </v-col>
      <v-col class="justify-center" cols="1">
        Hallu
        <CustomTooltip text="Number of facts for which the answer presented contradictory or misaligned information." />
      </v-col>
      <v-col class="justify-center" cols="1">
        Missing
        <CustomTooltip text="Number of facts that do not exist in the answer." />
      </v-col>
      <v-col class="justify-center" cols="1">
        Extra
        <CustomTooltip text="Additional information in the answer." />

      </v-col>
    </template>
    <template #body>
      <v-row
        v-for="group in paginatedItems"
        :key="`main-${group.originalIndex}`"
        class="table-row py-1"
        style="min-height: 55px;"
      >
        <v-col
          class="primary--text justify-center align-center clickable"
          cols="1"
          @click="$emit('toggle-expand', group)"
        >
          {{ group.originalIndex }}
        </v-col>
        <v-col
          class="primary--text align-center justify-start clickable"
          @click="$emit('toggle-expand', group)"
        >
          {{ group.question }}
        </v-col>
        <v-col class="align-center justify-center">
          {{ group.mainModel }}
        </v-col>
        <v-col
          class="align-center justify-center"
          cols="1"
        >
          {{ group.mainResult.factsCount }}
        </v-col>
        <v-col
          class="align-center justify-center"
          cols="1"
        >
          <FactStatusChips
            status-class="status-ok"
            :value="group.mainResult.ok"
            :total="group.mainResult.factsCount"
          />
        </v-col>
        <v-col
          class="align-center justify-center"
          cols="1"
        >
          <FactStatusChips
            status-class="status-error"
            :value="group.mainResult.hallu"
            :total="group.mainResult.factsCount"
          />
        </v-col>
        <v-col
          class="align-center justify-center"
          cols="1"
        >
          <FactStatusChips
            status-class="status-warning"
            :value="group.mainResult.missing"
            :total="group.mainResult.factsCount"
          />
        </v-col>
        <v-col
          class="align-center justify-center"
          cols="1"
        >
          <FactStatusChips
            status-class="status-extra"
            :value="group.mainResult.extra"
          />
        </v-col>
        <v-col
          v-if="group.showExpanded"
          class="d-block bg-grey-lighten1 black--text fade-in"
          cols="12"
        >
          <div class="answer-section">
            <h3 class="h3-text">
              Answer
            </h3>
            <div class="details-table">
              <div class="details-row">
                <span class="details-label">Date:</span>
                <span class="details-value">{{ formatDate(group.answerDate) }}</span>
              </div>
              <div class="details-row">
                <span class="details-label">Duration:</span>
                <span class="details-value">{{ group.answerDuration.toFixed(2) }}s</span>
              </div>
              <div class="details-row">
                <span class="details-label">Cost:</span>
                <span class="details-value">{{ formatCost(group.answerCost) }}</span>
              </div>
              <div class="details-row">
                <span class="details-label">Model:</span>
                <span class="details-value">{{ group.answerModel }}</span>
              </div>
            </div>
            <div class="answer-text" v-html="formatAnswer(group.answer)"></div>
          </div>
          <div class="evaluation-section">
            <h3 class="h3-text">
              Evaluation
            </h3>
            <div class="details-table">
              <div class="details-row">
                <span class="details-label">Date:</span>
                <span class="details-value">{{ formatDate(group.evalDate) }}</span>
              </div>
              <div class="details-row">
                <span class="details-label">Duration:</span>
                <span class="details-value">{{ group.evalDuration.toFixed(2) }}s</span>
              </div>
              <div class="details-row">
                <span class="details-label">Cost:</span>
                <span class="details-value">{{ formatCost(group.evalCost) }}</span>
              </div>
              <div class="details-row">
                <span class="details-label">Model:</span>
                <span class="details-value">{{ group.evalModel }}</span>
              </div>
            </div>
            <table class="evaluation-summary">
              <tr>
                <th>Score</th>
                <th>OK</th>
                <th>Hallu</th>
                <th>Missing</th>
                <th>Extra</th>
              </tr>
              <tr>
                <td>{{ group.mainResult.score.toFixed(2) }}</td>
                <td>{{ group.mainResult.ok }}</td>
                <td>{{ group.mainResult.hallu }}</td>
                <td>{{ group.mainResult.missing }}</td>
                <td>{{ group.mainResult.extra }}</td>
              </tr>
            </table>
          </div>
          <div class="facts-section">
            <h3 class="h3-text">
              Facts
            </h3>
            <ul class="fact-list">
              <li
                v-for="(fact, factIndex) in group.facts"
                :key="factIndex"
                class="fact-item"
              >
                <div class="fact-header">
                  <span :class="['fact-status', getFactStatusClass(fact.status)]"></span>
                  <span class="fact-text">{{ fact.text }}</span>
                </div>
                <div class="fact-evaluations">
                  <div
                    v-if="fact.evaluation"
                    class="fact-eval"
                    v-html="markdownToHtml(fact.evaluation)"
                  >
                  </div>
                  <div
                    v-if="fact.chunkEval"
                    class="chunk-eval"
                  >
                    <div v-if="fact.problemType" class="problem-analysis">
                      <p><strong>{{ fact.problemType }}</strong></p>
                      <p>{{ fact.problemExplanation }}</p>
                    </div>
                    <div v-html="fact.chunkEval"></div>
                    <div>
                      <button 
                        v-for="button in fact.chunkButtons" 
                        :key="button.number"
                        @click="$emit('toggle-fact-chunk', group, factIndex, button.number)"
                        class="chunk-button"
                      >
                        Chunk {{ button.number }}
                      </button>
                    </div>
                    <div 
                      v-for="button in fact.chunkButtons" 
                      :key="`text-${button.number}`" 
                      v-show="button.isVisible" 
                      class="chunk-text"
                    >
                      <p><strong>Chunk {{ button.number }}:</strong> {{ button.text }}</p>
                    </div>
                  </div>
                </div>
              </li>
            </ul>
          </div>
          <!-- New Chunks Section -->
          <div class="facts-section" v-if="group.chunks && group.chunks.length">
            <h3 class="h3-text">Chunks</h3>
            <div class="chunk-buttons-container">
              <button v-for="(chunk, chunkIndex) in group.chunks" 
                      :key="chunkIndex" 
                      class="chunk-button"
                      @click="$emit('toggle-chunk', group, chunkIndex)">
                      Chunk {{ chunkIndex + 1 }}
              </button>
            </div>
            <transition-group name="chunk-fade" tag="div" class="chunk-content-container">
              <div v-for="(chunk, chunkIndex) in group.chunks" 
                  :key="chunkIndex"
                  v-show="chunk.isVisible" 
                  class="fact-eval chunk-content">
                <strong>Chunk {{ chunkIndex + 1 }}:</strong> {{ chunk.text }}
              </div>
            </transition-group>
          </div>
        </v-col>
      </v-row>
    </template>
  </TableWithFooter>
</template>

<script>
import { computed, ref, watch } from 'vue';
import { formatDate } from '@/utils/dateFormatter';
import CustomTooltip from '@/components/Tooltip.vue';
import TableWithFooter from '@/components/elements/Tables/TableWithFooter.vue';
import FactStatusChips from '@/components/results/FactStatusChips.vue';
import { formatCost, getFactStatusClass } from '@/composables/experimentResultsTransforms';
import { formatAnswer, markdownToHtml } from '@/composables/useExperimentResults';

export default {
  name: 'DetailedResultsTable',
  components: {
    CustomTooltip,
    TableWithFooter,
    FactStatusChips,
  },
  props: {
    items: {
      type: Array,
      required: true,
    },
  },
  emits: ['toggle-expand', 'toggle-fact-chunk', 'toggle-chunk'],
  setup(props) {
    // Render one page at a time. A large experiment (e.g. 108 questions /
    // 2258 facts) previously rendered every group and every nested fact row
    // at once, which is the main cost of opening the results page. The
    // footer only appears when there is more than one page, so small
    // experiments look and behave exactly as before.
    const itemsPerPage = ref(25);
    const currentPage = ref(1);

    const paginatedItems = computed(() => {
      const start = (currentPage.value - 1) * itemsPerPage.value;
      return props.items.slice(start, start + itemsPerPage.value);
    });

    // Filters change the list length: go back to page 1 if the current page
    // no longer exists.
    watch(() => props.items.length, () => {
      const maxPage = Math.max(1, Math.ceil(props.items.length / itemsPerPage.value));
      if (currentPage.value > maxPage) currentPage.value = 1;
    });

    const onPageChange = (page) => { currentPage.value = page; };
    const onItemsPerPageChange = (count) => {
      itemsPerPage.value = count;
      currentPage.value = 1;
    };

    return {
      formatDate, formatCost, getFactStatusClass, formatAnswer, markdownToHtml,
      currentPage, itemsPerPage, paginatedItems,
      onPageChange, onItemsPerPageChange,
    };
  },
};
</script>

<style scoped>
/* Moved verbatim from ExperimentResults.vue. The generic table/th/td rules
   are kept because they cascade onto .evaluation-summary (background,
   specificity-resolved paddings) exactly as in the monolith. */
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
  background-color: white;
}

th, td {
  border: 1px solid #ddd;
  padding: 12px;
  text-align: left;
}

th {
  background-color: #f2f2f2;
  font-weight: bold;
}

.details-table {
  display: table;
  width: 100%;
  margin-bottom: 15px;
}

.details-row {
  display: table-row;
}

.details-label, .details-value {
  display: table-cell;
  padding: 5px;
  border-bottom: 1px solid #e0e0e0;
}

.details-label {
  font-weight: bold;
  width: 30%;
}

.evaluation-summary {
  width: 100%;
  border-collapse: collapse;
  margin-top: 15px;
}

.evaluation-summary th, .evaluation-summary td {
  border: 1px solid #e0e0e0;
  padding: 8px;
  text-align: center;
}

.evaluation-summary th {
  background-color: #f2f2f2;
  font-weight: bold;
}

.chunk-buttons-container {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}


.chunk-button {
  min-width: 40px;
  height: 40px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background-color: white;
  cursor: pointer;
  transition: all 0.3s ease;
}

.chunk-button.active {
  background-color: #17a2b8;
  color: white;
}

.chunk-button:hover {
  background-color: #f5f5f5;
  transform: translateY(-2px);
}

.chunk-fade-enter-active,
.chunk-fade-leave-active {
  transition: all 0.3s ease;
}

.chunk-fade-enter-from,
.chunk-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.chunk-content-container {
  margin-top: 16px;
}

.chunk-content {
  margin-bottom: 16px;
}
.chunk-content {
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 15px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.answer-text, .evaluation-text {
  font-family: 'Roboto', sans-serif;
  line-height: 1.6;
  background-color: #ffffff;
  padding: 15px;
  border-radius: 6px;
  margin-bottom: 15px;
  border: 1px solid #e0e0e0;
}

.facts-section, .chunks-section, .answers-section, .chunk-evaluations-section {
  margin-top: 20px;
  border-top: 1px solid #e0e0e0;
  padding-top: 20px;
}

.answer-section, .evaluation-section, .facts-section {
  margin: 20px 0;
  padding: 15px;
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.answer-text {
  margin-top: 15px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.fact-list {
  list-style-type: none;
  padding-left: 0;
}

.fact-status {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 10px;
}

/* Shared status colors (also scoped inside FactStatusChips): the fact dot
   above combines .fact-status with these classes. */
.status-ok { background-color: #28a745; }
.status-warning { background-color: #ffc107; }
.status-error { background-color: #dc3545; }
.status-extra { background-color: #787878; }

.fact-text {
  flex-grow: 1;
}

.fact-item {
  margin-bottom: 15px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.fact-header {
  display: flex;
  align-items: center;
  padding: 10px;
  background-color: #f8f9fa;
}

.fact-evaluations {
  padding: 10px;
}

.fact-eval {
  background-color: #e9ecef;
  padding: 10px;
  margin-bottom: 10px;
  border-radius: 4px;
}

.chunk-eval {
  background-color: #f0f4f8;
  padding: 10px;
  margin-bottom: 10px;
  border-radius: 4px;
}

.fact-eval, .chunk-eval {
  margin-top: 5px;
  padding: 8px;
  border-radius: 4px;
  font-size: 0.9em;
  color: #666;
}

.problem-analysis {
  background-color: #f8d7da;
  color: #721c24;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 10px;
}

.problem-analysis p {
  margin: 0;
}

.problem-analysis strong {
  display: block;
  margin-bottom: 5px;
}

.chunk-button {
  margin: 0 5px;
  padding: 2px 5px;
  background-color: #f0f0f0;
  border: 1px solid #ccc;
  border-radius: 3px;
  cursor: pointer;
}

.chunk-button:hover {
  background-color: #e0e0e0;
}

.chunk-text {
  margin-top: 10px;
  padding: 10px;
  background-color: #f9f9f9;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
}
</style>
