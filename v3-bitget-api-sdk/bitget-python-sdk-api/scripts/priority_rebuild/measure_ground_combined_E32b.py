#!/usr/bin/env python3
"""measure_ground_combined_E32b.py — P21+P23 合算地面（案2・cap停止つき・忠実ループ・自己検査つき）

背景（2026-06-13・まこさん GO）:
  E32 で「素朴な合算(rc.run P21+P23)は cap 0.264 BTC=2.2倍違反」を確定。replay_csv の add は
  混在Priorityで cap を守らない。→ cap停止（0.12到達でadd停止）を入れた合算を測る必要がある。
  rc.run は decider順(23→21)固定・cap停止なし。gen._step は P23専用(TRAILなし)。
  → measure側に「P21 TRAIL＋P23全Exit＋merge＋優先順位パラメータ＋cap停止」の忠実ループを自作。

忠実さの担保（自己検査・rc.run 再実行は省略＝既存 E31 単独CSVと突合）:
  cap=∞ で単独 P21 を回し E31 P21地面(trades_p21_E31_newwin_ground.csv)と件数・net 一致／
  cap=∞ で単独 P23 を回し E31 P23地面(trades_p23_E31_newwin_ground.csv)と一致。
  一致＝「P21 TRAIL 込みで V9 完全移植」を機械的に証明（不一致なら停止・直す）。

本測定:
  cap=0.12 で 23→21（decider順）と 21→23（まこさん仮説）を新窓 score。
  V9本体不変（replay_csv / cat_v9_decider / params は import のみ）。

★ entry/add/Exit のロジックは rc.run 本体 L1131-1377 を1字ずつ移植:
  - 開く: 引いた信号の Priority のサイズ・TP/SL。entry_priority=その Priority（Exit はこの Priority で回る）。
  - add : 引いた信号の Priority のサイズで積む(L1139)・max_adds は「最初に建てた Priority」のもの(L1346)・
          TP/SL は建てた Priority で再計算(L1202)。★cap停止: pos.size+unit>0.12 なら add しない。
  - Exit: TP→SL→TRAIL(P21のみ・L1284)→_check_exits_replay(12種)。MFE/trail更新は L1236-1251。

使い方: `python3 measure_ground_combined_E32b.py [--selfcheck-only]`
"""
from __future__ import annotations
import sys
import pathlib
from decimal import Decimal
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runner"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import replay_csv as rc                                       # noqa: E402
from strategies.cat_v9_decider import check_entry_priority    # noqa: E402

SLICE = ROOT / "data" / "BTCUSDT-5m-2024-09-01_2026-02-28_slice_V9FULL_safe.csv"
RAT = ROOT / "results" / "priority_rebuild" / "ratchet"
REF_P21 = RAT / "trades_p21_E31_newwin_ground.csv"
REF_P23 = RAT / "trades_p23_E31_newwin_ground.csv"
OUT_2321 = RAT / "trades_p21p23_E32b_2321_capstop.csv"
OUT_2123 = RAT / "trades_p21p23_E32b_2123_capstop.csv"
CAP = 0.12
INF = 9.99   # 自己検査用の実質無限 cap


def _mk_pending(df, i, close_p, fire_pri):
    lp = float(Decimal(str(close_p)) * Decimal("1.0001"))        # SHORT maker 指値 +0.01%
    g = lambda col: float(df.at[i, col]) if col in df.columns and pd.notna(df.at[i, col]) else float("nan")
    return {"side": "SHORT", "priority": fire_pri, "limit_price": lp, "placed_bar_ms": int(df.at[i, "timestamp_ms"]),
            "adx_at_entry": g("adx"), "bb_mid_slope_at_entry": g("bb_mid_slope"),
            "rsi_at_entry": g("rsi_short"), "rsi_slope_at_entry": g("rsi_slope_short"),
            "stoch_k_at_entry": g("stoch_k"), "stoch_d_at_entry": g("stoch_d"), "bb_width_at_entry": g("bb_width")}


def _max_adds(params, opener):
    return int(params.get(f"P{opener}_MAX_ADDS",
               params.get("MAX_ADDS_BY_PRIORITY", {}).get(str(opener), params.get("SHORT_MAX_ADDS", 5))))


def _step(state, df, bar_ms, i, params, p21only, p23only, order, cap):
    """1バー処理。merge(1ポジSHORT)・cap停止・優先順位パラメータ・P21 TRAIL 込み。"""
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
            fp_pri   = int(pending["priority"])                 # 引いた信号の Priority
            adx_val  = float(pending.get("adx_at_entry", 0.0))
            unit_size = float(params.get(f"P{fp_pri}_POSITION_SIZE_BTC", params["SHORT_POSITION_SIZE_BTC"]))
            states   = rc._calc_entry_states(df, i, ts_ms)
            if pos is None:                                     # 新規（entry_priority=引いた Priority）
                # ★P1/P21 は BB ベース TP（rc.run L1151-1161）・他は _calc_tp_price（P23 標準）
                if fp_pri in (1, 21):
                    _bu = float(df.at[i, "bb_sigma2_upper"]) if "bb_sigma2_upper" in df.columns else float("nan")
                    _bl = float(df.at[i, "bb_sigma2_lower"]) if "bb_sigma2_lower" in df.columns else float("nan")
                    if not (pd.isna(_bu) or pd.isna(_bl)):
                        _half = (_bu - _bl) / 2
                        _r = float(params.get(f"P{fp_pri}_TP_BB_RATIO", 1.0))
                        _m = float(params.get(f"P{fp_pri}_TP_MIN_PCT", 0.0003))
                        _dist = max(_half * _r, fill_p * _m)
                        tp_open = fill_p - _dist                # SHORT
                    else:
                        tp_open = rc._calc_tp_price(side, fill_p, adx_val, params, fp_pri, atr_14=states.get("atr_14", float("nan")))
                else:
                    tp_open = rc._calc_tp_price(side, fill_p, adx_val, params, fp_pri, atr_14=states.get("atr_14", float("nan")))
                pos = {
                    "side": side, "entry_priority": fp_pri, "entry_price": fill_p,
                    "entry_time": ts_ms, "add_count": 1, "size_btc": unit_size,
                    "tp_price": tp_open,
                    "sl_price": rc._calc_sl_price(side, fill_p, params, fp_pri),
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
                pending = None
            else:
                # ★cap停止: 積むと cap を超えるなら add しない（pending を捨てる）。max_adds は opener。
                opener = int(pos["entry_priority"])
                if float(pos["size_btc"]) + unit_size > cap + 1e-9:
                    pending = None                              # cap到達 → add 停止
                else:
                    old_sz, old_p = float(pos["size_btc"]), float(pos["entry_price"])
                    new_sz  = old_sz + unit_size
                    new_avg = (old_p * old_sz + fill_p * unit_size) / new_sz
                    new_cnt = int(pos["add_count"]) + 1
                    pos.update({
                        "entry_price": new_avg, "add_count": new_cnt, "size_btc": new_sz,
                        "tp_price": rc._calc_tp_price(side, new_avg, adx_val, params, opener, atr_14=states.get("atr_14", float("nan"))),
                        "sl_price": rc._calc_sl_price(side, new_avg, params, opener) if new_cnt >= 2 else None,
                    })
                    pending = None

    # 2. MFE/MAE/極値 + P21 trail 更新（rc.run L1217-1251）
    if pos is not None:
        entry_p, size_b = float(pos["entry_price"]), float(pos["size_btc"])
        unreal = (entry_p - mark_p) * size_b
        if unreal > float(pos.get("mfe_usd", 0.0)): pos["mfe_usd"] = unreal
        if unreal < float(pos.get("mae_usd", 0.0)): pos["mae_usd"] = unreal
        if low_p < float(pos.get("min_low", float("inf"))): pos["min_low"] = low_p
        if int(pos.get("entry_priority", -1)) in (1, 21):       # P21 TRAIL ピーク更新
            _ep = entry_p
            _fav_pct = (_ep - low_p) / _ep * 100                # SHORT
            if _fav_pct > float(pos.get("mfe_peak_pct", 0.0)):
                pos["mfe_peak_pct"] = _fav_pct
                _tp = int(pos["entry_priority"])
                _gate  = float(params.get(f"P{_tp}_MFE_GATE_PCT", 0.05))
                _ratio = float(params.get(f"P{_tp}_TRAIL_RATIO", 0.8))
                if _fav_pct >= _gate:
                    pos["trail_stop_price"] = _ep * (1 - _fav_pct / 100 * _ratio)

    # 3. TP（SHORT: low<=tp）
    if pos is not None and low_p <= float(pos["tp_price"]):
        rc._record_trade(trades, pos, exit_price=float(pos["tp_price"]), exit_reason="TP_FILLED", exit_ts_ms=ts_ms, params=params)
        pos = None
    # 4. SL（SHORT: high>=sl）
    if pos is not None and pos.get("sl_price") is not None and high_p >= float(pos["sl_price"]):
        rc._record_trade(trades, pos, exit_price=float(pos["sl_price"]), exit_reason="SL_FILLED", exit_ts_ms=ts_ms, params=params)
        pos = None
    # 4b. TRAIL_EXIT（P21専用・SHORT: high>=tsp）
    if pos is not None and int(pos.get("entry_priority", -1)) in (1, 21):
        tsp = pos.get("trail_stop_price")
        if tsp is not None and high_p >= float(tsp):
            rc._record_trade(trades, pos, exit_price=float(tsp), exit_reason="TRAIL_EXIT", exit_ts_ms=ts_ms, params=params)
            pos = None
    # 5. _check_exits_replay（TP/SL/TRAIL 以外の12種）
    if pos is not None:
        reason = rc._check_exits_replay(pos, mark_p, df, i, params, ts_ms)
        if reason:
            rc._record_trade(trades, pos, exit_price=mark_p, exit_reason=reason, exit_ts_ms=ts_ms, params=params)
            pos = None

    # 6. エントリー/ADD 判断（優先順位パラメータ）
    p21f = (check_entry_priority(i, df, p21only) == 21)
    p23f = (check_entry_priority(i, df, p23only) == 23)
    if order == "23>21":
        fire_pri = 23 if p23f else (21 if p21f else None)
    else:                                                       # "21>23"
        fire_pri = 21 if p21f else (23 if p23f else None)
    if fire_pri is not None and pending is None:
        if pos is None:
            pending = _mk_pending(df, i, close_p, fire_pri)     # 新規
        else:
            opener = int(pos["entry_priority"])
            if int(pos["add_count"]) < _max_adds(params, opener):
                pending = _mk_pending(df, i, close_p, fire_pri) # add 候補（cap停止は fill 時）

    state["pos"], state["pending"] = pos, pending


def run_combined(df, bar_ms, params, p21only, p23only, order, cap):
    state = {"pos": None, "pending": None, "trades": []}
    for i in range(rc.CANDLE_WARMUP, len(df)):
        _step(state, df, bar_ms, i, params, p21only, p23only, order, cap)
    if state["pos"] is not None:
        rc._record_trade(state["trades"], state["pos"], exit_price=float(df.iloc[-1]["close"]),
                         exit_reason="FORCE_CLOSE_EOD", exit_ts_ms=int(df.iloc[-1]["timestamp_ms"]), params=params)
    return state["trades"]


def _only(params, *enabled):
    p = dict(params)
    for k in list(p):
        if k.startswith("ENABLE_P") and k.endswith(("_LONG", "_SHORT")):
            p[k] = (k in enabled)
    return p


def main():
    selfcheck_only = "--selfcheck-only" in sys.argv
    params = rc._load_params()
    p21on = _only(params, "ENABLE_P21_SHORT")
    p23on = _only(params, "ENABLE_P23_SHORT")
    none_on = _only(params)                                     # 全OFF（片側を殺す用）

    df, _raw = rc.preload(str(SLICE), p21on)
    bar_ms = int(df.at[1, "timestamp_ms"] - df.at[0, "timestamp_ms"])
    print(f"[load] {SLICE.name} bars={len(df)}")

    # ---- 自己検査: cap=∞ で単独が rc.run（E31 CSV）と一致するか ----
    def _ref_net(path):
        d = pd.read_csv(path); return len(d), round(d["net_usd"].astype(float).sum(), 2)

    print("[自己検査1] 単独P21（cap=∞）vs E31 P21地面 ...")
    t21 = run_combined(df, bar_ms, params, p21on, none_on, "23>21", INF)   # p23 殺す → 純P21
    n21, net21 = len(t21), round(sum(float(t["net_usd"]) for t in t21), 2)
    rn21, rnet21 = _ref_net(REF_P21)
    ok21 = (n21 == rn21 and abs(net21 - rnet21) < 0.01)
    print(f"   自作 {n21}件/${net21}  vs  rc.run {rn21}件/${rnet21}  → {'✅一致' if ok21 else '❌不一致'}")

    print("[自己検査2] 単独P23（cap=∞）vs E31 P23地面 ...")
    t23 = run_combined(df, bar_ms, params, none_on, p23on, "23>21", INF)   # p21 殺す → 純P23
    n23, net23 = len(t23), round(sum(float(t["net_usd"]) for t in t23), 2)
    rn23, rnet23 = _ref_net(REF_P23)
    ok23 = (n23 == rn23 and abs(net23 - rnet23) < 0.01)
    print(f"   自作 {n23}件/${net23}  vs  rc.run {rn23}件/${rnet23}  → {'✅一致' if ok23 else '❌不一致'}")

    assert ok21 and ok23, "自己検査 不一致＝移植にバグ（TRAIL等）。本測定に進まない。"
    print("[自己検査] ✅ 両方一致＝P21 TRAIL 込みで V9 完全移植を機械的に証明")
    if selfcheck_only:
        print("[--selfcheck-only] 自己検査のみで終了。"); return

    # ---- 本測定: cap=0.12 で 23→21 と 21→23 ----
    for order, out in (("23>21", OUT_2321), ("21>23", OUT_2123)):
        print(f"[本測定] order={order} cap={CAP} ...")
        tr = run_combined(df, bar_ms, params, p21on, p23on, order, CAP)
        d = pd.DataFrame(tr)
        # cap物理検証（report_budget 相当）
        et = pd.to_datetime(d["entry_time"]).tolist(); xt = pd.to_datetime(d["exit_time"]).tolist()
        sz = d["size_btc"].astype(float).tolist()
        ev = [(et[i], sz[i]) for i in range(len(d))] + [(xt[i], -sz[i]) for i in range(len(d))]
        ev.sort(key=lambda x: (x[0], x[1])); cur = mx = 0.0
        for _t, s in ev:
            cur = round(cur + s, 9); mx = max(mx, cur)
        by_pri = d["priority"].astype(int).value_counts().to_dict()
        d.to_csv(out, index=False)
        print(f"   {len(d)}件 priority別{by_pri} / 同時保有max {mx:.4f}BTC {'✅' if mx<=CAP+1e-9 else '⛔超過'} → {out.name}")

    print("\n→ 採点:")
    for out in (OUT_2321, OUT_2123):
        print(f"  precheck.py {out.name} --authorize {out.name}")
        print(f"  score.py {out} --start 2025-06-01 --end 2026-02-28")


if __name__ == "__main__":
    main()
