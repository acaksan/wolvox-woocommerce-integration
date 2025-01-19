import os
import fdb
from dotenv import load_dotenv
import logging
from datetime import datetime

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
            cur = self.connection.cursor()
            
            # Ürünleri sorgula
            cur.execute("""
                SELECT 
                    s.STOK_KODU,
                    s.STOK_ADI,
                    s.BARKOD,
                    s.SATIS_FIYATI1,
                    s.SATIS_FIYATI2,
                    s.KDV_ORANI,
                    s.STOK_BIRIMI,
                    s.GRUP_KODU,
                    s.GRUP_ARA_KODU,
                    s.GRUP_ALT_KODU,
                    s.ACIKLAMA,
                    s.WEBDE_GORUNSUN,
                    s.AKTIF,
                    s.RESIM,
                    g.GRUP_ADI as ANA_GRUP,
                    ga.GRUP_ADI as ARA_GRUP,
                    galt.GRUP_ADI as ALT_GRUP
                FROM STOKLAR s
                LEFT JOIN GRUP g ON s.GRUP_KODU = g.BLKODU
                LEFT JOIN GRUP_ARA ga ON s.GRUP_ARA_KODU = ga.BLKODU
                LEFT JOIN GRUP_ALT galt ON s.GRUP_ALT_KODU = galt.BLKODU
                WHERE s.WEBDE_GORUNSUN = 1 
                AND s.AKTIF = 1
                ORDER BY s.STOK_KODU
            """)
            
            products = []
            for row in cur.fetchall():
                product = {
                    'stok_kodu': row[0],
                    'stok_adi': row[1].strip() if row[1] else '',
                    'barkod': row[2].strip() if row[2] else '',
                    'satis_fiyati1': float(row[3]) if row[3] else 0,
                    'satis_fiyati2': float(row[4]) if row[4] else 0,
                    'kdv_orani': float(row[5]) if row[5] else 0,
                    'stok_birimi': row[6].strip() if row[6] else '',
                    'grup_kodu': row[7],
                    'grup_ara_kodu': row[8],
                    'grup_alt_kodu': row[9],
                    'aciklama': row[10].strip() if row[10] else '',
                    'webde_gorunsun': bool(row[11]),
                    'aktif': bool(row[12]),
                    'resim': row[13].strip() if row[13] else '',
                    'ana_grup': row[14].strip() if row[14] else '',
                    'ara_grup': row[15].strip() if row[15] else '',
                    'alt_grup': row[16].strip() if row[16] else ''
                }
                products.append(product)
            
            logger.info(f"{len(products)} adet ürün bulundu")
            return products
            
        except Exception as e:
            logger.error(f"Ürünler alınırken hata oluştu: {str(e)}")
            raise
        finally:
            if cur:
                cur.close()
    
    def get_product_stock(self, stok_kodu):
        """Ürün stok miktarını getir"""
        try:
            cur = self.connection.cursor()
            
            # Stok miktarını sorgula
            cur.execute("""
                SELECT 
                    COALESCE(SUM(MIKTAR), 0) as STOK_MIKTARI
                FROM STOK_HAREKETLERI
                WHERE STOK_KODU = ?
                GROUP BY STOK_KODU
            """, (stok_kodu,))
            
            row = cur.fetchone()
            stock_quantity = float(row[0]) if row else 0
            
            logger.info(f"Stok miktarı alındı: {stok_kodu} - {stock_quantity}")
            return stock_quantity
            
        except Exception as e:
            logger.error(f"Stok miktarı alınırken hata oluştu: {str(e)}")
            raise
        finally:
            if cur:
                cur.close()
    
    def get_product_images(self, stok_kodu):
        """Ürün resimlerini getir"""
        try:
            cur = self.connection.cursor()
            
            # Resimleri sorgula
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
        print(f"Stok Kodu: {product['stok_kodu']}")
        print(f"Stok Adı: {product['stok_adi']}")
        print(f"Barkod: {product['barkod']}")
        print(f"Satış Fiyatı 1: {product['satis_fiyati1']}")
        print(f"Kategori: {product['ana_grup']} > {product['ara_grup']} > {product['alt_grup']}")
        
        stock = reader.get_product_stock(product['stok_kodu'])
        print(f"Stok Miktarı: {stock}")
        
        images = reader.get_product_images(product['stok_kodu'])
        print(f"Resim Sayısı: {len(images)}")
        print("-" * 50)
    
    reader.close()
