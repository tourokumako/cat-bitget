#!/usr/bin/env python3
"""train_p23_scaleout_E15.py — P23 部分決済の刻み ML（E15・strat_v9ml_design §10.17.1 章7-4・まこさん承認 2026-06-10）

設計（章7-4）:
  - 狙い = TIME_EXIT 出血（地面 74件 −$2,161・固定等分 scale out でも −$2,152）を「減らさず利確の形で調整」で取る。
    伸びない玉だけ早く刻んで確保・伸びる玉は刻まない（玉別の条件付き scale out）。
  - 木が当てる対象 = 保有中の各バーで「今1ロットだけ部分利確して残りを V9 のまま続けると、
    このまま全量持つより net が増えるか」の二値。ラベル=差額の符号・重み=|差額|（p99 クリップ）。
    アクション（1ロット部分利確）とラベルが完全一致（Triple Barrier 鉄則）。
  - 教師 = 地面ポジの保有中スナップショット（30分以降・ロット2以上）。A=全量持つ net（地面実結果）／
    B=1ロット降り（成行 ML_EXIT・rc._record_trade 計算）＋残りロットを V9 出口まで前向き sim（add 再開なし近似）。
  - 運用 = E0.3 _step_scaleout 型機構（部分決済で保有が減る・枠空き再add・案B）。固定等分の指値刻みは使わない。
    保有ロット2以上・30分以降・「降りた方が得」prob > cut → 最古1ロットを成行で部分利確（1バー1ロット・
    ML_EXIT・FIFO 1行出し=funding 正確）。prob 低下で停止・最後の1ロットは V9 出口に任せる。
  - 検証 = OOF（purged k-fold・ポジション単位）健全性 ＋ 学習期間内 hold-out（ポジ後半30%）の運用ループで
    6案（cut 上位{5,10,20}% × {無条件, 最古ロット含み益のみ}）を比較 → 1案選定 → まこさん GO 後 --score で採点1回。
自己検査: ① ML off ループ＝地面 1232件/$2558.80 完全一致 ② 教師 sim「降りない版」= final_net 一致（以後 add なし玉）。
★不正防止（cat_requirements §8.4-2.9）: 判定は score.py の数字のみ・本スクリプトは net 計算に触れない
  （rc._record_trade / score は import のみ）。V9 本体 / gen / score / eval_engine / E0.3 / E14 は import のみ・改造しない。
"""
from __future__ import annotations
import sys
import copy
import time
import json
import pathlib
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runner"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import replay_csv as rc                          # noqa: E402  V9 リプレイ（import のみ）
import gen_p23_candidates as gen                 # noqa: E402  連続モード移植（import のみ）
import score as judge                            # noqa: E402  審判（import のみ）
import ratchet_guards as rg                      # noqa: E402  番人
import measure_p23_ground_scaleout as ms         # noqa: E402  E0.3 機構（_emit_portion/_close_remaining/_refresh）
import train_p23_entry_E8b as e8b                # noqa: E402  期間分割・方向系特徴量
import train_p23_hold_E14 as e14                 # noqa: E402  スナップ基盤（市場特徴量・玉状態・k-fold・学習）
from strategies.cat_v9_decider import check_entry_priority   # noqa: E402

RAT = e8b.RAT
TRAIN_ENTRY_END = e8b.TRAIN_ENTRY_END
EMBARGO_END = e8b.EMBARGO_END
SC_START, SC_END = e8b.SC_START, e8b.SC_END
GROUND = e8b.GROUND

SNAP_MIN_AGE_MIN = e14.SNAP_MIN_AGE_MIN          # 30分（E14 承認値踏襲）
N_FOLDS = e14.N_FOLDS
W_CLIP_Q = e14.W_CLIP_Q
VOL_DOMINANCE_STOP = e14.VOL_DOMINANCE_STOP
HOLDOUT_POS_FRAC = 0.30                          # 学習期間内 hold-out = ポジション後半30%（6案比較用）
CANDIDATES = [(q, po) for q in (0.95, 0.90, 0.80) for po in (False, True)]   # (cut分位, 含み益ロットのみ)

OUT_CSV = RAT / "trades_p23_E15_scaleout.csv"
OUT_JSON = RAT / "p23_learned_params_E15.json"


def _log(m):
    print(m, flush=True)


# ---------------------------------------------------------------- 機構（E0.3 型 + ML 部分降りフック）
def _step_e15(state, df, arrays, bar_ms, i, params, fire_fn, ml=None):
    """E0.3 _step_scaleout と同一骨格（pending fill → MFE → [ML 部分降り] → TP → SL → V9 exits → entry/add）。
    固定等分刻み（E0.3 の 2.5）は載せず、代わりに ML 条件付き 1 ロット降りを同位置に置く。
    ml=None なら部分決済が一切起きない＝gen.run_continuous（地面）と完全一致（自己検査①）。"""
    pos, pending, trades = state["pos"], state["pending"], state["trades"]
    ts_arr, close_arr, high_arr, low_arr = arrays
    ts_ms = int(ts_arr[i])
    close_p = float(close_arr[i])
    high_p = float(high_arr[i])
    low_p = float(low_arr[i])
    side = "SHORT"
    unit = float(params.get(f"P{gen.PRIORITY}_POSITION_SIZE_BTC", params["SHORT_POSITION_SIZE_BTC"]))

    # 1. pending fill（SHORT: high>=limit）
    if pending is not None:
        if max(0, (ts_ms - int(pending["placed_bar_ms"])) // bar_ms) >= rc.PENDING_TTL_BARS:
            pending = None
        elif high_p >= float(pending["limit_price"]):
            fill_p = float(pending["limit_price"])
            adx_val = float(pending.get("adx_at_entry", 0.0))
            states = rc._calc_entry_states(df, i, ts_ms)
            if pos is None:
                pos = {
                    "side": side, "entry_priority": gen.PRIORITY, "entry_price": fill_p,
                    "entry_time": ts_ms, "add_count": 1, "size_btc": unit,
                    "tp_price": rc._calc_tp_price(side, fill_p, adx_val, params, gen.PRIORITY, atr_14=states.get("atr_14", float("nan"))),
                    "sl_price": rc._calc_sl_price(side, fill_p, params, gen.PRIORITY),
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
                    "_unit_size": unit, "_adx_last": adx_val, "_last_add_bar": i,
                    "_lots": [{"add_time": ts_ms, "add_price": fill_p}],
                }
            else:
                old_sz, old_p = float(pos["size_btc"]), float(pos["entry_price"])
                new_sz = old_sz + unit
                new_avg = (old_p * old_sz + fill_p * unit) / new_sz
                pos["entry_price"] = new_avg
                pos["_adx_last"] = adx_val
                pos["_last_add_bar"] = i
                pos["_lots"].append({"add_time": ts_ms, "add_price": fill_p})
                ms._refresh_v9_view(pos)
                pos["tp_price"] = rc._calc_tp_price(side, new_avg, adx_val, params, gen.PRIORITY, atr_14=states.get("atr_14", float("nan")))
                pos["sl_price"] = rc._calc_sl_price(side, new_avg, params, gen.PRIORITY) if pos["add_count"] >= 2 else None
            pending = None

    # 2. MFE/MAE/極値（現在の avg・size で更新＝部分降りで保有が減れば追従）
    if pos is not None:
        entry_p, size_b = float(pos["entry_price"]), float(pos["size_btc"])
        unreal = (entry_p - close_p) * size_b
        if unreal > float(pos.get("mfe_usd", 0.0)):
            pos["mfe_usd"] = unreal
        if unreal < float(pos.get("mae_usd", 0.0)):
            pos["mae_usd"] = unreal
        if low_p < float(pos.get("min_low", float("inf"))):
            pos["min_low"] = low_p

    # 2.5 ★ML 部分降り（E15）: ロット2以上・保有30分以降・「降りた方が得」prob>cut → 最古1ロット成行降り
    if ml is not None and pos is not None and len(pos["_lots"]) >= 2:
        age_min = (ts_ms - int(pos["entry_time"])) / 60_000.0
        if age_min >= SNAP_MIN_AGE_MIN:
            lot0 = pos["_lots"][0]
            ok = (not ml["profit_only"]) or ((float(lot0["add_price"]) - close_p) > 0.0)   # SHORT: 最古ロット含み益
            if ok:
                row = np.concatenate([ml["M"][i],
                                      np.asarray(e14._pos_state_row(pos, close_p, ts_ms, i), dtype=np.float32)])
                prob = float(ml["model"].predict(row.reshape(1, -1))[0])
                fire = (prob < ml["cut"]) if ml.get("invert") else (prob > ml["cut"])   # invert=対照実験（prob 逆）
                if fire:
                    lot = pos["_lots"].pop(0)
                    ms._emit_portion(trades, pos, lot["add_time"], exit_price=close_p,
                                     exit_reason="ML_EXIT", exit_ts_ms=ts_ms, params=params)
                    ms._refresh_v9_view(pos)
                    ml["n_cut"] += 1

    closed = False
    split_rows = ml is not None              # ML 運用時のみ FIFO ロット別行（ML off は満玉1行＝地面と同一構造）
    # 3. TP（SHORT: low<=tp）残り全ロット決済
    if pos is not None and low_p <= float(pos["tp_price"]):
        ms._close_remaining(trades, pos, float(pos["tp_price"]), "TP_FILLED", ts_ms, params, split_rows)
        pos = None
        closed = True
    # 4. SL（SHORT: high>=sl）
    if pos is not None and pos.get("sl_price") is not None and high_p >= float(pos["sl_price"]):
        ms._close_remaining(trades, pos, float(pos["sl_price"]), "SL_FILLED", ts_ms, params, split_rows)
        pos = None
        closed = True
    # 6. V9 の他出口（現在の保有で判定）
    if pos is not None:
        reason = rc._check_exits_replay(pos, close_p, df, i, params, ts_ms)
        if reason:
            ms._close_remaining(trades, pos, close_p, reason, ts_ms, params, split_rows)
            pos = None
            closed = True

    # 7. エントリー / ADD（部分降りで枠が空けばまた買い増せる＝案B・V9 のまま）
    fire_add = (fire_fn(i))
    want_initial = (pos is None and pending is None and fire_add)
    if (fire_add and pos is not None) or want_initial:
        if pos is not None:
            if len(pos["_lots"]) >= int(params.get("MAX_ADDS_BY_PRIORITY", {}).get(str(gen.PRIORITY), 5)):
                pass
            elif pending is None:
                pending = gen._mk_pending(df, i, close_p)
        elif pending is None:
            pending = gen._mk_pending(df, i, close_p)

    state["pos"], state["pending"] = pos, pending
    return closed


def run_e15(df, bar_ms, params, fire_fn, ml=None, collect=False, i_start=None, i_end=None):
    """連続モード＋E15。collect=True: 教師スナップ収集（ML 発動なし＝地面と同一軌道・ロット2以上のみ）。"""
    arrays = (df["timestamp_ms"].to_numpy(), df["close"].to_numpy(),
              df["high_raw"].to_numpy(), df["low_raw"].to_numpy())
    state = {"pos": None, "pending": None, "trades": []}
    snaps, cur = [], []
    lo = max(rc.CANDLE_WARMUP, i_start or rc.CANDLE_WARMUP)
    hi = i_end if i_end is not None else len(df)
    for i in range(lo, hi):
        n_before = len(state["trades"])
        _step_e15(state, df, arrays, bar_ms, i, params, fire_fn, ml=ml)
        pos = state["pos"]
        if collect and pos is not None and len(pos["_lots"]) >= 2:
            ts_ms = int(arrays[0][i])
            close_p = float(arrays[1][i])
            age = (ts_ms - int(pos["entry_time"])) / 60_000.0
            if age >= SNAP_MIN_AGE_MIN:
                cur.append({"bar_i": i, "ts": ts_ms, "close": close_p,
                            "state": e14._pos_state_row(pos, close_p, ts_ms, i),
                            "pos": copy.deepcopy(pos), "pos_entry": int(pos["entry_time"])})
        if collect and len(state["trades"]) > n_before:
            seg = state["trades"][n_before:]
            final_net = sum(float(t["net_usd"]) for t in seg)
            final_adds = int(seg[-1].get("add_count", 1))
            for s in cur:
                s["final_net"] = final_net
                s["final_adds"] = final_adds
            snaps.extend(cur)
            cur = []
    if state["pos"] is not None:
        ms._close_remaining(state["trades"], state["pos"], float(arrays[1][hi - 1]),
                            "FORCE_CLOSE_EOD", int(arrays[0][hi - 1]), params, ml is not None)
        if collect:
            seg_net = float(state["trades"][-1]["net_usd"])
            for s in cur:
                s["final_net"] = seg_net
                s["final_adds"] = int(state["trades"][-1].get("add_count", 1))
            snaps.extend(cur)
    return state["trades"], snaps


# ---------------------------------------------------------------- 教師 B 側（1ロット降り＋残り前向き sim）
def _sim_remaining(pos, df, arrays, start_i, params):
    """残りロットを V9 出口まで前向き sim（ML なし・add なし＝1段差額の近似）。net 合計を返す。"""
    ts_arr, close_arr, high_arr, low_arr = arrays
    scratch = []
    for j in range(start_i, len(df)):
        ts_ms = int(ts_arr[j])
        close_p = float(close_arr[j])
        high_p = float(high_arr[j])
        low_p = float(low_arr[j])
        entry_p, size_b = float(pos["entry_price"]), float(pos["size_btc"])
        unreal = (entry_p - close_p) * size_b
        if unreal > float(pos.get("mfe_usd", 0.0)):
            pos["mfe_usd"] = unreal
        if unreal < float(pos.get("mae_usd", 0.0)):
            pos["mae_usd"] = unreal
        if low_p < float(pos.get("min_low", float("inf"))):
            pos["min_low"] = low_p
        if low_p <= float(pos["tp_price"]):
            ms._close_remaining(scratch, pos, float(pos["tp_price"]), "TP_FILLED", ts_ms, params, True)
            break
        if pos.get("sl_price") is not None and high_p >= float(pos["sl_price"]):
            ms._close_remaining(scratch, pos, float(pos["sl_price"]), "SL_FILLED", ts_ms, params, True)
            break
        reason = rc._check_exits_replay(pos, close_p, df, j, params, ts_ms)
        if reason:
            ms._close_remaining(scratch, pos, close_p, reason, ts_ms, params, True)
            break
    else:
        ms._close_remaining(scratch, pos, float(close_arr[-1]), "FORCE_CLOSE_EOD", int(ts_arr[-1]), params, True)
    return sum(float(t["net_usd"]) for t in scratch)


def build_b_side(snaps, df, arrays, params):
    """各スナップの B = 1ロット降り（成行 ML_EXIT）net ＋ 残り sim net。所要時間を実測表示。"""
    t0 = time.time()
    for n, s in enumerate(snaps):
        tmp = copy.deepcopy(s["pos"])
        lot = tmp["_lots"].pop(0)
        scratch = []
        ms._emit_portion(scratch, tmp, lot["add_time"], exit_price=s["close"],
                         exit_reason="ML_EXIT", exit_ts_ms=s["ts"], params=params)
        ms._refresh_v9_view(tmp)
        s["b_net"] = float(scratch[-1]["net_usd"]) + _sim_remaining(tmp, df, arrays, s["bar_i"] + 1, params)
        if n == 199:
            per = (time.time() - t0) / 200.0
            _log(f"[B sim] 実測 {per*1000:.1f}ms/枚 → 全 {len(snaps)} 枚 見積もり {per*len(snaps)/60:.1f} 分")
    _log(f"[B sim] 完了 {len(snaps)} 枚 / {time.time()-t0:.0f} 秒")


def selfcheck_sim(snaps, df, arrays, params, n_check=50):
    """自己検査②: 「降りない版」sim が final_net と一致するか（スナップ後に add が無かった玉のみ対象）。"""
    done = 0
    for s in snaps:
        if int(s["pos"]["add_count"]) != int(s["final_adds"]):
            continue
        a = _sim_remaining(copy.deepcopy(s["pos"]), df, arrays, s["bar_i"] + 1, params)
        assert abs(a - float(s["final_net"])) < 0.01, \
            f"自己検査② FAIL: 降りない sim {a:.2f} ≠ final_net {s['final_net']:.2f}（bar_i={s['bar_i']}）→ 移植ミス・停止"
        done += 1
        if done >= n_check:
            break
    assert done > 0, "自己検査② FAIL: 検査対象スナップが 0"
    _log(f"[自己検査②] ✅ 降りない sim = final_net 完全一致（{done} 枚・以後 add なし玉）")


# ---------------------------------------------------------------- main
def main():
    SMOKE = "--smoke" in sys.argv
    DO_SCORE = "--score" in sys.argv
    sel_q = None
    sel_po = None
    if DO_SCORE:
        for a in sys.argv:
            if a.startswith("--cut-q="):
                sel_q = float(a.split("=")[1])
            if a.startswith("--profit-only="):
                sel_po = a.split("=")[1] in ("1", "true", "True")
        assert sel_q is not None and sel_po is not None, "--score には --cut-q= と --profit-only= が必要（選定案・GO 後）"

    _log("[E15] P23 部分決済の刻み ML（玉別の条件付き scale out・地面 $925.73 / 固定等分 $338 比較）")
    rg.assert_no_future_ref(pathlib.Path(__file__).read_text())
    rg.assert_period_split(TRAIN_ENTRY_END, SC_START)

    params = rc._load_params()
    p23 = dict(params)
    for k in list(p23):
        if k.startswith("ENABLE_P") and k.endswith(("_LONG", "_SHORT")):
            p23[k] = (k == "ENABLE_P23_SHORT")
    df, _ = rc.preload(str(gen.OHLCV_CSV), p23)
    bar_ms = int(df.at[1, "timestamp_ms"] - df.at[0, "timestamp_ms"])
    ohlcv = pd.read_csv(e8b.OHLCV)
    ohlcv["timestamp"] = pd.to_datetime(ohlcv["timestamp"])
    _log(f"[load] bars={len(df)}")
    Mdf = e14.build_market_matrix(df, ohlcv)
    market_cols = list(Mdf.columns)
    M = Mdf.to_numpy(dtype=np.float32)
    feat_cols = market_cols + e14.POS_STATE_COLS
    arrays = (df["timestamp_ms"].to_numpy(), df["close"].to_numpy(),
              df["high_raw"].to_numpy(), df["low_raw"].to_numpy())
    fire_fn = lambda i: (check_entry_priority(i, df, p23) == gen.PRIORITY)

    # ---- 教師収集（ML off ＝ 地面と同一軌道・1パス）＋ 自己検査① ----
    base_trades, snaps = run_e15(df, bar_ms, p23, fire_fn, ml=None, collect=True)
    g = pd.read_csv(GROUND)
    bsum, gsum = sum(float(t["net_usd"]) for t in base_trades), float(g["net_usd"].sum())
    _log(f"[自己検査①] ML off: {len(base_trades)}件/${bsum:.2f} vs 地面CSV {len(g)}件/${gsum:.2f}")
    assert len(base_trades) == len(g) and abs(bsum - gsum) < 0.01, "自己検査① FAIL: ML off が地面と不一致 → 停止"
    _log("[自己検査①] ✅ 一致（機構の移植は正しい・部分決済ゼロ＝地面）")

    # ---- 学習期間スナップのみ（H8）----
    sd = pd.DataFrame({
        "bar_i": [s["bar_i"] for s in snaps],
        "ts_dt": pd.to_datetime([s["ts"] for s in snaps], unit="ms"),
        "pos_entry": [s["pos_entry"] for s in snaps],
    })
    pos_entry_dt = pd.to_datetime(sd["pos_entry"], unit="ms")
    is_tr = ((pos_entry_dt < TRAIN_ENTRY_END) & (sd["ts_dt"] < EMBARGO_END)).values
    snaps_tr = [s for s, m in zip(snaps, is_tr) if m]
    if SMOKE:
        keep = sorted({s["pos_entry"] for s in snaps_tr})[-80:]
        snaps_tr = [s for s in snaps_tr if s["pos_entry"] in set(keep)]
        _log(f"[SMOKE] 末尾80ポジションに制限")
    _log(f"[教師] 学習期間スナップ {len(snaps_tr)} 枚 / ポジション {len({s['pos_entry'] for s in snaps_tr})} 本（ロット2以上のみ）")

    # ---- 自己検査② ＋ B 側計算 ----
    selfcheck_sim(snaps_tr, df, arrays, p23, n_check=20 if SMOKE else 50)
    build_b_side(snaps_tr, df, arrays, p23)

    sd_tr = pd.DataFrame({
        "bar_i": [s["bar_i"] for s in snaps_tr],
        "ts_dt": pd.to_datetime([s["ts"] for s in snaps_tr], unit="ms"),
        "pos_entry": [s["pos_entry"] for s in snaps_tr],
        "diff": [s["b_net"] - s["final_net"] for s in snaps_tr],
    })
    X_tr = pd.DataFrame(
        np.concatenate([M[sd_tr["bar_i"].values],
                        np.asarray([s["state"] for s in snaps_tr], dtype=np.float32)], axis=1),
        columns=feat_cols)
    y = (sd_tr["diff"] > 0).astype(int).values
    clip_at = float(sd_tr["diff"].abs().quantile(W_CLIP_Q))
    w = sd_tr["diff"].abs().clip(upper=clip_at).values
    keep = w > 0
    sd_tr, X_tr, y, w = sd_tr[keep].reset_index(drop=True), X_tr[keep].reset_index(drop=True), y[keep], w[keep]
    _log(f"[教師] 「降りた方が得」率 {y.mean()*100:.1f}% / 重み p99 クリップ ${clip_at:.2f}")

    # ---- OOF 健全性（purged k-fold・ポジション単位・E14 流用）----
    rows, oof = [], []
    for fi, (ti, vi, (v0, v1)) in enumerate(e14.purged_folds_by_pos(sd_tr, 2 if SMOKE else N_FOLDS)):
        if len(ti) < (200 if SMOKE else 1000) or len(vi) < (50 if SMOKE else 200) or len(np.unique(y[ti])) < 2:
            continue
        m = e14.fit_weighted(X_tr.iloc[ti], y[ti], w[ti], X_tr.iloc[vi], y[vi], w[vi])
        p = m.predict(X_tr.iloc[vi], num_iteration=m.best_iteration)
        dv = sd_tr["diff"].values[vi]
        sp = spearmanr(p, dv)
        auc = roc_auc_score(y[vi], p) if len(np.unique(y[vi])) > 1 else float("nan")
        rows.append({"fold": fi, "val_start": str(v0.date()), "val_end": str(v1.date()), "n_val": len(vi),
                     "best_iter": int(m.best_iteration),
                     "spearman_prob_diff": round(float(sp.statistic), 4), "auc": round(float(auc), 4)})
        oof.append(pd.DataFrame({"prob": p, "diff": dv}))
        _log(f"[fold{fi}] val {v0.date()}〜{v1.date()} n={len(vi)} Spearman(prob,差額)={sp.statistic:+.4f} "
             f"AUC={auc:.4f} best_iter={m.best_iteration}")
    assert rows, "有効 fold 0"
    oof = pd.concat(oof, ignore_index=True)
    sp_all = spearmanr(oof["prob"], oof["diff"])
    dec = oof.copy()
    dec["decile"] = pd.qcut(dec["prob"].rank(method="first"), 10, labels=False)
    dt = dec.groupby("decile").agg(n=("diff", "size"), diff_mean=("diff", "mean"),
                                   diff_sum=("diff", "sum")).reset_index()
    _log(f"\n[① prob×差額] OOF Spearman = {sp_all.statistic:+.4f}（正なら「降り得」検出が効く）")
    _log("[③ 較正] prob 10分位 ×「降りた場合の得（B−A）」（上位帯が大きくプラスなら刻みが効く）\n"
         + dt.to_string(index=False))

    # ---- hold-out 用学習（ポジ前半70%）＋ vol_share ----
    pos_sorted = sd_tr.groupby("pos_entry")["ts_dt"].min().sort_values()
    n_ho = max(1, int(len(pos_sorted) * HOLDOUT_POS_FRAC))
    ho_pos = set(pos_sorted.index[-n_ho:])
    tr_mask = ~sd_tr["pos_entry"].isin(ho_pos).values
    cut_i = int(tr_mask.sum() * 0.85)
    idx_tr = np.where(tr_mask)[0]
    m_sel = e14.fit_weighted(X_tr.iloc[idx_tr[:cut_i]], y[idx_tr[:cut_i]], w[idx_tr[:cut_i]],
                             X_tr.iloc[idx_tr[cut_i:]], y[idx_tr[cut_i:]], w[idx_tr[cut_i:]])
    vr = rg.report_vol_importance(dict(zip(m_sel.feature_name(), m_sel.feature_importance("gain"))))
    imp = pd.Series(m_sel.feature_importance("gain"), index=feat_cols).sort_values(ascending=False)
    _log(f"\n[② ボラ寄与] vol_share={vr['vol_share']}（停止 {VOL_DOMINANCE_STOP}） / top5={vr['top']}")
    _log("[重要特徴 top12]\n" + imp.head(12).to_string())
    if float(vr["vol_share"]) > VOL_DOMINANCE_STOP:
        _log("⛔ ボラ支配 → 停止・まこさんに報告")
        return
    prob_sel = m_sel.predict(X_tr.iloc[idx_tr], num_iteration=m_sel.best_iteration)

    if SMOKE:
        _log("\n[SMOKE] 完了（機構自己検査①②・B sim 実測・健全性まで。6案 hold-out と採点は本番のみ）")
        return

    # ---- 6案 hold-out 比較（学習期間内・ポジ後半30% 区間の運用ループ・採点期間 不接触）----
    ho_first = pd.to_datetime(min(ho_pos), unit="ms")
    ho_t0 = int((ho_first - pd.Timedelta(days=1)).timestamp() * 1000)
    i_start = int(np.searchsorted(arrays[0], ho_t0))
    train_end_ms = int(pd.Timestamp(TRAIN_ENTRY_END).timestamp() * 1000)
    i_end = int(np.searchsorted(arrays[0], train_end_ms))
    g["entry_time"] = pd.to_datetime(g["entry_time"])
    g_ho = g[(g["entry_time"] >= ho_first) & (g["entry_time"] < pd.Timestamp(TRAIN_ENTRY_END))]
    ground_ho = float(g_ho["net_usd"].sum())
    _log(f"\n[hold-out] 区間 {ho_first.date()}〜{TRAIN_ENTRY_END.date() if hasattr(TRAIN_ENTRY_END,'date') else TRAIN_ENTRY_END} "
         f"/ 地面（同区間 entry）= {len(g_ho)}件 ${ground_ho:.1f}")
    results = []
    for q, po in CANDIDATES:
        cut = float(np.quantile(prob_sel, q))
        ml = {"M": M, "model": m_sel, "cut": cut, "profit_only": po, "n_cut": 0}
        trades_ho, _ = run_e15(df, bar_ms, p23, fire_fn, ml=ml, i_start=i_start, i_end=i_end)
        tdf = pd.DataFrame(trades_ho)
        tdf["entry_time"] = pd.to_datetime(tdf["entry_time"])
        seg = tdf[(tdf["entry_time"] >= ho_first)]
        net = float(seg["net_usd"].sum())
        results.append({"cut_q": q, "profit_only": po, "cut": round(cut, 4),
                        "n_rows": int(len(seg)), "n_ml_cut": int(ml["n_cut"]),
                        "net_ho": round(net, 1), "vs_ground_ho": round(net - ground_ho, 1)})
        _log(f"[6案] cut上位{(1-q)*100:.0f}% / 含み益のみ={po} → {len(seg)}行 / 降り{ml['n_cut']}回 / "
             f"net ${net:.1f}（地面比 {net-ground_ho:+.1f}）")
    res_df = pd.DataFrame(results).sort_values("net_ho", ascending=False).reset_index(drop=True)
    _log("\n[6案まとめ（hold-out net 降順）]\n" + res_df.to_string(index=False))

    # ---- 対照実験（ML 寄与の切り分け）: prob 逆＝「下位20%」で降りる（含み益のみ）。
    #      ML に情報がなければ上位20%降りと同等の net になるはず（情報があれば下位降りは悪化する）。
    ctrl_cut = float(np.quantile(prob_sel, 0.20))
    ml_c = {"M": M, "model": m_sel, "cut": ctrl_cut, "profit_only": True, "invert": True, "n_cut": 0}
    trades_c, _ = run_e15(df, bar_ms, p23, fire_fn, ml=ml_c, i_start=i_start, i_end=i_end)
    tdf_c = pd.DataFrame(trades_c)
    tdf_c["entry_time"] = pd.to_datetime(tdf_c["entry_time"])
    seg_c = tdf_c[(tdf_c["entry_time"] >= ho_first)]
    net_c = float(seg_c["net_usd"].sum())
    control = {"cut_q_low": 0.20, "profit_only": True, "invert": True, "cut": round(ctrl_cut, 4),
               "n_ml_cut": int(ml_c["n_cut"]), "net_ho": round(net_c, 1),
               "vs_ground_ho": round(net_c - ground_ho, 1)}
    _log(f"\n[対照] prob 下位20%降り / 含み益のみ → 降り{ml_c['n_cut']}回 / net ${net_c:.1f}"
         f"（地面比 {net_c-ground_ho:+.1f}）⇔ 上位20%降り {res_df.iloc[0]['net_ho']}")

    out = {
        "_source": "train_p23_scaleout_E15.py（部分決済の刻み ML・§10.17.1 章7-4・Entry/add/V9既存Exit/サイズ 不変）",
        "_design": "教師=保有中スナップ(30分以降・ロット2以上)・ラベル=sign(1ロット降り+残りV9 − 全量持つ)・重み|差額|p99",
        "OOF_SPEARMAN_PROB_DIFF": round(float(sp_all.statistic), 4),
        "VOL_SHARE": vr["vol_share"],
        "N_SNAPSHOTS_TRAIN": int(len(sd_tr)),
        "POS_RATE_CUT_BETTER": round(float(y.mean()), 4),
        "CV_FOLDS": rows,
        "HOLDOUT_GROUND_NET": round(ground_ho, 1),
        "HOLDOUT_RESULTS": results,
        "CONTROL_INVERTED": control,
        "_top_features_gain": {k: round(float(v), 1) for k, v in imp.head(12).to_dict().items()},
        "_next": "まこさんが1案承認 → --score --cut-q=Q --profit-only=B で採点1回（2025-04〜12）",
    }
    json.dump(out, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    _log(f"\n[out] {OUT_JSON}")

    # ---- 採点（GO 後のみ・--score）----
    if DO_SCORE:
        _log(f"\n[採点] 選定案 cut_q={sel_q} profit_only={sel_po} で全学習スナップ再学習 → 全期間ループ → score.py")
        cut_i2 = int(len(X_tr) * 0.85)
        m_full = e14.fit_weighted(X_tr.iloc[:cut_i2], y[:cut_i2], w[:cut_i2],
                                  X_tr.iloc[cut_i2:], y[cut_i2:], w[cut_i2:])
        prob_full = m_full.predict(X_tr, num_iteration=m_full.best_iteration)
        cut = float(np.quantile(prob_full, sel_q))
        ml = {"M": M, "model": m_full, "cut": cut, "profit_only": sel_po, "n_cut": 0}
        trades, _ = run_e15(df, bar_ms, p23, fire_fn, ml=ml)
        tdf = pd.DataFrame(trades)
        for col in ("entry_time", "exit_time"):
            tdf[col] = pd.to_datetime(tdf[col])
        ms.verify_concurrent_budget(trades)
        tdf.to_csv(OUT_CSV, index=False)
        sc = tdf[(tdf["entry_time"] >= SC_START) & (tdf["entry_time"] < SC_END)].reset_index(drop=True)
        r = judge.score(sc)
        _log("\n===== 採点（score.py・cap0.12 ゲート・採点 2025-04〜12）=====")
        _log(f"  AI(E15 刻みML): {r['n_trades']:5d}行 / 月平均 ${r['monthly_avg']:8.2f} / 合計 ${r['total']:8.1f}"
             f"（ML 降り {ml['n_cut']} 回・全期間）")
        if r.get("anomaly"):
            _log("  ⚠️ 異常値・要調査（H12）: " + " / ".join(r["anomaly"]))
        gsc = g[(g["entry_time"] >= SC_START) & (g["entry_time"] < SC_END)].reset_index(drop=True)
        rg_ = judge.score(gsc)
        _log(f"  地面 E0.2: {rg_['n_trades']:5d}件 / 合計 ${rg_['total']:8.1f}")
        _log(f"  固定等分 E0.3: $338（ledger）")
        _log(f"  → AI {'勝ち' if r['total'] > rg_['total'] else '負け'}（地面比 ${r['total'] - rg_['total']:+.1f}）")
        out["SCORE"] = {"cut_q": sel_q, "profit_only": sel_po, "cut": round(cut, 4),
                        "AI_TOTAL": round(float(r["total"]), 2), "GROUND_TOTAL": round(float(rg_["total"]), 2),
                        "N_ML_CUT": int(ml["n_cut"])}
        json.dump(out, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        _log(f"[out] {OUT_CSV}")
        _log(f"[次] python3.13 scripts/priority_rebuild/report.py {OUT_CSV} --start 2025-04-01 --end 2025-12-31 --vs {GROUND}")


if __name__ == "__main__":
    main()
