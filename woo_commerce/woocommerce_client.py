import os
import requests
from requests.auth import HTTPBasicAuth
import json
from dotenv import load_dotenv
import logging
from datetime import datetime

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/woocommerce_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('WooCommerceClient')

class WooCommerceClient:
    def __init__(self):
        load_dotenv()
        self.url = os.getenv('WOOCOMMERCE_URL')
        self.consumer_key = os.getenv('WOOCOMMERCE_CONSUMER_KEY')
        self.consumer_secret = os.getenv('WOOCOMMERCE_CONSUMER_SECRET')
        self.base_url = f"{self.url}/wp-json/wc/v3"
        
    def _make_request(self, endpoint, method='GET', data=None, params=None):
        """API isteklerini yönetir"""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                auth=HTTPBasicAuth(self.consumer_key, self.consumer_secret),
                json=data if data else None,
                params=params if params else None,
                verify=False
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API isteği başarısız: {str(e)}")
            if hasattr(e.response, 'text'):
                logger.error(f"API yanıtı: {e.response.text}")
            raise
    
    def list_products(self, page=1, per_page=10):
        """Ürünleri listeler"""
        try:
            params = {
                'page': page,
                'per_page': per_page
            }
            return self._make_request('products', params=params)
        except Exception as e:
            logger.error(f"Ürünler listelenirken hata oluştu: {str(e)}")
            raise
    
    def get_product(self, product_id):
        """Belirli bir ürünün detaylarını getirir"""
        try:
            return self._make_request(f'products/{product_id}')
        except Exception as e:
            logger.error(f"Ürün detayları alınırken hata oluştu: {str(e)}")
            raise
    
    def create_product(self, product_data):
        """Yeni ürün oluşturur"""
        try:
            return self._make_request('products', method='POST', data=product_data)
        except Exception as e:
            logger.error(f"Ürün oluşturulurken hata oluştu: {str(e)}")
            raise
    
    def update_product(self, product_id, product_data):
        """Mevcut ürünü günceller"""
        try:
            return self._make_request(f'products/{product_id}', method='PUT', data=product_data)
        except Exception as e:
            logger.error(f"Ürün güncellenirken hata oluştu: {str(e)}")
            raise
    
    def update_product_stock(self, product_id, stock_quantity):
        """Ürün stok miktarını günceller"""
        try:
            data = {
                'stock_quantity': stock_quantity
            }
            return self._make_request(f'products/{product_id}', method='PUT', data=data)
        except Exception as e:
            logger.error(f"Stok güncellenirken hata oluştu: {str(e)}")
            raise
    
    def get_product_categories(self):
        """Ürün kategorilerini listeler"""
        try:
            return self._make_request('products/categories')
        except Exception as e:
            logger.error(f"Kategoriler listelenirken hata oluştu: {str(e)}")
            raise
    
    def create_product_category(self, category_data):
        """Yeni kategori oluşturur"""
        try:
            return self._make_request('products/categories', method='POST', data=category_data)
        except Exception as e:
            logger.error(f"Kategori oluşturulurken hata oluştu: {str(e)}")
            raise
