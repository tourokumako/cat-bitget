"""Binance Vision から BTCUSDT 1m足を taker_buy_base 列つきで取得（急騰キルスイッチ CVD 用）。

なぜ taker 列か:
  急騰の継続/反転は「総出来高」でなく「成行買い圧の偏り＝CVD（taker buy − taker sell）」で分かれる
  （order flow imbalance・cat-bitget E36 急騰Exit 調査 2026-06-21）。既存 1m CSV は OHLCV 6列で
  taker を捨てているため再取得が要る。Binance kline 9列目 = taker_buy_base_asset_volume。

データ仕様（§8.2.1.1 準拠）:
  source: https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/  ← Binance Spot（bitget 足は混ぜない）
  形式: 月次ZIP・CSV（12列）。μs(2025+)/ms(≤2024) は 1e14 境界で分離。
  price=Binance Spot / cost=Bitget 確定値（eval_engine・混同しない）。

出力（既存は温存・新ファイル名）:
  data/BTCUSDT-1m-binance-taker-<first>_<last>.csv
  形式: timestamp,open,high,low,close,volume,taker_buy_base

使い方:
  python3.13 scripts/data/download_binance_1m_taker.py [START_YYYY-MM] [END_YYYY-MM(exclusive)]
  既定 = 採点窓 2025-06 〜 2026-03（end 排他）
"""
from __future__ import annotations

import csv
import io
import sys
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "data"
TMP_DIR = REPO_ROOT / "data" / "_binance_tmp_1m"

BASE_URL = "https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m"
DEFAULT_START = (2025, 6)
DEFAULT_END_EXCL = (2026, 3)
TAKER_COL = 9  # Binance kline: 9 = taker_buy_base_asset_volume


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
    fname = f"BTCUSDT-1m-{year:04d}-{month:02d}.zip"
    url = f"{BASE_URL}/{fname}"
    dest = dest_dir / fname
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  [skip] {fname} already downloaded")
        return dest
    try:
        print(f"  [dl  ] {url}")
        req = urllib.request.Request(url, headers={"User-Agent": "cat-bitget/1.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
        dest.write_bytes(data)
        return dest
    except Exception as e:
        print(f"  [skip] {fname}: {e}")
        return None


def _zip_to_rows(zip_path: Path) -> list[list]:
    """Binance kline ZIP → [timestamp, open, high, low, close, volume, taker_buy_base]。
    列: 0=open_time, 1=open, 2=high, 3=low, 4=close, 5=volume, ..., 9=taker_buy_base。
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
                    # μs(2025+・16桁・1.7e15) / ms(≤2024・13桁) を 1e14 境界で分離（§8.2.1.1）
                    if raw > 1e14:
                        ts_sec = raw / 1e6
                    elif raw > 1e11:
                        ts_sec = raw / 1e3
                    else:
                        ts_sec = raw
                    try:
                        ts = datetime.utcfromtimestamp(ts_sec).strftime("%Y-%m-%d %H:%M:%S")
                    except (ValueError, OSError):
                        continue
                    if len(r) <= TAKER_COL:
                        continue  # taker 列が無い行はスキップ（壊れ行）
                    rows.append([ts, r[1], r[2], r[3], r[4], r[5], r[TAKER_COL]])
    return rows


def _continuity_check(df: pd.DataFrame) -> None:
    t = pd.to_datetime(df["timestamp"])
    dup = int(df["timestamp"].duplicated().sum())
    full = pd.date_range(t.iloc[0], t.iloc[-1], freq="1min")
    missing = len(full) - len(t.unique())
    # taker_buy_base ≤ volume の健全性（成行買い分は総出来高以下のはず）
    v = pd.to_numeric(df["volume"], errors="coerce")
    tb = pd.to_numeric(df["taker_buy_base"], errors="coerce")
    bad = int((tb > v * 1.0000001).sum())
    print(f"  [continuity] 重複 {dup} / 1分グリッド欠損 {missing} / taker>volume 異常 {bad}")
    print(f"  [taker健全性] taker_buy_base 中央比(/volume)={(tb / v).median():.3f}（0〜1の範囲ならOK）")


def main() -> None:
    start = DEFAULT_START
    end_excl = DEFAULT_END_EXCL
    if len(sys.argv) >= 2:
        y, m = sys.argv[1].split("-"); start = (int(y), int(m))
    if len(sys.argv) >= 3:
        y, m = sys.argv[2].split("-"); end_excl = (int(y), int(m))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    months = _months_between(start, end_excl)
    print(f"[download_binance_1m_taker] {len(months)} 月分取得 ({months[0]} 〜 {months[-1]})")

    downloaded = []
    for y, m in months:
        path = _download_month(y, m, TMP_DIR)
        if path:
            downloaded.append((y, m, path))
    if not downloaded:
        print("[error] no data downloaded")
        sys.exit(1)

    print("\n[merge] 月次CSVを統合...")
    all_rows = []
    for y, m, path in downloaded:
        rows = _zip_to_rows(path)
        all_rows.extend(rows)
        print(f"  {y:04d}-{m:02d}: {len(rows)} 行")
    print(f"  合計: {len(all_rows)} 行")

    cols = ["timestamp", "open", "high", "low", "close", "volume", "taker_buy_base"]
    df = pd.DataFrame(all_rows, columns=cols)
    df = df.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    print(f"  重複除去後: {len(df)} 行")
    _continuity_check(df)

    first = df["timestamp"].iloc[0][:10]
    last = df["timestamp"].iloc[-1][:10]
    out_name = f"BTCUSDT-1m-binance-taker-{first}_{last}.csv"
    out_path = OUT_DIR / out_name
    df.to_csv(out_path, index=False)
    print(f"\n→ {out_path}")
    print(f"   {len(df)} bars / {first} 〜 {last}")


if __name__ == "__main__":
    main()
