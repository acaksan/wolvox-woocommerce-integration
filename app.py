from flask import Flask, render_template, jsonify, request, flash, redirect, url_for
from flask_socketio import SocketIO
import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
from decimal import Decimal
import fdb
from config import DB_CONFIG, APP_CONFIG, LOG_CONFIG

from woocommerce.wc_client import WooCommerceClient
from woocommerce.sync_manager import WooCommerceSyncManager
from wolvox.product_reader import ProductReader

# Flask uygulamasını oluştur
app = Flask(__name__)
app.config.from_object(APP_CONFIG)

# Loglama ayarları
logging.basicConfig(
    filename=LOG_CONFIG['filename'],
    level=getattr(logging, LOG_CONFIG['level']),
    format=LOG_CONFIG['format']
)
logger = logging.getLogger(__name__)

# Konsol handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# Dosya handler
os.makedirs('logs', exist_ok=True)
file_handler = RotatingFileHandler('logs/app.log', maxBytes=10485760, backupCount=5)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

class Config:
    """Uygulama konfigürasyonu"""
    # Varsayılan değerler
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'E:\\AKINSOFT\\Wolvox8\\Database_FB\\100\\2024\\WOLVOX.FDB')
    DATABASE_USER = os.getenv('DATABASE_USER', 'SYSDBA')
    DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD', 'masterkey')
    
    # WooCommerce ayarları
    WC_URL = os.getenv('WC_URL', 'https://lastik-al.com')
    WC_CONSUMER_KEY = os.getenv('WC_CONSUMER_KEY', 'ck_14ca8aab6f546bb34e5fd7f27ab0f77c6728c066')
    WC_CONSUMER_SECRET = os.getenv('WC_CONSUMER_SECRET', 'cs_62e4007a181e06ed919fa469baaf6e3fac8ea45f')

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = 'secret_key_here'  # Secret key ekleyin
socketio = SocketIO(app)

# WooCommerce ayarları
app.config.update(
    WC_URL=os.getenv('WC_URL', 'https://lastik-al.com'),
    WC_CONSUMER_KEY=os.getenv('WC_CONSUMER_KEY', 'ck_14ca8aab6f546bb34e5fd7f27ab0f77c6728c066'),
    WC_CONSUMER_SECRET=os.getenv('WC_CONSUMER_SECRET', 'cs_62e4007a181e06ed919fa469baaf6e3fac8ea45f')
)

def get_db_connection():
    """Veritabanı bağlantısı oluştur"""
    try:
        # DSN formatında bağlantı
        dsn = f"{DB_CONFIG['host']}:{DB_CONFIG['database']}"
        conn = fdb.connect(
            dsn=dsn,
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            charset=DB_CONFIG['charset']
        )
        return conn
    except Exception as e:
        logger.error(f"Veritabanı bağlantı hatası: {str(e)}")
        raise Exception(f"Veritabanı bağlantı hatası: {str(e)}")

def decimal_default(obj):
    """JSON serializer için Decimal tipini destekler"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

@app.route('/')
def index():
    """Ana sayfa"""
    return render_template('index.html')

@app.route('/products')
def products():
    """Ürün listesi sayfası"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Arama parametresi
        search = request.args.get('q', '')
        
        # Ürünleri getir
        if search:
            cursor.execute("""
                SELECT 
                    s.BLKODU,
                    s.STOKKODU,
                    s.STOK_ADI,
                    s.BARKODU,
                    s.BIRIMI,
                    s.KDV_ORANI,
                    s.WEBDE_GORUNSUN,
                    s.AKTIF,
                    s.SATIS_FIYATI1,
                    s.SATIS_FIYATI2
                FROM STOK s
                WHERE s.AKTIF = 1
                AND (
                    UPPER(s.STOK_ADI) LIKE UPPER(?)
                    OR UPPER(s.STOKKODU) LIKE UPPER(?)
                    OR UPPER(s.BARKODU) LIKE UPPER(?)
                )
                ORDER BY s.STOK_ADI
                ROWS 50
            """, (f'%{search}%', f'%{search}%', f'%{search}%'))
        else:
            cursor.execute("""
                SELECT 
                    s.BLKODU,
                    s.STOKKODU,
                    s.STOK_ADI,
                    s.BARKODU,
                    s.BIRIMI,
                    s.KDV_ORANI,
                    s.WEBDE_GORUNSUN,
                    s.AKTIF,
                    s.SATIS_FIYATI1,
                    s.SATIS_FIYATI2
                FROM STOK s
                WHERE s.AKTIF = 1
                ORDER BY s.STOK_ADI
                ROWS 50
            """)
        
        products = []
        for row in cursor.fetchall():
            products.append({
                'blkodu': row[0],
                'stok_kodu': row[1],
                'stok_adi': row[2],
                'barkod': row[3],
                'birim': row[4],
                'kdv_orani': row[5],
                'webde_gorunsun': row[6],
                'aktif': row[7],
                'satis_fiyati1': float(row[8] or 0),
                'satis_fiyati2': float(row[9] or 0)
            })
        
        cursor.close()
        conn.close()
        
        return render_template('products.html', products=products)
        
    except Exception as e:
        logger.error(f"Ürün listesi getirilirken hata: {str(e)}")
        return f"Hata oluştu: {str(e)}", 500

@app.route('/api/test-connection')
def test_connection_api():
    """Veritabanı ve WooCommerce bağlantılarını test eder"""
    try:
        # Veritabanı bağlantı testi
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM RDB$DATABASE")
        cursor.fetchone()
        cursor.close()
        conn.close()
        db_status = "success"
    except Exception as e:
        db_status = str(e)
    
    return jsonify({
        'database': {
            'status': 'success' if db_status == 'success' else 'error',
            'message': 'Bağlantı başarılı' if db_status == 'success' else f'Hata: {db_status}'
        }
    })

def get_product_stock(stok_kodu):
    """Ürünün depo bazlı stok miktarlarını getirir"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Toplam stok miktarı
        cursor.execute("""
            SELECT 
                COALESCE(SUM(MIKTAR), 0) as STOK_MIKTARI
            FROM STOK_HAREKETLERI
            WHERE STOK_KODU = ?
        """, (stok_kodu,))
        
        total_stock = cursor.fetchone()[0]
        
        # Depo bazlı stok miktarları
        cursor.execute("""
            SELECT 
                d.DEPO_ADI,
                COALESCE(SUM(sh.MIKTAR), 0) as MIKTAR
            FROM DEPOLAR d
            LEFT JOIN STOK_HAREKETLERI sh ON sh.DEPO = d.DEPO_KODU AND sh.STOK_KODU = ?
            GROUP BY d.DEPO_ADI, d.DEPO_KODU
            HAVING COALESCE(SUM(sh.MIKTAR), 0) <> 0
            ORDER BY d.DEPO_ADI
        """, (stok_kodu,))
        
        depot_stocks = []
        for row in cursor.fetchall():
            depot_stocks.append(f"{row[0].strip()}: {float(row[1])}")
        
        return {
            'total': float(total_stock) if total_stock else 0,
            'depots': depot_stocks
        }
        
    except Exception as e:
        logger.error(f"Stok miktarı alınırken hata: {str(e)}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_product_prices(stok_kodu):
    """Ürünün satış fiyatlarını getirir"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                SATIS_FIYATI1,
                SATIS_FIYATI2,
                SATIS_FIYATI3,
                SATIS_FIYATI4,
                SATIS_FIYATI5
            FROM STOK
            WHERE STOK_KODU = ?
        """, (stok_kodu,))
        
        row = cursor.fetchone()
        if row:
            return {
                'satis_fiyati1': float(row[0]) if row[0] else 0,
                'satis_fiyati2': float(row[1]) if row[1] else 0,
                'satis_fiyati3': float(row[2]) if row[2] else 0,
                'satis_fiyati4': float(row[3]) if row[3] else 0,
                'satis_fiyati5': float(row[4]) if row[4] else 0
            }
        return None
        
    except Exception as e:
        logger.error(f"Fiyat bilgisi alınırken hata: {str(e)}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/products')
def api_products():
    """Ürün listesi API endpoint'i"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # URL parametreleri
        search = request.args.get('search', '')
        category = request.args.get('category', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Offset hesapla
        offset = (page - 1) * per_page
        
        # Ürünleri getir
        query_params = []
        where_clauses = ["s.AKTIF = 1", "s.WEBDE_GORUNSUN = 1"]  # Sadece aktif ve webde görünen ürünler
        
        if search:
            where_clauses.append("(UPPER(s.STOK_ADI) LIKE UPPER(?) OR UPPER(s.STOKKODU) LIKE UPPER(?))")
            query_params.extend([f'%{search}%', f'%{search}%'])
        
        if category and category != 'all':
            where_clauses.append("UPPER(s.GRUBU) = UPPER(?)")
            query_params.append(category)
        
        where_clause = " AND ".join(where_clauses)
        
        # Toplam kayıt sayısını al
        cursor.execute(f"""
            SELECT COUNT(*)
            FROM STOK s
            WHERE {where_clause}
        """, query_params)
        
        total_records = cursor.fetchone()[0]
        total_pages = (total_records + per_page - 1) // per_page
        
        # Ürünleri getir
        cursor.execute(f"""
            SELECT FIRST {per_page} SKIP {offset}
                s.BLKODU,
                s.STOKKODU,
                s.STOK_ADI,
                s.BARKOD,
                s.STOK_BIRIMI,
                s.GRUP_KODU,
                s.ARA_GRUP_KODU,
                s.ALT_GRUP_KODU,
                s.KDV_ORANI,
                s.WEBDE_GORUNSUN,
                s.AKTIF,
                s.RESIM,
                s.ACIKLAMA,
                g.GRUP_ADI as ANA_GRUP,
                ga.GRUP_ADI as ARA_GRUP,
                galt.GRUP_ADI as ALT_GRUP
            FROM STOKLAR s
            LEFT JOIN GRUP g ON s.GRUP_KODU = g.BLKODU
            LEFT JOIN GRUP_ARA ga ON s.ARA_GRUP_KODU = ga.BLKODU
            LEFT JOIN GRUP_ALT galt ON s.ALT_GRUP_KODU = galt.BLKODU
            WHERE {where_clause}
            GROUP BY 
                s.BLKODU,
                s.STOKKODU,
                s.STOK_ADI,
                s.BARKOD,
                s.STOK_BIRIMI,
                s.GRUP_KODU,
                s.ARA_GRUP_KODU,
                s.ALT_GRUP_KODU,
                s.KDV_ORANI,
                s.WEBDE_GORUNSUN,
                s.AKTIF,
                s.RESIM,
                s.ACIKLAMA,
                g.GRUP_ADI,
                ga.GRUP_ADI,
                galt.GRUP_ADI
            ORDER BY s.STOK_ADI
        """, query_params)
        
        products = []
        for row in cursor.fetchall():
            products.append({
                'BLKODU': row[0],
                'STOKKODU': row[1].strip() if row[1] else '',
                'STOK_ADI': row[2].strip() if row[2] else '',
                'BARKODU': row[3].strip() if row[3] else '',
                'BIRIMI': row[4].strip() if row[4] else '',
                'KDV_ORANI': float(row[8]) if row[8] else 0,
                'WEBDE_GORUNSUN': bool(row[9]),
                'AKTIF': bool(row[10]),
                'GRUBU': row[11].strip() if row[11] else '',
                'MARKASI': row[12].strip() if row[12] else '',
                'SATIS_FIYATI': float(row[13]) if row[13] else 0
            })
        
        # Kategorileri getir (sadece aktif ve webde görünen ürünlerin kategorileri)
        cursor.execute("""
            SELECT DISTINCT GRUBU
            FROM STOK s
            WHERE s.AKTIF = 1 
            AND s.WEBDE_GORUNSUN = 1 
            AND s.GRUBU IS NOT NULL 
            AND TRIM(s.GRUBU) <> ''
            ORDER BY GRUBU
        """)
        
        categories = ['all']  # 'Tümü' seçeneği
        categories.extend([row[0].strip() for row in cursor.fetchall()])
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'products': products,
            'categories': categories,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages,
                'total_records': total_records
            }
        })
        
    except Exception as e:
        logger.error(f"API ürün listesi getirilirken hata: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<stokkodu>')
def get_product_detail(stokkodu):
    """Stok detayını döndürür"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Ana ürün bilgilerini al
        cursor.execute("""
            SELECT 
                s.BLKODU,
                s.STOKKODU,
                s.STOK_ADI,
                s.BARKOD,
                s.STOK_BIRIMI,
                s.GRUP_KODU,
                s.ARA_GRUP_KODU,
                s.ALT_GRUP_KODU,
                s.KDV_ORANI,
                s.WEBDE_GORUNSUN,
                s.AKTIF,
                s.RESIM,
                s.ACIKLAMA,
                g.GRUP_ADI as ANA_GRUP,
                ga.GRUP_ADI as ARA_GRUP,
                galt.GRUP_ADI as ALT_GRUP
            FROM STOKLAR s
            LEFT JOIN GRUP g ON s.GRUP_KODU = g.BLKODU
            LEFT JOIN GRUP_ARA ga ON s.ARA_GRUP_KODU = ga.BLKODU
            LEFT JOIN GRUP_ALT galt ON s.ALT_GRUP_KODU = galt.BLKODU
            WHERE s.STOK_KODU = ? AND s.AKTIF = 1 AND s.WEBDE_GORUNSUN = 1
        """, (stokkodu,))
        
        product = dict(zip([column[0] for column in cursor.description], cursor.fetchone()))
        
        # Stok bilgilerini al
        stock_info = get_product_stock(product['STOK_KODU'])
        product['STOK_MIKTARI'] = stock_info['total']
        product['DEPO_STOKLARI'] = ', '.join(stock_info['depots'])
        
        # Fiyat bilgilerini al
        price_info = get_product_prices(product['STOK_KODU'])
        product['SATIS_FIYATI1'] = price_info['satis_fiyati1']
        product['SATIS_FIYATI2'] = price_info['satis_fiyati2']
        
        # Ürün özelliklerini al
        cursor.execute("""
            SELECT 
                o.OZELLIK_ADI,
                od.DEGER
            FROM STOK_OZELLIK_DEGER od
            JOIN STOK_OZELLIK o ON o.BLKODU = od.BLOZKODU
            WHERE od.STOK_KODU = ?
        """, (stokkodu,))
        
        product['ozellikler'] = [dict(zip(['name', 'value'], row)) for row in cursor.fetchall()]
        
        # Stok hareketlerini al
        cursor.execute("""
            SELECT FIRST 100
                sh.TARIH,
                sh.TUTAR_TURU,
                sh.MIKTAR,
                sh.ACIKLAMA,
                sh.BELGE_NO
            FROM STOK_HAREKETLERI sh
            WHERE sh.STOK_KODU = ?
            ORDER BY sh.TARIH DESC
        """, (stokkodu,))
        
        product['hareketler'] = [dict(zip(['tarih', 'tur', 'miktar', 'aciklama', 'belge_no'], row)) 
                                for row in cursor.fetchall()]
        
        # Resimleri al
        cursor.execute("""
            SELECT 
                s.RESIM,
                s.RESIM2,
                s.RESIM3,
                s.RESIM4,
                s.RESIM5
            FROM STOKLAR s
            WHERE s.STOK_KODU = ? AND s.AKTIF = 1 AND s.WEBDE_GORUNSUN = 1
        """, (stokkodu,))
        
        row = cursor.fetchone()
        product['resimler'] = [img.strip() for img in row if img and img.strip()]
        
        cursor.close()
        conn.close()
        
        return jsonify(product)
        
    except Exception as e:
        logger.error(f"Ürün detayı alınırken hata: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def get_stats():
    if not sync_instance:
        return jsonify({'error': 'Senkronizasyon başlatılmamış'})
    
    try:
        stats = sync_instance.get_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/sync/start', methods=['POST'])
def start_sync():
    global sync_instance, sync_thread, is_syncing
    
    if is_syncing:
        return jsonify({'status': 'error', 'message': 'Senkronizasyon zaten çalışıyor'})
    
    try:
        sync_instance = WolvoxWooCommerceSync()
        
        # Zamanlanmış görevleri ayarla
        schedule.clear()
        schedule.every(30).minutes.do(sync_instance.sync_products)
        schedule.every(15).minutes.do(sync_instance.sync_orders)
        schedule.every(60).minutes.do(sync_instance.sync_categories)
        
        # Hemen ilk senkronizasyonu başlat
        sync_instance.sync_categories()
        sync_instance.sync_products()
        sync_instance.sync_orders()
        
        # Arka plan thread'ini başlat
        if not sync_thread:
            sync_thread = socketio.start_background_task(background_task)
        
        is_syncing = True
        return jsonify({'status': 'success', 'message': 'Senkronizasyon başlatıldı'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/sync/stop', methods=['POST'])
def stop_sync():
    global sync_instance, is_syncing
    
    if not is_syncing:
        return jsonify({'status': 'error', 'message': 'Senkronizasyon zaten durdurulmuş'})
    
    try:
        schedule.clear()
        if sync_instance:
            sync_instance.close_connections()
            sync_instance = None
        is_syncing = False
        return jsonify({'status': 'success', 'message': 'Senkronizasyon durduruldu'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/sync/status')
def get_sync_status():
    """Senkronizasyon durumu API endpoint'i"""
    try:
        status = {
            'running': sync_thread is not None and sync_thread.is_alive(),
            'last_sync': None,  # TODO: Son senkronizasyon bilgisi
            'stats': None,      # TODO: Senkronizasyon istatistikleri
            'logs': []          # TODO: Senkronizasyon logları
        }
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/sync-status')
def sync_status():
    """Senkronizasyon durumu sayfası"""
    return render_template('sync_status.html')

@app.route('/sync-status-page')
def sync_status_page():
    """Senkronizasyon durumu sayfası"""
    return render_template('sync_status.html', 
                         last_sync=None,  # TODO: Son senkronizasyon bilgisi
                         stats=None,      # TODO: Senkronizasyon istatistikleri
                         logs=[]          # TODO: Senkronizasyon logları
                         )

@app.route('/api/logs')
def get_logs():
    try:
        with open('logs/sync.log', 'r', encoding='utf-8') as f:
            logs = f.readlines()[-100:]  # Son 100 log
        return jsonify({'logs': logs})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/test')
def test_product():
    """Test için referans ürünün bilgilerini getir"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Ürün bilgilerini al
        cursor.execute("""
            SELECT 
                s.BLKODU,
                s.STOKKODU,
                s.STOK_ADI,
                s.BARKODU,
                s.KDV_ORANI,
                s.BIRIMI,
                s.BLKODU
            FROM STOK s
            WHERE s.STOKKODU = 'PET-100-70-13-175-4000'
        """)
        
        row = cursor.fetchone()
        if not row:
            return jsonify({'error': 'Ürün bulunamadı'}), 404
            
        product = {
            'stok_kodu': row[1],
            'stok_adi': row[2],
            'barkod': row[3],
            'kdv_orani': row[4],
            'birim': row[5],
            'blkodu': row[6]
        }
        
        # Satış fiyatını al (Satış Fiyatı 1)
        cursor.execute("""
            SELECT f.FIYATI
            FROM STOK_FIYAT f
            WHERE f.BLSTKODU = ?
            AND f.ALIS_SATIS = 2  -- Satış fiyatı
            AND f.FIYAT_NO = 1    -- Fiyat 1
        """, (product['blkodu'],))
        
        row = cursor.fetchone()
        product['satis_fiyati'] = float(row[0]) if row and row[0] else 0
        
        # Depo bazlı stok miktarlarını al
        cursor.execute("""
            SELECT 
                d.DEPO_ADI,
                (SELECT -COALESCE(SUM(
                    CASE 
                        WHEN sh.TUTAR_TURU = 0 THEN sh.MIKTARI 
                        ELSE -sh.MIKTARI 
                    END), 0)
                FROM STOKHR sh 
                WHERE sh.DEPO_ADI = d.DEPO_ADI 
                AND sh.BLSTKODU = ?
                AND sh.SILINDI = 0) as KALAN_MIKTAR
            FROM DEPO d
            WHERE d.AKTIF = 1
            ORDER BY d.DEPO_ADI
        """, (product['blkodu'],))
        
        stok_miktarlari = {}
        for row in cursor.fetchall():
            if row[1] != 0:  # Sadece stok miktarı 0'dan farklı olanları ekle
                stok_miktarlari[row[0].strip()] = float(row[1])
        
        product['stok_miktarlari'] = stok_miktarlari
        product['toplam_stok'] = sum(stok_miktarlari.values())
        
        cursor.close()
        conn.close()
        
        # HTML sayfasını oluştur
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Ürün Detayları</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .container { max-width: 800px; margin: 0 auto; }
                .card { 
                    border: 1px solid #ddd; 
                    border-radius: 8px; 
                    padding: 20px;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .title { 
                    color: #333;
                    border-bottom: 2px solid #eee;
                    padding-bottom: 10px;
                    margin-bottom: 20px;
                }
                .info-row {
                    display: flex;
                    margin-bottom: 10px;
                }
                .label {
                    font-weight: bold;
                    width: 150px;
                    color: #666;
                }
                .value {
                    flex: 1;
                }
                .stock-table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 10px;
                }
                .stock-table th, .stock-table td {
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }
                .stock-table th {
                    background-color: #f5f5f5;
                }
                .total {
                    font-weight: bold;
                    color: #2196F3;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="card">
                    <h2 class="title">Ürün Bilgileri</h2>
                    <div class="info-row">
                        <div class="label">Stok Kodu:</div>
                        <div class="value">{stok_kodu}</div>
                    </div>
                    <div class="info-row">
                        <div class="label">Stok Adı:</div>
                        <div class="value">{stok_adi}</div>
                    </div>
                    <div class="info-row">
                        <div class="label">Barkod:</div>
                        <div class="value">{barkod}</div>
                    </div>
                    <div class="info-row">
                        <div class="label">KDV Oranı:</div>
                        <div class="value">%{kdv_orani}</div>
                    </div>
                    <div class="info-row">
                        <div class="label">Birim:</div>
                        <div class="value">{birim}</div>
                    </div>
                    <div class="info-row">
                        <div class="label">Satış Fiyatı:</div>
                        <div class="value">{satis_fiyati:.2f} TL</div>
                    </div>
                </div>
                
                <div class="card">
                    <h2 class="title">Depo Bazlı Stok Miktarları</h2>
                    <table class="stock-table">
                        <tr>
                            <th>Depo Adı</th>
                            <th>Stok Miktarı</th>
                        </tr>
                        {stok_satirlari}
                        <tr class="total">
                            <td>Toplam Stok</td>
                            <td>{toplam_stok}</td>
                        </tr>
                    </table>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Stok miktarları tablosunu oluştur
        stok_satirlari = ""
        for depo, miktar in stok_miktarlari.items():
            stok_satirlari += f"<tr><td>{depo}</td><td>{miktar}</td></tr>"
        
        # HTML şablonunu doldur
        html = html.format(
            stok_kodu=product['stok_kodu'],
            stok_adi=product['stok_adi'],
            barkod=product['barkod'],
            kdv_orani=product['kdv_orani'],
            birim=product['birim'],
            satis_fiyati=product['satis_fiyati'],
            stok_satirlari=stok_satirlari,
            toplam_stok=product['toplam_stok']
        )
        
        return html
        
    except Exception as e:
        logger.error(f"Test sırasında hata: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/stock-movements')
def stock_movements():
    """Stok hareketleri sayfası"""
    return "Stok hareketleri sayfası yapım aşamasında"

@app.route('/price-lists')
def price_lists():
    """Fiyat listeleri sayfası"""
    return "Fiyat listeleri sayfası yapım aşamasında"

@app.route('/product/<int:blkodu>')
def product_detail(blkodu):
    """Ürün detay sayfası"""
    return f"Ürün detay sayfası yapım aşamasında (BLKODU: {blkodu})"

@app.route('/settings')
def settings():
    """Ayarlar sayfası"""
    return render_template('settings.html')

@app.route('/product-groups')
def product_groups():
    """Ürün grupları sayfası"""
    return render_template('product_groups.html')

@app.route('/settings/test-connection', methods=['POST'])
def test_connection():
    """Veritabanı bağlantısını test et"""
    try:
        conn = get_db_connection()
        if conn:
            flash('Veritabanı bağlantısı başarılı!', 'success')
            conn.close()
        else:
            flash('Veritabanı bağlantısı başarısız!', 'error')
    except Exception as e:
        logger.error(f"Veritabanı bağlantı hatası: {str(e)}")
        flash(f'Veritabanı bağlantı hatası: {str(e)}', 'error')
    
    return redirect(url_for('settings'))

@app.route('/settings/test-wc-connection', methods=['POST'])
def test_wc_connection():
    """WooCommerce bağlantısını test et"""
    try:
        wc_client = get_wc_client()
        
        sync_manager = WooCommerceSyncManager(wc_client, get_db_connection())
        success, message = sync_manager.sync_product('PET-100-70-13-175-4000')
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"WooCommerce bağlantı hatası: {str(e)}")
        flash(f'WooCommerce bağlantı hatası: {str(e)}', 'error')
    
    return redirect(url_for('settings'))

# Lastik özellikleri endpoint'leri
@app.route('/api/tire-specs/<stok_kodu>')
def get_tire_specs(stok_kodu):
    """Lastik özelliklerini getir"""
    try:
        conn = get_db_connection()
        db = TireSpecsDB(conn)
        
        specs = db.get_tire_specs(stok_kodu)
        if not specs:
            return jsonify({'error': 'Lastik özellikleri bulunamadı'}), 404
            
        return jsonify({
            'stok_kodu': specs.stok_kodu,
            'full_specs': specs.get_full_specs(),
            'size': {
                'width': specs.size.width,
                'aspect_ratio': specs.size.aspect_ratio,
                'construction': specs.size.construction,
                'diameter': specs.size.diameter,
                'full_size': specs.get_full_size()
            },
            'season': {
                'name': specs.season.name,
                'code': specs.season.code,
                'description': specs.season.description
            },
            'speed_rating': {
                'code': specs.speed_rating.code,
                'speed': specs.speed_rating.speed,
                'description': specs.speed_rating.description
            },
            'load_index': {
                'code': specs.load_index.code,
                'weight': specs.load_index.weight,
                'description': specs.load_index.description
            }
        })
        
    except Exception as e:
        logger.error(f"Lastik özellikleri getirilirken hata: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/tire-specs')
def tire_specs_page():
    """Lastik özellikleri sayfası"""
    return render_template('tire_specs.html')

# WooCommerce API endpoint'leri
@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Dashboard istatistiklerini getir"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Toplam ürün sayısı
        cursor.execute("SELECT COUNT(*) FROM STOKLAR WHERE WEBDE_GORUNSUN = 1")
        total_products = cursor.fetchone()[0]
        
        # WooCommerce'de aktif ürün sayısı
        cursor.execute("""
            SELECT COUNT(*) FROM STOKLAR s
            WHERE s.WEBDE_GORUNSUN = 1
            AND EXISTS (
                SELECT 1 FROM WOO_PRODUCTS wp
                WHERE wp.STOK_KODU = s.STOKKODU
            )
        """)
        active_products = cursor.fetchone()[0]
        
        # Bekleyen güncelleme sayısı
        cursor.execute("""
            SELECT COUNT(*) FROM STOKLAR s
            WHERE s.WEBDE_GORUNSUN = 1
            AND (
                s.GUNCELLEME_TARIHI IS NULL
                OR s.GUNCELLEME_TARIHI < s.DEGISIKLIK_TARIHI
            )
        """)
        pending_updates = cursor.fetchone()[0]
        
        # Son senkronizasyon tarihi
        cursor.execute("""
            SELECT MAX(TARIH) FROM WOO_SYNC_LOG
        """)
        last_sync = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'total_products': total_products,
            'synced_products': active_products,
            'stock_updates': pending_updates,
            'price_updates': last_sync.strftime('%Y-%m-%d %H:%M:%S') if last_sync else '-'
        })
        
    except Exception as e:
        logger.error(f"Dashboard istatistikleri hatası: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/dashboard/activities')
def get_dashboard_activities():
    """Son aktiviteleri getir"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT TOP 10
                TARIH,
                ISLEM_TIPI,
                DURUM
            FROM WOO_SYNC_LOG
            ORDER BY TARIH DESC
        """)
        
        activities = []
        for row in cursor:
            activities.append({
                'date': row[0].strftime('%Y-%m-%d %H:%M:%S') if row[0] else '-',
                'type': row[1],
                'status': row[2]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'activities': activities
        })
        
    except Exception as e:
        logger.error(f"Son aktiviteler hatası: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/dashboard/errors')
def get_dashboard_errors():
    """Son hataları getir"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT TOP 10
                TARIH,
                HATA_TIPI,
                MESAJ
            FROM WOO_ERROR_LOG
            ORDER BY TARIH DESC
        """)
        
        errors = []
        for row in cursor:
            errors.append({
                'date': row[0].strftime('%Y-%m-%d %H:%M:%S') if row[0] else '-',
                'type': row[1],
                'message': row[2]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'errors': errors
        })
        
    except Exception as e:
        logger.error(f"Hata listesi hatası: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/sync/product/<stok_kodu>', methods=['POST'])
def sync_single_product(stok_kodu):
    """Tek bir ürünü WooCommerce ile senkronize et"""
    try:
        wc_client = get_wc_client()
        
        sync_manager = WooCommerceSyncManager(wc_client, get_db_connection())
        success, message = sync_manager.sync_product(stok_kodu)
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"Ürün senkronizasyon hatası: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sync/all', methods=['POST'])
def sync_all_products():
    """Tüm ürünleri WooCommerce ile senkronize et"""
    try:
        wc_client = get_wc_client()
        
        sync_manager = WooCommerceSyncManager(wc_client, get_db_connection())
        results = sync_manager.sync_all_products()
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Toplu senkronizasyon hatası: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sync/stock/<stok_kodu>', methods=['POST'])
def sync_stock(stok_kodu):
    """Stok miktarını WooCommerce ile senkronize et"""
    try:
        wc_client = get_wc_client()
        
        sync_manager = WooCommerceSyncManager(wc_client, get_db_connection())
        success, message = sync_manager.sync_stock(stok_kodu)
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"Stok senkronizasyon hatası: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sync/price/<stok_kodu>', methods=['POST'])
def sync_price(stok_kodu):
    """Fiyatı WooCommerce ile senkronize et"""
    try:
        wc_client = get_wc_client()
        
        sync_manager = WooCommerceSyncManager(wc_client, get_db_connection())
        success, message = sync_manager.sync_price(stok_kodu)
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"Fiyat senkronizasyon hatası: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/sync/all', methods=['POST'])
def sync_all():
    """Tüm ürünleri senkronize et"""
    try:
        conn = get_db_connection()
        wc_client = get_wc_client()
        product_reader = ProductReader(conn)
        sync_manager = WooCommerceSyncManager(wc_client, product_reader)
        
        results = sync_manager.sync_all_products()
        
        success_count = len([r for r, _ in results if r])
        total_count = len(results)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'{success_count}/{total_count} ürün senkronize edildi',
            'results': [{'success': r, 'message': m} for r, m in results]
        })
        
    except Exception as e:
        logger.error(f"Senkronizasyon hatası: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Hata: {str(e)}'
        }), 500

@app.route('/sync/stock-prices', methods=['POST'])
def sync_stock_prices():
    """Stok ve fiyatları senkronize et"""
    try:
        conn = get_db_connection()
        wc_client = get_wc_client()
        product_reader = ProductReader(conn)
        sync_manager = WooCommerceSyncManager(wc_client, product_reader)
        
        results = sync_manager.sync_stock_prices()
        
        success_count = len([r for r, _ in results if r])
        total_count = len(results)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'{success_count}/{total_count} ürün güncellendi',
            'results': [{'success': r, 'message': m} for r, m in results]
        })
        
    except Exception as e:
        logger.error(f"Stok/fiyat senkronizasyon hatası: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Hata: {str(e)}'
        }), 500

@app.route('/sync/product/<stok_kodu>', methods=['POST'])
def sync_product(stok_kodu):
    """Tek bir ürünü senkronize et"""
    try:
        conn = get_db_connection()
        wc_client = get_wc_client()
        product_reader = ProductReader(conn)
        sync_manager = WooCommerceSyncManager(wc_client, product_reader)
        
        product = product_reader.get_product_by_code(stok_kodu)
        if not product:
            return jsonify({
                'success': False,
                'message': f'Ürün bulunamadı: {stok_kodu}'
            }), 404
        
        success, message = sync_manager.sync_product(product)
        
        conn.close()
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"Ürün senkronizasyon hatası: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Hata: {str(e)}'
        }), 500

@app.route('/sync/status', methods=['GET'])
def get_sync_status_info():
    """Son senkronizasyon durumunu getir"""
    try:
        # TODO: Son senkronizasyon bilgilerini veritabanından al
        return jsonify({
            'success': True,
            'last_sync': datetime.now().isoformat(),
            'total_products': 0,
            'synced_products': 0,
            'failed_products': 0
        })
        
    except Exception as e:
        logger.error(f"Durum sorgulama hatası: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Hata: {str(e)}'
        }), 500

if __name__ == '__main__':
    socketio.run(app, host='localhost', debug=False, port=8080)
