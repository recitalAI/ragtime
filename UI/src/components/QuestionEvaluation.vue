<template>
  <div class="question-evaluation">
    <h2>Detailed Evaluation for Question {{ index + 1 }}</h2>
    <button @click="goBack" class="btn btn-primary">Back to Results</button>
    
    <div class="evaluation-item">
      <div class="question-section">
        <h3>Question:</h3>
        <p>{{ questionData.question }}</p>
      </div>

      <div v-if="questionData.facts && questionData.facts.length" class="facts-section">
        <h3>Facts:</h3>
        <ul class="fact-list">
          <li v-for="(fact, factIndex) in questionData.facts" :key="factIndex" class="fact-item">
            <span class="bullet">&#9679;</span> {{ fact.text }}
          </li>
        </ul>
      </div>

      <div v-if="questionData.chunks && questionData.chunks.length" class="chunks-section">
        <div class="chunk-header">
          <h3>Chunks</h3>
          <div class="chunk-buttons">
            <button 
              v-for="(chunk, chunkIndex) in questionData.chunks" 
              :key="chunkIndex" 
              @click="toggleChunkVisibility(chunkIndex)" 
              class="btn btn-info btn-sm chunk-button"
              :class="{ 'active': chunk.isVisible }"
            >
              Chunk {{ chunkIndex + 1 }}
            </button>
          </div>
        </div>
        <div v-for="(chunk, chunkIndex) in questionData.chunks" :key="chunkIndex" class="chunk-item">
          <transition name="fade">
            <div v-if="chunk.isVisible" class="chunk-content" :class="{ 'selected': chunk.isVisible }">
              <p><strong>Source:</strong> {{ chunk.meta.display_name }}</p>
              <p>{{ chunk.text }}</p>
            </div>
          </transition>
        </div>
      </div>
      
      <div v-if="questionData.answers && questionData.answers.length" class="answers-section">
        <h3>Answers:</h3>
        <div v-for="(answer, answerIndex) in questionData.answers" :key="answerIndex" class="answer-item">
          <h4>{{ answer.model }}</h4>
          <div v-if="answer.evaluation" class="evaluation-summary">
            <table class="data-table">
                <thead>
                <tr>
                    <th>Model</th>
                    <th>Date</th>
                    <th>Duration</th>
                    <th>Cost</th>
                    <th class="numeric">Score (%)</th>
                    <th class="numeric">Facts</th>
                    <th class="numeric status-column">Ok</th>
                    <th class="numeric status-column">Hallu</th>
                    <th class="numeric status-column">Missing</th>
                    <th class="numeric">Extra</th>
                </tr>
                </thead>
                <tbody>
                <tr>
                    <td>{{ answer.evaluation.model }}</td>
                    <td>{{ formatDate(answer.evaluation.time) }}</td>
                    <td>{{ answer.evaluation.duration !== undefined ? answer.evaluation.duration.toFixed(2) : 'N/A' }}s</td>
                    <td>${{ answer.evaluation.cost !== undefined ? answer.evaluation.cost.toFixed(6) : 'N/A' }}</td>
                    <td class="numeric">{{ answer.evaluation.auto !== undefined ? answer.evaluation.auto.toFixed(2) : 'N/A' }}</td>
                    <td class="numeric">{{ questionData.facts.length }}</td>
                    <td class="numeric status-column">
                    <span class="status-indicator status-ok"></span>
                    <span class="status-value">{{ answer.evaluation.ok ? answer.evaluation.ok.length : 0 }}</span>
                    </td>
                    <td class="numeric status-column">
                    <span class="status-indicator status-error"></span>
                    <span class="status-value">{{ answer.evaluation.hallu ? answer.evaluation.hallu.length : 0 }}</span>
                    </td>
                    <td class="numeric status-column">
                    <span class="status-indicator status-warning"></span>
                    <span class="status-value">{{ answer.evaluation.missing ? answer.evaluation.missing.length : 0 }}</span>
                    </td>
                    <td class="numeric">{{ answer.evaluation.extra || 0 }}</td>
                </tr>
                </tbody>
            </table>
          </div>
          <div v-html="formatAnswer(answer.text)" class="answer-text"></div>
          
          <div v-if="answer.evaluation" class="evaluation-section">
            <h4>Evaluation:</h4>
            <div v-html="formatEvaluation(answer.evaluation.text)" class="evaluation-text"></div>
          </div>
        </div>
      </div>

      <div v-if="questionData.chunkEvaluations && questionData.chunkEvaluations.length" class="chunk-evaluations-section">
        <h3>Chunk Evaluations:</h3>
        <div v-for="(chunkEval, chunkIndex) in questionData.chunkEvaluations" :key="chunkIndex">
          <h4>{{ chunkEval.type }}</h4>
          <div v-if="chunkEval.evaluation" class="evaluation-summary">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Model</th>
                  <th>Date</th>
                  <th>Duration</th>
                  <th>Cost</th>
                  <th class="numeric">Score (%)</th>
                  <th class="numeric">Facts</th>
                  <th class="numeric">Ok</th>
                  <th class="numeric">Hallu</th>
                  <th class="numeric">Missing</th>
                  <th class="numeric">Extra</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>{{ chunkEval.model }}</td>
                  <td>{{ formatDate(chunkEval.time) }}</td>
                  <td>{{ chunkEval.duration !== undefined ? chunkEval.duration.toFixed(2) : 'N/A' }}s</td>
                  <td>${{ chunkEval.cost !== undefined ? chunkEval.cost.toFixed(6) : 'N/A' }}</td>
                  <td class="numeric">{{ chunkEval.evaluation.auto !== undefined ? chunkEval.evaluation.auto.toFixed(2) : 'N/A' }}</td>
                  <td class="numeric">{{ questionData.facts.length }}</td>
                  <td class="numeric">
                    <span class="status-indicator status-ok"></span>
                    {{ chunkEval.evaluation.ok ? chunkEval.evaluation.ok.length : 0 }}
                  </td>
                  <td class="numeric">
                    <span class="status-indicator status-error"></span>
                    {{ chunkEval.evaluation.hallu ? chunkEval.evaluation.hallu.length : 0 }}
                  </td>
                  <td class="numeric">
                    <span class="status-indicator status-warning"></span>
                    {{ chunkEval.evaluation.missing ? chunkEval.evaluation.missing.length : 0 }}
                  </td>
                  <td class="numeric">{{ chunkEval.evaluation.extra || 0 }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="evaluation-summary">No evaluation data available</div>
          <div v-html="formatEvaluation(chunkEval.text)" class="evaluation-text"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { useRoute, useRouter } from 'vue-router';
import { ref, onMounted } from 'vue';
import { formatDate } from '@/utils/dateFormatter';

export default {
  name: 'QuestionEvaluation',

  setup() {
    const route = useRoute();
    const router = useRouter();
    const index = ref(parseInt(route.params.index));
    const questionData = ref(JSON.parse(route.query.data));

    const goBack = () => {
      router.go(-1);
    };

    onMounted(() => {
      if (!questionData.value) {
        goBack(); // Return to results page if no data is available
      }
    });

    const toggleAnswerDetails = (answerIndex) => {
      questionData.value.answers[answerIndex].showDetails = 
        !questionData.value.answers[answerIndex].showDetails;
    };

    const toggleEvaluationDetails = (answerIndex) => {
      questionData.value.answers[answerIndex].showEvaluationDetails = 
        !questionData.value.answers[answerIndex].showEvaluationDetails;
    };

    const toggleChunkVisibility = (chunkIndex) => {
      questionData.value.chunks[chunkIndex].isVisible = 
        !questionData.value.chunks[chunkIndex].isVisible;
    };

    const toggleChunkEvalDetails = (chunkEvalIndex) => {
      questionData.value.chunkEvaluations[chunkEvalIndex].showDetails = 
        !questionData.value.chunkEvaluations[chunkEvalIndex].showDetails;
    };

    const formatAnswer = (text) => {
      if (typeof text === 'object') {
        text = JSON.stringify(text, null, 2);
      }
      if (typeof text !== 'string') {
        text = String(text);
      }
      text = text.replace(/\[OK\]|\bOK\b/g, '<span class="eval-status ok">OK</span>');
      text = text.replace(/\[NOT FOUND\]|\bNOT FOUND\b/g, '<span class="eval-status not-found">NOT FOUND</span>');
      text = text.replace(/\[HALLU\]|\bHALLU\b/g, '<span class="eval-status hallu">HALLU</span>');
      return text;
    };

    const formatEvaluation = (text) => {
      const parser = new DOMParser();
      const doc = parser.parseFromString(text, 'text/html');

      doc.querySelectorAll('ol > li > p').forEach(p => {
        let content = p.innerHTML;
        content = content.replace(/\[OK\]/g, '<span class="eval-status ok">OK</span>');
        content = content.replace(/\[NOT FOUND\]/g, '<span class="eval-status not-found">NOT FOUND</span>');
        content = content.replace(/\[HALLU\]/g, '<span class="eval-status hallu">HALLU</span>');
        content = content.replace(/(Partie dans le paragraphe :)/g, '<span class="paragraph-part">$1</span>');
        p.innerHTML = content;
      });

      const extraP = doc.querySelector('ol + p');
      if (extraP) {
        let extraContent = extraP.innerHTML;
        extraContent = extraContent.replace(/\[EXTRA\] = (\d+)/, '<span class="extra-info">EXTRA: $1</span>');
        extraP.innerHTML = extraContent;
      }

      return doc.body.innerHTML;
    };

    const formatEvaluationSummary = (evaluation, isChunkEvaluation = false) => {
      if (!evaluation) return 'No evaluation data available';
      
      let summary = `
        <span class="eval-label">Auto:</span> <span class="eval-value">${evaluation.auto !== undefined ? evaluation.auto.toFixed(2) : 'N/A'}</span>
        <span class="eval-label">Ok:</span> <span class="eval-value">${evaluation.ok ? evaluation.ok.length : 0} ${JSON.stringify(evaluation.ok || [])}</span>
        <span class="eval-label">Missing:</span> <span class="eval-value">${evaluation.missing ? evaluation.missing.length : 0} ${JSON.stringify(evaluation.missing || [])}</span>
        <span class="eval-label">Hallus:</span> <span class="eval-value">${evaluation.hallu ? evaluation.hallu.length : 0} ${JSON.stringify(evaluation.hallu || [])}</span>
        <span class="eval-label">Nb extra:</span> <span class="eval-value">${evaluation.extra || 0}</span>
        <span class="eval-label">Human:</span> <span class="eval-value">${evaluation.human || 'N/A'}</span>
      `;

      if (!isChunkEvaluation) {
        summary += `<span class="eval-label">Eval made with:</span> <span class="eval-value">"${evaluation.model || 'Unknown'}"</span>`;
      }

      return summary;
    };

    return {
      index,
      questionData,
      goBack,
      toggleAnswerDetails,
      toggleEvaluationDetails,
      toggleChunkVisibility,
      formatEvaluation,
      formatAnswer,
      formatEvaluationSummary,
      toggleChunkEvalDetails,
      formatDate
    };
  }
};
</script>

<style scoped>
.question-evaluation {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Roboto', sans-serif;
}

h1, h3, h4, h5, h6 {
  color: #333;
  margin-bottom: 15px;
}

h2 { font-size: 2em; }
h3 { font-size: 1.75em; }
h4 { font-size: 1.5em; }
h5 { 
  font-size: 1.25em; 
  color: #007bff;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 16px;
  transition: all 0.3s ease;
  text-transform: uppercase;
  letter-spacing: 1px;
  font-weight: bold;
  box-shadow: 0 2px 5px rgba(0,0,0,0.2);
}

.btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}

.btn-primary {
  background: linear-gradient(45deg, #007bff, #0056b3);
  color: white;
  margin-bottom: 20px;
}

.btn-info {
  background: linear-gradient(45deg, #17a2b8, #138496);
  color: white;
}

.evaluation-item {
  background-color: #f9f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.question-section, .facts-section, .chunks-section, .answers-section, .chunk-evaluations-section {
  margin-bottom: 30px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 5px;
}

.facts-section, .chunks-section, .answers-section, .chunk-evaluations-section {
  margin-top: 20px;
  border-top: 1px solid #e0e0e0;
  padding-top: 20px;
}

.fact-list {
  list-style-type: none;
  padding-left: 0;
}

.fact-item {
  margin-bottom: 10px;
  padding: 10px;
  background-color: #f8f9fa;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
}

.bullet {
  font-size: 1.2em;
  color: #007bff;
  margin-right: 10px;
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

.chunk-content.selected {
  background-color: #e6f3ff;
  border: 1px solid #007bff;
}

.answer-item {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 20px;
  background-color: #f9f9fa;
}

.answer-details {
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

.data-table {
  table-layout: fixed;
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  margin: 20px 0;
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
  padding: 12px 8px;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.data-table th {
  font-weight: 600;
  color: #333;
  text-transform: uppercase;
  font-size: 0.85em;
  letter-spacing: 0.5px;
}

.data-table td {
  font-size: 0.95em;
  color: #333;
}

.data-table .numeric {
  text-align: right;
}

.status-column {
  min-width: 80px;
  width: 80px;
}

.status-indicator {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 5px;
  vertical-align: middle;
}

.status-value {
  vertical-align: middle;
}

.status-ok { background-color: #28a745; }
.status-warning { background-color: #ffc107; }
.status-error { background-color: #dc3545; }

.evaluation-summary {
  background-color: #e9ecef;
  padding: 15px;
  border-radius: 6px;
  margin-bottom: 20px;
  font-size: 0.9em;
  line-height: 1.8;
}

.evaluation-details {
  margin-top: 10px;
  padding: 10px;
  background-color: #f1f3f5;
  border-radius: 4px;
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

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s;
}

.fade-enter,
.fade-leave-to {
  opacity: 0;
}

/* Responsive adjustments */
@media screen and (max-width: 1200px) {
  .data-table {
    font-size: 0.9em;
  }
  
  .status-column {
    min-width: 70px;
    width: 70px;
  }
}

@media screen and (max-width: 992px) {
  .data-table {
    font-size: 0.8em;
  }
  
  .status-column {
    min-width: 60px;
    width: 60px;
  }
}
</style>