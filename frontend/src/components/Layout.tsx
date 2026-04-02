import { Link, Outlet, useLocation } from '@tanstack/react-router';
import {
  LayoutDashboard,
  Cpu,
  BarChart2,
  Users,
  Rss,
  LogOut,
  Wifi,
  WifiOff,
} from 'lucide-react';
import { useAuthStore } from '../stores/authStore';
import { useSensorStore } from '../stores/sensorStore';
import { useFireAlert } from '../hooks/useFireAlert';
import FireAlertModal from './FireAlertModal';

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/devices',   label: 'Devices',   icon: Cpu },
  { to: '/sensors',   label: 'Sensors',   icon: BarChart2 },
  { to: '/feeds',     label: 'Feeds',     icon: Rss,           adminOnly: true },
  { to: '/users',     label: 'Users',     icon: Users,         adminOnly: true },
];

export function Layout() {
  const { user, logout } = useAuthStore();
  const isConnected = useSensorStore((s) => s.isConnected);
  const pathname = useLocation({ select: (l) => l.pathname });
  const isLoginPage = pathname === '/login';

  // Open alert SSE connection for the lifetime of the authenticated session
  useFireAlert();

  if (isLoginPage || !user) {
    return <Outlet />;
  }

  return (
    <div className="flex h-screen bg-slate-900 text-slate-100">
      {/* Sidebar */}
      <aside className="flex flex-col w-56 shrink-0 bg-slate-800 border-r border-slate-700">
        {/* Brand */}
        <div className="flex items-center gap-2 px-5 py-4 border-b border-slate-700">
          <span className="text-xl">🏠</span>
          <span className="font-semibold text-sm tracking-wide">Smart Home</span>
        </div>

        {/* Nav */}
        <nav className="flex-1 py-4 space-y-1 px-2">
          {navItems.map(({ to, label, icon: Icon, adminOnly }) => {
            if (adminOnly && user.role !== 'admin') return null;
            const active = pathname.startsWith(to);
            return (
              <Link
                key={to}
                to={to}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  active
                    ? 'bg-indigo-600 text-white'
                    : 'text-slate-400 hover:bg-slate-700 hover:text-white'
                }`}
              >
                <Icon size={16} />
                {label}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="p-3 border-t border-slate-700 space-y-2">
          {/* SSE status */}
          <div className="flex items-center gap-2 px-2 py-1 text-xs text-slate-400">
            {isConnected ? (
              <><Wifi size={12} className="text-emerald-400" /><span className="text-emerald-400">Live</span></>
            ) : (
              <><WifiOff size={12} /><span>Offline</span></>
            )}
          </div>
          {/* User info */}
          <div className="px-2 py-1">
            <p className="text-xs font-medium text-slate-200 truncate">{user.username}</p>
            <p className="text-xs text-slate-500 capitalize">{user.role}</p>
          </div>
          <button
            onClick={logout}
            className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm text-slate-400 hover:bg-slate-700 hover:text-white transition-colors"
          >
            <LogOut size={14} />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>

      {/* Fire / environment alert overlay — rendered above everything */}
      <FireAlertModal />
    </div>
  );
}
