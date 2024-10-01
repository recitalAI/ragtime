<template>
  <div class="modify-validation-set page-padding py-7">
    <h2 class="h2-text mb-4">
      Modify validation set
    </h2>
    
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
          Import JSON
        </v-btn>
        <input
          ref="fileInputRef"
          type="file"
          accept=".json"
          @change="loadFile"
          style="display: none;"
          multiple
        >
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
            {{isGeneratingAll ? 'fa-duotone fa-solid fa-quote-right fa-bounce' : 'fa-solid fa-robot'}}
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
        <v-icon
            size="17"
            start
          >
          {{isGeneratingFacts ? 'fa-duotone fa-solid fa-quote-right fa-bounce' : 'fa-solid fa-lightbulb'}}
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
            <v-list-item v-bind="props" :disabled="item.raw.disabled">
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
            <v-list-item v-bind="props" :disabled="item.raw.disabled">
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
        No questions available. Import a JSON file or add a new question to get started.
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
          Save Changes
        </v-btn>
      </div>
    </v-card>

    <v-dialog v-model="showSaveConfirmation" max-width="500px">
      <v-card>
        <v-card-title class="text-h5">Congratulations!</v-card-title>
        <v-card-text>
          You have successfully modified the "{{ fileName }}" validation set.
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
  </div>
</template>


<script>
import { ref, onMounted, computed, onBeforeUnmount, watch, nextTick } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import QuestionEditor from './QuestionEditor/index.vue';
import { loadJsonFile, updateJsonFile } from '@/services/fileService';
import { answerGeneratorService, factGeneratorService } from '@/services/generatorService';
import { http } from '@/plugins/axios';
import { apiKeyService } from '@/services/apiKeyService';

export default {
  name: 'ModifyValidationSet',
  components: { 
    QuestionEditor,
  },
  setup() {
    const router = useRouter();
    const route = useRoute();
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
    const selectedAnswerModel = ref('');
    const selectedFactModel = ref('');
    const isComponentMounted = ref(false);
    const importedFiles = ref([]);
    const fileInputRef = ref(null);
    const isLoading = ref(false);

    const triggerFileInput = () => {
      fileInputRef.value.click();
    };

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

    const answerModelOptions = computed(() => [
      { title: 'Select a model', value: '', disabled: true },
      { title: 'GPT-4', value: 'gpt-4', disabled: !apiKeyAvailability.value.openai },
      { title: 'GPT-4o', value: 'gpt-4o', disabled: !apiKeyAvailability.value.openai },
      { title: 'Mistral Large', value: 'mistral/mistral-large-latest', disabled: !apiKeyAvailability.value.mistral },
    ]);

    const factModelOptions = computed(() => [
      { title: 'Select a model', value: '', disabled: true },
      { title: 'GPT-4', value: 'gpt-4', disabled: !apiKeyAvailability.value.openai },
      { title: 'GPT-4o', value: 'gpt-4o', disabled: !apiKeyAvailability.value.openai },
      { title: 'Mistral Large', value: 'mistral/mistral-large-latest', disabled: !apiKeyAvailability.value.mistral },
    ]);

    const loadExistingValidationSet = async () => {
      try {
        const fileData = JSON.parse(route.query.file);
        fileName.value = fileData.name;
        
        const response = await http.get(`validation-set/${encodeURIComponent(fileName.value)}`);
        if (!response) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = response.data;
        qa.value = data.items.map(formatQaItem);
        originalQa.value = JSON.parse(JSON.stringify(qa.value));
        hasUnsavedChanges.value = false;
      } catch (error) {
        console.error('Error loading validation set:', error);
        alert('Error loading validation set. Please try again.');
      }
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

    const loadFile = async (event) => {
      const files = event.target.files;
      if (!files.length) return;

      isLoading.value = true;
      
      try {
        for (let file of files) {
          if (importedFiles.value.includes(file.name)) {
            alert(`File "${file.name}" has already been imported.`);
            continue;
          }

          const data = await loadJsonFile(file);
          let normalizedData = data.items || [];

          const newQuestions = normalizedData.map(item => ({
            ...formatQaItem(item),
            sourceFile: file.name
          }));
          qa.value = [...qa.value, ...newQuestions];
          importedFiles.value.push(file.name);
        }
        
        hasUnsavedChanges.value = true;
        await nextTick();
      } catch (error) {
        console.error('Error loading file:', error);
        alert(`Error loading file: ${error.message}`);
      } finally {
        isLoading.value = false;
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
    };

    const updateQuestions = (newQuestions) => {
      qa.value = newQuestions;
      hasUnsavedChanges.value = true;
    };

    const toggleQuestionForm = () => {
      showQuestionForm.value = !showQuestionForm.value;
      if (!showQuestionForm.value) newQuestionText.value = '';
    };

    const addNewQuestion = () => {
      if (newQuestionText.value.trim()) {
        qa.value.push({
          question: { text: newQuestionText.value.trim() },
          answers: { items: [] },
          facts: { items: [] }
        });
        newQuestionText.value = '';
        showQuestionForm.value = false;
        hasUnsavedChanges.value = true;
      }
    };

    const generateAnswers = async () => {
      isGeneratingAll.value = true;
      try {
        console.log(`Generating answers with model: ${selectedAnswerModel.value}`);
        const updatedQuestions = await answerGeneratorService.generateAnswers(qa.value, selectedAnswerModel.value);
        qa.value = qa.value.map((q, index) => ({
          ...q,
          answers: {
            items: [...(q.answers?.items || []), ...(updatedQuestions[index].answers?.items || [])]
          }
        }));
        hasUnsavedChanges.value = true;
        alert('Answers generated successfully!');
      } catch (error) {
        console.error('Error generating answers:', error);
        alert('Error generating answers. Please check the console for details.');
      } finally {
        isGeneratingAll.value = false;
      }
    };

    const generateFacts = async () => {
      const invalidQuestions = qa.value.filter(q => 
        q.answers.items.filter(a => a.eval.human === 1).length !== 1
      );

      if (invalidQuestions.length > 0) {
        alert(`Please ensure that each question has exactly one answer. ${invalidQuestions.length} question(s) do not meet this criteria.`);
        return;
      }

      isGeneratingFacts.value = true;
      try {
        console.log(`Generating facts with model: ${selectedFactModel.value}`);
        const questionsWithValidatedAnswers = qa.value.filter(q => 
          q.answers && q.answers.items && q.answers.items.some(a => a.eval && a.eval.human === 1)
        );
        
        if (questionsWithValidatedAnswers.length === 0) {
          alert('No questions with validated answers found. Please validate at least one answer before generating facts.');
          return;
        }

        const updatedQuestions = await factGeneratorService.generateFacts(questionsWithValidatedAnswers, selectedFactModel.value);
        qa.value = qa.value.map(q => {
          const updatedQ = updatedQuestions.find(uq => uq.question.text === q.question.text);
          return updatedQ ? { ...q, facts: updatedQ.facts } : q;
        });
        hasUnsavedChanges.value = true;
        alert('Facts generated successfully!');
      } catch (error) {
        console.error('Error generating facts:', error);
        alert('Error generating facts. Please check the console for details.');
      } finally {
        isGeneratingFacts.value = false;
      }
    };

    const saveQuestions = async () => {
      if (!fileName.value.trim()) {
        alert('Please enter a file name.');
        return;
      }

      const questionsWithoutFacts = qa.value.filter(q => !q.facts || q.facts.items.length === 0);
      if (questionsWithoutFacts.length > 0) {
        alert(`${questionsWithoutFacts.length} question(s) do not have facts generated. Please generate facts for all questions before saving.`);
        return;
      }

      const questionsCount = qa.value.length;
      const factsCount = qa.value.reduce((total, q) => total + (q.facts?.items?.length || 0), 0);
      const newFileName = `${fileName.value.trim()}_Validation_set_Q${questionsCount}_F${factsCount}.json`;

      const dataToSave = {
        items: qa.value.map(q => {
          const { ...questionWithoutSource } = q;
          return {
            ...questionWithoutSource,
            answers: {
              ...questionWithoutSource.answers,
              items: questionWithoutSource.answers.items.map(a => ({
                ...a,
                isGolden: a.eval.human === 1
              }))
            }
          };
        })
      };

      try {
        const result = await updateJsonFile(dataToSave, newFileName, fileName.value);
        if (result.message.includes('successfully')) {
          savedFileName.value = newFileName;
          showSaveConfirmation.value = true;
          hasUnsavedChanges.value = false;
          originalQa.value = JSON.parse(JSON.stringify(qa.value));
          fileName.value = newFileName.split('_Validation_set_')[0];
        } else {
          throw new Error('Failed to save file');
        }
      } catch (error) {
        console.error('Error saving file:', error);
        alert('Error saving file. Please try again.');
      }
    };

    const goHome = () => {
      if (hasUnsavedChanges.value) {
        showUnsavedChangesWarning.value = true;
      } else {
        router.push('/');
      }
    };

    const confirmGoBack = () => hasUnsavedChanges.value ? showUnsavedChangesWarning.value = true : goHome();

    const confirmLeave = () => {
      showUnsavedChangesWarning.value = false;
      hasUnsavedChanges.value = false;
      goHome();
    };

    const cancelLeave = () => showUnsavedChangesWarning.value = false;

    const proceedToExperiment = () => {
      router.push({
        name: 'ExperimentSetup',
        query: { 
          validationSet: fileName.value,
          fullValidationSetName: savedFileName.value
        }
      });
    };

    onMounted(() => {
      loadExistingValidationSet();
      window.addEventListener('beforeunload', (event) => {
        if (hasUnsavedChanges.value) {
          event.preventDefault();
          event.returnValue = '';
        }
      });
      isComponentMounted.value = true;
    });

    onMounted(async () => {
      await fetchApiKeyAvailability();
    });

    onBeforeUnmount(() => window.removeEventListener('beforeunload', () => {}));

    watch([qa, importedFiles], () => {
      hasUnsavedChanges.value = true;
      originalQa.value = JSON.parse(JSON.stringify(qa.value));
    }, { deep: true });

    return {
      qa,
      showQuestionForm,
      newQuestionText,
      isGeneratingAll,
      isGeneratingFacts,
      fileName,
      showSaveConfirmation,
      savedFileName,
      showUnsavedChangesWarning,
      hasUnsavedChanges,
      selectedAnswerModel,
      selectedFactModel,
      answerModelOptions,
      factModelOptions,
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
      isComponentMounted,
      importedFiles,
      fileInputRef,
      isLoading,
      triggerFileInput,
      removeImportedFile,
      apiKeyAvailability,
      proceedToExperiment
    };
  }
};
</script>

<style scoped>
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