import { useEffect, useRef, useState } from 'react';
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
import { useSensorStream } from '../hooks/useSensorStream';
import type { SensorReading } from '../types';

type Metric = 'temperature' | 'humidity' | 'illuminance';

const METRICS: { key: Metric; label: string; unit: string; color: string }[] = [
  { key: 'temperature', label: 'Temperature', unit: '°C', color: '#f97316' },
  { key: 'humidity', label: 'Humidity', unit: '%', color: '#38bdf8' },
  { key: 'illuminance', label: 'Illuminance', unit: 'lux', color: '#facc15' },
];

const MAX_POINTS = 120; // keep last 2 minutes at 1 reading/s

function toChartPoint(r: SensorReading) {
  return {
    time: new Date(r.timestamp).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }),
    temperature: +r.temperature.toFixed(1),
    humidity: +r.humidity.toFixed(1),
    illuminance: r.illuminance,
  };
}

export function SensorsPage() {
  // Keep the SSE stream alive while on this page
  useSensorStream();

  const latest = useSensorStore((s) => s.latest);

  // Rolling buffer of chart points — updated in real-time from the SSE store
  const bufferRef = useRef<ReturnType<typeof toChartPoint>[]>([]);
  const [chartPoints, setChartPoints] = useState<ReturnType<typeof toChartPoint>[]>([]);

  // Seed from history on first load
  const { data: history } = useQuery({
    queryKey: ['sensors', 'history', 1],
    queryFn: () => sensorsApi.history(1, MAX_POINTS),
    staleTime: Infinity, // only fetch once; live updates come from SSE
  });

  useEffect(() => {
    if (!history) return;
    // history is newest-first; reverse to oldest-first for the chart
    bufferRef.current = [...history.data].reverse().map(toChartPoint);
    setChartPoints([...bufferRef.current]);
  }, [history]);

  // Append every new SSE reading to the rolling buffer
  useEffect(() => {
    if (!latest) return;
    bufferRef.current = [
      ...bufferRef.current.slice(-(MAX_POINTS - 1)),
      toChartPoint(latest),
    ];
    setChartPoints([...bufferRef.current]);
  }, [latest]);

  const [activeMetrics, setActiveMetrics] = useState<Set<Metric>>(
    new Set(['temperature', 'humidity', 'illuminance']),
  );

  const toggleMetric = (key: Metric) =>
    setActiveMetrics((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Sensor History</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            {history ? `${history.total.toLocaleString()} readings stored` : 'Loading…'}
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-full bg-emerald-500/10 text-emerald-400">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          Live
        </div>
      </div>

      {/* Live snapshot cards */}
      {latest && (
        <div className="grid grid-cols-3 gap-4">
          {METRICS.map(({ key, label, unit, color }) => (
            <div key={key} className="bg-slate-800 rounded-2xl p-4 text-center">
              <p className="text-xs text-slate-400 uppercase tracking-wide">{label}</p>
              <p className="text-3xl font-bold mt-1" style={{ color }}>
                {key === 'illuminance' ? latest[key] : +latest[key].toFixed(1)}
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
        {chartPoints.length === 0 ? (
          <div className="h-72 flex items-center justify-center text-slate-400 text-sm">
            Waiting for data…
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={360}>
            <LineChart
              data={chartPoints}
              margin={{ top: 4, right: 8, bottom: 4, left: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis
                dataKey="time"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                interval="preserveStartEnd"
                tickLine={false}
              />
              <YAxis
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                tickLine={false}
                axisLine={false}
              />
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
    </div>
  );
}
