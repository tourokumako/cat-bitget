#!/usr/bin/env python3
"""save_ml_artifacts.py — Phase 4-a の train fit artifact を ml_artifacts/ に集約

L-183 #13 解消:
  旧版は test 2025 features で scaler/kmeans を再 fit して artifact 化していた
  (= data snooping / out-of-sample 評価が偽の根源)。
  新版は Phase 4-a (train fit) で既に保存済みの joblib をコピー + roundtrip 検証のみ。
  test 2025 への再 fit ロジックは完全削除。

入力:
  results/priority_rebuild/ml_phase4_a/scaler_train_2021_2024.joblib
  results/priority_rebuild/ml_phase4_a/kmeans_k4_train_2021_2024.joblib
  results/priority_rebuild/ml_phase4_a/features.parquet (train 期間・26 列 + close)
  results/priority_rebuild/ml_phase4_a/cluster_labels_train_k4.parquet (roundtrip 比較用)

出力 (results/priority_rebuild/ml_artifacts/):
  scaler_train_2021_2024.joblib       StandardScaler (26 次元・train fit)
  kmeans_k4_train_2021_2024.joblib    KMeans k=4 (train fit)
  feature_columns.json                26 派生特徴量カラム名 (順序保持)
  artifact_meta.json                  fitted_on / inertia / source_dir 等

assertion:
  artifact 名に "test" 文字列禁止 (checklist 4a.4 / 7c.9 先行実装)
  artifact 名に "train_2021_2024" を含むこと
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import joblib
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
PHASE4A_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase4_a"
OUT_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_artifacts"

N_CLUSTERS = 4

SCALER_SRC = PHASE4A_DIR / "scaler_train_2021_2024.joblib"
KMEANS_SRC = PHASE4A_DIR / f"kmeans_k{N_CLUSTERS}_train_2021_2024.joblib"
FEATURES_SRC = PHASE4A_DIR / "features.parquet"
CLUSTER_TRAIN_SRC = PHASE4A_DIR / f"cluster_labels_train_k{N_CLUSTERS}.parquet"

SCALER_DST = OUT_DIR / "scaler_train_2021_2024.joblib"
KMEANS_DST = OUT_DIR / f"kmeans_k{N_CLUSTERS}_train_2021_2024.joblib"


def assert_artifact_naming(path: Path) -> None:
    """artifact 命名規約: "test" 文字列禁止・"train_2021_2024" 含むこと"""
    assert "test" not in path.name, f"ABORT: test-named artifact detected: {path}"
    assert "train_2021_2024" in path.name, \
        f"ABORT: artifact must contain 'train_2021_2024': {path}"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # assertion: 出力パスの命名規約検査 (L-183 / checklist 4a.4)
    for p in [SCALER_DST, KMEANS_DST]:
        assert_artifact_naming(p)
    print(f"✅ artifact naming assertions passed (no 'test', contains 'train_2021_2024')")

    # 入力 artifact 存在確認
    for src in [SCALER_SRC, KMEANS_SRC, FEATURES_SRC]:
        if not src.exists():
            raise FileNotFoundError(
                f"Phase 4-a artifact not found: {src}\n"
                f"  → Phase 4-a (run_phase4_a.py) を先に実行してください"
            )

    # Phase 4-a artifact コピー (再 fit せず・L-183 #13 解消)
    shutil.copy2(SCALER_SRC, SCALER_DST)
    shutil.copy2(KMEANS_SRC, KMEANS_DST)
    print(f"copied scaler: {SCALER_SRC.name} -> {SCALER_DST.name}")
    print(f"copied kmeans: {KMEANS_SRC.name} -> {KMEANS_DST.name}")

    # roundtrip 検証 (コピー後の joblib がロード可能か)
    scaler = joblib.load(SCALER_DST)
    km = joblib.load(KMEANS_DST)
    print(f"  scaler loaded: {type(scaler).__name__}")
    print(f"  kmeans loaded: k={km.n_clusters}, inertia={km.inertia_:.0f}")

    # feature_columns.json (Phase 4-a features.parquet の 26 派生特徴量列)
    feat = pd.read_parquet(FEATURES_SRC)
    feature_cols = [c for c in feat.columns if c != "close"]
    assert len(feature_cols) == 26, f"expected 26 features, got {len(feature_cols)}"
    with open(OUT_DIR / "feature_columns.json", "w") as f:
        json.dump(feature_cols, f, indent=2)
    print(f"saved feature_columns.json ({len(feature_cols)} cols)")

    # artifact_meta.json
    meta = {
        "fitted_on": "predictions_train_2021_2024.parquet",
        "n_clusters": int(km.n_clusters),
        "n_features": len(feature_cols),
        "inertia": float(km.inertia_),
        "source_dir": str(PHASE4A_DIR.relative_to(REPO_ROOT)),
        "naming_rule": "train_2021_2024 (no 'test' substring)",
    }
    with open(OUT_DIR / "artifact_meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    print("saved artifact_meta.json")

    # Phase 4-a cluster_labels_train_k4.parquet との roundtrip 一致確認
    if CLUSTER_TRAIN_SRC.exists():
        Xs = scaler.transform(feat[feature_cols].values)
        clusters = km.predict(Xs)
        clusters_p4a = pd.read_parquet(CLUSTER_TRAIN_SRC)["cluster"].values
        match = (clusters == clusters_p4a).all()
        if match:
            print(f"  roundtrip vs Phase 4-a cluster_labels_train_k{N_CLUSTERS}: MATCH ✅ (n={len(clusters)})")
        else:
            diff = (clusters != clusters_p4a).sum()
            print(f"  roundtrip vs Phase 4-a: MISMATCH ❌ ({diff}/{len(clusters)} differ)")
    else:
        print(f"  (skip roundtrip: {CLUSTER_TRAIN_SRC.name} not found)")


if __name__ == "__main__":
    main()
