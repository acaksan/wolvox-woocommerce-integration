# Wolvox - WooCommerce Entegrasyon

Bu proje, Wolvox ERP sistemi ile WooCommerce e-ticaret platformu arasında veri senkronizasyonunu sağlayan bir entegrasyon uygulamasıdır.

## Özellikler

- Ürün bilgilerinin Wolvox'tan WooCommerce'e aktarımı
- Stok durumu senkronizasyonu
- Sipariş bilgilerinin WooCommerce'den Wolvox'a aktarımı
- Fiyat güncellemelerinin otomatik senkronizasyonu

## Kurulum

1. Gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```

2. `.env` dosyasını oluşturun ve gerekli bilgileri ekleyin:
```
WOOCOMMERCE_URL=your_store_url
WOOCOMMERCE_KEY=your_consumer_key
WOOCOMMERCE_SECRET=your_consumer_secret
WOLVOX_CONNECTION_STRING=your_connection_string
```

## Kullanım

Uygulamayı başlatmak için:
```bash
python main.py
```
