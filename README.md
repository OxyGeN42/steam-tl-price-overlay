<div align="center">

# 🎮 Steam TL Price Overlay v3

**Steam istemcisindeki USD fiyatları anlık güncel kur ile Türk Lirası'na (₺) dönüştüren hafif ve akıllı overlay sistemi.**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6.svg)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Steam CEF](https://img.shields.io/badge/Steam-CEF_Remote_Debugging-171a21.svg)](https://store.steampowered.com/)

</div>

---

## 🌟 Öne Çıkan Özellikler

- ⚡ **Sıfır Mağaza API Bağımlılığı:** Steam Web API anahtarına gerek duymaz! Sayfadaki tüm `$XX.XX` formatındaki fiyatları Chromium Remote Debugging (CEF) üzerinden okur ve dönüştürür.
- 🎨 **Üç Katmanlı Şık Akıllı Rozet (Badge) Tasarımı:**
  - 🔵 **Canlı Fiyat:** Steam temasıyla uyumlu dikey accent çizgili mavi TL rozeti.
  - ⚪ **İndirim Öncesi Fiyat:** İndirimli ürünlerde orijinal fiyatın hemen yanında soluk gri TL karşılığı.
  - 🟢 **Tasarruf Göstergesi:** İndirimli ürünlerde toplamda kaç ₺ kar ettiğinizi gösteren yeşil tasarruf rozeti (`↓ -₺XXX tasarruf`).
- 🎯 **Esnek Ve Bütüncül:** Mağaza ana sayfası, Oyun İndirilebilir İçerikleri (DLC), Paket/Bundle sayfaları, Sepet ve İstek Listesi dahil tüm Steam sayfalarında kusursuz çalışır.
- 🧠 **Çevrimdışı & Güvenli Kur Önbelleği (Cache):** Sistem açılışında API'den güncel USD/TRY kurunu alır ve yerel diske kaydeder. İnternet kesintilerinde veya API erişim sorunlarında son kaydedilen kurdan çalışmaya devam eder.
- 🚀 **Otomatik Başlatma (Startup):** Windows başlangıcına arka planda görünmez (konsolsuz) çalışacak şekilde tek komutla kurulabilir.

---

## 📸 Ekran Görüntüleri

### 🛒 Öne Çıkanlar & Mağaza Vitrini
![Forza Horizon 6 ve Mağaza Vitrini](assets/preview-featured.png)

### 📋 İstek Listesi (İndirimli & Normal Fiyat Dönüşümleri)
![İstek Listesi Görünümü](assets/preview-wishlist.png)

### 🎮 Oyun Listeleri & Liste Görünümü
![Arama ve Mağaza Listesi](assets/preview-store-list.png)

### 🔲 Grid / Kart Görünümü
![Grid İstek Listesi Görünümü](assets/preview-wishlist-grid.png)

---

## 📦 İndirme ve Releases (Hazır Sürüm)

Python veya Git kurmadan doğrudan çalıştırmak için **[Releases](https://github.com/OxyGeN42/steam-tl-price-overlay/releases)** sayfasından hazır paketi indirebilirsiniz.

[![Latest Release](https://img.shields.io/github/v/release/OxyGeN42/steam-tl-price-overlay?style=for-the-badge&color=brightgreen)](https://github.com/OxyGeN42/steam-tl-price-overlay/releases/latest)

---

## ⚙️ Gereksinimler

- **İşletim Sistemi:** Windows
- **Python:** 3.8 veya üzeri
- **Steam İstemcisi**

---

## 🚀 Kurulum Adımları

### 1. Projeyi Kopyalayın ve Bağımlılıkları Yükleyin

```bash
git clone https://github.com/OxyGeN42/steam-tl-price-overlay.git
cd steam-tl-price-overlay
pip install websocket-client requests
```

### 2. Steam Remote Debugging Ayarını Yapın (İlk Seferlik)

Steam istemcisinin dışarıdan JavaScript komutlarını kabul etmesi için uzaktan hata ayıklama modunu aktifleştirmeniz gerekir:

1. Steam'i tamamen kapatın (Sistem tepsisinden / Görev çubuğundan da çıkış yapın).
2. Komut satırında şu komutu çalıştırın (Steam yolunuz farklıysa güncelleyin):

```bash
python Steam_tl_price_overlay.py --setup "C:\Program Files (x86)\Steam"
```

3. Steam'i tekrar açın.

---

## 💻 Kullanım

### Test Amaçlı Çalıştırma

Logları anlık konsolda görmek için:

```bash
python Steam_tl_price_overlay.py --debug
```

### Windows Başlangıcına Ekleme (Önerilen)

Sistemi Windows açılışında otomatik ve görünmez (konsol penceresi olmadan) çalışacak şekilde kurmak için:

```bash
python Steam_tl_price_overlay.py --install
```

### Otomatik Başlatmayı Kaldırmak İçin

```bash
python Steam_tl_price_overlay.py --uninstall
```

---

## 🔍 Loglar ve Arka Plan Bilgileri

Sistem arka planda çalışırken log kayıtlarını ve döviz kuru önbelleğini şu dizinde saklar:

```text
%LOCALAPPDATA%\SteamTLOverlay\
  ├── overlay.log         (Sistem günlükleri)
  └── rate_cache.json     (Son çekilen kur bilgisi)
```

---

## 📜 Lisans

Bu proje [MIT Lisansı](LICENSE) altında lisanslanmıştır. Kullanmakta, değiştirmekte ve dağıtmakta tamamen özgürsünüz.

---

<div align="center">
  <sub>Steam ve Steam logosu Valve Corporation'ın tescilli ticari markalarıdır. Bu proje Valve Corporation ile bağlantılı değildir.</sub>
</div>
