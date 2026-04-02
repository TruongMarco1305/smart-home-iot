import { useAlertStore } from '../stores/alertStore';
import type { AlertLevel } from '../types';

// ── Visual config per alert level ──────────────────────────────────────────

const CONFIG: Record<
  AlertLevel,
  { bg: string; border: string; badge: string; icon: string; title: string }
> = {
  fire: {
    bg: 'bg-red-950',
    border: 'border-red-500',
    badge: 'bg-red-600 text-white',
    icon: '🔥',
    title: 'FIRE ALERT',
  },
  high_temp: {
    bg: 'bg-orange-950',
    border: 'border-orange-500',
    badge: 'bg-orange-600 text-white',
    icon: '🌡️',
    title: 'HIGH TEMPERATURE',
  },
  high_light: {
    bg: 'bg-yellow-950',
    border: 'border-yellow-400',
    badge: 'bg-yellow-500 text-black',
    icon: '☀️',
    title: 'HIGH ILLUMINANCE',
  },
};

// ── Component ──────────────────────────────────────────────────────────────

export default function FireAlertModal() {
  const alert = useAlertStore((s) => s.alert);
  const dismiss = useAlertStore((s) => s.dismissAlert);

  if (!alert) return null;

  const cfg = CONFIG[alert.level];
  const ts = new Date(alert.timestamp).toLocaleTimeString();

  return (
    /* Full-screen backdrop */
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="fire-alert-title"
    >
      {/* Modal card */}
      <div
        className={`
          relative w-full max-w-md mx-4 rounded-2xl border-2 p-8
          shadow-2xl animate-pulse-once
          ${cfg.bg} ${cfg.border}
        `}
      >
        {/* Animated icon */}
        <div className="flex flex-col items-center gap-3 text-center">
          <span className="text-7xl animate-bounce select-none" aria-hidden>
            {cfg.icon}
          </span>

          {/* Title */}
          <h2
            id="fire-alert-title"
            className="text-3xl font-extrabold tracking-widest text-white uppercase"
          >
            {cfg.title}
          </h2>

          {/* Level badge */}
          <span
            className={`rounded-full px-4 py-1 text-xs font-bold uppercase tracking-widest ${cfg.badge}`}
          >
            {alert.level.replace('_', ' ')}
          </span>

          {/* Message */}
          <p className="mt-2 text-base text-gray-200 leading-relaxed">
            {alert.message}
          </p>

          {/* Sensor values */}
          <div className="mt-4 grid grid-cols-3 gap-4 w-full">
            <StatBox label="Temperature" value={`${alert.temperature.toFixed(1)} °C`} />
            <StatBox label="Humidity" value={`${alert.humidity.toFixed(1)} %`} />
            <StatBox label="Illuminance" value={`${alert.illuminance} lux`} />
          </div>

          {/* Meta */}
          <p className="mt-4 text-xs text-gray-400">
            Device: <span className="font-mono">{alert.device_id}</span>
            &nbsp;·&nbsp;{ts}
          </p>

          {/* Dismiss */}
          <button
            onClick={dismiss}
            className="mt-6 w-full rounded-xl bg-white/10 py-3 text-sm font-semibold
                       text-white hover:bg-white/20 active:scale-95 transition-all"
          >
            Acknowledge &amp; Dismiss
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Tiny helper ────────────────────────────────────────────────────────────

function StatBox({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col items-center rounded-xl bg-white/10 p-3 gap-1">
      <span className="text-xs text-gray-400 uppercase tracking-wider">{label}</span>
      <span className="text-lg font-bold text-white">{value}</span>
    </div>
  );
}
