<template>
  <div class="bottom-nav pr-5 my-8">
    <v-pagination
      v-model="page"
      class="right-gap"
      density="comfortable"
      active-color="primary"
      color="black"
      :length="totalPages"
      :total-visible="7"
      @update:model-value="onPageChange"
    />
    <div class="mr-6">
      {{ $t('datatable.footer.per_page') }}
    </div>
    <v-select
      style="width: 100px"
      class="flex-grow-0 mt-0"
      item-title="text"
      item-value="value"
      density="compact"
      variant="outlined"
      color="primary"
      :value="initialItemsPerPage"
      :items="itemsPerPageOptions"
      @update:model-value="onItemsPerPageChange"
      hide-details
    />
  </div>
</template>
<script>

export default {
  name: 'TableFooter',

  data() {
    return {
      page: null,
      itemsPerPageOptions: [
        { text: '5', value: 5 },
        { text: '10', value: 10 },
        { text: '20', value: 20 },
        { text: '100', value: 100 },
      ],
    };
  },

  watch: {
    currentPage() {
      this.page = this.currentPage;
    },
  },

  mounted() {
    this.page = this.currentPage;
  },

  methods: {
    onItemsPerPageChange(val) {
      this.$emit('changeItemsPerPage', val);
    },

    onPageChange(val) {
      this.$emit('changePage', val);
    }
  },

  props: {
    initialItemsPerPage: {
      type: Number,
      required: true,
    },
    currentPage: {
      type: Number,
      required: true,
    },
    totalPages: {
      type: Number,
      required: true,
    },
  },

  emits: ['changeItemsPerPage', 'changePage'],

}

</script>
<style lang="scss" scoped>

.bottom-nav {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  width: 100%;
}

</style>
