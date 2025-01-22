import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from decimal import Decimal

from .wc_client import WooCommerceClient
from wolvox.product_reader import ProductReader

logger = logging.getLogger(__name__)

class WooCommerceSyncManager:
    def __init__(self, wc_client: WooCommerceClient, product_reader: ProductReader):
        """WooCommerce senkronizasyon yöneticisi

        Args:
            wc_client: WooCommerce API istemcisi
            product_reader: Wolvox ürün okuyucu
        """
        self.wc = wc_client
        self.reader = product_reader
        
    def sync_product(self, wolvox_product: Dict) -> Tuple[bool, str]:
        """Tek bir ürünü senkronize et

        Args:
            wolvox_product: Wolvox'tan gelen ürün verisi

        Returns:
            (başarı durumu, mesaj)
        """
        try:
            # SKU'ya göre WooCommerce'de ara
            sku = wolvox_product.get('STOK_KODU')
            if not sku:
                return False, "Stok kodu bulunamadı"
                
            wc_product = self.wc.get_product_by_sku(sku)
            
            # Ürün verilerini hazırla
            product_data = {
                'name': wolvox_product.get('STOK_ADI', ''),
                'sku': sku,
                'regular_price': str(wolvox_product.get('SATIS_FIYATI1', '0')),
                'manage_stock': True,
                'stock_quantity': int(wolvox_product.get('BAKIYE', 0)),
                'status': 'publish'
            }
            
            # Açıklama varsa ekle
            description = wolvox_product.get('ACIKLAMA')
            if description:
                product_data['description'] = description
                
            # Kategori varsa ekle
            category = wolvox_product.get('KATEGORI')
            if category:
                # Kategoriyi bul veya oluştur
                categories = self.wc.get_categories()
                category_id = None
                
                if categories:
                    for cat in categories:
                        if cat['name'].lower() == category.lower():
                            category_id = cat['id']
                            break
                            
                if not category_id:
                    new_category = self.wc.create_category(category)
                    if new_category:
                        category_id = new_category['id']
                        
                if category_id:
                    product_data['categories'] = [{'id': category_id}]
            
            if wc_product:
                # Ürün varsa güncelle
                product_id = wc_product['id']
                updated_product = self.wc.update_product(product_id, product_data)
                if updated_product:
                    return True, f"Ürün güncellendi: {sku}"
                else:
                    return False, f"Ürün güncellenemedi: {sku}"
            else:
                # Ürün yoksa oluştur
                new_product = self.wc.create_product(product_data)
                if new_product:
                    return True, f"Yeni ürün oluşturuldu: {sku}"
                else:
                    return False, f"Ürün oluşturulamadı: {sku}"
                    
        except Exception as e:
            logger.error(f"Ürün senkronizasyon hatası: {str(e)}")
            return False, f"Hata: {str(e)}"
            
    def sync_all_products(self) -> List[Tuple[bool, str]]:
        """Tüm ürünleri senkronize et

        Returns:
            [(başarı durumu, mesaj), ...]
        """
        results = []
        products = self.reader.get_all_products()
        
        if not products:
            return [(False, "Ürün bulunamadı")]
            
        for product in products:
            result = self.sync_product(product)
            results.append(result)
            
        return results
        
    def sync_stock_prices(self) -> List[Tuple[bool, str]]:
        """Stok ve fiyatları senkronize et

        Returns:
            [(başarı durumu, mesaj), ...]
        """
        results = []
        products = self.reader.get_all_products()
        
        if not products:
            return [(False, "Ürün bulunamadı")]
            
        batch_updates = []
        for product in products:
            try:
                sku = product.get('STOK_KODU')
                if not sku:
                    results.append((False, "Stok kodu bulunamadı"))
                    continue
                    
                wc_product = self.wc.get_product_by_sku(sku)
                if not wc_product:
                    results.append((False, f"WooCommerce'de ürün bulunamadı: {sku}"))
                    continue
                    
                update_data = {
                    'id': wc_product['id'],
                    'regular_price': str(product.get('SATIS_FIYATI1', '0')),
                    'manage_stock': True,
                    'stock_quantity': int(product.get('BAKIYE', 0))
                }
                
                batch_updates.append(update_data)
                
                # Her 100 üründe bir toplu güncelleme yap
                if len(batch_updates) >= 100:
                    response = self.wc.batch_update_products(batch_updates)
                    if response:
                        results.extend([(True, f"Ürün güncellendi: {u['sku']}") for u in batch_updates])
                    else:
                        results.extend([(False, f"Ürün güncellenemedi: {u['sku']}") for u in batch_updates])
                    batch_updates = []
                    
            except Exception as e:
                results.append((False, f"Hata: {str(e)}"))
                
        # Kalan güncellemeleri yap
        if batch_updates:
            response = self.wc.batch_update_products(batch_updates)
            if response:
                results.extend([(True, f"Ürün güncellendi: {u['sku']}") for u in batch_updates])
            else:
                results.extend([(False, f"Ürün güncellenemedi: {u['sku']}") for u in batch_updates])
                
        return results
