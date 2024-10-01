<template>
  <div>
    <h3 class="h3-text mb-3">
      All experiment results
    </h3>
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
        @click="deleteSelectedExperiments"
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
      :items="filteredExperiments"
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
        <v-col cols="2">
          Name
        </v-col>
        <v-col cols="2">
          Date
        </v-col>
        <v-col cols="2">
          Models
        </v-col>
        <v-col
          cols="1"
        >
          <div class="horizontal-centered">
            Questions
          </div>
        </v-col>
        <v-col cols="1">
          <div class="horizontal-centered">
            Facts
          </div>
        </v-col>
        <v-col cols="1">
          <div class="horizontal-centered">
            Chunks
          </div>
        </v-col>
        <v-col cols="1">
          <div class="horizontal-centered">
            Chunk Eval
          </div>
        </v-col>
        <v-col cols="1">
          Retriever
        </v-col>
      </template>
      <template #body>
        <v-row
          v-for="experiment in filteredExperiments"
          class="table-row table-row-height"
          :key="experiment.id"
        >
          <v-col cols="auto">
            <v-checkbox
              v-model="experiment.selected"
              color="primary"
              hideDetails
            />
          </v-col>
          <v-col cols="2">
            <div
              class="ellipsis clickable primary--text"
              style="max-width: fit-content"
              @click="viewExperimentResults(experiment)"
            >
              {{ experiment.name }}
            </div>
          </v-col>
          <v-col cols="2">
            <small>
              {{ formatDate(experiment.date) }}
            </small>
          </v-col>
          <v-col cols="2">
            <MaxWidthChip
              v-if="experiment.models.length > 0"
              class="mr-1 mt-2"
              :max-width="175"
              :text-array="[experiment.models[0]]"
              small
            />
            <div
              v-if="experiment.models.length > 1"
              class="inline-middle"
            >
              <v-tooltip location="right">
                <template #activator="{ props }">
                  <div v-bind="props">
                    <MaxWidthChip
                      class="mr-1 mt-2"
                      :text-array="[`+${experiment.models.length - 1}`]"
                      small
                    />
                  </div>
                </template>
                {{ experiment.models.slice(1).join(', ') }}
              </v-tooltip>
            </div>
          </v-col>
          <v-col cols="1">
            <div class="horizontal-centered">
              {{ experiment.questions }}
            </div>
          </v-col>
          <v-col cols="1">
            <div class="horizontal-centered">
              {{ experiment.facts }}
            </div>
          </v-col>
          <v-col cols="1">
            <div class="horizontal-centered">
              {{ experiment.chunks }}
            </div>
          </v-col>
          <v-col cols="1">
            <div class="horizontal-centered">
              {{ experiment.hasChunkEval ? 'Yes' : 'No' }}
            </div>
          </v-col>
          <v-col cols="1">
            <div
              class="ellipsis"
              style="max-width: fit-content"
            >
              <small>
                {{ experiment.retriever }}
              </small>
            </div>
          </v-col>
        </v-row>
      </template>
    </TableWithFooter>
  </div>
</template>
<script>
import { experimentService } from '@/services/generatorService';
import { formatDate } from '@/utils/dateFormatter';
import TableWithFooter from '@/components/elements/Tables/TableWithFooter';
import MaxWidthChip from '@/components/elements/general/MaxWidthChip';

export default {
  name: 'ExperimentTable',

  components: {
    TableWithFooter,
    MaxWidthChip,
  },

  data() {
    return {
      experiments: [],
      selectAll: false,
      loading: false,
      error: null,
      currentPage: 1,
      itemsPerPage: 10,
      filter: '',
    };
  },

  computed: {
    trimmedFilter() {
      return this.filter.trim().toLowerCase();
    },

    filteredExperiments() {
      return this.experiments.filter(exp => {
        return exp.name.toLowerCase().includes(this.trimmedFilter);
      });
    },

    selectedItems() {      
      return this.experiments.filter(exp => exp.selected);
    },

    total() {
      return this.filteredExperiments.length;
    },
  },

  mounted() {
    this.fetchExperiments();
  },

  methods: {
    formatDate,
    selectAllItems() {
      this.experiments.forEach(exp => exp.selected = this.selectAll);
    },

    async fetchExperiments() {
      this.loading = true;
      try {
        const data = await experimentService.getAllExperiments();
        this.experiments = data.map(experiment => ({
          ...experiment,
          selected: false,
          models: experiment.models.filter(model => 
            model !== "Hallucinations Eval" && model !== "Missings Eval"
          ),
          hasChunkEval: experiment.models.includes("Hallucinations Eval") || experiment.models.includes("Missings Eval")
        }));
        this.error = null;
      } catch (e) {
        console.error('Error fetching experiments:', e);
        this.error = `Failed to fetch experiments: ${e.message}`;
      } finally {
        this.loading = false;
      }
    },

    async deleteSelectedExperiments() {
      if (this.selectedItems.length === 0) return;

      const confirmMessage = this.selectedItems.length === 1
        ? `Are you sure you want to delete the experiment "${this.selectedItems[0].name}"?`
        : `Are you sure you want to delete ${this.selectedItems.length} selected experiments?`;

      if (confirm(confirmMessage)) {
        try {
          for (const experiment of this.selectedItems) {
            await experimentService.deleteExperiment(experiment.name);
          }
          await this.fetchExperiments();
        } catch (error) {
          console.error('Error deleting experiments:', error);
          alert('Failed to delete one or more experiments. Please try again.');
        }
      }
    },

    viewExperimentResults(experiment) {
      this.$router.push({ 
        name: 'ExperimentResults', 
        query: { path: experiment.resultsPath } 
      });
    },
  },
}
</script>
<style lang="scss" scoped>
.filter-field {
  width: 265px;
}

.error-message {
  color: red;
  font-weight: bold;
}

.ellipsis {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>