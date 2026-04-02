import { apiClient } from './client';

export const gatewayApi = {
  getCollectionStatus: async (): Promise<{ collecting: boolean }> => {
    const { data } = await apiClient.get<{ collecting: boolean }>(
      '/gateway/collection',
    );
    return data;
  },

  setCollectionStatus: async (
    collecting: boolean,
  ): Promise<{ collecting: boolean }> => {
    const { data } = await apiClient.post<{ collecting: boolean }>(
      '/gateway/collection',
      { collecting },
    );
    return data;
  },
};
