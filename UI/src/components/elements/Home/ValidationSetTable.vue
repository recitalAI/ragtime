<template>
  <div class="saved-files-section">
    <h2 class="h3-text mb-3">
      Validation sets
    </h2>
    <div class="mb-4">
      <v-text-field
        v-model="filter"
        class="filter-field inline-middle mr-3"
        style="display: inline-block !important"
        variant="outlined"
        color="primary"
        density="compact"
        placeholder="Filter by name"
        hide-details
      />
      <v-btn
        v-if="selectedItems.length > 0"
        class="mr-3 inline-middle"
        color="primary"
        rounded
        @click="deleteSelectedValidationSets"
      >
        <v-icon
          size="17"
          start
        >
          fas fa-trash
        </v-icon>
        {{ $t('delete') }}
        <span
          v-if="selectedItems.length > 0"
          class="ml-2"
        >
          ({{ selectedItems.length }})
        </span>
      </v-btn>
    </div>
    <TableWithFooter
      no-results-message="validation_sets.not_found"
      :items="filteredValidationSets"
      :paginated-items-length="filteredValidationSets.length"
      :loading="loading"
      :current-page="currentPage"
      :items-per-page="itemsPerPage"
      :total="total"
      :show-footer="false"
    >
      <template #header>
        <v-col cols="auto">
          <v-checkbox
            v-model="selectAll"
            @change="selectAllItems"
            hideDetails
          />
        </v-col>
        <v-col cols="5">
          {{ $t('name') }}
        </v-col>
        <v-col cols="2">
          {{ $t('date') }}
        </v-col>
        <v-col
          class="justify-center"
          cols="1"
        >
          {{ $t('questions') }}
        </v-col>
        <v-col
          class="justify-center"
          cols="1"
        >
          {{ $t('answers') }}
        </v-col>
        <v-col
          class="justify-center"
          cols="1"
        >
          {{ $t('facts') }}
        </v-col>
        <v-col
          class="justify-center"
          cols="1"
        >
          {{ $t('chunks') }}
        </v-col>
      </template>
      <template #body>
        <v-row
          v-for="set in filteredValidationSets"
          class="table-row table-row-height"
          :key="set.id"
        >
          <v-col cols="auto">
            <v-checkbox
              v-model="set.selected"
              color="primary"
              hideDetails
            />
          </v-col>
          <v-col cols="5">
            <div
              class="clickable ellipsis primary--text"
              style="max-width: fit-content"
              @click="modifyValidationSet(set)"
            >
              {{ set.name }}
            </div>
          </v-col>
          <v-col cols="2">
            <small>
              {{ formatDate(set.date) }}
            </small>
          </v-col>
          <v-col
            class="justify-center"
            cols="1"
          >
            {{ set.questions }}
          </v-col>
          <v-col
            class="justify-center"
            cols="1"
          >
            {{ set.answers }}
          </v-col>
          <v-col
            class="justify-center"
            cols="1"
          >
            {{ set.facts }}
          </v-col>
          <v-col
            class="justify-center"
            cols="1"
          >
            {{ set.chunks }}
          </v-col>
        </v-row>
      </template>
    </TableWithFooter>
    <div v-if="error" class="error-message">{{ error }}</div>
  </div>
</template>
<script>
import { http } from '@/plugins/axios';
import TableWithFooter from '@/components/elements/Tables/TableWithFooter';
import { experimentService } from '@/services/generatorService';
import { formatDate } from '@/utils/dateFormatter';

export default {
  name: 'ValidationSetTable',

  data() {
    return {
      validationSets: [],
      filter: '',
      selectAll: false,
      loading: false,
      error: null,
      currentPage: 1,
      itemsPerPage: 10,
    };
  },

  components: {
    TableWithFooter,
  },

  computed: {
    trimmedFilter() {
      return this.filter.trim().toLowerCase();
    },

    filteredValidationSets() {
      return this.validationSets.filter(set => {
        return set.name.toLowerCase().includes(this.trimmedFilter);
      });
    },

    selectedItems() {      
      return this.validationSets.filter(set => set.selected);
    },

    total() {
      return this.filteredValidationSets.length;
    },
  },

  mounted() {
    this.fetchValidationSets();
  },

  methods: {
    formatDate,
    openSettings() {
      this.$router.push('/settings');
    },

    selectAllItems() {
      this.validationSets.forEach(set => set.selected = this.selectAll);
    },

    async fetchValidationSets() {
      this.loading = true;
      try {
        const response = await http.get('validation-sets');
        if (!response) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = response.data;
        this.validationSets = data;
        this.error = null;
      } catch (e) {
        console.error('Error fetching validation sets:', e);
        this.error = `Failed to fetch validation sets: ${e.message}`;
      } finally {
        this.loading = false;
      }
    },

    modifyValidationSet(file) {
      const { name, questions, answers, facts, chunks } = file;
      this.$router.push({ 
        name: 'ModifyValidationSet', 
        query: { file: JSON.stringify({ name, questions, answers, facts, chunks }) }
      });
    },

    async deleteSelectedValidationSets() {
      if (this.selectedItems.length === 0) return;

      const confirmMessage = this.selectedItems.length === 1
        ? `Are you sure you want to delete the validation set "${this.selectedItems[0].name}"?`
        : `Are you sure you want to delete ${this.selectedItems.length} selected validation sets?`;

      if (confirm(confirmMessage)) {
        try {
          for (const set of this.selectedItems) {
            await experimentService.deleteValidationSet(set.name);
          }
          await this.fetchValidationSets();
        } catch (error) {
          console.error('Error deleting validation sets:', error);
          alert('Failed to delete one or more validation sets. Please try again.');
        }
      }
    },
  },
};
</script>
<style lang="scss" scoped>
.filter-field {
  width: 265px;
}

.error-message {
  color: red;
  font-weight: bold;
}
</style>
