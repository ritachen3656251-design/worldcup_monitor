import axios from 'axios';
import type { CardsResponse, CategoriesResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  /**
   * Get hot topic cards for discovery feed.
   */
  getCards: async (
    category: string = '全部',
    limit: number = 20,
    offset: number = 0,
  ): Promise<CardsResponse> => {
    const response = await apiClient.get<CardsResponse>('/api/cards', {
      params: { category, limit, offset },
    });
    return response.data;
  },

  /**
   * Get new cards since a timestamp (for polling).
   */
  getNewCards: async (since: string, category: string = '全部'): Promise<CardsResponse> => {
    const response = await apiClient.get<CardsResponse>('/api/cards/new', {
      params: { since, category },
    });
    return response.data;
  },

  /**
   * Get card detail page.
   */
  getCardDetail: async (cardId: number): Promise<any> => {
    const response = await apiClient.get(`/api/cards/${cardId}/detail`);
    return response.data;
  },

  /**
   * Get channel categories with counts.
   */
  getCategories: async (): Promise<CategoriesResponse> => {
    const response = await apiClient.get<CategoriesResponse>('/api/categories');
    return response.data;
  },

  /**
   * Health check.
   */
  healthCheck: async (): Promise<any> => {
    const response = await apiClient.get('/api/health');
    return response.data;
  },
};

export default apiClient;
