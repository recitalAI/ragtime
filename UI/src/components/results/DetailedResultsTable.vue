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
          <span>{{ group.question }}</span>
          <span
            v-if="group.badge"
            class="question-badge"
            :class="group.badge.level === 'ok' ? 'badge-ok' : 'badge-warn'"
            :title="group.badge.level === 'ok' ? 'All facts correct' : 'Errors — see attribution'"
          >
            {{ group.badge.label }}
          </span>
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
            <h3
              class="h3-text answer-toggle"
              @click="toggleAnswer(group)"
              :title="isAnswerCollapsed(group) ? 'Show answer' : 'Hide answer'"
            >
              <v-icon size="16" class="answer-chevron">
                {{ isAnswerCollapsed(group) ? 'fas fa-chevron-right' : 'fas fa-chevron-down' }}
              </v-icon>
              Answer
            </h3>
            <div v-show="!isAnswerCollapsed(group)">
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
              <div class="answer-text" v-html="highlightAnswer(group.answer, group.facts)"></div>
            </div>
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
            <div class="fact-eval-head">
              <span class="col-fact">Fact</span>
              <span class="col-extract">Generated text</span>
              <span class="col-comment">Comment</span>
            </div>
            <ul class="fact-list">
              <li
                v-for="(fact, factIndex) in group.facts"
                :key="factIndex"
                class="fact-row"
              >
                <div class="col-fact">
                  <span
                    :class="['fact-status', getFactStatusClass(fact.status), { 'fb-dimmed': voteOf(group, factIndex, 'verdict') === 'down' }]"
                  ></span>
                  <div class="cell-with-fb">
                    <div class="cell-body">
                      <span class="fact-text" :class="{ 'fb-dimmed': voteOf(group, factIndex, 'verdict') === 'down' }">{{ fact.text }}</span>
                      <div v-if="voteOf(group, factIndex, 'verdict') === 'down'" class="fb-correction">
                        <span class="fb-badge">corrigé</span>
                        <span class="fb-verdict-corrected">{{ correctionOf(group, factIndex, 'verdict') }}</span>
                      </div>
                    </div>
                    <div class="fb-thumbs">
                      <v-btn
                        icon
                        size="x-small"
                        variant="text"
                        :color="voteOf(group, factIndex, 'verdict') === 'up' ? 'primary' : 'grey'"
                        title="Verdict correct"
                        @click="thumbUp(group, fact, factIndex, 'verdict')"
                      >
                        <v-icon size="16">{{ voteOf(group, factIndex, 'verdict') === 'up' ? 'fas fa-thumbs-up' : 'far fa-thumbs-up' }}</v-icon>
                      </v-btn>
                      <v-btn
                        icon
                        size="x-small"
                        variant="text"
                        :color="voteOf(group, factIndex, 'verdict') === 'down' ? 'primary' : 'grey'"
                        title="Verdict incorrect — choisir le statut correct"
                        @click="openThumbDown(group, fact, factIndex, 'verdict')"
                      >
                        <v-icon size="16">{{ voteOf(group, factIndex, 'verdict') === 'down' ? 'fas fa-thumbs-down' : 'far fa-thumbs-down' }}</v-icon>
                      </v-btn>
                    </div>
                  </div>
                </div>
                <div class="col-extract">
                  <div class="cell-with-fb">
                    <div class="cell-body">
                      <em v-if="fact.evalExtract" :class="{ 'fb-dimmed': voteOf(group, factIndex, 'passage') === 'down' }">{{ fact.evalExtract }}</em>
                      <span v-else class="col-empty">—</span>
                      <div v-if="voteOf(group, factIndex, 'passage') === 'down'" class="fb-correction">
                        <span class="fb-badge">corrigé</span>
                        <span class="fb-corrected-text">{{ correctionOf(group, factIndex, 'passage') }}</span>
                      </div>
                    </div>
                    <div class="fb-thumbs">
                      <v-btn
                        icon
                        size="x-small"
                        variant="text"
                        :color="voteOf(group, factIndex, 'passage') === 'up' ? 'primary' : 'grey'"
                        title="Passage correct"
                        @click="thumbUp(group, fact, factIndex, 'passage')"
                      >
                        <v-icon size="16">{{ voteOf(group, factIndex, 'passage') === 'up' ? 'fas fa-thumbs-up' : 'far fa-thumbs-up' }}</v-icon>
                      </v-btn>
                      <v-btn
                        icon
                        size="x-small"
                        variant="text"
                        :color="voteOf(group, factIndex, 'passage') === 'down' ? 'primary' : 'grey'"
                        title="Passage incorrect — proposer une correction"
                        @click="openThumbDown(group, fact, factIndex, 'passage')"
                      >
                        <v-icon size="16">{{ voteOf(group, factIndex, 'passage') === 'down' ? 'fas fa-thumbs-down' : 'far fa-thumbs-down' }}</v-icon>
                      </v-btn>
                    </div>
                  </div>
                </div>
                <div class="col-comment">
                  <div class="cell-with-fb">
                    <div class="cell-body">
                      <span v-if="fact.evalComment" :class="{ 'fb-dimmed': voteOf(group, factIndex, 'judgment') === 'down' }">{{ fact.evalComment }}</span>
                      <span v-else class="col-empty">—</span>
                      <div v-if="voteOf(group, factIndex, 'judgment') === 'down'" class="fb-correction">
                        <span class="fb-badge">corrigé</span>
                        <span class="fb-corrected-text">{{ correctionOf(group, factIndex, 'judgment') }}</span>
                      </div>
                    </div>
                    <div class="fb-thumbs">
                      <v-btn
                        icon
                        size="x-small"
                        variant="text"
                        :color="voteOf(group, factIndex, 'judgment') === 'up' ? 'primary' : 'grey'"
                        title="Jugement correct"
                        @click="thumbUp(group, fact, factIndex, 'judgment')"
                      >
                        <v-icon size="16">{{ voteOf(group, factIndex, 'judgment') === 'up' ? 'fas fa-thumbs-up' : 'far fa-thumbs-up' }}</v-icon>
                      </v-btn>
                      <v-btn
                        icon
                        size="x-small"
                        variant="text"
                        :color="voteOf(group, factIndex, 'judgment') === 'down' ? 'primary' : 'grey'"
                        title="Jugement incorrect — proposer votre jugement"
                        @click="openThumbDown(group, fact, factIndex, 'judgment')"
                      >
                        <v-icon size="16">{{ voteOf(group, factIndex, 'judgment') === 'down' ? 'fas fa-thumbs-down' : 'far fa-thumbs-down' }}</v-icon>
                      </v-btn>
                    </div>
                  </div>
                </div>
                <div class="fact-evaluations col-span-all">
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

  <!-- I1: feedback correction modal (opens on 👎). Focused dialog for text
       entry, per UX best practice for multi-line correction input. -->
  <teleport to="body">
    <div v-if="modal.open" class="fb-modal-overlay" @click.self="closeModal">
      <div class="fb-modal">
        <h3 class="fb-modal-title">
          {{ modal.dim === 'passage' ? 'Corriger le passage extrait' : (modal.dim === 'verdict' ? 'Corriger le verdict' : 'Corriger le jugement') }}
        </h3>
        <p v-if="modal.fact" class="fb-modal-fact"><strong>Fait :</strong> {{ modal.fact.text }}</p>
        <div class="fb-modal-original">
          <div class="fb-modal-label">{{ modal.dim === 'passage' ? 'Passage de l’éval' : (modal.dim === 'verdict' ? 'Verdict de l’éval' : 'Jugement de l’éval') }} (original)</div>
          <div class="fb-modal-original-text">{{ (modal.original || '—') }}</div>
        </div>

        <!-- Verdict: pick the correct status. The "why" goes in the judgment. -->
        <template v-if="modal.dim === 'verdict'">
          <div class="fb-modal-label">Statut correct</div>
          <div class="fb-verdict-choices">
            <label v-for="opt in verdictOptions" :key="opt" class="fb-verdict-option">
              <input type="radio" :value="opt" v-model="modal.verdictChoice" />
              <span class="fb-verdict-optlabel">{{ opt === 'ok' ? 'OK' : (opt === 'hallu' ? 'HALLU' : 'MISSING') }}</span>
            </label>
          </div>
          <p class="fb-modal-hint">Expliquez le « pourquoi » via le 👎 sur la colonne Comment (jugement).</p>
        </template>

        <!-- Passage / judgment: free-text correction. -->
        <template v-else>
          <div class="fb-modal-label fb-modal-label-row">
            <span>{{ modal.dim === 'passage' ? 'Passage correct' : 'Votre jugement et sa logique' }}</span>
            <span
              v-if="modal.dim === 'passage'"
              class="fb-help"
              title="S’il n’y a aucun passage à extraire dans la réponse, écrivez None."
            >ⓘ</span>
          </div>
          <textarea
            v-model="modal.text"
            class="fb-modal-textarea"
            rows="4"
            :placeholder="modal.dim === 'passage' ? 'Passage correct, ou None s’il n’y a rien à extraire' : 'Expliquez pourquoi l’éval se trompe et votre raisonnement'"
          ></textarea>
        </template>
        <div class="fb-modal-actions">
          <button type="button" class="fb-modal-btn" @click="closeModal">Annuler</button>
          <button type="button" class="fb-modal-btn primary" @click="submitModal">Valider</button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script>
import { computed, ref, watch } from 'vue';
import { formatDate } from '@/utils/dateFormatter';
import CustomTooltip from '@/components/Tooltip.vue';
import TableWithFooter from '@/components/elements/Tables/TableWithFooter.vue';
import FactStatusChips from '@/components/results/FactStatusChips.vue';
import { formatCost, getFactStatusClass } from '@/composables/experimentResultsTransforms';
import { highlightAnswer } from '@/composables/useExperimentResults';
import { experimentService } from '@/services/generatorService';

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
    experimentName: {
      type: String,
      default: '',
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

    // I3: collapsible answer block. Answers are expanded by default; the user
    // can collapse any one to save space. Keyed by question text (unique per
    // experiment) so it survives pagination.
    const collapsedAnswers = ref(new Set());
    const isAnswerCollapsed = (group) => collapsedAnswers.value.has(group.question);
    const toggleAnswer = (group) => {
      const s = new Set(collapsedAnswers.value);
      if (s.has(group.question)) s.delete(group.question);
      else s.add(group.question);
      collapsedAnswers.value = s;
    };

    // ── I1: human feedback (👍/👎 on passage & judgment) ──────────────────
    // feedback map keyed "questionIndex:factIndex" -> { passage?, judgment? }
    const feedback = ref({});
    const fbKey = (qi, fi) => `${qi}:${fi}`;
    // group.originalIndex is 1-based; the backend keys on 0-based question index.
    const qIndexOf = (group) => (group.originalIndex || 1) - 1;

    const loadFeedback = async () => {
      if (!props.experimentName) return;
      try {
        const data = await experimentService.getFeedback(props.experimentName);
        const map = {};
        for (const it of (data.items || [])) {
          map[fbKey(it.question_index, it.fact_index)] = {
            verdict: it.verdict || null,
            passage: it.passage || null,
            judgment: it.judgment || null,
          };
        }
        feedback.value = map;
      } catch (e) {
        // No feedback yet or endpoint unavailable — start empty, never block UI.
        feedback.value = {};
      }
    };
    // Load feedback as soon as the experiment name is available. Using a
    // watcher (immediate) instead of onMounted alone, because experimentName is
    // set asynchronously after the results fetch — onMounted could run before
    // the prop is populated, so the reload would show no feedback.
    watch(() => props.experimentName, (name) => {
      if (name) loadFeedback();
    }, { immediate: true });

    const getFb = (group, factIndex, dim) => {
      const e = feedback.value[fbKey(qIndexOf(group), factIndex)];
      return e ? e[dim] : null;
    };
    const voteOf = (group, factIndex, dim) => {
      const f = getFb(group, factIndex, dim);
      return f ? f.vote : null;
    };
    const correctionOf = (group, factIndex, dim) => {
      const f = getFb(group, factIndex, dim);
      return f && f.vote === 'down' ? (f.corrected || '') : '';
    };

    // Persist one dimension's feedback and update the local map.
    const persist = async (group, fact, factIndex, dim, payload) => {
      const qi = qIndexOf(group);
      const entry = {
        question_index: qi,
        question_text: group.question,
        fact_index: factIndex,
        fact_text: fact.text,
        status: fact.status,
        [dim]: payload,
      };
      // optimistic local update
      const key = fbKey(qi, factIndex);
      feedback.value = {
        ...feedback.value,
        [key]: { ...(feedback.value[key] || {}), [dim]: payload },
      };
      try {
        await experimentService.saveFeedback(props.experimentName, entry);
      } catch (e) {
        // revert on failure
        await loadFeedback();
      }
    };

    const clearFb = async (group, factIndex, dim) => {
      const qi = qIndexOf(group);
      const key = fbKey(qi, factIndex);
      const cur = { ...(feedback.value[key] || {}) };
      delete cur[dim];
      feedback.value = { ...feedback.value, [key]: cur };
      try {
        await experimentService.deleteFeedback(props.experimentName, qi, factIndex, dim);
      } catch (e) {
        await loadFeedback();
      }
    };

    // 👍 : just record an up vote (no correction needed).
    const thumbUp = (group, fact, factIndex, dim) => {
      if (voteOf(group, factIndex, dim) === 'up') { clearFb(group, factIndex, dim); return; } // toggle off
      persist(group, fact, factIndex, dim, { vote: 'up' });
    };

    // 👎 : open the modal to collect the correction.
    const modal = ref({
      open: false, group: null, fact: null, factIndex: null,
      dim: 'passage', original: '', text: '', verdictChoice: '',
    });
    const openThumbDown = (group, fact, factIndex, dim) => {
      const existing = getFb(group, factIndex, dim);
      let original = '';
      if (dim === 'passage') original = fact.evalExtract || '';
      else if (dim === 'judgment') original = fact.evalComment || '';
      else if (dim === 'verdict') original = fact.status || '';
      modal.value = {
        open: true, group, fact, factIndex, dim, original,
        text: existing && existing.vote === 'down' ? (existing.corrected || '') : '',
        // for verdict: preselect the existing correction, else a status != current
        verdictChoice: dim === 'verdict'
          ? (existing && existing.vote === 'down' ? (existing.corrected || '') : '')
          : '',
      };
    };
    const closeModal = () => { modal.value = { ...modal.value, open: false }; };
    // Verdict correction can't be the same as the LLM's original verdict: if it
    // was OK, only HALLU/MISSING are offered, etc.
    const verdictOptions = computed(() => {
      const cur = (modal.value.original || '').toLowerCase();
      return ['ok', 'hallu', 'missing'].filter((o) => o !== cur);
    });
    const submitModal = async () => {
      const m = modal.value;
      if (m.dim === 'verdict') {
        if (!m.verdictChoice) return; // must pick a corrected status
        await persist(m.group, m.fact, m.factIndex, 'verdict', {
          vote: 'down', original: m.original, corrected: m.verdictChoice,
        });
        closeModal();
        return;
      }
      const corrected = (m.text || '').trim() || (m.dim === 'passage' ? 'None' : '');
      await persist(m.group, m.fact, m.factIndex, m.dim, {
        vote: 'down', original: m.original, corrected,
      });
      closeModal();
    };

    return {
      formatDate, formatCost, getFactStatusClass, highlightAnswer,
      currentPage, itemsPerPage, paginatedItems,
      onPageChange, onItemsPerPageChange,
      isAnswerCollapsed, toggleAnswer,
      // feedback
      voteOf, correctionOf, thumbUp, openThumbDown,
      modal, closeModal, submitModal, verdictOptions,
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

.answer-toggle {
  cursor: pointer;
  user-select: none;
  display: flex;
  align-items: center;
  gap: 8px;
}
.answer-toggle:hover { opacity: 0.75; }
.answer-chevron { color: #6c757d; }
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
}
.answer-text :deep(mark.hl-ok) {
  background-color: #d9f2e3;
  color: inherit;
  padding: 0 1px;
  border-radius: 2px;
  cursor: help;
}
.answer-text :deep(mark.hl-multi) {
  background-color: #e7dbff;
  color: inherit;
  padding: 0 1px;
  border-radius: 2px;
  cursor: help;
}
.answer-text :deep(mark.hl-missing) {
  background-color: #fdecc8;
  color: inherit;
  padding: 0 1px;
  border-radius: 2px;
  cursor: help;
}
.answer-text :deep(mark.hl-hallu) {
  background-color: #fbdcdc;
  color: inherit;
  padding: 0 1px;
  border-radius: 2px;
  cursor: help;
}
.answer-text :deep(ul),
.answer-text :deep(ol) {
  margin: 8px 0;
  padding-left: 22px;
}
.answer-text :deep(li) {
  margin: 3px 0;
}
.answer-text :deep(p) {
  margin: 8px 0;
}

.fact-list {
  list-style-type: none;
  padding-left: 0;
}

.fact-status {
  display: inline-block;
  width: 10px;
  height: 10px;
  min-width: 10px;
  flex: 0 0 10px;
  border-radius: 50%;
  margin-right: 10px;
  margin-top: 5px;
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

/* 3-column evaluation layout: Fact | Generated text | Comment */
.fact-eval-head {
  display: grid;
  grid-template-columns: 1.4fr 1.6fr 2fr;
  gap: 12px;
  padding: 8px 12px;
  font-size: 0.75rem;
  font-weight: 600;
  color: #6c757d;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  border-bottom: 2px solid #e0e0e0;
}
.fact-row {
  display: grid;
  grid-template-columns: 1.4fr 1.6fr 2fr;
  gap: 12px;
  align-items: start;
  padding: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  margin-bottom: 8px;
}
.fact-row .col-fact {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}
.fact-row .col-extract em {
  color: #495057;
  font-style: italic;
}
.fact-row .col-comment {
  color: #212529;
}
.fact-row .col-empty {
  color: #adb5bd;
}
.fact-row .col-span-all {
  grid-column: 1 / -1;
}
.fact-row .col-span-all:empty {
  display: none;
}
@media (max-width: 800px) {
  .fact-eval-head { display: none; }
  .fact-row {
    grid-template-columns: 1fr;
    gap: 6px;
  }
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

.question-badge {
  display: inline-block;
  margin-left: 8px;
  padding: 1px 8px;
  border-radius: 10px;
  font-size: 0.7rem;
  font-weight: 600;
  white-space: nowrap;
  vertical-align: middle;
}
.question-badge.badge-ok { background: #e6f4ea; color: #1e7e34; }
.question-badge.badge-warn { background: #fdecea; color: #b3261e; }

/* I1: feedback thumbs + correction display */
.cell-with-fb { display: flex; align-items: flex-start; gap: 8px; }
.cell-with-fb .cell-body { flex: 1; min-width: 0; }
.fb-thumbs { display: flex; flex-direction: column; gap: 2px; flex: 0 0 auto; }

.fb-dimmed { opacity: 0.5; }
.fb-correction { margin-top: 6px; }
.fb-badge {
  display: inline-block; font-size: 0.65rem; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.03em;
  background: #502bff; color: #fff; padding: 1px 6px; border-radius: 8px; margin-right: 6px;
}
.fb-corrected-text { color: #212529; }

/* I1: modal */
.fb-modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center; z-index: 3000;
}
.fb-modal {
  background: #fff; border-radius: 10px; padding: 22px; width: min(560px, 92vw);
  max-height: 85vh; overflow-y: auto; box-shadow: 0 10px 40px rgba(0,0,0,0.25);
}
.fb-modal-title { margin: 0 0 12px; font-size: 1.1rem; font-weight: 600; }
.fb-modal-fact { font-size: 0.9rem; color: #333; margin: 0 0 12px; }
.fb-modal-original { background: #f6f6f8; border-radius: 6px; padding: 10px 12px; margin-bottom: 14px; }
.fb-modal-label { font-size: 0.75rem; font-weight: 600; color: #6c757d; text-transform: uppercase; letter-spacing: 0.03em; margin-bottom: 4px; }
.fb-modal-label-row { display: flex; align-items: center; gap: 6px; }
.fb-modal-original-text { font-size: 0.9rem; color: #495057; font-style: italic; }
.fb-help { cursor: help; color: #502bff; font-style: normal; }
.fb-modal-textarea { width: 100%; box-sizing: border-box; padding: 8px 10px; border: 1px solid #ced4da; border-radius: 6px; font: inherit; resize: vertical; }
.fb-modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 16px; }
.fb-modal-btn { padding: 7px 16px; border-radius: 20px; border: 1px solid #ced4da; background: #fff; cursor: pointer; font: inherit; }
.fb-modal-btn.primary { background: #502bff; color: #fff; border-color: transparent; }
.fb-modal-btn:hover { opacity: 0.9; }
.fb-verdict-choices { display: flex; gap: 16px; margin: 4px 0 4px; }
.fb-verdict-option { display: flex; align-items: center; gap: 6px; cursor: pointer; font-size: 0.9rem; }
.fb-verdict-optlabel { font-weight: 600; }
.fb-modal-hint { font-size: 0.8rem; color: #6c757d; margin: 8px 0 0; }
.fb-verdict-corrected { font-weight: 600; text-transform: uppercase; letter-spacing: 0.02em; }
</style>
