from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QStackedWidget, QFrame)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon

from config.settings import Settings
from utils.logger import setup_logger
from ui.style import ICONS
from ui.widgets.dashboard import DashboardWidget
from ui.widgets.product_list import ProductListWidget
from ui.widgets.settings import SettingsWidget

class MainWindow(QMainWindow):
    """Ana pencere"""
    
    def __init__(self):
        super().__init__()
        self.settings = Settings()
        self.logger = setup_logger(self.__class__.__name__)
        
        self.setup_ui()
        self.setup_connections()
        
        self.setWindowTitle("Wolvox - WooCommerce Entegrasyon")
        self.setMinimumSize(1200, 800)
        self.showMaximized()
    
    def setup_ui(self):
        """UI bileşenlerini oluştur"""
        # Ana widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Ana layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sol menü
        menu_frame = QFrame()
        menu_frame.setObjectName("menuFrame")
        menu_frame.setStyleSheet("""
            #menuFrame {
                background-color: #2c3e50;
                border: none;
            }
            
            QPushButton {
                color: #ecf0f1;
                background-color: transparent;
                border: none;
                text-align: left;
                padding: 10px;
                font-size: 14px;
            }
            
            QPushButton:hover {
                background-color: #34495e;
            }
            
            QPushButton:checked {
                background-color: #3498db;
            }
        """)
        
        menu_layout = QVBoxLayout(menu_frame)
        menu_layout.setContentsMargins(0, 0, 0, 0)
        menu_layout.setSpacing(0)
        
        # Logo
        logo_label = QLabel("Wolvox - WooCommerce")
        logo_label.setStyleSheet("""
            color: #ecf0f1;
            font-size: 16px;
            font-weight: bold;
            padding: 20px;
        """)
        menu_layout.addWidget(logo_label)
        
        # Menü butonları
        self.dashboard_button = QPushButton("Dashboard")
        self.dashboard_button.setIcon(QIcon(ICONS.DASHBOARD))
        self.dashboard_button.setIconSize(QSize(24, 24))
        self.dashboard_button.setCheckable(True)
        menu_layout.addWidget(self.dashboard_button)
        
        self.products_button = QPushButton("Ürün Yönetimi")
        self.products_button.setIcon(QIcon(ICONS.PRODUCTS))
        self.products_button.setIconSize(QSize(24, 24))
        self.products_button.setCheckable(True)
        menu_layout.addWidget(self.products_button)
        
        self.menu_buttons = [
            self.dashboard_button,
            self.products_button
        ]
        
        # Başlangıçta dashboard'ı göster
        self.dashboard_button.setChecked(True)
        
        menu_layout.addStretch()
        
        # Ayarlar butonu
        self.settings_button = QPushButton("Ayarlar")
        self.settings_button.setIcon(QIcon(ICONS.SETTINGS))
        self.settings_button.setIconSize(QSize(24, 24))
        self.settings_button.setCheckable(True)
        menu_layout.addWidget(self.settings_button)
        
        self.menu_buttons.append(self.settings_button)
        
        main_layout.addWidget(menu_frame)
        
        # İçerik alanı
        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")
        content_frame.setStyleSheet("""
            #contentFrame {
                background-color: #f5f6fa;
                border: none;
            }
        """)
        
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Stacked widget
        self.stacked_widget = QStackedWidget()
        
        # Widget'ları ekle
        self.dashboard_widget = DashboardWidget()
        self.stacked_widget.addWidget(self.dashboard_widget)
        
        self.products_widget = ProductListWidget()
        self.stacked_widget.addWidget(self.products_widget)
        
        self.settings_widget = SettingsWidget()
        self.stacked_widget.addWidget(self.settings_widget)

        content_layout.addWidget(self.stacked_widget)
        
        main_layout.addWidget(content_frame)
        
        # Sol menü genişliği
        menu_frame.setFixedWidth(250)
    
    def setup_connections(self):
        """Sinyal bağlantılarını kur"""
        # Menü butonları
        self.dashboard_button.clicked.connect(
            lambda: self.switch_page(0)
        )
        self.products_button.clicked.connect(
            lambda: self.switch_page(1)
        )
        self.settings_button.clicked.connect(
            lambda: self.switch_page(2)
        )
    
    def switch_page(self, index):
        """Sayfayı değiştir"""
        # Önceki butonu temizle
        for button in self.menu_buttons:
            button.setChecked(False)
        
        # Yeni butonu seç
        self.menu_buttons[index].setChecked(True)
        
        # Sayfayı değiştir
        self.stacked_widget.setCurrentIndex(index)
