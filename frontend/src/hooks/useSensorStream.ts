import { useEffect } from 'react';
import { startSensorStream } from '../api/sensors';
import { gatewayApi } from '../api/gateway';
import { useSensorStore } from '../stores/sensorStore';
import { useAuthStore } from '../stores/authStore';

/**
 * Opens the SSE sensor stream while the user is authenticated.
 * Also fetches initial device liveness and listens for watchdog sentinels.
 * Call this once at a high-level component (e.g. Dashboard or Layout).
 */
export function useSensorStream() {
  const token = useAuthStore((s) => s.token);
  const setLatest = useSensorStore((s) => s.setLatest);
  const setConnected = useSensorStore((s) => s.setConnected);
  const setDeviceOnline = useSensorStore((s) => s.setDeviceOnline);

  // Fetch initial device liveness once on mount
  useEffect(() => {
    if (!token) return;
    gatewayApi.getDeviceStatus()
      .then((status) => setDeviceOnline(status.is_online))
      .catch(() => setDeviceOnline(false));
  }, [token, setDeviceOnline]);

  useEffect(() => {
    if (!token) return;

    setConnected(true);
    const stop = startSensorStream(
      (reading) => {
        // The watchdog injects a sentinel with _device_status: true
        // instead of a real sensor reading — handle it separately.
        const raw = reading as unknown as Record<string, unknown>;
        if (raw._device_status === true) {
          setDeviceOnline(raw.is_online as boolean);
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
  }, [token, setLatest, setConnected, setDeviceOnline]);
}
