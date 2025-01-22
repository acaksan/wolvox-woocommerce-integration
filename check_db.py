from dotenv import load_dotenv
import os
import fdb

def main():
    try:
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
        
        # Tabloları listele
        cur = connection.cursor()
        cur.execute("""
            SELECT RDB$RELATION_NAME 
            FROM RDB$RELATIONS 
            WHERE RDB$SYSTEM_FLAG = 0 
            ORDER BY RDB$RELATION_NAME
        """)
        
        print("\nVeritabanındaki Tablolar:")
        print("-" * 50)
        for table in cur.fetchall():
            table_name = table[0].strip()
            print(f"\nTablo: {table_name}")
            
            # Her tablonun kolonlarını listele
            cur.execute("""
                SELECT r.RDB$FIELD_NAME, f.RDB$FIELD_TYPE 
                FROM RDB$RELATION_FIELDS r
                JOIN RDB$FIELDS f ON r.RDB$FIELD_SOURCE = f.RDB$FIELD_NAME
                WHERE r.RDB$RELATION_NAME = ?
                ORDER BY r.RDB$FIELD_POSITION
            """, (table_name,))
            
            print("Kolonlar:")
            for col in cur.fetchall():
                print(f"- {col[0].strip()}")
            
    except Exception as e:
        print(f"Hata oluştu: {str(e)}")
        
if __name__ == "__main__":
    main()
