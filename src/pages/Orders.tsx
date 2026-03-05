import { useEffect, useState, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, Eye, CheckCircle, Trash2, Receipt, Phone, AlertTriangle, ArrowRight } from 'lucide-react';
import { getOrders, createOrder, closeOrder, deleteOrder, searchCustomers, updateOrderPhone, getOpenOrderByCustomerName, getSetting } from '../lib/db';
import { formatCurrency, formatDateTime } from '../lib/utils';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Select } from '../components/ui/select';
import { Dialog } from '../components/ui/dialog';
import { Card } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { ConfirmDialog } from '../components/shared/ConfirmDialog';
import { EmptyState } from '../components/shared/EmptyState';
import { useAppStore } from '../store';
import type { Order, Customer } from '../types';

function daysSince(dateStr: string): number {
  const d = new Date(dateStr.replace(' ', 'T'));
  return Math.floor((Date.now() - d.getTime()) / 86_400_000);
}

const STATUS_OPTIONS = [
  { value: 'todas', label: 'Todos os status' },
  { value: 'aberta', label: 'Abertas' },
  { value: 'fechada', label: 'Fechadas' },
];

export default function Orders() {
  const navigate = useNavigate();
  const { addToast, setStaleOrdersCount } = useAppStore();

  const [orders, setOrders] = useState<Order[]>([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('todas');
  const [loading, setLoading] = useState(true);
  const [staleDays, setStaleDays] = useState(3);

  const [newOpen, setNewOpen] = useState(false);
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [suggestions, setSuggestions] = useState<Customer[]>([]);
  const [showSug, setShowSug] = useState(false);
  const [creating, setCreating] = useState(false);
  const [existingOpen, setExistingOpen] = useState<Order | null>(null);

  const [confirmClose, setConfirmClose] = useState<Order | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<Order | null>(null);
  const [acting, setActing] = useState(false);

  const inputRef = useRef<HTMLInputElement>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [data, days] = await Promise.all([
        getOrders(search, statusFilter),
        getSetting('stale_order_days', '3'),
      ]);
      const threshold = parseInt(days) || 3;
      setStaleDays(threshold);
      setOrders(data);
      // Update sidebar badge: count open orders past threshold
      const stale = data.filter(
        (o) => o.status === 'aberta' && daysSince(o.created_at) >= threshold
      ).length;
      setStaleOrdersCount(stale);
    } finally {
      setLoading(false);
    }
  }, [search, statusFilter, setStaleOrdersCount]);

  useEffect(() => {
    load();
  }, [load]);

  async function openNew() {
    setCustomerName('');
    setCustomerPhone('');
    setSuggestions([]);
    setShowSug(false);
    setExistingOpen(null);
    setNewOpen(true);
    setTimeout(() => inputRef.current?.focus(), 100);
  }

  async function onNameChange(v: string) {
    setCustomerName(v);
    setCustomerPhone('');
    setExistingOpen(null);
    if (v.length >= 1) {
      const found = await searchCustomers(v);
      setSuggestions(found);
      setShowSug(found.length > 0);
    } else {
      setSuggestions([]);
      setShowSug(false);
    }
  }

  async function selectCustomer(c: Customer) {
    setCustomerName(c.name);
    setCustomerPhone(c.phone ?? '');
    setShowSug(false);
    const open = await getOpenOrderByCustomerName(c.name);
    setExistingOpen(open);
  }

  async function handleCreate() {
    if (!customerName.trim()) return addToast('Informe o nome do cliente', 'error');
    // Check for existing open order before creating
    const open = await getOpenOrderByCustomerName(customerName.trim());
    if (open) {
      setExistingOpen(open);
      return;
    }
    setCreating(true);
    try {
      const id = await createOrder(customerName.trim());
      if (customerPhone.trim()) {
        await updateOrderPhone(id, customerPhone.trim());
      }
      setNewOpen(false);
      addToast('Comanda criada!');
      navigate(`/orders/${id}`);
    } catch (e) {
      addToast(`Erro: ${e}`, 'error');
    } finally {
      setCreating(false);
    }
  }

  function goToExisting() {
    if (!existingOpen) return;
    setNewOpen(false);
    navigate(`/orders/${existingOpen.id}`);
  }

  async function handleClose() {
    if (!confirmClose) return;
    setActing(true);
    try {
      await closeOrder(confirmClose.id);
      addToast('Comanda fechada! Estoque atualizado.');
      setConfirmClose(null);
      load();
    } catch (e) {
      addToast(`Erro: ${e}`, 'error');
    } finally {
      setActing(false);
    }
  }

  async function handleDelete() {
    if (!confirmDelete) return;
    setActing(true);
    try {
      await deleteOrder(confirmDelete.id);
      addToast('Comanda excluída');
      setConfirmDelete(null);
      load();
    } catch (e) {
      addToast(`Erro: ${e}`, 'error');
    } finally {
      setActing(false);
    }
  }

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">Comandas</h1>
        <Button variant="primary" size="md" icon={<Plus size={16} />} onClick={openNew}>
          Nova Comanda
        </Button>
      </div>

      {/* Filters */}
      <div className="flex items-end gap-3">
        <div className="flex-1">
          <Input
            placeholder="Buscar por cliente..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            leftIcon={<Search size={14} />}
          />
        </div>
        <div className="w-48">
          <Select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            options={STATUS_OPTIONS}
          />
        </div>
      </div>

      {/* Stale orders banner */}
      {(() => {
        const staleCount = orders.filter(
          (o) => o.status === 'aberta' && daysSince(o.created_at) >= staleDays
        ).length;
        return staleCount > 0 ? (
          <div className="flex items-center gap-3 px-4 py-2.5 bg-warning-subtle border border-warning/30 rounded-xl">
            <AlertTriangle size={14} className="text-warning shrink-0" />
            <p className="text-xs text-warning flex-1">
              <span className="font-bold">{staleCount}</span> comanda{staleCount > 1 ? 's' : ''} aberta{staleCount > 1 ? 's' : ''} há mais de{' '}
              <span className="font-bold">{staleDays} dia{staleDays > 1 ? 's' : ''}</span> — verifique se precisam ser finalizadas ou cobradas.
            </p>
          </div>
        ) : null;
      })()}

      {/* Table */}
      <Card noPad>
        {/* Header row */}
        <div className="grid grid-cols-[60px_1fr_100px_120px_160px_220px] gap-3 px-4 py-3 border-b border-border">
          {['ID', 'Cliente', 'Status', 'Total', 'Data / Hora', 'Ações'].map((h) => (
            <p key={h} className="text-[10px] font-semibold uppercase tracking-wider text-muted">
              {h}
            </p>
          ))}
        </div>

        {loading ? (
          <div className="py-12 flex justify-center">
            <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : orders.length === 0 ? (
          <EmptyState
            icon={Receipt}
            title="Nenhuma comanda encontrada"
            description="Crie uma nova comanda para começar."
            action={
              <Button variant="primary" size="sm" icon={<Plus size={14} />} onClick={openNew}>
                Nova comanda
              </Button>
            }
          />
        ) : (
          <div>
            {orders.map((order, i) => {
              const age = daysSince(order.created_at);
              const isStale = order.status === 'aberta' && age >= staleDays;
              return (
              <div
                key={order.id}
                className={`grid grid-cols-[60px_1fr_100px_120px_160px_220px] gap-3 px-4 py-3 items-center transition-colors border-b border-border last:border-0 hover:bg-white/[0.03] ${
                  isStale
                    ? 'bg-warning/[0.04] border-l-2 border-l-warning'
                    : i % 2 === 0 ? '' : 'bg-white/[0.02]'
                }`}
              >
                <span className="text-xs text-muted font-mono">#{order.id}</span>
                <div className="flex items-center gap-2 min-w-0">
                  <span className="text-sm text-white font-medium truncate">
                    {order.customer_name}
                  </span>
                  {isStale && (
                    <span className="flex items-center gap-0.5 text-[10px] font-bold text-warning bg-warning-subtle border border-warning/30 px-1.5 py-0.5 rounded-full shrink-0">
                      <AlertTriangle size={8} />
                      {age}d
                    </span>
                  )}
                </div>
                <div>
                  <Badge
                    variant={order.status === 'aberta' ? 'green' : 'gray'}
                    dot
                  >
                    {order.status === 'aberta' ? 'ABERTA' : 'FECHADA'}
                  </Badge>
                </div>
                <span className="text-sm font-semibold text-white">
                  {formatCurrency(order.total)}
                </span>
                <span className="text-xs text-muted">{formatDateTime(order.created_at)}</span>

                <div className="flex items-center gap-1.5">
                  <Button
                    variant="info"
                    size="xs"
                    icon={<Eye size={11} />}
                    onClick={() => navigate(`/orders/${order.id}`)}
                  >
                    Detalhes
                  </Button>

                  {order.status === 'aberta' && (
                    <>
                      <Button
                        variant="primary"
                        size="xs"
                        icon={<CheckCircle size={11} />}
                        onClick={() => setConfirmClose(order)}
                      >
                        Fechar
                      </Button>
                      <Button
                        variant="danger"
                        size="xs"
                        icon={<Trash2 size={11} />}
                        onClick={() => setConfirmDelete(order)}
                      >
                        Excluir
                      </Button>
                    </>
                  )}
                </div>
              </div>
              );
            })}
          </div>
        )}
      </Card>

      {/* New Order Dialog */}
      <Dialog
        open={newOpen}
        onClose={() => setNewOpen(false)}
        title="Nova Comanda"
        size="sm"
      >
        <div className="space-y-4">
          <div className="relative">
            <Input
              label="Nome do cliente"
              ref={inputRef}
              value={customerName}
              onChange={(e) => onNameChange(e.target.value)}
              onFocus={() => customerName.length >= 1 && suggestions.length > 0 && setShowSug(true)}
              onBlur={() => setTimeout(() => setShowSug(false), 150)}
              placeholder="Digite o nome ou selecione um cliente..."
              autoComplete="off"
            />
            {showSug && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-card border border-border rounded-xl shadow-xl z-50 overflow-hidden">
                {suggestions.map((c) => (
                  <button
                    key={c.id}
                    className="w-full text-left px-4 py-2.5 hover:bg-white/10 transition-colors flex items-center justify-between gap-3"
                    onMouseDown={() => selectCustomer(c)}
                  >
                    <span className="text-sm text-white font-medium">{c.name}</span>
                    {c.phone && (
                      <span className="text-xs text-muted shrink-0">{c.phone}</span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Phone auto-filled from customer */}
          {customerPhone && !existingOpen && (
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-primary-subtle border border-primary/20">
              <Phone size={13} className="text-primary shrink-0" />
              <span className="text-sm text-primary font-medium">{customerPhone}</span>
              <span className="text-xs text-primary/60 ml-auto">preenchido automaticamente</span>
            </div>
          )}

          {/* Existing open order warning */}
          {existingOpen && (
            <div className="rounded-lg border border-warning/30 bg-warning-subtle p-3 space-y-2">
              <div className="flex items-center gap-2">
                <AlertTriangle size={13} className="text-warning shrink-0" />
                <p className="text-xs font-semibold text-warning">Comanda aberta encontrada</p>
              </div>
              <p className="text-xs text-muted">
                <span className="text-white font-medium">{existingOpen.customer_name}</span> já tem
                a Comanda <span className="text-white font-medium">#{existingOpen.id}</span> aberta
                desde{' '}
                <span className="text-white">{new Date(existingOpen.created_at.replace(' ', 'T')).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}</span>.
              </p>
              <button
                className="w-full flex items-center justify-center gap-2 py-2 rounded-lg bg-warning/20 hover:bg-warning/30 text-warning text-sm font-semibold transition-colors"
                onClick={goToExisting}
              >
                Ir para comanda aberta
                <ArrowRight size={14} />
              </button>
            </div>
          )}

          <div className="flex gap-3">
            <Button
              variant="ghost"
              className="flex-1"
              onClick={() => setNewOpen(false)}
              disabled={creating}
            >
              Cancelar
            </Button>
            <Button
              variant="primary"
              className="flex-1"
              onClick={handleCreate}
              isLoading={creating}
              disabled={!!existingOpen}
            >
              Criar Comanda
            </Button>
          </div>
        </div>
      </Dialog>

      {/* Close order confirm */}
      <ConfirmDialog
        open={!!confirmClose}
        onClose={() => setConfirmClose(null)}
        onConfirm={handleClose}
        variant="warning"
        title="Fechar comanda?"
        message={`A comanda de ${confirmClose?.customer_name} será fechada e o estoque dos itens será descontado automaticamente.`}
        confirmLabel="Fechar e descontar"
        isLoading={acting}
      />

      {/* Delete confirm */}
      <ConfirmDialog
        open={!!confirmDelete}
        onClose={() => setConfirmDelete(null)}
        onConfirm={handleDelete}
        title="Excluir comanda?"
        message={`A comanda de ${confirmDelete?.customer_name} e todos os seus itens serão excluídos permanentemente.`}
        confirmLabel="Excluir"
        isLoading={acting}
      />
    </div>
  );
}
