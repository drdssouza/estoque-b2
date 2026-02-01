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
        self.lock = threading.Lock()
        
    def _create_default_products(self):
        return pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Água Mineral 500ml', 'Refrigerante Coca-Cola 350ml', 'Chips Ruffles 100g'],
            'category': ['bebida', 'bebida', 'chips'],
            'purchase_price': [1.50, 2.50, 4.00],
            'sale_price': [3.00, 5.00, 8.00],
            'minimum_stock': [20, 15, 10],
            'current_stock': [50, 30, 25],
            'active': [True, True, True]
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
    
    def load_products(self):
        with self.lock:
            if not self.products_file.exists() or self.products_file.stat().st_size == 0:
                df = self._create_default_products()
                df.to_parquet(self.products_file, index=False)
                return df
            try:
                return pd.read_parquet(self.products_file)
            except:
                df = self._create_default_products()
                df.to_parquet(self.products_file, index=False)
                return df
    
    def load_movements(self):
        with self.lock:
            if not self.movements_file.exists() or self.movements_file.stat().st_size == 0:
                df = self._create_default_movements()
                df.to_parquet(self.movements_file, index=False)
                return df
            try:
                return pd.read_parquet(self.movements_file)
            except:
                df = self._create_default_movements()
                df.to_parquet(self.movements_file, index=False)
                return df
    
    def save_products(self, df):
        with self.lock:
            df.to_parquet(self.products_file, index=False)
    
    def save_movements(self, df):
        with self.lock:
            df.to_parquet(self.movements_file, index=False)
    
    def add_product(self, name, category, purchase_price, sale_price, minimum_stock, current_stock):
        df = self.load_products()
        new_id = df['id'].max() + 1 if len(df) > 0 else 1
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
    
    def add_movement(self, product_id, movement_type, quantity, note=""):
        movements_df = self.load_movements()
        products_df = self.load_products()
        
        new_id = movements_df['id'].max() + 1 if len(movements_df) > 0 else 1
        
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
    
    def get_low_stock_products(self):
        df = self.load_products()
        return df[df['current_stock'] <= df['minimum_stock']]
    
    def search_products(self, query="", category=None):
        df = self.load_products()
        if query:
            df = df[df['name'].str.contains(query, case=False, na=False)]
        if category:
            df = df[df['category'] == category]
        return df