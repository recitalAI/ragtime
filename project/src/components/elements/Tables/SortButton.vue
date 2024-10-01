<template>
  <div
    class="sort-button clickable"
    @click="$emit('update:modelValue', !modelValue)"
  >
    <v-icon
      color="primary"
      style="display: block;"
      :style="{ opacity: modelValue ? 0.3 : 1 }"
    >
      fa fa-sort-up
    </v-icon>
    <v-icon
      color="primary"
      style="display: block; margin-top: -15px;"
      :style="{ opacity: modelValue ? 1 : 0.3 }"
    >
      fa fa-sort-down
    </v-icon>
  </div>
</template>

<script>
export default {
 name: 'SortButton',

 props: {
    modelValue: {
      type: Boolean,
      required: true,
    }
  },

  emits: ['update:modelValue'],
}
</script>
