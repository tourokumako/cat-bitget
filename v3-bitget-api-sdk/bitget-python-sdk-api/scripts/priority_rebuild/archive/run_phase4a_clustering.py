"""
Phase 4-a k-means クラスタリング (Entry 性質分類)

指示書: .claude/instructions/2026-05-14_phase4a_clustering.md
phase_compliance §4a 準拠:
  4a.1: fit は train 2021-04〜2024-12 のみ (refit 版 predictions 使用)
  4a.2: scaler/km の joblib 保存 (artifact 名に "train" 含む)
  4a.3: test 2025 への apply は transform/predict のみ (再 fit 禁止)
  4a.4: artifact 名禁止: "*test*" 含むファイル名禁止
  4a.5: K96 SHORT q99 フォールバック判定

Steps:
  1. silhouette score 再評価 (k=2〜8)
  2. 採用 k で k-means fit (train のみ)
  3. cluster 性質分析 + K12 LONG サンプル数チェック
  4. K96 SHORT q99 フォールバック判定
  5. test 2025 への apply
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "results" / "priority_rebuild"
REFIT_DIR = DATA_DIR / "ml_phase1_k12long_refit"
PHASE1_DIR = DATA_DIR / "ml_phase1"

TRAIN_PRED_PATH = REFIT_DIR / "predictions_train_2021_2024_k12long_refit.parquet"
# test 2025: refit 版 (K12 LONG 部分更新) を優先・なければ Phase 1 版
TEST_PRED_REFIT = REFIT_DIR / "predictions_test2025_k12long_refit.parquet"
TEST_PRED_P1 = PHASE1_DIR / "predictions_test2025.parquet"
LABELS_TRAIN = DATA_DIR / "labels_mfe_mae_train_2021_2024.parquet"

OUT_DIR = DATA_DIR / "ml_phase4_a"
OUT_DIR.mkdir(parents=True, exist_ok=True)

LABEL_COLS = [
    f"{side}_{kind}_K{k}"
    for k in (12, 24, 48, 96)
    for side in ("LONG", "SHORT")
    for kind in ("MFE", "MAE")
]
RANDOM_STATE = 42
SILHOUETTE_SAMPLE = 20000
K_RANGE = range(2, 9)


def log(msg):
    ts = datetime.now().isoformat(timespec="seconds")
    print(f"[{ts}] {msg}", flush=True)


def step1_silhouette(X_scaled):
    """k=2〜8 で silhouette score を評価."""
    log("Step 1: silhouette score 再評価 (k=2〜8) ...")
    rows = []
    for k in K_RANGE:
        log(f"  k={k} fitting ...")
        km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
        labels = km.fit_predict(X_scaled)
        sil = silhouette_score(
            X_scaled, labels,
            sample_size=SILHOUETTE_SAMPLE, random_state=RANDOM_STATE,
        )
        sizes = pd.Series(labels).value_counts().sort_index().to_dict()
        min_size = min(sizes.values())
        max_size = max(sizes.values())
        size_ratio = min_size / max_size
        log(f"    silhouette={sil:.4f}, sizes={sizes}, min/max={size_ratio:.3f}")
        rows.append({
            "k": k,
            "silhouette": sil,
            "cluster_sizes": json.dumps(sizes),
            "min_size": min_size,
            "max_size": max_size,
            "size_ratio_min_over_max": size_ratio,
        })
    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "silhouette_evaluation.csv", index=False)
    log(f"  saved silhouette_evaluation.csv")
    return df


def choose_k(df_sil):
    """採用 k を決定 (silhouette 最大 + size ratio 0.05 以上)."""
    df = df_sil[df_sil["size_ratio_min_over_max"] >= 0.05]
    if df.empty:
        df = df_sil
    best = df.loc[df["silhouette"].idxmax()]
    return int(best["k"])


def step2_fit(X_scaled, k):
    """採用 k で k-means fit + scaler/km の joblib 保存."""
    log(f"Step 2: k-means fit (k={k}・train のみ) ...")
    km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
    km.fit(X_scaled)
    log(f"  inertia={km.inertia_:.2f} n_iter={km.n_iter_}")
    return km


def step3_cluster_analysis(df, km, X_scaled):
    """cluster 性質分析 + K12 LONG サンプル数チェック."""
    log("Step 3: cluster 性質分析 + K12 LONG サンプル数チェック ...")
    labels = km.labels_
    df = df.copy()
    df["cluster"] = labels

    # cluster size
    sizes = pd.Series(labels).value_counts().sort_index()
    log(f"  cluster sizes: {sizes.to_dict()}")

    # cluster 性質 = 16 予測値の平均
    profile = df.groupby("cluster")[LABEL_COLS].mean()
    profile.to_csv(OUT_DIR / "cluster_profile.csv")
    log(f"  saved cluster_profile.csv")

    # K12 LONG q99 サンプル数チェック
    ratio_k12_long = df["LONG_MFE_K12"] / df["LONG_MAE_K12"].clip(lower=1e-9)
    q99_thr = ratio_k12_long.quantile(0.99)
    mask = ratio_k12_long >= q99_thr
    log(f"  K12 LONG q99 threshold={q99_thr:.4f} total fire={int(mask.sum())}")
    k12_dist = df[mask]["cluster"].value_counts().sort_index()
    log(f"  K12 LONG q99 cluster 別分散:")
    rows = []
    for cl, n in k12_dist.items():
        if n >= 100:
            verdict = "✅ 統計的有意"
        elif n >= 30:
            verdict = "⚠️ 仮説レベル"
        else:
            verdict = "❌ 根拠不足"
        log(f"    cluster {cl}: n={n} {verdict}")
        rows.append({"cluster": int(cl), "n_k12long_q99": int(n), "verdict": verdict})
    # クラスタに 0 件のものも記録
    for cl in range(km.n_clusters):
        if cl not in k12_dist.index:
            rows.append({"cluster": cl, "n_k12long_q99": 0, "verdict": "❌ 根拠不足"})
            log(f"    cluster {cl}: n=0 ❌ 根拠不足")
    pd.DataFrame(rows).sort_values("cluster").to_csv(
        OUT_DIR / "k12long_q99_sample_check.csv", index=False
    )
    log(f"  saved k12long_q99_sample_check.csv")
    return df


def step4_k96_short_fallback(df_clustered):
    """K96 SHORT q99 フォールバック判定 (§4a.5)."""
    log("Step 4: K96 SHORT q99 フォールバック判定 ...")
    labels_train = pd.read_parquet(LABELS_TRAIN).sort_index()
    df_clustered = df_clustered.sort_index()
    # index align
    common_idx = df_clustered.index.intersection(labels_train.index)
    assert len(common_idx) == len(df_clustered), "index mismatch"

    ratio_k96_short = df_clustered["SHORT_MFE_K96"] / df_clustered["SHORT_MAE_K96"].clip(lower=1e-9)
    q99_thr = ratio_k96_short.quantile(0.99)
    mask = ratio_k96_short >= q99_thr
    log(f"  K96 SHORT q99 threshold={q99_thr:.4f} total fire={int(mask.sum())}")

    rows = []
    for cl in sorted(df_clustered["cluster"].unique()):
        cl_mask = mask & (df_clustered["cluster"] == cl)
        n = int(cl_mask.sum())
        if n == 0:
            rows.append({
                "cluster": int(cl), "n_k96short_q99": 0,
                "real_MFE_mean": float("nan"), "real_MAE_mean": float("nan"),
                "mfe_mae_ratio": float("nan"), "fallback_flag": "—",
            })
            continue
        idx_in_labels = df_clustered.index[cl_mask]
        real_mfe = float(labels_train.loc[idx_in_labels, "SHORT_MFE_K96"].mean())
        real_mae = float(labels_train.loc[idx_in_labels, "SHORT_MAE_K96"].mean())
        ratio = real_mfe / real_mae if real_mae > 0 else float("nan")
        if ratio < 1.0:
            flag = "⚠️ no-trade 候補 (MFE/MAE < 1.0)"
        else:
            flag = "✅ trade 可"
        log(f"  cluster {cl}: n={n} MFE/MAE={ratio:.4f} {flag}")
        rows.append({
            "cluster": int(cl), "n_k96short_q99": n,
            "real_MFE_mean": real_mfe, "real_MAE_mean": real_mae,
            "mfe_mae_ratio": ratio, "fallback_flag": flag,
        })
    pd.DataFrame(rows).to_csv(OUT_DIR / "k96short_q99_fallback_check.csv", index=False)
    log(f"  saved k96short_q99_fallback_check.csv")
    return rows


def step5_apply_test(scaler, km):
    """test 2025 への apply (transform/predict のみ)."""
    log("Step 5: test 2025 への apply ...")
    if TEST_PRED_REFIT.exists():
        log(f"  using refit test predictions: {TEST_PRED_REFIT.name}")
        df_test = pd.read_parquet(TEST_PRED_REFIT).sort_index()
    else:
        log(f"  using Phase 1 test predictions: {TEST_PRED_P1.name}")
        df_test = pd.read_parquet(TEST_PRED_P1).sort_index()

    X_test = df_test[LABEL_COLS].values
    X_test_scaled = scaler.transform(X_test)
    test_labels = km.predict(X_test_scaled)
    df_test["cluster"] = test_labels
    df_test.to_parquet(OUT_DIR / "predictions_test2025_clustered.parquet")
    sizes = pd.Series(test_labels).value_counts().sort_index().to_dict()
    log(f"  saved predictions_test2025_clustered.parquet")
    log(f"  test cluster sizes: {sizes}")


def main():
    t0 = datetime.now()
    log(f"Phase 4-a clustering START at {t0.isoformat()}")
    log(f"input: {TRAIN_PRED_PATH}")
    log(f"output: {OUT_DIR}")

    df_train = pd.read_parquet(TRAIN_PRED_PATH).sort_index()
    log(f"  train: rows={len(df_train)} cols={len(df_train.columns)}")
    assert len(df_train) == 394753, f"expected 394753 rows, got {len(df_train)}"

    X = df_train[LABEL_COLS].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    log(f"  X_scaled shape: {X_scaled.shape}")

    # Step 1: silhouette 評価
    df_sil = step1_silhouette(X_scaled)
    chosen_k = choose_k(df_sil)
    log(f"=> 採用 k = {chosen_k} (silhouette {df_sil[df_sil.k==chosen_k]['silhouette'].iloc[0]:.4f})")

    # Step 2: fit
    km = step2_fit(X_scaled, chosen_k)

    # 4a.4: artifact 名に "test" 不在確認 + train 含む
    scaler_path = OUT_DIR / "scaler_train_2021_2024.joblib"
    km_path = OUT_DIR / f"kmeans_k{chosen_k}_train_2021_2024.joblib"
    assert "test" not in scaler_path.name.lower()
    assert "test" not in km_path.name.lower()
    assert "train" in scaler_path.name.lower()
    assert "train" in km_path.name.lower()
    joblib.dump(scaler, scaler_path)
    joblib.dump(km, km_path)
    log(f"  saved {scaler_path.name} / {km_path.name}")

    # Step 3: cluster 分析
    df_clustered = step3_cluster_analysis(df_train, km, X_scaled)

    # Step 4: K96 SHORT q99 フォールバック判定
    fallback_rows = step4_k96_short_fallback(df_clustered)

    # Step 5: test 2025 apply
    step5_apply_test(scaler, km)

    # summary
    summary = {
        "chosen_k": chosen_k,
        "chosen_silhouette": float(df_sil[df_sil.k == chosen_k]["silhouette"].iloc[0]),
        "n_rows_train": int(len(df_train)),
        "scaler_path": str(scaler_path.name),
        "km_path": str(km_path.name),
        "old_leak_k": 4,
        "old_leak_silhouette": 0.212,
        "fallback_check": fallback_rows,
    }
    with open(OUT_DIR / "phase4a_summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)
    log(f"  saved phase4a_summary.json")

    t1 = datetime.now()
    log(f"Phase 4-a clustering END at {t1.isoformat()} (elapsed {(t1-t0).total_seconds()/60:.2f} min)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
