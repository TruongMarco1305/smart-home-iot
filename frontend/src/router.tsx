import {
  createRootRoute,
  createRoute,
  createRouter,
  redirect,
} from '@tanstack/react-router';
import { useAuthStore } from './stores/authStore';

import { Layout } from './components/Layout';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { DevicesPage } from './pages/DevicesPage';
import { FeedsPage } from './pages/FeedsPage';
import { SensorsPage } from './pages/SensorsPage';
import { UsersPage } from './pages/UsersPage';

// ── Root ──────────────────────────────────────────────────────────────────────
const rootRoute = createRootRoute({
  component: Layout,
});

// ── Login (public) ────────────────────────────────────────────────────────────
const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/login',
  beforeLoad: () => {
    if (useAuthStore.getState().token) {
      throw redirect({ to: '/dashboard' });
    }
  },
  component: LoginPage,
});

// ── Protected layout guard ────────────────────────────────────────────────────
function requireAuth() {
  if (!useAuthStore.getState().token) {
    throw redirect({ to: '/login' });
  }
}

// ── Protected routes ──────────────────────────────────────────────────────────
const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  beforeLoad: requireAuth,
  loader: () => { throw redirect({ to: '/dashboard' }); },
});

const dashboardRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/dashboard',
  beforeLoad: requireAuth,
  component: DashboardPage,
});

const devicesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/devices',
  beforeLoad: requireAuth,
  component: DevicesPage,
});

const sensorsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/sensors',
  beforeLoad: requireAuth,
  component: SensorsPage,
});

const usersRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/users',
  beforeLoad: () => {
    requireAuth();
    const role = useAuthStore.getState().user?.role;
    if (role !== 'admin') {
      throw redirect({ to: '/dashboard' });
    }
  },
  component: UsersPage,
});

const feedsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/feeds',
  beforeLoad: () => {
    requireAuth();
    const role = useAuthStore.getState().user?.role;
    if (role !== 'admin') {
      throw redirect({ to: '/dashboard' });
    }
  },
  component: FeedsPage,
});

// ── Router ────────────────────────────────────────────────────────────────────
const routeTree = rootRoute.addChildren([
  indexRoute,
  loginRoute,
  dashboardRoute,
  devicesRoute,
  sensorsRoute,
  usersRoute,
  feedsRoute,
]);

export const router = createRouter({ routeTree });

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}
