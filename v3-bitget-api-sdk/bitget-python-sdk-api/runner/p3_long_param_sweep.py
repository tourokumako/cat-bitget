#!/usr/bin/env python3
"""
runner/p3_long_param_sweep.py — P3-LONG パラメータスイープ（Step N-2）

目的:
  前半90d（front）・後半90d（back）の両方でEV>0になる
  ADX_MAX / ATR_MIN / SLOPE_THRESH の組み合わせを探す。

使い方:
  python3 runner/p3_long_param_sweep.py \
    data/BTCUSDT-5m-2025-10-03_12-31_first90d.csv \
    data/BTCUSDT-5m-2026-01-01_04-01_combined_90d.csv
"""
from __future__ import annotations

import itertools
import pathlib
import sys
from dataclasses import dataclass

import numpy as np
import pandas as pd
import ta

_ROOT = pathlib.Path(__file__).resolve().parents[1]

# 固定パラメータ
ADX_MIN        = 30.0
GAP_MIN        = 0.3
POSITION_SIZE  = 0.024
FEE_RATE       = 0.00028   # maker×2
MAX_HOLD_BARS  = 96        # 480min
BAR_STEP       = 5

# 最良TP/SLペア（WORKFLOW記載の候補値）
TP_SL_PAIRS = [
    (0.003, 0.005),
    (0.005, 0.010),
    (0.008, 0.015),
    (0.010, 0.020),
    (0.012, 0.020),
    (0.012, 0.025),
    (0.015, 0.025),
]

# スイープ軸
SWEEP_ADX_MAX     = [40.0, 45.0, 50.0, 55.0, 60.0]
SWEEP_ATR_MIN     = [100.0, 150.0, 200.0, 250.0]
SWEEP_SLOPE_THRESH = [5.0, 10.0, 15.0, 20.0]


def load_df(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    stoch = ta.momentum.StochasticOscillator(df["high"], df["low"], df["close"], window=14, smooth_window=3)
    df["stoch_k"] = stoch.stoch()
    df["stoch_d"] = stoch.stoch_signal()
    adx_ind = ta.trend.ADXIndicator(df["high"], df["low"], df["close"], window=14)
    df["adx"] = adx_ind.adx()
    atr_ind = ta.volatility.AverageTrueRange(df["high"], df["low"], df["close"], window=14)
    df["atr14"] = atr_ind.average_true_range()
    bb_ind = ta.volatility.BollingerBands(df["close"], window=20, window_dev=2)
    df["bb_mid"] = bb_ind.bollinger_mavg()
    df["bb_mid_slope"] = df["bb_mid"] - df["bb_mid"].shift(1)
    return df


def detect_long_signals(df: pd.DataFrame, adx_max: float, atr_min: float, slope_thresh: float) -> list[int]:
    sigs = []
    for i in range(2, len(df)):
        sk_2 = df.at[i-2, "stoch_k"]; sd_2 = df.at[i-2, "stoch_d"]
        sk_1 = df.at[i-1, "stoch_k"]; sd_1 = df.at[i-1, "stoch_d"]
        sk   = df.at[i,   "stoch_k"]; sd   = df.at[i,   "stoch_d"]
        adx  = df.at[i, "adx"]; atr = df.at[i, "atr14"]
        slope = df.at[i, "bb_mid_slope"]
        close = df.at[i, "close"]; open_ = df.at[i, "open"]

        if any(pd.isna(v) for v in [sk_2, sd_2, sk_1, sd_1, sk, sd, adx, atr, slope]):
            continue
        if not (ADX_MIN <= adx < adx_max and atr >= atr_min):
            continue
        if (sk_2 < sd_2 and sk_1 < sd_1 and sk > sd
                and (sk - sd) > GAP_MIN
                and close >= open_
                and slope > slope_thresh):
            sigs.append(i)
    return sigs


def sim_tp_sl(df: pd.DataFrame, idx: int, tp_pct: float, sl_pct: float) -> float:
    ep   = df.at[idx, "close"]
    fee  = POSITION_SIZE * ep * FEE_RATE
    tp_p = ep * (1 + tp_pct)
    sl_p = ep * (1 - sl_pct)

    for j in range(idx + 1, min(idx + MAX_HOLD_BARS + 1, len(df))):
        h = df.at[j, "high"]; l = df.at[j, "low"]
        if l <= sl_p:
            return POSITION_SIZE * (sl_p - ep) - fee
        if h >= tp_p:
            return POSITION_SIZE * (tp_p - ep) - fee

    exit_p = df.at[min(idx + MAX_HOLD_BARS, len(df) - 1), "close"]
    return POSITION_SIZE * (exit_p - ep) - fee


def best_ev_for_signals(df: pd.DataFrame, sigs: list[int]) -> tuple[float, float, float]:
    """全TP/SLペアを試してbest EVとそのTP/SL・WRを返す"""
    if not sigs:
        return -999.0, 0.0, 0.0
    best_ev = -999.0
    best_tp = best_sl = 0.0
    for tp_pct, sl_pct in TP_SL_PAIRS:
        nets = [sim_tp_sl(df, i, tp_pct, sl_pct) for i in sigs]
        ev = float(np.mean(nets))
        if ev > best_ev:
            best_ev = ev
            best_tp = tp_pct
            best_sl = sl_pct
    return best_ev, best_tp, best_sl


@dataclass
class SweepResult:
    adx_max: float
    atr_min: float
    slope_thresh: float
    front_n: int
    back_n: int
    front_ev: float
    back_ev: float
    best_tp: float
    best_sl: float


def main() -> None:
    args = sys.argv[1:]
    if len(args) < 2:
        front_path = str(_ROOT / "data" / "BTCUSDT-5m-2025-10-03_12-31_first90d.csv")
        back_path  = str(_ROOT / "data" / "BTCUSDT-5m-2026-01-01_04-01_combined_90d.csv")
    else:
        front_path, back_path = args[0], args[1]

    print(f"前半90d: {front_path}")
    print(f"後半90d: {back_path}")
    print("指標計算中...")

    df_front = load_df(front_path)
    df_back  = load_df(back_path)

    total = len(SWEEP_ADX_MAX) * len(SWEEP_ATR_MIN) * len(SWEEP_SLOPE_THRESH)
    print(f"スイープ組み合わせ数: {total}\n")

    results: list[SweepResult] = []
    for adx_max, atr_min, slope in itertools.product(SWEEP_ADX_MAX, SWEEP_ATR_MIN, SWEEP_SLOPE_THRESH):
        f_sigs = detect_long_signals(df_front, adx_max, atr_min, slope)
        b_sigs = detect_long_signals(df_back,  adx_max, atr_min, slope)

        f_ev, best_tp, best_sl = best_ev_for_signals(df_front, f_sigs)
        b_ev, _, _ = best_ev_for_signals(df_back, b_sigs)
        # best_tp/sl は前半基準（両方に適用）
        if b_sigs:
            b_ev_at_best = float(np.mean([sim_tp_sl(df_back, i, best_tp, best_sl) for i in b_sigs]))
        else:
            b_ev_at_best = -999.0

        results.append(SweepResult(
            adx_max=adx_max, atr_min=atr_min, slope_thresh=slope,
            front_n=len(f_sigs), back_n=len(b_sigs),
            front_ev=f_ev, back_ev=b_ev_at_best,
            best_tp=best_tp, best_sl=best_sl,
        ))

    # ---- 結果表示 ----
    print(f"\n{'='*90}")
    print("【両期間EV>0 の組み合わせ】")
    print(f"{'='*90}")
    header = f"{'ADX_MAX':>8} {'ATR_MIN':>8} {'SLOPE':>7} | {'前半N':>6} {'後半N':>6} | {'前半EV':>8} {'後半EV':>8} | {'TP%':>5} {'SL%':>5}"
    print(header)
    print("-" * 90)

    both_positive = [r for r in results if r.front_ev > 0 and r.back_ev > 0]
    both_positive.sort(key=lambda r: r.front_ev + r.back_ev, reverse=True)

    if both_positive:
        for r in both_positive:
            print(f"{r.adx_max:>8.0f} {r.atr_min:>8.0f} {r.slope_thresh:>7.0f} | "
                  f"{r.front_n:>6} {r.back_n:>6} | "
                  f"{r.front_ev:>+8.2f}$ {r.back_ev:>+8.2f}$ | "
                  f"{r.best_tp*100:>4.1f}% {r.best_sl*100:>4.1f}%  ✅")
    else:
        print("  該当なし ← シグナル自体のエッジが不足")

    print(f"\n{'='*90}")
    print("【前半EV>0 のみ（後半NG）上位10件】")
    print(f"{'='*90}")
    front_only = [r for r in results if r.front_ev > 0 and r.back_ev <= 0]
    front_only.sort(key=lambda r: r.front_ev - abs(r.back_ev), reverse=True)
    print(header)
    print("-" * 90)
    for r in front_only[:10]:
        print(f"{r.adx_max:>8.0f} {r.atr_min:>8.0f} {r.slope_thresh:>7.0f} | "
              f"{r.front_n:>6} {r.back_n:>6} | "
              f"{r.front_ev:>+8.2f}$ {r.back_ev:>+8.2f}$ | "
              f"{r.best_tp*100:>4.1f}% {r.best_sl*100:>4.1f}%  ⚠️")

    print(f"\n【サマリー】")
    print(f"  総組み合わせ: {total}")
    print(f"  両期間EV>0: {len(both_positive)}件")
    print(f"  前半のみEV>0: {len(front_only)}件")
    if both_positive:
        best = both_positive[0]
        print(f"\n  ★ ベスト候補: ADX_MAX={best.adx_max:.0f}, ATR_MIN={best.atr_min:.0f}, SLOPE>={best.slope_thresh:.0f}")
        print(f"     前半{best.front_n}件 EV{best.front_ev:+.2f}$ / 後半{best.back_n}件 EV{best.back_ev:+.2f}$")
        print(f"     TP={best.best_tp*100:.1f}% / SL={best.best_sl*100:.1f}%")
    else:
        print("\n  → 両期間EV>0なし。P3-LONG採用は見送り推奨。")


if __name__ == "__main__":
    main()
