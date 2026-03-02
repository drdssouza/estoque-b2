import { useEffect, useState, useCallback } from 'react';
import {
  TrendingUp,
  RefreshCw,
  DollarSign,
  ShoppingBag,
  Calendar,
  BarChart3,
  Award,
  CheckCircle,
  Clock,
  Filter,
  X,
} from 'lucide-react';
import { getReportStats } from '../lib/db';
import { formatCurrency } from '../lib/utils';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import type { ReportStats } from '../types';

function RevenueCard({
  label,
  icon,
  total,
  count,
  accent,
}: {
  label: string;
  icon: React.ReactNode;
  total: number;
  count: number;
  accent?: string;
}) {
  return (
    <Card className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-wider text-muted">{label}</p>
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${accent ?? 'bg-primary-subtle'}`}>
          {icon}
        </div>
      </div>
      <div>
        <p className="text-2xl font-bold text-white">{formatCurrency(total)}</p>
        <p className="text-xs text-muted mt-0.5">
          {count} comanda{count !== 1 ? 's' : ''} fechada{count !== 1 ? 's' : ''}
        </p>
      </div>
    </Card>
  );
}

function formatDateBR(dateStr: string) {
  if (!dateStr) return '';
  const [y, m, d] = dateStr.split('-');
  return `${d}/${m}/${y}`;
}

export default function Reports() {
  const [stats, setStats] = useState<ReportStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState('');

  const [filterFrom, setFilterFrom] = useState('');
  const [filterTo, setFilterTo] = useState('');
  const [activeFilter, setActiveFilter] = useState<{ from: string; to: string } | null>(null);

  const loadStats = useCallback(async (from?: string, to?: string) => {
    setLoading(true);
    try {
      setStats(await getReportStats(from, to));
      setLastUpdate(
        new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  function applyFilter() {
    if (!filterFrom || !filterTo) return;
    setActiveFilter({ from: filterFrom, to: filterTo });
    loadStats(filterFrom, filterTo);
  }

  function clearFilter() {
    setFilterFrom('');
    setFilterTo('');
    setActiveFilter(null);
    loadStats();
  }

  const maxQty = stats?.topProducts[0]?.total_qty ?? 1;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Relatórios</h1>
          {lastUpdate && (
            <p className="text-xs text-muted mt-0.5">Atualizado às {lastUpdate}</p>
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          icon={<RefreshCw size={14} className={loading ? 'animate-spin' : ''} />}
          onClick={() => loadStats(activeFilter?.from, activeFilter?.to)}
        >
          Atualizar
        </Button>
      </div>

      {/* Date filter bar */}
      <div className="flex items-end gap-3 p-4 bg-card rounded-xl border border-border">
        <Filter size={14} className="text-muted shrink-0 mb-2.5" />
        <div className="flex-1">
          <label className="block text-xs text-muted mb-1.5">De</label>
          <input
            type="date"
            value={filterFrom}
            onChange={(e) => setFilterFrom(e.target.value)}
            className="[color-scheme:dark] w-full bg-bg border border-border rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary transition-colors"
          />
        </div>
        <div className="flex-1">
          <label className="block text-xs text-muted mb-1.5">Até</label>
          <input
            type="date"
            value={filterTo}
            onChange={(e) => setFilterTo(e.target.value)}
            min={filterFrom || undefined}
            className="[color-scheme:dark] w-full bg-bg border border-border rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary transition-colors"
          />
        </div>
        <Button
          variant="primary"
          size="md"
          icon={<Filter size={13} />}
          onClick={applyFilter}
          disabled={!filterFrom || !filterTo}
        >
          Filtrar
        </Button>
        {activeFilter && (
          <Button
            variant="ghost"
            size="md"
            icon={<X size={13} />}
            onClick={clearFilter}
          >
            Limpar
          </Button>
        )}
      </div>

      {/* Active filter badge */}
      {activeFilter && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-primary-subtle border border-primary/20">
          <Calendar size={12} className="text-primary shrink-0" />
          <span className="text-xs text-primary font-medium">
            Exibindo dados de{' '}
            <span className="font-bold">{formatDateBR(activeFilter.from)}</span>
            {' '}até{' '}
            <span className="font-bold">{formatDateBR(activeFilter.to)}</span>
          </span>
        </div>
      )}

      {loading && !stats ? (
        <div className="py-20 flex justify-center">
          <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      ) : !stats ? null : (
        <>
          {/* Revenue cards */}
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-muted mb-3 flex items-center gap-2">
              <TrendingUp size={12} className="text-primary" />
              {activeFilter ? 'Receita no Período' : 'Receita por Período'}
            </p>

            {activeFilter ? (
              /* Single period card when filter is active */
              <div className="grid grid-cols-4 gap-3">
                <RevenueCard
                  label={`${formatDateBR(activeFilter.from)} – ${formatDateBR(activeFilter.to)}`}
                  icon={<Calendar size={14} className="text-primary" />}
                  total={stats.allTime.total}
                  count={stats.allTime.count}
                  accent="bg-primary-subtle"
                />
              </div>
            ) : (
              <div className="grid grid-cols-4 gap-3">
                <RevenueCard
                  label="Hoje"
                  icon={<DollarSign size={14} className="text-primary" />}
                  total={stats.today.total}
                  count={stats.today.count}
                  accent="bg-primary-subtle"
                />
                <RevenueCard
                  label="Últimos 7 dias"
                  icon={<Calendar size={14} className="text-info" />}
                  total={stats.week.total}
                  count={stats.week.count}
                  accent="bg-info-subtle"
                />
                <RevenueCard
                  label="Este mês"
                  icon={<BarChart3 size={14} className="text-purple" />}
                  total={stats.month.total}
                  count={stats.month.count}
                  accent="bg-purple-subtle"
                />
                <RevenueCard
                  label="Total geral"
                  icon={<TrendingUp size={14} className="text-warning" />}
                  total={stats.allTime.total}
                  count={stats.allTime.count}
                  accent="bg-warning-subtle"
                />
              </div>
            )}
          </div>

          {/* Status + Monthly side by side */}
          <div className="grid grid-cols-2 gap-5">
            {/* Orders by status */}
            <Card>
              <div className="flex items-center gap-2 mb-4">
                <ShoppingBag size={14} className="text-primary" />
                <p className="text-xs font-semibold uppercase tracking-wider text-muted">
                  Comandas por Status
                </p>
              </div>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CheckCircle size={14} className="text-muted" />
                    <span className="text-sm text-white">Fechadas</span>
                  </div>
                  <Badge variant="gray">{stats.byStatus['fechada'] ?? 0}</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Clock size={14} className="text-primary" />
                    <span className="text-sm text-white">Abertas</span>
                  </div>
                  <Badge variant="green">{stats.byStatus['aberta'] ?? 0}</Badge>
                </div>
                <div className="pt-2 border-t border-border">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted">Total de comandas</span>
                    <span className="text-sm font-bold text-white">
                      {(stats.byStatus['aberta'] ?? 0) + (stats.byStatus['fechada'] ?? 0)}
                    </span>
                  </div>
                </div>
              </div>
            </Card>

            {/* Monthly revenue */}
            <Card>
              <div className="flex items-center gap-2 mb-4">
                <BarChart3 size={14} className="text-primary" />
                <p className="text-xs font-semibold uppercase tracking-wider text-muted">
                  {activeFilter ? 'Histórico no Período' : 'Histórico Mensal'}
                </p>
              </div>
              {stats.monthly.length === 0 ? (
                <p className="text-sm text-muted text-center py-4">Sem dados ainda.</p>
              ) : (
                <div className="space-y-3">
                  {stats.monthly.map((m) => {
                    const maxRev = Math.max(...stats.monthly.map((x) => x.revenue), 1);
                    const pct = Math.round((m.revenue / maxRev) * 100);
                    return (
                      <div key={m.month}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs text-muted">{m.month}</span>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-muted">{m.count} cmd</span>
                            <span className="text-xs font-semibold text-white">
                              {formatCurrency(m.revenue)}
                            </span>
                          </div>
                        </div>
                        <Progress value={pct} color="green" />
                      </div>
                    );
                  })}
                </div>
              )}
            </Card>
          </div>

          {/* Top products */}
          <Card noPad>
            <div className="flex items-center gap-2 px-5 py-4 border-b border-border">
              <Award size={14} className="text-warning" />
              <p className="text-xs font-semibold uppercase tracking-wider text-muted">
                Produtos Mais Vendidos
              </p>
            </div>

            {stats.topProducts.length === 0 ? (
              <div className="py-10 text-center">
                <p className="text-sm text-muted">
                  Nenhuma comanda fechada ainda. Os dados aparecerão aqui após fechar comandas.
                </p>
              </div>
            ) : (
              <div>
                {stats.topProducts.map((p, i) => {
                  const pct = Math.round((p.total_qty / maxQty) * 100);
                  return (
                    <div
                      key={p.name}
                      className={`flex items-center gap-4 px-5 py-3.5 border-b border-border last:border-0 ${
                        i % 2 === 0 ? '' : 'bg-white/[0.02]'
                      }`}
                    >
                      {/* Rank */}
                      <div
                        className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                          i === 0
                            ? 'bg-warning-subtle text-warning'
                            : i === 1
                            ? 'bg-zinc-700 text-zinc-300'
                            : i === 2
                            ? 'bg-orange-900/30 text-orange-400'
                            : 'bg-white/5 text-muted'
                        }`}
                      >
                        {i + 1}
                      </div>

                      {/* Name + bar */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1.5">
                          <p className="text-sm font-medium text-white truncate">{p.name}</p>
                          <div className="flex items-center gap-3 shrink-0">
                            <span className="text-xs text-muted">{p.total_qty} un.</span>
                            <span className="text-sm font-semibold text-primary">
                              {formatCurrency(p.revenue)}
                            </span>
                          </div>
                        </div>
                        <Progress value={pct} color="green" />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </Card>
        </>
      )}
    </div>
  );
}
