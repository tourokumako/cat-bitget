#!/usr/bin/env python3
"""tools/exit_compare.py — Exit Parity: 原本 vs 移植版 Exit条件比較

使い方:
    cd v3-bitget-api-sdk/bitget-python-sdk-api
    .venv/bin/python3 tools/exit_compare.py

設計:
  - 1ケース1目的: 固定ポジション + 固定バーで各Exit条件を個別テスト
  - 原本条件 (_orig_exit): CAT_v9_regime.py run_backtest の exit 条件を単バー版で実装
  - 移植版 (_ported_exit): run_once_v9.py の _check_exits をコピー
  - 両者の exit_reason を正規化して比較

既知の設計差異（スコープ外・本スクリプトでは検証しない）:
  - PROFIT_LOCK LONG: 原本=arm到達barで即発動 / 移植版=mfe累積後に価格後退で発動
  - P4_BREAK_EXIT: 原本=entry+hold_bars の1bar限定 / 移植版=±5min窓

ゲート条件 (全てMATCHで Phase 2c へ):
  BREAKOUT_CUT / MFE_STALE_CUT / MAE_CUT / PROFIT_LOCK(P22/P23_SHORT) /
  TIME_EXIT / STAGNATION_CUT
"""
from __future__ import annotations

import copy
import json
import math
import pathlib
import sys
import time
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO))

from strategies.cat_v9_decider import preprocess

# ---------------------------------------------------------------------------
# パラメータ
# ---------------------------------------------------------------------------
PARAMS_PATH = REPO / "config" / "cat_params_v9.json"
with open(PARAMS_PATH) as f:
    PARAMS = json.load(f)

# ---------------------------------------------------------------------------
# 移植版 _check_exits (run_once_v9.py からコピー・改変なし)
# ---------------------------------------------------------------------------
def _ported_exit(pos: Dict, mark_price: float, df, params: Dict) -> Optional[str]:
    side      = pos["side"]
    entry_p   = float(pos["entry_price"])
    add_count = int(pos.get("add_count", 1))
    entry_ms  = int(pos["entry_time"])
    priority  = int(pos.get("entry_priority", -1))
    size_btc  = float(pos.get("size_btc", params.get(f"{side}_POSITION_SIZE_BTC", 0.024)))
    hold_min  = (int(time.time() * 1000) - entry_ms) / 60_000
    unreal    = ((mark_price - entry_p) if side == "LONG" else (entry_p - mark_price)) * size_btc
    mfe_usd   = float(pos.get("mfe_usd", max(0.0, unreal)))

    def _col(col: str) -> float:
        if df is None or col not in df.columns:
            return float("nan")
        return float(df.at[len(df) - 1, col])

    # 1. BREAKOUT_CUT (P22/P23 SHORT, add==3, bb_width+rsi条件)
    if side == "SHORT" and priority in (22, 23) and add_count == 3:
        bw = _col("bb_width"); rsi = _col("rsi_short")
        if (not math.isnan(bw)  and bw  >= float(params.get("P23_BREAKOUT_BB_WIDTH_MIN", 0.03))
                and not math.isnan(rsi) and rsi >= float(params.get("P23_BREAKOUT_RSI_MIN", 70.0))):
            return "BREAKOUT_CUT"

    # 2. MFE_EXIT (P22 SHORT, hold≥TIME_EXIT×0.6, mfe_max≥20USD)
    if side == "SHORT" and priority == 22:
        _tmin = float(params.get("SHORT_TIME_EXIT_MIN", 480))
        if hold_min >= _tmin * 0.6 and mfe_usd >= float(params.get("P22_SHORT_MFE_MAX_GATE_USD", 20.0)):
            return "MFE_EXIT"

    # 3. MFE_STALE_CUT (P22 SHORT, add≥5, hold≥120min, mfe_max<12USD)
    if side == "SHORT" and priority == 22 and add_count >= 5 and hold_min >= 120:
        if mfe_usd < float(params.get("P22_SHORT_MFE_STALE_GATE_USD", 12.0)):
            return "MFE_STALE_CUT"

    # 4. RSI 逆行 EXIT (SHORT)
    if side == "SHORT" and bool(params.get("FEAT_SHORT_RSI_REVERSE_EXIT", False)):
        rsi_v = _col("rsi_short"); rsi_sl = _col("rsi_slope_short"); adx_v = _col("adx")
        if (hold_min >= float(params.get("SHORT_MIN_HOLD_FOR_RSI_EXIT", 1))
                and not math.isnan(rsi_v)  and rsi_v  < float(params.get("SHORT_RSI_THRESH", 50))
                and not math.isnan(rsi_sl) and rsi_sl > float(params.get("SHORT_RSI_SLOPE_MAX", 0.0))
                and not math.isnan(adx_v)  and adx_v  < float(params.get("SHORT_RSI_EXIT_ADX_MAX", 12))):
            return "RSI_REVERSE_EXIT"

    # 5. MAE_CUT (P23 SHORT, add≥4, hold≥300min, mark_price >= entry + 50/size)
    if side == "SHORT" and priority == 23 and add_count >= 4 and hold_min >= 300:
        _mae_cap_price = entry_p + (50.0 / size_btc)
        if mark_price >= _mae_cap_price:
            return "MAE_CUT"

    # 6. PROFIT_LOCK
    if side == "LONG" and int(params.get("LONG_PROFIT_LOCK_ENABLE", 0)):
        if (mfe_usd >= float(params.get("LONG_PROFIT_LOCK_ARM_USD", 15.0))
                and unreal < float(params.get("LONG_PROFIT_LOCK_USD", 6.0))):
            return "PROFIT_LOCK"
    if side == "SHORT" and priority == 22 and int(params.get("P22_SHORT_PROFIT_LOCK_ENABLE", 0)):
        if (mfe_usd >= float(params.get("P22_SHORT_PROFIT_LOCK_ARM_USD", 22.0))
                and unreal < float(params.get("P22_SHORT_PROFIT_LOCK_USD", 8.0))):
            return "PROFIT_LOCK"
    # 6a. PROFIT_LOCK (P23_SHORT, add==5, lock_usd=10固定)
    if side == "SHORT" and priority == 23 and add_count == 5:
        _lock_price_p23 = entry_p - (10.0 / size_btc)
        if mark_price <= _lock_price_p23:
            return "PROFIT_LOCK"
    # 6b. PROFIT_LOCK (P22_SHORT, add==5, lock_usd=10固定)
    if side == "SHORT" and priority == 22 and add_count == 5:
        _lock_price_p22 = entry_p - (10.0 / size_btc)
        if mark_price <= _lock_price_p22:
            return "PROFIT_LOCK"

    # 7. STAGNATION_CUT
    if priority == 4 and int(params.get("P4_STAGNATION_WIDE_ENABLE", 0)):
        if (hold_min >= float(params.get("P4_STAGNATION_WIDE_MIN", 20.0))
                and mfe_usd <= float(params.get("P4_STAGNATION_WIDE_MAX_MFE", 1.0))):
            return "STAGNATION_CUT"
    elif hold_min >= float(params.get("STAG_MIN_M", 30.0)) and mfe_usd <= float(params.get("STAG_MFE_USD", 1.0)):
        return "STAGNATION_CUT"

    # 8a. P4_BREAK_EXIT
    if side == "LONG" and priority == 4:
        _break_min   = float(params.get("P4_BREAK_HOLD_MIN", 90.0))
        _break_slope = float(params.get("P4_BREAK_SLOPE_MAX", -20.0))
        bb_slope = _col("bb_mid_slope")
        if (abs(hold_min - _break_min) < 5.0
                and not math.isnan(bb_slope) and bb_slope <= _break_slope):
            return "P4_BREAK_EXIT"

    # 8b. TIME_EXIT
    base_t = float(params.get("P2_TIME_EXIT_MIN" if priority == 2 else
                              f"{side}_TIME_EXIT_MIN", 150 if side == "LONG" else 480))
    down_f = float(params.get(f"{side}_TIME_EXIT_DOWN_FACTOR", 0.75))
    if hold_min >= base_t * (down_f if unreal < 0 else 1.0):
        return "TIME_EXIT"

    return None


# ---------------------------------------------------------------------------
# 原本 exit 条件（CAT_v9_regime.py run_backtest の条件を単バー版で実装）
# ---------------------------------------------------------------------------
def _orig_exit(pos: Dict, bar: Dict, params: Dict) -> Optional[str]:
    """
    CAT_v9_regime.py run_backtest() の exit 条件を単バー版で実装。

    pos: side, entry_priority, add_count, entry_price, size_btc,
         holding_minutes, mfe_max_usd, 各armed フラグ
    bar: open, high, low, close, bb_width, rsi_short, adx, rci_9,
         rsi_slope_short, bb_mid_slope (不要なものは float("nan") で可)
    """
    side         = pos["side"]
    side_is_long = (side == "LONG")
    priority     = int(pos.get("entry_priority", -1))
    add_count    = int(pos.get("add_count", 1))
    entry_price  = float(pos["entry_price"])
    size_btc     = float(pos.get("size_btc", params.get(f"{side}_POSITION_SIZE_BTC", 0.024)))
    hold_min     = float(pos["holding_minutes"])

    high  = float(bar.get("high",  0.0))
    low   = float(bar.get("low",   0.0))
    close = float(bar.get("close", 0.0))

    def _b(col: str) -> float:
        v = bar.get(col)
        if v is None:
            return float("nan")
        try:
            f = float(v)
            return float("nan") if math.isnan(f) else f
        except (TypeError, ValueError):
            return float("nan")

    # --- MFE_EXIT (P22 SHORT) L923-950 ---
    if not side_is_long and priority == 22:
        _tmin = float(params.get("SHORT_TIME_EXIT_MIN", 480))
        _mfe  = float(pos.get("mfe_max_usd", 0.0))
        if hold_min >= _tmin * 0.6 and _mfe >= float(params.get("P22_SHORT_MFE_MAX_GATE_USD", 20.0)):
            return "MFE_EXIT(P22_SHORT)"

    # --- BREAKOUT_CUT P22 SHORT add==3 L1003-1016 ---
    if not side_is_long and priority == 22 and add_count == 3:
        bw = _b("bb_width"); rv = _b("rsi_short")
        if (not math.isnan(bw) and bw >= float(params.get("P23_BREAKOUT_BB_WIDTH_MIN", 0.03))
                and not math.isnan(rv) and rv >= float(params.get("P23_BREAKOUT_RSI_MIN", 70.0))):
            return "BREAKOUT_CUT(P22_SHORT)"

    # --- BREAKOUT_CUT P23 SHORT add==3 L1018-1033 ---
    if not side_is_long and priority == 23 and add_count == 3:
        bw = _b("bb_width"); rv = _b("rsi_short")
        if (not math.isnan(bw) and bw >= float(params.get("P23_BREAKOUT_BB_WIDTH_MIN", 0.03))
                and not math.isnan(rv) and rv >= float(params.get("P23_BREAKOUT_RSI_MIN", 70.0))):
            return "BREAKOUT_CUT(P23_SHORT)"

    # --- MFE_STALE_CUT L1099-1127 (FEAT_SHORT_RSI_REVERSE_EXIT block 内) ---
    # 原本は ok_hold(hold>=SHORT_MIN_HOLD_FOR_RSI_EXIT=1) AND P22 add>=5 hold>=120 mfe<12
    if bool(params.get("FEAT_SHORT_RSI_REVERSE_EXIT", False)) and not side_is_long:
        _min_hold = int(params.get("SHORT_MIN_HOLD_FOR_RSI_EXIT", 1))
        if hold_min >= _min_hold:
            if priority == 22 and add_count >= 5 and hold_min >= 120:
                if float(pos.get("mfe_max_usd", 0.0)) < 12.0:
                    return "MFE_STALE_CUT(P22_SHORT)"

            # RSI逆行EXIT L1129
            rsi_v = _b("rsi_short"); rsi_sl = _b("rsi_slope_short")
            adx_v = _b("adx");       rci_9  = _b("rci_9")
            rsi_ok   = not math.isnan(rsi_v)  and rsi_v  <= float(params.get("SHORT_RSI_THRESH",       50))
            slope_ok = not math.isnan(rsi_sl) and rsi_sl >= float(params.get("SHORT_RSI_SLOPE_MAX",   0.0))
            adx_gate = not math.isnan(adx_v)  and adx_v  <  float(params.get("SHORT_RSI_EXIT_ADX_MAX", 12))
            rci_gate = not math.isnan(rci_9)  and rci_9  <= 0.0
            if rsi_ok and slope_ok and adx_gate and rci_gate:
                return "RSI下降Exit(SHORT)"

    # --- MAE_CUT (P23 SHORT) L1152-1168 ---
    if not side_is_long and priority == 23 and add_count >= 4 and hold_min >= 300:
        _mae_cap = entry_price + (50.0 / size_btc)
        if high >= _mae_cap:
            return "MAE_CUT(P23_SHORT)"

    # --- PROFIT_LOCK P23 SHORT add==5 L1170-1193 ---
    if not side_is_long and priority == 23 and add_count == 5:
        _lock_usd = 10.0
        _mfe_now  = (entry_price - low) * size_btc
        if _mfe_now >= _lock_usd:
            pos["p23_profit_lock_armed"] = True
        if pos.get("p23_profit_lock_armed"):
            _lock_price = entry_price - (_lock_usd / size_btc)
            if low <= _lock_price:
                return "PROFIT_LOCK(P23_SHORT)"

    # --- PROFIT_LOCK P22 SHORT add==5 L1195-1219 ---
    if not side_is_long and priority == 22 and add_count == 5:
        _lock_usd = 10.0
        _mfe_now  = (entry_price - low) * size_btc
        if _mfe_now >= _lock_usd:
            pos["p22_profit_lock_armed"] = True
        if pos.get("p22_profit_lock_armed"):
            _lock_price = entry_price - (_lock_usd / size_btc)
            if low <= _lock_price:
                return "PROFIT_LOCK(P22_SHORT)"

    # --- PROFIT_LOCK P22 SHORT V2 L1221-1249 ---
    if not side_is_long and priority == 22 and int(params.get("P22_SHORT_PROFIT_LOCK_ENABLE", 0)):
        _arm  = float(params.get("P22_SHORT_PROFIT_LOCK_ARM_USD", 10.0))
        _lock = float(params.get("P22_SHORT_PROFIT_LOCK_USD",      4.0))
        _mfe_now = (entry_price - low) * size_btc
        if _mfe_now >= _arm:
            pos["p22_short_profit_lock_v2_armed"] = True
        if pos.get("p22_short_profit_lock_v2_armed"):
            _lock_price = entry_price - (_lock / size_btc)
            if high >= _lock_price:
                return "PROFIT_LOCK(P22_SHORT_V2)"

    # --- PROFIT_LOCK LONG L1251-1276 ---
    if side_is_long and int(params.get("LONG_PROFIT_LOCK_ENABLE", 0)):
        _arm  = float(params.get("LONG_PROFIT_LOCK_ARM_USD", 15.0))
        _lock = float(params.get("LONG_PROFIT_LOCK_USD",      6.0))
        _mfe_now = (high - entry_price) * size_btc
        if _mfe_now >= _arm:
            pos["long_profit_lock_armed"] = True
        if pos.get("long_profit_lock_armed"):
            _lock_price = entry_price + (_lock / size_btc)
            if high >= _lock_price:
                return "PROFIT_LOCK(LONG)"

    # --- STAGNATION_CUT P4 wide L1443-1459 ---
    if side_is_long and priority == 4 and int(params.get("P4_STAGNATION_WIDE_ENABLE", 0)):
        _sw_min = float(params.get("P4_STAGNATION_WIDE_MIN",     45.0))
        _sw_mfe = float(params.get("P4_STAGNATION_WIDE_MAX_MFE",  3.0))
        _mfe    = float(pos.get("mfe_max_usd", 0.0))
        if hold_min >= _sw_min and _mfe <= _sw_mfe:
            return "STAGNATION_CUT(P4_MFE)"

    # --- STAGNATION_CUT general L1461-1477 ---
    if hold_min >= 30.0:
        if float(pos.get("mfe_max_usd", 0.0)) <= 1.0:
            return "STAGNATION_CUT(MFE<=1@30m)"

    # --- P4_BREAK_EXIT L1479-1510 ---
    if side_is_long and priority == 4:
        _break_min  = float(params.get("P4_BREAK_HOLD_MIN",  90.0))
        _break_bars = max(1, int(round(_break_min / 5.0)))
        _entry_i    = int(pos.get("entry_i", -1))
        _bar_j      = int(pos.get("bar_j",   -1))
        _slope_max  = float(params.get("P4_BREAK_SLOPE_MAX", -20.0))
        bb_slope    = _b("bb_mid_slope")
        if (_entry_i >= 0 and _bar_j >= 0 and _bar_j == _entry_i + _break_bars
                and not math.isnan(bb_slope) and bb_slope <= _slope_max):
            return "P4_BREAK_EXIT"

    # --- TIME_EXIT L1512+ ---
    if side_is_long and priority == 2:
        base_t = float(params.get("P2_TIME_EXIT_MIN", 480.0))
    else:
        base_t = float(params.get("LONG_TIME_EXIT_MIN" if side_is_long else "SHORT_TIME_EXIT_MIN",
                                   150 if side_is_long else 480))
    down_f = float(params.get(f"{side}_TIME_EXIT_DOWN_FACTOR", 0.75))
    unreal = ((close - entry_price) if side_is_long else (entry_price - close)) * size_btc
    eff_t  = base_t * (down_f if unreal < 0 else 1.0)
    if hold_min >= eff_t:
        return "TIME_EXIT"

    return None


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------
def _normalize(r: Optional[str]) -> Optional[str]:
    """原本の exit_reason から '(' 以降を除去して移植版と揃える。
    例: 'MFE_EXIT(P22_SHORT)' → 'MFE_EXIT'
    """
    if r is None:
        return None
    return r.split("(")[0]


def _run_case(case: dict, params: dict) -> dict:
    hold_min   = case["hold_min"]
    bar        = case["bar"]
    mark_price = case["mark_price"]
    df         = case.get("df")

    # 原本: holding_minutes を���接使う
    pos_orig = copy.deepcopy(case["pos_base"])
    pos_orig["holding_minutes"] = hold_min

    # 移植版: entry_time を hold_min から逆算
    pos_ported = copy.deepcopy(case["pos_base"])
    pos_ported["entry_time"] = str(int(time.time() * 1000) - int(hold_min * 60_000))

    orig_r   = _orig_exit(pos_orig,   bar,        params)
    ported_r = _ported_exit(pos_ported, mark_price, df, params)

    orig_norm = _normalize(orig_r)

    exp_orig   = case.get("expected_orig")
    exp_ported = case.get("expected_ported")
    match      = (orig_norm == ported_r)

    return {
        "id":        case["id"],
        "desc":      case["desc"],
        "hold_min":  hold_min,
        "mfe_usd":   case["pos_base"].get("mfe_usd", case["pos_base"].get("mfe_max_usd", 0.0)),
        "orig_raw":  orig_r,
        "ported_raw": ported_r,
        "orig_norm": orig_norm,
        "exp_orig":  exp_orig,
        "exp_ported": exp_ported,
        "match":     match,
        "note":      case.get("note", ""),
    }


# ---------------------------------------------------------------------------
# テストケース定義
# ---------------------------------------------------------------------------
SIZE       = 0.024
BASE_PRICE = 85000.0

CASES: List[dict] = []

# --------------------------------------------------
# T01: TIME_EXIT LONG P4 (hold=160min)
# --------------------------------------------------
CASES.append({
    "id": "T01", "desc": "TIME_EXIT LONG P4 (hold=160m)",
    "hold_min": 160.0,
    "pos_base": {
        "side": "LONG", "entry_priority": 4, "add_count": 1,
        "entry_price": BASE_PRICE, "size_btc": SIZE,
        "mfe_max_usd": 5.0, "mfe_usd": 5.0,
    },
    # unreal=0 → down_factor未適用 → base_t=150 → 160>=150 fires
    "bar": {"open": BASE_PRICE, "high": BASE_PRICE, "low": BASE_PRICE, "close": BASE_PRICE},
    "mark_price": BASE_PRICE,
    "df": None,
    "expected_orig": "TIME_EXIT",
    "expected_ported": "TIME_EXIT",
})

# --------------------------------------------------
# T02: TIME_EXIT SHORT P22 下方向 (hold=370min, unreal<0)
# short unreal<0 = 損失中 → down_factor適用 → eff_t=480*0.75=360 → 370>=360 fires
# --------------------------------------------------
CASES.append({
    "id": "T02", "desc": "TIME_EXIT SHORT P22 down-factor (hold=370m, loss)",
    "hold_min": 370.0,
    "pos_base": {
        "side": "SHORT", "entry_priority": 22, "add_count": 2,
        "entry_price": BASE_PRICE, "size_btc": SIZE,
        "mfe_max_usd": 3.0, "mfe_usd": 3.0,
    },
    # close > entry → SHORT unreal = (entry - close)*size < 0
    "bar": {
        "open":  BASE_PRICE + 200, "high":  BASE_PRICE + 200,
        "low":   BASE_PRICE + 200, "close": BASE_PRICE + 200,
    },
    "mark_price": BASE_PRICE + 200,
    "df": None,
    "expected_orig": "TIME_EXIT",
    "expected_ported": "TIME_EXIT",
})

# --------------------------------------------------
# T03: STAGNATION_CUT non-P4 SHORT P22 (hold=35m, mfe=0.5)
# hold=35>=STAG_MIN_M=30, mfe=0.5<=1.0, priority≠4 → fires
# --------------------------------------------------
CASES.append({
    "id": "T03", "desc": "STAGNATION_CUT SHORT P22 non-P4 (hold=35m, mfe=0.5)",
    "hold_min": 35.0,
    "pos_base": {
        "side": "SHORT", "entry_priority": 22, "add_count": 1,
        "entry_price": BASE_PRICE + 1000, "size_btc": SIZE,
        "mfe_max_usd": 0.5, "mfe_usd": 0.5,
    },
    "bar": {"open": BASE_PRICE, "high": BASE_PRICE, "low": BASE_PRICE, "close": BASE_PRICE},
    "mark_price": BASE_PRICE,
    "df": None,
    "expected_orig": "STAGNATION_CUT",
    "expected_ported": "STAGNATION_CUT",
})

# --------------------------------------------------
# T04: STAGNATION_CUT P4 LONG hold=25m [W-3 BUG]
# 原本: P4_STAGNATION_WIDE_ENABLE=1, P4_STAGNATION_WIDE_MIN=20 → hold=25>=20 → fires
# 移植: 外側ゲート STAG_MIN_M=30 → 25<30 → fires しない
# --------------------------------------------------
CASES.append({
    "id": "T04", "desc": "⚠️  STAGNATION_CUT P4 hold=25m [W-3]",
    "hold_min": 25.0,
    "pos_base": {
        "side": "LONG", "entry_priority": 4, "add_count": 1,
        "entry_price": BASE_PRICE, "size_btc": SIZE,
        "mfe_max_usd": 0.5, "mfe_usd": 0.5,
    },
    "bar": {"open": BASE_PRICE, "high": BASE_PRICE, "low": BASE_PRICE, "close": BASE_PRICE},
    "mark_price": BASE_PRICE,
    "df": None,
    "expected_orig":   "STAGNATION_CUT",
    "expected_ported": "STAGNATION_CUT",
    "note": "W-3 修正済み: P4パスを外側ゲートから独立させた",
})

# --------------------------------------------------
# T05: STAGNATION_CUT P4 LONG hold=35m (両方発動)
# --------------------------------------------------
CASES.append({
    "id": "T05", "desc": "STAGNATION_CUT P4 hold=35m (both OK)",
    "hold_min": 35.0,
    "pos_base": {
        "side": "LONG", "entry_priority": 4, "add_count": 1,
        "entry_price": BASE_PRICE, "size_btc": SIZE,
        "mfe_max_usd": 0.5, "mfe_usd": 0.5,
    },
    "bar": {"open": BASE_PRICE, "high": BASE_PRICE, "low": BASE_PRICE, "close": BASE_PRICE},
    "mark_price": BASE_PRICE,
    "df": None,
    "expected_orig": "STAGNATION_CUT",
    "expected_ported": "STAGNATION_CUT",
})

# --------------------------------------------------
# T06: MFE_STALE_CUT P22 SHORT (add=5, hold=130m, mfe=8)
# hold=130>=120, add=5, mfe=8<12 → fires
# --------------------------------------------------
CASES.append({
    "id": "T06", "desc": "MFE_STALE_CUT P22 SHORT (add=5, hold=130m, mfe=8)",
    "hold_min": 130.0,
    "pos_base": {
        "side": "SHORT", "entry_priority": 22, "add_count": 5,
        "entry_price": BASE_PRICE + 1000, "size_btc": SIZE,
        "mfe_max_usd": 8.0, "mfe_usd": 8.0,
    },
    "bar": {"open": BASE_PRICE, "high": BASE_PRICE, "low": BASE_PRICE, "close": BASE_PRICE},
    "mark_price": BASE_PRICE,
    "df": None,
    "expected_orig": "MFE_STALE_CUT",
    "expected_ported": "MFE_STALE_CUT",
})

# --------------------------------------------------
# T07: MFE_EXIT P22 SHORT (hold=300m, mfe=25, add=1)
# hold=300>=480*0.6=288, mfe=25>=20 → fires
# --------------------------------------------------
CASES.append({
    "id": "T07", "desc": "MFE_EXIT P22 SHORT (hold=300m, mfe=25, add=1)",
    "hold_min": 300.0,
    "pos_base": {
        "side": "SHORT", "entry_priority": 22, "add_count": 1,
        "entry_price": BASE_PRICE + 1000, "size_btc": SIZE,
        "mfe_max_usd": 25.0, "mfe_usd": 25.0,
    },
    "bar": {"open": BASE_PRICE, "high": BASE_PRICE, "low": BASE_PRICE, "close": BASE_PRICE},
    "mark_price": BASE_PRICE,
    "df": None,
    "expected_orig": "MFE_EXIT",
    "expected_ported": "MFE_EXIT",
})

# --------------------------------------------------
# T08: MAE_CUT P23 SHORT (add=4, hold=310m)
# entry=85000, mae_cap=85000+50/0.024=87083.33, close=high=87200>=87083.33 → fires
# --------------------------------------------------
_MAE_ENTRY = BASE_PRICE
_MAE_HIGH  = _MAE_ENTRY + 50.0 / SIZE + 100  # 100 margin above cap
CASES.append({
    "id": "T08", "desc": "MAE_CUT P23 SHORT (add=4, hold=310m)",
    "hold_min": 310.0,
    "pos_base": {
        "side": "SHORT", "entry_priority": 23, "add_count": 4,
        "entry_price": _MAE_ENTRY, "size_btc": SIZE,
        "mfe_max_usd": 3.0, "mfe_usd": 3.0,
    },
    "bar": {
        "open":  _MAE_HIGH, "high":  _MAE_HIGH,
        "low":   _MAE_HIGH, "close": _MAE_HIGH,
    },
    "mark_price": _MAE_HIGH,
    "df": None,
    "expected_orig": "MAE_CUT",
    "expected_ported": "MAE_CUT",
})

# --------------------------------------------------
# T09: PROFIT_LOCK P23 SHORT add=5
# entry=85000, lock_price=85000-10/0.024=84583.33
# close=low=84483(<84583.33) → fires
# (entry-low)*size=(85000-84483)*0.024=$12.4 → arms on this bar (or pre-armed)
# --------------------------------------------------
_PL_ENTRY = 85000.0
_PL_LOCK  = _PL_ENTRY - 10.0 / SIZE          # 84583.33
_PL_CLOSE = _PL_LOCK  - 100.0                # 84483.33
CASES.append({
    "id": "T09", "desc": "PROFIT_LOCK P23 SHORT add=5",
    "hold_min": 10.0,
    "pos_base": {
        "side": "SHORT", "entry_priority": 23, "add_count": 5,
        "entry_price": _PL_ENTRY, "size_btc": SIZE,
        "mfe_max_usd": 15.0, "mfe_usd": 15.0,
        "p23_profit_lock_armed": True,  # 事前armed（前barで到達済み想定）
    },
    "bar": {
        "open":  _PL_CLOSE, "high": _PL_CLOSE,
        "low":   _PL_CLOSE, "close": _PL_CLOSE,
    },
    "mark_price": _PL_CLOSE,
    "df": None,
    "expected_orig": "PROFIT_LOCK",
    "expected_ported": "PROFIT_LOCK",
})

# --------------------------------------------------
# T10: PROFIT_LOCK P22 SHORT add=5
# entry=85000, lock_price=84583.33, close=84483 → fires
# --------------------------------------------------
CASES.append({
    "id": "T10", "desc": "PROFIT_LOCK P22 SHORT add=5",
    "hold_min": 10.0,
    "pos_base": {
        "side": "SHORT", "entry_priority": 22, "add_count": 5,
        "entry_price": _PL_ENTRY, "size_btc": SIZE,
        "mfe_max_usd": 15.0, "mfe_usd": 15.0,
        "p22_profit_lock_armed": True,  # 事前armed
    },
    "bar": {
        "open":  _PL_CLOSE, "high": _PL_CLOSE,
        "low":   _PL_CLOSE, "close": _PL_CLOSE,
    },
    "mark_price": _PL_CLOSE,
    "df": None,
    "expected_orig": "PROFIT_LOCK",
    "expected_ported": "PROFIT_LOCK",
})

# --------------------------------------------------
# T11: BREAKOUT_CUT P22 SHORT (snapshot データ使用)
# snapshot.csv から bb_width>=0.03 AND rsi_short>=70 のバーを検索
# --------------------------------------------------
def _load_t11() -> Optional[dict]:
    csv_path = HERE / "data" / "snapshot.csv"
    if not csv_path.exists():
        return None

    raw = pd.read_csv(csv_path)
    raw["timestamp"] = pd.to_datetime(raw["timestamp_ms"].astype(int), unit="ms")
    df_raw = raw[["timestamp", "open", "high", "low", "close", "volume"]].copy()
    df_raw = df_raw.sort_values("timestamp").reset_index(drop=True)

    if len(df_raw) < 110:
        return None

    df_pp = preprocess(df_raw.copy(), PARAMS)

    bw_min  = float(PARAMS.get("P23_BREAKOUT_BB_WIDTH_MIN", 0.03))
    rsi_min = float(PARAMS.get("P23_BREAKOUT_RSI_MIN",      70.0))

    cand = df_pp[
        (df_pp["bb_width"]  >= bw_min) &
        (df_pp["rsi_short"] >= rsi_min)
    ]
    if cand.empty:
        return None

    i   = cand.index[0]
    row = df_pp.loc[i]
    cl  = float(row["close"])

    # ported用 df: 単行 DataFrame（last rowとして使用）
    df_single = df_pp.loc[[i]].reset_index(drop=True)

    # SHORT entry は close + 3000（十分に高い → 他のexit条件が発火しない）
    t11_entry = cl + 3000.0

    return {
        "id": "T11", "desc": f"BREAKOUT_CUT P22 SHORT (bar_idx={i}, bw={row['bb_width']:.4f}, rsi={row['rsi_short']:.1f})",
        "hold_min": 5.0,
        "pos_base": {
            "side": "SHORT", "entry_priority": 22, "add_count": 3,
            "entry_price": t11_entry, "size_btc": SIZE,
            "mfe_max_usd": 0.0, "mfe_usd": 0.0,
        },
        "bar": {
            "open":      float(row["open"]),
            "high":      float(row["high"]),
            "low":       float(row["low"]),
            "close":     cl,
            "bb_width":  float(row["bb_width"]),
            "rsi_short": float(row["rsi_short"]),
        },
        "mark_price": cl,
        "df": df_single,
        "expected_orig": "BREAKOUT_CUT",
        "expected_ported": "BREAKOUT_CUT",
    }

t11 = _load_t11()
if t11 is not None:
    CASES.append(t11)
else:
    print("[SKIP] T11: snapshot.csv に bb_width>=0.03 AND rsi_short>=70 のバーが見つかりません")


# ---------------------------------------------------------------------------
# 実行・出力
# ---------------------------------------------------------------------------
def _fmt(v: Optional[str]) -> str:
    return v if v is not None else "None"


def main():
    print()
    print("=" * 72)
    print("  Exit Parity: 原本 vs 移植版 比較")
    print(f"  params: {PARAMS_PATH.name}")
    print("=" * 72)
    print()

    results = [_run_case(c, PARAMS) for c in CASES]

    # 結果テーブル
    w_id   = 4
    w_desc = 46
    w_r    = 18

    header = (f"{'ID':<{w_id}}  {'説明':<{w_desc}}  "
              f"{'orig':<{w_r}}  {'ported':<{w_r}}  判定")
    print(header)
    print("-" * len(header))

    matches = 0
    mismatches = 0

    for r in results:
        orig_disp   = _fmt(r["orig_norm"])
        ported_disp = _fmt(r["ported_raw"])
        match       = r["match"]
        exp_match   = (r["orig_norm"] == r["exp_orig"]) and (r["ported_raw"] == r["exp_ported"])

        if match and exp_match:
            verdict = "✅ MATCH"
            matches += 1
        elif not match:
            verdict = "❌ MISMATCH"
            mismatches += 1
        else:
            verdict = "⚠️  UNEXPECTED"
            mismatches += 1

        print(f"{r['id']:<{w_id}}  {r['desc']:<{w_desc}}  "
              f"{orig_disp:<{w_r}}  {ported_disp:<{w_r}}  {verdict}")

        # 詳細（期待値と異なる場合 or note あり）
        if not exp_match or r.get("note"):
            if not exp_match:
                print(f"       期待 orig={r['exp_orig']}  ported={r['exp_ported']}")
            if r.get("note"):
                print(f"       NOTE: {r['note']}")

    # サマリー
    print()
    print("=" * 72)
    total = len(results)
    print(f"[SUMMARY]  全 {total} ケース  "
          f"MATCH: {matches}  MISMATCH: {mismatches}")

    if mismatches == 0:
        print("[RESULT] ✅ 全ケース一致 — Exit Parity ゲート通過")
    else:
        print("[RESULT] ❌ 不一致あり — 修正が必要")
        print()
        print("  不一致ケース:")
        for r in results:
            if not r["match"] or (r["orig_norm"] != r["exp_orig"]) or (r["ported_raw"] != r["exp_ported"]):
                print(f"    [{r['id']}] {r['desc']}")
                print(f"           orig={r['orig_raw']}  ported={r['ported_raw']}")
                if r.get("note"):
                    print(f"           NOTE: {r['note']}")
    print("=" * 72)
    print()


if __name__ == "__main__":
    main()
