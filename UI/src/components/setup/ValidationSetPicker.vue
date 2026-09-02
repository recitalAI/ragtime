<template>
  <v-col cols="12" sm="6">
    <v-select
      v-if="!lockedValidationSet"
      :model-value="selectedValidationSet"
      :items="validationSets"
      item-title="name"
      item-value="name"
      label="Validation Set"
      variant="outlined"
      color="primary"
      density="comfortable"
      hide-details="auto"
      class="basics-select"
      style="min-width: 200px"
      required
      @update:model-value="onChange"
    />
    <v-text-field
      v-else
      :model-value="lockedValidationSet"
      label="Validation Set"
      variant="outlined"
      color="primary"
      density="comfortable"
      disabled
    />
  </v-col>
</template>

<script>
export default {
  name: 'ValidationSetPicker',
  props: {
    validationSets: {
      type: Array,
      required: true,
    },
    selectedValidationSet: {
      type: String,
      default: '',
    },
    // Set when arriving from Create/Modify — shown read-only.
    lockedValidationSet: {
      type: String,
      default: '',
    },
  },
  emits: ['update:selectedValidationSet', 'change'],
  setup(props, { emit }) {
    // Mirrors the original v-model + @update pairing on the select.
    const onChange = (value) => {
      emit('update:selectedValidationSet', value);
      emit('change');
    };
    return { onChange };
  },
};
</script>

<style scoped>
/* The global `.v-select { height: 40px }` (_form.scss) clips a
   comfortable-density select and top-aligns its text. Keep natural height so
   the selected text stays vertically centered, matching the Evaluation Model
   select on the setup page. */
.basics-select.v-select {
  height: auto;
}
</style>
