<template>
  <!-- Shown when an import fails: states what went wrong AND what the file
       should look like, instead of a bare "invalid file" snackbar. -->
  <v-dialog :model-value="modelValue" max-width="640" @update:model-value="$emit('update:modelValue', $event)">
    <v-card>
      <v-card-title class="h2-text">Import failed</v-card-title>
      <v-card-text>
        <v-alert type="error" variant="tonal" class="mb-4">
          {{ message }}
        </v-alert>

        <ul v-if="details && details.length" class="mb-4 ml-4">
          <li v-for="(d, i) in details" :key="i" class="text-body-2">{{ d }}</li>
        </ul>

        <template v-if="spec">
          <p class="mb-2"><strong>Expected format</strong></p>
          <v-table density="compact" class="mb-2">
            <tbody>
              <tr v-for="col in spec.columns" :key="col.name">
                <td class="font-weight-medium" style="white-space: nowrap; vertical-align: top;">
                  {{ col.name }}<span v-if="col.required" class="text-error">*</span>
                </td>
                <td>{{ col.help }}</td>
              </tr>
            </tbody>
          </v-table>
          <p class="text-caption"><span class="text-error">*</span> required</p>
        </template>
      </v-card-text>
      <v-card-actions>
        <v-btn v-if="spec" variant="text" @click="$emit('download-template')">
          <v-icon size="x-small" class="mr-1">fas fa-download</v-icon>
          Download template
        </v-btn>
        <v-spacer />
        <v-btn color="primary" variant="flat" rounded @click="$emit('update:modelValue', false)">Close</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: 'FormatErrorDialog',
  props: {
    modelValue: { type: Boolean, default: false },
    message: { type: String, default: '' },
    details: { type: Array, default: () => [] },
    spec: { type: Object, default: null },
  },
  emits: ['update:modelValue', 'download-template'],
};
</script>
