import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, UserCheck, UserX, Shield, Eye, Wrench } from 'lucide-react';
import { usersApi } from '../api/users';
import type { User, CreateUserPayload, Role } from '../types';

const ROLE_META: Record<Role, { label: string; icon: React.ElementType; color: string }> = {
  admin:    { label: 'Admin',    icon: Shield,    color: 'text-red-400 bg-red-500/10' },
  operator: { label: 'Operator', icon: Wrench,    color: 'text-amber-400 bg-amber-500/10' },
  viewer:   { label: 'Viewer',   icon: Eye,       color: 'text-blue-400 bg-blue-500/10' },
};

function RoleBadge({ role }: { role: Role }) {
  const { label, icon: Icon, color } = ROLE_META[role];
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${color}`}>
      <Icon size={10} />
      {label}
    </span>
  );
}

function CreateUserModal({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient();
  const [form, setForm] = useState<CreateUserPayload>({
    username: '',
    email: '',
    password: '',
    role: 'viewer',
  });
  const [error, setError] = useState('');

  const { mutate, isPending } = useMutation({
    mutationFn: usersApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['users'] });
      onClose();
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Failed to create user');
    },
  });

  const set = (k: keyof CreateUserPayload, v: string) =>
    setForm((f) => ({ ...f, [k]: v }));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="bg-slate-800 rounded-2xl p-6 w-full max-w-md shadow-2xl">
        <h2 className="text-lg font-bold text-white mb-5">Create User</h2>
        <form
          onSubmit={(e) => { e.preventDefault(); setError(''); mutate(form); }}
          className="space-y-4"
        >
          {error && (
            <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          {([
            ['Username', 'username', 'text', 'alice'],
            ['Email', 'email', 'email', 'alice@smarthome.local'],
            ['Password', 'password', 'password', '••••••'],
          ] as const).map(([label, key, type, placeholder]) => (
            <div key={key} className="space-y-1">
              <label className="block text-xs font-medium text-slate-400 uppercase tracking-wide">
                {label}
              </label>
              <input
                type={type}
                value={form[key]}
                onChange={(e) => set(key, e.target.value)}
                placeholder={placeholder}
                required
                className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          ))}

          <div className="space-y-1">
            <label className="block text-xs font-medium text-slate-400 uppercase tracking-wide">
              Role
            </label>
            <select
              value={form.role}
              onChange={(e) => set('role', e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="viewer">Viewer</option>
              <option value="operator">Operator</option>
              <option value="admin">Admin</option>
            </select>
          </div>

          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose}
              className="flex-1 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg py-2.5 text-sm font-medium transition-colors">
              Cancel
            </button>
            <button type="submit" disabled={isPending}
              className="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg py-2.5 text-sm font-semibold transition-colors">
              {isPending ? 'Creating…' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function UserRow({ user }: { user: User }) {
  const qc = useQueryClient();

  const toggleActive = useMutation({
    mutationFn: () => usersApi.update(user.id, { is_active: !user.is_active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['users'] }),
  });

  const changeRole = useMutation({
    mutationFn: (role: Role) => usersApi.update(user.id, { role }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['users'] }),
  });

  return (
    <tr className="border-b border-slate-700/50 hover:bg-slate-700/20 transition-colors">
      <td className="px-5 py-4">
        <p className="font-medium text-white">{user.username}</p>
        <p className="text-xs text-slate-500">{user.email}</p>
      </td>
      <td className="px-5 py-4">
        <select
          value={user.role}
          onChange={(e) => changeRole.mutate(e.target.value as Role)}
          className="bg-slate-700 border border-slate-600 rounded-lg px-2 py-1 text-xs text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="viewer">Viewer</option>
          <option value="operator">Operator</option>
          <option value="admin">Admin</option>
        </select>
      </td>
      <td className="px-5 py-4">
        <RoleBadge role={user.role} />
      </td>
      <td className="px-5 py-4">
        <button
          onClick={() => toggleActive.mutate()}
          disabled={toggleActive.isPending}
          className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium transition-colors disabled:opacity-40 ${
            user.is_active
              ? 'bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20'
              : 'bg-red-500/10 text-red-400 hover:bg-red-500/20'
          }`}
        >
          {user.is_active ? <UserCheck size={12} /> : <UserX size={12} />}
          {user.is_active ? 'Active' : 'Disabled'}
        </button>
      </td>
    </tr>
  );
}

export function UsersPage() {
  const [showCreate, setShowCreate] = useState(false);

  const { data: users = [], isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: usersApi.list,
  });

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Users</h1>
          <p className="text-sm text-slate-400 mt-0.5">{users.length} accounts</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
        >
          <Plus size={16} />
          Create user
        </button>
      </div>

      <div className="bg-slate-800 rounded-2xl overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-slate-400 text-sm">Loading…</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700">
                {['User', 'Change Role', 'Current Role', 'Status'].map((h) => (
                  <th key={h} className="text-left px-5 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wide">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <UserRow key={u.id} user={u} />
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showCreate && <CreateUserModal onClose={() => setShowCreate(false)} />}
    </div>
  );
}
