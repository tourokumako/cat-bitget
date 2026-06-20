#!/usr/bin/env python3
"""train_p23_entry_E12.py — P23 Entry「TP できるか（実Exit で net>0）」学習＋金額重み（strat_v9ml_design §10.17.1 章7-2・まこさん承認 2026-06-10）

設計（章7-2・確定）:
  - ラベル = 「この型バーから章6の実Exitセット（V9 固定値）で入った場合 net がプラスになるか」の二値。
    教師 = typeonly 候補の独立前向き sim 実 net（p23_candidates_typeonly.csv = gen.simulate_independent・
    V9base Exit・add込み・eval_engine コスト控除後）。E10 の MFE%≥T ラベルは廃止（ラベル≠実出口が敗因＝
    prob×実net Spearman −0.08）。ラベルを作るバリア＝採点で使う Exit と完全一致（Triple Barrier の鉄則）。
  - ラベルは net の符号のみ（金額にしない・H15）。金額はサンプル重み w=|net|（学習期間 p99 クリップ）に
    入れる（AFML §4.6 Return Attribution・大勝ち玉の誤分類を金額比で重く罰し fat-tail を守る）。
  - 特徴量 = E10 と同一（e8b.build_multiperiod + make_features・複数期間 方向系＋MTF・ボラ系除外＝軸1）。
    変更は「ラベル＋重み」の1テーマのみ（H16）。
  - 本スクリプトは Step A（学習＋健全性測定・採点しない）:
      purged k-fold（5分割・label 区間 [entry_time, exit_time] purge＋embargo 1日）で
      ① Spearman(prob, 実net)（E10 −0.08 → プラス転換が核心の検証）
      ② vol_share / feature importance（H15・揺れ幅支配なら停止相当の警告）
      ③ 較正（prob 10分位 × 実net の単調性）
      ④ 過学習（best_iter・fold 間ばらつき）
      を測って報告する。score.py 採点・サイズ配分は Step B（まこさん GO 後・別実行）。
  - 採点期間（2025-04〜）の行は Step A では一切触れない（メトリクスも出さない・類型C回避）。

★ 不正防止3点（cat_requirements §8.4-2.9）: 判定は score.py の数字のみ（Step B）／実装後 独立レビュー→
  指摘を潰してから採点／番人(ratchet_guards)はメタ確認。本スクリプトは net 計算に触れない（CSV 保存値と
  score/eval_engine import のみ）。gen / replay_csv / score / eval_engine は import のみ・改造しない。
"""
from __future__ import annotations
import sys
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

import replay_csv as rc                       # noqa: E402  V9 リプレイ（import のみ）
import gen_p23_candidates as gen              # noqa: E402  型/_p23_type_fires（import のみ・改造しない）
import ratchet_guards as rg                   # noqa: E402  番人（leak/期間/ボラ可視化・既知答え済）
import train_p23_entry_E8b as e8b             # noqa: E402  特徴量・ラベル照合ヘルパを流用（重複回避）

RAT = e8b.RAT
TRAIN_ENTRY_END = e8b.TRAIN_ENTRY_END         # 2024-12-31（H8）
EMBARGO_END = e8b.EMBARGO_END                 # 2025-04-01（embargo 2025Q1）
SC_START, SC_END = e8b.SC_START, e8b.SC_END

N_FOLDS = 5                                   # purged k-fold 分割数（AFML Ch.7 標準）
PURGE_EMBARGO = pd.Timedelta(days=1)          # fold 境界の embargo（独立 sim の保有は exit_time で purge 済＋緩衝1日）
W_CLIP_Q = 0.99                               # 重み w=|net| のクリップ分位（超大勝ち数件の丸暗記防止・§10.17.1 章7-2）

LPARAMS = dict(objective="binary", metric=["auc", "binary_logloss"], learning_rate=0.03, num_leaves=15,
               min_child_samples=100, feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1,
               lambda_l1=1.0, lambda_l2=1.0, seed=42, verbose=-1)
# ⚠️ scale_pos_weight は使わない: 重み w=|net| が「勝ち$合計 vs 負け$合計」のバランスをそのまま表す。
#    クラス比補正を重ねると金額の意味が二重に歪む（重みの役割＝金額・設計の一部）。


def _log(m):
    print(m, flush=True)


def purged_folds(times_entry: pd.Series, times_exit: pd.Series, n_folds: int):
    """時系列順の contiguous k-fold + purge。
    val = 連続ブロック。train = 残りから「label 区間 [entry, exit] が val 区間＋embargo と重なる行」を除外
    （AFML Ch.7 Purged K-Fold・label 終端は実 exit_time を使う＝独立 sim の保有長を正確に purge）。"""
    order = np.argsort(times_entry.values)
    blocks = np.array_split(order, n_folds)
    for b in blocks:
        if not len(b):
            continue
        v_start = times_entry.iloc[b].min()
        v_end = times_entry.iloc[b].max()
        val_idx = b
        mask_overlap = (times_entry <= v_end + PURGE_EMBARGO) & (times_exit >= v_start - PURGE_EMBARGO)
        train_idx = np.array([i for i in order if not mask_overlap.iloc[i]])
        yield train_idx, val_idx, (v_start, v_end)


def fit_weighted(Xtr, ytr, wtr, Xva, yva, wva):
    """LightGBM 二値 + サンプル重み（金額）。early stopping は val の重み付き logloss/auc。"""
    dtr = lgb.Dataset(Xtr, label=ytr, weight=wtr)
    dva = lgb.Dataset(Xva, label=yva, weight=wva, reference=dtr)
    model = lgb.train(LPARAMS, dtr, num_boost_round=3000, valid_sets=[dva],
                      callbacks=[lgb.early_stopping(80, verbose=False)])
    return model


def decile_table(prob: np.ndarray, net: np.ndarray) -> pd.DataFrame:
    """prob 10分位 × 実net（較正の中身）。単調なら『確率が net に繋がっている』。"""
    d = pd.DataFrame({"prob": prob, "net": net})
    d["decile"] = pd.qcut(d["prob"].rank(method="first"), 10, labels=False)
    g = d.groupby("decile").agg(n=("net", "size"), prob_mean=("prob", "mean"),
                                net_mean=("net", "mean"), net_sum=("net", "sum"),
                                win_rate=("net", lambda s: float((s > 0).mean())))
    return g.reset_index()


def main():
    SMOKE = "--smoke" in sys.argv
    _log("[E12 Step A] Entry「TP できるか（実Exit で net>0）」学習＋金額重み（採点しない・健全性測定のみ）")

    # 静的番人（実行前）: leak 未来参照 / 期間分割
    rg.assert_no_future_ref(pathlib.Path(__file__).read_text())
    rg.assert_no_future_ref(pathlib.Path(e8b.__file__).read_text())
    rg.assert_period_split(TRAIN_ENTRY_END, SC_START)

    # ---- データ（P23 のみ有効・gen.main と同条件）----
    params = rc._load_params()
    p23 = dict(params)
    for k in list(p23):
        if k.startswith("ENABLE_P") and k.endswith(("_LONG", "_SHORT")):
            p23[k] = (k == "ENABLE_P23_SHORT")
    df, _ = rc.preload(str(gen.OHLCV_CSV), p23)
    ohlcv = pd.read_csv(e8b.OHLCV)
    ohlcv["timestamp"] = pd.to_datetime(ohlcv["timestamp"])
    mp = e8b.build_multiperiod(ohlcv)                          # 複数期間 方向系（ボラ系除外＝軸1・E10 と同一）

    # ---- 型バー（θ足切りなし＝全部）→ 教師 net（typeonly CSV・V9base 実Exit・再 sim 不要）----
    type_bars = [i for i in range(rc.CANDLE_WARMUP, len(df)) if gen._p23_type_fires(df, i)]
    _log(f"[型バー] {len(type_bars)} 本")
    lab = e8b.label_from_csv(df, type_bars)                    # bar_i/bar_time/entry_time/exit_time/net_usd
    lab = lab.drop_duplicates(subset=["bar_i"], keep="first").reset_index(drop=True)
    _log(f"[教師] typeonly CSV 照合 {len(lab)} 件（独立前向き sim・V9base 実Exit・add込み・コスト控除後）")

    # ---- 学習期間のみ（H8: entry<学習末 かつ exit<embargo 末＝採点期間の行は Step A で一切触れない）----
    tr = lab[(lab["bar_time"] < TRAIN_ENTRY_END) & (lab["exit_time"] < EMBARGO_END)].reset_index(drop=True)
    assert len(tr) > 0, "学習行が 0 件"
    assert tr["bar_time"].max() < TRAIN_ENTRY_END and tr["exit_time"].max() < SC_START, \
        "H8: 学習行が採点期間に侵入"
    if SMOKE:
        tr = tr.tail(4000).reset_index(drop=True)
        _log(f"[SMOKE] 学習行を末尾 {len(tr)} 件に制限（配管確認のみ）")

    # ---- ラベル y = net>0（符号のみ・H15）／重み w = |net|（学習 p99 クリップ・金額の役割分離）----
    net = tr["net_usd"].astype(float)
    y = (net > 0).astype(int).values
    w_raw = net.abs()
    clip_at = float(w_raw.quantile(W_CLIP_Q))
    w = w_raw.clip(upper=clip_at).values
    keep = w > 0                                               # |net|=0 は情報ゼロ（重み0）＝除外
    tr, y, w = tr[keep].reset_index(drop=True), y[keep], w[keep]
    n_pos = int(y.sum())
    _log(f"[ラベル] y=net>0: 勝ち {n_pos} / 全 {len(y)}（{n_pos/len(y)*100:.1f}%）・"
         f"重み w=|net| p99クリップ ${clip_at:.2f}・勝ち$重み比 {w[y==1].sum()/w.sum()*100:.1f}%")

    # ---- 特徴量（E10 と同一・方向系＋MTF・ボラ系除外 assert は make_features 内）----
    X = e8b.make_features(tr["bar_time"], mp, ohlcv)

    # ---- purged k-fold（label 区間 purge＋embargo 1日）: 健全性4点 ----
    folds = list(purged_folds(tr["entry_time"], tr["exit_time"], 2 if SMOKE else N_FOLDS))
    rows, oof = [], []
    for fi, (ti, vi, (v0, v1)) in enumerate(folds):
        if len(ti) < 500 or len(vi) < 100 or len(np.unique(y[ti])) < 2:
            _log(f"[fold{fi}] スキップ（train {len(ti)} / val {len(vi)} 件不足）")
            continue
        m = fit_weighted(X.iloc[ti], y[ti], w[ti], X.iloc[vi], y[vi], w[vi])
        p = m.predict(X.iloc[vi], num_iteration=m.best_iteration)
        nv = tr["net_usd"].values[vi]
        sp = spearmanr(p, nv)
        auc = roc_auc_score(y[vi], p) if len(np.unique(y[vi])) > 1 else float("nan")
        rows.append({"fold": fi, "val_start": str(v0.date()), "val_end": str(v1.date()),
                     "n_train": len(ti), "n_val": len(vi), "best_iter": int(m.best_iteration),
                     "spearman_prob_net": round(float(sp.statistic), 4), "auc": round(float(auc), 4)})
        oof.append(pd.DataFrame({"fold": fi, "bar_time": tr["bar_time"].values[vi],
                                 "prob": p, "net_usd": nv, "y": y[vi], "w": w[vi]}))
        _log(f"[fold{fi}] val {v0.date()}〜{v1.date()} n={len(vi)} "
             f"Spearman(prob,net)={sp.statistic:+.4f} AUC={auc:.4f} best_iter={m.best_iteration}")
    assert rows, "有効 fold が 0（データ不足）"
    cv = pd.DataFrame(rows)
    oof = pd.concat(oof, ignore_index=True)

    # ---- 健全性① Spearman(prob, 実net)（E10 −0.08 → プラス転換が核心）----
    sp_all = spearmanr(oof["prob"], oof["net_usd"])
    _log(f"\n[① prob×実net] OOF Spearman = {sp_all.statistic:+.4f}（E10 は −0.08）／ "
         f"fold平均 {cv['spearman_prob_net'].mean():+.4f} ± {cv['spearman_prob_net'].std():.4f}")

    # ---- 健全性③ 較正（prob 10分位 × 実net・単調なら確率が net に繋がっている）----
    dt = decile_table(oof["prob"].values, oof["net_usd"].values)
    mono = spearmanr(dt["decile"], dt["net_mean"]).statistic
    _log(f"[③ 較正] prob 10分位 × 実net（単調性 Spearman={mono:+.2f}・+1 が理想）\n" + dt.to_string(index=False))

    # ---- 健全性②④ 全学習行で参考モデル → vol_share / importance / 過学習 ----
    m_full = fit_weighted(X.iloc[:int(len(X)*0.85)], y[:int(len(X)*0.85)], w[:int(len(X)*0.85)],
                          X.iloc[int(len(X)*0.85):], y[int(len(X)*0.85):], w[int(len(X)*0.85):])
    vr = rg.report_vol_importance(dict(zip(m_full.feature_name(), m_full.feature_importance("gain"))))
    imp = pd.Series(m_full.feature_importance("gain"), index=X.columns).sort_values(ascending=False)
    _log(f"\n[② ボラ可視化] vol_share={vr['vol_share']}（H15・X からボラ系除外済＝0 期待） / top5={vr['top']}")
    _log(f"[④ 過学習] best_iter fold別 {cv['best_iter'].tolist()} / 参考モデル {m_full.best_iteration}")
    _log("[重要特徴 top15]\n" + imp.head(15).to_string())

    # ---- 保存（Step A 記録・E番号付き＝analysis_playbook §3.1）----
    oof.to_csv(RAT / "trades_p23_E12_stepA_cv.csv", index=False)
    out = {
        "_source": "train_p23_entry_E12.py Step A（§10.17.1 章7-2・採点なし・健全性測定）",
        "_design": "ラベル=実Exit(V9base)で net>0 の二値（typeonly CSV 教師）・重み w=|net| p99クリップ・"
                   "特徴量=E10 と同一（方向系＋MTF）・purged k-fold（label区間 purge＋embargo 1日）",
        "SMOKE": SMOKE,
        "N_TRAIN_ROWS": int(len(tr)),
        "LABEL_POS_RATE": round(float(y.mean()), 4),
        "W_CLIP_P99_USD": round(clip_at, 2),
        "OOF_SPEARMAN_PROB_NET": round(float(sp_all.statistic), 4),
        "OOF_SPEARMAN_E10_REF": -0.08,
        "CALIB_DECILE_MONOTONIC_SPEARMAN": round(float(mono), 3),
        "VOL_SHARE": vr["vol_share"],
        "CV_FOLDS": rows,
        "_top_features_gain": {k: round(float(v), 1) for k, v in imp.head(12).to_dict().items()},
    }
    json.dump(out, open(RAT / "p23_learned_params_E12_stepA.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    _log(f"\n[out] CV予測（学習期間OOFのみ）→ trades_p23_E12_stepA_cv.csv")
    _log(f"[out] Step A 記録 → p23_learned_params_E12_stepA.json")
    _log("[次] 結果をまこさんに報告 → GO 後に Step B（prob→サイズ連続配分・連続モード・score.py 採点）")


if __name__ == "__main__":
    main()
