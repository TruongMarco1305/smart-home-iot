import { create } from 'zustand';
import type { SensorReading } from '../types';

interface SensorState {
  latest: SensorReading | null;
  isConnected: boolean;       // SSE stream is alive
  isDeviceOnline: boolean;    // Yolo:Bit is sending MQTT messages
  setLatest: (reading: SensorReading) => void;
  setConnected: (connected: boolean) => void;
  setDeviceOnline: (online: boolean) => void;
}

export const useSensorStore = create<SensorState>((set) => ({
  latest: null,
  isConnected: false,
  isDeviceOnline: false,
  setLatest: (reading) => set({ latest: reading }),
  setConnected: (connected) => set({ isConnected: connected }),
  setDeviceOnline: (online) => set({ isDeviceOnline: online }),
}));
