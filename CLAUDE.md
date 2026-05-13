# CLAUDE.md — AI-Based Precision Agriculture System
## Smart Field Management | Biga Ovası, Çanakkale | Domates Tarlası (100 ha)

---

## 📌 PROJE GENEL BAKIŞ

Bu proje, İstanbul Beykent Üniversitesi Mühendislik ve Mimarlık Fakültesi kapsamında yürütülen
Applied Project Management dersi bitirme projesidir. 100 hektarlık domates tarlasına yapay zeka
destekli hassas tarım sistemi kurulmasını simüle etmektedir.

**Sponsor:** Symbiotic Farming Systems  
**Proje Danışmanları:** Asst. Prof. Dr. Tuğçe İnan & Prof. Dr. Mesut Kaçan  
**Proje Süresi:** 20.04.2026 – 20.06.2027 (14 ay)  
**Toplam Bütçe:** $315,000  
**Mevcut Faz:** Planning & Design

---

## 🎯 KPI HEDEFLERİ (Başarı Kriterleri)

| KPI | Mevcut Durum | Hedef | İyileştirme |
|-----|-------------|-------|-------------|
| Su tüketimi | 1.000.000 m³/yıl | 700.000 m³/yıl | **-%30** |
| Gübre kullanımı | 300 ton/yıl | 240 ton/yıl | **-%20** |
| Enerji tüketimi | 150.000 kWh/yıl | 127.500 kWh/yıl | **-%15** |
| Ürün verimi | 1.200 ton/yıl | 1.380 ton/yıl | **+%15** |
| Yıllık net tasarruf | — | $54,250 | Geri ödeme: ~5.8 yıl |

---

## 📍 LOKASYON & TARLA BİLGİSİ

- **Bölge:** Çanakkale — Biga Ovası
- **Koordinatlar:** ~40.17°N, 27.22°E
- **Ürün:** Domates (Solanum lycopersicum)
- **Toprak tipi:** Kil-tın (clay-loam)
- **Alan:** 100 hektar → 40 zone × 2.5 ha/zone
- **Sulama tipi:** Damla sulama (drip irrigation)
- **Sezon:** Yaklaşık Nisan – Eylül

### Biga'ya Özgü Kritik Riskler
- **Yüksek nem** → Mildiyö (*Phytophthora infestans*) ve külleme riski yüksek
- **Yağış + sulama dengesi** → Gereksiz sulama büyük verimlilik kaybı
- **Toprak drenajı** → Su birikmesi kök çürüklüğüne yol açar
- **Ca eksikliği** → Çiçek burnu çürüklüğü (Blossom End Rot) için kritik

---

## 🏗️ SİSTEM MİMARİSİ

### Bileşenler ve Maliyetler
| Bileşen | Maliyet | Tedarikçi |
|---------|---------|-----------|
| Variable-Rate Irrigation (VRI) Sistemi | $100,000 | Smart Terra Grid |
| AI Karar Destek Platformu | $75,000 | AgroSync Intelligence |
| IoT Saha Sensör Ağı (40 node) | $55,000 | TerraTech Adaptive Network |
| Hassas Gübreleme (Fertigation) Sistemi | $45,000 | — |
| Çiftçi Arayüzü & Kontrol Merkezi | $40,000 | — |

### Ağ Protokolleri
- **LoRaWAN** (868 MHz Türkiye bandı) → Uzun mesafe, düşük güç telemetri
- **NB-IoT** → Yüksek müdahale bölgelerinde kritik node'lar için
- **Edge Computing** → ARM Cortex işlemciler, SQLite buffer → internet kesilmesinde lokal işlem
- **SCADA** → Merkezi izleme ve kontrol
- **MODBUS / OPC-UA** → VRI valve ve pompa kontrol protokolleri

### AI Model Altyapısı
- **LSTM** (Long Short-Term Memory) → Nem döngüsü, zaman serisi analizi
- **Random Forest** → NPK seviyeleri, Sentinel-2 uydu görüntüsü çok değişkenli analiz
- **Hedef doğruluk:** >%85 verim tahmini

---

## 📊 VERİ KATEGORİLERİ VE DURUMLARI

### 1. 🌡️ HAVA DURUMU VERİLERİ
**Durum: ✅ Mevcut — Hemen kullanılabilir**

| Veri | Kaynak | Erişim |
|------|--------|--------|
| Sıcaklık, nem, yağış, rüzgar | Open-Meteo API | Ücretsiz, koordinat bazlı |
| Güneşlenme süresi | Open-Meteo API | Ücretsiz |
| Gece-gündüz sıcaklık farkı | Open-Meteo API | Hesaplanabilir |
| Don riski | Open-Meteo API | Ücretsiz |
| Yaprak ıslaklığı (leaf wetness) | Visual Crossing / Meteomatics | Ücretsiz katman mevcut |
| Yüksek nem günleri | MGM (mgm.gov.tr) | Çanakkale/Biga istasyonu |

**Biga koordinatları:** `lat=40.17, lon=27.22`  
**Open-Meteo endpoint:** `https://api.open-meteo.com/v1/forecast`  
**Geçmiş veri:** `https://archive-api.open-meteo.com/v1/archive`

> ⚠️ Yaprak ıslaklığı + nem verisi → Mildiyö risk modeli (Tom-Cast / Blitecast) için zorunlu

---

### 2. 🌱 TOPRAK VERİLERİ
**Durum: 🟡 Kısmen mevcut — Baseline literatürden, gerçek ölçüm sensör gerektirir**

| Veri | Kaynak | Not |
|------|--------|-----|
| pH değeri | ISRIC / FAO SoilSTAT | Biga için ~6.2–6.8 ideal aralık |
| Su tutma kapasitesi | ISRIC World Soil Database | Kil-tın profili |
| NPK referans aralıkları | Akademik makaleler | Baseline için |
| Toprak sınıflandırması | TAGEM (tagem.gov.tr) | Bölgesel harita |
| **Gerçek zamanlı:** nem, sıcaklık, pH, EC, NPK, Ca | **IoT sensör (40 node)** | Sensör kurulunca aktif |

**Simülasyon için:** Çanakkale koşullarına göre sentetik veri üretimi yapılabilir.  
**Alternatif:** Çanakkale Onsekiz Mart Üniversitesi Ziraat Fakültesi'nden tarla ölçüm verisi talep edilebilir.

---

### 3. 🛰️ BİTKİ / ÜRÜN VERİLERİ
**Durum: 🟡 Uydu verisi mevcut, gerçek zamanlı sensör gerektirir**

| Veri | Kaynak | Not |
|------|--------|-----|
| NDVI (bitki sağlık indeksi) | Sentinel-2 / Google Earth Engine | 10m çözünürlük, ücretsiz |
| Yaprak rengi (sararma → N eksikliği) | Sentinel-2 bant analizi | Hesaplanabilir |
| Büyüme evresi takvimi | Literatür | Nisan–Eylül, Biga iklimine göre |
| Baseline verim | TÜİK (tuik.gov.tr) | Çanakkale ili domates istatistikleri |
| Hastalık riski (mildiyö, külleme) | Tom-Cast model | Nem + sıcaklık verisinden hesaplanır |

**Sentinel-2 erişim:** `https://dataspace.copernicus.eu`  
**Google Earth Engine:** `https://earthengine.google.com`

---

### 4. 💧 SULAMA VERİLERİ
**Durum: 🟡 Hesaplanabilir — FAO-56 yöntemi**

| Veri | Yöntem | Not |
|------|--------|-----|
| Bitki su ihtiyacı (ETc) | FAO-56 Penman-Monteith | Hava verisinden hesaplanır |
| Sulama miktarı (litre/zone) | ETc - Yağış | Gereksiz sulama tespiti |
| Sulama zamanı ve sıklığı | Toprak nemi + ETc | Domates: az ama sık sulama |
| Damla sulama debisi | Sistem şartnamesi | VRI kurulumundan gelir |
| Zone bazlı sulama kaydı | SCADA / VRI sistemi | Sensör kurulunca aktif |

**Domates sulama notu:** Toprak nemi %60–80 field capacity arası tutulmalı.  
**Biga notu:** Yağış verisi mutlaka ETc hesabına dahil edilmeli.

---

### 5. ⚡ ENERJİ VERİLERİ
**Durum: 🟡 Hesaplanabilir — Pompa şartnamesinden**

| Veri | Yöntem | Not |
|------|--------|-----|
| Sulama sistemi enerji tüketimi (kWh) | Pompa gücü × çalışma süresi | Formül: P×t/η |
| Pompa çalışma süresi | SCADA logu | VFD sistemden |
| Enerji tasarrufu karşılaştırması | 150.000 → 127.500 kWh | Proje hedefi -%15 |

**VFD tasarruf formülü:** Hız %20 düşünce güç ~%49 düşer (kübik ilişki).

---

### 6. 💰 MALİYET VERİLERİ
**Durum: 🟡 Açık kaynaklardan bulunabilir**

| Veri | Kaynak |
|------|--------|
| Su maliyeti (₺/m³) | DSİ veya yerel sulama birliği, Biga |
| Gübre maliyeti (₺/ton) | Tarım Kredi Kooperatifleri (tarimkredi.gov.tr) |
| Enerji maliyeti (₺/kWh) | TEDAŞ tarımsal elektrik tarifesi |
| İlaçlama maliyeti | Tarım Kredi Kooperatifleri / yerel bayi |

---

### 7. 🤖 AI ÇIKTILARI
**Durum: 🔵 Sistem kurulunca üretilecek — Şu an tasarım fazında**

| AI Çıktısı | Girdi Verisi | Model |
|------------|-------------|-------|
| Sulama önerisi (ne zaman / ne kadar) | Toprak nemi + ETc + yağış tahmini | Random Forest + kural tabanlı |
| Gübreleme önerisi | NPK seviyeleri + bitki evresi | LSTM |
| Hastalık riski tahmini (mildiyö) | Nem + yaprak ıslaklığı + sıcaklık | Tom-Cast / LSTM |
| Verim tahmini | NDVI + toprak + iklim | Random Forest (>%85 hedef) |
| Hasat zamanı tahmini | Büyüme takvimi + GDD (growing degree days) | Kural tabanlı |

---

### 8. 📍 LOKASYON / ZONE VERİSİ
**Durum: ✅ Tasarım hazır**

- 100 ha → **40 zone** × 2.5 ha
- Her zone'un benzersiz **Zone ID**'si var
- Her veri noktasına `zone_id`, `timestamp`, `lat`, `lon` eklenmeli
- Zone bazlı toprak ve nem değişkenliği göz önünde bulundurulmalı

---

### 9. 🕐 ZAMAN VERİSİ
**Durum: ✅ Standart — Tüm verilere eklenmeli**

```
timestamp: ISO 8601 formatı → "2026-06-15T08:00:00Z"
Saatlik veri: Hava + sensör ölçümleri
Günlük veri: Sulama toplamı, enerji tüketimi, maliyet özeti
```

---

## 📁 ÖNERİLEN DOSYA / MODÜL YAPISI

```
precision-agriculture/
│
├── data/
│   ├── weather/          # Open-Meteo API çıktıları
│   ├── soil/             # Sensör verileri veya simülasyon
│   ├── satellite/        # Sentinel-2 NDVI görüntüleri
│   ├── irrigation/       # Sulama logları
│   ├── energy/           # Enerji tüketim verileri
│   └── cost/             # Maliyet verileri
│
├── models/
│   ├── lstm_moisture.py       # Nem döngüsü zaman serisi
│   ├── rf_yield_prediction.py # Verim tahmini
│   └── disease_risk.py        # Mildiyö risk modeli (Tom-Cast)
│
├── api/
│   ├── open_meteo.py          # Hava verisi çekme
│   ├── sentinel2.py           # Uydu görüntüsü
│   └── scada_connector.py     # VRI/sensör bağlantısı
│
├── dashboard/
│   ├── farmer_interface/      # Mobil/web arayüzü
│   └── alerts/                # 3 seviyeli alarm sistemi
│
└── CLAUDE.md                  # Bu dosya
```

---

## 🔄 KAPALI DÖNGÜ VERİ AKIŞI (Closed-Loop Pipeline)

```
[Sensörler] → [LoRaWAN/NB-IoT] → [Edge Gateway] → [Cloud AI Platform]
     ↑                                                        ↓
[VRI Valfler] ← [MODBUS/OPC-UA] ← [Kontrol Merkezi] ← [AI Kararı]
     ↓
[Doğrulama Sensörü] → Geri besleme → AI model güncelleme
```

---

## 📅 PROJE MİLESTONE'LARI

| Görev | Durum | Tarih |
|-------|-------|-------|
| SWOT Tabanlı Risk Haritalama | ✅ Tamamlandı | 03.05.2026 |
| AI Platform & Veri Pipeline Mimarisi | 🔄 Devam ediyor | 24.05.2026 |
| IoT Sensör Node Tedariki | 📋 Planlandı | 15.06.2026 |
| Saha Implementasyonu | 📋 Planlandı | 20.07.2026 |
| İlk Sezon Veri Analizi | 📋 Planlandı | 30.11.2026 |
| Kış Optimizasyonu & Kalibrasyon | 📋 Planlandı | 15.03.2027 |
| Final Performans Raporu | 📋 Planlandı | 20.06.2027 |

---

## ⚠️ RİSK ÖNCELİKLERİ (En Yüksekten Düşüğe)

| Risk | Skor | Sorumlu |
|------|------|---------|
| R4 — Kırsal internet altyapısı yetersizliği | 20 | Computer Eng. / Civil Eng. |
| R1 — Ekip koordinasyon & iletişim | 16 | Core Team |
| R15 — Teknoloji rekabeti | 16 | Core Team |
| R3 — Düşük kaliteli AI saha verisi | 15 | Computer Eng. |
| R6 — Düşük çiftçi adaptasyonu | 20 | Interior Arch. / Industrial Eng. |

---

## 💡 CURSOR İÇİN NOTLAR

- Her modül yazılırken `zone_id` ve `timestamp` alanları **zorunlu** olmalı
- Veri simülasyonu için Biga iklimine uygun parametreler kullanılmalı
- Mildiyö riski hesabında **Tom-Cast** veya **Blitecast** algoritması referans alınmalı
- Domates için kritik eşikler: pH 6.2–6.8, toprak nemi %60–80 FC, Ca >150 ppm
- VFD pompa enerji modelinde kübik hız-güç ilişkisi kullanılmalı: `P ∝ n³`
- Tüm API çağrıları `try/except` ile sarılmalı, veri kalitesi doğrulaması eklenmeli
- Open-Meteo geçmiş veri için: `start_date=2025-04-01`, `end_date=2025-09-30` (referans sezon)
