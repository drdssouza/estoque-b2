import React, { useEffect, useState } from 'react';
import Sidebar from './Sidebar';
import { useAppStore } from '../../store';
import { CheckCircle, XCircle, Info, X, Download } from 'lucide-react';
import { cn } from '../../lib/utils';
import { open } from '@tauri-apps/plugin-shell';
import type { Toast } from '../../types';

const CURRENT_VERSION = '2.0.0';
const GITHUB_REPO = 'drdssouza/estoque-b2';
const RELEASES_URL = `https://github.com/${GITHUB_REPO}/releases/latest`;
const RELEASES_API = `https://api.github.com/repos/${GITHUB_REPO}/releases/latest`;

function ToastItem({ toast, onRemove }: { toast: Toast; onRemove: () => void }) {
  const icons = {
    success: <CheckCircle size={16} className="text-primary shrink-0" />,
    error: <XCircle size={16} className="text-danger shrink-0" />,
    info: <Info size={16} className="text-info shrink-0" />,
  };

  const borders = {
    success: 'border-primary/30',
    error: 'border-danger/30',
    info: 'border-info/30',
  };

  return (
    <div
      className={cn(
        'flex items-center gap-3 px-4 py-3 bg-card border rounded-xl shadow-2xl min-w-72 max-w-sm animate-slide-in',
        borders[toast.type]
      )}
    >
      {icons[toast.type]}
      <p className="flex-1 text-sm text-white">{toast.text}</p>
      <button
        onClick={onRemove}
        className="p-0.5 text-muted hover:text-white transition-colors"
      >
        <X size={14} />
      </button>
    </div>
  );
}

export default function Layout({ children }: { children: React.ReactNode }) {
  const { toasts, removeToast } = useAppStore();
  const [updateVersion, setUpdateVersion] = useState<string | null>(null);

  useEffect(() => {
    fetch(RELEASES_API, { headers: { Accept: 'application/vnd.github+json' } })
      .then((r) => r.json())
      .then((data) => {
        const latest = String(data.tag_name ?? '').replace(/^v/, '').trim();
        if (latest && latest !== CURRENT_VERSION) {
          setUpdateVersion(latest);
        }
      })
      .catch(() => {/* silently ignore — offline or rate limit */});
  }, []);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-bg">
      <Sidebar />

      <main className="flex-1 overflow-hidden flex flex-col">
        {/* Update banner */}
        {updateVersion && (
          <div className="flex items-center gap-3 px-5 py-2.5 bg-info-subtle border-b border-info/20 shrink-0">
            <Download size={13} className="text-info shrink-0" />
            <p className="text-xs text-info flex-1">
              Nova versão{' '}
              <span className="font-bold text-white">v{updateVersion}</span>{' '}
              disponível! Baixe e instale para ter as últimas melhorias.
            </p>
            <button
              className="text-xs text-info font-semibold hover:text-white transition-colors underline underline-offset-2"
              onClick={() => open(RELEASES_URL)}
            >
              Baixar atualização →
            </button>
            <button
              className="p-0.5 text-info/50 hover:text-info transition-colors ml-1"
              onClick={() => setUpdateVersion(null)}
              aria-label="Fechar"
            >
              <X size={13} />
            </button>
          </div>
        )}

        <div className="flex-1 overflow-auto p-6">
          {children}
        </div>
      </main>

      {/* Toast container */}
      <div className="fixed bottom-5 right-5 flex flex-col gap-2 z-[100]">
        {toasts.map((t) => (
          <ToastItem key={t.id} toast={t} onRemove={() => removeToast(t.id)} />
        ))}
      </div>
    </div>
  );
}
