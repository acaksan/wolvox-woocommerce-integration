import os
import logging
from dotenv import load_dotenv
from woocommerce import API
import pyodbc
import schedule
import time
from datetime import datetime

# Logging yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sync.log'),
        logging.StreamHandler()
    ]
)

# .env dosyasından konfigürasyon yükleme
load_dotenv()

class WolvoxWooCommerceSync:
    def __init__(self):
        # WooCommerce API bağlantısı
        self.wcapi = API(
            url=os.getenv('WOOCOMMERCE_URL'),
            consumer_key=os.getenv('WOOCOMMERCE_KEY'),
            consumer_secret=os.getenv('WOOCOMMERCE_SECRET'),
            version="wc/v3"
        )
        
        # Wolvox veritabanı bağlantısı
        self.conn = pyodbc.connect(os.getenv('WOLVOX_CONNECTION_STRING'))
        self.cursor = self.conn.cursor()

    def sync_products(self):
        """Wolvox'tan WooCommerce'e ürün senkronizasyonu"""
        try:
            # Wolvox'tan ürünleri çek
            self.cursor.execute("SELECT * FROM ITEMS WHERE ACTIVE = 1")
            products = self.cursor.fetchall()

            for product in products:
                # WooCommerce'de ürün güncelleme/ekleme işlemi
                product_data = {
                    'name': product.NAME,
                    'regular_price': str(product.PRICE),
                    'stock_quantity': product.STOCK,
                    'manage_stock': True
                }

                # Ürün WooCommerce'de var mı kontrol et
                woo_products = self.wcapi.get(f"products?sku={product.CODE}").json()
                
                if woo_products:
                    # Ürün varsa güncelle
                    self.wcapi.put(f"products/{woo_products[0]['id']}", product_data)
                    logging.info(f"Ürün güncellendi: {product.NAME}")
                else:
                    # Ürün yoksa yeni ekle
                    product_data['sku'] = product.CODE
                    self.wcapi.post("products", product_data)
                    logging.info(f"Yeni ürün eklendi: {product.NAME}")

        except Exception as e:
            logging.error(f"Ürün senkronizasyonunda hata: {str(e)}")

    def sync_orders(self):
        """WooCommerce'den Wolvox'a sipariş senkronizasyonu"""
        try:
            # Son 24 saatteki siparişleri al
            orders = self.wcapi.get("orders?status=processing").json()

            for order in orders:
                # Siparişin Wolvox'ta olup olmadığını kontrol et
                self.cursor.execute("SELECT * FROM ORDERS WHERE ORDER_NO = ?", (order['id'],))
                existing_order = self.cursor.fetchone()

                if not existing_order:
                    # Yeni siparişi Wolvox'a ekle
                    order_date = datetime.fromisoformat(order['date_created'].replace('Z', '+00:00'))
                    
                    # Sipariş başlığını ekle
                    self.cursor.execute("""
                        INSERT INTO ORDERS (ORDER_NO, ORDER_DATE, CUSTOMER_NAME, TOTAL_AMOUNT)
                        VALUES (?, ?, ?, ?)
                    """, (order['id'], order_date, order['billing']['first_name'] + ' ' + order['billing']['last_name'], order['total']))

                    # Sipariş detaylarını ekle
                    for item in order['line_items']:
                        self.cursor.execute("""
                            INSERT INTO ORDER_DETAILS (ORDER_ID, PRODUCT_CODE, QUANTITY, PRICE)
                            VALUES (?, ?, ?, ?)
                        """, (order['id'], item['sku'], item['quantity'], item['price']))

                    self.conn.commit()
                    logging.info(f"Yeni sipariş eklendi: {order['id']}")

        except Exception as e:
            logging.error(f"Sipariş senkronizasyonunda hata: {str(e)}")

    def close_connections(self):
        """Veritabanı bağlantılarını kapat"""
        self.cursor.close()
        self.conn.close()

def main():
    sync = WolvoxWooCommerceSync()

    # Periyodik senkronizasyon görevlerini planla
    schedule.every(30).minutes.do(sync.sync_products)  # Her 30 dakikada bir ürün senkronizasyonu
    schedule.every(15).minutes.do(sync.sync_orders)    # Her 15 dakikada bir sipariş senkronizasyonu

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logging.info("Program sonlandırılıyor...")
        sync.close_connections()

if __name__ == "__main__":
    main()
