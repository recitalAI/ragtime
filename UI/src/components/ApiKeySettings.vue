<template>
  <div class="user-settings page-padding py-7">
    <h2 class="h2-text mb-4">
      <slot name="title">API Key Settings</slot>
    </h2>
    <v-card class="pa-6" style="min-width: 800px">
      <form @submit.prevent="saveSettings">
        <div class="api-keys-section">
          <h3 class="h3-text mb-4">
            <slot name="api-keys-title">API Keys</slot>
          </h3>
          <div 
            v-for="(key, index) in apiKeys" 
            :key="index" 
            class="api-key-item mb-4"
          >
            <slot name="api-key-field" :key="key" :index="index" :toggleVisibility="() => toggleKeyVisibility(index)" :updateKeyValue="updateKeyValue">
              <v-text-field
                :model-value="key.value"
                @input="(newValue) => updateKeyValue(index, newValue)"
                :label="key.name"
                :type="key.visible ? 'text' : 'password'"
                :placeholder="'Enter ' + key.name"
                variant="outlined"
                density="comfortable"
                hide-details
              >
                <template #append-inner>
                  <v-btn
                    icon
                    variant="text"
                    size="small"
                    @click="toggleKeyVisibility(index)"
                  >
                    <v-icon>
                      {{ key.visible ? 'fas fa-eye-slash' : 'fas fa-eye' }}
                    </v-icon>
                  </v-btn>
                </template>
              </v-text-field>
            </slot>
            <div class="d-flex mt-2">
              <slot name="api-key-actions" :key="key" :index="index" :toggleVisibility="() => toggleKeyVisibility(index)" :removeKey="() => removeApiKey(index)">
                <v-btn
                  color="primary"
                  variant="text"
                  size="small"
                  class="mr-2"
                  @click="toggleKeyVisibility(index)"
                >
                  <v-icon size="17" start>
                    {{key.visible ? 'fas fa-eye-slash' : 'fas fa-eye'}}
                  </v-icon>
                  {{key.visible ? 'Hide' : 'Show'}}
                </v-btn>
                <v-btn
                  color="error"
                  variant="text"
                  size="small"
                  class="mr-2"
                  @click="removeApiKey(index)"
                >
                  <v-icon size="17" start>
                    fas fa-trash
                  </v-icon>
                  Delete
                </v-btn>
              </slot>
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
            />
            <v-text-field
              v-if="newKeyType === 'custom'"
              v-model="customKeyName"
              label="Custom Key Name"
              placeholder="Enter custom key name"
              variant="outlined"
              density="comfortable"
              hide-details
              class="mb-4"
            />
            <v-text-field
              v-model="newKeyValue"
              label="API Key Value"
              placeholder="Enter API key value"
              variant="outlined"
              density="comfortable"
              hide-details
              class="mb-4"
            />
            <v-btn
              color="primary"
              :disabled="!newKeyType || !newKeyValue"
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

export default {
  name: 'ApiKeySettings',
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
      { value: 'HUGGINGFACE_API_KEY', title: 'Hugging Face API Key' },
      { value: 'custom', title: 'Custom API Key' },
    ];

    onMounted(async () => {
      await fetchApiKeys();
    });

    const fetchApiKeys = async () => {
      try {
        const keysData = await userService.getApiKeys();
        const defaultKeys = ['OPENAI_API_KEY', 'MISTRAL_API_KEY', 'HUGGINGFACE_API_KEY'];
        
        apiKeys.value = defaultKeys.map(keyName => {
          const existingKey = keysData.find(key => key.name === keyName);
          return {
            name: keyName,
            value: existingKey ? existingKey.value : '',
            visible: false
          };
        });

        // Add any custom keys that are not in the default list
        keysData.forEach(key => {
          if (!defaultKeys.includes(key.name)) {
            apiKeys.value.push({
              name: key.name,
              value: key.value,
              visible: false
            });
          }
        });
      } catch (error) {
        showMessage('Error fetching API keys. Please try again.', 'error');
      }
    };

    const toggleKeyVisibility = (index) => {
      apiKeys.value[index].visible = !apiKeys.value[index].visible;
    };

    const updateKeyValue = (index, newValue) => {
      apiKeys.value[index].value = newValue;
    };

    const addApiKey = () => {
      const keyName = newKeyType.value === 'custom' ? customKeyName.value : newKeyType.value;
      apiKeys.value.push({
        name: keyName,
        value: newKeyValue.value,
        visible: false
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
        const keysToSave = apiKeys.value.filter(key => key.value !== '');
        await userService.saveApiKeys(keysToSave.map(key => ({
          name: key.name,
          value: key.value
        })), deletedKeys.value);
        
        showMessage('API keys saved successfully!', 'success');
        deletedKeys.value = [];
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
      updateKeyValue
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