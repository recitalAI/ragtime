<template>
  <v-card class="mt-4 pa-4">
    <v-card-title>Models used for Answer generation</v-card-title>
    <v-card-text>
      <div class="providers-container d-flex flex-wrap">
        <v-btn
          v-for="(provider, providerName) in grouped"
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
              v-for="model in grouped[activeProvider]"
              :key="model"
              cols="12"
              sm="6"
              md="4"
            >
              <v-checkbox
                v-model="selectedLLMsModel"
                :label="model"
                :value="model"
                :disabled="isModelDisabled(activeProvider, model) || (evaluateChunks && selectedLLMs.length > 0 && !selectedLLMs.includes(model))"
                density="compact"
              >
              <template v-slot:label>
                <div style="display: flex; flex-direction: column; width: 100%; padding: 10px;">
                  {{ model }}
                  <span v-if="modelPriceTag(model)" class="text-caption text-medium-emphasis" style="margin-top: 2px;">
                    {{ modelPriceTag(model) }}
                  </span>
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
                v-model="selectedCustomLLMsModel"
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

          <!-- Reasoning controls for any selected reasoning-capable model.
               Togglable models get a switch (default off); always-on models
               show an informational note instead of a dead control. Models
               that accept an effort level get a low/medium/high selector. -->
          <v-row v-if="reasoningModels.length" class="mt-2">
            <v-col cols="12">
              <div class="text-subtitle-2 mb-1">Reasoning</div>
              <div v-for="rm in reasoningModels" :key="rm.name" class="mb-2">
                <div class="d-flex align-center flex-wrap">
                  <v-switch
                    v-if="rm.supports_reasoning_toggle"
                    :model-value="reasoningChoices[rm.name] || false"
                    @update:model-value="val => setReasoning(rm.name, val)"
                    :label="`${rm.title || rm.name} — enable reasoning`"
                    color="primary"
                    density="compact"
                    hide-details
                    class="ma-0 pa-0 mr-4"
                  />
                  <span v-else class="text-caption text-medium-emphasis mr-4">
                    {{ rm.title || rm.name }} — {{ rm.reasoning_note || 'reasoning always on' }}
                  </span>

                  <!-- Effort selector: shown when the model supports it and,
                       for togglable models, only while reasoning is enabled. -->
                  <v-select
                    v-if="rm.supports_reasoning_effort && effortActive(rm)"
                    :model-value="reasoningEffortChoices[rm.name] || 'medium'"
                    @update:model-value="val => setEffort(rm.name, val)"
                    :items="effortOptions"
                    label="Effort"
                    density="compact"
                    variant="outlined"
                    hide-details
                    style="max-width: 160px;"
                    class="mt-0"
                  />
                </div>
              </div>
            </v-col>
          </v-row>
        </div>
      </v-expand-transition>
    </v-card-text>
  </v-card>
</template>

<script>
import { computed } from 'vue';
import { isModelDisabled as catalogModelDisabled, formatModelPrice } from '@/services/modelCatalog';

export default {
  name: 'ModelSelection',
  props: {
    // {provider: [modelName, ...]} — built-ins from the unified catalog.
    grouped: {
      type: Object,
      required: true,
    },
    // Built-in entries with required_key, for generic availability checks.
    builtins: {
      type: Array,
      required: true,
    },
    customizedLLMs: {
      type: Array,
      required: true,
    },
    activeProvider: {
      type: String,
      default: null,
    },
    selectedLLMs: {
      type: Array,
      required: true,
    },
    selectedCustomLLMs: {
      type: Array,
      required: true,
    },
    evaluateChunks: {
      type: Boolean,
      default: false,
    },
    availability: {
      type: Object,
      required: true,
    },
    // { modelName: bool } — user's per-model reasoning choice (default off).
    reasoningChoices: {
      type: Object,
      default: () => ({}),
    },
    // { modelName: 'low'|'medium'|'high' } — per-model effort (default medium).
    reasoningEffortChoices: {
      type: Object,
      default: () => ({}),
    },
  },
  emits: ['update:activeProvider', 'update:selectedLLMs', 'update:selectedCustomLLMs', 'update:reasoningChoices', 'update:reasoningEffortChoices'],
  setup(props, { emit }) {
    // Reasoning-capable entries among the currently selected models. Built-in
    // catalog rows carry reasoning/supports_reasoning_toggle/reasoning_note;
    // customized reasoning models expose the same fields.
    const reasoningModels = computed(() => {
      const selected = new Set([...props.selectedLLMs, ...props.selectedCustomLLMs]);
      const rows = [
        ...props.builtins,
        ...props.customizedLLMs,
      ];
      return rows.filter(m => selected.has(m.name) && (m.reasoning || m.supports_reasoning_toggle || m.reasoning_note));
    });

    const setReasoning = (modelName, val) => {
      emit('update:reasoningChoices', { ...props.reasoningChoices, [modelName]: val });
    };

    const effortOptions = [
      { title: 'Low', value: 'low' },
      { title: 'Medium', value: 'medium' },
      { title: 'High', value: 'high' },
    ];

    const setEffort = (modelName, val) => {
      emit('update:reasoningEffortChoices', { ...props.reasoningEffortChoices, [modelName]: val });
    };

    // Effort applies when reasoning is actually on: always-on models (no
    // toggle) always show it; togglable models only while their switch is on.
    const effortActive = (rm) => {
      if (!rm.supports_reasoning_toggle) return true;
      return !!props.reasoningChoices[rm.name];
    };

    // Price tag for a model name, looked up in the builtins catalog rows.
    const modelPriceTag = (modelName) => {
      const meta = props.builtins.find(m => m.name === modelName);
      return meta ? formatModelPrice(meta.pricing) : '';
    };

    const toggleProvider = (providerName) => {
      if (props.activeProvider === providerName) {
        emit('update:activeProvider', null);
      } else {
        emit('update:activeProvider', providerName);
      }
    };

    const getSelectedModelsCount = (providerName) => {
      return props.selectedLLMs.filter(model => props.grouped[providerName].includes(model)).length;
    };

    // Generic replacement for the per-provider hardcoded check: a model is
    // disabled when its required_key is not configured (providerName kept
    // for signature parity with the original).
    const isModelDisabled = (providerName, modelName) => {
      return catalogModelDisabled(props.builtins, props.availability, modelName);
    };

    const selectedLLMsModel = computed({
      get: () => props.selectedLLMs,
      set: (value) => emit('update:selectedLLMs', value),
    });
    const selectedCustomLLMsModel = computed({
      get: () => props.selectedCustomLLMs,
      set: (value) => emit('update:selectedCustomLLMs', value),
    });

    return {
      toggleProvider,
      getSelectedModelsCount,
      isModelDisabled,
      selectedLLMsModel,
      selectedCustomLLMsModel,
      reasoningModels,
      setReasoning,
      effortOptions,
      setEffort,
      effortActive,
      modelPriceTag,
    };
  },
};
</script>

<style scoped>
.providers-container {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.v-checkbox ::v-deep(.v-label) {
  opacity: 1;
}
</style>
