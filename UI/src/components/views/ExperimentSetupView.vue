<template>
  <div class="experiment-setup page-padding py-7">
    <h2 class="text-h4 mb-4">Start experiment</h2>

    <v-card class="pa-6">
      <!-- Behavior fix (5.4): while a job is submitting or running, every
           form input is disabled (v-form propagates `disabled`); read-only
           toggles like chunk show/hide stay interactive. -->
      <v-form @submit.prevent="startExperiment" :disabled="isExperimentRunning">
        <v-text-field
          v-model="experimentName"
          label="Experiment Name"
          variant="outlined"
          color="primary"
          density="comfortable"
          placeholder="Enter experiment name"
          required
        />

        <v-row>
          <ValidationSetPicker
            :validation-sets="validationSets"
            v-model:selected-validation-set="selectedValidationSet"
            :locked-validation-set="lockedValidationSet"
            @change="onValidationSetChange"
          />

          <v-col cols="12" sm="6">
            <v-select
              v-model="evaluationModel"
              :items="evaluationModelOptions"
              item-title="title"
              item-value="value"
              label="Evaluation Model"
              variant="outlined"
              color="primary"
              density="comfortable"
              style="min-width: 200px; height: 80px"
              required
            >
              <template #item="{ item, props }">
                <v-list-item
                  v-bind="props"
                  :disabled="item.raw.disabled"
                  :subtitle="evalModelPrice(item.raw)"
                >
                  <template v-if="item.raw.disabled && item.raw.value !== ''">
                    (API key not available)
                  </template>
                </v-list-item>
              </template>
            </v-select>
          </v-col>
        </v-row>

        <DataFileImport
          v-if="selectedValidationSet || lockedValidationSet"
          @file-change="handleFileUpload"
          @clear="clearFileUpload"
        />

        <v-expand-transition>
          <div v-if="!fileName">
            <RetrieverOptions
              v-model:use-retriever="useRetriever"
              :disabled="isRetrieverSelectionDisabled"
              :retrievers="availableRetrievers"
              v-model:selected-retriever="selectedRetriever"
            />

            <ModelSelection
              :grouped="groupedLLMs"
              :builtins="builtinLLMs"
              :customizedLLMs="customizedLLMs"
              v-model:active-provider="activeProvider"
              v-model:selectedLLMs="selectedLLMs"
              v-model:selectedCustomLLMs="selectedCustomLLMs"
              v-model:reasoningChoices="reasoningChoices"
              v-model:reasoningEffortChoices="reasoningEffortChoices"
              :evaluate-chunks="evaluateChunks"
              :availability="apiKeyAvailability"
            />
          </div>
        </v-expand-transition>

        <v-card-text>
          <div class="d-flex flex-column flex-sm-row align-center justify-space-between mb-6">
            <v-checkbox
              v-model="evaluateAnswers"
              label="Evaluate Answers"
              class="ma-0 pa-0"
              hide-details
            />
            <v-checkbox
              v-model="evaluateChunks"
              label="Evaluate Chunks"
              class="ma-0 pa-0"
              hide-details
              :disabled="!canEvaluateChunks"
            />
          </div>
        </v-card-text>

        <v-expand-transition>
          <div v-if="matchedQuestions.length > 0" class="matched-questions mt-4">
            <v-card-title>Questions and Answers</v-card-title>
            <v-card-text>
              <v-expansion-panels>
                <v-expansion-panel
                  v-for="(item, index) in matchedQuestions"
                  :key="index"
                >
                  <v-expansion-panel-title>
                    Question: {{ item.question }}
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <v-textarea
                      v-if="item.isEditing"
                      v-model="item.editedAnswer"
                      label="Answer"
                      rows="3"
                      auto-grow
                    />
                    <p v-else>{{ item.answer }}</p>
                    <v-btn
                      v-if="item.isEditing"
                      color="primary"
                      :disabled="isExperimentRunning"
                      @click="saveAnswer(index)"
                      class="mr-2"
                    >
                      Save
                    </v-btn>
                    <v-btn
                      v-if="item.isEditing"
                      :disabled="isExperimentRunning"
                      @click="cancelEdit(index)"
                    >
                      Cancel
                    </v-btn>
                    <v-btn
                      v-else
                      color="primary"
                      :disabled="isExperimentRunning"
                      @click="editAnswer(index)"
                    >
                      Modify
                    </v-btn>
                    
                    <div v-if="item.chunks.length > 0" class="mt-4">
                      <v-card-subtitle>Chunks:</v-card-subtitle>
                      <div class="chunk-container">
                        <button 
                          type="button"
                          v-for="(chunk, chunkIndex) in item.chunks" 
                          :key="chunkIndex"
                          @click="toggleChunk(index, chunkIndex)"
                          class="chunk-button"
                        >
                          Chunk {{ chunkIndex + 1 }}
                        </button>
                      </div>
                      <div 
                        v-for="(chunk, chunkIndex) in item.chunks" 
                        :key="`text-${chunkIndex}`" 
                        v-show="item.visibleChunks[chunkIndex]" 
                        class="chunk-text mt-2"
                      >
                        <p><strong>Chunk {{ chunkIndex + 1 }}:</strong> {{ chunk }}</p>
                      </div>
                    </div>
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>
            </v-card-text>
          </div>
        </v-expand-transition>

        <v-card-text v-if="selectedModels.length > 0">
          <v-card-title>Selected Model:</v-card-title>
          <div class="d-flex align-center">
            <v-chip
              v-if="!isEditingModel"
              class="ma-2"
              :disabled="isExperimentRunning"
              @click="!isExperimentRunning && startEditingModel()"
            >
              {{ selectedModels[0] }}
            </v-chip>
            <v-text-field
              v-else
              v-model="editingModelName"
              dense
              hide-details
              class="model-edit-field ma-2"
              @keyup.enter="saveModelEdit"
              @blur="saveModelEdit"
            ></v-text-field>
            <v-btn
              v-if="isEditingModel"
              icon
              small
              @click="saveModelEdit"
            >
              <v-icon>mdi-check</v-icon>
            </v-btn>
          </div>
        </v-card-text>

        <LiveLogPanel
          v-if="isShowingLogs"
          :logs="liveLogs"
          v-model:auto-scroll="autoScroll"
        />

        <v-card-actions>
          <!-- type="submit" already routes the click through the form's
               @submit.prevent handler; a duplicate @click here used to fire
               startExperiment twice per click and queue two jobs. -->
          <v-btn
            color="primary"
            type="submit"
            :loading="isExperimentRunning"
            :disabled="!isFormValid || isExperimentRunning"
            block
          >
            {{ isExperimentRunning ? 'Experiment in Progress...' : 'Start Experiment' }}
          </v-btn>
        </v-card-actions>
      </v-form>
    </v-card>

    <FormatErrorDialog
      v-model="formatError.open"
      :message="formatError.message"
      :details="formatError.details"
      :spec="experimentDataFormat"
      @download-template="downloadExperimentTemplate"
    />

    <v-snackbar
      v-model="showSnackbar"
      :color="snackbarColor"
      :timeout="5000"
    >
      {{ message }}
    </v-snackbar>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch, nextTick } from 'vue';
import { useRoute } from 'vue-router';
import { experimentService, modelService } from '@/services/generatorService';
import * as XLSX from 'xlsx';
import { fetchModelCatalog, refreshAvailability, buildModelOptions, formatModelPrice } from '@/services/modelCatalog';
import { useExperimentLauncher } from '@/composables/useExperimentLauncher';
import ValidationSetPicker from '@/components/setup/ValidationSetPicker.vue';
import DataFileImport from '@/components/setup/DataFileImport.vue';
import FormatErrorDialog from '@/components/elements/general/FormatErrorDialog.vue';
import { EXPERIMENT_DATA_FORMAT, downloadExperimentDataTemplate } from '@/services/spreadsheetFormats';
import ModelSelection from '@/components/setup/ModelSelection.vue';
import RetrieverOptions from '@/components/setup/RetrieverOptions.vue';
import LiveLogPanel from '@/components/setup/LiveLogPanel.vue';

export default {
  name: 'ExperimentSetupView',
  components: {
    FormatErrorDialog,
    ValidationSetPicker,
    DataFileImport,
    ModelSelection,
    RetrieverOptions,
    LiveLogPanel,
  },
  setup() {
    const route = useRoute();
    const experimentName = ref('');
    const validationSets = ref([]);
    const selectedValidationSet = ref('');
    const evaluationModel = ref('');
    const selectedLLMs = ref([]);
    const evaluateAnswers = ref(true);
    const evaluateChunks = ref(false);
    const activeProvider = ref(null);
    const customizedLLMs = ref([]);
    const builtinLLMs = ref([]);
    const groupedLLMs = ref({});
    const availableRetrievers = ref([]);
    const selectedCustomLLMs = ref([]);
    // { modelName: bool } — per-model reasoning choice (default off).
    const reasoningChoices = ref({});
    const reasoningEffortChoices = ref({});
    const useRetriever = ref(false);
    const selectedRetriever = ref('');
    const lockedValidationSet = ref('');
    const fullValidationSetName = ref('');
    const fileData = ref(null);
    const formatError = ref({ open: false, message: '', details: [] });
    const experimentDataFormat = EXPERIMENT_DATA_FORMAT;
    const downloadExperimentTemplate = () => downloadExperimentDataTemplate(5);
    const fileName = ref('');
    const matchedQuestions = ref([]);
    const validationSetData = ref(null);
    const withCSV = ref(false);
    const selectedModels = ref([]);
    const hasChunks = ref(false);
    const message = ref('');
    const showSnackbar = ref(false);
    const snackbarColor = ref('');
    const isEditingModel = ref(false);
    const editingModelName = ref('');

    const apiKeyAvailability = ref({
      openai: true,
      mistral: true
    });

    const showMessage = (msg, type) => {
      message.value = msg;
      snackbarColor.value = type === 'success' ? 'success' : 'error';
      showSnackbar.value = true;
    };

    const startEditingModel = () => {
      isEditingModel.value = true;
      editingModelName.value = selectedModels.value[0];
      nextTick(() => {
        const input = document.querySelector('.model-edit-field input');
        if (input) input.focus();
      });
    };

    const saveModelEdit = () => {
      const newName = editingModelName.value.trim();
      if (newName && newName !== selectedModels.value[0]) {
        const oldName = selectedModels.value[0];
        selectedModels.value[0] = newName;
        // Update model name in matchedQuestions
        matchedQuestions.value.forEach(q => {
          if (q.modelName === oldName) {
            q.modelName = newName;
          }
        });
      }
      isEditingModel.value = false;
    };

    const fetchApiKeyAvailability = async () => {
      try {
        // Server-side refresh first, then read availability (this pairing
        // used to happen in apiKeyService.refreshLLMAvailability).
        apiKeyAvailability.value = await refreshAvailability();
      } catch (error) {
        console.error('Error fetching API key availability:', error);
      }
    };

    const fetchValidationSetData = async (validationSetName) => {
      try {
        const data = await experimentService.getValidationSet(validationSetName);
        validationSetData.value = data;
      } catch (error) {
        console.error('Error fetching validation set data:', error);
        showMessage('Failed to fetch validation set data. Please try again.', 'error');
      }
    };

    // Evaluation dropdown options come from the unified catalog; `disabled`
    // is derived generically from each model's required_key.
    const evaluationModelOptions = computed(() =>
      // The evaluation select mirrors the validation-set fact-generation list:
      // no answer-generation-only models (new GPT-5.x / Anthropic entries,
      // feature 3), and no OVH models. Unavailable models are shown greyed out
      // rather than hidden, so the price is still visible.
      buildModelOptions(builtinLLMs.value, apiKeyAvailability.value, {
        excludeAnswerGenOnly: true,
        excludeProviders: ['OVH'],
      })
    );

    // Price line for an eval option's subtitle (empty for the placeholder or
    // when no price is known).
    const evalModelPrice = (raw) => {
      if (!raw || !raw.value || !raw.pricing) return '';
      return formatModelPrice(raw.pricing);
    };

    const isAlbertSelected = computed(() => {
      return selectedCustomLLMs.value.some(llmName => {
        const model = customizedLLMs.value.find(m => m.name === llmName);
        return model && model.built_in_retriever;
      });
    });

    watch(isAlbertSelected, (newValue) => {
      if (newValue) {
        useRetriever.value = true;
      }
    });

    watch(evaluateChunks, (newValue) => {
      if (newValue) {
        if (selectedLLMs.value.length + selectedCustomLLMs.value.length > 1) {
          selectedLLMs.value = selectedLLMs.value.slice(0, 1);
          selectedCustomLLMs.value = [];
        }
      }
    });

    const canEvaluateChunks = computed(() => {
      return useRetriever.value || 
            selectedCustomLLMs.value.includes('Albert_LLM') ||
            selectedLLMs.value.some(model => model.toLowerCase().includes('albert')) ||
            hasChunks.value && !moreThanOneLLMSelected.value;
    });

    const moreThanOneLLMSelected = computed(() => {
      return (selectedLLMs.value.length + selectedCustomLLMs.value.length) > 1;
    });

    const isRetrieverSelectionDisabled = computed(() => {
      return selectedCustomLLMs.value.some(llmName => {
        const model = customizedLLMs.value.find(m => m.name === llmName);
        return model && model.built_in_retriever;
      });
    });

    const isFormValid = computed(() => {
      return experimentName.value.trim() !== '' &&
              evaluationModel.value !=='' &&
             (lockedValidationSet.value || selectedValidationSet.value !== '') &&
             (fileName.value !== '' || (selectedLLMs.value.length > 0 || selectedCustomLLMs.value.length > 0)) &&
             (evaluateAnswers.value || (evaluateChunks.value && hasChunks.value));
    });

    const fetchValidationSets = async () => {
      try {
        validationSets.value = await experimentService.getValidationSets();
      } catch (error) {
        console.error('Error fetching validation sets:', error);
      }
    };

    const handleFileUpload = async (event) => {
      const file = event.target.files[0];
      if (file) {
        clearFileUpload();
        
        fileName.value = file.name;
        if (file.name.endsWith('.csv')) {
          await readCSVFile(file);
        } else if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
          await readExcelFile(file);
        } else {
          showMessage('Please upload a CSV or Excel file', 'error');
          clearFileUpload();
          return;
        }
        processFileData();
      }
    };

    const readCSVFile = (file) => {
      return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = (e) => {
          const content = e.target.result;
          const firstLine = content.split('\n')[0];
          const separator = firstLine.includes(';') ? ';' : ',';
          fileData.value = content.split('\n').map(row => row.split(separator));
          resolve();
        };
        reader.readAsText(file);
      });
    };

    const readExcelFile = (file) => {
      return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = (e) => {
          const data = new Uint8Array(e.target.result);
          const workbook = XLSX.read(data, {type: 'array'});
          const firstSheetName = workbook.SheetNames[0];
          const worksheet = workbook.Sheets[firstSheetName];
          fileData.value = XLSX.utils.sheet_to_json(worksheet, {header: 1});
          resolve();
        };
        reader.readAsArrayBuffer(file);
      });
    };

    const fetchAvailableModelsAndRetrievers = async () => {
      try {
        const [catalog, retrievers] = await Promise.all([
          fetchModelCatalog(),
          modelService.getAvailableRetrievers()
        ]);
        builtinLLMs.value = catalog.builtins;
        groupedLLMs.value = catalog.grouped;
        customizedLLMs.value = catalog.customs;
        // Extract retriever names from the complex object
        availableRetrievers.value = Array.isArray(retrievers) 
          ? retrievers.map(r => typeof r === 'string' ? r : r.name || r.toString())
          : [];

        if (availableRetrievers.value.length > 0) {
          selectedRetriever.value = availableRetrievers.value[0];
        }
      } catch (error) {
        console.error('Error fetching available models and retrievers:', error);
      }
    };

    const clearFileUpload = () => {
      fileData.value = null;
      fileName.value = '';
      matchedQuestions.value = [];
      selectedModels.value = [];
      hasChunks.value = false;
      evaluateChunks.value = false;
      withCSV.value = false;
      
      selectedLLMs.value = [];
      selectedCustomLLMs.value = [];
      useRetriever.value = false;
      selectedRetriever.value = availableRetrievers.value.length > 0 ? availableRetrievers.value[0] : '';

      const fileInput = document.querySelector('input[type="file"]');
      if (fileInput) fileInput.value = '';
    };

    const processFileData = () => {
      if (!fileData.value || !validationSetData.value) return;

      matchedQuestions.value = [];
      selectedModels.value = [];
      hasChunks.value = false;
      
      const headers = fileData.value[0].map(header => header.trim().toLowerCase());
      const questionIndex = headers.indexOf('question');
      if (questionIndex === -1) {
        // Explanatory dialog (what is missing + the expected columns +
        // a template download) instead of a one-line snackbar.
        formatError.value = {
          open: true,
          message: 'The file must contain a "question" column.',
          details: [`Columns found: ${headers.filter(Boolean).join(', ') || '(none)'}`],
        };
        return;
      }
      withCSV.value = true;

      const answerIndex = headers.indexOf('answer');
      const modelIndex = headers.indexOf('model_name');
      const chunkIndexes = headers.reduce((acc, header, index) => {
        if (header.startsWith('chunk_')) {
          acc.push(index);
        }
        return acc;
      }, []);

      let hasAnyChunks = false;

      for (let i = 1; i < fileData.value.length; i++) {
        const values = fileData.value[i];
        const fileQuestion = values[questionIndex]?.trim();
        const fileAnswer = answerIndex !== -1 ? values[answerIndex]?.trim() : '';
        const fileChunks = chunkIndexes.map(index => values[index]?.trim()).filter(Boolean);
        const modelName = modelIndex !== -1 ? values[modelIndex]?.trim() : '';

        if (!fileQuestion) continue; 

        const matchedItem = validationSetData.value.items.find(
          item => item.question.text.trim().toLowerCase() === fileQuestion.toLowerCase()
        );

        if (matchedItem) {
          matchedQuestions.value.push({
            question: fileQuestion,
            answer: fileAnswer,
            editedAnswer: fileAnswer,
            isEditing: false,
            chunks: fileChunks,
            visibleChunks: fileChunks.map(() => false),
            facts: matchedItem.facts.items.map(fact => {
              if (typeof fact === 'object' && fact.text) {
                return fact.text;
              }
              return fact;
            }),
            originalIndex: validationSetData.value.items.indexOf(matchedItem),
            modelName: modelName || '(personalized model)' // Add modelName to each question
          });

          if (fileChunks.length > 0) {
            hasAnyChunks = true;
          }

          if (modelName && !selectedModels.value.includes(modelName)) {
            selectedModels.value.push(modelName);
          }
        }
      }

      if (selectedModels.value.length === 0) {
        selectedModels.value.push('(personalized model)');
      }

      // Ensure all questions have a valid model name
      matchedQuestions.value.forEach(q => {
        if (!q.modelName || !selectedModels.value.includes(q.modelName)) {
          q.modelName = selectedModels.value[0];
        }
      });

      hasChunks.value = hasAnyChunks;
    };

    const toggleChunk = (questionIndex, chunkIndex) => {
      matchedQuestions.value[questionIndex].visibleChunks[chunkIndex] = 
        !matchedQuestions.value[questionIndex].visibleChunks[chunkIndex];
    };

    const editAnswer = (index) => {
      matchedQuestions.value[index].isEditing = true;
    };

    const saveAnswer = (index) => {
      const question = matchedQuestions.value[index];
      question.answer = question.editedAnswer;
      question.isEditing = false;
    };

    const cancelEdit = (index) => {
      const question = matchedQuestions.value[index];
      question.editedAnswer = question.answer;
      question.isEditing = false;
    };

    const onValidationSetChange = async () => {
      clearFileUpload();
      if (selectedValidationSet.value || lockedValidationSet.value) {
        try {
          // When arriving from Create/Modify, the exact filename is in
          // fullValidationSetName; lockedValidationSet only holds the base
          // name for display and cannot be fetched from the backend.
          validationSetData.value = await experimentService.getValidationSet(
            selectedValidationSet.value || fullValidationSetName.value || lockedValidationSet.value
          );
        } catch (error) {
          console.error('Error fetching validation set data:', error);
          showMessage('Failed to fetch validation set data', 'error');
        }
      }
    };

    watch(selectedValidationSet, async (newValue) => {
      if (newValue) {
        await fetchValidationSetData(newValue);
      }
    });

    watch(fileName, (newValue) => {
      if (newValue === '') {
        matchedQuestions.value = [];
        selectedModels.value = [];
        hasChunks.value = false;
        evaluateChunks.value = false;
      }
    });

    const {
      isExperimentRunning,
      liveLogs,
      isShowingLogs,
      autoScroll,
      startExperiment,
      resumeRunningJob,
    } = useExperimentLauncher({
      experimentName,
      selectedValidationSet,
      fullValidationSetName,
      evaluationModel,
      selectedLLMs,
      selectedCustomLLMs,
      reasoningChoices,
      reasoningEffortChoices,
      selectedModels,
      evaluateAnswers,
      evaluateChunks,
      useRetriever,
      isAlbertSelected,
      selectedRetriever,
      validationSetData,
      matchedQuestions,
      fileName,
      withCSV,
    }, showMessage);

    onMounted(async () => {
      if (route.query.validationSet) {
        lockedValidationSet.value = route.query.validationSet;
        fullValidationSetName.value = route.query.fullValidationSetName;
        // Fetch with the EXACT filename: lockedValidationSet holds only the
        // base name (for display), which the backend cannot resolve -> 404
        // "Failed to fetch validation set data" right after saving a set.
        await fetchValidationSetData(
          fullValidationSetName.value || lockedValidationSet.value
        );
      } else {
        await fetchValidationSets();
      }
      await fetchApiKeyAvailability();
      await fetchAvailableModelsAndRetrievers();
      await resumeRunningJob();
    });

    return {
      formatError,
      experimentDataFormat,
      downloadExperimentTemplate,
      experimentName,
      validationSets,
      selectedValidationSet,
      evaluationModel,
      selectedLLMs,
      evaluateAnswers,
      evaluateChunks,
      hasChunks,
      validationSetData,
      isFormValid,
      isExperimentRunning,
      startExperiment,
      lockedValidationSet,
      fullValidationSetName,
      groupedLLMs,
      builtinLLMs,
      activeProvider,
      selectedRetriever,
      customizedLLMs,
      availableRetrievers,
      selectedCustomLLMs,
      reasoningChoices,
      reasoningEffortChoices,
      useRetriever,
      isRetrieverSelectionDisabled,
      canEvaluateChunks,
      moreThanOneLLMSelected,
      toggleChunk,
      isAlbertSelected,
      handleFileUpload,
      fileName,
      matchedQuestions,
      onValidationSetChange,
      clearFileUpload,
      editAnswer,
      saveAnswer,
      cancelEdit,
      selectedModels,
      evaluationModelOptions,
      evalModelPrice,
      apiKeyAvailability,
      liveLogs,
      isShowingLogs,
      autoScroll,
      snackbarColor,
      showSnackbar,
      message,
      isEditingModel,
      editingModelName,
      startEditingModel,
      saveModelEdit,
    };
  },
}
</script>

<style scoped>
.experiment-setup {
  height: calc(100vh - 64px); /* Adjust based on your app's header height */
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.v-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: auto;
}

.matched-questions {
  max-height: 500px;
  overflow-y: auto;
}

.chunk-container {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.chunk-button {
  background-color: #f0f0f0;
  border: 1px solid #ddd;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.chunk-button:hover {
  background-color: #e0e0e0;
}

.chunk-text {
  background-color: #f5f5f5;
  padding: 1rem;
  border-radius: 4px;
  margin-top: 0.5rem;
}

@media (max-width: 600px) {
  .providers-container {
    flex-direction: column;
  }
  
  .v-btn-toggle {
    flex-wrap: wrap;
  }
}


.model-edit-field {
  min-width: 300px;
}

.v-chip.editing {
  height: auto;
  padding: 0;
}
</style>
