from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QTableWidget, QTableWidgetItem, QDialog,
                               QComboBox, QLineEdit, QMessageBox, QFrame, QHeaderView)
from PySide6.QtCore import Qt
from desktop.controllers.orders_controller import OrdersController
from desktop.controllers.products_controller import ProductsController
from functools import partial
import webbrowser
import urllib.parse
import re
import json
from pathlib import Path


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


# ─── JANELA PRINCIPAL ─────────────────────────────────────────────────────────

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
                background-color: #27ae60; color: white;
                font-size: 16px; padding: 10px 20px;
                border-radius: 5px; font-weight: bold;
            }
            QPushButton:hover { background-color: #229954; }
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
                padding: 10px; font-size: 14px;
                border: 2px solid #bdc3c7; border-radius: 5px;
                background-color: white; color: #2c3e50;
            }
        """)
        self.search_input.textChanged.connect(self.load_orders)
        filter_layout.addWidget(self.search_input)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["Todas", "aberta", "fechada"])
        self.status_filter.setStyleSheet("""
            QComboBox {
                padding: 10px; font-size: 14px;
                border: 2px solid #bdc3c7; border-radius: 5px;
                background-color: white; color: #2c3e50;
            }
        """)
        self.status_filter.currentTextChanged.connect(self.load_orders)
        filter_layout.addWidget(self.status_filter)
        layout.addLayout(filter_layout)

        # ── Tabela ──
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Cliente", "Status", "Total", "Data/Hora", "Ações"
        ])
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white; border: none;
                font-size: 14px; color: #2c3e50;
            }
            QHeaderView::section {
                background-color: #34495e; color: white;
                padding: 10px; font-weight: bold;
                border: none; font-size: 13px;
            }
            QTableWidget::item {
                color: #2c3e50; padding: 8px; font-size: 13px;
            }
        """)
        orders_header = self.table.horizontalHeader()
        orders_header.setStretchLastSection(False)
        orders_header.setSectionResizeMode(QHeaderView.Interactive)
        self.table.setColumnWidth(0, 35)   # ID
        self.table.setColumnWidth(1, 207)  # Cliente
        self.table.setColumnWidth(2, 100)  # Status
        self.table.setColumnWidth(3, 140)  # Total
        self.table.setColumnWidth(4, 100)  # Data/Hora
        self.table.setColumnWidth(5, 277)  # Ações
        self.table.verticalHeader().setDefaultSectionSize(50)
        layout.addWidget(self.table)

    # ── DATA ─────────────────────────────────────────────────────────

    def load_orders(self):
        query = self.search_input.text()
        status = self.status_filter.currentText()
        orders = self.orders_controller.search_orders(query, status)

        self.table.setRowCount(len(orders))

        for row, order in enumerate(orders):
            item_id = QTableWidgetItem(str(order['id']))
            item_id.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, item_id)

            self.table.setItem(row, 1, QTableWidgetItem(order['customer_name']))

            status_text = "ABERTA" if order['status'] == 'aberta' else "FECHADA"
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignCenter)
            font = status_item.font()
            font.setBold(True)
            status_item.setFont(font)
            status_item.setForeground(Qt.darkGreen if order['status'] == 'aberta' else Qt.darkRed)
            self.table.setItem(row, 2, status_item)

            total_item = QTableWidgetItem(f"R$ {order['total']:.2f}")
            total_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, total_item)

            try:
                import pandas as pd
                created = pd.to_datetime(order['created_at'])
                data_hora = created.strftime('%d/%m/%Y %H:%M')
            except Exception:
                data_hora = str(order['created_at'])
            horario_item = QTableWidgetItem(data_hora)
            horario_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, horario_item)

            # Ações
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 5, 5, 5)
            actions_layout.setSpacing(6)

            btn_detail = QPushButton("Detalhes")
            btn_detail.setFixedSize(90, 35)
            btn_detail.setCursor(Qt.PointingHandCursor)
            btn_detail.setStyleSheet("""
                QPushButton {
                    background-color: #3498db; color: white;
                    border-radius: 4px; font-size: 12px; font-weight: bold; border: none;
                }
                QPushButton:hover { background-color: #2980b9; }
            """)
            btn_detail.clicked.connect(partial(self.show_order_detail, order))
            actions_layout.addWidget(btn_detail)

            if order['status'] == 'aberta':
                btn_close = QPushButton("Fechar")
                btn_close.setFixedSize(75, 35)
                btn_close.setCursor(Qt.PointingHandCursor)
                btn_close.setStyleSheet("""
                    QPushButton {
                        background-color: #27ae60; color: white;
                        border-radius: 4px; font-size: 12px; font-weight: bold; border: none;
                    }
                    QPushButton:hover { background-color: #229954; }
                """)
                btn_close.clicked.connect(partial(self.close_order, order['id']))
                actions_layout.addWidget(btn_close)

                btn_delete = QPushButton("Excluir")
                btn_delete.setFixedSize(75, 35)
                btn_delete.setCursor(Qt.PointingHandCursor)
                btn_delete.setStyleSheet("""
                    QPushButton {
                        background-color: #e74c3c; color: white;
                        border-radius: 4px; font-size: 12px; font-weight: bold; border: none;
                    }
                    QPushButton:hover { background-color: #c0392b; }
                """)
                btn_delete.clicked.connect(partial(self.delete_order, order['id']))
                actions_layout.addWidget(btn_delete)

            actions_layout.addStretch()
            self.table.setCellWidget(row, 5, actions_widget)

    # ── ACTIONS ──────────────────────────────────────────────────────

    def create_new_order(self):
        dialog = NewOrderDialog(self)
        if dialog.exec() == QDialog.Accepted:
            customer_name = dialog.get_customer_name()
            if customer_name.strip():
                order_id = self.orders_controller.create_order(customer_name.strip())
                order = {'id': order_id, 'customer_name': customer_name.strip(), 'status': 'aberta', 'total': 0.0, 'phone': ''}
                self.show_order_detail(order)

    def show_order_detail(self, order):
        dialog = OrderDetailDialog(self, order, self.orders_controller, self.products_controller)
        dialog.exec()
        self.load_orders()

    def close_order(self, order_id):
        items = self.orders_controller.get_order_items(order_id)
        if len(items) == 0:
            QMessageBox.warning(self, "Aviso", "A comanda não possui itens.\nAdicione pelo menos um item antes de fechar.")
            return
        reply = show_question_message(
            self, 'Confirmação',
            'Fechar esta comanda?\n\nOs itens serão descontados do estoque automaticamente.'
        )
        if reply == QMessageBox.Yes:
            self.orders_controller.close_order(order_id)

    def delete_order(self, order_id):
        reply = show_question_message(self, 'Confirmação', 'Excluir esta comanda e todos os seus itens?')
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
                padding: 10px; font-size: 15px;
                border: 2px solid #bdc3c7; border-radius: 5px;
                background-color: white; color: #2c3e50;
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
                background-color: #27ae60; color: white;
                padding: 10px 25px; border-radius: 5px;
                font-size: 15px; font-weight: bold;
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
                background-color: #95a5a6; color: white;
                padding: 10px 25px; border-radius: 5px;
                font-size: 15px; font-weight: bold;
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
        self.setMinimumWidth(660)
        self.setMinimumHeight(520)
        self.setup_ui()
        self.load_items()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(12)

        # ── Header ──
        info_frame = QFrame()
        info_frame.setStyleSheet("background-color: #34495e; border-radius: 8px; padding: 12px;")
        info_layout = QHBoxLayout(info_frame)

        name_label = QLabel(f"Cliente: {self.order['customer_name']}")
        name_label.setStyleSheet("color: white; font-size: 15px; font-weight: bold;")
        info_layout.addWidget(name_label)
        info_layout.addStretch()

        phone_icon = QLabel("📱")
        phone_icon.setStyleSheet("color: white; font-size: 14px; background: transparent;")
        info_layout.addWidget(phone_icon)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("(11) 99999-9999")
        self.phone_input.setText(str(self.order.get('phone', '') or ''))
        self.phone_input.setFixedWidth(155)
        self.phone_input.setStyleSheet("""
            QLineEdit {
                padding: 5px 10px; font-size: 13px;
                border: 2px solid #7f8c8d; border-radius: 4px;
                background-color: #2c3e50; color: white;
            }
            QLineEdit:focus { border: 2px solid #25d366; }
        """)
        self.phone_input.editingFinished.connect(self._save_phone)
        info_layout.addWidget(self.phone_input)

        info_layout.addSpacing(12)

        status_text = "ABERTA" if self.order['status'] == 'aberta' else "FECHADA"
        status_color = "#27ae60" if self.order['status'] == 'aberta' else "#e74c3c"
        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"color: {status_color}; font-size: 15px; font-weight: bold;")
        info_layout.addWidget(status_label)
        layout.addWidget(info_frame)

        # ── Adicionar item (só se aberta) ──
        if self.order['status'] == 'aberta':
            add_frame = QFrame()
            add_frame.setStyleSheet(
                "background-color: white; border-radius: 6px; padding: 8px; border: 1px solid #ddd;"
            )
            add_layout = QHBoxLayout(add_frame)
            add_layout.setSpacing(8)

            # Campo de busca visível com ícone
            self.product_search = QLineEdit()
            self.product_search.setPlaceholderText("🔍  Buscar produto...")
            self.product_search.setStyleSheet("""
                QLineEdit {
                    padding: 8px 12px; font-size: 13px;
                    border: 2px solid #bdc3c7; border-radius: 4px;
                    background-color: white; color: #2c3e50;
                    min-width: 150px;
                }
                QLineEdit:focus { border-color: #3498db; }
            """)
            add_layout.addWidget(self.product_search)

            # Combo de seleção (não editável — texto sempre visível)
            self.product_combo = QComboBox()
            self.product_combo.setStyleSheet("""
                QComboBox {
                    padding: 8px 12px; font-size: 13px;
                    border: 2px solid #bdc3c7; border-radius: 4px;
                    background-color: white; color: #2c3e50;
                    min-width: 200px;
                }
                QComboBox::drop-down { border: none; padding-right: 8px; }
                QComboBox QAbstractItemView {
                    color: #2c3e50; background-color: white;
                    selection-background-color: #3498db;
                    selection-color: white;
                }
            """)

            products = self.products_controller.get_all_products()
            self._all_products = [
                (p['name'], p['id'], p['sale_price']) for p in products if p['active']
            ]
            self._populate_product_combo("")
            self.product_search.textChanged.connect(self._populate_product_combo)
            add_layout.addWidget(self.product_combo)

            btn_add = QPushButton("+ Adicionar")
            btn_add.setFixedHeight(38)
            btn_add.setCursor(Qt.PointingHandCursor)
            btn_add.setStyleSheet("""
                QPushButton {
                    background-color: #3498db; color: white;
                    padding: 6px 18px; border-radius: 4px;
                    font-size: 13px; font-weight: bold; border: none;
                }
                QPushButton:hover { background-color: #2980b9; }
            """)
            btn_add.clicked.connect(self.add_item)
            add_layout.addWidget(btn_add)

            layout.addWidget(add_frame)

        # ── Tabela de itens (agrupada por produto) ──
        # Colunas: Produto | Quantidade | Preço Unit. | Subtotal | Histórico
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels(
            ["Produto", "Quantidade", "Preço Unit.", "Subtotal", "Histórico"]
        )
        self.items_table.setStyleSheet("""
            QTableWidget {
                background-color: white; border: none;
                font-size: 13px; color: #2c3e50;
            }
            QHeaderView::section {
                background-color: #34495e; color: white;
                padding: 8px; font-weight: bold;
                border: none; font-size: 12px;
            }
            QTableWidget::item { color: #2c3e50; padding: 6px; }
        """)
        items_header = self.items_table.horizontalHeader()
        items_header.setSectionResizeMode(0, QHeaderView.Stretch)           # Produto
        items_header.setSectionResizeMode(1, QHeaderView.Fixed)             # Quantidade
        items_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Preço Unit.
        items_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Subtotal
        items_header.setSectionResizeMode(4, QHeaderView.Fixed)             # Histórico
        self.items_table.setColumnWidth(1, 130)
        self.items_table.setColumnWidth(4, 100)
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.verticalHeader().setDefaultSectionSize(44)
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

        # ── Botões de ação ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        btn_whatsapp = QPushButton("📱 Cobrar via WhatsApp")
        btn_whatsapp.setFixedHeight(44)
        btn_whatsapp.setCursor(Qt.PointingHandCursor)
        btn_whatsapp.setStyleSheet("""
            QPushButton {
                background-color: #25d366; color: white;
                font-size: 15px; font-weight: bold; border-radius: 5px;
            }
            QPushButton:hover { background-color: #1ebe57; }
        """)
        btn_whatsapp.clicked.connect(self._enviar_whatsapp)
        btn_row.addWidget(btn_whatsapp)

        if self.order['status'] == 'aberta':
            btn_close = QPushButton("Fechar Comanda")
            btn_close.setFixedHeight(44)
            btn_close.setCursor(Qt.PointingHandCursor)
            btn_close.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60; color: white;
                    font-size: 15px; font-weight: bold; border-radius: 5px;
                }
                QPushButton:hover { background-color: #229954; }
            """)
            btn_close.clicked.connect(self.close_this_order)
            btn_row.addWidget(btn_close)

        layout.addLayout(btn_row)

    # ── ITEM MANAGEMENT ──────────────────────────────────────────────

    def _populate_product_combo(self, text=""):
        """Filtra o combo de produto conforme o texto de busca."""
        self.product_combo.clear()
        query = text.lower()
        for name, pid, price in self._all_products:
            if not query or query in name.lower():
                self.product_combo.addItem(f"{name} - R$ {price:.2f}", pid)

    def load_items(self):
        """Carrega itens agrupados por produto."""
        items = self.orders_controller.get_order_items(self.order['id'])

        # Agrupar por product_id
        groups = {}
        for item in items:
            pid = item['product_id']
            if pid not in groups:
                groups[pid] = {
                    'product_id': pid,
                    'product_name': item['product_name'],
                    'quantity': 0,
                    'unit_price': item['unit_price'],
                    'subtotal': 0.0,
                    'entries': []
                }
            groups[pid]['quantity'] += item['quantity']
            groups[pid]['subtotal'] += item['subtotal']
            groups[pid]['entries'].append(item)

        grouped = list(groups.values())
        self.items_table.setRowCount(len(grouped))

        total = 0.0
        for row, group in enumerate(grouped):
            # Produto
            self.items_table.setItem(row, 0, QTableWidgetItem(group['product_name']))

            # Quantidade: widget [−][n][+] se aberta, texto puro se fechada
            if self.order['status'] == 'aberta':
                self.items_table.setCellWidget(row, 1, self._create_grouped_qty_widget(group))
            else:
                qty_item = QTableWidgetItem(str(group['quantity']))
                qty_item.setTextAlignment(Qt.AlignCenter)
                self.items_table.setItem(row, 1, qty_item)

            price_item = QTableWidgetItem(f"R$ {group['unit_price']:.2f}")
            price_item.setTextAlignment(Qt.AlignCenter)
            self.items_table.setItem(row, 2, price_item)

            sub_item = QTableWidgetItem(f"R$ {group['subtotal']:.2f}")
            sub_item.setTextAlignment(Qt.AlignCenter)
            self.items_table.setItem(row, 3, sub_item)

            # Botão Histórico
            self.items_table.setCellWidget(row, 4, self._create_hist_widget(group))

            total += group['subtotal']

        self.total_label.setText(f"R$ {total:.2f}")

    def _create_grouped_qty_widget(self, group):
        """Widget [−] [qtd total] [+] para o grupo de um produto."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignCenter)

        btn_style = """
            QPushButton {
                background-color: #34495e; color: white; border: none;
                border-radius: 4px; font-size: 18px; font-weight: bold;
                width: 32px; height: 32px; padding: 0;
            }
            QPushButton:hover { background-color: #2c3e50; }
            QPushButton:pressed { background-color: #1a252f; }
        """

        btn_minus = QPushButton("−")
        btn_minus.setFixedSize(32, 32)
        btn_minus.setCursor(Qt.PointingHandCursor)
        btn_minus.setStyleSheet(btn_style)
        btn_minus.clicked.connect(partial(self._remove_last_entry, group['product_id']))
        layout.addWidget(btn_minus)

        qty_label = QLabel(str(group['quantity']))
        qty_label.setFixedWidth(40)
        qty_label.setAlignment(Qt.AlignCenter)
        qty_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(qty_label)

        btn_plus = QPushButton("+")
        btn_plus.setFixedSize(32, 32)
        btn_plus.setCursor(Qt.PointingHandCursor)
        btn_plus.setStyleSheet(btn_style)
        btn_plus.clicked.connect(partial(self._add_entry_for_product, group['product_id']))
        layout.addWidget(btn_plus)

        return widget

    def _create_hist_widget(self, group):
        """Botão 'Hist.' que abre o histórico de adições do produto."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setAlignment(Qt.AlignCenter)

        count = len(group['entries'])
        btn = QPushButton(f"📋 {count}x" if count > 1 else "📋 Hist.")
        btn.setFixedHeight(32)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad; color: white;
                padding: 4px 8px; border-radius: 4px;
                font-size: 12px; font-weight: bold; border: none;
            }
            QPushButton:hover { background-color: #7d3c98; }
        """)
        btn.clicked.connect(partial(self._show_item_history, group))
        layout.addWidget(btn)
        return widget

    def _show_item_history(self, group):
        dialog = ItemHistoryDialog(self, group, self.orders_controller, self.order)
        dialog.exec()
        self.load_items()

    def _remove_last_entry(self, product_id):
        """[−] remove/reduz a entrada mais recente desse produto."""
        self.orders_controller.remove_last_entry_for_product(self.order['id'], product_id)
        self.load_items()

    def _add_entry_for_product(self, product_id):
        """[+] adiciona mais uma unidade (nova entrada com timestamp)."""
        self.orders_controller.add_item_to_order(self.order['id'], product_id, 1)
        self.load_items()

    def add_item(self):
        """Botão '+ Adicionar': adiciona o produto selecionado no combo."""
        product_id = self.product_combo.currentData()
        if product_id is None:
            return
        self.orders_controller.add_item_to_order(self.order['id'], product_id, 1)
        self.product_search.clear()
        self.load_items()

    def _save_phone(self):
        phone = self.phone_input.text().strip()
        self.orders_controller.update_order_phone(self.order['id'], phone)
        self.order['phone'] = phone

    # ── WHATSAPP ──────────────────────────────────────────────────────

    def _settings_path(self):
        data_dir = Path(self.orders_controller.data_loader.data_dir)
        return data_dir / "settings.json"

    def _load_pix_key(self):
        try:
            path = self._settings_path()
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f).get('pix_key', 'pix@examplo.com')
        except Exception:
            pass
        return 'pix@examplo.com'

    def _save_pix_key(self, key):
        try:
            path = self._settings_path()
            settings = {}
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            settings['pix_key'] = key
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False)
        except Exception:
            pass

    def _formatar_numero(self, numero):
        digits = re.sub(r'\D', '', numero)
        if not digits.startswith('55'):
            digits = '55' + digits
        return digits

    def _gerar_mensagem(self, groups, nome, order_id, pix_key):
        total = sum(g['subtotal'] for g in groups)
        linhas = [f"Ola, {nome}!", "", f"Segue sua comanda #{order_id}:", ""]
        for g in groups:
            linhas.append(f"- {g['quantity']}x {g['product_name']} - R$ {g['subtotal']:.2f}")
        linhas += [
            "",
            f"*Total: R$ {total:.2f}*",
            "",
            "Pagamento via Pix:",
            pix_key,
            "",
            "Obrigado pela preferencia!",
        ]
        return "\n".join(linhas)

    def _enviar_whatsapp(self):
        items = self.orders_controller.get_order_items(self.order['id'])
        if not items:
            QMessageBox.warning(self, "Aviso", "A comanda não possui itens.")
            return

        groups = {}
        for item in items:
            pid = item['product_id']
            if pid not in groups:
                groups[pid] = {'product_name': item['product_name'], 'quantity': 0, 'subtotal': 0.0}
            groups[pid]['quantity'] += item['quantity']
            groups[pid]['subtotal'] += item['subtotal']
        grouped = list(groups.values())

        phone_atual = self.phone_input.text().strip()
        dialog = WhatsAppDialog(self, self.order['customer_name'], phone_atual, self._load_pix_key())
        if dialog.exec() != QDialog.Accepted:
            return

        numero = self._formatar_numero(dialog.get_numero())
        pix_key = dialog.get_pix_key()

        if len(numero) < 12:
            QMessageBox.warning(self, "Número inválido",
                                "Informe DDD + número.\nEx: (11) 99999-9999")
            return

        # Salva número na comanda e PIX key nas configurações
        self.phone_input.setText(dialog.get_numero())
        self._save_phone()
        self._save_pix_key(pix_key)

        mensagem = self._gerar_mensagem(grouped, self.order['customer_name'], self.order['id'], pix_key)
        url = f"https://wa.me/{numero}?text={urllib.parse.quote(mensagem, safe='')}"
        webbrowser.open(url)

    def close_this_order(self):
        items = self.orders_controller.get_order_items(self.order['id'])
        if len(items) == 0:
            QMessageBox.warning(self, "Aviso", "A comanda não possui itens.\nAdicione pelo menos um item antes de fechar.")
            return
        reply = show_question_message(
            self, 'Confirmação',
            'Fechar esta comanda?\n\nOs itens serão descontados do estoque automaticamente.'
        )
        if reply == QMessageBox.Yes:
            self.orders_controller.close_order(self.order['id'])
            self.accept()


# ─── HISTÓRICO DE ITENS ───────────────────────────────────────────────────────

class ItemHistoryDialog(QDialog):
    """Mostra cada adição individual de um produto na comanda, com data/hora."""

    def __init__(self, parent, group, orders_controller, order):
        super().__init__(parent)
        self.group = group
        self.orders_controller = orders_controller
        self.order = order
        self.setWindowTitle(f"Histórico — {group['product_name']}")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel(f"Histórico de adições: {self.group['product_name']}")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50;")
        title.setWordWrap(True)
        layout.addWidget(title)

        cols = 3 if self.order['status'] == 'aberta' else 2
        self.hist_table = QTableWidget()
        self.hist_table.setColumnCount(cols)
        headers = ["Adicionado em", "Quantidade"]
        if self.order['status'] == 'aberta':
            headers.append("Ações")
        self.hist_table.setHorizontalHeaderLabels(headers)
        self.hist_table.setStyleSheet("""
            QTableWidget { background-color: white; border: none; font-size: 13px; }
            QHeaderView::section {
                background-color: #34495e; color: white; padding: 8px;
                font-weight: bold; border: none;
            }
            QTableWidget::item { color: #2c3e50; padding: 6px; }
        """)
        h = self.hist_table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Stretch)
        h.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        if cols == 3:
            h.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.hist_table.verticalHeader().setVisible(False)
        self.hist_table.verticalHeader().setDefaultSectionSize(40)
        layout.addWidget(self.hist_table)

        self._load_entries()

        btn_close = QPushButton("Fechar")
        btn_close.setFixedHeight(38)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6; color: white;
                padding: 8px 20px; border-radius: 4px;
                font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #7f8c8d; }
        """)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignRight)

    def _load_entries(self):
        import pandas as pd
        entries = self.group['entries']
        cols = 3 if self.order['status'] == 'aberta' else 2
        self.hist_table.setRowCount(len(entries))

        for row, entry in enumerate(entries):
            try:
                added = pd.to_datetime(entry.get('added_at'))
                added_str = added.strftime('%d/%m/%Y %H:%M') if not pd.isna(added) else '-'
            except Exception:
                added_str = '-'

            self.hist_table.setItem(row, 0, QTableWidgetItem(added_str))

            qty_item = QTableWidgetItem(str(entry['quantity']))
            qty_item.setTextAlignment(Qt.AlignCenter)
            self.hist_table.setItem(row, 1, qty_item)

            if cols == 3:
                btn_remove = QPushButton("Remover")
                btn_remove.setFixedHeight(30)
                btn_remove.setCursor(Qt.PointingHandCursor)
                btn_remove.setStyleSheet("""
                    QPushButton {
                        background-color: #e74c3c; color: white;
                        padding: 4px 10px; border-radius: 3px;
                        font-size: 12px; font-weight: bold;
                    }
                    QPushButton:hover { background-color: #c0392b; }
                """)
                btn_remove.clicked.connect(partial(self._remove_entry, entry['id']))
                cell = QWidget()
                cell_layout = QHBoxLayout(cell)
                cell_layout.setContentsMargins(4, 4, 4, 4)
                cell_layout.setAlignment(Qt.AlignCenter)
                cell_layout.addWidget(btn_remove)
                self.hist_table.setCellWidget(row, 2, cell)

    def _remove_entry(self, item_id):
        """Remove uma entrada específica e recarrega o histórico."""
        self.orders_controller.remove_item_from_order(item_id)
        # Recarregar entradas do grupo
        all_items = self.orders_controller.get_order_items(self.order['id'])
        product_entries = [i for i in all_items if i['product_id'] == self.group['product_id']]
        self.group['entries'] = product_entries
        self.group['quantity'] = sum(e['quantity'] for e in product_entries)
        self._load_entries()
        if not product_entries:
            self.accept()


# ─── WHATSAPP DIALOG ──────────────────────────────────────────────────────────

class WhatsAppDialog(QDialog):
    def __init__(self, parent, customer_name, phone_default='', pix_key_default=''):
        super().__init__(parent)
        self.setWindowTitle("Cobrar via WhatsApp")
        self.setModal(True)
        self.setMinimumWidth(420)
        self.setup_ui(customer_name, phone_default, pix_key_default)

    def setup_ui(self, customer_name, phone_default, pix_key_default):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        self.setStyleSheet("background-color: #ecf0f1;")

        title = QLabel("Cobrar via WhatsApp")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        client_label = QLabel(f"Cliente: {customer_name}")
        client_label.setStyleSheet("font-size: 13px; color: #7f8c8d;")
        layout.addWidget(client_label)

        input_style = """
            QLineEdit {
                padding: 10px; font-size: 14px;
                border: 2px solid #bdc3c7; border-radius: 5px;
                background-color: white; color: #2c3e50;
            }
            QLineEdit:focus { border: 2px solid #25d366; }
        """
        label_style = "font-size: 14px; font-weight: bold; color: #2c3e50;"

        phone_label = QLabel("Número do WhatsApp:")
        phone_label.setStyleSheet(label_style)
        layout.addWidget(phone_label)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Ex: (11) 99999-9999")
        self.phone_input.setText(phone_default)
        self.phone_input.setStyleSheet(input_style)
        layout.addWidget(self.phone_input)

        pix_label = QLabel("Chave Pix:")
        pix_label.setStyleSheet(label_style)
        layout.addWidget(pix_label)

        self.pix_input = QLineEdit()
        self.pix_input.setPlaceholderText("Ex: seu@email.com ou CPF")
        self.pix_input.setText(pix_key_default)
        self.pix_input.setStyleSheet(input_style)
        layout.addWidget(self.pix_input)

        buttons = QHBoxLayout()

        btn_send = QPushButton("Abrir WhatsApp")
        btn_send.setFixedHeight(42)
        btn_send.setCursor(Qt.PointingHandCursor)
        btn_send.setStyleSheet("""
            QPushButton {
                background-color: #25d366; color: white;
                padding: 10px 25px; border-radius: 5px;
                font-size: 15px; font-weight: bold;
            }
            QPushButton:hover { background-color: #1ebe57; }
        """)
        btn_send.clicked.connect(self.accept)
        buttons.addWidget(btn_send)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setFixedHeight(42)
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6; color: white;
                padding: 10px 25px; border-radius: 5px;
                font-size: 15px; font-weight: bold;
            }
            QPushButton:hover { background-color: #7f8c8d; }
        """)
        btn_cancel.clicked.connect(self.reject)
        buttons.addWidget(btn_cancel)

        layout.addLayout(buttons)

    def get_numero(self):
        return self.phone_input.text()

    def get_pix_key(self):
        return self.pix_input.text()
