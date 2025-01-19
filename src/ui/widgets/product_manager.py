from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
                             QComboBox, QFrame, QHeaderView, QMenu, QAction,
                             QMessageBox, QDialog, QFormLayout, QSpinBox,
                             QDoubleSpinBox, QCheckBox, QTextEdit)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QIcon, QColor

from src.config.settings import Settings
from src.utils.logger import setup_logger
from src.database.models import Product
from src.database.connection import DatabaseManager
from src.ui.style import ICONS

class ProductDialog(QDialog):
    """Ürün ekleme/düzenleme dialog'u"""
    
    def __init__(self, parent=None, product=None):
        super().__init__(parent)
        self.product = product
        self.settings = Settings()
        self.logger = setup_logger(self.__class__.__name__)
        self.db = DatabaseManager()
        
        self.setup_ui()
        
        if product:
            self.load_product()
    
    def setup_ui(self):
        """UI bileşenlerini oluştur"""
        self.setWindowTitle("Ürün Ekle/Düzenle")
        self.setMinimumWidth(600)
        
        layout = QVBoxLayout(self)
        
        # Form layout
        form = QFormLayout()
        
        # Ürün adı
        self.name_edit = QLineEdit()
        form.addRow("Ürün Adı:", self.name_edit)
        
        # SKU
        self.sku_edit = QLineEdit()
        form.addRow("SKU:", self.sku_edit)
        
        # Açıklama
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        form.addRow("Açıklama:", self.description_edit)
        
        # Kısa açıklama
        self.short_description_edit = QTextEdit()
        self.short_description_edit.setMaximumHeight(60)
        form.addRow("Kısa Açıklama:", self.short_description_edit)
        
        # Normal fiyat
        self.regular_price_spin = QDoubleSpinBox()
        self.regular_price_spin.setMaximum(999999.99)
        self.regular_price_spin.setDecimals(2)
        form.addRow("Normal Fiyat:", self.regular_price_spin)
        
        # İndirimli fiyat
        self.sale_price_spin = QDoubleSpinBox()
        self.sale_price_spin.setMaximum(999999.99)
        self.sale_price_spin.setDecimals(2)
        form.addRow("İndirimli Fiyat:", self.sale_price_spin)
        
        # Stok miktarı
        self.stock_quantity_spin = QSpinBox()
        self.stock_quantity_spin.setMaximum(999999)
        form.addRow("Stok Miktarı:", self.stock_quantity_spin)
        
        # Stok durumu
        self.stock_status_combo = QComboBox()
        self.stock_status_combo.addItems(["instock", "outofstock", "onbackorder"])
        form.addRow("Stok Durumu:", self.stock_status_combo)
        
        # Ağırlık
        self.weight_spin = QDoubleSpinBox()
        self.weight_spin.setMaximum(999.99)
        self.weight_spin.setDecimals(2)
        form.addRow("Ağırlık (kg):", self.weight_spin)
        
        # Öne çıkan
        self.featured_check = QCheckBox()
        form.addRow("Öne Çıkan:", self.featured_check)
        
        # Katalogda görünür
        self.catalog_visible_check = QCheckBox()
        form.addRow("Katalogda Görünür:", self.catalog_visible_check)
        
        # Aktif
        self.active_check = QCheckBox()
        form.addRow("Aktif:", self.active_check)
        
        layout.addLayout(form)
        
        # Butonlar
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Kaydet")
        self.save_button.setIcon(QIcon(ICONS.SAVE))
        self.save_button.clicked.connect(self.save_product)
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("İptal")
        self.cancel_button.setIcon(QIcon(ICONS.CANCEL))
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def load_product(self):
        """Ürün bilgilerini yükle"""
        self.name_edit.setText(self.product.name)
        self.sku_edit.setText(self.product.sku)
        self.description_edit.setText(self.product.description)
        self.short_description_edit.setText(self.product.short_description)
        self.regular_price_spin.setValue(self.product.regular_price or 0)
        self.sale_price_spin.setValue(self.product.sale_price or 0)
        self.stock_quantity_spin.setValue(self.product.stock_quantity or 0)
        self.stock_status_combo.setCurrentText(self.product.stock_status or "instock")
        self.weight_spin.setValue(self.product.weight or 0)
        self.featured_check.setChecked(self.product.featured or False)
        self.catalog_visible_check.setChecked(self.product.catalog_visibility == "visible")
        self.active_check.setChecked(self.product.is_active or False)
    
    def save_product(self):
        """Ürünü kaydet"""
        try:
            data = {
                "name": self.name_edit.text(),
                "sku": self.sku_edit.text(),
                "description": self.description_edit.toPlainText(),
                "short_description": self.short_description_edit.toPlainText(),
                "regular_price": self.regular_price_spin.value(),
                "sale_price": self.sale_price_spin.value(),
                "stock_quantity": self.stock_quantity_spin.value(),
                "stock_status": self.stock_status_combo.currentText(),
                "weight": self.weight_spin.value(),
                "featured": self.featured_check.isChecked(),
                "catalog_visibility": "visible" if self.catalog_visible_check.isChecked() else "hidden",
                "is_active": self.active_check.isChecked()
            }
            
            with self.db.session_scope() as session:
                if self.product:
                    # Mevcut ürünü güncelle
                    for key, value in data.items():
                        setattr(self.product, key, value)
                    session.merge(self.product)
                else:
                    # Yeni ürün oluştur
                    product = Product(**data)
                    session.add(product)
            
            self.accept()
            
        except Exception as e:
            self.logger.error(f"Ürün kaydedilirken hata: {str(e)}")
            QMessageBox.critical(
                self,
                "Hata",
                "Ürün kaydedilirken bir hata oluştu!"
            )

class ProductManagerWidget(QWidget):
    """Ürün yönetimi widget'ı"""
    
    def __init__(self):
        super().__init__()
        self.settings = Settings()
        self.logger = setup_logger(self.__class__.__name__)
        self.db = DatabaseManager()
        
        self.setup_ui()
        self.load_products()
    
    def setup_ui(self):
        """UI bileşenlerini oluştur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Başlık
        title = QLabel("Ürün Yönetimi")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #333333;
        """)
        layout.addWidget(title)
        
        # Üst toolbar
        toolbar = QHBoxLayout()
        
        # Arama kutusu
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Ürün ara...")
        self.search_edit.textChanged.connect(self.filter_products)
        toolbar.addWidget(self.search_edit)
        
        # Filtre combobox
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "Tümü",
            "Aktif",
            "Pasif",
            "Stokta Var",
            "Stokta Yok",
            "İndirimli",
            "Öne Çıkan"
        ])
        self.filter_combo.currentTextChanged.connect(self.filter_products)
        toolbar.addWidget(self.filter_combo)
        
        # Yeni ekle butonu
        add_button = QPushButton("Yeni Ürün")
        add_button.setIcon(QIcon(ICONS.ADD))
        add_button.clicked.connect(self.add_product)
        toolbar.addWidget(add_button)
        
        layout.addLayout(toolbar)
        
        # Ürün tablosu
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "SKU",
            "Ürün Adı",
            "Fiyat",
            "Stok",
            "Durum",
            "WooCommerce",
            "Wolvox",
            "İşlemler"
        ])
        
        # Tablo ayarları
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setAlternatingRowColors(True)
        
        layout.addWidget(self.table)
    
    def load_products(self):
        """Ürünleri yükle"""
        try:
            with self.db.session_scope() as session:
                products = session.query(Product).all()
                
                self.table.setRowCount(len(products))
                
                for row, product in enumerate(products):
                    # SKU
                    self.table.setItem(
                        row, 0,
                        QTableWidgetItem(product.sku)
                    )
                    
                    # Ürün adı
                    self.table.setItem(
                        row, 1,
                        QTableWidgetItem(product.name)
                    )
                    
                    # Fiyat
                    price = product.sale_price or product.regular_price
                    self.table.setItem(
                        row, 2,
                        QTableWidgetItem(f"₺{price:,.2f}")
                    )
                    
                    # Stok
                    self.table.setItem(
                        row, 3,
                        QTableWidgetItem(str(product.stock_quantity))
                    )
                    
                    # Durum
                    status = "Aktif" if product.is_active else "Pasif"
                    self.table.setItem(
                        row, 4,
                        QTableWidgetItem(status)
                    )
                    
                    # WooCommerce ID
                    woo_id = str(product.woo_id) if product.woo_id else "-"
                    self.table.setItem(
                        row, 5,
                        QTableWidgetItem(woo_id)
                    )
                    
                    # Wolvox ID
                    wolvox_id = product.wolvox_id or "-"
                    self.table.setItem(
                        row, 6,
                        QTableWidgetItem(wolvox_id)
                    )
                    
                    # İşlem butonları
                    actions_widget = QWidget()
                    actions_layout = QHBoxLayout(actions_widget)
                    actions_layout.setContentsMargins(0, 0, 0, 0)
                    
                    # Düzenle butonu
                    edit_button = QPushButton()
                    edit_button.setIcon(QIcon(ICONS.EDIT))
                    edit_button.clicked.connect(
                        lambda checked, p=product: self.edit_product(p)
                    )
                    actions_layout.addWidget(edit_button)
                    
                    # Sil butonu
                    delete_button = QPushButton()
                    delete_button.setIcon(QIcon(ICONS.DELETE))
                    delete_button.clicked.connect(
                        lambda checked, p=product: self.delete_product(p)
                    )
                    actions_layout.addWidget(delete_button)
                    
                    self.table.setCellWidget(row, 7, actions_widget)
                    
        except Exception as e:
            self.logger.error(f"Ürünler yüklenirken hata: {str(e)}")
            QMessageBox.critical(
                self,
                "Hata",
                "Ürünler yüklenirken bir hata oluştu!"
            )
    
    def filter_products(self):
        """Ürünleri filtrele"""
        search_text = self.search_edit.text().lower()
        filter_text = self.filter_combo.currentText()
        
        for row in range(self.table.rowCount()):
            show = True
            
            # Metin araması
            if search_text:
                found = False
                for col in range(self.table.columnCount() - 1):  # Son sütun hariç
                    item = self.table.item(row, col)
                    if item and search_text in item.text().lower():
                        found = True
                        break
                if not found:
                    show = False
            
            # Filtre
            if show and filter_text != "Tümü":
                status_item = self.table.item(row, 4)
                if filter_text == "Aktif" and status_item.text() != "Aktif":
                    show = False
                elif filter_text == "Pasif" and status_item.text() != "Pasif":
                    show = False
                # Diğer filtreler...
            
            self.table.setRowHidden(row, not show)
    
    def add_product(self):
        """Yeni ürün ekle"""
        dialog = ProductDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_products()
    
    def edit_product(self, product):
        """Ürün düzenle"""
        dialog = ProductDialog(self, product)
        if dialog.exec_() == QDialog.Accepted:
            self.load_products()
    
    def delete_product(self, product):
        """Ürün sil"""
        reply = QMessageBox.question(
            self,
            "Ürün Sil",
            f"{product.name} ürününü silmek istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                with self.db.session_scope() as session:
                    session.delete(product)
                self.load_products()
            except Exception as e:
                self.logger.error(f"Ürün silinirken hata: {str(e)}")
                QMessageBox.critical(
                    self,
                    "Hata",
                    "Ürün silinirken bir hata oluştu!"
                )
