<template>
  <span class="format-help d-inline-flex align-center">
    <!-- Styled like the sibling action buttons (primary / outlined / rounded)
         instead of a bare icon, and labelled so it is obvious it opens a
         dialog. -->
    <v-tooltip location="top" text="Click to see the expected file format">
      <template #activator="{ props: tip }">
        <v-btn
          v-bind="tip"
          color="primary"
          variant="outlined"
          rounded
          class="mr-3"
          @click="dialog = true"
        >
          <v-icon size="17" start>
            fa-solid fa-circle-info
          </v-icon>
          Expected format
        </v-btn>
      </template>
    </v-tooltip>

    <v-btn
      v-if="showTemplateButton"
      color="primary"
      variant="outlined"
      rounded
      class="mr-3"
      @click="$emit('download-template')"
    >
      <v-icon size="17" start>
        fa-solid fa-file-excel
      </v-icon>
      Excel template
    </v-btn>

    <v-dialog
      v-model="dialog"
      max-width="900"
      scrollable
      class="format-help-dialog"
      content-class="format-help-content"
    >
      <v-card>
        <v-card-title class="h2-text primary--text pt-5 px-6 format-help-title">
          {{ spec.title }}
        </v-card-title>
        <v-card-text class="px-6">
          <p class="mb-4">
            Accepted file types:
            <strong>.xlsx</strong>{{ spec.jsonNote ? ', .csv and .json' : ' and .csv' }}.
          </p>

          <p class="mb-2"><strong>Columns</strong></p>
          <v-table density="comfortable" class="mb-4 format-table">
            <thead>
              <tr>
                <th style="width: 200px;">Column</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="col in spec.columns" :key="col.name">
                <td class="font-weight-medium text-no-wrap">
                  <code>{{ col.name }}</code>
                  <span v-if="col.required" class="text-error ml-1">*</span>
                </td>
                <td>{{ col.help }}</td>
              </tr>
            </tbody>
          </v-table>
          <p class="text-caption mb-5"><span class="text-error">*</span> required</p>

          <template v-if="spec.factsExample">
            <p class="mb-2"><strong>Facts cell — accepted separators</strong></p>
            <p class="text-body-2 mb-2">
              Facts can be separated by a semicolon, by a line break
              (Alt+Enter in Excel), or written as a list between brackets:
            </p>
            <pre class="format-code mb-5">{{ spec.factsExample }}</pre>
          </template>

          <template v-if="spec.jsonNote">
            <p class="mb-2"><strong>JSON is also accepted</strong></p>
            <pre class="format-code mb-5">{{ jsonExample }}</pre>
          </template>

          <p class="mb-2"><strong>Tip</strong></p>
          <p class="text-body-2 mb-2">
            Use the “Excel template” button to download a ready-to-fill file
            with the right columns and one example row.
          </p>
        </v-card-text>
        <v-card-actions class="px-6 pb-5">
          <v-btn
            color="primary"
            variant="outlined"
            rounded
            @click="$emit('download-template')"
          >
            <v-icon size="17" start>
              fa-solid fa-file-excel
            </v-icon>
            Excel template
          </v-btn>
          <v-spacer />
          <v-btn color="primary" variant="flat" rounded @click="dialog = false">
            Close
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </span>
</template>

<script>
import { ref, computed } from 'vue';

export default {
  name: 'FormatHelp',
  props: {
    // A spec object from services/spreadsheetFormats.js
    spec: { type: Object, required: true },
    showTemplateButton: { type: Boolean, default: true },
  },
  emits: ['download-template'],
  setup() {
    const dialog = ref(false);
    const jsonExample = computed(() => `[
  { "question": "a question", "answer": "an answer" },
  { "question": "another question", "answer": "another answer" }
]`);
    return { dialog, jsonExample };
  },
};
</script>

<!-- Not scoped: assets/scss/03-modules/vuetify/_dialog.scss caps every
     .v-dialog at 400px, which overrides the max-width prop. This guide needs
     the full width, so it opts out explicitly. -->
<style>
/* assets/scss/03-modules/vuetify/_dialog.scss caps EVERY .v-dialog at 400px.
   In Vuetify 3 the root overlay element carries `class` while the inner box
   carries `content-class`, so the cap sits on the PARENT — widening only the
   child cannot escape it. Both are overridden here. */
.v-overlay.format-help-dialog,
.v-dialog.format-help-dialog {
  max-width: none !important;
  width: 100% !important;
}

.format-help-dialog .v-overlay__content,
.v-overlay__content.format-help-content {
  max-width: 900px !important;
  width: calc(100vw - 48px) !important;
  margin: 24px auto !important;
}

/* v-card-title truncates with an ellipsis by default ("Validation set file fo…") */
.format-help-title {
  white-space: normal !important;
  overflow: visible !important;
  text-overflow: clip !important;
}

/* the global rule also forces 10px padding on any dialog card */
.format-help-dialog .v-overlay__content > .v-card,
.v-overlay__content.format-help-content > .v-card {
  padding: 0 !important;
  width: 100%;
}
</style>

<style scoped>
.format-code {
  background: #f5f5f5;
  border-radius: 4px;
  padding: 12px;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  overflow-x: auto;
}

.format-table code {
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 12px;
}

.format-table td {
  vertical-align: top;
  padding-top: 10px !important;
  padding-bottom: 10px !important;
}
</style>
