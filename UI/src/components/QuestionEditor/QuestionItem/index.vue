<template>
  <div class="question-item">
    <div v-if="isEditing" class="question-edit">
      <div class="question-form mb-6">
      <v-textarea
        v-model="editedQuestionText"
        label="Edit your question"
        variant="outlined"
        rows="3"
      />
        <v-btn
          color="primary"
          @click="saveQuestion"
          class="mr-2"
          rounded
        >
        <v-icon
          size="17"
          start
        >
          fa-solid fa-floppy-disk
        </v-icon>
          Save
        </v-btn>
        <v-btn
          color="grey"
          @click="cancelEdit"
          rounded
        >
        <v-icon
          size="17"
          start
        >
          fa-sharp-duotone fa-solid fa-xmark
        </v-icon>
          Cancel
        </v-btn>
      </div>
    </div>
    <div v-else class="question-display">
      <QuestionText :text="question.question.text" :index="index" />
      <div class="action-buttons">
        <div class="button-row">
          <v-btn
            v-for="button in topRowButtons"
            :key="button.text"
            :color="button.color"
            variant="outlined"
            @click="button.action"
            :disabled="button.disabled"
            class="custom-btn"
            rounded
          >
            <v-icon
              :icon="button.icon"
              size="18"
              start
            />
            {{ button.text }}
          </v-btn>
        </div>
        <div class="button-row mt-2">
          <v-btn
            v-for="button in bottomRowButtons"
            :key="button.text"
            :color="button.color"
            variant="outlined"
            @click="button.action"
            :disabled="button.disabled"
            class="custom-btn"
            rounded
          >
            <v-icon
              :icon="button.icon"
              size="18"
              start
            />
            {{ button.text }}
          </v-btn>
        </div>
      </div>
    </div>
    <AnswerList
      v-if="showAnswers"
      :answers="question.answers.items"
      @update="updateAnswers"
      @add="addAnswer"
    />
      <v-expand-transition>
      <div v-if="showFacts" class="facts-list">
        <h4 class="text-h6 mb-4">Facts</h4>
        <v-list v-if="question.facts && question.facts.items && question.facts.items.length > 0">
          <v-list-item v-for="(fact, factIndex) in question.facts.items" :key="factIndex" class="mb-3 fact-item">
            <template v-slot:default>
              <v-list-item-title class="fact-text">{{ `${factIndex + 1}. ${fact.text}` }}</v-list-item-title>
              <v-list-item-action>
                <v-btn color="primary" variant="text" @click="startEditingFact(factIndex)" class="mr-2">
                  <v-icon start>fa-solid fa-pen-to-square</v-icon>
                  Edit
                </v-btn>
                <v-btn color="error" variant="text" @click="deleteFact(factIndex)">
                  <v-icon start>fas fa-trash</v-icon>
                  Delete
                </v-btn>
              </v-list-item-action>
            </template>
          </v-list-item>
        </v-list>
        
        <v-dialog v-model="isEditingFact" min-width="800px">
          <v-card>
            <v-card-title class="text-h5 text-primary pb-2">
              Edit Fact
            </v-card-title>
            <v-card-text>
              <v-textarea
                v-model="editedFactText"
                label="Edit fact"
                rows="5"
                auto-grow
                variant="outlined"
              ></v-textarea>
            </v-card-text>
            <v-card-actions>
              <v-spacer></v-spacer>
              <v-btn 
              color="primary" 
              @click="saveFact"
              class="mr-2"
              rounded
              >        
              <v-icon
                size="17"
                start
              >
                fa-solid fa-floppy-disk
              </v-icon>
                Save
              </v-btn>
              <v-btn
                color="grey"
                @click="cancelEditFact"
                rounded
              >
              <v-icon
                size="17"
                start
              >
                fa-sharp-duotone fa-solid fa-xmark
              </v-icon>
                Cancel
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
        
        <div v-if="isAddingFact" class="mt-4">
          <v-textarea
            v-model="newFactText"
            label="Enter new fact"
            rows="3"
            auto-grow
            variant="outlined"
          ></v-textarea>
          <div class="d-flex justify-end mt-2">
          <v-btn 
            color="primary" 
            @click="saveNewFact"
            class="mr-2"
            rounded
            >        
            <v-icon
              size="17"
              start
            >
              fa-solid fa-floppy-disk
            </v-icon>
              Save
            </v-btn>
            <v-btn
              color="grey"
              @click="cancelAddFact"
              rounded
            >
            <v-icon
              size="17"
              start
            >
              fa-sharp-duotone fa-solid fa-xmark
            </v-icon>
              Cancel
            </v-btn>
          </div>
        </div>
        
        <div class="d-flex justify-space-between mt-4">
          <v-btn color="primary-lighten1" @click="startAddingFact" rounded>
            <v-icon start>fa-sharp-duotone fa-solid fa-plus</v-icon>
            Add Fact
          </v-btn>
          <v-btn
            v-if="!question.facts || !question.facts.items || question.facts.items.length === 0"
            color="primary-lighten2"
            @click="generateFacts"
            :disabled="isGeneratingFacts || !selectedFactModel"
            rounded
          >
          <v-icon
            size="17"
            start
          >
          {{isGeneratingFacts ? 'fa-solid fa-spinner fa-spin' : 'fa-solid fa-lightbulb'}}
          </v-icon>
            {{ isGeneratingFacts ? 'Generating Facts...' : 'Generate Facts' }}
          </v-btn>
        </div>
        
        <v-card v-if="question.facts && question.facts.llm_answer" flat class="mt-4 pa-2 bg-grey-lighten-4">
          <v-card-text class="text-caption">
            <p>Generated by: {{ question.facts.llm_answer.name }} ({{ formatDate(question.facts.llm_answer.timestamp) }})</p>
            <p v-if="question.facts.llm_answer.cost !== undefined" class="font-weight-medium">
              Cost: ${{ question.facts.llm_answer.cost.toFixed(6) }}
            </p>
            <p v-if="question.facts.llm_answer.duration !== undefined" class="font-weight-medium">
              Duration: {{ question.facts.llm_answer.duration.toFixed(2) }}s
            </p>
          </v-card-text>
        </v-card>
      </div>
    </v-expand-transition>
  </div>
</template>

<script>
import QuestionText from './QuestionText.vue';
import AnswerList from './AnswerList.vue';
import { answerGeneratorService, factGeneratorService } from '@/services/generatorService';
import { formatDate } from '@/utils/dateFormatter';

export default {
  name: 'QuestionItem',
  components: { QuestionText, AnswerList },
  props: {
    question: { type: Object, required: true },
    index: { type: Number, required: true },
    selectedAnswerModel: { type: String, required: true },
    selectedFactModel: { type: String, required: true }
  },
  data() {
    return {
      isEditing: false,
      isEditingFact: false,
      editedQuestionText: this.question.question.text,
      isGenerating: false,
      isGeneratingFacts: false,
      showAnswers: false,
      showFacts: false,
      editingFactIndex: null,
      editedFactText: '',
      isAddingFact: false,
      newFactText: ''
    };
  },
  computed: {
    topRowButtons() {
      return [
        {
          color: 'primary',
          action: this.startEditing,
          icon: 'fa-solid fa-edit',
          text: 'Edit Question'
        },
        {
          color: 'error',
          action: () => this.$emit('delete'),
          icon: 'fa-solid fa-trash',
          text: 'Delete Question'
        },
        {
          color: 'primary-darken1',
          action: this.generateAnswer,
          disabled: this.isGenerating || !this.selectedAnswerModel,
          icon: this.isGenerating ? 'fa-solid fa-spinner fa-spin' : 'fa-solid fa-robot',
          text: this.isGenerating ? 'Generating...' : 'Generate Answer'
        },
      ];
    },
    bottomRowButtons() {
      return [
        {
          color: 'primary-lighten1',
          action: this.toggleAnswersVisibility,
          icon: this.showAnswers ? 'fa-solid fa-eye-slash' : 'fa-solid fa-eye',
          text: this.showAnswers ? 'Hide Answers' : 'Show Answers'
        },
        {
          color: 'primary-lighten1',
          action: this.toggleFactsVisibility,
          icon: this.showFacts ? 'fa-solid fa-eye-slash' : 'fa-solid fa-eye',
          text: this.showFacts ? 'Hide Facts' : 'Show Facts'
        }
      ];
    }
  },
  methods: {
    formatDate,
    startEditing() {
      this.isEditing = true;
      this.editedQuestionText = this.question.question.text;
    },
    saveQuestion() {
      if (this.editedQuestionText.trim()) {
        const updatedQuestion = {
          ...this.question,
          question: { text: this.editedQuestionText.trim() }
        };
        this.$emit('update', this.index, updatedQuestion);
        this.isEditing = false;
      }
    },
    cancelEdit() {
      this.isEditing = false;
      this.editedQuestionText = this.question.question.text;
    },
    async generateAnswer() {
      this.isGenerating = true;
      try {
        const questionData = {
          question: {
            text: this.question.question.text
          }
        };
        const result = await answerGeneratorService.generateAnswerForQuestion(questionData, this.selectedAnswerModel);
        if (result && result.answers && result.answers.items) {
          const newAnswers = result.answers.items;
          this.updateAnswers([...this.question.answers.items, ...newAnswers]);
        }
      } catch (error) {
        console.error('Error generating answer:', error);
        alert('Error generating answer. Please try again.');
      } finally {
        this.isGenerating = false;
      }
    },
    updateAnswers(updatedAnswers) {
      const updatedQuestion = {
        ...this.question,
        answers: { items: updatedAnswers }
      };
      this.$emit('update', this.index, updatedQuestion);
    },
    addAnswer(newAnswer) {
      this.updateAnswers([...this.question.answers.items, newAnswer]);
    },
    toggleAnswersVisibility() {
      this.showAnswers = !this.showAnswers;
    },
    toggleFactsVisibility() {
      this.showFacts = !this.showFacts;
    },
    startEditingFact(index) {
      this.editingFactIndex = index;
      this.editedFactText = this.question.facts.items[index].text;
      this.isEditingFact = true;
    },

    saveFact() {
      if (this.editedFactText.trim()) {
        const updatedFacts = [...this.question.facts.items];
        updatedFacts[this.editingFactIndex] = {
          ...updatedFacts[this.editingFactIndex],
          text: this.editedFactText.trim()
        };
        this.updateFacts(updatedFacts);
        this.isEditingFact = false;
        this.editingFactIndex = null;
        this.editedFactText = '';
      }
    },

    cancelEditFact() {
      this.isEditingFact = false;
      this.editingFactIndex = null;
      this.editedFactText = '';
    },
    deleteFact(index) {
      const updatedFacts = this.question.facts.items.filter((_, i) => i !== index);
      this.updateFacts(this.renumberFacts(updatedFacts));
    },
    startAddingFact() {
      this.isAddingFact = true;
      this.newFactText = '';
    },
    saveNewFact() {
      if (this.newFactText.trim()) {
        const newFact = {
          meta: {},
          text: this.newFactText.trim()
        };
        const updatedFacts = [...(this.question.facts?.items || []), newFact];
        this.updateFacts(this.renumberFacts(updatedFacts));
        this.isAddingFact = false;
        this.newFactText = '';
      }
    },
    cancelAddFact() {
      this.isAddingFact = false;
      this.newFactText = '';
    },
    renumberFacts(facts) {
      return facts.map((fact, index) => {
        const numberMatch = fact.text.match(/^\d+\.\s/);
        if (numberMatch) {
          return {
            ...fact,
            text: fact.text.replace(/^\d+\.\s/, `${index + 1}. `)
          };
        } else {
          return {
            ...fact,
            text: `${index + 1}. ${fact.text}`
          };
        }
      });
    },
    updateFacts(updatedFacts) {
      const updatedQuestion = {
        ...this.question,
        facts: { items: updatedFacts }
      };
      this.$emit('update', this.index, updatedQuestion);
    },
    async generateFacts() {
      if (!this.selectedFactModel) {
        alert("Please select a fact generation model first.");
        return;
      }
      
      // Check if this question has exactly one validated answer
      const validatedAnswers = this.question.answers.items.filter(answer => answer.eval.human === 1);
      
      if (validatedAnswers.length !== 1) {
        alert("Please ensure that this question has exactly one answer before generating facts.");
        return;
      }


      this.isGeneratingFacts = true;
      try {
        const questionData = {
          question: {
            text: this.question.question.text
          },
          answers: {
            items: [validatedAnswers[0]]
          }
        };

        const result = await factGeneratorService.generateFactsForQuestion(questionData, this.selectedFactModel);
        if (result && result.facts) {
          this.$emit('update', this.index, {
            ...this.question,
            facts: result.facts
          });
          this.$emit('save-to-local-storage');
          alert('Facts generated successfully!');
        } else {
          alert('No facts were generated. Please try again.');
        }
      } catch (error) {
        console.error('Error generating facts:', error);
        alert('Error generating facts. Please check the console for details.');
      } finally {
        this.isGeneratingFacts = false;
      }
    },
  }
};
</script>

<style scoped>


.action-buttons {
  display: flex;
  flex-direction: column;
  margin-top: 12px;
  width: 100%;
}

.button-row {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
}

.custom-btn {
  flex: 1;
  text-transform: none;
  font-weight: normal;
  padding: 0 8px;
}

.custom-btn :deep(.v-btn__content) {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  font-size: 0.85rem;
}

.custom-btn :deep(.v-icon) {
  margin-right: 4px;
  flex-shrink: 0;
}

.custom-btn :deep(.v-btn__content > span) {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

@media (max-width: 600px) {
  .custom-btn :deep(.v-btn__content) {
    font-size: 0.75rem;
  }
}

.facts-list {
  margin-top: 16px;
}

.fact-item {
  background-color: #f5f5f5;
  border-radius: 8px;
  transition: background-color 0.3s;
}

.fact-text {
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 1rem;
  line-height: 1.5;
  color: rgba(0, 0, 0, 0.87);
}

.v-list-item-action {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

.v-btn {
  text-transform: none;
}

</style>