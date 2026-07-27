import { http } from '@/plugins/axios';

export const userService = {
  async getApiKeys() {
    const response = await http.get('user/api-keys');
    return response.data;
  },

  async saveApiKeys(apiKeys, deletedKeys = []) {
    const response = await http.post('user/api-keys', { apiKeys, deletedKeys });
    return response.data;
  },

  async getDefaultApiKey(keyName) {
    const response = await http.get(`user/api-keys/default/${keyName}`);
    return response.data.value;
  }
};