import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Sun, Droplets, Wifi, WifiOff } from 'lucide-react';
import { devicesApi } from '../api/devices';
import { feedsApi } from '../api/feeds';
import { useAuthStore } from '../stores/authStore';
import type { Device, CreateDevicePayload, DeviceType } from '../types';

// ---------------------------------------------------------------------------
// Toggle switch component
// ---------------------------------------------------------------------------

function ToggleSwitch({
  checked,
  onChange,
  disabled,
}: {
  checked: boolean;
  onChange: (val: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      disabled={disabled}
      className={`relative inline-flex h-7 w-12 shrink-0 items-center rounded-full transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 disabled:cursor-not-allowed disabled:opacity-40 ${
        checked ? 'bg-indigo-600' : 'bg-slate-600'
      }`}
    >
      <span
        className={`inline-block h-5 w-5 transform rounded-full bg-white shadow-md transition-transform duration-200 ${
          checked ? 'translate-x-6' : 'translate-x-1'
        }`}
      />
    </button>
  );
}

function DeviceCard({ device }: { device: Device }) {
  const qc = useQueryClient();
  const role = useAuthStore((s) => s.user?.role);
  const canControl = role === 'admin' || role === 'operator';

  const { mutate, isPending } = useMutation({
    mutationFn: (state: 'ON' | 'OFF') => devicesApi.command(device.id, state),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['devices'] }),
  });

  const isOn = device.state === 'ON';

  return (
    <div className="bg-slate-800 rounded-2xl p-5 space-y-4">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div
            className={`p-2.5 rounded-xl ${device.device_type === 'light' ? 'bg-amber-500/20' : 'bg-cyan-500/20'}`}
          >
            {device.device_type === 'light' ? (
              <Sun size={20} className="text-amber-400" />
            ) : (
              <Droplets size={20} className="text-cyan-400" />
            )}
          </div>
          <div>
            <p className="font-semibold text-white">{device.name}</p>
            <p className="text-xs text-slate-500 capitalize">{device.room}</p>
          </div>
        </div>
        <div className="flex items-center gap-1 text-xs text-slate-500">
          {device.is_online ? (
            <><Wifi size={12} className="text-emerald-400" /><span className="text-emerald-400">Online</span></>
          ) : (
            <><WifiOff size={12} /><span>Offline</span></>
          )}
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-slate-500">Feed</p>
          <p className="text-xs font-mono text-slate-300 mt-0.5">{device.adafruit_feed}</p>
        </div>
        <div className="flex items-center gap-2.5">
          <span className={`text-xs font-semibold ${isOn ? 'text-indigo-400' : 'text-slate-500'}`}>
            {isOn ? 'ON' : 'OFF'}
          </span>
          <ToggleSwitch
            checked={isOn}
            onChange={(val) => mutate(val ? 'ON' : 'OFF')}
            disabled={!canControl || isPending}
          />
        </div>
      </div>

      <p className="text-xs text-slate-600">
        Updated {new Date(device.updated_at).toLocaleString()}
      </p>
    </div>
  );
}

function RegisterDeviceModal({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient();
  const [form, setForm] = useState<CreateDevicePayload>({
    name: '',
    device_type: 'light',
    room: '',
    adafruit_feed: '',
  });
  const [error, setError] = useState('');

  const { data: feeds = [], isLoading: feedsLoading } = useQuery({
    queryKey: ['feeds'],
    queryFn: feedsApi.list,
  });

  const { mutate, isPending } = useMutation({
    mutationFn: devicesApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['devices'] });
      onClose();
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof msg === 'string' ? msg : 'Failed to create device');
    },
  });

  const set = (k: keyof CreateDevicePayload, v: string) =>
    setForm((f) => ({ ...f, [k]: v }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    mutate(form);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="bg-slate-800 rounded-2xl p-6 w-full max-w-md shadow-2xl">
        <h2 className="text-lg font-bold text-white mb-5">Register Device</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          {/* Device name */}
          <div className="space-y-1">
            <label className="block text-xs font-medium text-slate-400 uppercase tracking-wide">
              Device name
            </label>
            <input
              value={form.name}
              onChange={(e) => set('name', e.target.value)}
              placeholder="Living Room Light"
              required
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {/* Room */}
          <div className="space-y-1">
            <label className="block text-xs font-medium text-slate-400 uppercase tracking-wide">
              Room
            </label>
            <input
              value={form.room}
              onChange={(e) => set('room', e.target.value)}
              placeholder="livingroom"
              required
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {/* Type */}
          <div className="space-y-1">
            <label className="block text-xs font-medium text-slate-400 uppercase tracking-wide">
              Type
            </label>
            <select
              value={form.device_type}
              onChange={(e) => set('device_type', e.target.value as DeviceType)}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="light">Light</option>
              <option value="pump">Pump</option>
            </select>
          </div>

          {/* Adafruit feed — dropdown from the feeds collection */}
          <div className="space-y-1">
            <label className="block text-xs font-medium text-slate-400 uppercase tracking-wide">
              Adafruit feed
            </label>
            {feedsLoading ? (
              <p className="text-xs text-slate-500 py-2">Loading feeds…</p>
            ) : feeds.length === 0 ? (
              <p className="text-xs text-amber-400 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-2">
                No feeds registered yet. Go to <span className="font-semibold">Feeds</span> in the sidebar to add one first.
              </p>
            ) : (
              <select
                value={form.adafruit_feed}
                onChange={(e) => set('adafruit_feed', e.target.value)}
                required
                className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="" disabled>Select a feed…</option>
                {feeds.map((f) => (
                  <option key={f.id} value={f.key}>
                    {f.label} ({f.key})
                  </option>
                ))}
              </select>
            )}
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg py-2.5 text-sm font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isPending || feeds.length === 0}
              className="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg py-2.5 text-sm font-semibold transition-colors"
            >
              {isPending ? 'Registering…' : 'Register'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export function DevicesPage() {
  const role = useAuthStore((s) => s.user?.role);
  const [showModal, setShowModal] = useState(false);

  const { data: devices = [], isLoading } = useQuery({
    queryKey: ['devices'],
    queryFn: devicesApi.list,
    refetchInterval: 10_000,
  });

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Devices</h1>
          <p className="text-sm text-slate-400 mt-0.5">{devices.length} registered</p>
        </div>
        {role === 'admin' && (
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
          >
            <Plus size={16} />
            Register device
          </button>
        )}
      </div>

      {isLoading ? (
        <div className="text-slate-400 text-sm">Loading…</div>
      ) : devices.length === 0 ? (
        <div className="text-center py-16 text-slate-500">
          <p className="text-lg">No devices yet</p>
          {role === 'admin' && (
            <p className="text-sm mt-1">Click "Register device" to add one.</p>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {devices.map((d) => (
            <DeviceCard key={d.id} device={d} />
          ))}
        </div>
      )}

      {showModal && <RegisterDeviceModal onClose={() => setShowModal(false)} />}
    </div>
  );
}
