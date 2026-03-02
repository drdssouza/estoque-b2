import { useEffect, useState, useCallback } from 'react';
import {
  Package,
  Droplets,
  Cookie,
  Beef,
  Tag,
  RefreshCw,
  AlertTriangle,
  Receipt,
  TrendingUp,
} from 'lucide-react';
import { getDashboardStats } from '../lib/db';
import { formatCurrency, getStockLevel, getStockPercent } from '../lib/utils';
import { useAppStore } from '../store';
import { Card } from '../components/ui/card';
import { Progress } from '../components/ui/progress';
import { Button } from '../components/ui/button';
import type { DashboardStats, Product } from '../types';

const CATEGORY_ICONS: Record<string, React.ReactNode> = {
  bebida: <Droplets size={20} />,
  doce: <Cookie size={20} />,
  salgado: <Beef size={20} />,
  acessório: <Tag size={20} />,
  acessorio: <Tag size={20} />,
};

const CATEGORY_COLORS: Record<string, string> = {
  bebida: 'text-info bg-info-subtle border-info/20',
  doce: 'text-purple bg-purple-subtle border-purple/20',
  salgado: 'text-warning bg-warning-subtle border-warning/20',
  acessório: 'text-pink-400 bg-pink-400/10 border-pink-400/20',
  acessorio: 'text-pink-400 bg-pink-400/10 border-pink-400/20',
};

function StatCard({
  icon,
  label,
  value,
  sub,
  colorClass,
}: {
  icon: React.ReactNode;
  label: string;
  value: number | string;
  sub?: string;
  colorClass?: string;
}) {
  return (
    <Card className="flex items-center gap-4">
      <div
        className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 border ${
          colorClass ?? 'text-primary bg-primary-subtle border-primary/20'
        }`}
      >
        {icon}
      </div>
      <div className="min-w-0">
        <p className="text-xs text-muted uppercase tracking-wider truncate">{label}</p>
        <p className="text-2xl font-bold text-white mt-0.5">{value}</p>
        {sub && <p className="text-xs text-muted">{sub}</p>}
      </div>
    </Card>
  );
}

function StockAlertRow({ product }: { product: Product }) {
  const level = getStockLevel(product.current_stock, product.minimum_stock);
  const pct = getStockPercent(product.current_stock, product.minimum_stock);

  const progressColor = level === 'critical' ? 'red' : level === 'warning' ? 'yellow' : 'green';
  const dotColor =
    level === 'critical' ? 'bg-danger' : level === 'warning' ? 'bg-warning' : 'bg-primary';

  return (
    <div className="flex items-center gap-3 py-3 border-b border-border last:border-0">
      <div className={`w-2 h-2 rounded-full shrink-0 ${dotColor}`} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2 mb-1">
          <span className="text-sm text-white truncate">{product.name}</span>
          <span className="text-xs text-muted shrink-0">
            {product.current_stock} / {product.minimum_stock} ({pct}%)
          </span>
        </div>
        <Progress value={pct} color={progressColor} />
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState('');
  const { setLowStockCount } = useAppStore();

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const s = await getDashboardStats();
      setStats(s);
      setLowStockCount(s.lowStock.length);
      setLastUpdate(
        new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
      );
    } finally {
      setLoading(false);
    }
  }, [setLowStockCount]);

  useEffect(() => {
    load();
    const interval = setInterval(load, 30_000);
    return () => clearInterval(interval);
  }, [load]);

  const categories = ['bebida', 'doce', 'salgado', 'acessório'];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Dashboard</h1>
          {lastUpdate && (
            <p className="text-xs text-muted mt-0.5">Atualizado às {lastUpdate}</p>
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          icon={<RefreshCw size={14} className={loading ? 'animate-spin' : ''} />}
          onClick={load}
          isLoading={false}
        >
          Atualizar
        </Button>
      </div>

      {/* Quick stats row */}
      <div className="grid grid-cols-2 gap-3">
        <StatCard
          icon={<Receipt size={20} />}
          label="Comandas Abertas"
          value={stats?.openOrders ?? '—'}
          colorClass="text-info bg-info-subtle border-info/20"
        />
        <StatCard
          icon={<TrendingUp size={20} />}
          label="Receita Hoje"
          value={stats ? formatCurrency(stats.todayRevenue) : '—'}
          colorClass="text-primary bg-primary-subtle border-primary/20"
        />
      </div>

      {/* Product category cards */}
      <div className="grid grid-cols-5 gap-3">
        <StatCard
          icon={<Package size={20} />}
          label="Total Produtos"
          value={stats?.totalProducts ?? '—'}
        />
        {categories.map((cat) => (
          <StatCard
            key={cat}
            icon={CATEGORY_ICONS[cat] ?? <Package size={20} />}
            label={cat.charAt(0).toUpperCase() + cat.slice(1) + 's'}
            value={stats?.byCategory[cat] ?? 0}
            colorClass={CATEGORY_COLORS[cat]}
          />
        ))}
      </div>

      {/* Low stock alerts */}
      <Card noPad>
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <div className="flex items-center gap-2">
            <AlertTriangle size={16} className="text-warning" />
            <span className="text-sm font-semibold text-white">
              Alertas de Estoque Baixo
            </span>
            {stats && stats.lowStock.length > 0 && (
              <span className="text-xs font-bold text-warning bg-warning-subtle border border-warning/20 px-2 py-0.5 rounded-full">
                {stats.lowStock.length}
              </span>
            )}
          </div>
        </div>

        <div className="px-5">
          {loading ? (
            <div className="py-8 flex justify-center">
              <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            </div>
          ) : !stats || stats.lowStock.length === 0 ? (
            <div className="py-10 text-center">
              <div className="w-10 h-10 rounded-xl bg-primary-subtle border border-primary/20 flex items-center justify-center mx-auto mb-3">
                <Package size={20} className="text-primary" />
              </div>
              <p className="text-sm text-white font-medium">Estoque em dia!</p>
              <p className="text-xs text-muted mt-1">
                Todos os produtos estão acima do estoque mínimo.
              </p>
            </div>
          ) : (
            <div>
              {stats.lowStock.map((p) => (
                <StockAlertRow key={p.id} product={p} />
              ))}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
