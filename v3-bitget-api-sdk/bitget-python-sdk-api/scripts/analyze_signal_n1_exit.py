#!/usr/bin/env python3
"""
analyze_signal_n1_exit.py — N1 シグナルの Exit 再設計仮想シミュ

前提: N1 は per-trade 指標でフィルタ不能確定（grid結果）。
      本スクリプトはエッジ救済の最後の手段として TP_PCT / SL_PCT / MAX_HOLD の
      組合せを走査する。

Phase A: TP_PCT × SL_PCT マトリクス（MAX_HOLD=48 固定）
Phase B: 最良 TP/SL で MAX_HOLD を走査

採用基準:
  勝率 >= 60% かつ $/dt-day >= $10 → 本実装フェーズ
  どれも未達                       → N1 完全却下 → N3 ピボット

Usage:
  python3 scripts/analyze_signal_n1_exit.py data/BTCUSDT-5m-2025-10-03_04-01_combined_180d.csv
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

POSITION_BTC = 0.024
FEE_RATE     = 0.00014


def simulate(df: pd.DataFrame, entry_idx: int,
             tp_pct: float, sl_pct: float, max_hold_bars: int):
    if entry_idx + 1 >= len(df):
        return None
    entry_bar   = entry_idx + 1
    entry_price = float(df.at[entry_bar, "open"])
    tp_price    = entry_price * (1.0 - tp_pct)
    sl_price    = entry_price * (1.0 + sl_pct)

    max_hold    = min(max_hold_bars, len(df) - entry_bar - 1)
    exit_reason = "TIME_EXIT"
    exit_price  = float(df.at[entry_bar + max_hold, "close"])

    for j in range(entry_bar, entry_bar + max_hold + 1):
        if j >= len(df):
            break
        high_j = float(df.at[j, "high"])
        low_j  = float(df.at[j, "low"])
        # 保守的: 同一bar内で SL 優先
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
    return {
        "exit_reason": exit_reason,
        "net_usd":     gross - fee,
    }


def load_signals(csv_path: str):
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
    return df, fire_idx, max(1, len(dt_dates))


def run_combo(df, fire_idx, dt_days, tp_pct, sl_pct, max_hold):
    n = len(fire_idx)
    n_tp = 0
    net_sum = 0.0
    valid = 0
    for idx in fire_idx:
        t = simulate(df, idx, tp_pct, sl_pct, max_hold)
        if t is None:
            continue
        valid += 1
        net_sum += t["net_usd"]
        if t["exit_reason"] == "TP_FILLED":
            n_tp += 1
    if valid == 0:
        return {"n": 0, "winrate": 0.0, "net": 0.0, "dt": 0.0, "per_trade": 0.0}
    return {
        "n":         valid,
        "winrate":   n_tp / valid * 100.0,
        "net":       net_sum,
        "dt":        net_sum / dt_days,
        "per_trade": net_sum / valid,
    }


def main(csv_path: str):
    print(f"[N1-exit] CSV: {csv_path}")
    df, fire_idx, dt_days = load_signals(csv_path)
    print(f"[N1-exit] 発火: {len(fire_idx)}  DT日数: {dt_days}")

    # ---------------- Phase A: TP × SL マトリクス（MAX_HOLD=48 固定） ----------------
    print("\n============================================================")
    print("[Phase A] TP_PCT × SL_PCT  (MAX_HOLD=48)")
    print("============================================================")
    tp_list = [0.003, 0.004, 0.006, 0.008, 0.010, 0.012]
    sl_list = [0.005, 0.008, 0.010, 0.015, 0.020]

    header = "  TP \\ SL      " + "  ".join([f"SL={s:<6.3f}" for s in sl_list])
    print(header)
    best = {"key": None, "s": {"dt": -1e9, "winrate": 0.0, "n": 0}}
    results_a = {}
    for tp in tp_list:
        cells = []
        for sl in sl_list:
            s = run_combo(df, fire_idx, dt_days, tp, sl, 48)
            results_a[(tp, sl)] = s
            marker = "*" if (s["winrate"] >= 60.0 and s["dt"] >= 10.0) else " "
            cells.append(f"{marker}${s['dt']:>+6.2f}/w{s['winrate']:>4.1f}%")
            if s["n"] >= 30 and s["dt"] > best["s"]["dt"]:
                best = {"key": (tp, sl), "s": s}
        print(f"  TP={tp:<6.3f}    " + "  ".join(cells))

    print()
    if best["key"] is not None:
        tp, sl = best["key"]
        s = best["s"]
        print(f"  >>> Phase A best: TP={tp} / SL={sl}  "
              f"n={s['n']} win={s['winrate']:.1f}% ${s['dt']:+.2f}/dt-day "
              f"pt=${s['per_trade']:+.2f}")
    else:
        print("  >>> Phase A best: なし")

    # ---------------- Phase B: 最良TP/SL で MAX_HOLD を走査 ----------------
    if best["key"] is None:
        print("\n[Phase B] スキップ（Phase A best なし）")
        return
    tp, sl = best["key"]
    print("\n============================================================")
    print(f"[Phase B] MAX_HOLD 単軸  (TP={tp} / SL={sl})")
    print("============================================================")
    best_b = {"key": None, "s": {"dt": -1e9}}
    for mh in [12, 20, 30, 48, 72, 96]:
        s = run_combo(df, fire_idx, dt_days, tp, sl, mh)
        marker = "*" if (s["winrate"] >= 60.0 and s["dt"] >= 10.0) else " "
        print(f"  {marker} MAX_HOLD={mh:>3d}  n={s['n']:>4d}  "
              f"win={s['winrate']:>5.1f}%  NET=${s['net']:>+9.1f}  "
              f"${s['dt']:>+6.2f}/dt-day  pt=${s['per_trade']:>+5.2f}")
        if s["n"] >= 30 and s["dt"] > best_b["s"]["dt"]:
            best_b = {"key": mh, "s": s}
    print()
    if best_b["key"] is not None:
        print(f"  >>> Phase B best: MAX_HOLD={best_b['key']}  "
              f"${best_b['s']['dt']:+.2f}/dt-day")

    # ---------------- 最終判定 ----------------
    print("\n============================================================")
    print("[最終判定]")
    print("============================================================")
    final = best_b["s"] if best_b["key"] is not None else best["s"]
    tp, sl = best["key"]
    mh = best_b["key"] if best_b["key"] is not None else 48
    print(f"  最良構成: TP={tp} / SL={sl} / MAX_HOLD={mh}")
    print(f"  勝率 {final['winrate']:.1f}% / $/dt-day ${final['dt']:+.2f} / "
          f"per-trade ${final['per_trade']:+.2f}")
    if final["winrate"] >= 60.0 and final["dt"] >= 10.0:
        print("  ✅ 採用基準クリア → 本実装フェーズへ（Priority番号割当・実装）")
    elif final["dt"] >= 5.0:
        print("  △ 基準未達だが$5/dt-day超 → 追加シグナル条件強化の余地あり")
    else:
        print("  ❌ 全組合せで$10/dt-day未達 → N1 完全却下 → N3 へピボット")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/analyze_signal_n1_exit.py <csv_path>")
        sys.exit(1)
    main(sys.argv[1])
