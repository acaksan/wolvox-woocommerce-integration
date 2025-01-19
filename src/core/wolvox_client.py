import fdb
from sqlalchemy import create_engine
from config.settings import Settings
from utils.logger import setup_logger

class WolvoxClient:
    def __init__(self):
        self.settings = Settings()
        self.logger = setup_logger("wolvox_client")
        self.connection = None
        self.connect()
    
    def connect(self):
        """Veritabanı bağlantısını kur"""
        try:
            # Bağlantı bilgileri
            host = self.settings.get("wolvox.host", "localhost")
            database = self.settings.get("wolvox.database", "WOLVOX")
            user = self.settings.get("wolvox.user", "SYSDBA")
            password = self.settings.get("wolvox.password", "masterkey")
            
            # Bağlantı kur
            self.connection = fdb.connect(
                host=host,
                database=database,
                user=user,
                password=password,
                charset="UTF8"
            )
            
            self.logger.info("Wolvox veritabanı bağlantısı başarıyla kuruldu")
            
        except Exception as e:
            self.logger.error(f"Wolvox veritabanı bağlantısı kurulamadı: {str(e)}")
            raise
    
    def disconnect(self):
        """Veritabanı bağlantısını kapat"""
        if self.connection:
            try:
                self.connection.close()
                self.connection = None
            except Exception as e:
                self.logger.error(f"Bağlantı kapatılırken hata: {str(e)}")
    
    def execute_query(self, query, params=None):
        """SQL sorgusu çalıştır"""
        try:
            if not self.connection:
                self.connect()
            
            # Sorguyu çalıştır
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            return cursor
            
        except Exception as e:
            self.logger.error(f"Sorgu çalıştırılırken hata: {str(e)}")
            return None
    
    def get_products(self):
        """Ürünleri getir"""
        try:
            # Ana sorgu
            query = """
                SELECT 
                    s.STOKKODU,
                    s.STOK_ADI,
                    s.BARKODU,
                    CAST(MAX(COALESCE(sf.FIYATI, 0)) AS DECIMAL(15,2)) as LISTE_FIYATI,
                    CAST(MAX(COALESCE(sf.FIYATI, 0)) * (1 + s.KDV_ORANI / 100.0) AS DECIMAL(15,2)) as KDV_DAHIL_FIYAT,
                    s.KDV_ORANI,
                    s.MARKASI,
                    s.GRUBU,
                    s.ALT_GRUBU,
                    s.BLKODU
                FROM STOK s
                LEFT JOIN STOK_FIYAT sf ON sf.BLSTKODU = s.BLKODU AND sf.FIYAT_NO = 1
                WHERE s.AKTIF = 1 AND s.WEBDE_GORUNSUN = 1
                GROUP BY 
                    s.STOKKODU, s.STOK_ADI, s.BARKODU, s.KDV_ORANI,
                    s.MARKASI, s.GRUBU, s.ALT_GRUBU, s.BLKODU
                ORDER BY s.STOKKODU
            """
            
            # Sorguyu çalıştır
            cursor = self.execute_query(query)
            if not cursor:
                return []
            
            # Sonuçları dön
            products = []
            seen_skus = set()  # Yinelenen ürünleri kontrol etmek için
            
            for row in cursor:
                sku = row[0]
                if sku in seen_skus:
                    continue
                    
                seen_skus.add(sku)
                
                # Depo bazlı stok miktarları
                depo_query = """
                    SELECT 
                        d.DEPO_ADI,
                        CAST((SELECT -COALESCE(SUM(
                            CASE 
                                WHEN sh.TUTAR_TURU = 0 THEN sh.MIKTARI 
                                ELSE -sh.MIKTARI 
                            END), 0)
                        FROM STOKHR sh 
                        WHERE sh.DEPO_ADI = d.DEPO_ADI 
                        AND sh.BLSTKODU = ?
                        AND sh.SILINDI = 0) AS DECIMAL(15,2)) as KALAN_MIKTAR
                    FROM DEPO d
                    WHERE d.AKTIF = 1
                    ORDER BY d.DEPO_ADI
                """
                depo_cursor = self.execute_query(depo_query, (row[9],))
                depo_miktarlar = []
                toplam_stok = 0
                if depo_cursor:
                    for depo in depo_cursor:
                        if float(depo[1] or 0) != 0:
                            depo_miktarlar.append(f"{depo[0]}: {float(depo[1] or 0):.2f}")
                            toplam_stok += float(depo[1] or 0)
                
                product = {
                    "sku": sku,
                    "name": row[1],
                    "barcode": row[2],
                    "price": float(row[3] or 0),
                    "price_with_tax": float(row[4] or 0),
                    "tax_rate": float(row[5] or 0),
                    "brand": row[6],
                    "category": row[7],
                    "subcategory": row[8],
                    "stock": toplam_stok,
                    "warehouse_distribution": ", ".join(depo_miktarlar)
                }
                products.append(product)
            
            return products
            
        except Exception as e:
            self.logger.error(f"Ürünler getirilirken hata: {str(e)}")
            return []
    
    def get_product(self, product_code):
        """Belirli bir ürünü getir"""
        query = """
            SELECT
                STK.STK_KOD,
                STK.STK_ISIM,
                STK.STK_FIYAT1,
                STK.STK_FIYAT2,
                STK.STK_KDV,
                STK.STK_BIRIM,
                STK.STK_ACIKLAMA,
                STK.STK_GRUP_KOD,
                STK.STK_AKTIF,
                STK.STK_STOK
            FROM STOKLAR STK
            WHERE STK.STK_KOD = ?
        """
        
        cursor = self.execute_query(query, (product_code,))
        if cursor:
            row = cursor.fetchone()
            if row:
                return {
                    "code": row[0],
                    "name": row[1],
                    "price1": float(row[2] or 0),
                    "price2": float(row[3] or 0),
                    "vat": float(row[4] or 0),
                    "unit": row[5],
                    "description": row[6],
                    "category_code": row[7],
                    "is_active": bool(row[8]),
                    "stock": float(row[9] or 0)
                }
        return None
    
    def get_categories(self):
        """Kategorileri getir"""
        query = """
            SELECT
                GRP.GRUP_KOD,
                GRP.GRUP_ISIM,
                GRP.GRUP_UST_KOD
            FROM STOK_GRUPLARI GRP
            ORDER BY GRP.GRUP_KOD
        """
        
        cursor = self.execute_query(query)
        if cursor:
            categories = []
            for row in cursor:
                categories.append({
                    "code": row[0],
                    "name": row[1],
                    "parent_code": row[2]
                })
            return categories
        return []
    
    def get_category(self, category_code):
        """Belirli bir kategoriyi getir"""
        query = """
            SELECT
                GRP.GRUP_KOD,
                GRP.GRUP_ISIM,
                GRP.GRUP_UST_KOD
            FROM STOK_GRUPLARI GRP
            WHERE GRP.GRUP_KOD = ?
        """
        
        cursor = self.execute_query(query, (category_code,))
        if cursor:
            row = cursor.fetchone()
            if row:
                return {
                    "code": row[0],
                    "name": row[1],
                    "parent_code": row[2]
                }
        return None
    
    def get_tables(self):
        """Tablo listesini getir"""
        try:
            query = """
                SELECT RDB$RELATION_NAME
                FROM RDB$RELATIONS
                WHERE RDB$SYSTEM_FLAG = 0
                AND RDB$VIEW_BLR IS NULL
                ORDER BY RDB$RELATION_NAME
            """
            
            cursor = self.execute_query(query)
            if not cursor:
                return []
            
            tables = []
            for row in cursor:
                tables.append(row[0].strip())
            
            return tables
            
        except Exception as e:
            self.logger.error(f"Tablo listesi alınırken hata: {str(e)}")
            return []
    
    def test_connection(self):
        """Wolvox veritabanı bağlantısını test et"""
        try:
            # Test sorgusu çalıştır
            cursor = self.execute_query("SELECT 1 FROM RDB$DATABASE")
            if cursor:
                self.logger.info("Wolvox bağlantı testi başarılı")
                return True
            
        except Exception as e:
            self.logger.error(f"Wolvox bağlantı testi hatası: {str(e)}")
            return False
