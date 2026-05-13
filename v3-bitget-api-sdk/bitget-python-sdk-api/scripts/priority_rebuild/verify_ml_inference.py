#!/usr/bin/env python3
"""
verify_ml_inference.py — ML Phase 7-a step 2: 推論パイプラインの再現性検証

目的: 本番組込み時の「モデルロード → 予測 → cluster」フローが
Phase 3-b/4-a の出力と完全一致するか確認する。

検証項目:
  1. LightGBM 16 モデルを ml_phase3_b/models/ からロード
  2. test 2025 ラベル parquet で予測 → predictions_test2025.parquet と一致
  3. scaler/kmeans アーティファクトで cluster 判定 → cluster_labels_k4.parquet と一致
  4. 1 bar ずつ predict と batch predict が同一結果か (LightGBM の deterministic 確認)

入力:
  results/priority_rebuild/labels_mfe_mae_test_2025.parquet
  results/priority_rebuild/ml_phase3_b/models/lgbm_<label>.txt × 16
  results/priority_rebuild/ml_phase3_b/predictions_test2025.parquet
  results/priority_rebuild/ml_phase4_a/cluster_labels_k4.parquet
  results/priority_rebuild/ml_artifacts/{scaler,kmeans,feature_columns}.{joblib,json}

出力 (stdout のみ・パス/数値の検証結果):
  各検証項目の MATCH / MISMATCH レポート
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
LABELS_PATH = REPO_ROOT / "results" / "priority_rebuild" / "labels_mfe_mae_test_2025.parquet"
P3B_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase3_b"
P4A_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase4_a"
ARTIFACTS = REPO_ROOT / "results" / "priority_rebuild" / "ml_artifacts"

LABEL_COLS = [
    f"{side}_{kind}_K{k}"
    for k in (12, 24, 48, 96)
    for side in ("LONG", "SHORT")
    for kind in ("MFE", "MAE")
]
META_COLS = ["close"]
K_WINDOWS = (12, 24, 48, 96)
SIDES = ("LONG", "SHORT")


def build_cluster_features(pred: pd.DataFrame) -> pd.DataFrame:
    feat = pred[LABEL_COLS].copy()
    eps = 1e-9
    for k in K_WINDOWS:
        for side in SIDES:
            mfe = pred[f"{side}_MFE_K{k}"]
            mae = pred[f"{side}_MAE_K{k}"]
            feat[f"{side}_ratio_K{k}"] = mfe / (mae + eps)
    for side in SIDES:
        feat[f"{side}_long_vs_short"] = pred[f"{side}_MFE_K96"] / (pred[f"{side}_MFE_K12"] + eps)
    return feat.fillna(0.0).replace([np.inf, -np.inf], 0.0)


def main() -> None:
    print("=" * 60)
    print("Phase 7-a step 2: Inference reproducibility verification")
    print("=" * 60)

    print("\n[1] loading test 2025 labels ...")
    df = pd.read_parquet(LABELS_PATH)
    feature_cols = [c for c in df.columns if c not in LABEL_COLS + META_COLS]
    print(f"  shape: {df.shape}, features: {len(feature_cols)}")
    assert len(feature_cols) == 1432

    print("\n[2] loading 16 LightGBM models ...")
    boosters = {}
    for label in LABEL_COLS:
        model_path = P3B_DIR / "models" / f"lgbm_{label}.txt"
        boosters[label] = lgb.Booster(model_file=str(model_path))
    print(f"  loaded: {len(boosters)} models")

    print("\n[3] batch predict (16 labels) ...")
    t0 = time.time()
    pred_new = pd.DataFrame(index=df.index)
    for label in LABEL_COLS:
        pred_new[label] = boosters[label].predict(df[feature_cols])
    print(f"  done in {time.time()-t0:.1f}s")

    print("\n[4] compare vs predictions_test2025.parquet ...")
    pred_orig = pd.read_parquet(P3B_DIR / "predictions_test2025.parquet")
    max_diffs = {}
    for label in LABEL_COLS:
        diff = np.abs(pred_new[label].values - pred_orig[label].values).max()
        max_diffs[label] = diff
    overall_max = max(max_diffs.values())
    print(f"  overall max abs diff: {overall_max:.2e}")
    if overall_max < 1e-6:
        print("  ✅ MATCH (within float64 tolerance)")
    else:
        print(f"  ❌ MISMATCH (max diff = {overall_max:.2e})")
        for label, d in sorted(max_diffs.items(), key=lambda x: -x[1])[:5]:
            print(f"     {label}: {d:.4e}")

    print("\n[5] cluster prediction via saved scaler + kmeans ...")
    scaler = joblib.load(ARTIFACTS / "scaler_test2025.joblib")
    km = joblib.load(ARTIFACTS / "kmeans_k4_test2025.joblib")
    with open(ARTIFACTS / "feature_columns.json") as f:
        feature_cols_26 = json.load(f)
    feat_26 = build_cluster_features(pred_new)
    assert feat_26.columns.tolist() == feature_cols_26, "feature column order mismatch"
    Xs = scaler.transform(feat_26.values)
    clusters_new = km.predict(Xs)

    clusters_p4a = pd.read_parquet(P4A_DIR / "cluster_labels_k4.parquet")["cluster"].values
    match = (clusters_new == clusters_p4a).all()
    if match:
        print(f"  ✅ cluster MATCH (n={len(clusters_new)}, all equal)")
    else:
        diff = (clusters_new != clusters_p4a).sum()
        print(f"  ❌ cluster MISMATCH ({diff}/{len(clusters_new)} differ)")

    print("\n[6] 1-row predict reproducibility (single bar inference) ...")
    # 任意 5 bar を選んで個別 predict → batch と一致するか
    sample_idx = [0, 1000, 50000, 90000, 105119]
    one_row_preds = []
    for si in sample_idx:
        row = df.iloc[[si]][feature_cols]
        one_row = {}
        for label in LABEL_COLS:
            one_row[label] = boosters[label].predict(row)[0]
        one_row_preds.append(one_row)
    print("  sample bar |  batch LONG_MFE_K12 |  1-row LONG_MFE_K12  |  diff")
    for si, opr in zip(sample_idx, one_row_preds):
        batch_v = pred_new["LONG_MFE_K12"].iloc[si]
        one_v = opr["LONG_MFE_K12"]
        d = abs(batch_v - one_v)
        print(f"    bar {si:7d} | {batch_v:18.6f} | {one_v:18.6f} | {d:.2e}")
    max_1row_diff = max(
        abs(pred_new[label].iloc[si] - opr[label])
        for si, opr in zip(sample_idx, one_row_preds)
        for label in LABEL_COLS
    )
    print(f"  max diff across all 5 bars × 16 labels: {max_1row_diff:.2e}")
    if max_1row_diff < 1e-6:
        print("  ✅ single-bar inference reproduces batch")
    else:
        print("  ❌ MISMATCH")

    print("\n" + "=" * 60)
    print("Phase 7-a step 2 verification complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
