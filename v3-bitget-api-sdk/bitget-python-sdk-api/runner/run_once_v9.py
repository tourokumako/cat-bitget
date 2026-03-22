from __future__ import annotations
# ============================================================
#  SAFETY GUARD — DO NOT MODIFY WITHOUT USER APPROVAL
ALLOW_LIVE_ORDERS = True
# ============================================================
"""run_once_v9.py — V9 実行エンジン（1回実行型）
ALLOW_LIVE_ORDERS=False → DRY_RUN（発注スキップ）
ALLOW_LIVE_ORDERS=True  → 実発注（ユーザーのみ変更可）
"""
import json, math, sys, time
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional
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
_PENDING_PATH  = state_path("pending_entry.json")
_OPEN_POS_PATH = state_path("open_position.json")
_OVERRIDE_PATH = state_path("decision_override.json")
_LOG_PATH      = _ROOT / "logs" / "run_once_v9.jsonl"

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
    rec = {"ts": int(time.time() * 1000), "event": event, **kw}
    line = json.dumps(rec, ensure_ascii=False, default=str)
    _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line)


# ==============================================================
# パラメータロード（H-1/H-2）
# ==============================================================
def _load_params() -> Dict[str, Any]:
    params = read_json(_PARAMS_PATH)
    missing = [k for k in _REQUIRED_KEYS if k not in params]
    if missing:
        raise ValueError(f"cat_params_v9.json missing keys: {missing}")
    _log("PARAMS_LOADED", path=str(_PARAMS_PATH),
         sample={k: params[k] for k in [
             "LONG_TP_PCT", "SHORT_TP_PCT", "LONG_SL_PCT", "SHORT_SL_PCT",
             "LONG_POSITION_SIZE_BTC", "TP_FEE_FLOOR_ENABLE", "TP_ADX_BOOST_ENABLE",
         ]})
    return params


# ==============================================================
# 動的 TP 計算（H-5）
# ==============================================================
def _calc_tp_pct(side: str, adx: float, params: Dict[str, Any]) -> float:
    base = float(params[f"{side}_TP_PCT"])
    fee_applied = boost_applied = False

    if int(params.get("TP_FEE_FLOOR_ENABLE", 0)):
        base += float(params["FEE_RATE_MAKER"]) * float(params["FEE_MARGIN"]) * 2
        fee_applied = True

    if int(params.get("TP_ADX_BOOST_ENABLE", 0)) and adx > float(params["ADX_THRESH"]):
        if adx > float(params["ADX_TP_THRESH_HIGH"]):
            base *= float(params["TP_PCT_SCALE_HIGH"])
        else:
            base *= float(params["TP_PCT_SCALE"])
        boost_applied = True

    if int(params.get("TP_PCT_CLAMP_ENABLE", 0)):
        base = min(base, float(params.get("TP_PCT_CLAMP_MAX", 0.01)))

    _log("TPSL_CTX", side=side, effective_tp_pct=round(base, 8),
         adx=round(adx, 2), fee_applied=fee_applied, boost_applied=boost_applied)
    return base


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
        "size": size, "price": price,
        "side": "buy" if side == "LONG" else "sell",
        "tradeSide": "open",
        "orderType": "limit", "force": "post_only",
        "clientOid": client_oid,
    }
    _log("ENTRY_SEND", side=side, limit_price=price, size=size, client_oid=client_oid)
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


def _cancel_plan_order(adapter: BitgetAdapter, order_id: str) -> None:
    """TP/SL plan注文のキャンセル（失敗は WARN 止まり、例外にしない）"""
    if not ALLOW_LIVE_ORDERS:
        _log("DRY_RUN_SKIP", action="cancel_plan_order", order_id=order_id)
        return
    r = adapter.api._request_with_params(POST, "/api/v2/mix/order/cancel-plan-order",
        {"symbol": SYMBOL, "productType": PRODUCT_TYPE, "orderId": order_id})
    if r.get("code") != "00000":
        _log("TP_CANCEL_WARN", order_id=order_id, response=r)
    else:
        _log("TP_CANCELLED", order_id=order_id)


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
              position_size: Optional[float] = None) -> tuple:
    if side == "LONG":
        tp = q_down(entry_price * (Decimal("1") + Decimal(str(tp_pct))), PRICE_TICK)
        hold_side = "long"
        if not tp > entry_price:
            raise RuntimeError(f"LONG tp {tp} <= entry {entry_price}")
    else:
        tp = q_up(entry_price * (Decimal("1") - Decimal(str(tp_pct))), PRICE_TICK)
        hold_side = "short"
        if not tp < entry_price:
            raise RuntimeError(f"SHORT tp {tp} >= entry {entry_price}")
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

    # 1. BREAKOUT_CUT (P22/P23 SHORT, add≥3)
    if side == "SHORT" and priority in (22, 23) and add_count >= 3:
        if priority == 23:
            bw = _col("bb_width"); rsi = _col("rsi_short")
            if (not math.isnan(bw)  and bw  >= float(params.get("P23_BREAKOUT_BB_WIDTH_MIN", 0.03))
                    and not math.isnan(rsi) and rsi >= float(params.get("P23_BREAKOUT_RSI_MIN", 70.0))):
                return "BREAKOUT_CUT"
        else:
            return "BREAKOUT_CUT"

    # 2. MFE_STALE_CUT (P22 SHORT, add≥5, hold≥120min)
    if side == "SHORT" and priority == 22 and add_count >= 5 and hold_min >= 120:
        if (mfe_usd  >= float(params.get("P22_SHORT_MFE_EXIT_PROFIT_USD", 15.0))
                and unreal <= float(params.get("P22_SHORT_MFE_MAX_GATE_USD", 20.0))):
            return "MFE_STALE_CUT"

    # 3. RSI 逆行 EXIT (SHORT)
    if side == "SHORT" and bool(params.get("FEAT_SHORT_RSI_REVERSE_EXIT", False)):
        rsi_v = _col("rsi_short"); rsi_sl = _col("rsi_slope_short"); adx_v = _col("adx")
        if (hold_min >= float(params.get("SHORT_MIN_HOLD_FOR_RSI_EXIT", 1))
                and not math.isnan(rsi_v)  and rsi_v  < float(params.get("SHORT_RSI_THRESH", 50))
                and not math.isnan(rsi_sl) and rsi_sl > float(params.get("SHORT_RSI_SLOPE_MAX", 0.0))
                and not math.isnan(adx_v)  and adx_v  < float(params.get("SHORT_RSI_EXIT_ADX_MAX", 12))):
            return "RSI_REVERSE_EXIT"

    # 4. MAE_CUT (P23 SHORT, add≥4, hold≥300min)
    if side == "SHORT" and priority == 23 and add_count >= 4 and hold_min >= 300:
        return "MAE_CUT"

    # 5. PROFIT_LOCK
    if side == "LONG" and int(params.get("LONG_PROFIT_LOCK_ENABLE", 0)):
        if (mfe_usd >= float(params.get("LONG_PROFIT_LOCK_ARM_USD", 15.0))
                and unreal < float(params.get("LONG_PROFIT_LOCK_USD", 6.0))):
            return "PROFIT_LOCK"
    if side == "SHORT" and priority == 22 and int(params.get("P22_SHORT_PROFIT_LOCK_ENABLE", 0)):
        if (mfe_usd >= float(params.get("P22_SHORT_PROFIT_LOCK_ARM_USD", 22.0))
                and unreal < float(params.get("P22_SHORT_PROFIT_LOCK_USD", 8.0))):
            return "PROFIT_LOCK"

    # 6. STAGNATION_CUT
    if hold_min >= float(params.get("STAG_MIN_M", 20.0)) and mfe_usd <= float(params.get("STAG_MFE_USD", 1.0)):
        if priority == 4 and int(params.get("P4_STAGNATION_WIDE_ENABLE", 0)):
            if (hold_min >= float(params.get("P4_STAGNATION_WIDE_MIN", 20.0))
                    and mfe_usd <= float(params.get("P4_STAGNATION_WIDE_MAX_MFE", 1.0))):
                return "STAGNATION_CUT"
        elif priority != 4:
            return "STAGNATION_CUT"

    # 7. TIME_EXIT
    base_t = float(params.get("P2_TIME_EXIT_MIN" if priority == 2 else
                              f"{side}_TIME_EXIT_MIN", 150 if side == "LONG" else 480))
    down_f = float(params.get(f"{side}_TIME_EXIT_DOWN_FACTOR", 0.75))
    if hold_min >= base_t * (down_f if unreal < 0 else 1.0):
        return "TIME_EXIT"

    return None


# ==============================================================
# 約定確認 → open_position + TP/SL
# ==============================================================
def _confirm_entry(adapter: BitgetAdapter, pending: Dict, open_pos: Optional[Dict],
                   detail: Dict, mark_price: float, params: Dict) -> None:
    p_side    = str(pending["side"])
    p_pri     = int(pending.get("entry_priority", -1))
    adx_val   = float(pending.get("adx_at_entry", 0) or 0)
    size_btc  = float(pending.get("size", params[f"{p_side}_POSITION_SIZE_BTC"]))
    price_avg = float(detail.get("priceAvg") or 0) or mark_price
    filled_sz = float(detail.get("baseVolume") or 0) or size_btc

    tp_pct = _calc_tp_pct(p_side, adx_val, params)

    if open_pos is None:
        # 初回 ENTRY
        tp, tp_order_id = _place_tp(adapter, side=p_side, entry_price=Decimal(str(price_avg)), tp_pct=tp_pct, position_size=filled_sz)
        write_json(_OPEN_POS_PATH, {
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
        tp, tp_order_id = _place_tp(adapter, side=p_side, entry_price=entry_dec, tp_pct=tp_pct, position_size=new_sz)
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
        write_json(_OPEN_POS_PATH, open_pos)
        _log("ADD_CONFIRMED", side=p_side, add_count=new_cnt,
             avg_price=round(new_avg, 2), size=new_sz, tp=float(tp), sl=sl_val,
             sl_order_id=sl_order_id_new)


# ==============================================================
# Exit 実行
# ==============================================================
def _run_exit_checks(adapter: BitgetAdapter, open_pos: Dict, mark_price: float,
                     candles_raw: list, params: Dict) -> bool:
    """Exit を実行して True を返す。Exit なしなら False。"""
    try:
        live_pos = adapter.get_single_position(
            product_type=PRODUCT_TYPE, margin_coin=MARGIN_COIN, symbol=SYMBOL)
    except Exception as e:
        _log("STOP", reason=f"get_single_position_failed: {e}")
        return True

    if live_pos is None or float(live_pos.get("total", 0)) == 0:
        _side = open_pos.get("side", "")
        _sl   = open_pos.get("sl")
        _tp   = open_pos.get("tp")
        if _sl is None:
            ext_reason = "TP_FILLED"           # SLなし→TPのみ設定されていた
        elif _side == "LONG":
            if   _tp and mark_price >= float(_tp): ext_reason = "TP_FILLED"
            elif mark_price <= float(_sl):         ext_reason = "SL_FILLED"
            else:                                  ext_reason = "TP_OR_SL_HIT"
        else:  # SHORT
            if   _tp and mark_price <= float(_tp): ext_reason = "TP_FILLED"
            elif mark_price >= float(_sl):         ext_reason = "SL_FILLED"
            else:                                  ext_reason = "TP_OR_SL_HIT"
        _log("EXIT_EXTERNAL", reason=ext_reason, side=_side,
             mark_price=mark_price, tp=_tp, sl=_sl)
        _OPEN_POS_PATH.unlink(missing_ok=True)
        return True

    p_side  = open_pos["side"]
    entry_p = float(open_pos["entry_price"])
    size_b  = float(open_pos.get("size_btc", params.get(f"{p_side}_POSITION_SIZE_BTC", 0.024)))
    unreal  = ((mark_price - entry_p) if p_side == "LONG" else (entry_p - mark_price)) * size_b
    old_mfe = float(open_pos.get("mfe_usd", 0.0))
    if unreal > old_mfe:
        open_pos["mfe_usd"] = unreal
        open_pos["last_update_time"] = str(int(time.time() * 1000))
        write_json(_OPEN_POS_PATH, open_pos)

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

    hold_min = (int(time.time() * 1000) - int(open_pos["entry_time"])) / 60_000
    _log("EXIT_TRIGGERED", reason=exit_reason, side=p_side,
         mark_price=mark_price, entry_price=entry_p,
         hold_min=round(hold_min, 1), mfe_usd=open_pos.get("mfe_usd", 0),
         unreal_usd=round(unreal, 4))

    # クローズ前再確認
    try:
        lp2 = adapter.get_single_position(
            product_type=PRODUCT_TYPE, margin_coin=MARGIN_COIN, symbol=SYMBOL)
        if lp2 is None or float(lp2.get("total", 0)) == 0:
            _log("NO_POSITION", reason="already_closed_before_close_send")
            _OPEN_POS_PATH.unlink(missing_ok=True)
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
        lp3 = adapter.get_single_position(
            product_type=PRODUCT_TYPE, margin_coin=MARGIN_COIN, symbol=SYMBOL)
        remaining = float((lp3 or {}).get("total", 0))
    except Exception:
        remaining = -1.0

    if remaining <= 0:
        tp_oid = open_pos.get("tp_order_id")
        if tp_oid:
            _cancel_plan_order(adapter, tp_oid)
        sl_oid = open_pos.get("sl_order_id")
        if sl_oid:
            _cancel_plan_order(adapter, sl_oid)
        _OPEN_POS_PATH.unlink(missing_ok=True)
        _log("CLOSE_VERIFY", status="complete", reason=exit_reason)
    else:
        _log("EXIT_PENDING", remaining=remaining, reason=exit_reason)
    return True


# ==============================================================
# メインフロー
# ==============================================================
def run() -> None:
    _log("RUN_START", allow_live_orders=ALLOW_LIVE_ORDERS)

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
    _log("CONFIG_LOADED", paper_trading=paper_trading)

    # 2. state ロード
    pending = open_pos = None
    try:
        if _PENDING_PATH.exists():
            pending = read_json(_PENDING_PATH)
    except Exception as e:
        _log("PENDING_READ_ERROR", error=str(e))
    try:
        if _OPEN_POS_PATH.exists():
            open_pos = read_json(_OPEN_POS_PATH)
    except Exception as e:
        _log("OPEN_POS_READ_ERROR", error=str(e))

    # STARTUP RECONCILIATION: stateと取引所ポジの整合確認（両方向）
    if ALLOW_LIVE_ORDERS:
        try:
            _live_pos = adapter.get_single_position(
                product_type=PRODUCT_TYPE, margin_coin=MARGIN_COIN, symbol=SYMBOL)
            _exchange_has_pos = _live_pos is not None and float(_live_pos.get("total", 0)) > 0
        except Exception as e:
            _log("STOP", reason=f"startup_reconciliation_error: {e}")
            return
        if open_pos is None and pending is None and _exchange_has_pos:
            _log("STOP", reason=(
                f"startup_reconciliation_failed: exchange has position "
                f"(side={_live_pos.get('holdSide')} size={_live_pos.get('total')}) "
                f"but open_position.json is missing"
            ))
            return
        if open_pos is not None and not _exchange_has_pos:
            _log("STOP", reason=(
                f"startup_reconciliation_failed: open_position.json exists "
                f"(side={open_pos.get('side')} size={open_pos.get('size_btc')}) "
                f"but exchange has no position"
            ))
            return

    # S-5/S-6: tp_order_id 実在確認（ライブ時のみ）
    if open_pos is not None and ALLOW_LIVE_ORDERS:
        tp_oid = open_pos.get("tp_order_id")
        if not tp_oid:
            _log("STOP", reason="tp_order_id_missing: open_position.json has no tp_order_id — manual check required")
            return
        else:
            try:
                r = adapter.api.ordersPlanPending({
                    "symbol": SYMBOL, "productType": PRODUCT_TYPE,
                    "planType": "profit_loss",
                })
                data = r.get("data") or {}
                # レスポンスキーが entrustedList / orderList のどちらか実弾で要確認
                orders = (data.get("entrustedList")
                          or data.get("orderList")
                          or (data if isinstance(data, list) else []))
                ids = {str(o.get("orderId", "")) for o in orders if isinstance(o, dict)}
                if str(tp_oid) not in ids:
                    # TP消滅 → ポジションも確認してから判断
                    try:
                        live_chk = adapter.get_single_position(
                            product_type=PRODUCT_TYPE, margin_coin=MARGIN_COIN, symbol=SYMBOL)
                    except Exception as chk_e:
                        _log("STOP", reason=f"tp_order_missing_pos_check_failed: {chk_e}")
                        return
                    if live_chk is not None and float(live_chk.get("total", 0)) > 0:
                        _log("STOP", reason=f"tp_order_missing: tp_order_id={tp_oid} not in plan orders")
                        return
                    _log("TP_ORDER_MISSING_POS_GONE", tp_order_id=tp_oid)
                    # → _run_exit_checks (S-7) へ進む
                else:
                    _log("TP_ORDER_VERIFIED", tp_order_id=tp_oid)
            except Exception as e:
                _log("STOP", reason=f"tp_order_verify_failed: {e}")
                return

    # H-0: state 宣言
    _log("STATE_DECLARED",
         mode="live" if ALLOW_LIVE_ORDERS else "dry_run",
         paper_trading=paper_trading,
         pending_entry=pending is not None,
         open_position=open_pos is not None)

    override = None
    if _OVERRIDE_PATH.exists():
        try:
            override = read_json(_OVERRIDE_PATH)
        except Exception:
            pass
    _log("OVERRIDE_STATUS", active=override is not None, value=override)

    # 3. 市場健全性
    try:
        mark_price = _market_sanity(adapter)
    except RuntimeError as e:
        _log("STOP", reason=str(e))
        return

    # 4. 足データ
    try:
        candles_r   = adapter.get_candles(PRODUCT_TYPE, SYMBOL, "5m", CANDLE_LIMIT)
        candles_raw = candles_r.get("data") or []
        if len(candles_raw) < 60:
            _log("STOP", reason=f"insufficient_candles: {len(candles_raw)}")
            return
    except Exception as e:
        _log("STOP", reason=f"candles_fetch_failed: {e}")
        return

    last_close = float(candles_raw[-1][4]) if candles_raw else mark_price
    snapshot   = {"candles_5m": candles_raw, "params": params}

    # ----------------------------------------------------------
    # 5. pending_entry 状態確認
    # ----------------------------------------------------------
    if pending is not None:
        order_id      = str(pending.get("order_id", ""))
        placed_bar_ms = int(pending.get("placed_bar_time", 0))
        cur_bar_ms    = int(candles_raw[-1][0]) if candles_raw else 0
        bar_elapsed   = max(0, (cur_bar_ms - placed_bar_ms) // (5 * 60 * 1000))

        try:
            detail      = _get_order_state(adapter, order_id)
            order_state = detail.get("state", "unknown")
        except Exception as e:
            _log("PENDING_DETAIL_ERROR", error=str(e))
            order_state = "unknown"

        _log("PENDING_STATUS", order_id=order_id, state=order_state,
             bar_elapsed=bar_elapsed, ttl=PENDING_TTL_BARS)

        if order_state == "filled":
            try:
                _confirm_entry(adapter, pending, open_pos, detail, mark_price, params)
            except Exception as e:
                _log("STOP", reason=f"confirm_entry_failed: {e}")
                return
            try:
                open_pos = read_json(_OPEN_POS_PATH) if _OPEN_POS_PATH.exists() else None
            except Exception:
                pass
            _PENDING_PATH.unlink(missing_ok=True)
            _log("PENDING_CLEARED", reason="filled")
            pending = None

        elif order_state == "canceled":
            _PENDING_PATH.unlink(missing_ok=True)
            _log("PENDING_CLEARED", reason="externally_canceled")
            pending = None

        elif bar_elapsed >= PENDING_TTL_BARS:
            try:
                _cancel_order(adapter, order_id)
                _log("PENDING_TTL_CANCEL", order_id=order_id, bar_elapsed=bar_elapsed)
            except Exception as e:
                _log("PENDING_CANCEL_ERROR", error=str(e))

            # 部分約定残ポジ確認 → 残あればTP設定してopen_positionを作る
            try:
                lp = adapter.get_single_position(
                    product_type=PRODUCT_TYPE, margin_coin=MARGIN_COIN, symbol=SYMBOL)
                remaining_sz = float((lp or {}).get("total", 0)) if lp else 0.0
            except Exception as e:
                _log("STOP", reason=f"post_cancel_pos_check_failed: {e}")
                return

            existing_sz = float(open_pos.get("size_btc", 0)) if open_pos else 0.0
            if remaining_sz > existing_sz:
                p_side  = str(pending.get("side", ""))
                p_pri   = int(pending.get("entry_priority", -1))
                adx_val = float(pending.get("adx_at_entry", 0) or 0)
                actual_price = float((lp or {}).get("openPriceAvg")
                                     or pending.get("limit_price", 0))
                tp_pct = _calc_tp_pct(p_side, adx_val, params)
                try:
                    tp, tp_order_id = _place_tp(
                        adapter, side=p_side,
                        entry_price=Decimal(str(actual_price)),
                        tp_pct=tp_pct, position_size=remaining_sz)
                    write_json(_OPEN_POS_PATH, {
                        "side": p_side, "entry_priority": p_pri,
                        "entry_price": actual_price,
                        "entry_time": str(int(time.time() * 1000)),
                        "last_update_time": str(int(time.time() * 1000)),
                        "add_count": 1, "size_btc": remaining_sz,
                        "tp": float(tp), "tp_pct": tp_pct, "tp_order_id": tp_order_id,
                        "sl": None, "sl_order_id": None, "mfe_usd": 0.0, "pricePlace": 1,
                    })
                    open_pos = read_json(_OPEN_POS_PATH)
                    _log("PARTIAL_FILL_TP_SET", side=p_side, size=remaining_sz,
                         entry_price=actual_price, tp=float(tp))
                except Exception as e:
                    _log("STOP", reason=f"partial_fill_tp_failed: {e}")
                    return

            _PENDING_PATH.unlink(missing_ok=True)
            _log("PENDING_CLEARED", reason="ttl_expired")
            pending = None

        else:
            # まだ待機中 — Exit チェックだけして終了
            if open_pos is not None:
                _run_exit_checks(adapter, open_pos, mark_price, candles_raw, params)
            _log("NOOP", reason="pending_waiting", bar_elapsed=bar_elapsed)
            return

    # ----------------------------------------------------------
    # 6. Exit チェック
    # ----------------------------------------------------------
    if open_pos is not None:
        exited = _run_exit_checks(adapter, open_pos, mark_price, candles_raw, params)
        if exited:
            return

    # ----------------------------------------------------------
    # 7. エントリー / ADD 判断
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
            return

    _log("DECISION", action=decision.get("action"), reason=decision.get("reason"),
         side=decision.get("side"), priority=decision.get("entry_priority"))

    action = decision.get("action")
    if action == "STOP":
        _log("STOP", reason=decision.get("reason"))
        return
    if action == "NOOP":
        _log("NOOP", reason=decision.get("reason"), debug=decision.get("debug"))
        return
    if action != "ENTER":
        _log("STOP", reason=f"unexpected_action: {action}")
        return

    d_side     = str(decision["side"])
    d_priority = int(decision.get("entry_priority", decision.get("priority", -1)))
    material   = decision.get("material", {})

    # ポジションあり: サイド確認・ADD上限チェック
    if open_pos is not None:
        if open_pos["side"] != d_side:
            _log("NOOP", reason=f"pos_side_mismatch: pos={open_pos['side']} dec={d_side}")
            return
        add_count = int(open_pos.get("add_count", 1))
        pos_pri   = int(open_pos.get("entry_priority", d_priority))
        max_adds  = int(params.get("MAX_ADDS_BY_PRIORITY", {}).get(
                        str(pos_pri), params.get(f"{d_side}_MAX_ADDS", 5)))
        if add_count >= max_adds:
            _log("NOOP", reason=f"add_limit_reached: add_count={add_count} max={max_adds}")
            return

    # 同一 side の pending が残っていたら発注しない
    if pending is not None and pending.get("side") == d_side:
        _log("NOOP", reason=f"same_side_pending_exists: side={d_side}")
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
        return

    write_json(_PENDING_PATH, {
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


if __name__ == "__main__":
    run()
