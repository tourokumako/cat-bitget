#!/usr/bin/env python3
"""
runner/grid_tp.py — TP_PCT グリッドサーチ

使い方:
    cd v3-bitget-api-sdk/bitget-python-sdk-api
    .venv/bin/python3 runner/grid_tp.py

replay_v10.py を変更せず、_load_params をパッチして TP 値だけ差し替えて実行する。
SL_PCT は cat_params_v10.json の値を使用（固定）。
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

# BTC 参考価格（ドル換算表示用）
BTC_REF = 84_000

# テストする TP_PCT 候補
TP_CANDIDATES = [0.0005, 0.0006, 0.0008, 0.0010, 0.0012, 0.0015]


def run_with_tp(tp_pct: float) -> list[dict]:
    """_load_params をパッチして TP_PCT だけ上書きしてリプレイ実行。"""
    original = replay_mod._load_params

    def _patched():
        p = original()
        p["TP_PCT"] = tp_pct
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
    current_tp = float(base["TP_PCT"])
    current_sl = float(base["SL_PCT"])

    df_raw = _load_csv(str(_DATA_PATH))
    days   = (df_raw["timestamp_ms"].max() - df_raw["timestamp_ms"].min()) / (1000 * 60 * 60 * 24)

    sl_usd = current_sl * BTC_REF

    print(f"\n{'='*74}")
    print(f"  TP グリッドサーチ  ({_DATA_PATH.name}, {days:.0f}日)")
    print(f"  SL 固定: {current_sl:.4f} (≈${sl_usd:.0f} @BTC${BTC_REF:,})")
    print(f"{'='*74}")
    header = f"  {'TP_PCT':>8}  {'≈$TP':>6}  {'件数':>6}  {'件/日':>6}  {'TP率':>7}  {'GROSS/日':>10}  {'NET/日':>10}"
    print(header)
    print(f"  {'-'*70}")

    for tp_pct in TP_CANDIDATES:
        tp_usd = tp_pct * BTC_REF
        trades = run_with_tp(tp_pct)
        marker = " ◀ current" if tp_pct == current_tp else ""

        if not trades:
            print(f"  {tp_pct:>8.4f}  {tp_usd:>5.0f}$  トレードなし{marker}")
            continue

        df = pd.DataFrame(trades)
        total   = len(df)
        tp_n    = (df["exit_reason"] == "TP_FILLED").sum()
        tp_r    = tp_n / total * 100
        gross_d = df["gross_usd"].sum() / days
        net_d   = df["net_usd"].sum() / days

        print(f"  {tp_pct:>8.4f}  {tp_usd:>5.0f}$  {total:>6,}  {total/days:>6.1f}"
              f"  {tp_r:>6.1f}%  {gross_d:>+10.2f}$  {net_d:>+10.2f}${marker}")

    print(f"{'='*74}")


if __name__ == "__main__":
    main()
