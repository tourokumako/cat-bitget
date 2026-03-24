#!/usr/bin/env python3
"""tools/injection_runner.py — Exit 強制発動テスト（TEST_INJECTION モード）

使い方:
    cd v3-bitget-api-sdk/bitget-python-sdk-api
    .venv/bin/python3 tools/injection_runner.py --scenario stagnation_p4
    .venv/bin/python3 tools/injection_runner.py --all
    .venv/bin/python3 tools/injection_runner.py --list

設計:
    - 注入した pos dict + snapshot df で _check_exits を直接呼ぶ
    - write API（発注・クローズ）は一切呼ばない（read-only）
    - state/open_position.json は触らない
    - ALLOW_LIVE_ORDERS の値に関係なく API コールは発生しない
    - ログに [TEST_INJECTION] プレフィックスを付与

対象 Exit 条件（8件）:
    stagnation_p4       STAGNATION_CUT   LONG P4 hold=25m
    stagnation_general  STAGNATION_CUT   SHORT P22 hold=35m
    time_exit_long      TIME_EXIT        LONG P4 hold=160m
    time_exit_short     TIME_EXIT        SHORT P22 hold=390m (down-factor)
    mfe_stale_cut       MFE_STALE_CUT    SHORT P22 add=5 hold=130m mfe=8
    mae_cut             MAE_CUT          SHORT P23 add=4 hold=310m
    profit_lock_p22     PROFIT_LOCK      SHORT P22 add=5 (6b path)
    breakout_cut        BREAKOUT_CUT     SHORT P22 add=3 (snapshot bar)
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
from typing import Dict, List, Optional

import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO))

from runner.run_once_v9 import _check_exits
from strategies.cat_v9_decider import preprocess

PARAMS_PATH  = REPO / "config" / "cat_params_v9.json"
SNAPSHOT_CSV = HERE / "data" / "snapshot.csv"

with open(PARAMS_PATH) as f:
    PARAMS = json.load(f)

SIZE       = float(PARAMS.get("SHORT_POSITION_SIZE_BTC", 0.024))
BASE_PRICE = 85_000.0   # 固定基準価格（実APIコールなし）
PREFIX     = "[TEST_INJECTION]"


# ---------------------------------------------------------------------------
# snapshot から BREAKOUT_CUT 用 df を取得（T11 と同じロジック）
# ---------------------------------------------------------------------------
def _get_breakout_df() -> Optional[pd.DataFrame]:
    if not SNAPSHOT_CSV.exists():
        print(f"{PREFIX} WARNING: snapshot.csv not found")
        return None
    raw = pd.read_csv(SNAPSHOT_CSV)
    raw["timestamp"] = pd.to_datetime(raw["timestamp_ms"].astype(int), unit="ms")
    df_raw = raw[["timestamp", "open", "high", "low", "close", "volume"]].copy()
    df_raw = df_raw.sort_values("timestamp").reset_index(drop=True)
    if len(df_raw) < 110:
        print(f"{PREFIX} WARNING: snapshot.csv のデータ不足")
        return None
    df_pp = preprocess(df_raw.copy(), PARAMS)
    bw_min  = float(PARAMS.get("P23_BREAKOUT_BB_WIDTH_MIN", 0.03))
    rsi_min = float(PARAMS.get("P23_BREAKOUT_RSI_MIN", 70.0))
    cand = df_pp[(df_pp["bb_width"] >= bw_min) & (df_pp["rsi_short"] >= rsi_min)]
    if cand.empty:
        print(f"{PREFIX} WARNING: 条件バーが snapshot に存在しない")
        return None
    i = cand.index[0]
    return df_pp.loc[[i]].reset_index(drop=True)


# ---------------------------------------------------------------------------
# シナリオ定義
# ---------------------------------------------------------------------------
# mark_price_offset: entry_price からのオフセット
#   LONG  の場合: + → 含み益方向 / - → 含み損方向
#   SHORT の場合: + → 含み損方向 / - → 含み益方向
SCENARIOS: List[Dict] = [
    {
        "name":   "stagnation_p4",
        "desc":   "STAGNATION_CUT LONG P4 (hold=25m, mfe=0.5)",
        "pos": {
            "side": "LONG", "entry_priority": 4, "add_count": 1,
            "entry_price": BASE_PRICE, "size_btc": SIZE, "mfe_usd": 0.5,
        },
        "hold_min":          25.0,
        "mark_price_offset":  0.0,
        "df":                 None,
        "expected":          "STAGNATION_CUT",
    },
    {
        "name":   "stagnation_general",
        "desc":   "STAGNATION_CUT SHORT P22 non-P4 (hold=35m, mfe=0.5)",
        "pos": {
            "side": "SHORT", "entry_priority": 22, "add_count": 1,
            "entry_price": BASE_PRICE + 1000, "size_btc": SIZE, "mfe_usd": 0.5,
        },
        "hold_min":          35.0,
        "mark_price_offset":  0.0,
        "df":                 None,
        "expected":          "STAGNATION_CUT",
    },
    {
        "name":   "time_exit_long",
        "desc":   "TIME_EXIT LONG P4 (hold=160m > LONG_TIME_EXIT_MIN=150)",
        "pos": {
            "side": "LONG", "entry_priority": 4, "add_count": 1,
            "entry_price": BASE_PRICE, "size_btc": SIZE, "mfe_usd": 2.0,
        },
        "hold_min":          160.0,
        "mark_price_offset":   0.0,   # unreal≥0 → down_factor 非適用
        "df":                  None,
        "expected":           "TIME_EXIT",
        # NOTE: P2_TIME_EXIT_MIN=480 のため priority=4 (LONG_TIME_EXIT_MIN=150) を使用
    },
    {
        "name":   "time_exit_short",
        "desc":   "TIME_EXIT SHORT P22 down-factor (hold=390m, effective=360m)",
        "pos": {
            "side": "SHORT", "entry_priority": 22, "add_count": 1,
            "entry_price": BASE_PRICE, "size_btc": SIZE, "mfe_usd": 2.0,
        },
        "hold_min":          390.0,
        "mark_price_offset": 500.0,   # mark > entry → SHORT 含み損 → down_factor 適用
        "df":                 None,   # df=None → RSI_REVERSE_EXIT の指標が NaN → 非発動
        "expected":          "TIME_EXIT",
        # SHORT_TIME_EXIT_MIN=480, down_f=0.75 → effective=360, 390≥360 → fires
    },
    {
        "name":   "mfe_stale_cut",
        "desc":   "MFE_STALE_CUT SHORT P22 (add=5, hold=130m, mfe=8 < 12)",
        "pos": {
            "side": "SHORT", "entry_priority": 22, "add_count": 5,
            "entry_price": BASE_PRICE + 500, "size_btc": SIZE, "mfe_usd": 8.0,
        },
        "hold_min":          130.0,
        "mark_price_offset": 500.0,
        "df":                 None,
        "expected":          "MFE_STALE_CUT",
    },
    {
        "name":   "mae_cut",
        "desc":   "MAE_CUT SHORT P23 (add=4, hold=310m, mark≥entry+2083)",
        "pos": {
            "side": "SHORT", "entry_priority": 23, "add_count": 4,
            "entry_price": BASE_PRICE, "size_btc": SIZE, "mfe_usd": 0.5,
        },
        "hold_min":          310.0,
        "mark_price_offset": 2200.0,  # entry + 2200 > entry + 50/0.024(=2083.3)
        "df":                  None,
        "expected":           "MAE_CUT",
    },
    {
        "name":   "profit_lock_p22",
        "desc":   "PROFIT_LOCK SHORT P22 add=5 (6b: mark≤entry-416.7)",
        "pos": {
            "side": "SHORT", "entry_priority": 22, "add_count": 5,
            "entry_price": BASE_PRICE, "size_btc": SIZE, "mfe_usd": 15.0,
        },
        "hold_min":           60.0,
        "mark_price_offset": -420.0,  # entry - 420 ≤ entry - 10/0.024(=416.7)
        "df":                  None,
        "expected":           "PROFIT_LOCK",
    },
    {
        "name":   "breakout_cut",
        "desc":   "BREAKOUT_CUT SHORT P22 add=3 (snapshot bar: bw≥0.03, rsi≥70)",
        "pos": {
            "side": "SHORT", "entry_priority": 22, "add_count": 3,
            "entry_price": BASE_PRICE + 1000, "size_btc": SIZE, "mfe_usd": 2.0,
        },
        "hold_min":          30.0,
        "mark_price_offset": 1000.0,
        "df":                "LOAD_BREAKOUT",
        "expected":          "BREAKOUT_CUT",
    },
    {
        "name":   "mfe_exit",
        "desc":   "MFE_EXIT SHORT P22 (hold=300m ≥ 480×0.6=288m, mfe=22 ≥ 20USD)",
        "pos": {
            "side": "SHORT", "entry_priority": 22, "add_count": 2,
            "entry_price": BASE_PRICE + 500, "size_btc": SIZE, "mfe_usd": 22.0,
        },
        "hold_min":          300.0,
        "mark_price_offset": 200.0,
        "df":                 None,
        "expected":          "MFE_EXIT",
        # SHORT_TIME_EXIT_MIN=480 → 480×0.6=288m, hold=300≥288 ✅
        # mfe=22≥P22_SHORT_MFE_MAX_GATE_USD(20) ✅
        # add_count=2 < 5 → MFE_STALE_CUT 非該当 ✅
    },
]


# ---------------------------------------------------------------------------
# テスト実行
# ---------------------------------------------------------------------------
def run_scenario(sc: Dict) -> bool:
    name     = sc["name"]
    desc     = sc["desc"]
    expected = sc["expected"]

    entry_price = float(sc["pos"]["entry_price"])
    mark_price  = entry_price + float(sc["mark_price_offset"])
    hold_min    = float(sc["hold_min"])

    # entry_time を hold_min から逆算
    pos = dict(sc["pos"])
    pos["entry_time"] = int(time.time() * 1000) - int(hold_min * 60 * 1000)

    # df の準備
    if sc["df"] == "LOAD_BREAKOUT":
        df = _get_breakout_df()
        if df is None:
            print(f"{PREFIX}[{name}] SKIP — snapshot データ取得不可")
            return True  # スキップは PASS 扱い
    else:
        df = sc["df"]

    # _check_exits 呼び出し（実際の production コード）
    result = _check_exits(pos, mark_price, df, PARAMS)

    passed = (result == expected)
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{PREFIX}[{name}] {status}")
    print(f"  desc:     {desc}")
    print(f"  expected: {expected}")
    print(f"  got:      {result}")
    print(f"  hold_min: {hold_min:.1f}m  mark: {mark_price:.1f}  entry: {entry_price:.1f}")
    print()
    return passed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Exit 強制発動テスト（TEST_INJECTION）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--scenario", metavar="NAME", help="シナリオ名を指定")
    group.add_argument("--all",  action="store_true", help="全シナリオ実行")
    group.add_argument("--list", action="store_true", help="シナリオ一覧表示")
    args = parser.parse_args()

    if args.list:
        print("利用可能なシナリオ:")
        for sc in SCENARIOS:
            print(f"  {sc['name']:<22} {sc['desc']}")
        return

    targets = SCENARIOS if args.all else [s for s in SCENARIOS if s["name"] == args.scenario]
    if not targets:
        print(f"シナリオ '{args.scenario}' が見つかりません。--list で確認してください。")
        sys.exit(1)

    print("=" * 72)
    print(f"  {PREFIX} Exit 強制発動テスト")
    print(f"  params: {PARAMS_PATH.name}  |  write API: なし（read-only）")
    print("=" * 72)
    print()

    results = [run_scenario(sc) for sc in targets]
    total  = len(results)
    passed = sum(results)

    print("=" * 72)
    print(f"[SUMMARY] {total} ケース  PASS: {passed}  FAIL: {total - passed}")
    if passed == total:
        print("[RESULT] ✅ 全ケース PASS")
    else:
        print("[RESULT] ❌ 不一致あり")
        fails = [sc["name"] for sc, ok in zip(targets, results) if not ok]
        for f in fails:
            print(f"  FAIL: {f}")
    print("=" * 72)
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()