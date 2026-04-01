import { create } from 'zustand';
import type { SensorReading } from '../types';

interface SensorState {
  latest: SensorReading | null;
  isConnected: boolean;
  setLatest: (reading: SensorReading) => void;
  setConnected: (connected: boolean) => void;
}

export const useSensorStore = create<SensorState>((set) => ({
  latest: null,
  isConnected: false,
  setLatest: (reading) => set({ latest: reading }),
  setConnected: (connected) => set({ isConnected: connected }),
}));
