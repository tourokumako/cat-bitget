#!/usr/bin/env python3
"""
save_ml_artifacts.py — ML Phase 7-a step 1: scaler + kmeans を joblib 保存

Phase 4-a で fit したが保存していなかった scaler と kmeans を、
test 2025 features で再 fit してアーティファクト化する。
本番運用時に decider から load して再利用できるようにする。

入力:
  results/priority_rebuild/ml_phase3_b/predictions_test2025.parquet

出力 (results/priority_rebuild/ml_artifacts/):
  scaler_test2025.joblib       StandardScaler (26 次元)
  kmeans_k4_test2025.joblib    KMeans k=4 (Phase 4-a 採用)
  feature_columns.json         派生特徴量カラム名 (順序保持)
  artifact_meta.json           random_state / cluster center 等のメタ
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

REPO_ROOT = Path(__file__).resolve().parents[2]
PRED_PATH = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase3_b" / "predictions_test2025.parquet"
OUT_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_artifacts"

LABEL_COLS = [
    f"{side}_{kind}_K{k}"
    for k in (12, 24, 48, 96)
    for side in ("LONG", "SHORT")
    for kind in ("MFE", "MAE")
]
K_WINDOWS = (12, 24, 48, 96)
SIDES = ("LONG", "SHORT")
N_CLUSTERS = 4
RANDOM_STATE = 42


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
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"loading {PRED_PATH}")
    pred = pd.read_parquet(PRED_PATH)
    print(f"  pred: {pred.shape}")

    feat = build_cluster_features(pred)
    feature_cols = feat.columns.tolist()
    assert len(feature_cols) == 26, f"expected 26 features, got {len(feature_cols)}"
    print(f"  features: {len(feature_cols)} cols")

    scaler = StandardScaler()
    Xs = scaler.fit_transform(feat.values)
    print(f"  scaler fit done: mean~{Xs.mean():.2e} std~{Xs.std():.3f}")

    km = KMeans(n_clusters=N_CLUSTERS, random_state=RANDOM_STATE, n_init=10)
    km.fit(Xs)
    print(f"  kmeans fit done: inertia={km.inertia_:.0f}")

    joblib.dump(scaler, OUT_DIR / "scaler_test2025.joblib")
    joblib.dump(km, OUT_DIR / "kmeans_k4_test2025.joblib")
    print("saved scaler + kmeans")

    with open(OUT_DIR / "feature_columns.json", "w") as f:
        json.dump(feature_cols, f, indent=2)

    meta = {
        "random_state": RANDOM_STATE,
        "n_clusters": N_CLUSTERS,
        "n_features": len(feature_cols),
        "fitted_on": "predictions_test2025.parquet",
        "n_rows_fit": int(len(pred)),
        "inertia": float(km.inertia_),
        "cluster_centers_first_3": km.cluster_centers_[:, :3].tolist(),
    }
    with open(OUT_DIR / "artifact_meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    print("saved feature_columns.json + artifact_meta.json")

    # 確認: roundtrip
    print("verifying roundtrip ...")
    scaler_loaded = joblib.load(OUT_DIR / "scaler_test2025.joblib")
    km_loaded = joblib.load(OUT_DIR / "kmeans_k4_test2025.joblib")
    Xs2 = scaler_loaded.transform(feat.values)
    clusters_orig = km.predict(Xs)
    clusters_loaded = km_loaded.predict(Xs2)
    match = (clusters_orig == clusters_loaded).all()
    print(f"  cluster prediction roundtrip: {'MATCH ✅' if match else 'MISMATCH ❌'}")

    # Phase 4-a の cluster_labels_k4.parquet と一致するか
    p4a_path = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase4_a" / "cluster_labels_k4.parquet"
    if p4a_path.exists():
        clusters_p4a = pd.read_parquet(p4a_path)["cluster"].values
        match_p4a = (clusters_loaded == clusters_p4a).all()
        print(f"  vs Phase 4-a cluster_labels_k4: {'MATCH ✅' if match_p4a else 'MISMATCH ❌'}")
        if not match_p4a:
            diff = (clusters_loaded != clusters_p4a).sum()
            print(f"    diff count: {diff}/{len(clusters_p4a)}")


if __name__ == "__main__":
    main()
