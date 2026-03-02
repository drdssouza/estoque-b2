import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Package,
  Receipt,
  ArrowLeftRight,
  Settings,
  HardDrive,
  AlertTriangle,
  Users,
  BarChart3,
} from 'lucide-react';
import { cn, backupTimestamp } from '../../lib/utils';
import { useAppStore } from '../../store';
import { save } from '@tauri-apps/plugin-dialog';
import { invoke } from '@tauri-apps/api/core';

const NAV = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/products', icon: Package, label: 'Produtos' },
  { to: '/orders', icon: Receipt, label: 'Comandas' },
  { to: '/customers', icon: Users, label: 'Clientes' },
  { to: '/movements', icon: ArrowLeftRight, label: 'Movimentações' },
  { to: '/reports', icon: BarChart3, label: 'Relatórios' },
  { to: '/settings', icon: Settings, label: 'Configurações' },
];

export default function Sidebar() {
  const { lowStockCount, addToast } = useAppStore();

  async function handleBackup() {
    try {
      const dest = await save({
        title: 'Salvar backup do banco de dados',
        defaultPath: `backup_controle_b2_${backupTimestamp()}.db`,
        filters: [{ name: 'Banco de Dados', extensions: ['db'] }],
      });
      if (!dest) return;
      await invoke('backup_database', { destPath: dest });
      addToast('Backup salvo com sucesso!', 'success');
    } catch (e) {
      addToast(`Erro ao fazer backup: ${e}`, 'error');
    }
  }

  return (
    <aside className="flex flex-col w-60 shrink-0 h-full bg-sidebar border-r border-border">
      {/* Logo */}
      <div className="px-5 py-6 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center shrink-0">
            <Package size={16} className="text-black" />
          </div>
          <div>
            <p className="text-sm font-bold text-white tracking-tight">CONTROLE B2</p>
            <p className="text-[10px] text-muted">v2.0.0 — Arena B2</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-150 group',
                isActive
                  ? 'bg-primary-subtle text-primary border border-primary/20'
                  : 'text-muted hover:text-white hover:bg-white/5'
              )
            }
          >
            {({ isActive }) => (
              <>
                <Icon
                  size={16}
                  className={cn(
                    'shrink-0 transition-colors',
                    isActive ? 'text-primary' : 'text-muted group-hover:text-white'
                  )}
                />
                <span className="flex-1">{label}</span>

                {/* Low stock badge on Dashboard */}
                {to === '/dashboard' && lowStockCount > 0 && (
                  <span className="flex items-center gap-1 text-[10px] font-bold text-warning bg-warning-subtle border border-warning/20 px-1.5 py-0.5 rounded-full">
                    <AlertTriangle size={9} />
                    {lowStockCount}
                  </span>
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Backup button */}
      <div className="px-3 pb-4 border-t border-border pt-3">
        <button
          onClick={handleBackup}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-muted hover:text-white hover:bg-white/5 transition-all group"
        >
          <HardDrive size={16} className="shrink-0 group-hover:text-primary transition-colors" />
          <span>Fazer Backup</span>
        </button>
      </div>
    </aside>
  );
}
