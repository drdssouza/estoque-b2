import pandas as pd
import os
from pathlib import Path
from datetime import datetime
import threading


class DataLoader:
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.products_file = self.data_dir / "products.parquet"
        self.movements_file = self.data_dir / "movements.parquet"
        self.orders_file = self.data_dir / "orders.parquet"
        self.order_items_file = self.data_dir / "order_items.parquet"
        self.lock = threading.Lock()

    # ─── DEFAULTS ────────────────────────────────────────────────────

    def _create_default_products(self):
        return pd.DataFrame({
            'id': [1, 2, 3, 4],
            'name': ['Água Mineral 500ml', 'Refrigerante Coca-Cola 350ml', 'Chips Ruffles 100g', 'Raquete de Beach Tennis'],
            'category': ['bebida', 'bebida', 'chips', 'acessorios'],
            'purchase_price': [1.50, 2.50, 4.00, 80.00],
            'sale_price': [3.00, 5.00, 8.00, 150.00],
            'minimum_stock': [20, 15, 10, 5],
            'current_stock': [50, 30, 25, 10],
            'active': [True, True, True, True]
        })

    def _create_default_movements(self):
        return pd.DataFrame({
            'id': pd.Series([], dtype='int64'),
            'product_id': pd.Series([], dtype='int64'),
            'movement_type': pd.Series([], dtype='str'),
            'quantity': pd.Series([], dtype='int64'),
            'created_at': pd.Series([], dtype='datetime64[ns]'),
            'note': pd.Series([], dtype='str')
        })

    def _create_default_orders(self):
        return pd.DataFrame({
            'id': pd.Series([], dtype='int64'),
            'customer_name': pd.Series([], dtype='str'),
            'created_at': pd.Series([], dtype='datetime64[ns]'),
            'status': pd.Series([], dtype='str'),   # "aberta" ou "fechada"
            'total': pd.Series([], dtype='float64')
        })

    def _create_default_order_items(self):
        return pd.DataFrame({
            'id': pd.Series([], dtype='int64'),
            'order_id': pd.Series([], dtype='int64'),
            'product_id': pd.Series([], dtype='int64'),
            'quantity': pd.Series([], dtype='int64'),
            'unit_price': pd.Series([], dtype='float64'),
            'subtotal': pd.Series([], dtype='float64')
        })

    # ─── LOAD ────────────────────────────────────────────────────────

    def _safe_load(self, filepath, default_fn):
        with self.lock:
            if not filepath.exists() or filepath.stat().st_size == 0:
                df = default_fn()
                df.to_parquet(filepath, index=False)
                return df
            try:
                return pd.read_parquet(filepath)
            except Exception:
                df = default_fn()
                df.to_parquet(filepath, index=False)
                return df

    def load_products(self):
        return self._safe_load(self.products_file, self._create_default_products)

    def load_movements(self):
        return self._safe_load(self.movements_file, self._create_default_movements)

    def load_orders(self):
        return self._safe_load(self.orders_file, self._create_default_orders)

    def load_order_items(self):
        return self._safe_load(self.order_items_file, self._create_default_order_items)

    # ─── SAVE ────────────────────────────────────────────────────────

    def save_products(self, df):
        with self.lock:
            df.to_parquet(self.products_file, index=False)

    def save_movements(self, df):
        with self.lock:
            df.to_parquet(self.movements_file, index=False)

    def save_orders(self, df):
        with self.lock:
            df.to_parquet(self.orders_file, index=False)

    def save_order_items(self, df):
        with self.lock:
            df.to_parquet(self.order_items_file, index=False)

    # ─── PRODUCTS ────────────────────────────────────────────────────

    def add_product(self, name, category, purchase_price, sale_price, minimum_stock, current_stock):
        df = self.load_products()
        new_id = int(df['id'].max()) + 1 if len(df) > 0 else 1
        new_row = pd.DataFrame({
            'id': [new_id],
            'name': [name],
            'category': [category],
            'purchase_price': [purchase_price],
            'sale_price': [sale_price],
            'minimum_stock': [minimum_stock],
            'current_stock': [current_stock],
            'active': [True]
        })
        df = pd.concat([df, new_row], ignore_index=True)
        self.save_products(df)
        return new_id

    def update_product(self, product_id, **kwargs):
        df = self.load_products()
        mask = df['id'] == product_id
        for key, value in kwargs.items():
            if key in df.columns:
                df.loc[mask, key] = value
        self.save_products(df)

    def deactivate_product(self, product_id):
        self.update_product(product_id, active=False)

    def get_low_stock_products(self):
        df = self.load_products()
        active = df[df['active'] == True]
        return active[active['current_stock'] <= active['minimum_stock']]

    def search_products(self, query="", category=None):
        df = self.load_products()
        if query:
            df = df[df['name'].str.contains(query, case=False, na=False)]
        if category:
            df = df[df['category'] == category]
        return df

    # ─── MOVEMENTS ───────────────────────────────────────────────────

    def add_movement(self, product_id, movement_type, quantity, note=""):
        movements_df = self.load_movements()
        products_df = self.load_products()

        new_id = int(movements_df['id'].max()) + 1 if len(movements_df) > 0 else 1

        new_movement = pd.DataFrame({
            'id': [new_id],
            'product_id': [product_id],
            'movement_type': [movement_type],
            'quantity': [quantity],
            'created_at': [datetime.now()],
            'note': [note]
        })

        movements_df = pd.concat([movements_df, new_movement], ignore_index=True)
        self.save_movements(movements_df)

        mask = products_df['id'] == product_id
        if movement_type == "ENTRY":
            products_df.loc[mask, 'current_stock'] += quantity
        elif movement_type == "EXIT":
            products_df.loc[mask, 'current_stock'] -= quantity

        self.save_products(products_df)
        return new_id

    # ─── ORDERS ──────────────────────────────────────────────────────

    def add_order(self, customer_name):
        orders_df = self.load_orders()
        new_id = int(orders_df['id'].max()) + 1 if len(orders_df) > 0 else 1
        new_order = pd.DataFrame({
            'id': [new_id],
            'customer_name': [customer_name],
            'created_at': [datetime.now()],
            'status': ['aberta'],
            'total': [0.0]
        })
        orders_df = pd.concat([orders_df, new_order], ignore_index=True)
        self.save_orders(orders_df)
        return new_id

    def add_order_item(self, order_id, product_id, quantity, unit_price):
        items_df = self.load_order_items()
        new_id = int(items_df['id'].max()) + 1 if len(items_df) > 0 else 1
        subtotal = quantity * unit_price
        new_item = pd.DataFrame({
            'id': [new_id],
            'order_id': [order_id],
            'product_id': [product_id],
            'quantity': [quantity],
            'unit_price': [unit_price],
            'subtotal': [subtotal]
        })
        items_df = pd.concat([items_df, new_item], ignore_index=True)
        self.save_order_items(items_df)

        # Atualizar total da comanda
        self._recalculate_order_total(order_id)
        return new_id

    def remove_order_item(self, item_id):
        items_df = self.load_order_items()
        row = items_df[items_df['id'] == item_id]
        if len(row) == 0:
            return False
        order_id = int(row.iloc[0]['order_id'])
        items_df = items_df[items_df['id'] != item_id]
        self.save_order_items(items_df)
        self._recalculate_order_total(order_id)
        return True

    def close_order(self, order_id):
        orders_df = self.load_orders()
        mask = orders_df['id'] == order_id
        orders_df.loc[mask, 'status'] = 'fechada'
        self.save_orders(orders_df)

        # Registrar saídas de estoque para cada item da comanda
        items_df = self.load_order_items()
        order_items = items_df[items_df['order_id'] == order_id]
        for _, item in order_items.iterrows():
            self.add_movement(
                product_id=int(item['product_id']),
                movement_type="EXIT",
                quantity=int(item['quantity']),
                note=f"Comanda #{order_id}"
            )

    def delete_order(self, order_id):
        # Remover itens
        items_df = self.load_order_items()
        items_df = items_df[items_df['order_id'] != order_id]
        self.save_order_items(items_df)
        # Remover comanda
        orders_df = self.load_orders()
        orders_df = orders_df[orders_df['id'] != order_id]
        self.save_orders(orders_df)

    def _recalculate_order_total(self, order_id):
        items_df = self.load_order_items()
        order_items = items_df[items_df['order_id'] == order_id]
        total = float(order_items['subtotal'].sum()) if len(order_items) > 0 else 0.0
        orders_df = self.load_orders()
        mask = orders_df['id'] == order_id
        orders_df.loc[mask, 'total'] = total
        self.save_orders(orders_df)