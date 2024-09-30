<template>
  <div class="question-text">
    <h3>Question {{ index + 1 }}</h3>
    <p>{{ text }}</p>
  </div>
</template>

<script>
export default {
  name: 'QuestionText',
  props: {
    text: { type: String, required: true },
    index: { type: Number, required: true }
  }
};
</script>

<style scoped>
.question-text h3 {
  margin-top: 0;
  color: #333;
}
</style>