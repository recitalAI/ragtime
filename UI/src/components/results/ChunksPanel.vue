<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="onUpdate"
  >
    <v-card style="width: 600px">
      <v-card-title class="h2-text primary--text mb-6">
        {{ model }}
      </v-card-title>
      <v-card-text>
        <v-row
          class="table-row mb-2"
          style="border-bottom: none;"
        >
          <v-col cols="4">
          </v-col>
          <v-col
            class="justify-end"
            cols="4"
          >
            <h5 class="h5-text">
              Errors due to LLM
            </h5>
          </v-col>
          <v-col
            class="justify-end"
            cols="4"
          >
            <h5 class="h5-text">
              Errors due to retriever
            </h5>
          </v-col>
        </v-row>
        <v-row
          class="table-row mb-2"
          style="border-bottom: none;"
        >
          <v-col
            class="h5-text"
            cols="4"
          >
            <h5>
              Hallucinations
            </h5>
          </v-col>
          <v-col
            class="justify-end"
            cols="4"
          >
            {{ summary.llm.hallucinations }} ({{ summary.llm.hallucinationsPr.toFixed(1) }}%)
          </v-col>
          <v-col
            class="justify-end"
            cols="4"
          >
            {{ summary.chunks.hallucinations }} ({{ summary.chunks.hallucinationsPr.toFixed(1) }}%)
          </v-col>
        </v-row>
        <v-row
          class="table-row mb-2"
          style="border-bottom: none;"
        >
          <v-col
            class="h5-text"
            cols="4"
          >
            <h5>
              Missing
            </h5>
          </v-col>
          <v-col
            class="justify-end"
            cols="4"
          >
            {{ summary.llm.missings }} ({{ summary.llm.missingsPr.toFixed(1) }}%)
          </v-col>
          <v-col
            class="justify-end"
            cols="4"
          >
            {{ summary.chunks.missings }} ({{ summary.chunks.missingsPr.toFixed(1) }}%)
          </v-col>
        </v-row>
        <v-row
          class="table-row mb-2"
          style="border-bottom: none;"
        >
          <v-col
            class="h5-text"
            cols="4"
          >
            <h5>
              Combined
            </h5>
          </v-col>
          <v-col
            class="justify-end"
            cols="4"
          >
            {{ summary.llm.combined }} ({{ summary.llm.combinedPr.toFixed(1) }}%)
          </v-col>
          <v-col
            class="justify-end"
            cols="4"
          >
            {{ summary.chunks.combined }} ({{ summary.chunks.combinedPr.toFixed(1) }}%)
          </v-col>
        </v-row>
        <v-row
          class="table-row mb-2"
          style="border-bottom: none;"
        >
          <v-col
            class="h5-text"
            cols="4"
          >
            <h5>
              Whole Test
            </h5>
          </v-col>
          <v-col
            class="justify-end"
            cols="4"
          >
            {{ summary.llm.wholeTest }} ({{ summary.llm.wholeTestPr.toFixed(1) }}%)
          </v-col>
          <v-col
            class="justify-end"
            cols="4"
          >
            {{ summary.chunks.wholeTest }} ({{ summary.chunks.wholeTestPr.toFixed(1) }}%)
          </v-col>
        </v-row>
      </v-card-text>
      <v-card-actions>
        <v-btn
          color="primary"
          variant="flat"
          @click="$emit('close')"
          rounded
        >
          Close
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: 'ChunksPanel',
  props: {
    modelValue: {
      type: Boolean,
      required: true,
    },
    model: {
      type: String,
      default: '',
    },
    summary: {
      type: Object,
      required: true,
    },
  },
  emits: ['update:modelValue', 'close'],
  setup(props, { emit }) {
    // Mirrors the original v-model + @update:model-value pairing: closing the
    // dialog (backdrop/escape) both updates the flag and runs the close
    // handler that clears the selected model after the fade-out.
    const onUpdate = (value) => {
      emit('update:modelValue', value);
      if (!value) {
        emit('close');
      }
    };
    return { onUpdate };
  },
};
</script>
