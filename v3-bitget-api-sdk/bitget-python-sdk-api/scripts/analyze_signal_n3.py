#!/usr/bin/env python3
"""
analyze_signal_n3.py — N3 (ADX Spike Short-follow) シグナル検証

新規Priority設計フロー Step 2（365d直接検証・N1の教訓を反映）

シグナル条件（DT限定）:
  adx[i] - adx[i-3] >= SPIKE_THRESH  # ADX急上昇（モメンタム加速）
  bb_mid_slope[i] < 0                # 下降局面
  close[i] < open[i]                 # 陰線確定
  date(i) is DOWNTREND

Entry/Exit（素エッジ・タイトなTP/SL）:
  Entry : 次足 open で SHORT
  TP    : 0.004 / SL : 0.02 / TIME : 48本
  SIZE  : 0.024 BTC / FEE : MAKER 0.00014 × 2

採用基準:
  勝率 >= 60% かつ $/dt-day >= $10 → Step 3（grid/exit）へ
  勝率 >= 60% かつ $/dt-day < $10  → grid/exit 走査余地あり
  勝率 < 60%                       → N3 却下 → 他シグナル

Usage:
  python3 scripts/analyze_signal_n3.py data/BTCUSDT-5m-2025-04-01_03-31_365d.csv
"""
from __future__ import annotations

import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from runner.replay_csv import _build_regime_map, _load_csv
from strategies.cat_v9_decider import preprocess

TP_PCT        = 0.004
SL_PCT        = 0.02
MAX_HOLD_BARS = 48
POSITION_BTC  = 0.024
FEE_RATE      = 0.00014
SPIKE_THRESH  = 5.0     # adx[i] - adx[i-3] >= 5


def simulate_trade(df: pd.DataFrame, entry_idx: int):
    if entry_idx + 1 >= len(df):
        return None

    entry_bar   = entry_idx + 1
    entry_price = float(df.at[entry_bar, "open"])
    tp_price    = entry_price * (1.0 - TP_PCT)
    sl_price    = entry_price * (1.0 + SL_PCT)

    max_hold    = min(MAX_HOLD_BARS, len(df) - entry_bar - 1)
    exit_reason = "TIME_EXIT"
    exit_idx    = entry_bar + max_hold
    exit_price  = float(df.at[exit_idx, "close"])

    mfe = 0.0
    mae = 0.0

    for j in range(entry_bar, entry_bar + max_hold + 1):
        if j >= len(df):
            break
        high_j = float(df.at[j, "high"])
        low_j  = float(df.at[j, "low"])

        mfe_usd = (entry_price - low_j)  * POSITION_BTC
        mae_usd = (entry_price - high_j) * POSITION_BTC
        if mfe_usd > mfe:
            mfe = mfe_usd
        if mae_usd < mae:
            mae = mae_usd

        if high_j >= sl_price:
            exit_reason = "SL_FILLED"
            exit_idx    = j
            exit_price  = sl_price
            break
        if low_j <= tp_price:
            exit_reason = "TP_FILLED"
            exit_idx    = j
            exit_price  = tp_price
            break

    gross = (entry_price - exit_price) * POSITION_BTC
    fee   = (entry_price + exit_price) * POSITION_BTC * FEE_RATE
    net   = gross - fee

    return {
        "entry_idx":   entry_idx,
        "entry_time":  df.at[entry_idx, "timestamp"],
        "entry_price": entry_price,
        "exit_reason": exit_reason,
        "exit_price":  exit_price,
        "hold_bars":   exit_idx - entry_bar,
        "gross_usd":   gross,
        "fee_usd":     fee,
        "net_usd":     net,
        "mfe_usd":     mfe,
        "mae_usd":     mae,
    }


def main(csv_path: str) -> None:
    print(f"[N3] CSV: {csv_path}")

    regime_map = _build_regime_map(csv_path)
    dt_dates   = {d for d, r in regime_map.items() if r == "downtrend"}
    print(f"[N3] DT日数: {len(dt_dates)}")

    df_raw = _load_csv(csv_path)
    df = df_raw[["timestamp_ms", "open", "high", "low", "close"]].copy()
    df["timestamp"] = pd.to_datetime(df["timestamp_ms"], unit="ms")
    df = preprocess(df, params={})
    df["date"]        = df["timestamp"].dt.normalize()
    df["adx_diff_3"]  = df["adx"] - df["adx"].shift(3)

    sig = (
        (df["adx_diff_3"] >= SPIKE_THRESH) &
        (df["bb_mid_slope"] < 0.0) &
        (df["close"] < df["open"])  &
        (df["date"].isin(dt_dates))
    )
    fire_idx = df.index[sig].tolist()
    print(f"[N3] 発火件数: {len(fire_idx)}  (SPIKE_THRESH={SPIKE_THRESH})")

    trades = []
    for idx in fire_idx:
        t = simulate_trade(df, idx)
        if t is not None:
            trades.append(t)

    if not trades:
        print("[N3] トレードなし")
        return

    tr       = pd.DataFrame(trades)
    n_total  = len(tr)
    n_tp     = int((tr["exit_reason"] == "TP_FILLED").sum())
    n_sl     = int((tr["exit_reason"] == "SL_FILLED").sum())
    n_time   = int((tr["exit_reason"] == "TIME_EXIT").sum())
    winrate  = n_tp / n_total * 100.0 if n_total else 0.0
    net_sum  = float(tr["net_usd"].sum())
    dt_days  = max(1, len(dt_dates))
    net_per_day = net_sum / dt_days

    print("=" * 60)
    print(f"[N3] 集計（DT のみ・365d OOS）")
    print(f"  総件数          : {n_total}  ({n_total/dt_days:.1f}件/dt-day)")
    print(f"  TP_FILLED       : {n_tp}  ({n_tp/n_total*100:.1f}%)")
    print(f"  SL_FILLED       : {n_sl}  ({n_sl/n_total*100:.1f}%)")
    print(f"  TIME_EXIT       : {n_time}  ({n_time/n_total*100:.1f}%)")
    print(f"  勝率 (TP rate)  : {winrate:.2f}%")
    print(f"  avg MFE (USD)   : {tr['mfe_usd'].mean():.2f}")
    print(f"  avg MAE (USD)   : {tr['mae_usd'].mean():.2f}")
    print(f"  NET 合計 (USD)  : ${net_sum:.2f}")
    print(f"  NET per trade   : ${tr['net_usd'].mean():.2f}")
    print(f"  avg hold (bars) : {tr['hold_bars'].mean():.1f}")
    print(f"  DT 日数         : {dt_days}")
    print(f"  $/dt-day        : ${net_per_day:.2f}")
    print("=" * 60)

    print("[N3] 採用判定:")
    if winrate >= 60.0 and net_per_day >= 10.0:
        print(f"  OK 勝率 {winrate:.1f}% >=60% かつ $/dt-day ${net_per_day:.2f} >=$10 -> 本実装候補")
    elif winrate >= 60.0:
        print(f"  △ 勝率 {winrate:.1f}% >=60% だが $/dt-day ${net_per_day:.2f} <$10 -> grid/exit走査余地")
    else:
        print(f"  NG 勝率 {winrate:.1f}% <60% -> N3 却下 -> 他シグナル検討")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/analyze_signal_n3.py <csv_path>")
        sys.exit(1)
    main(sys.argv[1])
