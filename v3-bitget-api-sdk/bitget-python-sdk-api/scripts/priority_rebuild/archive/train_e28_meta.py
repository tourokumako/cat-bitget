#!/usr/bin/env python3
"""train_e28_meta.py — E28 Phase 1: 下げ相場 LONG（ドルバー行き過ぎ）メタラベリング（判別力測定・採点なし）

設計（まこさん GO 2026-06-12・E28 Phase 1 設計プレゼン）・正本 strat_v9ml_design §10.19.5-7 / §10.19.10:
  一次（型・高recall）= ドルバー行き過ぎ 5%ile cross-in（1%ile より広く候補を出す＝de Prado 一次は高recall・
    二次が「賭けるか見送るか」を判定）。確定の 1%ile は「dev_z が深い」＝特徴量として学習（ハードコードしない）。
  ラベル（方向・H15）= 各候補を eval_engine 前向き sim → net>0（TP-before-SL に辿り着けたか）二値。
    net 金額をラベルにしない（高ボラほど伸びる＝ボラ依存＝H15 違反）。バリア＝既存(ATR×1.75 maker/構造SL/4h)。
  特徴量（sig_time 確定値・leak-safe）= 主役: dev_z(行き過ぎ深さ)・taker_ls(Step2 確定の需給フィルタ)・
    RSI/stoch/モメンタム(ドルバー)・サポート距離・MTF(15m/30m/1h/4h regime/momentum・e8.build_mtf 流用)。
    脇役: atr_pct/bb_width(バリア幅・importance 監視のみ)。OI(oi_btc・E28 Step2 不採用)は入れない。
  二次 = LightGBM 二値・purged k-fold(候補単位・embargo 1day)・weight=|net| p99クリップ・scale_pos_weight。
  Phase 1 出力（採点なし）= OOF AUC / prob×実net Spearman / vol_share(H15<0.5) / 年別 net / importance(taker_ls 上位) / prob5分位×net。
  撤退でなく診断（特に 2023 が分離できるか）。

★不正防止(cat_requirements §8.4-2.9): net は eval_engine(改造禁止・import のみ)が出す数字だけ・自作 net 禁止。
  審判(eval_engine)/MTF(e8.build_mtf)/番人(ratchet_guards) は import のみ・改造しない。採点は Phase 2(別途 GO 後)。
"""
from __future__ import annotations
import json
import pathlib
import sys

import numpy as np
import pandas as pd
import ta
import lightgbm as lgb
from sklearn.metrics import roc_auc_score
from scipy.stats import spearmanr

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import e28_phase0_dollarbar as e28        # noqa: E402  ドルバー生成・指標・FR・OI・eval_engine 流用
import eval_engine as ee                  # noqa: E402  審判（per-trade net・改造禁止）
import train_p23_entry_E8 as e8           # noqa: E402  build_mtf（leak-safe MTF）流用
import ratchet_guards as rg               # noqa: E402  leak/期間/vol_share 番人

RAT = e28.RATCHET
TRAIN_END = e28.TRAIN_END                 # 学習 < 2025-01-01（採点 2025 不参照・H8）
N_FOLDS = 5
W_CLIP_Q = 0.99
EMBARGO = pd.Timedelta(days=1)
VOL_STOP = 0.5
Q1RY = 0.01                               # 一次プール＝確定エッジ 行き過ぎ 1%ile（5%ile は base 悪化で破棄・ledger E28 Phase1 第1回）

LPARAMS = dict(objective="binary", metric="auc", learning_rate=0.03,
               num_leaves=15, min_child_samples=50, feature_fraction=0.8, bagging_fraction=0.8,
               bagging_freq=1, lambda_l1=1.0, lambda_l2=1.0, seed=42, verbose=-1)


def _log(m):
    print(m, flush=True)


def add_meta_features(db):
    """ドルバー上の方向特徴（RSI/stoch/モメンタム/サポート距離）＋ボラ脇役（bb_width）。
    dev_z/atr_pct/taker_ls は add_indicators/add_oi で計算済み。すべて因果（rolling/shift）＝leak-safe。"""
    c, h, l = db.close, db.high, db.low
    db["rsi_db"] = ta.momentum.RSIIndicator(c, 14).rsi()
    db["rsi_slope"] = db["rsi_db"].diff()
    db["stoch_k_db"] = ta.momentum.StochasticOscillator(h, l, c, 14, 3).stoch()
    db["ret_3"] = c.pct_change(3)
    db["ret_10"] = c.pct_change(10)
    db["dist_swing"] = (c - db.swing_low) / c            # サポート（直近安値）からの距離
    bb = ta.volatility.BollingerBands(c, 20)
    db["bb_width"] = (bb.bollinger_hband() - bb.bollinger_lband()) / c   # 脇役（ボラ）
    return db


# 方向の主役（H15: ボラを方向スコアの主役にしない）
DIR_FEATS = ["dev_z", "taker_ls", "rsi_db", "rsi_slope", "stoch_k_db",
             "ret_3", "ret_10", "dist_swing"]
# 脇役（バリア幅・importance 監視・vol_share に算入）
VOL_FEATS = ["atr_pct", "bb_width"]


def main():
    SMOKE = "--smoke" in sys.argv
    _log("[E28 Phase1] ドルバー行き過ぎ メタラベリング（一次=5%ile高recall・ラベル=net>0方向・採点なし）")
    rg.assert_no_future_ref(pathlib.Path(__file__).read_text())
    rg.assert_period_split(TRAIN_END, pd.Timestamp("2025-04-01"))

    # ---- 価格・ドルバー・全指標（e28 と完全同一の前処理を流用）----
    df = pd.read_csv(e28.CSV); df["ts"] = pd.to_datetime(df["timestamp"])
    opens, highs, lows = df.open.to_numpy(float), df.high.to_numpy(float), df.low.to_numpy(float)
    closes, tss = df.close.to_numpy(float), df.ts.to_numpy()
    db = e28.build_dollar_bars(df)
    db = e28.add_indicators(db)
    db = e28.add_fr(db)
    db = e28.add_oi(db)
    db = add_meta_features(db)

    # ---- MTF（上位足 regime/momentum・e8.build_mtf＝確定バーのみ backward merge・leak-safe）----
    ohlcv = pd.read_csv(e28.CSV); ohlcv["timestamp"] = pd.to_datetime(ohlcv["timestamp"])
    mtf = e8.build_mtf(ohlcv, db.ts).reset_index(drop=True)
    mtf_cols = list(mtf.columns)
    db = pd.concat([db.reset_index(drop=True), mtf], axis=1)

    db_tr = db[db.ts < TRAIN_END].reset_index(drop=True)   # 学習期間のみ

    # ---- 一次（型・高recall）: 行き過ぎ 5%ile cross-in ----
    dev = db_tr.dev_z
    thr = dev.rolling(e28.PCT_WIN, min_periods=200).quantile(Q1RY)
    fires = (dev <= thr) & (dev.shift(1) > thr.shift(1))
    fire_db = db_tr[fires.fillna(False)].reset_index(drop=True)
    _log(f"[一次] 行き過ぎ{Q1RY:.0%}ile cross-in 候補 {len(fire_db)}件（学習期間）")

    feat_cols = DIR_FEATS + VOL_FEATS + mtf_cols
    n = len(closes)

    # ---- ラベル付け: 各候補を eval_engine 前向き sim（net は審判が出す数字・自作禁止）----
    rows = []
    for _, r in fire_db.iterrows():
        si = int(r.idx5m)
        if si < e28.SMA_N or si >= n - e28.HOLD_5M - 2:
            continue
        if not (np.isfinite(r.atr_pct) and np.isfinite(r.swing_low) and r.swing_low > 0):
            continue
        if not np.isfinite(r[feat_cols].to_numpy(dtype=float)).all():
            continue
        tp_pct = float(r.atr_pct * e28.TP_MULT)
        sl_pct = float(np.clip((r.close - r.swing_low) / r.close, 0.005, 0.08))
        tr = ee.simulate_trade(si, ee.LONG, e28.SIZE, opens, highs, lows, closes, tss,
                               tp_pct=tp_pct, sl_pct=sl_pct, max_hold_bars=e28.HOLD_5M, entry_type="maker")
        if tr is None:
            continue
        row = {"sig_ts": pd.Timestamp(r.ts), "net": float(tr.net), "y": int(tr.net > 0),
               "exit": tr.exit_reason, "year": int(pd.Timestamp(r.ts).year)}
        for c in feat_cols:
            row[c] = float(r[c])
        rows.append(row)
    cd = pd.DataFrame(rows).sort_values("sig_ts").reset_index(drop=True)
    if SMOKE:
        cd = cd.tail(150).reset_index(drop=True)
        _log("[SMOKE] 末尾150候補に制限")
    X = cd[feat_cols].to_numpy(dtype=np.float32)
    yv = cd["y"].to_numpy()
    clip = float(cd["net"].abs().quantile(W_CLIP_Q)) or 1.0
    w = cd["net"].abs().clip(upper=clip).to_numpy()
    w = np.where(w <= 0, 1e-6, w)
    spw = float((yv == 0).sum()) / max(1, int((yv == 1).sum()))
    _log(f"[教師] 約定候補 {len(cd)}件 / 勝率(net>0) {yv.mean():.3f} / scale_pos_weight {spw:.2f}"
         f" / 年別件数 {cd.groupby('year').size().to_dict()}")

    # ---- purged k-fold OOF（候補単位・時系列ブロック・embargo 1day）----
    oof = np.full(len(cd), np.nan)
    fold_rows = []
    lp = dict(LPARAMS); lp["scale_pos_weight"] = spw
    ts_all = cd["sig_ts"].to_numpy()
    blocks = np.array_split(np.arange(len(cd)), 2 if SMOKE else N_FOLDS)
    min_ti, min_vi = (40, 15) if SMOKE else (120, 30)
    for fi, vi in enumerate(blocks):
        if len(vi) == 0:
            continue
        v0, v1 = cd["sig_ts"].iloc[vi[0]], cd["sig_ts"].iloc[vi[-1]]
        # embargo: val 窓 ±1day と重なる候補を学習から除外（purge）
        purge = (ts_all >= np.datetime64(v0 - EMBARGO)) & (ts_all <= np.datetime64(v1 + EMBARGO))
        ti = np.where(~purge)[0]
        if len(ti) < min_ti or len(vi) < min_vi or len(np.unique(yv[ti])) < 2:
            continue
        dtr = lgb.Dataset(X[ti], label=yv[ti], weight=w[ti])
        m = lgb.train(lp, dtr, num_boost_round=300)
        p = m.predict(X[vi])
        oof[vi] = p
        try:
            auc = roc_auc_score(yv[vi], p)
        except ValueError:
            auc = float("nan")
        fold_rows.append({"fold": fi, "val": f"{v0.date()}〜{v1.date()}", "n": int(len(vi)), "auc": round(float(auc), 3)})
        _log(f"[fold{fi}] {v0.date()}〜{v1.date()} n={len(vi)} train={len(ti)} AUC={auc:.3f}")
    assert fold_rows, "有効 fold 0"

    mask = ~np.isnan(oof)
    oof_auc = float(roc_auc_score(yv[mask], oof[mask])) if len(np.unique(yv[mask])) > 1 else float("nan")
    sp = spearmanr(oof[mask], cd["net"].to_numpy()[mask])
    _log("\n===== Phase 1 判別力（学習期間 OOF・採点なし）=====")
    _log(f"  OOF AUC（net>0 を見分けるか）: {oof_auc:.3f}")
    _log(f"  OOF prob × 実net Spearman   : {sp.correlation:+.3f} (p={sp.pvalue:.3g})")
    _log(f"  fold別 AUC: {[r['auc'] for r in fold_rows]}")

    # ---- 本学習（全候補）→ vol_share（H15）+ importance ----
    dall = lgb.Dataset(X, label=yv, weight=w)
    m_full = lgb.train(lp, dall, num_boost_round=300)
    imp = pd.Series(m_full.feature_importance("gain"), index=feat_cols).sort_values(ascending=False)
    vr = rg.report_vol_importance(dict(zip(feat_cols, m_full.feature_importance("gain"))))
    _log(f"\n[H15 ボラ寄与] vol_share={vr['vol_share']}（停止 {VOL_STOP}）/ top5={vr['top']}")
    taker_rank = list(imp.index).index("taker_ls") + 1 if "taker_ls" in imp.index else -1
    _log(f"[Step2 確認] taker_ls importance 順位 = {taker_rank} / {len(feat_cols)}")
    _log("[重要特徴 top15]\n" + imp.head(15).to_string())

    # ---- prob 5分位 × 実net（厳選/配分の余地が見えるか・採点しない）----
    cd2 = cd.copy(); cd2["oof"] = oof
    sub = cd2.loc[mask]
    q = pd.qcut(sub["oof"], 5, labels=False, duplicates="drop")
    tbl = sub.assign(qbin=q).groupby("qbin").agg(
        n=("net", "count"), winrate=("y", "mean"), net_sum=("net", "sum"), net_mean=("net", "mean")).round(3)
    _log("\n[OOF prob 5分位 × 実net（上位ほど net+ なら厳選/配分の余地）]\n" + tbl.to_string())

    # ---- 年別: 上位 prob（act）の net が 2023 を分離できるか（OOF・採点でない・診断）----
    thr_top = float(np.nanquantile(oof[mask], 0.5))
    act = mask & (oof >= thr_top)
    yr_all = cd.groupby("year")["net"].sum().round(0).to_dict()
    yr_act = cd[act].groupby("year")["net"].sum().round(0).to_dict()
    _log(f"\n[年別 net（OOF診断・prob上位50%=act）]\n  全候補: {yr_all}\n  act   : {yr_act}（2023 が + に転じるか）")

    out = {"_source": "train_e28_meta.py（E28 Phase1・メタラベリング・判別力測定・採点なし）",
           "PRIMARY": f"行き過ぎ{Q1RY:.0%}ile cross-in", "N_CAND": int(len(cd)),
           "BASE_RATE": round(float(yv.mean()), 3), "OOF_AUC": round(oof_auc, 3),
           "PROB_NET_SPEARMAN": round(float(sp.correlation), 3), "FOLDS": fold_rows,
           "VOL_SHARE": vr["vol_share"], "TAKER_RANK": taker_rank,
           "YR_ALL": yr_all, "YR_ACT": yr_act,
           "_top15": {k: round(float(v), 1) for k, v in imp.head(15).to_dict().items()}}
    json.dump(out, open(RAT / "e28_meta_phase1.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    _log("\n[out] results/priority_rebuild/ratchet/e28_meta_phase1.json")
    _log("→ Phase1 のみ（採点なし）。AUC・vol_share・taker_ls順位・2023分離 を見て Phase 2（採点・別途 GO）へ。")


if __name__ == "__main__":
    main()
