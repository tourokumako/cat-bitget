#!/usr/bin/env python3
"""
runner/replay_csv.py — 本番エンジンロジックの CSV リプレイスクリプト

目的:
    同じ CSV を BT（CAT_v9_regime.py）と両方に流し、差分を取る。
    差分 = バックテスト側で修正すべき箇所。

使い方:
    .venv/bin/python3 runner/replay_csv.py /path/to/BTCUSDT-5m-2026-03-27_04-01_combined.csv

出力:
    results/replay_{filename}.csv  （live_trades.csv と同カラム構成）
    サマリーを標準出力に表示

設計方針:
    - mark_price = close（BT と同条件、スリッページなし）
    - TP/SL 判定もclose ベース（BT と同条件）
    - pending fill: LONG=low<=limit / SHORT=high>=limit（翌バー以降、TTL=3バー）
    - MFE は close ベースで各バー更新
    - API 呼び出し・state ファイル I/O はすべてスキップ
    - MAX_SIDES=2: LONG と SHORT を同時保有可
"""
from __future__ import annotations

import csv
import json
import math
import pathlib
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

import pandas as pd

_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from strategies.cat_v9_decider import preprocess, check_entry_priority

# ---- 定数 ----
PENDING_TTL_BARS = 2
CANDLE_WARMUP   = 200   # 指標計算に必要な最小バー数（live engine と同値）
_PARAMS_PATH    = _ROOT / "config" / "cat_params_v9.json"
_RESULTS_DIR    = _ROOT / "results"
_JST            = timezone(timedelta(hours=9))
_LONG_PRIORITIES  = (1, 2, 3, 4)
_SHORT_PRIORITIES = (21, 22, 23, 24)

_DAILY_WARMUP = str(_ROOT / "data" / "BTCUSDT-1d-2024-09-01_04-15_227d.csv")

# 日足MA70レジーム → Priority enable/disable セット
_REGIME_PRIORITY_SETS: Dict[str, Dict] = {
    "downtrend": {"ENABLE_P1_LONG": False, "ENABLE_P2_LONG": True,  "ENABLE_P3_LONG": False,
                  "ENABLE_P4_LONG": False,  "ENABLE_P21_SHORT": True,  "ENABLE_P22_SHORT": False,
                  "ENABLE_P23_SHORT": True,  "ENABLE_P24_SHORT": False, "ENABLE_P25_SHORT": False},
    "range":     {"ENABLE_P1_LONG": False, "ENABLE_P2_LONG": False, "ENABLE_P3_LONG": False,
                  "ENABLE_P4_LONG": True,  "ENABLE_P21_SHORT": False, "ENABLE_P22_SHORT": False,
                  "ENABLE_P23_SHORT": False, "ENABLE_P24_SHORT": False, "ENABLE_P25_SHORT": False},
    "uptrend":   {"ENABLE_P1_LONG": True,  "ENABLE_P2_LONG": False, "ENABLE_P3_LONG": False,
                  "ENABLE_P4_LONG": False, "ENABLE_P21_SHORT": False, "ENABLE_P22_SHORT": False,
                  "ENABLE_P23_SHORT": False, "ENABLE_P24_SHORT": True,  "ENABLE_P25_SHORT": False},
    "mixed":     {"ENABLE_P1_LONG": False, "ENABLE_P2_LONG": False, "ENABLE_P3_LONG": False,
                  "ENABLE_P4_LONG": True,  "ENABLE_P21_SHORT": False, "ENABLE_P22_SHORT": False,
                  "ENABLE_P23_SHORT": False, "ENABLE_P24_SHORT": False, "ENABLE_P25_SHORT": False},
    "unknown":   {"ENABLE_P1_LONG": False, "ENABLE_P2_LONG": False, "ENABLE_P3_LONG": False,
                  "ENABLE_P4_LONG": False, "ENABLE_P21_SHORT": False, "ENABLE_P22_SHORT": False,
                  "ENABLE_P23_SHORT": False, "ENABLE_P24_SHORT": False, "ENABLE_P25_SHORT": False},
}


# ==============================================================
# パラメータ読み込み
# ==============================================================
def _load_params() -> Dict[str, Any]:
    with open(_PARAMS_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    for k, v in raw.items():
        if isinstance(v, str):
            try:
                raw[k] = int(v) if "." not in v else float(v)
            except ValueError:
                pass
    return raw


# ==============================================================
# CSV 読み込み（Binance/Bitget/datetime 形式を自動判別）
# ==============================================================
def _load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    rename = {}
    for c in df.columns:
        lc = c.lower().strip()
        if lc in ("timestamp", "ts", "ts_ms", "timestamp_ms", "open_time"):
            rename[c] = "_ts_raw"
        elif lc == "open":   rename[c] = "open"
        elif lc == "high":   rename[c] = "high"
        elif lc == "low":    rename[c] = "low"
        elif lc == "close":  rename[c] = "close"
        elif lc in ("vol", "volume"): rename[c] = "volume"
    df = df.rename(columns=rename)

    # timestamp → ms（μs / ms / datetime string）
    ts_raw = df["_ts_raw"]
    if pd.api.types.is_numeric_dtype(ts_raw):
        sample = float(ts_raw.iloc[0])
        if sample > 1e15:
            df["timestamp_ms"] = (ts_raw.astype(float) / 1000).astype(int)  # μs → ms
        else:
            df["timestamp_ms"] = ts_raw.astype(int)
    else:
        df["timestamp_ms"] = (pd.to_datetime(ts_raw).astype("int64") // 1_000_000).astype(int)

    df = df.sort_values("timestamp_ms").reset_index(drop=True)
    for c in ("open", "high", "low", "close"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


# ==============================================================
# TP 価格計算（run_once_v9._calc_tp_pct と完全一致）
# ==============================================================
def _calc_tp_price(side: str, entry_price: float, adx: float, params: Dict, priority=None) -> float:
    pri_key  = f"P{priority}_TP_PCT" if priority is not None else None
    base     = float(params[pri_key] if pri_key and pri_key in params else params[f"{side}_TP_PCT"])
    fee_rate = float(params.get("FEE_RATE_MAKER", 0.00014))
    margin   = float(params.get("FEE_MARGIN", 1.5))
    if int(params.get("TP_FEE_FLOOR_ENABLE", 0)):
        base = max(base, fee_rate * 2 * margin)
    if int(params.get("TP_ADX_BOOST_ENABLE", 0)):
        adx_thresh = float(params.get("ADX_THRESH", 25.0))
        adx_range  = float(params.get("TP_ADX_RANGE", 15.0))
        adx_factor = float(params.get("TP_ADX_FACTOR", 1.5))
        adx_clamped = max(0.0, min(adx - adx_thresh, adx_range))
        boost = 1.0 + (adx_clamped / adx_range) * (adx_factor - 1.0) if adx_range > 0 else 1.0
        base *= boost
    if int(params.get("TP_PCT_CLAMP_ENABLE", 0)):
        scale      = float(params.get("TP_PCT_SCALE", 1.0))
        scale_high = float(params.get("TP_PCT_SCALE_HIGH", 1.5))
        adx_high   = float(params.get("ADX_TP_THRESH_HIGH", 40.0))
        base *= scale_high if adx >= adx_high else scale

    ep = Decimal(str(entry_price))
    if side == "LONG":
        return float(ep * (Decimal("1") + Decimal(str(base))))
    else:
        return float(ep * (Decimal("1") - Decimal(str(base))))


# ==============================================================
# SL 価格計算
# ==============================================================
def _calc_sl_price(side: str, entry_price: float, params: Dict, priority: int = 0) -> float:
    pri_key = f"P{priority}_SL_PCT"
    sl_pct = float(params.get(pri_key, params[f"{side}_SL_PCT"]))
    ep = Decimal(str(entry_price))
    if side == "LONG":
        return float(ep * (Decimal("1") - Decimal(str(sl_pct))))
    else:
        return float(ep * (Decimal("1") + Decimal(str(sl_pct))))


# ==============================================================
# Exit 判定（run_once_v9._check_exits と同ロジック）
# hold_min は ts_ms ベースで計算（time.time() 不使用）
# ==============================================================
def _check_exits_replay(pos: Dict, mark_price: float, df: pd.DataFrame, i: int,
                        params: Dict, current_ts_ms: int) -> Optional[str]:
    side      = pos["side"]
    entry_p   = float(pos["entry_price"])
    add_count = int(pos.get("add_count", 1))
    entry_ms  = int(pos["entry_time"])
    priority  = int(pos.get("entry_priority", -1))
    size_btc  = float(pos.get("size_btc", params.get(f"{side}_POSITION_SIZE_BTC", 0.024)))
    hold_min  = (current_ts_ms - entry_ms) / 60_000
    unreal    = ((mark_price - entry_p) if side == "LONG" else (entry_p - mark_price)) * size_btc
    mfe_usd   = float(pos.get("mfe_usd", max(0.0, unreal)))

    def _col(col: str) -> float:
        if col not in df.columns or i < 0 or i >= len(df):
            return float("nan")
        return float(df.at[i, col])

    # 1. BREAKOUT_CUT (P22 SHORT, add==3)
    if side == "SHORT" and priority == 22 and add_count == 3:
        bw = _col("bb_width"); rsi = _col("rsi_short")
        if (not math.isnan(bw)  and bw  >= float(params.get("P23_BREAKOUT_BB_WIDTH_MIN", 0.03))
                and not math.isnan(rsi) and rsi >= float(params.get("P23_BREAKOUT_RSI_MIN", 70.0))):
            return "BREAKOUT_CUT"

    # 2. MFE_EXIT (P22 SHORT, hold>=TIME_EXIT*0.6, mfe>=20USD)
    if side == "SHORT" and priority == 22:
        _tmin = float(params.get("SHORT_TIME_EXIT_MIN", 480))
        if hold_min >= _tmin * 0.6 and mfe_usd >= float(params.get("P22_SHORT_MFE_MAX_GATE_USD", 20.0)):
            return "MFE_EXIT"

    # 3. MFE_STALE_CUT (P22 SHORT, add>=5, hold>=120min)
    if side == "SHORT" and priority == 22 and add_count >= 5 and hold_min >= 120:
        if mfe_usd < float(params.get("P22_SHORT_MFE_STALE_GATE_USD", 12.0)):
            return "MFE_STALE_CUT"


    # 3b. MFE_STALE_CUT (P2 LONG, add==1, hold>=P2_MFE_STALE_HOLD_MIN)
    if side == "LONG" and priority == 2 and add_count == 1:
        _p2_hold_min = float(params.get("P2_MFE_STALE_HOLD_MIN", 120.0))
        if hold_min >= _p2_hold_min and mfe_usd < float(params.get("P2_MFE_STALE_GATE_USD", 10.0)):
            return "MFE_STALE_CUT"

    # 3c. MFE_STALE_CUT / MFE_DRAWDOWN_CUT (P23 SHORT)
    if side == "SHORT" and priority == 23:
        _p23_hold_min = float(params.get("P23_MFE_STALE_HOLD_MIN", 30.0))

        # Phase 1: STALE_CUT（P23_MFE_STALE_ADD_MIN未設定=従来add==1のみ / 設定時=>=N全対応）
        _p23_add_min = params.get("P23_MFE_STALE_ADD_MIN")
        _stale_cond  = (add_count == 1) if _p23_add_min is None else (add_count >= int(_p23_add_min))
        if _stale_cond and hold_min >= _p23_hold_min:
            _sz_atr_f = params.get("P23_MFE_STALE_SIZE_ATR_FACTOR")
            _atr_f    = params.get("P23_MFE_STALE_ATR_FACTOR")
            if _sz_atr_f is not None:
                _gate = size_btc * _col("atr_14") * float(_sz_atr_f)
            elif _atr_f is not None:
                _gate = _col("atr_14") * float(_atr_f)
            else:
                _gate = float(params.get("P23_MFE_STALE_GATE_USD", 4.0))
            if mfe_usd < _gate:
                return "MFE_STALE_CUT"

        # Phase 2: MFE_DRAWDOWN_CUT（TYPE II高MFE反転カット）
        # 条件: MFEがmin_usd以上に達した後、unrealがMFE×ratioを下回ったらカット
        _dmin   = params.get("P23_MFE_DRAWDOWN_MIN_USD")
        _dratio = params.get("P23_MFE_DRAWDOWN_RATIO")
        if _dmin is not None and _dratio is not None:
            if mfe_usd >= float(_dmin) and unreal < mfe_usd * float(_dratio):
                return "MFE_DRAWDOWN_CUT"

    # 3f. STOCH_REVERSE_EXIT (P23 SHORT: Stochゴールデンクロス＋MFEゲート複合Exit)
    # 条件: mfe>=gate AND hold>=min_hold AND unreal>=unreal_min AND stoch golden cross
    if (side == "SHORT" and priority == 23
            and bool(params.get("P23_STOCH_REVERSE_EXIT_ENABLE", False))):
        _sk_now  = _col("stoch_k")
        _sd_now  = _col("stoch_d")
        _sk_prev = float(df.at[i - 1, "stoch_k"]) if i > 0 and "stoch_k" in df.columns else float("nan")
        _sd_prev = float(df.at[i - 1, "stoch_d"]) if i > 0 and "stoch_d" in df.columns else float("nan")
        _golden_cross = (
            not math.isnan(_sk_now) and not math.isnan(_sd_now)
            and not math.isnan(_sk_prev) and not math.isnan(_sd_prev)
            and _sk_prev < _sd_prev and _sk_now > _sd_now
        )
        if (_golden_cross
                and mfe_usd  >= float(params.get("P23_STOCH_EXIT_MFE_GATE",   15.0))
                and hold_min >= float(params.get("P23_STOCH_EXIT_MIN_HOLD",    30.0))
                and unreal   >= float(params.get("P23_STOCH_EXIT_UNREAL_MIN",   0.0))):
            return "STOCH_REVERSE_EXIT"

    # 3d. MFE_STALE_CUT (P3 LONG, add==1, hold>=P3_MFE_STALE_HOLD_MIN)
    if side == "LONG" and priority == 3 and add_count == 1:
        _p3_hold_min = float(params.get("P3_MFE_STALE_HOLD_MIN", 90.0))
        if hold_min >= _p3_hold_min and mfe_usd < float(params.get("P3_MFE_STALE_GATE_USD", 4.0)):
            return "MFE_STALE_CUT"

    # 3e. MFE_STALE_CUT (P21 SHORT, add==1, hold>=P21_MFE_STALE_HOLD_MIN)
    if side == "SHORT" and priority == 21 and add_count == 1:
        _p21_hold_min = float(params.get("P21_MFE_STALE_HOLD_MIN", 90.0))
        if hold_min >= _p21_hold_min and mfe_usd < float(params.get("P21_MFE_STALE_GATE_USD", 4.0)):
            return "MFE_STALE_CUT"

    # 4. RSI_REVERSE_EXIT (SHORT)
    if side == "SHORT" and bool(params.get("FEAT_SHORT_RSI_REVERSE_EXIT", False)):
        rsi_v = _col("rsi_short"); rsi_sl = _col("rsi_slope_short"); adx_v = _col("adx")
        if (hold_min >= float(params.get("SHORT_MIN_HOLD_FOR_RSI_EXIT", 1))
                and not math.isnan(rsi_v)  and rsi_v  < float(params.get("SHORT_RSI_THRESH", 50))
                and not math.isnan(rsi_sl) and rsi_sl > float(params.get("SHORT_RSI_SLOPE_MAX", 0.0))
                and not math.isnan(adx_v)  and adx_v  < float(params.get("SHORT_RSI_EXIT_ADX_MAX", 12))):
            return "RSI_REVERSE_EXIT"

    # 5b. MAE_CUT (P2 LONG, add>=4, hold>=300min)
    if side == "LONG" and priority == 2 and add_count >= 4 and hold_min >= 300:
        _mae_cap_long = entry_p - (50.0 / size_btc)
        if mark_price <= _mae_cap_long:
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
    # 6a. P23 SHORT PROFIT_LOCK V2 (MFE-drawdown type: add_count非依存)
    if side == "SHORT" and priority == 23 and int(params.get("P23_SHORT_PROFIT_LOCK_ENABLE", 1)):
        _arm  = float(params.get("P23_SHORT_PROFIT_LOCK_ARM_USD", 15.0))
        _lock = float(params.get("P23_SHORT_PROFIT_LOCK_USD", 5.0))
        if mfe_usd >= _arm and unreal < _lock:
            return "PROFIT_LOCK"
    # 6b. P22 SHORT add==5
    if side == "SHORT" and priority == 22 and add_count == 5:
        _lock_price = entry_p - (10.0 / size_btc)
        if mark_price <= _lock_price:
            return "PROFIT_LOCK"

    # 7. STAGNATION_CUT
    if priority == 4 and int(params.get("P4_STAGNATION_WIDE_ENABLE", 0)):
        if (hold_min >= float(params.get("P4_STAGNATION_WIDE_MIN", 20.0))
                and mfe_usd <= float(params.get("P4_STAGNATION_WIDE_MAX_MFE", 1.0))):
            return "STAGNATION_CUT"
    elif hold_min >= float(params.get("STAG_MIN_M", 30.0)) and mfe_usd <= float(params.get("STAG_MFE_USD", 1.0)):
        return "STAGNATION_CUT"

    # 8. TIME_EXIT
    _pri_t_key = f"P{priority}_TIME_EXIT_MIN"
    base_t = float(params[_pri_t_key] if _pri_t_key in params else
                   params.get(f"{side}_TIME_EXIT_MIN", 150 if side == "LONG" else 480))
    _pri_df_key = f"P{priority}_TIME_EXIT_DOWN_FACTOR"
    down_f = float(params[_pri_df_key] if _pri_df_key in params else
                   params.get(f"{side}_TIME_EXIT_DOWN_FACTOR", 0.75))
    if hold_min >= base_t * (down_f if unreal < 0 else 1.0):
        return "TIME_EXIT"

    return None


# ==============================================================
# ユーティリティ
# ==============================================================
def _ts_to_str(ts_ms: int) -> str:
    # UTC で出力（candles.csv と timezone を合わせる）
    dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _calc_tp_diff(pos: Dict, side: str, size_b: float) -> float:
    """TPまでの距離をUSDで返す（正値=TP未到達、負値=TP超過）
    LONG:  tp_diff = (tp_price - max_high) * size_b  （正=届かなかった）
    SHORT: tp_diff = (min_low - tp_price) * size_b   （正=届かなかった）
    """
    tp_price = float(pos.get("tp_price", float("nan")))
    if side == "LONG":
        max_high = float(pos.get("max_high", float("-inf")))
        if max_high == float("-inf") or tp_price != tp_price:
            return float("nan")
        return (tp_price - max_high) * size_b
    else:
        min_low = float(pos.get("min_low", float("inf")))
        if min_low == float("inf") or tp_price != tp_price:
            return float("nan")
        return (min_low - tp_price) * size_b


def _record_trade(trades: List, pos: Dict, exit_price: float, exit_reason: str,
                  exit_ts_ms: int, params: Dict) -> None:
    side      = pos["side"]
    entry_p   = float(pos["entry_price"])
    size_b    = float(pos["size_btc"])
    add_count = int(pos["add_count"])
    entry_ms  = int(pos["entry_time"])
    priority  = pos.get("entry_priority", -1)
    hold_min  = round((exit_ts_ms - entry_ms) / 60_000, 1)

    gross = (exit_price - entry_p) * size_b if side == "LONG" else (entry_p - exit_price) * size_b
    maker = float(params.get("FEE_RATE_MAKER", 0.00014))
    taker = float(params.get("FEE_RATE_TAKER", 0.00042))
    exit_rate = maker if exit_reason == "TP_FILLED" else taker
    fee = size_b * exit_price * (maker + exit_rate)
    net   = gross - fee

    trades.append({
        "entry_time":            _ts_to_str(entry_ms),
        "exit_time":             _ts_to_str(exit_ts_ms),
        "side":                  side,
        "priority":              priority,
        "regime":                pos.get("regime", ""),
        "add_count":             add_count,
        "size_btc":              round(size_b, 4),
        "entry_price":           round(entry_p, 2),
        "exit_price":            round(exit_price, 2),
        "exit_reason":           exit_reason,
        "hold_min":              hold_min,
        "gross_usd":             round(gross, 4),
        "fee_usd":               round(fee, 4),
        "net_usd":               round(net, 4),
        "adx_at_entry":          round(float(pos.get("adx_at_entry", 0.0)), 2),
        "bb_mid_slope_at_entry": round(float(pos.get("bb_mid_slope_at_entry", float("nan"))), 4),
        "rsi_at_entry":          round(float(pos.get("rsi_at_entry", float("nan"))), 2),
        "rsi_slope_at_entry":    round(float(pos.get("rsi_slope_at_entry", float("nan"))), 4),
        "ret_5":                 round(float(pos.get("ret_5", float("nan"))), 4),
        "atr_14":                round(float(pos.get("atr_14", float("nan"))), 2),
        "entry_hour":            int(pos.get("entry_hour", -1)),
        "entry_weekday":         int(pos.get("entry_weekday", -1)),
        "mfe_usd":               round(float(pos.get("mfe_usd", 0.0)), 4),
        "mae_usd":               round(float(pos.get("mae_usd", 0.0)), 4),
        "stoch_k_at_entry":      round(float(pos.get("stoch_k_at_entry", float("nan"))), 2),
        "stoch_d_at_entry":      round(float(pos.get("stoch_d_at_entry", float("nan"))), 2),
        "bb_width_at_entry":     round(float(pos.get("bb_width_at_entry", float("nan"))), 4),
        "tp_diff_usd":           round(_calc_tp_diff(pos, side, size_b), 4),
    })


def _write_results(csv_path: str, trades: List) -> None:
    _RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stem     = pathlib.Path(csv_path).stem
    out_path = _RESULTS_DIR / f"replay_{stem}.csv"
    fields   = ["entry_time", "exit_time", "side", "priority", "regime", "add_count",
                 "size_btc", "entry_price", "exit_price", "exit_reason",
                 "hold_min", "gross_usd", "fee_usd", "net_usd",
                 "adx_at_entry", "bb_mid_slope_at_entry", "rsi_at_entry", "rsi_slope_at_entry",
                 "ret_5", "atr_14", "entry_hour", "entry_weekday",
                 "mfe_usd", "mae_usd", "tp_diff_usd",
                 "stoch_k_at_entry", "stoch_d_at_entry", "bb_width_at_entry"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(trades)
    print(f"\n[replay_csv] → {out_path}  ({len(trades)} trades)")


def _print_summary(trades: List, regime_switch: bool = False, regime_days: Dict = None) -> None:
    if not trades:
        print("[replay_csv] No trades.")
        return

    import math
    from datetime import datetime as _dt

    def _avg(vals):
        v = [x for x in vals if x is not None and not (isinstance(x, float) and math.isnan(x))]
        return sum(v) / len(v) if v else float("nan")

    # 期間計算（最初と最後のentryから）
    try:
        ts_min = min(_dt.strptime(t["entry_time"], "%Y-%m-%d %H:%M:%S") for t in trades)
        ts_max = max(_dt.strptime(t["entry_time"], "%Y-%m-%d %H:%M:%S") for t in trades)
        n_days = max(1.0, (ts_max - ts_min).total_seconds() / 86400 + 1)
    except Exception:
        n_days = 90.0

    total_net   = sum(t["net_usd"]   for t in trades)
    total_gross = sum(t["gross_usd"] for t in trades)
    total_fee   = sum(t["fee_usd"]   for t in trades)
    hold_mins   = [t["hold_min"] for t in trades]

    by_pri_all = defaultdict(list)
    for t in trades:
        by_pri_all[f"P{t['priority']}-{t['side']}"].append(t)
    pri_keys_order = sorted(by_pri_all.keys())

    _rdays = regime_days or {}
    mode_str = "レジーム切り替えON" if regime_switch else "固定パラメータ"
    print(f"\n{'='*68}")
    print(f"  [{mode_str}]  期間: {n_days:.0f}日")
    print(f"  総トレード数: {len(trades)}   NET: ${total_net:+.2f} (${total_net/n_days:+.2f}/day)")
    print(f"  GROSS: ${total_gross:+.2f}   手数料: ${total_fee:.2f}   平均保持: {_avg(hold_mins):.1f}min")
    print(f"{'='*68}")

    if regime_switch and _rdays:
        _dt_d = _rdays.get("downtrend", 1)
        _dt_net = sum(t["net_usd"] for t in trades if t.get("regime") == "downtrend")
        _dt_per = _dt_net / max(1, _dt_d)
        _goal   = 60.0
        print(f"\n  [目標対比]")
        print(f"    DT合計:  ${_dt_per:+.2f}/dt-day  ({_dt_d}dt-day)  /  目標 ${_goal:.0f}/dt-day  /  残差 {_dt_per - _goal:+.2f}")
        print(f"    全体:    ${total_net/n_days:+.2f}/total-day  ({n_days:.0f}日)")

    # ─── レジーム別セクション ────────────────────────────────────
    if regime_switch:
        _REGIME_LABEL = {
            "downtrend": "▼ DOWNTREND",
            "range":     "◆ RANGE    ",
            "uptrend":   "▲ UPTREND  ",
            "mixed":     "～ MIXED   ",
            "unknown":   "? UNKNOWN  ",
            "":          "? UNKNOWN  ",
        }
        _REGIME_PSET = {
            "downtrend": "P2-LONG / P3-LONG / P23-SHORT",
            "range":     "P4-LONG",
            "uptrend":   "P24-SHORT",
            "mixed":     "P4-LONG",
            "unknown":   "（全無効）",
            "":          "（全無効）",
        }
        by_regime = defaultdict(list)
        for t in trades:
            by_regime[t.get("regime", "unknown")].append(t)

        print(f"\n  {'━'*62}")
        print(f"  レジーム別パフォーマンス")
        print(f"  {'━'*62}")
        print(f"  {'レジーム':<13} {'件数':>4}  {'NET':>9}  {'/total':>8}  {'/rg-day':>9}  {'rg日数':>5}  {'有効Priority'}")
        print(f"  {'─'*70}")
        for regime in ["downtrend", "range", "uptrend", "mixed", "unknown", ""]:
            rts = by_regime.get(regime, [])
            if not rts:
                continue
            r_net  = sum(t["net_usd"] for t in rts)
            label  = _REGIME_LABEL.get(regime, regime)
            pset   = _REGIME_PSET.get(regime, "")
            _rg_d  = _rdays.get(regime, len(rts))
            print(f"  {label} {len(rts):4}  ${r_net:+8.2f}  ${r_net/n_days:+6.2f}/total  ${r_net/max(1,_rg_d):+6.2f}/rg  {_rg_d:4}日  {pset}")

        for regime in ["downtrend", "range", "uptrend", "mixed", "unknown", ""]:
            rts = by_regime.get(regime, [])
            if not rts:
                continue
            label = _REGIME_LABEL.get(regime, regime).strip()
            pset  = _REGIME_PSET.get(regime, "")
            r_net = sum(t["net_usd"] for t in rts)

            print(f"\n  ┌── {label}  (有効: {pset}) ──")
            _rg_d_sec = max(1, _rdays.get(regime, int(n_days)))
            print(f"  │  {'Priority':<12} {'件数':>4}  {'NET':>9}  {'/total':>8}  {'/rg-day':>9}  {'TP率':>5}  {'avgNET':>7}  {'avgHold':>8}  {'損失合計':>9}")

            by_pri_r = defaultdict(list)
            for t in rts:
                by_pri_r[f"P{t['priority']}-{t['side']}"].append(t)
            for pri in sorted(by_pri_r):
                ts2   = by_pri_r[pri]
                n     = len(ts2)
                net   = sum(t["net_usd"] for t in ts2)
                tp_n  = sum(1 for t in ts2 if t["exit_reason"] == "TP_FILLED")
                avg_h = _avg([t["hold_min"] for t in ts2])
                loss_n = sum(t["net_usd"] for t in ts2 if t["net_usd"] < 0)
                print(f"  │  {pri:<12} {n:4}  ${net:+8.2f}  ${net/n_days:+6.2f}/total  ${net/_rg_d_sec:+6.2f}/rg  {tp_n/n*100:4.0f}%  ${net/n:+6.2f}  {avg_h:7.1f}min  ${loss_n:+.0f}")

            # Exit理由別（テーブル形式）
            by_reason_r: dict = defaultdict(lambda: {"c": 0, "n": 0.0})
            for t in rts:
                by_reason_r[t["exit_reason"]]["c"] += 1
                by_reason_r[t["exit_reason"]]["n"] += t["net_usd"]
            print(f"  │  {'Exit理由':<24} {'件数':>5}  {'NET':>9}")
            for _r, _v in sorted(by_reason_r.items(), key=lambda x: -abs(x[1]["n"])):
                print(f"  │   {_r:<23} {_v['c']:4}件  ${_v['n']:+8.0f}")

            # Pri × Exit クロス集計（レジーム別）
            _all_r_rg = sorted(by_reason_r.keys(), key=lambda r: -abs(by_reason_r[r]["n"]))
            print(f"  │")
            print(f"  │  [Pri × Exit クロス]")
            _hdr_x = f"  │  {'Pri':<12}" + "".join(f"  {r[:10]:>10}" for r in _all_r_rg)
            print(_hdr_x)
            for _pri_x in sorted(by_pri_r):
                _cross = defaultdict(lambda: {"count": 0, "net": 0.0})
                for t in by_pri_r[_pri_x]:
                    _cross[t["exit_reason"]]["count"] += 1
                    _cross[t["exit_reason"]]["net"]   += t["net_usd"]
                _row_x = f"  │  {_pri_x:<12}"
                for _r in _all_r_rg:
                    _cell = f"{_cross[_r]['count']}件${_cross[_r]['net']:+.0f}" if _cross[_r]["count"] else "-"
                    _row_x += f"  {_cell:>10}"
                print(_row_x)

            # TIME_EXIT × add_count（レジーム別）
            _te_rg = [t for t in rts if t["exit_reason"] == "TIME_EXIT"]
            if _te_rg:
                _by_add_te: dict = defaultdict(list)
                for t in _te_rg:
                    _by_add_te[t["add_count"]].append(t)
                print(f"  │")
                print(f"  │  [TIME_EXIT × add_count]")
                print(f"  │  {'add':>4}  {'件数':>4}  {'NET':>9}  {'avgNET':>7}  {'avgHold':>8}  {'avgADX':>7}")
                for _add in sorted(_by_add_te):
                    _ts_a = _by_add_te[_add]
                    _net_a = sum(t["net_usd"] for t in _ts_a)
                    print(f"  │  {_add:4}  {len(_ts_a):4}  ${_net_a:+8.2f}  ${_net_a/len(_ts_a):+6.2f}"
                          f"  {_avg([t['hold_min'] for t in _ts_a]):7.1f}min  {_avg([t['adx_at_entry'] for t in _ts_a]):6.1f}")

            # TP_FILLED × add_count（レジーム別）
            _tp_rg = [t for t in rts if t["exit_reason"] == "TP_FILLED"]
            if _tp_rg:
                _by_add_tp: dict = defaultdict(list)
                for t in _tp_rg:
                    _by_add_tp[t["add_count"]].append(t)
                print(f"  │")
                print(f"  │  [TP_FILLED × add_count]")
                print(f"  │  {'add':>4}  {'件数':>4}  {'NET':>9}  {'avgNET':>7}  {'avgHold':>8}  {'avgADX':>7}")
                for _add in sorted(_by_add_tp):
                    _ts_a = _by_add_tp[_add]
                    _net_a = sum(t["net_usd"] for t in _ts_a)
                    print(f"  │  {_add:4}  {len(_ts_a):4}  ${_net_a:+8.2f}  ${_net_a/len(_ts_a):+6.2f}"
                          f"  {_avg([t['hold_min'] for t in _ts_a]):7.1f}min  {_avg([t['adx_at_entry'] for t in _ts_a]):6.1f}")

            # MFE_STALE_CUT Priority別（レジーム別）
            _stale_rg = [t for t in rts if t["exit_reason"] == "MFE_STALE_CUT"]
            if _stale_rg:
                _by_pri_s: dict = defaultdict(list)
                for t in _stale_rg:
                    _by_pri_s[f"P{t['priority']}-{t['side']}"].append(t)
                print(f"  │")
                print(f"  │  [MFE_STALE_CUT Priority別]")
                print(f"  │  {'Pri':<12}  {'件数':>4}  {'NET':>9}  {'avgMFE':>8}  {'avgMAE':>8}  {'avgHold':>8}")
                for _pri_s in sorted(_by_pri_s):
                    _ts_s = _by_pri_s[_pri_s]
                    _net_s = sum(t["net_usd"] for t in _ts_s)
                    print(f"  │  {_pri_s:<12}  {len(_ts_s):4}  ${_net_s:+8.2f}"
                          f"  ${_avg([t['mfe_usd'] for t in _ts_s]):+7.2f}"
                          f"  ${_avg([t['mae_usd'] for t in _ts_s]):+7.2f}"
                          f"  {_avg([t['hold_min'] for t in _ts_s]):7.1f}min")

            # Entry指標統計 TP vs 損失（レジーム別）
            _tp_r2   = [t for t in rts if t["exit_reason"] == "TP_FILLED"]
            _loss_r2 = [t for t in rts if t["exit_reason"] != "TP_FILLED"]
            print(f"  │")
            print(f"  │  [Entry指標 TP vs 損失]")
            print(f"  │  {'指標':<22}  {'TP avg':>8}  {'損失 avg':>8}")
            for _field, _label in [("adx_at_entry", "ADX"), ("bb_mid_slope_at_entry", "BB_slope"),
                                    ("rsi_at_entry", "RSI"), ("atr_14", "atr_14($)")]:
                print(f"  │  {_label:<22}  {_avg([t[_field] for t in _tp_r2]):8.2f}"
                      f"  {_avg([t[_field] for t in _loss_r2]):8.2f}")

            # TIME_EXIT Entry指標 Priority別（レジーム別）
            _te2_rg = [t for t in rts if t["exit_reason"] == "TIME_EXIT"]
            if _te2_rg:
                _by_pri_te: dict = defaultdict(list)
                for t in _te2_rg:
                    _by_pri_te[f"P{t['priority']}-{t['side']}"].append(t)
                print(f"  │")
                print(f"  │  [TIME_EXIT Entry指標 Priority別]")
                print(f"  │  {'Pri':<12}  {'件数':>4}  {'NET':>9}  {'avgADX':>7}  {'avgSlope':>9}  {'avgATR':>7}")
                for _pri_te in sorted(_by_pri_te):
                    _ts_t = _by_pri_te[_pri_te]
                    _net_t = sum(t["net_usd"] for t in _ts_t)
                    print(f"  │  {_pri_te:<12}  {len(_ts_t):4}  ${_net_t:+8.2f}"
                          f"  {_avg([t['adx_at_entry'] for t in _ts_t]):6.1f}"
                          f"  {_avg([t['bb_mid_slope_at_entry'] for t in _ts_t]):8.1f}"
                          f"  {_avg([t['atr_14'] for t in _ts_t]):7.1f}")

            print(f"  └{'─'*61}")

    # ─── 全体Exit理由別 ──────────────────────────────────────────
    by_reason = defaultdict(lambda: {"count": 0, "net": 0.0})
    for t in trades:
        by_reason[t["exit_reason"]]["count"] += 1
        by_reason[t["exit_reason"]]["net"]   += t["net_usd"]
    all_reasons = sorted({t["exit_reason"] for t in trades}, key=lambda r: -abs(by_reason[r]["net"]))

    print(f"\n  [Exit理由別（全体）]")
    print(f"    {'理由':<28} {'件数':>4}  {'NET':>9}  {'/day':>7}")
    for reason, v in sorted(by_reason.items(), key=lambda x: -abs(x[1]["net"])):
        print(f"    {reason:<28} {v['count']:4}件  ${v['net']:+8.2f}  ${v['net']/n_days:+6.2f}")

    # ─── Priority × Exit reason クロス集計 ──────────────────────
    print(f"\n  [Priority × Exit reason クロス集計]")
    hdr = f"    {'Pri':<12}" + "".join(f"  {r[:10]:>10}" for r in all_reasons)
    print(hdr)
    for pri in pri_keys_order:
        ts = by_pri_all[pri]
        cross = defaultdict(lambda: {"count": 0, "net": 0.0})
        for t in ts:
            cross[t["exit_reason"]]["count"] += 1
            cross[t["exit_reason"]]["net"]   += t["net_usd"]
        row = f"    {pri:<12}"
        for r in all_reasons:
            cell = f"{cross[r]['count']}件${cross[r]['net']:+.0f}" if cross[r]["count"] else "-"
            row += f"  {cell:>10}"
        print(row)

    # ─── TIME_EXIT × add_count 詳細 ─────────────────────────────
    bad_te = [t for t in trades if t["exit_reason"] == "TIME_EXIT"]
    if bad_te:
        by_add = defaultdict(list)
        for t in bad_te:
            by_add[t["add_count"]].append(t)
        print(f"\n  [TIME_EXIT × add_count 詳細]")
        print(f"    {'add':>4}  {'件数':>4}  {'NET':>9}  {'avgNET':>7}  {'avgHold':>8}  {'avgADX':>7}")
        for add in sorted(by_add):
            ts2 = by_add[add]
            net2 = sum(t["net_usd"] for t in ts2)
            print(f"    {add:4}  {len(ts2):4}  ${net2:+8.2f}  ${net2/len(ts2):+6.2f}"
                  f"  {_avg([t['hold_min'] for t in ts2]):7.1f}min  {_avg([t['adx_at_entry'] for t in ts2]):6.1f}")

    # ─── TP_FILLED × add_count 詳細 ─────────────────────────────
    tp_filled = [t for t in trades if t["exit_reason"] == "TP_FILLED"]
    if tp_filled:
        by_add_tp = defaultdict(list)
        for t in tp_filled:
            by_add_tp[t["add_count"]].append(t)
        print(f"\n  [TP_FILLED × add_count 詳細]")
        print(f"    {'add':>4}  {'件数':>4}  {'NET':>9}  {'avgNET':>7}  {'avgHold':>8}  {'avgADX':>7}")
        for add in sorted(by_add_tp):
            ts2 = by_add_tp[add]
            net2 = sum(t["net_usd"] for t in ts2)
            print(f"    {add:4}  {len(ts2):4}  ${net2:+8.2f}  ${net2/len(ts2):+6.2f}"
                  f"  {_avg([t['hold_min'] for t in ts2]):7.1f}min  {_avg([t['adx_at_entry'] for t in ts2]):6.1f}")

    # ─── MFE_STALE_CUT 詳細 ─────────────────────────────────────
    stale_trades = [t for t in trades if t["exit_reason"] == "MFE_STALE_CUT"]
    if stale_trades:
        by_pri_stale = defaultdict(list)
        for t in stale_trades:
            by_pri_stale[f"P{t['priority']}-{t['side']}"].append(t)
        print(f"\n  [MFE_STALE_CUT 詳細 Priority別]")
        print(f"    {'Pri':<12}  {'件数':>4}  {'NET':>9}  {'avgMFE':>8}  {'avgMAE':>8}  {'avgTP_diff':>10}  {'avgHold':>8}")
        for pri in pri_keys_order:
            ts_s = by_pri_stale.get(pri, [])
            if not ts_s:
                continue
            net_s = sum(t["net_usd"] for t in ts_s)
            print(f"    {pri:<12}  {len(ts_s):4}  ${net_s:+8.2f}"
                  f"  ${_avg([t['mfe_usd'] for t in ts_s]):+7.2f}"
                  f"  ${_avg([t['mae_usd'] for t in ts_s]):+7.2f}"
                  f"  ${_avg([t['tp_diff_usd'] for t in ts_s]):+9.2f}"
                  f"  {_avg([t['hold_min'] for t in ts_s]):7.1f}min")

    # ─── Entry指標統計（TP vs 損失） ─────────────────────────────
    tp_trades   = [t for t in trades if t["exit_reason"] == "TP_FILLED"]
    loss_trades = [t for t in trades if t["exit_reason"] != "TP_FILLED"]
    print(f"\n  [Entry指標統計 TP vs 損失]")
    print(f"    {'指標':<22}  {'TP avg':>8}  {'損失 avg':>8}")
    for field, label in [("adx_at_entry", "ADX"), ("bb_mid_slope_at_entry", "BB_slope"),
                         ("rsi_at_entry", "RSI"), ("ret_5", "ret_5(%)"), ("atr_14", "atr_14($)")]:
        print(f"    {label:<22}  {_avg([t[field] for t in tp_trades]):8.2f}"
              f"  {_avg([t[field] for t in loss_trades]):8.2f}")

    # ─── 月別 NET ────────────────────────────────────────────────
    by_month: Dict[str, List] = defaultdict(list)
    for t in trades:
        month = t["entry_time"][:7]  # "YYYY-MM"
        by_month[month].append(t)
    print(f"\n  [月別 NET]")
    print(f"    {'月':>7}  {'件数':>4}  {'NET':>9}  {'TP率':>5}  {'/day':>7}")
    for month in sorted(by_month):
        ts_m  = by_month[month]
        net_m = sum(t["net_usd"] for t in ts_m)
        tp_r  = sum(1 for t in ts_m if t["exit_reason"] == "TP_FILLED") / len(ts_m) * 100
        # 月の日数（月末日 - 月初日 + 1 の近似として件数の最初と最後から計算）
        days_m = 30.0
        try:
            t_min = min(_dt.strptime(t["entry_time"], "%Y-%m-%d %H:%M:%S") for t in ts_m)
            t_max = max(_dt.strptime(t["entry_time"], "%Y-%m-%d %H:%M:%S") for t in ts_m)
            days_m = max(1.0, (t_max - t_min).total_seconds() / 86400 + 1)
        except Exception:
            pass
        print(f"    {month}  {len(ts_m):4}  ${net_m:+8.2f}  {tp_r:4.0f}%  ${net_m/days_m:+6.2f}")

    # ─── 時間帯別 NET ────────────────────────────────────────────
    by_hour: Dict[int, List] = defaultdict(list)
    for t in trades:
        by_hour[t["entry_hour"]].append(t)
    print(f"\n  [時間帯別 NET（JST）]")
    print(f"    {'hour':>4}  {'件数':>4}  {'NET':>9}  {'TP率':>5}  {'avgNET':>7}")
    for h in sorted(by_hour):
        ts_h  = by_hour[h]
        net_h = sum(t["net_usd"] for t in ts_h)
        tp_r  = sum(1 for t in ts_h if t["exit_reason"] == "TP_FILLED") / len(ts_h) * 100
        print(f"    {h:4}  {len(ts_h):4}  ${net_h:+8.2f}  {tp_r:4.0f}%  ${net_h/len(ts_h):+6.2f}")

    # ─── TIME_EXIT Entry指標 Priority別 ─────────────────────────
    bad_te2 = [t for t in trades if t["exit_reason"] == "TIME_EXIT"]
    if bad_te2:
        by_pri2 = defaultdict(list)
        for t in bad_te2:
            by_pri2[f"P{t['priority']}-{t['side']}"].append(t)
        print(f"\n  [TIME_EXIT Entry指標 Priority別]")
        print(f"    {'Pri':<12}  {'件数':>4}  {'NET':>9}  {'avgADX':>7}  {'avgSlope':>9}  {'avgRSI':>7}  {'avgATR':>8}")
        for pri in pri_keys_order:
            ts3 = by_pri2.get(pri, [])
            if not ts3:
                continue
            net3 = sum(t["net_usd"] for t in ts3)
            print(f"    {pri:<12}  {len(ts3):4}  ${net3:+8.2f}"
                  f"  {_avg([t['adx_at_entry'] for t in ts3]):6.1f}"
                  f"  {_avg([t['bb_mid_slope_at_entry'] for t in ts3]):8.1f}"
                  f"  {_avg([t['rsi_at_entry'] for t in ts3]):6.1f}"
                  f"  {_avg([t['atr_14'] for t in ts3]):7.1f}")

    print(f"\n{'='*64}\n")


# ==============================================================
# エントリー時の状態指標計算
# ==============================================================
def _calc_entry_states(df: "pd.DataFrame", i: int, ts_ms: int) -> Dict:
    """ret_5 / atr_14 / entry_hour / entry_weekday を計算して返す"""
    close_now = float(df.iloc[i]["close"])

    # 直前5本リターン（%）
    ret_5 = (close_now / float(df.iloc[i - 5]["close"]) - 1.0) * 100 if i >= 5 else float("nan")

    # ATR14: 直前14本の平均 True Range（$）
    tr_vals = []
    for j in range(max(1, i - 13), i + 1):
        h  = float(df.iloc[j]["high_raw"])
        l  = float(df.iloc[j]["low_raw"])
        pc = float(df.iloc[j - 1]["close"])
        tr_vals.append(max(h - l, abs(h - pc), abs(l - pc)))
    atr_14 = sum(tr_vals) / len(tr_vals) if tr_vals else float("nan")

    dt = datetime.fromtimestamp(ts_ms / 1000, tz=_JST)
    return {
        "ret_5":         round(ret_5, 4),
        "atr_14":        round(atr_14, 2),
        "entry_hour":    dt.hour,
        "entry_weekday": dt.weekday(),   # 0=Mon, 6=Sun
    }


# ==============================================================
# メインループ
# ==============================================================
def _build_regime_map(csv_5m_path: str) -> Dict:
    """5m CSV + 日足warmupから date(Timestamp normalized) → regime文字列 のdictを返す。"""
    try:
        import numpy as np
        import ta
    except ImportError:
        print("[regime] numpy/ta not available; regime_switch disabled")
        return {}

    df_5m = _load_csv(csv_5m_path)
    df_5m_indexed = df_5m.copy()
    df_5m_indexed.index = pd.to_datetime(df_5m["timestamp_ms"], unit="ms")
    df_5m_indexed = df_5m_indexed.sort_index()
    daily_5m = df_5m_indexed.resample("D").agg(
        {"close": "last", "high": "max", "low": "min"}
    ).dropna()

    dw = pd.read_csv(_DAILY_WARMUP)
    dw["ts"] = pd.to_datetime(dw["timestamp"])
    for c in ("close", "high", "low"):
        dw[c] = pd.to_numeric(dw[c], errors="coerce")
    dw = dw.set_index("ts").sort_index()

    combined = pd.concat([dw[["close", "high", "low"]], daily_5m[["close", "high", "low"]]])
    combined = combined[~combined.index.duplicated(keep="last")].sort_index()
    for c in ("close", "high", "low"):
        combined[c] = pd.to_numeric(combined[c], errors="coerce")

    combined["ma70"]       = combined["close"].rolling(70, min_periods=70).mean()
    combined["ma70_slope"] = combined["ma70"].diff(5)
    adx_obj = ta.trend.ADXIndicator(combined["high"], combined["low"], combined["close"], window=14)
    combined["adx_d"] = adx_obj.adx()

    def _classify(row):
        slope, adx_v, close, ma = row["ma70_slope"], row["adx_d"], row["close"], row["ma70"]
        if any(pd.isna(v) for v in [slope, adx_v, close, ma]):
            return "unknown"
        if adx_v < 20:
            return "range"
        if slope > 0 and close > ma:
            return "uptrend"
        if slope < 0 and close < ma:
            return "downtrend"
        return "mixed"

    start = pd.to_datetime(df_5m["timestamp_ms"].min(), unit="ms").normalize()
    regime_df = combined[combined.index >= start].copy()
    regime_df["regime"] = regime_df.apply(_classify, axis=1)
    print(f"[regime] 分布: {regime_df['regime'].value_counts().to_dict()}")
    return {pd.Timestamp(idx).normalize(): r for idx, r in zip(regime_df.index, regime_df["regime"])}


def preload(csv_path: str, params: Dict):
    """CSV読み込み＋preprocess を実行して (df, df_raw) を返す。
    グリッドサーチで preprocess を1回だけ走らせたい場合に使う。"""
    df_raw = _load_csv(csv_path)
    df_for_prep = df_raw[["timestamp_ms", "open", "high", "low", "close"]].copy()
    df_for_prep["timestamp"] = pd.to_datetime(df_for_prep["timestamp_ms"], unit="ms")
    if "volume" in df_raw.columns:
        df_for_prep["volume"] = df_raw["volume"].values
    else:
        df_for_prep["volume"] = 0.0
    df = preprocess(df_for_prep[["timestamp", "open", "high", "low", "close", "volume"]].copy(), params)
    df["timestamp_ms"] = df_raw["timestamp_ms"].values
    df["high_raw"] = df_raw["high"].values
    df["low_raw"]  = df_raw["low"].values
    return df, df_raw


def run(csv_path: str, params: Dict, _preloaded=None, regime_switch: bool = False,
        _regime_map_in: Dict = None) -> List[Dict]:
    """CSV をリプレイして trades リストを返す。グリッドサーチ等から直接呼び出し可。
    _preloaded=(df, df_raw) を渡すと CSV読み込み・preprocess をスキップする。
    _regime_map_in を渡すと _build_regime_map の再実行をスキップする。"""
    if _preloaded is not None:
        df, df_raw = _preloaded
    else:
        try:
            df, df_raw = preload(csv_path, params)
        except Exception as e:
            print(f"[ERROR] preprocess failed: {e}")
            return []

    # バー足間隔を自動検出（5m=300000ms, 1m=60000ms 等）
    _bar_ms = int(df_raw["timestamp_ms"].iloc[1] - df_raw["timestamp_ms"].iloc[0])

    # 状態変数（in-memory）
    pos:     Dict[str, Optional[Dict]] = {"LONG": None, "SHORT": None}
    pending: Dict[str, Optional[Dict]] = {"LONG": None, "SHORT": None}
    trades:  List[Dict]                = []

    # レジーム切り替え用
    if regime_switch:
        _regime_map = _regime_map_in if _regime_map_in is not None else _build_regime_map(csv_path)
    else:
        _regime_map = {}
    _current_regime: Optional[str] = None
    _working_params = dict(params)

    # ---- バーごとのループ ----
    for i in range(CANDLE_WARMUP, len(df)):
        row       = df.iloc[i]
        ts_ms     = int(row["timestamp_ms"])
        close_p   = float(row["close"])
        high_p    = float(row["high_raw"])
        low_p     = float(row["low_raw"])
        mark_p    = close_p  # BT と同条件

        # --------------------------------------------------
        # 1. pending fill チェック
        # --------------------------------------------------
        for side in ("LONG", "SHORT"):
            pnd = pending[side]
            if pnd is None:
                continue

            placed_ms   = int(pnd["placed_bar_ms"])
            bar_elapsed = max(0, (ts_ms - placed_ms) // _bar_ms)

            # TTL 切れ → キャンセル
            if bar_elapsed >= PENDING_TTL_BARS:
                pending[side] = None
                continue

            # fill判定（intra-bar: LONG=low, SHORT=high）
            limit_p = float(pnd["limit_price"])
            filled  = (side == "LONG" and low_p <= limit_p) or \
                      (side == "SHORT" and high_p >= limit_p)
            if not filled:
                continue
            fill_p = limit_p
            adx_val   = float(pnd.get("adx_at_entry", 0.0))
            _pri_size_key = f"P{pnd['priority']}_POSITION_SIZE_BTC"
            _add_sizes = params.get(f"P{pnd['priority']}_ADD_SIZES_BTC")
            if _add_sizes:
                _cur_add_idx = int(pos[side]["add_count"]) if pos[side] is not None else 0
                unit_size = float(_add_sizes[min(_cur_add_idx, len(_add_sizes) - 1)])
            else:
                unit_size = float(params.get(_pri_size_key, params[f"{side}_POSITION_SIZE_BTC"]))
            states    = _calc_entry_states(df, i, ts_ms)

            if pos[side] is None:
                # 新規エントリー
                _entry_pri = pnd["priority"]
                if _entry_pri in (1, 21):
                    _bb_u = float(df.at[i, "bb_sigma2_upper"]) if "bb_sigma2_upper" in df.columns else float("nan")
                    _bb_l = float(df.at[i, "bb_sigma2_lower"]) if "bb_sigma2_lower" in df.columns else float("nan")
                    if not (math.isnan(_bb_u) or math.isnan(_bb_l)):
                        _bb_half  = (_bb_u - _bb_l) / 2
                        _tp_key_r = "P1_TP_BB_RATIO" if _entry_pri == 1 else "P21_TP_BB_RATIO"
                        _tp_key_m = "P1_TP_MIN_PCT"  if _entry_pri == 1 else "P21_TP_MIN_PCT"
                        _tp_ratio = float(params.get(_tp_key_r, 1.0))
                        _tp_min   = float(params.get(_tp_key_m, 0.0003))
                        _tp_dist  = max(_bb_half * _tp_ratio, fill_p * _tp_min)
                        tp_price  = fill_p + _tp_dist if side == "LONG" else fill_p - _tp_dist
                    else:
                        tp_price = _calc_tp_price(side, fill_p, adx_val, params, _entry_pri)
                else:
                    tp_price = _calc_tp_price(side, fill_p, adx_val, params, _entry_pri)
                pos[side] = {
                    "side":                  side,
                    "entry_priority":        pnd["priority"],
                    "entry_price":           fill_p,
                    "entry_time":            ts_ms,
                    "add_count":             1,
                    "size_btc":              unit_size,
                    "tp_price":              tp_price,
                    "sl_price":              _calc_sl_price(side, fill_p, params, _entry_pri),
                    "regime":                _current_regime or "",
                    "mfe_usd":               0.0,
                    "mae_usd":               0.0,
                    "max_high":              float("-inf"),
                    "min_low":               float("inf"),
                    "adx_at_entry":          pnd.get("adx_at_entry", 0.0),
                    "bb_mid_slope_at_entry": pnd.get("bb_mid_slope_at_entry", float("nan")),
                    "rsi_at_entry":          pnd.get("rsi_at_entry", float("nan")),
                    "rsi_slope_at_entry":    pnd.get("rsi_slope_at_entry", float("nan")),
                    "stoch_k_at_entry":      pnd.get("stoch_k_at_entry", float("nan")),
                    "stoch_d_at_entry":      pnd.get("stoch_d_at_entry", float("nan")),
                    "bb_width_at_entry":     pnd.get("bb_width_at_entry", float("nan")),
                    "ret_5":                 states["ret_5"],
                    "atr_14":                states["atr_14"],
                    "entry_hour":            states["entry_hour"],
                    "entry_weekday":         states["entry_weekday"],
                    "mfe_peak_pct":          0.0,
                    "trail_stop_price":      None,
                }
            else:
                # ADD
                p       = pos[side]
                old_sz  = float(p["size_btc"])
                old_p   = float(p["entry_price"])
                new_sz  = old_sz + unit_size
                new_avg = (old_p * old_sz + fill_p * unit_size) / new_sz
                new_cnt = int(p["add_count"]) + 1
                tp_price = _calc_tp_price(side, new_avg, adx_val, params, p["entry_priority"])
                sl_price = _calc_sl_price(side, new_avg, params, int(p.get("entry_priority", 0))) if new_cnt >= 2 else None
                p.update({
                    "entry_price": new_avg,
                    "add_count":   new_cnt,
                    "size_btc":    new_sz,
                    "tp_price":    tp_price,
                    "sl_price":    sl_price,
                })

            pending[side] = None

        # --------------------------------------------------
        # 2. MFE / MAE / 価格極値 更新（exit チェック前に必ず更新）
        # --------------------------------------------------
        for side in ("LONG", "SHORT"):
            p = pos[side]
            if p is None:
                continue
            entry_p = float(p["entry_price"])
            size_b  = float(p["size_btc"])
            unreal  = ((mark_p - entry_p) if side == "LONG" else (entry_p - mark_p)) * size_b
            if unreal > float(p.get("mfe_usd", 0.0)):
                p["mfe_usd"] = unreal
            if unreal < float(p.get("mae_usd", 0.0)):
                p["mae_usd"] = unreal
            # 価格極値（tp_diff計算用）
            if side == "LONG":
                if high_p > float(p.get("max_high", float("-inf"))):
                    p["max_high"] = high_p
            else:
                if low_p < float(p.get("min_low", float("inf"))):
                    p["min_low"] = low_p

            # P1/P21: high/low ベースで MFE ピーク追跡 → trail_stop_price 更新
            if int(p.get("entry_priority", -1)) in (1, 21):
                _ep = float(p["entry_price"])
                _fav_pct = ((high_p - _ep) / _ep * 100 if side == "LONG"
                            else ((_ep - low_p) / _ep * 100))
                _prev_peak = float(p.get("mfe_peak_pct", 0.0))
                if _fav_pct > _prev_peak:
                    p["mfe_peak_pct"] = _fav_pct
                    _trail_pri = int(p.get("entry_priority", 1))
                    _gate  = float(params.get(f"P{_trail_pri}_MFE_GATE_PCT", 0.05))
                    _ratio = float(params.get(f"P{_trail_pri}_TRAIL_RATIO", 0.8))
                    if _fav_pct >= _gate:
                        if side == "LONG":
                            p["trail_stop_price"] = _ep * (1 + _fav_pct / 100 * _ratio)
                        else:
                            p["trail_stop_price"] = _ep * (1 - _fav_pct / 100 * _ratio)

        # --------------------------------------------------
        # 3. TP 発動チェック（close が TP 価格を超えたか）
        # --------------------------------------------------
        for side in ("LONG", "SHORT"):
            p = pos[side]
            if p is None:
                continue
            tp = float(p["tp_price"])
            tp_hit = (side == "LONG" and high_p >= tp) or \
                     (side == "SHORT" and low_p <= tp)
            if tp_hit:
                _record_trade(trades, p, exit_price=tp, exit_reason="TP_FILLED",
                              exit_ts_ms=ts_ms, params=params)
                pos[side] = None

        # --------------------------------------------------
        # 4. SL 発動チェック（close が SL 価格を超えたか）
        # --------------------------------------------------
        for side in ("LONG", "SHORT"):
            p = pos[side]
            if p is None or p.get("sl_price") is None:
                continue
            sl = float(p["sl_price"])
            sl_hit = (side == "LONG" and low_p <= sl) or \
                     (side == "SHORT" and high_p >= sl)
            if sl_hit:
                _record_trade(trades, p, exit_price=sl, exit_reason="SL_FILLED",
                              exit_ts_ms=ts_ms, params=params)
                pos[side] = None

        # --------------------------------------------------
        # 4b. TRAIL_EXIT チェック（P1/P21専用・price-level trailing stop）
        # --------------------------------------------------
        for side in ("LONG", "SHORT"):
            p = pos[side]
            if p is None or int(p.get("entry_priority", -1)) not in (1, 21):
                continue
            tsp = p.get("trail_stop_price")
            if tsp is None:
                continue
            tsp = float(tsp)
            trail_hit = (side == "LONG" and low_p <= tsp) or \
                        (side == "SHORT" and high_p >= tsp)
            if trail_hit:
                _record_trade(trades, p, exit_price=tsp, exit_reason="TRAIL_EXIT",
                              exit_ts_ms=ts_ms, params=params)
                pos[side] = None

        # --------------------------------------------------
        # 5. _check_exits_replay（TP/SL 以外の Exit）
        # --------------------------------------------------
        for side in ("LONG", "SHORT"):
            p = pos[side]
            if p is None:
                continue
            exit_reason = _check_exits_replay(p, mark_p, df, i, params, ts_ms)
            if exit_reason:
                _record_trade(trades, p, exit_price=mark_p, exit_reason=exit_reason,
                              exit_ts_ms=ts_ms, params=params)
                pos[side] = None

        # --------------------------------------------------
        # 6. エントリー / ADD 判断
        # --------------------------------------------------
        # レジーム切り替え（新規エントリーのみに影響。既存ポジションは継続）
        if regime_switch and _regime_map:
            _bar_date   = pd.Timestamp(ts_ms, unit="ms").normalize()
            _new_regime = _regime_map.get(_bar_date, "unknown")
            if _new_regime != _current_regime:
                _current_regime = _new_regime
                _working_params = dict(params)
                _working_params.update(_REGIME_PRIORITY_SETS.get(_new_regime, {}))

        try:
            priority = check_entry_priority(i, df, _working_params)
        except Exception:
            priority = None

        if priority is None:
            continue

        side = "LONG" if priority in _LONG_PRIORITIES else "SHORT"

        # pending がすでにあればスキップ
        if pending[side] is not None:
            continue

        # ADD 上限チェック
        if pos[side] is not None:
            p        = pos[side]
            add_cnt  = int(p["add_count"])
            pos_pri  = int(p["entry_priority"])
            max_adds = int(params.get(f"P{pos_pri}_MAX_ADDS",
                           params.get("MAX_ADDS_BY_PRIORITY", {}).get(
                               str(pos_pri), params.get(f"{side}_MAX_ADDS", 5))))
            if add_cnt >= max_adds:
                continue

        # maker指値: ±0.01%
        if side == "LONG":
            lp = float(Decimal(str(close_p)) * Decimal("0.9999"))
        else:
            lp = float(Decimal(str(close_p)) * Decimal("1.0001"))

        adx_val        = float(df.at[i, "adx"])             if "adx"             in df.columns else 0.0
        slope_val      = float(df.at[i, "bb_mid_slope"])    if "bb_mid_slope"    in df.columns else float("nan")
        rsi_val        = float(df.at[i, "rsi_short"])       if "rsi_short"       in df.columns else float("nan")
        rsi_slope_val  = float(df.at[i, "rsi_slope_short"]) if "rsi_slope_short" in df.columns else float("nan")
        stoch_k_val    = float(df.at[i, "stoch_k"])         if "stoch_k"         in df.columns else float("nan")
        stoch_d_val    = float(df.at[i, "stoch_d"])         if "stoch_d"         in df.columns else float("nan")
        bb_width_val   = float(df.at[i, "bb_width"])        if "bb_width"        in df.columns else float("nan")
        pending[side] = {
            "side":                  side,
            "priority":              priority,
            "limit_price":           lp,
            "placed_bar_ms":         ts_ms,
            "adx_at_entry":          adx_val,
            "bb_mid_slope_at_entry": slope_val,
            "rsi_at_entry":          rsi_val,
            "rsi_slope_at_entry":    rsi_slope_val,
            "stoch_k_at_entry":      stoch_k_val,
            "stoch_d_at_entry":      stoch_d_val,
            "bb_width_at_entry":     bb_width_val,
        }

    # ---- 未クローズポジションを強制クローズ（期間末） ----
    last_ts    = int(df.iloc[-1]["timestamp_ms"])
    last_close = float(df.iloc[-1]["close"])
    for side in ("LONG", "SHORT"):
        if pos[side] is not None:
            _record_trade(trades, pos[side], exit_price=last_close,
                          exit_reason="FORCE_CLOSE_EOD", exit_ts_ms=last_ts, params=params)

    return trades


# ==============================================================
# シグナルファネル分析（P2/P3/P23 フィルター段階別通過件数）
# ==============================================================
def _signal_funnel(df: "pd.DataFrame", params: Dict) -> None:
    """P2/P3/P23 各フィルター段階で何件落とされているかを表示する。
    run() とは独立して呼ぶ（グリッドサーチには影響しない）。"""
    import math

    n_bars = len(df) - CANDLE_WARMUP
    ts_start = int(df.iloc[CANDLE_WARMUP]["timestamp_ms"])
    ts_end   = int(df.iloc[-1]["timestamp_ms"])
    n_days   = max(1.0, (ts_end - ts_start) / (86_400 * 1_000))

    def _g(i, col):
        if col not in df.columns or i < 0 or i >= len(df):
            return float("nan")
        try:
            return float(df.at[i, col])
        except Exception:
            return float("nan")

    # ── P2 LONG フィルター定数 ──
    p2_gap_min      = float(params.get("P2_STOCH_GAP_MIN",  0.3))
    p2_k_min        = float(params.get("P2_STOCH_K_MIN",    0.0))
    p2_adx_min      = float(params.get("P2_ADX_MIN",        0.0))
    p2_rsi_min      = float(params.get("P2_RSI_MIN",        0.0))
    p2_atr_min      = float(params.get("P2_ATR14_MIN",      0.0))
    p2_atr_max      = float(params.get("P2_ATR14_MAX",  99999.0))
    p2_adx_excl_min = float(params.get("P2_ADX_EXCL_MIN",   0.0))
    p2_adx_excl_max = float(params.get("P2_ADX_EXCL_MAX",   0.0))

    # ── P23 SHORT フィルター定数 ──
    p23_slope_max = float(params.get("P23_BB_MID_SLOPE_MAX", 0.0))
    p23_adx_min   = float(params.get("P23_ADX_MIN",         0.0))
    p23_adx_max   = float(params.get("P23_ADX_MAX",      9999.0))
    p23_atr_min   = float(params.get("P23_ATR14_MIN",       0.0))

    # ── P3 LONG フィルター定数 ──
    p3_slope_min = float(params.get("P3_BB_MID_SLOPE_MIN", 10.0))
    p3_adx_min   = float(params.get("P3_ADX_MIN",          30.0))
    p3_adx_max   = float(params.get("P3_ADX_MAX",          50.0))
    p3_atr_min   = float(params.get("P3_ATR14_MIN",       250.0))

    p2_counts  = [0] * 6   # [base, +k, +adx, +rsi, +atr, +adx_excl]
    p23_counts = [0] * 4   # [base, +adx_range, +atr, ...]
    p3_counts  = [0] * 3   # [base, +adx_range, +atr]

    for i in range(CANDLE_WARMUP, len(df)):
        sk   = _g(i,   "stoch_k")
        sd   = _g(i,   "stoch_d")
        sk1  = _g(i-1, "stoch_k")
        sd1  = _g(i-1, "stoch_d")
        sk2  = _g(i-2, "stoch_k")
        sd2  = _g(i-2, "stoch_d")
        adx  = _g(i, "adx")
        rsi  = _g(i, "rsi_short")
        atr  = _g(i, "atr_14")
        cls  = _g(i, "close")
        opn  = _g(i, "open")
        slp  = _g(i, "bb_mid_slope")

        # ── P2 ──
        cross = (
            i >= 2
            and not any(math.isnan(v) for v in [sk2, sd2, sk1, sd1, sk, sd, cls, opn])
            and sk2 < sd2 and sk1 < sd1 and sk > sd
            and (sk - sd) > p2_gap_min
            and cls >= opn
        )
        if cross:
            p2_counts[0] += 1
            if sk >= p2_k_min:
                p2_counts[1] += 1
                if not math.isnan(adx) and adx >= p2_adx_min:
                    p2_counts[2] += 1
                    if not math.isnan(rsi) and rsi >= p2_rsi_min:
                        p2_counts[3] += 1
                        if not math.isnan(atr) and p2_atr_min <= atr <= p2_atr_max:
                            p2_counts[4] += 1
                            if not (p2_adx_excl_min <= adx < p2_adx_excl_max):
                                p2_counts[5] += 1

        # ── P23 ──
        dead = (
            i >= 2
            and not any(math.isnan(v) for v in [sk2, sd2, sk1, sd1, sk, sd, cls, opn, slp])
            and sk2 > sd2 and sk1 > sd1 and sk < sd
            and (sd - sk) > 0.3
            and cls <= opn
            and slp < p23_slope_max
        )
        if dead:
            p23_counts[0] += 1
            if not math.isnan(adx) and p23_adx_min <= adx < p23_adx_max:
                p23_counts[1] += 1
                if not math.isnan(atr) and atr >= p23_atr_min:
                    p23_counts[2] += 1

        # ── P3 ──
        golden = (
            i >= 2
            and not any(math.isnan(v) for v in [sk2, sd2, sk1, sd1, sk, sd, cls, opn, slp])
            and sk2 < sd2 and sk1 < sd1 and sk > sd
            and (sk - sd) > 0.3
            and cls >= opn
            and slp > p3_slope_min
        )
        if golden:
            p3_counts[0] += 1
            if not math.isnan(adx) and p3_adx_min <= adx < p3_adx_max:
                p3_counts[1] += 1
                if not math.isnan(atr) and atr >= p3_atr_min:
                    p3_counts[2] += 1

    def _line(label, n, prev):
        drop = f"  落:{prev-n}" if prev is not None else ""
        return f"    {label:<42} {n:5}件  ({n/n_days:.1f}/day){drop}"

    print(f"\n{'='*60}")
    print(f"  [シグナルファネル]  期間: {n_days:.0f}日  全バー: {n_bars}")
    print(f"{'='*60}")

    print(f"\n  P2-LONG:")
    labels = [
        f"stoch_cross (gap>{p2_gap_min}, close>=open)",
        f"+ stoch_k >= {p2_k_min:.0f}",
        f"+ ADX >= {p2_adx_min:.0f}",
        f"+ RSI >= {p2_rsi_min:.0f}",
        f"+ ATR [{p2_atr_min:.0f}, {p2_atr_max:.0f}]",
        f"+ ADX excl [{p2_adx_excl_min:.0f}, {p2_adx_excl_max:.0f})",
    ]
    for j, (lbl, cnt) in enumerate(zip(labels, p2_counts)):
        prev = p2_counts[j-1] if j > 0 else None
        print(_line(lbl, cnt, prev))

    print(f"\n  P23-SHORT:")
    p23_labels = [
        f"stoch_dead (gap>0.3, close<=open, slope<{p23_slope_max:.0f})",
        f"+ ADX [{p23_adx_min:.0f}, {p23_adx_max:.0f})",
        f"+ ATR >= {p23_atr_min:.0f}",
    ]
    for j, (lbl, cnt) in enumerate(zip(p23_labels, p23_counts)):
        prev = p23_counts[j-1] if j > 0 else None
        print(_line(lbl, cnt, prev))

    print(f"\n  P3-LONG:")
    p3_labels = [
        f"stoch_golden (gap>0.3, close>=open, slope>{p3_slope_min:.0f})",
        f"+ ADX [{p3_adx_min:.0f}, {p3_adx_max:.0f})",
        f"+ ATR >= {p3_atr_min:.0f}",
    ]
    for j, (lbl, cnt) in enumerate(zip(p3_labels, p3_counts)):
        prev = p3_counts[j-1] if j > 0 else None
        print(_line(lbl, cnt, prev))

    print(f"\n{'='*60}\n")


def main(csv_path: str, regime_sw: bool = False) -> None:
    params = _load_params()
    mode = "【レジーム切り替えON】" if regime_sw else "【固定パラメータ】"
    print(f"[replay_csv] {mode} loaded from {csv_path}")
    preloaded = preload(csv_path, params)

    regime_map_built: Dict = {}
    regime_days: Dict[str, int] = {}
    if regime_sw:
        from collections import Counter
        regime_map_built = _build_regime_map(csv_path)
        regime_days = dict(Counter(v for v in regime_map_built.values() if v != "unknown"))

    trades = run(csv_path, params, _preloaded=preloaded, regime_switch=regime_sw,
                 _regime_map_in=regime_map_built)
    _write_results(csv_path, trades)
    _print_summary(trades, regime_switch=regime_sw, regime_days=regime_days)
    _signal_funnel(preloaded[0], params)


if __name__ == "__main__":
    if "--summary" in sys.argv:
        idx = sys.argv.index("--summary")
        results_path = sys.argv[idx + 1]
        df_r = pd.read_csv(results_path)
        trades_from_csv = df_r.to_dict("records")
        has_regime = "regime" in df_r.columns and df_r["regime"].notna().any() and (df_r["regime"] != "").any()
        # regime_days をトレードデータ内のユニーク日付から推定（--summaryモード用）
        rdays_est: Dict[str, int] = {}
        if has_regime and "entry_time" in df_r.columns:
            df_r["_date"] = df_r["entry_time"].str[:10]
            for _rg in df_r["regime"].dropna().unique():
                if _rg:
                    rdays_est[str(_rg)] = int(df_r[df_r["regime"] == _rg]["_date"].nunique())
        _print_summary(trades_from_csv, regime_switch=has_regime, regime_days=rdays_est)
        sys.exit(0)

    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} /path/to/BTCUSDT-5m-*.csv [--regime]")
        print(f"       {sys.argv[0]} --summary results/replay_*.csv")
        sys.exit(1)
    main(sys.argv[1], regime_sw="--regime" in sys.argv)
