"""
Phase 0 v3 max_ts_verify — high/low ベース独立再計算で公式 label_stats.csv と整合確認
生成物: results/priority_rebuild/phase0_v3_stats/max_ts_verify.json
"""

import json
import sys
from pathlib import Path

import pandas as pd

# ── パス定義 ──────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
PARQ = ROOT / "results/priority_rebuild/labels_mfe_mae_pct_train_2021_2024.parquet"
CSV  = ROOT / "data/BTCUSDT-5m-bitget-2021-04-01_2026-03-31_5y.csv"
OUT  = ROOT / "results/priority_rebuild/phase0_v3_stats/max_ts_verify.json"

K = 288  # 検証対象の K 値

# ── ① parquet 読み込み ────────────────────────────────────
print("=== [1] parquet 読み込み ===")
df = pd.read_parquet(PARQ, columns=["close", "LONG_MFE_pct_K288", "LONG_MAE_pct_K288"])
df = df.reset_index().rename(columns={"timestamp": "ts"})
print(f"  rows={len(df)}, ts_range={df['ts'].iloc[0]} ~ {df['ts'].iloc[-1]}")

# ── ② idxmax 取得 ─────────────────────────────────────────
print("=== [2] idxmax 取得 ===")
idx_mfe = df["LONG_MFE_pct_K288"].idxmax()
idx_mae = df["LONG_MAE_pct_K288"].idxmax()

ts_mfe   = df.loc[idx_mfe, "ts"]
ts_mae   = df.loc[idx_mae, "ts"]
cls_mfe  = float(df.loc[idx_mfe, "close"])
cls_mae  = float(df.loc[idx_mae, "close"])
official_mfe = float(df.loc[idx_mfe, "LONG_MFE_pct_K288"])
official_mae = float(df.loc[idx_mae, "LONG_MAE_pct_K288"])

print(f"  LONG_MFE_pct_K288 max ts = {ts_mfe}  val = {official_mfe:.6f}%  close = {cls_mfe}")
print(f"  LONG_MAE_pct_K288 max ts = {ts_mae}   val = {official_mae:.6f}%  close = {cls_mae}")

# ── ③ 生 CSV 読み込み ─────────────────────────────────────
print("=== [3] 生 CSV 読み込み ===")
raw = pd.read_csv(CSV, parse_dates=["timestamp"])
raw = raw.sort_values("timestamp").reset_index(drop=True)
print(f"  rows={len(raw)}, ts_range={raw['timestamp'].iloc[0]} ~ {raw['timestamp'].iloc[-1]}")

# ── ④ MFE の独立再計算 ────────────────────────────────────
# LONG_MFE_pct_K288[i] = (max(high[i+1:i+K+1]) - close[i]) / close[i] * 100
# → ts_mfe のインデックス pos を CSV で探し、high[pos+1:pos+K+1] の max を使う

def recalc_mfe(raw_df, entry_ts, close_val, k):
    pos_matches = raw_df.index[raw_df["timestamp"] == entry_ts].tolist()
    if not pos_matches:
        print(f"  ERROR: {entry_ts} が CSV に存在しない")
        sys.exit(1)
    pos = pos_matches[0]
    win = raw_df.iloc[pos + 1: pos + k + 1]
    win_bars = len(win)
    high_max = float(win["high"].max())
    recalc = (high_max - close_val) / close_val * 100
    return recalc, win_bars, high_max, pos

def recalc_mae(raw_df, entry_ts, close_val, k):
    pos_matches = raw_df.index[raw_df["timestamp"] == entry_ts].tolist()
    if not pos_matches:
        print(f"  ERROR: {entry_ts} が CSV に存在しない")
        sys.exit(1)
    pos = pos_matches[0]
    win = raw_df.iloc[pos + 1: pos + k + 1]
    win_bars = len(win)
    low_min = float(win["low"].min())
    recalc = (close_val - low_min) / close_val * 100
    return recalc, win_bars, low_min, pos

print("=== [4] 独立再計算 (MFE) ===")
recalc_mfe_val, win_bars_mfe, high_max, pos_mfe = recalc_mfe(raw, ts_mfe, cls_mfe, K)
diff_mfe = abs(recalc_mfe_val - official_mfe)
print(f"  pos={pos_mfe}  win_bars={win_bars_mfe}  high_max={high_max}")
print(f"  recalc={recalc_mfe_val:.8f}%  official={official_mfe:.8f}%  diff={diff_mfe:.2e}")

print("=== [5] 独立再計算 (MAE) ===")
recalc_mae_val, win_bars_mae, low_min, pos_mae = recalc_mae(raw, ts_mae, cls_mae, K)
diff_mae = abs(recalc_mae_val - official_mae)
print(f"  pos={pos_mae}  win_bars={win_bars_mae}  low_min={low_min}")
print(f"  recalc={recalc_mae_val:.8f}%  official={official_mae:.8f}%  diff={diff_mae:.2e}")

# ── ⑤ アサーション ────────────────────────────────────────
print("=== [6] アサーション ===")
assert win_bars_mfe == K, f"FAIL: win_bars_mfe={win_bars_mfe} != {K}"
print(f"  ✅ win_bars_mfe == {K}")

assert win_bars_mae == K, f"FAIL: win_bars_mae={win_bars_mae} != {K}"
print(f"  ✅ win_bars_mae == {K}")

assert diff_mfe < 1e-6, f"FAIL: diff_mfe={diff_mfe:.2e} >= 1e-6"
print(f"  ✅ diff_mfe < 1e-6 ({diff_mfe:.2e})")

assert diff_mae < 1e-6, f"FAIL: diff_mae={diff_mae:.2e} >= 1e-6"
print(f"  ✅ diff_mae < 1e-6 ({diff_mae:.2e})")

# ── ⑥ JSON 出力 ───────────────────────────────────────────
result = {
    "generated": "2026-05-21",
    "K": K,
    "LONG_MFE_pct_K288": {
        "entry_ts":      str(ts_mfe),
        "entry_close":   cls_mfe,
        "official_val":  official_mfe,
        "recalc_val":    recalc_mfe_val,
        "diff":          diff_mfe,
        "win_bars":      win_bars_mfe,
        "window_high_max": high_max,
        "assert_diff_lt_1e6": diff_mfe < 1e-6,
        "assert_win_bars_eq_K": win_bars_mfe == K,
    },
    "LONG_MAE_pct_K288": {
        "entry_ts":      str(ts_mae),
        "entry_close":   cls_mae,
        "official_val":  official_mae,
        "recalc_val":    recalc_mae_val,
        "diff":          diff_mae,
        "win_bars":      win_bars_mae,
        "window_low_min": low_min,
        "assert_diff_lt_1e6": diff_mae < 1e-6,
        "assert_win_bars_eq_K": win_bars_mae == K,
    },
    "overall_pass": True,
}

OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False))
print(f"\n=== ✅ 完了 → {OUT} ===")
print(json.dumps(result, indent=2, ensure_ascii=False))
