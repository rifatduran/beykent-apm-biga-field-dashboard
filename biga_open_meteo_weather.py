#!/usr/bin/env python3
"""
Biga Ovasi merkez koordinatlari icin Open-Meteo arsiv + tahmin hava verisini
tek bir CSV dosyasinda birlestirir.

Cikti: data/weather/biga_open_meteo_hourly.csv

Her satir: zone_id, lat, lon, zaman + saatlik meteoroloji + gunluk et0 (o gune ait).

Bagimlilik: yalnizca Python 3 standart kutuphanesi (urllib, json, csv, argparse).
"""

from __future__ import annotations

import argparse
import csv
import json
import ssl
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# CLAUDE.md / proje notlari
DEFAULT_LAT = 40.17
DEFAULT_LON = 27.22
# Mevcut Excel seti ile hizali varsayilan zone listesi (aynı seri her zone'a cogaltilir)
DEFAULT_ZONES = ("A1", "A2", "B1", "B2")

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

HOURLY_PARAMS = [
    "temperature_2m",
    "relative_humidity_2m",
    "dew_point_2m",
    "precipitation",
    "rain",
    "showers",
    "snowfall",
    "weather_code",
    "cloud_cover",
    "pressure_msl",
    "surface_pressure",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
    "shortwave_radiation",
    "direct_radiation",
    "diffuse_radiation",
    "direct_normal_irradiance",
    "global_tilted_irradiance",
]

DAILY_PARAMS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "rain_sum",
    "et0_fao_evapotranspiration",
]


def fetch_json(
    url: str, timeout: int = 60, ssl_context: ssl.SSLContext | None = None
) -> dict:
    req = Request(url, headers={"User-Agent": "precision-ag-biga/1.0"})
    try:
        with urlopen(req, timeout=timeout, context=ssl_context) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"HTTP {e.code} for {url}: {body}") from e
    except URLError as e:
        raise RuntimeError(f"Ag baglantisi basarisiz ({url}): {e.reason}") from e


def iter_archive_chunks(
    start: date, end: date, chunk_days: int
) -> list[tuple[date, date]]:
    """[start,end] araligini chunk_days uzunlugunda (son parca kisa olabilir) parcalara ayir."""
    if start > end:
        return []
    out: list[tuple[date, date]] = []
    cur = start
    while cur <= end:
        chunk_end = min(cur + timedelta(days=max(chunk_days, 1) - 1), end)
        out.append((cur, chunk_end))
        cur = chunk_end + timedelta(days=1)
    return out


def fetch_archive_hourly_merged(
    lat: float,
    lon: float,
    start: date,
    end: date,
    ssl_context: ssl.SSLContext | None,
    chunk_days: int = 90,
    request_timeout: int = 120,
) -> tuple[list[str], list[dict], dict[str, float | None]]:
    """
    Uzun arsiv araligi icin birden fazla istek; zamanlari birlestirir, tekrarlayan saatleri atar.
    Donus: (times, hourly_row_dict_list, gun -> et0)
    """
    merged_times: list[str] = []
    merged_rows: list[dict] = []
    merged_et0: dict[str, float | None] = {}
    seen: set[str] = set()
    chunks = iter_archive_chunks(start, end, chunk_days)
    for i, (cs, ce) in enumerate(chunks):
        arch = fetch_archive_hourly_chunk(lat, lon, cs, ce, ssl_context, request_timeout)
        arch_hourly = arch.get("hourly") or {}
        times = arch_hourly.get("time") or []
        _, rows = hourly_index(times, arch_hourly)
        for t, r in zip(times, rows):
            if t in seen:
                continue
            seen.add(t)
            merged_times.append(t)
            merged_rows.append(r)
        arch_d = fetch_archive_daily_et0_chunk(lat, lon, cs, ce, ssl_context, request_timeout)
        merged_et0.update(daily_et0_map(arch_d.get("daily") or {}))
        print(f"  arsiv parca {i + 1}/{len(chunks)}: {cs} .. {ce} ({len(times)} saat)", file=sys.stderr)
        if i < len(chunks) - 1:
            time.sleep(0.6)
    return merged_times, merged_rows, merged_et0


def fetch_archive_hourly_chunk(
    lat: float,
    lon: float,
    start: date,
    end: date,
    ssl_context: ssl.SSLContext | None,
    timeout: int,
) -> dict:
    q = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "timezone": "Europe/Istanbul",
        "hourly": ",".join(HOURLY_PARAMS),
    }
    return fetch_json(f"{ARCHIVE_URL}?{urlencode(q)}", timeout=timeout, ssl_context=ssl_context)


def fetch_archive_daily_et0_chunk(
    lat: float,
    lon: float,
    start: date,
    end: date,
    ssl_context: ssl.SSLContext | None,
    timeout: int,
) -> dict:
    q = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "timezone": "Europe/Istanbul",
        "daily": "et0_fao_evapotranspiration",
    }
    return fetch_json(f"{ARCHIVE_URL}?{urlencode(q)}", timeout=timeout, ssl_context=ssl_context)


def fetch_forecast_hourly_daily(
    lat: float, lon: float, days: int, ssl_context: ssl.SSLContext | None
) -> dict:
    q = {
        "latitude": lat,
        "longitude": lon,
        "timezone": "Europe/Istanbul",
        "forecast_days": str(days),
        "hourly": ",".join(HOURLY_PARAMS),
        "daily": ",".join(DAILY_PARAMS),
    }
    return fetch_json(
        f"{FORECAST_URL}?{urlencode(q)}", timeout=90, ssl_context=ssl_context
    )


def hourly_index(times: list[str], hourly_data: dict) -> tuple[list[str], list[dict]]:
    """Open-Meteo hourly -> list of row dicts keyed by short column names."""
    cols = []
    rows: list[dict] = []
    n = len(times)
    series_keys = [k for k in hourly_data if k != "time"]
    for i in range(n):
        row = {}
        for key in series_keys:
            vals = hourly_data[key]
            col_name = key
            row[col_name] = vals[i] if i < len(vals) else None
        rows.append(row)
    cols = ["time"] + series_keys
    return cols, rows


def daily_et0_map(daily: dict) -> dict[str, float | None]:
    """date_str -> et0_fao_evapotranspiration (daily sum)."""
    times = daily.get("time", [])
    et0 = daily.get("et0_fao_evapotranspiration")
    if not times or not et0:
        return {}
    out: dict[str, float | None] = {}
    for i, t in enumerate(times):
        d = str(t)[:10]
        out[d] = et0[i] if i < len(et0) else None
    return out


def to_istanbul_iso(ts: str) -> str:
    """Open-Meteo saat stringi (yerel, tz yok) -> ISO 8601 Europe/Istanbul."""
    ts = str(ts).strip()
    if not ts:
        return ts
    if " " in ts and "T" not in ts:
        ts = ts.replace(" ", "T", 1)
    if len(ts) == 16:
        ts = ts + ":00"
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("Europe/Istanbul"))
    return dt.isoformat()


def build_output_rows(
    times: list[str],
    hourly_rows: list[dict],
    source: str,
    et0_by_date: dict[str, float | None],
    zones: tuple[str, ...],
    lat: float,
    lon: float,
) -> list[dict]:
    out: list[dict] = []
    for i, t in enumerate(times):
        day = str(t)[:10]
        et0 = et0_by_date.get(day)
        base = {
            "timestamp": to_istanbul_iso(str(t)),
            "source": source,
            "latitude": lat,
            "longitude": lon,
            "et0_fao_evapotranspiration_daily_mm": et0,
        }
        hr = hourly_rows[i] if i < len(hourly_rows) else {}
        for zone_id in zones:
            row = {
                "zone_id": zone_id,
                **base,
            }
            for k, v in hr.items():
                row[k] = v
            out.append(row)
    return out


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError("Yazilacak satir yok")
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def main() -> int:
    p = argparse.ArgumentParser(description="Biga Open-Meteo tek CSV hava verisi")
    p.add_argument("--lat", type=float, default=DEFAULT_LAT)
    p.add_argument("--lon", type=float, default=DEFAULT_LON)
    p.add_argument(
        "--archive-start",
        type=str,
        default=None,
        help=(
            "Arsiv baslangic (YYYY-MM-DD). Verilmezse: "
            "--archive-years-back ile (bugunun yilinden N yil cikarilip) o yilin 1 Nisani"
        ),
    )
    p.add_argument(
        "--archive-years-back",
        type=int,
        default=2,
        help=(
            "--archive-start yokken: bugunun takvim yilindan N cikartilinca elde edilen yilin "
            "1 Nisan'indan basla. 0 = icinde bulunulan yilin 1 Nisani"
        ),
    )
    p.add_argument(
        "--archive-chunk-days",
        type=int,
        default=90,
        help="Uzun arsivde API istegini parcalamak icin gun sayisi (90 onerilir)",
    )
    p.add_argument(
        "--archive-end",
        type=str,
        default=None,
        help="Arsiv bitis (YYYY-MM-DD). Varsayilan: bugun",
    )
    p.add_argument(
        "--forecast-days",
        type=int,
        default=16,
        help="Tahmin gun sayisi (0=tahmin yok). Open-Meteo ust siniri genelde 16",
    )
    p.add_argument(
        "--zones",
        type=str,
        default=",".join(DEFAULT_ZONES),
        help="Virgulle ayrilmis zone_id listesi (her biri icin ayni met istasyonu tekrarlanir)",
    )
    p.add_argument(
        "-o",
        "--output",
        type=str,
        default="data/weather/biga_open_meteo_hourly.csv",
    )
    p.add_argument(
        "--insecure",
        action="store_true",
        help="SSL sertifika dogrulamasini kapat (gelistirme; kurumsal/mac ca sorunlarinda)",
    )
    args = p.parse_args()
    ssl_ctx: ssl.SSLContext | None
    if args.insecure:
        ssl_ctx = ssl._create_unverified_context()
    else:
        ssl_ctx = None

    zones = tuple(z.strip() for z in args.zones.split(",") if z.strip())
    if not zones:
        zones = DEFAULT_ZONES

    today = date.today()
    arch_end_requested = parse_date(args.archive_end) if args.archive_end else today
    if args.archive_start:
        arch_start = parse_date(args.archive_start)
    elif args.archive_years_back <= 0:
        arch_start = date(today.year, 4, 1)
    else:
        arch_start = date(today.year - args.archive_years_back, 4, 1)
    yesterday = today - timedelta(days=1)
    arch_end = min(arch_end_requested, yesterday)
    if arch_start > arch_end_requested:
        print("archive-start, talep edilen archive-end'ten sonra olamaz", file=sys.stderr)
        return 1

    all_rows: list[dict] = []
    arch_times: list[str] = []

    # --- Arsiv (tahminle cakismasin: en fazla dun tarihine kadar) ---
    if arch_start <= arch_end:
        try:
            print(
                f"Arsiv cekiliyor: {arch_start} .. {arch_end} "
                f"(parca ~{args.archive_chunk_days} gun)",
                file=sys.stderr,
            )
            arch_times, arch_h_rows, arch_et0 = fetch_archive_hourly_merged(
                args.lat,
                args.lon,
                arch_start,
                arch_end,
                ssl_ctx,
                chunk_days=args.archive_chunk_days,
            )
        except Exception as e:
            print(f"Arsiv alinamadi: {e}", file=sys.stderr)
            return 2

        all_rows.extend(
            build_output_rows(
                arch_times, arch_h_rows, "archive", arch_et0, zones, args.lat, args.lon
            )
        )
    else:
        print(
            f"Uyari: arsiv penceresi bos (baslangic {arch_start}, arsiv bitis capi {arch_end}); yalnizca tahmin yazilir.",
            file=sys.stderr,
        )

    fc_times: list[str] = []
    # --- Tahmin ---
    if args.forecast_days > 0:
        try:
            fc = fetch_forecast_hourly_daily(
                args.lat, args.lon, args.forecast_days, ssl_ctx
            )
        except Exception as e:
            print(f"Tahmin alinamadi: {e}", file=sys.stderr)
            return 3

        fc_hourly = fc.get("hourly") or {}
        fc_times = fc_hourly.get("time") or []
        _, fc_h_rows = hourly_index(fc_times, fc_hourly)
        fc_daily = fc.get("daily") or {}
        et0_map = daily_et0_map(fc_daily)
        all_rows.extend(
            build_output_rows(
                fc_times, fc_h_rows, "forecast", et0_map, zones, args.lat, args.lon
            )
        )

    if not all_rows:
        print("Hic satir uretilmedi (arsiv bos ve tahmin kapali mi?)", file=sys.stderr)
        return 5

    out_path = Path(args.output)
    try:
        write_csv(out_path, all_rows)
    except OSError as e:
        print(f"CSV yazilamadi: {e}", file=sys.stderr)
        return 4

    fc_note = (
        f"tahmin {args.forecast_days} gun ({len(fc_times)} saat * {len(zones)} zone)"
        if args.forecast_days > 0
        else "tahmin yok"
    )
    print(
        f"OK: {len(all_rows)} satir -> {out_path.resolve()} | "
        f"arsiv {arch_start}..{arch_end} ({len(arch_times)} saat * {len(zones)} zone) | "
        f"{fc_note}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
