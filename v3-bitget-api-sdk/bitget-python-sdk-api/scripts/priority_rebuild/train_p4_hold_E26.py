#!/usr/bin/env python3
"""train_p4_hold_E26.py — P4 LONG: 保有中の Exit policy ML（持つ/部分利確/全降り の3アクション・net 最大化）

設計（WORKFLOW 改訂77・next_step.md・まこさん GO 2026-06-12）:
  狙い = P4 の最大出血 時間切れ 111件 −$2,364（採点）。E23 で「Exit 値の entry 時点学習は不成立
    （OOF 改善ゼロ）が、玉ごとに最良 Exit を選べれば +$1,547 の天井がある」と実証済み。その天井は
    entry 時でなく「保有中の経路情報」を使えば取りに行ける。P4 は fat-tail でない（勝ち玉は20分で TP 到達）
    ＝E14（P23 早逃げ −$194）の「勝ち玉の反転を巻き込む」失敗が構造的に起きない。

  ★止血のみにしない（まこさん指示）: アクション空間 = {A0 持つ / A1 1ロット部分利確 / A2 全降り}。
    伸びてる玉の取り逃しを A1 で拾い、順行しない玉を A2 で切る＝両側で net 最大化。E15(P23 部分決済)が
    失敗したのは fat-tail の大勝ちを削ったから＝P4(非fat-tail・伸びた玉に取り逃し)は構造が違うので外さない。

  教師 = 学習期間の P4 地面ポジの保有中スナップ（保有20分以降・E14 機構）。各スナップで3アクションの
    「ここから残ポジを最後まで回した net」を rc._record_trade（V9 の記録関数）で計算＝net 計算に触れない。
      A0 持つ  = その玉の final_net（base 軌道から）
      A2 全降り = exitnow（今 close 成行・即計算）
      A1 部分  = 1ロット今 close 成行 + 残り(k-1)ロットを V9 出口まで前向き sim（新規 add なし＝保守）
    ラベル = net 最大アクション（3クラス）／重み = 最良 − 次善 net。
  特徴量 = 市場（E13 方向系＋ボラ pct＋MTF・ボラ系を方向の主役にしない H15）＋保有経路 POS_STATE。
  運用 = 毎バー（20分以降）ML が選んだアクションを実行（rc._record_trade・score.py が taker/コスト自動計上）。
  自己検査 = ML を全部 A0(持つ) 固定 → P4 地面 trades_p4_E22_ground.csv と件数・net 完全一致 assert。
  対照実験 = prob 逆転（ML が逆の選別）で net が悪化するか＝ML 寄与の検証（E15 の轍＝機械ルールが源泉なら破棄）。
  検証 = purged k-fold をポジション単位。判定 = score.py で P4 地面（採点 月−$76）超え。

★不正防止3点（cat_requirements §8.4-2.9）: 判定は score.py の数字のみ／番人メタ確認／net 計算に触れない。
V9 本体 / gen / score / eval_engine / E14・E0.3 機構は import のみ・改造しない。LONG 化のみ自前。
"""
from __future__ import annotations
import sys
import copy
import json
import pathlib
from decimal import Decimal
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.metrics import roc_auc_score
from scipy.stats import spearmanr

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runner"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import replay_csv as rc                       # noqa: E402
import gen_p23_candidates as gen              # noqa: E402  OHLCV_CSV / 連続モード機構の参照
import score as judge                         # noqa: E402
import ratchet_guards as rg                   # noqa: E402
import train_p23_entry_E8b as e8b             # noqa: E402  方向系複数期間特徴量・期間定数
import train_p23_entry_E8 as e8               # noqa: E402  build_mtf
import train_p23_size_E13 as e13              # noqa: E402  build_vol_feats（ボラ系 pct）
from preload_cache import cached_preload       # noqa: E402  parquet キャッシュ（共通 HIT・数秒）
from strategies.cat_v9_decider import check_entry_priority   # noqa: E402

RAT = e8b.RAT
TRAIN_ENTRY_END = e8b.TRAIN_ENTRY_END
EMBARGO_END = e8b.EMBARGO_END
SC_START, SC_END = e8b.SC_START, e8b.SC_END
GROUND = ROOT / "results" / "priority_rebuild" / "ratchet" / "trades_p4_E22_ground.csv"

PRIORITY = 4
SIDE = "LONG"
SNAP_MIN_AGE_MIN = 20            # E23 oracle 主成分が「20分で順行しない玉の見切り」＝20分以降を判定
N_FOLDS = 5
W_CLIP_Q = 0.99
VOL_DOMINANCE_STOP = 0.5
PURGE_EMBARGO = pd.Timedelta(days=1)

# 3アクション
A_HOLD, A_PARTIAL, A_FULL = 0, 1, 2
POS_STATE_COLS = ["age_min", "unreal_pct", "peak_pct", "dd_from_peak_pct", "add_count", "bars_since_add"]

LPARAMS = dict(objective="multiclass", num_class=3, metric="multi_logloss", learning_rate=0.03,
               num_leaves=15, min_child_samples=200, feature_fraction=0.8, bagging_fraction=0.8,
               bagging_freq=1, lambda_l1=1.0, lambda_l2=1.0, seed=42, verbose=-1)


def _log(m):
    print(m, flush=True)


# ── P4 LONG 連続モード（gen._step の LONG 版・_lots FIFO 台帳つき＝E0.3 流儀）─────────
def _mk_pending_long(df, i, close_p):
    lp = float(Decimal(str(close_p)) * Decimal("0.9999"))        # LONG maker 指値 −0.01%
    g = lambda col: float(df.at[i, col]) if col in df.columns and pd.notna(df.at[i, col]) else float("nan")
    rsi_col = "rsi_long" if "rsi_long" in df.columns else "rsi"
    rss_col = "rsi_slope_long" if "rsi_slope_long" in df.columns else "rsi_slope"
    return {"side": SIDE, "priority": PRIORITY, "limit_price": lp,
            "placed_bar_ms": int(df.at[i, "timestamp_ms"]),
            "adx_at_entry": g("adx"), "bb_mid_slope_at_entry": g("bb_mid_slope"),
            "rsi_at_entry": g(rsi_col), "rsi_slope_at_entry": g(rss_col),
            "stoch_k_at_entry": g("stoch_k"), "stoch_d_at_entry": g("stoch_d"),
            "bb_width_at_entry": g("bb_width")}


def _new_pos(fill_p, ts_ms, unit, adx_val, states, pending):
    return {
        "side": SIDE, "entry_priority": PRIORITY, "entry_price": fill_p,
        "entry_time": ts_ms, "add_count": 1, "size_btc": unit,
        "tp_price": rc._calc_tp_price(SIDE, fill_p, adx_val, _PARAMS, PRIORITY, atr_14=states.get("atr_14", float("nan"))),
        "sl_price": rc._calc_sl_price(SIDE, fill_p, _PARAMS, PRIORITY),
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
        "_unit_size": unit, "_lots": [{"add_time": ts_ms, "add_price": fill_p}], "_last_add_bar": None,
    }


def _refresh_v9_view(pos):
    pos["size_btc"] = len(pos["_lots"]) * float(pos["_unit_size"])
    pos["add_count"] = len(pos["_lots"])


def _emit_portion(trades, pos, add_time_ms, exit_price, exit_reason, exit_ts_ms):
    tmp = copy.copy(pos)
    tmp["size_btc"] = float(pos["_unit_size"])
    tmp["entry_price"] = float(pos["entry_price"])
    tmp["entry_time"] = int(add_time_ms)
    rc._record_trade(trades, tmp, exit_price=exit_price, exit_reason=exit_reason,
                     exit_ts_ms=exit_ts_ms, params=_PARAMS)


def _close_remaining(trades, pos, exit_price, exit_reason, exit_ts_ms, scaleout):
    if not scaleout:
        rc._record_trade(trades, pos, exit_price=exit_price, exit_reason=exit_reason,
                         exit_ts_ms=exit_ts_ms, params=_PARAMS)
        return
    for lot in pos["_lots"]:
        _emit_portion(trades, pos, lot["add_time"], exit_price, exit_reason, exit_ts_ms)
    pos["_lots"] = []


def _pos_state_row(pos, close_p, ts_ms, bar_i):
    avg = float(pos["entry_price"]); size = float(pos["size_btc"])
    notional = avg * size
    unreal_pct = (close_p - avg) / avg * 100.0                          # LONG
    peak_pct = float(pos.get("mfe_usd", 0.0)) / notional * 100.0 if notional > 0 else 0.0
    age_min = (int(ts_ms) - int(pos["entry_time"])) / 60_000.0
    last_add = pos.get("_last_add_bar") or bar_i
    return [age_min, unreal_pct, peak_pct, peak_pct - unreal_pct,
            float(pos["add_count"]), float(bar_i - last_add)]


def _forward_remaining_net(pos_lots, avg, tp_price, sl_price, mfe_usd, mae_usd, min_low, max_high,
                           pos_template, df, arrays, i_start):
    """A1 用: 残り (k) ロットを bar i_start+1 から V9 出口まで前向き sim（新規 add なし＝保守）→ net 合計。"""
    ts_a, cl_a, hi_a, lo_a = arrays
    p = copy.copy(pos_template)
    p["_lots"] = list(pos_lots)
    p["entry_price"] = avg
    p["tp_price"] = tp_price
    p["sl_price"] = sl_price
    p["mfe_usd"] = mfe_usd; p["mae_usd"] = mae_usd
    p["min_low"] = min_low; p["max_high"] = max_high
    _refresh_v9_view(p)
    n = len(df)
    trades = []
    for j in range(i_start + 1, n):
        ts_ms = int(ts_a[j]); close_p = float(cl_a[j]); high_p = float(hi_a[j]); low_p = float(lo_a[j])
        size_b = float(p["size_btc"])
        unreal = (close_p - avg) * size_b
        if unreal > float(p.get("mfe_usd", 0.0)): p["mfe_usd"] = unreal
        if unreal < float(p.get("mae_usd", 0.0)): p["mae_usd"] = unreal
        if high_p > float(p.get("max_high", float("-inf"))): p["max_high"] = high_p
        if low_p < float(p.get("min_low", float("inf"))): p["min_low"] = low_p
        # TP（LONG: high>=tp）
        if high_p >= float(p["tp_price"]):
            _close_remaining(trades, p, float(p["tp_price"]), "TP_FILLED", ts_ms, True); break
        # SL（LONG: low<=sl）
        if p.get("sl_price") is not None and low_p <= float(p["sl_price"]):
            _close_remaining(trades, p, float(p["sl_price"]), "SL_FILLED", ts_ms, True); break
        reason = rc._check_exits_replay(p, close_p, df, j, _PARAMS, ts_ms)
        if reason:
            _close_remaining(trades, p, close_p, reason, ts_ms, True); break
    else:
        _close_remaining(trades, p, float(cl_a[n - 1]), "FORCE_CLOSE_EOD", int(ts_a[n - 1]), True)
    return sum(float(t["net_usd"]) for t in trades)


def _exitnow_all_net(pos, close_p, ts_ms):
    """A2 全降り: 残り全ロットを今 close 成行（ML_EXIT・taker）で閉じた net 合計。"""
    scratch = []
    _close_remaining(scratch, copy.deepcopy(pos), float(close_p), "ML_EXIT", int(ts_ms), True)
    return sum(float(t["net_usd"]) for t in scratch)


def _partial_now_net(pos, close_p, ts_ms, df, arrays, i):
    """A1 部分利確: 最古1ロットを今 close 成行で利確 + 残り(k-1)を V9 で前向き sim。"""
    if len(pos["_lots"]) < 2:
        return None
    scratch = []
    oldest = pos["_lots"][0]
    _emit_portion(scratch, pos, oldest["add_time"], float(close_p), "ML_EXIT", int(ts_ms))
    realized = float(scratch[-1]["net_usd"])
    rest = _forward_remaining_net(pos["_lots"][1:], float(pos["entry_price"]), float(pos["tp_price"]),
                                  pos.get("sl_price"), float(pos.get("mfe_usd", 0.0)),
                                  float(pos.get("mae_usd", 0.0)), float(pos.get("min_low", float("inf"))),
                                  float(pos.get("max_high", float("-inf"))), pos, df, arrays, i)
    return realized + rest


# ── 連続モード本体（collect=教師収集 / model=運用）───────────────────────────────
def run_loop(df, arrays, bar_ms, initial_fn, M=None, model=None, feat_cols=None,
             collect=False, invert=False):
    ts_a, cl_a, hi_a, lo_a = arrays
    state = {"pos": None, "pending": None, "trades": []}
    snaps, cur_snaps = [], []
    n_action = {A_PARTIAL: 0, A_FULL: 0}
    n = len(df)
    for i in range(rc.CANDLE_WARMUP, n):
        n_before = len(state["trades"])
        pos = state["pos"]; pending = state["pending"]
        ts_ms = int(ts_a[i]); close_p = float(cl_a[i]); high_p = float(hi_a[i]); low_p = float(lo_a[i])
        unit = float(_PARAMS.get(f"P{PRIORITY}_POSITION_SIZE_BTC", _PARAMS["LONG_POSITION_SIZE_BTC"]))

        # 1. pending fill（LONG: low<=limit）
        if pending is not None:
            if max(0, (ts_ms - int(pending["placed_bar_ms"])) // bar_ms) >= rc.PENDING_TTL_BARS:
                pending = None
            elif low_p <= float(pending["limit_price"]):
                fill_p = float(pending["limit_price"]); adx_val = float(pending.get("adx_at_entry", 0.0))
                states = rc._calc_entry_states(df, i, ts_ms)
                if pos is None:
                    pos = _new_pos(fill_p, ts_ms, unit, adx_val, states, pending)
                    pos["_last_add_bar"] = i
                else:
                    old_sz, old_p = float(pos["size_btc"]), float(pos["entry_price"])
                    new_sz = old_sz + unit
                    new_avg = (old_p * old_sz + fill_p * unit) / new_sz
                    pos["entry_price"] = new_avg
                    pos["_lots"].append({"add_time": ts_ms, "add_price": fill_p})
                    pos["_last_add_bar"] = i
                    _refresh_v9_view(pos)
                    pos["tp_price"] = rc._calc_tp_price(SIDE, new_avg, adx_val, _PARAMS, PRIORITY,
                                                        atr_14=states.get("atr_14", float("nan")))
                    pos["sl_price"] = rc._calc_sl_price(SIDE, new_avg, _PARAMS, PRIORITY) if pos["add_count"] >= 2 else None
                pending = None

        # 2. MFE/MAE/極値（LONG）
        if pos is not None:
            avg, size_b = float(pos["entry_price"]), float(pos["size_btc"])
            unreal = (close_p - avg) * size_b
            if unreal > float(pos.get("mfe_usd", 0.0)): pos["mfe_usd"] = unreal
            if unreal < float(pos.get("mae_usd", 0.0)): pos["mae_usd"] = unreal
            if high_p > float(pos.get("max_high", float("-inf"))): pos["max_high"] = high_p
            if low_p < float(pos.get("min_low", float("inf"))): pos["min_low"] = low_p

        # 2.5 ★保有中アクション（20分以降）── collect: 3アクション net を記録 / model: ML が選んで実行
        if pos is not None:
            age_min = (ts_ms - int(pos["entry_time"])) / 60_000.0
            if age_min >= SNAP_MIN_AGE_MIN:
                if collect:
                    net_hold = None  # position close 時に final_net で埋める
                    net_full = _exitnow_all_net(pos, close_p, ts_ms)
                    net_part = _partial_now_net(pos, close_p, ts_ms, df, arrays, i)
                    cur_snaps.append({
                        "bar_i": i, "ts": ts_ms, "pos_entry": int(pos["entry_time"]),
                        "state": _pos_state_row(pos, close_p, ts_ms, i),
                        "net_full": net_full, "net_part": net_part,
                    })
                elif model is not None:
                    row = np.concatenate([M[i], np.asarray(_pos_state_row(pos, close_p, ts_ms, i), dtype=np.float32)])
                    proba = model.predict(row.reshape(1, -1))[0]      # [p_hold, p_part, p_full]
                    act = int(np.argmax(proba))
                    if invert:                                        # 対照実験: hold 以外を逆向きに
                        act = {A_HOLD: A_HOLD, A_PARTIAL: A_FULL, A_FULL: A_PARTIAL}[act]
                    if act == A_FULL:
                        _close_remaining(state["trades"], pos, close_p, "ML_EXIT", ts_ms, pos.get("_partial_done", False))
                        n_action[A_FULL] += 1
                        state["pos"] = None; state["pending"] = None
                        if collect:
                            pass
                        # position 終了 → cur_snaps 確定は下の closeブロックに任せず即（collect でないので不要）
                        continue
                    elif act == A_PARTIAL and len(pos["_lots"]) >= 2:
                        oldest = pos["_lots"].pop(0)
                        _emit_portion(state["trades"], pos, oldest["add_time"], close_p, "ML_EXIT", ts_ms)
                        _refresh_v9_view(pos)
                        pos["_partial_done"] = True
                        n_action[A_PARTIAL] += 1

        # 3. TP（LONG: high>=tp）
        if pos is not None and high_p >= float(pos["tp_price"]):
            _close_remaining(state["trades"], pos, float(pos["tp_price"]), "TP_FILLED", ts_ms, pos.get("_partial_done", False))
            pos = None
        # 4. SL（LONG: low<=sl）
        if pos is not None and pos.get("sl_price") is not None and low_p <= float(pos["sl_price"]):
            _close_remaining(state["trades"], pos, float(pos["sl_price"]), "SL_FILLED", ts_ms, pos.get("_partial_done", False))
            pos = None
        # 6. _check_exits_replay（V9 出口）
        if pos is not None:
            reason = rc._check_exits_replay(pos, close_p, df, i, _PARAMS, ts_ms)
            if reason:
                _close_remaining(state["trades"], pos, close_p, reason, ts_ms, pos.get("_partial_done", False))
                pos = None

        # 7. エントリー / ADD（部分利確で枠が空けば V9 発火で再 add）
        fire_add = (check_entry_priority(i, df, _PARAMS) == PRIORITY)
        want_initial = (pos is None and pending is None and initial_fn(i))
        if (fire_add and pos is not None) or want_initial:
            if pos is not None:
                if len(pos["_lots"]) >= int(_PARAMS.get("MAX_ADDS_BY_PRIORITY", {}).get(str(PRIORITY), 5)):
                    pass
                elif pending is None:
                    pending = _mk_pending_long(df, i, close_p)
            elif pending is None:
                pending = _mk_pending_long(df, i, close_p)

        state["pos"], state["pending"] = pos, pending

        if collect and len(state["trades"]) > n_before and pos is None:
            final_net = float(state["trades"][-1]["net_usd"])
            # final_net は「最後に閉じたロット」の net。A0(持つ)の評価は玉全体の最終 net 合計が必要だが、
            # collect モードは V9 軌道（部分利確なし＝1ポジ満玉一括）なので最後の1行が玉全体の net。
            for s in cur_snaps:
                s["net_hold"] = final_net
            snaps.extend(cur_snaps); cur_snaps = []

    if state["pos"] is not None:
        _close_remaining(state["trades"], state["pos"], float(cl_a[len(df) - 1]),
                         "FORCE_CLOSE_EOD", int(ts_a[len(df) - 1]), state["pos"].get("_partial_done", False))
        if collect:
            final_net = float(state["trades"][-1]["net_usd"])
            for s in cur_snaps:
                s["net_hold"] = final_net
            snaps.extend(cur_snaps)
    return state["trades"], snaps, n_action


def build_market_matrix(df, ohlcv):
    mp = e8b.build_multiperiod(ohlcv)
    vol = e13.build_vol_feats(ohlcv)
    bt = pd.to_datetime(df["timestamp_ms"], unit="ms")
    M_mp = mp.reindex(bt).reset_index(drop=True)
    M_vol = vol.reindex(bt).reset_index(drop=True)
    mtf = e8.build_mtf(ohlcv, pd.Series(bt))
    M = pd.concat([M_mp, M_vol, mtf.reset_index(drop=True)], axis=1)
    leaked = e8b.BANNED & set(M.columns)
    assert not leaked, f"H2/H6 leak: {leaked}"
    bad = [c for c in M.columns if "bb_slope" in c and "pct" not in c]
    assert not bad, f"H6 違反: {bad}"
    return M.astype(np.float32)


def purged_folds_by_pos(sd, n_folds):
    pos_tbl = sd.groupby("pos_entry").agg(p_start=("ts_dt", "min"), p_end=("ts_dt", "max")).reset_index()
    pos_tbl = pos_tbl.sort_values("p_start").reset_index(drop=True)
    for b in np.array_split(pos_tbl.index.values, n_folds):
        if not len(b):
            continue
        v_pos = set(pos_tbl.loc[b, "pos_entry"])
        v0, v1 = pos_tbl.loc[b, "p_start"].min(), pos_tbl.loc[b, "p_end"].max()
        ov = pos_tbl[(pos_tbl.p_start <= v1 + PURGE_EMBARGO) & (pos_tbl.p_end >= v0 - PURGE_EMBARGO)]
        t_pos = set(pos_tbl.pos_entry) - set(ov.pos_entry)
        vi = sd.index[sd.pos_entry.isin(v_pos)].values
        ti = sd.index[sd.pos_entry.isin(t_pos)].values
        yield ti, vi, (v0, v1)


def main():
    global _PARAMS
    SMOKE = "--smoke" in sys.argv
    _log("[E26] P4 保有中 Exit policy ML（持つ/部分利確/全降り・地面 P4 採点 月−$76）")

    rg.assert_no_future_ref(pathlib.Path(__file__).read_text())
    rg.assert_period_split(TRAIN_ENTRY_END, SC_START)

    base = rc._load_params()
    _PARAMS = dict(base)
    for k in list(_PARAMS):
        if k.startswith("ENABLE_P") and k.endswith(("_LONG", "_SHORT")):
            _PARAMS[k] = (k == f"ENABLE_P{PRIORITY}_LONG")
    df, _ = cached_preload(str(gen.OHLCV_CSV), _PARAMS)
    bar_ms = int(df.at[1, "timestamp_ms"] - df.at[0, "timestamp_ms"])
    arrays = (df["timestamp_ms"].to_numpy(), df["close"].to_numpy(),
              df["high_raw"].to_numpy(), df["low_raw"].to_numpy())
    ohlcv = pd.read_csv(e8b.OHLCV); ohlcv["timestamp"] = pd.to_datetime(ohlcv["timestamp"])
    _log(f"[load] bars={len(df)}")
    fire_fn = lambda i: (check_entry_priority(i, df, _PARAMS) == PRIORITY)

    # ---- 自己検査: 教師収集パス（ML 発動なし＝V9 軌道）が地面と一致 ----
    base_trades, snaps, _ = run_loop(df, arrays, bar_ms, fire_fn, collect=True)
    g = pd.read_csv(GROUND)
    bsum, gsum = sum(float(t["net_usd"]) for t in base_trades), float(g["net_usd"].sum())
    _log(f"[自己検査] 教師パス: {len(base_trades)}件/${bsum:.2f} vs 地面CSV {len(g)}件/${gsum:.2f}")
    assert len(base_trades) == len(g) and abs(bsum - gsum) < 0.01, "自己検査 FAIL: 教師パスが地面と不一致"
    _log("[自己検査] ✅ 一致（LONG 移植は正しい・収集は軌道を変えていない）")

    Mdf = build_market_matrix(df, ohlcv)
    feat_cols = list(Mdf.columns) + POS_STATE_COLS
    M = Mdf.to_numpy(dtype=np.float32)

    # ---- 教師ラベル: 3アクションの net → argmax ----
    rows = []
    for s in snaps:
        if "net_hold" not in s:
            continue
        nets = {A_HOLD: s["net_hold"], A_FULL: s["net_full"]}
        if s["net_part"] is not None:
            nets[A_PARTIAL] = s["net_part"]
        best = max(nets, key=nets.get)
        srt = sorted(nets.values(), reverse=True)
        margin = srt[0] - srt[1] if len(srt) > 1 else 0.0
        rows.append({"bar_i": s["bar_i"], "ts_dt": pd.to_datetime(s["ts"], unit="ms"),
                     "pos_entry": s["pos_entry"], "y": best, "w": abs(margin), "state": s["state"]})
    sd = pd.DataFrame(rows)
    pos_dt = pd.to_datetime(sd["pos_entry"], unit="ms")
    is_tr = (pos_dt < TRAIN_ENTRY_END) & (sd["ts_dt"] < EMBARGO_END)
    sd = sd[is_tr.values].reset_index(drop=True)
    if SMOKE:
        keep = sd["pos_entry"].drop_duplicates().tail(80)
        sd = sd[sd["pos_entry"].isin(set(keep))].reset_index(drop=True)
        _log("[SMOKE] 末尾80ポジに制限")
    Xs = np.concatenate([M[sd["bar_i"].values],
                         np.asarray(list(sd["state"]), dtype=np.float32)], axis=1)
    X = pd.DataFrame(Xs, columns=feat_cols)
    y = sd["y"].to_numpy()
    clip = float(sd["w"].quantile(W_CLIP_Q)) or 1.0
    w = sd["w"].clip(upper=clip).to_numpy()
    w = np.where(w <= 0, 1e-6, w)
    dist = pd.Series(y).value_counts(normalize=True).round(3).to_dict()
    _log(f"[教師] スナップ {len(sd)} 枚 / ポジ {sd['pos_entry'].nunique()} 本 / "
         f"アクション分布(0持つ/1部分/2全降り)={dist}")

    # ---- purged k-fold 健全性 ----
    oof_rows, fold_rows = [], []
    min_ti, min_vi = (40, 15) if SMOKE else (500, 100)
    for fi, (ti, vi, (v0, v1)) in enumerate(purged_folds_by_pos(sd, 2 if SMOKE else N_FOLDS)):
        if len(ti) < min_ti or len(vi) < min_vi or len(np.unique(y[ti])) < 2:
            continue
        dtr = lgb.Dataset(X.iloc[ti], label=y[ti], weight=w[ti])
        m = lgb.train(LPARAMS, dtr, num_boost_round=400)
        proba = m.predict(X.iloc[vi])
        pred = proba.argmax(1)
        acc = float((pred == y[vi]).mean())
        # 「降りる系(1/2)を当てられるか」を AUC で（hold=0 vs それ以外）
        try:
            auc = roc_auc_score((y[vi] != A_HOLD).astype(int), 1 - proba[:, A_HOLD])
        except ValueError:
            auc = float("nan")
        fold_rows.append({"fold": fi, "val": f"{v0.date()}〜{v1.date()}", "n": len(vi),
                          "acc": round(acc, 3), "auc_act_vs_hold": round(float(auc), 3)})
        _log(f"[fold{fi}] {v0.date()}〜{v1.date()} n={len(vi)} acc={acc:.3f} auc(降りvs持つ)={auc:.3f}")
    assert fold_rows, "有効 fold 0"

    # ---- 本学習 → ボラ支配チェック ----
    cut_i = int(len(X) * 0.85)
    dtr = lgb.Dataset(X.iloc[:cut_i], label=y[:cut_i], weight=w[:cut_i])
    dva = lgb.Dataset(X.iloc[cut_i:], label=y[cut_i:], weight=w[cut_i:], reference=dtr)
    m_full = lgb.train(LPARAMS, dtr, num_boost_round=2000, valid_sets=[dva],
                       callbacks=[lgb.early_stopping(80, verbose=False)])
    vr = rg.report_vol_importance(dict(zip(m_full.feature_name(), m_full.feature_importance("gain"))))
    imp = pd.Series(m_full.feature_importance("gain"), index=feat_cols).sort_values(ascending=False)
    _log(f"\n[ボラ寄与] vol_share={vr['vol_share']}（停止 {VOL_DOMINANCE_STOP}）/ top5={vr['top']}")
    _log("[重要特徴 top15]\n" + imp.head(15).to_string())
    if float(vr["vol_share"]) > VOL_DOMINANCE_STOP:
        _log("⛔ ボラ支配 → 採点せず停止・まこさんに報告")
        return

    if SMOKE:
        _log("[SMOKE] 完了（自己検査・教師・健全性・本学習まで・採点は本番のみ）")
        return

    # ---- 本番運用 + 対照実験 → score.py 採点 ----
    def _score(trades):
        t = pd.DataFrame(trades)
        for c in ("entry_time", "exit_time"):
            t[c] = pd.to_datetime(t[c])
        sc = t[(t["entry_time"] >= SC_START) & (t["entry_time"] < SC_END)].reset_index(drop=True)
        return judge.score(sc), t

    trades, _, nact = run_loop(df, arrays, bar_ms, fire_fn, M=M, model=m_full, feat_cols=feat_cols)
    r, tdf = _score(trades)
    tdf.to_csv(RAT / "trades_p4_E26_hold.csv", index=False)
    inv_trades, _, _ = run_loop(df, arrays, bar_ms, fire_fn, M=M, model=m_full, feat_cols=feat_cols, invert=True)
    r_inv, _ = _score(inv_trades)
    g["entry_time"] = pd.to_datetime(g["entry_time"]); g["exit_time"] = pd.to_datetime(g["exit_time"])
    gsc = g[(g["entry_time"] >= SC_START) & (g["entry_time"] < SC_END)].reset_index(drop=True)
    rg_ = judge.score(gsc)

    _log("\n===== 採点（score.py・cap0.12・採点 2025-04〜12）=====")
    _log(f"  AI(3アクション): {r['n_trades']:5d}件 / 月平均 ${r['monthly_avg']:8.2f} / 合計 ${r['total']:8.1f}"
         f"（部分{nact[A_PARTIAL]}・全降り{nact[A_FULL]}）")
    _log(f"  対照(prob逆転)  : 合計 ${r_inv['total']:8.1f}（本命がこれより良ければ ML 寄与あり）")
    _log(f"  地面 P4 E22     : {rg_['n_trades']:5d}件 / 合計 ${rg_['total']:8.1f}")
    _log(f"  → AI {'勝ち' if r['total'] > rg_['total'] else '負け'}（差 ${r['total'] - rg_['total']:+.1f}）"
         f" / ML寄与 {'あり' if r['total'] > r_inv['total'] else 'なし(機械ルール疑い)'}")
    if r.get("anomaly"):
        _log("  ⚠️ 異常値・要調査（H12）: " + " / ".join(r["anomaly"]))

    out = {"_source": "train_p4_hold_E26.py（P4 保有中 Exit policy・3アクション）",
           "ACTIONS_TAKEN": {"partial": int(nact[A_PARTIAL]), "full": int(nact[A_FULL])},
           "VOL_SHARE": vr["vol_share"], "FOLDS": fold_rows,
           "AI_TOTAL": round(float(r["total"]), 2), "INVERT_TOTAL": round(float(r_inv["total"]), 2),
           "GROUND_TOTAL": round(float(rg_["total"]), 2),
           "_top_features": {k: round(float(v), 1) for k, v in imp.head(12).to_dict().items()}}
    json.dump(out, open(RAT / "p4_learned_params_E26.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    _log(f"\n[out] {RAT / 'trades_p4_E26_hold.csv'} / p4_learned_params_E26.json")


if __name__ == "__main__":
    main()
