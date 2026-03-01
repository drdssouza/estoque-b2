from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QStackedWidget, QFrame,
                               QFileDialog, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from desktop.ui.dashboard_window import DashboardWindow
from desktop.ui.products_window import ProductsWindow
from desktop.ui.movements_window import MovementsWindow
from desktop.ui.order_window import OrdersWindow
from desktop.ui.reports_window import ReportsWindow
from desktop.controllers.backup_controller import BackupController

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arena B2 - Controle de Estoque")
        self.setGeometry(100, 100, 1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar)
        
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget, 1)
        
        # Índices no stacked_widget:
        # 0 - Dashboard
        # 1 - Produtos
        # 2 - Movimentações
        # 3 - Comandas
        # 4 - Relatórios
        
        self.dashboard_window = DashboardWindow()
        self.products_window = ProductsWindow()
        self.movements_window = MovementsWindow()
        self.orders_window = OrdersWindow()
        self.reports_window = ReportsWindow()
        
        self.stacked_widget.addWidget(self.dashboard_window)   # 0
        self.stacked_widget.addWidget(self.products_window)    # 1
        self.stacked_widget.addWidget(self.movements_window)   # 2
        self.stacked_widget.addWidget(self.orders_window)      # 3
        self.stacked_widget.addWidget(self.reports_window)     # 4
        
        # Conectar sinais para atualizar dashboard quando houver mudanças
        self.products_window.controller.products_updated.connect(self.dashboard_window.load_data)
        self.movements_window.movements_controller.movements_updated.connect(self.dashboard_window.load_data)
        
        # Atualizar produtos quando houver movimentações
        self.movements_window.movements_controller.movements_updated.connect(self.products_window.load_products)
        
        # Atualizar dashboard quando houver comandas fechadas (gera movimentações)
        self.orders_window.orders_controller.orders_updated.connect(self.dashboard_window.load_data)
        self.orders_window.orders_controller.orders_updated.connect(self.products_window.load_products)
        self.orders_window.orders_controller.orders_updated.connect(self.movements_window.load_movements)

        # Badge de estoque baixo no botão Dashboard
        self.products_window.controller.products_updated.connect(self._update_stock_badge)
        self.movements_window.movements_controller.movements_updated.connect(self._update_stock_badge)
        self.orders_window.orders_controller.orders_updated.connect(self._update_stock_badge)
        self._update_stock_badge()

        self.apply_styles()
    
    def create_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("background-color: #2c3e50;")
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(10)
        
        title = QLabel("ARENA B2")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: white; font-size: 24px; font-weight: bold; padding: 20px;")
        layout.addWidget(title)
        
        subtitle = QLabel("Controle de Estoque")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #95a5a6; font-size: 14px; padding-bottom: 30px;")
        layout.addWidget(subtitle)
        
        self.btn_dashboard = self.create_menu_button("📊 Dashboard")
        self.btn_products = self.create_menu_button("📦 Produtos")
        self.btn_movements = self.create_menu_button("🔄 Movimentações")
        self.btn_orders = self.create_menu_button("🧾 Comandas")
        self.btn_reports = self.create_menu_button("📈 Relatórios")
        
        layout.addWidget(self.btn_dashboard)
        layout.addWidget(self.btn_products)
        layout.addWidget(self.btn_movements)
        layout.addWidget(self.btn_orders)
        layout.addWidget(self.btn_reports)

        layout.addStretch()

        self.btn_backup = QPushButton("💾 Backup dos Dados")
        self.btn_backup.setFixedHeight(50)
        self.btn_backup.setStyleSheet("""
            QPushButton {
                background-color: #c0392b;
                color: white;
                text-align: left;
                padding-left: 30px;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover { background-color: #a93226; }
            QPushButton:pressed { background-color: #922b21; }
        """)
        layout.addWidget(self.btn_backup)

        self.btn_dashboard.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        self.btn_products.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        self.btn_movements.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        self.btn_orders.clicked.connect(lambda: self.navigate_to_orders())
        self.btn_reports.clicked.connect(lambda: self.navigate_to_reports())
        self.btn_backup.clicked.connect(self._run_backup)

        return sidebar
    
    def navigate_to_orders(self):
        self.stacked_widget.setCurrentIndex(3)
        self.orders_window.load_orders()
    
    def navigate_to_reports(self):
        self.stacked_widget.setCurrentIndex(4)
        self.reports_window.load_report()
    
    def create_menu_button(self, text):
        button = QPushButton(text)
        button.setFixedHeight(50)
        button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                text-align: left;
                padding-left: 30px;
                font-size: 16px;
                border: none;
                border-left: 3px solid transparent;
            }
            QPushButton:hover {
                background-color: #34495e;
                border-left: 3px solid #3498db;
            }
            QPushButton:pressed {
                background-color: #2c3e50;
            }
        """)
        return button
    
    def _update_stock_badge(self):
        """Atualiza o texto do botão Dashboard com contagem de itens em estoque baixo."""
        try:
            from backend.utils.data_loader import DataLoader
            dl = DataLoader()
            count = len(dl.get_low_stock_products())
            if count > 0:
                self.btn_dashboard.setText(f"📊 Dashboard  ⚠ {count}")
            else:
                self.btn_dashboard.setText("📊 Dashboard")
        except Exception:
            self.btn_dashboard.setText("📊 Dashboard")

    def _run_backup(self):
        """Abre diálogo para escolher pasta de destino e cria o backup."""
        dest = QFileDialog.getExistingDirectory(self, "Escolha a pasta para salvar o backup")
        if not dest:
            return
        try:
            backup_path = BackupController().create_backup(dest)
            QMessageBox.information(
                self, "Backup criado com sucesso!",
                f"Dados salvos em:\n{backup_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro no Backup", str(e))

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ecf0f1;
            }
        """)