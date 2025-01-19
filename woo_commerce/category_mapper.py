from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTreeWidget, QTreeWidgetItem, QPushButton, QLabel,
                             QMessageBox, QDialog, QLineEdit, QComboBox,
                             QAction, QFileDialog, QDialogButtonBox)
from PyQt5.QtCore import Qt
import os
import json
import fdb
from dotenv import load_dotenv
import requests

class CategoryMapperWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Kategori Eşleştirme')
        self.setGeometry(100, 100, 1400, 800)
        
        # Ana widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Ana düzen
        main_layout = QHBoxLayout(central_widget)
        
        # Sol panel - Wolvox kategorileri
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        # Başlık ve arama alanı
        left_header = QWidget()
        left_header_layout = QHBoxLayout()
        left_label = QLabel('Wolvox Kategorileri:')
        left_label.setStyleSheet('font-weight: bold; font-size: 14px;')
        self.wolvox_search = QLineEdit()
        self.wolvox_search.setPlaceholderText('Ara...')
        self.wolvox_search.textChanged.connect(self.filter_wolvox_tree)
        left_header_layout.addWidget(left_label)
        left_header_layout.addWidget(self.wolvox_search)
        left_header.setLayout(left_header_layout)
        
        # Kategori ağacı
        self.wolvox_tree = QTreeWidget()
        self.wolvox_tree.setHeaderLabels(['Kod', 'İsim', 'Durum'])
        self.wolvox_tree.setColumnWidth(0, 100)  # Kod sütunu
        self.wolvox_tree.setColumnWidth(1, 300)  # İsim sütunu
        self.wolvox_tree.setColumnWidth(2, 150)  # Durum sütunu
        self.wolvox_tree.itemClicked.connect(self.on_wolvox_item_clicked)
        
        left_layout.addWidget(left_header)
        left_layout.addWidget(self.wolvox_tree)
        left_panel.setLayout(left_layout)
        
        # Orta panel - Eşleştirme butonları
        middle_panel = QWidget()
        middle_layout = QVBoxLayout()
        
        map_button = QPushButton('Eşleştir >>')
        map_button.clicked.connect(self.map_categories)
        map_button.setStyleSheet('font-weight: bold; padding: 10px;')
        
        unmap_button = QPushButton('<< Kaldır')
        unmap_button.clicked.connect(self.unmap_categories)
        unmap_button.setStyleSheet('font-weight: bold; padding: 10px;')
        
        create_button = QPushButton('Yeni WooCommerce\nKategorisi Oluştur')
        create_button.clicked.connect(self.create_woo_category)
        create_button.setStyleSheet('font-weight: bold; padding: 10px;')
        
        middle_layout.addStretch()
        middle_layout.addWidget(map_button)
        middle_layout.addWidget(unmap_button)
        middle_layout.addWidget(create_button)
        middle_layout.addStretch()
        
        middle_panel.setLayout(middle_layout)
        
        # Sağ panel - WooCommerce kategorileri
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        # Başlık ve arama alanı
        right_header = QWidget()
        right_header_layout = QHBoxLayout()
        right_label = QLabel('WooCommerce Kategorileri:')
        right_label.setStyleSheet('font-weight: bold; font-size: 14px;')
        self.woo_search = QLineEdit()
        self.woo_search.setPlaceholderText('Ara...')
        self.woo_search.textChanged.connect(self.filter_woo_tree)
        right_header_layout.addWidget(right_label)
        right_header_layout.addWidget(self.woo_search)
        right_header.setLayout(right_header_layout)
        
        # Kategori ağacı
        self.woo_tree = QTreeWidget()
        self.woo_tree.setHeaderLabels(['ID', 'İsim', 'Durum'])
        self.woo_tree.setColumnWidth(0, 100)  # ID sütunu
        self.woo_tree.setColumnWidth(1, 300)  # İsim sütunu
        self.woo_tree.setColumnWidth(2, 150)  # Durum sütunu
        self.woo_tree.itemClicked.connect(self.on_woo_item_clicked)
        
        sync_button = QPushButton('WooCommerce Kategorilerini Güncelle')
        sync_button.clicked.connect(self.sync_woo_categories)
        sync_button.setStyleSheet('font-weight: bold; padding: 10px;')
        
        right_layout.addWidget(right_header)
        right_layout.addWidget(self.woo_tree)
        right_layout.addWidget(sync_button)
        right_panel.setLayout(right_layout)
        
        # Panelleri ana düzene ekle
        main_layout.addWidget(left_panel)
        main_layout.addWidget(middle_panel)
        main_layout.addWidget(right_panel)
        
        # Durum çubuğu
        self.statusBar().showMessage('Hazır')
        
        # Menü çubuğu
        menubar = self.menuBar()
        file_menu = menubar.addMenu('Dosya')
        
        export_action = QAction('Eşleştirmeleri Dışa Aktar', self)
        export_action.triggered.connect(self.export_mappings)
        file_menu.addAction(export_action)
        
        import_action = QAction('Eşleştirmeleri İçe Aktar', self)
        import_action.triggered.connect(self.import_mappings)
        file_menu.addAction(import_action)
        
        # Başlangıç yüklemeleri
        self.load_wolvox_categories()
        self.load_woo_categories()
        self.load_mappings()
    
    def filter_wolvox_tree(self):
        """Wolvox kategori ağacını filtrele"""
        search_text = self.wolvox_search.text().lower()
        self._filter_tree(self.wolvox_tree, search_text)
    
    def filter_woo_tree(self):
        """WooCommerce kategori ağacını filtrele"""
        search_text = self.woo_search.text().lower()
        self._filter_tree(self.woo_tree, search_text)
    
    def _filter_tree(self, tree, search_text):
        """Ağaç yapısını filtrele"""
        def _filter_item(item):
            # Öğenin kendisi eşleşiyor mu?
            item_matches = False
            for column in range(item.columnCount()):
                if search_text in item.text(column).lower():
                    item_matches = True
                    break
            
            # Alt öğeleri kontrol et
            child_visible = False
            for i in range(item.childCount()):
                if _filter_item(item.child(i)):
                    child_visible = True
            
            # Öğeyi göster/gizle
            item.setHidden(not (item_matches or child_visible))
            return item_matches or child_visible
        
        # Kök öğelerden başla
        for i in range(tree.topLevelItemCount()):
            _filter_item(tree.topLevelItem(i))
    
    def on_wolvox_item_clicked(self, item, column):
        """Wolvox kategori seçildiğinde"""
        # Eşleştirme durumunu güncelle
        self.update_mapping_status(item)
    
    def on_woo_item_clicked(self, item, column):
        """WooCommerce kategori seçildiğinde"""
        # Eşleştirme durumunu güncelle
        self.update_mapping_status(item)
    
    def update_mapping_status(self, item):
        """Seçili kategorinin eşleştirme durumunu güncelle"""
        try:
            if os.path.exists('category_mappings.json'):
                with open('category_mappings.json', 'r', encoding='utf-8') as f:
                    mappings = json.load(f)
                
                # Wolvox tarafında eşleştirmeleri kontrol et
                def check_wolvox_mapping(item):
                    wolvox_path = []
                    current = item
                    while current:
                        wolvox_path.insert(0, {'code': current.text(0), 'name': current.text(1)})
                        current = current.parent()
                    
                    key = '_'.join(item['code'] for item in wolvox_path)
                    if key in mappings:
                        return mappings[key]['woo_name']
                    return None
                
                # WooCommerce tarafında eşleştirmeleri kontrol et
                def check_woo_mapping(item):
                    woo_id = item.text(0)
                    for mapping in mappings.values():
                        if mapping['woo_id'] == woo_id:
                            return ' -> '.join(item['name'] for item in mapping['wolvox_path'])
                    return None
                
                # Durum sütununu güncelle
                if isinstance(item, QTreeWidgetItem):
                    if item.treeWidget() == self.wolvox_tree:
                        mapped_to = check_wolvox_mapping(item)
                        item.setText(2, f'→ {mapped_to}' if mapped_to else '')
                    else:
                        mapped_from = check_woo_mapping(item)
                        item.setText(2, f'← {mapped_from}' if mapped_from else '')
        
        except Exception as e:
            self.statusBar().showMessage(f'Eşleştirme durumu güncellenirken hata: {str(e)}')
    
    def create_woo_category(self):
        """Yeni WooCommerce kategorisi oluştur"""
        wolvox_item = self.wolvox_tree.currentItem()
        if not wolvox_item:
            QMessageBox.warning(self, 'Uyarı', 'Lütfen bir Wolvox kategorisi seçin!')
            return
        
        # Yeni kategori bilgilerini al
        dialog = QDialog(self)
        dialog.setWindowTitle('Yeni WooCommerce Kategorisi')
        dialog.setModal(True)
        
        layout = QVBoxLayout()
        
        name_layout = QHBoxLayout()
        name_label = QLabel('Kategori Adı:')
        name_edit = QLineEdit()
        name_edit.setText(wolvox_item.text(1))  # Varsayılan olarak Wolvox kategori adını kullan
        name_layout.addWidget(name_label)
        name_layout.addWidget(name_edit)
        
        parent_layout = QHBoxLayout()
        parent_label = QLabel('Üst Kategori:')
        parent_combo = QComboBox()
        parent_combo.addItem('-- Üst Kategori Yok --', 0)
        
        # Mevcut WooCommerce kategorilerini combo box'a ekle
        def add_categories_to_combo(item, prefix=''):
            for i in range(item.childCount()):
                child = item.child(i)
                parent_combo.addItem(prefix + child.text(1), child.text(0))
                add_categories_to_combo(child, prefix + '  ')
        
        for i in range(self.woo_tree.topLevelItemCount()):
            item = self.woo_tree.topLevelItem(i)
            parent_combo.addItem(item.text(1), item.text(0))
            add_categories_to_combo(item, '  ')
        
        parent_layout.addWidget(parent_label)
        parent_layout.addWidget(parent_combo)
        
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        
        layout.addLayout(name_layout)
        layout.addLayout(parent_layout)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            try:
                # WooCommerce API bilgileri
                url = os.getenv('WOOCOMMERCE_URL')
                consumer_key = os.getenv('WOOCOMMERCE_CONSUMER_KEY')
                consumer_secret = os.getenv('WOOCOMMERCE_CONSUMER_SECRET')
                
                # Kategoriyi oluştur
                data = {
                    'name': name_edit.text(),
                    'parent': int(parent_combo.currentData())
                }
                
                response = requests.post(
                    f"{url}/wp-json/wc/v3/products/categories",
                    auth=(consumer_key, consumer_secret),
                    json=data
                )
                
                if response.status_code == 201:
                    QMessageBox.information(self, 'Başarılı', 'Kategori oluşturuldu!')
                    
                    # Kategorileri yeniden yükle
                    self.load_woo_categories()
                    
                    # Yeni kategoriyi otomatik olarak eşleştir
                    new_category = response.json()
                    self.map_to_new_category(wolvox_item, new_category)
                else:
                    QMessageBox.warning(self, 'Uyarı', 'Kategori oluşturulamadı!')
                
            except Exception as e:
                QMessageBox.warning(self, 'Uyarı', f'Kategori oluşturulurken hata: {str(e)}')
    
    def map_to_new_category(self, wolvox_item, woo_category):
        """Yeni oluşturulan WooCommerce kategorisini Wolvox kategorisi ile eşleştir"""
        try:
            mappings = {}
            if os.path.exists('category_mappings.json'):
                with open('category_mappings.json', 'r', encoding='utf-8') as f:
                    mappings = json.load(f)
            
            # Eşleştirmeyi kaydet
            wolvox_path = []
            item = wolvox_item
            while item:
                wolvox_path.insert(0, {'code': item.text(0), 'name': item.text(1)})
                item = item.parent()
            
            key = '_'.join(item['code'] for item in wolvox_path)
            mappings[key] = {
                'wolvox_path': wolvox_path,
                'woo_id': str(woo_category['id']),
                'woo_name': woo_category['name']
            }
            
            with open('category_mappings.json', 'w', encoding='utf-8') as f:
                json.dump(mappings, f, ensure_ascii=False, indent=4)
            
            self.load_mappings()
            self.statusBar().showMessage('Eşleştirme kaydedildi')
            
        except Exception as e:
            QMessageBox.warning(self, 'Uyarı', f'Eşleştirme kaydedilirken hata: {str(e)}')
    
    def export_mappings(self):
        """Eşleştirmeleri dışa aktar"""
        try:
            if os.path.exists('category_mappings.json'):
                file_name, _ = QFileDialog.getSaveFileName(
                    self,
                    'Eşleştirmeleri Kaydet',
                    '',
                    'JSON Dosyaları (*.json)'
                )
                
                if file_name:
                    if not file_name.endswith('.json'):
                        file_name += '.json'
                    
                    with open('category_mappings.json', 'r', encoding='utf-8') as source:
                        with open(file_name, 'w', encoding='utf-8') as target:
                            target.write(source.read())
                    
                    QMessageBox.information(self, 'Başarılı', 'Eşleştirmeler dışa aktarıldı!')
            else:
                QMessageBox.warning(self, 'Uyarı', 'Kayıtlı eşleştirme bulunamadı!')
        
        except Exception as e:
            QMessageBox.warning(self, 'Uyarı', f'Dışa aktarma sırasında hata: {str(e)}')
    
    def import_mappings(self):
        """Eşleştirmeleri içe aktar"""
        try:
            file_name, _ = QFileDialog.getOpenFileName(
                self,
                'Eşleştirmeleri Yükle',
                '',
                'JSON Dosyaları (*.json)'
            )
            
            if file_name:
                with open(file_name, 'r', encoding='utf-8') as source:
                    with open('category_mappings.json', 'w', encoding='utf-8') as target:
                        target.write(source.read())
                
                self.load_mappings()
                QMessageBox.information(self, 'Başarılı', 'Eşleştirmeler içe aktarıldı!')
        
        except Exception as e:
            QMessageBox.warning(self, 'Uyarı', f'İçe aktarma sırasında hata: {str(e)}')
    
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
    
    def load_wolvox_categories(self):
        """Wolvox kategorilerini yükle"""
        try:
            con = self.get_db_connection()
            if not con:
                return
            
            cur = con.cursor()
            
            # Ana grupları al (sadece stok modülü)
            cur.execute("""
                SELECT BLKODU, GRUP_ADI 
                FROM GRUP 
                WHERE WEBDE_GORUNSUN = 1
                AND MODUL = 'STOK'
                ORDER BY GRUP_ADI
            """)
            
            for grup in cur.fetchall():
                grup_item = QTreeWidgetItem(self.wolvox_tree)
                grup_item.setText(0, str(grup[0]))  # Kod (sayısal)
                grup_item.setText(1, grup[1].strip())  # İsim (metin)
                
                # Ara grupları al (sadece stok modülü)
                cur.execute("""
                    SELECT ga.BLKODU, ga.GRUP_ADI 
                    FROM GRUP_ARA ga
                    WHERE ga.UST_GRUP_ADI = ? 
                    AND ga.WEBDE_GORUNSUN = 1
                    AND ga.MODUL = 'STOK'
                    ORDER BY ga.GRUP_ADI
                """, (grup[1].strip(),))
                
                for aragrup in cur.fetchall():
                    aragrup_item = QTreeWidgetItem(grup_item)
                    aragrup_item.setText(0, str(aragrup[0]))  # Kod (sayısal)
                    aragrup_item.setText(1, aragrup[1].strip())  # İsim (metin)
                    
                    # Alt grupları al (sadece stok modülü)
                    cur.execute("""
                        SELECT galt.BLKODU, galt.GRUP_ADI 
                        FROM GRUP_ALT galt
                        WHERE galt.UST_GRUP_ADI = ? 
                        AND galt.UST_GRUP_ADI2 = ? 
                        AND galt.WEBDE_GORUNSUN = 1
                        AND galt.MODUL = 'STOK'
                        ORDER BY galt.GRUP_ADI
                    """, (grup[1].strip(), aragrup[1].strip()))
                    
                    for altgrup in cur.fetchall():
                        altgrup_item = QTreeWidgetItem(aragrup_item)
                        altgrup_item.setText(0, str(altgrup[0]))  # Kod (sayısal)
                        altgrup_item.setText(1, altgrup[1].strip())  # İsim (metin)
            
            con.close()
            self.wolvox_tree.expandAll()
            
        except Exception as e:
            QMessageBox.warning(self, 'Uyarı', f'Wolvox kategorileri yüklenirken hata: {str(e)}')
    
    def load_woo_categories(self):
        """WooCommerce kategorilerini yükle"""
        try:
            # WooCommerce API bilgileri
            url = os.getenv('WOOCOMMERCE_URL')
            consumer_key = os.getenv('WOOCOMMERCE_CONSUMER_KEY')
            consumer_secret = os.getenv('WOOCOMMERCE_CONSUMER_SECRET')
            
            # Kategorileri al
            response = requests.get(
                f"{url}/wp-json/wc/v3/products/categories",
                auth=(consumer_key, consumer_secret),
                params={"per_page": 100}
            )
            
            if response.status_code == 200:
                categories = response.json()
                self.woo_tree.clear()
                
                # Önce üst kategorileri ekle
                parent_items = {}
                for cat in categories:
                    if cat['parent'] == 0:
                        item = QTreeWidgetItem(self.woo_tree)
                        item.setText(0, str(cat['id']))
                        item.setText(1, cat['name'])
                        parent_items[cat['id']] = item
                
                # Sonra alt kategorileri ekle
                for cat in categories:
                    if cat['parent'] != 0 and cat['parent'] in parent_items:
                        item = QTreeWidgetItem(parent_items[cat['parent']])
                        item.setText(0, str(cat['id']))
                        item.setText(1, cat['name'])
                
                self.woo_tree.expandAll()
            else:
                QMessageBox.warning(self, 'Uyarı', 'WooCommerce kategorileri alınamadı!')
                
        except Exception as e:
            QMessageBox.warning(self, 'Uyarı', f'WooCommerce kategorileri yüklenirken hata: {str(e)}')
    
    def sync_woo_categories(self):
        """Wolvox kategorilerini WooCommerce'e senkronize et"""
        try:
            # WooCommerce API bilgileri
            url = os.getenv('WOOCOMMERCE_URL')
            consumer_key = os.getenv('WOOCOMMERCE_CONSUMER_KEY')
            consumer_secret = os.getenv('WOOCOMMERCE_CONSUMER_SECRET')
            
            # Mevcut WooCommerce kategorilerini al
            response = requests.get(
                f"{url}/wp-json/wc/v3/products/categories",
                auth=(consumer_key, consumer_secret),
                params={"per_page": 100}
            )
            
            if response.status_code == 200:
                existing_categories = {cat['name']: cat['id'] for cat in response.json()}
                
                # Wolvox kategorilerini ekle
                for i in range(self.wolvox_tree.topLevelItemCount()):
                    grup_item = self.wolvox_tree.topLevelItem(i)
                    grup_name = grup_item.text(1)
                    
                    # Ana grup yoksa ekle
                    if grup_name not in existing_categories:
                        response = requests.post(
                            f"{url}/wp-json/wc/v3/products/categories",
                            auth=(consumer_key, consumer_secret),
                            json={"name": grup_name}
                        )
                        
                        if response.status_code == 201:
                            grup_id = response.json()['id']
                            existing_categories[grup_name] = grup_id
                    
                    grup_id = existing_categories.get(grup_name)
                    
                    # Ara grupları ekle
                    for j in range(grup_item.childCount()):
                        aragrup_item = grup_item.child(j)
                        aragrup_name = aragrup_item.text(1)
                        
                        if aragrup_name not in existing_categories:
                            response = requests.post(
                                f"{url}/wp-json/wc/v3/products/categories",
                                auth=(consumer_key, consumer_secret),
                                json={"name": aragrup_name, "parent": grup_id}
                            )
                            
                            if response.status_code == 201:
                                aragrup_id = response.json()['id']
                                existing_categories[aragrup_name] = aragrup_id
                        
                        aragrup_id = existing_categories.get(aragrup_name)
                        
                        # Alt grupları ekle
                        for k in range(aragrup_item.childCount()):
                            altgrup_item = aragrup_item.child(k)
                            altgrup_name = altgrup_item.text(1)
                            
                            if altgrup_name not in existing_categories:
                                response = requests.post(
                                    f"{url}/wp-json/wc/v3/products/categories",
                                    auth=(consumer_key, consumer_secret),
                                    json={"name": altgrup_name, "parent": aragrup_id}
                                )
                
                # Kategorileri yeniden yükle
                self.load_woo_categories()
                QMessageBox.information(self, 'Başarılı', 'Kategoriler senkronize edildi!')
                
            else:
                QMessageBox.warning(self, 'Uyarı', 'WooCommerce kategorileri alınamadı!')
                
        except Exception as e:
            QMessageBox.warning(self, 'Uyarı', f'Kategori senkronizasyonu sırasında hata: {str(e)}')
    
    def map_categories(self):
        """Seçili kategorileri eşleştir"""
        wolvox_item = self.wolvox_tree.currentItem()
        woo_item = self.woo_tree.currentItem()
        
        if not wolvox_item or not woo_item:
            QMessageBox.warning(self, 'Uyarı', 'Lütfen her iki taraftan da kategori seçin!')
            return
        
        try:
            mappings = {}
            if os.path.exists('category_mappings.json'):
                with open('category_mappings.json', 'r', encoding='utf-8') as f:
                    mappings = json.load(f)
            
            # Eşleştirmeyi kaydet
            wolvox_path = []
            item = wolvox_item
            while item:
                wolvox_path.insert(0, {'code': item.text(0), 'name': item.text(1)})
                item = item.parent()
            
            woo_id = woo_item.text(0)
            woo_name = woo_item.text(1)
            
            key = '_'.join(x['code'] for x in wolvox_path)
            mappings[key] = {
                'wolvox_path': wolvox_path,
                'woo_id': woo_id,
                'woo_name': woo_name
            }
            
            with open('category_mappings.json', 'w', encoding='utf-8') as f:
                json.dump(mappings, f, ensure_ascii=False, indent=4)
            
            # Eşleştirme durumunu güncelle
            self.update_mapping_status(wolvox_item)
            self.update_mapping_status(woo_item)
            
            QMessageBox.information(self, 'Başarılı', 'Kategori eşleştirmesi kaydedildi!')
            
        except Exception as e:
            QMessageBox.warning(self, 'Uyarı', f'Eşleştirme kaydedilirken hata: {str(e)}')
    
    def unmap_categories(self):
        """Seçili eşleştirmeyi kaldır"""
        wolvox_item = self.wolvox_tree.currentItem()
        
        if not wolvox_item:
            QMessageBox.warning(self, 'Uyarı', 'Lütfen Wolvox tarafından bir kategori seçin!')
            return
        
        try:
            if os.path.exists('category_mappings.json'):
                with open('category_mappings.json', 'r', encoding='utf-8') as f:
                    mappings = json.load(f)
                
                # Eşleştirme anahtarını oluştur
                wolvox_path = []
                item = wolvox_item
                while item:
                    wolvox_path.insert(0, {'code': item.text(0), 'name': item.text(1)})
                    item = item.parent()
                
                key = '_'.join(x['code'] for x in wolvox_path)
                
                if key in mappings:
                    # WooCommerce tarafındaki eşleşen öğeyi bul
                    woo_id = mappings[key]['woo_id']
                    woo_item = self.find_woo_item_by_id(woo_id)
                    
                    del mappings[key]
                    
                    with open('category_mappings.json', 'w', encoding='utf-8') as f:
                        json.dump(mappings, f, ensure_ascii=False, indent=4)
                    
                    # Eşleştirme durumunu güncelle
                    self.update_mapping_status(wolvox_item)
                    if woo_item:
                        self.update_mapping_status(woo_item)
                    
                    QMessageBox.information(self, 'Başarılı', 'Kategori eşleştirmesi kaldırıldı!')
                else:
                    QMessageBox.warning(self, 'Uyarı', 'Bu kategori için eşleştirme bulunamadı!')
                
        except Exception as e:
            QMessageBox.warning(self, 'Uyarı', f'Eşleştirme kaldırılırken hata: {str(e)}')
    
    def find_woo_item_by_id(self, woo_id):
        """ID'ye göre WooCommerce öğesini bul"""
        def search_item(item):
            if item.text(0) == woo_id:
                return item
            for i in range(item.childCount()):
                result = search_item(item.child(i))
                if result:
                    return result
            return None
        
        for i in range(self.woo_tree.topLevelItemCount()):
            result = search_item(self.woo_tree.topLevelItem(i))
            if result:
                return result
        return None
    
    def load_mappings(self):
        """Kayıtlı eşleştirmeleri yükle"""
        try:
            if os.path.exists('category_mappings.json'):
                with open('category_mappings.json', 'r', encoding='utf-8') as f:
                    mappings = json.load(f)
                
                # Wolvox tarafındaki eşleştirmeleri işaretle
                for i in range(self.wolvox_tree.topLevelItemCount()):
                    self.update_mapping_status(self.wolvox_tree.topLevelItem(i))
                
                # WooCommerce tarafındaki eşleştirmeleri işaretle
                for i in range(self.woo_tree.topLevelItemCount()):
                    self.update_mapping_status(self.woo_tree.topLevelItem(i))
                
        except Exception as e:
            QMessageBox.warning(self, 'Uyarı', f'Eşleştirmeler yüklenirken hata: {str(e)}')
