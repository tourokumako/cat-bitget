#!/usr/bin/env python3
"""
runner/fetch_ohlcv.py — Binance公開APIからBTCUSDT 5m OHLCVデータを取得

使い方:
  python3 runner/fetch_ohlcv.py                          # デフォルト: 365日
  python3 runner/fetch_ohlcv.py --days 365               # 365日
  python3 runner/fetch_ohlcv.py --start 2025-04-01 --end 2026-04-01

出力:
  data/BTCUSDT-5m-{start}_{end}_365d.csv  (既存CSVと同形式)

Binance public API (認証不要):
  GET https://api.binance.com/api/v3/klines
  limit: max 1000 bars/request
  rate limit: ~1200 req/min
"""
from __future__ import annotations

import argparse
import pathlib
import time
from datetime import datetime, timezone, timedelta

import pandas as pd
import json
import urllib.request
import urllib.parse

_ROOT    = pathlib.Path(__file__).resolve().parents[1]
_DATA    = _ROOT / "data"
_API_URL = "https://api.binance.com/api/v3/klines"
_SYMBOL  = "BTCUSDT"
_INTERVAL = "5m"
_LIMIT   = 1000          # Binance max per request
_SLEEP   = 0.12          # ~8 req/s (well within 1200/min limit)


def fetch_chunk(start_ms: int, end_ms: int) -> list[list]:
    """1リクエスト分（最大1000バー）を取得して返す"""
    params = urllib.parse.urlencode({
        "symbol":    _SYMBOL,
        "interval":  _INTERVAL,
        "startTime": start_ms,
        "endTime":   end_ms,
        "limit":     _LIMIT,
    })
    url = f"{_API_URL}?{params}"
    with urllib.request.urlopen(url, timeout=15) as resp:
        return json.loads(resp.read().decode())


def fetch_range(start_dt: datetime, end_dt: datetime) -> pd.DataFrame:
    """期間全体を複数リクエストに分割して取得"""
    start_ms = int(start_dt.timestamp() * 1000)
    end_ms   = int(end_dt.timestamp() * 1000)

    # 5m足: 1バー = 300_000ms
    bar_ms   = 300_000
    total_bars = (end_ms - start_ms) // bar_ms
    n_requests = (total_bars + _LIMIT - 1) // _LIMIT

    print(f"期間: {start_dt.date()} 〜 {end_dt.date()}")
    print(f"予想バー数: {total_bars:,}  リクエスト数: {n_requests}")
    print("取得開始...")

    all_rows: list[list] = []
    cur_ms = start_ms
    req_count = 0

    while cur_ms < end_ms:
        chunk = fetch_chunk(cur_ms, end_ms - 1)
        if not chunk:
            break
        all_rows.extend(chunk)
        req_count += 1

        last_ts = int(chunk[-1][0])
        cur_ms  = last_ts + bar_ms

        if req_count % 50 == 0:
            pct = (cur_ms - start_ms) / (end_ms - start_ms) * 100
            print(f"  {req_count}/{n_requests} req  {pct:.0f}%  {len(all_rows):,}バー取得済み")

        time.sleep(_SLEEP)

    print(f"完了: {req_count}リクエスト  {len(all_rows):,}バー取得")
    return _to_dataframe(all_rows)


def _to_dataframe(rows: list[list]) -> pd.DataFrame:
    """Binance klines レスポンスを既存CSVと同形式のDataFrameに変換"""
    df = pd.DataFrame(rows, columns=[
        "ts_ms", "open", "high", "low", "close", "volume",
        "_close_ts", "_qvol", "_trades", "_tbvol", "_tqvol", "_ignore"
    ])
    df = df[["ts_ms", "open", "high", "low", "close", "volume"]].copy()
    df["ts_ms"]  = df["ts_ms"].astype(int)
    df["open"]   = df["open"].astype(float)
    df["high"]   = df["high"].astype(float)
    df["low"]    = df["low"].astype(float)
    df["close"]  = df["close"].astype(float)
    df["volume"] = df["volume"].astype(float)

    # timestamp列: "YYYY-MM-DD HH:MM:SS" UTC（既存CSVと同形式）
    df["timestamp"] = pd.to_datetime(df["ts_ms"], unit="ms", utc=True) \
                        .dt.tz_localize(None) \
                        .dt.strftime("%Y-%m-%d %H:%M:%S")

    df = df[["timestamp", "open", "high", "low", "close", "volume"]]
    df = df.drop_duplicates("timestamp").sort_values("timestamp").reset_index(drop=True)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Binance BTCUSDT 5m OHLCV取得")
    parser.add_argument("--days",  type=int, default=365, help="取得日数（デフォルト: 365）")
    parser.add_argument("--start", type=str, default=None, help="開始日 YYYY-MM-DD (UTC)")
    parser.add_argument("--end",   type=str, default=None, help="終了日 YYYY-MM-DD (UTC, exclusive)")
    args = parser.parse_args()

    # 終了: 2026-04-01 00:00:00 UTC（既存CSVと同じ終端）
    if args.end:
        end_dt = datetime.strptime(args.end, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        end_dt = datetime(2026, 4, 1, 0, 0, 0, tzinfo=timezone.utc)

    if args.start:
        start_dt = datetime.strptime(args.start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        start_dt = end_dt - timedelta(days=args.days)

    # 出力ファイル名
    s_str = start_dt.strftime("%Y-%m-%d")
    e_str = (end_dt - timedelta(days=1)).strftime("%m-%d")
    days_actual = (end_dt - start_dt).days
    out_path = _DATA / f"BTCUSDT-5m-{s_str}_{e_str}_{days_actual}d.csv"

    df = fetch_range(start_dt, end_dt)

    # バー数・期間の最終確認
    first_ts = df["timestamp"].iloc[0]
    last_ts  = df["timestamp"].iloc[-1]
    print(f"\n取得結果: {first_ts} 〜 {last_ts}  ({len(df):,}バー)")

    df.to_csv(out_path, index=False)
    print(f"保存完了: {out_path}")
    print(f"ファイルサイズ: {out_path.stat().st_size / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
