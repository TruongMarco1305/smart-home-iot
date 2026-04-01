import { apiClient } from './client';
import type { Device, CreateDevicePayload } from '../types';

export const devicesApi = {
  list: async (): Promise<Device[]> => {
    const { data } = await apiClient.get<Device[]>('/devices');
    return data;
  },

  create: async (payload: CreateDevicePayload): Promise<Device> => {
    const { data } = await apiClient.post<Device>('/devices', payload);
    return data;
  },

  command: async (deviceId: string, state: 'ON' | 'OFF'): Promise<Device> => {
    const { data } = await apiClient.patch<Device>(
      `/devices/${deviceId}/command`,
      { state },
    );
    return data;
  },
};
