import { useEffect, useState } from 'react';
import { Key, HardDrive, Info, Check, Save, Bell } from 'lucide-react';
import { getSetting, setSetting } from '../lib/db';
import { backupTimestamp } from '../lib/utils';
import { invoke } from '@tauri-apps/api/core';
import { save } from '@tauri-apps/plugin-dialog';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardHeader, CardTitle } from '../components/ui/card';
import { useAppStore } from '../store';

export default function Settings() {
  const { addToast, pixKey: storedPixKey, setPixKey: setStoredPixKey } = useAppStore();

  const [pixKey, setPixKey] = useState('');
  const [savingPix, setSavingPix] = useState(false);
  const [pixSaved, setPixSaved] = useState(false);

  const [staleDays, setStaleDays] = useState('3');
  const [savingStale, setSavingStale] = useState(false);
  const [staleSaved, setStaleSaved] = useState(false);

  const [backingUp, setBackingUp] = useState(false);

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
      await invoke('backup_database', { destPath: dest });
      addToast(`Backup salvo com sucesso!`);
    } catch (e) {
      addToast(`Erro ao fazer backup: ${e}`, 'error');
    } finally {
      setBackingUp(false);
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
            <span className="text-xs text-primary font-semibold">v2.0.1</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted">Desenvolvido por</span>
            <span className="text-xs text-white">Eduardo Schrotke</span>
          </div>
        </div>
      </Card>
    </div>
  );
}
