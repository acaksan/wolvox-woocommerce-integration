import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask ayarları
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev')
    
    # WooCommerce ayarları
    WOOCOMMERCE_STORES = {
        'default': {
            'url': os.getenv('WOOCOMMERCE_URL'),
            'consumer_key': os.getenv('WOOCOMMERCE_CONSUMER_KEY'),
            'consumer_secret': os.getenv('WOOCOMMERCE_CONSUMER_SECRET')
        }
        # Buraya başka mağazalar eklenebilir
    }
    
    # Firebird veritabanı ayarları
    DB_CONFIG = {
        'host': 'localhost',
        'database': 'E:/AKINSOFT/WOLVOX8/DATABASE_FB/100/2024/WOLVOX.FDB',  # Forward slash kullanıyoruz
        'user': 'SYSDBA',
        'password': 'masterkey',
        'charset': 'WIN1254'  # Turkish Windows charset
    }
    
    # WooCommerce API ayarları
    WOOCOMMERCE_CONFIG = {
        'url': 'https://example.com',
        'consumer_key': 'your_consumer_key',
        'consumer_secret': 'your_consumer_secret',
        'verify_ssl': True,
        'version': 'wc/v3'
    }
    
    # Uygulama ayarları
    APP_CONFIG = {
        'debug': True,
        'host': 'localhost',
        'port': 8080,
        'secret_key': 'your-secret-key-here'
    }
    
    # Loglama ayarları
    LOG_CONFIG = {
        'filename': 'app.log',
        'level': 'DEBUG',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    }
    
    # Senkronizasyon ayarları
    SYNC_CONFIG = {
        'interval': 300,  # 5 dakika
        'batch_size': 100,
        'retry_count': 3,
        'retry_delay': 5
    }
    
    # Yol ayarları
    PATH_CONFIG = {
        'upload_folder': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads'),
        'temp_folder': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp'),
        'log_folder': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    }
    
    # Klasörleri oluştur
    for folder in PATH_CONFIG.values():
        if not os.path.exists(folder):
            os.makedirs(folder)
            
    # Senkronizasyon ayarları
    SYNC_SETTINGS = {
        'PRODUCT_SYNC_INTERVAL': 30,  # dakika
        'ORDER_SYNC_INTERVAL': 15,    # dakika
        'CATEGORY_SYNC_INTERVAL': 60, # dakika
        'MIN_STOCK_LEVEL': 0,
        'PRICE_MARGIN': 1.0,  # 1.0 = fiyat değişikliği yok
        'AUTO_PRICE_UPDATE': False,
        'IMAGE_OPTIMIZATION': True,
        'MAX_IMAGE_SIZE': 1024,  # pixel
        'CURRENCY_UPDATE': False
    }
    
    # Döviz kuru ayarları
    EXCHANGE_RATES_API_KEY = os.getenv('EXCHANGE_RATES_API_KEY')
    
    # SEO ayarları
    SEO_TEMPLATES = {
        'title': '{product_name} | {brand} | {category}',
        'description': '{short_description}\n\nMarka: {brand}\nKategori: {category}\nKod: {sku}'
    }
    
    # Resim optimizasyon ayarları
    IMAGE_SETTINGS = {
        'OPTIMIZE_IMAGES': True,
        'MAX_WIDTH': 1024,
        'MAX_HEIGHT': 1024,
        'QUALITY': 85,
        'FORMAT': 'JPEG'
    }
    
    # Log ayarları
    LOG_SETTINGS = {
        'MAX_SIZE': 10485760,  # 10MB
        'BACKUP_COUNT': 5,
        'LEVEL': 'INFO'
    }
