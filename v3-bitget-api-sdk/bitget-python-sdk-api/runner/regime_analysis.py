#!/usr/bin/env python3
"""
runner/regime_analysis.py — 相場レジーム × Priority別パフォーマンス分析

目的:
  各Priorityがどの相場条件（トレンド方向・強度・ボラ）で機能するかを分析する。
  相場切り替えルール設計のための探索的分析。

使い方:
  python3 runner/regime_analysis.py [csv_path]

デフォルト: data/BTCUSDT-5m-2025-04-01_03-31_365d.csv
"""
from __future__ import annotations

import json
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd
import ta

from runner.replay_csv import run, preload

_PARAMS_PATH = _ROOT / "config" / "cat_params_v9.json"
_DEFAULT_CSV = str(_ROOT / "data" / "BTCUSDT-5m-2025-04-01_03-31_365d.csv")
_DAILY_WARMUP = str(_ROOT / "data" / "BTCUSDT-1d-2024-09-01_04-15_227d.csv")

# 全Priority有効化（分析専用）
_ALL_ENABLED = {
    "ENABLE_P1_LONG":   True,
    "ENABLE_P2_LONG":   True,
    "ENABLE_P3_LONG":   True,
    "ENABLE_P4_LONG":   True,
    "ENABLE_P21_SHORT": True,
    "ENABLE_P22_SHORT": True,
    "ENABLE_P23_SHORT": True,
    "ENABLE_P24_SHORT": True,
}


def build_daily_regime(csv_5m: str) -> pd.DataFrame:
    """5mデータ（+warmup日足）から日次レジーム指標を計算して返す。"""
    # warm-up日足
    dw = pd.read_csv(_DAILY_WARMUP)
    dw["ts"] = pd.to_datetime(dw["timestamp"])
    dw["close"] = pd.to_numeric(dw["close"], errors="coerce")
    dw["high"]  = pd.to_numeric(dw["high"],  errors="coerce")
    dw["low"]   = pd.to_numeric(dw["low"],   errors="coerce")
    dw = dw.set_index("ts").sort_index()

    # 5m → 日足
    df5 = pd.read_csv(csv_5m)
    df5["ts"]    = pd.to_datetime(df5["timestamp"])
    df5["close"] = pd.to_numeric(df5["close"], errors="coerce")
    df5["high"]  = pd.to_numeric(df5["high"],  errors="coerce")
    df5["low"]   = pd.to_numeric(df5["low"],   errors="coerce")
    df5 = df5.set_index("ts").sort_index()
    daily_5m = df5.resample("D").agg({"close": "last", "high": "max", "low": "min"}).dropna()

    # 結合
    combined = pd.concat([
        dw[["close", "high", "low"]],
        daily_5m[["close", "high", "low"]]
    ])
    combined = combined[~combined.index.duplicated(keep="last")].sort_index()
    combined["close"] = pd.to_numeric(combined["close"], errors="coerce")
    combined["high"]  = pd.to_numeric(combined["high"],  errors="coerce")
    combined["low"]   = pd.to_numeric(combined["low"],   errors="coerce")

    # MA: 50/70/100/150/200
    for n in [50, 70, 100, 150, 200]:
        combined[f"ma{n}"] = combined["close"].rolling(n, min_periods=n).mean()
        combined[f"ma{n}_slope"] = combined[f"ma{n}"].diff(5)  # 5日変化

    # ADX (14)
    adx_ind = ta.trend.ADXIndicator(combined["high"], combined["low"], combined["close"], window=14)
    combined["adx_d"] = adx_ind.adx()

    # BB width (20日)
    bb = ta.volatility.BollingerBands(combined["close"], window=20)
    combined["bb_width_d"] = (bb.bollinger_hband() - bb.bollinger_lband()) / bb.bollinger_mavg()

    # 日次リターン
    combined["ret_1d"] = combined["close"].pct_change()

    # 365d期間のみ
    start = df5.index.min().normalize()
    regime_df = combined[combined.index >= start].copy()

    return regime_df


def classify_trend(row: pd.Series, ma_col: str) -> str:
    """MA方向 + ADXでレジーム分類。"""
    slope = row.get(f"{ma_col}_slope", np.nan)
    adx   = row.get("adx_d", np.nan)
    close = row.get("close", np.nan)
    ma    = row.get(ma_col, np.nan)

    if pd.isna(slope) or pd.isna(adx) or pd.isna(close) or pd.isna(ma):
        return "unknown"

    trending = adx >= 20
    if not trending:
        return "range"
    if slope > 0 and close > ma:
        return "uptrend"
    if slope < 0 and close < ma:
        return "downtrend"
    return "mixed"


def attach_regime(trades: list, regime_df: pd.DataFrame, ma_col: str) -> pd.DataFrame:
    """各トレードにエントリー日のレジーム情報を付与。"""
    df = pd.DataFrame(trades)
    df["entry_date"] = pd.to_datetime(df["entry_time"]).dt.normalize()

    regime_cols = ["close", ma_col, f"{ma_col}_slope", "adx_d", "bb_width_d", "ret_1d"]
    regime_snap = regime_df[regime_cols].copy()
    regime_snap.index = pd.to_datetime(regime_snap.index).normalize()
    regime_snap = regime_snap.reset_index().rename(columns={"index": "entry_date", "ts": "entry_date"})
    regime_snap["entry_date"] = pd.to_datetime(regime_snap["entry_date"]).dt.normalize()

    df = pd.merge(df, regime_snap, on="entry_date", how="left")
    df["regime"] = df.apply(lambda r: classify_trend(r, ma_col), axis=1)
    return df


def print_priority_by_regime(df: pd.DataFrame, ma_col: str) -> None:
    print(f"\n{'='*70}")
    print(f"  Priority別 × レジーム別パフォーマンス  (MA基準: {ma_col})")
    print(f"{'='*70}")

    regimes = ["uptrend", "downtrend", "range", "mixed", "unknown"]
    priorities = sorted(df["priority"].unique())

    for pri in priorities:
        pt = df[df["priority"] == pri]
        total_net = pt["net_usd"].sum()
        tp_rate   = (pt["exit_reason"] == "TP_FILLED").mean()
        print(f"\n  [P{pri}]  {len(pt)}件  NET=${total_net:.1f}  TP率={tp_rate:.1%}")

        for reg in regimes:
            sub = pt[pt["regime"] == reg]
            if len(sub) == 0:
                continue
            net = sub["net_usd"].sum()
            tp  = (sub["exit_reason"] == "TP_FILLED").mean()
            print(f"    {reg:10s}: {len(sub):3d}件  NET=${net:7.1f}  TP率={tp:.1%}  /day=${net/365:.2f}")


def print_regime_summary(regime_df: pd.DataFrame, ma_col: str) -> None:
    """365d中の各レジームの日数割合。"""
    regime_df = regime_df.copy()
    regime_df["regime"] = regime_df.apply(lambda r: classify_trend(r, ma_col), axis=1)
    counts = regime_df["regime"].value_counts()
    total  = len(regime_df)
    print(f"\n  365d レジーム日数分布 ({ma_col}):")
    for reg, cnt in counts.items():
        print(f"    {reg:10s}: {cnt:3d}日  ({cnt/total:.1%})")


def main(csv_path: str) -> None:
    print(f"CSV: {csv_path}")
    print("全Priority有効化で365d replay 実行中...")

    base_params = json.loads(_PARAMS_PATH.read_text())
    params = {**base_params, **_ALL_ENABLED}

    preloaded = preload(csv_path, params)
    trades = run(csv_path, params, _preloaded=preloaded)
    print(f"トレード件数: {len(trades)}")

    print("日足レジーム指標計算中...")
    regime_df = build_daily_regime(csv_path)

    # MA期間別に分析
    for ma_col in ["ma50", "ma70", "ma100", "ma150", "ma200"]:
        print_regime_summary(regime_df, ma_col)
        df = attach_regime(trades, regime_df, ma_col)
        print_priority_by_regime(df, ma_col)

    # ADX分位別分析（補足）
    print(f"\n{'='*70}")
    print("  日足ADX分位別 Priority NET（全MA共通）")
    df_all = attach_regime(trades, regime_df, "ma70")
    df_all["adx_bin"] = pd.cut(df_all["adx_d"], bins=[0, 15, 25, 35, 999],
                                labels=["≤15(弱)", "15-25(中)", "25-35(強)", "35+(激強)"])
    for pri in sorted(df_all["priority"].unique()):
        pt = df_all[df_all["priority"] == pri]
        print(f"\n  [P{pri}] ADX分位別:")
        for bin_label, sub in pt.groupby("adx_bin", observed=True):
            net = sub["net_usd"].sum()
            tp  = (sub["exit_reason"] == "TP_FILLED").mean()
            print(f"    ADX {bin_label}: {len(sub):3d}件  NET=${net:7.1f}  TP率={tp:.1%}")


if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else _DEFAULT_CSV
    main(csv_path)
