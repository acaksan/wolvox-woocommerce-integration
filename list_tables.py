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
        
        # Tablo listesini al
        cur.execute("""
            SELECT RDB$RELATION_NAME 
            FROM RDB$RELATIONS 
            WHERE RDB$SYSTEM_FLAG = 0 
            AND RDB$RELATION_TYPE = 0 
            ORDER BY RDB$RELATION_NAME
        """)
        
        print("Veritabanındaki tablolar:")
        print("-" * 30)
        for table in cur.fetchall():
            print(table[0].strip())
        
        con.close()
        
    except Exception as e:
        print(f"Hata: {str(e)}")

if __name__ == "__main__":
    main()
