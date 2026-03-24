#!/usr/bin/env python3
"""
tools/snapshot_compare.py — Logic Parity B: 原本 vs 移植版 エントリー判断比較

使い方:
    cd v3-bitget-api-sdk/bitget-python-sdk-api
    .venv/bin/python3 tools/snapshot_compare.py

CSV入力 (tools/data/snapshot.csv):
    timestamp_ms,open,high,low,close,volume
    ※ 最低 200 本以上を推奨 (RCI52 のウォームアップ確保)

比較方法:
    1. 同一 CSV を原本 (CAT_v9_regime.preprocess) と
       移植版 (cat_v9_decider.preprocess) でそれぞれ前処理する
    2. bar WARMUP〜末尾の各バーで check_entry_priority(i, df, params) を呼ぶ
    3. 両者の戻り値 (priority: int | None) が一致するか確認する
    ※ ローリング窓は後ろ方向参照なし → 全体 1 回の前処理で比較可能
"""
from __future__ import annotations

import json
import pathlib
import sys
from collections import Counter

import importlib.util
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# パス設定
# ---------------------------------------------------------------------------
HERE = pathlib.Path(__file__).resolve().parent           # tools/
REPO = HERE.parent                                        # bitget-python-sdk-api/
ORIG_PATH = pathlib.Path(
    "/Users/tachiharamasako/Documents/GitHub/cat-swing-sniper"
    "/strategies/CAT_v9_regime.py"
)

sys.path.insert(0, str(REPO))
import strategies.cat_v9_decider as ported  # noqa: E402

if not ORIG_PATH.exists():
    print(f"[ERROR] 原本が見つかりません: {ORIG_PATH}")
    sys.exit(1)

spec = importlib.util.spec_from_file_location("cat_v9_regime_orig", ORIG_PATH)
orig = importlib.util.module_from_spec(spec)
spec.loader.exec_module(orig)  # type: ignore

# ---------------------------------------------------------------------------
# パラメータ (cat_params_v9.json が正本)
# ---------------------------------------------------------------------------
PARAMS_PATH = REPO / "config" / "cat_params_v9.json"
with open(PARAMS_PATH) as f:
    params = json.load(f)

# ---------------------------------------------------------------------------
# データ読み込み
# ---------------------------------------------------------------------------
CSV_PATH = HERE / "data" / "snapshot.csv"
if not CSV_PATH.exists():
    print(f"[ERROR] CSVが見つかりません: {CSV_PATH}")
    print("  先に tools/fetch_snapshot.py を実行してCSVを生成してください")
    sys.exit(1)

raw = pd.read_csv(CSV_PATH)
raw["timestamp"] = pd.to_datetime(raw["timestamp_ms"].astype(int), unit="ms")
df_raw = raw[["timestamp", "open", "high", "low", "close", "volume"]].copy()
df_raw = df_raw.sort_values("timestamp").reset_index(drop=True)

WARMUP = 100  # RCI(52) + BB(20) + ADX(14) のウォームアップ
if len(df_raw) < WARMUP + 10:
    print(f"[ERROR] データが不足しています: {len(df_raw)} 本 (最低 {WARMUP + 10} 本必要)")
    sys.exit(1)

print(f"[INFO] データ   : {len(df_raw)} 本")
print(f"[INFO] テスト   : bar {WARMUP}〜{len(df_raw) - 1}  ({len(df_raw) - WARMUP} バー)")
print(f"[INFO] params   : {PARAMS_PATH.name}")
print(f"[INFO] 原本     : {ORIG_PATH.name}")
print()

# ---------------------------------------------------------------------------
# 前処理（各版で 1 回だけ実行）
# ---------------------------------------------------------------------------
print("[STEP 1] 原本 preprocess ...", end=" ", flush=True)
orig_df = orig.preprocess(df_raw.copy(), params)
print("done")

print("[STEP 2] 移植版 preprocess ...", end=" ", flush=True)
ported_df = ported.preprocess(df_raw.copy(), params)
print("done")
print()

# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------
def _label(p: int | None) -> str:
    if p is None:
        return "NOOP"
    side = "LONG" if p in (2, 4) else "SHORT"
    return f"P{p}({side})"


# ---------------------------------------------------------------------------
# 比較ループ
# ---------------------------------------------------------------------------
mismatches: list[tuple] = []

for i in range(WARMUP, len(df_raw)):
    orig_p   = orig.check_entry_priority(i, orig_df,    params)
    ported_p = ported.check_entry_priority(i, ported_df, params)

    if orig_p != ported_p:
        ts = df_raw.at[i, "timestamp"]
        mismatches.append((i, ts, orig_p, ported_p))
        print(f"[MISMATCH] bar={i:4d}  {ts}  "
              f"原本={_label(orig_p):<14}  移植={_label(ported_p)}")

# ---------------------------------------------------------------------------
# サマリー
# ---------------------------------------------------------------------------
total   = len(df_raw) - WARMUP
matched = total - len(mismatches)

print()
print("=" * 60)
print(f"[SUMMARY] 比較バー数 : {total}")
print(f"  MATCH    : {matched:4d}  ({matched / total * 100:.1f}%)")
print(f"  MISMATCH : {len(mismatches):4d}  ({len(mismatches) / total * 100:.1f}%)")

if not mismatches:
    print()
    print("[RESULT] ✅ 全バー一致 — Logic Parity B 合格")
else:
    print()
    print("[RESULT] ❌ 不一致あり — 修正が必要")
    pairs = Counter((o, p) for _, _, o, p in mismatches)
    print("  不一致の内訳:")
    for (o, p), cnt in pairs.most_common():
        print(f"    原本={_label(o):<14}  vs  移植={_label(p):<14}: {cnt} 件")

print("=" * 60)