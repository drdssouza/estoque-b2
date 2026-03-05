import { useEffect, useState, useCallback, useRef } from 'react';
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
  Search,
  User,
  Receipt,
} from 'lucide-react';
import { getReportStats, getCustomerSpending, getTopCustomers, getCustomerNames, getOrderItems } from '../lib/db';
import { formatCurrency, formatDateTime } from '../lib/utils';
import type { OrderItem } from '../types';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import type { ReportStats, CustomerSpending, TopCustomer } from '../types';

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

  // Customer search
  const [clienteSearch, setClienteSearch] = useState('');
  const [allCustomerNames, setAllCustomerNames] = useState<string[]>([]);
  const [clienteSuggestions, setClienteSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [clienteData, setClienteData] = useState<CustomerSpending | null>(null);
  const [topClientes, setTopClientes] = useState<TopCustomer[]>([]);
  const [loadingCliente, setLoadingCliente] = useState(false);
  const [clienteNotFound, setClienteNotFound] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

  // Expandable order items
  const [expandedOrderId, setExpandedOrderId] = useState<number | null>(null);
  const [orderItemsCache, setOrderItemsCache] = useState<Record<number, (OrderItem & { product_name: string })[]>>({});

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
    getTopCustomers(15).then(setTopClientes);
    getCustomerNames().then(setAllCustomerNames);
  }, [loadStats]);

  // Close suggestions when clicking outside
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  function applyFilter() {
    if (!filterFrom || !filterTo) return;
    setActiveFilter({ from: filterFrom, to: filterTo });
    loadStats(filterFrom, filterTo);
    getTopCustomers(15, filterFrom, filterTo).then(setTopClientes);
  }

  function clearFilter() {
    setFilterFrom('');
    setFilterTo('');
    setActiveFilter(null);
    loadStats();
    getTopCustomers(15).then(setTopClientes);
  }

  function onClienteInput(value: string) {
    setClienteSearch(value);
    setClienteNotFound(false);
    if (value.trim().length < 2) {
      setClienteSuggestions([]);
      setShowSuggestions(false);
      return;
    }
    const lower = value.toLowerCase();
    const filtered = allCustomerNames
      .filter((n) => n.toLowerCase().includes(lower))
      .slice(0, 8);
    setClienteSuggestions(filtered);
    setShowSuggestions(filtered.length > 0);
  }

  async function buscarCliente(name: string) {
    const searchName = name || clienteSearch;
    if (!searchName.trim()) return;
    setShowSuggestions(false);
    setClienteSearch(searchName);
    setLoadingCliente(true);
    setClienteData(null);
    setClienteNotFound(false);
    try {
      const result = await getCustomerSpending(searchName);
      if (result) {
        setClienteData(result);
      } else {
        setClienteNotFound(true);
      }
    } finally {
      setLoadingCliente(false);
    }
  }

  async function toggleOrderExpand(orderId: number) {
    if (expandedOrderId === orderId) {
      setExpandedOrderId(null);
      return;
    }
    setExpandedOrderId(orderId);
    if (!orderItemsCache[orderId]) {
      const items = await getOrderItems(orderId);
      setOrderItemsCache((prev) => ({ ...prev, [orderId]: items }));
    }
  }

  const maxQty = stats?.topProducts[0]?.total_qty ?? 1;
  const maxTopTotal = topClientes[0]?.total ?? 1;

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

          {/* Customer section */}
          <div className="grid grid-cols-2 gap-5">
            {/* Customer search */}
            <Card>
              <div className="flex items-center gap-2 mb-4">
                <User size={14} className="text-info" />
                <p className="text-xs font-semibold uppercase tracking-wider text-muted">
                  Busca por Cliente
                </p>
              </div>

              <div ref={searchRef} className="relative mb-4">
                <div className="relative">
                  <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted pointer-events-none" />
                  <input
                    type="text"
                    placeholder="Nome do cliente..."
                    value={clienteSearch}
                    onChange={(e) => onClienteInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && buscarCliente('')}
                    className="w-full bg-bg border border-border rounded-lg pl-9 pr-3 py-2 text-sm text-white placeholder:text-muted focus:outline-none focus:border-primary transition-colors"
                  />
                </div>

                {showSuggestions && (
                  <div className="absolute z-10 w-full mt-1 bg-card border border-border rounded-lg shadow-xl overflow-hidden">
                    {clienteSuggestions.map((name) => (
                      <button
                        key={name}
                        className="w-full px-3 py-2 text-sm text-left text-white hover:bg-white/5 transition-colors"
                        onMouseDown={() => buscarCliente(name)}
                      >
                        {name}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <Button
                variant="primary"
                size="sm"
                icon={<Search size={13} />}
                onClick={() => buscarCliente('')}
                disabled={!clienteSearch.trim() || loadingCliente}
                className="w-full mb-4"
              >
                {loadingCliente ? 'Buscando...' : 'Buscar'}
              </Button>

              {clienteNotFound && (
                <p className="text-sm text-muted text-center py-2">
                  Nenhum cliente encontrado com esse nome.
                </p>
              )}

              {clienteData && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 pb-3 border-b border-border">
                    <div className="w-8 h-8 rounded-full bg-info-subtle flex items-center justify-center shrink-0">
                      <User size={14} className="text-info" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-white">{clienteData.customer_name}</p>
                      <p className="text-xs text-muted">{clienteData.count} comanda{clienteData.count !== 1 ? 's' : ''} fechada{clienteData.count !== 1 ? 's' : ''}</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 rounded-lg bg-bg border border-border">
                      <p className="text-xs text-muted mb-0.5">Total gasto</p>
                      <p className="text-lg font-bold text-primary">{formatCurrency(clienteData.total)}</p>
                    </div>
                    <div className="p-3 rounded-lg bg-bg border border-border">
                      <p className="text-xs text-muted mb-0.5">Ticket médio</p>
                      <p className="text-lg font-bold text-white">{formatCurrency(clienteData.avg_ticket)}</p>
                    </div>
                  </div>

                  <div>
                    <p className="text-xs text-muted mb-2 flex items-center gap-1.5">
                      <Receipt size={11} />
                      Últimas comandas <span className="text-zinc-600">(clique para ver os itens)</span>
                    </p>
                    <div className="space-y-1 max-h-72 overflow-y-auto pr-1">
                      {clienteData.orders.slice(0, 10).map((o) => {
                        const isOpen = expandedOrderId === o.id;
                        const items = orderItemsCache[o.id];
                        return (
                          <div key={o.id}>
                            <button
                              onClick={() => toggleOrderExpand(o.id)}
                              className="w-full flex items-center justify-between text-xs py-2 px-2 rounded-md hover:bg-white/5 transition-colors cursor-pointer"
                            >
                              <div className="flex items-center gap-1.5">
                                <span className={`transition-transform ${isOpen ? 'rotate-90' : ''}`} style={{ display: 'inline-block' }}>›</span>
                                <span className="text-muted">{formatDateTime(o.created_at)}</span>
                              </div>
                              <span className="font-semibold text-white">{formatCurrency(o.total)}</span>
                            </button>
                            {isOpen && (
                              <div className="ml-4 mb-1 rounded-md bg-white/[0.03] border border-border overflow-hidden">
                                {!items ? (
                                  <div className="py-3 text-center">
                                    <div className="w-3 h-3 border border-primary border-t-transparent rounded-full animate-spin inline-block" />
                                  </div>
                                ) : items.length === 0 ? (
                                  <p className="text-xs text-muted px-3 py-2">Sem itens registrados.</p>
                                ) : (
                                  <table className="w-full text-xs">
                                    <thead>
                                      <tr className="border-b border-border">
                                        <th className="text-left px-3 py-1.5 text-muted font-medium">Produto</th>
                                        <th className="text-center px-2 py-1.5 text-muted font-medium">Qtd</th>
                                        <th className="text-right px-3 py-1.5 text-muted font-medium">Subtotal</th>
                                      </tr>
                                    </thead>
                                    <tbody>
                                      {items.map((item) => (
                                        <tr key={item.id} className="border-b border-border/50 last:border-0">
                                          <td className="px-3 py-1.5 text-white">{item.product_name}</td>
                                          <td className="px-2 py-1.5 text-center text-muted">{item.quantity}</td>
                                          <td className="px-3 py-1.5 text-right text-primary font-semibold">{formatCurrency(item.subtotal)}</td>
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                )}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}

              {!clienteData && !clienteNotFound && !loadingCliente && (
                <p className="text-xs text-muted text-center py-4">
                  Digite o nome do cliente para ver o histórico de gastos.
                </p>
              )}
            </Card>

            {/* Top customers ranking */}
            <Card noPad>
              <div className="flex items-center gap-2 px-4 py-3.5 border-b border-border">
                <Award size={14} className="text-info" />
                <p className="text-xs font-semibold uppercase tracking-wider text-muted">
                  Clientes que Mais Gastaram
                </p>
              </div>

              {topClientes.length === 0 ? (
                <div className="py-8 text-center">
                  <p className="text-sm text-muted px-4">Nenhuma comanda fechada ainda.</p>
                </div>
              ) : (
                <div>
                  {topClientes.map((c, i) => {
                    const pct = Math.round((c.total / maxTopTotal) * 100);
                    return (
                      <div
                        key={c.customer_name}
                        className={`flex items-center gap-3 px-4 py-3 border-b border-border last:border-0 ${
                          i % 2 === 0 ? '' : 'bg-white/[0.02]'
                        }`}
                      >
                        <div
                          className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
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

                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-1">
                            <p className="text-xs font-medium text-white truncate">{c.customer_name}</p>
                            <div className="flex items-center gap-2 shrink-0">
                              <span className="text-xs text-muted">{c.count}x</span>
                              <span className="text-xs font-semibold text-info">
                                {formatCurrency(c.total)}
                              </span>
                            </div>
                          </div>
                          <Progress value={pct} color="blue" />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
