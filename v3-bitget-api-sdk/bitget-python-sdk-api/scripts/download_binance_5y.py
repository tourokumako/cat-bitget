"""Binance Vision から BTCUSDT 5m足 5年分をダウンロード。

データ仕様:
  source: https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/5m/
  期間: 2020-01 〜 直前月（実行時点で取得可能な最新月まで）
  形式: 月次ZIP・CSV（12列）

出力:
  data/BTCUSDT-5m-2020-01-01_<latest>_5y.csv
  形式: timestamp,open,high,low,close,volume（既存CSV形式に統一）
"""
from __future__ import annotations

import csv
import io
import sys
import urllib.request
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "data"
TMP_DIR = REPO_ROOT / "data" / "_binance_tmp"

BASE_URL = "https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/5m"
START = (2020, 1)


def _months_between(start: tuple[int, int], end_excl: tuple[int, int]) -> list[tuple[int, int]]:
    out = []
    y, m = start
    while (y, m) < end_excl:
        out.append((y, m))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return out


def _download_month(year: int, month: int, dest_dir: Path) -> Path | None:
    fname = f"BTCUSDT-5m-{year:04d}-{month:02d}.zip"
    url = f"{BASE_URL}/{fname}"
    dest = dest_dir / fname
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  [skip] {fname} already downloaded")
        return dest
    try:
        print(f"  [dl  ] {url}")
        req = urllib.request.Request(url, headers={"User-Agent": "cat-bitget/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
        dest.write_bytes(data)
        return dest
    except Exception as e:
        print(f"  [skip] {fname}: {e}")
        return None


def _zip_to_rows(zip_path: Path) -> list[list]:
    """Binance kline ZIP を読んで [timestamp, open, high, low, close, volume] のlistに変換。
    Binance kline 列: 0=open_time(ms), 1=open, 2=high, 3=low, 4=close, 5=volume, 6=close_time, ...
    """
    rows = []
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if not name.endswith(".csv"):
                continue
            with zf.open(name) as f:
                text = io.TextIOWrapper(f, encoding="utf-8")
                reader = csv.reader(text)
                for r in reader:
                    if not r or not r[0].lstrip("-").isdigit():
                        continue
                    raw = int(r[0])
                    # Binance Vision: 2024年以前=ms (13桁), 2025年以降=μs (16桁) になっている
                    if raw > 1e16:
                        ts_sec = raw / 1e6  # microseconds
                    elif raw > 1e13:
                        ts_sec = raw / 1e3  # milliseconds (legacy)
                    else:
                        ts_sec = raw / 1e3
                    try:
                        ts = datetime.utcfromtimestamp(ts_sec).strftime("%Y-%m-%d %H:%M:%S")
                    except (ValueError, OSError):
                        continue
                    rows.append([ts, r[1], r[2], r[3], r[4], r[5]])
    return rows


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    today = datetime.utcnow()
    end_year, end_month = today.year, today.month  # 当月は除外（未完成）
    months = _months_between(START, (end_year, end_month))
    print(f"[download_binance_5y] {len(months)} 月分取得 ({months[0]} 〜 {months[-1]})")

    downloaded = []
    for y, m in months:
        path = _download_month(y, m, TMP_DIR)
        if path:
            downloaded.append((y, m, path))

    if not downloaded:
        print("[error] no data downloaded")
        sys.exit(1)

    print(f"\n[merge] 月次CSVを統合...")
    all_rows = []
    for y, m, path in downloaded:
        rows = _zip_to_rows(path)
        all_rows.extend(rows)
        print(f"  {y:04d}-{m:02d}: {len(rows)} 行")
    print(f"  合計: {len(all_rows)} 行")

    # 重複除去 + ソート
    df = pd.DataFrame(all_rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df = df.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    print(f"  重複除去後: {len(df)} 行")

    first = df["timestamp"].iloc[0][:10]
    last = df["timestamp"].iloc[-1][:10]
    out_name = f"BTCUSDT-5m-{first}_{last}_5y.csv"
    out_path = OUT_DIR / out_name
    df.to_csv(out_path, index=False)
    print(f"\n→ {out_path}")
    print(f"   {len(df)} bars / {first} 〜 {last}")


if __name__ == "__main__":
    main()
