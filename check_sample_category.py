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
        
        # Örnek bir grup al
        print("\nGrup Tablosu:")
        print("-" * 50)
        cur.execute("""
            SELECT FIRST 1 BLKODU, GRUP_ADI, WEBDE_GORUNSUN
            FROM GRUP
            WHERE WEBDE_GORUNSUN = 1
        """)
        for row in cur.fetchall():
            print(f"BLKODU: {row[0]}")
            print(f"GRUP_ADI: {row[1]}")
            print(f"WEBDE_GORUNSUN: {row[2]}")
        
        con.close()
        
    except Exception as e:
        print(f"Hata: {str(e)}")

if __name__ == "__main__":
    main()
