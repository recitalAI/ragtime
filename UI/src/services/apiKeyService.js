import { http } from '@/plugins/axios';

export const apiKeyService = {
  async checkApiKeyAvailability() {
    try {
      const response = await http.get('user/api-keys/availability');
      return response.data;
    } catch (error) {
      console.error('Error checking API key availability:', error);
      throw error;
    }
  },

  async refreshApiKeyAvailability() {
    try {
      const response = await http.post('user/api-keys/refresh');
      return response.data;
    } catch (error) {
      console.error('Error refreshing API key availability:', error);
      throw error;
    }
  }
};