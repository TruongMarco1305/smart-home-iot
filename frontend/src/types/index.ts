export type Role = 'admin' | 'operator' | 'viewer';
export type DeviceType = 'light' | 'pump';
export type DeviceState = 'ON' | 'OFF';

export interface User {
  id: string;
  username: string;
  email: string;
  role: Role;
  is_active: boolean;
}

export interface Device {
  id: string;
  name: string;
  device_type: DeviceType;
  room: string;
  adafruit_feed: string;
  state: DeviceState;
  is_online: boolean;
  updated_at: string;
}

export interface SensorReading {
  _id: string;
  device_id: string;
  temperature: number;
  humidity: number;
  illuminance: number;
  timestamp: string;
}

export interface SensorHistoryResponse {
  total: number;
  page: number;
  limit: number;
  data: SensorReading[];
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface CreateUserPayload {
  username: string;
  email: string;
  password: string;
  role: Role;
}

export interface UpdateUserPayload {
  email?: string;
  password?: string;
  role?: Role;
  is_active?: boolean;
}

export interface CreateDevicePayload {
  name: string;
  device_type: DeviceType;
  room: string;
  adafruit_feed: string;
}

export interface ApiError {
  detail: string | { loc: string[]; msg: string; type: string }[];
}
