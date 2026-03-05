import React, { useEffect, useState } from 'react';
import Sidebar from './Sidebar';
import { useAppStore } from '../../store';
import { CheckCircle, XCircle, Info, X, Download, RefreshCw, Sparkles } from 'lucide-react';
import { cn } from '../../lib/utils';
import type { Toast } from '../../types';

type UpdateState =
  | { phase: 'idle' }
  | { phase: 'available'; version: string; notes: string }
  | { phase: 'downloading'; version: string; pct: number }
  | { phase: 'installing'; version: string }
  | { phase: 'error'; message: string };

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
  const [update, setUpdate] = useState<UpdateState>({ phase: 'idle' });
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    // Dynamic import — only available in Tauri runtime, not in tests/browser
    let cancelled = false;
    async function checkForUpdate() {
      try {
        const { check } = await import('@tauri-apps/plugin-updater');
        const result = await check();
        if (cancelled || !result?.available) return;
        setUpdate({
          phase: 'available',
          version: result.version,
          notes: result.body ?? '',
        });
        // Store the update object for later use
        (window as unknown as Record<string, unknown>).__tauri_update__ = result;
      } catch {
        // Silently ignore — offline, dev mode, or not in Tauri context
      }
    }
    // Delay 3s so the app loads first
    const t = setTimeout(checkForUpdate, 3000);
    return () => { cancelled = true; clearTimeout(t); };
  }, []);

  async function startUpdate() {
    const result = (window as unknown as Record<string, unknown>).__tauri_update__ as {
      version: string;
      downloadAndInstall: (cb: (ev: { event: string; data?: { contentLength?: number; chunkLength?: number } }) => void) => Promise<void>;
    } | undefined;
    if (!result) return;

    const version = result.version;
    let totalBytes = 0;
    let downloadedBytes = 0;

    setUpdate({ phase: 'downloading', version, pct: 0 });

    try {
      await result.downloadAndInstall((event) => {
        if (event.event === 'Started') {
          totalBytes = event.data?.contentLength ?? 0;
        } else if (event.event === 'Progress') {
          downloadedBytes += event.data?.chunkLength ?? 0;
          const pct = totalBytes > 0 ? Math.round((downloadedBytes / totalBytes) * 100) : 0;
          setUpdate({ phase: 'downloading', version, pct });
        } else if (event.event === 'Finished') {
          setUpdate({ phase: 'installing', version });
        }
      });

      // Restart after install
      const { relaunch } = await import('@tauri-apps/plugin-process');
      await relaunch();
    } catch (e) {
      setUpdate({ phase: 'error', message: String(e) });
    }
  }

  const showBanner = !dismissed && update.phase !== 'idle';

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-bg">
      <Sidebar />

      <main className="flex-1 overflow-hidden flex flex-col">
        {/* Update banner */}
        {showBanner && (
          <div className={cn(
            'flex items-center gap-3 px-5 py-2.5 shrink-0 border-b transition-colors',
            update.phase === 'available' && 'bg-primary-subtle border-primary/20',
            update.phase === 'downloading' && 'bg-info-subtle border-info/20',
            update.phase === 'installing' && 'bg-warning-subtle border-warning/20',
            update.phase === 'error' && 'bg-danger-subtle border-danger/20',
          )}>
            {/* Icon */}
            {update.phase === 'available' && <Sparkles size={13} className="text-primary shrink-0" />}
            {update.phase === 'downloading' && <Download size={13} className="text-info shrink-0 animate-pulse" />}
            {update.phase === 'installing' && <RefreshCw size={13} className="text-warning shrink-0 animate-spin" />}
            {update.phase === 'error' && <XCircle size={13} className="text-danger shrink-0" />}

            {/* Text */}
            {update.phase === 'available' && (
              <p className="text-xs text-white flex-1">
                Nova versão <span className="font-bold text-primary">v{update.version}</span> disponível!
                {update.notes && <span className="text-muted ml-1">— {update.notes}</span>}
              </p>
            )}
            {update.phase === 'downloading' && (
              <div className="flex-1 flex items-center gap-3">
                <p className="text-xs text-info whitespace-nowrap">
                  Baixando v{update.version}…
                </p>
                <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-info rounded-full transition-all duration-300"
                    style={{ width: `${update.pct}%` }}
                  />
                </div>
                <span className="text-xs text-info font-semibold w-8 text-right">{update.pct}%</span>
              </div>
            )}
            {update.phase === 'installing' && (
              <p className="text-xs text-warning flex-1">
                Instalando v{update.version}… O aplicativo vai reiniciar automaticamente.
              </p>
            )}
            {update.phase === 'error' && (
              <p className="text-xs text-danger flex-1">
                Erro na atualização: {update.message}
              </p>
            )}

            {/* Action button */}
            {update.phase === 'available' && (
              <button
                onClick={startUpdate}
                className="text-xs font-semibold bg-primary text-white px-3 py-1 rounded-md hover:bg-primary/80 transition-colors shrink-0"
              >
                Atualizar agora
              </button>
            )}

            {/* Dismiss — only when not in active process */}
            {(update.phase === 'available' || update.phase === 'error') && (
              <button
                onClick={() => setDismissed(true)}
                className="p-0.5 text-muted hover:text-white transition-colors ml-1 shrink-0"
                aria-label="Fechar"
              >
                <X size={13} />
              </button>
            )}
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
