<template>
  <v-container class="question-editor pa-0">
    <QuestionList 
      :questions="localQuestions" 
      :selectedAnswerModel="selectedAnswerModel"
      :selectedFactModel="selectedFactModel"
      @update="handleUpdate"
    />
  </v-container>
</template>

<script>
import { defineComponent, ref, watch, computed } from 'vue';
import QuestionList from './QuestionList.vue';

export default defineComponent({
  name: 'QuestionEditor',
  components: { QuestionList },
  props: {
    qa: { type: Array, required: true },
    selectedAnswerModel: { type: String, required: true },
    selectedFactModel: { type: String, required: true }
  },
  emits: ['update:qa'],
  setup(props, { emit }) {
    const initializeQuestions = computed(() => 
      props.qa.map(q => ({
        ...q,
        answers: {
          items: q.answers.items.map(a => ({ ...a, isEditing: false, eval: a.eval || { human: 0 } }))
        }
      }))
    );

    const localQuestions = ref(initializeQuestions.value);

    const handleUpdate = (updatedQuestions) => {
      localQuestions.value = updatedQuestions;
      emit('update:qa', localQuestions.value);
    };

    watch(() => props.qa, () => {
      localQuestions.value = initializeQuestions.value;
    }, { deep: true });

    return {
      localQuestions,
      handleUpdate
    };
  }
});
</script>

<style lang="scss" scoped>
.question-editor {
  max-width: 1200px;
  margin: 0 auto;
}
</style>