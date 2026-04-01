import { useEffect } from 'react';
import { startSensorStream } from '../api/sensors';
import { useSensorStore } from '../stores/sensorStore';
import { useAuthStore } from '../stores/authStore';

/**
 * Opens the SSE sensor stream while the user is authenticated.
 * Call this once at a high-level component (e.g. Dashboard or Layout).
 */
export function useSensorStream() {
  const token = useAuthStore((s) => s.token);
  const setLatest = useSensorStore((s) => s.setLatest);
  const setConnected = useSensorStore((s) => s.setConnected);

  useEffect(() => {
    if (!token) return;

    setConnected(true);
    const stop = startSensorStream(
      (reading) => {
        setLatest(reading);
        setConnected(true);
      },
      () => setConnected(false),
    );

    return () => {
      stop();
      setConnected(false);
    };
  }, [token, setLatest, setConnected]);
}
