from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QProgressBar, QTableWidget, QTableWidgetItem,
                             QHeaderView, QComboBox, QCheckBox, QSpinBox,
                             QMessageBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QColor

from config.settings import Settings
from utils.logger import setup_logger
from database.models import SyncLog, Product, Category
from database.connection import DatabaseManager
from core.woo_client import WooCommerceClient
from core.wolvox_client import WolvoxClient
from ui.style import ICONS

class SyncManagerWidget(QWidget):
    """Senkronizasyon yönetimi widget'ı"""
    
    sync_started = pyqtSignal()
    sync_finished = pyqtSignal()
    sync_error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.settings = Settings()
        self.logger = setup_logger(self.__class__.__name__)
        self.db = DatabaseManager()
        
        self.woo_client = WooCommerceClient()
        self.wolvox_client = WolvoxClient()
        
        self.is_syncing = False
        self.current_sync = None
        
        self.setup_ui()
        self.load_sync_logs()
        
        # Otomatik yenileme
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.load_sync_logs)
        self.refresh_timer.start(60000)  # Her dakika güncelle
    
    def setup_ui(self):
        """UI bileşenlerini oluştur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Başlık
        title = QLabel("Senkronizasyon")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #333333;
        """)
        layout.addWidget(title)
        
        # Kontrol paneli
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        
        # Senkronizasyon ayarları
        settings_layout = QHBoxLayout()
        
        # Yön seçimi
        self.direction_combo = QComboBox()
        self.direction_combo.addItems([
            "Wolvox → WooCommerce",
            "WooCommerce → Wolvox",
            "İki Yönlü"
        ])
        settings_layout.addWidget(QLabel("Yön:"))
        settings_layout.addWidget(self.direction_combo)
        
        # Veri tipi seçimi
        self.data_type_combo = QComboBox()
        self.data_type_combo.addItems([
            "Ürünler",
            "Kategoriler",
            "Tümü"
        ])
        settings_layout.addWidget(QLabel("Veri Tipi:"))
        settings_layout.addWidget(self.data_type_combo)
        
        # Otomatik eşleştirme
        self.auto_match_check = QCheckBox("Otomatik Eşleştir")
        self.auto_match_check.setChecked(True)
        settings_layout.addWidget(self.auto_match_check)
        
        # Güncelleme aralığı
        self.interval_spin = QSpinBox()
        self.interval_spin.setMinimum(1)
        self.interval_spin.setMaximum(60)
        self.interval_spin.setValue(5)
        settings_layout.addWidget(QLabel("Güncelleme Aralığı (dk):"))
        settings_layout.addWidget(self.interval_spin)
        
        control_layout.addLayout(settings_layout)
        
        # İlerleme çubuğu
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%v / %m (%p%)")
        control_layout.addWidget(self.progress_bar)
        
        # Butonlar
        button_layout = QHBoxLayout()
        
        self.sync_button = QPushButton("Senkronizasyonu Başlat")
        self.sync_button.setIcon(QIcon(ICONS.SYNC))
        self.sync_button.clicked.connect(self.start_sync)
        button_layout.addWidget(self.sync_button)
        
        self.cancel_button = QPushButton("İptal")
        self.cancel_button.setIcon(QIcon(ICONS.CANCEL))
        self.cancel_button.clicked.connect(self.cancel_sync)
        self.cancel_button.setEnabled(False)
        button_layout.addWidget(self.cancel_button)
        
        control_layout.addLayout(button_layout)
        
        layout.addWidget(control_panel)
        
        # Senkronizasyon geçmişi
        history_label = QLabel("Senkronizasyon Geçmişi")
        history_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #333333;
        """)
        layout.addWidget(history_label)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Tarih",
            "Yön",
            "Veri Tipi",
            "Durum",
            "Başarılı",
            "Hatalı"
        ])
        
        # Tablo ayarları
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setAlternatingRowColors(True)
        
        layout.addWidget(self.table)
    
    def load_sync_logs(self):
        """Senkronizasyon geçmişini yükle"""
        try:
            with self.db.session_scope() as session:
                logs = session.query(SyncLog).order_by(
                    SyncLog.created_at.desc()
                ).limit(100).all()
                
                self.table.setRowCount(len(logs))
                
                for row, log in enumerate(logs):
                    # Tarih
                    self.table.setItem(
                        row, 0,
                        QTableWidgetItem(
                            log.created_at.strftime("%d.%m.%Y %H:%M")
                        )
                    )
                    
                    # Yön
                    self.table.setItem(
                        row, 1,
                        QTableWidgetItem(log.direction)
                    )
                    
                    # Veri tipi
                    self.table.setItem(
                        row, 2,
                        QTableWidgetItem(log.data_type)
                    )
                    
                    # Durum
                    status_item = QTableWidgetItem(log.status)
                    if log.status == "completed":
                        status_item.setForeground(QColor("#27ae60"))
                    elif log.status == "error":
                        status_item.setForeground(QColor("#c0392b"))
                    self.table.setItem(row, 3, status_item)
                    
                    # Başarılı
                    self.table.setItem(
                        row, 4,
                        QTableWidgetItem(str(log.success_count))
                    )
                    
                    # Hatalı
                    error_item = QTableWidgetItem(str(log.error_count))
                    if log.error_count > 0:
                        error_item.setForeground(QColor("#c0392b"))
                    self.table.setItem(row, 5, error_item)
                    
        except Exception as e:
            self.logger.error(f"Senkronizasyon geçmişi yüklenirken hata: {str(e)}")
            QMessageBox.critical(
                self,
                "Hata",
                "Senkronizasyon geçmişi yüklenirken bir hata oluştu!"
            )
    
    def start_sync(self):
        """Senkronizasyonu başlat"""
        if self.is_syncing:
            return
        
        try:
            # Senkronizasyon kaydı oluştur
            with self.db.session_scope() as session:
                self.current_sync = SyncLog(
                    direction=self.direction_combo.currentText(),
                    data_type=self.data_type_combo.currentText(),
                    status="running"
                )
                session.add(self.current_sync)
            
            self.is_syncing = True
            self.sync_started.emit()
            
            # UI güncellemeleri
            self.sync_button.setEnabled(False)
            self.cancel_button.setEnabled(True)
            self.progress_bar.setValue(0)
            
            # Senkronizasyon tipine göre işlem yap
            if self.data_type_combo.currentText() == "Ürünler":
                self.sync_products()
            elif self.data_type_combo.currentText() == "Kategoriler":
                self.sync_categories()
            else:
                self.sync_all()
            
        except Exception as e:
            self.logger.error(f"Senkronizasyon başlatılırken hata: {str(e)}")
            self.sync_error.emit(str(e))
            self.finish_sync(error=True)
    
    def cancel_sync(self):
        """Senkronizasyonu iptal et"""
        if not self.is_syncing:
            return
        
        reply = QMessageBox.question(
            self,
            "Senkronizasyonu İptal Et",
            "Senkronizasyonu iptal etmek istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.is_syncing = False
            self.finish_sync(cancelled=True)
    
    def finish_sync(self, error=False, cancelled=False):
        """Senkronizasyonu bitir"""
        try:
            if self.current_sync:
                with self.db.session_scope() as session:
                    if error:
                        self.current_sync.status = "error"
                    elif cancelled:
                        self.current_sync.status = "cancelled"
                    else:
                        self.current_sync.status = "completed"
                    
                    session.merge(self.current_sync)
            
            self.is_syncing = False
            self.current_sync = None
            
            # UI güncellemeleri
            self.sync_button.setEnabled(True)
            self.cancel_button.setEnabled(False)
            self.progress_bar.setValue(0)
            
            self.sync_finished.emit()
            self.load_sync_logs()
            
        except Exception as e:
            self.logger.error(f"Senkronizasyon bitirme hatası: {str(e)}")
    
    def sync_products(self):
        """Ürünleri senkronize et"""
        try:
            direction = self.direction_combo.currentText()
            
            if direction in ["Wolvox → WooCommerce", "İki Yönlü"]:
                # Wolvox'tan ürünleri al
                wolvox_products = self.wolvox_client.get_products()
                
                # WooCommerce'e gönder
                for product in wolvox_products:
                    if not self.is_syncing:
                        break
                    
                    try:
                        self.woo_client.create_or_update_product(product)
                        self.current_sync.success_count += 1
                    except Exception as e:
                        self.logger.error(f"Ürün senkronizasyon hatası: {str(e)}")
                        self.current_sync.error_count += 1
            
            if direction in ["WooCommerce → Wolvox", "İki Yönlü"]:
                # WooCommerce'den ürünleri al
                woo_products = self.woo_client.get_products()
                
                # Wolvox'a gönder
                for product in woo_products:
                    if not self.is_syncing:
                        break
                    
                    try:
                        self.wolvox_client.create_or_update_product(product)
                        self.current_sync.success_count += 1
                    except Exception as e:
                        self.logger.error(f"Ürün senkronizasyon hatası: {str(e)}")
                        self.current_sync.error_count += 1
            
            self.finish_sync()
            
        except Exception as e:
            self.logger.error(f"Ürün senkronizasyon hatası: {str(e)}")
            self.sync_error.emit(str(e))
            self.finish_sync(error=True)
    
    def sync_categories(self):
        """Kategorileri senkronize et"""
        try:
            direction = self.direction_combo.currentText()
            
            if direction in ["Wolvox → WooCommerce", "İki Yönlü"]:
                # Wolvox'tan kategorileri al
                wolvox_categories = self.wolvox_client.get_categories()
                
                # WooCommerce'e gönder
                for category in wolvox_categories:
                    if not self.is_syncing:
                        break
                    
                    try:
                        self.woo_client.create_or_update_category(category)
                        self.current_sync.success_count += 1
                    except Exception as e:
                        self.logger.error(f"Kategori senkronizasyon hatası: {str(e)}")
                        self.current_sync.error_count += 1
            
            if direction in ["WooCommerce → Wolvox", "İki Yönlü"]:
                # WooCommerce'den kategorileri al
                woo_categories = self.woo_client.get_categories()
                
                # Wolvox'a gönder
                for category in woo_categories:
                    if not self.is_syncing:
                        break
                    
                    try:
                        self.wolvox_client.create_or_update_category(category)
                        self.current_sync.success_count += 1
                    except Exception as e:
                        self.logger.error(f"Kategori senkronizasyon hatası: {str(e)}")
                        self.current_sync.error_count += 1
            
            self.finish_sync()
            
        except Exception as e:
            self.logger.error(f"Kategori senkronizasyon hatası: {str(e)}")
            self.sync_error.emit(str(e))
            self.finish_sync(error=True)
    
    def sync_all(self):
        """Tüm verileri senkronize et"""
        try:
            # Önce kategorileri senkronize et
            self.sync_categories()
            
            if self.is_syncing:
                # Sonra ürünleri senkronize et
                self.sync_products()
            
        except Exception as e:
            self.logger.error(f"Tam senkronizasyon hatası: {str(e)}")
            self.sync_error.emit(str(e))
            self.finish_sync(error=True)
