<template>
  <!-- Percentage variant: dot + percentage + absolute count -->
  <div
    v-if="total !== null && total !== undefined"
    class="percentage"
  ><span :class="['status-indicator', statusClass]"></span>{{ calculatePercentage(value, total) }}%  <div class="absolute-count">({{ value }}/{{ total }})</div></div>
  <!-- Count variant with .numeric wrapper (summary "Extra" column) -->
  <div
    v-else-if="numeric"
    class="numeric"
  ><span :class="['status-indicator', statusClass]"></span>{{ value }}</div>
  <!-- Bare count variant (detailed "Extra" column) -->
  <template v-else><span :class="['status-indicator', statusClass]"></span>{{ value }}</template>
</template>

<script>
import { calculatePercentage } from '@/composables/experimentResultsTransforms';

export default {
  name: 'FactStatusChips',
  props: {
    statusClass: {
      type: String,
      required: true,
    },
    value: {
      type: [Number, String],
      required: true,
    },
    total: {
      type: [Number, String],
      default: null,
    },
    numeric: {
      type: Boolean,
      default: false,
    },
  },
  setup() {
    return { calculatePercentage };
  },
};
</script>

<style scoped>
/* Status indicators (moved verbatim from ExperimentResults.vue) */
.status-indicator {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 5px;
}

.status-ok { background-color: #28a745; }
.status-warning { background-color: #ffc107; }
.status-error { background-color: #dc3545; }
.status-extra { background-color: #787878; }

.percentage {
  font-size: 1em;
  font-weight: bold;
}

.absolute-count {
  font-size: 0.8em;
  color: #666;
  text-align: center;
}

.numeric {
  text-align: center;
}
</style>
