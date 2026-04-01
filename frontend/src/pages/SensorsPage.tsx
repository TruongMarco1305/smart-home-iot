import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { sensorsApi } from '../api/sensors';
import { useSensorStore } from '../stores/sensorStore';
import type { SensorReading } from '../types';

type Metric = 'temperature' | 'humidity' | 'illuminance';

const METRICS: { key: Metric; label: string; unit: string; color: string }[] = [
  { key: 'temperature', label: 'Temperature', unit: '°C', color: '#f97316' },
  { key: 'humidity', label: 'Humidity', unit: '%', color: '#38bdf8' },
  { key: 'illuminance', label: 'Illuminance', unit: 'lux', color: '#facc15' },
];

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function chartData(readings: SensorReading[]) {
  return [...readings].reverse().map((r) => ({
    time: formatTime(r.timestamp),
    temperature: +r.temperature.toFixed(1),
    humidity: +r.humidity.toFixed(1),
    illuminance: r.illuminance,
  }));
}

export function SensorsPage() {
  const latest = useSensorStore((s) => s.latest);
  const [page, setPage] = useState(1);
  const limit = 100;
  const [activeMetrics, setActiveMetrics] = useState<Set<Metric>>(
    new Set(['temperature', 'humidity', 'illuminance']),
  );

  const { data, isLoading } = useQuery({
    queryKey: ['sensors', 'history', page],
    queryFn: () => sensorsApi.history(page, limit),
    placeholderData: (prev) => prev,
  });

  const totalPages = data ? Math.ceil(data.total / limit) : 1;
  const chart = data ? chartData(data.data) : [];

  const toggleMetric = (key: Metric) => {
    setActiveMetrics((prev) => {
      const next = new Set(prev);
      if (next.has(key)) { next.delete(key); } else { next.add(key); }
      return next;
    });
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Sensor History</h1>
        <p className="text-sm text-slate-400 mt-0.5">
          {data ? `${data.total.toLocaleString()} readings stored` : 'Loading…'}
        </p>
      </div>

      {/* Live snapshot */}
      {latest && (
        <div className="grid grid-cols-3 gap-4">
          {METRICS.map(({ key, label, unit, color }) => (
            <div key={key} className="bg-slate-800 rounded-2xl p-4 text-center">
              <p className="text-xs text-slate-400 uppercase tracking-wide">{label}</p>
              <p className="text-3xl font-bold mt-1" style={{ color }}>
                {key === 'illuminance'
                  ? latest[key]
                  : (+latest[key].toFixed(1))}
                <span className="text-base font-normal text-slate-400 ml-1">{unit}</span>
              </p>
              <p className="text-xs text-slate-600 mt-1">live</p>
            </div>
          ))}
        </div>
      )}

      {/* Metric toggles */}
      <div className="flex items-center gap-3">
        {METRICS.map(({ key, label, color }) => (
          <button
            key={key}
            onClick={() => toggleMetric(key)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
              activeMetrics.has(key)
                ? 'bg-slate-700 border-slate-500 text-white'
                : 'bg-transparent border-slate-700 text-slate-500'
            }`}
          >
            <span
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: activeMetrics.has(key) ? color : '#475569' }}
            />
            {label}
          </button>
        ))}
      </div>

      {/* Chart */}
      <div className="bg-slate-800 rounded-2xl p-6">
        {isLoading ? (
          <div className="h-64 flex items-center justify-center text-slate-400 text-sm">
            Loading chart…
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chart} margin={{ top: 4, right: 4, bottom: 4, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis
                dataKey="time"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                interval="preserveStartEnd"
                tickLine={false}
              />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} tickLine={false} axisLine={false} />
              <Tooltip
                contentStyle={{
                  background: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: 8,
                  color: '#f1f5f9',
                  fontSize: 12,
                }}
              />
              <Legend wrapperStyle={{ fontSize: 12, color: '#94a3b8' }} />
              {METRICS.map(({ key, label, color }) =>
                activeMetrics.has(key) ? (
                  <Line
                    key={key}
                    type="monotone"
                    dataKey={key}
                    name={label}
                    stroke={color}
                    dot={false}
                    strokeWidth={2}
                    isAnimationActive={false}
                  />
                ) : null,
              )}
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Table */}
      <div className="bg-slate-800 rounded-2xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700">
              {['Timestamp', 'Temp (°C)', 'Humidity (%)', 'Illuminance (lux)'].map((h) => (
                <th
                  key={h}
                  className="text-left px-5 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wide"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {(data?.data ?? []).map((r) => (
              <tr
                key={r._id}
                className="border-b border-slate-700/50 hover:bg-slate-700/30 transition-colors"
              >
                <td className="px-5 py-3 text-slate-300 font-mono text-xs">
                  {new Date(r.timestamp).toLocaleString()}
                </td>
                <td className="px-5 py-3 text-orange-400">{r.temperature.toFixed(1)}</td>
                <td className="px-5 py-3 text-sky-400">{r.humidity.toFixed(1)}</td>
                <td className="px-5 py-3 text-yellow-400">{r.illuminance}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Pagination */}
        <div className="flex items-center justify-between px-5 py-3 border-t border-slate-700">
          <span className="text-xs text-slate-500">
            Page {page} of {totalPages}
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1.5 text-xs bg-slate-700 hover:bg-slate-600 disabled:opacity-40 text-slate-300 rounded-lg transition-colors"
            >
              Previous
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-3 py-1.5 text-xs bg-slate-700 hover:bg-slate-600 disabled:opacity-40 text-slate-300 rounded-lg transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
