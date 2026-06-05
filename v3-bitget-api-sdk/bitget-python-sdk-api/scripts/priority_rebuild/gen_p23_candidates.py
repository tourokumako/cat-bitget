"""
gen_p23_candidates.py — P23 候補生成 + V9前向きシミュレーション（ratchet E6 土台）

目的（まこさん合意 2026-06-05）:
  P23 の「型」(stochデッドクロス+陰線) が出た場面を **数字の閾値を外して全部** 拾い、
  各候補を1つずつ「もしここで売ったら、買い増し(add)と出口は **V9のまま** で最後いくらか」を
  独立に前向きシミュレーションして net ラベルを付ける。→ AI が「儲かる場面の見分け方」を学ぶ土台。

設計の肝（E5/E4 の失敗を直す）:
  - 最初に入るか = ML 化対象（候補を型だけで広げる）
  - 買い増し(add) = **V9のまま**（add は check_entry_priority フル閾値で発火・大勝ちの源を壊さない）
  - 出口 = **V9のまま**（_check_exits_replay / TP / SL を import して呼ぶ・改造ゼロ）

V9本体は一切変更しない。replay_csv.py / cat_v9_decider.py / cat_params_v9.json は **import のみ**。
run() のバーごと処理順 (L1107-1387) を SHORT 単独ポジション用に忠実に移植し、
**自己検査**（continuous モードが本物の replay_csv.run() と完全一致するか assert）を通してから
独立モードの候補ラベルを出力する。一致しなければ即停止＝偽の数字を出さない（H13/関所A 思想）。

§4.6: H2(leak=特徴量はentry時点のみ/netは教師ラベル/期間分割は学習側で) / H6(atr→pct化は学習側) /
       H13(V9・score.py 改造なし・import) / H1H9(size=V9の P23_POSITION_SIZE_BTC=0.024 固定)
出力: results/priority_rebuild/ratchet/p23_candidates_{full,typeonly}.csv（score.py に通せる列 + 特徴量）
"""
from __future__ import annotations
import sys, pathlib, math
from decimal import Decimal
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runner"))

import replay_csv as rc                                   # V9 リプレイエンジン（import のみ・改造しない）
from strategies.cat_v9_decider import check_entry_priority  # V9 entry/add 判定（import のみ）

OHLCV_CSV = ROOT / "data" / "BTCUSDT-5m-2021-04-01_03-31_1826d_V9FULL_safe.csv"
OUT_DIR   = ROOT / "results" / "priority_rebuild" / "ratchet"
PRIORITY  = 23

# 入口時点の特徴量として trade に残す列（E5 と同じ顔ぶれ・MTF と pct 化は学習スクリプト側）
FEAT_KEYS = ["adx_at_entry", "bb_mid_slope_at_entry", "rsi_at_entry", "rsi_slope_at_entry",
             "stoch_k_at_entry", "stoch_d_at_entry", "bb_width_at_entry",
             "ret_5", "atr_14", "entry_hour", "entry_weekday"]


def _log(m): print(m, flush=True)


def _p23_type_fires(df: pd.DataFrame, i: int) -> bool:
    """P23 の『型』のみ（数字の閾値を外す）= stochデッドクロス + 陰線 + gap>0.3（gap はコード直書きで残る）。
    cat_v9_decider.check_entry_priority の P23 ブロック(L469-484)から ADX/ATR/bb_slope/high_adx を除いたもの。"""
    if i < 2:
        return False
    k2, d2 = df.at[i-2, "stoch_k"], df.at[i-2, "stoch_d"]
    k1, d1 = df.at[i-1, "stoch_k"], df.at[i-1, "stoch_d"]
    k0, d0 = df.at[i,   "stoch_k"], df.at[i,   "stoch_d"]
    o0, c0 = df.at[i, "open"],     df.at[i, "close"]
    if any(pd.isna(x) for x in (k2, d2, k1, d1, k0, d0, o0, c0)):
        return False
    return (k2 > d2) and (k1 > d1) and (k0 < d0) and ((d0 - k0) > 0.3) and (c0 <= o0)


# ----------------------------------------------------------------------
# 1ポジション分のバー処理（run() L1115-1377 を SHORT 単独に忠実移植）
# state = {"pos":dict|None, "pending":dict|None, "trades":list}
# initial_fn(i) が True を返すバーで（pos も pending も無ければ）新規 SHORT pending を置く。
# add は常に check_entry_priority(i)==23（フル閾値）で発火＝V9のまま。
# ----------------------------------------------------------------------
def _step(state, df, bar_ms, i, params, initial_fn):
    pos, pending, trades = state["pos"], state["pending"], state["trades"]
    ts_ms   = int(df.at[i, "timestamp_ms"])
    close_p = float(df.at[i, "close"])
    high_p  = float(df.at[i, "high_raw"])
    low_p   = float(df.at[i, "low_raw"])
    mark_p  = close_p
    side = "SHORT"

    # 1. pending fill（SHORT: high>=limit）
    if pending is not None:
        if max(0, (ts_ms - int(pending["placed_bar_ms"])) // bar_ms) >= rc.PENDING_TTL_BARS:
            pending = None
        elif high_p >= float(pending["limit_price"]):
            fill_p   = float(pending["limit_price"])
            adx_val  = float(pending.get("adx_at_entry", 0.0))
            unit_size = float(params.get(f"P{PRIORITY}_POSITION_SIZE_BTC", params["SHORT_POSITION_SIZE_BTC"]))
            states   = rc._calc_entry_states(df, i, ts_ms)
            if pos is None:
                pos = {
                    "side": side, "entry_priority": PRIORITY, "entry_price": fill_p,
                    "entry_time": ts_ms, "add_count": 1, "size_btc": unit_size,
                    "tp_price": rc._calc_tp_price(side, fill_p, adx_val, params, PRIORITY, atr_14=states.get("atr_14", float("nan"))),
                    "sl_price": rc._calc_sl_price(side, fill_p, params, PRIORITY),
                    "regime": "", "mfe_usd": 0.0, "mae_usd": 0.0,
                    "max_high": float("-inf"), "min_low": float("inf"),
                    "adx_at_entry": pending.get("adx_at_entry", 0.0),
                    "bb_mid_slope_at_entry": pending.get("bb_mid_slope_at_entry", float("nan")),
                    "rsi_at_entry": pending.get("rsi_at_entry", float("nan")),
                    "rsi_slope_at_entry": pending.get("rsi_slope_at_entry", float("nan")),
                    "stoch_k_at_entry": pending.get("stoch_k_at_entry", float("nan")),
                    "stoch_d_at_entry": pending.get("stoch_d_at_entry", float("nan")),
                    "bb_width_at_entry": pending.get("bb_width_at_entry", float("nan")),
                    "ret_5": states["ret_5"], "atr_14": states["atr_14"],
                    "entry_hour": states["entry_hour"], "entry_weekday": states["entry_weekday"],
                    "mfe_peak_pct": 0.0, "trail_stop_price": None,
                }
            else:                                            # ADD（run() L1194-1210）
                old_sz, old_p = float(pos["size_btc"]), float(pos["entry_price"])
                new_sz  = old_sz + unit_size
                new_avg = (old_p * old_sz + fill_p * unit_size) / new_sz
                new_cnt = int(pos["add_count"]) + 1
                pos.update({
                    "entry_price": new_avg, "add_count": new_cnt, "size_btc": new_sz,
                    "tp_price": rc._calc_tp_price(side, new_avg, adx_val, params, PRIORITY, atr_14=states.get("atr_14", float("nan"))),
                    "sl_price": rc._calc_sl_price(side, new_avg, params, PRIORITY) if new_cnt >= 2 else None,
                })
            pending = None

    closed = False
    # 2. MFE/MAE/極値（run() L1217-1234・P23 は trail peak 対象外）
    if pos is not None:
        entry_p, size_b = float(pos["entry_price"]), float(pos["size_btc"])
        unreal = (entry_p - mark_p) * size_b
        if unreal > float(pos.get("mfe_usd", 0.0)): pos["mfe_usd"] = unreal
        if unreal < float(pos.get("mae_usd", 0.0)): pos["mae_usd"] = unreal
        if low_p < float(pos.get("min_low", float("inf"))): pos["min_low"] = low_p

    # 3. TP（SHORT: low<=tp）
    if pos is not None and low_p <= float(pos["tp_price"]):
        rc._record_trade(trades, pos, exit_price=float(pos["tp_price"]), exit_reason="TP_FILLED", exit_ts_ms=ts_ms, params=params)
        pos = None; closed = True
    # 4. SL（SHORT: high>=sl）
    if pos is not None and pos.get("sl_price") is not None and high_p >= float(pos["sl_price"]):
        rc._record_trade(trades, pos, exit_price=float(pos["sl_price"]), exit_reason="SL_FILLED", exit_ts_ms=ts_ms, params=params)
        pos = None; closed = True
    # 5. TRAIL は P1/P21 専用 → P23 は無し
    # 6. _check_exits_replay（TP/SL 以外の V9 出口 12種）
    if pos is not None:
        reason = rc._check_exits_replay(pos, mark_p, df, i, params, ts_ms)
        if reason:
            rc._record_trade(trades, pos, exit_price=mark_p, exit_reason=reason, exit_ts_ms=ts_ms, params=params)
            pos = None; closed = True

    # 7. エントリー / ADD 判断（run() L1316-1377・SHORT 単独）
    fire_add = (check_entry_priority(i, df, params) == PRIORITY)   # add は常にフル閾値（V9のまま）
    want_initial = (pos is None and pending is None and initial_fn(i))
    if (fire_add and pos is not None) or want_initial:
        if pos is not None:                                       # ADD 上限
            if int(pos["add_count"]) >= int(params.get("MAX_ADDS_BY_PRIORITY", {}).get(str(PRIORITY), 5)):
                pass
            elif pending is None:
                pending = _mk_pending(df, i, close_p)
        elif pending is None:
            pending = _mk_pending(df, i, close_p)

    state["pos"], state["pending"] = pos, pending
    return closed


def _mk_pending(df, i, close_p):
    lp = float(Decimal(str(close_p)) * Decimal("1.0001"))        # SHORT maker 指値 +0.01%
    g = lambda col: float(df.at[i, col]) if col in df.columns and pd.notna(df.at[i, col]) else float("nan")
    return {"side": "SHORT", "priority": PRIORITY, "limit_price": lp, "placed_bar_ms": int(df.at[i, "timestamp_ms"]),
            "adx_at_entry": g("adx"), "bb_mid_slope_at_entry": g("bb_mid_slope"),
            "rsi_at_entry": g("rsi_short"), "rsi_slope_at_entry": g("rsi_slope_short"),
            "stoch_k_at_entry": g("stoch_k"), "stoch_d_at_entry": g("stoch_d"), "bb_width_at_entry": g("bb_width")}


def simulate_independent(df, bar_ms, signal_i, params):
    """候補 signal_i を単独で前向きシミュレーション → 1 trade（fill しなければ None）。add はV9フル閾値。"""
    state = {"pos": None, "pending": _mk_pending(df, signal_i, float(df.at[signal_i, "close"])), "trades": []}
    only_this = lambda i: False                                  # 新規 initial はこの候補のみ（既に pending 済）
    for i in range(signal_i + 1, len(df)):
        if _step(state, df, bar_ms, i, params, only_this):
            return state["trades"][-1]
        if state["pos"] is None and state["pending"] is None:    # 不約定 or クローズ済で次が無い
            return state["trades"][-1] if state["trades"] else None
    if state["pos"] is not None:                                 # 期間末強制クローズ
        rc._record_trade(state["trades"], state["pos"], exit_price=float(df.iloc[-1]["close"]),
                         exit_reason="FORCE_CLOSE_EOD", exit_ts_ms=int(df.iloc[-1]["timestamp_ms"]), params=params)
    return state["trades"][-1] if state["trades"] else None


def run_continuous(df, bar_ms, params, initial_fn):
    """連続モード（run() と同じ：閉じたら次を開く）= 自己検査用。"""
    state = {"pos": None, "pending": None, "trades": []}
    for i in range(rc.CANDLE_WARMUP, len(df)):
        _step(state, df, bar_ms, i, params, initial_fn)
    if state["pos"] is not None:
        rc._record_trade(state["trades"], state["pos"], exit_price=float(df.iloc[-1]["close"]),
                         exit_reason="FORCE_CLOSE_EOD", exit_ts_ms=int(df.iloc[-1]["timestamp_ms"]), params=params)
    return state["trades"]


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    params = rc._load_params()
    # P23 のみ有効・他 Priority 無効（V9 フル閾値はそのまま）
    p23 = dict(params)
    for k in list(p23):
        if k.startswith("ENABLE_P") and k.endswith(("_LONG", "_SHORT")):
            p23[k] = (k == "ENABLE_P23_SHORT")
    df, _df_raw = rc.preload(str(OHLCV_CSV), p23)
    bar_ms = int(df.at[1, "timestamp_ms"] - df.at[0, "timestamp_ms"])
    _log(f"[load] bars={len(df)} bar_ms={bar_ms}")

    # ---- 自己検査: 連続モード（フル閾値）が本物 replay_csv.run() と完全一致するか ----
    full_fn = lambda i: (check_entry_priority(i, df, p23) == PRIORITY)
    mine = run_continuous(df, bar_ms, p23, full_fn)
    ref  = rc.run(str(OHLCV_CSV), p23, _preloaded=(df, _df_raw), regime_switch=False)
    ref  = [t for t in ref if int(t.get("priority", t.get("entry_priority", 0))) == PRIORITY]
    nmine, nref = len(mine), len(ref)
    smine = sum(float(t["net_usd"]) for t in mine); sref = sum(float(t["net_usd"]) for t in ref)
    _log(f"[self-check] 自作 連続: {nmine}件 net=${smine:.2f}  /  本物 run(): {nref}件 net=${sref:.2f}")
    assert nmine == nref and abs(smine - sref) < 0.01, \
        f"自己検査NG: 自作シミュレーターが本物V9と一致しない（件数 {nmine}vs{nref} / net {smine:.2f}vs{sref:.2f}）→ 移植ミス・停止"
    _log("[self-check] ✅ 一致。シミュレーターは V9 と同一挙動と確認 → 候補生成に進む")

    # ---- 候補生成 + 独立ラベル ----
    for tag, fn in [("full", full_fn), ("typeonly", lambda i: _p23_type_fires(df, i))]:
        sig = [i for i in range(rc.CANDLE_WARMUP, len(df)) if fn(i)]
        rows = []
        for c in sig:
            tr = simulate_independent(df, bar_ms, c, params)     # add/exit は V9 フルparams
            if tr is None:
                continue
            rows.append(tr)
        out = pd.DataFrame(rows)
        path = OUT_DIR / f"p23_candidates_{tag}.csv"
        out.to_csv(path, index=False)
        _log(f"[{tag}] 候補発火 {len(sig)} → 約定 {len(out)}件 / net合計 ${out['net_usd'].sum():.1f} "
             f"/ avg ${out['net_usd'].mean():.2f} / 勝率 {(out['net_usd']>0).mean():.3f} → {path}")


if __name__ == "__main__":
    main()
