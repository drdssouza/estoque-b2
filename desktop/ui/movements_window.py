from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QTableWidget, QTableWidgetItem, QDialog,
                               QFormLayout, QComboBox, QSpinBox, QTextEdit,
                               QMessageBox)
from PySide6.QtCore import Qt
from desktop.controllers.movements_controller import MovementsController
from desktop.controllers.products_controller import ProductsController
from functools import partial

def show_success_message(parent, title, message):
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setStyleSheet("""
        QMessageBox { background-color: #ecf0f1; }
        QMessageBox QLabel {
            color: #2c3e50; font-size: 14px; font-weight: bold; min-width: 300px;
        }
        QPushButton {
            background-color: #27ae60; color: white; padding: 8px 20px;
            border-radius: 4px; font-size: 13px; font-weight: bold; min-width: 80px;
        }
        QPushButton:hover { background-color: #229954; }
    """)
    msg.exec()

def show_warning_message(parent, title, message):
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setStyleSheet("""
        QMessageBox { background-color: #ecf0f1; }
        QMessageBox QLabel {
            color: #2c3e50; font-size: 14px; font-weight: bold; min-width: 300px;
        }
        QPushButton {
            background-color: #e74c3c; color: white; padding: 8px 20px;
            border-radius: 4px; font-size: 13px; font-weight: bold; min-width: 80px;
        }
        QPushButton:hover { background-color: #c0392b; }
    """)
    msg.exec()

def show_question_message(parent, title, message):
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Question)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msg.setStyleSheet("""
        QMessageBox { background-color: #ecf0f1; }
        QMessageBox QLabel {
            color: #2c3e50; font-size: 14px; font-weight: bold; min-width: 300px;
        }
        QPushButton {
            background-color: #3498db; color: white; padding: 8px 20px;
            border-radius: 4px; font-size: 13px; font-weight: bold; min-width: 80px;
        }
        QPushButton:hover { background-color: #2980b9; }
    """)
    return msg.exec()


class MovementsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.movements_controller = MovementsController()
        self.products_controller = ProductsController()
        self.movements_controller.movements_updated.connect(self.load_movements)
        self.setup_ui()
        self.load_movements()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        self.setStyleSheet("background-color: #ecf0f1;")
        
        # ── Header ──
        header_layout = QHBoxLayout()
        
        title = QLabel("Movimentações de Estoque")
        title.setStyleSheet("font-size: 32px; font-weight: bold; color: #2c3e50; background-color: transparent;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        btn_entry = QPushButton("+ Registrar Entrada")
        btn_entry.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-size: 16px;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #229954; }
        """)
        btn_entry.clicked.connect(self.show_entry_dialog)
        header_layout.addWidget(btn_entry)
        
        layout.addLayout(header_layout)
        
        # ── Tabela ──
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Produto", "Tipo", "Quantidade", "Data", "Observação", "Ações"
        ])
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: none;
                font-size: 14px;
                color: #2c3e50;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 10px;
                font-weight: bold;
                border: none;
                font-size: 13px;
            }
            QTableWidget::item {
                color: #2c3e50;
                padding: 8px;
                font-size: 13px;
            }
        """)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 180)
        self.table.setColumnWidth(5, 200)
        self.table.setColumnWidth(6, 120)
        self.table.verticalHeader().setDefaultSectionSize(50)
        layout.addWidget(self.table)
    
    def load_movements(self):
        movements = self.movements_controller.get_all_movements()
        products = {p['id']: p['name'] for p in self.products_controller.get_all_products()}
        
        self.table.setRowCount(len(movements))
        
        for row, movement in enumerate(reversed(movements)):
            # ID
            item_id = QTableWidgetItem(str(movement['id']))
            item_id.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, item_id)
            
            # Produto
            product_name = products.get(movement['product_id'], "Produto desconhecido")
            self.table.setItem(row, 1, QTableWidgetItem(product_name))
            
            # Tipo
            movement_type = "ENTRADA" if movement['movement_type'] == "ENTRY" else "SAÍDA"
            type_item = QTableWidgetItem(movement_type)
            type_item.setTextAlignment(Qt.AlignCenter)
            font = type_item.font()
            font.setBold(True)
            type_item.setFont(font)
            if movement['movement_type'] == "ENTRY":
                type_item.setForeground(Qt.darkGreen)
            else:
                type_item.setForeground(Qt.red)
            self.table.setItem(row, 2, type_item)
            
            # Quantidade
            item_qty = QTableWidgetItem(str(movement['quantity']))
            item_qty.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, item_qty)
            
            # Data
            item_date = QTableWidgetItem(str(movement['created_at']))
            item_date.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, item_date)
            
            # Observação
            self.table.setItem(row, 5, QTableWidgetItem(movement.get('note', '')))
            
            # Ações — botão Remover só aparece em entradas manuais (não geradas por comanda)
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 5, 5, 5)
            
            note = movement.get('note', '') or ''
            is_order_exit = movement['movement_type'] == "EXIT" and note.startswith("Comanda #")
            
            if not is_order_exit:
                btn_delete = QPushButton("Remover")
                btn_delete.setMinimumWidth(90)
                btn_delete.setMinimumHeight(35)
                btn_delete.setCursor(Qt.PointingHandCursor)
                btn_delete.setStyleSheet("""
                    QPushButton {
                        background-color: #e74c3c; color: white;
                        padding: 8px 12px; border-radius: 4px;
                        font-size: 13px; font-weight: bold; border: none;
                    }
                    QPushButton:hover { background-color: #c0392b; }
                    QPushButton:pressed { background-color: #a93226; }
                """)
                btn_delete.clicked.connect(partial(self.delete_movement, movement['id']))
                actions_layout.addWidget(btn_delete)
            else:
                # Saídas geradas por comanda não podem ser removidas individualmente
                lbl = QLabel("Auto")
                lbl.setStyleSheet("color: #95a5a6; font-size: 12px; font-style: italic;")
                lbl.setAlignment(Qt.AlignCenter)
                actions_layout.addWidget(lbl)
            
            self.table.setCellWidget(row, 6, actions_widget)
    
    def show_entry_dialog(self):
        dialog = EntryDialog(self, self.products_controller)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            movement_id, error = self.movements_controller.add_movement(**data)
            
            if error:
                show_warning_message(self, "Erro", error)
            else:
                show_success_message(self, "Sucesso", "Entrada registrada com sucesso!")
        
    def delete_movement(self, movement_id):
        result = show_question_message(
            self, 'Confirmação', 
            'Deseja realmente remover esta movimentação?\n\nO estoque será revertido automaticamente.'
        )
        if result == QMessageBox.Yes:
            success = self.movements_controller.delete_movement(movement_id)
            if success:
                show_success_message(self, "Sucesso", "Movimentação removida e estoque revertido!")
            else:
                show_warning_message(self, "Erro", "Não foi possível remover a movimentação")


class EntryDialog(QDialog):
    def __init__(self, parent, products_controller):
        super().__init__(parent)
        self.products_controller = products_controller
        self.setWindowTitle("Registrar Entrada")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(350)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        label_style = "color: #2c3e50; font-size: 14px; font-weight: bold;"
        
        input_style = """
            QComboBox, QSpinBox, QTextEdit {
                padding: 8px;
                font-size: 14px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background-color: white;
                color: #2c3e50;
            }
            QComboBox:focus, QSpinBox:focus, QTextEdit:focus {
                border: 2px solid #3498db;
            }
            QComboBox::drop-down { border: none; padding-right: 10px; }
        """
        self.setStyleSheet(input_style)
        
        # Título
        title = QLabel("➕ ENTRADA DE ESTOQUE")
        title.setStyleSheet("color: #27ae60; font-size: 18px; font-weight: bold; padding: 10px; background-color: transparent;")
        title.setAlignment(Qt.AlignCenter)
        layout.addRow(title)
        
        # Produto
        product_label = QLabel("Produto:")
        product_label.setStyleSheet(label_style)
        
        self.product_combo = QComboBox()
        self.product_combo.setMinimumHeight(40)
        products = self.products_controller.get_all_products()
        for product in products:
            if product['active']:
                display_text = f"{product['name']} (Estoque: {product['current_stock']})"
                self.product_combo.addItem(display_text, product['id'])
        
        layout.addRow(product_label, self.product_combo)
        
        # Quantidade
        quantity_label = QLabel("Quantidade:")
        quantity_label.setStyleSheet(label_style)
        
        self.quantity_input = QSpinBox()
        self.quantity_input.setMinimum(1)
        self.quantity_input.setMaximum(10000)
        self.quantity_input.setValue(1)
        self.quantity_input.setMinimumHeight(40)
        self.quantity_input.setSuffix(" unidades")
        
        layout.addRow(quantity_label, self.quantity_input)
        
        # Observação
        note_label = QLabel("Observação (opcional):")
        note_label.setStyleSheet(label_style)
        
        self.note_input = QTextEdit()
        self.note_input.setMaximumHeight(100)
        self.note_input.setPlaceholderText("Ex: Reposição semanal, fornecedor X, etc...")
        
        layout.addRow(note_label, self.note_input)
        
        # Botões
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        btn_save = QPushButton("✓ Confirmar")
        btn_save.setFixedHeight(45)
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; color: white;
                padding: 10px 30px; border-radius: 5px;
                font-size: 15px; font-weight: bold;
            }
            QPushButton:hover { background-color: #229954; }
        """)
        btn_save.clicked.connect(self.accept)
        
        btn_cancel = QPushButton("✗ Cancelar")
        btn_cancel.setFixedHeight(45)
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6; color: white;
                padding: 10px 30px; border-radius: 5px;
                font-size: 15px; font-weight: bold;
            }
            QPushButton:hover { background-color: #7f8c8d; }
        """)
        btn_cancel.clicked.connect(self.reject)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(btn_save)
        buttons_layout.addWidget(btn_cancel)
        
        layout.addRow(buttons_layout)
    
    def get_data(self):
        return {
            'product_id': self.product_combo.currentData(),
            'movement_type': 'ENTRY',
            'quantity': self.quantity_input.value(),
            'note': self.note_input.toPlainText()
        }