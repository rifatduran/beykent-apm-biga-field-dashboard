# Veri envanteri ve eksiklikler raporu

**Proje:** Hassas tarım / Biga domates (CLAUDE.md)  
**Rapor tarihi:** 2026-05-13  
**Kapsam:** Çalışma klasöründeki dosyalar, CLAUDE.md hedefleri, veri boşlukları.

---

## 1. Şu anda klasörde olanlar (tespit)

| Dosya | Ne içeriyor |
|-------|-------------|
| `CLAUDE.md` | Proje özeti: KPI, 40 zone hedefi, mimari, Open-Meteo uçları, Sentinel-2, FAO-56, modül önerisi. |
| `BigaDomatesSulamaDataset.xlsx` | ~100 satır sulama/çevre: `timestamp`, `zone_id`, sıcaklık, nem, yağış, toprak nemi, sulama hacmi/süre, debi, sıklık, `etc_mm`, `disease_risk`. Bölgeler: A1, A2, B1, B2. |
| `BigaDomatesMaliyetDataset - Kopya.xlsx` | ~100 satır maliyet (USD): su, gübre, enerji, ilaçlama, toplam; `humidity_percent`, `disease_risk`. |
| `Veri Setlerinin Yapısı.docx` | A1–A2 / B1–B2 açıklaması, `rain_skip`, `disease_risk`, debi-süre, kaynakça. |
| `zaman ve lokasyon veri .pdf` | Zaman/lokasyon dokümanı (PDF; otomatik metin çıkarımı ortamda güvenilir değil). |
| `biga_open_meteo_weather.py` | **Tek dosya:** Open-Meteo arşiv (düne kadar) + tahmin; çıktı: `data/weather/biga_open_meteo_hourly.csv`. Her zone için satır çoğaltımı (`A1,A2,B1,B2`). `--insecure` ile macOS/SSL sertifika sorununda geçici çözüm. |
| `data/weather/biga_open_meteo_hourly.csv` | Script çalıştırılınca üretilen birleşik saatlik hava + günlük ET₀ (tahmin bloğunda) |

---

## 2. Durum özeti: tam / yarım / eksik

### Tam (mevcut ve doğrudan kullanılabilir)

- Proje tanımı ve hedef KPI’lar (`CLAUDE.md`).
- Sulama tarafı tablo verisi (Excel).
- Maliyet tablosu (Excel).
- Metodoloji özeti (docx).

### Yarım (var ama eksik, tutarsız veya doğrulanmalı)

- **Zone ölçeği:** Hedef 40 zone; Excel’de 4 zone (A1–B2).
- **Konum:** Excel’de `lat` / `lon` yok; PDF’de olabilir — netleştirilmeli.
- **Hava:** Excel’de basit sıcaklık/nem/yağış var; Open-Meteo ile tam saatlik seri ve kaynak şeffaflığı **script ile tamamlanıyor** (tek CSV).
- **Toprak (IoT/laboratuvar):** Gerçek zamanlı NPK, pH, Ca vb. yok; sadece sulama dosyasındaki toprak nemi.
- **İki Excel birleşimi:** `(timestamp, zone_id)` kesişimi düşük (~28/100) — hizalı anahtar veya veri üretim mantığı netleştirilmeli.
- **Tarih formatı:** Sulama `YYYY-MM-DD HH:MM`, maliyet `DD.MM.YYYY HH:MM` — birleştirmede normalize edilmeli.
- **`etc_mm`:** Büyüklükler pratik ET beklentisiyle uyumsuz görünebilir — birim doğrulaması.
- **Yazılım mimarisi:** `precision-agriculture/` ağacı, `api/`, `models/`, `dashboard/` henüz kurulmadı (sadece bu rapor + hava scripti adımı).

### Eksik (hedef dokümana göre yok veya başlanmadı)

- `data/weather/`, `data/soil/`, `data/satellite/`, `data/energy/` altında düzenli ham/üretilmiş klasör standardı (isteğe bağlı; script `data/weather/` oluşturur).
- Sentinel-2 / NDVI ürünleri.
- MGM veya yaprak ıslaklığı katmanı (mildiyö modeli için CLAUDE’de vurgulanan kısım).
- SCADA / IoT ham logları.
- Tom-Cast / Blitecast veya LSTM/RF model kodu.

---

## 3. Toprak verisini nereden çekebiliriz? (araştırma özeti)

Amaç: Biga (~40.17N, 27.22E) için **referans/baseline** toprak özellikleri (bünye, pH, organik karbon, N/P/K göstergeleri vb.) ve mümkünse Türkiye ulusal katmanları.

| Kaynak | Ne sunar | Erişim / not |
|--------|----------|----------------|
| **ISRIC SoilGrids 2.0** | Küresel 250 m (yaklaşık) raster ve nokta sorgusu: kil/kum/silt, pH, SOC, BD, vb. | REST: `https://rest.isric.org` — dokümantasyonda ara ara kesinti/uyarı olabildiği belirtiliyor; alternatif: COG indirme. Python/R: soilstats, soilDB (`fetchSoilGrids`). İstek başına hız limiti (ör. ~5 dk’da 5 istek) politikasına uy. |
| **FAO HWSD v2.0** | ~1 km çözünürlükte harmonize toprak birimleri ve öznitelik veritabanı | [FAO Soils Portal — HWSD 2.0](https://www.fao.org/soils-portal/data-hub/soil-maps-and-databases/harmonized-world-soil-database-v20/) — raster + .mdb/veri paketi; GIS veya DB ile sorgu. |
| **OpenLandMap / WoSIS** | Küresel tahmin yüzeyleri (bazı özellikler ISRIC ekosisteminde) | Harita/indirme üzerinden; akademik ve ticari kullanım koşullarına bak. |
| **TAGEM — Ülkesel Toprak Bilgi Sistemi** | Türkiye ölçeğinde pH, EC, bünye, P, K, KDK, karbon vb. harita/veri | [TAGEM duyuruları / Tarım Bilgi Sistemi](https://www.tarimorman.gov.tr/TAGEM/) üzerinden; bölgesel tamamlanma durumu değişebilir — Biga için özel tabaka var mı kontrol edilmeli. |
| **TUCBS** | Ulusal coğrafi veri altyapısı | [tucbs.gov.tr](https://tucbs.gov.tr/) — ortofoto, tematik harita ve servisler için; toprak temalı katmanlar varsa metaveriden doğrula. |
| **Yerel / akademik** | Ölçüm veya öğrenci projesi için gerçek saha profili | Örn. bölgesel ziraat fakültesi veya TAGEM biriminden örnek profil — IoT gelene kadar baseline için en güvenilir yol. |

**Önerilen sıra (teknik):** (1) Biga merkez koordinat için **SoilGrids nokta sorgusu** veya küçük bbox ile raster örnek; → (2) aynı hücre için **HWSD** karşılaştırması; → (3) **TAGEM** katmanında Çanakkale/Biga uyumluluğu; → (4) sensör gelince CSV şemasına `zone_id`, `timestamp` ile gerçek zamanlı kolonlar.

---

## 4. Sonraki adımlar (öncelik)

1. **Hava:** `biga_open_meteo_weather.py` çalıştır → `data/weather/biga_open_meteo_hourly.csv` üret; Excel ile birleştirirken tarih/saat normalizasyonu kullan.
2. **Toprak:** SoilGrids ve/veya HWSD ile tek satırlık “baseline profil” + kaynak atfı; TAGEM portalında bölge kontrolü.
3. **Şema:** İstenirse 40 zone için merkez koordinat tablosu (PDF veya yeni CSV) — hava/tekrarlanan grid ile uyum.

### 4.1 Hava CSV’sini üretmek

Proje kökünde (SSL sorunu varsa `--insecure`):

```bash
python3 biga_open_meteo_weather.py --insecure
```

**Varsayılanlar:** `--archive-years-back 2` → takvimde **2 yıl önceki 1 Nisan**dan **düne** kadar arşiv; arşiv istekleri **~90 günlük parçalarla** birleştirilir. Üzerine **16 gün tahmin** eklenir.

Özelleştirme örnekleri:

| İhtiyaç | Örnek |
|--------|--------|
| Daha eski başlangıç | `--archive-start 2022-04-01` veya `--archive-years-back 5` |
| Sabit sezon bitişi (kapalı tarih) | `--archive-end 2025-09-30` |
| Sadece geçmiş, tahmin yok | `--forecast-days 0` |
| Sadece bu yıl Nisan’dan | `--archive-years-back 0` |

Uzun vadede macOS’ta Python sertifikalarını `Applications/Python 3.x/Install Certificates.command` ile kurmak daha doğrudur (`--insecure` gereksiz kalır).

### 4.2 HTML dashboard (biga_dashboard ile aynı görünüm)

```bash
.venv/bin/python generate_weather_dashboard.py
```

Çıktı: `data/weather/biga_weather_dashboard.html` — `biga_dashboard.html` ile aynı Chart.js düzeni ve KPI’lar; veri CSV’den üretilir. Tahmin günlerini de eklemek için: `--include-forecast`.

---

*Bu rapor, depodaki dosya envanteri ve açık kaynak toprak kanalları için yapılan taramaya dayanır; hukuki/lisans koşulları her kaynak için ayrı doğrulanmalıdır.*
