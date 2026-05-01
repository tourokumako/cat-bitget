"""Binance Futures API: Funding/OI/Long-Short の過去取得可能範囲を検証。

確認内容:
  1. Funding Rate の最古取得日時（2019/9 開始の全期間取れるか）
  2. Open Interest Stats の制限（30日制限か全期間か）
  3. Long/Short Ratio (account / top trader) の制限
  4. レート制限の体感
"""
from __future__ import annotations

import json
import time
import urllib.request
from datetime import datetime, timezone

BASE = "https://fapi.binance.com"
SYMBOL = "BTCUSDT"


def fetch(path: str, params: dict) -> dict:
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{BASE}{path}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": "phase4-binance"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def fmt_ts(ms: int) -> str:
    return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).isoformat()


def test_funding():
    print("=" * 60)
    print("[1] Funding Rate History  /fapi/v1/fundingRate")
    print("=" * 60)
    # 直近100件
    res = fetch("/fapi/v1/fundingRate", {"symbol": SYMBOL, "limit": 100})
    print(f"   直近100件取得: {len(res)} 件")
    if res:
        print(f"   最古: {fmt_ts(res[0]['fundingTime'])}  rate={res[0]['fundingRate']}")
        print(f"   最新: {fmt_ts(res[-1]['fundingTime'])}  rate={res[-1]['fundingRate']}")

    # 2019-09-08 (BTCUSDT Perp 開始日付近) を狙う
    start_ms = int(datetime(2019, 9, 8, tzinfo=timezone.utc).timestamp() * 1000)
    res2 = fetch("/fapi/v1/fundingRate", {
        "symbol": SYMBOL, "startTime": start_ms, "limit": 1000,
    })
    print(f"\n   2019-09-08 起点で取得: {len(res2)} 件")
    if res2:
        print(f"   最古: {fmt_ts(res2[0]['fundingTime'])}")
        print(f"   最新: {fmt_ts(res2[-1]['fundingTime'])}")
        # 推定取得可能範囲
        return res2[0]['fundingTime']
    return None


def test_oi_hist():
    print("\n" + "=" * 60)
    print("[2] Open Interest Stats  /futures/data/openInterestHist")
    print("=" * 60)
    # 直近 limit=30 で試行
    res = fetch("/futures/data/openInterestHist", {
        "symbol": SYMBOL, "period": "1h", "limit": 30,
    })
    print(f"   直近30件取得: {len(res)} 件")
    if res:
        print(f"   最古: {fmt_ts(res[0]['timestamp'])}  OI={res[0]['sumOpenInterest']}")
        print(f"   最新: {fmt_ts(res[-1]['timestamp'])}  OI={res[-1]['sumOpenInterest']}")

    # 2020-01-01 起点で試す（古いデータが取れるか）
    start_ms = int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
    res2 = fetch("/futures/data/openInterestHist", {
        "symbol": SYMBOL, "period": "1h", "startTime": start_ms, "limit": 500,
    })
    print(f"\n   2020-01-01 起点で取得: {len(res2)} 件")
    if res2:
        print(f"   最古: {fmt_ts(res2[0]['timestamp'])}")
        print(f"   最新: {fmt_ts(res2[-1]['timestamp'])}")

    # 90日前を狙う
    days_ago_ms = int((time.time() - 90 * 86400) * 1000)
    res3 = fetch("/futures/data/openInterestHist", {
        "symbol": SYMBOL, "period": "1h", "startTime": days_ago_ms, "limit": 500,
    })
    print(f"\n   90日前起点: {len(res3)} 件")
    if res3:
        print(f"   最古: {fmt_ts(res3[0]['timestamp'])}")
        print(f"   最新: {fmt_ts(res3[-1]['timestamp'])}")


def test_long_short():
    print("\n" + "=" * 60)
    print("[3] Long/Short Ratio")
    print("=" * 60)
    endpoints = [
        ("globalLongShortAccountRatio", "/futures/data/globalLongShortAccountRatio"),
        ("topLongShortAccountRatio",    "/futures/data/topLongShortAccountRatio"),
        ("topLongShortPositionRatio",   "/futures/data/topLongShortPositionRatio"),
    ]
    for name, path in endpoints:
        res = fetch(path, {"symbol": SYMBOL, "period": "1h", "limit": 30})
        print(f"\n   [{name}]  {len(res)} 件")
        if res:
            print(f"     最古: {fmt_ts(res[0]['timestamp'])}  sample={res[0]}")

    # 古いデータが取れるか確認
    start_ms = int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
    res = fetch("/futures/data/globalLongShortAccountRatio", {
        "symbol": SYMBOL, "period": "1h", "startTime": start_ms, "limit": 500,
    })
    print(f"\n   古いデータ取得試行(globalLongShortAccountRatio・2020-01-01起点): {len(res)} 件")
    if res:
        print(f"     最古: {fmt_ts(res[0]['timestamp'])}")
        print(f"     最新: {fmt_ts(res[-1]['timestamp'])}")


def main():
    test_funding()
    time.sleep(0.5)
    test_oi_hist()
    time.sleep(0.5)
    test_long_short()


if __name__ == "__main__":
    main()
