"""Bitget の Funding Rate / Open Interest / L-S Ratio の過去取得APIを試験。

目的: 5年分(2020-2024)のデータが無料で取得可能か検証。
取得不可 / 期間不足なら別ソース(Coinglass無料枠等)に切り替え判断する。

検証内容:
  1. 直近1週間の funding rate 取得（API疎通確認）
  2. 取得可能な最古日時を確認（5年遡れるか）
  3. OI / L-S Ratio エンドポイントも同様に確認

無認証で叩けるpublic endpointのみ使用（API Key不要）。
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone

import urllib.request

BASE = "https://api.bitget.com"
SYMBOL = "BTCUSDT"
PRODUCT = "USDT-FUTURES"


def fetch(path: str, params: dict) -> dict:
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{BASE}{path}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": "phase4-test"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def to_ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


def test_funding():
    print("=" * 60)
    print("[1] Funding Rate History")
    print("=" * 60)
    # 直近100件（仕様: pageSize最大100）
    res = fetch("/api/v2/mix/market/history-fund-rate", {
        "symbol": SYMBOL,
        "productType": PRODUCT,
        "pageSize": 100,
    })
    if res.get("code") != "00000":
        print(f"❌ FAIL code={res.get('code')} msg={res.get('msg')}")
        return None
    data = res.get("data", [])
    print(f"✅ 取得成功: {len(data)} 件")
    if data:
        first = data[0]
        last = data[-1]
        first_ts = datetime.fromtimestamp(int(first.get("fundingTime", 0)) / 1000, tz=timezone.utc)
        last_ts = datetime.fromtimestamp(int(last.get("fundingTime", 0)) / 1000, tz=timezone.utc)
        print(f"   最新: {first_ts}  rate={first.get('fundingRate')}")
        print(f"   最古: {last_ts}  rate={last.get('fundingRate')}")
        print(f"   サンプル: {data[0]}")
    return data


def test_funding_old(target_dt: datetime):
    print(f"\n[1b] Funding Rate History（{target_dt.isoformat()} 周辺取得試行）")
    res = fetch("/api/v2/mix/market/history-fund-rate", {
        "symbol": SYMBOL,
        "productType": PRODUCT,
        "pageSize": 100,
        "endTime": to_ms(target_dt),
    })
    if res.get("code") != "00000":
        print(f"   ❌ code={res.get('code')} msg={res.get('msg')}")
        return None
    data = res.get("data", [])
    print(f"   取得 {len(data)} 件")
    if data:
        first = data[0]
        last = data[-1]
        first_ts = datetime.fromtimestamp(int(first.get("fundingTime", 0)) / 1000, tz=timezone.utc)
        last_ts = datetime.fromtimestamp(int(last.get("fundingTime", 0)) / 1000, tz=timezone.utc)
        print(f"   範囲: {last_ts} 〜 {first_ts}")
    return data


def test_open_interest():
    print("\n" + "=" * 60)
    print("[2] Open Interest")
    print("=" * 60)
    # 現在値
    res = fetch("/api/v2/mix/market/open-interest", {
        "symbol": SYMBOL,
        "productType": PRODUCT,
    })
    print(f"現在OI: code={res.get('code')}")
    if res.get("code") == "00000":
        print(f"   data={res.get('data')}")
    else:
        print(f"   msg={res.get('msg')}")


def test_oi_history():
    print("\n[2b] Open Interest 履歴試行")
    # 試すエンドポイント候補
    candidates = [
        "/api/v2/mix/market/history-open-interest",
        "/api/v2/mix/market/open-interest-period",
        "/api/v2/mix/market/oi-history",
    ]
    for path in candidates:
        try:
            res = fetch(path, {
                "symbol": SYMBOL,
                "productType": PRODUCT,
                "granularity": "1H",
                "limit": 100,
            })
            print(f"   {path}  code={res.get('code')}")
            if res.get("code") == "00000":
                d = res.get("data", [])
                print(f"   ✅ 取得 {len(d) if isinstance(d, list) else 'dict'} 件")
                if isinstance(d, list) and d:
                    print(f"   サンプル: {d[0]}")
                return d
        except Exception as e:
            print(f"   {path}  EXC: {e}")
    return None


def test_long_short():
    print("\n" + "=" * 60)
    print("[3] Long/Short Ratio")
    print("=" * 60)
    candidates = [
        "/api/v2/mix/market/account-long-short",
        "/api/v2/mix/market/position-long-short",
        "/api/v2/mix/market/long-short-ratio",
        "/api/v2/mix/market/account-ratio",
    ]
    for path in candidates:
        try:
            res = fetch(path, {
                "symbol": SYMBOL,
                "productType": PRODUCT,
                "period": "1h",
                "limit": 100,
            })
            print(f"   {path}  code={res.get('code')}")
            if res.get("code") == "00000":
                d = res.get("data", [])
                print(f"   ✅ 取得 {len(d) if isinstance(d, list) else 'dict'} 件")
                if isinstance(d, list) and d:
                    print(f"   サンプル: {d[0]}")
                return d
        except Exception as e:
            print(f"   {path}  EXC: {e}")
    return None


def main():
    # 1. Funding Rate 直近
    funding = test_funding()

    # 1b. 5年前(2020-01-01) 取得試行
    if funding:
        time.sleep(0.5)
        old = test_funding_old(datetime(2020, 6, 1, tzinfo=timezone.utc))
        if old:
            time.sleep(0.5)
            very_old = test_funding_old(datetime(2020, 1, 31, tzinfo=timezone.utc))

    # 2. Open Interest
    test_open_interest()
    time.sleep(0.5)
    test_oi_history()

    # 3. Long/Short Ratio
    test_long_short()

    print("\n" + "=" * 60)
    print("検証完了")
    print("=" * 60)


if __name__ == "__main__":
    main()
