import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface SourceContent {
  id: number;
  platform: string;
  url: string;
  title: string;
  cleaned_text: string;
  author: string | null;
  published_at: string;
  interaction_count: number;
  scraped_at: string;
}

export const api = {
  // Get raw content list (Spec 1)
  getCards: async (limit: number = 20): Promise<SourceContent[]> => {
    const response = await apiClient.get(`/api/cards/`, { params: { limit } });
    return response.data;
  },

  // Health check
  healthCheck: async (): Promise<{ status: string; message: string }> => {
    const response = await apiClient.get('/api/health/');
    return response.data;
  },
};

export default apiClient;
