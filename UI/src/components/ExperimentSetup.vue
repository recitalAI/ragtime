<template>
  <div class="experiment-setup page-padding py-7">
    <h2 class="text-h4 mb-4">Start experiment</h2>

    <v-card class="pa-6">
      <v-form @submit.prevent="startExperiment">
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
          <v-col cols="12" sm="6">
            <v-select
              v-if="!lockedValidationSet"
              v-model="selectedValidationSet"
              :items="validationSets"
              item-title="name"
              item-value="name"
              label="Validation Set"
              variant="outlined"
              color="primary"
              density="comfortable"
              style="min-width: 200px; height: 80px"
              required
              @update:model-value="onValidationSetChange"
            />
            <v-text-field
              v-else
              v-model="lockedValidationSet"
              label="Validation Set"
              variant="outlined"
              color="primary"
              density="comfortable"
              disabled
            />
          </v-col>
          
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
                <v-list-item v-bind="props" :disabled="item.raw.disabled">
                  <template v-if="item.raw.disabled && item.raw.value !== ''">
                    (API key not available)
                  </template>
                </v-list-item>
              </template>
            </v-select>
          </v-col>
        </v-row>

        <div v-if="selectedValidationSet || lockedValidationSet">
          <v-file-input
            label="Import Data File (CSV or XLSX)"
            accept=".csv,.xlsx,.xls"
            prepend-icon="fa-solid fa-sheet-plastic"
            @change="handleFileUpload"
            :clearable="true"
            @click:clear="clearFileUpload"
          />
        </div>

        <v-expand-transition>
          <div v-if="!fileName">
            <v-switch
              v-model="useRetriever"
              label="Use Retriever"
              :disabled="isRetrieverSelectionDisabled"
            />

            <v-select
              v-if="useRetriever && !isRetrieverSelectionDisabled && availableRetrievers.length > 0"
              v-model="selectedRetriever"
              :items="availableRetrievers"
              label="Retriever configuration"
              variant="outlined"
              color="primary"
              style="min-width: 200px; height: 80px"
              density="comfortable"
            />

            <v-card class="mt-4 pa-4">
              <v-card-title>LLM configuration</v-card-title>
              <v-card-text>
                <div class="providers-container d-flex flex-wrap">
                  <v-btn
                    v-for="(provider, providerName) in groupedLLMs"
                    :key="providerName"
                    @click="toggleProvider(providerName)"
                    :color="activeProvider === providerName ? 'primary' : ''"
                    :outlined="activeProvider !== providerName"
                    class="mr-2 mb-2"
                  >
                    {{ providerName }}
                    <v-badge
                      v-if="getSelectedModelsCount(providerName) > 0"
                      :content="getSelectedModelsCount(providerName)"
                      color="primary"
                      class="ml-2"
                    />
                  </v-btn>
                  <v-btn
                    @click="toggleProvider('Customized')"
                    :color="activeProvider === 'Customized' ? 'primary' : ''"
                    :outlined="activeProvider !== 'Customized'"
                    class="mr-2 mb-2"
                  >
                    Customized
                    <v-badge
                      v-if="selectedCustomLLMs.length > 0"
                      :content="selectedCustomLLMs.length"
                      color="primary"
                      class="ml-2"
                    />
                  </v-btn>
                </div>

                <v-expand-transition>
                  <div v-if="activeProvider" class="mt-4">
                    <v-row v-if="activeProvider !== 'Customized'">
                      <v-col
                        v-for="model in groupedLLMs[activeProvider]"
                        :key="model"
                        cols="12"
                        sm="6"
                        md="4"
                      >
                        <v-checkbox
                          v-model="selectedLLMs"
                          :label="model"
                          :value="model"
                          :disabled="isModelDisabled(activeProvider, model) || (evaluateChunks && selectedLLMs.length > 0 && !selectedLLMs.includes(model))"
                          density="compact"
                        >
                        <template v-slot:label>
                          <div style="display: flex; flex-direction: column; width: 100%; padding: 10px;">
                            {{ model }}
                            <span v-if="isModelDisabled(activeProvider, model)" class="text-caption" style="white-space: pre-wrap; margin-top: 5px;">
                              API key not available
                            </span>
                          </div>
                        </template>
                        </v-checkbox>
                      </v-col>
                    </v-row>
                    <v-row v-else>
                      <v-col
                        v-for="llm in customizedLLMs"
                        :key="llm.name"
                        cols="12"
                        sm="6"
                        md="4"
                      >
                        <v-checkbox
                          v-model="selectedCustomLLMs"
                          :label="llm.name"
                          :value="llm.name"
                          :disabled="evaluateChunks && selectedCustomLLMs.length > 0 && !selectedCustomLLMs.includes(llm.name)"
                          density="compact"
                        >
                          <template v-slot:label>
                            <div style="display: flex; flex-direction: column; width: 100%; padding: 10px;">
                              {{ llm.name }}
                              <span v-if="llm.built_in_retriever" class="text-caption" style="white-space: pre-wrap; margin-top: 5px;">
                                Built-in retriever
                              </span>
                            </div>
                          </template>
                        </v-checkbox>
                      </v-col>
                    </v-row>
                  </div>
                </v-expand-transition>
              </v-card-text>
            </v-card>
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
            <v-card-title>Matched Questions and Answers</v-card-title>
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
                      @click="saveAnswer(index)"
                      class="mr-2"
                    >
                      Save
                    </v-btn>
                    <v-btn
                      v-if="item.isEditing"
                      @click="cancelEdit(index)"
                    >
                      Cancel
                    </v-btn>
                    <v-btn
                      v-else
                      color="primary"
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
          <v-card-title>Selected Models:</v-card-title>
          <v-chip-group>
            <v-chip
              v-for="model in selectedModels"
              :key="model"
            >
              {{ model }}
            </v-chip>
          </v-chip-group>
        </v-card-text>

        <v-card v-if="isShowingLogs" class="mt-4">
          <v-card-title>
            Experiment Logs
            <v-spacer></v-spacer>
            <v-switch v-model="autoScroll" label="Auto-scroll"></v-switch>
          </v-card-title>
          <v-card-text>
            <div
              ref="logContainer"
              class="log-container"
              @scroll="handleScroll"
            >
              <p v-if="liveLogs.length === 0">Waiting for logs...</p>
              <pre v-for="(log, index) in liveLogs" :key="index">{{ log }}</pre>
            </div>
          </v-card-text>
        </v-card>

        <v-card-actions>
          <v-btn
            color="primary"
            type="submit"
            :loading="isExperimentRunning"
            :disabled="!isFormValid || isExperimentRunning"
            @click="startExperiment"
            block
          >
            {{ isExperimentRunning ? 'Experiment in Progress...' : 'Start Experiment' }}
          </v-btn>
        </v-card-actions>
      </v-form>
    </v-card>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { experimentService, modelService } from '@/services/generatorService';
import { formatDateForBackend } from '@/utils/dateFormatter';
import * as XLSX from 'xlsx';
import { http } from '@/plugins/axios';
import { apiKeyService } from '@/services/apiKeyService';
import { logService } from '@/services/logService';

export default {
  name: 'ExperimentSetup',
  setup() {
    const router = useRouter();
    const route = useRoute();
    const experimentName = ref('');
    const validationSets = ref([]);
    const selectedValidationSet = ref('');
    const evaluationModel = ref('');
    const selectedLLMs = ref([]);
    const evaluateAnswers = ref(true);
    const evaluateChunks = ref(false);
    const isExperimentRunning = ref(false);
    const activeProvider = ref(null);
    const customizedLLMs = ref([]);
    const availableRetrievers = ref([]);
    const selectedCustomLLMs = ref([]);
    const useRetriever = ref(false);
    const selectedRetriever = ref('');
    const lockedValidationSet = ref('');
    const fullValidationSetName = ref('');
    const fileData = ref(null);
    const fileName = ref('');
    const matchedQuestions = ref([]);
    const validationSetData = ref(null);
    const withCSV = ref(false);
    const selectedModels = ref([]);
    const hasChunks = ref(false);

    // Log-related refs
    const liveLogs = ref([]);
    const isShowingLogs = ref(false);
    const autoScroll = ref(true);
    const logContainer = ref(null);
    let logPollingInterval = null;
    let lastLogTimestamp = null;
    let isExperimentComplete = false;

    const apiKeyAvailability = ref({
      openai: true,
      mistral: true
    });

    const fetchApiKeyAvailability = async () => {
      try {
        apiKeyAvailability.value = await apiKeyService.checkApiKeyAvailability();
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
        alert('Failed to fetch validation set data. Please try again.');
      }
    };

    const openAIModels = ['gpt-3.5-turbo', 'gpt-4', 'gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo'];
    const mistralAIModels = ['mistral/mistral-tiny', 'mistral/mistral-small', 'mistral/mistral-medium', 'mistral/mistral-large-latest'];

    const isModelDisabled = (providerName, modelName) => {
      if (providerName === 'OpenAI' && openAIModels.includes(modelName) && !apiKeyAvailability.value.openai) {
        return true;
      }
      if (providerName === 'Mistral AI' && mistralAIModels.includes(modelName) && !apiKeyAvailability.value.mistral) {
        return true;
      }
      return false;
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

    const groupedLLMs = {
      'OpenAI': [
        'gpt-3.5-turbo', 'gpt-4', 'gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo'
      ],
      'Anthropic': [
        'claude-3-haiku-20240307', 'claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-5-sonnet-20240620'
      ],
      'Google': [
        'gemini/gemini-pro', 'gemini/gemini-1.5-pro'
      ],
      'Mistral AI': [
        'mistral/mistral-tiny', 'mistral/mistral-small', 'mistral/mistral-medium', 'mistral/mistral-large-latest'
      ],
      'Cohere': [
        'command', 'command-light', 'command-nightly', 'command-r', 'command-r-plus'
      ],
      'Together AI': [
        'together_ai/mistralai/Mixtral-8x7B-Instruct-v0.1', 'together_ai/togethercomputer/CodeLlama-34b-Instruct'
      ],
      'Ollama': [
        'ollama/llama2', 'ollama/mistral', 'ollama/codellama', 'ollama/vicuna'
      ],
      'HuggingFace': [
        'huggingface/BigScience/bloom', 'huggingface/google/flan-t5-xxl'
      ]
    };

    const canEvaluateChunks = computed(() => {
      return useRetriever.value || 
            selectedCustomLLMs.value.includes('Albert_LLM') ||
            selectedLLMs.value.some(model => model.toLowerCase().includes('albert')) ||
            hasChunks.value && !moreThanOneLLMSelected.value;
    });

    const evaluationModelOptions = computed(() => [
      { title: 'Select a model', value: '', disabled: true },
      { title: 'GPT-4', value: 'gpt-4', disabled: !apiKeyAvailability.value.openai },
      { title: 'GPT-4o', value: 'gpt-4o', disabled: !apiKeyAvailability.value.openai },
      { title: 'Mistral Large', value: 'mistral/mistral-large-latest', disabled: !apiKeyAvailability.value.mistral },
    ]);

    const moreThanOneLLMSelected = computed(() => {
      return (selectedLLMs.value.length + selectedCustomLLMs.value.length) > 1;
    });

    const isRetrieverSelectionPossible = computed(() => {
      return selectedCustomLLMs.value.some(llmName => {
        const model = customizedLLMs.value.find(m => m.name === llmName);
        return model && !model.built_in_retriever;
      });
    });

    const isRetrieverSelectionDisabled = computed(() => {
      return selectedCustomLLMs.value.some(llmName => {
        const model = customizedLLMs.value.find(m => m.name === llmName);
        return model && model.built_in_retriever;
      });
    });
    

    const handleLLMSelection = (llm, isCustom = false) => {
      if (evaluateChunks.value) {
        selectedLLMs.value = isCustom ? [] : [llm];
        selectedCustomLLMs.value = isCustom ? [llm] : [];
      } else {
        if (isCustom) {
          const index = selectedCustomLLMs.value.indexOf(llm);
          if (index > -1) {
            selectedCustomLLMs.value.splice(index, 1);
          } else {
            selectedCustomLLMs.value.push(llm);
          }
        } else {
          const index = selectedLLMs.value.indexOf(llm);
          if (index > -1) {
            selectedLLMs.value.splice(index, 1);
          } else {
            selectedLLMs.value.push(llm);
          }
        }
      }
    };

    const isFormValid = computed(() => {
      return experimentName.value.trim() !== '' &&
              evaluationModel.value !=='' &&
             (lockedValidationSet.value || selectedValidationSet.value !== '') &&
             (fileName.value !== '' || (selectedLLMs.value.length > 0 || selectedCustomLLMs.value.length > 0)) &&
             (evaluateAnswers.value || (evaluateChunks.value && hasChunks.value));
    });

    const fetchValidationSets = async () => {
      try {
        const response = await http.get('validation-sets');
        if (!response) throw new Error(`HTTP error! status: ${response.status}`);
        validationSets.value = response.data;
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
          alert('Please upload a CSV or Excel file');
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
        const [models, retrievers] = await Promise.all([
          modelService.getAvailableModels(),
          modelService.getAvailableRetrievers()
        ]);
        customizedLLMs.value = models;
        // Extract retriever names from the complex object
        availableRetrievers.value = Array.isArray(retrievers) 
          ? retrievers.map(r => typeof r === 'string' ? r : r.name || r.toString())
          : [];

        if (availableRetrievers.value.length > 0) {
          selectedRetriever.value = availableRetrievers.value[0];
        }
        console.log('Fetched custom models:', models);
        console.log('Fetched available retrievers:', availableRetrievers.value);
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
        alert('File must contain a "question" column');
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

      console.log('Chunk indexes:', chunkIndexes);


      let hasAnyChunks = false;

      for (let i = 1; i < fileData.value.length; i++) {
        const values = fileData.value[i];
        const fileQuestion = values[questionIndex]?.trim();
        const fileAnswer = answerIndex !== -1 ? values[answerIndex]?.trim() : '';
        const fileChunks = chunkIndexes.map(index => values[index]?.trim()).filter(Boolean);
        const modelName = modelIndex !== -1 ? values[modelIndex]?.trim() : '';


        console.log(`Processing row ${i}:`);
        console.log('  Question:', fileQuestion);
        console.log('  Answer:', fileAnswer);
        console.log('  Chunks:', fileChunks);
        console.log('  Model:', modelName);

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
            originalIndex: validationSetData.value.items.indexOf(matchedItem)
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
          validationSetData.value = await experimentService.getValidationSet(
            selectedValidationSet.value || lockedValidationSet.value
          );
        } catch (error) {
          console.error('Error fetching validation set data:', error);
          alert('Failed to fetch validation set data');
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

    const fetchLiveLogs = async () => {
      try {
        const response = await logService.getLiveLogs(lastLogTimestamp);
        
        if (response.logs && Array.isArray(response.logs) && response.logs.length > 0) {
          console.log("Fetched new logs:", response.logs);
          liveLogs.value = [...liveLogs.value, ...response.logs];
          lastLogTimestamp = response.lastTimestamp;
          
          if (autoScroll.value) {
            nextTick(() => {
              if (logContainer.value) {
                logContainer.value.scrollTop = logContainer.value.scrollHeight;
              }
            });
          }
        } else {
          console.log("No new logs received");
        }

        isExperimentComplete = response.isComplete;
        if (isExperimentComplete && logPollingInterval) {
          console.log("Experiment complete, stopping log fetching");
          clearInterval(logPollingInterval);
          logPollingInterval = null;
        }
      } catch (error) {
        console.error('Failed to fetch live logs:', error);
      }
    };

    const startLogPolling = () => {
      if (!logPollingInterval) {
        fetchLiveLogs();
        logPollingInterval = setInterval(fetchLiveLogs, 1000);
      }
    };

    const stopLogPolling = () => {
      if (logPollingInterval) {
        clearInterval(logPollingInterval);
        logPollingInterval = null;
      }
    };

    const handleScroll = () => {
      if (logContainer.value) {
        const { scrollTop, scrollHeight, clientHeight } = logContainer.value;
        autoScroll.value = scrollTop + clientHeight >= scrollHeight - 10;
      }
    };

    const startExperiment = async () => {
      if (!validationSetData.value) {
        alert('Validation set data is not loaded. Please select a validation set.');
        return;
      }
      isExperimentRunning.value = true;
      isShowingLogs.value = true;
      lastLogTimestamp = null;
      isExperimentComplete = false;
      liveLogs.value = [];
      
      stopLogPolling();
      startLogPolling();
      
      fetchLiveLogs();
      logPollingInterval = setInterval(fetchLiveLogs, 1000);

      const selectedModel = fileName.value 
        ? selectedModels.value[0]
        : [...selectedLLMs.value, ...selectedCustomLLMs.value][0];

      if (matchedQuestions.value.length > 0) {
        validationSetData.value.items = matchedQuestions.value.map(item => ({
          question: { text: item.question },
          facts: { 
            items: item.facts.map(fact => ({ text: fact }))
          },
          answers: { 
            items: [
              {
                llm_answer: {
                  meta: {},
                  text: item.answer,
                  prompt: {
                    meta: {},
                    user: item.question,
                    system: "",
                    prompter: "AnsPrompterBase"
                  },
                  name: selectedModel,
                  full_name: selectedModel,
                  timestamp: formatDateForBackend(new Date()),
                  duration: 0,
                  chunks: item.chunks
                },
                meta: {},
                text: item.answer
              }
            ]
          },
          chunks: {
            meta: {},
            items: item.chunks.map(chunk => ({ text: chunk }))
          },
          timestamp: formatDateForBackend(new Date())
        }));
      }
      const experimentConfig = {
        name: experimentName.value,
        test: fullValidationSetName.value,
        validationSet: fullValidationSetName.value || selectedValidationSet.value,
        evaluationModel: evaluationModel.value,
        answerGenerationModels: [selectedModel],
        evaluateAnswers: evaluateAnswers.value,
        evaluateChunks: evaluateChunks.value,
        useRetriever: useRetriever.value || isAlbertSelected.value,
        retrieverType: selectedRetriever.value,
        validationSetData: validationSetData.value,
        withCSV: withCSV.value
      };

      try {
        const result = await experimentService.startExperiment(experimentConfig);
        alert(`Experiment completed successfully. Results are saved at: ${result.results_path}`);
        router.push({ 
          name: 'ExperimentResults', 
          query: { path: result.results_path } 
        });
      } catch (error) {
        console.error('Error starting experiment:', error);
        let errorMessage = 'An unexpected error occurred.';
        if (error.response && error.response.data && error.response.data.error) {
          errorMessage = error.response.data.error;
        }
        alert(`Error starting experiment: ${errorMessage}`);
      } finally {
        isExperimentRunning.value = false;
        if (logPollingInterval) {
          clearInterval(logPollingInterval);
          logPollingInterval = null;
        }
        await fetchLiveLogs();
      }
    };

    const toggleProvider = (providerName) => {
      if (activeProvider.value === providerName) {
        activeProvider.value = null;
      } else {
        activeProvider.value = providerName;
      }
    };

    const getSelectedModelsCount = (providerName) => {
      return selectedLLMs.value.filter(model => groupedLLMs[providerName].includes(model)).length;
    };

    onMounted(async () => {
      if (route.query.validationSet) {
        lockedValidationSet.value = route.query.validationSet;
        fullValidationSetName.value = route.query.fullValidationSetName;
        await fetchValidationSetData(lockedValidationSet.value);
      } else {
        await fetchValidationSets();
      }
      await fetchApiKeyAvailability();
      await fetchAvailableModelsAndRetrievers();
    });

    onUnmounted(() => {
      if (logPollingInterval) {
        clearInterval(logPollingInterval);
      }
    });

    return {
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
      toggleProvider,
      activeProvider,
      getSelectedModelsCount,
      selectedRetriever,
      customizedLLMs,
      availableRetrievers,
      selectedCustomLLMs,
      useRetriever,
      isRetrieverSelectionPossible,
      isRetrieverSelectionDisabled,
      canEvaluateChunks,
      moreThanOneLLMSelected,
      handleLLMSelection,
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
      isModelDisabled,
      apiKeyAvailability,
      liveLogs,
      isShowingLogs,
      startLogPolling,
      stopLogPolling,
      autoScroll,
      logContainer,
      handleScroll,
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

.providers-container {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.v-checkbox ::v-deep(.v-label) {
  opacity: 1;
}

.log-container {
  height: 300px;
  overflow-y: auto;
  background-color: #f5f5f5;
  padding: 10px;
  font-family: monospace;
  white-space: pre-wrap;
  word-wrap: break-word;
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

</style>