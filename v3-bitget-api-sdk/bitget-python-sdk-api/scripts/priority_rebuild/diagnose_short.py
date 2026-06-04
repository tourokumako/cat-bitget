#!/usr/bin/env python3
"""diagnose_short.py — E3 で SHORT が死んだ原因切り分け（学習 vs 判定 vs 素材）。

調査1: 局面別の予測勝率（モデルが下落で「SHORT勝てる」と思っているか）
調査2: SHORTモデルの feature importance（MA/regime/上位足の素材を使っているか）
調査3: SHORT予測値の分布（θ0.5を超えるbarが存在するか）
調査4: 下落barで実際にSHORTした時の勝率（素材で分離可能か）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402

import eval_engine as ee  # noqa: E402
import strat_v1 as s  # noqa: E402


def log(m):
    print(m, flush=True)


arrays, ts2idx = s.load_ohlc()
opens, highs, lows, closes, tss = arrays
feats = s.select_features(pq.ParquetFile(s.TRAIN_PQ).schema.names)
feat_all = feats + s.REGIME_FEATS

Xtr = pd.read_parquet(s.TRAIN_PQ, columns=feats).join(
    pd.read_parquet(s.REGIME_TRAIN, columns=s.REGIME_FEATS), how="left")

models = {}
for side in s.SIDE_PARAMS:
    y = s.make_labels(side, Xtr.index, ts2idx, arrays)
    models[side] = s.train_model(Xtr[feat_all].to_numpy(), y, feat_all)
    log(f"[train] {side} 完了")

Xte = pd.read_parquet(s.TEST_PQ, columns=feats).join(
    pd.read_parquet(s.REGIME_TEST, columns=s.REGIME_FEATS), how="left")
Xte = Xte[(Xte.index >= s.SCORE_START) & (Xte.index <= s.SCORE_END)]

# 局面判定（1h & 4h の価格 vs ema50）
c1 = [c for c in Xte.columns if "ema50" in c and "__1h" in c]
c4 = [c for c in Xte.columns if "ema50" in c and "__4h" in c]
c1, c4 = c1[0], c4[0]
log(f"\n使用MA列: {c1}, {c4}")
down = (Xte[c1] < 0) & (Xte[c4] < 0)
up = (Xte[c1] > 0) & (Xte[c4] > 0)
log(f"採点期間 n={len(Xte):,} / 下落bar={int(down.sum()):,} 上昇bar={int(up.sum()):,} レンジ={int((~down & ~up).sum()):,}")

pred = {k: models[k].predict(Xte[feat_all].to_numpy()) for k in models}

log("\n=== 調査1: 局面別 予測勝率（モデルが各局面で勝てると思うか）===")
for k in models:
    log(f"  {k}: 全={pred[k].mean():.3f}  下落={pred[k][down.values].mean():.3f}  上昇={pred[k][up.values].mean():.3f}")

log("\n=== 調査3: SHORT予測分布（θ0.5超のbarがあるか）===")
sp, lp = pred["SHORT"], pred["LONG"]
log(f"  SHORT: max={sp.max():.3f} p90={np.percentile(sp, 90):.3f} p99={np.percentile(sp, 99):.3f} "
    f">=0.5割合={(sp >= 0.5).mean():.4f}  下落bar内>=0.5={(sp[down.values] >= 0.5).mean():.4f}")
log(f"  LONG : max={lp.max():.3f} >=0.5割合={(lp >= 0.5).mean():.4f}")

log("\n=== 調査2: SHORTモデル feature importance top15（素材を使ってるか）===")
imp = models["SHORT"].feature_importance(importance_type="gain")
for i in np.argsort(imp)[::-1][:15]:
    log(f"  {feat_all[i]}: {imp[i]:.0f}")

log("\n=== 調査4: 局面別の実勝率（素材で分離可能か）===")
for side, mask, lbl in [("SHORT", down, "下落bar SHORT"), ("LONG", up, "上昇bar LONG")]:
    p = s.SIDE_PARAMS[side]
    wins = tot = 0
    for ts in Xte.index[mask.values][::5]:  # 5本間引き
        si = ts2idx.get(ts)
        if si is None:
            continue
        r = ee.simulate_trade(si, p["direction"], s.SIZE_BTC, opens, highs, lows, closes, tss,
                              p["tp"], p["sl"], p["hold"])
        if r is None:
            continue
        tot += 1
        wins += int(r.net > 0)
    log(f"  {lbl} 実勝率 = {wins}/{tot} = {wins/max(tot,1):.3f}")
log("\n[診断完了]")
