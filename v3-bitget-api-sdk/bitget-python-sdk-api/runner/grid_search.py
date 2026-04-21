#!/usr/bin/env python3
"""
runner/grid_search.py — Priority別パラメータグリッドサーチ

使い方:
    python3 runner/grid_search.py [csv_path]

デフォルトCSV: data/BTCUSDT-1m-binance-2026-04-06_90d.csv

GRID の内容を書き換えて使う。
TARGET_PRIORITY を変えれば他Priorityにも適用可。
"""
from __future__ import annotations

import copy
import itertools
import json
import pathlib
import sys
from typing import Any, Dict, List

_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from runner.replay_csv import run, preload

_PARAMS_PATH = _ROOT / "config" / "cat_params_v9.json"
_DEFAULT_CSV = str(_ROOT / "data" / "BTCUSDT-5m-2026-01-01_04-01_combined_90d.csv")

# ============================================================
# ▼ ここを変更して使う
# ============================================================
TARGET_PRIORITY = 3  # 詳細集計するPriority（NETソートの基準）

GRID: Dict[str, List[Any]] = {
    "LONG_PROFIT_LOCK_ENABLE": [0, 1],               # 0=無効(主仮説), 1=現状
    "P3_SL_PCT":               [0.010, 0.015, 0.020], # タイト, 現状, ワイド
    "P3_MFE_STALE_HOLD_MIN":   [240],                 # Phase1で方向確定
}

# P3・P23のみ有効（単一Priority精度調整）
FIXED_PARAMS: Dict[str, Any] = {
    "ENABLE_P2_LONG":   False,
    "ENABLE_P4_LONG":   False,
    "ENABLE_P22_SHORT": False,
    "ENABLE_P1_LONG":   False,
    "ENABLE_P21_SHORT": False,
}
# ============================================================


def _summarize(trades: List[Dict], priority: int) -> Dict:
    pt = [t for t in trades if t.get("priority") == priority]
    if not pt:
        return {"trades": 0, "net": 0.0, "tp_rate": 0.0, "time_exit": 0, "total_net": 0.0}
    net      = sum(t["net_usd"] for t in pt)
    tp       = sum(1 for t in pt if t["exit_reason"] == "TP_FILLED")
    te       = sum(1 for t in pt if t["exit_reason"] == "TIME_EXIT")
    all_net  = sum(t["net_usd"] for t in trades)
    return {
        "trades":    len(pt),
        "net":       net,
        "tp_rate":   tp / len(pt),
        "time_exit": te,
        "total_net": all_net,
    }


def main(csv_path: str) -> None:
    base_params = json.loads(_PARAMS_PATH.read_text())

    keys   = list(GRID.keys())
    combos = list(itertools.product(*[GRID[k] for k in keys]))

    print(f"Grid search: {len(combos)} combinations  |  Target: P{TARGET_PRIORITY}")
    print(f"CSV: {csv_path}")
    print("preprocess中（1回のみ）...")
    preloaded = preload(csv_path, base_params)
    print(f"preprocess完了。バーループ × {len(combos)} 開始\n")

    rows = []
    for idx, combo in enumerate(combos, 1):
        params = copy.deepcopy(base_params)
        params.update(FIXED_PARAMS)
        label  = {}
        for k, v in zip(keys, combo):
            if "." in k:
                outer, inner = k.split(".", 1)
                if outer in params and isinstance(params[outer], dict):
                    params[outer][inner] = v
                else:
                    params[k] = v
            else:
                params[k] = v
            label[k]  = v

        trades = run(csv_path, params, _preloaded=preloaded)
        s = _summarize(trades, TARGET_PRIORITY)
        rows.append({**label, **s})
        print(f"  [{idx:>2}/{len(combos)}] {label}  NET=${s['net']:.2f}  TP率={s['tp_rate']:.1%}  TIME_EXIT={s['time_exit']}")

    # P{TARGET_PRIORITY} NET 降順でソート
    rows.sort(key=lambda r: -r["net"])

    # ---- 結果テーブル ----
    print(f"\n{'='*70}")
    print(f"  GRID SEARCH RESULTS — P{TARGET_PRIORITY} NET 降順")
    print(f"{'='*70}")
    header = f"{'Rank':>4}  "
    for k in keys:
        header += f"{k:>26}  "
    header += f"{'P'+str(TARGET_PRIORITY)+'_NET':>10}  {'TP率':>6}  {'TIME_EXIT':>9}  {'全体NET':>10}"
    print(header)
    print("-" * len(header))

    for rank, r in enumerate(rows, 1):
        line = f"{rank:>4}  "
        for k in keys:
            line += f"{str(r[k]):>26}  "
        line += f"${r['net']:>9.2f}  {r['tp_rate']:>5.1%}  {r['time_exit']:>9}  ${r['total_net']:>9.2f}"
        print(line)

    best = rows[0]
    print(f"\n✅ Best combination:")
    for k in keys:
        print(f"   {k} = {best[k]}")
    print(f"   → P{TARGET_PRIORITY} NET=${best['net']:.2f}  TP率={best['tp_rate']:.1%}  TIME_EXIT={best['time_exit']}  全体NET=${best['total_net']:.2f}")


if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else _DEFAULT_CSV
    main(csv_path)
