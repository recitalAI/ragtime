<template>
  <TableWithFooter
    class="mb-8"
    :items="items"
    :paginated-items-length="items.length"
    :loading="loading"
    :current-page="1"
    :items-per-page="items.length || 1"
    :total="items.length"
    :show-footer="false"
  >
    <template #header>
      <v-col cols="3">
        Model
      </v-col>
      <v-col cols="3">
        Date
      </v-col>
      <v-col
        class="justify-center"
        cols="1"
      >
        Price
        <CustomTooltip text="Total cost: answer generation + evaluation. Shows $0 for imported data or when no price was recorded." />
      </v-col>
      <v-col
        class="justify-center"
        cols="1"
      >
        Facts
      </v-col>
      <v-col
        class="justify-center"
        cols="1"
      >
        Ok
        <CustomTooltip text="Number of facts that exist in the answer." />
      </v-col>
      <v-col
        class="justify-center"
        cols="1"
      >
        Hallu
        <CustomTooltip text="Number of facts for which the answer presented contradictory or misaligned information." />
      </v-col>
      <v-col
        class="justify-center"
        cols="1"
      >
        Missing
        <CustomTooltip text="Number of facts that do not exist in the answer." />
      </v-col>
      <v-col
        class="justify-center"
        cols="1"
      >
        Extra
        <CustomTooltip text="Additional information in the answer." />

      </v-col>
    </template>
    <template #body>
      <v-row
        v-for="result in items"
        class="table-row table-row-height"
        :key="result.name"
      >
        <v-col
          :class="[
            'primary--text',
            'align-center',
            { 'clickable': hasChunkEvaluations }
          ]"
          cols="3"
          @click="hasChunkEvaluations ? $emit('model-click', result.name) : null"
        >
          {{ result.name }}
        </v-col>
        <v-col cols="3">
          {{ formatDate(result.date) }}
        </v-col>
        <v-col
          class="justify-center"
          cols="1"
        >
          {{ result.isChunkEval ? '—' : formatCostUSD(result.cost) }}
        </v-col>
        <v-col
          class="justify-center"
          cols="1"
        >
          {{ result.facts }}
        </v-col>
        <v-col
          class="justify-center"
          cols="1"
        >
          <FactStatusChips
            status-class="status-ok"
            :value="result.ok"
            :total="result.facts"
          />
        </v-col>
        <v-col
          class="justify-center"
          cols="1"
        >
          <FactStatusChips
            status-class="status-error"
            :value="result.hallu"
            :total="result.facts"
          />
        </v-col>
        <v-col
          class="justify-center"
          cols="1"
        >
          <FactStatusChips
            status-class="status-warning"
            :value="result.missing"
            :total="result.facts"
          />
        </v-col>
        <v-col
          class="justify-center"
          cols="1"
        >
          <FactStatusChips
            status-class="status-extra"
            :value="result.extra"
            numeric
          />
        </v-col>
      </v-row>
    </template>
  </TableWithFooter>
</template>

<script>
import { formatDate } from '@/utils/dateFormatter';
import { formatCostUSD } from '@/composables/experimentResultsTransforms';
import CustomTooltip from '@/components/Tooltip.vue';
import TableWithFooter from '@/components/elements/Tables/TableWithFooter.vue';
import FactStatusChips from '@/components/results/FactStatusChips.vue';

export default {
  name: 'ResultsSummaryTable',
  components: {
    CustomTooltip,
    TableWithFooter,
    FactStatusChips,
  },
  props: {
    items: {
      type: Array,
      required: true,
    },
    loading: {
      type: Boolean,
      default: false,
    },
    hasChunkEvaluations: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['model-click'],
  setup() {
    return { formatDate, formatCostUSD };
  },
};
</script>
