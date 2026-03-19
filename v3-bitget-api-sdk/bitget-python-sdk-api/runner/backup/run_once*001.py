from __future__ import annotations

import json
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict

import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from runner.io_json import read_json, write_json, state_path

from runner.bitget_adapter import (
    BitgetAdapter,
    load_keys,
)
from strategies.cat_live_decider import decide as strategy_decide

# ===== 固定設定（Phase1/2で合意済み） =====
PRODUCT_TYPE = "USDT-FUTURES"
SYMBOL = "BTCUSDT"
MARGIN_COIN = "USDT"
MARGIN_MODE = "isolated"

# --- ADD: RSI (Wilder) + slope (CAT_v8_01 runner責務) ---
def _rsi_wilder(closes: list[float], period: int) -> list[float]:
    """
    Wilder RSI. ta.momentum.RSIIndicator と同系統（Wilder smoothing）。
    戻り: len(closes) と同じ長さ（先頭は nan が混ざる）
    """
    import math
    n = int(period)
    if n <= 1 or not isinstance(closes, list) or len(closes) < n + 1:
        return [float("nan")] * (len(closes) if isinstance(closes, list) else 0)

    gains = [0.0]
    losses = [0.0]
    for i in range(1, len(closes)):
        d = float(closes[i]) - float(closes[i - 1])
        gains.append(d if d > 0 else 0.0)
        losses.append(-d if d < 0 else 0.0)

    rsi = [float("nan")] * len(closes)

    # initial avg (simple)
    avg_gain = sum(gains[1 : n + 1]) / n
    avg_loss = sum(losses[1 : n + 1]) / n

    def _calc(_ag: float, _al: float) -> float:
        if _al == 0.0:
            return 100.0
        rs = _ag / _al
        return 100.0 - (100.0 / (1.0 + rs))

    rsi[n] = _calc(avg_gain, avg_loss)

    # Wilder smoothing
    for i in range(n + 1, len(closes)):
        avg_gain = (avg_gain * (n - 1) + gains[i]) / n
        avg_loss = (avg_loss * (n - 1) + losses[i]) / n
        rsi[i] = _calc(avg_gain, avg_loss)

    return rsi


def _rsi_now_prev_slope(closes: list[float], rsi_period: int, slope_n: int) -> dict:
    """
    slope は CAT_v8_01 と同じく diff(n) 相当。
    戻り: rsi_now, rsi_prev, slope_now, slope_prev
    """
    r = _rsi_wilder(closes, int(rsi_period))
    n = int(slope_n)
    if not r or len(r) < max(3, n + 2):
        return {"rsi_now": float("nan"), "rsi_prev": float("nan"), "slope_now": float("nan"), "slope_prev": float("nan")}

    i = len(r) - 1
    rsi_now = float(r[i])
    rsi_prev = float(r[i - 1])

    def _slope(idx: int) -> float:
        if idx - n < 0:
            return float("nan")
        a = r[idx]
        b = r[idx - n]
        if not (a == a and b == b):
            return float("nan")
        return float(a - b)

    return {
        "rsi_now": rsi_now,
        "rsi_prev": rsi_prev,
        "slope_now": _slope(i),
        "slope_prev": _slope(i - 1),
    }


def load_cat_params() -> dict:
    """
    本番向け：CAT_v8_01 相当のパラメータを1か所から読む（ENV禁止）
    """
    p = Path("config/cat_params.json")
    if not p.exists():
        stop("missing config/cat_params.json")
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        stop(f"cat_params.json parse failed ({e})")
    if not isinstance(d, dict):
        stop("cat_params.json invalid: not a dict")
    return d


# =========================
# state/open_position.json
# =========================
def _open_position_path() -> str:
    return state_path("open_position.json")


def read_open_position() -> Dict[str, Any] | None:
    p = Path(_open_position_path())
    if not p.exists():
        return None
    d = read_json(p)
    return d if isinstance(d, dict) else None


def write_open_position(pos: Dict[str, Any]) -> None:
    write_json(_open_position_path(), pos)


def delete_open_position() -> None:
    p = Path(_open_position_path())
    try:
        if p.exists():
            p.unlink()
    except Exception:
        pass


def update_open_position_with_candle(pos: Dict[str, Any], candle_last: Dict[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(pos, dict) or not isinstance(candle_last, dict):
        return pos

    ts = candle_last.get("ts")
    if ts is not None:
        pos["last_update_time"] = ts

    side = str(pos.get("side", "")).upper()
    hi = candle_last.get("high")
    lo = candle_last.get("low")

    if side == "LONG":
        try:
            if hi is not None:
                hi_f = float(hi)
                cur = pos.get("max_high", None)
                pos["max_high"] = hi_f if cur is None else max(float(cur), hi_f)
        except Exception:
            pass

    if side == "SHORT":
        try:
            if lo is not None:
                lo_f = float(lo)
                cur = pos.get("min_low", None)
                pos["min_low"] = lo_f if cur is None else min(float(cur), lo_f)
        except Exception:
            pass

    return pos


def _calc_tp_sl(
    entry_price: float,
    *,
    side: str,
    pos_size: float,
    tp_pct: float,
    sl_usd: float,
) -> tuple[float, float]:


    """
    CAT_v8_01 と同型（式・round(...,10)）
    ここでは “入力(tp_pct, sl_usd)” を確定させてから渡す（runnerの責務）。
    """
    ps = float(pos_size)
    if not (ps > 0.0):
        return float("nan"), float("nan")

    if str(side).upper() == "LONG":
        tp = round(float(entry_price) * (1.0 + float(tp_pct)), 10)
        sl = round(float(entry_price) - (float(sl_usd) / ps), 10)
    else:  # SHORT
        tp = round(float(entry_price) * (1.0 - float(tp_pct)), 10)
        sl = round(float(entry_price) + (float(sl_usd) / ps), 10)

    return tp, sl


def _median(vals: list[float]) -> float:

    xs = [float(x) for x in vals if x is not None]
    xs = [x for x in xs if x == x]  # drop NaN
    xs.sort()
    n = len(xs)
    if n == 0:
        return float("nan")
    mid = n // 2
    if n % 2 == 1:
        return xs[mid]
    return (xs[mid - 1] + xs[mid]) / 2.0


def _vol_ratio_from_candles(c_list: list, window: int = 20, min_periods: int = 5) -> float:
    """
    CAT_v8_01 fallback と同じ：
    vol_ratio = volume_now / rolling_median(volume, window)  (min_periods=5)
    """
    if not isinstance(c_list, list) or len(c_list) < min_periods:
        return float("nan")

    last = c_list[-1]
    if not isinstance(last, list) or len(last) < 6:
        return float("nan")

    vol_now = float(last[5]) if last[5] is not None else float("nan")
    if not (vol_now == vol_now):
        return float("nan")

    take = c_list[-window:] if len(c_list) >= window else c_list[:]
    vols = []
    for r in take:
        if isinstance(r, list) and len(r) >= 6:
            v = r[5]
            if v is not None:
                try:
                    fv = float(v)
                    if fv == fv:
                        vols.append(fv)
                except Exception:
                    pass

    if len(vols) < min_periods:
        return float("nan")

    base = _median(vols)
    if not (base == base and base > 0.0):
        return float("nan")
    return vol_now / base

def _adx14_from_candles_5m(candles_5m: list) -> float:
    """
    CAT_v8_01 と同じ定義（ADX window=14）
    入力 candles_5m: [ts, open, high, low, close, volume, quoteVol]
    """
    try:
        if not isinstance(candles_5m, list) or len(candles_5m) < 20:
            return float("nan")

        high = [float(x[2]) for x in candles_5m]
        low  = [float(x[3]) for x in candles_5m]
        close= [float(x[4]) for x in candles_5m]

        n = 14

        def _rma(vals: list[float], n: int) -> list[float]:
            out = [float("nan")] * len(vals)
            s = float("nan")
            for i, v in enumerate(vals):
                if v != v:  # NaN
                    continue
                if s != s:
                    s = v
                else:
                    s = (s * (n - 1) + v) / n
                out[i] = s
            return out

        tr  = [float("nan")] * len(close)
        pdm = [0.0] * len(close)
        ndm = [0.0] * len(close)

        for i in range(1, len(close)):
            up = high[i] - high[i - 1]
            dn = low[i - 1] - low[i]
            pdm[i] = up if (up > dn and up > 0) else 0.0
            ndm[i] = dn if (dn > up and dn > 0) else 0.0

            tr[i] = max(
                high[i] - low[i],
                abs(high[i] - close[i - 1]),
                abs(low[i] - close[i - 1]),
            )

        atr   = _rma([0.0 if (v != v) else v for v in tr], n)
        pdm_r = _rma(pdm, n)
        ndm_r = _rma(ndm, n)

        pdi = [float("nan")] * len(close)
        ndi = [float("nan")] * len(close)
        dx  = [float("nan")] * len(close)

        for i in range(len(close)):
            if atr[i] == atr[i] and atr[i] > 0:
                pdi[i] = 100.0 * (pdm_r[i] / atr[i])
                ndi[i] = 100.0 * (ndm_r[i] / atr[i])
                den = pdi[i] + ndi[i]
                dx[i] = (100.0 * abs(pdi[i] - ndi[i]) / den) if den else float("nan")

        adx = _rma([0.0 if (v != v) else v for v in dx], n)
        return float(adx[-1])

    except Exception:
        return float("nan")


# ===== ログ（最小） =====
def log(event: str, data: Dict[str, Any] | None = None) -> None:
    payload = {"event": event}
    if data:
        payload.update(data)
    from decimal import Decimal  # 既にimport済みなら不要

    def _json_default(o):
        if isinstance(o, Decimal):
            return float(o)  # Decimalはfloat化してログに出す
        return str(o)        # それ以外の非JSON型は文字列化（ログ用途なのでOK）

    print(json.dumps(payload, ensure_ascii=False, default=_json_default))


def stop(reason: str) -> None:
    log("STOP", {"reason": reason})
    sys.exit(0)


def main() -> None:
    run_id = uuid.uuid4().hex[:12]
    write_json(state_path("run_id.txt"), {"run_id": run_id})
    log("BOOT", {"run_id": run_id, "symbol": SYMBOL, "productType": PRODUCT_TYPE})

    # --- keys / adapter ---
    keys_path = Path("config/bitget_keys.json")
    keys = load_keys(keys_path)

    # paper_trading は keys.json から読む（無ければ True=デモ既定）
    raw = json.loads(keys_path.read_text(encoding="utf-8"))
    paper_trading = bool(raw.get("paper_trading", True))

    adp = BitgetAdapter(keys, paper_trading=paper_trading)


    # --- PRECHECK ---
    pos_n = adp.pos_count(PRODUCT_TYPE, MARGIN_COIN)
    pend_n = len(adp.get_pending_profit_loss(PRODUCT_TYPE, SYMBOL))

    # Exit検証のため、pos/pending が残っていても STOP しない（証跡としてログに残す）
    log("PRECHECK", {"pos_count": pos_n, "pending_pl_count": pend_n})

    log("PRECHECK_OK")


    # --- PUBLIC snapshot（必要最小限だけ抜く） ---
    contracts = adp.get_contracts(PRODUCT_TYPE)
    contracts_list = contracts.get("data") or []
    btc_contract = next((x for x in contracts_list if x.get("symbol") == SYMBOL), None)

    ticker = adp.get_ticker(PRODUCT_TYPE, SYMBOL)
    t0 = (ticker.get("data") or [])
    t0 = t0[0] if isinstance(t0, list) and t0 else {}

    symp = adp.get_symbol_price(PRODUCT_TYPE, SYMBOL)
    s0 = (symp.get("data") or [])
    s0 = s0[0] if isinstance(s0, list) and s0 else {}

    # --- market sanity guard (critical) ---
    # ask/bid/mark/index の乖離が大きいと Bitget が 45121 で建玉を拒否するため、
    # 発注に進まず STOP してログで証明する（追撃しない）
    try:
        from decimal import Decimal

        bid = Decimal(str(t0.get("bidPr")))
        ask = Decimal(str(t0.get("askPr")))
        last = Decimal(str(t0.get("lastPr")))
        mark = Decimal(str(t0.get("markPrice")))

        if bid <= 0 or ask <= 0 or mark <= 0:
            stop(f"market_sanity: non-positive prices bid={bid} ask={ask} mark={mark}")

        spread_ratio = (ask - bid) / mark
        mark_last_ratio = abs(mark - last) / mark

        # 固定しきい値（安全優先）
        # spread>1% もしくは mark-last>3% なら STOP
        if spread_ratio > Decimal("0.01"):
            stop(f"market_sanity: spread too wide bid={bid} ask={ask} mark={mark} ratio={spread_ratio}")
        if mark_last_ratio > Decimal("0.03"):
            stop(f"market_sanity: mark-last diverged last={last} mark={mark} ratio={mark_last_ratio}")

    except Exception as e:
        stop(f"market_sanity: parse failed ({e})")

    params = load_cat_params()

    candles = adp.get_candles(PRODUCT_TYPE, SYMBOL, granularity="5m", limit=100)
    c_list = candles.get("data") or []
    c_last = c_list[-1] if isinstance(c_list, list) and c_list else None

    params = load_cat_params()

    market_snapshot = {
        "ts_ms": int(time.time() * 1000),
        "symbol": SYMBOL,
        "productType": PRODUCT_TYPE,

        # 最新足（volume/quoteVol を後段で使うため、まず事実として保存）
        "candle_last": None if not isinstance(c_last, list) else {
            "ts": c_last[0] if len(c_last) > 0 else None,
            "open": c_last[1] if len(c_last) > 1 else None,
            "high": c_last[2] if len(c_last) > 2 else None,
            "low": c_last[3] if len(c_last) > 3 else None,
            "close": c_last[4] if len(c_last) > 4 else None,
            "volume": c_last[5] if len(c_last) > 5 else None,
            "quoteVol": c_last[6] if len(c_last) > 6 else None,
        },

                "vol_ratio": (lambda _cl: (
            float("nan")
            if (not isinstance(_cl, dict))
            else (lambda _v: (
                float("nan") if not (_v == _v and _v > 0) else _v
            ))(float(_cl.get("volume", float("nan"))))
        ))(None if not isinstance(c_last, list) else {
            "volume": c_last[5] if len(c_last) > 5 else None
        }),

        "contracts_btcusdt": None if not isinstance(btc_contract, dict) else {
            "symbol": btc_contract.get("symbol"),
            "minTradeNum": btc_contract.get("minTradeNum"),
            "pricePlace": btc_contract.get("pricePlace"),
            "volumePlace": btc_contract.get("volumePlace"),
            "sizeMultiplier": btc_contract.get("sizeMultiplier"),
            "minTradeUSDT": btc_contract.get("minTradeUSDT"),
            "quoteCoin": btc_contract.get("quoteCoin"),
            "baseCoin": btc_contract.get("baseCoin"),
        },
        "ticker_btcusdt": {
            "lastPr": t0.get("lastPr"),
            "askPr": t0.get("askPr"),
            "bidPr": t0.get("bidPr"),
            "markPrice": t0.get("markPrice"),
            "indexPrice": t0.get("indexPrice"),
            "ts": t0.get("ts"),
        },
        "symbol_price_btcusdt": {
            "price": s0.get("price"),
            "indexPrice": s0.get("indexPrice"),
            "markPrice": s0.get("markPrice"),
            "ts": s0.get("ts"),
        },
        "candles_5m": c_list,
        "candle_last_5m": c_last,
        "vol_ratio": _vol_ratio_from_candles(c_list, window=20, min_periods=5),

        # RSI / slope（runner責務）
        "rsi_ctx": (lambda _cl: _rsi_now_prev_slope(_cl, rsi_period=int(params.get("rsi_period", 13)), slope_n=int(params.get("rsi_slope_n", 3))))(
            [float(x[4]) for x in c_list if isinstance(x, list) and len(x) > 4 and (x[4] is not None)]
        ),

    }

    # ★A: strategy 入力の正本に params/trace_flags を含める（SNAPSHOT保存前）
    market_snapshot["params"] = params if isinstance(params, dict) else {}
    market_snapshot.setdefault("trace_flags", {}).setdefault("TRACE_P22", True)  # テスト用：ON

    # E-3_C test-only: 前回 snapshot に force_action があれば引き継ぐ（相場データは今回のもの）
    try:
        prev = read_json(state_path("market_snapshot.json"))
        fa = prev.get("force_action")
        if fa in ("ENTER", "EXIT", "NOOP", "STOP", "ENTER_SHORT", "EXIT_SHORT"):
            market_snapshot["force_action"] = fa

        # decision-only も引き継ぐ（Entry条件検証専用）
        if prev.get("decision_only") is True:
            market_snapshot["decision_only"] = True

    except Exception:
        pass

    write_json(state_path("market_snapshot.json"), market_snapshot)
    log("SNAPSHOT_WRITTEN")

    # --- decision ---
    dec_path = state_path("decision.json")

    # test-only: decision_override.json があれば strategy_decide を呼ばずに採用する
    override_path = state_path("decision_override.json")
    decision = None
    try:
        if Path(override_path).exists():
            d = read_json(override_path)
            if not isinstance(d, dict):
                stop("decision_override invalid: not a dict")
            if d.get("action") not in ("ENTER", "EXIT", "NOOP", "STOP"):
                stop(f"decision_override invalid action: {d.get('action')}")
            decision = d
            decision.setdefault("reason", "decision_override(test_only)")
        else:
            decision = strategy_decide(market_snapshot)
    except Exception as e:
        stop(f"decision_override read failed ({e})")

# decision は常に state に保存（事後検証の根拠）
    write_json(dec_path, decision)
    log("DECISION", decision)

    log("DECISION_ONLY_CHECK", {
        "decision_only": (market_snapshot.get("decision_only") if isinstance(market_snapshot, dict) else None),
        "keys_has_decision_only": (isinstance(market_snapshot, dict) and ("decision_only" in market_snapshot)),
    })

    # --- decision-only モード（Entry条件検証専用） ---
    # market_snapshot.json に decision_only=true がある場合、
    # DECISIONを書いた時点で安全に終了（EXIT判定・発注・状態更新を一切しない）
    if isinstance(market_snapshot, dict) and market_snapshot.get("decision_only") is True:
        log("STOP", {"reason": "decision_only"})
        return


    # --- runner EXIT override (CAT_v8_01 order: TP/SL -> RSI_EXIT -> TIME_EXIT) ---
    op = read_open_position()
    if isinstance(op, dict) and isinstance(market_snapshot, dict):
        cl = market_snapshot.get("candle_last") or {}
        try:
            ts_now = int(cl.get("ts")) if cl.get("ts") is not None else None
        except Exception:
            ts_now = None

        if ts_now is not None:
            try:
                entry_ts = int(op.get("entry_time"))
            except Exception:
                entry_ts = None

            holding_min = float("nan")
            if entry_ts is not None and ts_now >= entry_ts:
                holding_min = (ts_now - entry_ts) / 60000.0

            side = str(op.get("side", "")).upper()
            tp = float(op.get("tp")) if op.get("tp") is not None else float("nan")
            sl = float(op.get("sl")) if op.get("sl") is not None else float("nan")

            hi = float(cl.get("high")) if cl.get("high") is not None else float("nan")
            lo = float(cl.get("low")) if cl.get("low") is not None else float("nan")
            close = float(cl.get("close")) if cl.get("close") is not None else float("nan")

            exit_reason = None

            # 1) TP
            if side == "LONG":
                if (hi == hi) and (tp == tp) and hi >= tp:
                    exit_reason = "TP利確"
            elif side == "SHORT":
                if (lo == lo) and (tp == tp) and lo <= tp:
                    exit_reason = "TP利確"

            # 2) SL
            if exit_reason is None:
                if side == "LONG":
                    if (close == close) and (sl == sl) and close <= sl:
                        exit_reason = "SL到達"
                elif side == "SHORT":
                    if (close == close) and (sl == sl) and close >= sl:
                        exit_reason = "SL到達"

            # 3) RSI_EXIT
            if exit_reason is None:
                rsi_ctx = market_snapshot.get("rsi_ctx") if isinstance(market_snapshot.get("rsi_ctx"), dict) else {}
                rsi_now = float(rsi_ctx.get("rsi_now", float("nan")))
                rsi_prev = float(rsi_ctx.get("rsi_prev", float("nan")))
                slp_now = float(rsi_ctx.get("slope_now", float("nan")))
                slp_prev = float(rsi_ctx.get("slope_prev", float("nan")))

                # 最短保持（CAT側 key に合わせる：min_hold_for_rsi_exit / min_hold_for_rsi_exit_short）
                base_min_hold = float(params.get("min_hold_for_rsi_exit", 20.0))
                min_hold_short = float(params.get("min_hold_for_rsi_exit_short", base_min_hold))
                min_hold = min_hold_short if side == "SHORT" else base_min_hold

                if (holding_min == holding_min) and (holding_min >= min_hold):
                    if side == "LONG" and int(op.get("entry_priority", 0)) in (1, 3):
                        # CAT正本：基本 44 / -0.18
                        rsi_thresh = float(params.get("rsi_thresh", 44.0))
                        slope_thresh = float(params.get("slope_thresh", -0.18))

                        # CAT正本：p=3 LONG は局所でさらに厳しく（rsi -2, slope -0.02）
                        if int(op.get("entry_priority", 0)) == 3:
                            rsi_thresh -= 2.0
                            slope_thresh -= 0.02

                        cond_now = (rsi_now == rsi_now) and (slp_now == slp_now) and (rsi_now < rsi_thresh) and (slp_now <= slope_thresh)
                        cond_prev = (rsi_prev == rsi_prev) and (slp_prev == slp_prev) and (rsi_prev < rsi_thresh) and (slp_prev <= slope_thresh)
                        if cond_now and cond_prev:
                            exit_reason = "RSI下降Exit(LONG)"

            # 4) TIME_EXIT
            if exit_reason is None:
                # CAT正本：effective_hold_limit_min（down_ctx / P21 / LONG clamp）
                hold_limit_min_base = float(params.get("hold_limit_min", 120.0))
                hold_limit_min_down = float(params.get("hold_limit_min_down", hold_limit_min_base))

                # down_ctx（存在する場合のみ反映：なければFalse）
                is_down_ctx = bool(op.get("is_downtrend_ctx", False) or cl.get("is_downtrend_ctx", False) or market_snapshot.get("is_downtrend_ctx", False))

                effective_hold_limit_min = hold_limit_min_down if is_down_ctx else hold_limit_min_base

                # P21専用（SHORT prio=21）
                if side == "SHORT" and int(op.get("entry_priority", 0)) == 21:
                    p21_max = float(params.get("P21_HOLD_MAX_MIN", 120.0))
                    effective_hold_limit_min = min(effective_hold_limit_min, p21_max)

                # ★追加：adx14 はここで必ず定義（取れなければ nan）
                adx14 = float(_adx14_from_candles_5m(market_snapshot.get("candles_5m") or []))

                # LONG clamp（90 / 75）
                if side == "LONG":
                    effective_hold_limit_min = min(effective_hold_limit_min, float(params.get("HARD_HOLD_MAX_LONG_BASE", 90.0)))

                    # low_trend / bearish が取れる範囲でのみ適用（取れないときはFalse扱い）
                    adx_thresh = float(params.get("ADX_THRESH", 25.0))
                    low_trend = (adx14 == adx14) and (adx14 < adx_thresh)


                    ema20 = market_snapshot.get("ema_20")
                    ema20_prev = market_snapshot.get("ema_20_prev")
                    bearish = False
                    if (ema20 is not None) and (ema20_prev is not None) and (close == close):
                        try:
                            bearish = (float(ema20) - float(ema20_prev) < 0.0) and (close < float(ema20))
                        except Exception:
                            bearish = False

                    if low_trend or bearish:
                        effective_hold_limit_min = min(effective_hold_limit_min, float(params.get("HARD_HOLD_MAX_LONG_BEAR", 75.0)))

                if (holding_min == holding_min) and (holding_min >= effective_hold_limit_min):
                    exit_reason = "TIME_EXIT"

                # CAT正本：LONGは TIME_EXIT確定の瞬間に shallow TP 到達済みなら TP利確に再分類
                if exit_reason == "TIME_EXIT" and side == "LONG":
                    try:
                        entry_price = float(op.get("entry_price"))
                        tp_pct_for_trade = float(op.get("tp_pct"))
                        entry_priority = int(op.get("entry_priority", 0))

                        red_base = float(params.get("LONG_TP_WEAK_REDUCE", 0.85))
                        red = 0.99 if entry_priority == 3 else red_base
                        red = max(0.0, min(red, 0.995))

                        shallow_tp = round(entry_price * (1.0 + tp_pct_for_trade * (1.0 - red)), 10)

                        mh = op.get("max_high")
                        mh = float(mh) if mh is not None else float("nan")

                        tol_param = float(params.get("PRICE_HIT_TOL", 1e-6))
                        tol = max(tol_param, 2e-4)

                        if (mh == mh) and (mh >= shallow_tp * (1.0 - tol)):
                            exit_reason = "TP利確"
                    except Exception:
                        pass
                
                
            if exit_reason is not None:
                # 取引所にポジションが無い場合は、ローカルstate起因のEXIT判定を出さない（Exit検証の混乱防止）
                if pos_n == 0:
                    exit_reason = None
                else:
                    # decision override（runnerがEXITを最優先）
                    decision = {
                        "action": "EXIT",
                        "reason": f"runner_exit:{exit_reason}",
                    }
                    log("EXIT_DECIDED", {
                        "exit_reason": exit_reason,
                        "holding_min": holding_min,
                        "side": side,
                        "tp": tp, "sl": sl,
                        "rsi_ctx": (market_snapshot.get("rsi_ctx") if isinstance(market_snapshot.get("rsi_ctx"), dict) else None),
                    })
                    # write_json(dec_path, decision)  # ← decision.json は L515側で1回だけ保存する（重複防止）
                    # log("DECISION_WRITTEN", {"path": dec_path})  # ← 上行を消すので不要

                # --- decision-only モード（Entry条件検証専用） ---
                # market_snapshot.json に decision_only=true がある場合、
                # DECISIONを書いた時点で安全に終了（発注・TPSL・状態更新を一切しない）
                if market_snapshot.get("decision_only") is True:
                    log("STOP", {"reason": "decision_only"})
                    return

# ====== 修正後（run_once.py：decision確定直後に追加）======
    action = decision.get("action", "STOP")
    # log("DECISION", decision)  # ← DECISION は L516側で1回だけ出す（重複防止）


    # open_position があれば毎回更新（max_high/min_low/last_update_time）
    try:
        op = read_open_position()
        if isinstance(op, dict):
            op = update_open_position_with_candle(op, market_snapshot.get("candle_last"))
            write_open_position(op)
            
    except Exception:
        pass


    # ===== EXIT判定（runner責務） =====
    # NOTE:
    # 531行付近の「runner EXIT override（TP/SL→RSI→TIME）」で decision.json をEXITへ上書きしているため、
    # ここ（旧ロジック）のEXIT判定ログは二重出力になり検証を阻害する。よって無効化する。
    if False:
        # （ここに旧EXIT判定ブロックを丸ごと残す：中身変更なし、インデントだけ+1）
        pass


    params = load_cat_params()   # ← ★これを追加（1行だけ）
    # TP / SL は取引所側で約定するため、runner側では
    # ・RSI_EXIT
    # ・TIME_EXIT
    # のみを判定して action=EXIT を生成する

    # --- RSI_EXIT / TIME_EXIT（重複防止）---
    # runner EXIT override（上のブロック）が正なので、ここは無効化する
    if False:
        op = read_open_position()
        if isinstance(op, dict):
            now_ts = int((market_snapshot.get("candle_last") or {}).get("ts") or 0)
            entry_ts = int(op.get("entry_time") or 0)
            holding_min = (now_ts - entry_ts) / 60000 if now_ts and entry_ts else 0.0

            side = str(op.get("side", "")).upper()

            # --- RSI EXIT（最小構成：数値はCAT_v8_01と同値を使用）---
            rsi_val = market_snapshot.get("rsi")
            rsi_slope = market_snapshot.get("rsi_slope")

            if (
                rsi_val is not None
                and rsi_slope is not None
                and rsi_val < float(params.get("rsi_thresh", 46)
    )
                and rsi_slope <= float(params.get("slope_thresh", -0.17))
            ):
                log("EXIT_DECIDED", {"reason": "RSI_EXIT", "rsi": rsi_val, "rsi_slope": rsi_slope})
                action = "EXIT"

            # --- TIME EXIT ---
            hold_limit = float(params.get("hold_limit_min", 120))
            if holding_min >= hold_limit:
                log("EXIT_DECIDED", {"reason": "TIME_EXIT", "holding_min": holding_min})
                action = "EXIT"



    ALLOW_LIVE_ORDERS = False  # 本番許可はここを True にするまで絶対に実弾に行かない


    # demo/paper は keys.json のフラグでのみ許可する（本番は従来通り STOP）
    raw = json.loads(Path("config/bitget_keys.json").read_text(encoding="utf-8"))
    paper_trading = bool(raw.get("paper_trading", False))
    allow_paper_orders = bool(raw.get("allow_paper_orders", False))

    if action in ("ENTER", "EXIT"):
        if paper_trading:
            if not allow_paper_orders:
                stop(f"safety_guard: paper orders disabled (action={action})")
        else:
            if not ALLOW_LIVE_ORDERS:
                stop(f"safety_guard: live orders disabled (action={action})")


    # --- ACTION ---
    if action == "NOOP":
        # posがある場合：このrunでは「新規エントリーなし」なだけで、ポジは保有中（正常）
        # ここを NOOP とすると「ポジあるのに終了？」の混乱になるため、結果ラベルを分ける
        if pos_n != 0:
            log("END", {"result": "HOLDING"})
            return
        log("END", {"result": "NOOP"})
        return


    if action == "STOP":
        stop(decision.get("reason", "strategy STOP"))

    if action == "ENTER":
        # 必須項目チェック（不足はSTOP）
        # 合意：decision は「判断のみ」→ TP/SL/サイズは runner 側
        need = ["side"]
        for k in need:
            if k not in decision:
                stop(f"ENTER missing field: {k}")

        side = decision["side"]  # LONG/SHORT

        # --- CAT params（本番・デモ共通の入力） ---
        params = load_cat_params()
        pos_size_btc = float(params.get("POSITION_SIZE_BTC", 0.0))
        if not (pos_size_btc > 0.0):
            stop("cat_params: POSITION_SIZE_BTC must be > 0")
        size = str(pos_size_btc)  # Bitget注文サイズ（BTC）

        # Bitget用のside/holdSide
        open_side = "buy" if side == "LONG" else "sell"
        hold_side = "long" if side == "LONG" else "short"

        coid = "CAT_" + uuid.uuid4().hex[:16]
        # safety: multi-position は最終的に対応するが、現時点では未対応
        # Exit検証のため pos!=0 でも run は進めるが、新規ENTRYは増やさない
        if pos_n != 0:
            log("ENTRY_GUARD_NOOP", {"reason": "pos!=0 (multi-position not enabled)", "pos_n": pos_n})
            log("END", {"result": "ENTRY_SKIPPED_POS_EXISTS"})
            return
            action = "NOOP"

        if action == "ENTER":
            log("ENTRY_SEND", {"clientOid": coid, "side": side, "size": size})

        adp.place_market_order(
            symbol=SYMBOL,
            product_type=PRODUCT_TYPE,
            margin_mode=MARGIN_MODE,
            margin_coin=MARGIN_COIN,
            size=size,
            side=open_side,
            trade_side="open",
            client_oid=coid,
        )
        log("ENTRY_OK")

        entry = adp.wait_open_price_avg(
            product_type=PRODUCT_TYPE,
            margin_coin=MARGIN_COIN,
        )

        # ===== CAT_v8_01準拠：TP/SL入力生成（損益に効く部分のみ） =====
        entry_priority = int(decision.get("entry_priority", -1))
        close_px = float((market_snapshot.get("candle_last") or {}).get("close", float("nan")))

        candles_5m = market_snapshot.get("candles_5m") or []
        adx14 = _adx14_from_candles_5m(candles_5m)  # 取れなければnan

        pos_size = float(size)  # 実注文size（BTC）

        # 既定（LONG）
        tp_pct = float(params.get("tp_pct", 0.001))
        sl_pct_default = float(params.get("sl_pct", 0.001))
        sl_usd = float(entry) * sl_pct_default * pos_size  # CAT正本：entry基準（entry * sl_pct * pos_size）

        # SHORT（CAT: SHORT_TP_PCT=0.0010, SHORT_SL_PCT=0.0005）
        if str(side).upper() == "SHORT":
            tp_pct = float(params.get("SHORT_TP_PCT", 0.0010))
            sl_usd = float(entry) * float(params.get("SHORT_SL_PCT", 0.0005)) * pos_size  # CAT正本：entry基準

        # P4（LONGのみ）：ADX帯でTP_USD=3 or 5、SL_USD=5（CAT既定）
        if str(side).upper() == "LONG" and entry_priority == 4:
            tp_usd = float(params.get("P4_TP_USD", 3.0))
            if (adx14 == adx14) and 20.0 <= adx14 < 25.0:
                tp_usd = float(params.get("P4_TP_USD_MID", 5.0))
            sl_usd = float(params.get("P4_SL_USD", 5.0))
            entry_px = float(entry)
            if entry_px > 0.0 and pos_size > 0.0:
                tp_pct = (tp_usd / pos_size) / entry_px

        tp, sl = _calc_tp_sl(
            float(entry),
            side=side,
            pos_size=pos_size,
            tp_pct=tp_pct,
            sl_usd=sl_usd,
        )

        # Bitget: 送信直前に1回だけ pricePlace へ丸める（CAT側のround(...,10)は保持）
        price_place = int((market_snapshot.get("contracts_btcusdt") or {}).get("pricePlace", 1))
        tp = round(float(tp), price_place)
        sl = round(float(sl), price_place)

        log("TPSL_CTX", {
            "entry_priority": entry_priority,
            "side": side,
            "entry": float(entry),
            "close": close_px,
            "adx14": adx14,
            "tp_pct": tp_pct,
            "sl_usd": sl_usd,
            "pricePlace": price_place,
        })
        log("TPSL_SEND", {"tp": tp, "sl": sl, "entry": float(entry), "side": side, "size": size, "pricePlace": price_place})

        r = adp.api.placePosTpsl({
            "marginCoin": MARGIN_COIN,
            "productType": PRODUCT_TYPE,
            "symbol": SYMBOL,
            "holdSide": hold_side,
            "stopSurplusTriggerPrice": str(tp),
            "stopSurplusTriggerType": "mark_price",
            "stopSurplusExecutePrice": str(tp),
            "stopLossTriggerPrice": str(sl),
            "stopLossTriggerType": "mark_price",
            "stopLossExecutePrice": str(sl),
        })
        log("TPSL_RESP", {"resp": r})  # ★追加：成功レスポンスID検出のため
        if r.get("code") != "00000":
            stop("TPSL attach failed")
        log("TPSL_OK")


# ====== 修正後（run_once.py：ENTER 成功時に open_position を保存）======
        if len(adp.get_pending_profit_loss(PRODUCT_TYPE, SYMBOL)) == 0:
            stop("TPSL verify failed")
        log("PENDING_VERIFY_OK")

        # open_position 保存（CATの entry_dict 相当：損益/Exitに効く最小）
        try:
            cl = market_snapshot.get("candle_last") or {}
            entry_time = cl.get("ts")
            op: Dict[str, Any] = {
                "entry_time": entry_time,
                "entry_price": float(entry),
                "side": side,
                "entry_priority": int(entry_priority),
                "entry_condition": str(decision.get("entry_condition", f"entry_priority={int(entry_priority)}")),
                "tp_pct": float(tp_pct),
                "sl_usd": float(sl_usd),
                "tp": float(tp),
                "sl": float(sl),
                "pricePlace": int(price_place),
                "last_update_time": entry_time,
            }
            if str(side).upper() == "LONG":
                try:
                    op["max_high"] = float(cl.get("high")) if cl.get("high") is not None else None
                except Exception:
                    op["max_high"] = None
            if str(side).upper() == "SHORT":
                try:
                    op["min_low"] = float(cl.get("low")) if cl.get("low") is not None else None
                except Exception:
                    op["min_low"] = None

            write_open_position(op)
            log("OPEN_POSITION_UPDATED", {"last_update_time": op.get("last_update_time"), "max_high": op.get("max_high"), "min_low": op.get("min_low")})
            log("OPEN_POSITION_SAVED", {"path": _open_position_path()})
        except Exception as e:
            log("OPEN_POSITION_SAVE_FAILED", {"err": repr(e), "path": _open_position_path()})


        log("END", {"result": "ENTER_DONE"})
        return


    if action == "EXIT":
        # --- CLOSE (safe) ---
        # 現在ポジションを取得（決済は runner が 100% 管理）

        # --- EXIT guard: no position -> skip exit logic (normal end) ---
        if pos_n == 0:
            log("END", {"result": "NO_POSITION"})
            return

        pos = adp.get_single_position(product_type=PRODUCT_TYPE, margin_coin=MARGIN_COIN, symbol=SYMBOL)

        # --- EXIT guard: no position on exchange -> backup local state and end ---
        if pos is None:
            try:
                import shutil
                sp = Path("state/open_position.json")
                if sp.exists():
                    bp = Path("state/backups")
                    bp.mkdir(parents=True, exist_ok=True)
                    dst = bp / f"open_position.no_position.{run_id}.json"
                    shutil.copy2(sp, dst)
                    log("STATE_BACKUP", {"path": str(dst)})
            except Exception as e:
                log("STATE_BACKUP_FAIL", {"error": str(e)})
            log("END", {"result": "NO_POSITION"})
            return

        hold_side = pos.get("holdSide")  # "long" / "short"

        if hold_side not in ("long", "short"):
            stop("invalid holdSide for close")

        # CLOSE size（取引所の現在ポジから決済数量を確定）
        try:
            pos_size_btc = float(pos.get("total") or pos.get("available") or 0.0)
        except Exception:
            pos_size_btc = 0.0
        if not (pos_size_btc > 0.0):
            stop(f"invalid close size (total/available): {pos.get('total')}/{pos.get('available')}")

        # 逆サイドで決済
        if hold_side == "long":
            side_close = "buy"
        else:
            side_close = "sell"

        coid = "CAT_CLOSE_" + uuid.uuid4().hex[:12]
        payload = {
            "symbol": SYMBOL,
            "productType": PRODUCT_TYPE,
            "marginCoin": MARGIN_COIN,
            "tradeSide": "close",
            "side": side_close,
            "holdSide": hold_side,
            "size": str(pos_size_btc),
            "clientOid": coid,
        }

        log("CLOSE_SEND", payload)


        # CLOSE直前に再照会（TP/SL等で消えていたらNO_POSITIONで正常終了）
        try:
            ps2 = adp.get_positions(PRODUCT_TYPE, MARGIN_COIN)
            if not ps2:
                log("END", {"result": "NO_POSITION"})
                return
        except Exception:
            # ここで落とすと検証が止まるので、そのまま close を試す
            pass

        try:
            adp.close_market_order(
                symbol=SYMBOL,
                product_type=PRODUCT_TYPE,
                margin_mode="isolated",
                margin_coin=MARGIN_COIN,
                size=payload["size"],
                side=payload["side"],
                hold_side=payload["holdSide"],
                client_oid=payload["clientOid"],
            )

        except Exception as e:
            # Bitgetが「平仓できる建玉なし」を返すケースは NO_POSITION として扱う（混乱防止）
            if "code=22002" in str(e):
                log("END", {"result": "NO_POSITION"})
                return
            raise

        log("CLOSE_OK")


        try:
            delete_open_position()
        except Exception:
            pass

        log("END", {"result": "EXIT_DONE"})
        return


    stop(f"unknown action: {action}")


if __name__ == "__main__":
    main()
