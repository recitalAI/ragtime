<template>
  <div class="user-settings page-padding py-7">
    <h2 class="h2-text mb-4">API Key Settings</h2>
    <v-card class="pa-6" style="min-width: 800px">
      <form @submit.prevent="saveSettings">
        <!-- API Keys section -->
        <div class="api-keys-section">
          <h3 class="h3-text mb-4">API Keys</h3>
          <div 
            v-for="(key, index) in apiKeys" 
            :key="index" 
            class="api-key-item mb-4"
          >
            <v-text-field
              :model-value="key.visible ? key.value : maskKey(key.value)"
              @input="updateKeyValue(index, $event)"
              :label="key.name"
              type="text"
              :placeholder="'Enter ' + key.name"
              variant="outlined"
              density="comfortable"
              hide-details
              :readonly="!key.editable"
            >
              <template #append-inner>
                <v-btn
                  icon
                  variant="text"
                  size="small"
                  @click="toggleKeyVisibility(index)"
                  :disabled="key.editable"
                >
                  <v-icon>
                    {{ key.visible ? 'fas fa-eye-slash' : 'fas fa-eye' }}
                  </v-icon>
                </v-btn>
              </template>
            </v-text-field>
            <div class="d-flex mt-2">
              <v-btn
                color="primary-lighten1"
                variant="text"
                size="small"
                class="mr-2"
                @click="toggleKeyEditable(index)"
              >
                <v-icon
                  size="17"
                  start
                >
                  {{key.editable ? 'fas fa-check' : 'fas fa-edit'}}
                </v-icon>
                {{key.editable ? 'Save' : 'Edit'}}
              </v-btn>
              <v-btn
                color="error"
                variant="text"
                size="small"
                class="mr-2"
                @click="removeApiKey(index)"
              >
                <v-icon
                  size="17"
                  start
                >
                  fas fa-trash
                </v-icon>
                Delete
              </v-btn>
            </div>
          </div>
          <div class="add-api-key mt-6">
            <v-select
              v-model="newKeyType"
              :items="keyTypeOptions"
              label="Select API Key Type"
              variant="outlined"
              density="comfortable"
              hide-details
              class="mb-4"
            ></v-select>
            <v-text-field
              v-if="newKeyType === 'custom'"
              v-model="customKeyName"
              label="Custom Key Name"
              placeholder="Enter custom key name"
              variant="outlined"
              density="comfortable"
              hide-details
              class="mb-4"
            ></v-text-field>
            <v-text-field
              v-model="newKeyValue"
              label="API Key Value"
              placeholder="Enter API key value"
              variant="outlined"
              density="comfortable"
              hide-details
              class="mb-4"
            ></v-text-field>
            <v-btn
              color="primary"
              :disabled="!newKeyType || !newKeyValue || (newKeyType === 'custom' && !customKeyName)"
              @click="addApiKey"
            >
              Add API Key
            </v-btn>
          </div>
        </div>

        <v-btn
          color="primary"
          type="submit"
          class="mt-6"
        >
          Save Changes
        </v-btn>
      </form>
    </v-card>
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
import { ref, onMounted } from 'vue';
import { userService } from '@/services/userService';
import { apiKeyService } from '@/services/apiKeyService';

export default {
  name: 'UserSettings',
  setup() {
    const apiKeys = ref([]);
    const newKeyType = ref('');
    const customKeyName = ref('');
    const newKeyValue = ref('');
    const message = ref('');
    const showSnackbar = ref(false);
    const snackbarColor = ref('');
    const deletedKeys = ref([]);

    const keyTypeOptions = [
      { value: '', title: 'Select API Key Type' },
      { value: 'OPENAI_API_KEY', title: 'OpenAI API Key' },
      { value: 'MISTRAL_API_KEY', title: 'Mistral API Key' },
      { value: 'custom', title: 'Custom API Key' },
    ];

    onMounted(async () => {
      await fetchApiKeys();
    });

    const fetchApiKeys = async () => {
      try {
        const keysData = await userService.getApiKeys();
        const defaultKeys = [];
        
        apiKeys.value = defaultKeys.map(keyName => {
          const existingKey = keysData.find(key => key.name === keyName);
          return {
            name: keyName,
            value: existingKey ? existingKey.value : '',
            visible: false,
            editable: false
          };
        });

        // Add custom keys
        keysData.forEach(key => {
          if (!defaultKeys.includes(key.name)) {
            apiKeys.value.push({
              name: key.name,
              value: key.value,
              visible: false,
              editable: false
            });
          }
        });
      } catch (error) {
        showMessage('Error fetching API keys. Please try again.', 'error');
      }
    };

    const toggleKeyVisibility = (index) => {
      if (!apiKeys.value[index].editable) {
        apiKeys.value[index].visible = !apiKeys.value[index].visible;
      }
    };

    const toggleKeyEditable = (index) => {
      const key = apiKeys.value[index];
      if (key.editable) {
        // Save changes
        key.editable = false;
        key.visible = false;
      } else {
        // Enter edit mode
        key.editable = true;
        key.visible = true;
      }
    };

    const updateKeyValue = (index, event) => {
      if (apiKeys.value[index].editable) {
        if (event instanceof InputEvent && event.target) {
          apiKeys.value[index].value = event.target.value;
        } else if (typeof event === 'string') {
          apiKeys.value[index].value = event;
        }
      }
    };

    const addApiKey = () => {
      const keyName = newKeyType.value === 'custom' ? customKeyName.value : newKeyType.value;
      apiKeys.value.push({
        name: keyName,
        value: newKeyValue.value,
        visible: false,
        editable: false
      });
      newKeyType.value = '';
      customKeyName.value = '';
      newKeyValue.value = '';
    };

    const removeApiKey = (index) => {
      const removedKey = apiKeys.value[index];
      if (removedKey.value) {
        deletedKeys.value.push(removedKey.name);
      }
      apiKeys.value.splice(index, 1);
    };

    const saveSettings = async () => {
      try {
        // Filter out keys with empty values
        const keysToSave = apiKeys.value.filter(key => key.value !== '');
        
        // Save all keys to database and .env file
        await userService.saveApiKeys(keysToSave.map(key => ({
          name: key.name,
          value: key.value
        })), deletedKeys.value);
        
        // Refresh API key availability
        await apiKeyService.refreshApiKeyAvailability();
        
        showMessage('API keys saved and refreshed successfully!', 'success');
        deletedKeys.value = []; // Clear the deleted keys array after saving
        
        // Fetch the updated keys
        await fetchApiKeys();
      } catch (error) {
        showMessage('Error saving API keys. Please try again.', 'error');
      }
    };

    const showMessage = (msg, type) => {
      message.value = msg;
      snackbarColor.value = type === 'success' ? 'success' : 'error';
      showSnackbar.value = true;
    };

    const maskKey = (key) => {
      if (!key || typeof key !== 'string') return '';
      return `${key.slice(0, 4)}${'.'.repeat(4)}${key.slice(-4)}`;
    };

    return {
      apiKeys,
      newKeyType,
      customKeyName,
      newKeyValue,
      message,
      showSnackbar,
      snackbarColor,
      keyTypeOptions,
      saveSettings,
      addApiKey,
      removeApiKey,
      toggleKeyVisibility,
      toggleKeyEditable,
      updateKeyValue,
      maskKey
    };
  }
};
</script>

<style lang="scss" scoped>
.user-settings {
  max-width: 800px;
  margin: 0 auto;
}

.api-keys-section {
  margin-top: 20px;
}

.api-key-item {
  margin-bottom: 20px;
}

.add-api-key {
  margin-top: 30px;
}
</style>