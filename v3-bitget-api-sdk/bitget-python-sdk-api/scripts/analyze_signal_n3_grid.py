#!/usr/bin/env python3
"""
analyze_signal_n3_grid.py — N3 (ADX Spike) per-trade フィルタ仮想シミュ

前提: N3 exit grid で TP=0.010/SL=0.020/MH=72 → $10.63/dt-day（勝率45.3%）
      TP=0.010/SL=0.020/MH=96 → $12.21/dt-day（勝率51.1%）
MH=72 baseline（スロット効率優先）で per-trade 指標・SPIKE_THRESH 軸を走査し、
$15+/dt-day を狙う。

走査軸:
  単軸: adx_at_entry / atr14 / bb_slope / rsi_at_entry / stoch_k / SPIKE_THRESH
  2軸 : ADX × ATR / ADX × SPIKE_THRESH / SPIKE × ATR

Usage:
  python3 scripts/analyze_signal_n3_grid.py data/BTCUSDT-5m-2025-04-01_03-31_365d.csv
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

TP_PCT       = 0.010
SL_PCT       = 0.020
MAX_HOLD     = 72
POSITION_BTC = 0.024
FEE_RATE     = 0.00014


def simulate_trade(df: pd.DataFrame, entry_idx: int):
    if entry_idx + 1 >= len(df):
        return None
    entry_bar   = entry_idx + 1
    entry_price = float(df.at[entry_bar, "open"])
    tp_price    = entry_price * (1.0 - TP_PCT)
    sl_price    = entry_price * (1.0 + SL_PCT)

    max_hold    = min(MAX_HOLD, len(df) - entry_bar - 1)
    exit_reason = "TIME_EXIT"
    exit_price  = float(df.at[entry_bar + max_hold, "close"])

    for j in range(entry_bar, entry_bar + max_hold + 1):
        if j >= len(df):
            break
        high_j = float(df.at[j, "high"])
        low_j  = float(df.at[j, "low"])
        if high_j >= sl_price:
            exit_reason = "SL_FILLED"
            exit_price  = sl_price
            break
        if low_j <= tp_price:
            exit_reason = "TP_FILLED"
            exit_price  = tp_price
            break

    gross = (entry_price - exit_price) * POSITION_BTC
    fee   = (entry_price + exit_price) * POSITION_BTC * FEE_RATE
    return {"exit_reason": exit_reason, "net_usd": gross - fee}


def build_trades(csv_path: str, spike_min: float = 5.0):
    regime_map = _build_regime_map(csv_path)
    dt_dates   = {d for d, r in regime_map.items() if r == "downtrend"}

    df_raw = _load_csv(csv_path)
    df = df_raw[["timestamp_ms", "open", "high", "low", "close"]].copy()
    df["timestamp"] = pd.to_datetime(df["timestamp_ms"], unit="ms")
    df = preprocess(df, params={})
    df["date"]       = df["timestamp"].dt.normalize()
    df["adx_diff_3"] = df["adx"] - df["adx"].shift(3)

    sig = (
        (df["adx_diff_3"] >= spike_min) &
        (df["bb_mid_slope"] < 0.0) &
        (df["close"] < df["open"])  &
        (df["date"].isin(dt_dates))
    )
    fire_idx = df.index[sig].tolist()

    trades = []
    for idx in fire_idx:
        t = simulate_trade(df, idx)
        if t is None:
            continue
        t["adx_at_entry"] = float(df.at[idx, "adx"])         if pd.notna(df.at[idx, "adx"])         else np.nan
        t["atr14"]        = float(df.at[idx, "atr_14"])      if pd.notna(df.at[idx, "atr_14"])      else np.nan
        t["bb_slope"]     = float(df.at[idx, "bb_mid_slope"])if pd.notna(df.at[idx, "bb_mid_slope"])else np.nan
        t["rsi_at_entry"] = float(df.at[idx, "rsi_short"])   if pd.notna(df.at[idx, "rsi_short"])   else np.nan
        t["stoch_k"]      = float(df.at[idx, "stoch_k"])     if pd.notna(df.at[idx, "stoch_k"])     else np.nan
        t["adx_diff_3"]   = float(df.at[idx, "adx_diff_3"])  if pd.notna(df.at[idx, "adx_diff_3"])  else np.nan
        trades.append(t)

    return pd.DataFrame(trades), max(1, len(dt_dates))


def summarize(tr: pd.DataFrame, dt_days: int) -> dict:
    n = len(tr)
    if n == 0:
        return {"n": 0, "winrate": 0.0, "net": 0.0, "dt": 0.0, "per_trade": 0.0}
    n_tp = int((tr["exit_reason"] == "TP_FILLED").sum())
    net  = float(tr["net_usd"].sum())
    return {"n": n, "winrate": n_tp / n * 100.0, "net": net,
            "dt": net / dt_days, "per_trade": net / n}


def fmt_row(label: str, s: dict) -> str:
    return (f"  {label:<30s} n={s['n']:>4d}  win={s['winrate']:>5.1f}%  "
            f"NET=${s['net']:>+9.1f}  ${s['dt']:>+6.2f}/dt-day  pt=${s['per_trade']:>+5.2f}")


def scan_single(tr, dt_days, col, thresholds, op):
    print(f"\n--- 単軸: {col} {op} X ---")
    base = summarize(tr, dt_days)
    print(fmt_row("baseline", base))
    best = (None, base)
    for thr in thresholds:
        if op == ">=":
            f = tr[tr[col] >= thr]; lbl = f"{col} >= {thr}"
        else:
            f = tr[tr[col] <= thr]; lbl = f"{col} <= {thr}"
        s = summarize(f, dt_days)
        mark = "*" if (s["winrate"] >= 40.0 and s["dt"] >= 15.0) else " "
        print(f"{mark} " + fmt_row(lbl, s)[2:])
        if s["n"] >= 30 and s["dt"] > best[1]["dt"]:
            best = (thr, s)
    if best[0] is not None:
        print(f"  >>> best(n>=30): {col}{op}{best[0]}  ${best[1]['dt']:.2f}/dt-day")


def scan_combo(tr, dt_days, col_a, thrs_a, op_a, col_b, thrs_b, op_b):
    print(f"\n--- 2軸: {col_a} {op_a} X  ×  {col_b} {op_b} Y ---")
    header = f"  {'':<18s} " + "  ".join([f"{col_b}{op_b}{t:>5}" for t in thrs_b])
    print(header)
    best = (None, None, summarize(tr, dt_days))
    for ta in thrs_a:
        cells = []
        for tb in thrs_b:
            mask = pd.Series(True, index=tr.index)
            mask = mask & ((tr[col_a] >= ta) if op_a == ">=" else (tr[col_a] <= ta))
            mask = mask & ((tr[col_b] >= tb) if op_b == ">=" else (tr[col_b] <= tb))
            s = summarize(tr[mask], dt_days)
            mark = "*" if (s["dt"] >= 15.0 and s["n"] >= 30) else " "
            cells.append(f"{mark}n={s['n']:>3d}/${s['dt']:>+5.1f}")
            if s["n"] >= 30 and s["dt"] > best[2]["dt"]:
                best = (ta, tb, s)
        print(f"  {col_a}{op_a}{ta:<12}" + "  ".join(cells))
    if best[0] is not None:
        print(f"  >>> best(n>=30): {col_a}{op_a}{best[0]} × {col_b}{op_b}{best[1]}  "
              f"n={best[2]['n']} win={best[2]['winrate']:.1f}% ${best[2]['dt']:.2f}/dt-day")


def main(csv_path: str):
    print(f"[N3-grid] CSV: {csv_path}  (TP={TP_PCT}, SL={SL_PCT}, MH={MAX_HOLD})")

    # baseline: SPIKE>=5 で全件
    tr, dt_days = build_trades(csv_path, spike_min=5.0)
    print(f"[N3-grid] baseline trades: {len(tr)}  DT日数: {dt_days}")
    base = summarize(tr, dt_days)
    print(fmt_row("[baseline SPIKE>=5]", base))

    # 指標分布
    print("\n============================================================")
    print("[N3-grid] per-trade 指標分布（TP vs TIME vs SL）")
    print("============================================================")
    for col in ["adx_at_entry", "atr14", "bb_slope", "rsi_at_entry", "stoch_k", "adx_diff_3"]:
        for rsn in ["TP_FILLED", "TIME_EXIT", "SL_FILLED"]:
            g = tr[tr["exit_reason"] == rsn][col].dropna()
            if len(g) == 0:
                continue
            print(f"  {col:<15s} {rsn:<11s} n={len(g):>3d} "
                  f"mean={g.mean():>+7.2f} p25={g.quantile(0.25):>+7.2f} "
                  f"p50={g.quantile(0.50):>+7.2f} p75={g.quantile(0.75):>+7.2f}")
        print()

    # 単軸走査
    scan_single(tr, dt_days, "adx_at_entry", [20, 25, 30, 35, 40], ">=")
    scan_single(tr, dt_days, "atr14",        [100, 150, 200, 250, 300], ">=")
    scan_single(tr, dt_days, "bb_slope",     [-5, -10, -15, -20, -30], "<=")
    scan_single(tr, dt_days, "rsi_at_entry", [45, 50, 55, 60], ">=")
    scan_single(tr, dt_days, "stoch_k",      [30, 40, 50, 60, 70], ">=")
    scan_single(tr, dt_days, "adx_diff_3",   [5, 7, 10, 15], ">=")

    # SPIKE_THRESH 軸（シグナル条件自体の強度）
    print("\n--- SPIKE_THRESH 軸（シグナル条件変更） ---")
    for spike in [3, 5, 7, 10, 15]:
        tr_s, _ = build_trades(csv_path, spike_min=float(spike))
        s = summarize(tr_s, dt_days)
        mark = "*" if (s["dt"] >= 15.0 and s["n"] >= 30) else " "
        print(f"{mark} " + fmt_row(f"SPIKE>={spike}", s)[2:])

    # 2軸組合せ
    scan_combo(tr, dt_days, "adx_at_entry", [25, 30, 35], ">=", "atr14",      [150, 200, 250], ">=")
    scan_combo(tr, dt_days, "adx_at_entry", [25, 30, 35], ">=", "adx_diff_3", [5, 7, 10], ">=")
    scan_combo(tr, dt_days, "adx_diff_3",   [5, 7, 10],   ">=", "atr14",      [150, 200, 250], ">=")
    scan_combo(tr, dt_days, "adx_at_entry", [25, 30, 35], ">=", "bb_slope",   [-10, -15, -20], "<=")

    print("\n[N3-grid] 完了")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/analyze_signal_n3_grid.py <csv_path>")
        sys.exit(1)
    main(sys.argv[1])
