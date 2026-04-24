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

from runner.replay_csv import run, preload, _build_regime_map

_PARAMS_PATH = _ROOT / "config" / "cat_params_v9.json"
_DEFAULT_CSV = str(_ROOT / "data" / "BTCUSDT-5m-2025-10-03_04-01_combined_180d.csv")

# ============================================================
# ▼ ここを変更して使う
# ============================================================
TARGET_PRIORITY = 23     # 詳細集計するPriority（NETソートの基準）
TARGET_REGIME   = "downtrend"  # P21=downtrend / P4=range / P24=uptrend / None=全日数

# P23 TIME_EXIT_MIN グリッド（2026-04-24・365d検証）
# ベースライン: +$18.74/dt-day（P23_TIME_EXIT_MIN=480・実効240min）
# 問題: TIME_EXIT 43件(-$2476/-$17.32/dt-day) add=3,4,5 に集中（avg -$58~-$94）
# 仮説: 実効180minで早期脱出→add=3,4,5 の積み上げを防ぎ損失削減
# リスク: STOCH_REVERSE_EXIT（181-240min帯 10件+$551）の奪取リスクあり
# 注: SHORT_TIME_EXIT_DOWN_FACTOR=0.5が適用されるので実効=MIN×0.5
GRID: Dict[str, List[Any]] = {
    "P23_TIME_EXIT_MIN": [300, 360, 420, 480],  # 実効 150/180/210/240分
}

# [旧: P21 ATR14_MIN グリッド（2026-04-24 結論: ATR14_MIN=150維持）]
# GRID = { "P21_ATR14_MIN": [50, 80, 100, 120, 150] }

# [旧: P23 PROFIT_LOCK グリッド（2026-04-24 REJECTED・L-111）]
# GRID = {
#     "P23_SHORT_PROFIT_LOCK_ENABLE":  [0, 1],
#     "P23_SHORT_PROFIT_LOCK_ARM_USD": [20, 22],
#     "P23_SHORT_PROFIT_LOCK_USD":     [5, 8],
# }

# [旧: P2-LONG Phase 1 ADX_MAX × ATR14_MIN グリッド（2026-04-23 完了）]
# GRID = {
#     "P2_ADX_MAX":   [50, 60, 999],
#     "P2_ATR14_MIN": [100, 140, 180],
# }

# P23のみ有効
FIXED_PARAMS: Dict[str, Any] = {
    "ENABLE_P21_SHORT":  False,
    "ENABLE_P23_SHORT":  True,
    "ENABLE_P2_LONG":    False,
    "ENABLE_P3_LONG":    False,
    "ENABLE_P4_LONG":    False,
    "ENABLE_P22_SHORT":  False,
    "ENABLE_P1_LONG":    False,
    "ENABLE_P24_SHORT":  False,
}

REGIME_SWITCH = True  # P2はDOWNTREND限定で評価
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


def _count_regime_days(csv_path: str, regime: str) -> int:
    """対象レジームの日数を返す。TARGET_REGIME=None なら CSV の総日数。"""
    if regime is None:
        df = pathlib.Path(csv_path)
        import pandas as pd
        return len(pd.read_csv(df, usecols=["timestamp"])["timestamp"].str[:10].unique()) if df.exists() else 1
    try:
        regime_map = _build_regime_map(csv_path)
        days = {str(k.date()) for k, v in regime_map.items() if v == regime}
        return len(days) or 1
    except Exception:
        return 1


def main(csv_path: str) -> None:
    base_params = json.loads(_PARAMS_PATH.read_text())

    keys   = list(GRID.keys())
    combos = list(itertools.product(*[GRID[k] for k in keys]))

    regime_days = _count_regime_days(csv_path, TARGET_REGIME)
    regime_label = f"{TARGET_REGIME}({regime_days}日)" if TARGET_REGIME else f"全({regime_days}日)"

    print(f"Grid search: {len(combos)} combinations  |  Target: P{TARGET_PRIORITY}  |  評価基準: $/day [{regime_label}]")
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

        trades = run(csv_path, params, _preloaded=preloaded, regime_switch=REGIME_SWITCH)
        s = _summarize(trades, TARGET_PRIORITY)
        per_day = s["net"] / regime_days
        rows.append({**label, **s, "per_day": per_day})
        print(f"  [{idx:>2}/{len(combos)}] {label}  "
              f"NET=${s['net']:.2f}({per_day:+.2f}/day)  TP率={s['tp_rate']:.1%}  TIME_EXIT={s['time_exit']}")

    # P{TARGET_PRIORITY} $/regime-day 降順でソート
    rows.sort(key=lambda r: -r["per_day"])

    # ---- 結果テーブル ----
    print(f"\n{'='*80}")
    print(f"  GRID SEARCH RESULTS — P{TARGET_PRIORITY}  [{regime_label} $/day 降順]")
    print(f"{'='*80}")
    header = f"{'Rank':>4}  "
    for k in keys:
        header += f"{k:>28}  "
    header += f"{'$/'+TARGET_REGIME[:2]+'day':>10}  {'P'+str(TARGET_PRIORITY)+'_NET':>10}  {'TP率':>6}  {'TIME_EXIT':>9}"
    print(header)
    print("-" * len(header))

    for rank, r in enumerate(rows, 1):
        line = f"{rank:>4}  "
        for k in keys:
            line += f"{str(r[k]):>28}  "
        line += f"{r['per_day']:>+9.2f}  ${r['net']:>9.2f}  {r['tp_rate']:>5.1%}  {r['time_exit']:>9}"
        print(line)

    best = rows[0]
    print(f"\n✅ Best combination:")
    for k in keys:
        print(f"   {k} = {best[k]}")
    print(f"   → {regime_label} $/day={best['per_day']:+.2f}  P{TARGET_PRIORITY} NET=${best['net']:.2f}  TP率={best['tp_rate']:.1%}  TIME_EXIT={best['time_exit']}")


if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else _DEFAULT_CSV
    main(csv_path)
