#!/usr/bin/env python3
"""train_p4_meta_E27.py — P4 メタラベリング Phase 1（判別力測定・採点なし）

設計（まこさん GO 2026-06-12・E27 設計プレゼン）:
  一次モデル = V9 P4 押し目 Entry（固定・fire_arr）。Exit も V9 のまま（不変）＝1ターン1変更。
  ラベル = ポジション単位 net>0（V9 実 Exit で利確に辿り着いたか・自作 net 禁止・rc._record_trade の net）。
    add数ラベルは不採用（学習/採点で不安定＝add5 学習−245/採点+124）。
  特徴量 = entry サイン時点の 上位足 regime 主役（MTF）+ 5m 押し目 + 複数期間。
    ボラ系(atr)は方向主役にしない・importance で監視（H15）。regime は分類でなく生値を渡す。
  二次モデル = LightGBM 二値・purged k-fold（ポジ単位・embargo 1day）・sample weight=|net|・class_weight。
    学習サンプルが少ない（〜526ポジ）→ min_child_samples 大きめ・OOF を厳しく見る。
  Phase 1 = 学習期間 OOF で AUC + prob×net 相関を測る（entry 時点で利確到達が見分くか）。
    低くても撤退でなく「何が足りないか診断して立たせる手を尽くす」（まこさん指示）。
  Phase 2（AUC が立ったら別途・本スクリプト外）= cut / E13型サイズ配分を OOF で比較 → 採点1回。
  自己検査 = collect の trades が地面 trades_p4_E22_ground.csv と件数・net 一致（V9 軌道を変えていない）。

★不正防止3点（cat_requirements §8.4-2.9）: 判定は score.py（Phase2）/ net は V9 記録に触れない /
  番人メタ確認。V9 本体 / 審判 / E26 機構（fire_arr/MTF/purged）は import のみ・改造しない。
"""
from __future__ import annotations
import sys
import json
import pathlib
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
import gen_p23_candidates as gen              # noqa: E402
import score as judge                         # noqa: E402  Phase2 採点（固定審判・改造禁止）
import ratchet_guards as rg                   # noqa: E402
import train_p4_hold_E26 as e26               # noqa: E402  機構流用（fire_arr/MTF/purged/_new_pos 等）
import train_p23_entry_E8b as e8b             # noqa: E402  RAT / 期間定数
from preload_cache import cached_preload       # noqa: E402
from strategies.cat_v9_decider import check_entry_priority   # noqa: E402

RAT = e8b.RAT
TRAIN_ENTRY_END = e8b.TRAIN_ENTRY_END
EMBARGO_END = e8b.EMBARGO_END
GROUND = ROOT / "results" / "priority_rebuild" / "ratchet" / "trades_p4_E22_ground.csv"

PRIORITY = 4
SIDE = "LONG"
N_FOLDS = 5
W_CLIP_Q = 0.99
VOL_DOMINANCE_STOP = 0.5
PURGE_EMBARGO = pd.Timedelta(days=1)

LPARAMS = dict(objective="binary", metric="auc", learning_rate=0.03,
               num_leaves=15, min_child_samples=50, feature_fraction=0.8, bagging_fraction=0.8,
               bagging_freq=1, lambda_l1=1.0, lambda_l2=1.0, seed=42, verbose=-1)


def _log(m):
    print(m, flush=True)


# ── V9 P4 連続モード（ML なし）: 各ポジの (sig_bar, sig_ts, net) を収集 ───────────
#   sig_bar = そのポジの最初の押し目発火 bar（一次シグナル時点・推論で取得可能）。
#   net     = ポジの合計 net（V9 実 Exit・rc._record_trade・部分利確なし＝1ポジ1行）。
#   collect の trades は自己検査用（地面と一致を assert）。
def collect_pos(df, arrays, bar_ms, fire_arr):
    ts_a, cl_a, hi_a, lo_a = arrays
    state = {"pos": None, "pending": None, "trades": []}
    recs = []
    n = len(df)
    for i in range(rc.CANDLE_WARMUP, n):
        pos = state["pos"]; pending = state["pending"]
        ts_ms = int(ts_a[i]); close_p = float(cl_a[i]); high_p = float(hi_a[i]); low_p = float(lo_a[i])
        unit = float(e26._PARAMS.get(f"P{PRIORITY}_POSITION_SIZE_BTC", e26._PARAMS["LONG_POSITION_SIZE_BTC"]))

        # 1. pending fill（LONG: low<=limit）
        if pending is not None:
            if max(0, (ts_ms - int(pending["placed_bar_ms"])) // bar_ms) >= rc.PENDING_TTL_BARS:
                pending = None
            elif low_p <= float(pending["limit_price"]):
                fill_p = float(pending["limit_price"]); adx_val = float(pending.get("adx_at_entry", 0.0))
                states = rc._calc_entry_states(df, i, ts_ms)
                if pos is None:
                    pos = e26._new_pos(fill_p, ts_ms, unit, adx_val, states, pending)
                    pos["sig_bar"] = int(pending["sig_bar"]); pos["_last_add_bar"] = i
                else:
                    old_sz, old_p = float(pos["size_btc"]), float(pos["entry_price"])
                    new_sz = old_sz + unit
                    new_avg = (old_p * old_sz + fill_p * unit) / new_sz
                    pos["entry_price"] = new_avg
                    pos["_lots"].append({"add_time": ts_ms, "add_price": fill_p})
                    pos["_last_add_bar"] = i
                    e26._refresh_v9_view(pos)
                    pos["tp_price"] = rc._calc_tp_price(SIDE, new_avg, adx_val, e26._PARAMS, PRIORITY,
                                                        atr_14=states.get("atr_14", float("nan")))
                    pos["sl_price"] = rc._calc_sl_price(SIDE, new_avg, e26._PARAMS, PRIORITY) if pos["add_count"] >= 2 else None
                pending = None

        # 2. MFE/MAE/極値（LONG）
        if pos is not None:
            avg, size_b = float(pos["entry_price"]), float(pos["size_btc"])
            unreal = (close_p - avg) * size_b
            if unreal > float(pos.get("mfe_usd", 0.0)): pos["mfe_usd"] = unreal
            if unreal < float(pos.get("mae_usd", 0.0)): pos["mae_usd"] = unreal
            if high_p > float(pos.get("max_high", float("-inf"))): pos["max_high"] = high_p
            if low_p < float(pos.get("min_low", float("inf"))): pos["min_low"] = low_p

        # 3. TP（LONG: high>=tp）
        if pos is not None and high_p >= float(pos["tp_price"]):
            sb = int(pos["sig_bar"])
            e26._close_remaining(state["trades"], pos, float(pos["tp_price"]), "TP_FILLED", ts_ms, False)
            recs.append((sb, int(ts_a[sb]), float(state["trades"][-1]["net_usd"]))); pos = None
        # 4. SL（LONG: low<=sl）
        if pos is not None and pos.get("sl_price") is not None and low_p <= float(pos["sl_price"]):
            sb = int(pos["sig_bar"])
            e26._close_remaining(state["trades"], pos, float(pos["sl_price"]), "SL_FILLED", ts_ms, False)
            recs.append((sb, int(ts_a[sb]), float(state["trades"][-1]["net_usd"]))); pos = None
        # 6. _check_exits_replay（V9 出口）
        if pos is not None:
            reason = rc._check_exits_replay(pos, close_p, df, i, e26._PARAMS, ts_ms)
            if reason:
                sb = int(pos["sig_bar"])
                e26._close_remaining(state["trades"], pos, close_p, reason, ts_ms, False)
                recs.append((sb, int(ts_a[sb]), float(state["trades"][-1]["net_usd"]))); pos = None

        # 7. エントリー / ADD（V9 押し目発火 = fire_arr[i]）
        fire_i = bool(fire_arr[i])
        want_initial = (pos is None and pending is None and fire_i)
        if (fire_i and pos is not None) or want_initial:
            if pos is not None:
                if len(pos["_lots"]) >= int(e26._PARAMS.get("MAX_ADDS_BY_PRIORITY", {}).get(str(PRIORITY), 5)):
                    pass
                elif pending is None:
                    pending = e26._mk_pending_long(df, i, close_p); pending["sig_bar"] = i
            elif pending is None:
                pending = e26._mk_pending_long(df, i, close_p); pending["sig_bar"] = i

        state["pos"], state["pending"] = pos, pending

    if state["pos"] is not None:
        pos = state["pos"]; sb = int(pos["sig_bar"])
        e26._close_remaining(state["trades"], pos, float(cl_a[n - 1]), "FORCE_CLOSE_EOD", int(ts_a[n - 1]), False)
        recs.append((sb, int(ts_a[sb]), float(state["trades"][-1]["net_usd"])))
    return state["trades"], recs


# ── Phase 2 運用: 初回 entry を二次 prob でゲート（add は V9 のまま・cut）───────────
#   want_initial（pos なし・押し目発火）時のみ prob≥thr で入る／add（pos あり）は無ゲート。
#   ラベルがポジ単位（最初の押し目）＝ゲートも最初の押し目に当てる（構造一致）。
#   invert=True は対照実験（prob<thr の「悪い押し目」で入る）＝ML 寄与の検証。
def operation(df, arrays, bar_ms, fire_arr, M, model, thr, invert=False):
    ts_a, cl_a, hi_a, lo_a = arrays
    state = {"pos": None, "pending": None, "trades": []}
    n = len(df)
    for i in range(rc.CANDLE_WARMUP, n):
        pos = state["pos"]; pending = state["pending"]
        ts_ms = int(ts_a[i]); close_p = float(cl_a[i]); high_p = float(hi_a[i]); low_p = float(lo_a[i])
        unit = float(e26._PARAMS.get(f"P{PRIORITY}_POSITION_SIZE_BTC", e26._PARAMS["LONG_POSITION_SIZE_BTC"]))

        if pending is not None:
            if max(0, (ts_ms - int(pending["placed_bar_ms"])) // bar_ms) >= rc.PENDING_TTL_BARS:
                pending = None
            elif low_p <= float(pending["limit_price"]):
                fill_p = float(pending["limit_price"]); adx_val = float(pending.get("adx_at_entry", 0.0))
                states = rc._calc_entry_states(df, i, ts_ms)
                if pos is None:
                    pos = e26._new_pos(fill_p, ts_ms, unit, adx_val, states, pending); pos["_last_add_bar"] = i
                else:
                    old_sz, old_p = float(pos["size_btc"]), float(pos["entry_price"])
                    new_sz = old_sz + unit; new_avg = (old_p * old_sz + fill_p * unit) / new_sz
                    pos["entry_price"] = new_avg
                    pos["_lots"].append({"add_time": ts_ms, "add_price": fill_p}); pos["_last_add_bar"] = i
                    e26._refresh_v9_view(pos)
                    pos["tp_price"] = rc._calc_tp_price(SIDE, new_avg, adx_val, e26._PARAMS, PRIORITY, atr_14=states.get("atr_14", float("nan")))
                    pos["sl_price"] = rc._calc_sl_price(SIDE, new_avg, e26._PARAMS, PRIORITY) if pos["add_count"] >= 2 else None
                pending = None

        if pos is not None:
            avg, size_b = float(pos["entry_price"]), float(pos["size_btc"])
            unreal = (close_p - avg) * size_b
            if unreal > float(pos.get("mfe_usd", 0.0)): pos["mfe_usd"] = unreal
            if unreal < float(pos.get("mae_usd", 0.0)): pos["mae_usd"] = unreal
            if high_p > float(pos.get("max_high", float("-inf"))): pos["max_high"] = high_p
            if low_p < float(pos.get("min_low", float("inf"))): pos["min_low"] = low_p

        if pos is not None and high_p >= float(pos["tp_price"]):
            e26._close_remaining(state["trades"], pos, float(pos["tp_price"]), "TP_FILLED", ts_ms, False); pos = None
        if pos is not None and pos.get("sl_price") is not None and low_p <= float(pos["sl_price"]):
            e26._close_remaining(state["trades"], pos, float(pos["sl_price"]), "SL_FILLED", ts_ms, False); pos = None
        if pos is not None:
            reason = rc._check_exits_replay(pos, close_p, df, i, e26._PARAMS, ts_ms)
            if reason:
                e26._close_remaining(state["trades"], pos, close_p, reason, ts_ms, False); pos = None

        fire_i = bool(fire_arr[i])
        if fire_i and pos is not None:                       # ADD（無ゲート＝V9）
            if len(pos["_lots"]) < int(e26._PARAMS.get("MAX_ADDS_BY_PRIORITY", {}).get(str(PRIORITY), 5)) and pending is None:
                pending = e26._mk_pending_long(df, i, close_p)
        elif pos is None and pending is None and fire_i:     # 初回 ENTRY（二次 prob ゲート）
            prob = float(model.predict(M[i:i + 1])[0])
            enter = (prob < thr) if invert else (prob >= thr)
            if enter:
                pending = e26._mk_pending_long(df, i, close_p)

        state["pos"], state["pending"] = pos, pending

    if state["pos"] is not None:
        e26._close_remaining(state["trades"], state["pos"], float(cl_a[n - 1]), "FORCE_CLOSE_EOD", int(ts_a[n - 1]), False)
    return state["trades"]


def main():
    SMOKE = "--smoke" in sys.argv
    _log("[E27] P4 メタラベリング Phase 1（一次=V9押し目・ラベル=ポジ単位net>0・採点なし・判別力測定）")

    rg.assert_no_future_ref(pathlib.Path(__file__).read_text())
    rg.assert_period_split(TRAIN_ENTRY_END, e8b.SC_START)

    base = rc._load_params()
    e26._PARAMS = dict(base)
    for k in list(e26._PARAMS):
        if k.startswith("ENABLE_P") and k.endswith(("_LONG", "_SHORT")):
            e26._PARAMS[k] = (k == f"ENABLE_P{PRIORITY}_LONG")
    df, _ = cached_preload(str(gen.OHLCV_CSV), e26._PARAMS)
    bar_ms = int(df.at[1, "timestamp_ms"] - df.at[0, "timestamp_ms"])
    arrays = (df["timestamp_ms"].to_numpy(), df["close"].to_numpy(),
              df["high_raw"].to_numpy(), df["low_raw"].to_numpy())
    ohlcv = pd.read_csv(e8b.OHLCV); ohlcv["timestamp"] = pd.to_datetime(ohlcv["timestamp"])
    _log(f"[load] bars={len(df)}")

    fire_arr = e26.build_fire_arr(df, e26._PARAMS)

    # ---- 自己検査: collect が地面と一致（V9 軌道を変えていない）----
    trades, recs = collect_pos(df, arrays, bar_ms, fire_arr)
    g = pd.read_csv(GROUND)
    bsum, gsum = sum(float(t["net_usd"]) for t in trades), float(g["net_usd"].sum())
    _log(f"[自己検査] collect: {len(trades)}件/${bsum:.2f} vs 地面CSV {len(g)}件/${gsum:.2f} / ポジ収集 {len(recs)}本")
    assert len(trades) == len(g) and abs(bsum - gsum) < 0.01, "自己検査 FAIL: collect が地面と不一致"
    assert len(recs) == len(trades), "ポジ収集数と trades 数が不一致"
    _log("[自己検査] ✅ 一致")

    # ---- 特徴量行列（上位足 MTF + 5m + 複数期間 + ボラ pct）----
    Mdf = e26.build_market_matrix(df, ohlcv)
    feat_cols = list(Mdf.columns)
    M = Mdf.to_numpy(dtype=np.float32)

    # ---- ポジ単位 教師（sig_bar 時点の特徴・ラベル net>0・重み |net|）----
    rdf = pd.DataFrame(recs, columns=["bar_i", "sig_ts", "net"])
    rdf["ts_dt"] = pd.to_datetime(rdf["sig_ts"], unit="ms")
    rdf["pos_entry"] = rdf["bar_i"]
    rdf["y"] = (rdf["net"] > 0).astype(int)
    is_tr = rdf["ts_dt"] < TRAIN_ENTRY_END
    sd = rdf[is_tr.values].reset_index(drop=True)
    if SMOKE:
        sd = sd.tail(120).reset_index(drop=True)
        _log("[SMOKE] 末尾120ポジに制限")
    X = pd.DataFrame(M[sd["bar_i"].values], columns=feat_cols)
    y = sd["y"].to_numpy()
    clip = float(sd["net"].abs().quantile(W_CLIP_Q)) or 1.0
    w = sd["net"].abs().clip(upper=clip).to_numpy()
    w = np.where(w <= 0, 1e-6, w)
    spw = float((y == 0).sum()) / max(1, int((y == 1).sum()))   # class_weight balanced 相当
    base_rate = float(y.mean())
    _log(f"[教師] 学習期間ポジ {len(sd)}本 / 勝率(net>0) {base_rate:.3f} / scale_pos_weight {spw:.2f}")

    # ---- purged k-fold OOF（ポジ単位）----
    oof = np.full(len(sd), np.nan)
    fold_rows = []
    min_ti, min_vi = (40, 15) if SMOKE else (150, 40)
    lp = dict(LPARAMS); lp["scale_pos_weight"] = spw
    for fi, (ti, vi, (v0, v1)) in enumerate(e26.purged_folds_by_pos(sd, 2 if SMOKE else N_FOLDS)):
        if len(ti) < min_ti or len(vi) < min_vi or len(np.unique(y[ti])) < 2:
            continue
        dtr = lgb.Dataset(X.iloc[ti], label=y[ti], weight=w[ti])
        m = lgb.train(lp, dtr, num_boost_round=300)
        p = m.predict(X.iloc[vi])
        oof[vi] = p
        try:
            auc = roc_auc_score(y[vi], p)
        except ValueError:
            auc = float("nan")
        fold_rows.append({"fold": fi, "val": f"{v0.date()}〜{v1.date()}", "n": int(len(vi)), "auc": round(float(auc), 3)})
        _log(f"[fold{fi}] {v0.date()}〜{v1.date()} n={len(vi)} AUC={auc:.3f}")
    assert fold_rows, "有効 fold 0"

    mask = ~np.isnan(oof)
    oof_auc = float(roc_auc_score(y[mask], oof[mask])) if len(np.unique(y[mask])) > 1 else float("nan")
    sp = spearmanr(oof[mask], sd["net"].to_numpy()[mask])
    _log(f"\n===== Phase 1 判別力（学習期間 OOF・採点なし）=====")
    _log(f"  OOF AUC（勝ち/負け）        : {oof_auc:.3f}")
    _log(f"  OOF prob × 実net Spearman  : {sp.correlation:+.3f} (p={sp.pvalue:.3g})")
    _log(f"  fold別 AUC: {[r['auc'] for r in fold_rows]}")

    # ---- 本学習（全学習期間）→ ボラ支配チェック + importance ----
    dall = lgb.Dataset(X, label=y, weight=w)
    m_full = lgb.train(lp, dall, num_boost_round=300)
    vr = rg.report_vol_importance(dict(zip(m_full.feature_name(), m_full.feature_importance("gain"))))
    imp = pd.Series(m_full.feature_importance("gain"), index=feat_cols).sort_values(ascending=False)
    _log(f"\n[ボラ寄与] vol_share={vr['vol_share']}（停止 {VOL_DOMINANCE_STOP}）/ top5={vr['top']}")
    _log("[重要特徴 top15]\n" + imp.head(15).to_string())

    # ---- prob 分位ごとの実net（厚薄/cut の余地が見えるか・採点はしない）----
    sd2 = sd.copy(); sd2["oof"] = oof
    q = pd.qcut(sd2.loc[mask, "oof"], 5, labels=False, duplicates="drop")
    tbl = sd2.loc[mask].assign(qbin=q).groupby("qbin").agg(
        n=("net", "count"), winrate=("y", "mean"), net_sum=("net", "sum"), net_mean=("net", "mean")).round(2)
    _log("\n[OOF prob 5分位 × 実net（上位ほど net+ なら厳選/配分の余地）]\n" + tbl.to_string())

    out = {"_source": "train_p4_meta_E27.py（P4 メタラベリング Phase1・判別力測定・採点なし）",
           "OOF_AUC": round(oof_auc, 3), "PROB_NET_SPEARMAN": round(float(sp.correlation), 3),
           "FOLDS": fold_rows, "TRAIN_POS": int(len(sd)), "BASE_RATE": round(base_rate, 3),
           "VOL_SHARE": vr["vol_share"], "_top_features": {k: round(float(v), 1) for k, v in imp.head(15).to_dict().items()}}
    json.dump(out, open(RAT / "p4_meta_E27_phase1.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    _log(f"\n[out] p4_meta_E27_phase1.json")

    if SMOKE or "--phase2" not in sys.argv:
        _log("→ Phase1 のみ完了（--phase2 で運用+採点・まこさん GO 後）。")
        return

    # ===== Phase 2: cut 閾値（学習 OOF kept-net 最大化・覗き見なし）→ 運用 → 採点 =====
    nets = sd["net"].to_numpy()
    all_take = float(nets[mask].sum())
    best_thr, best_net = 0.0, all_take
    for thr in np.quantile(oof[mask], np.linspace(0.05, 0.9, 18)):
        sel = mask & (oof >= thr)
        if sel.sum() < 30:
            continue
        kn = float(nets[sel].sum())
        if kn > best_net:
            best_net, best_thr = kn, float(thr)
    _log(f"\n[Phase2] cut 閾値 prob≥{best_thr:.3f}（学習 OOF: 採用 {int((mask&(oof>=best_thr)).sum())}本/${best_net:.0f} vs 全取り {int(mask.sum())}本/${all_take:.0f}）")

    trades = operation(df, arrays, bar_ms, fire_arr, M, m_full, best_thr)
    inv_trades = operation(df, arrays, bar_ms, fire_arr, M, m_full, best_thr, invert=True)

    def _score(tr):
        t = pd.DataFrame(tr)
        for c in ("entry_time", "exit_time"):
            t[c] = pd.to_datetime(t[c])
        sc = t[(t["entry_time"] >= e8b.SC_START) & (t["entry_time"] < e8b.SC_END)].reset_index(drop=True)
        return judge.score(sc), t

    r, tdf = _score(trades); tdf.to_csv(RAT / "trades_p4_E27_cut.csv", index=False)
    r_inv, _ = _score(inv_trades)
    g["entry_time"] = pd.to_datetime(g["entry_time"]); g["exit_time"] = pd.to_datetime(g["exit_time"])
    gsc = g[(g["entry_time"] >= e8b.SC_START) & (g["entry_time"] < e8b.SC_END)].reset_index(drop=True)
    rg_ = judge.score(gsc)

    _log("\n===== Phase2 採点（score.py・cap0.12・採点 2025-04〜12）=====")
    _log(f"  AI(cut prob≥{best_thr:.3f}): {r['n_trades']:4d}件 / 月平均 ${r['monthly_avg']:8.2f} / 合計 ${r['total']:8.1f}")
    _log(f"  対照(prob<閾値で入る)    : {r_inv['n_trades']:4d}件 / 合計 ${r_inv['total']:8.1f}（本命がこれより良ければ ML 寄与）")
    _log(f"  地面 P4 E22（全取り）    : {rg_['n_trades']:4d}件 / 合計 ${rg_['total']:8.1f}")
    _log(f"  → AI {'勝ち' if r['total'] > rg_['total'] else '負け'}（差 ${r['total'] - rg_['total']:+.1f}）"
         f" / ML寄与 {'あり' if r['total'] > r_inv['total'] else 'なし(機械ルール疑い)'}")
    if r.get("anomaly"):
        _log("  ⚠️ 異常値・要調査（H12）: " + " / ".join(r["anomaly"]))

    out["PHASE2"] = {"CUT_THR": round(best_thr, 4), "AI_TOTAL": round(float(r["total"]), 2),
                     "INVERT_TOTAL": round(float(r_inv["total"]), 2), "GROUND_TOTAL": round(float(rg_["total"]), 2),
                     "AI_N": int(r["n_trades"]), "GROUND_N": int(rg_["n_trades"])}
    json.dump(out, open(RAT / "p4_meta_E27_phase1.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    _log(f"\n[out] trades_p4_E27_cut.csv / p4_meta_E27_phase1.json（PHASE2 追記）"
         f"\n→ 次: precheck → score → report --vs → analyze → ledger 5問。")


if __name__ == "__main__":
    main()
