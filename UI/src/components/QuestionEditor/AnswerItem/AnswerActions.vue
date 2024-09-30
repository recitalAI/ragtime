<template>
  <div class="d-flex justify-end mt-2">
    <v-btn
      v-if="!isEditing"
      color="primary"
      @click="$emit('edit')"
      class="mr-2"
      small
    >
      <v-icon left>fa-solid fa-pen-to-square</v-icon>
      Edit
    </v-btn>
    <v-btn
      v-if="!isEditing"
      color="error"
      @click="$emit('delete')"
      class="mr-2"
      small
    >
      <v-icon left>fas fa-trash</v-icon>
      Delete
    </v-btn>
    <!-- <v-btn
      :color="isValidated ? 'warning' : 'success'"
      @click="$emit('validate')"
      small
    >
      <v-icon left>{{ isValidated ? 'fa-solid fa-circle-xmark' : 'fa-solid fa-vial-circle-check' }}</v-icon>
      {{ isValidated ? 'Invalidate' : 'Validate' }}
    </v-btn> -->
  </div>
</template>

<script>
export default {
  name: 'AnswerActions',
  props: {
    isEditing: { type: Boolean, required: true },
    // isValidated: { type: Boolean, required: true }
  }
};
</script>

<style scoped>
.v-btn {
  text-transform: none;
}
</style>