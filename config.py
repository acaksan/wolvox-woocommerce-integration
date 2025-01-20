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
    
    # Wolvox ayarları
    WOLVOX_DB_PATH = os.getenv('WOLVOX_DB_PATH')
    WOLVOX_DB_USER = os.getenv('WOLVOX_DB_USER')
    WOLVOX_DB_PASSWORD = os.getenv('WOLVOX_DB_PASSWORD')
    FIREBIRD_CLIENT_PATH = os.getenv('FIREBIRD_CLIENT_PATH')
    
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
