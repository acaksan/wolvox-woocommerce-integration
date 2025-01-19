import os
import sys
from pathlib import Path

# Ana dizini Python path'ine ekle
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

import fdb
from dotenv import load_dotenv
import logging
from datetime import datetime

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/db_sync_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('DBSync')

class DBSync:
    def __init__(self):
        load_dotenv()
        self.db_path = os.getenv('DB_PATH')
        self.connection = None
        
    def connect(self):
        """Veritabanına bağlanır"""
        try:
            self.connection = fdb.connect(
                dsn=self.db_path,
                user='SYSDBA',
                password='masterkey'
            )
            logger.info("Veritabanı bağlantısı başarılı")
            return True
        except Exception as e:
            logger.error(f"Veritabanı bağlantısı başarısız: {str(e)}")
            return False
    
    def disconnect(self):
        """Veritabanı bağlantısını kapatır"""
        if self.connection:
            self.connection.close()
            logger.info("Veritabanı bağlantısı kapatıldı")
    
    def get_tire_products(self):
        """Lastik ürünlerini getirir"""
        try:
            if not self.connection:
                self.connect()
                
            cursor = self.connection.cursor()
            
            query = """
                SELECT 
                    s.STOKKODU,
                    s.STOK_ADI,
                    s.BARKODU,
                    s.BIRIMI,
                    s.KDV_ORANI,
                    s.MARKASI,
                    s.MODELI,
                    s.ETICARET_ACIKLAMA,
                    s.RESIM_YOLU,
                    s.GRUBU,
                    s.WEBDE_GORUNSUN,
                    s.AKTIF,
                    s.BLKODU,
                    (
                        SELECT COALESCE(SUM(CASE WHEN sh.TUTAR_TURU = 0 THEN sh.MIKTARI ELSE -sh.MIKTARI END), 0)
                        FROM STOKHR sh
                        WHERE sh.BLSTKODU = s.BLKODU
                    ) as STOK_MIKTARI
                FROM STOK s
                WHERE s.STOK_ADI LIKE '%LASTİ%'
                OR s.STOK_ADI LIKE '%LASTIK%'
                OR s.STOK_ADI LIKE '%LASTİK%'
            """
            
            cursor.execute(query)
            products = []
            
            for row in cursor.fetchall():
                product = {
                    'sku': row[0],
                    'name': row[1],
                    'barcode': row[2],
                    'unit': row[3],
                    'tax_rate': row[4],
                    'brand': row[5],
                    'model': row[6],
                    'description': row[7],
                    'image_path': row[8],
                    'group': row[9],
                    'show_on_web': row[10],
                    'active': row[11],
                    'bl_code': row[12],
                    'stock': float(row[13]) if row[13] else 0,
                }
                products.append(product)
            
            logger.info(f"Toplam {len(products)} lastik ürünü bulundu")
            return products
            
        except Exception as e:
            logger.error(f"Ürünler getirilirken hata oluştu: {str(e)}")
            raise
        finally:
            if cursor:
                cursor.close()
    
    def get_product_by_sku(self, sku):
        """SKU'ya göre ürün bilgilerini getirir"""
        try:
            if not self.connection:
                self.connect()
                
            cursor = self.connection.cursor()
            
            query = """
                SELECT 
                    s.STOKKODU,
                    s.STOK_ADI,
                    s.BARKODU,
                    s.BIRIMI,
                    s.KDV_ORANI,
                    s.MARKASI,
                    s.MODELI,
                    s.ETICARET_ACIKLAMA,
                    s.RESIM_YOLU,
                    s.GRUBU,
                    s.WEBDE_GORUNSUN,
                    s.AKTIF,
                    s.BLKODU,
                    (
                        SELECT COALESCE(SUM(CASE WHEN sh.TUTAR_TURU = 0 THEN sh.MIKTARI ELSE -sh.MIKTARI END), 0)
                        FROM STOKHR sh
                        WHERE sh.BLSTKODU = s.BLKODU
                    ) as STOK_MIKTARI
                FROM STOK s
                WHERE s.STOKKODU = ?
            """
            
            cursor.execute(query, (sku,))
            row = cursor.fetchone()
            
            if row:
                product = {
                    'sku': row[0],
                    'name': row[1],
                    'barcode': row[2],
                    'unit': row[3],
                    'tax_rate': row[4],
                    'brand': row[5],
                    'model': row[6],
                    'description': row[7],
                    'image_path': row[8],
                    'group': row[9],
                    'show_on_web': row[10],
                    'active': row[11],
                    'bl_code': row[12],
                    'stock': float(row[13]) if row[13] else 0,
                }
                return product
            
            return None
            
        except Exception as e:
            logger.error(f"Ürün bilgileri getirilirken hata oluştu: {str(e)}")
            raise
        finally:
            if cursor:
                cursor.close()

if __name__ == "__main__":
    # Test
    db = DBSync()
    if db.connect():
        try:
            print("Lastik ürünleri getiriliyor...")
            print("-" * 50)
            
            products = db.get_tire_products()
            for product in products[:5]:  # İlk 5 ürünü göster
                print(f"SKU: {product['sku']}")
                print(f"İsim: {product['name']}")
                print(f"Stok: {product['stock']}")
                print("-" * 50)
                
        finally:
            db.disconnect()
