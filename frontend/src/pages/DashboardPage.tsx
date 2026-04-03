import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Thermometer, Droplets, Sun, Cpu, AlertTriangle, WifiOff } from 'lucide-react';
import { useSensorStore } from '../stores/sensorStore';
import { useSensorStream } from '../hooks/useSensorStream';
import { devicesApi } from '../api/devices';
import { useAuthStore } from '../stores/authStore';
import type { Device } from '../types';

function SensorCard({
  label,
  value,
  unit,
  icon: Icon,
  color,
}: {
  label: string;
  value: number | null;
  unit: string;
  icon: React.ElementType;
  color: string;
}) {
  return (
    <div className="bg-slate-800 rounded-2xl p-6 flex items-center gap-5">
      <div className={`p-3 rounded-xl ${color}`}>
        <Icon size={22} className="text-white" />
      </div>
      <div>
        <p className="text-xs text-slate-400 font-medium uppercase tracking-wide">{label}</p>
        <p className="text-2xl font-bold text-white mt-0.5">
          {value !== null ? `${value}${unit}` : '—'}
        </p>
      </div>
    </div>
  );
}

function DeviceToggle({ device, isConnected }: { device: Device; isConnected: boolean }) {
  const qc = useQueryClient();
  const role = useAuthStore((s) => s.user?.role);
  const canControl = role === 'admin' || role === 'operator';
  const controlDisabled = !canControl || !device.is_online || !isConnected;

  const { mutate, isPending } = useMutation({
    mutationFn: (state: 'ON' | 'OFF') => devicesApi.command(device.id, state),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['devices'] }),
  });

  const isOn = device.state === 'ON';

  return (
    <div className={`flex items-center justify-between rounded-2xl px-5 py-4 ${
      !device.is_online ? 'bg-slate-800/50 border border-slate-700' : 'bg-slate-800'
    }`}>
      <div className="flex items-center gap-3">
        <div
          className={`p-2 rounded-lg ${
            !device.is_online ? 'bg-slate-700'
            : device.device_type === 'light' ? 'bg-amber-500/20' : 'bg-cyan-500/20'
          }`}
        >
          {device.device_type === 'light' ? (
            <Sun size={18} className={device.is_online ? 'text-amber-400' : 'text-slate-500'} />
          ) : (
            <Droplets size={18} className={device.is_online ? 'text-cyan-400' : 'text-slate-500'} />
          )}
        </div>
        <div>
          <p className={`text-sm font-medium ${device.is_online ? 'text-white' : 'text-slate-500'}`}>
            {device.name}
          </p>
          <p className="text-xs text-slate-500 capitalize">
            {device.is_online ? device.room : `${device.room} — offline`}
          </p>
        </div>
      </div>

      <button
        onClick={() => mutate(isOn ? 'OFF' : 'ON')}
        disabled={controlDisabled || isPending}
        title={!device.is_online ? 'Device is offline' : !isConnected ? 'No live connection' : undefined}
        className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors focus:outline-none disabled:opacity-40 disabled:cursor-not-allowed ${
          isOn && device.is_online ? 'bg-indigo-600' : 'bg-slate-600'
        }`}
      >
        <span
          className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform ${
            isOn && device.is_online ? 'translate-x-5' : 'translate-x-0'
          }`}
        />
      </button>
    </div>
  );
}

export function DashboardPage() {
  // Start the SSE stream
  useSensorStream();

  const latest = useSensorStore((s) => s.latest);
  const isConnected = useSensorStore((s) => s.isConnected);
  const isDeviceOnline = useSensorStore((s) => s.isDeviceOnline);

  const { data: devices = [] } = useQuery({
    queryKey: ['devices'],
    queryFn: devicesApi.list,
    refetchInterval: 10_000,
  });

  const timestamp = latest?.timestamp
    ? new Date(latest.timestamp).toLocaleTimeString()
    : null;

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            {isConnected && timestamp
              ? `Last update: ${timestamp}`
              : 'Connecting to live stream…'}
          </p>
        </div>
        <div
          className={`flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-full ${
            isConnected
              ? 'bg-emerald-500/10 text-emerald-400'
              : 'bg-slate-700 text-slate-400'
          }`}
        >
          <span
            className={`w-1.5 h-1.5 rounded-full ${isConnected ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`}
          />
          {isConnected ? 'Live' : 'Offline'}
        </div>
      </div>

      {/* Sensor cards */}
      <section>
        <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">
          Sensor Readings
        </h2>
        {!isConnected && (
          <div className="flex items-center gap-3 mb-4 bg-amber-500/10 border border-amber-500/20 rounded-xl px-4 py-3 text-sm text-amber-400">
            <WifiOff size={15} className="shrink-0" />
            <span>Stream disconnected — showing last known values. Live data will resume automatically.</span>
          </div>
        )}
        {isConnected && !isDeviceOnline && (
          <div className="flex items-center gap-3 mb-4 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3 text-sm text-red-400">
            <AlertTriangle size={15} className="shrink-0" />
            <span><span className="font-semibold">IoT device is offline</span> — no signal from Yolo:Bit in the last 60 s.</span>
          </div>
        )}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <SensorCard
            label="Temperature"
            value={latest ? +latest.temperature.toFixed(1) : null}
            unit="°C"
            icon={Thermometer}
            color="bg-orange-500"
          />
          <SensorCard
            label="Humidity"
            value={latest ? +latest.humidity.toFixed(1) : null}
            unit="%"
            icon={Droplets}
            color="bg-blue-500"
          />
          <SensorCard
            label="Illuminance"
            value={latest?.illuminance ?? null}
            unit=" lux"
            icon={Sun}
            color="bg-yellow-500"
          />
        </div>
      </section>

      {/* Device quick-control */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
            Devices
          </h2>
          <div className="flex items-center gap-1.5 text-xs text-slate-500">
            <Cpu size={12} />
            {devices.length} registered
          </div>
        </div>
        {devices.length === 0 ? (
          <p className="text-sm text-slate-500">No devices registered yet.</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {devices.map((d) => (
              <DeviceToggle key={d.id} device={d} isConnected={isConnected && isDeviceOnline} />
            ))}
          </div>
        )}
      </section>

      {/* Online/Offline stats */}
      <section className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Total devices', value: devices.length },
          { label: 'Online', value: devices.filter((d) => d.is_online).length },
          { label: 'ON', value: devices.filter((d) => d.state === 'ON').length },
          { label: 'OFF', value: devices.filter((d) => d.state === 'OFF').length },
        ].map(({ label, value }) => (
          <div key={label} className="bg-slate-800 rounded-2xl p-4 text-center">
            <p className="text-2xl font-bold text-white">{value}</p>
            <p className="text-xs text-slate-400 mt-1">{label}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
