<template>
  <div>
    <v-card class="pa-0">
      <v-container
        class="pa-0 table-row-height"
        fluid
      >
        <div class="header-container">
          <SortButton
            v-if="sortable"
            v-model="descendingSort"
            class="ml-2"
          />
          <v-row class="table-row table-row-height pt-0">
            <slot name="header" />
          </v-row>
        </div>
      </v-container>
      <div v-if="loading">
        <div v-if="paginatedItemsLength === 0">
          <div
            v-for="item in 10"
            :key="item"
            class="table-row-height"
          >
            <v-skeleton-loader type="table-row" />
          </div>
        </div>
        <div
          v-for="item in paginatedItemsLength"
          :key="item"
          class="table-row-height"
        >
          <v-skeleton-loader type="table-row" />
        </div>
      </div>
      <div
        v-else-if="total === 0"
        class="table-row fade-in table-row-height"
        style="text-align: center; padding-top: 15px;"
      >
        <i>{{ $t(noResultsMessage) }}</i>
      </div>
      <div
        v-else
        :class="{'ml-7': sortable}"
      >
        <slot name="body" />
      </div>
      <TableFooter
        v-if="showFoother && total > 0 && includeFooterInTableCard === true"
        class="custom-footer-margins"
        :initial-items-per-page="itemsPerPage"
        :current-page="currentPage"
        :total-pages="totalPages"
        @change-items-per-page="onItemsPerPageChange"
        @change-page="onPageChange"
      />
    </v-card>
    <TableFooter
      v-if="showFooter && total > 0 && includeFooterInTableCard === false"
      :initial-items-per-page="itemsPerPage"
      :current-page="currentPage"
      :total-pages="totalPages"
      @change-items-per-page="onItemsPerPageChange"
      @change-page="onPageChange"
    />
  </div>
</template>

<script>

import TableFooter from '@/components/elements/Tables/TableFooter';
import SortButton from '@/components/elements/Tables/SortButton';

export default {
  name: 'TableWithFooter',

  components: {
    TableFooter,
    SortButton,
  },

  data() {
    return {
      descendingSort: true,
    };
  },

  computed: {
    totalPages() {
      return Math.ceil(this.total / this.itemsPerPage);
    },
  },

  watch: {
    descendingSort() {
      this.$emit('sort', this.descendingSort);
    },
  },

  methods: {
    onItemsPerPageChange(itemsPerPage) {
      this.$emit('changeItemsPerPage', itemsPerPage);
    },

    onPageChange(page) {
      this.$emit('changePage', page);
    },
  },

  props: {
    loading: {
      type: Boolean,
      required: true,
    },
    paginatedItemsLength: {
      type: Number,
      required: true,
    },
    total: {
      type: Number,
      required: true,
    },
    currentPage: {
      type: Number,
      required: true,
    },
    itemsPerPage: {
      type: Number,
      required: true,
    },
    includeFooterInTableCard: {
      type: Boolean,
      default: false,
    },
    noResultsMessage: {
      type: String,
      default: 'no_results',
    },
    type: {
      type: String,
      default: 'default',
    },
    sortable: {
      type: Boolean,
      default: false,
    },
    showFooter: {
      type: Boolean,
      default: true,
    },
  },

  emits: ['changeItemsPerPage', 'changePage', 'sort'],

}

</script>
<style lang="scss" scoped>

.custom-footer-margins {
  margin-top: 10px !important;
  margin-right: 20px !important;
  margin-bottom: 5px !important;
}

.header-container {
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  border-bottom: 1px solid rgb(var(--v-theme-primary));
}

</style>
