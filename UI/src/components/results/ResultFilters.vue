<template>
  <div class="filter-container">
    <span class="h4-text">
      Filter:
    </span>
    <div class="filter-checkboxes">
      <v-checkbox
        v-model="ok"
        label="Ok"
        hide-details
      />
      <v-checkbox
        v-model="hallu"
        class="ml-3 mt-0"
        label="Hallu"
        hide-details
      />
      <v-checkbox
        v-model="missing"
        class="ml-3 mt-0"
        label="Missing"
        hide-details
      />
      <v-checkbox
        v-model="extra"
        class="ml-3 mt-0"
        label="Extra"
        hide-details
      />
    </div>
  </div>
</template>

<script>
import { computed } from 'vue';

export default {
  name: 'ResultFilters',
  props: {
    filters: {
      type: Object,
      required: true,
    },
  },
  emits: ['update:filters'],
  setup(props, { emit }) {
    // props-in / events-out: each checkbox proxies one flag and emits the
    // merged object so the parent's `filters` stays the single source.
    const flag = (key) => computed({
      get: () => props.filters[key],
      set: (value) => emit('update:filters', { ...props.filters, [key]: value }),
    });

    return {
      ok: flag('ok'),
      hallu: flag('hallu'),
      missing: flag('missing'),
      extra: flag('extra'),
    };
  },
};
</script>

<style scoped>
/* Moved verbatim from ExperimentResults.vue */
.filter-container {
  display: flex;
  align-items: center;
}

.filter-checkboxes {
  display: flex;
  align-items: center;
  cursor: pointer;
  margin: 0 10px;
}

.filter-checkboxes input[type="checkbox"] {
  margin-right: 5px;
}

/* Styles pour rendre les cases à cocher plus jolies */
.filter-checkboxes input[type="checkbox"] {
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border: 2px solid #007bff;
  border-radius: 3px;
  outline: none;
  transition: all 0.3s;
  position: relative;
  cursor: pointer;
}

.filter-checkboxes input[type="checkbox"]:checked {
  background-color: #007bff;
}

.filter-checkboxes input[type="checkbox"]:checked::before {
  content: '\2713';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  font-size: 14px;
}

.filter-checkboxes label:hover input[type="checkbox"] {
  border-color: #0056b3;
}
</style>
