#!/usr/bin/env python3
"""train_p23_size_E13.py — P23 サイズ強弱 ML（E13・strat_v9ml_design §10.17.1 章7-2 Step B 改＝まこさん承認 2026-06-10）

設計（チャット承認・2026-06-10）:
  - Entry 条件・Exit 全部・add・件数 ＝ V9 のまま（地面 E0.2 と完全同一・check_entry_priority==23）。
  - ML が決めるのは各玉のサイズだけ: 「この玉は net プラスになりそうか」の prob で
      prob < 学習期間分布の下位1/3 → unit 0.012（薄く＝ダメそうな玉の損を半分に）
      それ以外                     → unit 0.024（現状のまま）
    ※ 0.024 より厚くしない（add5×0.024=0.12＝予算上限・H1）。θ足切りなし＝件数は地面と同一。
  - 学習 = E12 と同じ（ラベル=実Exitで net>0 の符号・重み w=|net| p99クリップ・purged 5fold 健全性）。
    変更点 = 特徴量に ATR/bb_width（ボラ系）を戻す（V9 本人が ATR≥150 を Entry 条件に使う黒字材料・
    cat_v9_decider L480 で原本確認済み）。H15 は「ボラがラベル」「ボラが支配」の禁止であり、
    ラベルは符号なので前者は閉じたまま。支配（vol_share）は実測して報告・支配したら採点前に停止。
  - 自己検査: 同じ実行機構で全玉のサイズを 0.024 に固定すると地面 CSV と件数・net が一致すること
    （一致しなければ機構の移植ミス＝停止）。
  - 判定 = score.py（cap0.12 ゲート・採点 2025-04〜12）vs 地面 $925.73。

★ 不正防止3点（cat_requirements §8.4-2.9）: 判定は score.py の数字のみ／実装後 独立レビュー→指摘を
  潰してから採点／番人メタ確認。本スクリプトは net 計算に触れない（CSV 保存値と score import のみ）。
V9 本体（cat_v9_decider/replay_csv/cat_params_v9）/ gen / score / eval_engine は import のみ・改造しない。
"""
from __future__ import annotations
import sys
import pathlib
import json
import numpy as np
import pandas as pd
import ta
import lightgbm as lgb
from sklearn.metrics import roc_auc_score
from scipy.stats import spearmanr

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runner"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import replay_csv as rc                       # noqa: E402  V9 リプレイ（import のみ）
import gen_p23_candidates as gen              # noqa: E402  連続モード/_step/型（import のみ・改造しない）
import score as judge                         # noqa: E402  審判（import のみ・改造禁止）
import ratchet_guards as rg                   # noqa: E402  番人（leak/期間/ボラ可視化・既知答え済）
import train_p23_entry_E8b as e8b             # noqa: E402  方向系特徴量・ラベル照合ヘルパ流用
import train_p23_entry_E8 as e8               # noqa: E402  build_mtf 流用（leak-safe MTF）
from strategies.cat_v9_decider import check_entry_priority   # noqa: E402

RAT = e8b.RAT
TRAIN_ENTRY_END = e8b.TRAIN_ENTRY_END         # 2024-12-31（H8）
EMBARGO_END = e8b.EMBARGO_END                 # 2025-04-01
SC_START, SC_END = e8b.SC_START, e8b.SC_END
GROUND = e8b.GROUND                           # trades_p23_ground_capped.csv（地面 $925.73）

N_FOLDS = 5
PURGE_EMBARGO = pd.Timedelta(days=1)
W_CLIP_Q = 0.99

# サイズ強弱（まこさん承認のチャット提案値・2026-06-10）
UNIT_BASE = 0.024                             # 現状サイズ（地面と同一・add5×0.024=0.12=H1 上限）
UNIT_THIN = 0.012                             # ダメそうな玉（prob 下位1/3）を半分に
THIN_QUANTILE = 1.0 / 3.0                     # 学習期間 prob 分布の下位1/3（採点期間は覗かない・類型C回避）
VOL_DOMINANCE_STOP = 0.5                      # vol_share がこれを超えたら「ボラ支配」として採点前に停止（H15①）

LPARAMS = dict(objective="binary", metric=["auc", "binary_logloss"], learning_rate=0.03, num_leaves=15,
               min_child_samples=100, feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1,
               lambda_l1=1.0, lambda_l2=1.0, seed=42, verbose=-1)
# scale_pos_weight は使わない（重み w=|net| が勝ち$/負け$バランスを表す・E12 と同じ設計）。


def _log(m):
    print(m, flush=True)


# ======================================================================
# 特徴量（E13）: E12 の方向系＋MTF に ボラ系（atr_pct/bb_width_pct・複数期間）を戻す。
# H6: pct 化のみ（USD 絶対値にしない）。H2: shift は正方向のみ・結果列 BANNED assert。
# ★ e8b.make_features は「ボラ系ゼロ」を assert するため使えない＝E13 専用に組む（e8b は不変）。
# ======================================================================
def build_vol_feats(ohlcv: pd.DataFrame) -> pd.DataFrame:
    o = ohlcv.set_index("timestamp").sort_index()
    c, h, l = o["close"], o["high"], o["low"]
    f = pd.DataFrame(index=o.index)
    for p in (7, 14, 28):
        atr = ta.volatility.AverageTrueRange(h, l, c, window=p).average_true_range()
        f[f"atr_pct_{p}"] = atr / c * 100.0                       # 価格比 pct（H6・t 時点確定値）
    for p in (10, 20, 40):
        bb = ta.volatility.BollingerBands(c, window=p, window_dev=2)
        f[f"bb_width_pct_{p}"] = (bb.bollinger_hband() - bb.bollinger_lband()) / bb.bollinger_mavg() * 100.0
    return f


def make_features_e13(bar_times: pd.Series, mp_feats, vol_feats, ohlcv) -> pd.DataFrame:
    bt = pd.to_datetime(bar_times.values)
    X_mp = mp_feats.reindex(bt).reset_index(drop=True)            # 方向系（複数期間・確定値）
    X_vol = vol_feats.reindex(bt).reset_index(drop=True)          # ボラ系（pct・確定値・E13 で復帰）
    mtf = e8.build_mtf(ohlcv, pd.Series(bt))                      # 上位足 backward merge（leak-safe）
    bt_s = pd.Series(bt)
    tcol = pd.DataFrame({"entry_hour": bt_s.dt.hour.values, "entry_weekday": bt_s.dt.weekday.values})
    X = pd.concat([X_mp, X_vol, mtf.reset_index(drop=True), tcol], axis=1)
    leaked = e8b.BANNED & set(X.columns)
    assert not leaked, f"H2/H6 leak: 結果列が特徴量に混入 {leaked}"
    bad = [c for c in X.columns if "bb_slope" in c and "pct" not in c]
    assert not bad, f"H6 違反: USD 絶対値の特徴量が pct 化されていない {bad}"
    return X


def purged_folds(times_entry: pd.Series, times_exit: pd.Series, n_folds: int):
    """E12 と同一（AFML Ch.7 Purged K-Fold・label 終端は実 exit_time）。"""
    order = np.argsort(times_entry.values)
    blocks = np.array_split(order, n_folds)
    for b in blocks:
        if not len(b):
            continue
        v_start = times_entry.iloc[b].min()
        v_end = times_entry.iloc[b].max()
        mask_overlap = (times_entry <= v_end + PURGE_EMBARGO) & (times_exit >= v_start - PURGE_EMBARGO)
        train_idx = np.array([i for i in order if not mask_overlap.iloc[i]])
        yield train_idx, b, (v_start, v_end)


def fit_weighted(Xtr, ytr, wtr, Xva, yva, wva):
    dtr = lgb.Dataset(Xtr, label=ytr, weight=wtr)
    dva = lgb.Dataset(Xva, label=yva, weight=wva, reference=dtr)
    return lgb.train(LPARAMS, dtr, num_boost_round=3000, valid_sets=[dva],
                     callbacks=[lgb.early_stopping(80, verbose=False)])


def run_sized_continuous(df, bar_ms, p23, prob_by_bar, thin_cut, fire_fn, force_base=False):
    """連続モード（地面と同一機構）＋玉ごとのサイズ強弱。
    新規建玉が開くバー i（pos も pending も無く V9 フル閾値が発火）の prob でその建玉の unit を確定:
      prob < thin_cut → UNIT_THIN / それ以外 → UNIT_BASE（force_base=True なら全玉 UNIT_BASE＝自己検査用）。
    add は同じ建玉に積むので unit を引き継ぐ（active params を変えない・E10 と同じ機構）。
    ⚠ 既知の近似（E10 と同じ・レビュー対象）: 1バーで前建玉が閉じ同バーで次が開く稀ケースは前 unit を引き継ぐ。"""
    p_base = dict(p23); p_base["P23_POSITION_SIZE_BTC"] = UNIT_BASE
    p_thin = dict(p23); p_thin["P23_POSITION_SIZE_BTC"] = UNIT_THIN
    state = {"pos": None, "pending": None, "trades": []}
    active = p_base
    n_thin = 0
    for i in range(rc.CANDLE_WARMUP, len(df)):
        if state["pos"] is None and state["pending"] is None and fire_fn(i):
            if force_base or prob_by_bar.get(i, 1.0) >= thin_cut:
                active = p_base
            else:
                active = p_thin
                n_thin += 1
        gen._step(state, df, bar_ms, i, active, fire_fn)
    if state["pos"] is not None:
        rc._record_trade(state["trades"], state["pos"], exit_price=float(df.iloc[-1]["close"]),
                         exit_reason="FORCE_CLOSE_EOD", exit_ts_ms=int(df.iloc[-1]["timestamp_ms"]), params=active)
    return state["trades"], n_thin


def main():
    SMOKE = "--smoke" in sys.argv
    _log("[E13] P23 サイズ強弱 ML（Entry/Exit/add/件数=V9 のまま・サイズだけ・地面 $925.73）")

    rg.assert_no_future_ref(pathlib.Path(__file__).read_text())
    rg.assert_no_future_ref(pathlib.Path(e8b.__file__).read_text())
    rg.assert_period_split(TRAIN_ENTRY_END, SC_START)

    # ---- データ（P23 のみ有効・地面測定と同条件）----
    params = rc._load_params()
    p23 = dict(params)
    for k in list(p23):
        if k.startswith("ENABLE_P") and k.endswith(("_LONG", "_SHORT")):
            p23[k] = (k == "ENABLE_P23_SHORT")
    df, _ = rc.preload(str(gen.OHLCV_CSV), p23)
    bar_ms = int(df.at[1, "timestamp_ms"] - df.at[0, "timestamp_ms"])
    ohlcv = pd.read_csv(e8b.OHLCV)
    ohlcv["timestamp"] = pd.to_datetime(ohlcv["timestamp"])
    mp = e8b.build_multiperiod(ohlcv)
    vol = build_vol_feats(ohlcv)

    # ---- 教師（E12 と同一・typeonly CSV＝V9 実Exit の独立 sim net）----
    type_bars = [i for i in range(rc.CANDLE_WARMUP, len(df)) if gen._p23_type_fires(df, i)]
    lab_all = e8b.label_from_csv(df, type_bars).drop_duplicates(subset=["bar_i"], keep="first").reset_index(drop=True)
    tr = lab_all[(lab_all["bar_time"] < TRAIN_ENTRY_END) & (lab_all["exit_time"] < EMBARGO_END)].reset_index(drop=True)
    assert tr["bar_time"].max() < TRAIN_ENTRY_END and tr["exit_time"].max() < SC_START, "H8: 学習行が採点期間に侵入"
    if SMOKE:
        tr = tr.tail(4000).reset_index(drop=True)
        _log(f"[SMOKE] 学習行を末尾 {len(tr)} 件に制限")

    net = tr["net_usd"].astype(float)
    y = (net > 0).astype(int).values
    clip_at = float(net.abs().quantile(W_CLIP_Q))
    w = net.abs().clip(upper=clip_at).values
    keep = w > 0
    tr, y, w = tr[keep].reset_index(drop=True), y[keep], w[keep]
    _log(f"[教師] {len(tr)} 件・勝ち {y.mean()*100:.1f}%・重み p99 クリップ ${clip_at:.2f}")

    # ---- 特徴量（E13＝方向系＋MTF＋ボラ系復帰）----
    X = make_features_e13(tr["bar_time"], mp, vol, ohlcv)

    # ---- 健全性（purged k-fold・E12 と同じ4点）----
    rows, oof = [], []
    for fi, (ti, vi, (v0, v1)) in enumerate(purged_folds(tr["entry_time"], tr["exit_time"], 2 if SMOKE else N_FOLDS)):
        if len(ti) < 500 or len(vi) < 100 or len(np.unique(y[ti])) < 2:
            continue
        m = fit_weighted(X.iloc[ti], y[ti], w[ti], X.iloc[vi], y[vi], w[vi])
        p = m.predict(X.iloc[vi], num_iteration=m.best_iteration)
        nv = tr["net_usd"].values[vi]
        sp = spearmanr(p, nv)
        auc = roc_auc_score(y[vi], p) if len(np.unique(y[vi])) > 1 else float("nan")
        rows.append({"fold": fi, "val_start": str(v0.date()), "val_end": str(v1.date()), "n_val": len(vi),
                     "best_iter": int(m.best_iteration),
                     "spearman_prob_net": round(float(sp.statistic), 4), "auc": round(float(auc), 4)})
        oof.append(pd.DataFrame({"fold": fi, "prob": p, "net_usd": nv}))
        _log(f"[fold{fi}] val {v0.date()}〜{v1.date()} Spearman(prob,net)={sp.statistic:+.4f} "
             f"AUC={auc:.4f} best_iter={m.best_iteration}")
    assert rows, "有効 fold 0"
    oof = pd.concat(oof, ignore_index=True)
    sp_all = spearmanr(oof["prob"], oof["net_usd"])
    _log(f"[① prob×実net] OOF Spearman = {sp_all.statistic:+.4f}（E12 ボラ無し +0.028 / E10 −0.08）")

    # ---- 本学習（全学習行・末尾15% early stop）→ ボラ支配チェック（H15①）----
    cut = int(len(X) * 0.85)
    m_full = fit_weighted(X.iloc[:cut], y[:cut], w[:cut], X.iloc[cut:], y[cut:], w[cut:])
    vr = rg.report_vol_importance(dict(zip(m_full.feature_name(), m_full.feature_importance("gain"))))
    imp = pd.Series(m_full.feature_importance("gain"), index=X.columns).sort_values(ascending=False)
    _log(f"[② ボラ寄与] vol_share={vr['vol_share']}（停止しきい値 {VOL_DOMINANCE_STOP}・H15①） / top5={vr['top']}")
    _log("[重要特徴 top15]\n" + imp.head(15).to_string())
    if float(vr["vol_share"]) > VOL_DOMINANCE_STOP:
        _log(f"⛔ ボラ支配（vol_share {vr['vol_share']} > {VOL_DOMINANCE_STOP}）→ H15① により採点せず停止・まこさんに報告")
        return

    # ---- 全型バーの prob（推論・特徴量は各バー時点の確定値のみ）と thin 境界（学習分布の下位1/3）----
    X_all = make_features_e13(lab_all["bar_time"], mp, vol, ohlcv)
    prob_all = m_full.predict(X_all, num_iteration=m_full.best_iteration)
    prob_by_bar = dict(zip(lab_all["bar_i"].astype(int).values, prob_all))
    is_tr_all = (lab_all["bar_time"] < TRAIN_ENTRY_END).values
    thin_cut = float(np.quantile(prob_all[is_tr_all], THIN_QUANTILE))
    _log(f"[サイズ境界] 学習 prob 下位1/3 = {thin_cut:.4f} 未満 → unit {UNIT_THIN} / 以上 → {UNIT_BASE}")

    if SMOKE:
        _log("[SMOKE] 完了（学習・健全性・境界まで確認・連続モード/採点は本番のみ）")
        return

    fire_fn = lambda i: (check_entry_priority(i, df, p23) == gen.PRIORITY)

    # ---- 自己検査: 全玉 0.024 固定 → 地面 CSV と件数・net 一致（機構の移植が正しい証明）----
    base_trades, _ = run_sized_continuous(df, bar_ms, p23, prob_by_bar, thin_cut, fire_fn, force_base=True)
    g = pd.read_csv(GROUND)
    bsum, gsum = sum(float(t["net_usd"]) for t in base_trades), float(g["net_usd"].sum())
    _log(f"[自己検査] force_base: {len(base_trades)}件/${bsum:.2f} vs 地面CSV {len(g)}件/${gsum:.2f}")
    assert len(base_trades) == len(g) and abs(bsum - gsum) < 0.01, "自己検査 FAIL: 機構が地面を再現しない（移植ミス）"
    _log("[自己検査] ✅ 一致（サイズ注入機構は地面と同一の振る舞い）")

    # ---- 本番: サイズ強弱 → score.py 採点 vs 地面 ----
    trades, n_thin = run_sized_continuous(df, bar_ms, p23, prob_by_bar, thin_cut, fire_fn)
    out_csv = RAT / "trades_p23_E13_sized.csv"
    tdf = pd.DataFrame(trades)
    for col in ("entry_time", "exit_time"):
        tdf[col] = pd.to_datetime(tdf[col])
    tdf.to_csv(out_csv, index=False)
    sc = tdf[(tdf["entry_time"] >= SC_START) & (tdf["entry_time"] < SC_END)].reset_index(drop=True)
    r = judge.score(sc)
    _log("\n===== 採点（score.py・cap0.12 ゲート・採点 2025-04〜12・連続モード）=====")
    _log(f"  AI(サイズ強弱): {r['n_trades']:5d}件 / 月平均 ${r['monthly_avg']:8.2f} / 合計 ${r['total']:8.1f}"
         f"（thin 適用 {n_thin} 玉・全期間）")
    if r.get("anomaly"):
        _log("  ⚠️ 異常値・要調査（H12）: " + " / ".join(r["anomaly"]))
    g["entry_time"] = pd.to_datetime(g["entry_time"]); g["exit_time"] = pd.to_datetime(g["exit_time"])
    gsc = g[(g["entry_time"] >= SC_START) & (g["entry_time"] < SC_END)].reset_index(drop=True)
    rg_ = judge.score(gsc)
    _log(f"  地面 E0.2: {rg_['n_trades']:5d}件 / 合計 ${rg_['total']:8.1f}")
    _log(f"  → AI {'勝ち' if r['total'] > rg_['total'] else '負け'}（差 ${r['total'] - rg_['total']:+.1f}）")

    out = {
        "_source": "train_p23_size_E13.py（サイズ強弱のみ ML・Entry/Exit/add/件数=V9）",
        "_design": f"ラベル=実Exit net>0・重み|net| p99クリップ・特徴量=方向系+MTF+ボラ系復帰・"
                   f"prob<学習下位1/3({thin_cut:.4f})→unit {UNIT_THIN}/他 {UNIT_BASE}",
        "OOF_SPEARMAN_PROB_NET": round(float(sp_all.statistic), 4),
        "VOL_SHARE": vr["vol_share"],
        "THIN_CUT": round(thin_cut, 4),
        "N_THIN_POSITIONS": int(n_thin),
        "AI_SCORE_TOTAL_USD": round(float(r["total"]), 2),
        "GROUND_E02_TOTAL_USD": round(float(rg_["total"]), 2),
        "CV_FOLDS": rows,
        "_top_features_gain": {k: round(float(v), 1) for k, v in imp.head(12).to_dict().items()},
    }
    json.dump(out, open(RAT / "p23_learned_params_E13.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    _log(f"\n[out] {out_csv}")
    _log(f"[out] p23_learned_params_E13.json")
    _log(f"[次] python3 scripts/priority_rebuild/report.py {out_csv} --start 2025-04-01 --end 2025-12-31 --vs {GROUND}")


if __name__ == "__main__":
    main()
