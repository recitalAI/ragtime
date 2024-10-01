<template>
  <div class="add-answer-section mt-4">
    <v-btn
      color="secondary"
      @click="addAnswer"
      rounded
    >
      <v-icon left>fa-sharp-duotone fa-solid fa-plus</v-icon>
      Add Answer
    </v-btn>
  </div>
</template>

<script>
import { formatDate } from '@/utils/dateFormatter';

export default {
  name: 'AddAnswer',
  methods: {
    addAnswer() {
      const newAnswer = {
        text: '',
        isEditing: true,
        llm_answer: {
          name: 'Human',
          timestamp: formatDate(new Date()) 
        },
        eval: { human: 0 }
      };
      this.$emit('add', newAnswer);
    }
  }
};
</script>

<style scoped>
.v-btn {
  text-transform: none;
}
</style>