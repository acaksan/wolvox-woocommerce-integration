from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLabel, QLineEdit, QPushButton, QSpinBox,
                             QComboBox, QCheckBox, QMessageBox, QTabWidget,
                             QGroupBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from config.settings import Settings
from utils.logger import setup_logger
from database.connection import DatabaseManager
from core.woo_client import WooClient
from core.wolvox_client import WolvoxClient
from ui.style import ICONS

class SettingsWidget(QWidget):
    """Ayarlar widget'ı"""
    
    def __init__(self):
        super().__init__()
        self.settings = Settings()
        self.logger = setup_logger(self.__class__.__name__)
        self.db = DatabaseManager()
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """UI bileşenlerini oluştur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Başlık
        title = QLabel("Ayarlar")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #333333;
        """)
        layout.addWidget(title)
        
        # Tab widget
        tab_widget = QTabWidget()
        
        # WooCommerce ayarları
        woo_tab = QWidget()
        woo_layout = QVBoxLayout(woo_tab)
        
        woo_group = QGroupBox("WooCommerce API")
        woo_form = QFormLayout(woo_group)
        
        self.woo_url_edit = QLineEdit()
        woo_form.addRow("Site URL:", self.woo_url_edit)
        
        self.woo_key_edit = QLineEdit()
        woo_form.addRow("Consumer Key:", self.woo_key_edit)
        
        self.woo_secret_edit = QLineEdit()
        self.woo_secret_edit.setEchoMode(QLineEdit.Password)
        woo_form.addRow("Consumer Secret:", self.woo_secret_edit)
        
        self.woo_version_combo = QComboBox()
        self.woo_version_combo.addItems(["wc/v3", "wc/v2", "wc/v1"])
        woo_form.addRow("API Versiyonu:", self.woo_version_combo)
        
        woo_layout.addWidget(woo_group)
        
        # WooCommerce test butonu
        woo_test_button = QPushButton("Bağlantıyı Test Et")
        woo_test_button.setIcon(QIcon(ICONS.TEST))
        woo_test_button.clicked.connect(self.test_woo_connection)
        woo_layout.addWidget(woo_test_button)
        
        woo_layout.addStretch()
        
        tab_widget.addTab(woo_tab, "WooCommerce")
        
        # Wolvox ayarları
        wolvox_tab = QWidget()
        wolvox_layout = QVBoxLayout(wolvox_tab)
        
        wolvox_group = QGroupBox("Wolvox Veritabanı")
        wolvox_form = QFormLayout(wolvox_group)
        
        self.wolvox_host_edit = QLineEdit()
        wolvox_form.addRow("Sunucu:", self.wolvox_host_edit)
        
        self.wolvox_port_spin = QSpinBox()
        self.wolvox_port_spin.setMinimum(1)
        self.wolvox_port_spin.setMaximum(65535)
        self.wolvox_port_spin.setValue(1433)
        wolvox_form.addRow("Port:", self.wolvox_port_spin)
        
        self.wolvox_database_edit = QLineEdit()
        wolvox_form.addRow("Veritabanı:", self.wolvox_database_edit)
        
        self.wolvox_username_edit = QLineEdit()
        wolvox_form.addRow("Kullanıcı Adı:", self.wolvox_username_edit)
        
        self.wolvox_password_edit = QLineEdit()
        self.wolvox_password_edit.setEchoMode(QLineEdit.Password)
        wolvox_form.addRow("Şifre:", self.wolvox_password_edit)
        
        wolvox_layout.addWidget(wolvox_group)
        
        # Wolvox test butonu
        wolvox_test_button = QPushButton("Bağlantıyı Test Et")
        wolvox_test_button.setIcon(QIcon(ICONS.TEST))
        wolvox_test_button.clicked.connect(self.test_wolvox_connection)
        wolvox_layout.addWidget(wolvox_test_button)
        
        wolvox_layout.addStretch()
        
        tab_widget.addTab(wolvox_tab, "Wolvox")
        
        # Senkronizasyon ayarları
        sync_tab = QWidget()
        sync_layout = QVBoxLayout(sync_tab)
        
        sync_group = QGroupBox("Senkronizasyon")
        sync_form = QFormLayout(sync_group)
        
        self.sync_interval_spin = QSpinBox()
        self.sync_interval_spin.setMinimum(1)
        self.sync_interval_spin.setMaximum(60)
        self.sync_interval_spin.setValue(5)
        sync_form.addRow("Otomatik Senkronizasyon Aralığı (dk):", self.sync_interval_spin)
        
        self.auto_sync_check = QCheckBox()
        sync_form.addRow("Otomatik Senkronizasyon:", self.auto_sync_check)
        
        self.auto_match_check = QCheckBox()
        sync_form.addRow("Otomatik Eşleştirme:", self.auto_match_check)
        
        self.sync_on_change_check = QCheckBox()
        sync_form.addRow("Değişiklikte Senkronize Et:", self.sync_on_change_check)
        
        sync_layout.addWidget(sync_group)
        
        # Eşleştirme ayarları
        match_group = QGroupBox("Eşleştirme")
        match_form = QFormLayout(match_group)
        
        self.match_by_sku_check = QCheckBox()
        match_form.addRow("SKU ile Eşleştir:", self.match_by_sku_check)
        
        self.match_by_name_check = QCheckBox()
        match_form.addRow("İsim ile Eşleştir:", self.match_by_name_check)
        
        self.match_by_barcode_check = QCheckBox()
        match_form.addRow("Barkod ile Eşleştir:", self.match_by_barcode_check)
        
        sync_layout.addWidget(match_group)
        
        sync_layout.addStretch()
        
        tab_widget.addTab(sync_tab, "Senkronizasyon")
        
        # Görünüm ayarları
        appearance_tab = QWidget()
        appearance_layout = QVBoxLayout(appearance_tab)
        
        appearance_group = QGroupBox("Görünüm")
        appearance_form = QFormLayout(appearance_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Açık", "Koyu", "Sistem"])
        appearance_form.addRow("Tema:", self.theme_combo)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Türkçe", "English"])
        appearance_form.addRow("Dil:", self.language_combo)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setMinimum(8)
        self.font_size_spin.setMaximum(24)
        self.font_size_spin.setValue(12)
        appearance_form.addRow("Yazı Boyutu:", self.font_size_spin)
        
        appearance_layout.addWidget(appearance_group)
        appearance_layout.addStretch()
        
        tab_widget.addTab(appearance_tab, "Görünüm")
        
        layout.addWidget(tab_widget)
        
        # Kaydet butonu
        save_button = QPushButton("Ayarları Kaydet")
        save_button.setIcon(QIcon(ICONS.SAVE))
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)
    
    def load_settings(self):
        """Ayarları yükle"""
        try:
            # WooCommerce ayarları
            self.woo_url_edit.setText(self.settings.get("woo_url"))
            self.woo_key_edit.setText(self.settings.get("woo_key"))
            self.woo_secret_edit.setText(self.settings.get("woo_secret"))
            
            woo_version = self.settings.get("woo_version", "wc/v3")
            index = self.woo_version_combo.findText(woo_version)
            if index >= 0:
                self.woo_version_combo.setCurrentIndex(index)
            
            # Wolvox ayarları
            self.wolvox_host_edit.setText(self.settings.get("wolvox_host"))
            self.wolvox_port_spin.setValue(
                int(self.settings.get("wolvox_port", 1433))
            )
            self.wolvox_database_edit.setText(self.settings.get("wolvox_database"))
            self.wolvox_username_edit.setText(self.settings.get("wolvox_username"))
            self.wolvox_password_edit.setText(self.settings.get("wolvox_password"))
            
            # Senkronizasyon ayarları
            self.sync_interval_spin.setValue(
                int(self.settings.get("sync_interval", 5))
            )
            self.auto_sync_check.setChecked(
                bool(self.settings.get("auto_sync", False))
            )
            self.auto_match_check.setChecked(
                bool(self.settings.get("auto_match", True))
            )
            self.sync_on_change_check.setChecked(
                bool(self.settings.get("sync_on_change", True))
            )
            
            # Eşleştirme ayarları
            self.match_by_sku_check.setChecked(
                bool(self.settings.get("match_by_sku", True))
            )
            self.match_by_name_check.setChecked(
                bool(self.settings.get("match_by_name", True))
            )
            self.match_by_barcode_check.setChecked(
                bool(self.settings.get("match_by_barcode", False))
            )
            
            # Görünüm ayarları
            theme = self.settings.get("theme", "Açık")
            index = self.theme_combo.findText(theme)
            if index >= 0:
                self.theme_combo.setCurrentIndex(index)
            
            language = self.settings.get("language", "Türkçe")
            index = self.language_combo.findText(language)
            if index >= 0:
                self.language_combo.setCurrentIndex(index)
            
            self.font_size_spin.setValue(
                int(self.settings.get("font_size", 12))
            )
            
        except Exception as e:
            self.logger.error(f"Ayarlar yüklenirken hata: {str(e)}")
            QMessageBox.critical(
                self,
                "Hata",
                "Ayarlar yüklenirken bir hata oluştu!"
            )
    
    def save_settings(self):
        """Ayarları kaydet"""
        try:
            # WooCommerce ayarları
            self.settings.set("woo_url", self.woo_url_edit.text())
            self.settings.set("woo_key", self.woo_key_edit.text())
            self.settings.set("woo_secret", self.woo_secret_edit.text())
            self.settings.set("woo_version", self.woo_version_combo.currentText())
            
            # Wolvox ayarları
            self.settings.set("wolvox_host", self.wolvox_host_edit.text())
            self.settings.set("wolvox_port", self.wolvox_port_spin.value())
            self.settings.set("wolvox_database", self.wolvox_database_edit.text())
            self.settings.set("wolvox_username", self.wolvox_username_edit.text())
            self.settings.set("wolvox_password", self.wolvox_password_edit.text())
            
            # Senkronizasyon ayarları
            self.settings.set("sync_interval", self.sync_interval_spin.value())
            self.settings.set("auto_sync", self.auto_sync_check.isChecked())
            self.settings.set("auto_match", self.auto_match_check.isChecked())
            self.settings.set("sync_on_change", self.sync_on_change_check.isChecked())
            
            # Eşleştirme ayarları
            self.settings.set("match_by_sku", self.match_by_sku_check.isChecked())
            self.settings.set("match_by_name", self.match_by_name_check.isChecked())
            self.settings.set("match_by_barcode", self.match_by_barcode_check.isChecked())
            
            # Görünüm ayarları
            self.settings.set("theme", self.theme_combo.currentText())
            self.settings.set("language", self.language_combo.currentText())
            self.settings.set("font_size", self.font_size_spin.value())
            
            # Ayarları kaydet
            self.settings.save()
            
            QMessageBox.information(
                self,
                "Başarılı",
                "Ayarlar başarıyla kaydedildi!"
            )
            
        except Exception as e:
            self.logger.error(f"Ayarlar kaydedilirken hata: {str(e)}")
            QMessageBox.critical(
                self,
                "Hata",
                "Ayarlar kaydedilirken bir hata oluştu!"
            )
    
    def test_woo_connection(self):
        """WooCommerce bağlantısını test et"""
        try:
            client = WooClient()
            client.test_connection()
            
            QMessageBox.information(
                self,
                "Başarılı",
                "WooCommerce bağlantısı başarılı!"
            )
            
        except Exception as e:
            self.logger.error(f"WooCommerce bağlantı testi hatası: {str(e)}")
            QMessageBox.critical(
                self,
                "Hata",
                f"WooCommerce bağlantısı başarısız: {str(e)}"
            )
    
    def test_wolvox_connection(self):
        """Wolvox bağlantısını test et"""
        try:
            client = WolvoxClient()
            client.test_connection()
            
            QMessageBox.information(
                self,
                "Başarılı",
                "Wolvox bağlantısı başarılı!"
            )
            
        except Exception as e:
            self.logger.error(f"Wolvox bağlantı testi hatası: {str(e)}")
            QMessageBox.critical(
                self,
                "Hata",
                f"Wolvox bağlantısı başarısız: {str(e)}"
            )
