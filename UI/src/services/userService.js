import { http } from '@/plugins/axios';

export const userService = {
  async getApiKeys() {
    try {
      const response = await http.get('user/api-keys');
      return response.data;
    } catch (error) {
      console.error('Error fetching API keys:', error);
      throw error;
    }
  },

  async saveApiKeys(apiKeys, deletedKeys = []) {
    try {
      const response = await http.post('user/api-keys', { apiKeys, deletedKeys });
      return response.data;
    } catch (error) {
      console.error('Error saving API keys:', error);
      throw error;
    }
  },

  async getDefaultApiKey(keyName) {
    try {
      const response = await http.get(`user/api-keys/default/${keyName}`);
      return response.data.value;
    } catch (error) {
      console.error('Error fetching default API key:', error);
      throw error;
    }
  }
};