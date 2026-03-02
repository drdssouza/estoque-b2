import { useEffect, useState, useCallback } from 'react';
import {
  Plus,
  Search,
  Pencil,
  Trash2,
  Users,
  Phone,
  MessageCircle,
} from 'lucide-react';
import { getCustomers, addCustomer, updateCustomer, deleteCustomer } from '../lib/db';
import { formatDateTime } from '../lib/utils';
import { open as openUrl } from '@tauri-apps/plugin-shell';
import { Button } from '../components/ui/button';
import { Input, Textarea } from '../components/ui/input';
import { Dialog } from '../components/ui/dialog';
import { Card } from '../components/ui/card';
import { ConfirmDialog } from '../components/shared/ConfirmDialog';
import { EmptyState } from '../components/shared/EmptyState';
import { useAppStore } from '../store';
import type { Customer } from '../types';

const emptyForm = { name: '', phone: '', note: '' };

export default function Customers() {
  const { addToast } = useAppStore();

  const [customers, setCustomers] = useState<Customer[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Customer | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);

  const [confirmId, setConfirmId] = useState<number | null>(null);
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setCustomers(await getCustomers(search));
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => {
    load();
  }, [load]);

  function openAdd() {
    setEditing(null);
    setForm(emptyForm);
    setDialogOpen(true);
  }

  function openEdit(c: Customer) {
    setEditing(c);
    setForm({ name: c.name, phone: c.phone ?? '', note: c.note ?? '' });
    setDialogOpen(true);
  }

  async function handleSave() {
    if (!form.name.trim()) return addToast('Nome é obrigatório', 'error');
    setSaving(true);
    try {
      if (editing) {
        await updateCustomer(editing.id, form);
        addToast('Cliente atualizado!');
      } else {
        await addCustomer(form);
        addToast('Cliente cadastrado!');
      }
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
      await deleteCustomer(confirmId);
      addToast('Cliente removido');
      setConfirmId(null);
      load();
    } catch (e) {
      addToast(`Erro: ${e}`, 'error');
    } finally {
      setDeleting(false);
    }
  }

  async function openWhatsApp(customer: Customer) {
    if (!customer.phone) return addToast('Cliente sem telefone cadastrado', 'info');
    const cleanPhone = customer.phone.replace(/\D/g, '');
    await openUrl(`https://api.whatsapp.com/send?phone=55${cleanPhone}`);
  }

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Clientes</h1>
          <p className="text-xs text-muted mt-0.5">
            {customers.length} cliente{customers.length !== 1 ? 's' : ''} cadastrado{customers.length !== 1 ? 's' : ''}
          </p>
        </div>
        <Button variant="primary" size="md" icon={<Plus size={16} />} onClick={openAdd}>
          Novo Cliente
        </Button>
      </div>

      {/* Search */}
      <Input
        placeholder="Buscar por nome ou telefone..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        leftIcon={<Search size={14} />}
      />

      {/* Table */}
      <Card noPad>
        {/* Header row */}
        <div className="grid grid-cols-[50px_1fr_160px_1fr_180px] gap-4 px-5 py-3 border-b border-border">
          {['ID', 'Nome', 'Telefone', 'Observação', 'Ações'].map((h) => (
            <p key={h} className="text-[10px] font-semibold uppercase tracking-wider text-muted">
              {h}
            </p>
          ))}
        </div>

        {loading ? (
          <div className="py-12 flex justify-center">
            <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : customers.length === 0 ? (
          <EmptyState
            icon={Users}
            title="Nenhum cliente cadastrado"
            description="Cadastre clientes para agilizar a criação de comandas e o envio de mensagens."
            action={
              <Button variant="primary" size="sm" icon={<Plus size={14} />} onClick={openAdd}>
                Cadastrar cliente
              </Button>
            }
          />
        ) : (
          <div>
            {customers.map((c, i) => (
              <div
                key={c.id}
                className={`grid grid-cols-[50px_1fr_160px_1fr_180px] gap-4 px-5 py-3 items-center border-b border-border last:border-0 transition-colors hover:bg-white/[0.03] ${
                  i % 2 === 0 ? '' : 'bg-white/[0.02]'
                }`}
              >
                <span className="text-xs text-muted font-mono">#{c.id}</span>

                <div>
                  <p className="text-sm font-medium text-white">{c.name}</p>
                  <p className="text-[10px] text-muted">{formatDateTime(c.created_at)}</p>
                </div>

                <div className="flex items-center gap-1.5">
                  <Phone size={12} className="text-muted shrink-0" />
                  <span className="text-sm text-white">
                    {c.phone || <span className="text-muted italic">—</span>}
                  </span>
                </div>

                <span className="text-sm text-muted truncate">{c.note || '—'}</span>

                <div className="flex items-center gap-1.5">
                  <Button
                    variant="ghost"
                    size="xs"
                    icon={<Pencil size={11} />}
                    onClick={() => openEdit(c)}
                  >
                    Editar
                  </Button>
                  <Button
                    variant="ghost"
                    size="xs"
                    icon={<MessageCircle size={11} className="text-green-400" />}
                    onClick={() => openWhatsApp(c)}
                    className="hover:border-green-500 hover:text-green-400"
                  >
                    WhatsApp
                  </Button>
                  <button
                    className="p-1.5 rounded-lg text-muted hover:text-danger hover:bg-danger-subtle transition-colors"
                    onClick={() => setConfirmId(c.id)}
                    title="Remover"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Add / Edit Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        title={editing ? 'Editar Cliente' : 'Novo Cliente'}
        size="sm"
      >
        <div className="space-y-4">
          <Input
            label="Nome completo"
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            placeholder="Ex: João Silva"
          />

          <Input
            label="Telefone / WhatsApp"
            value={form.phone}
            onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
            placeholder="(11) 99999-9999"
            leftIcon={<Phone size={13} />}
          />

          <Textarea
            label="Observação (opcional)"
            value={form.note}
            onChange={(e) => setForm((f) => ({ ...f, note: e.target.value }))}
            placeholder="Preferências, histórico..."
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
              {editing ? 'Salvar' : 'Cadastrar'}
            </Button>
          </div>
        </div>
      </Dialog>

      {/* Confirm delete */}
      <ConfirmDialog
        open={confirmId !== null}
        onClose={() => setConfirmId(null)}
        onConfirm={handleDelete}
        title="Remover cliente?"
        message="O cliente será removido do cadastro. As comandas já criadas com o nome dele permanecem."
        confirmLabel="Remover"
        isLoading={deleting}
      />
    </div>
  );
}
