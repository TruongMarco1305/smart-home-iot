import { apiClient } from './client';
import type { LoginRequest, TokenResponse, User } from '../types';

export const authApi = {
  login: async (payload: LoginRequest): Promise<TokenResponse> => {
    const { data } = await apiClient.post<TokenResponse>('/auth/login', payload);
    return data;
  },

  me: async (): Promise<User> => {
    const { data } = await apiClient.get<User>('/auth/me');
    return data;
  },
};
