import sys
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QStackedWidget,
                           QFrame, QScrollArea, QSizePolicy)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor

# Ana dizini Python path'ine ekle
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

class MenuButton(QPushButton):
    def __init__(self, text, icon_path=None, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setMinimumHeight(50)
        self.setFont(QFont('Segoe UI', 10))
        if icon_path:
            self.setIcon(QIcon(icon_path))
            self.setIconSize(QSize(24, 24))
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 5px 15px;
                border: none;
                border-radius: 5px;
                margin: 2px 10px;
                background-color: transparent;
                color: #333333;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:checked {
                background-color: #0078D4;
                color: white;
            }
        """)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Wolvox - WooCommerce Entegrasyon")
        self.setMinimumSize(1200, 800)
        
        # Ana widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Ana layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sol menü
        menu_frame = QFrame()
        menu_frame.setMaximumWidth(250)
        menu_frame.setMinimumWidth(250)
        menu_frame.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border-right: 1px solid #e0e0e0;
            }
        """)
        
        menu_layout = QVBoxLayout(menu_frame)
        menu_layout.setContentsMargins(0, 0, 0, 0)
        menu_layout.setSpacing(0)
        
        # Logo ve başlık
        logo_layout = QHBoxLayout()
        logo_label = QLabel("LOGO")  # Logo eklenecek
        logo_label.setFont(QFont('Segoe UI', 18, QFont.Bold))
        logo_label.setStyleSheet("color: #0078D4; padding: 20px;")
        logo_layout.addWidget(logo_label)
        menu_layout.addLayout(logo_layout)
        
        # Menü butonları
        self.dashboard_btn = MenuButton("Dashboard", "icons/dashboard.png")
        self.dashboard_btn.setChecked(True)
        menu_layout.addWidget(self.dashboard_btn)
        
        self.products_btn = MenuButton("Ürün Yönetimi", "icons/products.png")
        menu_layout.addWidget(self.products_btn)
        
        self.categories_btn = MenuButton("Kategori Eşleştirme", "icons/categories.png")
        menu_layout.addWidget(self.categories_btn)
        
        self.fields_btn = MenuButton("Alan Eşleştirme", "icons/fields.png")
        menu_layout.addWidget(self.fields_btn)
        
        self.sync_btn = MenuButton("Senkronizasyon", "icons/sync.png")
        menu_layout.addWidget(self.sync_btn)
        
        self.settings_btn = MenuButton("Ayarlar", "icons/settings.png")
        menu_layout.addWidget(self.settings_btn)
        
        menu_layout.addStretch()
        
        # Alt menü
        self.help_btn = MenuButton("Yardım", "icons/help.png")
        menu_layout.addWidget(self.help_btn)
        
        self.about_btn = MenuButton("Hakkında", "icons/about.png")
        menu_layout.addWidget(self.about_btn)
        
        main_layout.addWidget(menu_frame)
        
        # Sağ içerik alanı
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # Üst bar
        top_bar = QFrame()
        top_bar.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
            }
        """)
        top_bar.setMinimumHeight(60)
        
        top_layout = QHBoxLayout(top_bar)
        
        # Başlık
        self.page_title = QLabel("Dashboard")
        self.page_title.setFont(QFont('Segoe UI', 16))
        top_layout.addWidget(self.page_title)
        
        # Sağ üst butonlar
        top_layout.addStretch()
        
        self.notifications_btn = QPushButton("0")  # Bildirim sayısı
        self.notifications_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078D4;
                color: white;
                border-radius: 15px;
                min-width: 30px;
                min-height: 30px;
            }
        """)
        top_layout.addWidget(self.notifications_btn)
        
        content_layout.addWidget(top_bar)
        
        # İçerik alanı
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("""
            QStackedWidget {
                background-color: white;
                border-radius: 10px;
            }
        """)
        
        # Dashboard sayfası
        dashboard_page = QWidget()
        dashboard_layout = QVBoxLayout(dashboard_page)
        
        # İstatistik kartları
        stats_layout = QHBoxLayout()
        
        # Toplam ürün sayısı
        products_card = QFrame()
        products_card.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        products_layout = QVBoxLayout(products_card)
        
        products_title = QLabel("Toplam Ürün")
        products_title.setFont(QFont('Segoe UI', 12))
        products_layout.addWidget(products_title)
        
        products_count = QLabel("0")
        products_count.setFont(QFont('Segoe UI', 24, QFont.Bold))
        products_layout.addWidget(products_count)
        
        stats_layout.addWidget(products_card)
        
        # Eşleşen ürün sayısı
        matched_card = QFrame()
        matched_card.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        matched_layout = QVBoxLayout(matched_card)
        
        matched_title = QLabel("Eşleşen Ürün")
        matched_title.setFont(QFont('Segoe UI', 12))
        matched_layout.addWidget(matched_title)
        
        matched_count = QLabel("0")
        matched_count.setFont(QFont('Segoe UI', 24, QFont.Bold))
        matched_layout.addWidget(matched_count)
        
        stats_layout.addWidget(matched_card)
        
        # Son senkronizasyon
        sync_card = QFrame()
        sync_card.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        sync_layout = QVBoxLayout(sync_card)
        
        sync_title = QLabel("Son Senkronizasyon")
        sync_title.setFont(QFont('Segoe UI', 12))
        sync_layout.addWidget(sync_title)
        
        sync_time = QLabel("-")
        sync_time.setFont(QFont('Segoe UI', 24, QFont.Bold))
        sync_layout.addWidget(sync_time)
        
        stats_layout.addWidget(sync_card)
        
        dashboard_layout.addLayout(stats_layout)
        dashboard_layout.addStretch()
        
        self.content_stack.addWidget(dashboard_page)
        content_layout.addWidget(self.content_stack)
        
        main_layout.addLayout(content_layout)
        
        # Stil ayarları
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
        """)
        
        # Sinyal bağlantıları
        self.dashboard_btn.clicked.connect(lambda: self.change_page("Dashboard"))
        self.products_btn.clicked.connect(lambda: self.change_page("Ürün Yönetimi"))
        self.categories_btn.clicked.connect(lambda: self.change_page("Kategori Eşleştirme"))
        self.fields_btn.clicked.connect(lambda: self.change_page("Alan Eşleştirme"))
        self.sync_btn.clicked.connect(lambda: self.change_page("Senkronizasyon"))
        self.settings_btn.clicked.connect(lambda: self.change_page("Ayarlar"))
        self.help_btn.clicked.connect(lambda: self.change_page("Yardım"))
        self.about_btn.clicked.connect(lambda: self.change_page("Hakkında"))
    
    def change_page(self, page_name):
        # Tüm butonların seçimini kaldır
        for btn in self.findChildren(MenuButton):
            btn.setChecked(False)
        
        # Tıklanan butonu seç
        sender = self.sender()
        if sender:
            sender.setChecked(True)
        
        # Sayfa başlığını güncelle
        self.page_title.setText(page_name)
        
        # TODO: Sayfa içeriğini güncelle

def main():
    app = QApplication(sys.argv)
    
    # Uygulama stili
    app.setStyle('Fusion')
    
    # Koyu tema
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(240, 240, 240))
    palette.setColor(QPalette.WindowText, QColor(51, 51, 51))
    app.setPalette(palette)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
