# Wolvox WooCommerce Entegrasyon

Bu proje, Wolvox ERP sistemi ile WooCommerce e-ticaret platformu arasında entegrasyon sağlar.

## Özellikler

- Wolvox ürünlerini WooCommerce'e aktarma
- Stok durumlarını senkronize etme
- Fiyat güncellemelerini otomatik yapma
- Ürün gruplarını kategori olarak aktarma
- Sipariş bilgilerini Wolvox'a aktarma

## Gereksinimler

- Python 3.8+
- Firebird SQL Client
- WooCommerce REST API erişimi

## Kurulum

1. Depoyu klonlayın:
```bash
git clone https://github.com/yourusername/wolvox-woocommerce-integration.git
cd wolvox-woocommerce-integration
```

2. Sanal ortam oluşturun ve etkinleştirin:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Gereksinimleri yükleyin:
```bash
pip install -r requirements.txt
```

4. `.env` dosyasını oluşturun ve gerekli değişkenleri ayarlayın:
```env
FIREBIRD_CLIENT_PATH=C:/Program Files/Firebird/Firebird_3_0/fbclient.dll
WOLVOX_DB_HOST=localhost
WOLVOX_DB_PATH=C:/WolvoxData/WOLVOX.FDB
WOLVOX_DB_USER=SYSDBA
WOLVOX_DB_PASSWORD=masterkey

WOOCOMMERCE_URL=https://your-store.com
WOOCOMMERCE_CONSUMER_KEY=your-consumer-key
WOOCOMMERCE_CONSUMER_SECRET=your-consumer-secret
```

## Kullanım

1. Uygulamayı başlatın:
```bash
python app.py
```

2. Tarayıcıda http://localhost:5000 adresini açın

3. Ayarlar sayfasından bağlantıları test edin

4. Ürünleri senkronize etmeye başlayın

## Katkıda Bulunma

1. Bu depoyu fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add some amazing feature'`)
4. Branch'inizi push edin (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.
