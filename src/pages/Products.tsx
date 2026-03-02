import { useEffect, useState, useCallback } from 'react';
import { Plus, Search, ArrowUpDown, Pencil, PackageX } from 'lucide-react';
import {
  getProducts,
  addProduct,
  updateProduct,
  deactivateProduct,
  getLowStockProducts,
} from '../lib/db';
import { formatCurrency, getStockLevel } from '../lib/utils';
import { useAppStore } from '../store';
import { Button } from '../components/ui/button';
import { Input, Textarea } from '../components/ui/input';
import { Select } from '../components/ui/select';
import { Dialog } from '../components/ui/dialog';
import { Card } from '../components/ui/card';
import { StockBadge } from '../components/shared/StockBadge';
import { ConfirmDialog } from '../components/shared/ConfirmDialog';
import { EmptyState } from '../components/shared/EmptyState';
import type { Product } from '../types';

const CATEGORIES = [
  { value: 'bebida', label: 'Bebida' },
  { value: 'doce', label: 'Doce' },
  { value: 'salgado', label: 'Salgado' },
  { value: 'acessório', label: 'Acessório' },
];

const FILTER_CATS = [{ value: 'todas', label: 'Todas as categorias' }, ...CATEGORIES];

type SortMode = 'none' | 'asc' | 'desc';

const emptyForm = {
  name: '',
  category: 'bebida',
  purchase_price: 0,
  sale_price: 0,
  minimum_stock: 0,
  current_stock: 0,
};

export default function Products() {
  const [products, setProducts] = useState<Product[]>([]);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('todas');
  const [sort, setSort] = useState<SortMode>('none');
  const [loading, setLoading] = useState(true);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Product | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);

  const [confirmId, setConfirmId] = useState<number | null>(null);
  const [deactivating, setDeactivating] = useState(false);

  const { setLowStockCount, addToast } = useAppStore();

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [data, low] = await Promise.all([
        getProducts(search, category === 'todas' ? '' : category),
        getLowStockProducts(),
      ]);
      let result = data;
      if (sort === 'asc') result = [...data].sort((a, b) => a.current_stock - b.current_stock);
      if (sort === 'desc') result = [...data].sort((a, b) => b.current_stock - a.current_stock);
      setProducts(result);
      setLowStockCount(low.length);
    } finally {
      setLoading(false);
    }
  }, [search, category, sort, setLowStockCount]);

  useEffect(() => {
    load();
  }, [load]);

  function openAdd() {
    setEditing(null);
    setForm(emptyForm);
    setDialogOpen(true);
  }

  function openEdit(p: Product) {
    setEditing(p);
    setForm({
      name: p.name,
      category: p.category,
      purchase_price: p.purchase_price,
      sale_price: p.sale_price,
      minimum_stock: p.minimum_stock,
      current_stock: p.current_stock,
    });
    setDialogOpen(true);
  }

  async function handleSave() {
    if (!form.name.trim()) return addToast('Nome é obrigatório', 'error');
    setSaving(true);
    try {
      if (editing) {
        await updateProduct(editing.id, form);
        addToast('Produto atualizado!');
      } else {
        await addProduct(form);
        addToast('Produto adicionado!');
      }
      setDialogOpen(false);
      load();
    } catch (e) {
      addToast(`Erro: ${e}`, 'error');
    } finally {
      setSaving(false);
    }
  }

  async function handleDeactivate() {
    if (!confirmId) return;
    setDeactivating(true);
    try {
      await deactivateProduct(confirmId);
      addToast('Produto desativado');
      setConfirmId(null);
      load();
    } catch (e) {
      addToast(`Erro: ${e}`, 'error');
    } finally {
      setDeactivating(false);
    }
  }

  function numField(field: keyof typeof form, value: string) {
    setForm((f) => ({ ...f, [field]: parseFloat(value) || 0 }));
  }

  const toggleSort = () =>
    setSort((s) => (s === 'none' ? 'asc' : s === 'asc' ? 'desc' : 'none'));

  const sortLabel =
    sort === 'asc' ? '↑ Menor estoque' : sort === 'desc' ? '↓ Maior estoque' : 'Ordenar';

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">Produtos</h1>
        <Button variant="primary" size="md" icon={<Plus size={16} />} onClick={openAdd}>
          Adicionar Produto
        </Button>
      </div>

      {/* Filters */}
      <div className="flex items-end gap-3">
        <div className="flex-1">
          <Input
            placeholder="Buscar produto..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            leftIcon={<Search size={14} />}
          />
        </div>
        <div className="w-52">
          <Select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            options={FILTER_CATS}
          />
        </div>
        <Button
          variant={sort !== 'none' ? 'primary' : 'ghost'}
          size="md"
          icon={<ArrowUpDown size={14} />}
          onClick={toggleSort}
        >
          {sortLabel}
        </Button>
      </div>

      {/* Table */}
      <Card noPad>
        {/* Table header */}
        <div className="grid grid-cols-[50px_1fr_110px_110px_110px_80px_80px_160px] gap-3 px-4 py-3 border-b border-border">
          {['ID', 'Nome', 'Categoria', 'Compra', 'Venda', 'Est.Mín', 'Est.Atual', 'Ações'].map(
            (h) => (
              <p key={h} className="text-[10px] font-semibold uppercase tracking-wider text-muted">
                {h}
              </p>
            )
          )}
        </div>

        {loading ? (
          <div className="py-12 flex justify-center">
            <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : products.length === 0 ? (
          <EmptyState
            icon={PackageX}
            title="Nenhum produto encontrado"
            description="Tente ajustar os filtros ou adicione um novo produto."
            action={
              <Button variant="primary" size="sm" icon={<Plus size={14} />} onClick={openAdd}>
                Adicionar
              </Button>
            }
          />
        ) : (
          <div>
            {products.map((p, i) => {
              const level = getStockLevel(p.current_stock, p.minimum_stock);
              return (
                <div
                  key={p.id}
                  className={`grid grid-cols-[50px_1fr_110px_110px_110px_80px_80px_160px] gap-3 px-4 py-3 items-center transition-colors ${
                    i % 2 === 0 ? '' : 'bg-white/[0.02]'
                  } hover:bg-white/[0.04] border-b border-border last:border-0`}
                >
                  <span className="text-xs text-muted font-mono">#{p.id}</span>
                  <span className="text-sm text-white font-medium truncate">{p.name}</span>
                  <span className="text-xs text-muted capitalize">{p.category}</span>
                  <span className="text-sm text-white">{formatCurrency(p.purchase_price)}</span>
                  <span className="text-sm text-white">{formatCurrency(p.sale_price)}</span>
                  <span className="text-sm text-muted text-center">{p.minimum_stock}</span>
                  <div className="flex justify-center">
                    <StockBadge current={p.current_stock} minimum={p.minimum_stock} />
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      icon={<Pencil size={12} />}
                      onClick={() => openEdit(p)}
                    >
                      Editar
                    </Button>
                    <Button
                      variant={level === 'critical' ? 'danger' : 'ghost'}
                      size="sm"
                      icon={<PackageX size={12} />}
                      onClick={() => setConfirmId(p.id)}
                    >
                      Desativar
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>

      {/* Add / Edit Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        title={editing ? 'Editar Produto' : 'Adicionar Produto'}
        size="md"
      >
        <div className="space-y-4">
          <Input
            label="Nome do Produto"
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            placeholder="Ex: Água Mineral 500ml"
          />

          <Select
            label="Categoria"
            value={form.category}
            onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}
            options={CATEGORIES}
          />

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Preço de Compra (R$)"
              type="number"
              step="0.01"
              min="0"
              value={form.purchase_price}
              onChange={(e) => numField('purchase_price', e.target.value)}
            />
            <Input
              label="Preço de Venda (R$)"
              type="number"
              step="0.01"
              min="0"
              value={form.sale_price}
              onChange={(e) => numField('sale_price', e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Estoque Mínimo"
              type="number"
              min="0"
              value={form.minimum_stock}
              onChange={(e) => numField('minimum_stock', e.target.value)}
            />
            <Input
              label="Estoque Atual"
              type="number"
              min="0"
              value={form.current_stock}
              onChange={(e) => numField('current_stock', e.target.value)}
            />
          </div>

          <div className="flex gap-3 pt-2">
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
              {editing ? 'Salvar alterações' : 'Adicionar produto'}
            </Button>
          </div>
        </div>
      </Dialog>

      {/* Confirm deactivate */}
      <ConfirmDialog
        open={confirmId !== null}
        onClose={() => setConfirmId(null)}
        onConfirm={handleDeactivate}
        title="Desativar produto?"
        message="O produto será desativado e não aparecerá mais nas listas. Esta ação pode ser revertida manualmente no banco de dados."
        confirmLabel="Desativar"
        isLoading={deactivating}
      />
    </div>
  );
}
