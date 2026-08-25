import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Plus,
  Minus,
  Trash2,
  FileText,
  MessageCircle,
  CheckCircle,
  Search,
  History,
  Phone,
  Clock,
  HandCoins,
  Wallet,
} from 'lucide-react';
import {
  getOrderById,
  getOrderItems,
  getAllActiveProducts,
  addOrderItem,
  decrementOrderItem,
  removeAllItemsOfProduct,
  closeOrder,
  updateOrderPhone,
  getOrdersByCustomer,
  getSetting,
  getOrderPayments,
  addOrderPayment,
  deleteOrderPayment,
} from '../lib/db';
import {
  formatCurrency,
  formatDateTime,
  formatShortDateTime,
  parseAmount,
  nowSqlite,
} from '../lib/utils';
import { generateOrderPdf } from '../lib/pdf';
import { invoke } from '@tauri-apps/api/core';
import { save } from '@tauri-apps/plugin-dialog';
import { open as openUrl } from '@tauri-apps/plugin-shell';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Select } from '../components/ui/select';
import { Badge } from '../components/ui/badge';
import { Dialog } from '../components/ui/dialog';
import { Card } from '../components/ui/card';
import { Progress } from '../components/ui/progress';
import { ConfirmDialog } from '../components/shared/ConfirmDialog';
import { EmptyState } from '../components/shared/EmptyState';
import { useAppStore } from '../store';
import type { Order, OrderItem, OrderPayment, Product, GroupedOrderItem } from '../types';
import { PAYMENT_METHODS } from '../types';

const METHOD_OPTIONS = PAYMENT_METHODS.map((m) => ({ value: m, label: m }));

function toTime(dt: string): string {
  return new Date(dt.replace(' ', 'T')).toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

function groupItems(items: (OrderItem & { product_name: string })[]): GroupedOrderItem[] {
  const map: Record<number, GroupedOrderItem> = {};
  for (const item of items) {
    if (!map[item.product_id]) {
      map[item.product_id] = {
        product_id: item.product_id,
        product_name: item.product_name ?? 'Produto',
        total_quantity: 0,
        unit_price: item.unit_price,
        subtotal: 0,
        item_ids: [],
        added_at: item.added_at,
        added_ats: [],
      };
    }
    // Each row with qty=1 = one addition event; repeat timestamp for rows with qty>1
    for (let i = 0; i < item.quantity; i++) {
      map[item.product_id].added_ats.push(item.added_at);
    }
    map[item.product_id].total_quantity += item.quantity;
    map[item.product_id].subtotal += item.subtotal;
    map[item.product_id].item_ids.push(item.id);
  }
  return Object.values(map);
}

export default function OrderDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { addToast, pixKey: storedPixKey } = useAppStore();

  const orderId = Number(id);

  const [order, setOrder] = useState<Order | null>(null);
  const [items, setItems] = useState<GroupedOrderItem[]>([]);
  const [payments, setPayments] = useState<OrderPayment[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  // Add item state
  const [itemSearch, setItemSearch] = useState('');
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [adding, setAdding] = useState(false);
  const [itemInputFocused, setItemInputFocused] = useState(false);

  // Phone editing
  const [phone, setPhone] = useState('');

  // Payments (abatimentos)
  const [payOpen, setPayOpen] = useState(false);
  const [payAmount, setPayAmount] = useState('');
  const [payMethod, setPayMethod] = useState<string>(PAYMENT_METHODS[0]);
  const [payNote, setPayNote] = useState('');
  const [paying, setPaying] = useState(false);
  const [confirmDeletePayment, setConfirmDeletePayment] = useState<OrderPayment | null>(null);

  // Dialogs
  const [confirmClose, setConfirmClose] = useState(false);
  const [closing, setClosing] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [customerOrders, setCustomerOrders] = useState<Order[]>([]);

  // WhatsApp dialog
  const [waOpen, setWaOpen] = useState(false);
  const [waPhone, setWaPhone] = useState('');
  const [pixKey, setPixKey] = useState('');

  const load = useCallback(async () => {
    const [ord, rawItems, prods, pays] = await Promise.all([
      getOrderById(orderId),
      getOrderItems(orderId),
      getAllActiveProducts(),
      getOrderPayments(orderId),
    ]);
    if (!ord) { navigate('/orders'); return; }
    setOrder(ord);
    setPhone(ord.phone ?? '');
    setItems(groupItems(rawItems));
    setProducts(prods);
    setPayments(pays);
    setLoading(false);
  }, [orderId, navigate]);

  useEffect(() => {
    load();
  }, [load]);

  // Totais de pagamento (abatimentos)
  const paidTotal = payments.reduce((sum, p) => sum + p.amount, 0);
  const orderTotal = order?.total ?? 0;
  const remaining = Math.max(0, orderTotal - paidTotal);
  const isFullyPaid = payments.length > 0 && remaining <= 0.009;
  const paidPercent = orderTotal > 0 ? (paidTotal / orderTotal) * 100 : 0;
  const parsedPayAmount = parseAmount(payAmount);
  const payPreview = Number.isFinite(parsedPayAmount) && parsedPayAmount > 0 ? parsedPayAmount : 0;

  const filteredProducts = itemSearch
    ? products.filter((p) => p.name.toLowerCase().includes(itemSearch.toLowerCase()))
    : products;

  async function handleAddItem() {
    if (!selectedProduct) return;
    setAdding(true);
    try {
      await addOrderItem(orderId, selectedProduct.id, selectedProduct.sale_price);
      setItemSearch('');
      setSelectedProduct(null);
      load();
    } catch (e) {
      addToast(`Erro: ${e}`, 'error');
    } finally {
      setAdding(false);
    }
  }

  async function handleIncrement(productId: number) {
    const prod = products.find((p) => p.id === productId);
    if (!prod) return;
    await addOrderItem(orderId, productId, prod.sale_price);
    load();
  }

  async function handleDecrement(productId: number) {
    await decrementOrderItem(orderId, productId);
    load();
  }

  async function handleRemoveAll(productId: number) {
    await removeAllItemsOfProduct(orderId, productId);
    addToast('Item removido');
    load();
  }

  function openPayment() {
    setPayAmount(remaining > 0 ? remaining.toFixed(2).replace('.', ',') : '');
    setPayMethod(PAYMENT_METHODS[0]);
    setPayNote('');
    setPayOpen(true);
  }

  async function handleAddPayment() {
    const amount = parseAmount(payAmount);
    if (!Number.isFinite(amount) || amount <= 0) {
      addToast('Informe um valor maior que zero.', 'error');
      return;
    }
    setPaying(true);
    try {
      await addOrderPayment(orderId, Number(amount.toFixed(2)), payMethod, payNote.trim());
      addToast(`Pagamento de ${formatCurrency(amount)} registrado!`);
      setPayOpen(false);
      load();
    } catch (e) {
      addToast(`Erro: ${e}`, 'error');
    } finally {
      setPaying(false);
    }
  }

  async function handleDeletePayment() {
    if (!confirmDeletePayment) return;
    try {
      await deleteOrderPayment(confirmDeletePayment.id);
      addToast('Pagamento removido');
      setConfirmDeletePayment(null);
      load();
    } catch (e) {
      addToast(`Erro: ${e}`, 'error');
    }
  }

  async function handlePhoneBlur() {
    if (order && phone !== order.phone) {
      await updateOrderPhone(orderId, phone);
    }
  }

  async function handleClose() {
    setClosing(true);
    try {
      await closeOrder(orderId);
      addToast('Comanda fechada! Estoque atualizado.');
      setConfirmClose(false);
      load();
    } catch (e) {
      addToast(`Erro: ${e}`, 'error');
    } finally {
      setClosing(false);
    }
  }

  async function handleSavePdf() {
    if (!order) return;
    try {
      const pk = storedPixKey || (await getSetting('pix_key'));
      const bytes = generateOrderPdf(order, items, pk, payments);
      const dest = await save({
        title: 'Salvar PDF da Comanda',
        defaultPath: `comanda_${order.id}_${order.customer_name.replace(/\s+/g, '_')}.pdf`,
        filters: [{ name: 'PDF', extensions: ['pdf'] }],
      });
      if (!dest) return;
      await invoke('write_bytes', { path: dest, data: Array.from(bytes) });
      addToast('PDF salvo!');
      await invoke('open_file', { path: dest });
    } catch (e) {
      addToast(`Erro ao salvar PDF: ${e}`, 'error');
    }
  }

  async function openWhatsApp() {
    const pk = storedPixKey || (await getSetting('pix_key'));
    setWaPhone(phone || '');
    setPixKey(pk);
    setWaOpen(true);
  }

  async function sendWhatsApp() {
    if (!order) return;
    const isOpenOrder = order.status === 'aberta';
    const lines = [
      `Olá, *${order.customer_name}*! 👋`,
      '',
      `📋 *Comanda #${order.id}* ${isOpenOrder ? '(aberta)' : '(fechada)'}`,
      '',
      ...items.map(
        (i) =>
          `• ${i.product_name} x${i.total_quantity} — ${formatCurrency(i.subtotal)}`
      ),
      '',
      `💰 *Total: ${formatCurrency(order.total)}*`,
    ];

    if (payments.length > 0) {
      lines.push('', `✅ *Valor já acertado: ${formatCurrency(paidTotal)}*`);
      lines.push(
        ...payments.map(
          (p) =>
            `   ↳ ${formatShortDateTime(p.created_at)}${p.method ? ` (${p.method})` : ''} — ${formatCurrency(p.amount)}`
        )
      );
      lines.push(
        '',
        remaining > 0.009
          ? `🔴 *Falta pagar: ${formatCurrency(remaining)}*`
          : '🎉 *Comanda quitada — nada a pagar!*'
      );
    }

    if (pixKey && remaining > 0.009) {
      lines.push('', `🔑 PIX: \`${pixKey}\``);
    }
    const text = encodeURIComponent(lines.join('\n'));
    const cleanPhone = waPhone.replace(/\D/g, '');
    const url = cleanPhone
      ? `https://api.whatsapp.com/send?phone=55${cleanPhone}&text=${text}`
      : `https://api.whatsapp.com/send?text=${text}`;
    await openUrl(url);
    setWaOpen(false);
  }

  async function openHistory() {
    if (!order) return;
    const orders = await getOrdersByCustomer(order.customer_name);
    setCustomerOrders(orders);
    setHistoryOpen(true);
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!order) return null;

  const isOpen = order.status === 'aberta';

  return (
    <div className="space-y-5 animate-fade-in max-w-4xl">
      {/* Back button */}
      <button
        onClick={() => navigate('/orders')}
        className="flex items-center gap-2 text-sm text-muted hover:text-white transition-colors"
      >
        <ArrowLeft size={14} />
        Voltar para Comandas
      </button>

      {/* Order header */}
      <Card className="bg-[#111113] border-border">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-3">
              <h1 className="text-xl font-bold text-white">
                Comanda #{order.id}
              </h1>
              <Badge variant={isOpen ? 'green' : 'gray'} dot>
                {isOpen ? 'ABERTA' : 'FECHADA'}
              </Badge>
            </div>

            <div className="flex items-center gap-4 flex-wrap">
              <div>
                <p className="text-xs text-muted mb-1">Cliente</p>
                <div className="flex items-center gap-2">
                  <p className="text-base font-semibold text-white">
                    {order.customer_name}
                  </p>
                  <button
                    onClick={openHistory}
                    className="flex items-center gap-1 text-xs text-purple hover:text-violet-400 transition-colors bg-purple-subtle border border-purple/20 px-2 py-0.5 rounded-full"
                  >
                    <History size={10} />
                    Histórico
                  </button>
                </div>
              </div>

              <div>
                <p className="text-xs text-muted mb-1">Telefone</p>
                <div className="flex items-center gap-1.5">
                  <Phone size={12} className="text-muted" />
                  <input
                    className="bg-transparent text-sm text-white border-b border-transparent hover:border-border focus:border-primary focus:outline-none transition-colors py-0.5 w-36"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    onBlur={handlePhoneBlur}
                    placeholder="(11) 99999-9999"
                  />
                </div>
              </div>

              <div>
                <p className="text-xs text-muted mb-1">Abertura</p>
                <div className="flex items-center gap-1.5">
                  <Clock size={12} className="text-muted" />
                  <p className="text-sm text-white">{formatDateTime(order.created_at)}</p>
                </div>
              </div>

              {order.closed_at && (
                <div>
                  <p className="text-xs text-muted mb-1">Fechamento</p>
                  <div className="flex items-center gap-1.5">
                    <CheckCircle size={12} className="text-muted" />
                    <p className="text-sm text-white">{formatDateTime(order.closed_at)}</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Total */}
          <div className="text-right shrink-0">
            <p className="text-xs text-muted mb-1">Total</p>
            <p className="text-3xl font-bold text-primary">
              {formatCurrency(order.total)}
            </p>
            {payments.length > 0 && (
              <div className="mt-2 space-y-0.5">
                <p className="text-xs text-info">
                  Já pago:{' '}
                  <span className="font-semibold">{formatCurrency(paidTotal)}</span>
                </p>
                <p
                  className={`text-sm font-bold ${
                    isFullyPaid ? 'text-primary' : 'text-warning'
                  }`}
                >
                  {isFullyPaid
                    ? 'Comanda quitada'
                    : `Falta ${formatCurrency(remaining)}`}
                </p>
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* Add item (only if open) */}
      {isOpen && (
        <Card>
          <p className="text-xs font-semibold uppercase tracking-wider text-muted mb-3">
            Adicionar item
          </p>
          <div className="flex items-end gap-3">
            <div className="flex-1 relative">
              <Input
                placeholder="Clique ou digite para buscar produto..."
                value={itemSearch}
                onChange={(e) => {
                  setItemSearch(e.target.value);
                  setSelectedProduct(null);
                }}
                onFocus={() => setItemInputFocused(true)}
                onBlur={() => setTimeout(() => setItemInputFocused(false), 150)}
                leftIcon={<Search size={14} />}
              />
              {(itemInputFocused || itemSearch) && !selectedProduct && filteredProducts.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-card border border-border rounded-xl shadow-xl z-30 max-h-52 overflow-y-auto">
                  {filteredProducts.map((p) => (
                    <button
                      key={p.id}
                      className="w-full text-left px-4 py-2.5 hover:bg-white/10 transition-colors flex items-center justify-between gap-2"
                      onMouseDown={(e) => e.preventDefault()}
                      onClick={() => {
                        setSelectedProduct(p);
                        setItemSearch(p.name);
                        setItemInputFocused(false);
                      }}
                    >
                      <span className="text-sm text-white">{p.name}</span>
                      <span className="text-xs text-primary font-semibold shrink-0">
                        {formatCurrency(p.sale_price)}
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <Button
              variant="primary"
              size="md"
              icon={<Plus size={16} />}
              onClick={handleAddItem}
              disabled={!selectedProduct}
              isLoading={adding}
            >
              Adicionar
            </Button>
          </div>
        </Card>
      )}

      {/* Items table */}
      <Card noPad>
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <p className="text-sm font-semibold text-white">Itens da Comanda</p>
          <p className="text-xs text-muted">{items.length} produto(s)</p>
        </div>

        {/* Table header */}
        <div
          className={`grid gap-3 px-5 py-3 border-b border-border text-[10px] font-semibold uppercase tracking-wider text-muted ${
            isOpen ? 'grid-cols-[1fr_140px_90px_90px_80px]' : 'grid-cols-[1fr_60px_90px_90px]'
          }`}
        >
          <span>Produto</span>
          {isOpen && <span className="text-center">Quantidade</span>}
          {!isOpen && <span className="text-center">Qtd</span>}
          <span className="text-right">Unitário</span>
          <span className="text-right">Subtotal</span>
          {isOpen && <span className="text-center">Remover</span>}
        </div>

        {items.length === 0 ? (
          <EmptyState
            icon={FileText}
            title="Nenhum item adicionado"
            description={isOpen ? 'Use o campo acima para adicionar produtos.' : ''}
          />
        ) : (
          <div>
            {items.map((item, i) => (
              <div
                key={item.product_id}
                className={`grid gap-3 px-5 py-3 items-center border-b border-border last:border-0 ${
                  i % 2 === 0 ? '' : 'bg-white/[0.02]'
                } ${
                  isOpen
                    ? 'grid-cols-[1fr_140px_90px_90px_80px]'
                    : 'grid-cols-[1fr_60px_90px_90px]'
                }`}
              >
                <div>
                  <p className="text-sm text-white">{item.product_name}</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {item.added_ats.map((at, idx) => (
                      <span
                        key={idx}
                        className="text-[10px] text-muted bg-white/[0.05] border border-border px-1.5 py-0.5 rounded"
                      >
                        {toTime(at)}
                      </span>
                    ))}
                  </div>
                </div>

                {isOpen ? (
                  <div className="flex items-center justify-center gap-2">
                    <button
                      className="w-7 h-7 rounded-lg bg-white/10 hover:bg-danger/20 hover:text-danger text-muted flex items-center justify-center transition-colors"
                      onClick={() => handleDecrement(item.product_id)}
                    >
                      <Minus size={12} />
                    </button>
                    <span className="w-8 text-center text-sm font-semibold text-white">
                      {item.total_quantity}
                    </span>
                    <button
                      className="w-7 h-7 rounded-lg bg-white/10 hover:bg-primary/20 hover:text-primary text-muted flex items-center justify-center transition-colors"
                      onClick={() => handleIncrement(item.product_id)}
                    >
                      <Plus size={12} />
                    </button>
                  </div>
                ) : (
                  <span className="text-sm text-center text-white">{item.total_quantity}</span>
                )}

                <span className="text-sm text-right text-muted">
                  {formatCurrency(item.unit_price)}
                </span>
                <span className="text-sm text-right font-semibold text-white">
                  {formatCurrency(item.subtotal)}
                </span>

                {isOpen && (
                  <div className="flex justify-center">
                    <button
                      className="p-1.5 rounded-lg text-muted hover:text-danger hover:bg-danger-subtle transition-colors"
                      onClick={() => handleRemoveAll(item.product_id)}
                      title="Remover todos"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Total footer */}
        <div className="flex items-center justify-between px-5 py-4 border-t border-primary/20 bg-primary-subtle rounded-b-xl">
          <span className="text-sm font-semibold text-primary">Total da Comanda</span>
          <span className="text-2xl font-bold text-primary">
            {formatCurrency(order.total)}
          </span>
        </div>
      </Card>

      {/* Pagamentos parciais (abatimentos) */}
      <Card noPad>
        <div className="flex items-center justify-between gap-3 px-5 py-4 border-b border-border">
          <div>
            <p className="text-sm font-semibold text-white flex items-center gap-2">
              <Wallet size={14} className="text-info" />
              Pagamentos recebidos
            </p>
            <p className="text-[11px] text-muted mt-0.5">
              Valores que o cliente já acertou desta comanda
            </p>
          </div>
          <Button
            variant="info"
            size="sm"
            icon={<HandCoins size={14} />}
            onClick={openPayment}
          >
            Registrar pagamento
          </Button>
        </div>

        {payments.length === 0 ? (
          <p className="px-5 py-5 text-xs text-muted text-center">
            Nenhum pagamento registrado — o cliente ainda não acertou nada desta comanda.
          </p>
        ) : (
          <div>
            <div className="grid grid-cols-[1fr_110px_120px_60px] gap-3 px-5 py-2.5 border-b border-border text-[10px] font-semibold uppercase tracking-wider text-muted">
              <span>Quando</span>
              <span>Forma</span>
              <span className="text-right">Valor</span>
              <span className="text-center">Remover</span>
            </div>
            {payments.map((p, i) => (
              <div
                key={p.id}
                className={`grid grid-cols-[1fr_110px_120px_60px] gap-3 px-5 py-3 items-center border-b border-border last:border-0 ${
                  i % 2 === 0 ? '' : 'bg-white/[0.02]'
                }`}
              >
                <div className="min-w-0">
                  <p className="text-sm text-white">{formatShortDateTime(p.created_at)}</p>
                  {p.note && (
                    <p className="text-[11px] text-muted truncate mt-0.5">{p.note}</p>
                  )}
                </div>
                <div>{p.method && <Badge variant="blue">{p.method}</Badge>}</div>
                <span className="text-sm text-right font-semibold text-info">
                  − {formatCurrency(p.amount)}
                </span>
                <div className="flex justify-center">
                  <button
                    className="p-1.5 rounded-lg text-muted hover:text-danger hover:bg-danger-subtle transition-colors"
                    onClick={() => setConfirmDeletePayment(p)}
                    title="Remover pagamento"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Resumo do acerto */}
        <div className="border-t border-border">
          <div className="grid grid-cols-3">
            <div className="px-5 py-4">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-muted mb-1">
                Total da comanda
              </p>
              <p className="text-lg font-bold text-white">{formatCurrency(orderTotal)}</p>
            </div>
            <div className="px-5 py-4 border-l border-border">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-muted mb-1">
                Já pago
              </p>
              <p className="text-lg font-bold text-info">{formatCurrency(paidTotal)}</p>
            </div>
            <div
              className={`px-5 py-4 border-l border-border ${
                isFullyPaid ? 'bg-primary-subtle' : 'bg-warning-subtle'
              }`}
            >
              <p className="text-[10px] font-semibold uppercase tracking-wider text-muted mb-1">
                Falta pagar
              </p>
              <p
                className={`text-lg font-bold ${
                  isFullyPaid ? 'text-primary' : 'text-warning'
                }`}
              >
                {isFullyPaid ? 'Quitada 🎉' : formatCurrency(remaining)}
              </p>
            </div>
          </div>
          {orderTotal > 0 && (
            <div className="px-5 pb-4">
              <Progress value={paidPercent} color={isFullyPaid ? 'green' : 'blue'} />
            </div>
          )}
        </div>
      </Card>

      {/* Action buttons */}
      <div className="flex items-center gap-3">
        <Button
          variant="secondary"
          size="lg"
          icon={<FileText size={16} />}
          onClick={handleSavePdf}
        >
          Salvar PDF
        </Button>

        <Button
          variant="ghost"
          size="lg"
          icon={<MessageCircle size={16} className="text-green-400" />}
          onClick={openWhatsApp}
          className="border-green-900 hover:border-green-500 hover:text-green-400"
        >
          WhatsApp
        </Button>

        {isOpen && (
          <Button
            variant="primary"
            size="lg"
            icon={<CheckCircle size={16} />}
            onClick={() => setConfirmClose(true)}
            className="ml-auto"
          >
            Fechar Comanda
          </Button>
        )}
      </div>

      {/* Close confirm */}
      <ConfirmDialog
        open={confirmClose}
        onClose={() => setConfirmClose(false)}
        onConfirm={handleClose}
        variant="warning"
        title="Fechar comanda?"
        message={`O estoque de ${items.length} produto(s) será descontado automaticamente.${
          remaining > 0.009 && payments.length > 0
            ? ` Atenção: ainda faltam ${formatCurrency(remaining)} a receber desta comanda.`
            : ''
        } Esta ação não pode ser desfeita.`}
        confirmLabel="Fechar comanda"
        isLoading={closing}
      />

      {/* Registrar pagamento */}
      <Dialog
        open={payOpen}
        onClose={() => setPayOpen(false)}
        title="Registrar pagamento"
        size="sm"
      >
        <div className="space-y-4">
          <div className="rounded-lg border border-border bg-white/[0.02] px-3 py-2.5 space-y-1.5">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted">Total da comanda</span>
              <span className="text-white font-semibold">{formatCurrency(orderTotal)}</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted">Já pago</span>
              <span className="text-info font-semibold">{formatCurrency(paidTotal)}</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted">Falta pagar</span>
              <span className="text-warning font-semibold">{formatCurrency(remaining)}</span>
            </div>
          </div>

          <Input
            label="Valor recebido (R$)"
            value={payAmount}
            onChange={(e) => setPayAmount(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleAddPayment();
            }}
            placeholder="0,00"
            inputMode="decimal"
            autoFocus
          />

          {remaining > 0.009 && (
            <div className="flex gap-2">
              <button
                type="button"
                className="flex-1 py-1.5 rounded-lg border border-border text-xs text-muted hover:text-white hover:bg-white/5 transition-colors"
                onClick={() => setPayAmount((remaining / 2).toFixed(2).replace('.', ','))}
              >
                Metade ({formatCurrency(remaining / 2)})
              </button>
              <button
                type="button"
                className="flex-1 py-1.5 rounded-lg border border-border text-xs text-muted hover:text-white hover:bg-white/5 transition-colors"
                onClick={() => setPayAmount(remaining.toFixed(2).replace('.', ','))}
              >
                Tudo ({formatCurrency(remaining)})
              </button>
            </div>
          )}

          <Select
            label="Forma de pagamento"
            value={payMethod}
            onChange={(e) => setPayMethod(e.target.value)}
            options={METHOD_OPTIONS}
          />

          <Input
            label="Observação (opcional)"
            value={payNote}
            onChange={(e) => setPayNote(e.target.value)}
            placeholder="Ex: adiantamento, pago pelo amigo..."
          />

          {payPreview > 0 && (
            payPreview > remaining + 0.009 ? (
              <p className="text-xs text-warning">
                Este valor passa {formatCurrency(payPreview - remaining)} do que falta pagar.
                Confira antes de registrar.
              </p>
            ) : (
              <p className="text-xs text-muted">
                Depois deste pagamento vão faltar{' '}
                <span className="text-white font-semibold">
                  {formatCurrency(Math.max(0, remaining - payPreview))}
                </span>
                .
              </p>
            )
          )}

          <div className="flex gap-3">
            <Button
              variant="ghost"
              className="flex-1"
              onClick={() => setPayOpen(false)}
              disabled={paying}
            >
              Cancelar
            </Button>
            <Button
              variant="info"
              className="flex-1"
              icon={<HandCoins size={15} />}
              onClick={handleAddPayment}
              isLoading={paying}
            >
              Registrar
            </Button>
          </div>
        </div>
      </Dialog>

      {/* Remover pagamento */}
      <ConfirmDialog
        open={!!confirmDeletePayment}
        onClose={() => setConfirmDeletePayment(null)}
        onConfirm={handleDeletePayment}
        title="Remover pagamento?"
        message={
          confirmDeletePayment
            ? `O pagamento de ${formatCurrency(confirmDeletePayment.amount)} registrado em ${formatShortDateTime(confirmDeletePayment.created_at)} será excluído e voltará a contar como valor em aberto.`
            : ''
        }
        confirmLabel="Remover"
      />

      {/* WhatsApp dialog */}
      <Dialog open={waOpen} onClose={() => setWaOpen(false)} title="Enviar via WhatsApp" size="sm">
        <div className="space-y-4">
          <Input
            label="Telefone do cliente"
            value={waPhone}
            onChange={(e) => setWaPhone(e.target.value)}
            placeholder="11 999999999"
          />
          <Input
            label="Chave PIX (opcional)"
            value={pixKey}
            onChange={(e) => setPixKey(e.target.value)}
            placeholder="email, CPF, telefone..."
          />
          <div className="flex gap-3">
            <Button variant="ghost" className="flex-1" onClick={() => setWaOpen(false)}>
              Cancelar
            </Button>
            <Button
              variant="primary"
              className="flex-1 !bg-[#25d366] hover:!bg-[#1da852]"
              icon={<MessageCircle size={15} />}
              onClick={sendWhatsApp}
            >
              Enviar
            </Button>
          </div>
        </div>
      </Dialog>

      {/* Customer history dialog */}
      <Dialog
        open={historyOpen}
        onClose={() => setHistoryOpen(false)}
        title={`Histórico — ${order.customer_name}`}
        size="lg"
      >
        <div className="space-y-2 max-h-80 overflow-y-auto">
          {customerOrders.length === 0 ? (
            <p className="text-sm text-muted text-center py-6">Nenhuma comanda anterior.</p>
          ) : (
            customerOrders.map((o) => (
              <button
                key={o.id}
                className="w-full flex items-center justify-between px-4 py-3 rounded-lg border border-border hover:bg-white/5 transition-colors text-left"
                onClick={() => {
                  setHistoryOpen(false);
                  navigate(`/orders/${o.id}`);
                }}
              >
                <div className="flex items-center gap-3">
                  <span className="text-xs text-muted font-mono">#{o.id}</span>
                  <Badge variant={o.status === 'aberta' ? 'green' : 'gray'} dot>
                    {o.status === 'aberta' ? 'ABERTA' : 'FECHADA'}
                  </Badge>
                  <span className="text-xs text-muted">{formatDateTime(o.created_at)}</span>
                </div>
                <div className="text-right">
                  <span className="text-sm font-semibold text-white">
                    {formatCurrency(o.total)}
                  </span>
                  {!!o.paid && o.paid > 0.009 && (
                    <p
                      className={`text-[10px] ${
                        o.total - o.paid > 0.009 ? 'text-warning' : 'text-primary'
                      }`}
                    >
                      {o.total - o.paid > 0.009
                        ? `falta ${formatCurrency(o.total - o.paid)}`
                        : 'quitada'}
                    </p>
                  )}
                </div>
              </button>
            ))
          )}
        </div>
      </Dialog>
    </div>
  );
}
