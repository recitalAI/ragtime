import { http } from '@/plugins/axios';

export const logService = {
  async getLiveLogs(lastTimestamp) {
    try {
      const response = await http.get('live-logs', { params: { lastTimestamp } });
      return response.data;
    } catch (error) {
      console.error('Error fetching live logs:', error);
      throw error;
    }
  },
};