from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QTableWidget, QTableWidgetItem, QFrame,
                               QComboBox, QFileDialog, QMessageBox, QScrollArea)
from PySide6.QtCore import Qt
from desktop.controllers.reports_controller import ReportsController
from datetime import datetime, date


class ReportsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.controller = ReportsController()
        self.current_date = date.today()
        self.setup_ui()

    def setup_ui(self):
        # Layout raiz da tela
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.setStyleSheet("background-color: #ecf0f1;")

        # ── ScrollArea para todo o conteúdo ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: #ecf0f1; border: none; }")

        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background-color: #ecf0f1;")
        layout = QVBoxLayout(scroll_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(18)

        scroll.setWidget(scroll_widget)
        root_layout.addWidget(scroll)

        # ── Header ──
        header_layout = QHBoxLayout()

        title = QLabel("Relatório do Dia")
        title.setStyleSheet("font-size: 32px; font-weight: bold; color: #2c3e50; background-color: transparent;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        btn_excel = QPushButton("📄 Exportar Excel")
        btn_excel.setFixedHeight(42)
        btn_excel.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; color: white;
                font-size: 15px; padding: 0 20px;
                border-radius: 5px; font-weight: bold;
            }
            QPushButton:hover { background-color: #229954; }
        """)
        btn_excel.clicked.connect(self.export_excel)
        header_layout.addWidget(btn_excel)

        layout.addLayout(header_layout)

        # ── Seletor de data ──
        date_layout = QHBoxLayout()

        date_label = QLabel("Data:")
        date_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #2c3e50;")
        date_layout.addWidget(date_label)

        self.date_combo = QComboBox()
        self.date_combo.setFixedHeight(36)
        self.date_combo.setStyleSheet("""
            QComboBox {
                padding: 0 12px;
                font-size: 14px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background-color: white;
                color: #2c3e50;
                min-width: 200px;
            }
        """)
        self.date_combo.currentIndexChanged.connect(self.on_date_changed)
        date_layout.addWidget(self.date_combo)

        date_layout.addStretch()
        layout.addLayout(date_layout)

        # ── Cards de resumo ──
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)

        self.card_orders = self._create_summary_card("Comandas Fechadas", "0", "#3498db")
        self.card_revenue = self._create_summary_card("Receita Total", "R$ 0,00", "#27ae60")
        self.card_items = self._create_summary_card("Itens Vendidos", "0", "#9b59b6")

        cards_layout.addWidget(self.card_orders)
        cards_layout.addWidget(self.card_revenue)
        cards_layout.addWidget(self.card_items)

        layout.addLayout(cards_layout)

        # ── Tabela: Vendas por Categoria ──
        layout.addWidget(self._create_table_section(
            "📦 Vendas por Categoria",
            ["Categoria", "Quantidade", "Receita"],
            [160, 120, 120],
            self, "category_table"
        ))

        # ── Tabela: Vendas por Produto ──
        layout.addWidget(self._create_table_section(
            "🏷️ Vendas por Produto",
            ["Produto", "Categoria", "Quantidade", "Receita"],
            [240, 140, 110, 120],
            self, "product_table"
        ))

        # ── Tabela: Comandas fechadas ──
        layout.addWidget(self._create_table_section(
            "🧾 Comandas Fechadas",
            ["ID", "Cliente", "Horário", "Total"],
            [60, 220, 120, 120],
            self, "orders_table"
        ))

    # ── HELPERS ──────────────────────────────────────────────────────

    def _create_summary_card(self, title, value, color):
        card = QFrame()
        card.setFixedHeight(90)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 10px;
            }}
        """)
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(20, 0, 20, 0)
        card_layout.setSpacing(20)

        # Lado esquerdo: título
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: rgba(255,255,255,0.85); font-size: 13px; background-color: transparent;")
        text_layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setStyleSheet("color: white; font-size: 28px; font-weight: bold; background-color: transparent;")
        value_label.setObjectName("value_label")
        text_layout.addWidget(value_label)

        card_layout.addLayout(text_layout)
        card_layout.addStretch()

        return card

    def _create_table_section(self, section_title, headers, col_widths, owner, attr_name):
        """Cria um QFrame com título e tabela, e atribui a tabela em self.<attr_name>."""
        frame = QFrame()
        frame.setStyleSheet("background-color: white; border-radius: 10px; padding: 18px;")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setSpacing(10)
        frame_layout.setContentsMargins(18, 14, 18, 14)

        title_label = QLabel(section_title)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        frame_layout.addWidget(title_label)

        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: none;
                font-size: 14px;
                color: #2c3e50;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: none;
                font-size: 13px;
            }
            QTableWidget::item {
                color: #2c3e50;
                padding: 6px 8px;
            }
        """)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(38)
        table.horizontalHeader().setStretchLastSection(True)

        for i, w in enumerate(col_widths):
            table.setColumnWidth(i, w)

        frame_layout.addWidget(table)

        # Guardar referência na instância
        setattr(owner, attr_name, table)

        return frame

    # ── DATA ─────────────────────────────────────────────────────────

    def load_report(self):
        self._populate_date_combo()
        self._load_report_for_date(self.current_date)

    def _populate_date_combo(self):
        self.date_combo.blockSignals(True)
        self.date_combo.clear()

        available_dates = self.controller.get_available_dates()

        today = date.today()
        if today not in available_dates:
            available_dates.insert(0, today)

        for d in available_dates:
            label = d.strftime("%d/%m/%Y")
            if d == today:
                label += " (hoje)"
            self.date_combo.addItem(label, d)

        for i in range(self.date_combo.count()):
            if self.date_combo.itemData(i) == today:
                self.date_combo.setCurrentIndex(i)
                break

        self.date_combo.blockSignals(False)

    def on_date_changed(self, index):
        selected_date = self.date_combo.itemData(index)
        if selected_date:
            self.current_date = selected_date
            self._load_report_for_date(selected_date)

    def _load_report_for_date(self, report_date):
        data = self.controller.get_daily_report(report_date)

        # ── Cards ──
        self.card_orders.findChild(QLabel, "value_label").setText(str(data['total_orders']))
        self.card_revenue.findChild(QLabel, "value_label").setText(f"R$ {data['total_revenue']:.2f}")

        total_items = sum(item['quantity'] for item in data['by_product']) if data['by_product'] else 0
        self.card_items.findChild(QLabel, "value_label").setText(str(total_items))

        # ── Tabela por categoria ──
        categories = data['by_category']
        self.category_table.setRowCount(len(categories))
        for row, (cat, info) in enumerate(categories.items()):
            self.category_table.setItem(row, 0, QTableWidgetItem(cat.capitalize()))

            qty = QTableWidgetItem(str(info['quantity']))
            qty.setTextAlignment(Qt.AlignCenter)
            self.category_table.setItem(row, 1, qty)

            rev = QTableWidgetItem(f"R$ {info['revenue']:.2f}")
            rev.setTextAlignment(Qt.AlignCenter)
            self.category_table.setItem(row, 2, rev)

        # ── Tabela por produto ──
        products = data['by_product']
        self.product_table.setRowCount(len(products))
        for row, p in enumerate(products):
            self.product_table.setItem(row, 0, QTableWidgetItem(p['product_name']))

            cat = QTableWidgetItem(p['category'].capitalize())
            cat.setTextAlignment(Qt.AlignCenter)
            self.product_table.setItem(row, 1, cat)

            qty = QTableWidgetItem(str(p['quantity']))
            qty.setTextAlignment(Qt.AlignCenter)
            self.product_table.setItem(row, 2, qty)

            rev = QTableWidgetItem(f"R$ {p['revenue']:.2f}")
            rev.setTextAlignment(Qt.AlignCenter)
            self.product_table.setItem(row, 3, rev)

        # ── Tabela de comandas ──
        orders = data['order_list']
        self.orders_table.setRowCount(len(orders))
        for row, order in enumerate(orders):
            id_item = QTableWidgetItem(str(order['id']))
            id_item.setTextAlignment(Qt.AlignCenter)
            self.orders_table.setItem(row, 0, id_item)

            self.orders_table.setItem(row, 1, QTableWidgetItem(order['customer_name']))

            time_item = QTableWidgetItem(order['created_at'])
            time_item.setTextAlignment(Qt.AlignCenter)
            self.orders_table.setItem(row, 2, time_item)

            total_item = QTableWidgetItem(f"R$ {order['total']:.2f}")
            total_item.setTextAlignment(Qt.AlignCenter)
            self.orders_table.setItem(row, 3, total_item)

    # ── EXPORT ───────────────────────────────────────────────────────

    def export_excel(self):
        try:
            import openpyxl
        except ImportError:
            QMessageBox.warning(self, "Erro", "openpyxl não instalado.\nExecute: pip install openpyxl")
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Salvar Relatório",
            f"relatorio_{self.current_date.strftime('%Y-%m-%d')}.xlsx",
            "Excel (*.xlsx)"
        )
        if not filepath:
            return

        data = self.controller.get_daily_report(self.current_date)

        wb = openpyxl.Workbook()

        # Sheet 1: Resumo
        ws = wb.active
        ws.title = "Resumo"
        ws.append([f"Relatório do Dia - {self.current_date.strftime('%d/%m/%Y')}"])
        ws.append([])
        ws.append(["Comandas Fechadas", data['total_orders']])
        ws.append(["Receita Total", data['total_revenue']])
        total_items = sum(item['quantity'] for item in data['by_product']) if data['by_product'] else 0
        ws.append(["Itens Vendidos", total_items])

        # Sheet 2: Por Categoria
        ws_cat = wb.create_sheet("Por Categoria")
        ws_cat.append(["Categoria", "Quantidade", "Receita"])
        for cat, info in data['by_category'].items():
            ws_cat.append([cat.capitalize(), info['quantity'], info['revenue']])

        # Sheet 3: Por Produto
        ws_prod = wb.create_sheet("Por Produto")
        ws_prod.append(["Produto", "Categoria", "Quantidade", "Receita"])
        for p in data['by_product']:
            ws_prod.append([p['product_name'], p['category'].capitalize(), p['quantity'], p['revenue']])

        # Sheet 4: Comandas
        ws_orders = wb.create_sheet("Comandas")
        ws_orders.append(["ID", "Cliente", "Horário", "Total"])
        for order in data['order_list']:
            ws_orders.append([order['id'], order['customer_name'], order['created_at'], order['total']])

        wb.save(filepath)
        QMessageBox.information(self, "Sucesso", f"Relatório exportado:\n{filepath}")