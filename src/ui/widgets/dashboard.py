from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QGraphicsDropShadowEffect, QSpacerItem,
                             QSizePolicy)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QIcon

from config.settings import Settings
from utils.logger import setup_logger
from database.models import Product, Category, SyncLog
from database.connection import DatabaseManager

class StatCard(QFrame):
    """İstatistik kartı widget'ı"""
    def __init__(self, title, value, icon_path, color="#4a90e2"):
        super().__init__()
        self.title = title
        self.value = value
        self.icon_path = icon_path
        self.color = color
        
        self.setup_ui()
    
    def setup_ui(self):
        """UI bileşenlerini oluştur"""
        # Ana layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # Başlık ve ikon
        header_layout = QHBoxLayout()
        
        title_label = QLabel(self.title)
        title_label.setStyleSheet(f"""
            color: {self.color};
            font-size: 16px;
            font-weight: bold;
        """)
        header_layout.addWidget(title_label)
        
        icon_label = QLabel()
        icon_label.setPixmap(QIcon(self.icon_path).pixmap(32, 32))
        header_layout.addWidget(icon_label, alignment=Qt.AlignRight)
        
        layout.addLayout(header_layout)
        
        # Değer
        self.value_label = QLabel(str(self.value))
        self.value_label.setStyleSheet("""
            color: #2c3e50;
            font-size: 24px;
            font-weight: bold;
        """)
        layout.addWidget(self.value_label)
        
        # Gölge efekti
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)
        
        # Stil
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 10px;
                border: 1px solid {self.color};
            }}
        """)
        
        # Minimum boyut
        self.setMinimumSize(200, 120)
    
    def update_value(self, value):
        """Değeri güncelle"""
        self.value = value
        self.value_label.setText(str(value))

class DashboardWidget(QWidget):
    """Dashboard widget'ı"""
    
    def __init__(self):
        super().__init__()
        self.settings = Settings()
        self.logger = setup_logger(self.__class__.__name__)
        self.db = DatabaseManager()
        
        self.setup_ui()
        
        # Otomatik yenileme
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_stats)
        self.refresh_timer.start(60000)  # Her dakika güncelle
        
    def setup_ui(self):
        """UI bileşenlerini oluştur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Başlık
        title = QLabel("Dashboard")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #333333;
        """)
        layout.addWidget(title)
        
        # İstatistik kartları
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)
        
        # Toplam ürün sayısı
        self.total_products_card = StatCard(
            "Toplam Ürün",
            self.get_total_products(),
            "assets/icons/products.png",
            "#4a90e2"
        )
        stats_layout.addWidget(self.total_products_card)
        
        # Eşleşen ürün sayısı
        self.matched_products_card = StatCard(
            "Eşleşen Ürün",
            self.get_matched_products(),
            "assets/icons/matched.png",
            "#2ecc71"
        )
        stats_layout.addWidget(self.matched_products_card)
        
        # Bekleyen ürün sayısı
        self.pending_products_card = StatCard(
            "Bekleyen Ürün",
            self.get_pending_products(),
            "assets/icons/pending.png",
            "#f1c40f"
        )
        stats_layout.addWidget(self.pending_products_card)
        
        # Hatalı ürün sayısı
        self.error_products_card = StatCard(
            "Hatalı Ürün",
            self.get_error_products(),
            "assets/icons/error.png",
            "#e74c3c"
        )
        stats_layout.addWidget(self.error_products_card)
        
        layout.addLayout(stats_layout)
        
        # Son senkronizasyon bilgisi
        self.sync_info = QLabel(f"Son Senkronizasyon: {self.get_last_sync()}")
        self.sync_info.setStyleSheet("""
            color: #666666;
            font-size: 14px;
        """)
        layout.addWidget(self.sync_info)
        
        # Boşluk ekle
        layout.addStretch()
    
    def get_total_products(self):
        """Toplam ürün sayısını getir"""
        try:
            return self.db.session.query(Product).count()
        except Exception as e:
            self.logger.error(f"Toplam ürün sayısı alınırken hata: {str(e)}")
            return 0
    
    def get_matched_products(self):
        """Eşleşen ürün sayısını getir"""
        try:
            return self.db.session.query(Product).filter(Product.woo_id.isnot(None)).count()
        except Exception as e:
            self.logger.error(f"Eşleşen ürün sayısı alınırken hata: {str(e)}")
            return 0
    
    def get_pending_products(self):
        """Bekleyen ürün sayısını getir"""
        try:
            return self.db.session.query(Product).filter(Product.woo_id.is_(None)).count()
        except Exception as e:
            self.logger.error(f"Bekleyen ürün sayısı alınırken hata: {str(e)}")
            return 0
    
    def get_error_products(self):
        """Hatalı ürün sayısını getir"""
        try:
            return self.db.session.query(Product).filter(Product.status == "error").count()
        except Exception as e:
            self.logger.error(f"Hatalı ürün sayısı alınırken hata: {str(e)}")
            return 0
    
    def get_last_sync(self) -> str:
        """Son senkronizasyon zamanını getir"""
        try:
            with self.db.session_scope() as session:
                last_sync = session.query(SyncLog).order_by(
                    SyncLog.created_at.desc()
                ).first()
                
                if last_sync:
                    return last_sync.created_at.strftime("%d.%m.%Y %H:%M")
                return "Henüz senkronizasyon yapılmadı"
        except Exception as e:
            self.logger.error(f"Son senkronizasyon zamanı alınırken hata: {str(e)}")
            return "Bilinmiyor"
    
    def refresh_stats(self):
        """İstatistikleri yenile"""
        try:
            # Kart değerlerini güncelle
            self.total_products_card.update_value(self.get_total_products())
            self.matched_products_card.update_value(self.get_matched_products())
            self.pending_products_card.update_value(self.get_pending_products())
            self.error_products_card.update_value(self.get_error_products())
            
            # Son senkronizasyon bilgisini güncelle
            self.sync_info.setText(f"Son Senkronizasyon: {self.get_last_sync()}")
            
        except Exception as e:
            self.logger.error(f"İstatistikler güncellenirken hata: {str(e)}")
    
    def paintEvent(self, event):
        """Widget'ın arka planını çiz"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Yuvarlak köşeli arka plan
        path = QPainterPath()
        rect = self.rect()
        path.addRoundedRect(float(rect.x()), float(rect.y()),
                          float(rect.width()), float(rect.height()),
                          10.0, 10.0)
        
        painter.fillPath(path, QColor("#ffffff"))
