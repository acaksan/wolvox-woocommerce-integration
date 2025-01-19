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
        
        # Farklı modül değerlerini kontrol et
        print("\nMODUL değerleri:")
        print("-" * 50)
        cur.execute("""
            SELECT DISTINCT MODUL, COUNT(*) as ADET
            FROM GRUP
            GROUP BY MODUL
            ORDER BY MODUL
        """)
        for row in cur.fetchall():
            print(f"MODUL: {row[0]}, ADET: {row[1]}")
        
        con.close()
        
    except Exception as e:
        print(f"Hata: {str(e)}")

if __name__ == "__main__":
    main()
