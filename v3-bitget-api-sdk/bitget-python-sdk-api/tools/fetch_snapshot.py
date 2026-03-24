#!/usr/bin/env python3
"""
tools/fetch_snapshot.py — Bitget API から固定スナップショット CSV を生成

使い方:
    cd v3-bitget-api-sdk/bitget-python-sdk-api
    .venv/bin/python3 tools/fetch_snapshot.py

出力: tools/data/snapshot.csv（300 本 × 5m 足）
※ 一度生成したら再実行しない（Logic Parity は固定データで比較するため）
"""
from __future__ import annotations

import json
import pathlib
import sys

import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent   # tools/
REPO = HERE.parent                                # bitget-python-sdk-api/
sys.path.insert(0, str(REPO))

from runner.bitget_adapter import BitgetAdapter, load_keys  # noqa: E402

KEYS_PATH = REPO / "config" / "bitget_keys.json"
with open(KEYS_PATH) as f:
    keys_data = json.load(f)
paper_trading = bool(keys_data.get("paper_trading", True))
keys = load_keys(KEYS_PATH)

OUT = HERE / "data" / "snapshot.csv"

if OUT.exists():
    print(f"[INFO] 既に存在します: {OUT}")
    print("  上書きしたい場合は手動で削除してから再実行してください")
    sys.exit(0)

adapter = BitgetAdapter(keys, paper_trading=paper_trading)
print("[INFO] Bitget API から 5m 足 300 本を取得中 ...")
resp    = adapter.get_candles(product_type="USDT-FUTURES", symbol="BTCUSDT", granularity="5m", limit=300)
candles = resp["data"]

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
    if len(c) >= 5
]

df = pd.DataFrame(rows).sort_values("timestamp_ms").reset_index(drop=True)
OUT.parent.mkdir(exist_ok=True)
df.to_csv(OUT, index=False)
print(f"[OK] {len(df)} 本を保存しました: {OUT}")
print("     次回から snapshot_compare.py でこのCSVを使って比較できます")