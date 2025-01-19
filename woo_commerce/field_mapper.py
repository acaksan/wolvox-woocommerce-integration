import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QComboBox, QPushButton, QLabel, QScrollArea,
                           QMessageBox, QTabWidget, QTextEdit, QGroupBox, QLineEdit,
                           QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
                           QSpinBox, QDialog, QDialogButtonBox, QAction, QMenuBar,
                           QFileDialog, QTreeWidget, QTreeWidgetItem)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor
import json
import os
from dotenv import load_dotenv
import fdb
import requests
from datetime import datetime
from category_mapper import CategoryMapperWindow

class CustomRuleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Özel Kural Ekle')
        self.setModal(True)
        layout = QVBoxLayout(self)
        
        # Kural adı
        name_layout = QHBoxLayout()
        name_label = QLabel('Kural Adı:')
        self.name_edit = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # SQL sorgusu
        sql_label = QLabel('SQL Sorgusu:')
        self.sql_edit = QTextEdit()
        layout.addWidget(sql_label)
        layout.addWidget(self.sql_edit)
        
        # WooCommerce alanı
        woo_layout = QHBoxLayout()
        woo_label = QLabel('WooCommerce Alanı:')
        self.woo_combo = QComboBox()
        self.woo_combo.addItems(['name', 'description', 'regular_price', 'sale_price', 'stock_quantity'])
        woo_layout.addWidget(woo_label)
        woo_layout.addWidget(self.woo_combo)
        layout.addLayout(woo_layout)
        
        # Butonlar
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

class CategoryMapperDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Kategori Eşleştirme')
        self.setModal(True)
        self.resize(600, 400)
        layout = QVBoxLayout(self)
        
        # Kategori tablosu
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['Wolvox Grubu', 'WooCommerce Kategorisi', 'Aktif'])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        layout.addWidget(self.table)
        
        # Butonlar
        button_layout = QHBoxLayout()
        add_btn = QPushButton('Yeni Ekle')
        add_btn.clicked.connect(self.add_row)
        save_btn = QPushButton('Kaydet')
        save_btn.clicked.connect(self.save_categories)
        button_layout.addWidget(add_btn)
        button_layout.addWidget(save_btn)
        layout.addLayout(button_layout)
        
        self.load_categories()
    
    def add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setCellWidget(row, 2, QCheckBox())
        
    def load_categories(self):
        try:
            if os.path.exists('category_mappings.json'):
                with open('category_mappings.json', 'r', encoding='utf-8') as f:
                    categories = json.load(f)
                
                for category in categories:
                    row = self.table.rowCount()
                    self.table.insertRow(row)
                    self.table.setItem(row, 0, QTableWidgetItem(category['wolvox_group']))
                    self.table.setItem(row, 1, QTableWidgetItem(category['woo_category']))
                    checkbox = QCheckBox()
                    checkbox.setChecked(category['active'])
                    self.table.setCellWidget(row, 2, checkbox)
        except Exception as e:
            QMessageBox.warning(self, 'Uyarı', f'Kategoriler yüklenirken hata: {str(e)}')
    
    def save_categories(self):
        categories = []
        for row in range(self.table.rowCount()):
            wolvox_group = self.table.item(row, 0)
            woo_category = self.table.item(row, 1)
            active = self.table.cellWidget(row, 2)
            
            if wolvox_group and woo_category:
                categories.append({
                    'wolvox_group': wolvox_group.text(),
                    'woo_category': woo_category.text(),
                    'active': active.isChecked()
                })
        
        try:
            with open('category_mappings.json', 'w', encoding='utf-8') as f:
                json.dump(categories, f, ensure_ascii=False, indent=4)
            QMessageBox.information(self, 'Başarılı', 'Kategoriler kaydedildi!')
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Kategoriler kaydedilirken hata: {str(e)}')

class FieldMapperWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Wolvox - WooCommerce Alan Eşleştirme')
        self.setGeometry(100, 100, 1200, 800)

        # WooCommerce alanları
        self.woo_fields = [
            'name',
            'type',
            'regular_price',
            'sale_price',
            'description',
            'short_description',
            'categories',
            'images',
            'stock_quantity',
            'stock_status',
            'weight',
            'dimensions',
            'sku',
            'attributes',
            'meta_data'
        ]

        # Ana widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Ana düzen
        main_layout = QVBoxLayout(central_widget)
        
        # Üst kısım - Tab widget
        self.tab_widget = QTabWidget()
        
        # Alan Eşleştirme sekmesi
        mapping_tab = QWidget()
        mapping_layout = QHBoxLayout()
        
        # Sol panel - Eşleştirmeler
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        # Örnek ürün seçici
        sample_layout = QHBoxLayout()
        self.sample_combo = QComboBox()
        self.sample_combo.setMinimumWidth(300)
        refresh_button = QPushButton('Ürünleri Yenile')
        refresh_button.clicked.connect(self.load_sample_products)
        sample_layout.addWidget(QLabel('Örnek Ürün:'))
        sample_layout.addWidget(self.sample_combo)
        sample_layout.addWidget(refresh_button)
        left_layout.addLayout(sample_layout)
        
        # Alan eşleştirmeleri
        self.mapping_widgets = {}
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        for field in self.woo_fields:
            field_layout = QHBoxLayout()
            label = QLabel(f"{field}:")
            label.setMinimumWidth(150)
            combo = QComboBox()
            combo.setMinimumWidth(300)
            combo.addItem('-- Seçiniz --')
            field_layout.addWidget(label)
            field_layout.addWidget(combo)
            self.mapping_widgets[field] = combo
            scroll_layout.addLayout(field_layout)
        
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        left_layout.addWidget(scroll_area)
        
        # Butonlar
        buttons_layout = QHBoxLayout()
        
        # Önizleme butonu
        preview_button = QPushButton('Önizle')
        preview_button.clicked.connect(self.update_preview)
        buttons_layout.addWidget(preview_button)
        
        # Kategori eşleştirme butonu
        category_button = QPushButton('Kategori Eşleştirme')
        category_button.clicked.connect(self.show_category_mapper)
        buttons_layout.addWidget(category_button)
        
        left_layout.addLayout(buttons_layout)
        
        left_panel.setLayout(left_layout)
        
        # Sağ panel - Önizleme
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        preview_label = QLabel('Önizleme:')
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        right_layout.addWidget(preview_label)
        right_layout.addWidget(self.preview_text)
        right_panel.setLayout(right_layout)
        
        # Panelleri ana düzene ekle
        mapping_layout.addWidget(left_panel, 1)
        mapping_layout.addWidget(right_panel, 1)
        mapping_tab.setLayout(mapping_layout)
        
        # Özel Kurallar sekmesi
        rules_tab = QWidget()
        rules_layout = QVBoxLayout()
        
        # Kural tablosu
        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(4)
        self.rules_table.setHorizontalHeaderLabels(['Kural Adı', 'SQL Sorgusu', 'WooCommerce Alanı', 'Aktif'])
        self.rules_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        # Kural ekleme düğmeleri
        buttons_layout = QHBoxLayout()
        add_button = QPushButton('Kural Ekle')
        add_button.clicked.connect(self.add_rule)
        remove_button = QPushButton('Seçili Kuralı Sil')
        remove_button.clicked.connect(self.remove_rule)
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(remove_button)
        
        rules_layout.addWidget(self.rules_table)
        rules_layout.addLayout(buttons_layout)
        rules_tab.setLayout(rules_layout)
        
        # Ürün sekmesi
        product_tab = QWidget()
        product_layout = QVBoxLayout(product_tab)
        
        # Ürün butonları
        open_manager_button = QPushButton("Ürün Yöneticisini Aç")
        open_manager_button.clicked.connect(self.open_product_manager)
        product_layout.addWidget(open_manager_button)
        
        sync_all_button = QPushButton("Tüm Ürünleri Senkronize Et")
        sync_all_button.clicked.connect(self.sync_all_products)
        product_layout.addWidget(sync_all_button)
        
        sync_stock_button = QPushButton("Stok Miktarlarını Senkronize Et")
        sync_stock_button.clicked.connect(self.sync_stock_quantities)
        product_layout.addWidget(sync_stock_button)
        
        match_products_button = QPushButton("Ürün Eşleştirmelerini Göster")
        match_products_button.clicked.connect(self.show_product_matches)
        product_layout.addWidget(match_products_button)
        
        product_layout.addStretch()
        
        # Sekmeleri ekle
        self.tab_widget.addTab(mapping_tab, 'Alan Eşleştirme')
        self.tab_widget.addTab(rules_tab, 'Özel Kurallar')
        self.tab_widget.addTab(product_tab, 'Ürün Yönetimi')
        
        # Ana menü
        menubar = self.menuBar()
        file_menu = menubar.addMenu('Dosya')
        tools_menu = menubar.addMenu('Araçlar')
        
        # Dosya menüsü
        save_action = QAction('Kaydet', self)
        save_action.triggered.connect(self.save_mappings)
        load_action = QAction('Yükle', self)
        load_action.triggered.connect(self.load_mappings)
        file_menu.addAction(save_action)
        file_menu.addAction(load_action)
        
        # Araçlar menüsü
        test_action = QAction('Bağlantıları Test Et', self)
        test_action.triggered.connect(self.test_connections)
        tools_menu.addAction(test_action)
        
        main_layout.addWidget(self.tab_widget)
        
        # Başlangıç yüklemeleri
        self.load_sample_products()
        self.load_db_fields()
        self.load_saved_rules()
        self.load_existing_mappings()
    
    def setStyle(self):
        """Arayüz stilini ayarla"""
        # Yazı tipi
        font = QFont('Segoe UI', 10)
        self.setFont(font)
        
        # Renkler
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
        palette.setColor(QPalette.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
        palette.setColor(QPalette.Text, QColor(0, 0, 0))
        palette.setColor(QPalette.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
        self.setPalette(palette)
    
    def show_category_mapper(self):
        """Kategori eşleştirme penceresini göster"""
        dialog = CategoryMapperWindow(self)
        dialog.show()
    
    def add_rule(self):
        """Yeni özel kural ekle"""
        dialog = CustomRuleDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            row = self.rules_table.rowCount()
            self.rules_table.insertRow(row)
            self.rules_table.setItem(row, 0, QTableWidgetItem(dialog.name_edit.text()))
            self.rules_table.setItem(row, 1, QTableWidgetItem(dialog.sql_edit.toPlainText()))
            self.rules_table.setItem(row, 2, QTableWidgetItem(dialog.woo_combo.currentText()))
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            self.rules_table.setCellWidget(row, 3, checkbox)
    
    def remove_rule(self):
        """Seçili özel kuralı sil"""
        row = self.rules_table.currentRow()
        if row != -1:
            self.rules_table.removeRow(row)
    
    def load_db_fields(self):
        """Veritabanından alan isimlerini al"""
        try:
            con = self.get_db_connection()
            if not con:
                return
            
            cur = con.cursor()
            
            # STOK tablosunun yapısını al
            cur.execute("""
                SELECT RDB$FIELD_NAME 
                FROM RDB$RELATION_FIELDS 
                WHERE RDB$RELATION_NAME = 'STOK'
                ORDER BY RDB$FIELD_POSITION
            """)
            
            fields = [field[0].strip() for field in cur.fetchall()]
            
            # STOKHR tablosunun yapısını al
            cur.execute("""
                SELECT RDB$FIELD_NAME 
                FROM RDB$RELATION_FIELDS 
                WHERE RDB$RELATION_NAME = 'STOKHR'
                ORDER BY RDB$FIELD_POSITION
            """)
            
            fields.extend([f"STOKHR.{field[0].strip()}" for field in cur.fetchall()])
            
            # STOK_FIYAT tablosunun yapısını al
            cur.execute("""
                SELECT RDB$FIELD_NAME 
                FROM RDB$RELATION_FIELDS 
                WHERE RDB$RELATION_NAME = 'STOK_FIYAT'
                ORDER BY RDB$FIELD_POSITION
            """)
            
            fields.extend([f"STOK_FIYAT.{field[0].strip()}" for field in cur.fetchall()])
            
            con.close()
            
            # Alan eşleştirmeleri için veritabanı alanlarını ekle
            for combo in self.mapping_widgets.values():
                combo.addItems(fields)
        
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Veritabanı alanları alınırken hata: {str(e)}')
    
    def load_sample_products(self):
        """Örnek ürünleri yükle"""
        try:
            con = self.get_db_connection()
            if not con:
                return
            
            cur = con.cursor()
            
            # Aktif ve web'de görünür olan ürünleri al
            cur.execute("""
                SELECT FIRST 20 s.STOKKODU, s.STOK_ADI 
                FROM STOK s
                WHERE s.AKTIF = 1 
                AND s.WEBDE_GORUNSUN = 1
                AND s.STOK_ADI IS NOT NULL
                AND s.STOK_ADI <> ''
                ORDER BY s.STOK_ADI
            """)
            
            products = cur.fetchall()
            
            self.sample_combo.clear()
            for product in products:
                self.sample_combo.addItem(f"{product[1]} ({product[0]})", product[0])
            
            con.close()
            
        except Exception as e:
            QMessageBox.warning(self, 'Uyarı', f'Örnek ürünler yüklenirken hata: {str(e)}')
    
    def update_preview(self):
        """Ön izlemeyi güncelle"""
        try:
            if self.sample_combo.currentData():
                con = self.get_db_connection()
                if not con:
                    return
                
                cur = con.cursor()
                
                # Ürün verilerini al
                product_data = {}
                for woo_field, combo in self.mapping_widgets.items():
                    if combo.currentText() != '-- Seçiniz --':
                        field = combo.currentText()
                        table = 'STOK'
                        if '.' in field:
                            table, field = field.split('.')
                        
                        cur.execute(f"""
                            SELECT {field}
                            FROM {table}
                            WHERE STOKKODU = ?
                        """, (self.sample_combo.currentData(),))
                        
                        value = cur.fetchone()
                        if value:
                            product_data[woo_field] = value[0]
                
                # Özel kuralları uygula
                for row in range(self.rules_table.rowCount()):
                    if self.rules_table.cellWidget(row, 3).isChecked():
                        sql = self.rules_table.item(row, 1).text()
                        woo_field = self.rules_table.item(row, 2).text()
                        
                        cur.execute(sql, (self.sample_combo.currentData(),))
                        value = cur.fetchone()
                        if value:
                            product_data[woo_field] = value[0]
                
                con.close()
                
                # Ön izleme metnini oluştur
                preview = "WooCommerce'de Görünüm:\n\n"
                for field, value in product_data.items():
                    preview += f"{field}: {value}\n"
                
                self.preview_text.setText(preview)
                
        except Exception as e:
            self.preview_text.setText(f"Ön izleme oluşturulurken hata: {str(e)}")
    
    def test_connections(self):
        """Veritabanı ve WooCommerce bağlantılarını test et"""
        message = ""
        
        # Veritabanı bağlantısını test et
        try:
            con = self.get_db_connection()
            if con:
                con.close()
                message += "✓ Veritabanı bağlantısı başarılı\n"
            else:
                message += "✗ Veritabanı bağlantısı başarısız\n"
        except Exception as e:
            message += f"✗ Veritabanı bağlantısı başarısız: {str(e)}\n"
        
        # WooCommerce bağlantısını test et
        try:
            url = os.getenv('WOOCOMMERCE_URL')
            consumer_key = os.getenv('WOOCOMMERCE_CONSUMER_KEY')
            consumer_secret = os.getenv('WOOCOMMERCE_CONSUMER_SECRET')
            
            response = requests.get(
                f"{url}/wp-json/wc/v3/products",
                auth=(consumer_key, consumer_secret),
                params={'per_page': 1},
                verify=False
            )
            
            if response.status_code == 200:
                message += "✓ WooCommerce bağlantısı başarılı"
            else:
                message += f"✗ WooCommerce bağlantısı başarısız: HTTP {response.status_code}"
                
        except Exception as e:
            message += f"✗ WooCommerce bağlantısı başarısız: {str(e)}"
        
        QMessageBox.information(self, 'Bağlantı Testi', message)

    def get_db_connection(self):
        """Veritabanı bağlantısı oluştur"""
        try:
            load_dotenv()
            
            # Firebird client path'ini ayarla
            fb_client_path = os.getenv('FIREBIRD_CLIENT_PATH')
            if fb_client_path and os.path.exists(fb_client_path):
                fdb.load_api(fb_client_path)
            
            # Veritabanı bağlantısı
            con = fdb.connect(
                dsn=f"{os.getenv('WOLVOX_DB_HOST')}:{os.getenv('WOLVOX_DB_PATH')}",
                user=os.getenv('WOLVOX_DB_USER'),
                password=os.getenv('WOLVOX_DB_PASSWORD')
            )
            return con
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Veritabanı bağlantısı kurulamadı: {str(e)}')
            return None

    def load_saved_rules(self):
        """Özel kuralları yükle"""
        try:
            if os.path.exists('custom_rules.json'):
                with open('custom_rules.json', 'r', encoding='utf-8') as f:
                    rules = json.load(f)
                
                for rule in rules:
                    row = self.rules_table.rowCount()
                    self.rules_table.insertRow(row)
                    self.rules_table.setItem(row, 0, QTableWidgetItem(rule['name']))
                    self.rules_table.setItem(row, 1, QTableWidgetItem(rule['sql']))
                    self.rules_table.setItem(row, 2, QTableWidgetItem(rule['woo_field']))
                    checkbox = QCheckBox()
                    checkbox.setChecked(rule['active'])
                    self.rules_table.setCellWidget(row, 3, checkbox)
        except Exception as e:
            QMessageBox.warning(self, 'Uyarı', f'Özel kurallar yüklenirken hata: {str(e)}')
    
    def load_existing_mappings(self):
        """Varolan eşleştirmeleri yükle"""
        try:
            if os.path.exists('mappings.json'):
                with open('mappings.json', 'r', encoding='utf-8') as f:
                    mappings = json.load(f)
                
                for woo_field, db_field in mappings.items():
                    if woo_field in self.mapping_widgets:
                        self.mapping_widgets[woo_field].setCurrentText(db_field)
        except Exception as e:
            QMessageBox.warning(self, 'Uyarı', f'Eşleştirmeler yüklenirken hata: {str(e)}')
    
    def load_mappings(self):
        """Eşleştirmeleri yükle"""
        try:
            # Dosya seçme dialog'unu göster
            file_name, _ = QFileDialog.getOpenFileName(
                self,
                'Eşleştirme Dosyası Seç',
                '',
                'JSON Dosyaları (*.json)'
            )
            
            if file_name:
                with open(file_name, 'r', encoding='utf-8') as f:
                    mappings = json.load(f)
                
                # Eşleştirmeleri yükle
                for woo_field, db_field in mappings.items():
                    if woo_field in self.mapping_widgets:
                        combo = self.mapping_widgets[woo_field]
                        index = combo.findText(db_field)
                        if index >= 0:
                            combo.setCurrentIndex(index)
                
                QMessageBox.information(self, 'Başarılı', 'Eşleştirmeler yüklendi!')
                
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Eşleştirmeler yüklenirken hata: {str(e)}')
    
    def save_mappings(self):
        """Eşleştirmeleri kaydet"""
        mappings = {}
        for woo_field, combo in self.mapping_widgets.items():
            db_field = combo.currentText()
            if db_field != '-- Seçiniz --':
                mappings[woo_field] = db_field
        
        try:
            with open('mappings.json', 'w', encoding='utf-8') as f:
                json.dump(mappings, f, ensure_ascii=False, indent=4)
            QMessageBox.information(self, 'Başarılı', 'Eşleştirmeler kaydedildi!')
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Eşleştirmeler kaydedilirken hata: {str(e)}')

    def sync_all_products(self):
        """Tüm ürünleri senkronize et"""
        try:
            from woo_commerce.product_sync import ProductSync
            sync = ProductSync()
            sync.sync_all_products()
            QMessageBox.information(self, "Başarılı", "Ürün senkronizasyonu tamamlandı!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Ürün senkronizasyonu sırasında hata oluştu: {str(e)}")
    
    def sync_stock_quantities(self):
        """Stok miktarlarını senkronize et"""
        try:
            from woo_commerce.product_sync import ProductSync
            sync = ProductSync()
            sync.sync_stock_quantities()
            QMessageBox.information(self, "Başarılı", "Stok senkronizasyonu tamamlandı!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Stok senkronizasyonu sırasında hata oluştu: {str(e)}")
    
    def show_product_matches(self):
        """Ürün eşleştirmelerini göster"""
        try:
            from woo_commerce.product_sync import ProductSync
            sync = ProductSync()
            sync.match_products_by_stock_number()
            QMessageBox.information(self, "Başarılı", "Ürün eşleştirmeleri gösterildi!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Ürün eşleştirmeleri gösterilirken hata oluştu: {str(e)}")

    def open_product_manager(self):
        """Ürün yöneticisini aç"""
        try:
            from woo_commerce.product_manager import ProductManagerWindow
            self.product_manager = ProductManagerWindow()
            self.product_manager.show()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Ürün yöneticisi açılırken hata oluştu: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = FieldMapperWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
