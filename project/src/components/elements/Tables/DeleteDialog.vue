<template>
  <v-dialog
    v-model="openDialog"
    max-width="400"
    @click:outside="$emit('close')"
    @keydown.esc="$emit('close')"
  >
    <v-card class="dialog-card">
      <h2 class="dialog-title mb-8">
        {{ title }}
      </h2>
      {{ message }}
      <div class="mt-8 d-flex">
        <div class="dialog-button mr-2">
          <v-btn
            style="box-shadow: none"
            variant="outlined"
            @click="$emit('close')"
            block
            rounded
          >
            {{ $t('cancel') }}
          </v-btn>
        </div>
        <div class="dialog-button ml-2">
          <v-btn
            color="primary"
            @click="$emit('confirm')"
            block
            rounded
          >
            {{ $t('confirm') }}
          </v-btn>
        </div>
      </div>
    </v-card>
  </v-dialog>
</template>
<script>
export default {
  name: 'DeleteDialog',

  data() {
    return ({
      openDialog: this.modelValue,
    });
  },

  watch: {
    openDialog(open) {
      this.$emit('update:modelValue', open);
    },

    modelValue(show) {
      this.openDialog = show;
    },
  },

  mounted() {
    this.handleKeydown();
  },

  methods: {
    handleKeydown() {
      document.addEventListener("keydown", event => {
        if (this.openDialog === false) {
          return;
        }
        switch (event.key) {
          case "Enter":
            this.$emit('confirm');
            break;
        }
      });
    }
  },

  props: {
    title: {
      required: true,
      type: String,
    },

    message: {
      required: true,
      type: String
    },

    modelValue: {
      type: Boolean,
      required: true,
    },
  },

  emits: ['close', 'confirm', 'update:modelValue'],
}
</script>

<style lang="scss" scoped>
.dialog-button {
  width: 100%;
}
</style>
