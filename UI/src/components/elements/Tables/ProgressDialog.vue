<template>
  <v-dialog
    v-model="openDialog"
    max-width="400"
    persistent
  >
    <v-card class="dialog-card">
      <h2 class="dialog-title mb-3">
        {{ $t('datatable.deleting_file') }} {{ currentDelete }} / {{ allDelete }}
      </h2>
      <v-progress-linear
        bg-color="primary-lighten2"
        color="primary"
        :model-value="Math.floor(currentDelete / allDelete * 100)"
      />
    </v-card>
  </v-dialog>
</template>
<script>
export default {
  name: 'ProgressDialog',

  data() {
    return {
      openDialog: this.modelValue,
    };
  },

  watch: {
    openDialog(open) {
      this.$emit('update:modelValue', open);
    },

    modelValue(show) {
      this.openDialog = show;
    },
  },

  props: {
    currentDelete: {
      type: Number,
      required: true,
    },
    allDelete: {
      type: Number,
      required: true,
    },
    modelValue: {
      type: Boolean,
      required: true,
    },
  },

  emits: ['update:modelValue'],
};
</script>