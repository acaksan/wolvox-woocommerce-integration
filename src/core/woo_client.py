from woocommerce import API
from config.settings import Settings
from utils.logger import setup_logger

class WooClient:
    def __init__(self):
        self.settings = Settings()
        self.logger = setup_logger("woo_client")
        
        # WooCommerce API istemcisini başlat
        url = self.settings.get("woo.url")
        if not url.startswith("https://"):
            url = "https://" + url
            
        self.logger.info(f"WooCommerce URL: {url}")
        self.logger.info(f"WooCommerce Key: {self.settings.get('woo.key')}")
        
        self.client = API(
            url=url,
            consumer_key=self.settings.get("woo.key"),
            consumer_secret=self.settings.get("woo.secret"),
            version=self.settings.get("woo.version", "wc/v3"),
            verify=False,  # SSL sertifikası olmayan siteler için
            timeout=30
        )
    
    def get_products(self):
        """Ürünleri getir"""
        try:
            self.logger.info("WooCommerce'den ürünler getiriliyor...")
            
            # WooCommerce'den ürünleri getir
            response = self.client.get("products", params={
                "per_page": 100,
                "status": "publish",  # Sadece yayınlanmış ürünler
                "orderby": "date",    # Tarihe göre sırala
                "order": "desc"       # Yeniden eskiye
            })
            
            self.logger.info(f"WooCommerce yanıt kodu: {response.status_code}")
            self.logger.info(f"WooCommerce yanıt başlıkları: {response.headers}")
            
            try:
                products = response.json()
                self.logger.info(f"WooCommerce yanıt içeriği: {products}")
            except Exception as e:
                self.logger.error(f"JSON parse hatası: {str(e)}")
                products = []
            
            if isinstance(products, dict) and "code" in products:
                self.logger.error(f"WooCommerce API hatası: {products}")
                return []
                
            self.logger.info(f"WooCommerce'den {len(products)} ürün alındı")
            
            # Sonuçları dön
            result = []
            seen_skus = set()  # Yinelenen SKU'ları kontrol etmek için
            
            for product in products:
                if isinstance(product, str):
                    self.logger.warning(f"Geçersiz ürün verisi: {product}")
                    continue
                    
                sku = product.get("sku", "")
                if not sku:
                    self.logger.warning(f"SKU'su olmayan ürün: {product.get('id')}")
                    continue
                    
                if sku in seen_skus:
                    self.logger.warning(f"Yinelenen SKU: {sku}")
                    continue
                    
                seen_skus.add(sku)
                try:
                    item = {
                        "id": product["id"],
                        "sku": sku,
                        "name": product["name"],
                        "price": float(product.get("price", 0) or 0),
                        "stock": int(product.get("stock_quantity", 0) or 0),
                        "status": product["status"],
                        "description": product.get("description", ""),
                        "short_description": product.get("short_description", ""),
                        "category": ", ".join([cat["name"] for cat in product.get("categories", [])]),
                        "tags": ", ".join([tag["name"] for tag in product.get("tags", [])]),
                        "visibility": "Görünür" if product["status"] == "publish" else "Gizli"
                    }
                    result.append(item)
                except Exception as e:
                    self.logger.error(f"Ürün dönüştürme hatası: {str(e)}, Ürün: {product}")
            
            self.logger.info(f"Toplam {len(result)} ürün dönüştürüldü")
            return result
            
        except Exception as e:
            self.logger.error(f"Ürünler getirilirken hata: {str(e)}")
            return []
    
    def update_product(self, product_id, data):
        """Ürün güncelle"""
        try:
            response = self.client.put(f"products/{product_id}", data).json()
            return response
        except Exception as e:
            self.logger.error(f"Ürün güncellenirken hata: {str(e)}")
            return None
    
    def test_connection(self):
        """Bağlantıyı test et"""
        try:
            response = self.client.get("").json()
            if response:
                self.logger.info("WooCommerce bağlantı testi başarılı")
                return True
        except Exception as e:
            self.logger.error(f"WooCommerce bağlantı hatası: {str(e)}")
        return False
