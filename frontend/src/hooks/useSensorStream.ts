import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { startSensorStream } from '../api/sensors';
import { gatewayApi } from '../api/gateway';
import { useSensorStore } from '../stores/sensorStore';
import { useAuthStore } from '../stores/authStore';

/**
 * Opens the SSE sensor stream while the user is authenticated.
 * Also fetches initial device liveness and listens for watchdog sentinels.
 * When the watchdog reports an online-state change, the ['devices'] query is
 * immediately invalidated so device cards reflect the new is_online flag
 * without waiting for the next 10 s poll.
 */
export function useSensorStream() {
  const token = useAuthStore((s) => s.token);
  const setLatest = useSensorStore((s) => s.setLatest);
  const setConnected = useSensorStore((s) => s.setConnected);
  const setDeviceOnline = useSensorStore((s) => s.setDeviceOnline);
  const qc = useQueryClient();

  // Fetch initial device liveness once on mount
  useEffect(() => {
    if (!token) return;
    gatewayApi.getDeviceStatus()
      .then((status) => {
        setDeviceOnline(status.is_online);
        // Also sync the device list immediately so is_online on each card is fresh
        qc.invalidateQueries({ queryKey: ['devices'] });
      })
      .catch(() => setDeviceOnline(false));
  }, [token, setDeviceOnline, qc]);

  useEffect(() => {
    if (!token) return;

    setConnected(true);
    const stop = startSensorStream(
      (reading) => {
        // The watchdog injects a sentinel with _device_status: true
        // instead of a real sensor reading — handle it separately.
        const raw = reading as unknown as Record<string, unknown>;
        if (raw._device_status === true) {
          const online = raw.is_online as boolean;
          setDeviceOnline(online);
          // Refetch device list so every card's is_online flag updates instantly
          qc.invalidateQueries({ queryKey: ['devices'] });
          return;
        }
        setLatest(reading);
        setConnected(true);
      },
      () => setConnected(false),
    );

    return () => {
      stop();
      setConnected(false);
    };
  }, [token, setLatest, setConnected, setDeviceOnline, qc]);
}
