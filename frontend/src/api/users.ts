import { apiClient } from './client';
import type { User, CreateUserPayload, UpdateUserPayload } from '../types';

export const usersApi = {
  list: async (): Promise<User[]> => {
    const { data } = await apiClient.get<User[]>('/users');
    return data;
  },

  get: async (userId: string): Promise<User> => {
    const { data } = await apiClient.get<User>(`/users/${userId}`);
    return data;
  },

  create: async (payload: CreateUserPayload): Promise<User> => {
    const { data } = await apiClient.post<User>('/users', payload);
    return data;
  },

  update: async (userId: string, payload: UpdateUserPayload): Promise<User> => {
    const { data } = await apiClient.patch<User>(`/users/${userId}`, payload);
    return data;
  },
};
