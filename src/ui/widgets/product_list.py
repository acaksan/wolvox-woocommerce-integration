from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTreeWidget, QTreeWidgetItem, QPushButton,
                             QFrame, QSplitter, QMenu, QMessageBox, QLineEdit, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon

from config.settings import Settings
from utils.logger import setup_logger
from database.models import Product, Category
from database.connection import DatabaseManager
from core.woo_client import WooClient
from core.wolvox_client import WolvoxClient

class ProductListWidget(QWidget):
    """Ürün listesi widget'ı"""
    
    product_selected = pyqtSignal(Product)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = setup_logger(self.__class__.__name__)
        self.settings = Settings()
        self.db = DatabaseManager()
        self.woo = WooClient()
        self.wolvox = WolvoxClient()
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """UI bileşenlerini oluştur"""
        # Ana layout
        layout = QVBoxLayout(self)
        
        # Araç çubuğu
        toolbar = QHBoxLayout()
        
        # Arama kutusu
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Ürün Ara (Kod, Ad, Barkod)")
        toolbar.addWidget(self.search_box)
        
        # Filtreler
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Tümü", "Stokta Var", "Stokta Yok", "Fiyat Farkı Var"])
        toolbar.addWidget(self.filter_combo)
        
        # Yenile butonu
        self.refresh_button = QPushButton("Yenile")
        self.refresh_button.setIcon(QIcon("assets/icons/refresh.png"))
        toolbar.addWidget(self.refresh_button)
        
        # Senkronize et butonu
        self.sync_button = QPushButton("Senkronize Et")
        self.sync_button.setIcon(QIcon("assets/icons/sync.png"))
        toolbar.addWidget(self.sync_button)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Wolvox ürünleri
        wolvox_frame = QFrame()
        wolvox_layout = QVBoxLayout(wolvox_frame)
        wolvox_header = QHBoxLayout()
        wolvox_header.addWidget(QLabel("Wolvox Ürünleri"))
        self.wolvox_count = QLabel("0 ürün")
        wolvox_header.addWidget(self.wolvox_count)
        wolvox_layout.addLayout(wolvox_header)
        
        self.wolvox_tree = QTreeWidget()
        self.wolvox_tree.setHeaderLabels([
            "Kod", "Ad", "Barkod", "Liste Fiyatı", "KDV Dahil", 
            "Stok", "Depo Dağılımı", "Kategori", "Marka"
        ])
        self.wolvox_tree.setAlternatingRowColors(True)
        self.wolvox_tree.setSortingEnabled(True)
        wolvox_layout.addWidget(self.wolvox_tree)
        splitter.addWidget(wolvox_frame)
        
        # WooCommerce ürünleri
        woo_frame = QFrame()
        woo_layout = QVBoxLayout(woo_frame)
        woo_header = QHBoxLayout()
        woo_header.addWidget(QLabel("WooCommerce Ürünleri"))
        self.woo_count = QLabel("0 ürün")
        woo_header.addWidget(self.woo_count)
        woo_layout.addLayout(woo_header)
        
        self.woo_tree = QTreeWidget()
        self.woo_tree.setHeaderLabels([
            "ID", "SKU", "Ad", "Fiyat", "Stok", "Durum",
            "Kategori", "Etiketler", "Görünürlük"
        ])
        self.woo_tree.setAlternatingRowColors(True)
        self.woo_tree.setSortingEnabled(True)
        woo_layout.addWidget(self.woo_tree)
        splitter.addWidget(woo_frame)
        
        layout.addWidget(splitter)
        
        # Durum çubuğu
        status_bar = QHBoxLayout()
        self.status_label = QLabel("")
        status_bar.addWidget(self.status_label)
        layout.addLayout(status_bar)
    
    def setup_connections(self):
        """Sinyal bağlantılarını kur"""
        self.refresh_button.clicked.connect(self.load_data)
        self.sync_button.clicked.connect(self.sync_products)
        self.search_box.textChanged.connect(self.filter_products)
        self.filter_combo.currentIndexChanged.connect(self.filter_products)
        
        # Başlangıçta verileri yükleme
        self.load_data()
    
    def load_data(self):
        """Verileri yükle"""
        try:
            # WooCommerce bağlantısını test et
            self.logger.info("WooCommerce bağlantısı test ediliyor...")
            self.woo.test_connection()
            
            # Wolvox bağlantısını test et
            self.logger.info("Wolvox bağlantısı test ediliyor...")
            self.wolvox.test_connection()
            
            # Ürünleri getir
            self.logger.info("Ürünler getiriliyor...")
            wolvox_products = self.wolvox.get_products()
            woo_products = self.woo.get_products()
            
            # Ağaçları temizle
            self.wolvox_tree.clear()
            self.woo_tree.clear()
            
            # Wolvox ürünlerini ekle
            for product in wolvox_products:
                item = QTreeWidgetItem(self.wolvox_tree)
                item.setText(0, str(product["sku"]))
                item.setText(1, str(product["name"]))
                item.setText(2, str(product["barcode"]))
                item.setText(3, f"{product['price']:.2f} TL")
                item.setText(4, str(product["category"]))
                item.setText(5, str(product["stock"]))
            
            # WooCommerce ürünlerini ekle
            for product in woo_products:
                item = QTreeWidgetItem(self.woo_tree)
                item.setText(0, str(product["name"]))
                item.setText(1, str(product["sku"]))
                item.setText(2, str(product["category"]))
                item.setText(3, f"{product['price']:.2f} TL")
                item.setText(4, str(product["stock"]))
                item.setText(5, str(product["visibility"]))
            
            # Başlıkları ayarla
            self.wolvox_tree.setHeaderLabels(["SKU", "Ad", "Barkod", "Fiyat", "Kategori", "Stok"])
            self.woo_tree.setHeaderLabels(["Ad", "SKU", "Kategori", "Fiyat", "Stok", "Durum"])
            
            # Sütun genişliklerini ayarla
            for i in range(6):
                self.wolvox_tree.resizeColumnToContents(i)
                self.woo_tree.resizeColumnToContents(i)
            
            # Ürün sayılarını güncelle
            self.update_product_counts()
            
            self.logger.info("Veriler başarıyla yüklendi")
            
        except Exception as e:
            self.logger.error(f"Veriler yüklenirken hata: {str(e)}")
            QMessageBox.critical(self, "Hata", f"Veriler yüklenirken hata oluştu: {str(e)}")
    
    def sync_products(self):
        """Ürünleri senkronize et"""
        try:
            # Seçili ürünleri al
            selected_wolvox = self.wolvox_tree.selectedItems()
            selected_woo = self.woo_tree.selectedItems()
            
            if not selected_wolvox or not selected_woo:
                QMessageBox.warning(self, "Uyarı", "Lütfen eşleştirmek istediğiniz ürünleri seçin")
                return
            
            # TODO: Senkronizasyon işlemini gerçekleştir
            
        except Exception as e:
            self.logger.error(f"Senkronizasyon hatası: {str(e)}")
            QMessageBox.critical(self, "Hata", f"Senkronizasyon sırasında hata oluştu: {str(e)}")
    
    def load_products(self, category=None):
        """Ürünleri yükle"""
        try:
            self.wolvox_tree.clear()
            self.woo_tree.clear()
            
            products = []
            
            for product in products:
                item = QTreeWidgetItem(self.wolvox_tree)
                item.setText(0, product.sku)
                item.setText(1, product.name)
                item.setText(2, f"{product.price:.2f} TL")
                item.setText(3, str(product.stock))
                item.setData(0, Qt.UserRole, product)
        
        except Exception as e:
            self.logger.error(f"Ürünler yüklenirken hata: {str(e)}")
            QMessageBox.critical(self, "Hata", "Ürünler yüklenirken hata oluştu!")
    
    def get_status_text(self, product):
        """Ürün durumunu metin olarak döndür"""
        if product.woo_id:
            return "Eşleşti"
        elif product.error:
            return "Hata"
        else:
            return "Bekliyor"
    
    def on_category_selected(self, item):
        """Kategori seçildiğinde"""
        category = item.data(0, Qt.UserRole)
        self.load_products(category)
    
    def on_product_selected(self, item):
        """Ürün seçildiğinde"""
        product = item.data(0, Qt.UserRole)
        if product:
            # Ürün nesnesini oluştur
            product_obj = Product()
            product_obj.id = product.get("id")
            product_obj.sku = product.get("sku")
            product_obj.name = product.get("name")
            product_obj.price = product.get("price")
            product_obj.stock = product.get("stock")
            product_obj.status = product.get("status")
            
            self.product_selected.emit(product_obj)

    def filter_products(self):
        """Ürünleri filtrele"""
        search_text = self.search_box.text().lower()
        filter_option = self.filter_combo.currentText()
        
        # Tüm ürünleri göster/gizle
        for i in range(self.wolvox_tree.topLevelItemCount()):
            wolvox_item = self.wolvox_tree.topLevelItem(i)
            wolvox_sku = wolvox_item.text(0)  # SKU kolonu
            wolvox_name = wolvox_item.text(1)  # Ad kolonu
            wolvox_barcode = wolvox_item.text(2)  # Barkod kolonu
            
            # WooCommerce'de eşleşen ürünü bul
            woo_match = None
            for j in range(self.woo_tree.topLevelItemCount()):
                woo_item = self.woo_tree.topLevelItem(j)
                if woo_item.text(1) == wolvox_sku:  # SKU eşleşmesi
                    woo_match = woo_item
                    break
            
            # Filtreleme koşulları
            show_item = True
            if search_text:
                show_item = (search_text in wolvox_sku.lower() or 
                            search_text in wolvox_name.lower() or 
                            search_text in wolvox_barcode.lower())
            
            if filter_option == "Stokta Var":
                show_item = show_item and float(wolvox_item.text(5)) > 0
            elif filter_option == "Stokta Yok":
                show_item = show_item and float(wolvox_item.text(5)) <= 0
            elif filter_option == "Fiyat Farkı Var" and woo_match:
                wolvox_price = float(wolvox_item.text(3).replace(" TL", ""))
                woo_price = float(woo_match.text(3).replace(" TL", ""))
                show_item = show_item and abs(wolvox_price - woo_price) > 0.01
            
            # Eşleşen ürünleri vurgula
            if woo_match:
                wolvox_item.setBackground(0, Qt.yellow)  # SKU kolonunu sarı yap
                woo_match.setBackground(0, Qt.yellow)    # SKU kolonunu sarı yap
            else:
                wolvox_item.setBackground(0, Qt.white)   # Eşleşme yoksa beyaz yap
            
            wolvox_item.setHidden(not show_item)
            
            # WooCommerce ürününü de göster/gizle
            if woo_match:
                woo_match.setHidden(not show_item)

    def update_product_counts(self):
        """Ürün sayılarını güncelle"""
        wolvox_count = 0
        for i in range(self.wolvox_tree.topLevelItemCount()):
            if not self.wolvox_tree.topLevelItem(i).isHidden():
                wolvox_count += 1
        
        woo_count = 0
        for i in range(self.woo_tree.topLevelItemCount()):
            if not self.woo_tree.topLevelItem(i).isHidden():
                woo_count += 1
        
        self.wolvox_count.setText(f"{wolvox_count} ürün")
        self.woo_count.setText(f"{woo_count} ürün")
