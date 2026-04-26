"""Binance Futures Funding Rate 過去5年分（2020-01-01〜2024-12-31）を取得→CSV保存。

API: GET https://fapi.binance.com/fapi/v1/fundingRate
  - limit max 1000, startTime/endTime 指定可能
  - BTCUSDT は 2019-09-10 開始、8時間ごと

出力: data/funding_rate_BTCUSDT_5y.csv
  カラム: funding_time(UTC) / funding_rate
"""
from __future__ import annotations

import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = REPO_ROOT / "data" / "funding_rate_BTCUSDT_5y.csv"

BASE = "https://fapi.binance.com"
SYMBOL = "BTCUSDT"
START_DT = datetime(2020, 1, 1, tzinfo=timezone.utc)
END_DT   = datetime(2025, 1, 1, tzinfo=timezone.utc)


def fetch(start_ms: int) -> list[dict]:
    qs = f"symbol={SYMBOL}&startTime={start_ms}&limit=1000"
    url = f"{BASE}/fapi/v1/fundingRate?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": "phase4-dl"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def main() -> None:
    start_ms = int(START_DT.timestamp() * 1000)
    end_ms   = int(END_DT.timestamp() * 1000)
    all_rows = []

    cursor = start_ms
    iter_count = 0
    while cursor < end_ms:
        chunk = fetch(cursor)
        if not chunk:
            print(f"  [stop] empty chunk at cursor={cursor}")
            break
        all_rows.extend(chunk)
        last_ts = chunk[-1]["fundingTime"]
        last_dt = datetime.fromtimestamp(last_ts / 1000, tz=timezone.utc)
        iter_count += 1
        print(f"  [{iter_count}] +{len(chunk)} rows  last={last_dt}")
        if last_ts <= cursor:
            break
        cursor = last_ts + 1
        time.sleep(0.3)
        if last_ts >= end_ms:
            break

    print(f"\n取得完了: {len(all_rows)} 件")

    df = pd.DataFrame(all_rows)
    df["funding_time"] = pd.to_datetime(df["fundingTime"].astype(int), unit="ms", utc=True)
    df["funding_rate"] = df["fundingRate"].astype(float)
    df = df[["funding_time", "funding_rate"]].sort_values("funding_time")

    # 期間でフィルタ
    df = df[(df["funding_time"] >= START_DT) & (df["funding_time"] < END_DT)].reset_index(drop=True)
    df = df.drop_duplicates(subset=["funding_time"]).reset_index(drop=True)

    print(f"フィルタ後: {len(df)} 件 ({df['funding_time'].min()} 〜 {df['funding_time'].max()})")
    print(f"  期待値: 5年 × 365日 × 3回/日 ≈ 5475件")
    print(f"\nfunding_rate 統計:")
    print(df["funding_rate"].describe().round(6))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)
    print(f"\n→ {OUT_PATH}")


if __name__ == "__main__":
    main()
