import os
import fdb
from dotenv import load_dotenv
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/wolvox_product_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('WolvoxProduct')

class ProductReader:
    def __init__(self, connection):
        """Wolvox ürün okuyucu

        Args:
            connection: Veritabanı bağlantısı
        """
        self.conn = connection

    def get_all_products(self) -> Optional[List[Dict]]:
        """Tüm ürünleri getir

        Returns:
            Ürün listesi veya None
        """
        try:
            cursor = self.conn.cursor()
            
            # Ana ürün bilgilerini al
            cursor.execute("""
                SELECT 
                    s.STOK_KODU,
                    s.STOK_ADI,
                    s.BARKOD,
                    s.GRUP_KODU,
                    s.MARKA_KODU,
                    s.MODEL_KODU,
                    s.ACIKLAMA,
                    s.SATIS_FIYATI1,
                    s.BAKIYE,
                    s.WEB_DURUM,
                    s.AKTIF,
                    g.GRUP_ADI,
                    m.MARKA_ADI,
                    md.MODEL_ADI
                FROM STOKLAR s
                LEFT JOIN STOK_GRUPLARI g ON s.GRUP_KODU = g.GRUP_KODU
                LEFT JOIN STOK_MARKALARI m ON s.MARKA_KODU = m.MARKA_KODU
                LEFT JOIN STOK_MODELLERI md ON s.MODEL_KODU = md.MODEL_KODU
                WHERE s.WEB_DURUM = 1 AND s.AKTIF = 1
            """)
            
            products = []
            for row in cursor.fetchall():
                product = {
                    'STOK_KODU': row[0],
                    'STOK_ADI': row[1],
                    'BARKOD': row[2],
                    'GRUP_KODU': row[3],
                    'MARKA_KODU': row[4],
                    'MODEL_KODU': row[5],
                    'ACIKLAMA': row[6],
                    'SATIS_FIYATI1': float(row[7]) if row[7] else 0.0,
                    'BAKIYE': float(row[8]) if row[8] else 0.0,
                    'WEB_DURUM': row[9],
                    'AKTIF': row[10],
                    'KATEGORI': row[11],  # GRUP_ADI
                    'MARKA': row[12],     # MARKA_ADI
                    'MODEL': row[13]      # MODEL_ADI
                }
                products.append(product)
                
            return products
            
        except Exception as e:
            logger.error(f"Ürün okuma hatası: {str(e)}")
            return None

    def get_product_by_code(self, stok_kodu: str) -> Optional[Dict]:
        """Stok koduna göre ürün getir

        Args:
            stok_kodu: Ürün stok kodu

        Returns:
            Ürün bilgileri veya None
        """
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                SELECT 
                    s.STOK_KODU,
                    s.STOK_ADI,
                    s.BARKOD,
                    s.GRUP_KODU,
                    s.MARKA_KODU,
                    s.MODEL_KODU,
                    s.ACIKLAMA,
                    s.SATIS_FIYATI1,
                    s.BAKIYE,
                    s.WEB_DURUM,
                    s.AKTIF,
                    g.GRUP_ADI,
                    m.MARKA_ADI,
                    md.MODEL_ADI
                FROM STOKLAR s
                LEFT JOIN STOK_GRUPLARI g ON s.GRUP_KODU = g.GRUP_KODU
                LEFT JOIN STOK_MARKALARI m ON s.MARKA_KODU = m.MARKA_KODU
                LEFT JOIN STOK_MODELLERI md ON s.MODEL_KODU = md.MODEL_KODU
                WHERE s.STOK_KODU = ? AND s.WEB_DURUM = 1 AND s.AKTIF = 1
            """, (stok_kodu,))
            
            row = cursor.fetchone()
            if not row:
                return None
                
            return {
                'STOK_KODU': row[0],
                'STOK_ADI': row[1],
                'BARKOD': row[2],
                'GRUP_KODU': row[3],
                'MARKA_KODU': row[4],
                'MODEL_KODU': row[5],
                'ACIKLAMA': row[6],
                'SATIS_FIYATI1': float(row[7]) if row[7] else 0.0,
                'BAKIYE': float(row[8]) if row[8] else 0.0,
                'WEB_DURUM': row[9],
                'AKTIF': row[10],
                'KATEGORI': row[11],  # GRUP_ADI
                'MARKA': row[12],     # MARKA_ADI
                'MODEL': row[13]      # MODEL_ADI
            }
            
        except Exception as e:
            logger.error(f"Ürün okuma hatası: {str(e)}")
            return None

    def get_stock_and_prices(self) -> Optional[List[Dict]]:
        """Stok ve fiyat bilgilerini getir

        Returns:
            Stok ve fiyat listesi veya None
        """
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                SELECT 
                    STOK_KODU,
                    SATIS_FIYATI1,
                    BAKIYE
                FROM STOKLAR
                WHERE WEB_DURUM = 1 AND AKTIF = 1
            """)
            
            products = []
            for row in cursor.fetchall():
                product = {
                    'STOK_KODU': row[0],
                    'SATIS_FIYATI1': float(row[1]) if row[1] else 0.0,
                    'BAKIYE': float(row[2]) if row[2] else 0.0
                }
                products.append(product)
                
            return products
            
        except Exception as e:
            logger.error(f"Stok ve fiyat okuma hatası: {str(e)}")
            return None

class WolvoxProductReader:
    def __init__(self):
        self.connection = None
        self.setup_connection()
    
    def setup_connection(self):
        """Veritabanı bağlantısını kur"""
        try:
            load_dotenv()
            
            # Firebird client path'ini ayarla
            fb_client_path = os.getenv('FIREBIRD_CLIENT_PATH')
            if fb_client_path and os.path.exists(fb_client_path):
                fdb.load_api(fb_client_path)
            
            # Veritabanı bağlantısı
            self.connection = fdb.connect(
                dsn=f"{os.getenv('WOLVOX_DB_HOST')}:{os.getenv('WOLVOX_DB_PATH')}",
                user=os.getenv('WOLVOX_DB_USER'),
                password=os.getenv('WOLVOX_DB_PASSWORD')
            )
            logger.info("Veritabanı bağlantısı kuruldu")
            
        except Exception as e:
            logger.error(f"Veritabanı bağlantısı kurulamadı: {str(e)}")
            raise
    
    def get_all_products(self):
        """Tüm aktif ürünleri getir"""
        try:
            product_reader = ProductReader(self.connection)
            return product_reader.get_all_products()
            
        except Exception as e:
            logger.error(f"Ürünler alınırken hata oluştu: {str(e)}")
            raise
    
    def get_product_stock(self, stok_kodu):
        """Ürün stok miktarını getir"""
        try:
            product_reader = ProductReader(self.connection)
            product = product_reader.get_product_by_code(stok_kodu)
            if product:
                return product['BAKIYE']
            else:
                return 0
            
        except Exception as e:
            logger.error(f"Stok miktarı alınırken hata oluştu: {str(e)}")
            raise
    
    def get_product_images(self, stok_kodu):
        """Ürün resimlerini getir"""
        try:
            # Resimleri sorgula
            cur = self.connection.cursor()
            cur.execute("""
                SELECT 
                    RESIM,
                    RESIM2,
                    RESIM3,
                    RESIM4,
                    RESIM5
                FROM STOKLAR
                WHERE STOK_KODU = ?
            """, (stok_kodu,))
            
            row = cur.fetchone()
            if not row:
                return []
            
            images = []
            for image_path in row:
                if image_path and image_path.strip():
                    images.append(image_path.strip())
            
            logger.info(f"Resimler alındı: {stok_kodu} - {len(images)} adet")
            return images
            
        except Exception as e:
            logger.error(f"Resimler alınırken hata oluştu: {str(e)}")
            raise
        finally:
            if cur:
                cur.close()
    
    def close(self):
        """Veritabanı bağlantısını kapat"""
        if self.connection:
            self.connection.close()
            logger.info("Veritabanı bağlantısı kapatıldı")

if __name__ == "__main__":
    # Test
    reader = WolvoxProductReader()
    
    print("Ürünler listeleniyor...")
    print("-" * 50)
    
    products = reader.get_all_products()
    for product in products[:5]:  # İlk 5 ürünü göster
        print(f"Stok Kodu: {product['STOK_KODU']}")
        print(f"Stok Adı: {product['STOK_ADI']}")
        print(f"Barkod: {product['BARKOD']}")
        print(f"Satış Fiyatı 1: {product['SATIS_FIYATI1']}")
        print(f"Kategori: {product['KATEGORI']} > {product['MARKA']} > {product['MODEL']}")
        
        stock = reader.get_product_stock(product['STOK_KODU'])
        print(f"Stok Miktarı: {stock}")
        
        images = reader.get_product_images(product['STOK_KODU'])
        print(f"Resim Sayısı: {len(images)}")
        print("-" * 50)
    
    reader.close()
