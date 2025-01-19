import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
import json

# Load environment variables
load_dotenv()

try:
    # WooCommerce API credentials
    url = os.getenv('WOOCOMMERCE_URL')
    consumer_key = os.getenv('WOOCOMMERCE_CONSUMER_KEY')
    consumer_secret = os.getenv('WOOCOMMERCE_CONSUMER_SECRET')

    # Test connection by getting products
    print("WooCommerce bağlantısı test ediliyor...")
    
    # API endpoint
    endpoint = f"{url}/wp-json/wc/v3/products"
    
    # Make request
    response = requests.get(
        endpoint,
        auth=HTTPBasicAuth(consumer_key, consumer_secret),
        verify=False  # SSL sertifika doğrulamasını devre dışı bırak
    )
    
    if response.status_code == 200:
        products = response.json()
        print(f"\nBağlantı başarılı!")
        print(f"Toplam ürün sayısı: {len(products)}")
        
        # İlk birkaç ürünü göster
        print("\nÖrnek ürünler:")
        for product in products[:3]:  # İlk 3 ürün
            print(f"- {product.get('name')} (ID: {product.get('id')})")
    else:
        print(f"Hata! Status code: {response.status_code}")
        print(f"Hata mesajı: {response.text}")

except Exception as e:
    print(f"Hata oluştu: {str(e)}")
