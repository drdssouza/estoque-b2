from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QTableWidget, QTableWidgetItem, QLineEdit,
                               QDialog, QFormLayout, QDoubleSpinBox, QSpinBox,
                               QComboBox, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from desktop.controllers.products_controller import ProductsController
from functools import partial

def show_success_message(parent, title, message):
    """Mostra mensagem de sucesso com estilo personalizado"""
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setStyleSheet("""
        QMessageBox {
            background-color: #ecf0f1;
        }
        QMessageBox QLabel {
            color: #2c3e50;
            font-size: 14px;
            font-weight: bold;
            min-width: 300px;
        }
        QPushButton {
            background-color: #27ae60;
            color: white;
            padding: 8px 20px;
            border-radius: 4px;
            font-size: 13px;
            font-weight: bold;
            min-width: 80px;
        }
        QPushButton:hover {
            background-color: #229954;
        }
    """)
    msg.exec()

def show_question_message(parent, title, message):
    """Mostra mensagem de confirmação com estilo personalizado"""
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Question)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msg.setStyleSheet("""
        QMessageBox {
            background-color: #ecf0f1;
        }
        QMessageBox QLabel {
            color: #2c3e50;
            font-size: 14px;
            font-weight: bold;
            min-width: 300px;
        }
        QPushButton {
            background-color: #3498db;
            color: white;
            padding: 8px 20px;
            border-radius: 4px;
            font-size: 13px;
            font-weight: bold;
            min-width: 80px;
        }
        QPushButton:hover {
            background-color: #2980b9;
        }
    """)
    return msg.exec()

class ProductsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.controller = ProductsController()
        self.controller.products_updated.connect(self.load_products)
        self.setup_ui()
        self.load_products()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Cor de fundo
        self.setStyleSheet("background-color: #ecf0f1;")
        
        header_layout = QHBoxLayout()
        
        title = QLabel("Gestão de Produtos")
        title.setStyleSheet("font-size: 32px; font-weight: bold; color: #2c3e50; background-color: transparent;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        btn_add = QPushButton("+ Adicionar Produto")
        btn_add.setStyleSheet("""
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
        btn_add.clicked.connect(self.show_add_product_dialog)
        header_layout.addWidget(btn_add)
        
        layout.addLayout(header_layout)
        
        # Layout de busca e filtros
        filters_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar produto por nome...")
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
        self.search_input.textChanged.connect(self.apply_filters)
        filters_layout.addWidget(self.search_input, 3)
        
        self.category_filter = QComboBox()
        self.category_filter.addItems(["Todas", "bebida", "doce", "salgado", "acessório"])
        self.category_filter.setStyleSheet("""
            QComboBox {
                padding: 10px;
                font-size: 14px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background-color: white;
                color: #2c3e50;
            }
        """)
        self.category_filter.currentTextChanged.connect(self.apply_filters)
        filters_layout.addWidget(self.category_filter, 1)
        
        # Botões de ordenação
        btn_sort_asc = QPushButton("↑ Menor Estoque")
        btn_sort_asc.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-size: 14px;
                padding: 10px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        btn_sort_asc.clicked.connect(self.sort_by_stock_asc)
        filters_layout.addWidget(btn_sort_asc, 1)
        
        btn_sort_desc = QPushButton("↓ Maior Estoque")
        btn_sort_desc.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                font-size: 14px;
                padding: 10px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        btn_sort_desc.clicked.connect(self.sort_by_stock_desc)
        filters_layout.addWidget(btn_sort_desc, 1)
        
        layout.addLayout(filters_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Nome", "Categoria", "Preço Compra", "Preço Venda", 
            "Estoque Mínimo", "Estoque Atual", "Ações"
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
        self.table.setColumnWidth(0, 50)   # ID
        self.table.setColumnWidth(1, 200)  # Nome
        self.table.setColumnWidth(2, 100)  # Categoria
        self.table.setColumnWidth(3, 120)  # Preço Compra
        self.table.setColumnWidth(4, 120)  # Preço Venda
        self.table.setColumnWidth(5, 130)  # Estoque Mínimo
        self.table.setColumnWidth(6, 130)  # Estoque Atual
        self.table.setColumnWidth(7, 220)  # Ações (botões)
        layout.addWidget(self.table)
    
    def load_products(self):
    # Resetar ordenação ao recarregar
        if hasattr(self, 'current_sort'):
            delattr(self, 'current_sort')
        
        products = self.controller.get_all_products()
        
        # Filtrar apenas produtos ativos
        active_products = [p for p in products if p['active']]
        
        self.display_products(active_products)
        
        for row, product in enumerate(active_products):
            self.table.setRowHeight(row, 50)
            self.table.setItem(row, 0, QTableWidgetItem(str(product['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(product['name']))
            self.table.setItem(row, 2, QTableWidgetItem(product['category']))
            self.table.setItem(row, 3, QTableWidgetItem(f"R$ {product['purchase_price']:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"R$ {product['sale_price']:.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(str(product['minimum_stock'])))
            self.table.setItem(row, 6, QTableWidgetItem(str(product['current_stock'])))
            
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 0, 5, 0)
            
            btn_edit = QPushButton("Editar")
            btn_edit.setStyleSheet("""
                background-color: #3498db; 
                color: white; 
                padding: 5px 8px; /* Mantive o padding sugerido na resposta anterior */
                font-size: 14px; /* <--- NOVO: Aumenta a fonte */
                font-weight: bold; /* <--- NOVO: Deixa em negrito */
                border-radius: 4px; 
            """)
            btn_edit.clicked.connect(partial(self.show_edit_product_dialog, product))
            actions_layout.addWidget(btn_edit)
            
            btn_delete = QPushButton("Desativar")
            btn_delete.setStyleSheet("""
                background-color: #e74c3c; 
                color: white; 
                padding: 5px 8px; /* Mantive o padding sugerido na resposta anterior */
                font-size: 14px; /* <--- NOVO: Aumenta a fonte */
                font-weight: bold; /* <--- NOVO: Deixa em negrito */
                border-radius: 4px;
            """)
            btn_delete.clicked.connect(partial(self.deactivate_product, product['id']))
            actions_layout.addWidget(btn_delete)
            
            self.table.setCellWidget(row, 7, actions_widget)
    
    def search_products(self):
        query = self.search_input.text()
        category = self.category_filter.currentText()
        category = None if category == "Todas" else category
        
        products = self.controller.search_products(query, category)
        
        # Filtrar apenas produtos ativos
        active_products = [p for p in products if p['active']]
        self.table.setRowCount(len(active_products))
        
        for row, product in enumerate(active_products):
            self.table.setRowHeight(row, 50)
            self.table.setItem(row, 0, QTableWidgetItem(str(product['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(product['name']))
            self.table.setItem(row, 2, QTableWidgetItem(product['category']))
            self.table.setItem(row, 3, QTableWidgetItem(f"R$ {product['purchase_price']:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"R$ {product['sale_price']:.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(str(product['minimum_stock'])))
            self.table.setItem(row, 6, QTableWidgetItem(str(product['current_stock'])))
            
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 0, 5, 0)
            
            btn_edit = QPushButton("Editar")
            btn_edit.setStyleSheet("background-color: #3498db; color: white; padding: 5px;")
            btn_edit.clicked.connect(partial(self.show_edit_product_dialog, product))
            actions_layout.addWidget(btn_edit)
            
            btn_delete = QPushButton("Desativar")
            btn_delete.setStyleSheet("background-color: #e74c3c; color: white; padding: 5px;")
            btn_delete.clicked.connect(partial(self.deactivate_product, product['id']))
            actions_layout.addWidget(btn_delete)
            
            self.table.setCellWidget(row, 7, actions_widget)

    def sort_by_stock_asc(self):
        """Ordena produtos por estoque crescente (menor para maior)"""
        self.current_sort = 'asc'
        self.apply_filters()

    def sort_by_stock_desc(self):
        """Ordena produtos por estoque decrescente (maior para menor)"""
        self.current_sort = 'desc'
        self.apply_filters()

    def apply_filters(self):
        """Aplica busca, categoria e ordenação"""
        query = self.search_input.text()
        category = self.category_filter.currentText()
        category = None if category == "Todas" else category
        
        products = self.controller.search_products(query, category)
        
        # Filtrar apenas produtos ativos
        active_products = [p for p in products if p['active']]
        
        # Aplicar ordenação se houver
        if hasattr(self, 'current_sort'):
            if self.current_sort == 'asc':
                active_products.sort(key=lambda x: x['current_stock'])
            elif self.current_sort == 'desc':
                active_products.sort(key=lambda x: x['current_stock'], reverse=True)
        
        self.display_products(active_products)

    def display_products(self, products):
        """Exibe produtos na tabela"""
        self.table.setRowCount(len(products))
        
        # Definir altura padrão das linhas
        self.table.verticalHeader().setDefaultSectionSize(50)
        
        for row, product in enumerate(products):
            # Centralizar o conteúdo das células
            item_id = QTableWidgetItem(str(product['id']))
            item_id.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, item_id)
            
            self.table.setItem(row, 1, QTableWidgetItem(product['name']))
            
            item_cat = QTableWidgetItem(product['category'])
            item_cat.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, item_cat)
            
            item_purchase = QTableWidgetItem(f"R$ {product['purchase_price']:.2f}")
            item_purchase.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, item_purchase)
            
            item_sale = QTableWidgetItem(f"R$ {product['sale_price']:.2f}")
            item_sale.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, item_sale)
            
            item_min = QTableWidgetItem(str(product['minimum_stock']))
            item_min.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, item_min)
            
            # Destacar estoque atual com cores
            item_current = QTableWidgetItem(str(product['current_stock']))
            item_current.setTextAlignment(Qt.AlignCenter)
            
            # Colorir baseado no estoque
            if product['current_stock'] <= product['minimum_stock'] * 0.5:
                item_current.setForeground(Qt.red)
                font = item_current.font()
                font.setBold(True)
                item_current.setFont(font)
            elif product['current_stock'] <= product['minimum_stock']:
                item_current.setForeground(Qt.darkYellow)
                font = item_current.font()
                font.setBold(True)
                item_current.setFont(font)
            
            self.table.setItem(row, 6, item_current)
            
            # Widget para os botões de ação
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 5, 5, 5)
            actions_layout.setSpacing(8)
            
            btn_edit = QPushButton("Editar")
            btn_edit.setMinimumWidth(85)
            btn_edit.setMinimumHeight(35)
            btn_edit.setCursor(Qt.PointingHandCursor)
            btn_edit.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    padding: 8px 12px;
                    border-radius: 4px;
                    font-size: 13px;
                    font-weight: bold;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #21618c;
                }
            """)
            btn_edit.clicked.connect(partial(self.show_edit_product_dialog, product))
            actions_layout.addWidget(btn_edit)
            
            btn_delete = QPushButton("Desativar")
            btn_delete.setMinimumWidth(85)
            btn_delete.setMinimumHeight(35)
            btn_delete.setCursor(Qt.PointingHandCursor)
            btn_delete.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    padding: 8px 12px;
                    border-radius: 4px;
                    font-size: 13px;
                    font-weight: bold;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
                QPushButton:pressed {
                    background-color: #a93226;
                }
            """)
            btn_delete.clicked.connect(partial(self.deactivate_product, product['id']))
            actions_layout.addWidget(btn_delete)
            
            actions_layout.addStretch()
            
            self.table.setCellWidget(row, 7, actions_widget)

    def show_add_product_dialog(self):
        dialog = ProductDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            self.controller.add_product(**data)
    
    def show_edit_product_dialog(self, product):
        dialog = ProductDialog(self, product)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            self.controller.update_product(product['id'], **data)
    
    def deactivate_product(self, product_id):
        result = show_question_message(
            self, 
            'Confirmação', 
            'Deseja realmente desativar este produto?'
        )
        if result == QMessageBox.Yes:
            self.controller.deactivate_product(product_id)
            show_success_message(self, "Sucesso", "Produto desativado com sucesso!")

class ProductDialog(QDialog):
    def __init__(self, parent=None, product=None):
        super().__init__(parent)
        self.product = product
        self.setWindowTitle("Adicionar Produto" if not product else "Editar Produto")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(550)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Fundo da janela
        self.setStyleSheet("""
            QDialog {
                background-color: #ecf0f1;
            }
        """)
        
        # Título grande
        title_text = "➕ ADICIONAR NOVO PRODUTO" if not self.product else "✏️ EDITAR PRODUTO"
        title = QLabel(title_text)
        title.setStyleSheet("""
            color: #2c3e50;
            font-size: 22px;
            font-weight: bold;
            padding: 15px;
            background-color: white;
            border-radius: 8px;
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Container para os campos
        form_container = QWidget()
        form_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        form_layout = QFormLayout(form_container)
        form_layout.setSpacing(20)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # Estilo para labels (textos à esquerda)
        label_style = """
            color: #2c3e50;
            font-size: 15px;
            font-weight: bold;
            padding-right: 15px;
        """
        
        # Estilo para inputs
        input_style = """
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                padding: 12px;
                font-size: 15px;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                background-color: #ffffff;
                color: #2c3e50;
                font-weight: bold;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border: 2px solid #3498db;
                background-color: #f0f8ff;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
        """
        
        # Nome do Produto
        name_label = QLabel("Nome do Produto:")
        name_label.setStyleSheet(label_style)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ex: Coca-Cola 350ml, Água Mineral 500ml...")
        self.name_input.setStyleSheet(input_style)
        self.name_input.setMinimumHeight(45)
        
        form_layout.addRow(name_label, self.name_input)
        
        # Categoria
        category_label = QLabel("Categoria:")
        category_label.setStyleSheet(label_style)
        
        self.category_input = QComboBox()
        self.category_input.addItems(["bebida", "doce", "salgado", "acessório"])
        self.category_input.setStyleSheet(input_style)
        self.category_input.setMinimumHeight(45)
        
        form_layout.addRow(category_label, self.category_input)
        
        # Preço de Compra
        purchase_label = QLabel("Preço de Compra:")
        purchase_label.setStyleSheet(label_style)
        
        self.purchase_price_input = QDoubleSpinBox()
        self.purchase_price_input.setPrefix("R$ ")
        self.purchase_price_input.setMaximum(10000)
        self.purchase_price_input.setDecimals(2)
        self.purchase_price_input.setStyleSheet(input_style)
        self.purchase_price_input.setMinimumHeight(45)
        
        form_layout.addRow(purchase_label, self.purchase_price_input)
        
        # Preço de Venda
        sale_label = QLabel("Preço de Venda:")
        sale_label.setStyleSheet(label_style)
        
        self.sale_price_input = QDoubleSpinBox()
        self.sale_price_input.setPrefix("R$ ")
        self.sale_price_input.setMaximum(10000)
        self.sale_price_input.setDecimals(2)
        self.sale_price_input.setStyleSheet(input_style)
        self.sale_price_input.setMinimumHeight(45)
        
        form_layout.addRow(sale_label, self.sale_price_input)
        
        # Estoque Mínimo
        min_label = QLabel("Estoque Mínimo:")
        min_label.setStyleSheet(label_style)
        
        self.minimum_stock_input = QSpinBox()
        self.minimum_stock_input.setMaximum(10000)
        self.minimum_stock_input.setSuffix(" unidades")
        self.minimum_stock_input.setStyleSheet(input_style)
        self.minimum_stock_input.setMinimumHeight(45)
        
        form_layout.addRow(min_label, self.minimum_stock_input)
        
        # Estoque Atual
        current_label = QLabel("Estoque Atual:")
        current_label.setStyleSheet(label_style)
        
        self.current_stock_input = QSpinBox()
        self.current_stock_input.setMaximum(10000)
        self.current_stock_input.setSuffix(" unidades")
        self.current_stock_input.setStyleSheet(input_style)
        self.current_stock_input.setMinimumHeight(45)
        
        form_layout.addRow(current_label, self.current_stock_input)
        
        layout.addWidget(form_container)
        
        # Se estiver editando, preencher os campos
        if self.product:
            self.name_input.setText(self.product['name'])
            self.category_input.setCurrentText(self.product['category'])
            self.purchase_price_input.setValue(self.product['purchase_price'])
            self.sale_price_input.setValue(self.product['sale_price'])
            self.minimum_stock_input.setValue(self.product['minimum_stock'])
            self.current_stock_input.setValue(self.product['current_stock'])
        
        # Botões
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        
        btn_save = QPushButton("✓ Salvar Produto")
        btn_save.setFixedHeight(50)
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 12px 40px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        btn_save.clicked.connect(self.accept)
        
        btn_cancel = QPushButton("✗ Cancelar")
        btn_cancel.setFixedHeight(50)
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 12px 40px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
            QPushButton:pressed {
                background-color: #6c7a7b;
            }
        """)
        btn_cancel.clicked.connect(self.reject)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(btn_save)
        buttons_layout.addWidget(btn_cancel)
        
        layout.addLayout(buttons_layout)
    
    def get_data(self):
        return {
            'name': self.name_input.text(),
            'category': self.category_input.currentText(),
            'purchase_price': self.purchase_price_input.value(),
            'sale_price': self.sale_price_input.value(),
            'minimum_stock': self.minimum_stock_input.value(),
            'current_stock': self.current_stock_input.value()
        }