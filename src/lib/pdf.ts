import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import type { Order, GroupedOrderItem } from '../types';
import { formatCurrency, formatDateTime } from './utils';

export function generateOrderPdf(
  order: Order,
  items: GroupedOrderItem[],
  pixKey: string
): Uint8Array {
  const doc = new jsPDF({ unit: 'mm', format: 'a4' });

  const green = [34, 197, 94] as [number, number, number];
  const dark = [9, 9, 11] as [number, number, number];
  const white = [255, 255, 255] as [number, number, number];
  const gray = [120, 120, 120] as [number, number, number];

  const pageW = doc.internal.pageSize.getWidth();

  // ── Header background ──────────────────────────────────────────────────────
  doc.setFillColor(...dark);
  doc.rect(0, 0, pageW, 42, 'F');

  // Logo text
  doc.setFontSize(22);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(...green);
  doc.text('CONTROLE B2', 15, 16);

  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(...white);
  doc.text('Sistema de Gestão de Estoque e Comandas', 15, 23);

  // Order title (right side)
  doc.setFontSize(18);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(...green);
  doc.text(`Comanda #${order.id}`, pageW - 15, 16, { align: 'right' });

  doc.setFontSize(9);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(...white);
  doc.text(
    order.status === 'fechada' ? '● FECHADA' : '● ABERTA',
    pageW - 15,
    23,
    { align: 'right' }
  );

  // ── Info section ──────────────────────────────────────────────────────────
  doc.setFillColor(245, 245, 245);
  doc.rect(0, 42, pageW, 28, 'F');

  doc.setFontSize(9);
  doc.setTextColor(...gray);
  doc.setFont('helvetica', 'normal');

  doc.text('CLIENTE', 15, 52);
  doc.text('DATA / HORA', 90, 52);
  doc.text('TELEFONE', 155, 52);

  doc.setFontSize(11);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(20, 20, 20);
  doc.text(order.customer_name, 15, 60);
  doc.text(formatDateTime(order.created_at), 90, 60);
  doc.text(order.phone || '—', 155, 60);

  // ── Items table ───────────────────────────────────────────────────────────
  autoTable(doc, {
    startY: 78,
    head: [['Produto', 'Qtd', 'Preço Unit.', 'Subtotal']],
    body: items.map((item) => [
      item.product_name,
      item.total_quantity.toString(),
      formatCurrency(item.unit_price),
      formatCurrency(item.subtotal),
    ]),
    headStyles: {
      fillColor: dark,
      textColor: green,
      fontStyle: 'bold',
      fontSize: 9,
    },
    bodyStyles: {
      fontSize: 9,
      textColor: [30, 30, 30],
    },
    alternateRowStyles: {
      fillColor: [248, 248, 248],
    },
    columnStyles: {
      0: { cellWidth: 'auto' },
      1: { halign: 'center', cellWidth: 20 },
      2: { halign: 'right', cellWidth: 35 },
      3: { halign: 'right', cellWidth: 35 },
    },
    margin: { left: 15, right: 15 },
  });

  // ── Total ─────────────────────────────────────────────────────────────────
  const finalY = (doc as unknown as { lastAutoTable: { finalY: number } })
    .lastAutoTable.finalY;

  doc.setFillColor(...dark);
  doc.rect(0, finalY + 4, pageW, 18, 'F');

  doc.setFontSize(11);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(...white);
  doc.text('TOTAL DA COMANDA', 15, finalY + 15);

  doc.setTextColor(...green);
  doc.setFontSize(14);
  doc.text(formatCurrency(order.total), pageW - 15, finalY + 15, {
    align: 'right',
  });

  // ── PIX footer ────────────────────────────────────────────────────────────
  if (pixKey) {
    const footerY = finalY + 32;
    doc.setFillColor(245, 245, 245);
    doc.roundedRect(15, footerY, pageW - 30, 20, 3, 3, 'F');

    doc.setFontSize(8);
    doc.setTextColor(...gray);
    doc.setFont('helvetica', 'normal');
    doc.text('PAGAMENTO VIA PIX', pageW / 2, footerY + 7, { align: 'center' });

    doc.setFontSize(11);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(20, 20, 20);
    doc.text(pixKey, pageW / 2, footerY + 15, { align: 'center' });
  }

  return new Uint8Array(doc.output('arraybuffer') as ArrayBuffer);
}
