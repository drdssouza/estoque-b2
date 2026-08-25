import type { StockLevel } from '../types';

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value);
}

export function formatDateTime(dt: string): string {
  if (!dt) return '';
  try {
    const d = new Date(dt.replace(' ', 'T'));
    return d.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dt;
  }
}

export function formatDate(dt: string): string {
  if (!dt) return '';
  try {
    const d = new Date(dt.replace(' ', 'T'));
    return d.toLocaleDateString('pt-BR');
  } catch {
    return dt;
  }
}

/** Data/hora curta para mensagens e listas: "25/08 às 14:30" */
export function formatShortDateTime(dt: string): string {
  if (!dt) return '';
  try {
    const d = new Date(dt.replace(' ', 'T'));
    const date = d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
    const time = d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    return `${date} às ${time}`;
  } catch {
    return dt;
  }
}

/** Converte o que o usuário digitou ("1.234,50", "100.50", "R$ 80") em número. NaN se inválido. */
export function parseAmount(input: string): number {
  const clean = String(input).replace(/[^\d.,-]/g, '').trim();
  if (!clean) return NaN;
  // pt-BR: vírgula é o separador decimal, ponto é separador de milhar
  const normalized = clean.includes(',')
    ? clean.replace(/\./g, '').replace(',', '.')
    : clean;
  const n = Number(normalized);
  return Number.isFinite(n) ? n : NaN;
}

export function getStockLevel(current: number, minimum: number): StockLevel {
  if (minimum === 0) return 'ok';
  const ratio = current / minimum;
  if (ratio <= 0.5) return 'critical';
  if (ratio <= 1) return 'warning';
  return 'ok';
}

export function getStockPercent(current: number, minimum: number): number {
  if (minimum === 0) return 100;
  return Math.min(100, Math.round((current / minimum) * 100));
}

export function cn(...classes: (string | false | undefined | null)[]): string {
  return classes.filter(Boolean).join(' ');
}

export function nowSqlite(): string {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

export function backupTimestamp(): string {
  return new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
}
