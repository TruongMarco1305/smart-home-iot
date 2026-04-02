import { apiClient } from './client';
import type { Feed, CreateFeedPayload } from '../types';

export const feedsApi = {
  list: async (): Promise<Feed[]> => {
    const { data } = await apiClient.get<Feed[]>('/feeds');
    return data;
  },

  create: async (payload: CreateFeedPayload): Promise<Feed> => {
    const { data } = await apiClient.post<Feed>('/feeds', payload);
    return data;
  },

  delete: async (feedId: string): Promise<void> => {
    await apiClient.delete(`/feeds/${feedId}`);
  },
};
