from dataclasses import dataclass
import os
from PyQt5.QtGui import QIcon

@dataclass
class Icons:
    """İkon yolları"""
    
    # Ana dizin
    ICONS_DIR = os.path.join("src", "assets", "icons")
    
    # Menü ikonları
    DASHBOARD = os.path.join(ICONS_DIR, "dashboard.png")
    PRODUCTS = os.path.join(ICONS_DIR, "products.png")
    CATEGORIES = os.path.join(ICONS_DIR, "categories.png")
    SYNC = os.path.join(ICONS_DIR, "sync.png")
    SETTINGS = os.path.join(ICONS_DIR, "settings.png")
    
    # İşlem ikonları
    ADD = os.path.join(ICONS_DIR, "add.png")
    EDIT = os.path.join(ICONS_DIR, "edit.png")
    DELETE = os.path.join(ICONS_DIR, "delete.png")
    SAVE = os.path.join(ICONS_DIR, "save.png")
    CANCEL = os.path.join(ICONS_DIR, "cancel.png")
    TEST = os.path.join(ICONS_DIR, "test.png")

# İkon nesnesi
ICONS = Icons()

# Açık tema
LIGHT_THEME = """
QMainWindow {
    background-color: #f5f6fa;
}

QWidget {
    font-family: "Segoe UI", sans-serif;
}

QLabel {
    color: #2c3e50;
}

QPushButton {
    background-color: #3498db;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
}

QPushButton:hover {
    background-color: #2980b9;
}

QPushButton:pressed {
    background-color: #2472a4;
}

QPushButton:disabled {
    background-color: #bdc3c7;
}

QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox {
    background-color: white;
    border: 1px solid #bdc3c7;
    padding: 8px;
    border-radius: 4px;
}

QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #3498db;
}

QComboBox {
    background-color: white;
    border: 1px solid #bdc3c7;
    padding: 8px;
    border-radius: 4px;
}

QComboBox::drop-down {
    border: none;
}

QComboBox::down-arrow {
    image: url(src/assets/icons/down-arrow.png);
    width: 12px;
    height: 12px;
}

QTableWidget {
    background-color: white;
    border: 1px solid #bdc3c7;
    border-radius: 4px;
}

QTableWidget::item {
    padding: 8px;
}

QTableWidget::item:selected {
    background-color: #3498db;
    color: white;
}

QHeaderView::section {
    background-color: #f8f9fa;
    padding: 8px;
    border: none;
    border-right: 1px solid #bdc3c7;
    border-bottom: 1px solid #bdc3c7;
}

QScrollBar:vertical {
    border: none;
    background-color: #f8f9fa;
    width: 12px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #bdc3c7;
    min-height: 20px;
    border-radius: 6px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}

QProgressBar {
    border: 1px solid #bdc3c7;
    border-radius: 4px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #3498db;
}

QGroupBox {
    border: 1px solid #bdc3c7;
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 24px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 4px;
    color: #2c3e50;
}
"""

# Koyu tema
DARK_THEME = """
QMainWindow {
    background-color: #2c3e50;
}

QWidget {
    font-family: "Segoe UI", sans-serif;
    color: #ecf0f1;
}

QLabel {
    color: #ecf0f1;
}

QPushButton {
    background-color: #3498db;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
}

QPushButton:hover {
    background-color: #2980b9;
}

QPushButton:pressed {
    background-color: #2472a4;
}

QPushButton:disabled {
    background-color: #34495e;
}

QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox {
    background-color: #34495e;
    border: 1px solid #2c3e50;
    color: #ecf0f1;
    padding: 8px;
    border-radius: 4px;
}

QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #3498db;
}

QComboBox {
    background-color: #34495e;
    border: 1px solid #2c3e50;
    color: #ecf0f1;
    padding: 8px;
    border-radius: 4px;
}

QComboBox::drop-down {
    border: none;
}

QComboBox::down-arrow {
    image: url(src/assets/icons/down-arrow-light.png);
    width: 12px;
    height: 12px;
}

QTableWidget {
    background-color: #34495e;
    border: 1px solid #2c3e50;
    border-radius: 4px;
    color: #ecf0f1;
}

QTableWidget::item {
    padding: 8px;
}

QTableWidget::item:selected {
    background-color: #3498db;
    color: white;
}

QHeaderView::section {
    background-color: #2c3e50;
    color: #ecf0f1;
    padding: 8px;
    border: none;
    border-right: 1px solid #34495e;
    border-bottom: 1px solid #34495e;
}

QScrollBar:vertical {
    border: none;
    background-color: #2c3e50;
    width: 12px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #34495e;
    min-height: 20px;
    border-radius: 6px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}

QProgressBar {
    border: 1px solid #2c3e50;
    border-radius: 4px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #3498db;
}

QGroupBox {
    border: 1px solid #2c3e50;
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 24px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 4px;
    color: #ecf0f1;
}
"""

def get_style_sheet(theme="light"):
    """Tema stil dosyasını getir"""
    if theme == "dark":
        return DARK_THEME
    return LIGHT_THEME
