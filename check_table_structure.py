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
        
        tables = ['GRUP', 'GRUP_ARA', 'GRUP_ALT']
        
        for table in tables:
            print(f"\nTablo: {table}")
            print("-" * 50)
            
            cur.execute(f"""
                SELECT r.RDB$FIELD_NAME, r.RDB$DESCRIPTION, f.RDB$FIELD_LENGTH, f.RDB$FIELD_TYPE
                FROM RDB$RELATION_FIELDS r
                LEFT JOIN RDB$FIELDS f ON r.RDB$FIELD_SOURCE = f.RDB$FIELD_NAME
                WHERE r.RDB$RELATION_NAME = '{table}'
                ORDER BY r.RDB$FIELD_POSITION
            """)
            
            for row in cur.fetchall():
                field_name = row[0].strip()
                field_length = row[2]
                field_type = row[3]
                print(f"{field_name}: {field_type} ({field_length})")
        
        con.close()
        
    except Exception as e:
        print(f"Hata: {str(e)}")

if __name__ == "__main__":
    main()
