from PySide6.QtCore import QObject, Signal
from backend.utils.data_loader import DataLoader
from datetime import datetime, timedelta
import pandas as pd

class DashboardController(QObject):
    data_updated = Signal()
    
    def __init__(self):
        super().__init__()
        self.data_loader = DataLoader()
    
    def get_dashboard_data(self):
        products_df = self.data_loader.load_products()
        movements_df = self.data_loader.load_movements()
        
        # FILTRAR APENAS PRODUTOS ATIVOS
        active_products = products_df[products_df['active'] == True]
        
        total_products = len(active_products)
        total_bebidas = len(active_products[active_products['category'] == 'bebida'])
        total_doces = len(active_products[active_products['category'] == 'doce'])
        total_chips = len(active_products[active_products['category'] == 'salgado'])
        
        # Estoque baixo - APENAS PRODUTOS ATIVOS
        low_stock = active_products[active_products['current_stock'] <= active_products['minimum_stock']]
        low_stock_count = len(low_stock)
        
        seven_days_ago = datetime.now() - timedelta(days=7)
        if len(movements_df) > 0:
            movements_df['created_at'] = pd.to_datetime(movements_df['created_at'])
            recent_movements = movements_df[movements_df['created_at'] >= seven_days_ago]
        else:
            recent_movements = movements_df
        
        # Filtrar movimentações apenas de produtos ATIVOS
        if len(recent_movements) > 0:
            active_product_ids = active_products['id'].tolist()
            recent_movements = recent_movements[recent_movements['product_id'].isin(active_product_ids)]
        
        entries = len(recent_movements[recent_movements['movement_type'] == 'ENTRY']) if len(recent_movements) > 0 else 0
        exits = len(recent_movements[recent_movements['movement_type'] == 'EXIT']) if len(recent_movements) > 0 else 0
        
        top_products_data = []
        if len(recent_movements) > 0:
            top_products = recent_movements.groupby('product_id').size().sort_values(ascending=False).head(5)
            for product_id, count in top_products.items():
                # Verificar se o produto ainda está ativo
                product = active_products[active_products['id'] == product_id]
                if len(product) > 0:
                    top_products_data.append({
                        'name': product.iloc[0]['name'],
                        'count': count
                    })
        
        return {
            'total_products': total_products,
            'total_bebidas': total_bebidas,
            'total_doces': total_doces,
            'total_salgado': total_chips,
            'low_stock_count': low_stock_count,
            'low_stock_items': low_stock.to_dict(orient='records'),
            'entries_7days': entries,
            'exits_7days': exits,
            'top_products': top_products_data
        }