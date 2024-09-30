<template>
  <v-card class="answer-list pa-4">
    <h4 class="text-h6 mb-4">Reference answers</h4>
    <v-alert
      v-if="answers.length === 0 && !isAddingNew"
      border="top"
      color=#502BFF
      type="info"
      text="No answers saved for this question."
      class="mb-4"
      variant="outlined"
    ></v-alert>
    <AnswerItem
      v-for="(answer, index) in answers"
      :key="index"
      :answer="answer"
      :index="index"
      @update="updateAnswer"
      @delete="deleteAnswer"
    />
    <v-expand-transition>
      <div v-if="isAddingNew" class="new-answer mt-4">
        <v-textarea
          v-model="newAnswerText"
          label="Type your answer here..."
          rows="4"
          auto-grow
          outlined
        ></v-textarea>
        <v-card-actions class="justify-end mt-2">
          <v-btn color="primary" @click="saveNewAnswer" class="mr-2">
            <v-icon left>fa-solid fa-floppy-disk</v-icon>
            Save
          </v-btn>
          <v-btn color="grey" @click="cancelNewAnswer">
            <v-icon left>fa-sharp-duotone fa-solid fa-xmark</v-icon>
            Cancel
          </v-btn>
        </v-card-actions>
      </div>
    </v-expand-transition>
    <v-btn
      v-if="!isAddingNew"
      color="primary-darken3"
      @click="startAddingNewAnswer"
      class="mt-4"
      rounded
    >
      <v-icon left>fa-sharp-duotone fa-solid fa-plus</v-icon>
      Add Answer
    </v-btn>
  </v-card>
</template>

<script>
import AnswerItem from '../AnswerItem/index.vue';
import { formatDateForBackend } from '@/utils/dateFormatter';

export default {
  name: 'AnswerList',
  components: { AnswerItem },
  props: {
    answers: { type: Array, required: true }
  },
  data() {
    return {
      isAddingNew: false,
      newAnswerText: ''
    };
  },
  methods: {
    updateAnswer(index, updatedAnswer) {
      const updatedAnswers = [...this.answers];
      updatedAnswers[index] = updatedAnswer;
      this.$emit('update', updatedAnswers);
    },
    deleteAnswer(index) {
      const updatedAnswers = this.answers.filter((_, i) => i !== index);
      this.$emit('update', updatedAnswers);
    },
    startAddingNewAnswer() {
      this.isAddingNew = true;
      this.newAnswerText = '';
    },
    saveNewAnswer() {
      if (this.newAnswerText.trim()) {
        const newAnswer = {
          text: this.newAnswerText.trim(),
          isEditing: false,
          llm_answer: {
            name: 'Human',
            timestamp: formatDateForBackend(new Date()) 
          },
          eval: { human: 0 }
        };
        this.$emit('update', [...this.answers, newAnswer]);
        this.isAddingNew = false;
        this.newAnswerText = '';
      }
    },
    cancelNewAnswer() {
      this.isAddingNew = false;
      this.newAnswerText = '';
    }
  }
};
</script>

<style scoped>
.answer-list {
  margin-top: 20px;
}
</style>