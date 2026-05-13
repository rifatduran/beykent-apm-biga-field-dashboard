#!/usr/bin/env python3
"""
biga_open_meteo_hourly.csv -> data/weather/biga_weather_dashboard.html

Cikti: Chart.js pano (orijinal 6 grafik + su/iklim özeti: kümülatif, sıcaklık genişliği, bulut/radyasyon). KPI +1.

  .venv/bin/pip install -r requirements-viz.txt
  .venv/bin/python generate_weather_dashboard.py

Varsayilan: yalnizca source=archive. Tahmin dahil: --include-forecast
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

# biga_dashboard.html ile ayni renkler / Kc
KC_DEFAULT = 1.15


def load_hourly(path: Path, zone_id: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    if zone_id and "zone_id" in df.columns:
        df = df[df["zone_id"].astype(str) == str(zone_id)].copy()
    if df.empty:
        raise ValueError(f"Bos veri: {path} zone={zone_id!r}")
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp"])
    df["ts_local"] = df["timestamp"].dt.tz_convert("Europe/Istanbul")
    df["date"] = df["ts_local"].dt.strftime("%Y-%m-%d")
    return df.sort_values("ts_local")


def daily_records(df: pd.DataFrame, kc: float) -> list[dict]:
    rows = []
    for day, g in df.groupby("date", sort=True):
        precip = float(g["precipitation"].sum())
        et0 = float(g["et0_fao_evapotranspiration_daily_mm"].dropna().max() or 0.0)
        etc = et0 * kc
        need = max(0.0, round(etc - precip, 2))
        tmin = float(g["temperature_2m"].min())
        tmax = float(g["temperature_2m"].max())
        tavg = float(g["temperature_2m"].mean())
        hum_avg = float(g["relative_humidity_2m"].mean())
        hum_hours_80 = int((g["relative_humidity_2m"] >= 80).sum())
        wind_avg = float(g["wind_speed_10m"].mean()) if "wind_speed_10m" in g else 0.0
        tspan = round(tmax - tmin, 1)
        cloud_avg = (
            round(float(g["cloud_cover"].mean()), 1) if "cloud_cover" in g.columns else 0.0
        )
        sw_mean = (
            round(float(g["shortwave_radiation"].mean()), 1)
            if "shortwave_radiation" in g.columns
            else 0.0
        )
        risk = disease_risk(hum_hours_80, tavg, hum_avg)
        rows.append(
            {
                "date": day,
                "tmin": round(tmin, 1),
                "tmax": round(tmax, 1),
                "tavg": round(tavg, 1),
                "tspan": tspan,
                "hum_avg": round(hum_avg, 1),
                "hum_hours_80": hum_hours_80,
                "precip": round(precip, 1),
                "et0": round(et0, 2),
                "etc": round(etc, 2),
                "irrigation_needed": need,
                "wind_avg": round(wind_avg, 1),
                "cloud_avg": cloud_avg,
                "sw_mean": sw_mean,
                "disease_risk": risk,
            }
        )
    add_cumulative_sums(rows)
    return rows


def add_cumulative_sums(records: list[dict]) -> None:
    cp = ce = cn = 0.0
    for r in records:
        cp += r["precip"]
        ce += r["et0"]
        cn += r["irrigation_needed"]
        r["cum_precip"] = round(cp, 1)
        r["cum_et0"] = round(ce, 1)
        r["cum_irr_need"] = round(cn, 1)


def disease_risk(hum_hours_80: int, tavg: float, hum_avg: float) -> str:
    """biga_dashboard.html ile uyumlu basit Tom-Cast uyarisi (nem saati + sicaklik bandi)."""
    if hum_hours_80 >= 10 or (hum_hours_80 >= 8 and 10 <= tavg <= 25):
        return "HIGH"
    if hum_hours_80 >= 4 or hum_avg >= 78:
        return "MEDIUM"
    return "LOW"


def kpis(records: list[dict]) -> dict[str, float | int]:
    precip_total = sum(r["precip"] for r in records)
    et0_total = sum(r["et0"] for r in records)
    irr_total = sum(r["irrigation_needed"] for r in records)
    high_days = sum(1 for r in records if r["disease_risk"] == "HIGH")
    rain_days = sum(1 for r in records if r["precip"] > 0.05)
    tspan_avg = sum(r["tspan"] for r in records) / max(len(records), 1)
    return {
        "precip_total": round(precip_total, 0),
        "et0_total": round(et0_total, 0),
        "irr_total": round(irr_total, 0),
        "high_days": int(high_days),
        "rain_days": int(rain_days),
        "tspan_avg": round(tspan_avg, 1),
    }


def date_range_line(records: list[dict]) -> str:
    if not records:
        return "Veri yok"
    a, b = records[0]["date"], records[-1]["date"]
    # 2026-04-01 -> "1 Nisan"
    def tr_date(iso: str) -> str:
        y, m, d = map(int, iso.split("-"))
        aylar = (
            "",
            "Ocak",
            "Şubat",
            "Mart",
            "Nisan",
            "Mayıs",
            "Haziran",
            "Temmuz",
            "Ağustos",
            "Eylül",
            "Ekim",
            "Kasım",
            "Aralık",
        )
        return f"{d} {aylar[m]} {y}"

    return f"{tr_date(a)} – {tr_date(b)}"


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Biga Ovası — Hava Durumu Dashboard</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: 'Segoe UI', system-ui, sans-serif;
    background: #f5f4f0;
    color: #1a1a18;
    min-height: 100vh;
    padding: 2rem 1.5rem;
  }

  header {
    margin-bottom: 2rem;
  }

  header .tag {
    display: inline-block;
    font-size: 11px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    background: #1a1a18;
    color: #f5f4f0;
    padding: 4px 10px;
    border-radius: 4px;
    margin-bottom: 10px;
  }

  header h1 {
    font-size: 26px;
    font-weight: 600;
    color: #1a1a18;
    line-height: 1.2;
  }

  header p {
    font-size: 13px;
    color: #6b6a65;
    margin-top: 6px;
  }

  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 10px;
    margin-bottom: 2rem;
  }

  .kpi {
    background: #fff;
    border: 0.5px solid #d8d7d0;
    border-radius: 10px;
    padding: 1rem 1.1rem;
  }

  .kpi .label {
    font-size: 11px;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 6px;
  }

  .kpi .value {
    font-size: 24px;
    font-weight: 600;
    color: #1a1a18;
    line-height: 1;
  }

  .kpi .value.danger { color: #c0392b; }
  .kpi .value.blue   { color: #1a5fa8; }
  .kpi .value.green  { color: #1a7a52; }
  .kpi .value.amber  { color: #9a6200; }

  .charts-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }

  @media (max-width: 800px) {
    .charts-grid { grid-template-columns: 1fr; }
  }

  .chart-card {
    background: #fff;
    border: 0.5px solid #d8d7d0;
    border-radius: 12px;
    padding: 1.25rem 1.4rem 1.1rem;
  }

  .chart-card.full-width {
    grid-column: 1 / -1;
  }

  .chart-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 10px;
    gap: 12px;
  }

  .chart-title {
    font-size: 13px;
    font-weight: 600;
    color: #1a1a18;
  }

  .chart-sub {
    font-size: 11px;
    color: #999;
    margin-top: 2px;
  }

  .legend {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 10px;
  }

  .legend span {
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 11px;
    color: #666;
  }

  .legend .dot {
    width: 10px;
    height: 10px;
    border-radius: 2px;
    flex-shrink: 0;
  }

  .legend .line {
    width: 16px;
    height: 2px;
    flex-shrink: 0;
  }

  .chart-wrap {
    position: relative;
    width: 100%%;
  }

  footer {
    margin-top: 2rem;
    font-size: 11px;
    color: #aaa;
    text-align: center;
  }
</style>
</head>
<body>

<header>
  <div class="tag">APM Group 8 — Beykent Üniversitesi</div>
  <h1>Biga Ovası Hava Durumu Dashboard</h1>
  <p>Domates tarlası · 40.17°N 27.22°E · %(range_line)s · %(source_note)s</p>
</header>

<div class="kpi-grid">
  <div class="kpi">
    <div class="label">Toplam yağış</div>
    <div class="value blue">%(kpi_precip)s <small style="font-size:14px;font-weight:400">mm</small></div>
  </div>
  <div class="kpi">
    <div class="label">Toplam ET₀</div>
    <div class="value amber">%(kpi_et0)s <small style="font-size:14px;font-weight:400">mm</small></div>
  </div>
  <div class="kpi">
    <div class="label">Net sulama ihtiyacı</div>
    <div class="value green">%(kpi_irr)s <small style="font-size:14px;font-weight:400">mm</small></div>
  </div>
  <div class="kpi">
    <div class="label">Yüksek hastalık riski</div>
    <div class="value danger">%(kpi_high)s <small style="font-size:14px;font-weight:400">gün</small></div>
  </div>
  <div class="kpi">
    <div class="label">Yağışlı gün</div>
    <div class="value blue">%(kpi_rain_days)s <small style="font-size:14px;font-weight:400">gün</small></div>
  </div>
  <div class="kpi">
    <div class="label">Ort. günlük sıcaklık genişliği</div>
    <div class="value amber">%(kpi_tspan_avg)s <small style="font-size:14px;font-weight:400">°C</small></div>
  </div>
</div>

<div class="charts-grid">

  <div class="chart-card full-width">
    <div class="chart-header">
      <div>
        <div class="chart-title">Günlük Sıcaklık Bandı</div>
        <div class="chart-sub">Min / Ortalama / Max · °C · tarih ekseni GG.AA.YYYY</div>
      </div>
    </div>
    <div class="legend">
      <span><span class="dot" style="background:#e05252;"></span>Max sıcaklık</span>
      <span><span class="dot" style="background:#1d9e75;"></span>Ortalama</span>
      <span><span class="dot" style="background:#378add;"></span>Min sıcaklık</span>
    </div>
    <div class="chart-wrap" style="height:220px;">
      <canvas id="c1" role="img" aria-label="Min, ortalama ve max sıcaklık"></canvas>
    </div>
  </div>

  <div class="chart-card">
    <div class="chart-header">
      <div>
        <div class="chart-title">Yağış vs. Sulama İhtiyacı</div>
        <div class="chart-sub">Günlük · mm · Kc=%(kc)s (domates meyve)</div>
      </div>
    </div>
    <div class="legend">
      <span><span class="dot" style="background:#378add;"></span>Yağış</span>
      <span><span class="dot" style="background:#1d9e75;"></span>Sulama ihtiyacı (ETc−yağış)</span>
    </div>
    <div class="chart-wrap" style="height:210px;">
      <canvas id="c2" role="img" aria-label="Yağış ve sulama ihtiyacı"></canvas>
    </div>
  </div>

  <div class="chart-card">
    <div class="chart-header">
      <div>
        <div class="chart-title">Bağıl Nem + Mildiyö Eşiği</div>
        <div class="chart-sub">Günlük ortalama · %%</div>
      </div>
    </div>
    <div class="legend">
      <span><span class="dot" style="background:#7f77dd;"></span>Ortalama nem</span>
      <span><span class="line" style="background:#e05252; border-top: 2px dashed #e05252;"></span>%%80 eşiği</span>
    </div>
    <div class="chart-wrap" style="height:210px;">
      <canvas id="c3" role="img" aria-label="Bağıl nem"></canvas>
    </div>
  </div>

  <div class="chart-card">
    <div class="chart-header">
      <div>
        <div class="chart-title">Mildiyö Hastalık Riski</div>
        <div class="chart-sub">Nem ≥%%80 saati / gün · basit Tom-Cast uyarisi</div>
      </div>
    </div>
    <div class="legend">
      <span><span class="dot" style="background:#e05252;"></span>Yüksek</span>
      <span><span class="dot" style="background:#ef9f27;"></span>Orta</span>
      <span><span class="dot" style="background:#639922;"></span>Düşük</span>
    </div>
    <div class="chart-wrap" style="height:210px;">
      <canvas id="c4" role="img" aria-label="Hastalık riski"></canvas>
    </div>
  </div>

  <div class="chart-card">
    <div class="chart-header">
      <div>
        <div class="chart-title">ET₀ — Referans Evapotranspirasyon</div>
        <div class="chart-sub">FAO Penman-Monteith · mm/gün</div>
      </div>
    </div>
    <div class="legend">
      <span><span class="dot" style="background:#ef9f27;"></span>ET₀ (mm/gün)</span>
    </div>
    <div class="chart-wrap" style="height:210px;">
      <canvas id="c5" role="img" aria-label="ET0"></canvas>
    </div>
  </div>

  <div class="chart-card">
    <div class="chart-header">
      <div>
        <div class="chart-title">Ortalama Rüzgar Hızı</div>
        <div class="chart-sub">Günlük ortalama · km/sa</div>
      </div>
    </div>
    <div class="legend">
      <span><span class="dot" style="background:#888780;"></span>Rüzgar hızı</span>
    </div>
    <div class="chart-wrap" style="height:210px;">
      <canvas id="c6" role="img" aria-label="Rüzgar"></canvas>
    </div>
  </div>

  <div class="chart-card full-width">
    <div class="chart-header">
      <div>
        <div class="chart-title">Kümülatif yağış ve ET₀</div>
        <div class="chart-sub">Sezon boyunca birikim · mm · sulama–iklim dengesi özeti</div>
      </div>
    </div>
    <div class="legend">
      <span><span class="dot" style="background:#378add;"></span>Kümülatif yağış</span>
      <span><span class="dot" style="background:#ef9f27;"></span>Kümülatif ET₀</span>
    </div>
    <div class="chart-wrap" style="height:240px;">
      <canvas id="c7" role="img" aria-label="Kümülatif yağış ve ET0"></canvas>
    </div>
  </div>

  <div class="chart-card">
    <div class="chart-header">
      <div>
        <div class="chart-title">Günlük sıcaklık genişliği</div>
        <div class="chart-sub">Max − Min · °C · ani sıcaklık dalgalanması</div>
      </div>
    </div>
    <div class="legend">
      <span><span class="dot" style="background:#6d4c41;"></span>Günlük fark</span>
    </div>
    <div class="chart-wrap" style="height:210px;">
      <canvas id="c8" role="img" aria-label="Sıcaklık genişliği"></canvas>
    </div>
  </div>

  <div class="chart-card">
    <div class="chart-header">
      <div>
        <div class="chart-title">Kümülatif net sulama ihtiyacı</div>
        <div class="chart-sub">Günlük max(0, ETc−yağış) birikimi · mm · Kc=%(kc)s</div>
      </div>
    </div>
    <div class="legend">
      <span><span class="dot" style="background:#1a7a52;"></span>Birikimli ihtiyaç</span>
    </div>
    <div class="chart-wrap" style="height:210px;">
      <canvas id="c9" role="img" aria-label="Kümülatif sulama ihtiyacı"></canvas>
    </div>
  </div>

  <div class="chart-card full-width">
    <div class="chart-header">
      <div>
        <div class="chart-title">Bulutluluk ve kısa dalga radyasyon</div>
        <div class="chart-sub">Günlük ortalama · %% bulut · W/m² (saatlik ort.)</div>
      </div>
    </div>
    <div class="legend">
      <span><span class="dot" style="background:#78909c;"></span>Bulutluluk</span>
      <span><span class="dot" style="background:#f9a825;"></span>Kısa dalga</span>
    </div>
    <div class="chart-wrap" style="height:240px;">
      <canvas id="c10" role="img" aria-label="Bulut ve radyasyon"></canvas>
    </div>
  </div>

</div>

<footer>
  Veri: %(footer_data)s · Koordinat: 40.17°N, 27.22°E · Kc=%(kc)s (domates meyve dönemi) ·
  Risk: nem≥%%80 saat + 10–25°C bandı (basitleştirilmiş)
</footer>

<script>
const DATA = %(data_json)s;

const labels = DATA.map(d => {
  const parts = d.date.split('-');
  return `${parts[2]}.${parts[1]}.${parts[0]}`;
});
const tickCfg = { autoSkip: true, maxTicksLimit: 12, font: { size: 10 }, color: '#999', maxRotation: 50 };
const gridCfg = { color: 'rgba(0,0,0,0.06)' };
const baseOpts = (yLabel) => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false }, tooltip: { mode: 'index', intersect: false, bodyFont: { size: 12 }, titleFont: { size: 12 } } },
  scales: {
    x: { ticks: tickCfg, grid: { display: false } },
    y: { ticks: tickCfg, grid: gridCfg, title: yLabel ? { display: true, text: yLabel, font: { size: 11 }, color: '#aaa' } : { display: false } }
  }
});

new Chart(document.getElementById('c1'), {
  type: 'line',
  data: { labels, datasets: [
    { label: 'Max', data: DATA.map(d=>d.tmax), borderColor:'#e05252', borderWidth:1.5, pointRadius:0, fill:false, tension:0.3 },
    { label: 'Ortalama', data: DATA.map(d=>d.tavg), borderColor:'#1d9e75', borderWidth:2, pointRadius:0, fill:false, tension:0.3 },
    { label: 'Min', data: DATA.map(d=>d.tmin), borderColor:'#378add', borderWidth:1.5, pointRadius:0, fill:false, tension:0.3 }
  ]},
  options: baseOpts('°C')
});

new Chart(document.getElementById('c2'), {
  type: 'bar',
  data: { labels, datasets: [
    { label: 'Yağış', data: DATA.map(d=>d.precip), backgroundColor:'rgba(55,138,221,0.65)', borderRadius:2 },
    { label: 'Sulama ihtiyacı', data: DATA.map(d=>d.irrigation_needed), backgroundColor:'rgba(29,158,117,0.65)', borderRadius:2 }
  ]},
  options: { ...baseOpts('mm'), scales: { ...baseOpts('mm').scales, x: { ...baseOpts().scales.x, stacked: false } } }
});

new Chart(document.getElementById('c3'), {
  type: 'line',
  data: { labels, datasets: [
    { label: 'Ortalama nem', data: DATA.map(d=>d.hum_avg), borderColor:'#7f77dd', backgroundColor:'rgba(127,119,221,0.09)', borderWidth:2, pointRadius:0, fill:true, tension:0.3 },
    { label: '%%80 eşiği', data: DATA.map(()=>80), borderColor:'#e05252', borderWidth:1.2, borderDash:[5,4], pointRadius:0, fill:false }
  ]},
  options: { ...baseOpts('%%'), scales: { ...baseOpts('%%').scales, y: { ...baseOpts('%%').scales.y, min:40, max:100 } } }
});

const riskColor = r => r==='HIGH' ? 'rgba(224,82,82,0.75)' : r==='MEDIUM' ? 'rgba(239,159,39,0.7)' : 'rgba(99,153,34,0.65)';
new Chart(document.getElementById('c4'), {
  type: 'bar',
  data: { labels, datasets: [{
    label: 'Nem≥80%% saati',
    data: DATA.map(d=>d.hum_hours_80),
    backgroundColor: DATA.map(d=>riskColor(d.disease_risk)),
    borderRadius: 2
  }]},
  options: {
    ...baseOpts('saat/gün'),
    plugins: {
      legend: { display: false },
      tooltip: { callbacks: { label: ctx => `${ctx.raw} saat ≥%%80 nem · ${DATA[ctx.dataIndex].disease_risk}` } }
    },
    scales: { ...baseOpts('saat/gün').scales, y: { ...baseOpts('saat/gün').scales.y, max: 24 } }
  }
});

new Chart(document.getElementById('c5'), {
  type: 'line',
  data: { labels, datasets: [{
    label: 'ET₀',
    data: DATA.map(d=>d.et0),
    borderColor:'#ef9f27', backgroundColor:'rgba(239,159,39,0.1)', borderWidth:2, pointRadius:0, fill:true, tension:0.3
  }]},
  options: baseOpts('mm/gün')
});

new Chart(document.getElementById('c6'), {
  type: 'line',
  data: { labels, datasets: [{
    label: 'Rüzgar',
    data: DATA.map(d=>d.wind_avg),
    borderColor:'#888780', backgroundColor:'rgba(136,135,128,0.08)', borderWidth:1.5, pointRadius:0, fill:true, tension:0.3
  }]},
  options: baseOpts('km/sa')
});

new Chart(document.getElementById('c7'), {
  type: 'line',
  data: { labels, datasets: [
    { label: 'Kümülatif yağış', data: DATA.map(d=>d.cum_precip), borderColor:'#378add', borderWidth:2, pointRadius:0, fill:false, tension:0.2 },
    { label: 'Kümülatif ET₀', data: DATA.map(d=>d.cum_et0), borderColor:'#ef9f27', borderWidth:2, pointRadius:0, fill:false, tension:0.2 }
  ]},
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: true, position: 'top', labels: { boxWidth: 12, font: { size: 11 } } },
      tooltip: { mode: 'index', intersect: false, bodyFont: { size: 12 }, titleFont: { size: 12 } }
    },
    scales: {
      x: { ticks: tickCfg, grid: { display: false } },
      y: { ticks: tickCfg, grid: gridCfg, title: { display: true, text: 'mm (birikimli)', font: { size: 11 }, color: '#aaa' } }
    }
  }
});

new Chart(document.getElementById('c8'), {
  type: 'line',
  data: { labels, datasets: [{
    label: 'Max−Min',
    data: DATA.map(d=>d.tspan),
    borderColor:'#6d4c41', backgroundColor:'rgba(109,76,65,0.1)', borderWidth:2, pointRadius:0, fill:true, tension:0.3
  }]},
  options: baseOpts('°C')
});

new Chart(document.getElementById('c9'), {
  type: 'line',
  data: { labels, datasets: [{
    label: 'Birikim',
    data: DATA.map(d=>d.cum_irr_need),
    borderColor:'#1a7a52', backgroundColor:'rgba(26,122,82,0.12)', borderWidth:2, pointRadius:0, fill:true, tension:0.25
  }]},
  options: baseOpts('mm (birikimli)')
});

new Chart(document.getElementById('c10'), {
  type: 'line',
  data: { labels, datasets: [
    { label: 'Bulutluluk', data: DATA.map(d=>d.cloud_avg), borderColor:'#78909c', backgroundColor:'rgba(120,144,156,0.06)', borderWidth:2, pointRadius:0, fill:true, tension:0.3, yAxisID: 'y' },
    { label: 'Kısa dalga', data: DATA.map(d=>d.sw_mean), borderColor:'#f9a825', borderWidth:2, pointRadius:0, fill:false, tension:0.3, yAxisID: 'y1' }
  ]},
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: true, position: 'top', labels: { boxWidth: 12, font: { size: 11 } } },
      tooltip: { mode: 'index', intersect: false, bodyFont: { size: 12 }, titleFont: { size: 12 } }
    },
    scales: {
      x: { ticks: tickCfg, grid: { display: false } },
      y: {
        type: 'linear', display: true, position: 'left',
        ticks: tickCfg, grid: gridCfg,
        min: 0, max: 100,
        title: { display: true, text: 'Bulut %%', font: { size: 11 }, color: '#78909c' }
      },
      y1: {
        type: 'linear', display: true, position: 'right',
        ticks: tickCfg, grid: { drawOnChartArea: false },
        title: { display: true, text: 'W/m²', font: { size: 11 }, color: '#f9a825' }
      }
    }
  }
});
</script>
</body>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="CSV → Chart.js dashboard (biga_dashboard stili)")
    ap.add_argument("-i", "--input", type=Path, default=Path("data/weather/biga_open_meteo_hourly.csv"))
    ap.add_argument("-o", "--output", type=Path, default=Path("data/weather/biga_weather_dashboard.html"))
    ap.add_argument("--zone", default="A1")
    ap.add_argument("--kc", type=float, default=KC_DEFAULT, help="Domates ETc katsayisi")
    ap.add_argument(
        "--include-forecast",
        action="store_true",
        help="Tahmin (source=forecast) gunlerini de dahil et; vermezsen sadece arsiv",
    )
    args = ap.parse_args()

    if not args.input.is_file():
        print(f"Bulunamadi: {args.input}")
        return 1

    df = load_hourly(args.input, args.zone)
    archive_only = not args.include_forecast
    if archive_only and "source" in df.columns:
        df = df[df["source"].astype(str) == "archive"].copy()
        if df.empty:
            print("Uyari: archive filtresi sonrasi bos; tum kaynaklar kullaniliyor.", flush=True)
            df = load_hourly(args.input, args.zone)
            archive_only = False

    records = daily_records(df, args.kc)
    if not records:
        print("Gunluk kayit uretilemedi.")
        return 1

    k = kpis(records)
    src_types = df["source"].dropna().unique().tolist() if "source" in df.columns else []
    if archive_only:
        source_note = "Open-Meteo arşiv verisi"
        footer_data = "Open-Meteo Archive API"
    else:
        source_note = "Open-Meteo (" + ", ".join(sorted(str(x) for x in src_types)) + ")"
        footer_data = "Open-Meteo API (arşiv + tahmin)"

    html = HTML_TEMPLATE % {
        "range_line": date_range_line(records),
        "source_note": source_note,
        "kpi_precip": int(k["precip_total"]),
        "kpi_et0": int(k["et0_total"]),
        "kpi_irr": int(k["irr_total"]),
        "kpi_high": k["high_days"],
        "kpi_rain_days": k["rain_days"],
        "kpi_tspan_avg": k["tspan_avg"],
        "kc": args.kc,
        "footer_data": footer_data,
        "data_json": json.dumps(records, ensure_ascii=False),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding="utf-8")
    print(
        f"OK: {args.output.resolve()} | {len(records)} gun | zone={args.zone} | archive_only={archive_only}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
