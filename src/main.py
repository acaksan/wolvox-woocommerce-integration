from PyQt5.QtGui import QIcon
import sys
import os
from PyQt5.QtWidgets import QApplication

# Add the project root directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.main_window import MainWindow
from config.settings import Settings
from utils.logger import setup_logger
from database.connection import DatabaseManager

# Logger'ı başlat
logger = setup_logger("main")

def setup_environment():
    """Uygulama ortamını hazırla"""
    try:
        # Ana dizinleri oluştur
        directories = [
            "logs",
            "data",
            os.path.join("src", "assets"),
            os.path.join("src", "assets", "icons")
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
        
        # Veritabanını başlat
        db = DatabaseManager()
        
        logger.info("Uygulama ortamı başarıyla hazırlandı")
    except Exception as e:
        logger.error(f"Ortam hazırlanırken hata: {str(e)}")
        raise

def main():
    """Ana uygulama fonksiyonu"""
    try:
        # Ortamı hazırla
        setup_environment()
        
        # Ayarları yükle
        settings = Settings()
        
        # Qt uygulamasını başlat
        app = QApplication(sys.argv)
        
        # Uygulama bilgilerini ayarla
        app.setApplicationName("Wolvox - WooCommerce Entegrasyon")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("Akinon")
        app.setOrganizationDomain("akinon.com")
        
        # Ana pencereyi oluştur
        window = MainWindow()
        window.show()
        
        # Uygulamayı çalıştır
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"Uygulama başlatılırken hata: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
