import os
from dotenv import load_dotenv
from woocommerce import API
import fdb
from datetime import datetime

# .env dosyasından konfigürasyon yükleme
load_dotenv()

def connect_to_woocommerce():
    """WooCommerce API bağlantısını oluşturur"""
    return API(
        url=os.getenv('WOOCOMMERCE_URL'),
        consumer_key=os.getenv('WOOCOMMERCE_CONSUMER_KEY'),
        consumer_secret=os.getenv('WOOCOMMERCE_CONSUMER_SECRET'),
        version="wc/v3"
    )

def connect_to_wolvox():
    """Wolvox veritabanı bağlantısını oluşturur"""
    fb_client_path = os.getenv('FIREBIRD_CLIENT_PATH')
    if fb_client_path and os.path.exists(fb_client_path):
        fdb.load_api(fb_client_path)
    
    return fdb.connect(
        database=os.getenv('WOLVOX_DB_PATH'),
        user=os.getenv('WOLVOX_DB_USER'),
        password=os.getenv('WOLVOX_DB_PASSWORD')
    )

def get_product_data(cursor, stok_kodu):
    """Wolvox'tan ürün bilgilerini getirir"""
    # Ürün detaylarını getir
    cursor.execute("""
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
            s.BLKODU
        FROM STOK s
        WHERE s.STOKKODU = ?
    """, (stok_kodu,))
    
    urun = cursor.fetchone()
    if not urun:
        return None
    
    # Stok miktarını getir
    cursor.execute("""
        SELECT 
            COALESCE(SUM(CASE WHEN sh.TUTAR_TURU = 0 THEN sh.MIKTARI ELSE -sh.MIKTARI END), 0) as MIKTAR_KALAN
        FROM STOK s
        LEFT JOIN STOKHR sh ON sh.BLSTKODU = s.BLKODU
        WHERE s.STOKKODU = ?
        GROUP BY s.STOKKODU
    """, (stok_kodu,))
    
    stok_miktar = cursor.fetchone()
    miktar = float(stok_miktar[0]) if stok_miktar else 0
    
    # Fiyat bilgilerini getir
    cursor.execute("""
        SELECT 
            sf.FIYATI,
            sf.ALIS_SATIS,
            sf.FIYAT_NO,
            sf.BIRIMI,
            sf.TANIMI
        FROM STOK_FIYAT sf
        WHERE sf.BLSTKODU = ? AND sf.FIYAT_NO = 1 AND sf.ALIS_SATIS = 1
        ORDER BY sf.FIYAT_NO
    """, (urun[12],))
    
    fiyat_bilgisi = cursor.fetchone()
    fiyat = float(fiyat_bilgisi[0]) if fiyat_bilgisi else 0
    
    # KDV hesaplamaları
    kdv_orani = float(urun[4])
    fiyat_kdv_dahil = fiyat
    fiyat_kdv_haric = fiyat_kdv_dahil / (1 + (kdv_orani / 100))
    
    return {
        'stok_kodu': urun[0].strip(),
        'urun_adi': urun[1].strip(),
        'barkod': urun[2].strip() if urun[2] else '',
        'birim': urun[3].strip(),
        'kdv_orani': kdv_orani,
        'marka': urun[5].strip() if urun[5] else '',
        'model': urun[6].strip() if urun[6] else '',
        'aciklama': urun[7].strip() if urun[7] else '',
        'resim_yolu': urun[8].strip() if urun[8] else '',
        'kategori': urun[9].strip() if urun[9] else '',
        'webde_gorunsun': urun[10] == 1,
        'aktif': urun[11] == 1,
        'stok_miktar': miktar,
        'fiyat_kdv_dahil': fiyat_kdv_dahil,
        'fiyat_kdv_haric': fiyat_kdv_haric
    }

def sync_product_to_woocommerce(wcapi, product_data):
    """Ürün bilgilerini WooCommerce'e senkronize eder"""
    # WooCommerce'de SKU'ya göre ürün ara
    products = wcapi.get("products", params={"sku": product_data['stok_kodu']}).json()
    
    # Ürün verilerini hazırla
    wc_product_data = {
        "name": product_data['urun_adi'],
        "type": "simple",
        "regular_price": str(product_data['fiyat_kdv_dahil']),
        "description": product_data['aciklama'] or product_data['urun_adi'],
        "short_description": f"Marka: {product_data['marka']}\nModel: {product_data['model']}",
        "sku": product_data['stok_kodu'],
        "manage_stock": True,
        "stock_quantity": int(product_data['stok_miktar']),
        "categories": [{"name": product_data['kategori']}] if product_data['kategori'] else [],
        "status": "publish" if product_data['webde_gorunsun'] and product_data['aktif'] else "private",
        "meta_data": [
            {"key": "barkod", "value": product_data['barkod']},
            {"key": "marka", "value": product_data['marka']},
            {"key": "model", "value": product_data['model']},
            {"key": "kdv_orani", "value": str(product_data['kdv_orani'])},
            {"key": "fiyat_kdv_haric", "value": str(product_data['fiyat_kdv_haric'])}
        ]
    }
    
    if products:
        # Ürün varsa güncelle
        product_id = products[0]['id']
        response = wcapi.put(f"products/{product_id}", wc_product_data)
        print(f"Ürün güncellendi: {product_data['stok_kodu']}")
    else:
        # Ürün yoksa yeni oluştur
        response = wcapi.post("products", wc_product_data)
        print(f"Yeni ürün oluşturuldu: {product_data['stok_kodu']}")
    
    return response.json()

def main():
    try:
        # WooCommerce bağlantısı
        wcapi = connect_to_woocommerce()
        
        # Wolvox bağlantısı
        wolvox_conn = connect_to_wolvox()
        cursor = wolvox_conn.cursor()
        
        # Test için örnek ürün kodu
        ornek_stok_kodu = "PET-100-70-13-175-4000"
        
        # Ürün bilgilerini al
        product_data = get_product_data(cursor, ornek_stok_kodu)
        
        if product_data:
            # WooCommerce'e senkronize et
            result = sync_product_to_woocommerce(wcapi, product_data)
            print("Senkronizasyon başarılı!")
            print(f"WooCommerce Ürün ID: {result.get('id')}")
        else:
            print(f"Ürün bulunamadı: {ornek_stok_kodu}")
        
    except Exception as e:
        print(f"Hata: {str(e)}")
    finally:
        if 'wolvox_conn' in locals():
            wolvox_conn.close()
            print("Veritabanı bağlantısı kapatıldı.")

if __name__ == "__main__":
    main()
