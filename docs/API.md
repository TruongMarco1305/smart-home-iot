# Smart Home API — Frontend Integration Guide

Base URL: `http://localhost:8000` (development)  
Interactive docs: `http://localhost:8000/docs`

> **No external MQTT broker (Mosquitto) required.**  
> The Adafruit IO MQTT client runs as a background task embedded inside the FastAPI process.

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [RBAC Roles](#2-rbac-roles)
3. [Users](#3-users)
4. [Devices](#4-devices)
5. [Sensors](#5-sensors)
6. [Real-time Stream (SSE)](#6-real-time-stream-sse)
7. [Error Reference](#7-error-reference)
8. [Frontend Recipes](#8-frontend-recipes)

---

## 1. Authentication

All protected endpoints require a **JWT Bearer token** in the `Authorization` header.

```
Authorization: Bearer <access_token>
```

### POST `/api/auth/login`

Authenticate with a username and password. Returns an access token.

**Request body**

```json
{
  "username": "admin",
  "password": "admin1234"
}
```

| Field | Type | Rules |
|---|---|---|
| `username` | string | 3–50 chars |
| `password` | string | min 6 chars |

**Response `200`**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

> Store the token in memory (or `localStorage` for web). Attach it to every subsequent request.

---

### GET `/api/auth/me`

Returns the profile of the currently authenticated user.

**Headers:** `Authorization: Bearer <token>`

**Response `200`**

```json
{
  "id": "660f1a2b3c4d5e6f7a8b9c0d",
  "username": "admin",
  "email": "admin@smarthome.local",
  "role": "admin",
  "is_active": true
}
```

---

## 2. RBAC Roles

| Role | Permissions |
|---|---|
| `admin` | Full access — manage users, view data, register & control devices |
| `operator` | Control devices (ON/OFF) + view sensor data; cannot manage users |
| `viewer` | Read-only — view sensor data and device list only |

The `role` value is embedded in the JWT. Endpoints that require a specific role return `403 Forbidden` if the caller's role is insufficient.

---

## 3. Users

> All `/api/users` endpoints require **admin** role except `GET /api/users/{id}` and `PATCH /api/users/{id}` which also allow the user to access their own record.

### GET `/api/users` — List all users *(admin)*

**Headers:** `Authorization: Bearer <token>`

**Response `200`** — array of user objects

```json
[
  {
    "id": "660f1a2b3c4d5e6f7a8b9c0d",
    "username": "alice",
    "email": "alice@smarthome.local",
    "role": "operator",
    "is_active": true
  }
]
```

---

### POST `/api/users` — Create a user *(admin)*

**Headers:** `Authorization: Bearer <token>`

**Request body**

```json
{
  "username": "alice",
  "email": "alice@smarthome.local",
  "password": "securepass",
  "role": "operator"
}
```

| Field | Type | Rules |
|---|---|---|
| `username` | string | 3–50 chars, unique |
| `email` | string | valid email, unique |
| `password` | string | min 6 chars |
| `role` | string | `"admin"` \| `"operator"` \| `"viewer"` — defaults to `"viewer"` |

**Response `201`** — created user object (no password)

---

### GET `/api/users/{user_id}` — Get a single user

*(admin can fetch any user; a user can only fetch themselves)*

**Response `200`** — user object

---

### PATCH `/api/users/{user_id}` — Update a user

*(admin can update any field; a non-admin can only update their own `password`)*

**Request body** — all fields optional

```json
{
  "email": "newemail@smarthome.local",
  "password": "newpassword",
  "role": "viewer",
  "is_active": false
}
```

| Field | Who can set it | Notes |
|---|---|---|
| `password` | self or admin | min 6 chars |
| `email` | admin only | must be unique |
| `role` | admin only | `"admin"` \| `"operator"` \| `"viewer"` |
| `is_active` | admin only | `false` disables login |

**Response `200`** — updated user object

---

## 4. Devices

### GET `/api/devices` — List all devices *(any authenticated user)*

**Response `200`**

```json
[
  {
    "id": "661a2b3c4d5e6f7a8b9c0d1e",
    "name": "Living Room Light",
    "device_type": "light",
    "room": "livingroom",
    "adafruit_feed": "light-livingroom",
    "state": "OFF",
    "is_online": true,
    "updated_at": "2026-03-30T10:00:00"
  },
  {
    "id": "661a2b3c4d5e6f7a8b9c0d1f",
    "name": "Garden Pump",
    "device_type": "pump",
    "room": "garden",
    "adafruit_feed": "pump-garden",
    "state": "ON",
    "is_online": true,
    "updated_at": "2026-03-30T10:01:00"
  }
]
```

| Field | Type | Description |
|---|---|---|
| `id` | string | MongoDB ObjectId |
| `device_type` | `"light"` \| `"pump"` | Hardware type |
| `room` | string | Room identifier (lowercase, no spaces) |
| `adafruit_feed` | string | Adafruit IO feed key |
| `state` | `"ON"` \| `"OFF"` | Last known state |
| `is_online` | bool | Whether the device is reachable |

---

### POST `/api/devices` — Register a new device *(admin)*

**Request body**

```json
{
  "name": "Bedroom Light",
  "device_type": "light",
  "room": "bedroom",
  "adafruit_feed": "light-bedroom"
}
```

> `adafruit_feed` **must exactly match** the feed key created in Adafruit IO.  
> Convention: `{device_type}-{room}` — e.g. `light-livingroom`, `pump-garden`.

**Response `201`** — created device object

---

### PATCH `/api/devices/{device_id}/command` — Control a device *(operator / admin)*

Turns a device ON or OFF. The backend persists the new state and publishes an MQTT command that the gateway forwards to Adafruit IO.

**Request body**

```json
{ "state": "ON" }
```

| Field | Values |
|---|---|
| `state` | `"ON"` or `"OFF"` |

**Response `200`** — updated device object with new `state` and `updated_at`

---

## 5. Sensors

### GET `/api/sensors/latest` — Most recent reading *(any authenticated user)*

Returns the single most recent sensor snapshot stored in the database.

**Response `200`**

```json
{
  "_id": "661b3c4d5e6f7a8b9c0d1e2f",
  "device_id": "yolobit-living-room",
  "temperature": 27.5,
  "humidity": 63.0,
  "illuminance": 420,
  "timestamp": "2026-03-30T10:05:00.123456+00:00"
}
```

| Field | Type | Unit |
|---|---|---|
| `temperature` | float | °C |
| `humidity` | float | % RH |
| `illuminance` | integer | lux |
| `timestamp` | ISO 8601 string | UTC |

---

### GET `/api/sensors/history` — Paginated history *(any authenticated user)*

**Query parameters**

| Param | Type | Default | Description |
|---|---|---|---|
| `page` | integer | `1` | Page number (1-based) |
| `limit` | integer | `50` | Results per page (max 500) |
| `device_id` | string | — | Filter by device, e.g. `yolobit-living-room` |

**Example**

```
GET /api/sensors/history?page=1&limit=100&device_id=yolobit-living-room
```

**Response `200`**

```json
{
  "total": 8640,
  "page": 1,
  "limit": 100,
  "data": [
    {
      "_id": "...",
      "device_id": "yolobit-living-room",
      "temperature": 27.5,
      "humidity": 63.0,
      "illuminance": 420,
      "timestamp": "2026-03-30T10:05:00+00:00"
    }
  ]
}
```

> Results are sorted newest-first. Readings older than **7 days** are automatically deleted by MongoDB TTL.

---

## 6. Real-time Stream (SSE)

### GET `/api/sensors/stream` — Live sensor data *(any authenticated user)*

Opens a persistent **Server-Sent Events** connection. The backend pushes the latest sensor snapshot **every 1 second**.

Because the native `EventSource` API does not support custom headers, pass the token as a query parameter or use a polyfill (see recipes below).

**Connection**

```
GET /api/sensors/stream
Authorization: Bearer <token>
Accept: text/event-stream
```

**Each event**

```
data: {"_id":"...","device_id":"yolobit-living-room","temperature":27.5,"humidity":63.0,"illuminance":420,"timestamp":"2026-03-30T10:05:01+00:00"}

data: {"_id":"...","device_id":"yolobit-living-room","temperature":27.6,"humidity":62.8,"illuminance":418,"timestamp":"2026-03-30T10:05:02+00:00"}
```

Each message is a single `data:` line followed by two newlines. Parse it with `JSON.parse(event.data)`.

---

## 7. Error Reference

| Status | When it occurs |
|---|---|
| `400 Bad Request` | Validation error or malformed ObjectId |
| `401 Unauthorized` | Missing, expired, or invalid JWT |
| `403 Forbidden` | Valid JWT but role is insufficient, or account is disabled |
| `404 Not Found` | Resource with given id does not exist |
| `409 Conflict` | Username or email already taken; Adafruit feed already registered |
| `422 Unprocessable Entity` | Request body fails Pydantic schema validation |

**Error body shape**

```json
{
  "detail": "Incorrect username or password"
}
```

For `422` errors the `detail` field is an array:

```json
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "String should have at least 6 characters",
      "type": "string_too_short"
    }
  ]
}
```

---

## 8. Frontend Recipes

### Login and store token

```typescript
async function login(username: string, password: string): Promise<string> {
  const res = await fetch('http://localhost:8000/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) throw new Error('Login failed');
  const { access_token } = await res.json();
  localStorage.setItem('token', access_token);
  return access_token;
}
```

### Authenticated fetch helper

```typescript
function authFetch(path: string, init: RequestInit = {}) {
  const token = localStorage.getItem('token');
  return fetch(`http://localhost:8000${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...init.headers,
    },
  });
}
```

### Turn a device on/off

```typescript
async function setDeviceState(deviceId: string, state: 'ON' | 'OFF') {
  const res = await authFetch(`/api/devices/${deviceId}/command`, {
    method: 'PATCH',
    body: JSON.stringify({ state }),
  });
  if (!res.ok) throw new Error(`Command failed: ${res.status}`);
  return res.json(); // returns updated DevicePublic
}
```

### Real-time sensor stream with `fetch` (supports auth header)

```typescript
async function startSensorStream(
  onReading: (data: SensorReading) => void,
  signal: AbortSignal,
) {
  const token = localStorage.getItem('token');
  const res = await fetch('http://localhost:8000/api/sensors/stream', {
    headers: { Authorization: `Bearer ${token}` },
    signal,
  });

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n\n');
    buffer = lines.pop() ?? '';
    for (const chunk of lines) {
      const line = chunk.replace(/^data:\s*/, '');
      if (line) onReading(JSON.parse(line));
    }
  }
}

// Usage
const controller = new AbortController();
startSensorStream((reading) => {
  console.log('Temp:', reading.temperature, '°C');
  console.log('Humidity:', reading.humidity, '%');
  console.log('Illuminance:', reading.illuminance, 'lux');
}, controller.signal);

// Stop streaming
controller.abort();
```

### Sensor history chart (last 100 readings)

```typescript
async function fetchHistory(deviceId = 'yolobit-living-room') {
  const res = await authFetch(
    `/api/sensors/history?page=1&limit=100&device_id=${deviceId}`,
  );
  const json = await res.json();
  // json.data — array of readings sorted newest-first
  // json.total — total record count
  return json;
}
```

### TypeScript types

```typescript
type Role = 'admin' | 'operator' | 'viewer';
type DeviceType = 'light' | 'pump';
type DeviceState = 'ON' | 'OFF';

interface User {
  id: string;
  username: string;
  email: string;
  role: Role;
  is_active: boolean;
}

interface Device {
  id: string;
  name: string;
  device_type: DeviceType;
  room: string;
  adafruit_feed: string;
  state: DeviceState;
  is_online: boolean;
  updated_at: string;
}

interface SensorReading {
  _id: string;
  device_id: string;
  temperature: number;   // °C
  humidity: number;      // % RH
  illuminance: number;   // lux
  timestamp: string;     // ISO 8601 UTC
}

interface SensorHistoryResponse {
  total: number;
  page: number;
  limit: number;
  data: SensorReading[];
}
```
