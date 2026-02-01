from PySide6.QtCore import QObject, Signal
from backend.utils.data_loader import DataLoader

class ProductsController(QObject):
    products_updated = Signal()
    
    def __init__(self):
        super().__init__()
        self.data_loader = DataLoader()
    
    def get_all_products(self):
        df = self.data_loader.load_products()
        return df.to_dict(orient='records')
    
    def add_product(self, name, category, purchase_price, sale_price, minimum_stock, current_stock):
        product_id = self.data_loader.add_product(
            name, category, purchase_price, sale_price, minimum_stock, current_stock
        )
        self.products_updated.emit()
        return product_id
    
    def update_product(self, product_id, **kwargs):
        self.data_loader.update_product(product_id, **kwargs)
        self.products_updated.emit()
    
    def deactivate_product(self, product_id):
        self.data_loader.deactivate_product(product_id)
        self.products_updated.emit()
    
    def search_products(self, query="", category=None):
        df = self.data_loader.search_products(query, category)
        return df.to_dict(orient='records')