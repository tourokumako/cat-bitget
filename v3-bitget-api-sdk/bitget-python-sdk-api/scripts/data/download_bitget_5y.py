"""download_bitget_5y.py — Bitget USDT-FUTURES 5m × 5y 取得

期間: TRAIN 2021-04-01〜2024-12-31 + 仮 test 2025 + 本 test 2026 Q1
source: https://api.bitget.com/api/v2/mix/market/history-candles

仕様:
  - max 200 bar/req
  - 約 8 req/s (rate limit 10 req/s から safety margin)
  - 取得時間 約 5-7 分

出力: data/BTCUSDT-5m-bitget-2021-04-01_2026-03-31_5y.csv
"""

import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_CSV = REPO_ROOT / "data" / "BTCUSDT-5m-bitget-2021-04-01_2026-03-31_5y.csv"
BINANCE_CSV = REPO_ROOT / "data" / "BTCUSDT-5m-2021-04-01_03-31_1826d.csv"

BASE = "https://api.bitget.com"
ENDPOINT = "/api/v2/mix/market/history-candles"
SYMBOL = "BTCUSDT"
PRODUCT_TYPE = "USDT-FUTURES"
GRANULARITY = "5m"
LIMIT = 200
SLEEP_BETWEEN_REQS = 0.12
MAX_RETRIES = 3

START = pd.Timestamp("2021-04-01 00:00:00")
END = pd.Timestamp("2026-03-31 23:55:00")


def fetch_with_retry(end_time_ms: int) -> list:
    params = {
        "symbol": SYMBOL,
        "productType": PRODUCT_TYPE,
        "granularity": GRANULARITY,
        "endTime": str(end_time_ms),
        "limit": str(LIMIT),
    }
    url = BASE + ENDPOINT + "?" + urllib.parse.urlencode(params)
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "phase0-bitget-5y/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                payload = json.loads(r.read())
            if payload.get("code") != "00000":
                raise RuntimeError(f"API code={payload.get('code')} msg={payload.get('msg')}")
            return payload.get("data", [])
        except Exception as e:
            last_err = e
            wait = 2 ** attempt
            print(f"  retry {attempt+1}/{MAX_RETRIES}: {e} (wait {wait}s)", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"failed after {MAX_RETRIES}: {last_err}")


def download_all() -> list:
    all_rows = []
    cur_end_ms = int(END.timestamp() * 1000) + 60_000
    start_ms = int(START.timestamp() * 1000)
    n_req = 0
    t0 = time.time()
    while cur_end_ms > start_ms:
        rows = fetch_with_retry(cur_end_ms)
        n_req += 1
        if not rows:
            print(f"  end_time={pd.Timestamp(cur_end_ms, unit='ms')} で 0 rows → 取得完了", flush=True)
            break
        all_rows.extend(rows)
        # Bitget レスポンスは ascending (古→新) 順: rows[0]=oldest, rows[-1]=newest
        oldest_ms = int(rows[0][0])
        if n_req % 50 == 0:
            elapsed = time.time() - t0
            print(f"  [{n_req}] oldest={pd.Timestamp(oldest_ms, unit='ms')} total={len(all_rows)} elapsed={elapsed:.0f}s", flush=True)
        if oldest_ms <= start_ms:
            break
        cur_end_ms = oldest_ms
        time.sleep(SLEEP_BETWEEN_REQS)
    print(f"  done: {n_req} reqs / {len(all_rows)} rows / {time.time()-t0:.0f}s", flush=True)
    return all_rows


def to_dataframe(rows: list) -> pd.DataFrame:
    cols = ["timestamp_ms", "open", "high", "low", "close", "volume_base", "volume_quote"]
    df = pd.DataFrame(rows, columns=cols)
    df["timestamp_ms"] = df["timestamp_ms"].astype("int64")
    for c in ["open", "high", "low", "close", "volume_base"]:
        df[c] = df[c].astype(float)
    df["timestamp"] = pd.to_datetime(df["timestamp_ms"], unit="ms")
    df = df[["timestamp", "open", "high", "low", "close", "volume_base"]].rename(
        columns={"volume_base": "volume"}
    )
    df = df.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    df = df[(df["timestamp"] >= START) & (df["timestamp"] <= END)].reset_index(drop=True)
    return df


def verify_integrity(df: pd.DataFrame) -> dict:
    issues = []
    expected = int((END - START).total_seconds() / 300) + 1
    n = len(df)
    if abs(n - expected) > expected * 0.01:
        issues.append(f"bar数: 期待 {expected} vs 実 {n} (誤差 {abs(n-expected)/expected*100:.2f}%)")
    diffs = df["timestamp"].diff().dropna()
    expected_td = pd.Timedelta("5min")
    irregular = (diffs != expected_td).sum()
    if irregular > 0:
        max_gap = diffs.max()
        issues.append(f"非連続 bar: {irregular} 件 (最大ギャップ: {max_gap})")
    dup = df["timestamp"].duplicated().sum()
    if dup > 0:
        issues.append(f"重複 timestamp: {dup} 件")
    for col in ["open", "high", "low", "close"]:
        n_nan = df[col].isna().sum()
        n_zero = (df[col] == 0).sum()
        if n_nan > 0 or n_zero > 0:
            issues.append(f"{col}: NaN={n_nan}, zero={n_zero}")
    return {"n_rows": n, "expected": expected, "issues": issues}


def verify_vs_binance(df_btg: pd.DataFrame) -> dict:
    if not BINANCE_CSV.exists():
        return {"skipped": "Binance CSV not found"}
    df_bnc = pd.read_csv(BINANCE_CSV, parse_dates=["timestamp"])
    df_btg2 = df_btg.set_index("timestamp").sort_index()
    df_bnc = df_bnc.set_index("timestamp").sort_index()
    common = df_btg2.index.intersection(df_bnc.index)
    if len(common) == 0:
        return {"skipped": "no common timestamps"}
    m = df_btg2.loc[common].join(df_bnc.loc[common], lsuffix="_btg", rsuffix="_bnc")
    close_mae_rel = ((m["close_btg"] - m["close_bnc"]).abs() / m["close_bnc"]).median() * 100
    wick_high_rel = ((m["high_btg"] - m["high_bnc"]).abs() / m["close_bnc"]) * 100
    wick_low_rel = ((m["low_btg"] - m["low_bnc"]).abs() / m["close_bnc"]) * 100
    wick_max = pd.concat([wick_high_rel, wick_low_rel], axis=1).max(axis=1)
    p95 = wick_max.quantile(0.95)
    issues = []
    if close_mae_rel > 0.05:
        issues.append(f"close 中央値 MAE = {close_mae_rel:.4f}% > 0.05%")
    if p95 > 0.5:
        issues.append(f"wick p95 = {p95:.4f}% > 0.5%")
    return {
        "common_bars": len(common),
        "close_med_MAE_rel_pct": close_mae_rel,
        "wick_p95_rel_pct": p95,
        "issues": issues,
    }


def main() -> int:
    print(f"[start] {datetime.now(timezone.utc).isoformat()}")
    print(f"  期間: {START} → {END}")
    print(f"  output: {OUT_CSV.relative_to(REPO_ROOT)}")
    print()

    print("[download]")
    rows = download_all()

    print()
    print("[parse]")
    df = to_dataframe(rows)
    print(f"  parsed: {len(df)} rows  {df['timestamp'].min()} → {df['timestamp'].max()}")

    print()
    print("[verify integrity]")
    integ = verify_integrity(df)
    print(f"  bar数: 期待 {integ['expected']} / 実 {integ['n_rows']}")
    if integ["issues"]:
        print(f"  ⚠️ ISSUES ({len(integ['issues'])}):")
        for x in integ["issues"]:
            print(f"    - {x}")
    else:
        print(f"  ✅ 整合性 verify 全通過")

    print()
    print("[verify vs Binance]")
    bnc = verify_vs_binance(df)
    if "skipped" in bnc:
        print(f"  skipped: {bnc['skipped']}")
    else:
        print(f"  共通 bars: {bnc['common_bars']}")
        print(f"  close 中央値 MAE: {bnc['close_med_MAE_rel_pct']:.4f}%")
        print(f"  wick p95:         {bnc['wick_p95_rel_pct']:.4f}%")
        if bnc["issues"]:
            print(f"  ⚠️ ISSUES:")
            for x in bnc["issues"]:
                print(f"    - {x}")
        else:
            print(f"  ✅ Binance 重ね合わせ verify 通過")

    print()
    print("[save]")
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    print(f"  saved: {OUT_CSV.relative_to(REPO_ROOT)} ({OUT_CSV.stat().st_size / 1e6:.1f} MB)")

    print()
    print(f"[end] {datetime.now(timezone.utc).isoformat()}")
    return 1 if (integ["issues"] or bnc.get("issues") or []) else 0


if __name__ == "__main__":
    sys.exit(main())
