#!/usr/bin/env python3
"""
runner/p23_exit_analysis.py — P23-SHORT エントリー後の価格挙動分析

目的:
  TP/TIME_EXIT のjoint設計根拠を作るために、
  P23エントリー後の favorable move 分布を計測する。

使い方:
  python3 runner/p23_exit_analysis.py [replay_csv] [ohlcv_csv]

デフォルト:
  replay_csv : results/replay_BTCUSDT-5m-2026-01-01_04-01_combined_90d.csv
  ohlcv_csv  : data/BTCUSDT-5m-2026-01-01_04-01_combined_90d.csv
"""
from __future__ import annotations

import json
import pathlib
import sys
from typing import Dict, List, Optional

import pandas as pd
import numpy as np

_ROOT = pathlib.Path(__file__).resolve().parents[1]

_DEFAULT_REPLAY = str(_ROOT / "results" / "replay_BTCUSDT-5m-2026-01-01_04-01_combined_90d.csv")
_DEFAULT_OHLCV  = str(_ROOT / "data"    / "BTCUSDT-5m-2026-01-01_04-01_combined_90d.csv")

# 計測するタイムホライゾン（分）
HORIZONS = [30, 60, 120, 240, 360, 480, 720, 1440]
# 各バーは5分なので bars = minutes / 5
BAR_STEP = 5

# P23 TP_PCT の現在値（比較用）
P23_TP_PCT_CURRENT = 0.007
# P23 TIME_EXIT の現在値（分）
P23_TIME_EXIT_CURRENT = 240


def load_replay(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["entry_time", "exit_time"])
    p23 = df[df["priority"] == 23].copy()
    print(f"[replay] 全トレード: {len(df)}件  P23: {len(p23)}件")
    return p23


def load_ohlcv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    # timestamp → index マップ（高速lookup用）
    df["_idx"] = df.index
    return df


def favorable_move_at(
    entry_price: float,
    entry_time: pd.Timestamp,
    ohlcv: pd.DataFrame,
    horizon_min: int,
) -> Optional[float]:
    """
    SHORT方向の favorable move を計算する。
    entry_time から horizon_min 分間の最安値を見て、
    (entry_price - min_low) / entry_price * 100 を返す（%）。
    負なら価格が上昇（逆行）。
    """
    n_bars = horizon_min // BAR_STEP
    mask = ohlcv["timestamp"] >= entry_time
    start_idx = ohlcv.loc[mask, "_idx"].min()
    if pd.isna(start_idx):
        return None
    end_idx = min(int(start_idx) + n_bars, len(ohlcv) - 1)
    window = ohlcv.iloc[int(start_idx):end_idx + 1]
    if window.empty:
        return None
    min_low = window["low"].min()
    return (entry_price - min_low) / entry_price * 100  # %


def tp_reach_time(
    entry_price: float,
    entry_time: pd.Timestamp,
    ohlcv: pd.DataFrame,
    tp_pct: float,
    max_horizon_min: int = 1440,
) -> Optional[int]:
    """
    TP価格に初めて到達する時間（分）を返す。未到達はNone。
    SHORT: tp_price = entry_price * (1 - tp_pct)
    """
    tp_price = entry_price * (1 - tp_pct)
    n_bars = max_horizon_min // BAR_STEP
    mask = ohlcv["timestamp"] >= entry_time
    start_idx = ohlcv.loc[mask, "_idx"].min()
    if pd.isna(start_idx):
        return None
    for i in range(int(start_idx), min(int(start_idx) + n_bars + 1, len(ohlcv))):
        if ohlcv.loc[i, "low"] <= tp_price:
            elapsed_bars = i - int(start_idx)
            return elapsed_bars * BAR_STEP
    return None


def main(replay_path: str, ohlcv_path: str) -> None:
    p23 = load_replay(replay_path)
    ohlcv = load_ohlcv(ohlcv_path)

    n = len(p23)
    if n == 0:
        print("P23トレードが0件です。")
        return

    entry_prices = p23["entry_price"].values
    entry_times  = p23["entry_time"].values
    exit_reasons = p23["exit_reason"].values
    net_usds     = p23["net_usd"].values
    size_btcs    = p23["size_btc"].values
    hold_mins    = p23["hold_min"].values

    # ---- Section 1: Favorable Move 分布 ----
    print("\n" + "=" * 60)
    print("【Section 1】P23 SHORT エントリー後の Favorable Move 分布")
    print("  (Short方向の最大動き: (entry - min_low) / entry × 100 %)")
    print("=" * 60)

    fm_matrix = np.full((n, len(HORIZONS)), np.nan)
    for i, (ep, et) in enumerate(zip(entry_prices, pd.to_datetime(entry_times))):
        for j, h in enumerate(HORIZONS):
            fm = favorable_move_at(ep, et, ohlcv, h)
            if fm is not None:
                fm_matrix[i, j] = fm

    header = f"{'exit_reason':<16} {'size':>6} {'hold':>6} | " + \
             " | ".join(f"{h:>5}m" for h in HORIZONS)
    print(header)
    print("-" * len(header))

    for i in range(n):
        row = f"{exit_reasons[i]:<16} {size_btcs[i]:>6.3f} {hold_mins[i]:>6.0f} | "
        row += " | ".join(
            f"{fm_matrix[i, j]:>5.2f}" if not np.isnan(fm_matrix[i, j]) else "  N/A"
            for j in range(len(HORIZONS))
        )
        print(row)

    print("\n--- 全件 パーセンタイル ---")
    pct_header = f"{'pct':<8} | " + " | ".join(f"{h:>5}m" for h in HORIZONS)
    print(pct_header)
    for pct in [25, 50, 75, 90, 95]:
        vals = [np.nanpercentile(fm_matrix[:, j], pct) for j in range(len(HORIZONS))]
        row = f"p{pct:<7} | " + " | ".join(f"{v:>5.2f}" for v in vals)
        print(row)

    # ---- Section 2: TIME_EXIT 件のみ掘り下げ ----
    time_exit_mask = [r == "TIME_EXIT" for r in exit_reasons]
    te_indices = [i for i, m in enumerate(time_exit_mask) if m]
    print(f"\n" + "=" * 60)
    print(f"【Section 2】TIME_EXIT {len(te_indices)}件 — 待ち続けたら何分後にTP到達？")
    print(f"  TP_PCT={P23_TP_PCT_CURRENT} (現在値)")
    print("=" * 60)

    tp_reach_times = []
    for i in te_indices:
        et = pd.Timestamp(entry_times[i])
        ep = entry_prices[i]
        t = tp_reach_time(ep, et, ohlcv, P23_TP_PCT_CURRENT, max_horizon_min=1440)
        tp_reach_times.append(t)
        status = f"{t}min" if t is not None else "未到達(>1440min)"
        print(f"  entry={et}  hold={hold_mins[i]:.0f}min  net={net_usds[i]:.1f}$  TP到達: {status}")

    reached = [t for t in tp_reach_times if t is not None]
    not_reached = [t for t in tp_reach_times if t is None]
    print(f"\nTP到達: {len(reached)}/{len(te_indices)}件")
    if reached:
        print(f"  到達時間 中央値: {np.median(reached):.0f}min  最大: {max(reached)}min")
    print(f"未到達(>1440min): {len(not_reached)}件")

    # ---- Section 3: TP × TIME_EXIT の2次元EV試算 ----
    print(f"\n" + "=" * 60)
    print("【Section 3】TP × TIME_EXIT の2次元期待値試算")
    print("  (全P23トレードで TP_PCT/TIME_EXIT を変化させたシミュレーション)")
    print("  ※手数料は size_btc × entry_price × 0.0002 × 2 で概算")
    print("=" * 60)

    tp_candidates = [0.003, 0.005, 0.007, 0.010, 0.015, 0.020]
    te_candidates = [120, 180, 240, 360, 480, 720]

    # ヘッダー
    te_header = f"{'TP\\TIME':>10} | " + " | ".join(f"{te:>5}m" for te in te_candidates)
    print(te_header)
    print("-" * len(te_header))

    for tp_pct in tp_candidates:
        row_vals = []
        for te_min in te_candidates:
            total_net = 0.0
            for i, (ep, et) in enumerate(zip(entry_prices, pd.to_datetime(entry_times))):
                fee = size_btcs[i] * ep * 0.0002 * 2
                tp_price = ep * (1 - tp_pct)
                t = tp_reach_time(ep, et, ohlcv, tp_pct, max_horizon_min=te_min)
                if t is not None:
                    # TP到達
                    gross = size_btcs[i] * ep * tp_pct
                    total_net += gross - fee
                else:
                    # TIME_EXIT: 実際の価格で計算（te_min時点のclose）
                    n_bars_te = te_min // BAR_STEP
                    mask = ohlcv["timestamp"] >= pd.Timestamp(et)
                    start_idx = ohlcv.loc[mask, "_idx"].min()
                    if pd.isna(start_idx):
                        total_net += -fee
                        continue
                    exit_idx = min(int(start_idx) + n_bars_te, len(ohlcv) - 1)
                    exit_price = ohlcv.loc[exit_idx, "close"]
                    gross = size_btcs[i] * (ep - exit_price)
                    total_net += gross - fee
            row_vals.append(total_net)
        row = f"TP={tp_pct:.3f}   | " + " | ".join(f"{v:>+6.0f}" for v in row_vals)
        print(row)

    print(f"\n  【現在値】TP={P23_TP_PCT_CURRENT}  TIME_EXIT={P23_TIME_EXIT_CURRENT}min")

    # ---- Section 4: TP到達率まとめ ----
    print(f"\n" + "=" * 60)
    print("【Section 4】TP到達率（TP_PCT別）")
    print("=" * 60)
    tp_reach_header = f"{'TP_PCT':>10} | {'到達件数':>8} | {'到達率':>6} | {'NET/90d':>10}"
    print(tp_reach_header)
    print("-" * len(tp_reach_header))
    for tp_pct in tp_candidates:
        reach_count = 0
        total_net = 0.0
        for i, (ep, et) in enumerate(zip(entry_prices, pd.to_datetime(entry_times))):
            fee = size_btcs[i] * ep * 0.0002 * 2
            t = tp_reach_time(ep, et, ohlcv, tp_pct, max_horizon_min=24*60)  # 24h上限
            if t is not None:
                reach_count += 1
                gross = size_btcs[i] * ep * tp_pct
                total_net += gross - fee
            else:
                # 実際のexit_price（replay結果から）を使う
                gross = size_btcs[i] * (ep - entry_prices[i])  # placeholder
                total_net += -fee  # worst case
        rate = reach_count / n * 100
        print(f"TP={tp_pct:.3f}   | {reach_count:>8}件 | {rate:>5.1f}% | {total_net:>+10.0f}")

    print("\n完了。")


if __name__ == "__main__":
    replay_path = sys.argv[1] if len(sys.argv) > 1 else _DEFAULT_REPLAY
    ohlcv_path  = sys.argv[2] if len(sys.argv) > 2 else _DEFAULT_OHLCV
    main(replay_path, ohlcv_path)
