import os
import fdb
from dotenv import load_dotenv

def main():
    try:
        load_dotenv()
        
        # Firebird client path'ini ayarla
        fb_client_path = os.getenv('FIREBIRD_CLIENT_PATH')
        if fb_client_path and os.path.exists(fb_client_path):
            fdb.load_api(fb_client_path)
        
        # Veritabanı bağlantısı
        con = fdb.connect(
            dsn=f"{os.getenv('WOLVOX_DB_HOST')}:{os.getenv('WOLVOX_DB_PATH')}",
            user=os.getenv('WOLVOX_DB_USER'),
            password=os.getenv('WOLVOX_DB_PASSWORD')
        )
        
        cur = con.cursor()
        
        print("\nWeb'de Görünecek Kategoriler:")
        print("-" * 50)
        
        # Ana gruplar
        print("\nAna Gruplar:")
        cur.execute("""
            SELECT BLKODU, GRUP_ADI, WEBDE_GORUNSUN
            FROM GRUP
            WHERE WEBDE_GORUNSUN = 1
            ORDER BY GRUP_ADI
        """)
        for row in cur.fetchall():
            print(f"BLKODU: {row[0]}, GRUP_ADI: {row[1]}, WEBDE_GORUNSUN: {row[2]}")
            
            # Bu grubun ara grupları
            print("\n  Ara Gruplar:")
            cur.execute("""
                SELECT BLKODU, GRUP_ADI, WEBDE_GORUNSUN
                FROM GRUP_ARA
                WHERE UST_GRUP_ADI = ? AND WEBDE_GORUNSUN = 1
                ORDER BY GRUP_ADI
            """, (row[1].strip(),))
            
            for aragrup in cur.fetchall():
                print(f"  BLKODU: {aragrup[0]}, GRUP_ADI: {aragrup[1]}, WEBDE_GORUNSUN: {aragrup[2]}")
                
                # Bu ara grubun alt grupları
                print("\n    Alt Gruplar:")
                cur.execute("""
                    SELECT BLKODU, GRUP_ADI, WEBDE_GORUNSUN
                    FROM GRUP_ALT
                    WHERE UST_GRUP_ADI = ? AND UST_GRUP_ADI2 = ? AND WEBDE_GORUNSUN = 1
                    ORDER BY GRUP_ADI
                """, (row[1].strip(), aragrup[1].strip()))
                
                for altgrup in cur.fetchall():
                    print(f"    BLKODU: {altgrup[0]}, GRUP_ADI: {altgrup[1]}, WEBDE_GORUNSUN: {altgrup[2]}")
            
            print("-" * 30)
        
        con.close()
        
    except Exception as e:
        print(f"Hata: {str(e)}")

if __name__ == "__main__":
    main()
