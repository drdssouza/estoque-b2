export interface Product {
  id: number;
  name: string;
  category: string;
  purchase_price: number;
  sale_price: number;
  minimum_stock: number;
  current_stock: number;
  active: number; // SQLite stores booleans as 0/1
}

export interface Movement {
  id: number;
  product_id: number;
  product_name?: string;
  movement_type: 'ENTRY' | 'EXIT';
  quantity: number;
  note: string;
  created_at: string;
}

export interface Order {
  id: number;
  customer_name: string;
  phone: string;
  status: 'aberta' | 'fechada';
  total: number;
  created_at: string;
  closed_at?: string | null;
}

export interface OrderItem {
  id: number;
  order_id: number;
  product_id: number;
  product_name?: string;
  quantity: number;
  unit_price: number;
  subtotal: number;
  added_at: string;
}

export interface GroupedOrderItem {
  product_id: number;
  product_name: string;
  total_quantity: number;
  unit_price: number;
  subtotal: number;
  item_ids: number[];
  added_at: string;
  added_ats: string[];
}

export interface DashboardStats {
  totalProducts: number;
  byCategory: Record<string, number>;
  openOrders: number;
  todayRevenue: number;
  lowStock: Product[];
}

export type StockLevel = 'ok' | 'warning' | 'critical';

export interface Toast {
  id: number;
  text: string;
  type: 'success' | 'error' | 'info';
}

export interface Customer {
  id: number;
  name: string;
  phone: string;
  note: string;
  created_at: string;
}

export interface ReportStats {
  today: { total: number; count: number };
  week: { total: number; count: number };
  month: { total: number; count: number };
  allTime: { total: number; count: number };
  topProducts: { name: string; total_qty: number; revenue: number }[];
  monthly: { month: string; count: number; revenue: number }[];
  byStatus: Record<string, number>;
}
