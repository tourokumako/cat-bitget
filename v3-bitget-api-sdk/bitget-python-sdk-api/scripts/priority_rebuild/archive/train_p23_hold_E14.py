#!/usr/bin/env python3
"""train_p23_hold_E14.py — P23 保有中の早逃げ ML（E14・strat_v9ml_design §10.17.1 章7-3・まこさん承認 2026-06-10）

設計（章7-3・§10.8 B2 の実装）:
  - 狙い = 地面の最大出血源 TIME_EXIT（74件 −$2,161）。部分決済では消えず（E0.3 実測 140件 −$2,152）・
    entry 時の予測でも見つからず（E13 下位1/3 に 74件中7件）・TIME 玉は保有中に平均 +$12 浮いてから死ぬ
    （実測）＝保有中の形に情報がある。
  - 木が当てる対象 = 保有中の各バーで「ここから V9 出口まで持ち続けたら、今すぐ閉じるより net が増えるか」。
  - 教師 = 学習期間の地面ポジション（V9 フル・連続モード）の保有中スナップショット（保有30分以降）。
    ラベル = sign(最終 net − 今閉じた場合の net)。両方とも rc._record_trade（V9 の記録関数）が計算
    ＝本スクリプトは net 計算に触れない。重み = |差額|（p99 クリップ）。
  - 運用 = V9 の Entry/add/既存 Exit は全部そのまま。毎バー（保有30分以降）prob < しきい値
    （学習スナップショット分布の下位10%）なら成行で早逃げ（ML_EXIT・score.py が taker+slippage 自動計上・
    審判改造なし）。早逃げ時は pending（add 注文）も取り消す。ML は「V9 より早く逃げる」方向にしか作用しない。
  - 自己検査 = ML 無効で地面 1232件・$2558.80 と完全一致 assert。
  - 検証 = purged k-fold を【ポジション単位】で分割（同一玉のスナップショットは fold をまたがない）→
    score.py 採点 vs 地面 $925.73。

★ 不正防止3点（cat_requirements §8.4-2.9）: 判定は score.py の数字のみ／番人メタ確認／
  本スクリプトは net 計算に触れない（rc._record_trade / score import のみ）。
V9 本体 / gen / score / eval_engine は import のみ・改造しない。
"""
from __future__ import annotations
import sys
import copy
import pathlib
import json
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
import score as judge                         # noqa: E402
import ratchet_guards as rg                   # noqa: E402
import train_p23_entry_E8b as e8b             # noqa: E402  方向系特徴量
import train_p23_entry_E8 as e8               # noqa: E402  build_mtf
import train_p23_size_E13 as e13              # noqa: E402  build_vol_feats 流用（ボラ系 pct）
from strategies.cat_v9_decider import check_entry_priority   # noqa: E402

RAT = e8b.RAT
TRAIN_ENTRY_END = e8b.TRAIN_ENTRY_END
EMBARGO_END = e8b.EMBARGO_END
SC_START, SC_END = e8b.SC_START, e8b.SC_END
GROUND = e8b.GROUND

SNAP_MIN_AGE_MIN = 30                          # 保有30分未満は判定しない（entry 直後ノイズ・承認値）
CUT_QUANTILE = 0.10                            # 早逃げしきい値 = 学習スナップショット prob 下位10%（承認値）
N_FOLDS = 5
PURGE_EMBARGO = pd.Timedelta(days=1)
W_CLIP_Q = 0.99
VOL_DOMINANCE_STOP = 0.5

POS_STATE_COLS = ["age_min", "unreal_pct", "peak_pct", "dd_from_peak_pct", "add_count", "bars_since_add"]

LPARAMS = dict(objective="binary", metric=["auc", "binary_logloss"], learning_rate=0.03, num_leaves=15,
               min_child_samples=200, feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1,
               lambda_l1=1.0, lambda_l2=1.0, seed=42, verbose=-1)


def _log(m):
    print(m, flush=True)


def build_market_matrix(df, ohlcv):
    """全バーの市場特徴量（E13 と同じ顔ぶれ＝方向系複数期間＋ボラ系 pct＋MTF）を 1 枚の行列に。"""
    mp = e8b.build_multiperiod(ohlcv)
    vol = e13.build_vol_feats(ohlcv)
    bt = pd.to_datetime(df["timestamp_ms"], unit="ms")
    M_mp = mp.reindex(bt).reset_index(drop=True)
    M_vol = vol.reindex(bt).reset_index(drop=True)
    mtf = e8.build_mtf(ohlcv, pd.Series(bt))
    M = pd.concat([M_mp, M_vol, mtf.reset_index(drop=True)], axis=1)
    leaked = e8b.BANNED & set(M.columns)
    assert not leaked, f"H2/H6 leak: 結果列が市場特徴量に混入 {leaked}"
    bad = [c for c in M.columns if "bb_slope" in c and "pct" not in c]
    assert not bad, f"H6 違反: {bad}"
    return M.astype(np.float32)


def _exitnow_net(pos, close_p, ts_ms, params):
    """「今すぐ成行で閉じたら」の net を V9 の記録関数で計算（CC は net 計算に触れない）。"""
    scratch = []
    rc._record_trade(scratch, copy.copy(pos), exit_price=float(close_p), exit_reason="ML_EXIT",
                     exit_ts_ms=int(ts_ms), params=params)
    return float(scratch[-1]["net_usd"])


def _pos_state_row(pos, close_p, ts_ms, bar_i):
    avg = float(pos["entry_price"]); size = float(pos["size_btc"])
    notional = avg * size
    unreal_pct = (avg - close_p) / avg * 100.0                          # SHORT
    peak_pct = float(pos.get("mfe_usd", 0.0)) / notional * 100.0 if notional > 0 else 0.0
    age_min = (int(ts_ms) - int(pos["entry_time"])) / 60_000.0
    return [age_min, unreal_pct, peak_pct, peak_pct - unreal_pct,
            float(pos["add_count"]), float(bar_i - pos.get("_last_add_bar", bar_i))]


def run_loop(df, bar_ms, p23, fire_fn, M=None, model=None, cut=None, feat_cols=None, collect=False):
    """連続モード（gen._step・地面と同一機構）＋ E14 フック。
    collect=True: 教師スナップショット収集（ML 発動なし＝地面と同一の軌道）。
    model 指定: 保有30分以降の各バーで prob < cut なら成行早逃げ（ML_EXIT・pending も取消）。
    どちらも無し: 地面そのもの（自己検査用）。"""
    state = {"pos": None, "pending": None, "trades": []}
    snaps, pos_seq = [], []                      # snaps: 未確定スナップ（position close で確定）
    cur_snaps = []
    prev_add = 0
    n_mlexit = 0
    for i in range(rc.CANDLE_WARMUP, len(df)):
        n_before = len(state["trades"])
        gen._step(state, df, bar_ms, i, p23, fire_fn)
        pos = state["pos"]
        ts_ms = int(df.at[i, "timestamp_ms"])
        close_p = float(df.at[i, "close"])
        if pos is not None:
            if int(pos["add_count"]) != prev_add:                       # add 検出（最終 add バー記録）
                pos["_last_add_bar"] = i
            prev_add = int(pos["add_count"])
            age_min = (ts_ms - int(pos["entry_time"])) / 60_000.0
            if age_min >= SNAP_MIN_AGE_MIN:
                if collect:
                    cur_snaps.append({
                        "bar_i": i, "ts": ts_ms,
                        "state": _pos_state_row(pos, close_p, ts_ms, i),
                        "exitnow": _exitnow_net(pos, close_p, ts_ms, p23),
                        "pos_entry": int(pos["entry_time"]),
                    })
                elif model is not None:
                    row = np.concatenate([M[i], np.asarray(_pos_state_row(pos, close_p, ts_ms, i),
                                                           dtype=np.float32)])
                    prob = model.predict(row.reshape(1, -1))[0]
                    if prob < cut:                                      # 早逃げ（成行・V9 より早く逃げるのみ）
                        rc._record_trade(state["trades"], pos, exit_price=close_p,
                                         exit_reason="ML_EXIT", exit_ts_ms=ts_ms, params=p23)
                        state["pos"] = None
                        state["pending"] = None                         # add 注文も取消
                        prev_add = 0
                        n_mlexit += 1
                        continue
        else:
            prev_add = 0
        if collect and len(state["trades"]) > n_before:                 # position close → スナップ確定
            final_net = float(state["trades"][-1]["net_usd"])
            for s in cur_snaps:
                s["final_net"] = final_net
            snaps.extend(cur_snaps)
            cur_snaps = []
    if state["pos"] is not None:
        rc._record_trade(state["trades"], state["pos"], exit_price=float(df.iloc[-1]["close"]),
                         exit_reason="FORCE_CLOSE_EOD", exit_ts_ms=int(df.iloc[-1]["timestamp_ms"]), params=p23)
        if collect:
            final_net = float(state["trades"][-1]["net_usd"])
            for s in cur_snaps:
                s["final_net"] = final_net
            snaps.extend(cur_snaps)
    return state["trades"], snaps, n_mlexit


def purged_folds_by_pos(snap_df, n_folds):
    """ポジション単位の purged k-fold（同一玉のスナップは fold をまたがない・保有区間で purge）。"""
    pos_tbl = snap_df.groupby("pos_entry").agg(p_start=("ts_dt", "min"), p_end=("ts_dt", "max")).reset_index()
    pos_tbl = pos_tbl.sort_values("p_start").reset_index(drop=True)
    blocks = np.array_split(pos_tbl.index.values, n_folds)
    for b in blocks:
        if not len(b):
            continue
        v_pos = set(pos_tbl.loc[b, "pos_entry"])
        v0, v1 = pos_tbl.loc[b, "p_start"].min(), pos_tbl.loc[b, "p_end"].max()
        ov = pos_tbl[(pos_tbl.p_start <= v1 + PURGE_EMBARGO) & (pos_tbl.p_end >= v0 - PURGE_EMBARGO)]
        t_pos = set(pos_tbl.pos_entry) - set(ov.pos_entry)
        vi = snap_df.index[snap_df.pos_entry.isin(v_pos)].values
        ti = snap_df.index[snap_df.pos_entry.isin(t_pos)].values
        yield ti, vi, (v0, v1)


def fit_weighted(Xtr, ytr, wtr, Xva, yva, wva):
    dtr = lgb.Dataset(Xtr, label=ytr, weight=wtr)
    dva = lgb.Dataset(Xva, label=yva, weight=wva, reference=dtr)
    return lgb.train(LPARAMS, dtr, num_boost_round=3000, valid_sets=[dva],
                     callbacks=[lgb.early_stopping(80, verbose=False)])


def main():
    SMOKE = "--smoke" in sys.argv
    _log("[E14] P23 保有中の早逃げ ML（TimeExit 出血を保有中に切る・地面 $925.73）")

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
    Mdf = build_market_matrix(df, ohlcv)
    market_cols = list(Mdf.columns)
    M = Mdf.to_numpy(dtype=np.float32)
    feat_cols = market_cols + POS_STATE_COLS
    fire_fn = lambda i: (check_entry_priority(i, df, p23) == gen.PRIORITY)

    # ---- 教師スナップショット収集（地面と同一軌道・ML 発動なし・1パス）----
    base_trades, snaps, _ = run_loop(df, bar_ms, p23, fire_fn, collect=True)
    g = pd.read_csv(GROUND)
    bsum, gsum = sum(float(t["net_usd"]) for t in base_trades), float(g["net_usd"].sum())
    _log(f"[自己検査] 教師パス: {len(base_trades)}件/${bsum:.2f} vs 地面CSV {len(g)}件/${gsum:.2f}")
    assert len(base_trades) == len(g) and abs(bsum - gsum) < 0.01, "自己検査 FAIL: 教師パスが地面と不一致"
    _log("[自己検査] ✅ 一致（収集は地面の軌道を変えていない）")

    sd = pd.DataFrame({
        "bar_i": [s["bar_i"] for s in snaps],
        "ts_dt": pd.to_datetime([s["ts"] for s in snaps], unit="ms"),
        "pos_entry": [s["pos_entry"] for s in snaps],
        "increment": [s["final_net"] - s["exitnow"] for s in snaps],
    })
    Xs = np.concatenate([M[sd["bar_i"].values],
                         np.asarray([s["state"] for s in snaps], dtype=np.float32)], axis=1)
    Xs = pd.DataFrame(Xs, columns=feat_cols)

    # ---- 学習期間のみ（H8）----
    pos_entry_dt = pd.to_datetime(sd["pos_entry"], unit="ms")
    is_tr = (pos_entry_dt < TRAIN_ENTRY_END) & (sd["ts_dt"] < EMBARGO_END)
    sd_tr = sd[is_tr.values].reset_index(drop=True)
    X_tr = Xs[is_tr.values].reset_index(drop=True)
    if SMOKE:
        keep_pos = sd_tr["pos_entry"].drop_duplicates().tail(120)
        m = sd_tr["pos_entry"].isin(set(keep_pos))
        sd_tr, X_tr = sd_tr[m.values].reset_index(drop=True), X_tr[m.values].reset_index(drop=True)
        _log(f"[SMOKE] 末尾120ポジションに制限")
    y = (sd_tr["increment"] > 0).astype(int).values
    clip_at = float(sd_tr["increment"].abs().quantile(W_CLIP_Q))
    w = sd_tr["increment"].abs().clip(upper=clip_at).values
    keep = w > 0
    sd_tr, X_tr, y, w = sd_tr[keep].reset_index(drop=True), X_tr[keep].reset_index(drop=True), y[keep], w[keep]
    n_pos_tr = sd_tr["pos_entry"].nunique()
    _log(f"[教師] スナップ {len(sd_tr)} 枚 / ポジション {n_pos_tr} 本 / 「持つ価値あり」率 {y.mean()*100:.1f}% / "
         f"重み p99 クリップ ${clip_at:.2f}")

    # ---- purged k-fold（ポジション単位）健全性 ----
    rows, oof = [], []
    for fi, (ti, vi, (v0, v1)) in enumerate(purged_folds_by_pos(sd_tr, 2 if SMOKE else N_FOLDS)):
        if len(ti) < 1000 or len(vi) < 200 or len(np.unique(y[ti])) < 2:
            continue
        m = fit_weighted(X_tr.iloc[ti], y[ti], w[ti], X_tr.iloc[vi], y[vi], w[vi])
        p = m.predict(X_tr.iloc[vi], num_iteration=m.best_iteration)
        inc = sd_tr["increment"].values[vi]
        sp = spearmanr(p, inc)
        auc = roc_auc_score(y[vi], p) if len(np.unique(y[vi])) > 1 else float("nan")
        rows.append({"fold": fi, "val_start": str(v0.date()), "val_end": str(v1.date()), "n_val": len(vi),
                     "best_iter": int(m.best_iteration),
                     "spearman_prob_inc": round(float(sp.statistic), 4), "auc": round(float(auc), 4)})
        oof.append(pd.DataFrame({"prob": p, "increment": inc}))
        _log(f"[fold{fi}] val {v0.date()}〜{v1.date()} n={len(vi)} Spearman(prob,増分)={sp.statistic:+.4f} "
             f"AUC={auc:.4f} best_iter={m.best_iteration}")
    assert rows, "有効 fold 0"
    oof = pd.concat(oof, ignore_index=True)
    sp_all = spearmanr(oof["prob"], oof["increment"])
    dec = oof.copy()
    dec["decile"] = pd.qcut(dec["prob"].rank(method="first"), 10, labels=False)
    dt = dec.groupby("decile").agg(n=("increment", "size"), inc_mean=("increment", "mean"),
                                   inc_sum=("increment", "sum")).reset_index()
    _log(f"\n[① prob×増分] OOF Spearman = {sp_all.statistic:+.4f}")
    _log("[③ 較正] prob 10分位 × 「持ち続けた場合の増分」（下位帯が大きくマイナスなら早逃げが効く）\n"
         + dt.to_string(index=False))

    # ---- 本学習（全学習スナップ・末尾15% early stop）→ ボラ支配チェック ----
    cut_i = int(len(X_tr) * 0.85)
    m_full = fit_weighted(X_tr.iloc[:cut_i], y[:cut_i], w[:cut_i], X_tr.iloc[cut_i:], y[cut_i:], w[cut_i:])
    vr = rg.report_vol_importance(dict(zip(m_full.feature_name(), m_full.feature_importance("gain"))))
    imp = pd.Series(m_full.feature_importance("gain"), index=feat_cols).sort_values(ascending=False)
    _log(f"\n[② ボラ寄与] vol_share={vr['vol_share']}（停止 {VOL_DOMINANCE_STOP}） / top5={vr['top']}")
    _log("[重要特徴 top15]\n" + imp.head(15).to_string())
    if float(vr["vol_share"]) > VOL_DOMINANCE_STOP:
        _log("⛔ ボラ支配 → 採点せず停止・まこさんに報告")
        return

    prob_tr = m_full.predict(X_tr, num_iteration=m_full.best_iteration)
    cut = float(np.quantile(prob_tr, CUT_QUANTILE))
    _log(f"[しきい値] 学習スナップ prob 下位{CUT_QUANTILE*100:.0f}% = {cut:.4f} 未満で早逃げ（保有{SNAP_MIN_AGE_MIN}分以降）")

    if SMOKE:
        _log("[SMOKE] 完了（教師収集・自己検査・健全性・しきい値まで・本採点は本番のみ）")
        return

    # ---- 本番: 早逃げ ML を載せて連続モード → score.py 採点 ----
    trades, _, n_mlexit = run_loop(df, bar_ms, p23, fire_fn, M=M, model=m_full, cut=cut, feat_cols=feat_cols)
    out_csv = RAT / "trades_p23_E14_hold.csv"
    tdf = pd.DataFrame(trades)
    for col in ("entry_time", "exit_time"):
        tdf[col] = pd.to_datetime(tdf[col])
    tdf.to_csv(out_csv, index=False)
    sc = tdf[(tdf["entry_time"] >= SC_START) & (tdf["entry_time"] < SC_END)].reset_index(drop=True)
    r = judge.score(sc)
    _log("\n===== 採点（score.py・cap0.12 ゲート・採点 2025-04〜12・連続モード）=====")
    _log(f"  AI(早逃げML): {r['n_trades']:5d}件 / 月平均 ${r['monthly_avg']:8.2f} / 合計 ${r['total']:8.1f}"
         f"（ML_EXIT {n_mlexit} 玉・全期間）")
    if r.get("anomaly"):
        _log("  ⚠️ 異常値・要調査（H12）: " + " / ".join(r["anomaly"]))
    g["entry_time"] = pd.to_datetime(g["entry_time"]); g["exit_time"] = pd.to_datetime(g["exit_time"])
    gsc = g[(g["entry_time"] >= SC_START) & (g["entry_time"] < SC_END)].reset_index(drop=True)
    rg_ = judge.score(gsc)
    _log(f"  地面 E0.2: {rg_['n_trades']:5d}件 / 合計 ${rg_['total']:8.1f}")
    _log(f"  → AI {'勝ち' if r['total'] > rg_['total'] else '負け'}（差 ${r['total'] - rg_['total']:+.1f}）")

    out = {
        "_source": "train_p23_hold_E14.py（保有中の早逃げ ML・§10.8 B2・Entry/add/V9既存Exit 不変）",
        "_design": f"教師=保有中スナップ(30分以降)・ラベル=sign(最終net−今閉じnet)・重み|差額|p99クリップ・"
                   f"早逃げ=prob<学習下位{CUT_QUANTILE*100:.0f}%({cut:.4f})・ML_EXIT(taker)",
        "OOF_SPEARMAN_PROB_INCREMENT": round(float(sp_all.statistic), 4),
        "VOL_SHARE": vr["vol_share"],
        "CUT": round(cut, 4),
        "N_ML_EXIT": int(n_mlexit),
        "N_SNAPSHOTS_TRAIN": int(len(sd_tr)),
        "AI_SCORE_TOTAL_USD": round(float(r["total"]), 2),
        "GROUND_E02_TOTAL_USD": round(float(rg_["total"]), 2),
        "CV_FOLDS": rows,
        "_top_features_gain": {k: round(float(v), 1) for k, v in imp.head(12).to_dict().items()},
    }
    json.dump(out, open(RAT / "p23_learned_params_E14.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    _log(f"\n[out] {out_csv}")
    _log(f"[out] p23_learned_params_E14.json")
    _log(f"[次] python3 scripts/priority_rebuild/report.py {out_csv} --start 2025-04-01 --end 2025-12-31 --vs {GROUND}")


if __name__ == "__main__":
    main()
