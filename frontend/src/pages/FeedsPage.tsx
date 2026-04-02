import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Trash2, Rss } from 'lucide-react';
import { feedsApi } from '../api/feeds';
import type { CreateFeedPayload, Feed } from '../types';

// ---------------------------------------------------------------------------
// Add Feed Modal
// ---------------------------------------------------------------------------

function AddFeedModal({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient();
  const [form, setForm] = useState<CreateFeedPayload>({ key: '', label: '' });
  const [error, setError] = useState('');

  const { mutate, isPending } = useMutation({
    mutationFn: feedsApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['feeds'] });
      onClose();
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail;
      setError(typeof msg === 'string' ? msg : 'Failed to add feed');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    mutate({ key: form.key.trim(), label: form.label.trim() });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="bg-slate-800 rounded-2xl p-6 w-full max-w-sm shadow-2xl">
        <h2 className="text-lg font-bold text-white mb-5">Add Adafruit Feed</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <div className="space-y-1">
            <label className="block text-xs font-medium text-slate-400 uppercase tracking-wide">
              Feed key
            </label>
            <input
              value={form.key}
              onChange={(e) => setForm((f) => ({ ...f, key: e.target.value }))}
              placeholder="light-livingroom"
              required
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono"
            />
            <p className="text-xs text-slate-500">Must exactly match the key in your Adafruit IO dashboard.</p>
          </div>

          <div className="space-y-1">
            <label className="block text-xs font-medium text-slate-400 uppercase tracking-wide">
              Label
            </label>
            <input
              value={form.label}
              onChange={(e) => setForm((f) => ({ ...f, label: e.target.value }))}
              placeholder="Living Room Light"
              required
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg py-2.5 text-sm font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isPending}
              className="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg py-2.5 text-sm font-semibold transition-colors"
            >
              {isPending ? 'Adding…' : 'Add feed'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Feed row
// ---------------------------------------------------------------------------

function FeedRow({ feed }: { feed: Feed }) {
  const qc = useQueryClient();
  const [confirming, setConfirming] = useState(false);

  const { mutate: remove, isPending } = useMutation({
    mutationFn: () => feedsApi.delete(feed.id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['feeds'] }),
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail;
      alert(typeof msg === 'string' ? msg : 'Failed to delete feed');
      setConfirming(false);
    },
  });

  return (
    <div className="flex items-center justify-between bg-slate-800 rounded-xl px-4 py-3">
      <div className="flex items-center gap-3 min-w-0">
        <div className="p-2 rounded-lg bg-indigo-500/15 shrink-0">
          <Rss size={14} className="text-indigo-400" />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-medium text-white truncate">{feed.label}</p>
          <p className="text-xs font-mono text-slate-400 truncate">{feed.key}</p>
        </div>
      </div>

      <div className="flex items-center gap-2 shrink-0 ml-4">
        {confirming ? (
          <>
            <span className="text-xs text-slate-400">Delete?</span>
            <button
              onClick={() => remove()}
              disabled={isPending}
              className="text-xs bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white px-3 py-1.5 rounded-lg font-semibold transition-colors"
            >
              {isPending ? '…' : 'Yes'}
            </button>
            <button
              onClick={() => setConfirming(false)}
              className="text-xs bg-slate-700 hover:bg-slate-600 text-slate-300 px-3 py-1.5 rounded-lg transition-colors"
            >
              No
            </button>
          </>
        ) : (
          <button
            onClick={() => setConfirming(true)}
            className="p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
            title="Delete feed"
          >
            <Trash2 size={14} />
          </button>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export function FeedsPage() {
  const [showModal, setShowModal] = useState(false);

  const { data: feeds = [], isLoading } = useQuery({
    queryKey: ['feeds'],
    queryFn: feedsApi.list,
  });

  return (
    <div className="p-8 max-w-2xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Adafruit Feeds</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            {feeds.length} feed{feeds.length !== 1 ? 's' : ''} registered — these appear as options when adding a device.
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
        >
          <Plus size={16} />
          Add feed
        </button>
      </div>

      {isLoading ? (
        <div className="text-slate-400 text-sm">Loading…</div>
      ) : feeds.length === 0 ? (
        <div className="text-center py-16 text-slate-500">
          <Rss size={32} className="mx-auto mb-3 opacity-30" />
          <p className="text-lg">No feeds yet</p>
          <p className="text-sm mt-1">
            Add the feed keys you've created in your{' '}
            <a
              href="https://io.adafruit.com"
              target="_blank"
              rel="noreferrer"
              className="text-indigo-400 hover:underline"
            >
              Adafruit IO dashboard
            </a>
            .
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {feeds.map((f) => (
            <FeedRow key={f.id} feed={f} />
          ))}
        </div>
      )}

      {showModal && <AddFeedModal onClose={() => setShowModal(false)} />}
    </div>
  );
}
