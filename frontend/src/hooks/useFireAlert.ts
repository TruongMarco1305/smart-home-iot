import { useEffect } from 'react';
import { useAuthStore } from '../stores/authStore';
import { useAlertStore } from '../stores/alertStore';
import { startAlertStream } from '../api/sensors';

/**
 * Opens an SSE connection to /api/sensors/alerts when the user is
 * authenticated, and writes incoming AlertEvents into the alertStore.
 *
 * Mount this hook once (in Layout) so the connection is shared across pages.
 */
export function useFireAlert(): void {
  const token = useAuthStore((s) => s.token);
  const setAlert = useAlertStore((s) => s.setAlert);

  useEffect(() => {
    if (!token) return;

    const cancel = startAlertStream(
      (alert) => {
        console.warn('[FireAlert]', alert.level, alert.message);
        setAlert(alert);
      },
      (err) => {
        console.error('[FireAlert] stream error:', err);
      },
    );

    return cancel;
  }, [token, setAlert]);
}
