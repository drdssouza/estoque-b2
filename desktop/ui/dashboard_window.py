from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QScrollArea, QGridLayout)
from PySide6.QtCore import Qt, QTimer
from desktop.controllers.dashboard_controller import DashboardController
import pandas as pd

class DashboardWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.controller = DashboardController()
        self.setup_ui()
        
        # Timer para atualização automática a cada 5 segundos
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_data)
        self.timer.start(5000)  # 5 segundos
    
    def showEvent(self, event):
        """Chamado toda vez que a janela é mostrada"""
        super().showEvent(event)
        self.load_data()  # Atualiza os dados sempre que o dashboard é exibido
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Cor de fundo da janela
        self.setStyleSheet("background-color: #ecf0f1;")
        
        # Header com título e botão de refresh
        header_layout = QHBoxLayout()
        
        title = QLabel("Dashboard")
        title.setStyleSheet("font-size: 32px; font-weight: bold; color: #2c3e50; background-color: transparent;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Label de última atualização
        self.last_update_label = QLabel("Última atualização: --:--:--")
        self.last_update_label.setStyleSheet("font-size: 12px; color: #7f8c8d; background-color: transparent;")
        header_layout.addWidget(self.last_update_label)
        
        layout.addLayout(header_layout)
        
        stats_layout = QGridLayout()
        stats_layout.setSpacing(20)
        
        self.card_total = self.create_stat_card("Total de Produtos", "0", "#3498db")
        self.card_bebidas = self.create_stat_card("Bebidas", "0", "#1abc9c")
        self.card_doces = self.create_stat_card("Doces", "0", "#e74c3c")
        self.card_chips = self.create_stat_card("Salgados", "0", "#f39c12")
        
        stats_layout.addWidget(self.card_total, 0, 0)
        stats_layout.addWidget(self.card_bebidas, 0, 1)
        stats_layout.addWidget(self.card_doces, 0, 2)
        stats_layout.addWidget(self.card_chips, 0, 3)
        
        layout.addLayout(stats_layout)
        
        # Frame de alertas
        alerts_frame = QFrame()
        alerts_frame.setStyleSheet("""
            QFrame {
                background-color: white; 
                border-radius: 10px; 
                padding: 20px;
            }
        """)
        alerts_layout = QVBoxLayout(alerts_frame)
        
        alerts_header = QHBoxLayout()
        alerts_title = QLabel("⚠️ Alertas de Estoque Baixo")
        alerts_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #e74c3c; background-color: transparent;")
        alerts_header.addWidget(alerts_title)
        
        self.alerts_count_label = QLabel("(0)")
        self.alerts_count_label.setStyleSheet("font-size: 16px; color: #e74c3c; background-color: transparent;")
        alerts_header.addWidget(self.alerts_count_label)
        alerts_header.addStretch()
        
        alerts_layout.addLayout(alerts_header)
        
        self.alerts_container = QVBoxLayout()
        alerts_layout.addLayout(self.alerts_container)
        
        layout.addWidget(alerts_frame)
        
        layout.addStretch()
    
    def create_stat_card(self, title, value, color):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 10px;
                padding: 20px;
                min-height: 120px;
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(10)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: white; font-size: 16px; background-color: transparent; font-weight: normal;")
        title_label.setWordWrap(True)
        card_layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("color: white; font-size: 42px; font-weight: bold; background-color: transparent;")
        value_label.setObjectName("value_label")
        card_layout.addWidget(value_label)
        
        card_layout.addStretch()
        
        return card
    
    def load_data(self):
        """Carrega e atualiza todos os dados do dashboard"""
        data = self.controller.get_dashboard_data()
        
        # Atualizar cards de estatísticas
        self.card_total.findChild(QLabel, "value_label").setText(str(data['total_products']))
        self.card_bebidas.findChild(QLabel, "value_label").setText(str(data['total_bebidas']))
        self.card_doces.findChild(QLabel, "value_label").setText(str(data['total_doces']))
        self.card_chips.findChild(QLabel, "value_label").setText(str(data['total_salgado']))
        
        # Atualizar alertas de estoque baixo
        self.update_alerts(data)
        
        # Atualizar label de última atualização
        from datetime import datetime
        now = datetime.now().strftime("%H:%M:%S")
        self.last_update_label.setText(f"Última atualização: {now}")
    
    def update_alerts(self, data):
        """Atualiza a seção de alertas de estoque baixo"""
        # Limpar alertas antigos
        while self.alerts_container.count():
            child = self.alerts_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Atualizar contador
        self.alerts_count_label.setText(f"({data['low_stock_count']})")
        
        if data['low_stock_count'] == 0:
            no_alerts = QLabel("✅ Todos os produtos com estoque adequado")
            no_alerts.setStyleSheet("color: #27ae60; font-size: 14px; margin-top: 10px; background-color: transparent; font-weight: bold;")
            self.alerts_container.addWidget(no_alerts)
        else:
            for item in data['low_stock_items']:
                # Calcular percentual do estoque
                if item['minimum_stock'] > 0:
                    percent = (item['current_stock'] / item['minimum_stock']) * 100
                else:
                    percent = 0
                
                # Definir cor baseado na criticidade
                if percent <= 50:
                    color = "#e74c3c"  # Vermelho - crítico
                    icon = "🔴"
                elif percent <= 100:
                    color = "#f39c12"  # Laranja - atenção
                    icon = "🟡"
                else:
                    color = "#3498db"  # Azul - normal
                    icon = "🔵"
                
                alert = QLabel(f"{icon} {item['name']} - Estoque: {item['current_stock']} / Mínimo: {item['minimum_stock']} ({percent:.0f}%)")
                alert.setStyleSheet(f"color: {color}; font-size: 13px; margin-top: 5px; background-color: transparent; padding: 5px;")
                alert.setWordWrap(True)
                self.alerts_container.addWidget(alert)