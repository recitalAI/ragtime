<template>
  <div class="experiment-results page-padding py-7">
    <div v-if="loading">Loading results...</div>
    <div v-else-if="error" class="error-message">{{ error }}</div>
    <h2
      v-else
      class="h2-text mb-7"
    >
      {{ experimentName }}
    </h2>
      <!-- Main Summary table -->
      <h3 class="h3-text black--text mb-4">
        Summary
      </h3>
      <TableWithFooter
        class="mb-8"
        :items="mainResults"
        :loading="loading"
        :show-footer="false"
      >
        <template #header>
          <v-col cols="3">
            Model
          </v-col>
          <v-col cols="3">
            Date
          </v-col>
          <v-col
            class="justify-center"
            cols="1"
          >
            Facts
          </v-col>
          <v-col
            class="justify-center"
            cols="1"
          >
            Ok
            <CustomTooltip text="Number of facts that exist in the answer." />
          </v-col>
          <v-col
            class="justify-center"
            cols="1"
          >
            Hallu
            <CustomTooltip text="Number of facts for which the answer presented contradictory or misaligned information." />
          </v-col>
          <v-col
            class="justify-center"
            cols="1"
          >
            Missing
            <CustomTooltip text="Number of facts that do not exist in the answer." />
          </v-col>
          <v-col
            class="justify-center"
            cols="1"
          >
            Extra
            <CustomTooltip text="Additional information in the answer." />

          </v-col>
        </template>
        <template #body>
          <v-row
            v-for="result in mainResults"
            class="table-row table-row-height"
            :key="result.name"
          >
            <v-col
              :class="[
                'primary--text',
                'align-center',
                { 'clickable': hasChunkEvaluations }
              ]"
              cols="3"
              @click="hasChunkEvaluations ? toggleChunksSummary(result.name) : null"
            >
              {{ result.name }}
            </v-col>
            <v-col cols="3">
              {{ formatDate(result.date) }}
            </v-col>
            <v-col
              class="justify-center"
              cols="1"
            >
              {{ result.facts }}
            </v-col>
            <v-col
              class="justify-center"
              cols="1"
            >
              <div class="percentage"><span class="status-indicator status-ok"></span>{{ calculatePercentage(result.ok, result.facts) }}%  <div class="absolute-count">({{ result.ok }}/{{ result.facts }})</div></div>
            </v-col>
            <v-col
              class="justify-center"
              cols="1"
            >
              <div class="percentage"><span class="status-indicator status-error"></span>{{ calculatePercentage(result.hallu, result.facts) }}%  <div class="absolute-count">({{ result.hallu }}/{{ result.facts }})</div></div>
            </v-col>
            <v-col
              class="justify-center"
              cols="1"
            >
                <div class="percentage"><span class="status-indicator status-warning"></span>{{ calculatePercentage(result.missing, result.facts) }}%  <div class="absolute-count">({{ result.missing }}/{{ result.facts }})</div></div>
            </v-col>
            <v-col
              class="justify-center"
              cols="1"
            >
            <div class="numeric"><span class="status-indicator status-extra"></span>{{ result.extra }}</div>
            </v-col>
          </v-row>
        </template>
      </TableWithFooter>
      <v-dialog
        v-model="showChunksSummary"
        @update:model-value="(value) => {
          if (!value) {
            closeChunksSummary();
          }
        }"
      >
        <v-card style="width: 600px">
          <v-card-title class="h2-text primary--text mb-6">
            {{ selectedModel }}
          </v-card-title>
          <v-card-body>
            <v-row
              class="table-row mb-2"
              style="border-bottom: none;"
            >
              <v-col cols="4">
              </v-col>
              <v-col
                class="justify-end"
                cols="4"
              >
                <h5 class="h5-text">
                  Errors due to LLM
                </h5>
              </v-col>
              <v-col
                class="justify-end"
                cols="4"
              >
                <h5 class="h5-text">
                  Errors due to retriever
                </h5>
              </v-col>
            </v-row>
            <v-row
              class="table-row mb-2"
              style="border-bottom: none;"
            >
              <v-col
                class="h5-text"
                cols="4"
              >
                <h5>
                  Hallucinations
                </h5>
              </v-col>
              <v-col
                class="justify-end"
                cols="4"
              >
                {{ chunksSummary.llm.hallucinations }} ({{ chunksSummary.llm.hallucinationsPr.toFixed(1) }}%)
              </v-col>
              <v-col
                class="justify-end"
                cols="4"
              >
                {{ chunksSummary.chunks.hallucinations }} ({{ chunksSummary.chunks.hallucinationsPr.toFixed(1) }}%)
              </v-col>
            </v-row>
            <v-row
              class="table-row mb-2"
              style="border-bottom: none;"
            >
              <v-col
                class="h5-text"
                cols="4"
              >
                <h5>
                  Missing
                </h5>
              </v-col>
              <v-col
                class="justify-end"
                cols="4"
              >
                {{ chunksSummary.llm.missings }} ({{ chunksSummary.llm.missingsPr.toFixed(1) }}%)
              </v-col>
              <v-col
                class="justify-end"
                cols="4"
              >
                {{ chunksSummary.chunks.missings }} ({{ chunksSummary.chunks.missingsPr.toFixed(1) }}%)
              </v-col>
            </v-row>
            <v-row
              class="table-row mb-2"
              style="border-bottom: none;"
            >
              <v-col
                class="h5-text"
                cols="4"
              >
                <h5>
                  Combined
                </h5>
              </v-col>
              <v-col
                class="justify-end"
                cols="4"
              >
                {{ chunksSummary.llm.combined }} ({{ chunksSummary.llm.combinedPr.toFixed(1) }}%)
              </v-col>
              <v-col
                class="justify-end"
                cols="4"
              >
                {{ chunksSummary.chunks.combined }} ({{ chunksSummary.chunks.combinedPr.toFixed(1) }}%)
              </v-col>
            </v-row>
            <v-row
              class="table-row mb-2"
              style="border-bottom: none;"
            >
              <v-col
                class="h5-text"
                cols="4"
              >
                <h5>
                  Whole Test
                </h5>
              </v-col>
              <v-col
                class="justify-end"
                cols="4"
              >
                {{ chunksSummary.llm.wholeTest }} ({{ chunksSummary.llm.wholeTestPr.toFixed(1) }}%)
              </v-col>
              <v-col
                class="justify-end"
                cols="4"
              >
                {{ chunksSummary.chunks.wholeTest }} ({{ chunksSummary.chunks.wholeTestPr.toFixed(1) }}%)
              </v-col>
            </v-row>
          </v-card-body>
          <v-card-actions>
            <v-btn
              color="primary"
              variant="flat"
              @click="closeChunksSummary"
              rounded
            >
              Close
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>

      <!-- Detailed question-by-question results -->
      <div class="detailed-results">
        <div class="results-header">
          <h3 class="h3-text black--text">
            Question results
          </h3>
          <div class="filter-container">
            <span class="h4-text">
              Filter:
            </span>
            <div class="filter-checkboxes">
              <v-checkbox
                v-model="filters.ok"
                label="Ok"
                hide-details
              />
              <v-checkbox
                v-model="filters.hallu"
                class="ml-3 mt-0"
                label="Hallu"
                hide-details
              />
              <v-checkbox
                v-model="filters.missing"
                class="ml-3 mt-0"
                label="Missing"
                hide-details
              />
              <v-checkbox
                v-model="filters.extra"
                class="ml-3 mt-0"
                label="Extra"
                hide-details
              />
            </div>
          </div>
        </div>
        <TableWithFooter
          :items="filteredDetailedResults"
          :loading="loadingDetails"
          :show-footer="false"
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
              v-for="(group, index) in filteredDetailedResults"
              :key="`main-${index}`"
              class="table-row py-1"
              style="min-height: 55px;"
            >
              <v-col
                class="primary--text justify-center align-center clickable"
                cols="1"
                @click="toggleExpandedDetails(group)"
              >
                {{ index + 1 }}
              </v-col>
              <v-col
                class="primary--text align-center justify-start clickable"
                @click="toggleExpandedDetails(group)"
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
                <div class="percentage"><span class="status-indicator status-ok"></span>{{ calculatePercentage(group.mainResult.ok, group.mainResult.factsCount) }}%  <div class="absolute-count">({{ group.mainResult.ok }}/{{group.mainResult.factsCount}})</div></div>

              </v-col>
              <v-col
                class="align-center justify-center"
                cols="1"
              >
                <div class="percentage"><span class="status-indicator status-error"></span>{{ calculatePercentage(group.mainResult.hallu, group.mainResult.factsCount) }}%  <div class="absolute-count">({{ group.mainResult.hallu }}/{{group.mainResult.factsCount}})</div></div>
              </v-col>
              <v-col
                class="align-center justify-center"
                cols="1"
              >
                <div class="percentage"><span class="status-indicator status-warning"></span>{{ calculatePercentage(group.mainResult.missing, group.mainResult.factsCount) }}%  <div class="absolute-count">({{ group.mainResult.missing }}/{{group.mainResult.factsCount}})</div></div>
              </v-col>
              <v-col
                class="align-center justify-center"
                cols="1"
              >
                <span class="status-indicator status-extra"></span>{{ group.mainResult.extra }}
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
                              @click="showChunk(group, factIndex, button.number)"
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
              </v-col>
            </v-row>
          </template>
        </TableWithFooter>
      </div>
    </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { experimentService } from '@/services/generatorService';
import { formatDate } from '@/utils/dateFormatter';
import CustomTooltip from './Tooltip.vue';
import { marked } from 'marked';
import TableWithFooter from '@/components/elements/Tables/TableWithFooter.vue';


export default {
  name: 'ExperimentResults',
  props: {
    path: String
  },

  components: {
    CustomTooltip,
    TableWithFooter,
  },

  setup(props) {
    const router = useRouter();
    const mainResults = ref([]);
    const chunkResults = ref([]);
    const detailedResults = ref([]);
    const fullEvaluation = ref([]);
    const loading = ref(true);
    const error = ref(null);
    const experimentName = ref('');
    const showDetailedResults = ref(false);
    const showChunksSummary = ref(false);
    const selectedModel = ref('');
    const visibleQuestions = ref({});
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
      return groupedDetailedResults.value.filter(group => {
        if (filters.value.ok || filters.value.hallu || filters.value.missing || filters.value.extra) {
          return (
            (filters.value.ok && group.mainResult.ok > 0) ||
            (filters.value.hallu && group.mainResult.hallu > 0) ||
            (filters.value.missing && group.mainResult.missing > 0) ||
            (filters.value.extra && group.mainResult.extra > 0)
          );
        }
        return true;
      });
    });


    const getChunkEvalClass = (model) => {
      if (model === 'Missings Eval') return 'missings-eval';
      if (model === 'Hallucinations Eval' || model === 'Hallucination Eval') return 'hallucinations-eval';
      return '';
    };
    
    const processDetailedResults = (results, fullEval) => {
      const groups = {};
      results.forEach(result => {
        if (!groups[result.text]) {
          const fullEvalItem = fullEval.find(item => item.question === result.text);
          
          if (!fullEvalItem) {
            console.error(`No matching full evaluation item found for question: ${result.text}`);
            return; // Skip this iteration
          }
          
          const mainAnswer = fullEvalItem.answers && fullEvalItem.answers[0];
          
          if (!mainAnswer) {
            console.error(`No main answer found for question: ${result.text}`);
            return; // Skip this iteration
          }
          
          const evaluation = mainAnswer.evaluation;
          groups[result.text] = {
            question: result.text,
            mainResult: null,
            factsCount: result.factsCount,
            chunkEvals: [],
            hasChunkEvals: false,
            showChunkEvals: false,
            showDetails: false,
            showExpanded: false,
            facts: (fullEvalItem.facts || []).map((fact, index) => {
              const factNumber = index + 1;
              let status = 'unknown';
              let factEvaluation = ''; 
              if (evaluation && evaluation.text) {
                factEvaluation = extractFactEvaluation(evaluation.text, factNumber);
                if (factEvaluation.result.includes('[OK]')) status = 'ok';
                else if (factEvaluation.result.includes('[NOT FOUND]')) status = 'missing';
                else if (factEvaluation.result.includes('[HALLU]')) status = 'hallu';
              }

              const { status: chunkStatus, evaluation: chunkEvaluation, chunkButtons } = extractChunkEvaluation(fullEvalItem.chunkEvaluations, factNumber, fullEvalItem.chunks || []);
              
              
              const { problemType, explanation } = analyzeFactAndChunkStatus(status, chunkStatus);
              return {
                ...fact,
                status,
                evaluation: factEvaluation.evalShow,
                chunkEval: chunkEvaluation,
                chunkButtons: chunkButtons.map(button => ({ ...button, isVisible: false })),
                problemType,
                problemExplanation: explanation
              };
            }),
            answer: mainAnswer.text || '',
            answerModel: mainAnswer.model || 'Unknown',
            answerDate: mainAnswer.time || '',
            answerDuration: mainAnswer.duration || 0,
            answerCost: mainAnswer.cost || 0,
            evalModel: evaluation?.model || 'Unknown',
            evalDate: evaluation?.time || '',
            evalDuration: evaluation?.duration || 0,
            evalCost: evaluation?.cost || 0,
          };
        }
        if (result.model !== "Missings Eval" && result.model !== "Hallucinations Eval" && result.model !== "Hallucination Eval") {
          groups[result.text].mainResult = result;
          groups[result.text].mainModel = result.model;
        } else {
          groups[result.text].chunkEvals.push(result);
          groups[result.text].hasChunkEvals = true;
        }
      });
      groupedDetailedResults.value = Object.values(groups);
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

    const extractFactEvaluation = (evalText, factNumber) => {
      if (!evalText) return { factEvaluation: '', evalShow: '' };
      // Remove HTML tags and normalize newlines
      const cleanText = evalText.replace(/<\/?[^>]+(>|$)/g, "\n").replace(/\n+/g, "\n").trim();

      // Remove [EXTRA] and everything after it
      const textWithoutExtra = cleanText.split(/\[extra\]|\[EXTRA\]|<p>\s*\[?extra\]?/i)[0];

      // Pattern for numbered or unnumbered list items
      const itemPattern = new RegExp(
        `(?:^|\\n)\\s*(?:${factNumber}\\.|\\[?${factNumber}\\]?)?\\s*` +
        `\\[(OK|NOT FOUND|HALLU)\\]` +
        `(?:(?!(?:\\n\\s*(?:${factNumber}\\.|\\[?${factNumber}\\]?)?\\s*\\[(OK|NOT FOUND|HALLU)\\])).)*`,
        'gms'
      );
      const paragraphPattern = new RegExp(`(?:Part(?:ie)? (?:in|dans) (?:the|le) paragraphe?|Citation pertinente du paragraphe|Part in the paragraph)\\s*(?::|:?\\s*)(.*)|(No part in the paragraph supports this fact\\.)`, 'i');
      let matches;
      let result;
      try {
        matches = [...(textWithoutExtra.matchAll(itemPattern) || [])];
        if (matches.length > 0) {
          result = matches[factNumber - 1][0].trim();
          
          // Check for multiple occurrences of the pattern
          const patternToCheck = /(?:\n\s*(?:\d+\.|\[?\d+\]?)?\s*\[(OK|NOT FOUND|HALLU)\])/g;
          const occurrences = (result.match(patternToCheck) || []).length;
          
          if (occurrences > 1) {
            console.warn('Multiple fact patterns found in the result. Resetting matches.');
            matches = [];
            result = '';
          }
        }
      } catch (error) {
        console.warn('Error with initial pattern matching:', error);
        matches = [];
        result = '';
      }

      if (matches.length === 0) {
        console.log('No matches found with itemPattern, trying itemPattern2');
        const itemPattern2 = new RegExp(
          `(?:^|\\n)\\s*(?:${factNumber}\\.|\\[?${factNumber}\\]?)?\\s*` +
          `\\[(OK|NOT FOUND|HALLU)\\]` +
          `(?:(?!(?:\\n\\s*(?:\\d+\\.|\\[?\\d+\\]?)?\\s*\\[(OK|NOT FOUND|HALLU)\\])).)*` +
          `(?=\\s*\\d+\\s*$|$)`,
          'gms'
        );
        try {
          matches = textWithoutExtra.match(itemPattern2);
          result = matches[0].trim();
        } catch (error) {
          console.warn('Error with fallback pattern matching:', error);
          matches = [];
        }
      }
      if (!matches) return { factEvaluation: '', evalShow: '' };
      
      const stateMatch = result.match(/^\s*(?:\d+\.|\[\d+\])?\s*\[(OK|NOT FOUND|HALLU)\]/i);
      const state = stateMatch ? stateMatch[1] : '';
      
      let uniqueResult = result.replace(/^\s*(?:\d+\.|\[\d+\])?\s*\[(OK|NOT FOUND|HALLU)\]\s*-?\s*/i, '');
      const partMatch = result.match(paragraphPattern);
      let processedPartMatch = '';
      
      if (partMatch) {
        processedPartMatch = (partMatch[1] || partMatch[2] || '').trim();
        uniqueResult = uniqueResult.replace(partMatch[0], '').trim();
      }
      processedPartMatch = processedPartMatch.replace(/N\/A|None/gi, "").trim();
      const evalShow = `<p><em>${processedPartMatch || ' '}</em></p><p>${uniqueResult}</p>`;

      return { result: `[${state}] ${uniqueResult}`, evalShow };
    };

    const extractChunkEvaluation = (chunkEvals, factNumber, qaChunks) => {

      if (!chunkEvals) {
        return { status: '', evaluation: '', chunkButtons: [] };
      }

      const relevantEval = chunkEvals.find(evalItem => 
        evalItem.evaluation && evalItem.evaluation.text && evalItem.evaluation.text.includes(`[Fait ${factNumber}]`)
      );

      if (relevantEval) {
        
        const regex = new RegExp(`\\[Fait ${factNumber}\\].*?(?=\\[Fait|$)`, 's');
        const match = relevantEval.evaluation.text.match(regex);
        const result = match ? match[0].trim() : '';

        const statusRegex = /(?:statut|status)\s*(?::)?\s*\[?(OK|HALLU|MISSING)\]?/i;
        const statusMatch = result.match(statusRegex);
        const status = statusMatch ? statusMatch[1].toLowerCase() : '';

        const explanationRegex = /Explication : (.*?)(?=\nLes chunks|\nSource|$)/s;
        const explanationMatch = result.match(explanationRegex);
        const explanation = explanationMatch ? explanationMatch[1].trim() : '';

        const sourceRegex = /Source(?:\s*\(si applicable\))?\s*(?::)?\s*"([^"]*)"/;
        const sourceMatch = result.match(sourceRegex);
        const source = sourceMatch ? `<em>${sourceMatch[1]}</em>` : '';

        // Extract chunks and create buttons
        const chunksRegex = /Les chunks(?:\s*\(si applicable\))?\s*(?::)?\s*"([^"]*)"/;
        const chunksMatch = result.match(chunksRegex);
        const chunks = chunksMatch ? chunksMatch[1] : '';

        const chunkNumbers = chunks.match(/\d+/g) || [];

        const chunkButtons = chunkNumbers.map(num => ({
          number: parseInt(num),
          text: qaChunks[parseInt(num) - 1]?.text || 'Chunk not found',
          isVisible: false
        }));
        console.log('Created chunk buttons:', chunkButtons);

        const formattedEval = `
          ${source ? `<p>Source : ${source}</p>` : ''}
          <p>${explanation}</p>
        `;

        return { status, evaluation: formattedEval, chunkButtons };
      }

      return { status: '', evaluation: '', chunkButtons: [] };
    };


    const analyzeFactAndChunkStatus = (factStatus, chunkStatus) => {
      let problemType = '';
      let explanation = '';

      switch (`${factStatus}${chunkStatus}`) {
        case 'missingok':
          problemType = 'LLM issue';
          explanation = `Correct chunks retrieved but the LLM failed to generate the correct answer.`;
          break;
        case 'missingmissing':
          problemType = 'Retriever or source issue';
          explanation = 'Chunks do not provide the correct context.';
          break;
        case 'missinghallu':
          problemType = 'Retriever or source issue';
          explanation = `Chunks provide inconsistent context, LLM detected that and didn't answer.`;
          break;
        case 'halluok':
          problemType = 'LLM issue';
          explanation = 'Retriever provided correct context, but the LLM hallucinated the answer.';
          break;
        case 'hallumissing':
          problemType = 'LLM and retriever or source issue'; 
          explanation = 'Retriever provided incorrect context, LLM hallucinated the answer.';
          break;
        case 'halluhallu':
          problemType = 'LLM and retriever or source issue';
          explanation = 'Retriever provided incorrect context, LLM then provided an hallucinated answer.';
          break;
        default:
          problemType = '';
          explanation = '';
      }

      return { problemType, explanation };
    };
    const toggleChunkEvals = (group) => {
      group.showChunkEvals = !group.showChunkEvals;
    };

    const toggleExpandedDetails = (group) => {
      group.showExpanded = !group.showExpanded;
    };

    const fetchResults = async () => {
      if (props.path) {
        try {
          loading.value = true;
          error.value = null;
          const data = await experimentService.getExperimentResults(props.path);
          processResults(data.summary);
          processDetailedResults(data.detailed, data.full);
          fullEvaluation.value = data.full;
          experimentName.value = props.path.split('/').pop().replace('.json', '');
        } catch (err) {
          console.error('Error fetching experiment results:', err);
          error.value = 'Error fetching experiment results: ' + err.message;
        } finally {
          loading.value = false;
        }
      } else {
        error.value = 'No results path provided';
        loading.value = false;
      }
    };

    const processResults = (results) => {
      mainResults.value = results.filter(result => !result.isChunkEval);
      chunkResults.value = results.filter(result => result.isChunkEval);
    };

    const markdownToHtml = (text) => {
      return marked(text);
    };

    const formatAnswer = (text) => {
      const formattedText = text.replace(/([:.)\]])(nn?)/g, (match, p1, p2) => {
        return p1 + (p2 === 'nn' ? '<br><br>' : '<br>');
      });
      return marked(formattedText);
    };

    const toggleChunksSummary = (modelName) => {
      if (selectedModel.value === modelName && showChunksSummary.value) {
        showChunksSummary.value = false;
      } else {
        selectedModel.value = modelName;
        calculateChunksSummary(modelName);
        showChunksSummary.value = true;
      }
    };

    const calculateChunksSummary = (modelName) => {
      let totalFacts = 0;
      let totalHallu = 0, totalMissing = 0;
      let llmHallu = 0, llmMissing = 0, chunksHallu = 0, chunksMissing = 0;

      fullEvaluation.value.forEach((item) => {
        totalFacts += item.facts.length;

        const mainAnswer = item.answers.find(a => a.model === modelName);
        if (mainAnswer && mainAnswer.evaluation) {
          totalHallu += mainAnswer.evaluation.hallu?.length || 0;
          totalMissing += mainAnswer.evaluation.missing?.length || 0;
        }

        const chunksHalluEval = item.chunkEvaluations.find(e => e.type === "Hallucinations Eval" || e.type === "Hallucination Eval")?.evaluation;
        const chunksMissingEval = item.chunkEvaluations.find(e => e.type === "Missings Eval")?.evaluation;

        if (chunksHalluEval && chunksHalluEval.meta) {
          llmHallu += (chunksHalluEval.meta.nb_ok || 0) + (chunksHalluEval.meta.nb_missing || 0);
          chunksHallu += (chunksHalluEval.meta.nb_hallu || 0) + (chunksHalluEval.meta.nb_missing || 0);
        }

        if (chunksMissingEval && chunksMissingEval.meta) {
          llmMissing += chunksMissingEval.meta.nb_ok || 0;
          chunksMissing += (chunksMissingEval.meta.nb_missing || 0) + (chunksMissingEval.meta.nb_hallu || 0);
        }
      });

      const llmCombined = llmHallu + llmMissing;
      const chunksCombined = chunksHallu + chunksMissing;
      const totalErrors = totalHallu + totalMissing;

      const calculatePercentage = (value, total) => {
        return total !== 0 ? Number((value / total * 100).toFixed(2)) : 0;
      };

      chunksSummary.value = {
        llm: {
          hallucinations: `${llmHallu} / ${totalHallu}`,
          hallucinationsPr: calculatePercentage(llmHallu, totalHallu),
          missings: `${llmMissing}/ ${totalMissing}`,
          missingsPr: calculatePercentage(llmMissing, totalMissing),
          combined: `${llmCombined}/ ${totalErrors}`,
          combinedPr: calculatePercentage(llmCombined, totalErrors),
          wholeTest: `${llmCombined}/ ${totalFacts}`,
          wholeTestPr: calculatePercentage(llmCombined, totalFacts)
        },
        chunks: {
          hallucinationsPr: calculatePercentage(chunksHallu, totalHallu),
          hallucinations: `${chunksHallu}/ ${totalHallu}`,
          missingsPr: calculatePercentage(chunksMissing, totalMissing),
          missings: `${chunksMissing}/ ${totalMissing}`,
          combinedPr: calculatePercentage(chunksCombined, totalErrors),
          combined: `${chunksCombined}/ ${totalErrors}`,
          wholeTestPr: calculatePercentage(chunksCombined, totalFacts),
          wholeTest: `${chunksCombined}/ ${totalFacts}`
        }
      };
    };

    const getFactStatusClass = (status) => {
      switch (status) {
        case 'ok':
          return 'status-ok';
        case 'hallu':
          return 'status-error';
        case 'missing':
          return 'status-warning';
        default:
          return '';
      }
    };

    const formatCost = (cost) => {
      return `${(cost * 100).toFixed(2)}c$`;
    };

    const showDetailedEvaluation = (group) => {
      const index = groupedDetailedResults.value.findIndex(g => g === group);
      const questionData = fullEvaluation.value[index];
      router.push({
        name: 'QuestionEvaluation',
        params: { index: index },
        query: { data: JSON.stringify(questionData) }
      });
    };

    const calculatePercentage = (value, total) => {
      if (total === 0) return '0.0';
      return ((value / total) * 100).toFixed(1);
    };

    const closeChunksSummary = () => {
      showChunksSummary.value = false;
      setTimeout(() => {
        selectedModel.value = '';
      }, 150);
    };

    onMounted(fetchResults);

    return {
      mainResults,
      chunkResults,
      detailedResults,
      fullEvaluation,
      loading,
      error,
      experimentName,
      showDetailedResults,
      formatDate,
      showChunksSummary,
      selectedModel,
      chunksSummary,
      hasChunkEvaluations,
      visibleQuestions,
      groupedDetailedResults,
      filteredDetailedResults,
      filters,
      showChunk,
      calculatePercentage,
      formatCost,
      getChunkEvalClass,
      toggleChunksSummary,
      toggleChunkEvals,
      toggleExpandedDetails,
      getFactStatusClass,
      markdownToHtml,
      formatAnswer,
      showDetailedEvaluation,
      closeChunksSummary,
    };
  }
};
</script>

<style scoped>
.experiment-results {
  max-width: 2000px;
}

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

.btn {
  padding: 10px 20px;
  margin: 10px 0;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 16px;
  transition: background-color 0.3s;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-info {
  background-color: #17a2b8;
  color: white;
}

.btn-sm {
  padding: 5px 10px;
  font-size: 14px;
}

.btn:hover {
  opacity: 0.9;
}

.full-evaluation {
  margin-top: 30px;
}

.answer-details, .evaluation-details {
  margin-top: 10px;
  background-color: #e9ecef;
  padding: 15px;
  border-radius: 6px;
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

.evaluation-text ol {
  padding-left: 20px;
}

.evaluation-text li {
  margin-bottom: 10px;
}

.eval-status {
  font-weight: bold;
  padding: 2px 6px;
  border-radius: 3px;
  margin-right: 5px;
  display: inline-block;
}

.eval-status.ok {
  background-color: #d4edda;
  color: #155724;
}

.eval-status.not-found {
  background-color: #f8d7da;
  color: #721c24;
}

.eval-status.hallu {
  background-color: #fff3cd;
  color: #856404;
}

.paragraph-part {
  font-style: italic;
  color: #6c757d;
  display: block;
  margin-top: 5px;
}

.extra-info {
  font-weight: bold;
  color: #0056b3;
  display: block;
  margin-top: 10px;
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

.eval-label {
  margin-right: 5px;
  font-weight: bold;
  color: #555;}

.eval-value {
  color: #333;
  margin-right: 15px;
}

.error-message {
  color: #721c24;
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
  padding: 10px;
  margin-top: 20px;
}

.facts-section, .chunks-section, .answers-section, .chunk-evaluations-section {
  margin-top: 20px;
  border-top: 1px solid #e0e0e0;
  padding-top: 20px;
}

.answer-item {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 20px;
  background-color: #f9f9f9;
}

.chunk-item {
  margin-bottom: 15px;
}

.chunk-content {
  background-color: #f8f9fa;
  padding: 10px;
  border-radius: 4px;
  margin-top: 10px;
}

.chunk-eval-row {
  background-color: #f0f8ff; 
  font-style: italic;
}

.chunk-eval-row td {
  color: #666; 
  border-top: none; 
}

.chunk-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 15px;
}

.chunk-buttons {
  display: flex;
  flex-wrap: wrap;
}

.chunk-button {
  margin-left: 10px;
  margin-bottom: 10px;
  transition: background-color 0.3s, color 0.3s, border-color 0.3s;
  border: 2px solid #17a2b8;
}

.chunk-button.active {
  background-color: #17a2b8;
  color: white;
}

.chunk-button:hover {
  background-color: #138496;
  border-color: #138496;
  color: white;
}

.chunk-content {
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 15px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.fade-enter,
.fade-leave-to {
  opacity: 0;
}

.missings-eval {
  background-color: #ffecb8 !important;
}

.hallucinations-eval {
  background-color: #ffaaaa !important;
}

.expanded-details {
  background-color: #f9f9f9;
  border-top: 1px solid #e0e0e0;
}

.answer-section, .evaluation-section, .facts-section {
  margin: 20px 0;
  padding: 15px;
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.answer-details {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  font-size: 0.9em;
  color: #666;
}

.answer-text {
  margin-top: 15px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.eval-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 15px;
}

.eval-table th, .eval-table td {
  border: 1px solid #e0e0e0;
  padding: 10px;
  text-align: center;
}

.eval-table th {
  background-color: #f2f2f2;
  font-weight: bold;
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

.fact-status.ok { background-color: #28a745; }
.fact-status.missing { background-color: #ffc107; }
.fact-status.hallu { background-color: #dc3545; }

.fact-number {
  font-weight: bold;
  margin-right: 10px;
}

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

.btn-expand {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.2em;
  color: #007bff;
}

.bullet {
  font-size: 1.2em;
  color: #007bff;
  margin-right: 10px;
}

.modal {
  display: block;
  position: fixed;
  z-index: 1;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  overflow: auto;
  background-color: rgba(0,0,0,0.4);
}

.modal-content {
  background-color: #fefefe;
  margin: 15% auto;
  padding: 20px;
  border: 1px solid #888;
  width: 80%;
  max-width: 600px;
  border-radius: 5px;
}

.close {
  color: #aaa;
  float: right;
  font-size: 28px;
  font-weight: bold;
  cursor: pointer;
}

.close:hover,
.close:focus {
  color: black;
  text-decoration: none;
  cursor: pointer;
}

.chunks-summary-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}

.chunks-summary-table th,
.chunks-summary-table td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: center;
}

.chunks-summary-table th {
  background-color: #f2f2f2;
  font-weight: bold;
}

.chunks-summary-table tr:nth-child(even) {
  background-color: #f9f9f9;
}

.chunk-eval-row[data-model="Missings Eval"] {
  background-color: #ffecb8;
}

.chunk-eval-row[data-model="Hallucinations Eval"],
.chunk-eval-row[data-model="Hallucination Eval"] {
  background-color: #ed8b8b;
}

.chunk-summary-btn {
  background-color: #28a745;
  color: white;
  border: none;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s, transform 0.2s;
}

.chunk-summary-btn:hover {
  background-color: #218838;
  transform: scale(1.05);
}

.chunks-summary {
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.summary-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-top: 20px;
}

.summary-card h5 {
  margin-bottom: 10px;
  color: #333;
}

.summary-card p {
  margin: 5px 0;
  color: #555;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s, transform 0.5s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

.chunks-summary-btn {
  background: linear-gradient(45deg, #4CAF50, #45a049);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  box-shadow: 0 2px 5px rgba(0,0,0,0.2);
}

.chunks-summary-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.3);
}

.btn-text {
  margin-right: 8px;
}

.btn-icon {
  background: none;
  border: none;
  font-size: 1.2em;
  cursor: pointer;
  padding: 5px;
  margin: 0 2px;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.3s;
}

.btn-icon:hover {
  background-color: #f0f0f0;
}

.btn-icon[title="Expand"],
.btn-icon[title="Collapse"] {
  color: #28a745;
}

.btn-icon[title="View Details"] {
  color: #007bff;
}

.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

.modal {
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-content {
  background-color: #ffffff;
  border-radius: 10px;
  padding: 30px;
  max-width: 600px;
  width: 90%;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}

.close-btn {
  position: absolute;
  top: 10px;
  right: 15px;
  font-size: 24px;
  cursor: pointer;
  background: none;
  border: none;
  color: #333;
}

.modal-title {
  text-align: center;
  margin-bottom: 20px;
  color: #333;
}

.summary-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.summary-card {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  transition: transform 0.3s;
}

.summary-card:hover {
  transform: translateY(-5px);
}

.summary-card.llm {
  border-top: 4px solid #4CAF50;
}

.summary-card.chunks {
  border-top: 4px solid #2196F3;
}

.summary-item {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.summary-label {
  font-weight: bold;
  color: #555;
}

.summary-value {
  color: #333;
}

/* Enhanced Table Styles */
.data-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  background-color: #ffffff;
  box-shadow: 0 2px 15px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  overflow: hidden;
}

.data-table thead {
  background-color: #f8f9fa;
}

.data-table th,
.data-table td {
  padding: 12px 15px;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

.data-table th {
  font-weight: 600;
  color: #333;
  text-transform: uppercase;
  font-size: 0.85em;
  letter-spacing: 0.5px;
}

.data-table tbody tr:not(.chunk-eval-row) {
  position: relative;
  z-index: 1;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.data-table tbody tr:hover {
  background-color: white;
  transition: background-color 0.3s ease;
}

.data-table td {
  font-size: 0.95em;
  color: #333;
}

/* Specific column styles */
.data-table {
  text-align: right;
}

.data-table .actions {
  text-align: center;
}

@media screen and (max-width: 600px) {
  .data-table {
    font-size: 0.8em;
  }
  
  .data-table th,
  .data-table td {
    padding: 8px 10px;
  }
}

.chunk-eval-row {
  font-style: italic;
}

.chunk-eval-row td {
  color: #666;
  border-top: none;
}

.missings-eval {
  background-color: #fff3cd; /* Light yellow background */
}

.hallucinations-eval {
  background-color: #f8d7da; /* Light red background */
}

/* Button styles within table */
.table-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9em;
  transition: all 0.3s ease;
}

.table-btn-primary {
  background-color: transparent;
  color: black;
}

.table-btn-primary:hover {
  background-color: transparent;
  color: black;
}

.details-box {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  font-size: 0.9em;
  background-color: #f0f0f0;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 10px;
  margin-bottom: 15px;
}

.details-box span {
  display: flex;
  align-items: center;
}

.details-box i {
  margin-right: 5px;
  color: #666;
}

/* Status indicators */
.status-indicator {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 5px;
}

.status-ok { background-color: #28a745; }
.status-warning { background-color: #ffc107; }
.status-error { background-color: #dc3545; }
.status-extra { background-color: #787878; }

.percentage {
  font-size: 1em;
  font-weight: bold;
}

.absolute-count {
  font-size: 0.8em;
  color: #666;
  text-align: center;
}

.numeric {
  text-align: center;
}

.detailed-results-table .question-col {
  width: 30%;
  max-width: 300px;
}

.detailed-results-table .ok-column {
  width: 20%;
}

.detailed-results-table .numeric {
  width: 10%;
}

.ok-count {
  font-weight: bold;
  margin-right: 5px;
}

.ok-details {
  margin-top: 10px;
  font-size: 0.9em;
  max-height: 100px;
  overflow-y: auto;
  background-color: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 5px;
}

.ok-details ul {
  padding-left: 20px;
  margin: 0;
}

.btn-outline-secondary {
  color: #6c757d;
  border-color: #6c757d;
  background-color: transparent;
}

.btn-outline-secondary:hover {
  color: #fff;
  background-color: #6c757d;
}

.question-buttons {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
  margin-bottom: 20px;
}

.question-button {
  background-color: #f0f0f0;
  border: none;
  border-radius: 20px;
  padding: 10px 20px;
  font-size: 14px;
  font-weight: bold;
  color: #333;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.question-button:hover {
  background-color: #e0e0e0;
}

.question-button.active {
  background-color: #007bff;
  color: white;
}

.question-button i {
  margin-left: 5px;
}

.evaluation-item {
  background-color: #f9f9f9;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.question-section {
  background-color: #007bff;
  color: white;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 15px;
}

.question-text {
  font-size: 18px;
  font-weight: bold;
  margin: 0;
}

.chunks-summary-container {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  margin-top: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.summary-title {
  text-align: center;
  margin-bottom: 20px;
  color: #333;
}

.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s ease-in-out;
  max-height: 1000px;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
}

.btn-link {
  color: #007bff;
  text-decoration: none;
  background-color: transparent;
  border: none;
  padding: 0;
  cursor: pointer;
}

.btn-link:hover {
  color: #0056b3;
  text-decoration: underline;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.filter-container {
  display: flex;
  align-items: center;
}

.filter-checkboxes {
  display: flex;
  align-items: center;
  cursor: pointer;
  margin: 0 10px;
}

.filter-checkboxes input[type="checkbox"] {
  margin-right: 5px;
}

/* Styles pour rendre les cases à cocher plus jolies */
.filter-checkboxes input[type="checkbox"] {
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border: 2px solid #007bff;
  border-radius: 3px;
  outline: none;
  transition: all 0.3s;
  position: relative;
  cursor: pointer;
}

.filter-checkboxes input[type="checkbox"]:checked {
  background-color: #007bff;
}

.filter-checkboxes input[type="checkbox"]:checked::before {
  content: '\2713';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  font-size: 14px;
}

.filter-checkboxes label:hover input[type="checkbox"] {
  border-color: #0056b3;
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