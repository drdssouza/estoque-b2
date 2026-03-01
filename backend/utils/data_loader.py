import sys
import pandas as pd
import os
from pathlib import Path
from datetime import datetime
import threading


class DataLoader:
    def __init__(self, data_dir=None):
        if data_dir is None:
            if getattr(sys, 'frozen', False):
                # Rodando como .exe gerado pelo PyInstaller
                base = Path(sys.executable).parent
            else:
                base = Path.cwd()
            data_dir = base / "data"
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.products_file = self.data_dir / "products.parquet"
        self.movements_file = self.data_dir / "movements.parquet"
        self.orders_file = self.data_dir / "orders.parquet"
        self.order_items_file = self.data_dir / "order_items.parquet"
        self.lock = threading.RLock()  # Reentrant: permite que o mesmo thread re-adquira o lock

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
            'phone': pd.Series([], dtype='str'),
            'created_at': pd.Series([], dtype='datetime64[ns]'),
            'status': pd.Series([], dtype='str'),
            'total': pd.Series([], dtype='float64')
        })

    def _create_default_order_items(self):
        return pd.DataFrame({
            'id': pd.Series([], dtype='int64'),
            'order_id': pd.Series([], dtype='int64'),
            'product_id': pd.Series([], dtype='int64'),
            'quantity': pd.Series([], dtype='int64'),
            'unit_price': pd.Series([], dtype='float64'),
            'subtotal': pd.Series([], dtype='float64'),
            'added_at': pd.Series([], dtype='datetime64[ns]')
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

    def _migrate(self, df, migrations):
        """Aplica migrações de colunas ausentes. migrations = {coluna: valor_default}"""
        changed = False
        for col, default in migrations.items():
            if col not in df.columns:
                df[col] = default
                changed = True
        return df, changed

    def load_products(self):
        df = self._safe_load(self.products_file, self._create_default_products)
        df, changed = self._migrate(df, {
            'id':             0,
            'name':           '',
            'category':       '',
            'purchase_price': 0.0,
            'sale_price':     0.0,
            'minimum_stock':  0,
            'current_stock':  0,
            'active':         True,
        })
        if changed:
            self.save_products(df)
        return df

    def load_movements(self):
        df = self._safe_load(self.movements_file, self._create_default_movements)
        df, changed = self._migrate(df, {
            'id':            0,
            'product_id':    0,
            'movement_type': '',
            'quantity':      0,
            'created_at':    pd.NaT,
            'note':          '',
        })
        if changed:
            self.save_movements(df)
        return df

    def load_orders(self):
        df = self._safe_load(self.orders_file, self._create_default_orders)
        df, changed = self._migrate(df, {
            'id':            0,
            'customer_name': '',
            'phone':         '',
            'created_at':    pd.NaT,
            'status':        '',
            'total':         0.0,
        })
        if changed:
            self.save_orders(df)
        return df

    def load_order_items(self):
        df = self._safe_load(self.order_items_file, self._create_default_order_items)
        df, changed = self._migrate(df, {
            'id':         0,
            'order_id':   0,
            'product_id': 0,
            'quantity':   0,
            'unit_price': 0.0,
            'subtotal':   0.0,
            'added_at':   pd.NaT,
        })
        if changed:
            self.save_order_items(df)
        return df

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
        with self.lock:
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
        with self.lock:
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
        """
        Retorna tupla (new_id, error):
          - Sucesso:  (new_id, None)
          - Erro:     (None,   mensagem)
        """
        with self.lock:
            movements_df = self.load_movements()
            products_df = self.load_products()

            mask = products_df['id'] == product_id
            if not mask.any():
                return None, "Produto não encontrado."

            current_stock = int(products_df.loc[mask, 'current_stock'].iloc[0])

            if movement_type == "EXIT" and quantity > current_stock:
                return None, f"Estoque insuficiente. Disponível: {current_stock} unidades."

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

            if movement_type == "ENTRY":
                products_df.loc[mask, 'current_stock'] += quantity
            elif movement_type == "EXIT":
                products_df.loc[mask, 'current_stock'] -= quantity

            self.save_products(products_df)
            return new_id, None

    # ─── ORDERS ──────────────────────────────────────────────────────

    def add_order(self, customer_name):
        with self.lock:
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

    def update_order_phone(self, order_id, phone):
        with self.lock:
            df = self.load_orders()
            mask = df['id'] == order_id
            df.loc[mask, 'phone'] = phone
            self.save_orders(df)

    def add_order_item(self, order_id, product_id, quantity, unit_price):
        with self.lock:
            items_df = self.load_order_items()
            new_id = int(items_df['id'].max()) + 1 if len(items_df) > 0 else 1
            subtotal = quantity * unit_price
            new_item = pd.DataFrame({
                'id': [new_id],
                'order_id': [order_id],
                'product_id': [product_id],
                'quantity': [quantity],
                'unit_price': [unit_price],
                'subtotal': [subtotal],
                'added_at': [datetime.now()]
            })
            items_df = pd.concat([items_df, new_item], ignore_index=True)
            self.save_order_items(items_df)
            self._recalculate_order_total(order_id)
            return new_id

    def remove_order_item(self, item_id):
        with self.lock:
            items_df = self.load_order_items()
            row = items_df[items_df['id'] == item_id]
            if len(row) == 0:
                return False
            order_id = int(row.iloc[0]['order_id'])
            items_df = items_df[items_df['id'] != item_id]
            self.save_order_items(items_df)
            self._recalculate_order_total(order_id)
            return True

    def update_order_item_quantity(self, item_id, new_quantity):
        """
        Atualiza a quantidade de um item da comanda.
        Se new_quantity <= 0, remove o item.
        """
        with self.lock:
            items_df = self.load_order_items()
            mask = items_df['id'] == item_id
            if not mask.any():
                return False

            order_id = int(items_df.loc[mask, 'order_id'].iloc[0])

            if new_quantity <= 0:
                items_df = items_df[~mask]
                self.save_order_items(items_df)
            else:
                unit_price = float(items_df.loc[mask, 'unit_price'].iloc[0])
                items_df.loc[mask, 'quantity'] = new_quantity
                items_df.loc[mask, 'subtotal'] = new_quantity * unit_price
                self.save_order_items(items_df)

            self._recalculate_order_total(order_id)
            return True

    def close_order(self, order_id):
        with self.lock:
            orders_df = self.load_orders()
            mask = orders_df['id'] == order_id
            orders_df.loc[mask, 'status'] = 'fechada'
            self.save_orders(orders_df)

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
        with self.lock:
            items_df = self.load_order_items()
            items_df = items_df[items_df['order_id'] != order_id]
            self.save_order_items(items_df)

            orders_df = self.load_orders()
            orders_df = orders_df[orders_df['id'] != order_id]
            self.save_orders(orders_df)

    def _recalculate_order_total(self, order_id):
        with self.lock:
            items_df = self.load_order_items()
            order_items = items_df[items_df['order_id'] == order_id]
            total = float(order_items['subtotal'].sum()) if len(order_items) > 0 else 0.0
            orders_df = self.load_orders()
            mask = orders_df['id'] == order_id
            orders_df.loc[mask, 'total'] = total
            self.save_orders(orders_df)