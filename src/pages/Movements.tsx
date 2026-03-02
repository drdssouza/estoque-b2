import { useEffect, useState, useCallback } from 'react';
import { Plus, ArrowUpCircle, ArrowDownCircle, Trash2, ArrowLeftRight } from 'lucide-react';
import { getMovements, addMovement, removeMovement, getAllActiveProducts } from '../lib/db';
import { formatDateTime } from '../lib/utils';
import { Button } from '../components/ui/button';
import { Input, Textarea } from '../components/ui/input';
import { Select } from '../components/ui/select';
import { Dialog } from '../components/ui/dialog';
import { Card } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { ConfirmDialog } from '../components/shared/ConfirmDialog';
import { EmptyState } from '../components/shared/EmptyState';
import { useAppStore } from '../store';
import type { Movement, Product } from '../types';

export default function Movements() {
  const { addToast } = useAppStore();

  const [movements, setMovements] = useState<(Movement & { product_name: string })[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState('');
  const [quantity, setQuantity] = useState(1);
  const [note, setNote] = useState('');
  const [saving, setSaving] = useState(false);

  const [confirmId, setConfirmId] = useState<number | null>(null);
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [movs, prods] = await Promise.all([getMovements(), getAllActiveProducts()]);
      setMovements(movs);
      setProducts(prods);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  function openDialog() {
    setSelectedProduct(products[0]?.id.toString() ?? '');
    setQuantity(1);
    setNote('');
    setDialogOpen(true);
  }

  async function handleSave() {
    if (!selectedProduct) return addToast('Selecione um produto', 'error');
    if (quantity <= 0) return addToast('Quantidade deve ser maior que 0', 'error');
    setSaving(true);
    try {
      await addMovement(Number(selectedProduct), quantity, note.trim());
      addToast('Entrada registrada!');
      setDialogOpen(false);
      load();
    } catch (e) {
      addToast(`Erro: ${e}`, 'error');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!confirmId) return;
    setDeleting(true);
    try {
      await removeMovement(confirmId);
      addToast('Movimentação removida');
      setConfirmId(null);
      load();
    } catch (e) {
      addToast(`Erro: ${e}`, 'error');
    } finally {
      setDeleting(false);
    }
  }

  const isAuto = (m: Movement) =>
    m.movement_type === 'EXIT' && m.note?.startsWith('Comanda #');

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">Movimentações</h1>
        <Button
          variant="primary"
          size="md"
          icon={<Plus size={16} />}
          onClick={openDialog}
        >
          Registrar Entrada
        </Button>
      </div>

      {/* Table */}
      <Card noPad>
        {/* Header */}
        <div className="grid grid-cols-[60px_1fr_100px_80px_180px_1fr_100px] gap-3 px-4 py-3 border-b border-border">
          {['ID', 'Produto', 'Tipo', 'Qtd', 'Data / Hora', 'Obs.', 'Ação'].map((h) => (
            <p key={h} className="text-[10px] font-semibold uppercase tracking-wider text-muted">
              {h}
            </p>
          ))}
        </div>

        {loading ? (
          <div className="py-12 flex justify-center">
            <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : movements.length === 0 ? (
          <EmptyState
            icon={ArrowLeftRight}
            title="Nenhuma movimentação"
            description="Registre entradas de estoque manualmente. Saídas são geradas ao fechar comandas."
          />
        ) : (
          <div>
            {movements.map((m, i) => (
              <div
                key={m.id}
                className={`grid grid-cols-[60px_1fr_100px_80px_180px_1fr_100px] gap-3 px-4 py-3 items-center border-b border-border last:border-0 transition-colors ${
                  i % 2 === 0 ? '' : 'bg-white/[0.02]'
                } hover:bg-white/[0.03]`}
              >
                <span className="text-xs text-muted font-mono">#{m.id}</span>
                <span className="text-sm text-white truncate">{m.product_name}</span>

                <div>
                  {m.movement_type === 'ENTRY' ? (
                    <Badge variant="green" dot>
                      <ArrowUpCircle size={10} className="inline mr-0.5" />
                      ENTRADA
                    </Badge>
                  ) : (
                    <Badge variant="red" dot>
                      <ArrowDownCircle size={10} className="inline mr-0.5" />
                      SAÍDA
                    </Badge>
                  )}
                </div>

                <span
                  className={`text-sm font-semibold text-center ${
                    m.movement_type === 'ENTRY' ? 'text-primary' : 'text-danger'
                  }`}
                >
                  {m.movement_type === 'ENTRY' ? '+' : '−'}{m.quantity}
                </span>

                <span className="text-xs text-muted">{formatDateTime(m.created_at)}</span>

                <span className="text-xs text-muted truncate">{m.note || '—'}</span>

                <div>
                  {isAuto(m) ? (
                    <span className="text-xs text-muted italic px-2">Auto</span>
                  ) : (
                    <Button
                      variant="ghost"
                      size="xs"
                      icon={<Trash2 size={11} />}
                      onClick={() => setConfirmId(m.id)}
                      className="hover:text-danger hover:border-danger/30"
                    >
                      Remover
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Add entry dialog */}
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        title="Registrar Entrada de Estoque"
        size="sm"
      >
        <div className="space-y-4">
          <Select
            label="Produto"
            value={selectedProduct}
            onChange={(e) => setSelectedProduct(e.target.value)}
            options={products.map((p) => ({
              value: p.id.toString(),
              label: `${p.name} (Estoque: ${p.current_stock})`,
            }))}
          />

          <Input
            label="Quantidade"
            type="number"
            min="1"
            value={quantity}
            onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
          />

          <Textarea
            label="Observação (opcional)"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Ex: Compra de fornecedor..."
            rows={2}
          />

          <div className="flex gap-3 pt-1">
            <Button
              variant="ghost"
              className="flex-1"
              onClick={() => setDialogOpen(false)}
              disabled={saving}
            >
              Cancelar
            </Button>
            <Button
              variant="primary"
              className="flex-1"
              onClick={handleSave}
              isLoading={saving}
            >
              Confirmar entrada
            </Button>
          </div>
        </div>
      </Dialog>

      {/* Delete confirm */}
      <ConfirmDialog
        open={confirmId !== null}
        onClose={() => setConfirmId(null)}
        onConfirm={handleDelete}
        title="Remover movimentação?"
        message="A movimentação será removida e o estoque do produto será revertido."
        confirmLabel="Remover"
        isLoading={deleting}
      />
    </div>
  );
}
