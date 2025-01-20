import os
import logging
from dotenv import load_dotenv
from woocommerce import API
import fdb
import schedule
import time
from datetime import datetime
import requests

# Logging yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# .env dosyasından konfigürasyon yükleme
load_dotenv()

class WolvoxWooCommerceSync:
    def __init__(self):
        self.stats = {
            'products': 0,
            'orders': 0,
            'categories': 0,
            'last_sync': None,
            'errors': 0
        }
        self.last_sync = None
        self.exchange_rates = {}
        
        # WooCommerce API bağlantısı
        self.wcapi = API(
            url=os.getenv('WOOCOMMERCE_URL'),
            consumer_key=os.getenv('WOOCOMMERCE_CONSUMER_KEY'),
            consumer_secret=os.getenv('WOOCOMMERCE_CONSUMER_SECRET'),
            version="wc/v3"
        )
        
        # Wolvox veritabanı bağlantısı
        fb_client_path = os.getenv('FIREBIRD_CLIENT_PATH')
        if fb_client_path and os.path.exists(fb_client_path):
            fdb.load_api(fb_client_path)
        
        self.conn = fdb.connect(
            database=os.getenv('WOLVOX_DB_PATH'),
            user=os.getenv('WOLVOX_DB_USER'),
            password=os.getenv('WOLVOX_DB_PASSWORD')
        )
        self.cursor = self.conn.cursor()
        
        # Döviz kurlarını güncelle
        self.update_exchange_rates()

    def update_exchange_rates(self):
        """Döviz kurlarını günceller"""
        try:
            api_key = os.getenv('EXCHANGE_RATES_API_KEY')
            if not api_key:
                logger.warning("Döviz kuru API anahtarı bulunamadı")
                return

            response = requests.get(f'https://api.exchangeratesapi.io/latest?base=TRY&access_key={api_key}')
            if response.status_code == 200:
                data = response.json()
                self.exchange_rates = data['rates']
                logger.info("Döviz kurları güncellendi")
            else:
                logger.error(f"Döviz kurları güncellenemedi: {response.status_code}")
        except Exception as e:
            logger.error(f"Döviz kuru güncelleme hatası: {str(e)}")

    def get_stats(self):
        """Senkronizasyon istatistiklerini döndürür"""
        return {
            'products': self.stats['products'],
            'orders': self.stats['orders'],
            'categories': self.stats['categories'],
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'errors': self.stats['errors']
        }

    def update_stats(self, stat_type, increment=1):
        """İstatistikleri günceller"""
        if stat_type in self.stats:
            self.stats[stat_type] += increment
        self.last_sync = datetime.now()

    def convert_price(self, price, from_currency, to_currency='TRY'):
        """Fiyatı belirtilen para birimine çevirir"""
        try:
            if from_currency == to_currency:
                return price
            
            if not self.exchange_rates:
                return price
            
            if from_currency not in self.exchange_rates or to_currency not in self.exchange_rates:
                return price
            
            # TRY'den hedef para birimine çevir
            rate = self.exchange_rates[to_currency] / self.exchange_rates[from_currency]
            converted_price = price * rate
            
            return round(converted_price, 2)
        except Exception as e:
            logger.error(f"Fiyat dönüşüm hatası: {str(e)}")
            return price

    def sync_categories(self):
        """Wolvox'tan WooCommerce'e kategori senkronizasyonu"""
        try:
            # Wolvox'tan kategorileri çek
            self.cursor.execute("""
                SELECT 
                    s.GRUBU as KATEGORI,
                    s.UST_GRUBU as UST_KATEGORI
                FROM STOK s
                WHERE s.GRUBU IS NOT NULL
                GROUP BY s.GRUBU, s.UST_GRUBU
                ORDER BY s.UST_GRUBU, s.GRUBU
            """)
            categories = self.cursor.fetchall()

            # Mevcut WooCommerce kategorilerini al
            existing_categories = {cat['name']: cat['id'] for cat in self.wcapi.get("products/categories").json()}
            category_map = {}  # Kategori eşleştirme için

            for category in categories:
                cat_name = category[0].strip()
                parent_name = category[1].strip() if category[1] else None

                try:
                    # Kategori verilerini hazırla
                    category_data = {
                        'name': cat_name,
                        'slug': self.slugify_turkish(cat_name)
                    }

                    # Üst kategori varsa ve daha önce oluşturulduysa
                    if parent_name and parent_name in category_map:
                        category_data['parent'] = category_map[parent_name]

                    if cat_name in existing_categories:
                        # Kategori varsa güncelle
                        cat_id = existing_categories[cat_name]
                        self.wcapi.put(f"products/categories/{cat_id}", category_data)
                        category_map[cat_name] = cat_id
                        logger.info(f"Kategori güncellendi: {cat_name}")
                    else:
                        # Yeni kategori oluştur
                        response = self.wcapi.post("products/categories", category_data)
                        cat_id = response.json()['id']
                        category_map[cat_name] = cat_id
                        existing_categories[cat_name] = cat_id
                        logger.info(f"Yeni kategori eklendi: {cat_name}")

                except Exception as e:
                    logger.error(f"Kategori işleme hatası ({cat_name}): {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Kategori senkronizasyonunda hata: {str(e)}")

    def slugify_turkish(self, text):
        """Türkçe karakterleri destekleyen URL dostu string oluşturur"""
        text = text.replace('ı', 'i').replace('İ', 'i')
        text = text.replace('ğ', 'g').replace('Ğ', 'g')
        text = text.replace('ü', 'u').replace('Ü', 'u')
        text = text.replace('ş', 's').replace('Ş', 's')
        text = text.replace('ö', 'o').replace('Ö', 'o')
        text = text.replace('ç', 'c').replace('Ç', 'c')
        text = text.lower()
        return '-'.join(text.split())

    def sync_products(self):
        """Wolvox'tan WooCommerce'e ürün senkronizasyonu"""
        try:
            # Wolvox'tan ürünleri çek
            self.cursor.execute("""
                SELECT 
                    s.*,
                    m.MARKA_ADI,
                    COALESCE(
                        (SELECT TOP 1 RESIM FROM STOK_RESIM sr WHERE sr.BLSTKODU = s.BLKODU),
                        s.RESIM_YOLU
                    ) as URUN_RESIM
                FROM STOK s
                LEFT JOIN MARKALAR m ON m.BLKODU = s.MARKA_BLKODU
                WHERE s.AKTIF = 1 AND s.WEBDE_GORUNSUN = 1
            """)
            products = self.cursor.fetchall()

            for product in products:
                try:
                    # Stok miktarını getir
                    self.cursor.execute("""
                        SELECT 
                            COALESCE(SUM(CASE WHEN sh.TUTAR_TURU = 0 THEN sh.MIKTARI ELSE -sh.MIKTARI END), 0) as MIKTAR_KALAN
                        FROM STOK s
                        LEFT JOIN STOKHR sh ON sh.BLSTKODU = s.BLKODU
                        WHERE s.STOKKODU = ?
                        GROUP BY s.STOKKODU
                    """, (product[0],))
                    
                    stok_miktar = self.cursor.fetchone()
                    miktar = float(stok_miktar[0]) if stok_miktar else 0

                    # Fiyat bilgilerini getir
                    self.cursor.execute("""
                        SELECT 
                            sf.FIYATI,
                            sf.DOVIZ_TURU
                        FROM STOK_FIYAT sf
                        WHERE sf.BLSTKODU = ? AND sf.FIYAT_NO = 1 AND sf.ALIS_SATIS = 1
                        ORDER BY sf.FIYAT_NO
                    """, (product[12],))
                    
                    fiyat_bilgisi = self.cursor.fetchone()
                    fiyat = float(fiyat_bilgisi[0]) if fiyat_bilgisi else 0
                    
                    # Ürün özelliklerini getir
                    self.cursor.execute("""
                        SELECT 
                            o.OZELLIK_ADI,
                            od.DEGER
                        FROM STOK_OZELLIK_DEGER od
                        JOIN STOK_OZELLIK o ON o.BLKODU = od.BLOZKODU
                        WHERE od.BLSTKODU = ?
                    """, (product[12],))
                    
                    ozellikler = self.cursor.fetchall()
                    
                    # Ürün varyantlarını getir
                    self.cursor.execute("""
                        SELECT 
                            v.VARYANT_ADI,
                            v.BARKOD,
                            v.STOK_MIKTARI,
                            v.FIYAT
                        FROM STOK_VARYANT v
                        WHERE v.BLSTKODU = ?
                    """, (product[12],))
                    
                    varyantlar = self.cursor.fetchall()

                    # WooCommerce'de ürün güncelleme/ekleme işlemi
                    product_data = {
                        'name': product[1].strip(),
                        'regular_price': str(fiyat),
                        'stock_quantity': int(miktar),
                        'manage_stock': True,
                        'description': product[7].strip() if product[7] else '',
                        'short_description': f"Marka: {product[5].strip() if product[5] else ''}\nModel: {product[6].strip() if product[6] else ''}",
                        'categories': [{'name': product[9].strip()}] if product[9] else [],
                        'attributes': [
                            {
                                'name': ozellik[0].strip(),
                                'visible': True,
                                'variation': False,
                                'options': [ozellik[1].strip()]
                            } for ozellik in ozellikler
                        ],
                        'meta_data': [
                            {'key': 'marka', 'value': product[-2] if product[-2] else ''},
                            {'key': 'barkod', 'value': product[2] if product[2] else ''},
                            {'key': 'kod', 'value': product[0].strip()}
                        ]
                    }

                    # Ürün resmi varsa ekle
                    if product[-1]:
                        product_data['images'] = [{'src': product[-1]}]

                    # Varyantlar varsa ekle
                    if varyantlar:
                        product_data['type'] = 'variable'
                        product_data['variations'] = []
                        for varyant in varyantlar:
                            variation_data = {
                                'regular_price': str(varyant[3]),
                                'stock_quantity': int(varyant[2]),
                                'attributes': [
                                    {
                                        'name': varyant[0].strip(),
                                        'option': varyant[0].strip()
                                    }
                                ]
                            }
                            product_data['variations'].append(variation_data)

                    # Ürün WooCommerce'de var mı kontrol et
                    woo_products = self.wcapi.get(f"products?sku={product[0].strip()}").json()
                    
                    if woo_products:
                        # Ürün varsa güncelle
                        self.wcapi.put(f"products/{woo_products[0]['id']}", product_data)
                        logger.info(f"Ürün güncellendi: {product[1].strip()}")
                    else:
                        # Ürün yoksa yeni ekle
                        product_data['sku'] = product[0].strip()
                        self.wcapi.post("products", product_data)
                        logger.info(f"Yeni ürün eklendi: {product[1].strip()}")

                except Exception as e:
                    logger.error(f"Ürün işleme hatası ({product[0].strip()}): {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Ürün senkronizasyonunda hata: {str(e)}")

    def sync_orders(self):
        """WooCommerce'den Wolvox'a sipariş senkronizasyonu"""
        try:
            # Son 24 saatteki siparişleri al
            orders = self.wcapi.get("orders?status=processing").json()

            for order in orders:
                # Siparişin Wolvox'ta olup olmadığını kontrol et
                self.cursor.execute("SELECT * FROM SIPARIS WHERE SIPARIS_NO = ?", (str(order['id']),))
                existing_order = self.cursor.fetchone()

                if not existing_order:
                    try:
                        # Transaction başlat
                        self.conn.begin()
                        
                        # Sipariş başlığını ekle
                        order_date = datetime.fromisoformat(order['date_created'].replace('Z', '+00:00'))
                        self.cursor.execute("""
                            INSERT INTO SIPARIS (SIPARIS_NO, SIPARIS_TARIHI, MUSTERI_ADI, TOPLAM_TUTAR)
                            VALUES (?, ?, ?, ?)
                        """, (str(order['id']), order_date, order['billing']['first_name'] + ' ' + order['billing']['last_name'], float(order['total'])))

                        # Sipariş detaylarını ekle
                        for item in order['line_items']:
                            self.cursor.execute("""
                                INSERT INTO SIPARIS_DETAY (SIPARIS_ID, STOK_KODU, MIKTAR, BIRIM_FIYAT)
                                VALUES (?, ?, ?, ?)
                            """, (str(order['id']), item['sku'], float(item['quantity']), float(item['price'])))

                        # Transaction'ı onayla
                        self.conn.commit()
                        logger.info(f"Yeni sipariş eklendi: {order['id']}")
                        
                    except Exception as e:
                        # Hata durumunda rollback
                        self.conn.rollback()
                        logger.error(f"Sipariş ekleme hatası ({order['id']}): {str(e)}")
                        continue

        except Exception as e:
            logger.error(f"Sipariş senkronizasyonunda hata: {str(e)}")

    def close_connections(self):
        """Veritabanı bağlantılarını kapat"""
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

def main():
    sync = WolvoxWooCommerceSync()

    # Periyodik senkronizasyon görevlerini planla
    schedule.every(30).minutes.do(sync.sync_products)  # Her 30 dakikada bir ürün senkronizasyonu
    schedule.every(15).minutes.do(sync.sync_orders)    # Her 15 dakikada bir sipariş senkronizasyonu
    schedule.every(60).minutes.do(sync.sync_categories)  # Her 60 dakikada bir kategori senkronizasyonu

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Program sonlandırılıyor...")
        sync.close_connections()

if __name__ == "__main__":
    main()
