"""
工程 [1.5] regime ensemble — k-means 判定器 (Stage C)

設計書: .claude/memory/ml_pipeline_baseline_v1.md v2.8 §6.1.4
CP1 監査 m2 反映: k ∈ {2,3,4,5} elbow + silhouette data-driven
CP1 監査 C1 反映: Gaussian kernel `exp(-d²/2σ²)` で確率化 + isotonic キャリブレーション

機能:
  1. Phase 0 v3.1 parquet 3 種を読み込み 1h grid に reduce
  2. 4 特徴量を生成: log_returns_1h / rolling_volatility(20)_1h / close_vs_sma20_pct__1h / adx14__1h
  3. RobustScaler + Walk-Forward Purged K-Fold 5 fold で k ∈ {2,3,4,5} 探索
  4. 最頻 k 採用 + train 全期間 final fit
  5. post-hoc ラベル付け (= cluster ADX + DI diff で uptrend/downtrend/range マッピング・HMM v15 と同じ手法)
  6. Gaussian kernel `exp(-d²/2σ²)` で確率化 (= σ = cluster median distance)
  7. isotonic キャリブレーション fit (= train_2021_2024 全期間 1 calibrator・target = future 4h log_return 3 クラス)
  8. 3 dataset 全部に対して予測 + 確率出力

入力:
  - results/priority_rebuild/labels_mfe_mae_pct_{train_2021_2024, test_2025, test_2026_q1}.parquet
出力:
  - results/regime_step1/kmeans_classifier_{ds}.parquet
  - results/regime_step1/kmeans_classifier_artifact.json
  - results/regime_step1/kmeans_train_2021_2024.joblib (final k-means)
  - results/regime_step1/kmeans_scaler_train_2021_2024.joblib (final RobustScaler)
  - results/regime_step1/kmeans_isotonic_train_2021_2024.joblib (3 calibrators)

CC 独断・要レビュー項目:
  K1: 最頻 k 決定 = 各 fold の best (silhouette_score 最大) k の最多
       根拠: data-driven 判定の業界 default
  K2: Gaussian kernel σ = train 全期間で各 cluster の median distance
       根拠: scikit-learn の RBF kernel default に類似
  K3: post-hoc ラベル付けは ADX 平均 + DI diff 平均 (= 過去 indicator ベース)
       根拠: HMM v15 と同じ手法・future_4h_logret 使用は leak 同型懸念のため避ける
       影響: cluster 数 > 3 のとき「複数 cluster が同一 regime にマップ」される可能性
  K4: cluster 数 > 3 の場合: 上位 1 つを uptrend / 下位 1 つを downtrend / 残りを range にマッピング
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import RobustScaler

# 共通モジュール
sys.path.insert(0, str(Path(__file__).resolve().parent))
from regime_target_labels import compute_target_for_dataset, get_config as target_config

# ===== 定数 =====
DATASETS = ["train_2021_2024", "test_2025", "test_2026_q1"]
LABEL_TF = "1h"
N_FOLDS = 5  # Walk-Forward Purged K-Fold
PURGE_HOURS = 24
EMBARGO_HOURS = 24
K_GRID = [2, 3, 4, 5]
ROLLING_VOL_WINDOW = 20
RANDOM_STATE = 42

# パス
REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_DIR = REPO_ROOT / "results/priority_rebuild"
OUT_DIR = REPO_ROOT / "results/regime_step1"
OUT_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACT_JSON = OUT_DIR / "kmeans_classifier_artifact.json"
KMEANS_ARTIFACT = OUT_DIR / "kmeans_train_2021_2024.joblib"
SCALER_ARTIFACT = OUT_DIR / "kmeans_scaler_train_2021_2024.joblib"
ISO_ARTIFACT = OUT_DIR / "kmeans_isotonic_train_2021_2024.joblib"


def load_features_1h(ds: str) -> pd.DataFrame:
    """1h grid の 4 特徴量を構築する (= HMM 独立 + 方向情報あり・v3 改訂).

    v3 改訂理由: v2 (volume_ratio / stoch_k / donchian_position / hour_of_day) は HMM 独立だが方向情報を含まず
    → k-means が方向で分離できず post-hoc ラベル付け破綻 (= 両 cluster の DI diff ほぼ同じ).
    v3 では「HMM 独立 + 方向情報」両立する特徴量に差し替え.

    1. obv_slope_10b__1h: OBV (= 出来高ベース累積) 10 bar 傾き — HMM ゼロ + 売買圧の方向
    2. streak_diff (= bullish_streak - bearish_streak): 連続トレンド差分 — HMM ゼロ + 直接方向
    3. zscore_return_20b__1h: 20 bar 標準化リターン — HMM の log_returns 直接値とは別系 (= 標準化版・部分独立) + 符号で方向
    4. donchian_position_20__1h: レンジ内位置 0-1 — HMM 未使用 (= v2 から継続採用・方向音痴の原因ではない)

    cluster ラベル付け用の補助列 (adx14__1h + di_diff__1h) は HMM v15 同手法で利用継続.
    """
    p = INPUT_DIR / f"labels_mfe_mae_pct_{ds}.parquet"
    df = pd.read_parquet(p, columns=[
        "obv_slope_10b__1h",
        "bullish_streak__1h", "bearish_streak__1h",
        "zscore_return_20b__1h",
        "donchian_position_20__1h",
        "adx14__1h", "di_plus__1h", "di_minus__1h",
    ])
    df = df.sort_index()

    # 5m grid forward fill 済 → 1h grid 末尾 = 確定値
    df_1h = df.resample("1h", label="right", closed="right").last()

    # streak_diff = bullish_streak - bearish_streak (= 符号で方向・絶対値で強度)
    streak_diff = (df_1h["bullish_streak__1h"] - df_1h["bearish_streak__1h"])
    streak_diff.name = "streak_diff_1h"

    feats = pd.DataFrame({
        "obv_slope_10b__1h": df_1h["obv_slope_10b__1h"],
        "streak_diff_1h": streak_diff,
        "zscore_return_20b__1h": df_1h["zscore_return_20b__1h"],
        "donchian_position_20__1h": df_1h["donchian_position_20__1h"],
    })
    # ラベル付け用補助列 (= 学習特徴量には含めない・HMM 同手法)
    feats["_adx14__1h_aux"] = df_1h["adx14__1h"]
    feats["_di_diff_aux"] = df_1h["di_plus__1h"] - df_1h["di_minus__1h"]
    return feats


FEATURE_COLS = [
    "obv_slope_10b__1h",
    "streak_diff_1h",
    "zscore_return_20b__1h",
    "donchian_position_20__1h",
]


def walk_forward_purged_indices(n: int, n_folds: int, embargo_bars: int):
    """シンプルな Walk-Forward Purged K-Fold (= time-sequential・各 fold は連続 chunk).

    fold i = test, [0, fold_i_start) は train (= 過去). Walk-forward 形式.
    train 終了点と test 開始点の間に embargo_bars の空白を入れる.
    """
    fold_size = n // n_folds
    for i in range(n_folds):
        test_start = i * fold_size
        test_end = (i + 1) * fold_size if i < n_folds - 1 else n
        train_end = test_start - embargo_bars
        if train_end <= 0:
            # 最初の fold は test 開始前に train データなし → スキップ (= n_folds-1 fold で実質回す)
            continue
        train_idx = np.arange(0, train_end)
        test_idx = np.arange(test_start, test_end)
        yield i, train_idx, test_idx


def explore_k(X_train: np.ndarray) -> dict:
    """k ∈ K_GRID で elbow (inertia) + silhouette を計算.
    戻り値: {"best_k": int, "metrics": {k: {"inertia": float, "silhouette": float}}}.
    """
    metrics: dict[int, dict] = {}
    best_k = K_GRID[0]
    best_silhouette = -np.inf
    for k in K_GRID:
        km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
        labels = km.fit_predict(X_train)
        inertia = float(km.inertia_)
        # silhouette は計算コスト高い → サンプリングして計算 (= 10000 max)
        n_for_sil = min(10000, len(X_train))
        if n_for_sil >= 10:
            idx = np.random.RandomState(RANDOM_STATE).choice(len(X_train), n_for_sil, replace=False)
            sil = float(silhouette_score(X_train[idx], labels[idx]))
        else:
            sil = float("nan")
        metrics[k] = {"inertia": inertia, "silhouette": sil}
        if sil > best_silhouette:
            best_silhouette = sil
            best_k = k
    return {"best_k": best_k, "metrics": metrics}


def post_hoc_label_clusters(
    km: KMeans,
    X_scaled: np.ndarray,
    aux_adx: np.ndarray,
    aux_di_diff: np.ndarray,
) -> dict:
    """cluster ごとに ADX 平均 + DI diff 平均を計算し uptrend/downtrend/range にマッピング.

    K3 + K4: 上位 1 つ (= DI diff 大) を uptrend / 下位 1 つ (= DI diff 小) を downtrend / 残りを range.
    """
    labels = km.predict(X_scaled)
    k = km.n_clusters
    per_cluster: dict[int, dict] = {}
    for c in range(k):
        mask = labels == c
        per_cluster[c] = {
            "count": int(mask.sum()),
            "di_diff_mean": float(np.nanmean(aux_di_diff[mask])) if mask.sum() > 0 else float("nan"),
            "adx_mean": float(np.nanmean(aux_adx[mask])) if mask.sum() > 0 else float("nan"),
        }

    # DI diff で降順ソート → 上位 1 = uptrend / 下位 1 = downtrend / 残り = range
    sorted_by_di = sorted(per_cluster.items(), key=lambda x: x[1]["di_diff_mean"], reverse=True)
    cluster_to_label: dict[int, str] = {}
    if k >= 1:
        cluster_to_label[sorted_by_di[0][0]] = "uptrend"
    if k >= 2:
        cluster_to_label[sorted_by_di[-1][0]] = "downtrend"
    for c, _ in sorted_by_di[1:-1] if k >= 3 else []:
        cluster_to_label[c] = "range"

    # k=2 のとき range 不在 → uptrend/downtrend 二択になる
    return {
        "cluster_to_label": cluster_to_label,
        "per_cluster_stats": per_cluster,
    }


def gaussian_kernel_probs(
    X_scaled: np.ndarray,
    km: KMeans,
    sigma_per_cluster: np.ndarray,
    cluster_to_label: dict,
) -> pd.DataFrame:
    """cluster 中心からの距離を Gaussian kernel で確率化.

    p_k(x) = exp(-d_k² / 2σ_k²)
    各 cluster の確率を post-hoc label (uptrend/downtrend/range) にマージ:
      - 同じラベルの cluster の確率は加算
    最後に sum で正規化.
    """
    # 距離計算: cluster 中心と各サンプル間の Euclidean
    centers = km.cluster_centers_
    diffs = X_scaled[:, None, :] - centers[None, :, :]  # (n, k, d)
    d2 = (diffs ** 2).sum(axis=2)  # (n, k)
    # Gaussian kernel
    sigma2 = (sigma_per_cluster ** 2)[None, :]  # (1, k)
    raw_p = np.exp(-d2 / (2.0 * sigma2 + 1e-12))  # (n, k)
    # 正規化 (= 各サンプルで sum=1)
    p_sum = raw_p.sum(axis=1, keepdims=True)
    p_normalized = raw_p / np.where(p_sum > 0, p_sum, 1.0)

    # post-hoc label に集約
    label_probs = {"uptrend": np.zeros(len(X_scaled)), "downtrend": np.zeros(len(X_scaled)), "range": np.zeros(len(X_scaled))}
    for c, lbl in cluster_to_label.items():
        if lbl in label_probs:
            label_probs[lbl] += p_normalized[:, c]

    df = pd.DataFrame(label_probs)
    # 念のため正規化 (= label_probs の合計が 1 になることを保証)
    s = df.sum(axis=1)
    df = df.div(s.where(s > 0, 1.0), axis=0)
    return df


def fit_isotonic_calibrators(
    raw_probs: pd.DataFrame,
    target_label: pd.Series,
    valid_mask: pd.Series,
) -> dict[str, IsotonicRegression]:
    """各カテゴリで isotonic regression を fit (= raw_prob → P(target == category))."""
    cals: dict[str, IsotonicRegression] = {}
    for cat in ["uptrend", "downtrend", "range"]:
        m = valid_mask & raw_probs[cat].notna() & target_label.notna()
        x = raw_probs.loc[m, cat].values
        y = (target_label.loc[m] == cat).astype(float).values
        if len(x) < 100:
            print(f"  WARN: isotonic fit skipped for {cat} (n={len(x)} < 100)")
            cals[cat] = None
            continue
        iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
        iso.fit(x, y)
        cals[cat] = iso
    return cals


def apply_isotonic_calibrators(
    raw_probs: pd.DataFrame,
    cals: dict,
) -> pd.DataFrame:
    cal_probs: dict[str, pd.Series] = {}
    for cat in ["uptrend", "downtrend", "range"]:
        if cals.get(cat) is None:
            cal_probs[cat] = raw_probs[cat].copy()
        else:
            cal_probs[cat] = pd.Series(
                cals[cat].predict(raw_probs[cat].values),
                index=raw_probs.index,
            )
    df = pd.DataFrame(cal_probs)
    s = df.sum(axis=1)
    df = df.div(s.where(s > 0, 1.0 / 3.0), axis=0)
    return df


def main() -> int:
    print(f"[input dir] {INPUT_DIR}")
    print(f"[output dir] {OUT_DIR}")

    # ========== train データ準備 ==========
    print("\n[1/6] loading train data ...")
    feats_train = load_features_1h("train_2021_2024")
    target_train_df = compute_target_for_dataset("train_2021_2024")
    print(f"  feats shape: {feats_train.shape}")
    print(f"  target shape: {target_train_df.shape}")

    # NaN drop (= feature 側)
    train_full = feats_train.copy()
    train_full["_target"] = target_train_df["target_3class"].reindex(train_full.index)

    # 学習用 mask: 4 特徴量が全部非 NaN
    feat_mask = train_full[FEATURE_COLS].notna().all(axis=1)
    train_valid = train_full[feat_mask]
    print(f"  after feat NaN drop: {len(train_valid)}")

    X_train_raw = train_valid[FEATURE_COLS].values
    aux_adx_train = train_valid["_adx14__1h_aux"].values
    aux_di_train = train_valid["_di_diff_aux"].values

    # ========== Walk-Forward Purged K-Fold で k 探索 ==========
    print("\n[2/6] Walk-Forward Purged K-Fold k exploration ...")
    fold_best_ks: list[int] = []
    fold_metrics: list[dict] = []
    for fold_i, train_idx, test_idx in walk_forward_purged_indices(len(X_train_raw), N_FOLDS, EMBARGO_HOURS):
        sc = RobustScaler()
        X_fold_train = sc.fit_transform(X_train_raw[train_idx])
        res = explore_k(X_fold_train)
        fold_best_ks.append(res["best_k"])
        fold_metrics.append({"fold": fold_i, "best_k": res["best_k"], "metrics": res["metrics"]})
        print(f"  fold {fold_i}: best_k={res['best_k']}  metrics={ {k: round(v['silhouette'], 4) for k, v in res['metrics'].items()} }")

    counter = Counter(fold_best_ks)
    # 同票時の優先順位: k=3 (= 設計書 §6.1.4 業界 default + range cluster 必須) → 小さい k
    # 単独最頻なら最頻採用
    top_freq = max(counter.values())
    top_candidates = [k for k, v in counter.items() if v == top_freq]
    if 3 in top_candidates:
        final_k = 3
    else:
        final_k = min(top_candidates)
    print(f"  >>> chosen k: {final_k}  (fold votes: {dict(counter)}, tied_candidates={top_candidates})")

    # ========== train 全期間で final fit ==========
    print(f"\n[3/6] fitting final k-means with k={final_k} on full train ...")
    final_scaler = RobustScaler()
    X_train_scaled = final_scaler.fit_transform(X_train_raw)
    final_km = KMeans(n_clusters=final_k, random_state=RANDOM_STATE, n_init=10)
    final_km.fit(X_train_scaled)

    # ========== post-hoc ラベル付け ==========
    print("\n[4/6] post-hoc cluster labeling ...")
    label_info = post_hoc_label_clusters(final_km, X_train_scaled, aux_adx_train, aux_di_train)
    print(f"  cluster_to_label: {label_info['cluster_to_label']}")
    for c, st in label_info["per_cluster_stats"].items():
        print(f"  cluster {c}: count={st['count']} di_diff={st['di_diff_mean']:.3f} adx={st['adx_mean']:.2f}")

    # Gaussian kernel σ 算出: 各 cluster の median distance to its center
    train_labels = final_km.predict(X_train_scaled)
    sigma_per_cluster = np.zeros(final_k)
    for c in range(final_k):
        mask = train_labels == c
        if mask.sum() > 0:
            dists = np.linalg.norm(X_train_scaled[mask] - final_km.cluster_centers_[c], axis=1)
            sigma_per_cluster[c] = float(np.median(dists))
        else:
            sigma_per_cluster[c] = 1.0
    print(f"  sigma_per_cluster: {sigma_per_cluster.tolist()}")

    # ========== raw 確率 (train) → isotonic キャリブレーション fit ==========
    print("\n[5/6] fitting isotonic calibrators (target = future 4h log_return 3-class) ...")
    raw_probs_train = gaussian_kernel_probs(X_train_scaled, final_km, sigma_per_cluster, label_info["cluster_to_label"])
    raw_probs_train.index = train_valid.index

    # target を train_valid index に整合
    target_train_aligned = train_full["_target"].reindex(train_valid.index)
    isotonic_cals = fit_isotonic_calibrators(
        raw_probs_train,
        target_train_aligned,
        pd.Series(True, index=train_valid.index),
    )
    print(f"  isotonic calibrators: {[k for k, v in isotonic_cals.items() if v is not None]}")

    # ========== 3 dataset 全部に適用 ==========
    print("\n[6/6] applying to all 3 datasets ...")
    summaries: dict = {}

    for ds in DATASETS:
        print(f"\n  ----- {ds} -----")
        feats = load_features_1h(ds)
        feat_mask_ds = feats[FEATURE_COLS].notna().all(axis=1)
        feats_valid = feats[feat_mask_ds]
        X = feats_valid[FEATURE_COLS].values
        X_scaled = final_scaler.transform(X)

        cluster_labels = final_km.predict(X_scaled)
        raw_probs = gaussian_kernel_probs(X_scaled, final_km, sigma_per_cluster, label_info["cluster_to_label"])
        raw_probs.index = feats_valid.index

        cal_probs = apply_isotonic_calibrators(raw_probs, isotonic_cals)
        cal_probs.index = feats_valid.index

        # 最終 label: cal_probs の最高
        final_label = cal_probs.idxmax(axis=1)
        # 全 1h index に reindex (= NaN サンプルは "unknown")
        full_index = feats.index
        out = pd.DataFrame(index=full_index)
        out["regime_label"] = final_label.reindex(full_index).fillna("unknown")
        out["regime_prob_up"] = cal_probs["uptrend"].reindex(full_index)
        out["regime_prob_down"] = cal_probs["downtrend"].reindex(full_index)
        out["regime_prob_range"] = cal_probs["range"].reindex(full_index)
        out["regime_confidence"] = (cal_probs.max(axis=1) - cal_probs.apply(lambda r: sorted(r.values)[-2] if r.notna().all() else np.nan, axis=1)).reindex(full_index)
        out["_cluster_id"] = pd.Series(cluster_labels, index=feats_valid.index).reindex(full_index)
        out["_raw_prob_up"] = raw_probs["uptrend"].reindex(full_index)
        out["_raw_prob_down"] = raw_probs["downtrend"].reindex(full_index)
        out["_raw_prob_range"] = raw_probs["range"].reindex(full_index)

        out_path = OUT_DIR / f"kmeans_classifier_{ds}.parquet"
        out.to_parquet(out_path)

        dist = out["regime_label"].value_counts(dropna=False).to_dict()
        print(f"    rows={len(out)}, label dist: {dist}")
        summaries[ds] = {
            "rows": int(len(out)),
            "label_distribution": {str(k): int(v) for k, v in dist.items()},
        }

    # ========== artifact 保存 ==========
    print("\n[saving artifacts] ...")
    joblib.dump(final_km, KMEANS_ARTIFACT)
    joblib.dump(final_scaler, SCALER_ARTIFACT)
    joblib.dump(isotonic_cals, ISO_ARTIFACT)

    artifact = {
        "script": str(Path(__file__).relative_to(REPO_ROOT)),
        "design_doc": ".claude/memory/ml_pipeline_baseline_v1.md (v2.8 §6.1.4)",
        "cp1_audit": ".claude/audits/2026-05-27_step15_regime_ensemble_design_cp1_audit_report.md",
        "k_grid": K_GRID,
        "fold_best_ks": fold_best_ks,
        "chosen_k": final_k,
        "fold_metrics": fold_metrics,
        "feature_cols": FEATURE_COLS,
        "rolling_vol_window": ROLLING_VOL_WINDOW,
        "n_folds": N_FOLDS,
        "purge_hours": PURGE_HOURS,
        "embargo_hours": EMBARGO_HOURS,
        "random_state": RANDOM_STATE,
        "sigma_per_cluster": sigma_per_cluster.tolist(),
        "cluster_to_label": {str(k): v for k, v in label_info["cluster_to_label"].items()},
        "per_cluster_stats": {str(k): v for k, v in label_info["per_cluster_stats"].items()},
        "target_config": target_config(),
        "summaries": summaries,
        "isotonic_target": "future 4h log_return 3-class (T1, T2)",
        "cc_independent_judgements": [
            "K1: 最頻 k 決定 = silhouette ベース fold mode",
            "K2: Gaussian kernel σ = train 全期間 cluster median distance",
            "K3: post-hoc ラベル = ADX + DI diff (HMM 同手法)",
            "K4: k > 3 のとき DI diff 上位 = uptrend / 下位 = downtrend / 残り = range",
        ],
    }
    with ARTIFACT_JSON.open("w") as f:
        json.dump(artifact, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n[DONE] artifact saved: {ARTIFACT_JSON}")
    print(f"  kmeans:   {KMEANS_ARTIFACT}")
    print(f"  scaler:   {SCALER_ARTIFACT}")
    print(f"  isotonic: {ISO_ARTIFACT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
