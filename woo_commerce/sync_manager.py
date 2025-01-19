import os
import sys
from pathlib import Path

# Ana dizini Python path'ine ekle
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from woo_commerce.woocommerce_client import WooCommerceClient
from woo_commerce.db_sync import DBSync
import logging
from datetime import datetime

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/sync_manager_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('SyncManager')

class SyncManager:
    def __init__(self):
        self.woo = WooCommerceClient()
        self.db = DBSync()
        
    def sync_all_products(self):
        """Tüm ürünleri senkronize eder"""
        try:
            # Veritabanına bağlan
            if not self.db.connect():
                raise Exception("Veritabanı bağlantısı kurulamadı")
            
            # Veritabanından ürünleri al
            db_products = self.db.get_tire_products()
            logger.info(f"Veritabanından {len(db_products)} ürün alındı")
            
            # WooCommerce'daki ürünleri al
            woo_products = self.woo.list_products(per_page=100)
            
            # SKU'ya göre WooCommerce ürünlerini maple
            woo_products_map = {p['sku']: p for p in woo_products if p['sku']}
            
            updated_count = 0
            created_count = 0
            
            # Her ürün için kontrol et
            for db_product in db_products:
                try:
                    # Ürün WooCommerce'da var mı?
                    if db_product['sku'] in woo_products_map:
                        # Ürünü güncelle
                        woo_product = woo_products_map[db_product['sku']]
                        self._update_product(woo_product['id'], db_product)
                        updated_count += 1
                    else:
                        # Yeni ürün oluştur
                        self._create_product(db_product)
                        created_count += 1
                        
                except Exception as e:
                    logger.error(f"Ürün senkronizasyonunda hata: {str(e)}")
                    continue
            
            logger.info(f"Senkronizasyon tamamlandı: {created_count} yeni ürün, {updated_count} güncelleme")
            
        except Exception as e:
            logger.error(f"Senkronizasyon sırasında hata oluştu: {str(e)}")
            raise
        finally:
            self.db.disconnect()
    
    def sync_stock_levels(self):
        """Sadece stok seviyelerini senkronize eder"""
        try:
            # Veritabanına bağlan
            if not self.db.connect():
                raise Exception("Veritabanı bağlantısı kurulamadı")
            
            # Veritabanından ürünleri al
            db_products = self.db.get_tire_products()
            
            # WooCommerce'daki ürünleri al
            woo_products = self.woo.list_products(per_page=100)
            
            # SKU'ya göre WooCommerce ürünlerini maple
            woo_products_map = {p['sku']: p for p in woo_products if p['sku']}
            
            updated_count = 0
            
            # Her ürün için stok kontrolü yap
            for db_product in db_products:
                try:
                    if db_product['sku'] in woo_products_map:
                        woo_product = woo_products_map[db_product['sku']]
                        
                        # Stok miktarı farklı ise güncelle
                        if woo_product.get('stock_quantity') != db_product['stock']:
                            self.woo.update_product_stock(
                                woo_product['id'],
                                db_product['stock']
                            )
                            updated_count += 1
                            
                except Exception as e:
                    logger.error(f"Stok güncellemede hata: {str(e)}")
                    continue
            
            logger.info(f"Stok senkronizasyonu tamamlandı: {updated_count} ürün güncellendi")
            
        except Exception as e:
            logger.error(f"Stok senkronizasyonu sırasında hata oluştu: {str(e)}")
            raise
        finally:
            self.db.disconnect()
    
    def _create_product(self, db_product):
        """Yeni ürün oluşturur"""
        product_data = {
            'name': db_product['name'],
            'sku': db_product['sku'],
            'regular_price': str(db_product['price']),
            'stock_quantity': db_product['stock'],
            'manage_stock': True,
            'type': 'simple',
            'attributes': [
                {
                    'name': 'Genişlik',
                    'visible': True,
                    'options': [db_product['width']] if db_product['width'] else []
                },
                {
                    'name': 'Kesit Oranı',
                    'visible': True,
                    'options': [db_product['aspect_ratio']] if db_product['aspect_ratio'] else []
                },
                {
                    'name': 'Yapı',
                    'visible': True,
                    'options': [db_product['construction']] if db_product['construction'] else []
                },
                {
                    'name': 'Jant Çapı',
                    'visible': True,
                    'options': [db_product['rim_diameter']] if db_product['rim_diameter'] else []
                },
                {
                    'name': 'Yük Endeksi',
                    'visible': True,
                    'options': [db_product['load_index']] if db_product['load_index'] else []
                }
            ]
        }
        
        self.woo.create_product(product_data)
        logger.info(f"Yeni ürün oluşturuldu: {db_product['name']} (SKU: {db_product['sku']})")
    
    def _update_product(self, product_id, db_product):
        """Mevcut ürünü günceller"""
        product_data = {
            'name': db_product['name'],
            'regular_price': str(db_product['price']),
            'stock_quantity': db_product['stock'],
            'attributes': [
                {
                    'name': 'Genişlik',
                    'visible': True,
                    'options': [db_product['width']] if db_product['width'] else []
                },
                {
                    'name': 'Kesit Oranı',
                    'visible': True,
                    'options': [db_product['aspect_ratio']] if db_product['aspect_ratio'] else []
                },
                {
                    'name': 'Yapı',
                    'visible': True,
                    'options': [db_product['construction']] if db_product['construction'] else []
                },
                {
                    'name': 'Jant Çapı',
                    'visible': True,
                    'options': [db_product['rim_diameter']] if db_product['rim_diameter'] else []
                },
                {
                    'name': 'Yük Endeksi',
                    'visible': True,
                    'options': [db_product['load_index']] if db_product['load_index'] else []
                }
            ]
        }
        
        self.woo.update_product(product_id, product_data)
        logger.info(f"Ürün güncellendi: {db_product['name']} (SKU: {db_product['sku']})")

if __name__ == "__main__":
    # Test
    sync = SyncManager()
    
    print("Ürün senkronizasyonu başlatılıyor...")
    print("-" * 50)
    
    # Tüm ürünleri senkronize et
    sync.sync_all_products()
