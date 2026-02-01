from PySide6.QtCore import QObject, Signal
from backend.utils.data_loader import DataLoader

class MovementsController(QObject):
    movements_updated = Signal()
    
    def __init__(self):
        super().__init__()
        self.data_loader = DataLoader()
    
    def add_movement(self, product_id, movement_type, quantity, note=""):
        movement_id, error = self.data_loader.add_movement(product_id, movement_type, quantity, note)
        
        if error:
            # Retornar erro se houver
            return None, error
        
        self.movements_updated.emit()
        return movement_id, None
    
    def get_all_movements(self):
        df = self.data_loader.load_movements()
        return df.to_dict(orient='records')
    
    def get_product_movements(self, product_id):
        df = self.data_loader.load_movements()
        df = df[df['product_id'] == product_id]
        return df.to_dict(orient='records')
    
    def delete_movement(self, movement_id):
        # Carregar movimentações
        movements_df = self.data_loader.load_movements()
        
        # Encontrar a movimentação
        movement = movements_df[movements_df['id'] == movement_id]
        
        if len(movement) == 0:
            return False
        
        # Reverter o estoque
        movement_data = movement.iloc[0]
        products_df = self.data_loader.load_products()
        mask = products_df['id'] == movement_data['product_id']
        
        if movement_data['movement_type'] == "ENTRY":
            # Se foi entrada, subtrai do estoque
            products_df.loc[mask, 'current_stock'] -= movement_data['quantity']
        elif movement_data['movement_type'] == "EXIT":
            # Se foi saída, adiciona ao estoque
            products_df.loc[mask, 'current_stock'] += movement_data['quantity']
        
        self.data_loader.save_products(products_df)
        
        # Remover a movimentação
        movements_df = movements_df[movements_df['id'] != movement_id]
        self.data_loader.save_movements(movements_df)
        
        self.movements_updated.emit()
        return True