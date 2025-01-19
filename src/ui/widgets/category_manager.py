from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QTreeWidget, QTreeWidgetItem,
                             QMenu, QAction, QMessageBox, QDialog, QFormLayout,
                             QComboBox, QTextEdit)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QColor

from src.config.settings import Settings
from src.utils.logger import setup_logger
from src.database.models import Category
from src.database.connection import DatabaseManager
from src.ui.style import ICONS

class CategoryDialog(QDialog):
    """Kategori ekleme/düzenleme dialog'u"""
    
    def __init__(self, parent=None, category=None):
        super().__init__(parent)
        self.category = category
        self.settings = Settings()
        self.logger = setup_logger(self.__class__.__name__)
        self.db = DatabaseManager()
        
        self.setup_ui()
        
        if category:
            self.load_category()
    
    def setup_ui(self):
        """UI bileşenlerini oluştur"""
        self.setWindowTitle("Kategori Ekle/Düzenle")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Form layout
        form = QFormLayout()
        
        # Kategori adı
        self.name_edit = QLineEdit()
        form.addRow("Kategori Adı:", self.name_edit)
        
        # Üst kategori
        self.parent_combo = QComboBox()
        self.load_parent_categories()
        form.addRow("Üst Kategori:", self.parent_combo)
        
        # Açıklama
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        form.addRow("Açıklama:", self.description_edit)
        
        # Görüntüleme tipi
        self.display_combo = QComboBox()
        self.display_combo.addItems([
            "default",
            "products",
            "subcategories",
            "both"
        ])
        form.addRow("Görüntüleme:", self.display_combo)
        
        layout.addLayout(form)
        
        # Butonlar
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Kaydet")
        self.save_button.setIcon(QIcon(ICONS.SAVE))
        self.save_button.clicked.connect(self.save_category)
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("İptal")
        self.cancel_button.setIcon(QIcon(ICONS.CANCEL))
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def load_parent_categories(self):
        """Üst kategorileri yükle"""
        try:
            self.parent_combo.clear()
            self.parent_combo.addItem("Ana Kategori", None)
            
            with self.db.session_scope() as session:
                categories = session.query(Category).all()
                
                for category in categories:
                    if category != self.category:  # Kendisini üst kategori olarak seçemesin
                        self.parent_combo.addItem(category.name, category.id)
                        
        except Exception as e:
            self.logger.error(f"Üst kategoriler yüklenirken hata: {str(e)}")
    
    def load_category(self):
        """Kategori bilgilerini yükle"""
        self.name_edit.setText(self.category.name)
        
        if self.category.parent_id:
            index = self.parent_combo.findData(self.category.parent_id)
            if index >= 0:
                self.parent_combo.setCurrentIndex(index)
        
        self.description_edit.setText(self.category.description)
        
        index = self.display_combo.findText(self.category.display)
        if index >= 0:
            self.display_combo.setCurrentIndex(index)
    
    def save_category(self):
        """Kategoriyi kaydet"""
        try:
            data = {
                "name": self.name_edit.text(),
                "parent_id": self.parent_combo.currentData(),
                "description": self.description_edit.toPlainText(),
                "display": self.display_combo.currentText()
            }
            
            with self.db.session_scope() as session:
                if self.category:
                    # Mevcut kategoriyi güncelle
                    for key, value in data.items():
                        setattr(self.category, key, value)
                    session.merge(self.category)
                else:
                    # Yeni kategori oluştur
                    category = Category(**data)
                    session.add(category)
            
            self.accept()
            
        except Exception as e:
            self.logger.error(f"Kategori kaydedilirken hata: {str(e)}")
            QMessageBox.critical(
                self,
                "Hata",
                "Kategori kaydedilirken bir hata oluştu!"
            )

class CategoryManagerWidget(QWidget):
    """Kategori yönetimi widget'ı"""
    
    def __init__(self):
        super().__init__()
        self.settings = Settings()
        self.logger = setup_logger(self.__class__.__name__)
        self.db = DatabaseManager()
        
        self.setup_ui()
        self.load_categories()
    
    def setup_ui(self):
        """UI bileşenlerini oluştur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Başlık
        title = QLabel("Kategori Yönetimi")
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
        self.search_edit.setPlaceholderText("Kategori ara...")
        self.search_edit.textChanged.connect(self.filter_categories)
        toolbar.addWidget(self.search_edit)
        
        # Yeni ekle butonu
        add_button = QPushButton("Yeni Kategori")
        add_button.setIcon(QIcon(ICONS.ADD))
        add_button.clicked.connect(self.add_category)
        toolbar.addWidget(add_button)
        
        layout.addLayout(toolbar)
        
        # Kategori ağacı
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([
            "Kategori",
            "Ürün Sayısı",
            "WooCommerce",
            "Wolvox",
            "İşlemler"
        ])
        
        self.tree.setColumnWidth(0, 300)
        self.tree.setAlternatingRowColors(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.tree)
    
    def load_categories(self):
        """Kategorileri yükle"""
        try:
            self.tree.clear()
            
            with self.db.session_scope() as session:
                # Ana kategorileri al
                root_categories = session.query(Category).filter_by(
                    parent_id=None
                ).all()
                
                # Kategori ağacını oluştur
                for category in root_categories:
                    self.add_category_item(category)
                    
        except Exception as e:
            self.logger.error(f"Kategoriler yüklenirken hata: {str(e)}")
            QMessageBox.critical(
                self,
                "Hata",
                "Kategoriler yüklenirken bir hata oluştu!"
            )
    
    def add_category_item(self, category, parent=None):
        """Kategori öğesi ekle"""
        if parent is None:
            item = QTreeWidgetItem(self.tree)
        else:
            item = QTreeWidgetItem(parent)
        
        # Kategori adı
        item.setText(0, category.name)
        
        # Ürün sayısı
        item.setText(1, str(category.count or 0))
        
        # WooCommerce ID
        woo_id = str(category.woo_id) if category.woo_id else "-"
        item.setText(2, woo_id)
        
        # Wolvox ID
        wolvox_id = category.wolvox_id or "-"
        item.setText(3, wolvox_id)
        
        # İşlem butonları için widget
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        
        # Düzenle butonu
        edit_button = QPushButton()
        edit_button.setIcon(QIcon(ICONS.EDIT))
        edit_button.clicked.connect(
            lambda checked, c=category: self.edit_category(c)
        )
        actions_layout.addWidget(edit_button)
        
        # Sil butonu
        delete_button = QPushButton()
        delete_button.setIcon(QIcon(ICONS.DELETE))
        delete_button.clicked.connect(
            lambda checked, c=category: self.delete_category(c)
        )
        actions_layout.addWidget(delete_button)
        
        self.tree.setItemWidget(item, 4, actions_widget)
        
        # Alt kategorileri ekle
        for child in category.children:
            self.add_category_item(child, item)
    
    def filter_categories(self):
        """Kategorileri filtrele"""
        search_text = self.search_edit.text().lower()
        
        def filter_item(item):
            show = search_text in item.text(0).lower()
            
            # Alt öğeleri kontrol et
            for i in range(item.childCount()):
                child = item.child(i)
                show_child = filter_item(child)
                show = show or show_child
            
            item.setHidden(not show)
            return show
        
        # Kök öğeleri filtrele
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            filter_item(item)
    
    def show_context_menu(self, position):
        """Sağ tık menüsünü göster"""
        item = self.tree.itemAt(position)
        if item:
            menu = QMenu()
            
            edit_action = QAction(
                QIcon(ICONS.EDIT),
                "Düzenle",
                self
            )
            menu.addAction(edit_action)
            
            delete_action = QAction(
                QIcon(ICONS.DELETE),
                "Sil",
                self
            )
            menu.addAction(delete_action)
            
            action = menu.exec_(self.tree.viewport().mapToGlobal(position))
            
            if action == edit_action:
                self.edit_category(item.data(0, Qt.UserRole))
            elif action == delete_action:
                self.delete_category(item.data(0, Qt.UserRole))
    
    def add_category(self):
        """Yeni kategori ekle"""
        dialog = CategoryDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_categories()
    
    def edit_category(self, category):
        """Kategori düzenle"""
        dialog = CategoryDialog(self, category)
        if dialog.exec_() == QDialog.Accepted:
            self.load_categories()
    
    def delete_category(self, category):
        """Kategori sil"""
        reply = QMessageBox.question(
            self,
            "Kategori Sil",
            f"{category.name} kategorisini silmek istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                with self.db.session_scope() as session:
                    session.delete(category)
                self.load_categories()
            except Exception as e:
                self.logger.error(f"Kategori silinirken hata: {str(e)}")
                QMessageBox.critical(
                    self,
                    "Hata",
                    "Kategori silinirken bir hata oluştu!"
                )
