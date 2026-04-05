from __future__ import annotations
# ============================================================
#  SAFETY GUARD — DO NOT MODIFY WITHOUT USER APPROVAL
ALLOW_LIVE_ORDERS = True
# ============================================================
"""run_once_v9.py — V9 実行エンジン（1回実行型）
ALLOW_LIVE_ORDERS=False → DRY_RUN（発注スキップ）
ALLOW_LIVE_ORDERS=True  → 実発注（ユーザーのみ変更可）
"""
import csv, json, math, os, sys, time
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from bitget.consts import GET, POST
from runner.bitget_adapter import BitgetAdapter, load_keys, q_down, q_up, fmt_price_1dp
from runner.io_json import read_json, write_json, state_path
from strategies.cat_v9_decider import decide as v9_decide, preprocess

# ---- 定数 ----
SYMBOL           = "BTCUSDT"
PRODUCT_TYPE     = "USDT-FUTURES"
MARGIN_COIN      = "USDT"
MARGIN_MODE      = "isolated"
CANDLE_LIMIT     = 200
PENDING_TTL_BARS = 3
PRICE_TICK       = Decimal("0.1")

# ---- パス ----
_KEYS_PATH     = _ROOT / "config" / "bitget_keys.json"
_PARAMS_PATH   = _ROOT / "config" / "cat_params_v9.json"
_TEST_INJECTION = bool(os.environ.get("CAT_TEST_INJECTION"))
# per-side state files
_OPEN_POS_LONG  = state_path("test_injection_position_long.json"  if _TEST_INJECTION else "open_position_long.json")
_OPEN_POS_SHORT = state_path("test_injection_position_short.json" if _TEST_INJECTION else "open_position_short.json")
_PENDING_LONG   = state_path("pending_entry_long.json")
_PENDING_SHORT  = state_path("pending_entry_short.json")
_OVERRIDE_PATH  = state_path("decision_override.json")
_LOG_PATH       = _ROOT / "logs" / "run_once_v9.jsonl"
_FAIL_COUNT_PATH = state_path("api_failure_count.json")
API_FAILURE_LIMIT = 3  # S-9: 連続API失敗でSTOP


def _opp(side: str) -> Path:
    """open_position path for side"""
    return _OPEN_POS_LONG if side.upper() == "LONG" else _OPEN_POS_SHORT


def _pp(side: str) -> Path:
    """pending path for side"""
    return _PENDING_LONG if side.upper() == "LONG" else _PENDING_SHORT


# ---- ライブログ（paper_trading=False 時のみ書き出し） ----
_LIVE_MODE: bool = False
_JST = timezone(timedelta(hours=9))
_LIVE_DECISION_LOG = _ROOT / "logs" / "live_decision.log"
_LIVE_TRADES_CSV   = _ROOT / "logs" / "live_trades.csv"
_DECISION_LOG_EVENTS = {
    "DECISION", "ENTRY_SEND", "ENTRY_CONFIRMED",
    "EXIT_TRIGGERED", "EXIT_EXTERNAL", "CLOSE_VERIFY", "EXIT_COMPLETE", "STOP",
}

# ---- 必須パラメータキー（H-2: Fail-fast） ----
_REQUIRED_KEYS = [
    "LONG_POSITION_SIZE_BTC", "SHORT_POSITION_SIZE_BTC",
    "LONG_TP_PCT", "SHORT_TP_PCT", "LONG_SL_PCT", "SHORT_SL_PCT",
    "LONG_MAX_ADDS", "SHORT_MAX_ADDS",
    "LONG_TIME_EXIT_MIN", "SHORT_TIME_EXIT_MIN",
    "MAX_ADDS_BY_PRIORITY",
    "FEE_RATE_MAKER", "FEE_MARGIN",
    "TP_FEE_FLOOR_ENABLE", "TP_ADX_BOOST_ENABLE",
    "ADX_THRESH", "TP_ADX_RANGE", "TP_ADX_FACTOR",
    "TP_PCT_CLAMP_ENABLE", "TP_PCT_SCALE", "TP_PCT_SCALE_HIGH", "ADX_TP_THRESH_HIGH",
    "STAG_MIN_M", "STAG_MFE_USD",
]


# ==============================================================
# ログ
# ==============================================================
def _log(event: str, **kw) -> None:
    _ev = f"[TEST_INJECTION]{event}" if _TEST_INJECTION else event
    rec = {"ts": int(time.time() * 1000), "event": _ev, **kw}
    line = json.dumps(rec, ensure_ascii=False, default=str)
    _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line)
    if _LIVE_MODE and event in _DECISION_LOG_EVENTS and not _TEST_INJECTION:
        with open(_LIVE_DECISION_LOG, "a", encoding="utf-8") as _df:
            _df.write(line + "\n")


_CSV_HEADER = [
    "datetime_jst", "entry_time_jst", "holding_minutes",
    "side", "priority", "size_btc", "add_count",
    "entry_price_avg", "exit_price_approx", "exit_reason",
    "gross_usd_approx", "fee_usd_approx", "net_usd_approx",
]


def _append_trade_csv(open_pos: dict, exit_price: float, exit_reason: str) -> None:
    """1トレード1行の集計用CSVに追記（live時のみ）。近似値。秘密情報は出力しない。"""
    if not _LIVE_MODE or _TEST_INJECTION:
        return
    try:
        side        = open_pos.get("side", "")
        priority    = open_pos.get("entry_priority", "")
        size_btc    = float(open_pos.get("size_btc", 0))
        add_count   = int(open_pos.get("add_count", 1))
        entry_price = float(open_pos.get("entry_price", 0))
        entry_ms    = int(open_pos.get("entry_time", 0))
        now_jst     = datetime.now(_JST).strftime("%Y-%m-%dT%H:%M")
        entry_jst   = (datetime.fromtimestamp(entry_ms / 1000, tz=_JST).strftime("%Y-%m-%dT%H:%M")
                       if entry_ms else "")
        hold_min    = round((time.time() * 1000 - entry_ms) / 60_000, 1) if entry_ms else 0

        if side == "LONG":
            gross = (exit_price - entry_price) * size_btc
        else:
            gross = (entry_price - exit_price) * size_btc

        maker = float(open_pos.get("fee_rate_maker", 0.00014))
        fee   = size_btc * exit_price * maker * 2
        net   = gross - fee

        _LIVE_TRADES_CSV.parent.mkdir(parents=True, exist_ok=True)
        write_header = not _LIVE_TRADES_CSV.exists()
        with open(_LIVE_TRADES_CSV, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=_CSV_HEADER)
            if write_header:
                w.writeheader()
            w.writerow({
                "datetime_jst": now_jst, "entry_time_jst": entry_jst,
                "holding_minutes": hold_min,
                "side": side, "priority": priority,
                "size_btc": size_btc, "add_count": add_count,
                "entry_price_avg": round(entry_price, 2),
                "exit_price_approx": round(exit_price, 2),
                "exit_reason": exit_reason,
                "gross_usd_approx": round(gross, 4),
                "fee_usd_approx": round(fee, 4),
                "net_usd_approx": round(net, 4),
            })
    except Exception as e:
        _log("TRADE_CSV_ERROR", error=str(e))


# ==============================================================
# パラメータ
# ==============================================================
def _load_params() -> Dict[str, Any]:
    raw = read_json(_PARAMS_PATH)
    missing = [k for k in _REQUIRED_KEYS if k not in raw]
    if missing:
        raise ValueError(f"params missing keys: {missing}")
    for k, v in raw.items():
        if isinstance(v, str):
            try:
                raw[k] = int(v) if "." not in v else float(v)
            except ValueError:
                pass
    _log("PARAMS_LOADED", count=len(raw))
    return raw


# ==============================================================
# TP 計算
# ==============================================================
def _calc_tp_pct(side: str, adx: float, params: Dict[str, Any], priority: int = -1) -> float:
    pri_key  = f"P{priority}_TP_PCT" if priority > 0 else None
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
    _log("TPSL_CTX", side=side, adx=adx, effective_tp_pct=round(base, 6),
         fee_applied=int(params.get("TP_FEE_FLOOR_ENABLE", 0)),
         boost_applied=int(params.get("TP_ADX_BOOST_ENABLE", 0)))
    return base


# ==============================================================
# API 失敗カウンタ
# ==============================================================
def _update_fail_count(api_ok: dict) -> None:
    try:
        all_ok = all(api_ok.values())
        if all_ok:
            if _FAIL_COUNT_PATH.exists():
                _FAIL_COUNT_PATH.unlink()
        else:
            prev = 0
            if _FAIL_COUNT_PATH.exists():
                prev = int(read_json(_FAIL_COUNT_PATH).get("count", 0))
            write_json(_FAIL_COUNT_PATH, {"count": prev + 1})
    except Exception:
        pass


# ==============================================================
# 市場健全性
# ==============================================================
def _market_sanity(adapter: BitgetAdapter) -> float:
    r = adapter.get_symbol_price(PRODUCT_TYPE, SYMBOL)
    data = r.get("data") or {}
    if isinstance(data, list):
        data = data[0] if data else {}
    mark_p = float(data.get("markPrice") or data.get("mark_price") or 0)
    last_p = float(data.get("price") or data.get("lastPr") or 0)
    if mark_p <= 0 or last_p <= 0:
        raise RuntimeError(f"sanity_fail: zero price mark={mark_p} last={last_p}")
    spread = abs(mark_p - last_p) / mark_p
    if spread > 0.03:
        raise RuntimeError(f"sanity_fail: spread {spread:.4%}>3%")
    _log("MARKET_SANITY_OK", mark_price=mark_p, last_price=last_p, spread_pct=round(spread, 6))
    return mark_p


# ==============================================================
# API ヘルパー（ALLOW_LIVE_ORDERS ガード付き）
# ==============================================================
def _place_limit_order(adapter: BitgetAdapter, *, side: str, size: str,
                       price: str, client_oid: str) -> str:
    req = {
        "symbol": SYMBOL, "productType": PRODUCT_TYPE,
        "marginMode": MARGIN_MODE, "marginCoin": MARGIN_COIN,
        "size": size,
        "side": "buy" if side == "LONG" else "sell",
        "tradeSide": "open",
        "orderType": "market",
        "clientOid": client_oid,
    }
    _log("ENTRY_SEND", side=side, close_price=price, size=size, client_oid=client_oid)
    if not ALLOW_LIVE_ORDERS:
        _log("DRY_RUN_SKIP", action="place_limit_order")
        return f"DRY_{client_oid}"
    r = adapter.api._request_with_params(POST, "/api/v2/mix/order/place-order", req)
    if r.get("code") != "00000":
        raise RuntimeError(f"place_limit_order failed: {r}")
    return str((r.get("data") or {}).get("orderId", client_oid))


def _cancel_order(adapter: BitgetAdapter, order_id: str) -> None:
    if not ALLOW_LIVE_ORDERS:
        _log("DRY_RUN_SKIP", action="cancel_order", order_id=order_id)
        return
    r = adapter.api._request_with_params(POST, "/api/v2/mix/order/cancel-order",
        {"symbol": SYMBOL, "productType": PRODUCT_TYPE, "orderId": order_id})
    if r.get("code") != "00000":
        raise RuntimeError(f"cancel_order failed: {r}")


def _cancel_plan_order(adapter: BitgetAdapter, order_id: str, event: str = "TP_CANCELLED") -> None:
    """TP/SL plan注文のキャンセル（失敗は WARN 止まり、例外にしない）"""
    if not ALLOW_LIVE_ORDERS:
        _log("DRY_RUN_SKIP", action="cancel_plan_order", order_id=order_id)
        return
    r = adapter.api._request_with_params(POST, "/api/v2/mix/order/cancel-plan-order",
        {"symbol": SYMBOL, "productType": PRODUCT_TYPE, "orderId": order_id})
    if r.get("code") != "00000":
        _log("TP_CANCEL_WARN", order_id=order_id, response=r)
    else:
        _log(event, order_id=order_id)


def _get_order_state(adapter: BitgetAdapter, order_id: str) -> Dict[str, Any]:
    """DRY_RUN 時は synthetic state を返す"""
    if not ALLOW_LIVE_ORDERS:
        return {"state": "live", "priceAvg": "0", "baseVolume": "0"}
    r = adapter.api._request_with_params(GET, "/api/v2/mix/order/detail",
        {"symbol": SYMBOL, "productType": PRODUCT_TYPE, "orderId": order_id})
    if r.get("code") != "00000":
        raise RuntimeError(f"get_order_detail failed: {r}")
    data = r.get("data") or {}
    return data[0] if isinstance(data, list) and data else data


def _place_tp(adapter: BitgetAdapter, *, side: str,
              entry_price: Decimal, tp_pct: float,
              position_size: Optional[float] = None,
              mark_price: Optional[float] = None) -> tuple:
    if side == "LONG":
        tp = q_down(entry_price * (Decimal("1") + Decimal(str(tp_pct))), PRICE_TICK)
        hold_side = "long"
        if not tp > entry_price:
            raise RuntimeError(f"LONG tp {tp} <= entry {entry_price}")
        if mark_price and tp <= Decimal(str(mark_price)):
            tp = q_up(Decimal(str(mark_price)) + PRICE_TICK, PRICE_TICK)
            _log("TP_ADJUSTED_TO_MARK", side=side, adjusted_tp=float(tp), mark_price=mark_price)
    else:
        tp = q_up(entry_price * (Decimal("1") - Decimal(str(tp_pct))), PRICE_TICK)
        hold_side = "short"
        if not tp < entry_price:
            raise RuntimeError(f"SHORT tp {tp} >= entry {entry_price}")
        if mark_price and tp >= Decimal(str(mark_price)):
            tp = q_down(Decimal(str(mark_price)) - PRICE_TICK, PRICE_TICK)
            _log("TP_ADJUSTED_TO_MARK", side=side, adjusted_tp=float(tp), mark_price=mark_price)
    req = {
        "marginCoin": MARGIN_COIN, "productType": PRODUCT_TYPE, "symbol": SYMBOL,
        "holdSide": hold_side, "planType": "pos_profit", "triggerType": "mark_price",
        "triggerPrice": fmt_price_1dp(tp), "executePrice": fmt_price_1dp(tp),
    }
    _log("TP_LIMIT_SEND", side=side,
         plan_type="pos_profit", trigger_type="mark_price",
         hold_side=hold_side,
         trigger_price=fmt_price_1dp(tp),
         execute_price=fmt_price_1dp(tp),
         position_size=position_size)
    if not ALLOW_LIVE_ORDERS:
        _log("DRY_RUN_SKIP", action="place_tp", tp_price=float(tp))
        return tp, None
    r = adapter.api._request_with_params(POST, "/api/v2/mix/order/place-tpsl-order", req)
    if r.get("code") != "00000":
        raise RuntimeError(f"place_tp failed: {r}")
    tp_order_id = (r.get("data") or {}).get("orderId")
    _log("TP_SET", side=side, tp_price=float(tp), entry=float(entry_price), tp_order_id=tp_order_id)
    return tp, tp_order_id


def _place_sl(adapter: BitgetAdapter, *, side: str,
              entry_price: Decimal, sl_pct: float) -> tuple:
    if side == "LONG":
        sl = q_down(entry_price * (Decimal("1") - Decimal(str(sl_pct))), PRICE_TICK)
        hold_side = "long"
        if not sl < entry_price:
            raise RuntimeError(f"LONG sl {sl} >= entry {entry_price}")
    else:
        sl = q_up(entry_price * (Decimal("1") + Decimal(str(sl_pct))), PRICE_TICK)
        hold_side = "short"
        if not sl > entry_price:
            raise RuntimeError(f"SHORT sl {sl} <= entry {entry_price}")
    req = {
        "marginCoin": MARGIN_COIN, "productType": PRODUCT_TYPE, "symbol": SYMBOL,
        "holdSide": hold_side, "planType": "pos_loss", "triggerType": "mark_price",
        "triggerPrice": fmt_price_1dp(sl), "executePrice": fmt_price_1dp(sl),
    }
    if not ALLOW_LIVE_ORDERS:
        _log("DRY_RUN_SKIP", action="place_sl", sl_price=float(sl))
        return sl, None
    r = adapter.api._request_with_params(POST, "/api/v2/mix/order/place-tpsl-order", req)
    if r.get("code") != "00000":
        if r.get("code") == "40917":
            raise RuntimeError(f"SL_PRICE_INVALID:40917: {r}")
        raise RuntimeError(f"place_sl failed: {r}")
    sl_order_id = (r.get("data") or {}).get("orderId")
    _log("SL_SET", side=side, sl_price=float(sl), entry=float(entry_price),
         sl_order_id=sl_order_id)
    return sl, sl_order_id


def _do_close(adapter: BitgetAdapter, *, p_side: str, size: str, client_oid: str) -> None:
    _log("CLOSE_SEND", side=p_side, size=size, client_oid=client_oid)
    if not ALLOW_LIVE_ORDERS:
        _log("DRY_RUN_SKIP", action="close_market_order")
        return
    r = adapter.close_market_order(
        symbol=SYMBOL, product_type=PRODUCT_TYPE,
        margin_mode=MARGIN_MODE, margin_coin=MARGIN_COIN,
        size=size,
        side="sell" if p_side == "LONG" else "buy",
        hold_side="long" if p_side == "LONG" else "short",
        client_oid=client_oid,
    )
    if r.get("code") != "00000":
        raise RuntimeError(f"close_market_order failed: {r}")


# ==============================================================
# Exit 判定（優先順位順）
# ==============================================================
def _check_exits(pos: Dict, mark_price: float, df, params: Dict) -> Optional[str]:
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

    # 1. BREAKOUT_CUT (P22 SHORT, add==3, bb_width+rsi条件)
    if side == "SHORT" and priority == 22 and add_count == 3:
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

    # 5b. MAE_CUT (P2 LONG, add≥4, hold≥300min, mark_price <= entry - 50/size)
    if side == "LONG" and priority == 2 and add_count >= 4 and hold_min >= 300:
        _mae_cap_price_long = entry_p - (50.0 / size_btc)
        if mark_price <= _mae_cap_price_long:
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
    # 6a. PROFIT_LOCK V2 (P23 SHORT, add_count不問, ARM=$15, LOCK=$5)
    if side == "SHORT" and priority == 23 and int(params.get("P23_SHORT_PROFIT_LOCK_ENABLE", 1)):
        _arm_usd_p23 = float(params.get("P23_SHORT_PROFIT_LOCK_ARM_USD", 15.0))
        _lock_usd_p23 = float(params.get("P23_SHORT_PROFIT_LOCK_USD", 5.0))
        if mfe_usd >= _arm_usd_p23:
            _lock_price_p23 = entry_p - (_lock_usd_p23 / size_btc)
            if mark_price >= _lock_price_p23:
                return "PROFIT_LOCK"
    # 6b. PROFIT_LOCK (P22_SHORT, add==5, lock_usd=10固定)
    if side == "SHORT" and priority == 22 and add_count == 5:
        _lock_usd_p22 = 10.0
        _lock_price_p22 = entry_p - (_lock_usd_p22 / size_btc)
        if mark_price <= _lock_price_p22:
            return "PROFIT_LOCK"

    # 7. STAGNATION_CUT
    if priority == 4 and int(params.get("P4_STAGNATION_WIDE_ENABLE", 0)):
        if (hold_min >= float(params.get("P4_STAGNATION_WIDE_MIN", 20.0))
                and mfe_usd <= float(params.get("P4_STAGNATION_WIDE_MAX_MFE", 1.0))):
            return "STAGNATION_CUT"
    elif hold_min >= float(params.get("STAG_MIN_M", 30.0)) and mfe_usd <= float(params.get("STAG_MFE_USD", 1.0)):
        return "STAGNATION_CUT"

    # 8b. TIME_EXIT
    base_t = float(params.get("P2_TIME_EXIT_MIN" if priority == 2 else
                              f"{side}_TIME_EXIT_MIN", 150 if side == "LONG" else 480))
    down_f = float(params.get(f"{side}_TIME_EXIT_DOWN_FACTOR", 0.75))
    if hold_min >= base_t * (down_f if unreal < 0 else 1.0):
        return "TIME_EXIT"

    return None


# ==============================================================
# 旧 single-file state → per-side file 移行（1回限り）
# ==============================================================
def _migrate_legacy_state_files() -> None:
    for old_name, new_fn in (
        ("open_position.json",  _opp),
        ("pending_entry.json",  _pp),
    ):
        old_path = state_path(old_name)
        if not old_path.exists():
            continue
        try:
            data = read_json(old_path)
            side = str(data.get("side", "LONG")).upper()
            new_path = new_fn(side)
            if not new_path.exists():
                write_json(new_path, data)
                _log("STATE_MIGRATED", from_file=old_name, to_file=new_path.name, side=side)
            old_path.unlink(missing_ok=True)
        except Exception as e:
            _log("STATE_MIGRATION_ERROR", file=old_name, error=str(e))


# ==============================================================
# Startup Reconciliation（サイド別）
# ==============================================================
def _reconcile_side(
    adapter: BitgetAdapter,
    open_pos: Optional[dict],
    pending: Optional[dict],
    side: str,
    _api_ok: dict,
) -> Tuple[bool, Optional[dict], Optional[dict]]:
    """startup reconciliation for one side.
    Returns (ok, new_open_pos, new_pending).
    ok=False → STOP済み。caller は即 return する。
    """
    hold_side = side.lower()
    try:
        _live_pos = adapter.get_position_by_side(
            product_type=PRODUCT_TYPE, margin_coin=MARGIN_COIN,
            symbol=SYMBOL, hold_side=hold_side)
        _exchange_has_pos = _live_pos is not None and float(_live_pos.get("total", 0)) > 0
        _api_ok["pos"] = True
    except Exception as e:
        _log("STOP", reason=f"startup_reconciliation_error: side={side} {e}")
        _update_fail_count(_api_ok)
        return False, open_pos, pending

    if open_pos is None and pending is None and _exchange_has_pos:
        _log("STOP", reason=(
            f"startup_reconciliation_failed: exchange has {side} position "
            f"(size={_live_pos.get('total')}) "
            f"but open_position_{hold_side}.json is missing"
        ))
        return False, open_pos, pending

    if open_pos is not None and not _exchange_has_pos:
        if open_pos.get("active_close_sent"):
            _exit_r = open_pos["active_close_sent"]
            _log("EXIT_EXTERNAL", reason=f"ACTIVE_CLOSE_COMPLETE:{_exit_r}",
                 side=open_pos.get("side"), priority=open_pos.get("entry_priority"),
                 source="startup_reconciliation")
            _append_trade_csv(open_pos, 0.0, _exit_r)
            _opp(side).unlink(missing_ok=True)
            return True, None, None
        _tp_oid = open_pos.get("tp_order_id")
        _sl_oid = open_pos.get("sl_order_id")
        _exit_reason = None
        try:
            _plan_hist = adapter.get_plan_order_history(PRODUCT_TYPE, SYMBOL)
            _sl_execute_oid = None
            for _ph in _plan_hist:
                if _ph.get("planStatus") != "executed":
                    continue
                _ph_oid = _ph.get("orderId")
                if _tp_oid and _ph_oid == _tp_oid:
                    _exit_reason = "TP_FILLED"
                    break
                if _sl_oid and _ph_oid == _sl_oid:
                    _sl_execute_oid = _ph.get("executeOrderId") or None
                    if not _sl_execute_oid:
                        _log("SL_EXECUTE_OID_MISSING", sl_oid=_sl_oid)
            if _exit_reason is None and _sl_execute_oid:
                _fills = adapter.get_fill_history(PRODUCT_TYPE, SYMBOL, order_id=_sl_execute_oid)
                for _f in _fills:
                    if _f.get("orderId") == _sl_execute_oid and _f.get("tradeSide") == "close":
                        _exit_reason = "SL_FILLED"
                        break
        except Exception as _e:
            _log("RECONCILIATION_HISTORY_ERROR", error=str(_e))

        if _exit_reason:
            _log("EXIT_EXTERNAL", reason=_exit_reason, side=open_pos.get("side"),
                 priority=open_pos.get("entry_priority"),
                 tp=open_pos.get("tp"), sl=open_pos.get("sl"),
                 source="startup_reconciliation")
            _ep_recon = (float(open_pos.get("tp", 0)) if _exit_reason == "TP_FILLED"
                         else float(open_pos.get("sl", 0)) if _exit_reason == "SL_FILLED"
                         else 0.0)
            _append_trade_csv(open_pos, _ep_recon, _exit_reason)
            _opp(side).unlink(missing_ok=True)
            if pending is not None:
                try:
                    _cancel_order(adapter, pending["order_id"])
                    _log("PENDING_CANCELLED_ON_EXIT", order_id=pending["order_id"],
                         reason="exit_external_startup_recon")
                except Exception as _ce:
                    _log("PENDING_CANCEL_ERROR", order_id=pending.get("order_id"), error=str(_ce))
                finally:
                    _pp(side).unlink(missing_ok=True)
            return True, None, None  # EXIT_EXTERNAL 確定。他サイドの処理を続ける

        _log("STOP", reason=(
            f"startup_reconciliation_failed: open_position_{hold_side}.json exists "
            f"(size={open_pos.get('size_btc')}) but exchange has no {side} position"
        ))
        return False, open_pos, pending

    return True, open_pos, pending


# ==============================================================
# S-5/S-6: TP/SL 実在確認（サイド別）
# ==============================================================
def _check_tp_sl_side(
    adapter: BitgetAdapter,
    open_pos: dict,
    side: str,
) -> Tuple[bool, Optional[dict]]:
    """S-5/S-6: TP/SL order check for one side.
    Returns (ok, new_open_pos).
    ok=False → STOP済み。caller は即 return する。
    new_open_pos=None → EMERGENCY_CLOSE 実行済み。他サイドの処理を続ける。
    """
    tp_oid = open_pos.get("tp_order_id")
    if not tp_oid:
        _p_side = open_pos.get("side", side).lower()
        _size   = str(open_pos.get("size_btc", 0))
        _log("EMERGENCY_CLOSE", reason="tp_order_id_missing", side=_p_side, size=_size)
        try:
            _do_close(adapter, p_side=_p_side, size=_size,
                      client_oid=f"emergency_{int(time.time()*1000)}")
        except Exception as _ec:
            _log("STOP", reason=f"emergency_close_failed: {_ec}")
            return False, open_pos
        _opp(side).unlink(missing_ok=True)
        _log("EXIT_COMPLETE", exit_reason="EMERGENCY_CLOSE_TP_MISSING")
        return True, None

    try:
        r = adapter.api.ordersPlanPending({
            "symbol": SYMBOL, "productType": PRODUCT_TYPE,
            "planType": "profit_loss",
        })
        data = r.get("data") or {}
        orders = (data.get("entrustedList")
                  or data.get("orderList")
                  or (data if isinstance(data, list) else []))
        ids = {str(o.get("orderId", "")) for o in orders if isinstance(o, dict)}
        if str(tp_oid) not in ids:
            try:
                live_chk = adapter.get_position_by_side(
                    product_type=PRODUCT_TYPE, margin_coin=MARGIN_COIN,
                    symbol=SYMBOL, hold_side=side.lower())
            except Exception as chk_e:
                _log("STOP", reason=f"tp_order_missing_pos_check_failed: {chk_e}")
                return False, open_pos
            if live_chk is not None and float(live_chk.get("total", 0)) > 0:
                _tp_exit_confirmed = False
                try:
                    _ph_list = adapter.get_plan_order_history(PRODUCT_TYPE, SYMBOL)
                    for _ph in _ph_list:
                        if (_ph.get("planStatus") == "executed"
                                and str(_ph.get("orderId", "")) == str(tp_oid)):
                            _tp_exit_confirmed = True
                            break
                except Exception as _phe:
                    _log("RECONCILIATION_HISTORY_ERROR", error=str(_phe))
                if _tp_exit_confirmed:
                    _log("EXIT_EXTERNAL", reason="TP_FILLED",
                         side=open_pos.get("side"),
                         priority=open_pos.get("entry_priority"),
                         tp=open_pos.get("tp"), sl=open_pos.get("sl"),
                         source="tp_order_missing_lag_recovery")
                    _append_trade_csv(open_pos, float(open_pos.get("tp", 0)), "TP_FILLED")
                    _opp(side).unlink(missing_ok=True)
                    return True, None
                _log("STOP", reason=f"tp_order_missing: tp_order_id={tp_oid} not in plan orders")
                return False, open_pos
            _log("TP_ORDER_MISSING_POS_GONE", tp_order_id=tp_oid)
            # → _run_exit_checks (S-7) へ進む
        else:
            _log("TP_ORDER_VERIFIED", tp_order_id=tp_oid)
            sl_oid_chk = open_pos.get("sl_order_id")
            if sl_oid_chk and str(sl_oid_chk) not in ids:
                _log("STOP", reason=f"sl_order_missing_pos_exists: sl_order_id={sl_oid_chk}")
                return False, open_pos
            if sl_oid_chk:
                _log("SL_ORDER_VERIFIED", sl_order_id=sl_oid_chk)
    except Exception as e:
        _log("STOP", reason=f"tp_order_verify_failed: {e}")
        return False, open_pos

    return True, open_pos


# ==============================================================
# 約定確認 → open_position + TP/SL
# ==============================================================
def _confirm_entry(adapter: BitgetAdapter, pending: Dict, open_pos: Optional[Dict],
                   detail: Dict, mark_price: float, params: Dict,
                   pos_path: Path) -> None:
    p_side    = str(pending["side"])
    p_pri     = int(pending.get("entry_priority", -1))
    adx_val   = float(pending.get("adx_at_entry", 0) or 0)
    size_btc  = float(pending.get("size", params[f"{p_side}_POSITION_SIZE_BTC"]))
    price_avg = float(detail.get("priceAvg") or 0) or mark_price
    filled_sz = float(detail.get("baseVolume") or 0) or size_btc

    tp_pct = _calc_tp_pct(p_side, adx_val, params, p_pri)

    if open_pos is None:
        # 初回 ENTRY
        tp, tp_order_id = _place_tp(adapter, side=p_side, entry_price=Decimal(str(price_avg)),
                                    tp_pct=tp_pct, position_size=filled_sz, mark_price=mark_price)
        write_json(pos_path, {
            "side": p_side, "entry_priority": p_pri,
            "entry_price": price_avg,
            "entry_time": str(int(time.time() * 1000)),
            "last_update_time": str(int(time.time() * 1000)),
            "add_count": 1, "size_btc": filled_sz,
            "tp": float(tp), "tp_pct": tp_pct, "tp_order_id": tp_order_id,
            "sl": None, "sl_order_id": None, "mfe_usd": 0.0, "pricePlace": 1,
        })
        _log("ENTRY_CONFIRMED", side=p_side, priority=p_pri,
             price=price_avg, size=filled_sz, tp=float(tp), tp_order_id=tp_order_id)
    else:
        # ADD ENTRY
        old_cnt = int(open_pos.get("add_count", 1))
        new_cnt = old_cnt + 1
        old_sz  = float(open_pos.get("size_btc", 0))
        old_p   = float(open_pos["entry_price"])
        new_sz  = old_sz + filled_sz
        new_avg = (old_p * old_sz + price_avg * filled_sz) / new_sz
        entry_dec = Decimal(str(new_avg))
        old_tp_order_id = open_pos.get("tp_order_id")
        if old_tp_order_id:
            _cancel_plan_order(adapter, old_tp_order_id)
        tp, tp_order_id = _place_tp(adapter, side=p_side, entry_price=entry_dec,
                                    tp_pct=tp_pct, position_size=new_sz, mark_price=mark_price)
        sl_val = None
        sl_order_id_new = None
        if new_cnt >= 2:
            old_sl_order_id = open_pos.get("sl_order_id")
            if old_sl_order_id:
                _cancel_plan_order(adapter, old_sl_order_id)
            sl, sl_order_id_new = _place_sl(adapter, side=p_side, entry_price=entry_dec,
                                            sl_pct=float(params[f"{p_side}_SL_PCT"]))
            sl_val = float(sl)
        open_pos.update({
            "entry_price": new_avg, "add_count": new_cnt, "size_btc": new_sz,
            "tp": float(tp), "tp_pct": tp_pct, "tp_order_id": tp_order_id, "sl": sl_val,
            "sl_order_id": sl_order_id_new,
            "last_update_time": str(int(time.time() * 1000)),
        })
        write_json(pos_path, open_pos)
        _log("ADD_CONFIRMED", side=p_side, add_count=new_cnt,
             avg_price=round(new_avg, 2), size=new_sz, tp=float(tp), sl=sl_val,
             sl_order_id=sl_order_id_new)


# ==============================================================
# Exit 実行
# ==============================================================
def _run_exit_checks(adapter: BitgetAdapter, open_pos: Dict, mark_price: float,
                     candles_raw: list, params: Dict, pos_path: Path) -> bool:
    """Exit を実行して True を返す。Exit なしなら False。"""
    p_side = open_pos["side"]
    try:
        live_pos = adapter.get_position_by_side(
            product_type=PRODUCT_TYPE, margin_coin=MARGIN_COIN,
            symbol=SYMBOL, hold_side=p_side.lower())
    except Exception as e:
        _log("STOP", reason=f"get_position_by_side_failed: side={p_side} {e}")
        return True

    if live_pos is None or float(live_pos.get("total", 0)) == 0:
        _sl   = open_pos.get("sl")
        _tp   = open_pos.get("tp")
        if _sl is None:
            ext_reason = "TP_FILLED"
        elif p_side == "LONG":
            if   _tp and mark_price >= float(_tp): ext_reason = "TP_FILLED"
            elif mark_price <= float(_sl):          ext_reason = "SL_FILLED"
            else:                                   ext_reason = "TP_OR_SL_HIT"
        else:  # SHORT
            if   _tp and mark_price <= float(_tp): ext_reason = "TP_FILLED"
            elif mark_price >= float(_sl):          ext_reason = "SL_FILLED"
            else:                                   ext_reason = "TP_OR_SL_HIT"
        _log("EXIT_EXTERNAL", reason=ext_reason, side=p_side,
             priority=open_pos.get("entry_priority"),
             mark_price=mark_price, tp=_tp, sl=_sl)
        _ep = (float(_tp) if ext_reason == "TP_FILLED" and _tp
               else float(_sl) if ext_reason == "SL_FILLED" and _sl
               else mark_price)
        _append_trade_csv(open_pos, _ep, ext_reason)
        pos_path.unlink(missing_ok=True)
        return True

    entry_p = float(open_pos["entry_price"])
    size_b  = float(open_pos.get("size_btc", params.get(f"{p_side}_POSITION_SIZE_BTC", 0.024)))
    unreal  = ((mark_price - entry_p) if p_side == "LONG" else (entry_p - mark_price)) * size_b
    old_mfe = float(open_pos.get("mfe_usd", 0.0))
    if unreal > old_mfe:
        open_pos["mfe_usd"] = unreal
        open_pos["last_update_time"] = str(int(time.time() * 1000))
        write_json(pos_path, open_pos)

    df = None
    try:
        rows = []
        for row in candles_raw:
            if isinstance(row, list) and len(row) >= 5:
                try:
                    rows.append({
                        "timestamp": pd.to_datetime(int(row[0]), unit="ms"),
                        "open": float(row[1]), "high": float(row[2]),
                        "low":  float(row[3]), "close": float(row[4]),
                        "volume": float(row[5]) if len(row) > 5 else 0.0,
                    })
                except Exception:
                    pass
        if rows:
            df = preprocess(
                pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True), params)
    except Exception as e:
        _log("PREPROCESS_WARN", error=str(e))

    exit_reason = _check_exits(open_pos, mark_price, df, params)
    if exit_reason is None:
        return False

    hold_min   = (int(time.time() * 1000) - int(open_pos["entry_time"])) / 60_000
    p_priority = int(open_pos.get("entry_priority", -1))
    p_add      = int(open_pos.get("add_count", 1))

    def _col_last(col: str):
        if df is None or col not in df.columns: return None
        v = df.at[len(df) - 1, col]
        try: return round(float(v), 4) if not math.isnan(float(v)) else None
        except Exception: return None

    exit_ctx: Dict = {"add_count": p_add}
    if exit_reason == "TIME_EXIT":
        base_t = float(params.get("P2_TIME_EXIT_MIN" if p_priority == 2 else
                                  f"{p_side}_TIME_EXIT_MIN", 150 if p_side == "LONG" else 480))
        down_f = float(params.get(f"{p_side}_TIME_EXIT_DOWN_FACTOR", 0.75))
        exit_ctx["effective_exit_min"] = round(base_t * (down_f if unreal < 0 else 1.0), 1)
    elif exit_reason == "STAGNATION_CUT":
        exit_ctx.update({"stag_min_m": params.get("STAG_MIN_M"),
                         "stag_mfe_usd": params.get("STAG_MFE_USD")})
    elif exit_reason == "PROFIT_LOCK":
        arm_k  = ("P22_SHORT_PROFIT_LOCK_ARM_USD" if (p_side == "SHORT" and p_priority == 22)
                  else "LONG_PROFIT_LOCK_ARM_USD")
        lock_k = ("P22_SHORT_PROFIT_LOCK_USD" if (p_side == "SHORT" and p_priority == 22)
                  else "LONG_PROFIT_LOCK_USD")
        exit_ctx.update({"arm_usd": params.get(arm_k), "lock_usd": params.get(lock_k)})
    elif exit_reason == "RSI_REVERSE_EXIT":
        exit_ctx.update({"rsi": _col_last("rsi_short"), "rsi_slope": _col_last("rsi_slope_short"),
                         "adx": _col_last("adx"), "rsi_thresh": params.get("SHORT_RSI_THRESH"),
                         "adx_max": params.get("SHORT_RSI_EXIT_ADX_MAX")})
    elif exit_reason == "BREAKOUT_CUT":
        exit_ctx.update({"bb_width": _col_last("bb_width"), "rsi": _col_last("rsi_short")})
    elif exit_reason == "MFE_STALE_CUT":
        exit_ctx.update({"mfe_profit_thresh": params.get("P22_SHORT_MFE_EXIT_PROFIT_USD"),
                         "mfe_gate": params.get("P22_SHORT_MFE_MAX_GATE_USD")})

    _log("EXIT_TRIGGERED", reason=exit_reason, side=p_side,
         priority=open_pos.get("entry_priority"),
         mark_price=mark_price, entry_price=entry_p,
         hold_min=round(hold_min, 1), mfe_usd=open_pos.get("mfe_usd", 0),
         unreal_usd=round(unreal, 4), exit_ctx=exit_ctx)

    # クローズ前再確認
    try:
        lp2 = adapter.get_position_by_side(
            product_type=PRODUCT_TYPE, margin_coin=MARGIN_COIN,
            symbol=SYMBOL, hold_side=p_side.lower())
        if lp2 is None or float(lp2.get("total", 0)) == 0:
            _log("NO_POSITION", reason="already_closed_before_close_send")
            pos_path.unlink(missing_ok=True)
            return True
        close_size = str(lp2.get("total", size_b))
    except Exception as e:
        _log("STOP", reason=f"pos_recheck_failed: {e}")
        return True

    client_oid = f"close_{exit_reason}_{int(time.time()*1000)}"
    try:
        _do_close(adapter, p_side=p_side, size=close_size, client_oid=client_oid)
    except Exception as e:
        _log("STOP", reason=f"close_failed: {e}", exit_reason=exit_reason)
        return True

    time.sleep(1.0)
    try:
        lp3 = adapter.get_position_by_side(
            product_type=PRODUCT_TYPE, margin_coin=MARGIN_COIN,
            symbol=SYMBOL, hold_side=p_side.lower())
        remaining = float((lp3 or {}).get("total", 0))
    except Exception:
        remaining = -1.0

    if remaining <= 0:
        tp_oid = open_pos.get("tp_order_id")
        if tp_oid:
            _cancel_plan_order(adapter, tp_oid)
        sl_oid = open_pos.get("sl_order_id")
        if sl_oid:
            _cancel_plan_order(adapter, sl_oid, event="SL_CANCELLED")
        _append_trade_csv(open_pos, mark_price, exit_reason)
        pos_path.unlink(missing_ok=True)
        _log("CLOSE_VERIFY", status="complete", reason=exit_reason)
    else:
        _log("EXIT_PENDING", remaining=remaining, reason=exit_reason)
        open_pos["active_close_sent"] = exit_reason
        write_json(pos_path, open_pos)
    return True


# ==============================================================
# メインフロー
# ==============================================================
def run() -> None:
    _log("RUN_START", allow_live_orders=ALLOW_LIVE_ORDERS)

    # S-9: 連続API失敗チェック
    _api_ok = {"market": False, "candle": False, "pos": not ALLOW_LIVE_ORDERS}
    _fc = 0
    try:
        if _FAIL_COUNT_PATH.exists():
            _fc = int(read_json(_FAIL_COUNT_PATH).get("count", 0))
    except Exception:
        pass
    if _fc >= API_FAILURE_LIMIT:
        _log("STOP", reason=f"consecutive_api_failures: count={_fc} limit={API_FAILURE_LIMIT}")
        return

    # 1. 設定ロード
    try:
        keys_data     = read_json(_KEYS_PATH)
        paper_trading = bool(keys_data.get("paper_trading", True))
        keys          = load_keys(_KEYS_PATH)
        params        = _load_params()
    except Exception as e:
        _log("STOP", reason=f"config_load_failed: {e}")
        return
    adapter = BitgetAdapter(keys, paper_trading=paper_trading)
    global _LIVE_MODE
    _LIVE_MODE = not paper_trading
    _log("CONFIG_LOADED", paper_trading=paper_trading)

    # 2. 旧 single-file state → per-side file 移行
    _migrate_legacy_state_files()

    # 3. state ロード（両サイド）
    open_pos: Dict[str, Optional[dict]] = {"LONG": None, "SHORT": None}
    pending:  Dict[str, Optional[dict]] = {"LONG": None, "SHORT": None}
    for _s in ("LONG", "SHORT"):
        try:
            if _opp(_s).exists():
                open_pos[_s] = read_json(_opp(_s))
        except Exception as e:
            _log("OPEN_POS_READ_ERROR", side=_s, error=str(e))
        try:
            if _pp(_s).exists():
                pending[_s] = read_json(_pp(_s))
        except Exception as e:
            _log("PENDING_READ_ERROR", side=_s, error=str(e))

    # STARTUP RECONCILIATION（両サイド）
    if ALLOW_LIVE_ORDERS:
        for _s in ("LONG", "SHORT"):
            _ok, open_pos[_s], pending[_s] = _reconcile_side(
                adapter, open_pos[_s], pending[_s], _s, _api_ok)
            if not _ok:
                return

    # S-5/S-6: TP/SL 実在確認（両サイド）
    if ALLOW_LIVE_ORDERS:
        for _s in ("LONG", "SHORT"):
            if open_pos[_s] is not None:
                _ok, open_pos[_s] = _check_tp_sl_side(adapter, open_pos[_s], _s)
                if not _ok:
                    return

    # H-0: state 宣言
    _log("STATE_DECLARED",
         mode="live" if ALLOW_LIVE_ORDERS else "dry_run",
         paper_trading=paper_trading,
         pending_long=pending["LONG"] is not None,
         pending_short=pending["SHORT"] is not None,
         open_long=open_pos["LONG"] is not None,
         open_short=open_pos["SHORT"] is not None)

    override = None
    if _OVERRIDE_PATH.exists():
        try:
            override = read_json(_OVERRIDE_PATH)
        except Exception:
            pass
    _log("OVERRIDE_STATUS", active=override is not None, value=override)

    # 4. 市場健全性
    try:
        mark_price = _market_sanity(adapter)
        _api_ok["market"] = True
    except RuntimeError as e:
        _log("STOP", reason=str(e))
        _update_fail_count(_api_ok)
        return

    # 5. 足データ（429 時は最大3回リトライ）
    _candles_r = None
    for _retry in range(3):
        try:
            _candles_r = adapter.get_candles(PRODUCT_TYPE, SYMBOL, "5m", CANDLE_LIMIT)
            break
        except Exception as e:
            if "429" in str(e) and _retry < 2:
                _wait = 2.0 ** _retry
                _log("CANDLE_RETRY", attempt=_retry + 1, wait_s=_wait, error=str(e))
                time.sleep(_wait)
            else:
                _log("STOP", reason=f"candles_fetch_failed: {e}")
                _update_fail_count(_api_ok)
                return
    candles_raw = _candles_r.get("data") or []
    if len(candles_raw) < 60:
        _log("STOP", reason=f"insufficient_candles: {len(candles_raw)}")
        _update_fail_count(_api_ok)
        return
    _api_ok["candle"] = True

    last_close = float(candles_raw[-1][4]) if candles_raw else mark_price
    snapshot   = {"candles_5m": candles_raw, "params": params}

    # ----------------------------------------------------------
    # 6. pending_entry 状態確認（両サイド）
    # ----------------------------------------------------------
    for _s in ("LONG", "SHORT"):
        if pending[_s] is None:
            continue
        pnd           = pending[_s]
        order_id      = str(pnd.get("order_id", ""))
        placed_bar_ms = int(pnd.get("placed_bar_time", 0))
        cur_bar_ms    = int(candles_raw[-1][0]) if candles_raw else 0
        bar_elapsed   = max(0, (cur_bar_ms - placed_bar_ms) // (5 * 60 * 1000))

        try:
            detail      = _get_order_state(adapter, order_id)
            order_state = detail.get("state", "unknown")
        except Exception as e:
            _log("PENDING_DETAIL_ERROR", side=_s, error=str(e))
            order_state = "unknown"

        _log("PENDING_STATUS", side=_s, order_id=order_id, state=order_state,
             bar_elapsed=bar_elapsed, ttl=PENDING_TTL_BARS)

        if order_state == "filled":
            try:
                _confirm_entry(adapter, pnd, open_pos[_s], detail, mark_price, params, _opp(_s))
            except Exception as e:
                _pp(_s).unlink(missing_ok=True)
                if "SL_PRICE_INVALID:40917" in str(e):
                    p_side = str(pnd.get("side", ""))
                    _log("SL_PRICE_INVALID_CLOSE", side=p_side, reason=str(e))
                    try:
                        _do_close(adapter, p_side=p_side,
                                  size=str(pnd.get("size", "")),
                                  client_oid=f"sl_invalid_{int(time.time()*1000)}")
                        _opp(_s).unlink(missing_ok=True)
                        _log("EXIT_COMPLETE", exit_reason="SL_PRICE_INVALID")
                    except Exception as ce:
                        _log("STOP", reason=f"sl_invalid_close_failed: {ce}")
                    _update_fail_count(_api_ok)
                    return
                _log("STOP", reason=f"confirm_entry_failed: {e}")
                _update_fail_count(_api_ok)
                return
            try:
                open_pos[_s] = read_json(_opp(_s)) if _opp(_s).exists() else None
            except Exception:
                pass
            _pp(_s).unlink(missing_ok=True)
            _log("PENDING_CLEARED", side=_s, reason="filled")
            pending[_s] = None

        elif order_state == "canceled":
            _pp(_s).unlink(missing_ok=True)
            _log("PENDING_CLEARED", side=_s, reason="externally_canceled")
            pending[_s] = None

        elif bar_elapsed >= PENDING_TTL_BARS:
            try:
                _cancel_order(adapter, order_id)
                _log("PENDING_TTL_CANCEL", side=_s, order_id=order_id, bar_elapsed=bar_elapsed)
            except Exception as e:
                _log("PENDING_CANCEL_ERROR", side=_s, error=str(e))

            # 部分約定残ポジ確認
            try:
                lp = adapter.get_position_by_side(
                    product_type=PRODUCT_TYPE, margin_coin=MARGIN_COIN,
                    symbol=SYMBOL, hold_side=_s.lower())
                remaining_sz = float((lp or {}).get("total", 0)) if lp else 0.0
            except Exception as e:
                _log("STOP", reason=f"post_cancel_pos_check_failed: {e}")
                _update_fail_count(_api_ok)
                return

            existing_sz = float(open_pos[_s].get("size_btc", 0)) if open_pos[_s] else 0.0
            if remaining_sz > existing_sz:
                p_side  = str(pnd.get("side", ""))
                p_pri   = int(pnd.get("entry_priority", -1))
                adx_val = float(pnd.get("adx_at_entry", 0) or 0)
                actual_price = float((lp or {}).get("openPriceAvg")
                                     or pnd.get("limit_price", 0))
                tp_pct = _calc_tp_pct(p_side, adx_val, params, p_pri)
                try:
                    tp, tp_order_id = _place_tp(
                        adapter, side=p_side,
                        entry_price=Decimal(str(actual_price)),
                        tp_pct=tp_pct, position_size=remaining_sz,
                        mark_price=float((lp or {}).get("markPrice") or 0) or None)
                    write_json(_opp(_s), {
                        "side": p_side, "entry_priority": p_pri,
                        "entry_price": actual_price,
                        "entry_time": str(int(time.time() * 1000)),
                        "last_update_time": str(int(time.time() * 1000)),
                        "add_count": 1, "size_btc": remaining_sz,
                        "tp": float(tp), "tp_pct": tp_pct, "tp_order_id": tp_order_id,
                        "sl": None, "sl_order_id": None, "mfe_usd": 0.0, "pricePlace": 1,
                    })
                    open_pos[_s] = read_json(_opp(_s))
                    _log("PARTIAL_FILL_TP_SET", side=p_side, size=remaining_sz,
                         entry_price=actual_price, tp=float(tp))
                except Exception as e:
                    _log("STOP", reason=f"partial_fill_tp_failed: {e}")
                    _update_fail_count(_api_ok)
                    return

            _pp(_s).unlink(missing_ok=True)
            _log("PENDING_CLEARED", side=_s, reason="ttl_expired")
            pending[_s] = None

        else:
            # まだ待機中 — Exit チェックは下で実行
            _log("NOOP", reason="pending_waiting", side=_s, bar_elapsed=bar_elapsed)

    # ----------------------------------------------------------
    # 7. Exit チェック（両サイド）
    # ----------------------------------------------------------
    for _s in ("LONG", "SHORT"):
        if open_pos[_s] is not None:
            _run_exit_checks(adapter, open_pos[_s], mark_price, candles_raw, params, _opp(_s))

    # ----------------------------------------------------------
    # 8. エントリー / ADD 判断
    # ----------------------------------------------------------
    if override is not None:
        decision = dict(override)
        _log("DECISION_OVERRIDE", decision=decision)
        _OVERRIDE_PATH.unlink(missing_ok=True)
    else:
        try:
            decision = v9_decide(snapshot)
        except Exception as e:
            _log("STOP", reason=f"v9_decide_failed: {e}")
            _update_fail_count(_api_ok)
            return

    _log("DECISION", action=decision.get("action"), reason=decision.get("reason"),
         side=decision.get("side"), priority=decision.get("entry_priority"))

    action = decision.get("action")
    if action == "STOP":
        _log("STOP", reason=decision.get("reason"))
        _update_fail_count(_api_ok)
        return
    if action == "NOOP":
        _log("NOOP", reason=decision.get("reason"), debug=decision.get("debug"))
        _log("RUN_SUMMARY", action="NOOP", reason=decision.get("reason"),
             side=decision.get("side"), priority=decision.get("entry_priority"))
        _update_fail_count(_api_ok)
        return
    if action != "ENTER":
        _log("STOP", reason=f"unexpected_action: {action}")
        _update_fail_count(_api_ok)
        return

    d_side     = str(decision["side"])
    d_priority = int(decision.get("entry_priority", decision.get("priority", -1)))
    material   = decision.get("material", {})

    # 同一サイドのポジションあり: ADD上限チェック
    if open_pos[d_side] is not None:
        add_count = int(open_pos[d_side].get("add_count", 1))
        pos_pri   = int(open_pos[d_side].get("entry_priority", d_priority))
        max_adds  = int(params.get("MAX_ADDS_BY_PRIORITY", {}).get(
                        str(pos_pri), params.get(f"{d_side}_MAX_ADDS", 5)))
        if add_count >= max_adds:
            _log("NOOP", reason=f"add_limit_reached: add_count={add_count} max={max_adds}")
            _update_fail_count(_api_ok)
            return

    # 同一サイドの pending が残っていたら発注しない
    if pending[d_side] is not None:
        _log("NOOP", reason=f"same_side_pending_exists: side={d_side}")
        _update_fail_count(_api_ok)
        return

    # 指値計算
    if d_side == "LONG":
        lp = q_down(Decimal(str(last_close)) * Decimal("0.9999"), PRICE_TICK)
    else:
        lp = q_up(Decimal(str(last_close)) * Decimal("1.0001"), PRICE_TICK)
    lp_str     = fmt_price_1dp(lp)
    size_str   = str(float(params[f"{d_side}_POSITION_SIZE_BTC"]))
    adx_val    = float(material.get("adx", 0) or 0)
    client_oid = f"v9_{d_side.lower()}_{d_priority}_{int(time.time()*1000)}"

    # H-3: 参照パラメータ証跡
    _log("ENTRY_DECISION", side=d_side, priority=d_priority, adx=adx_val, material=material)

    try:
        order_id = _place_limit_order(adapter, side=d_side, size=size_str,
                                      price=lp_str, client_oid=client_oid)
    except Exception as e:
        _log("STOP", reason=f"place_limit_order_failed: {e}")
        _update_fail_count(_api_ok)
        return

    write_json(_pp(d_side), {
        "order_id":        order_id,
        "client_oid":      client_oid,
        "side":            d_side,
        "entry_priority":  d_priority,
        "limit_price":     lp_str,
        "size":            size_str,
        "placed_bar_time": int(candles_raw[-1][0]) if candles_raw else 0,
        "placed_time":     str(int(time.time() * 1000)),
        "adx_at_entry":    adx_val,
    })
    _log("PENDING_WRITTEN", order_id=order_id, side=d_side, limit_price=lp_str)
    _log("RUN_SUMMARY", action="ENTRY", side=d_side, priority=d_priority, limit_price=lp_str)
    _update_fail_count(_api_ok)


if __name__ == "__main__":
    run()
