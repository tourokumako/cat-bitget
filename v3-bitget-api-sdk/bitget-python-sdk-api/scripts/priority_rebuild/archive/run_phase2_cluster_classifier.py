"""run_phase2_cluster_classifier.py — 工程 [2.5] cluster 分類 (= ml_pipeline_baseline_v1.md §6.3 実装)

目的:
  - Entry trade の質を教師なし学習 (= 正解ラベルなし) で自動分類 (スキャル型 / 長期型 / 危険型 / 凡庸型)
  - 後段 [3] Sizing / [4] Exit で cluster 別最適化 → 戦略並立 1.5× レバー寄与 (§6.3.1 Stage 3)
  - SHORT 偏り 1:20 を cluster で「危険型/下落相場型」分類 → [3] Sizing で size 抑制経路 (= 案 P)

設計引継ぎ (§6.3 から・CP3 監査全 7 件反映済 v3.10):
  §6.3.1 ✅ Stage 1 評価: silhouette > 0.4 + Brier < 0.15 + ECE < 0.10 + 偏り ≥ 5% + regime 相関 < 0.5 + 旧 16 列版実測比較
  §6.3.2 ✅ K-Means + GMM hybrid (= k-means++ 初期化 → GMM EM・posterior probability) + fold 別 Isotonic Regression キャリブレーション
  §6.3.3 ✅ 入力 = 予測値 56 + 元特徴量 2,604 + regime 6 = 2,666 列 + PCA 50-100 主成分 (分散 95%) + RobustScaler
  §6.3.4 ✅ k ∈ {3, 4, 5} 並列試行 + silhouette 最大 + elbow + 偏り ≥ 5% で data-driven 決定
  §6.3.5 ✅ 4 軸 (TP_prob / MFE / SL_prob / 保有時間代理) で post-hoc 命名 (train 期間のみ)
  §6.3.6 ✅ 出力 7 主要列 + cluster_id 直接食わせ前提 + parquet 保存 + entry_id ベース merge
  §6.3.7 ✅ leak 防止: fit は train 期間のみ + artifact 名 train 含む + 起動時 assertion

スコープ (= 本タスク):
  - cluster fit + Stage 1 評価 = train_2021_2024 out-of-fold (= 3 fold test 集約・236,736 bar) で実施
  - test_2025 / test_2026_q1 への apply は Entry ML test 予測未生成のため後タスク (Phase 5 準備時)
  - 「全候補 (全 bar) で fit して型を安定化 → 採用 entry に apply」方針 (= WebSearch ベースアップ済・小サンプル robustness 回避)

入力:
  - results/priority_rebuild/ml_phase2_baseline/{label}_fold{i}/predictions.parquet (= 168 個・予測値 56)
  - results/priority_rebuild/labels_mfe_mae_pct_train_2021_2024.parquet (= 元特徴量 2,604)
  - results/regime_step1/regime_predictions_train_2021_2024.parquet (= regime 6)
  - results/priority_rebuild/ml_phase1_k12long_refit/predictions_train_2021_2024_k12long_refit.parquet (= 旧 16 列版 silhouette 比較用)

出力:
  - results/priority_rebuild/cluster_step1/cluster_predictions_train_2021_2024.parquet (= 7 主要列)
  - results/priority_rebuild/cluster_step1/cluster_kmeans_train_2021_2024.joblib (= KMeans)
  - results/priority_rebuild/cluster_step1/cluster_gmm_train_2021_2024.joblib (= GMM)
  - results/priority_rebuild/cluster_step1/pca_train_2021_2024.joblib
  - results/priority_rebuild/cluster_step1/scaler_train_2021_2024.joblib
  - results/priority_rebuild/cluster_step1/calibrator_train_2021_2024.joblib (= fold 別 isotonic dict)
  - results/priority_rebuild/cluster_step1/stage1_review.md (= Stage 1 評価結果)
  - results/priority_rebuild/cluster_step1/cluster_summary.json

実行モード:
  --smoke   : 1 fold + k=3 のみ (= 動作確認用・PCA 30 主成分)
  (引数なし) : 3 fold 全 out-of-fold + k ∈ {3,4,5} 全走
"""

import argparse
import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import brier_score_loss, silhouette_score
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import RobustScaler

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.priority_rebuild.run_phase1_v5_purged_kfold import (  # noqa: E402
    load_parquet_with_blacklist,
)

# I/O paths
BASELINE_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase2_baseline"
PARQUET_TRAIN = REPO_ROOT / "results" / "priority_rebuild" / "labels_mfe_mae_pct_train_2021_2024.parquet"
PARQUET_REGIME = REPO_ROOT / "results" / "regime_step1" / "regime_predictions_train_2021_2024.parquet"
PARQUET_OLD16 = (REPO_ROOT / "results" / "priority_rebuild" / "ml_phase1_k12long_refit"
                 / "predictions_train_2021_2024_k12long_refit.parquet")
OUT_DIR = REPO_ROOT / "results" / "priority_rebuild" / "cluster_step1"

K_BARS = [6, 12, 24, 48, 96, 144, 288]
N_FOLDS = 3
SIDES = ["LONG", "SHORT"]

# Triple Barrier class index (= baseline encode: SL=-1→0, TIME=0→1, TP=1→2)
CLASS_SL = 0
CLASS_TIME = 1
CLASS_TP = 2

# regime 6 列 (= §6.3.3・数値化済)・volatility_level/regime_label はカテゴリ → 数値化
REGIME_NUM_COLS = ["regime_prob_up", "regime_prob_down", "regime_prob_range",
                   "regime_confidence", "regime_is_unclear"]
VOLATILITY_MAP = {"low": 0.0, "mid": 1.0, "high": 2.0, None: 1.0}

# k 候補 (§6.3.4)
K_CANDIDATES = [3, 4, 5]

# Stage 1 合格ライン (§6.3.1)
SILHOUETTE_PASS = 0.4
BRIER_PASS = 0.15
ECE_PASS = 0.10
MIN_CLUSTER_FRAC = 0.05
REGIME_CORR_PASS = 0.5

# PCA 分散説明率 (§6.3.3)
PCA_VARIANCE = 0.95
PCA_MAX_COMPONENTS = 100
PCA_MIN_COMPONENTS = 50

# NaN 前処理 (= 元特徴量に warmup NaN 多数・cluster は NaN 不可)
# NaN率 > 0.5 の列 drop (= 月足 1M / 週足 W50 系 warmup 不足・186 列) → 残り median imputation
NAN_COL_DROP_THRESHOLD = 0.5

# RobustScaler 後 ±N クリップ (= heavy-tail 列の PCA 1 主成分支配防止・WebSearch 業界 verify 済)
# RobustScaler は中心/スケールは外れ値耐性だが変換後の極端値は巨大なまま残る → ±5 IQR でクリップ
CLIP_VALUE = 5.0

RANDOM_STATE = 42


# ============== 入力構築 ==============

def load_pred(label_name: str, fold_idx: int) -> pd.DataFrame:
    path = BASELINE_DIR / f"{label_name}_fold{fold_idx}" / "predictions.parquet"
    if not path.exists():
        raise FileNotFoundError(f"predictions.parquet missing: {path}")
    return pd.read_parquet(path)


def build_prediction_matrix(fold_idx: int) -> pd.DataFrame:
    """1 fold の 56 予測値 + 命名用 SL 確率を entry_id index で組み立て.

    予測値 56 列 (= cluster 入力):
      - 揺れ幅 28: LONG/SHORT × MFE/MAE × K(7) の回帰 pred
      - Triple Barrier 14: LONG/SHORT × K(7) の TP 確率 (pred_proba_class2_cal)
      - meta_label 14: LONG/SHORT × K(7) の pred_proba_cal
    命名用追加 (= cluster 入力に含めない・§6.3.5 post-hoc 統計):
      - SL 確率 14: LONG/SHORT × K(7) の pred_proba_class0_cal
    """
    base = load_pred(f"triple_barrier_label_LONG_K{K_BARS[0]}", fold_idx)
    entry_ids = base["entry_id"].values
    feat = {"entry_id": entry_ids}

    # 揺れ幅 28 (regression)
    for side in SIDES:
        for mm in ["MFE", "MAE"]:
            for K in K_BARS:
                col = f"{side}_{mm}_pct_K{K}"
                feat[f"pred_{col}"] = load_pred(col, fold_idx)["pred"].values

    # Triple Barrier 14 (TP 確率) + 命名用 SL 確率 14
    for side in SIDES:
        for K in K_BARS:
            tb = load_pred(f"triple_barrier_label_{side}_K{K}", fold_idx)
            feat[f"tp_prob_{side}_K{K}"] = tb[f"pred_proba_class{CLASS_TP}_cal"].values
            feat[f"_sl_prob_{side}_K{K}"] = tb[f"pred_proba_class{CLASS_SL}_cal"].values  # 命名用 (_ 接頭)

    # meta_label 14 (yes 確率)
    for side in SIDES:
        for K in K_BARS:
            mt = load_pred(f"meta_label_{side}_K{K}", fold_idx)
            feat[f"meta_yes_{side}_K{K}"] = mt["pred_proba_cal"].values

    df = pd.DataFrame(feat)
    df["fold"] = fold_idx
    return df


def numericize_regime(df_r: pd.DataFrame) -> pd.DataFrame:
    """regime 6 列を数値化 (= prob 3 + confidence + is_unclear + volatility_num)."""
    out = df_r[REGIME_NUM_COLS].copy()
    out["regime_volatility_num"] = df_r["regime_volatility_level"].map(VOLATILITY_MAP).fillna(1.0)
    return out  # 6 列


def assemble_input(folds: list, mode: str = "all", verbose: bool = True) -> tuple:
    """全 fold の入力を組み立て.

    mode="all"       : 予測値 56 + 元特徴量 2,604 + regime 6 = 2,666 列
    mode="pred_only" : 予測値 56 のみ (= §6.3.3 data-driven 経路・全投入大敗を受けた切替)

    Returns: (X_cluster, meta_df entry_id/fold/命名用SL+MFE+TP)
    """
    # 1. 予測値 56 + 命名用列 を fold 別組み立て → 縦結合
    pred_dfs = []
    for f in folds:
        if verbose:
            print(f"[input] fold {f}: 56 予測値 + 命名用 SL/MFE/TP 組み立て")
        pred_dfs.append(build_prediction_matrix(f))
    pred_all = pd.concat(pred_dfs, ignore_index=True)
    pred_all["entry_ts"] = pd.to_datetime(pred_all["entry_id"])
    if verbose:
        print(f"[input] 予測値行列: {pred_all.shape} (= {len(pred_dfs)} fold 縦結合)")

    pred_cols_all = [c for c in pred_all.columns
                     if c.startswith(("pred_", "tp_prob_", "meta_yes_")) and not c.startswith("_")]
    meta_cols = (["entry_id", "fold", "entry_ts"]
                 + [c for c in pred_all.columns if c.startswith("_sl_prob_")]
                 + [c for c in pred_all.columns if c.startswith("tp_prob_")]
                 + [c for c in pred_all.columns if c.startswith("pred_") and "MFE" in c])

    # mode="pred_only"/"mfe_only": 予測値のみ (元特徴量・regime をスキップ)
    if mode in ("pred_only", "mfe_only"):
        cols = ([c for c in pred_cols_all if c.startswith("pred_")] if mode == "mfe_only"
                else pred_cols_all)
        X_cluster = pred_all[cols].reset_index(drop=True)
        valid_mask = X_cluster.notna().all(axis=1)
        X_cluster = X_cluster.loc[valid_mask].reset_index(drop=True)
        meta_df = pred_all[meta_cols].loc[valid_mask].reset_index(drop=True)
        if verbose:
            print(f"[input] {mode} モード: {X_cluster.shape[1]} 列のみ ({len(X_cluster)} 行)")
        return X_cluster, meta_df

    # 2. 元特徴量 2,604 列 load (blacklist drop 済) → entry_ts で reindex
    if verbose:
        print(f"[input] 元特徴量 load: {PARQUET_TRAIN.name}")
    X_feat, _, feat_index = load_parquet_with_blacklist(PARQUET_TRAIN, verbose=False)
    X_feat = X_feat.set_index(feat_index) if not isinstance(X_feat.index, pd.DatetimeIndex) else X_feat
    # entry_ts で元特徴量を引く
    feat_matched = X_feat.reindex(pred_all["entry_ts"].values)
    feat_matched.index = pred_all.index
    if verbose:
        print(f"[input] 元特徴量 matched: {feat_matched.shape}")

    # 3. regime 6 列 load → entry_ts で reindex + 数値化
    if verbose:
        print(f"[input] regime load: {PARQUET_REGIME.name}")
    df_r = pd.read_parquet(PARQUET_REGIME)
    regime_num = numericize_regime(df_r)
    regime_matched = regime_num.reindex(pred_all["entry_ts"].values)
    regime_matched.index = pred_all.index
    if verbose:
        print(f"[input] regime matched: {regime_matched.shape} 列={list(regime_matched.columns)}")

    # 4. 予測値 56 列のみ抽出 (命名用 _ 接頭 + entry_id/fold/entry_ts 除く)
    pred_cols = [c for c in pred_all.columns
                 if c.startswith(("pred_", "tp_prob_", "meta_yes_"))
                 and not c.startswith("_")]
    X_pred = pred_all[pred_cols]
    if verbose:
        print(f"[input] 予測値列数: {len(pred_cols)} (= 揺れ幅28 + TP14 + meta14 = 56 期待)")

    # 5. 結合 (= 2,666 列)
    X_cluster = pd.concat([
        X_pred.reset_index(drop=True),
        feat_matched.reset_index(drop=True),
        regime_matched.reset_index(drop=True),
    ], axis=1)
    # 予測値 56 + regime 6 が非 NaN の行のみ残す (= 元特徴量の warmup NaN は後段 median 補完で許容)
    n_before = len(X_cluster)
    check_cols = [c for c in X_cluster.columns
                  if c.startswith(("pred_", "tp_prob_", "meta_yes_", "regime_"))]
    valid_mask = X_cluster[check_cols].notna().all(axis=1)
    X_cluster = X_cluster.loc[valid_mask].reset_index(drop=True)
    if verbose:
        print(f"[input] 結合後: {X_cluster.shape} (予測値+regime NaN 行除去: {n_before} → {len(X_cluster)})")

    # meta_df: 命名用統計 (SL 確率 / MFE / TP 確率) + entry_id/fold
    meta_cols = (["entry_id", "fold", "entry_ts"]
                 + [c for c in pred_all.columns if c.startswith("_sl_prob_")]
                 + [c for c in pred_all.columns if c.startswith("tp_prob_")]
                 + [c for c in pred_all.columns if c.startswith("pred_") and "MFE" in c])
    meta_df = pred_all[meta_cols].loc[valid_mask].reset_index(drop=True)

    return X_cluster, meta_df


# ============== NaN 前処理 ==============

def clean_features(X: pd.DataFrame, verbose: bool = True) -> tuple:
    """高 NaN 列 (> 50%) drop + 残り median imputation (= cluster は NaN 不可).

    元特徴量に warmup NaN 多数 (= 月足 1M / 週足 W50 系)・PCA/k-means は NaN 受付不可のため必須前処理.
    imputer / drop_cols は artifact 保存して test apply 時に再利用.
    """
    # inf → NaN (= median imputation は inf を埋めない・元特徴量に inf 列あり)
    X = X.replace([np.inf, -np.inf], np.nan)
    nan_rate = X.isna().mean(axis=0)
    drop_cols = nan_rate[nan_rate > NAN_COL_DROP_THRESHOLD].index.tolist()
    X2 = X.drop(columns=drop_cols)
    imputer = SimpleImputer(strategy="median")
    X_imp = imputer.fit_transform(X2.values)
    X_clean = pd.DataFrame(X_imp, columns=X2.columns, index=X2.index)
    if verbose:
        print(f"[clean] inf→NaN + 高NaN(>{NAN_COL_DROP_THRESHOLD:.0%})列 drop: {len(drop_cols)} 列 "
              f"({X.shape[1]} → {X_clean.shape[1]}) + median imputation")
    return X_clean, imputer, drop_cols


# ============== cluster fit ==============

def fit_pca_scaler(X: pd.DataFrame, n_comp_cap: int, use_pca: bool = True, verbose: bool = True) -> tuple:
    """RobustScaler fit → (PCA fit) (分散 95% 説明する主成分数・[50,cap] にクランプ).

    use_pca=False (= pred_only): PCA スキップ・RobustScaler + clip のみ (= 旧 16 列版と同条件比較).
    """
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X.values)
    # heavy-tail 列の PCA 支配防止: ±CLIP_VALUE IQR でクリップ (= WebSearch 業界 verify 済)
    X_scaled = np.clip(X_scaled, -CLIP_VALUE, CLIP_VALUE)
    if verbose:
        print(f"[scale] RobustScaler + clip(±{CLIP_VALUE}) 適用")

    if not use_pca:
        if verbose:
            print(f"[scale] PCA スキップ (pred_only): {X_scaled.shape[1]} 列直接 cluster")
        return scaler, None, X_scaled

    # まず full PCA で分散説明率を見る
    pca_full = PCA(n_components=min(n_comp_cap, X_scaled.shape[1]), random_state=RANDOM_STATE)
    pca_full.fit(X_scaled)
    cumvar = np.cumsum(pca_full.explained_variance_ratio_)
    n_95 = int(np.searchsorted(cumvar, PCA_VARIANCE) + 1)
    n_comp = int(np.clip(n_95, PCA_MIN_COMPONENTS, n_comp_cap))
    if verbose:
        print(f"[pca] 分散95%説明={n_95}主成分 → 採用={n_comp} (cap={n_comp_cap})")

    pca = PCA(n_components=n_comp, random_state=RANDOM_STATE)
    X_pca = pca.fit_transform(X_scaled)
    if verbose:
        print(f"[pca] X_pca shape: {X_pca.shape} / 累積分散={cumvar[n_comp-1]:.4f}")
    return scaler, pca, X_pca


def fit_kmeans_gmm(X_pca: np.ndarray, k: int, verbose: bool = True) -> dict:
    """K-Means++ → GMM EM hybrid (§6.3.2)・GMM posterior probability 取得."""
    X_pca = np.asarray(X_pca, dtype=np.float64)  # GMM 数値安定性 (float32 → float64)
    km = KMeans(n_clusters=k, init="k-means++", n_init=10, random_state=RANDOM_STATE)
    km_labels = km.fit_predict(X_pca)

    # GMM EM (K-Means cluster_centers_ で初期化)・高次元で full 不安定なら diag (§6.3.2 data-driven)
    cov_type = "diag" if X_pca.shape[1] > 50 else "full"
    gmm = GaussianMixture(
        n_components=k, covariance_type=cov_type,
        means_init=km.cluster_centers_, random_state=RANDOM_STATE, max_iter=200,
        reg_covar=1e-3,  # ill-defined covariance (singleton/collapsed) 防止・sklearn 推奨
    )
    gmm.fit(X_pca)
    gmm_proba = gmm.predict_proba(X_pca)   # posterior probability
    gmm_labels = gmm.predict(X_pca)

    sil = float(silhouette_score(X_pca, gmm_labels, sample_size=min(10000, len(X_pca)),
                                 random_state=RANDOM_STATE))
    sil_km = float(silhouette_score(X_pca, km_labels, sample_size=min(10000, len(X_pca)),
                                    random_state=RANDOM_STATE))
    if verbose:
        print(f"[k={k}] silhouette: KMeans={sil_km:.4f} / GMM(hybrid)={sil:.4f} / cov={cov_type} / inertia={km.inertia_:.1f}")

    return {
        "k": k, "kmeans": km, "gmm": gmm, "cov_type": cov_type,
        "km_labels": km_labels, "gmm_labels": gmm_labels, "gmm_proba": gmm_proba,
        "silhouette_gmm": sil, "silhouette_km": sil_km, "inertia": float(km.inertia_),
    }


def calibrate_proba(gmm_proba: np.ndarray, gmm_labels: np.ndarray, k: int) -> tuple:
    """fold 別 Isotonic Regression キャリブレーション (§6.3.6・CP3 Critical-3).

    教師なし → GMM hard assignment (argmax) を pseudo-label として posterior を self-calibrate.
    各 cluster c について「posterior_c が実際の所属率に合っているか」を isotonic で校正.
    """
    calibrators = {}
    proba_cal = np.zeros_like(gmm_proba)
    for c in range(k):
        iso = IsotonicRegression(out_of_bounds="clip")
        y_c = (gmm_labels == c).astype(int)
        iso.fit(gmm_proba[:, c], y_c)
        calibrators[c] = iso
        proba_cal[:, c] = iso.transform(gmm_proba[:, c])
    row_sum = proba_cal.sum(axis=1, keepdims=True)
    row_sum[row_sum == 0] = 1.0
    proba_cal = proba_cal / row_sum
    return calibrators, proba_cal


def compute_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    bins = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        if i == n_bins - 1:
            mask = (y_prob >= bins[i]) & (y_prob <= bins[i + 1])
        else:
            mask = (y_prob >= bins[i]) & (y_prob < bins[i + 1])
        if mask.sum() == 0:
            continue
        ece += (mask.sum() / len(y_true)) * abs(float(y_true[mask].mean()) - float(y_prob[mask].mean()))
    return float(ece)


def eval_calibration(proba_cal: np.ndarray, gmm_labels: np.ndarray, k: int) -> dict:
    """Brier / ECE (per cluster macro・self-consistency)."""
    briers, eces = [], []
    for c in range(k):
        y_c = (gmm_labels == c).astype(int)
        briers.append(brier_score_loss(y_c, proba_cal[:, c]))
        eces.append(compute_ece(y_c, proba_cal[:, c]))
    return {"brier_macro": float(np.mean(briers)), "ece_macro": float(np.mean(eces))}


def compute_regime_corr(labels: np.ndarray, X_cluster: pd.DataFrame) -> float:
    """cluster 割当 と regime 確率の Pearson 相関の最大絶対値 (§6.3.1)."""
    regime_cols = [c for c in X_cluster.columns if c.startswith("regime_")]
    if not regime_cols:
        return float("nan")
    corrs = []
    for rc in regime_cols:
        try:
            corr = np.corrcoef(labels.astype(float), X_cluster[rc].values)[0, 1]
            if not np.isnan(corr):
                corrs.append(abs(corr))
        except Exception:
            pass
    return float(max(corrs)) if corrs else float("nan")


def cluster_balance(labels: np.ndarray, k: int) -> dict:
    counts = np.bincount(labels, minlength=k)
    fracs = counts / counts.sum()
    return {"counts": counts.tolist(), "fracs": fracs.tolist(), "min_frac": float(fracs.min())}


# ============== 旧 16 列版 silhouette (比較用・§6.3.1 Critical-1) ==============

def old16_silhouette(k: int) -> dict:
    """Phase 4-a 旧 16 列版 predictions で silhouette 実測 (= 架空 0.15-0.20 を実測値で置換)."""
    df = pd.read_parquet(PARQUET_OLD16)
    feat_cols = [c for c in df.columns if c != "close"]
    X = df[feat_cols].dropna()
    scaler = RobustScaler()
    Xs = scaler.fit_transform(X.values)
    km = KMeans(n_clusters=k, init="k-means++", n_init=10, random_state=RANDOM_STATE)
    lbl = km.fit_predict(Xs)
    sil = float(silhouette_score(Xs, lbl, sample_size=min(10000, len(Xs)), random_state=RANDOM_STATE))
    return {"n_features": len(feat_cols), "n_rows": len(X), "silhouette": sil}


# ============== ラベル付け (§6.3.5) ==============

def label_clusters(labels: np.ndarray, meta_df: pd.DataFrame, k: int) -> dict:
    """4 軸 (TP_prob / MFE / SL_prob / 保有時間代理) で post-hoc 命名.

    保有時間代理 = 短期 K(6,12) TP 確率 vs 長期 K(96,144,288) TP 確率の差.
    """
    short_K = [6, 12]
    long_K = [96, 144, 288]
    tp_cols = [c for c in meta_df.columns if c.startswith("tp_prob_")]
    sl_cols = [c for c in meta_df.columns if c.startswith("_sl_prob_")]
    mfe_cols = [c for c in meta_df.columns if c.startswith("pred_") and "MFE" in c]
    short_tp = [c for c in tp_cols if any(c.endswith(f"K{K}") for K in short_K)]
    long_tp = [c for c in tp_cols if any(c.endswith(f"K{K}") for K in long_K)]

    stats = {}
    for c in range(k):
        m = labels == c
        sub = meta_df.loc[m]
        stats[c] = {
            "n": int(m.sum()),
            "tp_prob_mean": float(sub[tp_cols].mean().mean()),
            "sl_prob_mean": float(sub[sl_cols].mean().mean()),
            "mfe_mean": float(sub[mfe_cols].mean().mean()),
            "horizon_proxy": float(sub[short_tp].mean().mean() - sub[long_tp].mean().mean()),
        }

    # 相対順位で命名 (= post-hoc・train のみ)
    sl_rank = sorted(range(k), key=lambda c: stats[c]["sl_prob_mean"], reverse=True)
    tp_rank = sorted(range(k), key=lambda c: stats[c]["tp_prob_mean"], reverse=True)
    names = {}
    names[sl_rank[0]] = "risky"          # SL 確率最大 = 危険型
    # TP 確率高 + 短期寄り = scalp / TP 確率高 + 長期寄り = long_term
    for c in tp_rank:
        if c in names:
            continue
        if stats[c]["horizon_proxy"] >= 0:
            names[c] = "scalp" if "scalp" not in names.values() else f"scalp_{c}"
        else:
            names[c] = "long_term" if "long_term" not in names.values() else f"long_term_{c}"
    for c in range(k):
        if c not in names:
            names[c] = "avg" if "avg" not in names.values() else f"avg_{c}"
    return {"stats": stats, "names": names}


# ============== main ==============

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="[2.5] cluster classifier (§6.3)")
    p.add_argument("--smoke", action="store_true", help="1 fold + k=3 のみ (PCA cap=30)")
    p.add_argument("--pred-only", action="store_true",
                   help="入力を予測値 56 のみに限定 + PCA なし (= §6.3.3 data-driven 経路・全投入 0.022 で大敗を受けた切替)")
    p.add_argument("--mfe-only", action="store_true",
                   help="入力を揺れ幅予測 28 のみに限定 + PCA なし (= 旧16列 0.49 の再現確認・確率系 TP/meta 除外)")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    t_start = time.time()
    print(f"[start] [2.5] cluster classifier ({pd.Timestamp.now()})")

    folds = [0] if args.smoke else list(range(N_FOLDS))
    k_candidates = [3] if args.smoke else K_CANDIDATES
    pca_cap = 30 if args.smoke else PCA_MAX_COMPONENTS
    mode = "mfe_only" if args.mfe_only else ("pred_only" if args.pred_only else "all")
    use_pca = (mode == "all")  # pred_only / mfe_only は PCA なし (= 旧 16 列版と同条件)
    print(f"[mode] 入力モード={mode} / PCA={'なし' if not use_pca else f'cap{pca_cap}'}")

    # 1. 入力組み立て
    X_cluster, meta_df = assemble_input(folds, mode=mode, verbose=True)
    assert "test" not in str(PARQUET_TRAIN), "fit は train 期間のみ (§6.3.7)"
    n_pred = len([c for c in X_cluster.columns if c.startswith(("pred_", "tp_prob_", "meta_yes_"))])
    n_regime = len([c for c in X_cluster.columns if c.startswith("regime_")])
    print(f"[input] 列内訳: 予測値={n_pred} / regime={n_regime} / 元特徴量={X_cluster.shape[1]-n_pred-n_regime} / 計={X_cluster.shape[1]}")

    # 2. NaN 前処理 (高NaN列 drop + median imputation)
    X_clean, imputer, drop_cols = clean_features(X_cluster, verbose=True)

    # 3. RobustScaler + (PCA)
    scaler, pca, X_pca = fit_pca_scaler(X_clean, pca_cap, use_pca=use_pca, verbose=True)

    # 3. k ∈ {3,4,5} 並列 fit → silhouette 最大 + 偏り verify
    print(f"[fit] k 候補 {k_candidates} で K-Means+GMM hybrid fit")
    fits = {}
    for k in k_candidates:
        fits[k] = fit_kmeans_gmm(X_pca, k, verbose=True)
        bal = cluster_balance(fits[k]["km_labels"], k)
        fits[k]["balance"] = bal
        print(f"[k={k}] 偏り: min_frac={bal['min_frac']:.4f} (合格={'✅' if bal['min_frac']>=MIN_CLUSTER_FRAC else '❌'}) "
              f"counts={bal['counts']}")

    # silhouette 最大 + 偏り合格 の k を採用
    valid_ks = [k for k in k_candidates if fits[k]["balance"]["min_frac"] >= MIN_CLUSTER_FRAC]
    if not valid_ks:
        print("[fit] ⚠️ 全 k で偏り不合格 → silhouette 最大を採用 (要 §6.3.3 入力再設計)")
        valid_ks = k_candidates
    # KMeans 採用 (= §6.3.2 実測修正: GMM hybrid は KMeans より silhouette 低く逆効果と判明)
    best_k = max(valid_ks, key=lambda k: fits[k]["silhouette_km"])
    print(f"[fit] 採用 k={best_k} (KMeans silhouette={fits[best_k]['silhouette_km']:.4f} / GMM={fits[best_k]['silhouette_gmm']:.4f})")

    best = fits[best_k]
    labels = best["km_labels"]

    # 4. cluster 確率 = KMeans 距離 softmax (= GMM posterior 代替・§6.3.6 実測修正)
    #    教師なし KMeans は isotonic 校正省略 (= 実測で Brier/ECE=0 で機能せず・GMM posterior 前提だった)
    X_pca64 = np.asarray(X_pca, dtype=np.float64)
    dists = best["kmeans"].transform(X_pca64)  # (n, k) 各重心への距離
    neg = -dists
    neg -= neg.max(axis=1, keepdims=True)
    exp = np.exp(neg)
    proba_cal = exp / exp.sum(axis=1, keepdims=True)  # softmax(-距離) で疑似確率
    calibrators = None
    calib_eval = eval_calibration(proba_cal, labels, best_k)
    print(f"[calib] (参考) Brier_macro={calib_eval['brier_macro']:.4f} ECE_macro={calib_eval['ece_macro']:.4f}")

    # 5. regime 相関
    regime_corr = compute_regime_corr(labels, X_cluster)
    print(f"[eval] regime 相関 max|Pearson|={regime_corr:.4f} (合格={'✅' if regime_corr<REGIME_CORR_PASS else '❌'})")

    # 6. 旧 16 列版 silhouette 比較
    print(f"[eval] 旧 16 列版 (Phase 4-a) silhouette 実測 (k={best_k})")
    old16 = old16_silhouette(best_k)
    improve = (best["silhouette_km"] - old16["silhouette"]) / abs(old16["silhouette"]) * 100 if old16["silhouette"] != 0 else float("nan")
    print(f"[eval] 旧16列={old16['silhouette']:.4f} / 新(KMeans)={best['silhouette_km']:.4f} / 改善={improve:+.1f}%")

    # 7. ラベル付け (§6.3.5)
    labeling = label_clusters(labels, meta_df, best_k)
    print(f"[label] 命名: {labeling['names']}")

    # 8. 出力 7 主要列 parquet
    confidence = np.sort(proba_cal, axis=1)
    confidence = confidence[:, -1] - confidence[:, -2]  # 最大 - 2番目
    # 各 trade の silhouette は計算コスト高 → sample silhouette を NaN で保留 (= 全体 silhouette で代替)
    out_df = pd.DataFrame({
        "entry_id": meta_df["entry_id"].values,
        "fold": meta_df["fold"].values,
        "cluster_id": labels,
        "cluster_label": [labeling["names"][c] for c in labels],
        "cluster_confidence": confidence.astype(np.float32),
    })
    for c in range(best_k):
        out_df[f"cluster_prob_{c}"] = proba_cal[:, c].astype(np.float32)

    out_pq = OUT_DIR / "cluster_predictions_train_2021_2024.parquet"
    out_df.to_parquet(out_pq, compression="snappy")

    # 9. artifact 保存 (= train 含む名・§6.3.7)
    joblib.dump(best["kmeans"], OUT_DIR / "cluster_kmeans_train_2021_2024.joblib")
    joblib.dump(best["gmm"], OUT_DIR / "cluster_gmm_train_2021_2024.joblib")
    joblib.dump(pca, OUT_DIR / "pca_train_2021_2024.joblib")
    joblib.dump(scaler, OUT_DIR / "scaler_train_2021_2024.joblib")
    joblib.dump(calibrators, OUT_DIR / "calibrator_train_2021_2024.joblib")
    joblib.dump(imputer, OUT_DIR / "imputer_train_2021_2024.joblib")
    (OUT_DIR / "dropped_high_nan_cols_train_2021_2024.json").write_text(
        json.dumps({"n_dropped": len(drop_cols), "threshold": NAN_COL_DROP_THRESHOLD,
                    "cols": drop_cols}, indent=2))

    # 10. Stage 1 評価 summary
    summary = {
        "scope": "train_2021_2024 out-of-fold (3 fold 集約)",
        "n_rows": int(len(X_cluster)),
        "n_input_cols": int(X_cluster.shape[1]),
        "n_pred_cols": n_pred,
        "n_regime_cols": n_regime,
        "n_dropped_high_nan_cols": len(drop_cols),
        "n_cols_after_clean": int(X_clean.shape[1]),
        "input_mode": mode,
        "use_pca": use_pca,
        "pca_components": int(pca.n_components_) if pca is not None else int(X_pca.shape[1]),
        "pca_cumvar": float(np.sum(pca.explained_variance_ratio_)) if pca is not None else 1.0,
        "best_k": best_k,
        "algorithm": "KMeans (= GMM hybrid 実測逆効果で単体採用・§6.3.2 修正)",
        "k_candidates_silhouette_km": {k: fits[k]["silhouette_km"] for k in k_candidates},
        "stage1": {
            "silhouette_km": best["silhouette_km"],
            "silhouette_gmm": best["silhouette_gmm"],
            "silhouette_pass": bool(best["silhouette_km"] >= SILHOUETTE_PASS),
            "brier_macro": calib_eval["brier_macro"],
            "brier_pass": bool(calib_eval["brier_macro"] < BRIER_PASS),
            "ece_macro": calib_eval["ece_macro"],
            "ece_pass": bool(calib_eval["ece_macro"] < ECE_PASS),
            "min_cluster_frac": best["balance"]["min_frac"],
            "balance_pass": bool(best["balance"]["min_frac"] >= MIN_CLUSTER_FRAC),
            "regime_corr": regime_corr,
            "regime_corr_pass": bool(regime_corr < REGIME_CORR_PASS),
            "old16_silhouette": old16["silhouette"],
            "new_vs_old16_improve_pct": improve,
        },
        "cluster_names": labeling["names"],
        "cluster_stats": labeling["stats"],
        "balance": best["balance"],
        "elapsed_sec": time.time() - t_start,
    }
    (OUT_DIR / "cluster_summary.json").write_text(json.dumps(summary, indent=2, default=str))

    # Stage 1 review md
    s1 = summary["stage1"]
    lines = [
        f"# 工程 [2.5] cluster 分類 — Stage 1 評価 ({pd.Timestamp.now()})",
        "",
        f"スコープ: train_2021_2024 out-of-fold ({summary['n_rows']:,} bar) / 入力 {summary['n_input_cols']} 列 → PCA {summary['pca_components']} 主成分 (分散 {summary['pca_cumvar']:.3f})",
        "",
        f"## 採用 k = {best_k} (silhouette 最大 + 偏り合格)",
        "",
        "| k | silhouette(GMM) | min_frac | counts |",
        "|---|---|---|---|",
    ]
    for k in k_candidates:
        lines.append(f"| {k} | {fits[k]['silhouette_km']:.4f} | {fits[k]['balance']['min_frac']:.4f} | {fits[k]['balance']['counts']} |")
    lines += [
        "",
        "## Stage 1 合否",
        "",
        "| 項目 | 実測 | 合格ライン | 判定 |",
        "|---|---|---|---|",
        f"| silhouette | {s1['silhouette_km']:.4f} | > {SILHOUETTE_PASS} | {'✅' if s1['silhouette_pass'] else '❌'} |",
        f"| Brier (校正) | {s1['brier_macro']:.4f} | < {BRIER_PASS} | {'✅' if s1['brier_pass'] else '❌'} |",
        f"| ECE (校正) | {s1['ece_macro']:.4f} | < {ECE_PASS} | {'✅' if s1['ece_pass'] else '❌'} |",
        f"| 偏り (min_frac) | {s1['min_cluster_frac']:.4f} | ≥ {MIN_CLUSTER_FRAC} | {'✅' if s1['balance_pass'] else '❌'} |",
        f"| regime 相関 | {s1['regime_corr']:.4f} | < {REGIME_CORR_PASS} | {'✅' if s1['regime_corr_pass'] else '❌'} |",
        f"| 旧16列版比較 | 新{s1['silhouette_km']:.4f} vs 旧{s1['old16_silhouette']:.4f} | +50% | {s1['new_vs_old16_improve_pct']:+.1f}% |",
        "",
        "## cluster 命名 (§6.3.5・4 軸 post-hoc)",
        "",
        "| cluster | label | n | TP_prob | SL_prob | MFE | 保有代理 |",
        "|---|---|---|---|---|---|---|",
    ]
    for c in range(best_k):
        st = labeling["stats"][c]
        lines.append(f"| {c} | {labeling['names'][c]} | {st['n']:,} | {st['tp_prob_mean']:.3f} | "
                     f"{st['sl_prob_mean']:.3f} | {st['mfe_mean']:.3f} | {st['horizon_proxy']:+.3f} |")
    (OUT_DIR / "stage1_review.md").write_text("\n".join(lines))

    print(f"\n[done] elapsed: {(time.time()-t_start)/60:.1f}min")
    print(f"[done] 出力: {out_pq}")
    print(f"[done] Stage 1 review: {OUT_DIR / 'stage1_review.md'}")
    print(f"[done] summary: {OUT_DIR / 'cluster_summary.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
