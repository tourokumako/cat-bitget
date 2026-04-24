#!/usr/bin/env python3
"""
analyze_signal_n1_grid.py — N1 シグナルのフィルタ仮想シミュ（Step 3.5）

前提: analyze_signal_n1.py で勝率 65.19% / $2.07/dt-day / 19.9件/dt-day を確認済み。
本スクリプトは per-trade 指標（adx/atr14/bb_slope/rsi/ema_dist）で単軸・2軸フィルタを
走査し、勝率 >= 60% かつ $/dt-day >= $10 を満たす軸を探す。

Usage:
  python3 scripts/analyze_signal_n1_grid.py data/BTCUSDT-5m-2025-10-03_04-01_combined_180d.csv
"""
from __future__ import annotations

import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
_HERE = pathlib.Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import numpy as np
import pandas as pd

from analyze_signal_n1 import simulate_trade
from runner.replay_csv import _build_regime_map, _load_csv
from strategies.cat_v9_decider import preprocess


def build_trades(csv_path: str) -> tuple[pd.DataFrame, int]:
    regime_map = _build_regime_map(csv_path)
    dt_dates   = {d for d, r in regime_map.items() if r == "downtrend"}

    df_raw = _load_csv(csv_path)
    df = df_raw[["timestamp_ms", "open", "high", "low", "close"]].copy()
    df["timestamp"] = pd.to_datetime(df["timestamp_ms"], unit="ms")
    df = preprocess(df, params={})
    df["date"] = df["timestamp"].dt.normalize()

    sig = (
        (df["high"]  >  df["ema_20"]) &
        (df["close"] <= df["ema_20"]) &
        (df["close"] <  df["open"])   &
        (df["bb_mid_slope"] < 0.0)    &
        (df["date"].isin(dt_dates))
    )
    fire_idx = df.index[sig].tolist()

    trades = []
    for idx in fire_idx:
        t = simulate_trade(df, idx)
        if t is None:
            continue
        # per-trade 指標を付与（entry_idx 時点の値）
        t["adx_at_entry"]  = float(df.at[idx, "adx"])         if pd.notna(df.at[idx, "adx"])         else np.nan
        t["atr14"]         = float(df.at[idx, "atr_14"])      if pd.notna(df.at[idx, "atr_14"])      else np.nan
        t["bb_slope"]      = float(df.at[idx, "bb_mid_slope"])if pd.notna(df.at[idx, "bb_mid_slope"])else np.nan
        t["rsi_at_entry"]  = float(df.at[idx, "rsi_short"])   if pd.notna(df.at[idx, "rsi_short"])   else np.nan
        high_i = float(df.at[idx, "high"])
        ema_i  = float(df.at[idx, "ema_20"]) if pd.notna(df.at[idx, "ema_20"]) else np.nan
        t["ema_dist_pct"]  = (high_i - ema_i) / ema_i if ema_i and ema_i > 0 else np.nan
        trades.append(t)

    return pd.DataFrame(trades), max(1, len(dt_dates))


def summarize(tr: pd.DataFrame, dt_days: int) -> dict:
    n = len(tr)
    if n == 0:
        return {"n": 0, "winrate": 0.0, "net": 0.0, "dt": 0.0, "per_trade": 0.0}
    n_tp = int((tr["exit_reason"] == "TP_FILLED").sum())
    net  = float(tr["net_usd"].sum())
    return {
        "n":         n,
        "winrate":   n_tp / n * 100.0,
        "net":       net,
        "dt":        net / dt_days,
        "per_trade": net / n,
    }


def fmt_row(label: str, s: dict) -> str:
    return (
        f"  {label:<28s} n={s['n']:>5d}  "
        f"win={s['winrate']:>5.1f}%  "
        f"NET=${s['net']:>+9.1f}  "
        f"${s['dt']:>+6.2f}/dt-day  "
        f"pt=${s['per_trade']:>+5.2f}"
    )


def scan_single_axis(tr: pd.DataFrame, dt_days: int, col: str, thresholds: list, op: str):
    """op: '>=' or '<='"""
    print(f"\n--- 単軸: {col} {op} X ---")
    base = summarize(tr, dt_days)
    print(fmt_row("baseline (filter無し)", base))
    best_by_dtday = (None, base)
    for thr in thresholds:
        if op == ">=":
            filtered = tr[tr[col] >= thr]
            label = f"{col} >= {thr}"
        else:
            filtered = tr[tr[col] <= thr]
            label = f"{col} <= {thr}"
        s = summarize(filtered, dt_days)
        print(fmt_row(label, s))
        if s["n"] >= 30 and s["dt"] > best_by_dtday[1]["dt"]:
            best_by_dtday = (thr, s)
    if best_by_dtday[0] is not None:
        print(f"  >>> best (n>=30): {col} {op} {best_by_dtday[0]}  ${best_by_dtday[1]['dt']:.2f}/dt-day")


def scan_combo(tr: pd.DataFrame, dt_days: int,
               col_a: str, thrs_a: list, op_a: str,
               col_b: str, thrs_b: list, op_b: str):
    """2軸クロス"""
    print(f"\n--- 2軸: {col_a} {op_a} X  ×  {col_b} {op_b} Y ---")
    header = f"  {'':<18s} " + "  ".join([f"{col_b}{op_b}{t:>5}" for t in thrs_b])
    print(header)
    best = (None, None, summarize(tr, dt_days))
    for ta in thrs_a:
        cells = []
        for tb in thrs_b:
            mask = True
            if op_a == ">=": mask = mask & (tr[col_a] >= ta)
            else:            mask = mask & (tr[col_a] <= ta)
            if op_b == ">=": mask = mask & (tr[col_b] >= tb)
            else:            mask = mask & (tr[col_b] <= tb)
            s = summarize(tr[mask], dt_days)
            cells.append(f"n={s['n']:>3d}/${s['dt']:>+5.1f}")
            if s["n"] >= 30 and s["dt"] > best[2]["dt"]:
                best = (ta, tb, s)
        print(f"  {col_a}{op_a}{ta:<12}" + "  ".join(cells))
    if best[0] is not None:
        print(f"  >>> best (n>=30): {col_a}{op_a}{best[0]} × {col_b}{op_b}{best[1]}  "
              f"n={best[2]['n']} win={best[2]['winrate']:.1f}%  ${best[2]['dt']:.2f}/dt-day")


def main(csv_path: str):
    print(f"[N1-grid] CSV: {csv_path}")
    tr, dt_days = build_trades(csv_path)
    print(f"[N1-grid] trades: {len(tr)}  DT日数: {dt_days}")

    print("\n============================================================")
    print("[N1-grid] per-trade 指標の分布（TP vs TIME vs SL）")
    print("============================================================")
    for col in ["adx_at_entry", "atr14", "bb_slope", "rsi_at_entry", "ema_dist_pct"]:
        if col not in tr.columns:
            continue
        for rsn in ["TP_FILLED", "TIME_EXIT", "SL_FILLED"]:
            s = tr[tr["exit_reason"] == rsn][col].dropna()
            if len(s) == 0:
                continue
            print(f"  {col:<16s} {rsn:<11s} n={len(s):>4d} "
                  f"mean={s.mean():>+7.2f} p25={s.quantile(0.25):>+7.2f} "
                  f"p50={s.quantile(0.50):>+7.2f} p75={s.quantile(0.75):>+7.2f}")
        print()

    # 単軸走査
    scan_single_axis(tr, dt_days, "adx_at_entry", [25, 30, 35, 40, 45], ">=")
    scan_single_axis(tr, dt_days, "atr14",        [100, 150, 200, 250, 300], ">=")
    scan_single_axis(tr, dt_days, "bb_slope",     [-5, -10, -15, -20, -30], "<=")
    scan_single_axis(tr, dt_days, "rsi_at_entry", [45, 50, 55, 60], ">=")
    scan_single_axis(tr, dt_days, "ema_dist_pct", [0.0005, 0.001, 0.002, 0.003], ">=")

    # 2軸走査（P23 成功パターンに準拠: ADX × ATR）
    scan_combo(tr, dt_days,
               "adx_at_entry", [30, 35, 40], ">=",
               "atr14",        [150, 200, 250], ">=")

    # 2軸走査（ADX × bb_slope）
    scan_combo(tr, dt_days,
               "adx_at_entry", [25, 30, 35], ">=",
               "bb_slope",     [-10, -15, -20], "<=")

    print("\n[N1-grid] 完了")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/analyze_signal_n1_grid.py <csv_path>")
        sys.exit(1)
    main(sys.argv[1])
