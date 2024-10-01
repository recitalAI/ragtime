<template>
  <v-container class="question-list pa-0">
    <v-row>
      <v-col
        v-for="(question, index) in questions"
        :key="index"
        cols="12"
        class="question-item-wrapper pa-2"
      >
        <QuestionItem
          :question="question"
          :index="index"
          :selectedAnswerModel="selectedAnswerModel"
          :selectedFactModel="selectedFactModel"
          @update="updateQuestion"
          @delete="deleteQuestion(index)"
        />
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import { defineComponent } from 'vue';
import QuestionItem from './QuestionItem/index.vue';

export default defineComponent({
  name: 'QuestionList',
  components: { QuestionItem },
  props: {
    questions: { type: Array, required: true },
    selectedAnswerModel: { type: String, required: true },
    selectedFactModel: { type: String, required: true }
  },
  emits: ['update'],
  setup(props, { emit }) {
    const updateQuestion = (index, updatedQuestion) => {
      const updatedQuestions = [...props.questions];
      updatedQuestions[index] = updatedQuestion;
      emit('update', updatedQuestions);
    };

    const deleteQuestion = (index) => {
      const updatedQuestions = props.questions.filter((_, i) => i !== index);
      emit('update', updatedQuestions);
    };

    return {
      updateQuestion,
      deleteQuestion
    };
  }
});
</script>

<style lang="scss" scoped>
.question-list {
  margin-bottom: 20px;
}

.question-item-wrapper {
  transition: all 0.3s ease;

}
</style>