import os
import re
from dotenv import load_dotenv
import fdb
from tabulate import tabulate
from decimal import Decimal

# Load environment variables
load_dotenv()

def parse_tire_dimensions(stok_adi):
    """Lastik ölçülerini ayrıştır"""
    # Örnek: 175/70R13
    pattern = r'(\d{3})/(\d{2})R(\d{2})'
    match = re.search(pattern, stok_adi)
    if match:
        return {
            'genislik': match.group(1),  # 175
            'kesit_orani': match.group(2),  # 70
            'jant_capi': match.group(3)  # 13
        }
    return None

try:
    # Firebird client path'ini ayarla
    fb_client_path = os.getenv('FIREBIRD_CLIENT_PATH')
    if fb_client_path and os.path.exists(fb_client_path):
        fdb.load_api(fb_client_path)
    
    # Veritabanı bağlantı bilgilerini al
    database = os.getenv('WOLVOX_DB_PATH')
    user = os.getenv('WOLVOX_DB_USER')
    password = os.getenv('WOLVOX_DB_PASSWORD')

    print("Veritabanına bağlanılıyor...")
    print(f"Veritabanı: {database}\n")

    # Connect to the database
    con = fdb.connect(
        database=database,
        user=user,
        password=password
    )
    cur = con.cursor()

    # Örnek ürün bilgilerini al
    stok_adi = "175/70R13 TL 82T ELEGANT PT311 PETLAS"
    
    print(f"'{stok_adi}' için detaylı ürün bilgileri:\n")
    
    # Şimdi stok kartını sorgula
    cur.execute("""
        SELECT 
            s.BLKODU,
            s.STOKKODU,
            s.STOK_ADI,
            s.BARKODU,
            s.BIRIMI,
            s.KDV_ORANI,
            s.MARKASI,
            s.MODELI,
            s.GRUBU,
            s.ALT_GRUBU,
            s.WEBDE_GORUNSUN,
            s.AKTIF,
            s.BIRIM_AGIRLIK,
            s.ETICARET_ACIKLAMA,
            s.RESIM_YOLU,
            s.ACIKLAMA1,
            s.ACIKLAMA2,
            s.ACIKLAMA3,
            s.ACIKLAMA4,
            s.KALITE,
            s.URETICI_FIRMA,
            s.YERLI_URETIM,
            s.URETIM_YERI,
            s.GTIP_NO,
            s.OZELALANTANIM_3,
            s.OZELALANTANIM_5,
            s.OZELALANTANIM_6,
            s.OZELALANTANIM_7,
            s.OZELALANTANIM_8,
            s.OZELALANTANIM_9,
            s.OZELALANTANIM_10,
            s.OZELALANTANIM_11,
            s.OZELALANTANIM_12,
            s.OZELALANTANIM_13,
            s.OZELALANTANIM_22,
            s.OZELALANTANIM_23,
            s.OZELALANTANIM_27,
            s.OZELALANTANIM_28
        FROM STOK s
        WHERE s.STOK_ADI LIKE ?
    """, ('%' + stok_adi + '%',))
    
    stok = cur.fetchone()
    
    if stok:
        # Alanları ve değerlerini bir sözlükte topla
        fields = [
            "BLKODU", "STOKKODU", "STOK_ADI", "BARKODU", "BIRIMI", 
            "KDV_ORANI", "MARKASI", "MODELI", "GRUBU", "ALT_GRUBU",
            "WEBDE_GORUNSUN", "AKTIF", "BIRIM_AGIRLIK", "ETICARET_ACIKLAMA",
            "RESIM_YOLU", "ACIKLAMA1", "ACIKLAMA2", "ACIKLAMA3", "ACIKLAMA4",
            "KALITE", "URETICI_FIRMA", "YERLI_URETIM", "URETIM_YERI", "GTIP_NO",
            "OZELALANTANIM_3", "OZELALANTANIM_5", "OZELALANTANIM_6", "OZELALANTANIM_7",
            "OZELALANTANIM_8", "OZELALANTANIM_9", "OZELALANTANIM_10", "OZELALANTANIM_11",
            "OZELALANTANIM_12", "OZELALANTANIM_13", "OZELALANTANIM_22", "OZELALANTANIM_23",
            "OZELALANTANIM_27", "OZELALANTANIM_28"
        ]
        
        print("Ürün Detayları:")
        print("-" * 50)
        
        dolu_alanlar = []
        for i, field in enumerate(fields):
            value = stok[i]
            if value is not None and str(value).strip() != '':
                dolu_alanlar.append(field)
                # Özel karakter sorunlarını önlemek için strip() kullan
                if isinstance(value, str):
                    value = value.strip()
                print(f"{field}: {value}")
        
        # Lastik ölçülerini parse et
        boyutlar = parse_tire_dimensions(stok[2])  # STOK_ADI'ndan boyutları al
        if boyutlar:
            print("\nLastik Ölçüleri:")
            print("-" * 50)
            print(f"Genişlik: {boyutlar['genislik']}")
            print(f"Kesit Oranı: {boyutlar['kesit_orani']}")
            print(f"Jant Çapı: {boyutlar['jant_capi']}")
        
        print("\nDolu Alanlar:")
        print("-" * 50)
        print(", ".join(dolu_alanlar))
        
        # Stok fiyatlarını getir
        print("\nFiyat Bilgileri:")
        print("-" * 50)
        cur.execute("""
            SELECT 
                sf.FIYAT_NO,
                sf.FIYATI,
                sf.BIRIMI as PARA_BIRIMI,
                sf.ALIS_SATIS,
                sf.TANIMI
            FROM STOK_FIYAT sf
            WHERE sf.BLSTKODU = ?
            ORDER BY sf.FIYAT_NO
        """, (stok[0],))
        
        fiyatlar = cur.fetchall()
        if fiyatlar:
            headers = ["Fiyat No", "Fiyat", "Para Birimi", "Alış/Satış", "Tanım"]
            fiyat_data = []
            for fiyat in fiyatlar:
                fiyat_data.append([
                    fiyat[0],
                    float(fiyat[1]) if fiyat[1] else 0,
                    fiyat[2].strip() if fiyat[2] else "TL",
                    "Alış" if fiyat[3] == 0 else "Satış",
                    fiyat[4].strip() if fiyat[4] else ""
                ])
            print(tabulate(fiyat_data, headers=headers, tablefmt="grid"))
        
        # Depo bazlı stok miktarları
        print("\nDepo Bazlı Stok Miktarları:")
        print("-" * 50)
        cur.execute("""
            SELECT 
                d.DEPO_ADI,
                (SELECT -COALESCE(SUM(
                    CASE 
                        WHEN sh.TUTAR_TURU = 0 THEN sh.MIKTARI 
                        ELSE -sh.MIKTARI 
                    END), 0)
                FROM STOKHR sh 
                WHERE sh.DEPO_ADI = d.DEPO_ADI 
                AND sh.BLSTKODU = ?
                AND sh.SILINDI = 0) as KALAN_MIKTAR
            FROM DEPO d
            WHERE d.AKTIF = 1
            ORDER BY d.DEPO_ADI
        """, (stok[0],))
        
        depo_miktarlar = cur.fetchall()
        if depo_miktarlar:
            headers = ["Depo Adı", "Kalan Miktar"]
            depo_miktarlar = [[depo[0].strip(), float(depo[1])] for depo in depo_miktarlar if float(depo[1]) != 0]
            print(tabulate(depo_miktarlar, headers=headers, tablefmt="grid"))
            
            toplam_kalan = sum(miktar[1] for miktar in depo_miktarlar)
            print(f"\nToplam Kalan Miktar: {toplam_kalan}")
            
    else:
        print(f"'{stok_adi}' kodlu ürün bulunamadı!")

except Exception as e:
    print(f"Hata oluştu: {str(e)}")
    import traceback
    print(traceback.format_exc())

finally:
    print("\nVeritabanı bağlantısı kapatıldı.")
    if 'con' in locals():
        con.close()
