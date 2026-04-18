#!/usr/bin/env python3
"""
runner/p1p21_edge_check.py — P1/P21 MACD シグナルの方向性エッジ検証（Step N-2）

目的:
  5m足でMACDクロスに方向性エッジがあるかを確認する。
  フィルターなし / フィルターあり の2パターンで計測。

使い方:
  python3 runner/p1p21_edge_check.py [ohlcv_csv]

デフォルト:
  data/BTCUSDT-5m-2026-01-01_04-01_combined_90d.csv
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np
import pandas as pd
import ta

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_DEFAULT_CSV = str(_ROOT / "data" / "BTCUSDT-5m-2026-01-01_04-01_combined_90d.csv")

# MACD パラメータ（cat_params_v9.json と同値）
MACD_FAST   = 12
MACD_SLOW   = 26
MACD_SIGNAL = 9

# 現在のフィルター値（cat_params_v9.json）
ADX_MIN  = 30.0
ATR_MIN  = 60.0
ATR_MAX  = 9999.0

# 計測するタイムホライゾン（分）
HORIZONS = [5, 10, 15, 30, 60, 120, 240, 480]
BAR_STEP = 5

# タイトなTP/SL設定（エッジ検証用）
TIGHT_TP_SL_PAIRS = [
    (0.0006, 0.001),   # TP=0.06%  SL=0.10%
    (0.001,  0.002),   # TP=0.10%  SL=0.20%
    (0.003,  0.005),   # TP=0.30%  SL=0.50%
    (0.005,  0.010),   # TP=0.50%  SL=1.00%
    (0.010,  0.020),   # TP=1.00%  SL=2.00%
    (0.012,  0.020),   # TP=1.20%  SL=2.00%（P23採用値参考）
    (0.015,  0.025),   # TP=1.50%  SL=2.50%
]

POSITION_SIZE_BTC = 0.06  # P1/P21 current size
FEE_RATE = 0.0002         # maker × 2 往復概算


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    macd_ind = ta.trend.MACD(df["close"], window_fast=MACD_FAST,
                              window_slow=MACD_SLOW, window_sign=MACD_SIGNAL)
    df["macd"]        = macd_ind.macd()
    df["macd_signal"] = macd_ind.macd_signal()
    df["macd_hist"]   = df["macd"] - df["macd_signal"]

    adx_ind = ta.trend.ADXIndicator(df["high"], df["low"], df["close"], window=14)
    df["adx"] = adx_ind.adx()

    atr_ind = ta.volatility.AverageTrueRange(df["high"], df["low"], df["close"], window=14)
    df["atr14"] = atr_ind.average_true_range()

    df["_idx"] = df.index
    return df


def detect_crosses(df: pd.DataFrame) -> tuple[list[int], list[int]]:
    """MACDゴールデンクロス/デッドクロスのインデックスを返す"""
    golden, dead = [], []
    for i in range(1, len(df)):
        prev_m = df.at[i-1, "macd"];     prev_s = df.at[i-1, "macd_signal"]
        curr_m = df.at[i,   "macd"];     curr_s = df.at[i,   "macd_signal"]
        if any(pd.isna([prev_m, prev_s, curr_m, curr_s])):
            continue
        if prev_m <= prev_s and curr_m > curr_s:
            golden.append(i)
        elif prev_m >= prev_s and curr_m < curr_s:
            dead.append(i)
    return golden, dead


def favorable_move_series(df: pd.DataFrame, idx: int, side: str) -> list[float]:
    """エントリーから各HOIZONでの favorable move (%) を返す"""
    ep = df.at[idx, "close"]
    results = []
    for h in HORIZONS:
        n_bars = h // BAR_STEP
        end_idx = min(idx + n_bars, len(df) - 1)
        window = df.iloc[idx:end_idx + 1]
        if window.empty:
            results.append(np.nan)
            continue
        if side == "LONG":
            fm = (window["high"].max() - ep) / ep * 100
        else:
            fm = (ep - window["low"].min()) / ep * 100
        results.append(fm)
    return results


def sim_tp_sl(df: pd.DataFrame, idx: int, side: str,
              tp_pct: float, sl_pct: float, max_bars: int = 288) -> dict:
    """TP/SL到達シミュレーション（手数料込み）"""
    ep = df.at[idx, "close"]
    size = POSITION_SIZE_BTC
    fee  = size * ep * FEE_RATE

    if side == "LONG":
        tp_price = ep * (1 + tp_pct)
        sl_price = ep * (1 - sl_pct)
    else:
        tp_price = ep * (1 - tp_pct)
        sl_price = ep * (1 + sl_pct)

    for j in range(idx + 1, min(idx + max_bars + 1, len(df))):
        h = df.at[j, "high"]; l = df.at[j, "low"]
        if side == "LONG":
            if l <= sl_price:
                gross = size * (sl_price - ep)
                return {"result": "SL", "net": gross - fee, "bars": j - idx}
            if h >= tp_price:
                gross = size * (tp_price - ep)
                return {"result": "TP", "net": gross - fee, "bars": j - idx}
        else:
            if h >= sl_price:
                gross = size * (ep - sl_price)
                return {"result": "SL", "net": gross - fee, "bars": j - idx}
            if l <= tp_price:
                gross = size * (ep - tp_price)
                return {"result": "TP", "net": gross - fee, "bars": j - idx}

    # TIME_EXIT（max_bars到達）
    exit_price = df.at[min(idx + max_bars, len(df) - 1), "close"]
    if side == "LONG":
        gross = size * (exit_price - ep)
    else:
        gross = size * (ep - exit_price)
    return {"result": "TIME", "net": gross - fee, "bars": max_bars}


def analyze_signals(label: str, indices: list[int], side: str, df: pd.DataFrame) -> None:
    n = len(indices)
    days = len(df) * BAR_STEP / 60 / 24
    print(f"\n{'='*60}")
    print(f"【{label}】  {n}件 ({n/days:.1f}件/day)  side={side}")
    print(f"{'='*60}")

    # ---- 1. Favorable Move 分布 ----
    fm_matrix = np.full((n, len(HORIZONS)), np.nan)
    for i, idx in enumerate(indices):
        fm_matrix[i] = favorable_move_series(df, idx, side)

    print(f"\n--- Favorable Move 分布 (%) ---")
    print(f"{'pct':<6} | " + " | ".join(f"{h:>5}m" for h in HORIZONS))
    print("-" * (8 + 9 * len(HORIZONS)))
    for pct in [25, 50, 75, 90]:
        vals = [np.nanpercentile(fm_matrix[:, j], pct) for j in range(len(HORIZONS))]
        print(f"p{pct:<5} | " + " | ".join(f"{v:>5.2f}" for v in vals))

    # ---- 2. TP/SL 勝率・EV 試算 ----
    print(f"\n--- TP/SL 勝率・期待値試算 (size={POSITION_SIZE_BTC}BTC) ---")
    print(f"{'TP%':>6} {'SL%':>6} | {'TP件':>6} {'SL件':>6} {'TIME件':>6} | {'勝率':>6} | {'EV/件':>8} | {'NET/90d':>10}")
    print("-" * 72)
    for tp_pct, sl_pct in TIGHT_TP_SL_PAIRS:
        results = [sim_tp_sl(df, idx, side, tp_pct, sl_pct) for idx in indices]
        tp_c  = sum(1 for r in results if r["result"] == "TP")
        sl_c  = sum(1 for r in results if r["result"] == "SL")
        te_c  = sum(1 for r in results if r["result"] == "TIME")
        win_r = tp_c / n if n > 0 else 0
        ev    = np.mean([r["net"] for r in results]) if results else 0
        net90 = sum(r["net"] for r in results)
        mark = " ← 勝率≥60%" if win_r >= 0.6 else ("" if win_r >= 0.5 else " ⚠️")
        print(f"{tp_pct*100:>5.2f}% {sl_pct*100:>5.2f}% | {tp_c:>6} {sl_c:>6} {te_c:>6} | "
              f"{win_r:>5.1%} | {ev:>+8.2f}$ | {net90:>+10.1f}${mark}")


def main(csv_path: str) -> None:
    print(f"OHLCV: {csv_path}")
    df = pd.read_csv(csv_path, parse_dates=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    df = compute_indicators(df)

    days = len(df) * BAR_STEP / 60 / 24
    print(f"期間: {df['timestamp'].iloc[0].date()} 〜 {df['timestamp'].iloc[-1].date()}  ({days:.0f}日)")

    golden_all, dead_all = detect_crosses(df)

    # フィルターあり (ADX≥30, ATR in range)
    def apply_filter(indices: list[int]) -> list[int]:
        out = []
        for i in indices:
            adx = df.at[i, "adx"]; atr = df.at[i, "atr14"]
            if pd.notna(adx) and adx >= ADX_MIN and pd.notna(atr) and ATR_MIN <= atr <= ATR_MAX:
                out.append(i)
        return out

    golden_filt = apply_filter(golden_all)
    dead_filt   = apply_filter(dead_all)

    print(f"\nMACD({MACD_FAST},{MACD_SLOW},{MACD_SIGNAL}) クロス検出:")
    print(f"  ゴールデンクロス: {len(golden_all)}件 ({len(golden_all)/days:.1f}/day) → フィルター後: {len(golden_filt)}件 ({len(golden_filt)/days:.1f}/day)")
    print(f"  デッドクロス:     {len(dead_all)}件 ({len(dead_all)/days:.1f}/day) → フィルター後: {len(dead_filt)}件 ({len(dead_filt)/days:.1f}/day)")
    print(f"  フィルター: ADX≥{ADX_MIN}, ATR[{ATR_MIN},{ATR_MAX}]")

    analyze_signals("P1-LONG  フィルターなし（MACDクロスのみ）", golden_all,  "LONG",  df)
    analyze_signals("P1-LONG  フィルターあり（ADX≥30, ATR≥60）", golden_filt, "LONG",  df)
    analyze_signals("P21-SHORT フィルターなし（MACDクロスのみ）", dead_all,   "SHORT", df)
    analyze_signals("P21-SHORT フィルターあり（ADX≥30, ATR≥60）", dead_filt,  "SHORT", df)

    print("\n\n完了。")
    print("判定基準: 勝率≥60% かつ EV/件 > 0 → エッジあり")
    print("         勝率<60% または EV/件 ≤ 0 → シグナル設計を見直す")


if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else _DEFAULT_CSV
    main(csv_path)
