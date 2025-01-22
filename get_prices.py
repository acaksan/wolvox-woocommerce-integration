from dotenv import load_dotenv
import os
import fdb

def main():
    try:
        # Veritabanı bağlantısı
        load_dotenv()
        
        # Firebird client path'ini ayarla
        fb_client_path = os.getenv('FIREBIRD_CLIENT_PATH')
        if fb_client_path and os.path.exists(fb_client_path):
            fdb.load_api(fb_client_path)
        
        # Veritabanı bağlantısı
        connection = fdb.connect(
            dsn=f"{os.getenv('WOLVOX_DB_HOST')}:{os.getenv('WOLVOX_DB_PATH')}",
            user=os.getenv('WOLVOX_DB_USER'),
            password=os.getenv('WOLVOX_DB_PASSWORD')
        )
        
        cur = connection.cursor()
        
        # Belirli ürünün stok miktarlarını al
        urun_kodu = 'PET-100-70-13-175-4000'
        depolar = ['1_AC AKSAN', '2_LASTIK VS', '3_CADDE SUBE']
        
        # Önce ürünün BLKODU'nu al
        cur.execute("SELECT BLKODU FROM STOK WHERE STOKKODU = ?", [urun_kodu])
        row = cur.fetchone()
        if not row:
            print(f"Ürün bulunamadı: {urun_kodu}")
            return
            
        blkodu = row[0]
        
        # Şimdi STOKHR tablosundan depo bazında stok miktarlarını al
        query = """
            SELECT 
                sh.DEPO_ADI,
                SUM(CASE 
                    WHEN sh.TUTAR_TURU = 0 THEN -sh.MIKTARI 
                    WHEN sh.TUTAR_TURU = 1 THEN sh.MIKTARI 
                    ELSE 0 
                END) as MIKTAR
            FROM STOKHR sh
            WHERE sh.BLSTKODU = ?
            AND sh.SILINDI = 0
            AND sh.DEPO_ADI IN (?, ?, ?)
            GROUP BY sh.DEPO_ADI
            ORDER BY sh.DEPO_ADI
        """
        
        cur.execute(query, [blkodu] + depolar)
        
        print(f"\nÜrün Kodu: {urun_kodu}")
        print("-" * 35)
        print(f"{'Depo':<20} {'Adet':>10}")
        print("-" * 35)
        
        for row in cur.fetchall():
            depo_adi = row[0].strip() if row[0] else ''
            miktar = int(row[1]) if row[1] else 0  
            print(f"{depo_adi:<20} {miktar:>10}")
            
    except Exception as e:
        print(f"Hata oluştu: {str(e)}")

if __name__ == "__main__":
    main()
