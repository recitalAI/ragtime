<template>
  <v-dialog
    v-model="openDialog"
    max-width="440"
    @click:outside="close"
    @keydown.esc="close"
  >
    <v-card class="dialog-card">
      <div class="d-flex align-center mb-4">
        <v-icon color="error" size="28" class="mr-3">mdi-wifi-off</v-icon>
        <h2 class="dialog-title ma-0">
          {{ $t('offline.title') }}
        </h2>
      </div>
      <p class="mb-2">
        {{ $t('offline.message') }}
      </p>
      <div class="mt-8 d-flex justify-end">
        <div class="dialog-button">
          <v-btn
            color="primary"
            @click="close"
            block
            rounded
          >
            {{ $t('offline.ok') }}
          </v-btn>
        </div>
      </div>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: 'OfflineDialog',

  props: {
    modelValue: {
      type: Boolean,
      required: true,
    },
  },

  emits: ['update:modelValue'],

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

  methods: {
    close() {
      this.openDialog = false;
    },
  },
};
</script>

<style lang="scss" scoped>
.dialog-button {
  min-width: 120px;
}
</style>
