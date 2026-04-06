#!/usr/bin/env python3
"""
runner/grid_signal.py — RSI 閾値グリッドサーチ

使い方:
    cd v3-bitget-api-sdk/bitget-python-sdk-api
    .venv/bin/python3 runner/grid_signal.py

RSI_OS / RSI_OB を対称に変化させてシグナル件数・TP率・NET/日を比較する。
TP/SL は cat_params_v10.json の値を固定で使用。
"""
from __future__ import annotations

import json
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import runner.replay_v10 as replay_mod
from runner.replay_v10 import _load_csv

_PARAMS_PATH = _ROOT / "config" / "cat_params_v10.json"
_DATA_PATH   = _ROOT / "data" / "BTCUSDT-5m-2025-10-03_04-01_combined_180d.csv"

BTC_REF = 84_000

# RSI_OS 候補（RSI_OB = 100 - RSI_OS で対称）
RSI_OS_CANDIDATES = [50, 45, 40, 35, 30]


def run_with_rsi(rsi_os: float) -> list[dict]:
    rsi_ob = 100 - rsi_os
    original = replay_mod._load_params

    def _patched():
        p = original()
        p["RSI_OS"] = rsi_os
        p["RSI_OB"] = rsi_ob
        return p

    replay_mod._load_params = _patched
    try:
        return replay_mod.run_replay(str(_DATA_PATH))
    finally:
        replay_mod._load_params = original


def main() -> None:
    import pandas as pd

    with open(_PARAMS_PATH) as f:
        base = json.load(f)
    current_os = float(base.get("RSI_OS", 30))
    tp_pct = float(base["TP_PCT"])
    sl_pct = float(base["SL_PCT"])

    df_raw = _load_csv(str(_DATA_PATH))
    days   = (df_raw["timestamp_ms"].max() - df_raw["timestamp_ms"].min()) / (1000 * 60 * 60 * 24)

    print(f"\n{'='*72}")
    print(f"  RSI 閾値グリッドサーチ  ({_DATA_PATH.name}, {days:.0f}日)")
    print(f"  TP={tp_pct:.4f}(≈${tp_pct*BTC_REF:.0f})  SL={sl_pct:.4f}(≈${sl_pct*BTC_REF:.0f})  固定")
    print(f"{'='*72}")
    print(f"  {'RSI_OS/OB':>10}  {'件数':>6}  {'件/日':>6}  {'TP率':>7}  {'GROSS/日':>10}  {'NET/日':>10}")
    print(f"  {'-'*68}")

    for rsi_os in RSI_OS_CANDIDATES:
        rsi_ob = 100 - rsi_os
        trades = run_with_rsi(rsi_os)
        marker = " ◀ current" if rsi_os == current_os else ""

        if not trades:
            print(f"  {rsi_os:>3}/{rsi_ob:<3}{'':>5}  トレードなし{marker}")
            continue

        df      = pd.DataFrame(trades)
        total   = len(df)
        tp_n    = (df["exit_reason"] == "TP_FILLED").sum()
        tp_r    = tp_n / total * 100
        gross_d = df["gross_usd"].sum() / days
        net_d   = df["net_usd"].sum() / days

        print(f"  {rsi_os:>3}/{rsi_ob:<6}  {total:>6,}  {total/days:>6.1f}"
              f"  {tp_r:>6.1f}%  {gross_d:>+10.2f}$  {net_d:>+10.2f}${marker}")

    print(f"{'='*72}")


if __name__ == "__main__":
    main()
