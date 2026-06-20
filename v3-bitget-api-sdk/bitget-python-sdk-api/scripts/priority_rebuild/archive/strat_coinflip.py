#!/usr/bin/env python3
"""strat_coinflip.py — 配管確認用の捨て戦略（コイン投げ・seed 固定）

目的: 「戦略 → 売買記録 CSV → score.py（審判）→ 数字」の配管が正しいか確認するためだけの
使い捨て戦略。方向を seed 固定の乱数で決める＝エッジなし → score.py は **明確にマイナス**を
返すはず（gross ≒ 0 にコストだけ乗る）。プラスや 0 が出たら配管バグ。確認後は捨てる。

これは「選手」ではなく「配管テスト用ダミー」。残す価値はない（PDCA の正式な選手は別途）。
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
CSV = REPO / "data" / "BTCUSDT-5m-bitget-2021-04-01_2026-03-31_5y.csv"
SIZE_BTC = 0.024


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-04-01")
    ap.add_argument("--end", default="2025-12-31")
    ap.add_argument("--spacing", type=int, default=50, help="何本ごとにエントリーするか")
    ap.add_argument("--hold", type=int, default=12, help="保有本数（12=1h）")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=str(REPO / "results" / "priority_rebuild" / "ratchet" / "trades_coinflip.csv"))
    a = ap.parse_args()

    df = pd.read_csv(CSV, parse_dates=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    m = (df["timestamp"] >= pd.Timestamp(a.start)) & (df["timestamp"] < pd.Timestamp(a.end) + pd.Timedelta(days=1))
    df = df[m].reset_index(drop=True)

    rng = np.random.default_rng(a.seed)
    rows = []
    i = 0
    n = len(df)
    while i + a.hold < n:
        side = "LONG" if rng.random() < 0.5 else "SHORT"
        entry = df.iloc[i]
        ex = df.iloc[i + a.hold]
        rows.append({
            "entry_time": entry["timestamp"], "exit_time": ex["timestamp"],
            "side": side, "size_btc": SIZE_BTC,
            "entry_price": float(entry["close"]), "exit_price": float(ex["close"]),
            "exit_reason": "TIME",
        })
        i += a.spacing

    out = pd.DataFrame(rows)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(a.out, index=False)
    print(f"[捨て戦略 coinflip] {len(out)} trades "
          f"({a.start}〜{a.end} / {a.spacing}本ごと / 保有{a.hold}本 / seed{a.seed}) → {a.out}")


if __name__ == "__main__":
    main()
