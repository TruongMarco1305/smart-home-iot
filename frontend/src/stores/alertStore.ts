import { create } from 'zustand';
import type { AlertPayload } from '../types';

interface AlertState {
  alert: AlertPayload | null;
  setAlert: (alert: AlertPayload) => void;
  dismissAlert: () => void;
}

export const useAlertStore = create<AlertState>((set) => ({
  alert: null,
  setAlert: (alert) => set({ alert }),
  dismissAlert: () => set({ alert: null }),
}));
