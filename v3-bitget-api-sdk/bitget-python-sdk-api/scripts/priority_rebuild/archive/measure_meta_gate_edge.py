#!/usr/bin/env python3
"""measure_meta_gate_edge.py — 手③: メタ門番（縦カスケード）の効果測定

位置づけ（execlog 工程[2]「Entry エンジン 修正計画」手③・baseline §6.2 改訂バナー）:
  軸6（§18.5『Meta-Labeling 失敗（primary も secondary も同型）』cc_entry_logic_self_study.md:1576）。
  一段目（TB 方向）が発火したバー **だけ** を、別アーキの二段目（ロジスティック回帰）が
  「その賭けは勝つか(net>0)」で門番する。現「全bar独立 binary・集約一項」を置換。

  手② 実測（measure_primary_direction_edge）= 素の方向は弱エッジ(AUC0.54-0.56)だが per-trade net 負。
  WebSearch: primary が弱くてもゼロでなければメタは効く → 本スクリプトで「門番で黒字部分集合に
  絞れるか」を測る。

設計（軸6・§18.4 + WebSearch 準拠）:
  - 二段目は **primary 発火バーのみ** で学習（全bar独立を排除）
  - **別アーキ**: 一段目 LightGBM → 二段目 LogisticRegression（primary≠secondary）
  - 入力＝一段目の **盲点情報**（非ボラの entry品質シグナル: RSI/Stoch/BB位置/出来高/OBV/VWAP/MTF/DI・
    全 OHLCV 由来・大前提）。ATR/bb_width 等のボラ系は一段目が過用したので **入れない**。
  - LONG/SHORT 別に二段目を学習（勝敗ダイナミクスが side で異なる・手② の分離と整合）

leak 計画（Step 0 ⑥）:
  ① 特徴量＝既存生成列（shift(-)なし・Phase0 leak verify 済）・新規生成なし
  ② 二段目は train OOF のみで学習 → test 適用（test を学習に使わない・assert train末<test始）
  ③ 一段目 train 予測＝baseline OOF（fold外・Purged K-Fold 済 → 一段目 leak なし）
  ④ メタ正解(won)も train 期間 OHLC のみ（eval_engine が未来非参照）
  ⑤ StandardScaler は train のみ fit

データ:
  一段目 train＝ml_phase2_baseline/.../fold0-2（OOF 連結）/ test＝ml_phase2_production
  盲点特徴量＝labels_mfe_mae_pct_{train_2021_2024,test_2025,test_2026_q1}.parquet
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eval_engine as ee  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
PROD = REPO / "results" / "priority_rebuild" / "ml_phase2_production"
BASE = REPO / "results" / "priority_rebuild" / "ml_phase2_baseline"
CSV = REPO / "data" / "BTCUSDT-5m-bitget-2021-04-01_2026-03-31_5y.csv"
OUT_DIR = REPO / "results" / "priority_rebuild" / "primary_direction_edge"
LABELS = {
    "train": REPO / "results" / "priority_rebuild" / "labels_mfe_mae_pct_train_2021_2024.parquet",
    "test_2025": REPO / "results" / "priority_rebuild" / "labels_mfe_mae_pct_test_2025.parquet",
    "test_2026_q1": REPO / "results" / "priority_rebuild" / "labels_mfe_mae_pct_test_2026_q1.parquet",
}

TP_MULT, SL_MULT, SIZE_BTC = 2.0, 1.5, 0.024
ATR_COL = "atr14_pct__5m"
PROBA = "pred_proba_class2_cal"  # TP 先着確率（class2=TP）

# 二段目 盲点特徴量（非ボラ entry品質シグナル + MTF・ATR/bb_width 等は除外）
BLIND_FEATURES = [
    "rsi14__5m", "rsi7__5m", "stoch_k__5m", "stoch_d__5m", "stoch_kd_diff__5m",
    "bb_pct_b__5m", "close_vs_vwap20_pct__5m", "close_vs_sma20_pct__5m",
    "close_vs_sma50_pct__5m", "di_diff__5m", "di_plus__5m", "di_minus__5m",
    "adx14__5m", "volume_ratio_20b__5m", "obv_slope_10b__5m", "macd_hist__5m",
    "rsi14__1h", "di_diff__1h", "close_vs_sma20_pct__1h", "adx14__1h",
    "di_diff__4h", "close_vs_sma20_pct__4h",
]
META_THRESHOLDS = [0.50, 0.55, 0.60, 0.65]


def load_bars():
    df = pd.read_csv(CSV, parse_dates=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    ts = df["timestamp"].values.astype("datetime64[ns]")
    ts_to_pos = {str(pd.Timestamp(t)): i for i, t in enumerate(ts)}
    return (df["open"].to_numpy(float), df["high"].to_numpy(float),
            df["low"].to_numpy(float), df["close"].to_numpy(float), ts, ts_to_pos)


def load_primary(period: str, K: int) -> pd.DataFrame:
    """一段目 TP先着確率を LONG/SHORT で結合。train=baseline OOF連結 / test=production。"""
    def _one(side: str) -> pd.DataFrame:
        if period == "train":
            parts = [pd.read_parquet(BASE / f"triple_barrier_label_{side}_K{K}_fold{f}" / "predictions.parquet")
                     [["entry_id", PROBA]] for f in (0, 1, 2)]
            d = pd.concat(parts, ignore_index=True)
        else:
            d = pd.read_parquet(PROD / f"triple_barrier_label_{side}_K{K}" / f"predictions_{period}.parquet")[["entry_id", PROBA]]
        return d.rename(columns={PROBA: f"p_{side.lower()}"})
    dl, ds = _one("LONG"), _one("SHORT")
    return dl.merge(ds, on="entry_id", how="inner")


def build_fired(prim: pd.DataFrame, thr: float, ts_to_pos: dict) -> pd.DataFrame:
    prim = prim.copy()
    prim["side"] = np.where(prim["p_long"] >= prim["p_short"], ee.LONG, ee.SHORT)
    prim["p_chosen"] = np.maximum(prim["p_long"], prim["p_short"])
    fired = prim[prim["p_chosen"] >= thr].copy()
    pos = fired["entry_id"].map(ts_to_pos)
    fired = fired[pos.notna()].copy()
    fired["pos"] = pos[pos.notna()].astype(int).values
    return fired


def simulate(fired: pd.DataFrame, atr: pd.Series, bars) -> pd.DataFrame:
    o, h, l, c, ts, _ = bars
    fired = fired.merge(atr.rename("atr_pct"), left_on="entry_id", right_index=True, how="inner")
    fired = fired.dropna(subset=["atr_pct"])
    nets, wons, filled = [], [], []
    for _, r in fired.iterrows():
        tr = ee.simulate_trade(int(r["pos"]), int(r["side"]), SIZE_BTC, o, h, l, c, ts,
                               float(r["atr_pct"]) * TP_MULT / 100.0,
                               float(r["atr_pct"]) * SL_MULT / 100.0, max_hold_bars=int(r["__K"]))
        if tr is None:
            nets.append(np.nan); wons.append(np.nan); filled.append(False)
        else:
            nets.append(tr.net); wons.append(1 if tr.net > 0 else 0); filled.append(True)
    fired["net"] = nets; fired["won"] = wons; fired["filled"] = filled
    return fired[fired["filled"]].copy()


def load_features(period: str, entry_ids: pd.Series, feats: list[str]) -> pd.DataFrame:
    df = pd.read_parquet(LABELS[period], columns=feats)
    df.index = df.index.astype(str)
    return df.reindex(entry_ids.values)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", default="test_2025", choices=["test_2025", "test_2026_q1"])
    ap.add_argument("--k", type=int, default=12)
    ap.add_argument("--primary-thr", type=float, default=0.40)
    ap.add_argument("--smoke", type=int, default=None, help="train/test fired を先頭N に制限")
    args = ap.parse_args()

    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import roc_auc_score

    print("=" * 70)
    print(f"手③ メタ門番 効果測定 | test={args.test} K={args.k} primary_thr={args.primary_thr} smoke={args.smoke}")
    print("=" * 70)

    bars = load_bars()
    ts_to_pos = bars[5]
    feats = [f for f in BLIND_FEATURES if True]  # 存在チェックは load 時 reindex で NaN 許容

    # ── train: 一段目発火 → メタ正解(won) → 二段目学習 ──────────────────────
    pr_tr = build_fired(load_primary("train", args.k), args.primary_thr, ts_to_pos)
    atr_tr = pd.read_parquet(LABELS["train"], columns=[ATR_COL])
    atr_tr.index = atr_tr.index.astype(str)
    pr_tr["__K"] = args.k
    if args.smoke:
        pr_tr = pr_tr.iloc[:args.smoke].copy()
    sim_tr = simulate(pr_tr, atr_tr[ATR_COL], bars)
    Xtr_all = load_features("train", sim_tr["entry_id"], feats)
    avail = [f for f in feats if f in Xtr_all.columns and Xtr_all[f].notna().mean() > 0.5]
    print(f"[train] fired(filled)={len(sim_tr)} / 盲点特徴量 {len(avail)}/{len(feats)} 採用")

    models = {}
    for side, sname in [(ee.LONG, "LONG"), (ee.SHORT, "SHORT")]:
        m = sim_tr["side"] == side
        Xs = Xtr_all.loc[m.values, avail].fillna(0.0).values
        ys = sim_tr.loc[m, "won"].astype(int).values
        if len(np.unique(ys)) < 2:
            print(f"  [{sname}] 学習不可（won 単一クラス）"); continue
        sc = StandardScaler().fit(Xs)
        lr = LogisticRegression(class_weight="balanced", max_iter=1000).fit(sc.transform(Xs), ys)
        models[side] = (sc, lr)
        print(f"  [{sname}] train fired={m.sum()} 勝率(net>0)={ys.mean():.3f}")

    # ── test: 一段目発火 → 二段目で門番 → net 比較 ──────────────────────────
    pr_te = build_fired(load_primary(args.test, args.k), args.primary_thr, ts_to_pos)
    atr_te = pd.read_parquet(LABELS[args.test], columns=[ATR_COL])
    atr_te.index = atr_te.index.astype(str)
    pr_te["__K"] = args.k
    if args.smoke:
        pr_te = pr_te.iloc[:args.smoke].copy()
    sim_te = simulate(pr_te, atr_te[ATR_COL], bars)
    Xte_all = load_features(args.test, sim_te["entry_id"], avail)

    # leak assert: train 末 < test 始
    assert sim_tr["entry_id"].max() < sim_te["entry_id"].min(), "leak: train が test 期間に侵入"

    sim_te["p_win"] = np.nan
    for side, (sc, lr) in models.items():
        m = (sim_te["side"] == side).values
        if m.sum() == 0:
            continue
        Xs = Xte_all.loc[m, avail].fillna(0.0).values
        sim_te.loc[m, "p_win"] = lr.predict_proba(sc.transform(Xs))[:, 1]

    valid = sim_te.dropna(subset=["p_win"])
    base_avg = float(valid["net"].mean())
    try:
        auc = float(roc_auc_score(valid["won"].astype(int), valid["p_win"]))
    except Exception:
        auc = float("nan")

    print("-" * 70)
    print(f"[test={args.test}] 門番なし(手②素): n={len(valid)} avg_net/trade={base_avg:+.6f}")
    print(f"二段目 AUC(勝敗判別)={auc:.4f} (0.5=情報なし)")
    rows = []
    for mt in META_THRESHOLDS:
        g = valid[valid["p_win"] >= mt]
        avg = float(g["net"].mean()) if len(g) else float("nan")
        rows.append({"meta_thr": mt, "n_pass": int(len(g)),
                     "pass_rate": round(len(g) / len(valid), 4) if len(valid) else 0.0,
                     "avg_net_per_trade": round(avg, 6) if len(g) else None,
                     "total_net": round(float(g["net"].sum()), 2),
                     "win_rate": round(float(g["won"].mean()), 4) if len(g) else None})
        print(f"  門番 thr={mt}: 通過={len(g):6d} ({rows[-1]['pass_rate']:.1%}) "
              f"avg_net/trade={(f'{avg:+.6f}' if len(g) else 'n/a')} "
              f"total={rows[-1]['total_net']:+.1f}")
    print("-" * 70)

    res = {"手": "③ meta gate", "test": args.test, "K": args.k, "primary_thr": args.primary_thr,
           "smoke": args.smoke, "secondary": "LogisticRegression(class_weight=balanced)",
           "blind_features_used": avail, "train_fired": int(len(sim_tr)),
           "ungated_avg_net_per_trade": round(base_avg, 6), "test_fired": int(len(valid)),
           "secondary_auc": auc, "by_meta_threshold": rows,
           "verdict_hint": "門番で avg_net/trade が ungated より上がり 0 に近づく/超えるか"}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tag = f"meta_{args.test}_K{args.k}_pt{args.primary_thr}" + (f"_smoke{args.smoke}" if args.smoke else "")
    out = OUT_DIR / f"summary_{tag}.json"
    out.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(f"[出力] {out}")


if __name__ == "__main__":
    main()
