#!/usr/bin/env python3
"""
run_phase4_a.py — ML Phase 4-a: Entry の性質分類 (k-means × 16 予測値)

指示書: bitget-python-sdk-api/cc_ml_design_spec.md §3.3 / §5 Phase 4 step 1
採用 ML モデル: Phase 3-b (predictions_test2025.parquet)

スコープ:
  - test 2025 全 105,120 足の 16 予測値 + 派生特徴量で K-means
  - k=4 / k=6 / k=8 を比較し、シルエットスコアと解釈性で選ぶ
  - 各クラスタの統計 (Entry 発火率・MFE/MAE 比分布・K 窓特性)

入力:
  results/priority_rebuild/ml_phase3_b/predictions_test2025.parquet  (16 予測値 + close + timestamp)
  results/priority_rebuild/ml_phase3_b/entry_thresholds.json           (Phase 3-b 閾値)

出力 (results/priority_rebuild/ml_phase4_a/):
  phase4a_log_<TS>.txt
  features.parquet                      26 次元派生特徴量 (Entry 性質ベクトル)
  cluster_labels_k4.parquet             各足のクラスタ割当 (k=4)
  cluster_labels_k6.parquet             同 (k=6)
  cluster_labels_k8.parquet             同 (k=8)
  cluster_stats.csv                     各 k × cluster の統計
  silhouette_scores.csv                 k=4/6/8 のシルエット
  cluster_pca_viz.png                   PCA 2D 散布図 (クラスタ色分け)
  cluster_radar_kN.png                  各クラスタの 16 予測値レーダー (k 別)
  summary.md

技術要件:
  - 派生特徴量を標準化 (StandardScaler) してから K-means
  - random_state=42
  - k-means n_init=10
  - シルエットスコアはサンプル 5,000 行で算出 (105k 全件は重い)
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase3_b"
OUT_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase4_a"

PREDICTIONS = SRC_DIR / "predictions_test2025.parquet"
THRESHOLDS = SRC_DIR / "entry_thresholds.json"

LABEL_COLS = [
    f"{side}_{kind}_K{k}"
    for k in (12, 24, 48, 96)
    for side in ("LONG", "SHORT")
    for kind in ("MFE", "MAE")
]
K_WINDOWS = (12, 24, 48, 96)
K_CLUSTERS_LIST = (4, 6, 8)
RANDOM_STATE = 42
SILHOUETTE_SAMPLE_N = 5000

TS = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
LOG_PATH = OUT_DIR / f"phase4a_log_{TS}.txt"


def log(msg: str) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{now}] {msg}"
    print(line, flush=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")


def build_features(pred: pd.DataFrame) -> pd.DataFrame:
    """16 予測値 + 派生特徴量 (合計 26 次元) を組み立てる。

    派生:
      - MFE/MAE 比 × 4 K 窓 × 2 方向 = 8 (LONG_ratio_K12 etc)
      - K96 MFE / K12 MFE (長期/短期 伸び率) × 2 方向 = 2
      ※ 16 + 8 + 2 = 26 次元
    """
    feat = pred[LABEL_COLS].copy()
    eps = 1e-9
    for k in K_WINDOWS:
        for side in ("LONG", "SHORT"):
            mfe = pred[f"{side}_MFE_K{k}"]
            mae = pred[f"{side}_MAE_K{k}"]
            feat[f"{side}_ratio_K{k}"] = mfe / (mae + eps)
    for side in ("LONG", "SHORT"):
        feat[f"{side}_long_vs_short"] = pred[f"{side}_MFE_K96"] / (pred[f"{side}_MFE_K12"] + eps)
    return feat


def stats_per_cluster(
    feat_orig: pd.DataFrame,
    clusters: np.ndarray,
    k: int,
    thresholds: dict,
) -> pd.DataFrame:
    """各クラスタの統計を計算。

    返り値カラム:
      cluster, n, frac
      mean_LONG_ratio_K{12,24,48,96}, mean_SHORT_ratio_K{12,24,48,96}
      fire_K12_LONG_q95, fire_K12_SHORT_q95, ... (全 K × 方向 × q95)
    """
    rows = []
    n_total = len(clusters)
    for c in range(k):
        mask = clusters == c
        n = int(mask.sum())
        row = {"k": k, "cluster": c, "n": n, "frac": n / n_total}
        for kk in K_WINDOWS:
            for side in ("LONG", "SHORT"):
                ratio_col = f"{side}_ratio_K{kk}"
                row[f"mean_{ratio_col}"] = float(feat_orig.loc[mask, ratio_col].mean())
                # Entry 発火率 (Phase 3-b q95 閾値で)
                thr = thresholds[f"K{kk}"][side]["q95"]
                fire = (feat_orig.loc[mask, ratio_col] >= thr).mean()
                row[f"fire_K{kk}_{side}_q95"] = float(fire)
        rows.append(row)
    return pd.DataFrame(rows)


def plot_pca(
    Xs: np.ndarray,
    clusters_dict: dict[int, np.ndarray],
    out_path: Path,
) -> None:
    """PCA 2D で k=4/6/8 の散布図を 3 並べる。"""
    pca = PCA(n_components=2, random_state=RANDOM_STATE)
    # 重いのでサンプル 10k 行で
    rng = np.random.default_rng(RANDOM_STATE)
    if len(Xs) > 10000:
        idx = rng.choice(len(Xs), 10000, replace=False)
    else:
        idx = np.arange(len(Xs))
    Xp = pca.fit_transform(Xs[idx])
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    for ax, (k, cl) in zip(axes, sorted(clusters_dict.items())):
        scatter = ax.scatter(Xp[:, 0], Xp[:, 1], c=cl[idx], cmap="tab10", s=4, alpha=0.5)
        ax.set_title(f"k={k}")
        ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)")
        ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)")
    fig.suptitle("Phase 4-a — Entry cluster PCA 2D (sample 10k)", fontsize=13)
    plt.tight_layout()
    plt.savefig(out_path, dpi=110)
    plt.close(fig)


def plot_radar(
    feat_orig: pd.DataFrame,
    clusters: np.ndarray,
    k: int,
    out_path: Path,
) -> None:
    """各クラスタの 16 予測値の z-score をレーダー風に表示。"""
    means = pd.DataFrame(index=range(k), columns=LABEL_COLS, dtype=float)
    overall_mean = feat_orig[LABEL_COLS].mean()
    overall_std = feat_orig[LABEL_COLS].std()
    for c in range(k):
        mask = clusters == c
        means.loc[c] = (feat_orig.loc[mask, LABEL_COLS].mean() - overall_mean) / overall_std
    fig, ax = plt.subplots(figsize=(14, max(6, k * 0.6)))
    for c in range(k):
        ax.plot(range(len(LABEL_COLS)), means.loc[c].values, marker="o", label=f"cluster {c}")
    ax.set_xticks(range(len(LABEL_COLS)))
    ax.set_xticklabels(LABEL_COLS, rotation=60, ha="right", fontsize=8)
    ax.axhline(0, color="gray", linewidth=0.5)
    ax.set_ylabel("z-score (vs overall mean)")
    ax.set_title(f"Phase 4-a — Cluster mean z-score per label (k={k})")
    ax.legend(loc="upper right", fontsize=8)
    plt.tight_layout()
    plt.savefig(out_path, dpi=110)
    plt.close(fig)


def main() -> None:
    t0 = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log("=== Phase 4-a START ===")
    log(f"src: {SRC_DIR}")
    log(f"out: {OUT_DIR}")

    pred = pd.read_parquet(PREDICTIONS)
    log(f"predictions loaded: {pred.shape}")
    with open(THRESHOLDS) as f:
        thresholds = json.load(f)
    log(f"thresholds loaded: K windows={list(thresholds.keys())}")

    feat = build_features(pred)
    log(f"features: {feat.shape} cols={feat.columns.tolist()[:5]}...")
    assert feat.shape[1] == 26, f"expected 26 features, got {feat.shape[1]}"

    # NaN チェック (MFE/MAE 比は分母 0 の可能性) → 大量にあれば log
    nan_cnt = feat.isna().sum().sum()
    if nan_cnt > 0:
        log(f"  ⚠️ NaN count in features: {nan_cnt} (rows with any NaN: {feat.isna().any(axis=1).sum()})")
    feat = feat.fillna(0.0)  # MFE/MAE 比の inf は内部で別途処理されてるはず
    feat = feat.replace([np.inf, -np.inf], 0.0)

    # 標準化
    scaler = StandardScaler()
    Xs = scaler.fit_transform(feat.values)
    log(f"scaled: mean~{Xs.mean():.3e} std~{Xs.std():.3f}")

    feat_out = feat.copy()
    feat_out["close"] = pred["close"].values
    feat_out.to_parquet(OUT_DIR / "features.parquet")
    log("saved features.parquet")

    # K-means × k=4/6/8
    clusters_dict: dict[int, np.ndarray] = {}
    silhouette_records = []
    for k in K_CLUSTERS_LIST:
        log(f"--- k-means k={k} ---")
        t_k = time.time()
        km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
        clusters = km.fit_predict(Xs)
        clusters_dict[k] = clusters
        log(f"  inertia={km.inertia_:.0f} elapsed={time.time()-t_k:.1f}s")

        # シルエットスコア (サンプル)
        rng = np.random.default_rng(RANDOM_STATE)
        idx = rng.choice(len(Xs), min(SILHOUETTE_SAMPLE_N, len(Xs)), replace=False)
        sil = silhouette_score(Xs[idx], clusters[idx])
        silhouette_records.append({"k": k, "silhouette": float(sil), "inertia": float(km.inertia_)})
        log(f"  silhouette (n={SILHOUETTE_SAMPLE_N})={sil:.4f}")

        # 保存
        df_cl = pd.DataFrame({"cluster": clusters}, index=pred.index)
        df_cl.to_parquet(OUT_DIR / f"cluster_labels_k{k}.parquet")
        log(f"  saved cluster_labels_k{k}.parquet")

    pd.DataFrame(silhouette_records).to_csv(OUT_DIR / "silhouette_scores.csv", index=False)
    log("saved silhouette_scores.csv")

    # 各クラスタの統計
    all_stats = []
    for k, clusters in clusters_dict.items():
        s = stats_per_cluster(feat, clusters, k, thresholds)
        all_stats.append(s)
    df_stats = pd.concat(all_stats, ignore_index=True)
    df_stats.to_csv(OUT_DIR / "cluster_stats.csv", index=False)
    log("saved cluster_stats.csv")

    # PCA 2D 可視化
    plot_pca(Xs, clusters_dict, OUT_DIR / "cluster_pca_viz.png")
    log("saved cluster_pca_viz.png")

    # 各 k のレーダーチャート
    for k, clusters in clusters_dict.items():
        plot_radar(feat, clusters, k, OUT_DIR / f"cluster_radar_k{k}.png")
        log(f"saved cluster_radar_k{k}.png")

    elapsed = time.time() - t0
    log(f"=== Phase 4-a END (elapsed={elapsed/60:.2f} min) ===")

    write_summary(elapsed)


def write_summary(elapsed: float) -> None:
    sil = pd.read_csv(OUT_DIR / "silhouette_scores.csv")
    st = pd.read_csv(OUT_DIR / "cluster_stats.csv")

    md = []
    md.append("# Phase 4-a — Entry 性質分類 (k-means × 16 予測値 + 派生)\n\n")
    md.append(f"- 実行 TS: {TS}\n")
    md.append(f"- 所要: {elapsed/60:.2f} 分\n")
    md.append(f"- 採用 ML: Phase 3-b\n")
    md.append(f"- 特徴量次元: 26 (16 予測値 + 8 MFE/MAE比 + 2 long/short比)\n\n")
    md.append("## 再現コマンド\n\n")
    md.append("```\npython3 scripts/priority_rebuild/run_phase4_a.py\n```\n\n")

    md.append("## シルエットスコア (高いほどクラスタ分離良好)\n\n")
    md.append("| k | silhouette | inertia |\n|---|---|---|\n")
    for _, r in sil.iterrows():
        md.append(f"| {int(r['k'])} | {r['silhouette']:.4f} | {r['inertia']:.0f} |\n")
    md.append("\n")

    for k in K_CLUSTERS_LIST:
        sub = st[st.k == k]
        md.append(f"## k={k} クラスタ統計\n\n")
        md.append("| cluster | n | frac | mean LONG_ratio K12/K24/K48/K96 | mean SHORT_ratio K12/K24/K48/K96 |\n")
        md.append("|---|---|---|---|---|\n")
        for _, r in sub.iterrows():
            lr = "/".join(f"{r[f'mean_LONG_ratio_K{kk}']:.2f}" for kk in K_WINDOWS)
            sr = "/".join(f"{r[f'mean_SHORT_ratio_K{kk}']:.2f}" for kk in K_WINDOWS)
            md.append(f"| {int(r['cluster'])} | {int(r['n'])} | {r['frac']*100:.1f}% | {lr} | {sr} |\n")
        md.append("\n### Entry 発火率 (q95 閾値・Phase 3-b)\n\n")
        md.append("| cluster | K12 LONG | K12 SHORT | K24 LONG | K24 SHORT | K48 LONG | K48 SHORT | K96 LONG | K96 SHORT |\n")
        md.append("|---|---|---|---|---|---|---|---|---|\n")
        for _, r in sub.iterrows():
            cells = " | ".join(
                f"{r[f'fire_K{kk}_{side}_q95']*100:.1f}%"
                for kk in K_WINDOWS
                for side in ("LONG", "SHORT")
            )
            md.append(f"| {int(r['cluster'])} | {cells} |\n")
        md.append("\n")

    md.append("## 次フェーズ (Phase 4-b) への引き継ぎ\n\n")
    md.append("- Exit シミュレーションは各クラスタ別に試行する\n")
    md.append("- 採用 k 値はシルエットスコア + 解釈性 (レーダーチャート) で選ぶ → Phase 4-b 着手時に確定\n")
    md.append("- Entry 発火率が極端なクラスタ (例: 全 K×方向 = 0% or > 50%) は別途扱い\n")
    md.append("- bar OHLC: `data/BTCUSDT-5m-2025-*` CSV から 2025 全期間を読み込む\n")
    with open(OUT_DIR / "summary.md", "w") as f:
        f.write("".join(md))


if __name__ == "__main__":
    main()
