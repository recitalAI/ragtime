import { http } from '@/plugins/axios';

// The hardcoded model lists (availableLLMs / groupedLLMs / openAIModels /
// mistralAIModels) moved server-side in sub-step 5.3: /api/available-models
// is the single source of truth, consumed through services/modelCatalog.js.

export const apiKeyService = {
  async checkApiKeyAvailability() {
    const response = await http.get('user/api-keys/availability');
    return response.data;
  },

  async refreshApiKeyAvailability() {
    const response = await http.post('user/api-keys/refresh');
    return response.data;
  },
};
