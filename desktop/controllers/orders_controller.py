from PySide6.QtCore import QObject, Signal
from backend.utils.data_loader import DataLoader


class OrdersController(QObject):
    orders_updated = Signal()

    def __init__(self):
        super().__init__()
        self.data_loader = DataLoader()

    def get_all_orders(self):
        df = self.data_loader.load_orders()
        return df.to_dict(orient='records')

    def get_open_orders(self):
        df = self.data_loader.load_orders()
        return df[df['status'] == 'aberta'].to_dict(orient='records')

    def get_closed_orders(self):
        df = self.data_loader.load_orders()
        return df[df['status'] == 'fechada'].to_dict(orient='records')

    def get_order_items(self, order_id):
        items_df = self.data_loader.load_order_items()
        products_df = self.data_loader.load_products()
        products_map = dict(zip(products_df['id'], products_df['name']))

        order_items = items_df[items_df['order_id'] == order_id].to_dict(orient='records')
        for item in order_items:
            item['product_name'] = products_map.get(item['product_id'], 'Produto desconhecido')
        return order_items

    def create_order(self, customer_name):
        order_id = self.data_loader.add_order(customer_name)
        self.orders_updated.emit()
        return order_id

    def add_item_to_order(self, order_id, product_id, quantity):
        products_df = self.data_loader.load_products()
        product = products_df[products_df['id'] == product_id]
        if len(product) == 0:
            return False
        unit_price = float(product.iloc[0]['sale_price'])
        self.data_loader.add_order_item(order_id, product_id, quantity, unit_price)
        self.orders_updated.emit()
        return True

    def remove_item_from_order(self, item_id):
        success = self.data_loader.remove_order_item(item_id)
        if success:
            self.orders_updated.emit()
        return success

    def close_order(self, order_id):
        self.data_loader.close_order(order_id)
        self.orders_updated.emit()

    def delete_order(self, order_id):
        self.data_loader.delete_order(order_id)
        self.orders_updated.emit()

    def search_orders(self, query="", status_filter=None):
        df = self.data_loader.load_orders()
        if query:
            df = df[df['customer_name'].str.contains(query, case=False, na=False)]
        if status_filter and status_filter != "Todas":
            df = df[df['status'] == status_filter]
        return df.to_dict(orient='records')