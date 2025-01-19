import os
import sys
from pathlib import Path

# Ana dizini Python path'ine ekle
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from woo_commerce.woocommerce_client import WooCommerceClient
from wolvox.product_reader import WolvoxProductReader
import logging
from datetime import datetime
import json

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/product_sync_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('ProductSync')

class ProductSync:
    def __init__(self):
        self.woo = WooCommerceClient()
        self.wolvox = WolvoxProductReader()
        self.load_category_mappings()
    
    def load_category_mappings(self):
        """Kategori eşleştirmelerini yükle"""
        try:
            if os.path.exists('category_mappings.json'):
                with open('category_mappings.json', 'r', encoding='utf-8') as f:
                    self.category_mappings = json.load(f)
            else:
                self.category_mappings = {}
        except Exception as e:
            logger.error(f"Kategori eşleştirmeleri yüklenirken hata: {str(e)}")
            self.category_mappings = {}
    
    def get_woo_category_id(self, wolvox_product):
        """Wolvox ürününün WooCommerce kategori ID'sini bul"""
        try:
            # Kategori kodlarını birleştir
            codes = []
            if wolvox_product['grup_kodu']:
                codes.append(str(wolvox_product['grup_kodu']))
            if wolvox_product['grup_ara_kodu']:
                codes.append(str(wolvox_product['grup_ara_kodu']))
            if wolvox_product['grup_alt_kodu']:
                codes.append(str(wolvox_product['grup_alt_kodu']))
            
            key = '_'.join(codes)
            
            # Eşleştirmeyi bul
            if key in self.category_mappings:
                return int(self.category_mappings[key]['woo_id'])
            
            return None
            
        except Exception as e:
            logger.error(f"WooCommerce kategori ID'si bulunurken hata: {str(e)}")
            return None
    
    def convert_to_woo_product(self, wolvox_product):
        """Wolvox ürününü WooCommerce formatına dönüştür"""
        try:
            # Kategori ID'sini bul
            category_id = self.get_woo_category_id(wolvox_product)
            
            # Temel ürün bilgileri
            product_data = {
                'name': wolvox_product['stok_adi'],
                'sku': wolvox_product['stok_kodu'],
                'regular_price': str(wolvox_product['satis_fiyati1']),
                'description': wolvox_product['aciklama'],
                'short_description': '',  # Kısa açıklama opsiyonel
                'manage_stock': True,
                'stock_quantity': self.wolvox.get_product_stock(wolvox_product['stok_kodu']),
                'status': 'publish',
                'tax_status': 'taxable',
                'tax_class': f'kdv-{int(wolvox_product["kdv_orani"])}',
                'attributes': [
                    {
                        'name': 'Birim',
                        'visible': True,
                        'options': [wolvox_product['stok_birimi']]
                    },
                    {
                        'name': 'Barkod',
                        'visible': True,
                        'options': [wolvox_product['barkod']]
                    }
                ]
            }
            
            # Kategori ekle
            if category_id:
                product_data['categories'] = [{'id': category_id}]
            
            # Resimler
            images = self.wolvox.get_product_images(wolvox_product['stok_kodu'])
            if images:
                product_data['images'] = [{'src': img_path} for img_path in images]
            
            return product_data
            
        except Exception as e:
            logger.error(f"Ürün dönüştürülürken hata: {str(e)}")
            raise
    
    def sync_all_products(self):
        """Tüm ürünleri senkronize et"""
        try:
            # Wolvox'tan tüm ürünleri al
            wolvox_products = self.wolvox.get_all_products()
            logger.info(f"{len(wolvox_products)} adet ürün bulundu")
            
            # WooCommerce'deki mevcut ürünleri al
            existing_products = {}
            page = 1
            while True:
                products = self.woo.list_products(page=page)
                if not products:
                    break
                
                for product in products:
                    existing_products[product['sku']] = product['id']
                page += 1
            
            logger.info(f"{len(existing_products)} adet mevcut WooCommerce ürünü bulundu")
            
            # Her ürün için senkronizasyon yap
            for wolvox_product in wolvox_products:
                try:
                    sku = wolvox_product['stok_kodu']
                    product_data = self.convert_to_woo_product(wolvox_product)
                    
                    if sku in existing_products:
                        # Mevcut ürünü güncelle
                        product_id = existing_products[sku]
                        self.update_existing_product(product_id, product_data)
                        logger.info(f"Ürün güncellendi: {sku}")
                    else:
                        # Yeni ürün oluştur
                        self.create_new_product(product_data)
                        logger.info(f"Yeni ürün oluşturuldu: {sku}")
                    
                except Exception as e:
                    logger.error(f"Ürün senkronize edilirken hata: {sku} - {str(e)}")
                    continue
            
            logger.info("Ürün senkronizasyonu tamamlandı")
            
        except Exception as e:
            logger.error(f"Ürün senkronizasyonu sırasında hata: {str(e)}")
            raise
        finally:
            self.wolvox.close()
    
    def sync_stock_quantities(self):
        """Sadece stok miktarlarını senkronize et"""
        try:
            # Wolvox'tan tüm ürünleri al
            wolvox_products = self.wolvox.get_all_products()
            
            # WooCommerce'deki mevcut ürünleri al
            existing_products = {}
            page = 1
            while True:
                products = self.woo.list_products(page=page)
                if not products:
                    break
                
                for product in products:
                    existing_products[product['sku']] = product['id']
                page += 1
            
            # Her ürün için stok senkronizasyonu yap
            for wolvox_product in wolvox_products:
                try:
                    sku = wolvox_product['stok_kodu']
                    if sku in existing_products:
                        product_id = existing_products[sku]
                        stock_quantity = self.wolvox.get_product_stock(sku)
                        self.sync_stock_quantity(product_id, stock_quantity)
                        logger.info(f"Stok güncellendi: {sku} - {stock_quantity}")
                    
                except Exception as e:
                    logger.error(f"Stok senkronize edilirken hata: {sku} - {str(e)}")
                    continue
            
            logger.info("Stok senkronizasyonu tamamlandı")
            
        except Exception as e:
            logger.error(f"Stok senkronizasyonu sırasında hata: {str(e)}")
            raise
        finally:
            self.wolvox.close()

    def list_all_products(self):
        """Tüm ürünleri listeler"""
        try:
            page = 1
            while True:
                products = self.woo.list_products(page=page)
                if not products:
                    break
                    
                for product in products:
                    print(f"ID: {product['id']}")
                    print(f"İsim: {product['name']}")
                    print(f"SKU: {product['sku']}")
                    print(f"Fiyat: {product['price']}")
                    print(f"Stok: {product['stock_quantity']}")
                    print("-" * 50)
                
                page += 1
                
        except Exception as e:
            logger.error(f"Ürünler listelenirken hata oluştu: {str(e)}")
            raise
    
    def create_new_product(self, product_data):
        """Yeni ürün oluşturur"""
        try:
            result = self.woo.create_product(product_data)
            logger.info(f"Yeni ürün oluşturuldu: {result['name']} (ID: {result['id']})")
            return result
        except Exception as e:
            logger.error(f"Ürün oluşturulurken hata oluştu: {str(e)}")
            raise
    
    def update_existing_product(self, product_id, product_data):
        """Mevcut ürünü günceller"""
        try:
            result = self.woo.update_product(product_id, product_data)
            logger.info(f"Ürün güncellendi: {result['name']} (ID: {result['id']})")
            return result
        except Exception as e:
            logger.error(f"Ürün güncellenirken hata oluştu: {str(e)}")
            raise
    
    def sync_stock_quantity(self, product_id, stock_quantity):
        """Stok miktarını senkronize eder"""
        try:
            result = self.woo.update_product_stock(product_id, stock_quantity)
            logger.info(f"Stok güncellendi: {result['name']} (ID: {result['id']}) - Yeni stok: {stock_quantity}")
            return result
        except Exception as e:
            logger.error(f"Stok güncellenirken hata oluştu: {str(e)}")
            raise

    def match_products_by_stock_number(self):
        """Stok numarası aynı olan ürünleri eşleştir"""
        try:
            # Wolvox'tan tüm ürünleri al
            wolvox_products = self.wolvox.get_all_products()
            logger.info(f"{len(wolvox_products)} adet Wolvox ürünü bulundu")
            
            # WooCommerce'den tüm ürünleri al
            woo_products = {}
            page = 1
            while True:
                products = self.woo.list_products(page=page)
                if not products:
                    break
                
                for product in products:
                    if product.get('sku'):  # SKU boş olmayanları al
                        woo_products[product['sku']] = product['id']
                page += 1
            
            logger.info(f"{len(woo_products)} adet WooCommerce ürünü bulundu")
            
            # Eşleşen ve eşleşmeyen ürünleri bul
            matched = []
            unmatched_wolvox = []
            unmatched_woo = []
            
            for wolvox_product in wolvox_products:
                sku = wolvox_product['stok_kodu']
                if sku in woo_products:
                    matched.append({
                        'sku': sku,
                        'wolvox_name': wolvox_product['stok_adi'],
                        'woo_id': woo_products[sku]
                    })
                else:
                    unmatched_wolvox.append({
                        'sku': sku,
                        'name': wolvox_product['stok_adi']
                    })
            
            # WooCommerce'de olup Wolvox'ta olmayan ürünleri bul
            for sku, woo_id in woo_products.items():
                if not any(p['stok_kodu'] == sku for p in wolvox_products):
                    unmatched_woo.append({
                        'sku': sku,
                        'id': woo_id
                    })
            
            # Sonuçları yazdır
            print("\nEşleşen Ürünler:")
            print("-" * 50)
            for item in matched:
                print(f"SKU: {item['sku']}")
                print(f"Wolvox Adı: {item['wolvox_name']}")
                print(f"WooCommerce ID: {item['woo_id']}")
                print("-" * 30)
            
            print("\nWolvox'ta olup WooCommerce'de olmayan ürünler:")
            print("-" * 50)
            for item in unmatched_wolvox:
                print(f"SKU: {item['sku']}")
                print(f"Wolvox Adı: {item['name']}")
                print("-" * 30)
            
            print("\nWooCommerce'de olup Wolvox'ta olmayan ürünler:")
            print("-" * 50)
            for item in unmatched_woo:
                print(f"SKU: {item['sku']}")
                print(f"WooCommerce ID: {item['id']}")
                print("-" * 30)
            
            # İstatistikler
            print("\nÖzet:")
            print("-" * 50)
            print(f"Toplam Wolvox Ürünü: {len(wolvox_products)}")
            print(f"Toplam WooCommerce Ürünü: {len(woo_products)}")
            print(f"Eşleşen Ürün Sayısı: {len(matched)}")
            print(f"Wolvox'ta olup WooCommerce'de olmayan: {len(unmatched_wolvox)}")
            print(f"WooCommerce'de olup Wolvox'ta olmayan: {len(unmatched_woo)}")
            
            return {
                'matched': matched,
                'unmatched_wolvox': unmatched_wolvox,
                'unmatched_woo': unmatched_woo
            }
            
        except Exception as e:
            logger.error(f"Ürünler eşleştirilirken hata: {str(e)}")
            raise
        finally:
            self.wolvox.close()

if __name__ == "__main__":
    # Test
    sync = ProductSync()
    
    print("Ürün eşleştirmesi başlatılıyor...")
    print("-" * 50)
    sync.match_products_by_stock_number()
