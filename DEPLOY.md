# Vercel + günlük otomatik güncelleme

## Neden GitHub Actions?

Vercel sunucusuz fonksiyonları uzun süren (parçalı) Open-Meteo çekimleri ve büyük CSV üretimi için uygun değil; kalıcı dosya da repo dışına yazılır. Bu yüzden **günlük iş Python ile GitHub Actions’ta** çalışır; sonuç **commit + push** ile repoya yazılır. Repo Vercel’e bağlıysa her push yeni deploy üretir.

## Vercel

1. [vercel.com](https://vercel.com) → **Add New Project** → GitHub’dan bu repoyu seç.
2. Framework: **Other** (veya boş). `vercel.json` içinde `outputDirectory` → **`public`**.
3. Build Command boş bırakılabilir; Output Directory: **`public`** (Vercel arayüzünde doğrula).
4. Deploy. Ana sayfa `/` → `public/index.html`, pano → `/weather/biga_weather_dashboard.html`.

## Günlük cron

`.github/workflows/daily-weather.yml` her gün **06:15 UTC** civarında çalışır.

- `biga_open_meteo_weather.py` ile CSV güncellenir.
- `generate_weather_dashboard.py` ile `public/weather/biga_weather_dashboard.html` yenilenir.
- Değişiklik varsa otomatik commit + push ( **`Settings → Actions → General → Workflow permissions`: Read and write** açık olmalı).

Manuel tetikleme: GitHub → **Actions** → **Daily weather refresh** → **Run workflow**.

## İlk kurulumda `public/weather`

İlk deploy’da dosya yoksa workflow bir kez çalıştır veya yerelde:

```bash
mkdir -p public/weather
pip install -r requirements-viz.txt
python biga_open_meteo_weather.py
python generate_weather_dashboard.py -o public/weather/biga_weather_dashboard.html
git add public/weather/biga_weather_dashboard.html data/weather/biga_open_meteo_hourly.csv
git commit -m "chore: ilk public dashboard"
git push
```

## SSL

GitHub Actions (Ubuntu) genelde Open-Meteo için ek `--insecure` gerektirmez; macOS’ta lokal çalıştırırken gerekebilir.
