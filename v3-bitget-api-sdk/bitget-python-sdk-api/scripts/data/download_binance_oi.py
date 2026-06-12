"""Binance USDT-M futures の OI / L-S 比 5分足 履歴を取得→CSV保存（E28 Step2）。

source: https://data.binance.vision/data/futures/um/daily/metrics/BTCUSDT/BTCUSDT-metrics-YYYY-MM-DD.zip
  列: create_time, symbol, sum_open_interest, sum_open_interest_value,
      count_toptrader_long_short_ratio, sum_toptrader_long_short_ratio,
      count_long_short_ratio, sum_taker_long_short_vol_ratio（5分粒度）
期間: 2021-04-01 〜 2024-12-31（価格5m と FR の学習期間に合わせる）

出力: data/oi_BTCUSDT_5y.csv（time, oi_btc, oi_usd, ls_global, ls_toptrader, taker_ls）
無認証 public archive。価格=Binance spot proxy ／ OI=Binance futures（市場全体のセンチメント代理・microstructure）。
"""
from __future__ import annotations
import io
import time
import urllib.error
import urllib.request
import zipfile
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_PATH = REPO_ROOT / "data" / "oi_BTCUSDT_5y.csv"
BASE = "https://data.binance.vision/data/futures/um/daily/metrics/BTCUSDT"
START = date(2021, 4, 1)
END = date(2024, 12, 31)


def fetch_day(d: date):
    url = f"{BASE}/BTCUSDT-metrics-{d.isoformat()}.zip"
    req = urllib.request.Request(url, headers={"User-Agent": "oi-dl"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
    z = zipfile.ZipFile(io.BytesIO(raw))
    with z.open(z.namelist()[0]) as f:
        return pd.read_csv(f)


def main():
    rows = []
    missing = 0
    d = START
    i = 0
    while d <= END:
        try:
            df = fetch_day(d)
            rows.append(df)
        except urllib.error.HTTPError as e:
            missing += 1
            if e.code != 404:
                print(f"  [{d}] HTTP {e.code}")
        except Exception as e:
            missing += 1
            print(f"  [{d}] {type(e).__name__} {e}")
        i += 1
        if i % 60 == 0:
            got = sum(len(x) for x in rows)
            print(f"  [{d}] 累計 {got:,} 行 / 欠 {missing}", flush=True)
        d += timedelta(days=1)
        time.sleep(0.05)

    if not rows:
        print("❌ 取得ゼロ")
        return
    all_df = pd.concat(rows, ignore_index=True)
    out = pd.DataFrame({
        "time": pd.to_datetime(all_df["create_time"]),
        "oi_btc": pd.to_numeric(all_df["sum_open_interest"], errors="coerce"),
        "oi_usd": pd.to_numeric(all_df["sum_open_interest_value"], errors="coerce"),
        "ls_global": pd.to_numeric(all_df["count_long_short_ratio"], errors="coerce"),
        "ls_toptrader": pd.to_numeric(all_df["sum_toptrader_long_short_ratio"], errors="coerce"),
        "taker_ls": pd.to_numeric(all_df["sum_taker_long_short_vol_ratio"], errors="coerce"),
    })
    out = out.dropna(subset=["oi_btc"]).drop_duplicates(subset=["time"]).sort_values("time").reset_index(drop=True)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_PATH, index=False)
    print(f"\n取得完了: {len(out):,} 行（{out.time.min()} 〜 {out.time.max()}）欠損日 {missing}")
    print(f"  OI(BTC) 範囲: {out.oi_btc.min():,.0f} 〜 {out.oi_btc.max():,.0f}")
    print(f"  → {OUT_PATH}")


if __name__ == "__main__":
    main()
