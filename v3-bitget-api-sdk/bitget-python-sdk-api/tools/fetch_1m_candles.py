#!/usr/bin/env python3
"""
tools/fetch_1m_candles.py — Bitget から 1分足を一括取得して CSV 保存

使い方:
    cd v3-bitget-api-sdk/bitget-python-sdk-api
    .venv/bin/python3 tools/fetch_1m_candles.py [--days 180]

出力: data/BTCUSDT-1m-{end_date}_{days}d.csv
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO))

from runner.bitget_adapter import BitgetAdapter, load_keys

KEYS_PATH = REPO / "config" / "bitget_keys.json"
DATA_DIR  = REPO / "data"

SYMBOL       = "BTCUSDT"
PRODUCT_TYPE = "USDT-FUTURES"
GRANULARITY  = "1m"
LIMIT        = 1000
INTERVAL_MS  = 60_000          # 1分 = 60,000ms
SLEEP_S      = 0.1             # rate limit 対策（20 req/s）


def fetch_all(adapter: BitgetAdapter, days: int) -> pd.DataFrame:
    end_ms   = int(time.time() * 1000)
    start_ms = end_ms - days * 24 * 60 * 60 * 1000
    all_rows: list[dict] = []

    total_needed = days * 24 * 60
    print(f"[INFO] {days}日分 ({total_needed:,}本) を取得開始 ...")
    batch = 0

    while end_ms > start_ms:
        resp = adapter.api._request_with_params(
            "GET",
            "/api/v2/mix/market/candles",
            {
                "productType": PRODUCT_TYPE,
                "symbol":      SYMBOL,
                "granularity": GRANULARITY,
                "limit":       str(LIMIT),
                "endTime":     str(end_ms),
            },
        )
        if resp.get("code") != "00000":
            raise RuntimeError(f"candles failed: {resp}")

        candles = resp.get("data") or []
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
            for c in candles if len(c) >= 6
        ]
        all_rows.extend(rows)

        oldest_ms = min(r["timestamp_ms"] for r in rows)
        end_ms    = oldest_ms - INTERVAL_MS  # 重複しないよう1本前へ

        batch += 1
        if batch % 20 == 0:
            elapsed_ms = days * 24 * 60 * 60 * 1000 - (end_ms - start_ms)
            pct = elapsed_ms / (days * 24 * 60 * 60 * 1000) * 100
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

    with open(KEYS_PATH) as f:
        keys_data = json.load(f)
    paper_trading = bool(keys_data.get("paper_trading", True))
    keys = load_keys(KEYS_PATH)
    adapter = BitgetAdapter(keys, paper_trading=paper_trading)

    df = fetch_all(adapter, args.days)

    DATA_DIR.mkdir(exist_ok=True)
    from datetime import datetime, timezone
    end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out = DATA_DIR / f"BTCUSDT-1m-{end_date}_{args.days}d.csv"
    df.to_csv(out, index=False)

    print(f"[OK] {len(df):,}本 → {out}")
    print(f"     期間: {pd.to_datetime(df['timestamp_ms'].min(), unit='ms', utc=True)} 〜 "
          f"{pd.to_datetime(df['timestamp_ms'].max(), unit='ms', utc=True)}")


if __name__ == "__main__":
    main()
