import Database from '@tauri-apps/plugin-sql';
import type { Product, Movement, Order, OrderItem, DashboardStats, Customer, ReportStats, CustomerSpending, TopCustomer } from '../types';
import { nowSqlite } from './utils';

let _db: Database | null = null;

export async function initDb(): Promise<void> {
  _db = await Database.load('sqlite:controle_b2.db');
  await _db.execute(`
    CREATE TABLE IF NOT EXISTS products (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      category TEXT NOT NULL DEFAULT 'bebida',
      purchase_price REAL NOT NULL DEFAULT 0,
      sale_price REAL NOT NULL DEFAULT 0,
      minimum_stock INTEGER NOT NULL DEFAULT 0,
      current_stock INTEGER NOT NULL DEFAULT 0,
      active INTEGER NOT NULL DEFAULT 1
    )
  `);
  await _db.execute(`
    CREATE TABLE IF NOT EXISTS movements (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      product_id INTEGER NOT NULL,
      movement_type TEXT NOT NULL,
      quantity INTEGER NOT NULL,
      note TEXT DEFAULT '',
      created_at TEXT NOT NULL
    )
  `);
  await _db.execute(`
    CREATE TABLE IF NOT EXISTS orders (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      customer_name TEXT NOT NULL,
      phone TEXT DEFAULT '',
      status TEXT NOT NULL DEFAULT 'aberta',
      total REAL NOT NULL DEFAULT 0,
      created_at TEXT NOT NULL
    )
  `);
  await _db.execute(`
    CREATE TABLE IF NOT EXISTS order_items (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      order_id INTEGER NOT NULL,
      product_id INTEGER NOT NULL,
      quantity INTEGER NOT NULL DEFAULT 1,
      unit_price REAL NOT NULL,
      subtotal REAL NOT NULL,
      added_at TEXT NOT NULL
    )
  `);
  await _db.execute(`
    CREATE TABLE IF NOT EXISTS settings (
      key TEXT PRIMARY KEY,
      value TEXT NOT NULL DEFAULT ''
    )
  `);
  await _db.execute(`
    CREATE TABLE IF NOT EXISTS customers (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      phone TEXT DEFAULT '',
      note TEXT DEFAULT '',
      created_at TEXT NOT NULL
    )
  `);
  // Migration: add closed_at to orders if not exists
  const orderCols = await _db.select<{ name: string }[]>(
    `SELECT name FROM pragma_table_info('orders')`
  );
  if (!orderCols.some((c) => c.name === 'closed_at')) {
    await _db.execute(`ALTER TABLE orders ADD COLUMN closed_at TEXT DEFAULT NULL`);
  }
}

function db(): Database {
  if (!_db) throw new Error('Banco de dados não inicializado');
  return _db;
}

// ── Products ─────────────────────────────────────────────────────────────────

export async function getProducts(search = '', category = ''): Promise<Product[]> {
  let query = 'SELECT * FROM products WHERE active = 1';
  const params: unknown[] = [];
  if (search) {
    query += ' AND LOWER(name) LIKE ?';
    params.push(`%${search.toLowerCase()}%`);
  }
  if (category && category !== 'todas') {
    query += ' AND category = ?';
    params.push(category);
  }
  query += ' ORDER BY name ASC';
  return db().select<Product[]>(query, params);
}

export async function getAllActiveProducts(): Promise<Product[]> {
  return db().select<Product[]>(
    'SELECT * FROM products WHERE active = 1 ORDER BY name ASC'
  );
}

export async function getProductById(id: number): Promise<Product | null> {
  const rows = await db().select<Product[]>('SELECT * FROM products WHERE id = ?', [id]);
  return rows[0] ?? null;
}

export async function addProduct(
  data: Omit<Product, 'id' | 'active'>
): Promise<void> {
  await db().execute(
    `INSERT INTO products (name, category, purchase_price, sale_price, minimum_stock, current_stock)
     VALUES (?, ?, ?, ?, ?, ?)`,
    [
      data.name,
      data.category,
      data.purchase_price,
      data.sale_price,
      data.minimum_stock,
      data.current_stock,
    ]
  );
}

export async function updateProduct(
  id: number,
  data: Partial<Omit<Product, 'id' | 'active'>>
): Promise<void> {
  const fields = Object.keys(data) as (keyof typeof data)[];
  if (fields.length === 0) return;
  const sets = fields.map((f) => `${f} = ?`).join(', ');
  const values = fields.map((f) => data[f]);
  await db().execute(`UPDATE products SET ${sets} WHERE id = ?`, [
    ...values,
    id,
  ]);
}

export async function deactivateProduct(id: number): Promise<void> {
  await db().execute('UPDATE products SET active = 0 WHERE id = ?', [id]);
}

export async function getLowStockProducts(): Promise<Product[]> {
  return db().select<Product[]>(
    `SELECT * FROM products
     WHERE active = 1 AND current_stock <= minimum_stock
     ORDER BY CAST(current_stock AS REAL) / CASE WHEN minimum_stock = 0 THEN 1 ELSE minimum_stock END ASC`
  );
}

// ── Orders ───────────────────────────────────────────────────────────────────

export async function getOrders(search = '', status = ''): Promise<Order[]> {
  let query = 'SELECT * FROM orders WHERE 1=1';
  const params: unknown[] = [];
  if (search) {
    query += ' AND LOWER(customer_name) LIKE ?';
    params.push(`%${search.toLowerCase()}%`);
  }
  if (status && status !== 'todas') {
    query += ' AND status = ?';
    params.push(status);
  }
  query += ' ORDER BY created_at DESC';
  return db().select<Order[]>(query, params);
}

export async function getOrderById(id: number): Promise<Order | null> {
  const rows = await db().select<Order[]>(
    'SELECT * FROM orders WHERE id = ?',
    [id]
  );
  return rows[0] ?? null;
}

export async function createOrder(customerName: string): Promise<number> {
  const now = nowSqlite();
  const result = await db().execute(
    'INSERT INTO orders (customer_name, created_at) VALUES (?, ?)',
    [customerName, now]
  );
  return result.lastInsertId!;
}

export async function updateOrderPhone(id: number, phone: string): Promise<void> {
  await db().execute('UPDATE orders SET phone = ? WHERE id = ?', [phone, id]);
}

export async function closeOrder(id: number): Promise<void> {
  const items = await db().select<OrderItem[]>(
    'SELECT * FROM order_items WHERE order_id = ?',
    [id]
  );

  // Group quantities by product
  const grouped: Record<number, number> = {};
  for (const item of items) {
    grouped[item.product_id] = (grouped[item.product_id] ?? 0) + item.quantity;
  }

  const now = nowSqlite();
  for (const [productId, qty] of Object.entries(grouped)) {
    await db().execute(
      `INSERT INTO movements (product_id, movement_type, quantity, note, created_at)
       VALUES (?, 'EXIT', ?, ?, ?)`,
      [Number(productId), qty, `Comanda #${id}`, now]
    );
    await db().execute(
      'UPDATE products SET current_stock = MAX(0, current_stock - ?) WHERE id = ?',
      [qty, Number(productId)]
    );
  }

  await db().execute(
    "UPDATE orders SET status = 'fechada', closed_at = ? WHERE id = ?",
    [now, id]
  );
}

export async function deleteOrder(id: number): Promise<void> {
  await db().execute('DELETE FROM order_items WHERE order_id = ?', [id]);
  await db().execute('DELETE FROM orders WHERE id = ?', [id]);
}

export async function getCustomerNames(): Promise<string[]> {
  const rows = await db().select<{ customer_name: string }[]>(
    'SELECT DISTINCT customer_name FROM orders ORDER BY customer_name ASC'
  );
  return rows.map((r) => r.customer_name);
}

export async function getOpenOrderByCustomerName(name: string): Promise<Order | null> {
  const rows = await db().select<Order[]>(
    "SELECT * FROM orders WHERE LOWER(customer_name) = LOWER(?) AND status = 'aberta' ORDER BY id DESC LIMIT 1",
    [name]
  );
  return rows[0] ?? null;
}

export async function getOrdersByCustomer(name: string): Promise<Order[]> {
  return db().select<Order[]>(
    'SELECT * FROM orders WHERE customer_name = ? ORDER BY created_at DESC',
    [name]
  );
}

// ── Order Items ───────────────────────────────────────────────────────────────

export async function getOrderItems(
  orderId: number
): Promise<(OrderItem & { product_name: string })[]> {
  return db().select<(OrderItem & { product_name: string })[]>(
    `SELECT oi.*, COALESCE(p.name, 'Produto removido') as product_name
     FROM order_items oi
     LEFT JOIN products p ON oi.product_id = p.id
     WHERE oi.order_id = ?
     ORDER BY oi.id ASC`,
    [orderId]
  );
}

async function recalcOrderTotal(orderId: number): Promise<void> {
  await db().execute(
    `UPDATE orders
     SET total = (SELECT COALESCE(SUM(subtotal), 0) FROM order_items WHERE order_id = ?)
     WHERE id = ?`,
    [orderId, orderId]
  );
}

export async function addOrderItem(
  orderId: number,
  productId: number,
  unitPrice: number
): Promise<void> {
  const now = nowSqlite();
  await db().execute(
    `INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal, added_at)
     VALUES (?, ?, 1, ?, ?, ?)`,
    [orderId, productId, unitPrice, unitPrice, now]
  );
  await recalcOrderTotal(orderId);
}

export async function decrementOrderItem(
  orderId: number,
  productId: number
): Promise<void> {
  const rows = await db().select<OrderItem[]>(
    'SELECT * FROM order_items WHERE order_id = ? AND product_id = ? ORDER BY id DESC LIMIT 1',
    [orderId, productId]
  );
  if (!rows.length) return;
  const item = rows[0];
  if (item.quantity <= 1) {
    await db().execute('DELETE FROM order_items WHERE id = ?', [item.id]);
  } else {
    const newQty = item.quantity - 1;
    await db().execute(
      'UPDATE order_items SET quantity = ?, subtotal = ? WHERE id = ?',
      [newQty, newQty * item.unit_price, item.id]
    );
  }
  await recalcOrderTotal(orderId);
}

export async function removeAllItemsOfProduct(
  orderId: number,
  productId: number
): Promise<void> {
  await db().execute(
    'DELETE FROM order_items WHERE order_id = ? AND product_id = ?',
    [orderId, productId]
  );
  await recalcOrderTotal(orderId);
}

// ── Movements ────────────────────────────────────────────────────────────────

export async function getMovements(): Promise<
  (Movement & { product_name: string })[]
> {
  return db().select<(Movement & { product_name: string })[]>(
    `SELECT m.*, COALESCE(p.name, 'Produto removido') as product_name
     FROM movements m
     LEFT JOIN products p ON m.product_id = p.id
     ORDER BY m.id DESC`
  );
}

export async function addMovement(
  productId: number,
  quantity: number,
  note = ''
): Promise<void> {
  const now = nowSqlite();
  await db().execute(
    `INSERT INTO movements (product_id, movement_type, quantity, note, created_at)
     VALUES (?, 'ENTRY', ?, ?, ?)`,
    [productId, quantity, note, now]
  );
  await db().execute(
    'UPDATE products SET current_stock = current_stock + ? WHERE id = ?',
    [quantity, productId]
  );
}

export async function removeMovement(id: number): Promise<void> {
  const rows = await db().select<Movement[]>(
    'SELECT * FROM movements WHERE id = ?',
    [id]
  );
  if (!rows.length) return;
  const m = rows[0];
  await db().execute('DELETE FROM movements WHERE id = ?', [id]);
  if (m.movement_type === 'ENTRY') {
    await db().execute(
      'UPDATE products SET current_stock = MAX(0, current_stock - ?) WHERE id = ?',
      [m.quantity, m.product_id]
    );
  }
}

// ── Settings ─────────────────────────────────────────────────────────────────

export async function getSetting(key: string, fallback = ''): Promise<string> {
  const rows = await db().select<{ value: string }[]>(
    'SELECT value FROM settings WHERE key = ?',
    [key]
  );
  return rows[0]?.value ?? fallback;
}

export async function setSetting(key: string, value: string): Promise<void> {
  await db().execute(
    `INSERT INTO settings (key, value) VALUES (?, ?)
     ON CONFLICT(key) DO UPDATE SET value = excluded.value`,
    [key, value]
  );
}

// ── Dashboard ────────────────────────────────────────────────────────────────

export async function getDashboardStats(): Promise<DashboardStats> {
  const [totalRows, catRows, openRows, revenueRows, lowStock] =
    await Promise.all([
      db().select<{ count: number }[]>(
        'SELECT COUNT(*) as count FROM products WHERE active = 1'
      ),
      db().select<{ category: string; count: number }[]>(
        'SELECT category, COUNT(*) as count FROM products WHERE active = 1 GROUP BY category'
      ),
      db().select<{ count: number }[]>(
        "SELECT COUNT(*) as count FROM orders WHERE status = 'aberta'"
      ),
      db().select<{ total: number }[]>(
        `SELECT COALESCE(SUM(total), 0) as total FROM orders
         WHERE status = 'fechada'
         AND date(created_at) = date('now', 'localtime')`
      ),
      getLowStockProducts(),
    ]);

  const byCategory: Record<string, number> = {};
  for (const row of catRows) {
    byCategory[row.category] = row.count;
  }

  return {
    totalProducts: totalRows[0]?.count ?? 0,
    byCategory,
    openOrders: openRows[0]?.count ?? 0,
    todayRevenue: revenueRows[0]?.total ?? 0,
    lowStock,
  };
}

// ── Customers ─────────────────────────────────────────────────────────────────

export async function getCustomers(search = ''): Promise<Customer[]> {
  let query = 'SELECT * FROM customers';
  const params: unknown[] = [];
  if (search) {
    query += ' WHERE LOWER(name) LIKE ? OR LOWER(phone) LIKE ?';
    params.push(`%${search.toLowerCase()}%`, `%${search.toLowerCase()}%`);
  }
  query += ' ORDER BY name ASC';
  return db().select<Customer[]>(query, params);
}

export async function addCustomer(data: Omit<Customer, 'id' | 'created_at'>): Promise<void> {
  const now = nowSqlite();
  await db().execute(
    'INSERT INTO customers (name, phone, note, created_at) VALUES (?, ?, ?, ?)',
    [data.name, data.phone ?? '', data.note ?? '', now]
  );
}

export async function updateCustomer(id: number, data: Partial<Omit<Customer, 'id' | 'created_at'>>): Promise<void> {
  const fields = Object.keys(data) as (keyof typeof data)[];
  if (!fields.length) return;
  const sets = fields.map((f) => `${f} = ?`).join(', ');
  const values = fields.map((f) => data[f]);
  await db().execute(`UPDATE customers SET ${sets} WHERE id = ?`, [...values, id]);
}

export async function deleteCustomer(id: number): Promise<void> {
  await db().execute('DELETE FROM customers WHERE id = ?', [id]);
}

export async function searchCustomers(term: string): Promise<Customer[]> {
  if (!term) return [];
  return db().select<Customer[]>(
    `SELECT * FROM customers WHERE LOWER(name) LIKE ? ORDER BY name ASC LIMIT 8`,
    [`%${term.toLowerCase()}%`]
  );
}

// ── Seed / Demo Data ──────────────────────────────────────────────────────────

export async function seedDemoData(): Promise<void> {
  const existing = await db().select<{ count: number }[]>(
    'SELECT COUNT(*) as count FROM products WHERE active = 1'
  );
  if ((existing[0]?.count ?? 0) > 5) {
    throw new Error('Já existem dados cadastrados. Limpe o banco antes de popular com dados demo.');
  }

  function pastDate(daysAgo: number, hour = 14, minute = 30): string {
    const d = new Date();
    d.setDate(d.getDate() - daysAgo);
    d.setHours(hour, minute, 0, 0);
    const pad = (n: number) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
  }

  // ── Products ────────────────────────────────────────────────────────────────
  const PRODUCTS = [
    { name: 'Água Mineral 500ml',     category: 'bebida',    purchase_price: 0.80,  sale_price: 3.50,  minimum_stock: 30, current_stock: 120 },
    { name: 'Coca-Cola Lata 350ml',   category: 'bebida',    purchase_price: 2.50,  sale_price: 7.00,  minimum_stock: 20, current_stock: 85  },
    { name: 'Cerveja Heineken 600ml', category: 'bebida',    purchase_price: 8.00,  sale_price: 18.00, minimum_stock: 15, current_stock: 60  },
    { name: 'Cerveja Brahma 600ml',   category: 'bebida',    purchase_price: 5.50,  sale_price: 12.00, minimum_stock: 15, current_stock: 8   },
    { name: 'Red Bull 250ml',         category: 'bebida',    purchase_price: 6.00,  sale_price: 14.00, minimum_stock: 10, current_stock: 25  },
    { name: 'Suco de Laranja 400ml',  category: 'bebida',    purchase_price: 3.00,  sale_price: 9.00,  minimum_stock: 10, current_stock: 4   },
    { name: 'Água de Coco 330ml',     category: 'bebida',    purchase_price: 2.50,  sale_price: 8.00,  minimum_stock: 10, current_stock: 32  },
    { name: 'Isotônico Gatorade',     category: 'bebida',    purchase_price: 3.50,  sale_price: 9.00,  minimum_stock: 10, current_stock: 18  },
    { name: 'Açaí 300ml',             category: 'doce',      purchase_price: 8.00,  sale_price: 20.00, minimum_stock: 8,  current_stock: 14  },
    { name: 'Sorvete Napolitano',     category: 'doce',      purchase_price: 4.00,  sale_price: 10.00, minimum_stock: 10, current_stock: 3   },
    { name: 'Barra de Cereal',        category: 'doce',      purchase_price: 2.00,  sale_price: 5.00,  minimum_stock: 15, current_stock: 22  },
    { name: 'Coxinha de Frango',      category: 'salgado',   purchase_price: 3.50,  sale_price: 8.00,  minimum_stock: 20, current_stock: 45  },
    { name: 'Pão de Queijo (2un)',    category: 'salgado',   purchase_price: 2.00,  sale_price: 6.00,  minimum_stock: 20, current_stock: 38  },
    { name: 'Hambúrguer Artesanal',   category: 'salgado',   purchase_price: 12.00, sale_price: 28.00, minimum_stock: 5,  current_stock: 9   },
    { name: 'Sanduíche Natural',      category: 'salgado',   purchase_price: 6.00,  sale_price: 15.00, minimum_stock: 8,  current_stock: 20  },
    { name: 'Pastel de Queijo',       category: 'salgado',   purchase_price: 3.00,  sale_price: 7.00,  minimum_stock: 10, current_stock: 30  },
    { name: 'Meias Esportivas',       category: 'acessório', purchase_price: 8.00,  sale_price: 19.90, minimum_stock: 5,  current_stock: 14  },
    { name: 'Toalha Esportiva',       category: 'acessório', purchase_price: 12.00, sale_price: 29.90, minimum_stock: 3,  current_stock: 2   },
    { name: 'Protetor Solar FPS50',   category: 'acessório', purchase_price: 15.00, sale_price: 35.00, minimum_stock: 5,  current_stock: 8   },
  ];

  const pIds: number[] = [];
  for (const p of PRODUCTS) {
    const r = await db().execute(
      `INSERT INTO products (name, category, purchase_price, sale_price, minimum_stock, current_stock)
       VALUES (?, ?, ?, ?, ?, ?)`,
      [p.name, p.category, p.purchase_price, p.sale_price, p.minimum_stock, p.current_stock]
    );
    pIds.push(r.lastInsertId!);
  }

  // ── Customers ───────────────────────────────────────────────────────────────
  const CUSTOMERS = [
    { name: 'João Silva',       phone: '(11) 99234-5678', note: 'Cliente frequente' },
    { name: 'Maria Santos',     phone: '(11) 98765-4321', note: '' },
    { name: 'Carlos Oliveira',  phone: '(21) 97654-3210', note: 'Prefere água de coco' },
    { name: 'Ana Costa',        phone: '(11) 96543-2109', note: '' },
    { name: 'Pedro Almeida',    phone: '(21) 95432-1098', note: '' },
    { name: 'Fernanda Lima',    phone: '(11) 94321-0987', note: '' },
    { name: 'Lucas Souza',      phone: '(11) 93210-9876', note: 'Jogador de vôlei' },
    { name: 'Julia Ferreira',   phone: '(21) 92109-8765', note: '' },
    { name: 'Rafael Rodrigues', phone: '(11) 91098-7654', note: 'Mensalista' },
    { name: 'Camila Pereira',   phone: '(11) 90987-6543', note: '' },
    { name: 'Bruno Martins',    phone: '(21) 99876-5432', note: 'Professor de natação' },
    { name: 'Isabela Carvalho', phone: '(11) 98765-0001', note: '' },
  ];

  for (const c of CUSTOMERS) {
    await db().execute(
      'INSERT INTO customers (name, phone, note, created_at) VALUES (?, ?, ?, ?)',
      [c.name, c.phone, c.note, pastDate(90)]
    );
  }

  // ── Orders ──────────────────────────────────────────────────────────────────
  // [name, phone, daysAgo, hour, closed, [[productIdx, qty], ...]]
  type OS = [string, string, number, number, boolean, [number, number][]];
  const ORDERS: OS[] = [
    // Today - open
    ['João Silva',       '(11) 99234-5678', 0,  9,  false, [[0,2],[1,1],[11,1]]],
    ['Maria Santos',     '(11) 98765-4321', 0,  10, false, [[2,2],[12,3]]],
    ['Carlos Oliveira',  '(21) 97654-3210', 0,  11, false, [[6,1],[13,1],[0,1]]],
    // Today - closed
    ['Pedro Almeida',    '(21) 95432-1098', 0,  8,  true,  [[1,3],[11,2]]],
    ['Fernanda Lima',    '(11) 94321-0987', 0,  9,  true,  [[8,1],[1,2],[7,1]]],
    // Yesterday
    ['Lucas Souza',      '(11) 93210-9876', 1,  14, true,  [[2,4],[0,2],[12,2]]],
    ['Julia Ferreira',   '(21) 92109-8765', 1,  16, true,  [[4,2],[1,1],[9,1]]],
    ['Rafael Rodrigues', '(11) 91098-7654', 1,  18, false, [[3,3],[11,2],[16,1]]],
    // 2 days ago
    ['Camila Pereira',   '(11) 90987-6543', 2,  10, true,  [[8,1],[1,1],[12,2]]],
    ['Bruno Martins',    '(21) 99876-5432', 2,  12, true,  [[2,2],[13,1],[7,2]]],
    // 3 days ago
    ['João Silva',       '(11) 99234-5678', 3,  11, true,  [[0,3],[11,3],[12,2],[1,1]]],
    ['Isabela Carvalho', '(11) 98765-0001', 3,  15, true,  [[5,2],[10,1],[14,1]]],
    // 5 days ago
    ['Maria Santos',     '(11) 98765-4321', 5,  9,  true,  [[2,3],[0,2],[8,1]]],
    ['Carlos Oliveira',  '(21) 97654-3210', 5,  13, true,  [[6,3],[4,1],[17,1]]],
    // 7 days ago
    ['Pedro Almeida',    '(21) 95432-1098', 7,  10, true,  [[13,2],[0,3],[1,2]]],
    ['Lucas Souza',      '(11) 93210-9876', 7,  16, true,  [[2,2],[18,1],[9,1]]],
    // 10 days ago
    ['Rafael Rodrigues', '(11) 91098-7654', 10, 11, true,  [[8,1],[1,3],[11,2]]],
    ['Fernanda Lima',    '(11) 94321-0987', 10, 14, true,  [[3,4],[12,3],[7,1]]],
    // 15 days ago
    ['Camila Pereira',   '(11) 90987-6543', 15, 9,  true,  [[2,2],[0,4],[13,1]]],
    ['João Silva',       '(11) 99234-5678', 15, 17, true,  [[4,3],[11,2],[1,1],[16,1]]],
    // 20 days ago
    ['Julia Ferreira',   '(21) 92109-8765', 20, 10, true,  [[8,2],[12,2],[6,1]]],
    ['Bruno Martins',    '(21) 99876-5432', 20, 14, true,  [[2,3],[17,1],[0,2]]],
    // 25 days ago
    ['Maria Santos',     '(11) 98765-4321', 25, 11, true,  [[1,4],[11,3],[10,2]]],
    ['Isabela Carvalho', '(11) 98765-0001', 25, 16, true,  [[8,1],[13,1],[7,1],[0,2]]],
    // 35 days ago (last month)
    ['Carlos Oliveira',  '(21) 97654-3210', 35, 10, true,  [[2,5],[12,4],[0,3]]],
    ['Pedro Almeida',    '(21) 95432-1098', 35, 14, true,  [[4,2],[9,1],[11,2]]],
    // 45 days ago
    ['Rafael Rodrigues', '(11) 91098-7654', 45, 11, true,  [[8,1],[1,3],[13,1],[16,1]]],
    ['Lucas Souza',      '(11) 93210-9876', 45, 15, true,  [[2,4],[12,2],[0,2]]],
    // 60 days ago (2 months ago)
    ['Fernanda Lima',    '(11) 94321-0987', 60, 9,  true,  [[3,3],[11,2],[0,4]]],
    ['João Silva',       '(11) 99234-5678', 60, 13, true,  [[2,2],[8,1],[7,2],[1,1]]],
    // 70 days ago
    ['Camila Pereira',   '(11) 90987-6543', 70, 11, true,  [[13,2],[12,3],[0,2]]],
    ['Julia Ferreira',   '(21) 92109-8765', 70, 16, true,  [[4,1],[9,1],[11,1],[1,2]]],
    // 80 days ago
    ['Bruno Martins',    '(21) 99876-5432', 80, 10, true,  [[2,3],[17,1],[8,1]]],
    ['Maria Santos',     '(11) 98765-4321', 80, 14, true,  [[1,4],[11,3],[0,3]]],
    // 85 days ago
    ['Ana Costa',        '(11) 96543-2109', 85, 12, true,  [[15,2],[6,2],[0,4]]],
  ];

  for (const [cName, cPhone, daysAgo, hour, closed, items] of ORDERS) {
    const orderDate = pastDate(daysAgo, hour);
    const r = await db().execute(
      `INSERT INTO orders (customer_name, phone, status, total, created_at)
       VALUES (?, ?, 'aberta', 0, ?)`,
      [cName, cPhone, orderDate]
    );
    const orderId = r.lastInsertId;

    let total = 0;
    for (const [pIdx, qty] of items) {
      const unitPrice = PRODUCTS[pIdx].sale_price;
      const subtotal = unitPrice * qty;
      total += subtotal;
      await db().execute(
        `INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal, added_at)
         VALUES (?, ?, ?, ?, ?, ?)`,
        [orderId, pIds[pIdx], qty, unitPrice, subtotal, orderDate]
      );
    }

    await db().execute('UPDATE orders SET total = ? WHERE id = ?', [total, orderId]);

    if (closed) {
      for (const [pIdx, qty] of items) {
        await db().execute(
          `INSERT INTO movements (product_id, movement_type, quantity, note, created_at)
           VALUES (?, 'EXIT', ?, ?, ?)`,
          [pIds[pIdx], qty, `Comanda #${orderId}`, orderDate]
        );
      }
      await db().execute("UPDATE orders SET status = 'fechada' WHERE id = ?", [orderId]);
    }
  }

  // ── Entry movements (restocking history) ────────────────────────────────────
  const ENTRIES: [number, number, string, number][] = [
    [0,  200, 'Reposição inicial',            90],
    [1,  144, 'Reposição inicial',            90],
    [2,   96, 'Reposição inicial',            90],
    [3,   80, 'Reposição inicial',            90],
    [4,   60, 'Reposição inicial',            90],
    [5,   40, 'Reposição inicial',            90],
    [6,   80, 'Reposição inicial',            90],
    [7,   60, 'Reposição inicial',            90],
    [8,   40, 'Reposição inicial',            90],
    [11, 120, 'Reposição inicial',            90],
    [12, 100, 'Reposição inicial',            90],
    [0,  100, 'Compra Distribuidora Norte',   55],
    [1,   72, 'Compra Distribuidora Norte',   55],
    [2,   48, 'Compra Distribuidora Norte',   40],
    [11,  80, 'Compra Distribuidora Norte',   30],
    [3,   24, 'Compra Distribuidora Sul',     20],
    [8,   30, 'Fornecedor Açaí Premium',      15],
  ];

  for (const [pIdx, qty, note, daysAgo] of ENTRIES) {
    await db().execute(
      `INSERT INTO movements (product_id, movement_type, quantity, note, created_at)
       VALUES (?, 'ENTRY', ?, ?, ?)`,
      [pIds[pIdx], qty, note, pastDate(daysAgo, 8, 0)]
    );
  }
}

// ── Customer Spending ─────────────────────────────────────────────────────────

export async function getCustomerSpending(name: string): Promise<CustomerSpending | null> {
  if (!name.trim()) return null;
  const orders = await db().select<Order[]>(
    `SELECT * FROM orders WHERE LOWER(customer_name) LIKE LOWER(?) ORDER BY created_at DESC`,
    [`%${name.toLowerCase()}%`]
  );
  if (!orders.length) return null;
  const total = orders.reduce((sum, o) => sum + o.total, 0);
  return {
    customer_name: orders[0].customer_name,
    total,
    count: orders.length,
    avg_ticket: total / orders.length,
    orders,
  };
}

export async function getTopCustomers(limit = 15, dateFrom?: string, dateTo?: string): Promise<TopCustomer[]> {
  const hasFilter = !!(dateFrom && dateTo);
  const dateClause = hasFilter ? ` AND date(created_at) >= ? AND date(created_at) <= ?` : '';
  const params = hasFilter ? [dateFrom!, dateTo!, limit] : [limit];
  return db().select<TopCustomer[]>(
    `SELECT customer_name,
            SUM(total) as total,
            COUNT(*) as count
     FROM orders
     WHERE status = 'fechada'${dateClause}
     GROUP BY LOWER(customer_name)
     ORDER BY total DESC
     LIMIT ?`,
    params
  );
}

// ── Reports ───────────────────────────────────────────────────────────────────

export async function getReportStats(dateFrom?: string, dateTo?: string): Promise<ReportStats> {
  const hasFilter = !!(dateFrom && dateTo);

  if (hasFilter) {
    const dp = [dateFrom!, dateTo!];
    const closedDateFilter = ` AND date(created_at) >= ? AND date(created_at) <= ?`;
    const [periodRows, topProductRows, monthlyRows, statusRows] = await Promise.all([
      db().select<{ total: number; count: number }[]>(
        `SELECT COALESCE(SUM(total),0) as total, COUNT(*) as count FROM orders
         WHERE status='fechada'${closedDateFilter}`,
        dp
      ),
      db().select<{ name: string; total_qty: number; revenue: number }[]>(
        `SELECT p.name, SUM(oi.quantity) as total_qty, SUM(oi.subtotal) as revenue
         FROM order_items oi
         JOIN products p ON oi.product_id = p.id
         JOIN orders o ON oi.order_id = o.id
         WHERE o.status='fechada'${closedDateFilter}
         GROUP BY LOWER(p.name)
         ORDER BY total_qty DESC
         LIMIT 10`,
        dp
      ),
      db().select<{ month: string; count: number; revenue: number }[]>(
        `SELECT strftime('%m/%Y', created_at) as month,
                COUNT(*) as count,
                COALESCE(SUM(total),0) as revenue
         FROM orders WHERE status='fechada'${closedDateFilter}
         GROUP BY strftime('%Y-%m', created_at)
         ORDER BY strftime('%Y-%m', created_at) DESC`,
        dp
      ),
      db().select<{ status: string; count: number }[]>(
        `SELECT status, COUNT(*) as count FROM orders
         WHERE date(created_at) >= ? AND date(created_at) <= ?
         GROUP BY status`,
        dp
      ),
    ]);
    const zero = { total: 0, count: 0 };
    return {
      today: zero,
      week: zero,
      month: zero,
      allTime: { total: periodRows[0]?.total ?? 0, count: periodRows[0]?.count ?? 0 },
      topProducts: topProductRows,
      monthly: monthlyRows.reverse(),
      byStatus: Object.fromEntries(statusRows.map((r) => [r.status, r.count])),
    };
  }

  const [todayRows, weekRows, monthRows, allTimeRows, topProductRows, monthlyRows, statusRows] =
    await Promise.all([
      db().select<{ total: number; count: number }[]>(
        `SELECT COALESCE(SUM(total),0) as total, COUNT(*) as count FROM orders
         WHERE status='fechada' AND date(created_at)=date('now','localtime')`
      ),
      db().select<{ total: number; count: number }[]>(
        `SELECT COALESCE(SUM(total),0) as total, COUNT(*) as count FROM orders
         WHERE status='fechada' AND date(created_at)>=date('now','localtime','-6 days')`
      ),
      db().select<{ total: number; count: number }[]>(
        `SELECT COALESCE(SUM(total),0) as total, COUNT(*) as count FROM orders
         WHERE status='fechada' AND strftime('%Y-%m',created_at)=strftime('%Y-%m','now','localtime')`
      ),
      db().select<{ total: number; count: number }[]>(
        `SELECT COALESCE(SUM(total),0) as total, COUNT(*) as count FROM orders WHERE status='fechada'`
      ),
      db().select<{ name: string; total_qty: number; revenue: number }[]>(
        `SELECT p.name, SUM(oi.quantity) as total_qty, SUM(oi.subtotal) as revenue
         FROM order_items oi
         JOIN products p ON oi.product_id = p.id
         JOIN orders o ON oi.order_id = o.id
         WHERE o.status='fechada'
         GROUP BY LOWER(p.name)
         ORDER BY total_qty DESC
         LIMIT 10`
      ),
      db().select<{ month: string; count: number; revenue: number }[]>(
        `SELECT strftime('%m/%Y', created_at) as month,
                COUNT(*) as count,
                COALESCE(SUM(total),0) as revenue
         FROM orders WHERE status='fechada'
         GROUP BY strftime('%Y-%m', created_at)
         ORDER BY strftime('%Y-%m', created_at) DESC
         LIMIT 6`
      ),
      db().select<{ status: string; count: number }[]>(
        `SELECT status, COUNT(*) as count FROM orders GROUP BY status`
      ),
    ]);

  return {
    today: { total: todayRows[0]?.total ?? 0, count: todayRows[0]?.count ?? 0 },
    week: { total: weekRows[0]?.total ?? 0, count: weekRows[0]?.count ?? 0 },
    month: { total: monthRows[0]?.total ?? 0, count: monthRows[0]?.count ?? 0 },
    allTime: { total: allTimeRows[0]?.total ?? 0, count: allTimeRows[0]?.count ?? 0 },
    topProducts: topProductRows,
    monthly: monthlyRows.reverse(),
    byStatus: Object.fromEntries(statusRows.map((r) => [r.status, r.count])),
  };
}
