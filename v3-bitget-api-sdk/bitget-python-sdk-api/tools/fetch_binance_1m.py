#!/usr/bin/env python3
"""
tools/fetch_binance_1m.py — Binance から 1分足を一括取得して CSV 保存
認証不要（公開エンドポイント）

使い方:
    cd v3-bitget-api-sdk/bitget-python-sdk-api
    .venv/bin/python3 tools/fetch_binance_1m.py [--days 180]

出力: data/BTCUSDT-1m-binance-{end_date}_{days}d.csv
"""
from __future__ import annotations

import argparse
import pathlib
import time
from datetime import datetime, timezone

import pandas as pd
import requests

REPO     = pathlib.Path(__file__).resolve().parent.parent
DATA_DIR = REPO / "data"

SYMBOL      = "BTCUSDT"
INTERVAL    = "1m"
LIMIT       = 1500          # Binance 最大
INTERVAL_MS = 60_000
SLEEP_S     = 0.1
URL         = "https://fapi.binance.com/fapi/v1/klines"


def fetch_all(days: int) -> pd.DataFrame:
    end_ms   = int(time.time() * 1000)
    start_ms = end_ms - days * 24 * 60 * 60 * 1000
    all_rows: list[dict] = []

    print(f"[INFO] {days}日分 ({days*24*60:,}本) を Binance から取得開始 ...")
    batch = 0

    cur_end = end_ms
    while cur_end > start_ms:
        resp = requests.get(URL, params={
            "symbol":   SYMBOL,
            "interval": INTERVAL,
            "endTime":  cur_end,
            "limit":    LIMIT,
        }, timeout=10)
        resp.raise_for_status()
        candles = resp.json()

        if not candles:
            break

        rows = [
            {
                "timestamp_ms": int(c[0]),
                "open":   float(c[1]),
                "high":   float(c[2]),
                "low":    float(c[3]),
                "close":  float(c[4]),
                "volume": float(c[5]),
            }
            for c in candles
        ]
        all_rows.extend(rows)

        oldest_ms = min(r["timestamp_ms"] for r in rows)
        cur_end   = oldest_ms - INTERVAL_MS

        batch += 1
        if batch % 20 == 0:
            pct = (1 - (cur_end - start_ms) / (days * 24 * 60 * 60 * 1000)) * 100
            print(f"  [{batch}] 取得済み: {len(all_rows):,}本 ({pct:.0f}%)")

        time.sleep(SLEEP_S)

        if oldest_ms <= start_ms:
            break

    df = pd.DataFrame(all_rows)
    df = df[df["timestamp_ms"] >= start_ms]
    df = df.sort_values("timestamp_ms").drop_duplicates("timestamp_ms").reset_index(drop=True)
    return df


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=180)
    args = parser.parse_args()

    df = fetch_all(args.days)

    DATA_DIR.mkdir(exist_ok=True)
    end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out = DATA_DIR / f"BTCUSDT-1m-binance-{end_date}_{args.days}d.csv"
    df.to_csv(out, index=False)

    print(f"[OK] {len(df):,}本 → {out}")
    print(f"     期間: {pd.to_datetime(df['timestamp_ms'].min(), unit='ms', utc=True)} 〜 "
          f"{pd.to_datetime(df['timestamp_ms'].max(), unit='ms', utc=True)}")


if __name__ == "__main__":
    main()
