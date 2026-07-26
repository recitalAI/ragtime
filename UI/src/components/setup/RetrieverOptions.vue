<template>
  <!-- Fragment root: the switch and select were direct siblings in the
       original template — no wrapper element, same DOM. -->
  <!-- Behavior fix (5.4): when a selected custom model brings its own
       retriever, the toggle is hidden entirely (spec case: "retriever
       toggle hidden") — useRetriever is still forced ON internally, and
       the "Built-in retriever" caption on the model explains why. -->
  <v-switch
    v-if="!disabled"
    :model-value="useRetriever"
    label="Use Retriever"
    @update:model-value="$emit('update:useRetriever', $event)"
  />

  <v-select
      v-if="useRetriever && !disabled && retrievers.length > 0"
      :model-value="selectedRetriever"
      :items="retrievers"
      label="Retriever configuration"
      variant="outlined"
      color="primary"
      style="min-width: 200px; height: 80px"
      density="comfortable"
      @update:model-value="$emit('update:selectedRetriever', $event)"
  />
</template>

<script>
export default {
  name: 'RetrieverOptions',
  props: {
    useRetriever: {
      type: Boolean,
      required: true,
    },
    // True when a selected custom model has a built-in retriever.
    disabled: {
      type: Boolean,
      default: false,
    },
    retrievers: {
      type: Array,
      required: true,
    },
    selectedRetriever: {
      type: String,
      default: '',
    },
  },
  emits: ['update:useRetriever', 'update:selectedRetriever'],
};
</script>
