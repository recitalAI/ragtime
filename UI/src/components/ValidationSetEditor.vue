<template>
  <div :class="rootClass" class="page-padding py-7" v-if="isComponentMounted">
    <h2 :class="mode === 'create' ? 'text-h4' : 'h2-text'" class="mb-4">{{ mode === 'create' ? 'Create validation set' : 'Modify validation set' }}</h2>
    
    <v-card class="pa-6">
      <div class="action-buttons">
        <v-btn
          color="primary"
          variant="outlined"
          @click="triggerFileInput"
          rounded
          class="mr-3"
          :loading="isLoading"
        >
          <v-icon size="17" start>
            fa-solid fa-file-arrow-up
          </v-icon>
          Import file
        </v-btn>
        <input
          ref="fileInputRef"
          type="file"
          accept=".json,.xlsx,.csv"
          @change="loadFile"
          style="display: none;"
          multiple
        >
        <FormatHelp
          :spec="validationSetFormat"
          class="mr-3"
          @download-template="downloadValidationTemplate"
        />
        <v-btn
          class="mr-3"
          color="primary"
          variant="outlined"
          @click="toggleQuestionForm"
          rounded
        >
          <v-icon size="17" start>
            {{ showQuestionForm ? 'fa-sharp-duotone fa-solid fa-xmark' : 'fa-sharp-duotone fa-solid fa-plus' }}
          </v-icon>
          {{ showQuestionForm ? 'Cancel' : 'Add New Question' }}
        </v-btn>
        <v-btn
          color="primary"
          variant="outlined"
          @click="generateAnswers"
          :disabled="!qa.length || isGeneratingAll || !selectedAnswerModel"
          rounded
        >
          <v-icon size="17" start>
            {{ isGeneratingAll ? 'fa-duotone fa-solid fa-quote-right fa-bounce' : 'fa-solid fa-robot' }}
          </v-icon>
          {{ isGeneratingAll ? 'Generating...' : 'Generate All Answers' }}
        </v-btn>
        <v-btn
          color="primary"
          variant="outlined"
          @click="generateFacts"
          :disabled="!qa.length || isGeneratingFacts || !selectedFactModel"
          rounded
        >
          <v-icon size="17" start>
            {{ isGeneratingFacts ? 'fa-duotone fa-solid fa-quote-right fa-bounce' : 'fa-solid fa-lightbulb' }}
          </v-icon>
          {{ isGeneratingFacts ? 'Generating Facts...' : 'Generate Facts' }}
        </v-btn>
      </div>

      <div v-if="importedFiles.length" class="imported-files-section mt-4">
        <div class="text-caption mb-2">Imported files:</div>
        <v-chip
          v-for="(file, index) in importedFiles"
          :key="index"
          class="ma-1"
          size="small"
          closable
          @click:close="removeImportedFile(index)"
        >
          {{ file }}
        </v-chip>
      </div>

      <div class="select-container d-flex flex-column flex-sm-row justify-space-between justify-center mb-6">
        <v-select
          v-model="selectedAnswerModel"
          :items="answerModelOptions"
          item-title="title"
          item-value="value"
          label="Answer Generation Model"
          density="comfortable"
          variant="outlined"
          color="primary"
          class="flex-grow-1 mt-0"
          style="min-width: 200px; height: 80px"
          :hint="selectedAnswerModel ? 'Details: ' + answerModelOptions.find(option => option.value === selectedAnswerModel)?.title : ''"
          persistent-hint
        >
          <template #selection="{ item }">
            <span class="text-no-wrap">{{ item.raw.title }}</span>
          </template>
          <template #item="{ item, props }">
            <v-list-item
              v-bind="props"
              :disabled="item.raw.disabled"
              :subtitle="modelPriceTooltip(item.raw)"
            >
              <template v-if="item.raw.disabled && item.raw.value !== ''">
                (API key not available)
              </template>
            </v-list-item>
          </template>
        </v-select>

        <v-select
          v-model="selectedFactModel"
          :items="factModelOptions"
          item-title="title"
          item-value="value"
          label="Fact Generation Model"
          variant="outlined"
          color="primary"
          density="comfortable"
          class="flex-grow-1 mt-0"
          style="min-width: 200px; height: 80px"
          :hint="selectedFactModel ? 'Details: ' + factModelOptions.find(option => option.value === selectedFactModel)?.title : ''"
          persistent-hint
        >
          <template #selection="{ item }">
            <span class="text-no-wrap">{{ item.raw.title }}</span>
          </template>
          <template #item="{ item, props }">
            <v-list-item
              v-bind="props"
              :disabled="item.raw.disabled"
              :subtitle="modelPriceTooltip(item.raw)"
            >
              <template v-if="item.raw.disabled && item.raw.value !== ''">
                (API key not available)
              </template>
            </v-list-item>
          </template>
        </v-select>
      </div>

      <v-expand-transition>
        <div v-if="showQuestionForm" class="question-form mb-6">
          <v-textarea
            v-model="newQuestionText"
            label="Enter your question here"
            variant="outlined"
            rows="3"
          />
          <v-btn
            color="success"
            @click="addNewQuestion"
            class="mt-2"
          >
            Submit Question
          </v-btn>
        </div>
      </v-expand-transition>

      <QuestionEditor 
        v-if="qa.length"
        :qa="qa"
        :selectedAnswerModel="selectedAnswerModel"
        :selectedFactModel="selectedFactModel"
        @update:qa="updateQuestions"
      />

      <p v-if="!qa.length && !showQuestionForm" class="text-caption text-center my-4">
        No questions available. Import an Excel or JSON file, or add a new question to get started.
      </p>

      <div class="save-section mt-6" v-if="qa.length">
        <v-text-field
          v-model="fileName"
          label="Enter file name"
          variant="outlined"
          density="comfortable"
          class="mb-4"
        />
        <v-btn
          color="primary"
          @click="saveQuestions"
          :disabled="!fileName.trim()"
          rounded
        >
          {{ mode === 'create' ? 'Save Validation Set' : 'Save Changes' }}
        </v-btn>
      </div>

      <v-btn
        v-if="mode === 'create' && qa.length"
        color="error"
        @click="clearLocalStorage"
        class="mt-4"
        rounded
      >
        Clear Stored Data
      </v-btn>
    </v-card>

    <v-dialog v-model="showSaveConfirmation" max-width="500px">
      <v-card>
        <v-card-title class="text-h5">Congratulations!</v-card-title>
        <v-card-text>
          You have successfully {{ mode === 'create' ? 'created' : 'modified' }} the "{{ mode === 'create' ? savedFileName : fileName }}" validation set.
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" @click="goHome">Go Back Home</v-btn>
          <v-btn color="secondary" @click="proceedToExperiment">Proceed to Experiment</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="showUnsavedChangesWarning" max-width="500px">
      <v-card>
        <v-card-title class="text-h5">Warning</v-card-title>
        <v-card-text>
          You have unsaved changes. Are you sure you want to leave?
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="error" @click="confirmLeave">Leave</v-btn>
          <v-btn color="primary" @click="cancelLeave">Stay</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <FormatErrorDialog
      v-model="formatError.open"
      :message="formatError.message"
      :details="formatError.details"
      :spec="validationSetFormat"
      @download-template="downloadValidationTemplate"
    />

    <OfflineDialog v-model="showOfflineDialog" />

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
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import QuestionEditor from './QuestionEditor/index.vue';
import { loadJsonFile, saveJsonFile, updateJsonFile } from '@/services/fileService';
import FormatHelp from '@/components/elements/general/FormatHelp.vue';
import FormatErrorDialog from '@/components/elements/general/FormatErrorDialog.vue';
import OfflineDialog from '@/components/elements/general/OfflineDialog.vue';
import { useConnectivityGuard } from '@/composables/useConnectivityGuard';
import {
  VALIDATION_SET_FORMAT,
  downloadValidationSetTemplate,
  parseValidationSetSheet,
  SpreadsheetFormatError,
} from '@/services/spreadsheetFormats';
import { validateData, selectReferenceAnswer, buildFactAnswerPayload } from '@/services/validationHelper';
import { answerGeneratorService, factGeneratorService, experimentService } from '@/services/generatorService';
import { buildModelOptions, fetchModelCatalog, refreshAvailability, formatModelPrice } from '@/services/modelCatalog';

export default {
  name: 'ValidationSetEditor',
  props: {
    // 'create': blank editor with localStorage persistence (new sets)
    // 'edit':   loads an existing set from route.query.file and updates it
    mode: { type: String, default: 'create' }
  },
  components: { 
    FormatHelp,
    FormatErrorDialog,
    OfflineDialog,
    QuestionEditor,
  },
  setup(props) {
    const router = useRouter();
    const route = useRoute();
    const isCreate = props.mode === 'create';
    const { showOfflineDialog, ensureOnline, handleOfflineError } = useConnectivityGuard();
    const rootClass = isCreate ? 'create-validation-set' : 'modify-validation-set';
    // Exact filename on disk (with suffix + .json) — edit mode only; used
    // for fetch and update so saving never re-appends the suffix.
    const originalFileName = ref('');
    const qa = ref([]);
    const showQuestionForm = ref(false);
    const newQuestionText = ref('');
    const isGeneratingAll = ref(false);
    const isGeneratingFacts = ref(false);
    const fileName = ref('');
    const showSaveConfirmation = ref(false);
    const savedFileName = ref('');
    const showUnsavedChangesWarning = ref(false);
    const hasUnsavedChanges = ref(false);
    const originalQa = ref([]);
    const isComponentMounted = ref(false);
    const selectedAnswerModel = ref('');
    const selectedFactModel = ref('');
    const importedFiles = ref([]);
    const fileInputRef = ref(null);
    const isLoading = ref(false);
    const validationSetFormat = VALIDATION_SET_FORMAT;
    const formatError = ref({ open: false, message: '', details: [] });

    const showFormatError = (message, details = []) => {
      formatError.value = { open: true, message, details };
    };

    // Price line for a select option's tooltip/subtitle. Empty for the
    // "Select a model" placeholder and for models with no known price, so the
    // tooltip is disabled there.
    const modelPriceTooltip = (raw) => {
      if (!raw || !raw.value || !raw.pricing) return '';
      return formatModelPrice(raw.pricing);
    };

    const downloadValidationTemplate = () => {
      downloadValidationSetTemplate();
    };

    const message = ref('');
    const showSnackbar = ref(false);
    const snackbarColor = ref('');

    const triggerFileInput = () => {
      fileInputRef.value.click();
    };
    // Model options come from the unified catalog (/api/available-models,
    // sub-step 5.3); start with the placeholder and fill once the catalog
    // and key availability load.
    const answerModelOptions = ref([{ title: 'Select a model', value: '', disabled: true }]);
    const factModelOptions = ref([{ title: 'Select a model', value: '', disabled: true }]);
    (async () => {
      try {
        const [catalog, availability] = await Promise.all([fetchModelCatalog(), refreshAvailability()]);
        // Hide models whose provider key isn't configured, so these plain
        // selects stay short (the experiment-setup grid groups by provider and
        // keeps showing all, disabled).
        // OVH models are deliberately excluded from the validation-set
        // answer/fact generation selects (they remain available for the
        // experiment answer generation).
        const options = buildModelOptions(catalog.builtins, availability, {
          // Show every eligible model, but grey out the ones whose API key
          // isn't configured (they render disabled with an "API key not
          // available" note) instead of hiding them — an empty dropdown when
          // no key is set was confusing. buildModelOptions still sets each
          // option's `disabled` from availability.
          hideUnavailable: false,
          excludeProviders: ['OVH'],
          // New GPT-5.x / Anthropic models are answer-generation only for now
          // (feature 3): keep them out of validation-set answer/fact selects.
          excludeAnswerGenOnly: true,
        });
        answerModelOptions.value = options;
        factModelOptions.value = options;
      } catch (error) {
        console.error('Error loading model catalog:', error);
      }
    })();

    const apiKeyAvailability = ref({
      openai: true,
      mistral: true
    });

    // const fetchApiKeyAvailability = async () => {
    //   try {
    //     apiKeyAvailability.value = await apiKeyService.checkApiKeyAvailability();
    //   } catch (error) {
    //     console.error('Error fetching API key availability:', error);
    //   }
    // };

    const showMessage = (msg, type) => {
      message.value = msg;
      snackbarColor.value = type === 'success' ? 'success' : 'error';
      showSnackbar.value = true;
    };

    const formatQaItem = (item) => ({
      ...item,
      sourceFile: item.sourceFile || null,
      answers: {
        items: item.answers.items.map(answer => ({
          ...answer,
          isEditing: false,
          eval: answer.eval || { human: 0 }
        }))
      },
      facts: item.facts || { items: [] }
    });

    const loadExistingValidationSet = async () => {
      try {
        const fileData = JSON.parse(route.query.file);
        // fileData.name is the exact filename on disk. Keep it for fetch,
        // update and delete; only the base name is shown in the name field
        // (otherwise saving re-appends the _Validation_set_QxFy suffix and
        // creates duplicate files).
        originalFileName.value = fileData.name;
        fileName.value = fileData.name.replace(/\.json$/i, '').split('_Validation_set_')[0];

        // Normalize whatever is on disk: validation sets can come from
        // external tools and lack llm_answer / eval on their answers.
        const data = validateData(await experimentService.getValidationSet(originalFileName.value));
        qa.value = data.items.map(formatQaItem);
        originalQa.value = JSON.parse(JSON.stringify(qa.value));
        hasUnsavedChanges.value = false;
      } catch (error) {
        console.error('Error loading validation set:', error);
        const details = error.response?.data?.error || error.message || 'Unknown error';
        showMessage(`Error loading validation set: ${details}`, 'error');
      }
    };

    const goHome = () => {
      if (hasUnsavedChanges.value) {
        showUnsavedChangesWarning.value = true;
      } else {
        clearLocalStorage();
        router.push('/');
      }
    };

    const confirmGoBack = () => {
      if (hasUnsavedChanges.value) {
        showUnsavedChangesWarning.value = true;
      } else {
        goHome();
      }
    };

    const confirmLeave = () => {
      showUnsavedChangesWarning.value = false;
      hasUnsavedChanges.value = false;
      goHome();
    };

    const cancelLeave = () => {
      showUnsavedChangesWarning.value = false;
    };

    const loadFile = async (event) => {
      const files = event.target.files;
      if (!files.length) return;

      isLoading.value = true;
      let totalImportedCount = 0;
      
      try {
        for (let file of files) {
          // Check if the file has already been imported
          if (importedFiles.value.includes(file.name)) {
            showMessage(`File "${file.name}" has already been imported.`, 'error');
            continue;
          }

          // loadJsonFile already normalizes the structure (validateData):
          // question/answers/facts containers, llm_answer and eval defaults
          // are guaranteed. Only the source file needs to be tagged here.
          // Route by extension: .xlsx/.csv go through the spreadsheet parser,
          // .json through the (already normalizing) JSON loader.
          const isSheet = /\.(xlsx|xls|csv)$/i.test(file.name);
          const data = isSheet
            ? parseValidationSetSheet(await file.arrayBuffer())
            : await loadJsonFile(file);
          const skipped = data.skippedCount ?? data.skipped ?? 0;
          if (skipped > 0) {
            showMessage(`"${file.name}": ${skipped} item(s) without question text were skipped.`, 'error');
          }
          const newQuestions = data.items.map(item => ({
            ...item,
            sourceFile: file.name
          }));

          qa.value = [...qa.value, ...newQuestions];
          importedFiles.value.push(file.name);
          totalImportedCount += newQuestions.length;
        }
        
        hasUnsavedChanges.value = true;
        await nextTick();
        saveToLocalStorage();
        
        const msg = totalImportedCount === 0 
          ? 'No valid questions found in the imported file(s)'
          : `${totalImportedCount} ${totalImportedCount === 1 ? 'question' : 'questions'} imported`;
        showMessage(msg, totalImportedCount === 0 ? 'error' : 'success');

      } catch (error) {
        console.error('Error loading file:', error);
        // A format problem gets the explanatory dialog (what is wrong, what the
        // file should contain, and a template download) instead of a snackbar.
        if (error instanceof SpreadsheetFormatError || error.name === 'FormatError') {
          showFormatError(error.message, error.details || []);
        } else {
          showFormatError(`Could not read the file: ${error.message}`);
        }
      } finally {
        isLoading.value = false;
        // Reset the file input
        if (fileInputRef.value) {
          fileInputRef.value.value = '';
        }
      }
    };

    const removeImportedFile = (index) => {
      const fileToRemove = importedFiles.value[index];
      qa.value = qa.value.filter(q => q.sourceFile !== fileToRemove);
      importedFiles.value.splice(index, 1);
      hasUnsavedChanges.value = true;
      saveToLocalStorage();
    };

    const updateQuestions = async (newQuestions) => {
      qa.value = JSON.parse(JSON.stringify(newQuestions)); 
      hasUnsavedChanges.value = true;
      await nextTick();
      saveToLocalStorage();
    };

    const toggleQuestionForm = () => {
      showQuestionForm.value = !showQuestionForm.value;
      if (!showQuestionForm.value) {
        newQuestionText.value = '';
      }
    };

    const addNewQuestion = async () => {
      if (newQuestionText.value.trim()) {
        qa.value.push({
          question: { text: newQuestionText.value.trim() },
          answers: { items: [] },
          facts: { items: [] }
        });
        newQuestionText.value = '';
        showQuestionForm.value = false;
        hasUnsavedChanges.value = true;
        await nextTick();
        saveToLocalStorage();
      }
    };

    const generateAnswers = async () => {
      if (!qa.value.length) return;
      if (!ensureOnline()) return;
      
      isGeneratingAll.value = true;
      try {
        const updatedQuestions = await answerGeneratorService.generateAnswers(qa.value, selectedAnswerModel.value);
        qa.value = qa.value.map((q, index) => {
          const updatedQ = updatedQuestions[index];
          return {
            ...q,
            answers: {
              items: [...(q.answers?.items || []), ...(updatedQ.answers?.items || [])]
            }
          };
        });
        hasUnsavedChanges.value = true;
        await nextTick();
        saveToLocalStorage();
        showMessage('Answers generated successfully!', 'success');
      } catch (error) {
        console.error('Error generating answers:', error);
        if (handleOfflineError(error)) return;
        const details = error.response?.data?.error || error.message || 'Unknown error';
        showMessage(`Error generating answers: ${details}`, 'error');
      } finally {
        isGeneratingAll.value = false;
      }
    };

    const generateFacts = async () => {
      if (!qa.value.length) return;
      if (!ensureOnline()) return;

      // Facts are generated for every question, using its reference answer:
      // the first human-validated answer if any, otherwise the first answer.
      // The only requirement is that every question has at least one answer.
      const missing = [];
      qa.value.forEach((q, i) => {
        if (!selectReferenceAnswer(q)) missing.push(i + 1);
      });
      if (missing.length > 0) {
        const preview = missing.slice(0, 5).join(', ') + (missing.length > 5 ? ', \u2026' : '');
        showMessage(`Cannot generate facts: ${missing.length} question(s) have no answer (question ${preview}). Generate or add an answer for every question first.`, 'error');
        return;
      }

      isGeneratingFacts.value = true;
      try {
        const payloadQuestions = qa.value.map(q => ({
          question: { text: q.question.text },
          answers: { items: [buildFactAnswerPayload(selectReferenceAnswer(q))] }
        }));

        const updatedQuestions = await factGeneratorService.generateFacts(payloadQuestions, selectedFactModel.value);
        // Every question was sent, so responses align with qa by index.
        qa.value = qa.value.map((q, i) => {
          const updatedQ = updatedQuestions[i];
          return updatedQ?.facts?.items?.length ? { ...q, facts: updatedQ.facts } : q;
        });
        hasUnsavedChanges.value = true;
        await nextTick();
        saveToLocalStorage();
        const stillWithout = qa.value.filter(q => !q.facts?.items?.length).length;
        if (stillWithout > 0) {
          showMessage(`Facts generated, but ${stillWithout} question(s) still have none. You can retry them individually from the question card.`, 'error');
        } else {
          showMessage('Facts generated successfully!', 'success');
        }
      } catch (error) {
        console.error('Error generating facts:', error);
        if (handleOfflineError(error)) return;
        const details = error.response?.data?.error || error.message || 'Unknown error';
        showMessage(`Error generating facts: ${details}`, 'error');
      } finally {
        isGeneratingFacts.value = false;
      }
    };


    const saveQuestions = async () => {
      if (!fileName.value.trim()) {
        showMessage('Please enter a file name.', 'error');
        return;
      }

      const questionsWithoutFacts = qa.value.filter(q => !q.facts || q.facts.items.length === 0);
      if (questionsWithoutFacts.length > 0) {
        showMessage(`${questionsWithoutFacts.length} question(s) do not have facts generated. Please generate facts for all questions before saving.`, 'error');

        return;
      }

      const questionsCount = qa.value.length;
      const factsCount = qa.value.reduce((total, q) => total + (q.facts?.items?.length || 0), 0);
      
      const formattedFileName = `${fileName.value.trim()}_Validation_set_Q${questionsCount}_F${factsCount}.json`;

      const dataToSave = {
        meta: {},
        items: qa.value.map(q => {
          // eslint-disable-next-line no-unused-vars
          const { sourceFile, ...questionWithoutSource } = q;
          const reference = selectReferenceAnswer(q);
          const hasValidated = q.answers.items.some(a => a.eval?.human === 1);
          return {
            ...questionWithoutSource,
            answers: {
              ...questionWithoutSource.answers,
              items: questionWithoutSource.answers.items.map(a => {
                // eslint-disable-next-line no-unused-vars
                const { isEditing, ...answer } = a;
                const promote = !hasValidated && a === reference;
                const evalObj = promote ? { ...(a.eval || {}), human: 1 } : (a.eval || { human: 0 });
                return { ...answer, eval: evalObj, isGolden: evalObj.human === 1 };
              })
            }
          };
        })
      };

      try {
        const result = isCreate
          ? await saveJsonFile(dataToSave, formattedFileName)
          : await updateJsonFile(dataToSave, formattedFileName, originalFileName.value);
        if (result.message.includes('successfully')) {
          savedFileName.value = formattedFileName;
          if (!isCreate) originalFileName.value = formattedFileName;
          showSaveConfirmation.value = true;
          hasUnsavedChanges.value = false;
          originalQa.value = JSON.parse(JSON.stringify(qa.value));
          fileName.value = formattedFileName.split('_Validation_set_')[0];
        } else {
          throw new Error('Failed to save file');
        }
      } catch (error) {
        console.error('Error saving file:', error);
        const details = error.response?.data?.error || error.message || 'Unknown error';
        showMessage(`Error saving file: ${details}`, 'error');
      }
    };

    const saveToLocalStorage = () => {
      if (!isCreate) return;
      if (isComponentMounted.value) {
        localStorage.setItem('qaData', JSON.stringify(qa.value));
        localStorage.setItem('importedFiles', JSON.stringify(importedFiles.value));
      }
    };

    const loadFromLocalStorage = () => {
      if (!isCreate) return;
      const storedQaData = localStorage.getItem('qaData');
      const storedImportedFiles = localStorage.getItem('importedFiles');
      if (storedQaData) {
        try {
          // Normalize restored data too: localStorage may hold data written
          // by an older version of the app with a different shape.
          const restored = validateData({ items: JSON.parse(storedQaData) });
          qa.value = restored.items;
          originalQa.value = JSON.parse(JSON.stringify(restored.items));
        } catch (error) {
          console.error('Error parsing stored qa data:', error);
          clearLocalStorage();
        }
      }
      if (storedImportedFiles) {
        try {
          importedFiles.value = JSON.parse(storedImportedFiles);
        } catch (error) {
          console.error('Error parsing stored imported files:', error);
          importedFiles.value = [];
        }
      }
    };

    const clearLocalStorage = () => {
      if (!isCreate) return;
      localStorage.removeItem('qaData');
      localStorage.removeItem('importedFiles');
      qa.value = [];
      importedFiles.value = [];
      hasUnsavedChanges.value = false;
    };

    const proceedToExperiment = () => {
      clearLocalStorage();
      router.push({
        name: 'ExperimentSetup',
        query: { 
          validationSet: fileName.value,
          fullValidationSetName: savedFileName.value
        }
      });
    };

    const handleBeforeUnload = (event) => {
      if (hasUnsavedChanges.value) {
        event.preventDefault();
        event.returnValue = '';
      }
    };

    onMounted(() => {
      if (isCreate) {
        loadFromLocalStorage();
      } else {
        loadExistingValidationSet();
      }
      window.addEventListener('beforeunload', handleBeforeUnload);
      isComponentMounted.value = true;
    });

    // onMounted(async () => {
    //   await fetchApiKeyAvailability();
    // });



    onBeforeUnmount(() => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      isComponentMounted.value = false;
    });

    watch(qa, () => {
      if (isComponentMounted.value) {
        hasUnsavedChanges.value = JSON.stringify(qa.value) !== JSON.stringify(originalQa.value);
      }
    }, { deep: true });

    return {
      validationSetFormat,
      formatError,
      downloadValidationTemplate,
      qa,
      showQuestionForm,
      newQuestionText,
      isGeneratingAll,
      isGeneratingFacts,
      fileInputRef,
      isLoading,
      fileName,
      triggerFileInput,
      showSaveConfirmation,
      savedFileName,
      showUnsavedChangesWarning,
      hasUnsavedChanges,
      isComponentMounted,
      rootClass,
      selectedAnswerModel,
      selectedFactModel,    
      goHome,
      confirmGoBack,
      confirmLeave,
      cancelLeave,
      loadFile,
      updateQuestions,
      toggleQuestionForm,
      addNewQuestion,
      generateAnswers,
      generateFacts,
      saveQuestions,
      clearLocalStorage,
      importedFiles,
      removeImportedFile,
      factModelOptions,
      answerModelOptions,
      modelPriceTooltip,
      showOfflineDialog,
      apiKeyAvailability,
      showSnackbar,
      snackbarColor,
      message,
      proceedToExperiment
    };
  }
};
</script>


<style scoped>
.create-validation-set,
.modify-validation-set {
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

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1rem;
}

.v-btn {
  text-transform: none;
  font-weight: bold;
}

/* Ensure v-select takes full width */
:deep(.v-select) {
  width: 100%;
}

/* Adjust input field width */
:deep(.v-field__input) {
  width: 100% !important;
}

/* Custom styles for select elements */
:deep(.v-select__selection) {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:deep(.v-select__selection-text) {
  max-width: calc(100% - 24px);
  overflow: hidden;
  text-overflow: ellipsis;
}

.imported-files-section {
  width: 100%;
  border-top: 1px solid rgba(0, 0, 0, 0.12);
  padding-top: 1rem;
}

.select-container {
  flex-wrap: wrap;
  gap: 1rem;
}

@media (max-width: 600px) {
  .action-buttons {
    flex-direction: column;
  }
  
  .select-container {
    flex-direction: column;
  }
}
</style>