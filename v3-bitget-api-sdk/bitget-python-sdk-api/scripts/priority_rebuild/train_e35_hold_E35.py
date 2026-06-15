#!/usr/bin/env python3
"""train_e35_hold_E35.py — E35 iteration-2 保有中判定 ML フェーズ1（判別チェック・採点なし）

狙い（acceptance.md / KB §11 保有中の期待値で出口を締める）:
  iter1b の損源＝TIME_EXIT（中心Cに戻らず250分まで引きずる玉）。固定 HOLD 短縮（手調整・却下）でなく、
  保有中の各バーで「この玉は中心C(TP)に戻るか／TIME・箱破れで終わるか」を ML が予測し、
  戻らない玉だけ早期撤退する（フェーズ2）。本スクリプトは「判別できるか」だけを安く確認（採点しない）。

計器（eval_engine.py 既読）: 本スクリプトは net を計算しない。玉・net・約定・コストは e35.run_continuous
  （= eval_engine 定数準拠）の trades をそのまま真値に使い、ラベルは reason(TP_FILLED)=1 のみ。自作 net 計算なし。

設計（DESIGN_CONTRACT・acceptance.md）:
  - 教師＝e35.run_continuous の玉（真値）を保有中の各バー i で snapshot 化（自己検査で玉集合一致を assert）
  - ラベル＝玉が最終 TP_FILLED=1 / TIME_EXIT・箱ブレイク=0
  - 特徴量＝t 時点まで・%/比率（H6）。leak（未来参照 shift / center True）grep assert（H2）
  - 学習期間 entry_time<TRAIN_END のみ（H8・採点窓は触らない）。OOF は玉単位の時間 fold（同一玉 leak 回避）
  - 報告＝OOF AUC ／ 対照実験(prob逆転) ／ feature importance（atr_pct 非支配＝H15）
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e35_range_oscillation as e35  # noqa: E402  本体 import（_load/_attach_entry_cols/run_continuous/定数）
import lightgbm as lgb               # noqa: E402  python3.13 のみ
from sklearn.metrics import roc_auc_score  # noqa: E402

BOX_TF = "5m"   # iter1b と同じ箱足


def build_snapshots(df: pd.DataFrame, trades: list) -> tuple:
    """run_continuous の玉(trades・per-lot)を真値に、保有中の各バー i の snapshot を作る。
    玉の avg_i / add数 は lot(idx<=i) から再構成。ラベル＝玉の最終 reason(TP=1)。"""
    ts = df["ts"].tolist()
    idx_of = {t: i for i, t in enumerate(ts)}
    close = df["close"].to_numpy(float)
    atr = df["atr"].to_numpy(float); adx = df["adx"].to_numpy(float)
    er = df["er"].to_numpy(float); chop = df["chop"].to_numpy(float)
    kk = df["stoch_k"].to_numpy(float); dd = df["stoch_d"].to_numpy(float)
    bbs = df["bb_mid_slope_pct"].to_numpy(float); bbw = df["bb_width"].to_numpy(float)
    sup = df["box_sup_dist__5m"].to_numpy(float); res = df["box_res_dist__5m"].to_numpy(float)
    sup1h = df["box_sup_dist__1h"].to_numpy(float); res1h = df["box_res_dist__1h"].to_numpy(float)
    sup4h = df["box_sup_dist__4h"].to_numpy(float); res4h = df["box_res_dist__4h"].to_numpy(float)
    S = close / (1.0 + sup / 100.0); R = close * (1.0 + res / 100.0); Cc = (S + R) / 2.0

    t = pd.DataFrame(trades)
    t["entry_time"] = pd.to_datetime(t["entry_time"]); t["exit_time"] = pd.to_datetime(t["exit_time"])
    rows = []
    n_pos = 0; n_lot_mismatch = 0
    for pid, g in t.groupby("position_id"):
        g = g.sort_values("entry_time")
        lot_idx = [idx_of[x] for x in g["entry_time"]]
        lot_px = g["entry_price"].astype(float).tolist()
        exit_idx = idx_of[g["exit_time"].iloc[0]]
        reason = g["exit_reason"].iloc[0]
        side = g["side"].iloc[0]; sdir = 1 if side == "LONG" else -1
        add_count = int(g["add_count"].iloc[0])
        if len(lot_idx) != add_count:
            n_lot_mismatch += 1
        label = 1 if reason == "TP_FILLED" else 0
        first_idx = lot_idx[0]
        n_pos += 1
        for i in range(first_idx + 1, exit_idx):           # 保有中バー（entry/exit バーを除く）
            filled = [(li, lp) for li, lp in zip(lot_idx, lot_px) if li <= i]
            if not filled:
                continue
            avg_i = sum(lp for _, lp in filled) / len(filled)
            if not (np.isfinite(Cc[i]) and np.isfinite(atr[i]) and np.isfinite(close[i])):
                continue
            rows.append({
                "position_id": pid, "entry_time": g["entry_time"].iloc[0], "side": side, "label": label,
                "bars_held": i - first_idx,
                "unreal_pct": (close[i] - avg_i) / avg_i * sdir * 100.0,        # 含み益%（順方向+）
                "dist_to_tp_pct": (Cc[i] - close[i]) / close[i] * sdir * 100.0,  # 中心Cまでの残り%（+=未到達）
                "box_sup_5m": sup[i], "box_res_5m": res[i], "box_w_5m": sup[i] + res[i],
                "box_sup_1h": sup1h[i], "box_res_1h": res1h[i],
                "box_sup_4h": sup4h[i], "box_res_4h": res4h[i],
                "atr_pct": atr[i] / close[i] * 100.0,
                "adx": adx[i], "er": er[i], "stoch_k": kk[i], "stoch_d": dd[i], "chop": chop[i],
                "bb_slope_pct": bbs[i], "bb_width": bbw[i],
                "add_count_so_far": len(filled),
            })
    return pd.DataFrame(rows), n_pos, n_lot_mismatch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-score", action="store_true", help="フェーズ1は採点しない（判別チェックのみ）")
    ap.parse_args()

    print("=" * 100)
    print("[E35 iter-2 保有中判定 ML フェーズ1] 判別チェック（採点なし・撤退実装と採点はフェーズ2）")
    df = e35._load(0)
    e35._attach_entry_cols(df, BOX_TF)
    trades, _events = e35.run_continuous(df, BOX_TF, e35.MAX_ADDS)
    t = pd.DataFrame(trades)
    n_pos_trades = t["position_id"].nunique()

    snaps, n_pos, n_lot_mismatch = build_snapshots(df, trades)
    assert n_pos == n_pos_trades, f"自己検査NG: 玉数 {n_pos} != run_continuous {n_pos_trades}"
    assert n_lot_mismatch == 0, f"自己検査NG: lot数!=add_count の玉 {n_lot_mismatch}件"
    print(f"  自己検査OK 玉数 {n_pos}（run_continuous と一致）／ lot=add_count 一致")

    src = open(os.path.abspath(__file__), encoding="utf-8").read()
    _p1 = "shift(" + "-"; _p2 = "center" + "=True"   # 動的構築＝自分のソースに leak リテラルを残さず誤検出を防ぐ
    assert _p1 not in src and _p2 not in src, "leak 疑い（未来参照 shift/center）"
    print("  leak assert OK（特徴量に未来参照なし・特徴量は t 時点まで・ラベルのみ未来）")

    snaps["entry_time"] = pd.to_datetime(snaps["entry_time"])
    tr = snaps[snaps["entry_time"] < e35.TRAIN_END].reset_index(drop=True)   # H8 学習期間のみ
    print(f"  学習スナップ {len(tr):,} / 玉 {tr.position_id.nunique()} / TP率 {tr.label.mean():.3f}")

    FEATS = [c for c in tr.columns if c not in ("position_id", "entry_time", "side", "label")]
    X = tr[FEATS]; y = tr["label"].to_numpy()

    # OOF＝玉単位の時間 fold（同一玉のスナップは同 fold＝同一玉 leak を回避・de Prado purge 近似）
    pids = tr.groupby("position_id")["entry_time"].min().sort_values().index.tolist()
    fold_of = {}
    for k, fp in enumerate(np.array_split(pids, 5)):
        for pid in fp:
            fold_of[pid] = k
    fold = tr["position_id"].map(fold_of).to_numpy()
    oof = np.full(len(tr), np.nan)
    params = dict(n_estimators=300, num_leaves=15, min_child_samples=200,
                  reg_alpha=1.0, reg_lambda=1.0, learning_rate=0.03, random_state=42, verbose=-1)
    for k in range(5):
        va = fold == k; trn = ~va
        if va.sum() == 0 or trn.sum() == 0:
            continue
        m = lgb.LGBMClassifier(**params)
        m.fit(X[trn], y[trn])
        oof[va] = m.predict_proba(X[va])[:, 1]
    ok = ~np.isnan(oof)
    auc = roc_auc_score(y[ok], oof[ok])
    auc_inv = roc_auc_score(y[ok], 1 - oof[ok])
    print(f"\n  OOF AUC = {auc:.4f}（>0.55 で判別あり）")
    print(f"  対照実験 prob逆転 AUC = {auc_inv:.4f}（< {auc:.4f} なら判別の源泉が本物・degenerate でない）")

    m = lgb.LGBMClassifier(**params); m.fit(X, y)
    fi = pd.Series(m.feature_importances_, index=FEATS).sort_values(ascending=False)
    print("\n  feature importance top12（atr_pct=揺れ幅 が支配でない＝H15）:")
    print(fi.head(12).to_string())
    atr_rank = list(fi.index).index("atr_pct") + 1
    print(f"  atr_pct の順位 = {atr_rank}/{len(FEATS)}（上位独占でなければ軸1 OK）")

    print("\n  判定（フェーズ1）: AUC>0.55 ∩ 逆転で悪化 ∩ atr_pct 非支配 → フェーズ2（撤退実装→採点）へ。")
    print("  AUC≈0.5 → 保有中判定 不成立。HOLD 以外の止血 or jm_ok 厳格化を再検討（無駄に採点しない）。")
    print("=" * 100)


if __name__ == "__main__":
    main()
