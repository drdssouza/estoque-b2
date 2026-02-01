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
        self.timer.start(5000)
    
    def showEvent(self, event):
        super().showEvent(event)
        self.load_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        self.setStyleSheet("background-color: #ecf0f1;")
        
        # ── Header ──
        header_layout = QHBoxLayout()
        
        title = QLabel("Dashboard")
        title.setStyleSheet("font-size: 32px; font-weight: bold; color: #2c3e50; background-color: transparent;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        self.last_update_label = QLabel("Última atualização: --:--:--")
        self.last_update_label.setStyleSheet("font-size: 12px; color: #7f8c8d; background-color: transparent;")
        header_layout.addWidget(self.last_update_label)
        
        layout.addLayout(header_layout)
        
        # ── Grid de cards ──
        # Linha 0: Total | Bebidas | Doces
        # Linha 1: Salgados | Acessórios
        stats_layout = QGridLayout()
        stats_layout.setSpacing(15)
        
        self.card_total       = self.create_stat_card("Total de Produtos", "0", "#2c3e50")
        self.card_bebidas     = self.create_stat_card("Bebidas",           "0", "#3498db")
        self.card_doces       = self.create_stat_card("Doces",             "0", "#e74c3c")
        self.card_chips       = self.create_stat_card("Salgados",          "0", "#f39c12")
        self.card_acessorios  = self.create_stat_card("Acessórios",        "0", "#9b59b6")
        
        stats_layout.addWidget(self.card_total,      0, 0)
        stats_layout.addWidget(self.card_bebidas,    0, 1)
        stats_layout.addWidget(self.card_doces,      0, 2)
        stats_layout.addWidget(self.card_chips,      1, 0)
        stats_layout.addWidget(self.card_acessorios, 1, 1)
        
        # Esticar colunas igualmente
        for col in range(3):
            stats_layout.setColumnStretch(col, 1)
        
        layout.addLayout(stats_layout)
        
        # ── Frame de alertas ──
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
        card.setFixedHeight(110)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 10px;
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(6)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: rgba(255,255,255,0.85); font-size: 15px; background-color: transparent;")
        title_label.setWordWrap(True)
        card_layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("color: white; font-size: 38px; font-weight: bold; background-color: transparent;")
        value_label.setObjectName("value_label")
        card_layout.addWidget(value_label)
        
        card_layout.addStretch()
        
        return card
    
    def load_data(self):
        data = self.controller.get_dashboard_data()
        
        self.card_total.findChild(QLabel, "value_label").setText(str(data['total_products']))
        self.card_bebidas.findChild(QLabel, "value_label").setText(str(data['total_bebidas']))
        self.card_doces.findChild(QLabel, "value_label").setText(str(data['total_doces']))
        self.card_chips.findChild(QLabel, "value_label").setText(str(data['total_salgado']))
        self.card_acessorios.findChild(QLabel, "value_label").setText(str(data['total_acessorios']))
        
        self.update_alerts(data)
        
        from datetime import datetime
        now = datetime.now().strftime("%H:%M:%S")
        self.last_update_label.setText(f"Última atualização: {now}")
    
    def update_alerts(self, data):
        # Limpar alertas antigos
        while self.alerts_container.count():
            child = self.alerts_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        self.alerts_count_label.setText(f"({data['low_stock_count']})")
        
        if data['low_stock_count'] == 0:
            no_alerts = QLabel("✅ Todos os produtos com estoque adequado")
            no_alerts.setStyleSheet("color: #27ae60; font-size: 14px; margin-top: 10px; background-color: transparent; font-weight: bold;")
            self.alerts_container.addWidget(no_alerts)
        else:
            for item in data['low_stock_items']:
                if item['minimum_stock'] > 0:
                    percent = (item['current_stock'] / item['minimum_stock']) * 100
                else:
                    percent = 0
                
                if percent <= 50:
                    color = "#e74c3c"
                    icon = "🔴"
                elif percent <= 100:
                    color = "#f39c12"
                    icon = "🟡"
                else:
                    color = "#3498db"
                    icon = "🔵"
                
                alert = QLabel(f"{icon} {item['name']} - Estoque: {item['current_stock']} / Mínimo: {item['minimum_stock']} ({percent:.0f}%)")
                alert.setStyleSheet(f"color: {color}; font-size: 13px; margin-top: 5px; background-color: transparent; padding: 5px;")
                alert.setWordWrap(True)
                self.alerts_container.addWidget(alert)