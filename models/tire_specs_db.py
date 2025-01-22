from datetime import datetime
import fdb
from typing import List, Optional
from .tire_specs import TireSize, TireSeason, SpeedRating, LoadIndex, TireSpecs

class TireSpecsDB:
    def __init__(self, connection: fdb.Connection):
        self.conn = connection
        self.create_tables()

    def create_tables(self):
        """Gerekli tabloları oluşturur"""
        cursor = self.conn.cursor()
        
        # Ebat tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TIRE_SIZES (
                ID INTEGER NOT NULL PRIMARY KEY,
                WIDTH INTEGER NOT NULL,
                ASPECT_RATIO INTEGER NOT NULL,
                CONSTRUCTION VARCHAR(1) NOT NULL,
                DIAMETER INTEGER NOT NULL,
                CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UPDATED_AT TIMESTAMP,
                IS_ACTIVE INTEGER DEFAULT 1
            )
        """)
        
        # Mevsim tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TIRE_SEASONS (
                ID INTEGER NOT NULL PRIMARY KEY,
                NAME VARCHAR(50) NOT NULL,
                CODE VARCHAR(1) NOT NULL,
                DESCRIPTION VARCHAR(255),
                CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UPDATED_AT TIMESTAMP,
                IS_ACTIVE INTEGER DEFAULT 1
            )
        """)
        
        # Hız kodu tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS SPEED_RATINGS (
                ID INTEGER NOT NULL PRIMARY KEY,
                CODE VARCHAR(1) NOT NULL,
                SPEED INTEGER NOT NULL,
                DESCRIPTION VARCHAR(255),
                CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UPDATED_AT TIMESTAMP,
                IS_ACTIVE INTEGER DEFAULT 1
            )
        """)
        
        # Yük endeksi tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS LOAD_INDICES (
                ID INTEGER NOT NULL PRIMARY KEY,
                CODE INTEGER NOT NULL,
                WEIGHT INTEGER NOT NULL,
                DESCRIPTION VARCHAR(255),
                CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UPDATED_AT TIMESTAMP,
                IS_ACTIVE INTEGER DEFAULT 1
            )
        """)
        
        # Lastik özellikleri tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TIRE_SPECS (
                ID INTEGER NOT NULL PRIMARY KEY,
                STOK_KODU VARCHAR(50) NOT NULL,
                SIZE_ID INTEGER NOT NULL,
                SEASON_ID INTEGER NOT NULL,
                SPEED_RATING_ID INTEGER NOT NULL,
                LOAD_INDEX_ID INTEGER NOT NULL,
                CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UPDATED_AT TIMESTAMP,
                IS_ACTIVE INTEGER DEFAULT 1,
                FOREIGN KEY (SIZE_ID) REFERENCES TIRE_SIZES(ID),
                FOREIGN KEY (SEASON_ID) REFERENCES TIRE_SEASONS(ID),
                FOREIGN KEY (SPEED_RATING_ID) REFERENCES SPEED_RATINGS(ID),
                FOREIGN KEY (LOAD_INDEX_ID) REFERENCES LOAD_INDICES(ID)
            )
        """)
        
        # Varsayılan değerleri ekle
        self._insert_default_values()
        
        self.conn.commit()
    
    def _insert_default_values(self):
        """Varsayılan değerleri ekler"""
        cursor = self.conn.cursor()
        
        # Mevsim tipleri
        seasons = [
            (1, 'Yaz', 'S', 'Yaz lastiği'),
            (2, 'Kış', 'W', 'Kış lastiği'),
            (3, '4 Mevsim', 'A', 'Dört mevsim lastiği')
        ]
        
        for season in seasons:
            cursor.execute("""
                INSERT INTO TIRE_SEASONS (ID, NAME, CODE, DESCRIPTION)
                SELECT ?, ?, ?, ?
                WHERE NOT EXISTS (SELECT 1 FROM TIRE_SEASONS WHERE ID = ?)
            """, (season[0], season[1], season[2], season[3], season[0]))
        
        # Hız kodları
        speed_ratings = [
            (1, 'T', 190, 'Maksimum 190 km/h'),
            (2, 'H', 210, 'Maksimum 210 km/h'),
            (3, 'V', 240, 'Maksimum 240 km/h'),
            (4, 'W', 270, 'Maksimum 270 km/h'),
            (5, 'Y', 300, 'Maksimum 300 km/h')
        ]
        
        for rating in speed_ratings:
            cursor.execute("""
                INSERT INTO SPEED_RATINGS (ID, CODE, SPEED, DESCRIPTION)
                SELECT ?, ?, ?, ?
                WHERE NOT EXISTS (SELECT 1 FROM SPEED_RATINGS WHERE ID = ?)
            """, (rating[0], rating[1], rating[2], rating[3], rating[0]))
        
        self.conn.commit()
    
    def get_tire_specs(self, stok_kodu: str) -> Optional[TireSpecs]:
        """Stok koduna göre lastik özelliklerini getirir"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                ts.ID,
                ts.STOK_KODU,
                s.ID as SIZE_ID,
                s.WIDTH,
                s.ASPECT_RATIO,
                s.CONSTRUCTION,
                s.DIAMETER,
                sn.ID as SEASON_ID,
                sn.NAME as SEASON_NAME,
                sn.CODE as SEASON_CODE,
                sn.DESCRIPTION as SEASON_DESC,
                sr.ID as SPEED_ID,
                sr.CODE as SPEED_CODE,
                sr.SPEED,
                sr.DESCRIPTION as SPEED_DESC,
                li.ID as LOAD_ID,
                li.CODE as LOAD_CODE,
                li.WEIGHT,
                li.DESCRIPTION as LOAD_DESC,
                ts.CREATED_AT,
                ts.UPDATED_AT
            FROM TIRE_SPECS ts
            JOIN TIRE_SIZES s ON ts.SIZE_ID = s.ID
            JOIN TIRE_SEASONS sn ON ts.SEASON_ID = sn.ID
            JOIN SPEED_RATINGS sr ON ts.SPEED_RATING_ID = sr.ID
            JOIN LOAD_INDICES li ON ts.LOAD_INDEX_ID = li.ID
            WHERE ts.STOK_KODU = ? AND ts.IS_ACTIVE = 1
        """, (stok_kodu,))
        
        row = cursor.fetchone()
        if not row:
            return None
            
        # Veriyi modele dönüştür
        size = TireSize(
            id=row[2],
            width=row[3],
            aspect_ratio=row[4],
            construction=row[5],
            diameter=row[6],
            created_at=row[19],
            updated_at=row[20]
        )
        
        season = TireSeason(
            id=row[7],
            name=row[8],
            code=row[9],
            description=row[10],
            created_at=row[19],
            updated_at=row[20]
        )
        
        speed_rating = SpeedRating(
            id=row[11],
            code=row[12],
            speed=row[13],
            description=row[14],
            created_at=row[19],
            updated_at=row[20]
        )
        
        load_index = LoadIndex(
            id=row[15],
            code=row[16],
            weight=row[17],
            description=row[18],
            created_at=row[19],
            updated_at=row[20]
        )
        
        return TireSpecs(
            id=row[0],
            stok_kodu=row[1],
            size=size,
            season=season,
            speed_rating=speed_rating,
            load_index=load_index,
            created_at=row[19],
            updated_at=row[20]
        )
