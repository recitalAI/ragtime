<template>
  <v-card class="add-question-section pa-4 mt-6" color="grey-lighten-4">
    <v-card-title class="text-h6 mb-4">Add New Question</v-card-title>
    <v-textarea
      v-model="newQuestionText"
      label="Enter your new question here"
      rows="4"
      auto-grow
      variant="outlined"
      class="mb-4"
    ></v-textarea>
    <v-btn
      color="primary"
      @click="addQuestion"
      :disabled="!newQuestionText.trim()"
    >
      Add Question
    </v-btn>
  </v-card>
</template>

<script>
import { defineComponent, ref } from 'vue';

export default defineComponent({
  name: 'AddQuestion',
  emits: ['add'],
  setup(_, { emit }) {
    const newQuestionText = ref('');

    const addQuestion = () => {
      if (newQuestionText.value.trim()) {
        emit('add', newQuestionText.value);
        newQuestionText.value = '';
      }
    };

    return {
      newQuestionText,
      addQuestion
    };
  }
});
</script>

<style lang="scss" scoped>
.add-question-section {
  background-color: var(--v-grey-lighten4);
  border-radius: 8px;
}

.v-btn {
  text-transform: none;
}
</style>