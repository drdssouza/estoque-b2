import { useEffect, useState } from 'react';
import { Key, HardDrive, Info, Check, Save, Bell, RotateCcw, FileCheck2 } from 'lucide-react';
import { getSetting, setSetting, checkpointDb, closeDb, readBackupSummary, initDb } from '../lib/db';
import type { BackupSummary } from '../lib/db';
import { backupTimestamp, formatDateTime } from '../lib/utils';
import { invoke } from '@tauri-apps/api/core';
import { getVersion } from '@tauri-apps/api/app';
import { save, open } from '@tauri-apps/plugin-dialog';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardHeader, CardTitle } from '../components/ui/card';
import { ConfirmDialog } from '../components/shared/ConfirmDialog';
import { useAppStore } from '../store';

export default function Settings() {
  const { addToast, pixKey: storedPixKey, setPixKey: setStoredPixKey } = useAppStore();

  const [pixKey, setPixKey] = useState('');
  const [savingPix, setSavingPix] = useState(false);
  const [pixSaved, setPixSaved] = useState(false);

  const [restoreFile, setRestoreFile] = useState<string | null>(null);
  const [restoreSummary, setRestoreSummary] = useState<BackupSummary | null>(null);
  const [confirmRestore, setConfirmRestore] = useState(false);
  const [restoring, setRestoring] = useState(false);

  const [staleDays, setStaleDays] = useState('3');
  const [savingStale, setSavingStale] = useState(false);
  const [staleSaved, setStaleSaved] = useState(false);

  const [backingUp, setBackingUp] = useState(false);
  const [appVersion, setAppVersion] = useState('');

  useEffect(() => {
    if (storedPixKey) {
      setPixKey(storedPixKey);
    } else {
      getSetting('pix_key').then((v) => {
        setPixKey(v);
        setStoredPixKey(v);
      });
    }
    getSetting('stale_order_days', '3').then(setStaleDays);
    getVersion().then(setAppVersion).catch(() => { /* fora do Tauri */ });
  }, [storedPixKey, setStoredPixKey]);

  async function handleSavePix() {
    setSavingPix(true);
    try {
      await setSetting('pix_key', pixKey.trim());
      setStoredPixKey(pixKey.trim());
      setPixSaved(true);
      addToast('Chave PIX salva!');
      setTimeout(() => setPixSaved(false), 2000);
    } catch (e) {
      addToast(`Erro: ${e}`, 'error');
    } finally {
      setSavingPix(false);
    }
  }

  async function handleSaveStale() {
    const val = Math.max(1, Math.min(90, parseInt(staleDays) || 3));
    setStaleDays(String(val));
    setSavingStale(true);
    try {
      await setSetting('stale_order_days', String(val));
      setStaleSaved(true);
      addToast('Configuração salva!');
      setTimeout(() => setStaleSaved(false), 2000);
    } catch (e) {
      addToast(`Erro: ${e}`, 'error');
    } finally {
      setSavingStale(false);
    }
  }

  async function handleBackup() {
    setBackingUp(true);
    try {
      const dest = await save({
        title: 'Salvar backup do banco de dados',
        defaultPath: `backup_controle_b2_${backupTimestamp()}.db`,
        filters: [{ name: 'Banco de Dados SQLite', extensions: ['db'] }],
      });
      if (!dest) {
        setBackingUp(false);
        return;
      }
      // Grava o WAL dentro do .db antes de copiar, senão o backup sai incompleto
      await checkpointDb();
      await invoke('backup_database', { destPath: dest });
      addToast(`Backup salvo com sucesso!`);
    } catch (e) {
      addToast(`Erro ao fazer backup: ${e}`, 'error');
    } finally {
      setBackingUp(false);
    }
  }

  async function pickRestoreFile() {
    const picked = await open({
      title: 'Escolher arquivo de backup',
      multiple: false,
      directory: false,
      filters: [{ name: 'Backup do Controle B2', extensions: ['db'] }],
    });
    if (typeof picked !== 'string') return;
    setRestoreFile(picked);
    setRestoreSummary(await readBackupSummary(picked));
  }

  async function handleRestore() {
    if (!restoreFile) return;
    setRestoring(true);
    try {
      // A conexão precisa cair antes de o arquivo ser trocado embaixo dela.
      await closeDb();
      await invoke('restore_database', {
        srcPath: restoreFile,
        stamp: backupTimestamp(),
      });
      addToast('Backup restaurado! Reiniciando o programa...');
      const { relaunch } = await import('@tauri-apps/plugin-process');
      await relaunch();
    } catch (e) {
      // Reabre o banco atual para o app continuar utilizável.
      try { await initDb(); } catch { /* o reinício resolve */ }
      addToast(`Erro ao restaurar: ${e}`, 'error');
      setConfirmRestore(false);
    } finally {
      setRestoring(false);
    }
  }

  return (
    <div className="space-y-6 animate-fade-in max-w-lg">
      <h1 className="text-xl font-bold text-white">Configurações</h1>

      {/* PIX Key */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Key size={14} className="text-primary" />
            <CardTitle>Chave PIX</CardTitle>
          </div>
        </CardHeader>

        <div className="space-y-3">
          <p className="text-xs text-muted">
            A chave PIX aparece no rodapé dos PDFs e nas mensagens de WhatsApp.
          </p>
          <Input
            placeholder="email@exemplo.com, CPF, telefone..."
            value={pixKey}
            onChange={(e) => setPixKey(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSavePix()}
          />
          <Button
            variant={pixSaved ? 'primary' : 'secondary'}
            size="md"
            icon={pixSaved ? <Check size={14} /> : <Save size={14} />}
            onClick={handleSavePix}
            isLoading={savingPix}
          >
            {pixSaved ? 'Salvo!' : 'Salvar chave PIX'}
          </Button>
        </div>
      </Card>

      {/* Backup */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <HardDrive size={14} className="text-primary" />
            <CardTitle>Backup dos Dados</CardTitle>
          </div>
        </CardHeader>

        <div className="space-y-3">
          <p className="text-xs text-muted">
            Copia o arquivo do banco de dados SQLite para um local de sua escolha.
            Guarde em um lugar seguro como um pendrive ou serviço de nuvem.
          </p>
          <Button
            variant="secondary"
            size="md"
            icon={<HardDrive size={14} />}
            onClick={handleBackup}
            isLoading={backingUp}
          >
            {backingUp ? 'Fazendo backup...' : 'Fazer Backup Agora'}
          </Button>
        </div>
      </Card>

      {/* Restaurar backup */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <RotateCcw size={14} className="text-warning" />
            <CardTitle>Restaurar Backup</CardTitle>
          </div>
        </CardHeader>

        <div className="space-y-3">
          <p className="text-xs text-muted">
            Traz de volta os dados de um arquivo de backup (.db). Use ao trocar de
            computador ou depois de reinstalar o programa. Os dados atuais são
            substituídos — mas uma cópia deles é guardada automaticamente antes.
          </p>

          {!restoreFile ? (
            <Button
              variant="secondary"
              size="md"
              icon={<RotateCcw size={14} />}
              onClick={pickRestoreFile}
            >
              Escolher arquivo de backup
            </Button>
          ) : (
            <div className="space-y-3">
              <div className="rounded-lg border border-border bg-white/[0.02] p-3 space-y-2">
                <div className="flex items-start gap-2">
                  <FileCheck2 size={14} className="text-info shrink-0 mt-0.5" />
                  <p className="text-xs text-white break-all">
                    {restoreFile.split(/[\\/]/).pop()}
                  </p>
                </div>

                {restoreSummary ? (
                  <div className="pl-6 space-y-1">
                    <p className="text-[11px] text-muted">
                      Contém{' '}
                      <span className="text-white font-semibold">{restoreSummary.orders}</span> comanda(s),{' '}
                      <span className="text-white font-semibold">{restoreSummary.products}</span> produto(s) e{' '}
                      <span className="text-white font-semibold">{restoreSummary.customers}</span> cliente(s).
                    </p>
                    {restoreSummary.lastOrderDate && (
                      <p className="text-[11px] text-muted">
                        Comanda mais recente: {formatDateTime(restoreSummary.lastOrderDate)}
                      </p>
                    )}
                  </div>
                ) : (
                  <p className="pl-6 text-[11px] text-danger">
                    Não consegui ler este arquivo. Confira se é mesmo um backup do Controle B2.
                  </p>
                )}
              </div>

              <div className="flex gap-2">
                <Button variant="ghost" size="md" onClick={() => { setRestoreFile(null); setRestoreSummary(null); }}>
                  Escolher outro
                </Button>
                <Button
                  variant="warning"
                  size="md"
                  icon={<RotateCcw size={14} />}
                  onClick={() => setConfirmRestore(true)}
                  disabled={!restoreSummary}
                >
                  Restaurar este backup
                </Button>
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* Stale order alert */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Bell size={14} className="text-warning" />
            <CardTitle>Alerta de Comandas Antigas</CardTitle>
          </div>
        </CardHeader>
        <div className="space-y-3">
          <p className="text-xs text-muted">
            Exibe um aviso visual nas comandas que estão abertas há mais de X dias, para facilitar o controle.
          </p>
          <div className="flex items-center gap-3">
            <input
              type="number"
              min="1"
              max="90"
              value={staleDays}
              onChange={(e) => setStaleDays(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSaveStale()}
              className="w-20 bg-bg border border-border rounded-lg px-3 py-2 text-sm text-white text-center focus:outline-none focus:border-primary transition-colors"
            />
            <span className="text-sm text-muted">dia(s) aberta sem fechar</span>
          </div>
          <Button
            variant={staleSaved ? 'primary' : 'secondary'}
            size="md"
            icon={staleSaved ? <Check size={14} /> : <Save size={14} />}
            onClick={handleSaveStale}
            isLoading={savingStale}
          >
            {staleSaved ? 'Salvo!' : 'Salvar'}
          </Button>
        </div>
      </Card>

      {/* About */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Info size={14} className="text-primary" />
            <CardTitle>Sobre</CardTitle>
          </div>
        </CardHeader>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted">Aplicativo</span>
            <span className="text-xs text-white font-medium">Controle B2</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted">Versão</span>
            <span className="text-xs text-primary font-semibold">{appVersion ? `v${appVersion}` : '—'}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted">Desenvolvido por</span>
            <span className="text-xs text-white">Eduardo Schrotke</span>
          </div>
        </div>
      </Card>
      <ConfirmDialog
        open={confirmRestore}
        onClose={() => setConfirmRestore(false)}
        onConfirm={handleRestore}
        variant="danger"
        title="Restaurar este backup?"
        message={
          restoreSummary
            ? `Os dados atuais serão substituídos pelos do backup (${restoreSummary.orders} comanda(s), ${restoreSummary.products} produto(s)). Uma cópia dos dados atuais é guardada automaticamente antes da troca. O programa vai reiniciar em seguida.`
            : ''
        }
        confirmLabel="Restaurar e reiniciar"
        isLoading={restoring}
      />
    </div>
  );
}
