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
        
        # Örnek bir grup ve alt gruplarını al
        cur.execute("""
            SELECT FIRST 1 g.GRUPKODU, g.GRUPADI, 
                   ga.ARAGRUPKODU, ga.ARAGRUPADI,
                   galt.ALTGRUPKODU, galt.ALTGRUPADI
            FROM GRUP g
            LEFT JOIN GRUP_ARA ga ON ga.GRUPKODU = g.GRUPKODU AND ga.DURUM = 'A'
            LEFT JOIN GRUP_ALT galt ON galt.GRUPKODU = g.GRUPKODU 
                AND galt.ARAGRUPKODU = ga.ARAGRUPKODU AND galt.DURUM = 'A'
            WHERE g.DURUM = 'A'
        """)
        
        print("\nÖrnek Kategori Yapısı:")
        print("-" * 50)
        for row in cur.fetchall():
            print(f"Grup: {row[0]} - {row[1]}")
            if row[2]:
                print(f"  ├─ Ara Grup: {row[2]} - {row[3]}")
            if row[4]:
                print(f"     ├─ Alt Grup: {row[4]} - {row[5]}")
        
        con.close()
        
    except Exception as e:
        print(f"Hata: {str(e)}")

if __name__ == "__main__":
    main()
