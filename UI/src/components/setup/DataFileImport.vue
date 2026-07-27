<template>
  <div>
    <v-file-input
      label="Import Data File (CSV or XLSX)"
      accept=".csv,.xlsx,.xls"
      prepend-icon="fa-solid fa-sheet-plastic"
      @change="$emit('file-change', $event)"
      :clearable="true"
      @click:clear="$emit('clear')"
    />
    <!-- Explains the column convention (question / answer / model_name /
         chunk_*) and provides a ready-to-fill template. Placed on its own
         row so the buttons match the other action buttons instead of being
         squeezed next to the input. -->
    <div class="d-flex align-center flex-wrap mb-2">
      <FormatHelp
        :spec="experimentDataFormat"
        @download-template="downloadTemplate"
      />
    </div>
  </div>
</template>

<script>
import FormatHelp from '@/components/elements/general/FormatHelp.vue';
import { EXPERIMENT_DATA_FORMAT, downloadExperimentDataTemplate } from '@/services/spreadsheetFormats';

export default {
  components: { FormatHelp },
  setup() {
    return {
      experimentDataFormat: EXPERIMENT_DATA_FORMAT,
      downloadTemplate: () => downloadExperimentDataTemplate(5),
    };
  },
  name: 'DataFileImport',
  emits: ['file-change', 'clear'],
};
</script>
