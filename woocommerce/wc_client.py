import requests
import logging
from typing import Dict, List, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class WooCommerceClient:
    def __init__(self, url: str, consumer_key: str, consumer_secret: str):
        """WooCommerce API istemcisi

        Args:
            url: WooCommerce site URL'si
            consumer_key: API Consumer Key
            consumer_secret: API Consumer Secret
        """
        self.url = url.rstrip('/')
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.api_url = f"{self.url}/wp-json/wc/v3"
        self.auth = (consumer_key, consumer_secret)

    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Optional[Union[Dict, List]]:
        """API isteği gönder

        Args:
            method: HTTP metodu (GET, POST, PUT, DELETE)
            endpoint: API endpoint'i
            params: URL parametreleri
            data: POST/PUT için veri

        Returns:
            API yanıtı
        """
        url = f"{self.api_url}/{endpoint}"
        try:
            response = requests.request(
                method=method,
                url=url,
                auth=self.auth,
                params=params,
                json=data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"WooCommerce API hatası: {str(e)}")
            return None

    def get_product_by_sku(self, sku: str) -> Optional[Dict]:
        """SKU'ya göre ürün getir"""
        params = {'sku': sku}
        products = self._make_request('GET', 'products', params=params)
        if products and len(products) > 0:
            return products[0]
        return None

    def create_product(self, data: Dict) -> Optional[Dict]:
        """Yeni ürün oluştur"""
        return self._make_request('POST', 'products', data=data)

    def update_product(self, product_id: int, data: Dict) -> Optional[Dict]:
        """Ürün güncelle"""
        return self._make_request('PUT', f'products/{product_id}', data=data)

    def get_categories(self) -> Optional[List[Dict]]:
        """Tüm kategorileri getir"""
        return self._make_request('GET', 'products/categories', params={'per_page': 100})

    def create_category(self, name: str, parent: int = 0) -> Optional[Dict]:
        """Yeni kategori oluştur"""
        data = {
            'name': name,
            'parent': parent
        }
        return self._make_request('POST', 'products/categories', data=data)

    def update_stock(self, product_id: int, quantity: int, manage_stock: bool = True) -> Optional[Dict]:
        """Stok miktarını güncelle"""
        data = {
            'stock_quantity': quantity,
            'manage_stock': manage_stock,
            'stock_status': 'instock' if quantity > 0 else 'outofstock'
        }
        return self.update_product(product_id, data)

    def update_price(self, product_id: int, regular_price: str, sale_price: Optional[str] = None) -> Optional[Dict]:
        """Fiyat güncelle"""
        data = {
            'regular_price': regular_price
        }
        if sale_price:
            data['sale_price'] = sale_price
        return self.update_product(product_id, data)

    def batch_update_products(self, updates: List[Dict]) -> Optional[Dict]:
        """Toplu ürün güncelleme"""
        data = {'update': updates}
        return self._make_request('POST', 'products/batch', data=data)

    def get_product_variations(self, product_id: int) -> Optional[List[Dict]]:
        """Ürün varyasyonlarını getir"""
        return self._make_request('GET', f'products/{product_id}/variations')

    def create_product_variation(self, product_id: int, data: Dict) -> Optional[Dict]:
        """Ürün varyasyonu oluştur"""
        return self._make_request('POST', f'products/{product_id}/variations', data=data)

    def update_product_variation(self, product_id: int, variation_id: int, data: Dict) -> Optional[Dict]:
        """Ürün varyasyonu güncelle"""
        return self._make_request('PUT', f'products/{product_id}/variations/{variation_id}', data=data)

    def get_orders(self, status: Optional[str] = None, after: Optional[datetime] = None) -> Optional[List[Dict]]:
        """Siparişleri getir"""
        params = {'per_page': 100}
        if status:
            params['status'] = status
        if after:
            params['after'] = after.isoformat()
        return self._make_request('GET', 'orders', params=params)

    def update_order_status(self, order_id: int, status: str) -> Optional[Dict]:
        """Sipariş durumunu güncelle"""
        data = {'status': status}
        return self._make_request('PUT', f'orders/{order_id}', data=data)
