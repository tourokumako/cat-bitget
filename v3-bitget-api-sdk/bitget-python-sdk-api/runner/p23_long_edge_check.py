#!/usr/bin/env python3
"""
runner/p23_long_edge_check.py — P23-LONG ミラーシグナルのエッジ検証（Step N-2）

目的:
  P23-SHORT（stochデッドクロス）の鏡として、ゴールデンクロスをLONGに使えるか検証。
  前半90日(2025/10-12) / 後半90日(2026/01-04) それぞれで確認する。

シグナル定義:
  P23-LONG候補:
    stoch golden cross (k<d 2本連続 → k>d) + gap>0.3
    + close >= open（陽線）
    + bb_mid_slope > +10（上昇モメンタム確認）
    + ADX in [30, 40)
    + ATR_14 >= 150

  P23-SHORT（比較用・既存）:
    stoch dead cross (k>d 2本連続 → k<d) + gap>0.3
    + close <= open（陰線）
    + bb_mid_slope < -10
    + ADX in [30, 40)
    + ATR_14 >= 150

使い方:
  python3 runner/p23_long_edge_check.py [ohlcv_csv]
  python3 runner/p23_long_edge_check.py data/BTCUSDT-5m-2025-10-03_12-31_first90d.csv
  python3 runner/p23_long_edge_check.py data/BTCUSDT-5m-2026-01-01_04-01_combined_90d.csv
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np
import pandas as pd
import ta

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_DEFAULT_CSV = str(_ROOT / "data" / "BTCUSDT-5m-2026-01-01_04-01_combined_90d.csv")

# シグナルフィルター（P23ミラー）
ADX_MIN      = 30.0
ADX_MAX      = 40.0
ATR_MIN      = 150.0
SLOPE_THRESH = 10.0   # LONG: slope > +10, SHORT: slope < -10
GAP_MIN      = 0.3

# TP/SL 試算ペア（P23採用値 0.012 を中心に）
TIGHT_TP_SL_PAIRS = [
    (0.003, 0.005),
    (0.005, 0.010),
    (0.008, 0.015),
    (0.010, 0.020),
    (0.012, 0.020),  # P23採用値
    (0.012, 0.025),
    (0.015, 0.025),
    (0.020, 0.030),
]

POSITION_SIZE_BTC = 0.024  # P23 current per-add size
FEE_RATE = 0.00028          # maker × 2 往復（0.014% × 2）
BAR_STEP = 5                 # 5分足
MAX_HOLD_BARS = 96           # 480min（P23_TIME_EXIT_MIN=480と同じ）

HORIZONS = [15, 30, 60, 120, 240, 480]


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    stoch = ta.momentum.StochasticOscillator(
        df["high"], df["low"], df["close"], window=14, smooth_window=3
    )
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


def detect_signals(df: pd.DataFrame) -> tuple[list[int], list[int]]:
    """
    P23-LONG ゴールデンクロス / P23-SHORT デッドクロス を検出。
    フィルター（ADX/ATR/slope/方向）適用済み。
    """
    long_signals, short_signals = [], []

    for i in range(2, len(df)):
        sk_2  = df.at[i - 2, "stoch_k"]; sd_2  = df.at[i - 2, "stoch_d"]
        sk_1  = df.at[i - 1, "stoch_k"]; sd_1  = df.at[i - 1, "stoch_d"]
        sk    = df.at[i,     "stoch_k"]; sd    = df.at[i,     "stoch_d"]
        adx   = df.at[i, "adx"]
        atr   = df.at[i, "atr14"]
        slope = df.at[i, "bb_mid_slope"]
        close = df.at[i, "close"]; open_ = df.at[i, "open"]

        if any(pd.isna(v) for v in [sk_2, sd_2, sk_1, sd_1, sk, sd, adx, atr, slope]):
            continue

        # 共通フィルター
        if not (ADX_MIN <= adx < ADX_MAX and atr >= ATR_MIN):
            continue

        # P23-LONG: ゴールデンクロス（k<d→k<d→k>d）+ 陽線 + slope>+THRESH
        if (sk_2 < sd_2 and sk_1 < sd_1 and sk > sd
                and (sk - sd) > GAP_MIN
                and close >= open_
                and slope > SLOPE_THRESH):
            long_signals.append(i)

        # P23-SHORT: デッドクロス（k>d→k>d→k<d）+ 陰線 + slope<-THRESH
        if (sk_2 > sd_2 and sk_1 > sd_1 and sk < sd
                and (sd - sk) > GAP_MIN
                and close <= open_
                and slope < -SLOPE_THRESH):
            short_signals.append(i)

    return long_signals, short_signals


def favorable_move(df: pd.DataFrame, idx: int, side: str) -> list[float]:
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
            results.append((window["high"].max() - ep) / ep * 100)
        else:
            results.append((ep - window["low"].min()) / ep * 100)
    return results


def sim_tp_sl(df: pd.DataFrame, idx: int, side: str,
              tp_pct: float, sl_pct: float) -> dict:
    ep   = df.at[idx, "close"]
    size = POSITION_SIZE_BTC
    fee  = size * ep * FEE_RATE

    tp_price = ep * (1 + tp_pct) if side == "LONG" else ep * (1 - tp_pct)
    sl_price = ep * (1 - sl_pct) if side == "LONG" else ep * (1 + sl_pct)

    for j in range(idx + 1, min(idx + MAX_HOLD_BARS + 1, len(df))):
        h = df.at[j, "high"]; l = df.at[j, "low"]
        if side == "LONG":
            if l <= sl_price:
                return {"result": "SL", "net": size * (sl_price - ep) - fee}
            if h >= tp_price:
                return {"result": "TP", "net": size * (tp_price - ep) - fee}
        else:
            if h >= sl_price:
                return {"result": "SL", "net": size * (ep - sl_price) - fee}
            if l <= tp_price:
                return {"result": "TP", "net": size * (ep - tp_price) - fee}

    exit_price = df.at[min(idx + MAX_HOLD_BARS, len(df) - 1), "close"]
    gross = size * (exit_price - ep) if side == "LONG" else size * (ep - exit_price)
    return {"result": "TIME", "net": gross - fee}


def analyze(label: str, indices: list[int], side: str, df: pd.DataFrame) -> None:
    n = len(indices)
    days = (len(df) - 1) * BAR_STEP / 60 / 24
    print(f"\n{'='*65}")
    print(f"【{label}】  {n}件 ({n/days:.2f}件/day)  side={side}")
    print(f"{'='*65}")
    if n == 0:
        print("  シグナルなし")
        return

    # Favorable Move
    fm_matrix = np.array([favorable_move(df, i, side) for i in indices])
    print(f"\n  Favorable Move (%) ← エントリー後に有利方向へ何%動いたか")
    print(f"  {'pct':<5} | " + " | ".join(f"{h:>5}m" for h in HORIZONS))
    print("  " + "-" * (7 + 9 * len(HORIZONS)))
    for pct in [50, 75, 90]:
        vals = [np.nanpercentile(fm_matrix[:, j], pct) for j in range(len(HORIZONS))]
        print(f"  p{pct:<4} | " + " | ".join(f"{v:>5.2f}" for v in vals))

    # TP/SL 勝率・EV
    print(f"\n  TP/SL 勝率・期待値試算 (size={POSITION_SIZE_BTC}BTC, 保持上限{MAX_HOLD_BARS*BAR_STEP}min)")
    print(f"  {'TP%':>6} {'SL%':>6} | {'TP':>5} {'SL':>5} {'TIME':>5} | {'勝率':>6} | {'EV/件':>8} | {'NET/期間':>10}")
    print("  " + "-" * 70)
    best_ev = -999
    for tp_pct, sl_pct in TIGHT_TP_SL_PAIRS:
        results = [sim_tp_sl(df, i, side, tp_pct, sl_pct) for i in indices]
        tp_c  = sum(1 for r in results if r["result"] == "TP")
        sl_c  = sum(1 for r in results if r["result"] == "SL")
        te_c  = sum(1 for r in results if r["result"] == "TIME")
        wr    = tp_c / n
        ev    = np.mean([r["net"] for r in results])
        net   = sum(r["net"] for r in results)
        best_ev = max(best_ev, ev)
        mark = " ✅" if wr >= 0.6 and ev > 0 else (" 🔺" if ev > 0 else " ⚠️")
        print(f"  {tp_pct*100:>5.1f}% {sl_pct*100:>5.1f}% | {tp_c:>5} {sl_c:>5} {te_c:>5} | "
              f"{wr:>5.1%} | {ev:>+8.2f}$ | {net:>+10.1f}${mark}")

    print(f"\n  → best EV/件: ${best_ev:+.2f}")
    print(f"  → 判定: {'エッジあり ✅' if best_ev > 0 else 'エッジなし ❌ → シグナル見直し必要'}")


def main(csv_path: str) -> None:
    print(f"\nOHLCV: {csv_path}")
    df = pd.read_csv(csv_path, parse_dates=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    df = compute_indicators(df)

    days = (len(df) - 1) * BAR_STEP / 60 / 24
    print(f"期間: {df['timestamp'].iloc[0].date()} 〜 {df['timestamp'].iloc[-1].date()}  ({days:.0f}日)")
    print(f"フィルター: stoch(14,3) cross + gap>{GAP_MIN} + 方向一致 + bb_slope>{SLOPE_THRESH}/< -{SLOPE_THRESH}")
    print(f"           + ADX[{ADX_MIN},{ADX_MAX}) + ATR≥{ATR_MIN}")

    long_sigs, short_sigs = detect_signals(df)
    print(f"\nシグナル検出: LONG={len(long_sigs)}件({len(long_sigs)/days:.2f}/day)  "
          f"SHORT={len(short_sigs)}件({len(short_sigs)/days:.2f}/day)")

    analyze("P23-LONG候補（ゴールデンクロス）", long_sigs,  "LONG",  df)
    analyze("P23-SHORT 比較（デッドクロス）",   short_sigs, "SHORT", df)

    print("\n\n完了。")
    print("採用基準: 勝率≥50% かつ EV/件 > 0（前半・後半両方で）")


if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else _DEFAULT_CSV
    main(csv_path)
