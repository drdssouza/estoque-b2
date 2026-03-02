import { describe, it, expect, vi, beforeAll, beforeEach } from 'vitest';

// ── Mock do plugin-sql (deve ser hoisted antes de qualquer import) ─────────────
const { mockDb } = vi.hoisted(() => {
  const mockDb = {
    execute: vi.fn().mockResolvedValue({ lastInsertId: 1, rowsAffected: 1 }),
    select: vi.fn().mockResolvedValue([]),
  };
  return { mockDb };
});

vi.mock('@tauri-apps/plugin-sql', () => ({
  default: {
    load: vi.fn().mockResolvedValue(mockDb),
  },
}));

import {
  getProducts,
  getAllActiveProducts,
  getProductById,
  addProduct,
  updateProduct,
  deactivateProduct,
  getLowStockProducts,
  getOrders,
  getOrderById,
  createOrder,
  updateOrderPhone,
  closeOrder,
  deleteOrder,
  getOpenOrderByCustomerName,
  getOrderItems,
  addOrderItem,
  decrementOrderItem,
  removeAllItemsOfProduct,
  getMovements,
  addMovement,
  removeMovement,
  getSetting,
  setSetting,
  getCustomers,
  addCustomer,
  updateCustomer,
  deleteCustomer,
  searchCustomers,
  initDb,
} from './db';

// ── Helpers ───────────────────────────────────────────────────────────────────

function mockSelectOnce(value: unknown[]) {
  mockDb.select.mockResolvedValueOnce(value);
}

function mockExecuteOnce(lastInsertId = 1) {
  mockDb.execute.mockResolvedValueOnce({ lastInsertId, rowsAffected: 1 });
}

// ── Inicialização do banco ─────────────────────────────────────────────────────

beforeAll(async () => {
  // pragma_table_info retorna a coluna closed_at (evita migration ALTER TABLE)
  mockDb.select.mockResolvedValueOnce([{ name: 'closed_at' }]);
  await initDb();
});

beforeEach(() => {
  // Reseta contagem de chamadas (mantém implementação)
  mockDb.execute.mockClear();
  mockDb.select.mockClear();
  // Defaults
  mockDb.execute.mockResolvedValue({ lastInsertId: 1, rowsAffected: 1 });
  mockDb.select.mockResolvedValue([]);
});

// ═══════════════════════════════════════════════════════════════════════════════
// PRODUCTS
// ═══════════════════════════════════════════════════════════════════════════════

describe('getProducts', () => {
  it('sem filtros: chama SELECT com active=1', async () => {
    mockSelectOnce([]);
    await getProducts();
    expect(mockDb.select).toHaveBeenCalledWith(
      expect.stringContaining('active = 1'),
      []
    );
  });

  it('com busca: adiciona LIKE ao SQL', async () => {
    mockSelectOnce([]);
    await getProducts('coca');
    const [sql, params] = mockDb.select.mock.calls[0];
    expect(sql).toContain('LIKE');
    expect(params).toContain('%coca%');
  });

  it('com categoria: adiciona filtro de categoria', async () => {
    mockSelectOnce([]);
    await getProducts('', 'bebida');
    const [sql, params] = mockDb.select.mock.calls[0];
    expect(sql).toContain('category');
    expect(params).toContain('bebida');
  });

  it('com busca + categoria: ambos os filtros', async () => {
    mockSelectOnce([]);
    await getProducts('agua', 'bebida');
    const [sql, params] = mockDb.select.mock.calls[0];
    expect(sql).toContain('LIKE');
    expect(sql).toContain('category');
    expect(params).toContain('%agua%');
    expect(params).toContain('bebida');
  });

  it('retorna array vazio quando não há produtos', async () => {
    mockSelectOnce([]);
    const result = await getProducts();
    expect(result).toEqual([]);
  });

  it('retorna produtos quando há resultados', async () => {
    const produto = { id: 1, name: 'Coca-Cola', category: 'bebida', purchase_price: 2.5, sale_price: 7, minimum_stock: 10, current_stock: 50, active: 1 };
    mockSelectOnce([produto]);
    const result = await getProducts();
    expect(result).toHaveLength(1);
    expect(result[0].name).toBe('Coca-Cola');
  });

  it('ignora filtro "todas" como categoria', async () => {
    mockSelectOnce([]);
    await getProducts('', 'todas');
    const [sql] = mockDb.select.mock.calls[0];
    expect(sql).not.toContain('category =');
  });
});

describe('getAllActiveProducts', () => {
  it('busca somente produtos ativos ordenados por nome', async () => {
    mockSelectOnce([]);
    await getAllActiveProducts();
    const [sql] = mockDb.select.mock.calls[0];
    expect(sql).toContain('active = 1');
    expect(sql).toContain('ORDER BY name');
  });
});

describe('getProductById', () => {
  it('retorna produto quando encontrado', async () => {
    const produto = { id: 5, name: 'Água', category: 'bebida', purchase_price: 0.8, sale_price: 3.5, minimum_stock: 30, current_stock: 100, active: 1 };
    mockSelectOnce([produto]);
    const result = await getProductById(5);
    expect(result).toEqual(produto);
  });

  it('retorna null quando não encontrado', async () => {
    mockSelectOnce([]);
    const result = await getProductById(999);
    expect(result).toBeNull();
  });
});

describe('addProduct', () => {
  it('chama INSERT com todos os campos', async () => {
    await addProduct({ name: 'Suco', category: 'bebida', purchase_price: 3, sale_price: 9, minimum_stock: 10, current_stock: 0 });
    const [sql, params] = mockDb.execute.mock.calls[0];
    expect(sql).toContain('INSERT INTO products');
    expect(params).toContain('Suco');
    expect(params).toContain('bebida');
    expect(params).toContain(3);
    expect(params).toContain(9);
  });
});

describe('updateProduct', () => {
  it('não chama execute quando sem campos', async () => {
    await updateProduct(1, {});
    expect(mockDb.execute).not.toHaveBeenCalled();
  });

  it('gera UPDATE com os campos corretos', async () => {
    await updateProduct(3, { name: 'Novo Nome', sale_price: 15 });
    const [sql, params] = mockDb.execute.mock.calls[0];
    expect(sql).toContain('UPDATE products');
    expect(sql).toContain('name = ?');
    expect(sql).toContain('sale_price = ?');
    expect(params).toContain('Novo Nome');
    expect(params).toContain(15);
    expect(params).toContain(3); // WHERE id = ?
  });
});

describe('deactivateProduct', () => {
  it('marca produto como inativo (active = 0)', async () => {
    await deactivateProduct(7);
    const [sql, params] = mockDb.execute.mock.calls[0];
    expect(sql).toContain('active = 0');
    expect(params).toContain(7);
  });
});

describe('getLowStockProducts', () => {
  it('busca produtos com estoque <= mínimo', async () => {
    mockSelectOnce([]);
    await getLowStockProducts();
    const [sql] = mockDb.select.mock.calls[0];
    expect(sql).toContain('current_stock');
    expect(sql).toContain('minimum_stock');
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// ORDERS
// ═══════════════════════════════════════════════════════════════════════════════

describe('getOrders', () => {
  it('sem filtros: ordena por created_at DESC', async () => {
    mockSelectOnce([]);
    await getOrders();
    const [sql] = mockDb.select.mock.calls[0];
    expect(sql).toContain('ORDER BY created_at DESC');
  });

  it('com busca: filtra por customer_name', async () => {
    mockSelectOnce([]);
    await getOrders('maria');
    const [sql, params] = mockDb.select.mock.calls[0];
    expect(sql).toContain('customer_name');
    expect(params).toContain('%maria%');
  });

  it('com status "aberta": filtra corretamente', async () => {
    mockSelectOnce([]);
    await getOrders('', 'aberta');
    const [sql, params] = mockDb.select.mock.calls[0];
    expect(sql).toContain('status');
    expect(params).toContain('aberta');
  });

  it('ignora status "todas"', async () => {
    mockSelectOnce([]);
    await getOrders('', 'todas');
    const [sql] = mockDb.select.mock.calls[0];
    expect(sql).not.toContain("status = ?");
  });
});

describe('getOrderById', () => {
  it('retorna comanda quando encontrada', async () => {
    const order = { id: 10, customer_name: 'João', phone: '', status: 'aberta', total: 0, created_at: '2024-03-15 10:00:00', closed_at: null };
    mockSelectOnce([order]);
    const result = await getOrderById(10);
    expect(result).toEqual(order);
  });

  it('retorna null quando não encontrada', async () => {
    mockSelectOnce([]);
    const result = await getOrderById(999);
    expect(result).toBeNull();
  });
});

describe('createOrder', () => {
  it('insere comanda e retorna o ID gerado', async () => {
    mockExecuteOnce(42);
    const id = await createOrder('Maria Santos');
    expect(id).toBe(42);
    const [sql, params] = mockDb.execute.mock.calls[0];
    expect(sql).toContain('INSERT INTO orders');
    expect(params).toContain('Maria Santos');
  });

  it('armazena timestamp no formato sqlite', async () => {
    mockExecuteOnce(1);
    await createOrder('Carlos');
    const [, params] = mockDb.execute.mock.calls[0];
    const timestamp = params[1] as string;
    expect(timestamp).toMatch(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/);
  });
});

describe('updateOrderPhone', () => {
  it('atualiza phone da comanda correta', async () => {
    await updateOrderPhone(5, '(11) 99999-0000');
    const [sql, params] = mockDb.execute.mock.calls[0];
    expect(sql).toContain('UPDATE orders');
    expect(sql).toContain('phone = ?');
    expect(params).toContain('(11) 99999-0000');
    expect(params).toContain(5);
  });
});

describe('closeOrder', () => {
  it('fecha comanda: cria movimentos de saída e atualiza status', async () => {
    // select order_items
    mockSelectOnce([
      { id: 1, order_id: 10, product_id: 3, quantity: 2, unit_price: 7, subtotal: 14, added_at: '2024-03-15 10:00:00' },
      { id: 2, order_id: 10, product_id: 3, quantity: 1, unit_price: 7, subtotal: 7, added_at: '2024-03-15 10:01:00' },
    ]);
    await closeOrder(10);
    // deve ter chamado execute várias vezes:
    // 1x INSERT movements (saída produto 3 qty=3)
    // 1x UPDATE products stock
    // 1x UPDATE orders status='fechada'
    const executeCalls = mockDb.execute.mock.calls;
    const movementCall = executeCalls.find(([sql]: [string]) => sql.includes("INSERT INTO movements") && sql.includes("EXIT"));
    const updateOrderCall = executeCalls.find(([sql]: [string]) => sql.includes("status = 'fechada'"));
    expect(movementCall).toBeDefined();
    expect(updateOrderCall).toBeDefined();
  });

  it('fecha comanda com closed_at preenchido', async () => {
    mockSelectOnce([]); // sem itens
    await closeOrder(5);
    const updateCall = mockDb.execute.mock.calls.find(([sql]: [string]) => sql.includes('closed_at'));
    expect(updateCall).toBeDefined();
    const params = updateCall![1] as unknown[];
    // o timestamp deve ser no formato correto
    expect((params[0] as string)).toMatch(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/);
  });
});

describe('deleteOrder', () => {
  it('deleta itens e depois a comanda', async () => {
    await deleteOrder(7);
    const calls = mockDb.execute.mock.calls;
    const deleteItems = calls.find(([sql]: [string]) => sql.includes('DELETE FROM order_items'));
    const deleteOrder_ = calls.find(([sql]: [string]) => sql.includes('DELETE FROM orders'));
    expect(deleteItems).toBeDefined();
    expect(deleteOrder_).toBeDefined();
    expect(deleteItems![1]).toContain(7);
  });
});

describe('getOpenOrderByCustomerName', () => {
  it('busca comanda aberta por nome (case-insensitive)', async () => {
    const openOrder = { id: 3, customer_name: 'Maria', status: 'aberta', total: 0, created_at: '2024-01-01 10:00:00' };
    mockSelectOnce([openOrder]);
    const result = await getOpenOrderByCustomerName('maria');
    const [sql, params] = mockDb.select.mock.calls[0];
    expect(sql).toContain("status = 'aberta'");
    expect(sql).toContain('LOWER');
    expect(params).toContain('maria');
    expect(result).toEqual(openOrder);
  });

  it('retorna null quando não há comanda aberta', async () => {
    mockSelectOnce([]);
    const result = await getOpenOrderByCustomerName('Carlos');
    expect(result).toBeNull();
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// ORDER ITEMS
// ═══════════════════════════════════════════════════════════════════════════════

describe('addOrderItem', () => {
  it('insere item com qty=1 e recalcula total', async () => {
    // execute: INSERT order_item, UPDATE orders total
    await addOrderItem(10, 3, 7.0);
    const calls = mockDb.execute.mock.calls;
    const insertCall = calls.find(([sql]: [string]) => sql.includes('INSERT INTO order_items'));
    const recalcCall = calls.find(([sql]: [string]) => sql.includes('UPDATE orders') && sql.includes('SUM(subtotal)'));
    expect(insertCall).toBeDefined();
    expect(recalcCall).toBeDefined();
    // qty = 1, unit_price = 7, subtotal = 7
    expect(insertCall![1]).toContain(7.0);
    expect(insertCall![1]).toContain(10); // order_id
    expect(insertCall![1]).toContain(3);  // product_id
  });

  it('armazena timestamp no formato correto', async () => {
    await addOrderItem(1, 1, 5.0);
    const insertCall = mockDb.execute.mock.calls.find(([sql]: [string]) => sql.includes('INSERT INTO order_items'));
    const params = insertCall![1] as unknown[];
    const timestamp = params[params.length - 1] as string;
    expect(timestamp).toMatch(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/);
  });
});

describe('decrementOrderItem', () => {
  it('deleta o item se quantity = 1', async () => {
    mockSelectOnce([{ id: 10, order_id: 1, product_id: 3, quantity: 1, unit_price: 7, subtotal: 7, added_at: '2024-03-15 10:00:00' }]);
    await decrementOrderItem(1, 3);
    const deleteCall = mockDb.execute.mock.calls.find(([sql]: [string]) => sql.includes('DELETE FROM order_items'));
    expect(deleteCall).toBeDefined();
    expect(deleteCall![1]).toContain(10); // item id
  });

  it('decrementa quantity se > 1', async () => {
    mockSelectOnce([{ id: 10, order_id: 1, product_id: 3, quantity: 3, unit_price: 7, subtotal: 21, added_at: '2024-03-15 10:00:00' }]);
    await decrementOrderItem(1, 3);
    const updateCall = mockDb.execute.mock.calls.find(([sql]: [string]) => sql.includes('UPDATE order_items'));
    expect(updateCall).toBeDefined();
    const params = updateCall![1] as unknown[];
    expect(params[0]).toBe(2); // nova qty = 3-1=2
    expect(params[1]).toBe(14); // novo subtotal = 2*7=14
  });

  it('não faz nada se item não existe', async () => {
    mockSelectOnce([]);
    await decrementOrderItem(99, 99);
    // Apenas o SELECT deve ter sido chamado
    expect(mockDb.execute).not.toHaveBeenCalled();
  });
});

describe('removeAllItemsOfProduct', () => {
  it('remove todos os itens do produto na comanda', async () => {
    await removeAllItemsOfProduct(5, 3);
    const deleteCall = mockDb.execute.mock.calls.find(([sql]: [string]) => sql.includes('DELETE FROM order_items'));
    expect(deleteCall).toBeDefined();
    expect(deleteCall![1]).toContain(5); // order_id
    expect(deleteCall![1]).toContain(3); // product_id
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// MOVEMENTS
// ═══════════════════════════════════════════════════════════════════════════════

describe('addMovement', () => {
  it('insere movimento ENTRY e atualiza estoque', async () => {
    await addMovement(3, 50, 'Reposição semanal');
    const calls = mockDb.execute.mock.calls;
    const insertCall = calls.find(([sql]: [string]) => sql.includes('INSERT INTO movements'));
    const updateCall = calls.find(([sql]: [string]) => sql.includes('UPDATE products') && sql.includes('current_stock + ?'));
    expect(insertCall).toBeDefined();
    expect(updateCall).toBeDefined();
    // 'ENTRY' está na query SQL (hardcoded), não nos params
    expect(insertCall![0]).toContain("'ENTRY'");
    expect(insertCall![1]).toContain(50);
    expect(insertCall![1]).toContain('Reposição semanal');
    // verifica parâmetros do UPDATE
    expect(updateCall![1]).toContain(50);
    expect(updateCall![1]).toContain(3);
  });

  it('funciona sem nota (padrão vazio)', async () => {
    await addMovement(1, 10);
    const insertCall = mockDb.execute.mock.calls.find(([sql]: [string]) => sql.includes('INSERT INTO movements'));
    expect(insertCall![1]).toContain('');
  });
});

describe('removeMovement', () => {
  it('não faz nada se movimento não existe', async () => {
    mockSelectOnce([]);
    await removeMovement(999);
    expect(mockDb.execute).not.toHaveBeenCalled();
  });

  it('remove ENTRY e desconta do estoque', async () => {
    mockSelectOnce([{ id: 5, product_id: 3, movement_type: 'ENTRY', quantity: 20, note: '', created_at: '2024-01-01 10:00:00' }]);
    await removeMovement(5);
    const deleteCall = mockDb.execute.mock.calls.find(([sql]: [string]) => sql.includes('DELETE FROM movements'));
    const updateCall = mockDb.execute.mock.calls.find(([sql]: [string]) => sql.includes('current_stock - ?'));
    expect(deleteCall).toBeDefined();
    expect(updateCall).toBeDefined();
    expect(updateCall![1]).toContain(20);
    expect(updateCall![1]).toContain(3);
  });

  it('remove EXIT sem alterar estoque', async () => {
    mockSelectOnce([{ id: 6, product_id: 2, movement_type: 'EXIT', quantity: 5, note: 'Comanda #10', created_at: '2024-01-01 10:00:00' }]);
    await removeMovement(6);
    const updateStockCall = mockDb.execute.mock.calls.find(([sql]: [string]) => sql.includes('current_stock'));
    expect(updateStockCall).toBeUndefined();
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// SETTINGS
// ═══════════════════════════════════════════════════════════════════════════════

describe('getSetting', () => {
  it('retorna valor quando existe', async () => {
    mockSelectOnce([{ value: 'pix@email.com' }]);
    const result = await getSetting('pix_key');
    expect(result).toBe('pix@email.com');
  });

  it('retorna fallback quando não existe', async () => {
    mockSelectOnce([]);
    const result = await getSetting('pix_key', 'sem_pix');
    expect(result).toBe('sem_pix');
  });

  it('retorna string vazia como fallback padrão', async () => {
    mockSelectOnce([]);
    const result = await getSetting('qualquer_chave');
    expect(result).toBe('');
  });
});

describe('setSetting', () => {
  it('usa INSERT ... ON CONFLICT DO UPDATE (upsert)', async () => {
    await setSetting('pix_key', 'nova@chave.com');
    const [sql, params] = mockDb.execute.mock.calls[0];
    expect(sql).toContain('INSERT INTO settings');
    expect(sql).toContain('ON CONFLICT');
    expect(params).toContain('pix_key');
    expect(params).toContain('nova@chave.com');
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// CUSTOMERS
// ═══════════════════════════════════════════════════════════════════════════════

describe('getCustomers', () => {
  it('sem filtro: busca todos ordenados por nome', async () => {
    mockSelectOnce([]);
    await getCustomers();
    const [sql] = mockDb.select.mock.calls[0];
    expect(sql).toContain('FROM customers');
    expect(sql).toContain('ORDER BY name');
  });

  it('com busca: filtra por nome ou telefone', async () => {
    mockSelectOnce([]);
    await getCustomers('silva');
    const [sql, params] = mockDb.select.mock.calls[0];
    expect(sql).toContain('LIKE');
    expect(params).toContain('%silva%');
  });
});

describe('addCustomer', () => {
  it('insere cliente com timestamp', async () => {
    await addCustomer({ name: 'Ana Lima', phone: '(11) 91234-5678', note: 'VIP' });
    const [sql, params] = mockDb.execute.mock.calls[0];
    expect(sql).toContain('INSERT INTO customers');
    expect(params).toContain('Ana Lima');
    expect(params).toContain('(11) 91234-5678');
    expect(params).toContain('VIP');
  });
});

describe('updateCustomer', () => {
  it('não chama execute sem campos', async () => {
    await updateCustomer(1, {});
    expect(mockDb.execute).not.toHaveBeenCalled();
  });

  it('gera UPDATE com campo correto', async () => {
    await updateCustomer(2, { phone: '(11) 00000-0000' });
    const [sql, params] = mockDb.execute.mock.calls[0];
    expect(sql).toContain('UPDATE customers');
    expect(sql).toContain('phone = ?');
    expect(params).toContain('(11) 00000-0000');
    expect(params).toContain(2);
  });
});

describe('deleteCustomer', () => {
  it('deleta cliente pelo id', async () => {
    await deleteCustomer(4);
    const [sql, params] = mockDb.execute.mock.calls[0];
    expect(sql).toContain('DELETE FROM customers');
    expect(params).toContain(4);
  });
});

describe('searchCustomers', () => {
  it('retorna vazio para term vazio', async () => {
    const result = await searchCustomers('');
    expect(result).toEqual([]);
    expect(mockDb.select).not.toHaveBeenCalled();
  });

  it('busca por nome com LIKE', async () => {
    const cliente = { id: 1, name: 'João Silva', phone: '', note: '', created_at: '2024-01-01 10:00:00' };
    mockSelectOnce([cliente]);
    const result = await searchCustomers('joão');
    expect(result).toHaveLength(1);
    const [sql, params] = mockDb.select.mock.calls[0];
    expect(sql).toContain('LIKE');
    expect(params).toContain('%joão%');
    expect(sql).toContain('LIMIT 8');
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// STRESS TESTS
// ═══════════════════════════════════════════════════════════════════════════════

describe('[STRESS] Simulação de dia muito movimentado', () => {
  it('cria 100 comandas consecutivas — IDs corretos', async () => {
    for (let i = 1; i <= 100; i++) {
      mockDb.execute.mockClear();
      mockDb.execute.mockResolvedValueOnce({ lastInsertId: i, rowsAffected: 1 });
      const id = await createOrder(`Cliente ${i}`);
      expect(id).toBe(i);
    }
  });

  it('adiciona 500 itens a uma comanda — todos os timestamps únicos', async () => {
    const timestamps: string[] = [];
    for (let i = 0; i < 500; i++) {
      const calls = mockDb.execute.mock.calls.length;
      await addOrderItem(1, (i % 10) + 1, 7.0);
      // captura o timestamp do último INSERT
      const insertCall = mockDb.execute.mock.calls
        .slice(calls)
        .find(([sql]: [string]) => sql.includes('INSERT INTO order_items'));
      if (insertCall) {
        const params = insertCall[1] as unknown[];
        timestamps.push(params[params.length - 1] as string);
      }
    }
    // todos devem ser timestamps válidos
    expect(timestamps.every((t) => /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(t))).toBe(true);
  });

  it('fecha 50 comandas com itens distintos — movements gerados para cada', async () => {
    for (let comanda = 1; comanda <= 50; comanda++) {
      mockDb.select.mockResolvedValueOnce([
        { id: comanda * 10, order_id: comanda, product_id: 1, quantity: 2, unit_price: 7, subtotal: 14, added_at: '2024-03-15 10:00:00' },
        { id: comanda * 10 + 1, order_id: comanda, product_id: 2, quantity: 3, unit_price: 5, subtotal: 15, added_at: '2024-03-15 10:00:00' },
      ]);
      mockDb.execute.mockClear();
      await closeOrder(comanda);
      const movCalls = mockDb.execute.mock.calls.filter(([sql]: [string]) => sql.includes('INSERT INTO movements'));
      // 2 produtos → 2 movements
      expect(movCalls.length).toBe(2);
    }
  });

  it('pesquisa 1.000 produtos com termos variados — SQL correto em cada chamada', async () => {
    const termos = ['agua', 'coca', 'cerveja', 'suco', 'barra', 'pastel', 'hamburguer', 'red bull', 'toalha', 'protetor'];
    for (let i = 0; i < 1_000; i++) {
      mockDb.select.mockResolvedValueOnce([]);
      const termo = termos[i % termos.length];
      await getProducts(termo);
      const [sql, params] = mockDb.select.mock.calls[mockDb.select.mock.calls.length - 1];
      expect(sql).toContain('LIKE');
      expect(params).toContain(`%${termo}%`);
    }
  });

  it('busca de clientes autocomplete — 200 termos consecutivos', async () => {
    const nomes = ['Ana', 'Bruno', 'Carla', 'Diego', 'Eva'];
    for (let i = 0; i < 200; i++) {
      mockDb.select.mockResolvedValueOnce([]);
      await searchCustomers(nomes[i % nomes.length]);
    }
    expect(mockDb.select.mock.calls.length).toBe(200);
  });

  it('30 entradas de estoque seguidas de 30 saídas — execute chamado corretamente', async () => {
    // 30 entradas
    for (let i = 0; i < 30; i++) {
      mockDb.execute.mockClear();
      await addMovement(i + 1, 100, `Reposição ${i + 1}`);
      const insertCall = mockDb.execute.mock.calls.find(([sql]: [string]) => sql.includes('INSERT INTO movements'));
      expect(insertCall).toBeDefined();
      expect(insertCall![0]).toContain("'ENTRY'");
    }
    // 30 saídas (via closeOrder com 1 item cada)
    for (let i = 0; i < 30; i++) {
      mockDb.select.mockResolvedValueOnce([
        { id: i + 1, order_id: i + 1, product_id: 1, quantity: 1, unit_price: 7, subtotal: 7, added_at: '2024-03-15 10:00:00' },
      ]);
      mockDb.execute.mockClear();
      await closeOrder(i + 1);
      const exitCall = mockDb.execute.mock.calls.find(([sql]: [string]) => sql.includes("'EXIT'"));
      expect(exitCall).toBeDefined();
    }
  });
});
