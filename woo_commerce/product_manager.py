import sys
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                           QTableWidget, QTableWidgetItem, QTabWidget,
                           QMessageBox, QDialog, QFormLayout, QTextEdit,
                           QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

# Ana dizini Python path'ine ekle
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from woo_commerce.product_sync import ProductSync
from wolvox.product_reader import WolvoxProductReader
from woo_commerce.woocommerce_client import WooCommerceClient

class ProductDetailDialog(QDialog):
    def __init__(self, product_data, platform, parent=None):
        super().__init__(parent)
        self.product_data = product_data
        self.platform = platform
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle(f"Ürün Detayları - {self.platform}")
        self.setMinimumWidth(600)
        
        layout = QFormLayout(self)
        
        # Temel bilgiler
        self.name_edit = QLineEdit(self.product_data.get('name', ''))
        layout.addRow("Ürün Adı:", self.name_edit)
        
        self.sku_edit = QLineEdit(self.product_data.get('sku', ''))
        layout.addRow("Stok Kodu:", self.sku_edit)
        
        self.price_edit = QDoubleSpinBox()
        self.price_edit.setMaximum(999999.99)
        self.price_edit.setValue(float(self.product_data.get('price', 0)))
        layout.addRow("Fiyat:", self.price_edit)
        
        self.stock_edit = QSpinBox()
        self.stock_edit.setMaximum(999999)
        self.stock_edit.setValue(int(self.product_data.get('stock_quantity', 0)))
        layout.addRow("Stok:", self.stock_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setText(self.product_data.get('description', ''))
        layout.addRow("Açıklama:", self.description_edit)
        
        # Platform spesifik alanlar
        if self.platform == 'Wolvox':
            self.active_checkbox = QCheckBox("Aktif")
            self.active_checkbox.setChecked(self.product_data.get('aktif', False))
            layout.addRow("", self.active_checkbox)
            
            self.web_visible_checkbox = QCheckBox("Web'de Görünsün")
            self.web_visible_checkbox.setChecked(self.product_data.get('webde_gorunsun', False))
            layout.addRow("", self.web_visible_checkbox)
        
        elif self.platform == 'WooCommerce':
            self.status_combo = QComboBox()
            self.status_combo.addItems(['publish', 'draft', 'private'])
            self.status_combo.setCurrentText(self.product_data.get('status', 'publish'))
            layout.addRow("Durum:", self.status_combo)
        
        # Butonlar
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("Kaydet")
        save_button.clicked.connect(self.accept)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("İptal")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addRow("", button_layout)
    
    def get_updated_data(self):
        data = {
            'name': self.name_edit.text(),
            'sku': self.sku_edit.text(),
            'price': str(self.price_edit.value()),
            'stock_quantity': self.stock_edit.value(),
            'description': self.description_edit.toPlainText()
        }
        
        if self.platform == 'Wolvox':
            data.update({
                'aktif': self.active_checkbox.isChecked(),
                'webde_gorunsun': self.web_visible_checkbox.isChecked()
            })
        elif self.platform == 'WooCommerce':
            data.update({
                'status': self.status_combo.currentText()
            })
        
        return data

class ProductManagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.wolvox = WolvoxProductReader()
        self.woo = WooCommerceClient()
        self.sync = ProductSync()
        self.setup_ui()
        self.load_products()
    
    def setup_ui(self):
        self.setWindowTitle("Ürün Yönetimi")
        self.setMinimumSize(1200, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Üst butonlar
        top_buttons = QHBoxLayout()
        
        refresh_button = QPushButton("Yenile")
        refresh_button.clicked.connect(self.load_products)
        top_buttons.addWidget(refresh_button)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Ara...")
        self.search_edit.textChanged.connect(self.filter_products)
        top_buttons.addWidget(self.search_edit)
        
        layout.addLayout(top_buttons)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Wolvox ürünleri
        wolvox_tab = QWidget()
        wolvox_layout = QVBoxLayout(wolvox_tab)
        
        self.wolvox_table = QTableWidget()
        self.wolvox_table.setColumnCount(8)
        self.wolvox_table.setHorizontalHeaderLabels([
            "Stok Kodu", "Ürün Adı", "Fiyat", "Stok", "Aktif", 
            "Web'de Görünsün", "Eşleşme Durumu", "Eşleşen Ürün"
        ])
        self.wolvox_table.doubleClicked.connect(lambda idx: self.show_product_details(idx, 'Wolvox'))
        wolvox_layout.addWidget(self.wolvox_table)
        
        self.tab_widget.addTab(wolvox_tab, "Wolvox Ürünleri")
        
        # WooCommerce ürünleri
        woo_tab = QWidget()
        woo_layout = QVBoxLayout(woo_tab)
        
        self.woo_table = QTableWidget()
        self.woo_table.setColumnCount(7)
        self.woo_table.setHorizontalHeaderLabels([
            "SKU", "Ürün Adı", "Fiyat", "Stok", "Durum", 
            "Eşleşme Durumu", "Eşleşen Ürün"
        ])
        self.woo_table.doubleClicked.connect(lambda idx: self.show_product_details(idx, 'WooCommerce'))
        woo_layout.addWidget(self.woo_table)
        
        self.tab_widget.addTab(woo_tab, "WooCommerce Ürünleri")
    
    def load_products(self):
        try:
            # Wolvox ürünleri
            wolvox_products = self.wolvox.get_all_products()
            self.wolvox_table.setRowCount(len(wolvox_products))
            
            # WooCommerce ürünleri
            woo_products = {}
            page = 1
            while True:
                products = self.woo.list_products(page=page)
                if not products:
                    break
                for product in products:
                    woo_products[product['sku']] = product
                page += 1
            
            self.woo_table.setRowCount(len(woo_products))
            
            # Wolvox tablosunu doldur
            for i, product in enumerate(wolvox_products):
                sku = product['stok_kodu']
                self.wolvox_table.setItem(i, 0, QTableWidgetItem(sku))
                self.wolvox_table.setItem(i, 1, QTableWidgetItem(product['stok_adi']))
                self.wolvox_table.setItem(i, 2, QTableWidgetItem(str(product['satis_fiyati1'])))
                
                stock = self.wolvox.get_product_stock(sku)
                self.wolvox_table.setItem(i, 3, QTableWidgetItem(str(stock)))
                
                active_item = QTableWidgetItem()
                active_item.setCheckState(Qt.Checked if product['aktif'] else Qt.Unchecked)
                self.wolvox_table.setItem(i, 4, active_item)
                
                web_item = QTableWidgetItem()
                web_item.setCheckState(Qt.Checked if product['webde_gorunsun'] else Qt.Unchecked)
                self.wolvox_table.setItem(i, 5, web_item)
                
                # Eşleşme durumu
                if sku in woo_products:
                    self.wolvox_table.setItem(i, 6, QTableWidgetItem("Eşleşti"))
                    self.wolvox_table.setItem(i, 7, QTableWidgetItem(woo_products[sku]['name']))
                    # Yeşil arka plan
                    for col in range(8):
                        self.wolvox_table.item(i, col).setBackground(QColor(200, 255, 200))
                else:
                    self.wolvox_table.setItem(i, 6, QTableWidgetItem("Eşleşmedi"))
                    self.wolvox_table.setItem(i, 7, QTableWidgetItem("-"))
            
            # WooCommerce tablosunu doldur
            i = 0
            for sku, product in woo_products.items():
                self.woo_table.setItem(i, 0, QTableWidgetItem(sku))
                self.woo_table.setItem(i, 1, QTableWidgetItem(product['name']))
                self.woo_table.setItem(i, 2, QTableWidgetItem(str(product['price'])))
                self.woo_table.setItem(i, 3, QTableWidgetItem(str(product.get('stock_quantity', 0))))
                self.woo_table.setItem(i, 4, QTableWidgetItem(product['status']))
                
                # Eşleşme durumu
                if any(p['stok_kodu'] == sku for p in wolvox_products):
                    self.woo_table.setItem(i, 5, QTableWidgetItem("Eşleşti"))
                    matched_product = next(p for p in wolvox_products if p['stok_kodu'] == sku)
                    self.woo_table.setItem(i, 6, QTableWidgetItem(matched_product['stok_adi']))
                    # Yeşil arka plan
                    for col in range(7):
                        self.woo_table.item(i, col).setBackground(QColor(200, 255, 200))
                else:
                    self.woo_table.setItem(i, 5, QTableWidgetItem("Eşleşmedi"))
                    self.woo_table.setItem(i, 6, QTableWidgetItem("-"))
                
                i += 1
            
            # Tablo sütunlarını otomatik genişlet
            self.wolvox_table.resizeColumnsToContents()
            self.woo_table.resizeColumnsToContents()
            
            QMessageBox.information(self, "Başarılı", "Ürünler yüklendi!")
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Ürünler yüklenirken hata oluştu: {str(e)}")
    
    def filter_products(self):
        search_text = self.search_edit.text().lower()
        
        # Wolvox tablosunu filtrele
        for i in range(self.wolvox_table.rowCount()):
            show_row = False
            for j in range(self.wolvox_table.columnCount()):
                item = self.wolvox_table.item(i, j)
                if item and search_text in item.text().lower():
                    show_row = True
                    break
            self.wolvox_table.setRowHidden(i, not show_row)
        
        # WooCommerce tablosunu filtrele
        for i in range(self.woo_table.rowCount()):
            show_row = False
            for j in range(self.woo_table.columnCount()):
                item = self.woo_table.item(i, j)
                if item and search_text in item.text().lower():
                    show_row = True
                    break
            self.woo_table.setRowHidden(i, not show_row)
    
    def show_product_details(self, index, platform):
        try:
            if platform == 'Wolvox':
                table = self.wolvox_table
                sku = table.item(index.row(), 0).text()
                product = next(p for p in self.wolvox.get_all_products() if p['stok_kodu'] == sku)
            else:  # WooCommerce
                table = self.woo_table
                sku = table.item(index.row(), 0).text()
                product = self.woo.get_product_by_sku(sku)
            
            dialog = ProductDetailDialog(product, platform, self)
            if dialog.exec_() == QDialog.Accepted:
                updated_data = dialog.get_updated_data()
                
                if platform == 'Wolvox':
                    # Wolvox güncellemesi burada yapılacak
                    pass
                else:  # WooCommerce
                    self.woo.update_product(product['id'], updated_data)
                
                self.load_products()  # Tabloları yenile
                QMessageBox.information(self, "Başarılı", "Ürün güncellendi!")
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Ürün detayları gösterilirken hata oluştu: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = ProductManagerWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
