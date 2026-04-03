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
PENDING_TTL_BARS = 3
CANDLE_WARMUP   = 200   # 指標計算に必要な最小バー数（live engine と同値）
_PARAMS_PATH    = _ROOT / "config" / "cat_params_v9.json"
_RESULTS_DIR    = _ROOT / "results"
_JST            = timezone(timedelta(hours=9))
_LONG_PRIORITIES  = (2, 4)
_SHORT_PRIORITIES = (22, 23, 24)


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
def _calc_tp_price(side: str, entry_price: float, adx: float, params: Dict) -> float:
    base     = float(params[f"{side}_TP_PCT"])
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
def _calc_sl_price(side: str, entry_price: float, params: Dict) -> float:
    sl_pct = float(params[f"{side}_SL_PCT"])
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

    # 1. BREAKOUT_CUT (P22/P23 SHORT, add==3)
    if side == "SHORT" and priority in (22, 23) and add_count == 3:
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

    # 4. RSI_REVERSE_EXIT (SHORT)
    if side == "SHORT" and bool(params.get("FEAT_SHORT_RSI_REVERSE_EXIT", False)):
        rsi_v = _col("rsi_short"); rsi_sl = _col("rsi_slope_short"); adx_v = _col("adx")
        if (hold_min >= float(params.get("SHORT_MIN_HOLD_FOR_RSI_EXIT", 1))
                and not math.isnan(rsi_v)  and rsi_v  < float(params.get("SHORT_RSI_THRESH", 50))
                and not math.isnan(rsi_sl) and rsi_sl > float(params.get("SHORT_RSI_SLOPE_MAX", 0.0))
                and not math.isnan(adx_v)  and adx_v  < float(params.get("SHORT_RSI_EXIT_ADX_MAX", 12))):
            return "RSI_REVERSE_EXIT"

    # 5. MAE_CUT (P23 SHORT, add>=4, hold>=300min)
    if side == "SHORT" and priority == 23 and add_count >= 4 and hold_min >= 300:
        _mae_cap = entry_p + (50.0 / size_btc)
        if mark_price >= _mae_cap:
            return "MAE_CUT"

    # 5b. MAE_CUT (P2 LONG, add>=4, hold>=300min)
    if side == "LONG" and priority == 2 and add_count >= 4 and hold_min >= 300:
        _mae_cap_long = entry_p - (50.0 / size_btc)
        if mark_price <= _mae_cap_long:
            return "MAE_CUT"

    # 5c. MIDTERM_CUT (P4 LONG, add>=2, hold>=90min)
    if side == "LONG" and priority == 4 and add_count >= 2:
        if hold_min >= float(params.get("LONG_MIDTERM_HOLD_MIN", 90.0)):
            if unreal < float(params.get("LONG_MIDTERM_PNL_USD", -30.0)):
                return "MIDTERM_CUT"

    # 6. PROFIT_LOCK
    if side == "LONG" and int(params.get("LONG_PROFIT_LOCK_ENABLE", 0)):
        if (mfe_usd >= float(params.get("LONG_PROFIT_LOCK_ARM_USD", 15.0))
                and unreal < float(params.get("LONG_PROFIT_LOCK_USD", 6.0))):
            return "PROFIT_LOCK"
    if side == "SHORT" and priority == 22 and int(params.get("P22_SHORT_PROFIT_LOCK_ENABLE", 0)):
        if (mfe_usd >= float(params.get("P22_SHORT_PROFIT_LOCK_ARM_USD", 22.0))
                and unreal < float(params.get("P22_SHORT_PROFIT_LOCK_USD", 8.0))):
            return "PROFIT_LOCK"
    # 6a. P23 SHORT PROFIT_LOCK V2
    if side == "SHORT" and priority == 23 and int(params.get("P23_SHORT_PROFIT_LOCK_ENABLE", 1)):
        _arm  = float(params.get("P23_SHORT_PROFIT_LOCK_ARM_USD", 15.0))
        _lock = float(params.get("P23_SHORT_PROFIT_LOCK_USD", 5.0))
        if mfe_usd >= _arm:
            _lock_price = entry_p - (_lock / size_btc)
            if mark_price >= _lock_price:
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
    base_t = float(params.get("P2_TIME_EXIT_MIN" if priority == 2 else
                              f"{side}_TIME_EXIT_MIN", 150 if side == "LONG" else 480))
    down_f = float(params.get(f"{side}_TIME_EXIT_DOWN_FACTOR", 0.75))
    if hold_min >= base_t * (down_f if unreal < 0 else 1.0):
        return "TIME_EXIT"

    return None


# ==============================================================
# ユーティリティ
# ==============================================================
def _ts_to_str(ts_ms: int) -> str:
    dt = datetime.fromtimestamp(ts_ms / 1000, tz=_JST)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


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
    fee   = size_b * exit_price * maker * 2
    net   = gross - fee

    trades.append({
        "entry_time":            _ts_to_str(entry_ms),
        "exit_time":             _ts_to_str(exit_ts_ms),
        "side":                  side,
        "priority":              priority,
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
    })


def _write_results(csv_path: str, trades: List) -> None:
    _RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stem     = pathlib.Path(csv_path).stem
    out_path = _RESULTS_DIR / f"replay_{stem}.csv"
    fields   = ["entry_time", "exit_time", "side", "priority", "add_count",
                 "size_btc", "entry_price", "exit_price", "exit_reason",
                 "hold_min", "gross_usd", "fee_usd", "net_usd",
                 "adx_at_entry", "bb_mid_slope_at_entry", "rsi_at_entry"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(trades)
    print(f"\n[replay_csv] → {out_path}  ({len(trades)} trades)")


def _print_summary(trades: List) -> None:
    if not trades:
        print("[replay_csv] No trades.")
        return

    total_net   = sum(t["net_usd"]   for t in trades)
    total_gross = sum(t["gross_usd"] for t in trades)
    total_fee   = sum(t["fee_usd"]   for t in trades)
    hold_mins   = [t["hold_min"] for t in trades]

    print(f"\n{'='*52}")
    print(f"  総トレード数:   {len(trades)}")
    print(f"  NET合計:        ${total_net:+.2f}")
    print(f"  GROSS合計:      ${total_gross:+.2f}")
    print(f"  手数料合計:     ${total_fee:.2f}")
    print(f"  平均保持時間:   {sum(hold_mins)/len(hold_mins):.1f}min")
    print(f"{'='*52}")

    by_reason = defaultdict(lambda: {"count": 0, "net": 0.0})
    for t in trades:
        by_reason[t["exit_reason"]]["count"] += 1
        by_reason[t["exit_reason"]]["net"]   += t["net_usd"]
    print("\n  Exit理由別:")
    for reason, v in sorted(by_reason.items(), key=lambda x: -abs(x[1]["net"])):
        print(f"    {reason:<28} {v['count']:3}件  net ${v['net']:+8.2f}")

    by_pri = defaultdict(lambda: {"count": 0, "net": 0.0})
    for t in trades:
        k = f"P{t['priority']}-{t['side']}"
        by_pri[k]["count"] += 1
        by_pri[k]["net"]   += t["net_usd"]
    print("\n  Priority別:")
    for pri, v in sorted(by_pri.items()):
        print(f"    {pri:<12} {v['count']:3}件  net ${v['net']:+8.2f}")
    print(f"{'='*52}\n")


# ==============================================================
# メインループ
# ==============================================================
def main(csv_path: str) -> None:
    params = _load_params()
    df_raw = _load_csv(csv_path)
    print(f"[replay_csv] loaded {len(df_raw)} bars from {csv_path}")

    # preprocess（全バー一括で指標計算）
    df_for_prep = df_raw[["timestamp_ms", "open", "high", "low", "close"]].copy()
    df_for_prep["timestamp"] = pd.to_datetime(df_for_prep["timestamp_ms"], unit="ms")
    if "volume" in df_raw.columns:
        df_for_prep["volume"] = df_raw["volume"].values
    else:
        df_for_prep["volume"] = 0.0

    try:
        df = preprocess(df_for_prep[["timestamp", "open", "high", "low", "close", "volume"]].copy(), params)
        df["timestamp_ms"] = df_raw["timestamp_ms"].values
        df["high_raw"] = df_raw["high"].values
        df["low_raw"]  = df_raw["low"].values
    except Exception as e:
        print(f"[ERROR] preprocess failed: {e}")
        return

    # 状態変数（in-memory）
    pos:     Dict[str, Optional[Dict]] = {"LONG": None, "SHORT": None}
    pending: Dict[str, Optional[Dict]] = {"LONG": None, "SHORT": None}
    trades:  List[Dict]                = []

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
            bar_elapsed = max(0, (ts_ms - placed_ms) // (5 * 60 * 1000))

            # TTL 切れ → キャンセル
            if bar_elapsed >= PENDING_TTL_BARS:
                pending[side] = None
                continue

            # fill 判定（intra-bar: LONG=low, SHORT=high）
            limit_p = float(pnd["limit_price"])
            filled  = (side == "LONG" and low_p <= limit_p) or \
                      (side == "SHORT" and high_p >= limit_p)
            if not filled:
                continue

            # 約定処理
            fill_p    = limit_p  # post-only なので limit_price で約定
            adx_val   = float(pnd.get("adx_at_entry", 0.0))
            unit_size = float(params[f"{side}_POSITION_SIZE_BTC"])

            if pos[side] is None:
                # 新規エントリー
                tp_price = _calc_tp_price(side, fill_p, adx_val, params)
                pos[side] = {
                    "side":                  side,
                    "entry_priority":        pnd["priority"],
                    "entry_price":           fill_p,
                    "entry_time":            ts_ms,
                    "add_count":             1,
                    "size_btc":              unit_size,
                    "tp_price":              tp_price,
                    "sl_price":              None,  # add_count=1 は SL 不要
                    "mfe_usd":               0.0,
                    "adx_at_entry":          pnd.get("adx_at_entry", 0.0),
                    "bb_mid_slope_at_entry": pnd.get("bb_mid_slope_at_entry", float("nan")),
                    "rsi_at_entry":          pnd.get("rsi_at_entry", float("nan")),
                }
            else:
                # ADD
                p       = pos[side]
                old_sz  = float(p["size_btc"])
                old_p   = float(p["entry_price"])
                new_sz  = old_sz + unit_size
                new_avg = (old_p * old_sz + fill_p * unit_size) / new_sz
                new_cnt = int(p["add_count"]) + 1
                tp_price = _calc_tp_price(side, new_avg, adx_val, params)
                sl_price = _calc_sl_price(side, new_avg, params) if new_cnt >= 2 else None
                p.update({
                    "entry_price": new_avg,
                    "add_count":   new_cnt,
                    "size_btc":    new_sz,
                    "tp_price":    tp_price,
                    "sl_price":    sl_price,
                })

            pending[side] = None

        # --------------------------------------------------
        # 2. MFE 更新（exit チェック前に必ず更新）
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

        # --------------------------------------------------
        # 3. TP 発動チェック（close が TP 価格を超えたか）
        # --------------------------------------------------
        for side in ("LONG", "SHORT"):
            p = pos[side]
            if p is None:
                continue
            tp = float(p["tp_price"])
            tp_hit = (side == "LONG" and close_p >= tp) or \
                     (side == "SHORT" and close_p <= tp)
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
            sl_hit = (side == "LONG" and close_p <= sl) or \
                     (side == "SHORT" and close_p >= sl)
            if sl_hit:
                _record_trade(trades, p, exit_price=sl, exit_reason="SL_FILLED",
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
        try:
            priority = check_entry_priority(i, df, params)
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
            max_adds = int(params.get("MAX_ADDS_BY_PRIORITY", {}).get(
                str(pos_pri), params.get(f"{side}_MAX_ADDS", 5)))
            if add_cnt >= max_adds:
                continue

        # 指値計算（run_once_v9 と同じ係数）
        if side == "LONG":
            lp = float(Decimal(str(close_p)) * Decimal("0.9999"))
        else:
            lp = float(Decimal(str(close_p)) * Decimal("1.0001"))

        adx_val   = float(df.at[i, "adx"])          if "adx"          in df.columns else 0.0
        slope_val = float(df.at[i, "bb_mid_slope"]) if "bb_mid_slope" in df.columns else float("nan")
        rsi_val   = float(df.at[i, "rsi_short"])    if "rsi_short"    in df.columns else float("nan")
        pending[side] = {
            "side":                  side,
            "priority":              priority,
            "limit_price":           lp,
            "placed_bar_ms":         ts_ms,
            "adx_at_entry":          adx_val,
            "bb_mid_slope_at_entry": slope_val,
            "rsi_at_entry":          rsi_val,
        }

    # ---- 未クローズポジションを強制クローズ（期間末） ----
    last_ts    = int(df.iloc[-1]["timestamp_ms"])
    last_close = float(df.iloc[-1]["close"])
    for side in ("LONG", "SHORT"):
        if pos[side] is not None:
            _record_trade(trades, pos[side], exit_price=last_close,
                          exit_reason="FORCE_CLOSE_EOD", exit_ts_ms=last_ts, params=params)

    # ---- 出力 ----
    _write_results(csv_path, trades)
    _print_summary(trades)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} /path/to/BTCUSDT-5m-*.csv")
        sys.exit(1)
    main(sys.argv[1])
