from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QTableWidget, QTableWidgetItem, QDialog,
                               QFormLayout, QComboBox, QSpinBox, QLineEdit,
                               QMessageBox, QFrame, QScrollArea)
from PySide6.QtCore import Qt
from desktop.controllers.orders_controller import OrdersController
from desktop.controllers.products_controller import ProductsController
from functools import partial


class OrdersWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.orders_controller = OrdersController()
        self.products_controller = ProductsController()
        self.orders_controller.orders_updated.connect(self.load_orders)
        self.setup_ui()
        self.load_orders()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        self.setStyleSheet("background-color: #ecf0f1;")

        # ── Header ──
        header_layout = QHBoxLayout()

        title = QLabel("Comandas")
        title.setStyleSheet("font-size: 32px; font-weight: bold; color: #2c3e50; background-color: transparent;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        btn_new = QPushButton("+ Nova Comanda")
        btn_new.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-size: 16px;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        btn_new.clicked.connect(self.create_new_order)
        header_layout.addWidget(btn_new)

        layout.addLayout(header_layout)

        # ── Filtros ──
        filter_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por nome do cliente...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                font-size: 14px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background-color: white;
                color: #2c3e50;
            }
        """)
        self.search_input.textChanged.connect(self.load_orders)
        filter_layout.addWidget(self.search_input)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["Todas", "aberta", "fechada"])
        self.status_filter.setStyleSheet("""
            QComboBox {
                padding: 10px;
                font-size: 14px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background-color: white;
                color: #2c3e50;
            }
        """)
        self.status_filter.currentTextChanged.connect(self.load_orders)
        filter_layout.addWidget(self.status_filter)

        layout.addLayout(filter_layout)

        # ── Tabela ──
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Cliente", "Status", "Total", "Horário", "Ações"
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
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(1, 220)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 110)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(5, 200)
        self.table.verticalHeader().setDefaultSectionSize(50)

        layout.addWidget(self.table)

    # ── DATA ─────────────────────────────────────────────────────────

    def load_orders(self):
        query = self.search_input.text()
        status = self.status_filter.currentText()
        orders = self.orders_controller.search_orders(query, status)

        self.table.setRowCount(len(orders))

        for row, order in enumerate(orders):
            # ID
            item_id = QTableWidgetItem(str(order['id']))
            item_id.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, item_id)

            # Cliente
            self.table.setItem(row, 1, QTableWidgetItem(order['customer_name']))

            # Status
            status_text = "ABERTA" if order['status'] == 'aberta' else "FECHADA"
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignCenter)
            font = status_item.font()
            font.setBold(True)
            status_item.setFont(font)
            if order['status'] == 'aberta':
                status_item.setForeground(Qt.darkGreen)
            else:
                status_item.setForeground(Qt.darkRed)
            self.table.setItem(row, 2, status_item)

            # Total
            total_item = QTableWidgetItem(f"R$ {order['total']:.2f}")
            total_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, total_item)

            # Horário
            try:
                from datetime import datetime as dt
                import pandas as pd
                created = pd.to_datetime(order['created_at'])
                horario = created.strftime('%H:%M:%S')
            except Exception:
                horario = str(order['created_at'])
            horario_item = QTableWidgetItem(horario)
            horario_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, horario_item)

            # Ações
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 5, 5, 5)
            actions_layout.setSpacing(6)

            btn_detail = QPushButton("Detalhes")
            btn_detail.setMinimumWidth(80)
            btn_detail.setMinimumHeight(35)
            btn_detail.setCursor(Qt.PointingHandCursor)
            btn_detail.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    padding: 6px 10px;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: bold;
                    border: none;
                }
                QPushButton:hover { background-color: #2980b9; }
            """)
            btn_detail.clicked.connect(partial(self.show_order_detail, order))
            actions_layout.addWidget(btn_detail)

            if order['status'] == 'aberta':
                btn_close = QPushButton("Fechar")
                btn_close.setMinimumWidth(70)
                btn_close.setMinimumHeight(35)
                btn_close.setCursor(Qt.PointingHandCursor)
                btn_close.setStyleSheet("""
                    QPushButton {
                        background-color: #27ae60;
                        color: white;
                        padding: 6px 10px;
                        border-radius: 4px;
                        font-size: 12px;
                        font-weight: bold;
                        border: none;
                    }
                    QPushButton:hover { background-color: #229954; }
                """)
                btn_close.clicked.connect(partial(self.close_order, order['id']))
                actions_layout.addWidget(btn_close)

                btn_delete = QPushButton("Excluir")
                btn_delete.setMinimumWidth(70)
                btn_delete.setMinimumHeight(35)
                btn_delete.setCursor(Qt.PointingHandCursor)
                btn_delete.setStyleSheet("""
                    QPushButton {
                        background-color: #e74c3c;
                        color: white;
                        padding: 6px 10px;
                        border-radius: 4px;
                        font-size: 12px;
                        font-weight: bold;
                        border: none;
                    }
                    QPushButton:hover { background-color: #c0392b; }
                """)
                btn_delete.clicked.connect(partial(self.delete_order, order['id']))
                actions_layout.addWidget(btn_delete)

            self.table.setCellWidget(row, 5, actions_widget)

    # ── ACTIONS ──────────────────────────────────────────────────────

    def create_new_order(self):
        dialog = NewOrderDialog(self)
        if dialog.exec() == QDialog.Accepted:
            customer_name = dialog.get_customer_name()
            if customer_name.strip():
                order_id = self.orders_controller.create_order(customer_name.strip())
                # Abrir detalhes imediatamente
                order = {'id': order_id, 'customer_name': customer_name.strip(), 'status': 'aberta', 'total': 0.0}
                self.show_order_detail(order)

    def show_order_detail(self, order):
        dialog = OrderDetailDialog(self, order, self.orders_controller, self.products_controller)
        dialog.exec()
        self.load_orders()

    def close_order(self, order_id):
        # Verificar se a comanda tem itens
        items = self.orders_controller.get_order_items(order_id)
        if len(items) == 0:
            QMessageBox.warning(self, "Aviso", "A comanda não possui itens.\nAdicione pelo menos um item antes de fechar.")
            return

        reply = QMessageBox.question(
            self, 'Confirmação',
            'Fechar esta comanda?\n\nOs itens serão descontados do estoque automaticamente.',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.orders_controller.close_order(order_id)

    def delete_order(self, order_id):
        reply = QMessageBox.question(
            self, 'Confirmação',
            'Excluir esta comanda e todos os seus itens?',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.orders_controller.delete_order(order_id)


# ─── DIALOGS ─────────────────────────────────────────────────────────────────

class NewOrderDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Nova Comanda")
        self.setModal(True)
        self.setMinimumWidth(420)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        title = QLabel("Nova Comanda")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        label = QLabel("Nome do Cliente:")
        label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ex: João Silva")
        self.name_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                font-size: 15px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background-color: white;
                color: #2c3e50;
            }
            QLineEdit:focus { border: 2px solid #3498db; }
        """)
        layout.addWidget(self.name_input)

        buttons = QHBoxLayout()
        btn_create = QPushButton("Criar Comanda")
        btn_create.setFixedHeight(42)
        btn_create.setCursor(Qt.PointingHandCursor)
        btn_create.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px 25px;
                border-radius: 5px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #229954; }
        """)
        btn_create.clicked.connect(self.accept)
        buttons.addWidget(btn_create)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setFixedHeight(42)
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 10px 25px;
                border-radius: 5px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #7f8c8d; }
        """)
        btn_cancel.clicked.connect(self.reject)
        buttons.addWidget(btn_cancel)

        layout.addLayout(buttons)

    def get_customer_name(self):
        return self.name_input.text()


class OrderDetailDialog(QDialog):
    def __init__(self, parent, order, orders_controller, products_controller):
        super().__init__(parent)
        self.order = order
        self.orders_controller = orders_controller
        self.products_controller = products_controller
        self.setWindowTitle(f"Comanda #{order['id']} - {order['customer_name']}")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self.setup_ui()
        self.load_items()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(12)

        # ── Header info ──
        info_frame = QFrame()
        info_frame.setStyleSheet("background-color: #34495e; border-radius: 8px; padding: 12px;")
        info_layout = QHBoxLayout(info_frame)

        name_label = QLabel(f"Cliente: {self.order['customer_name']}")
        name_label.setStyleSheet("color: white; font-size: 15px; font-weight: bold;")
        info_layout.addWidget(name_label)

        info_layout.addStretch()

        status_text = "ABERTA" if self.order['status'] == 'aberta' else "FECHADA"
        status_color = "#27ae60" if self.order['status'] == 'aberta' else "#e74c3c"
        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"color: {status_color}; font-size: 15px; font-weight: bold;")
        info_layout.addWidget(status_label)

        layout.addWidget(info_frame)

        # ── Adicionar item (só se aberta) ──
        if self.order['status'] == 'aberta':
            add_frame = QFrame()
            add_frame.setStyleSheet("background-color: white; border-radius: 6px; padding: 10px; border: 1px solid #ddd;")
            add_layout = QHBoxLayout(add_frame)

            self.product_combo = QComboBox()
            self.product_combo.setStyleSheet("""
                QComboBox {
                    padding: 8px;
                    font-size: 13px;
                    border: 2px solid #bdc3c7;
                    border-radius: 4px;
                    background-color: white;
                    color: #2c3e50;
                }
            """)
            products = self.products_controller.get_all_products()
            for p in products:
                if p['active']:
                    self.product_combo.addItem(f"{p['name']} - R$ {p['sale_price']:.2f}", p['id'])
            add_layout.addWidget(self.product_combo)

            self.qty_input = QSpinBox()
            self.qty_input.setMinimum(1)
            self.qty_input.setMaximum(999)
            self.qty_input.setValue(1)
            self.qty_input.setFixedWidth(80)
            self.qty_input.setStyleSheet("""
                QSpinBox {
                    padding: 8px;
                    font-size: 13px;
                    border: 2px solid #bdc3c7;
                    border-radius: 4px;
                    background-color: white;
                    color: #2c3e50;
                }
            """)
            add_layout.addWidget(self.qty_input)

            btn_add = QPushButton("+ Adicionar")
            btn_add.setFixedHeight(38)
            btn_add.setCursor(Qt.PointingHandCursor)
            btn_add.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    padding: 6px 16px;
                    border-radius: 4px;
                    font-size: 13px;
                    font-weight: bold;
                    border: none;
                }
                QPushButton:hover { background-color: #2980b9; }
            """)
            btn_add.clicked.connect(self.add_item)
            add_layout.addWidget(btn_add)

            layout.addWidget(add_frame)

        # ── Tabela de itens ──
        self.items_table = QTableWidget()
        col_count = 5 if self.order['status'] == 'aberta' else 4
        self.items_table.setColumnCount(col_count)
        headers = ["Produto", "Qtd", "Preço Unit.", "Subtotal"]
        if self.order['status'] == 'aberta':
            headers.append("Remover")
        self.items_table.setHorizontalHeaderLabels(headers)
        self.items_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: none;
                font-size: 13px;
                color: #2c3e50;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: none;
                font-size: 12px;
            }
            QTableWidget::item {
                color: #2c3e50;
                padding: 6px;
            }
        """)
        self.items_table.horizontalHeader().setStretchLastSection(False)
        self.items_table.setColumnWidth(0, 220)
        self.items_table.setColumnWidth(1, 60)
        self.items_table.setColumnWidth(2, 100)
        self.items_table.setColumnWidth(3, 100)
        if self.order['status'] == 'aberta':
            self.items_table.setColumnWidth(4, 90)
        self.items_table.verticalHeader().setDefaultSectionSize(40)

        layout.addWidget(self.items_table)

        # ── Total ──
        total_frame = QFrame()
        total_frame.setStyleSheet("background-color: #2c3e50; border-radius: 6px; padding: 12px;")
        total_layout = QHBoxLayout(total_frame)

        total_label_text = QLabel("TOTAL DA COMANDA:")
        total_label_text.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        total_layout.addWidget(total_label_text)

        total_layout.addStretch()

        self.total_label = QLabel("R$ 0,00")
        self.total_label.setStyleSheet("color: #2ecc71; font-size: 22px; font-weight: bold;")
        total_layout.addWidget(self.total_label)

        layout.addWidget(total_frame)

        # ── Botão fechar (se aberta) ──
        if self.order['status'] == 'aberta':
            btn_close = QPushButton("Fechar Comanda")
            btn_close.setFixedHeight(44)
            btn_close.setCursor(Qt.PointingHandCursor)
            btn_close.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    font-size: 16px;
                    font-weight: bold;
                    border-radius: 5px;
                }
                QPushButton:hover { background-color: #229954; }
            """)
            btn_close.clicked.connect(self.close_this_order)
            layout.addWidget(btn_close)

    # ── ITEM MANAGEMENT ──────────────────────────────────────────────

    def load_items(self):
        items = self.orders_controller.get_order_items(self.order['id'])
        self.items_table.setRowCount(len(items))

        total = 0.0
        for row, item in enumerate(items):
            self.items_table.setItem(row, 0, QTableWidgetItem(item['product_name']))

            qty_item = QTableWidgetItem(str(item['quantity']))
            qty_item.setTextAlignment(Qt.AlignCenter)
            self.items_table.setItem(row, 1, qty_item)

            price_item = QTableWidgetItem(f"R$ {item['unit_price']:.2f}")
            price_item.setTextAlignment(Qt.AlignCenter)
            self.items_table.setItem(row, 2, price_item)

            sub_item = QTableWidgetItem(f"R$ {item['subtotal']:.2f}")
            sub_item.setTextAlignment(Qt.AlignCenter)
            self.items_table.setItem(row, 3, sub_item)

            total += item['subtotal']

            if self.order['status'] == 'aberta':
                btn_remove = QPushButton("X")
                btn_remove.setFixedSize(60, 30)
                btn_remove.setCursor(Qt.PointingHandCursor)
                btn_remove.setStyleSheet("""
                    QPushButton {
                        background-color: #e74c3c;
                        color: white;
                        border-radius: 4px;
                        font-size: 13px;
                        font-weight: bold;
                        border: none;
                    }
                    QPushButton:hover { background-color: #c0392b; }
                """)
                btn_remove.clicked.connect(partial(self.remove_item, item['id']))

                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(5, 5, 5, 5)
                btn_layout.addWidget(btn_remove)
                self.items_table.setCellWidget(row, 4, btn_widget)

        self.total_label.setText(f"R$ {total:.2f}")

    def add_item(self):
        product_id = self.product_combo.currentData()
        quantity = self.qty_input.value()
        self.orders_controller.add_item_to_order(self.order['id'], product_id, quantity)
        self.qty_input.setValue(1)
        self.load_items()

    def remove_item(self, item_id):
        self.orders_controller.remove_item_from_order(item_id)
        self.load_items()

    def close_this_order(self):
        items = self.orders_controller.get_order_items(self.order['id'])
        if len(items) == 0:
            QMessageBox.warning(self, "Aviso", "A comanda não possui itens.\nAdicione pelo menos um item antes de fechar.")
            return

        reply = QMessageBox.question(
            self, 'Confirmação',
            'Fechar esta comanda?\n\nOs itens serão descontados do estoque automaticamente.',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.orders_controller.close_order(self.order['id'])
            self.accept()