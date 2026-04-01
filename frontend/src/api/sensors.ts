import { apiClient } from './client';
import type { SensorReading, SensorHistoryResponse } from '../types';
import { useAuthStore } from '../stores/authStore';

export const sensorsApi = {
  latest: async (): Promise<SensorReading> => {
    const { data } = await apiClient.get<SensorReading>('/sensors/latest');
    return data;
  },

  history: async (
    page = 1,
    limit = 100,
    deviceId?: string,
  ): Promise<SensorHistoryResponse> => {
    const params: Record<string, unknown> = { page, limit };
    if (deviceId) params.device_id = deviceId;
    const { data } = await apiClient.get<SensorHistoryResponse>(
      '/sensors/history',
      { params },
    );
    return data;
  },
};

/**
 * Opens a fetch-based SSE connection to /api/sensors/stream.
 * Calls onReading for every parsed event.
 * Returns a cancel function.
 */
export function startSensorStream(
  onReading: (reading: SensorReading) => void,
  onError?: (err: unknown) => void,
): () => void {
  const controller = new AbortController();

  (async () => {
    const token = useAuthStore.getState().token;
    try {
      const res = await fetch('/api/sensors/stream', {
        headers: { Authorization: `Bearer ${token}` },
        signal: controller.signal,
      });

      if (!res.ok || !res.body) {
        onError?.(new Error(`SSE connect failed: ${res.status}`));
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop() ?? '';
        for (const chunk of parts) {
          const line = chunk.replace(/^data:\s*/, '').trim();
          if (line) {
            try {
              onReading(JSON.parse(line) as SensorReading);
            } catch {
              // skip malformed event
            }
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        onError?.(err);
      }
    }
  })();

  return () => controller.abort();
}
