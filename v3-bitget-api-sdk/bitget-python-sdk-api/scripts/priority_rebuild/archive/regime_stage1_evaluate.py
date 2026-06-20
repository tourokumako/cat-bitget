"""
工程 [1.5] regime ensemble — Stage 1 内部スコア評価 (Stage G)

設計書: .claude/memory/ml_pipeline_baseline_v1.md v2.8 §6.1.1 Stage 1
CP1 監査 Q1 改善 1 反映: Brier / ECE / reliability + 3 判定器予測誤差 Pearson 相関

機能:
  1. HMM log_likelihood + BIC (= hmm_calibrated_artifact.json から取得 + パラメータ数算出)
  2. k-means silhouette score (= kmeans_classifier_artifact.json から取得)
  3. Brier score multiclass (= 各判定器 + ensemble・target = future 4h log_return 3 クラス)
  4. ECE (Expected Calibration Error・10 bin)
  5. 3 判定器の予測誤差 pairwise Pearson 相関 (= ensemble 前提条件 verify・相関 < 0.5 で OK・> 0.7 で要見直し)
  6. reliability diagram データ (= 各判定器 + ensemble の 10 bin 予測 vs 実測)

出力:
  - results/regime_step1/stage1_evaluation_report.json
  - results/regime_step1/stage1_reliability_diagram_data.parquet
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss

sys.path.insert(0, str(Path(__file__).resolve().parent))
from regime_target_labels import compute_target_for_dataset, get_config as target_config

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "results/regime_step1"

DATASETS = ["train_2021_2024", "test_2025", "test_2026_q1"]
CATEGORIES = ["uptrend", "downtrend", "range"]
N_BIN_ECE = 10


def load_classifier_probs(ds: str) -> dict[str, pd.DataFrame]:
    """各判定器の raw 確率 (1h grid) を取得."""
    rule = pd.read_parquet(OUT_DIR / f"rule_classifier_{ds}.parquet")
    km = pd.read_parquet(OUT_DIR / f"kmeans_classifier_{ds}.parquet")
    hmm = pd.read_parquet(OUT_DIR / f"hmm_calibrated_{ds}.parquet")
    ens = pd.read_parquet(OUT_DIR / f"ensemble_{ds}.parquet")

    rule_probs = rule[["regime_prob_up", "regime_prob_down", "regime_prob_range"]].rename(columns={
        "regime_prob_up": "uptrend", "regime_prob_down": "downtrend", "regime_prob_range": "range"
    })
    km_probs = km[["_raw_prob_up", "_raw_prob_down", "_raw_prob_range"]].rename(columns={
        "_raw_prob_up": "uptrend", "_raw_prob_down": "downtrend", "_raw_prob_range": "range"
    })
    hmm_probs = hmm[["_raw_prob_up", "_raw_prob_down", "_raw_prob_range"]].rename(columns={
        "_raw_prob_up": "uptrend", "_raw_prob_down": "downtrend", "_raw_prob_range": "range"
    })
    ens_probs = ens[["regime_prob_up", "regime_prob_down", "regime_prob_range"]].rename(columns={
        "regime_prob_up": "uptrend", "regime_prob_down": "downtrend", "regime_prob_range": "range"
    })

    return {"rule": rule_probs, "kmeans": km_probs, "hmm": hmm_probs, "ensemble": ens_probs}


def compute_brier_multiclass(probs: pd.DataFrame, target: pd.Series) -> dict:
    """3 クラス Brier = カテゴリごとに binary brier の平均."""
    out = {}
    for cat in CATEGORIES:
        y = (target == cat).astype(float)
        m = probs[cat].notna() & target.notna()
        if m.sum() < 100:
            out[cat] = None
            continue
        bs = brier_score_loss(y[m].values, probs.loc[m, cat].values)
        out[cat] = float(bs)
    valid = [v for v in out.values() if v is not None]
    out["mean"] = float(np.mean(valid)) if valid else None
    return out


def compute_ece(probs: pd.DataFrame, target: pd.Series, n_bins: int = N_BIN_ECE) -> dict:
    """Expected Calibration Error: 各カテゴリで bin 別の予測確率 vs 実測陽性率の差."""
    out = {}
    for cat in CATEGORIES:
        y = (target == cat).astype(float)
        p = probs[cat]
        m = p.notna() & target.notna()
        if m.sum() < 100:
            out[cat] = None
            continue
        y_v = y[m].values
        p_v = p[m].values
        bins = np.linspace(0, 1, n_bins + 1)
        ece = 0.0
        total = len(p_v)
        for i in range(n_bins):
            lo, hi = bins[i], bins[i + 1]
            mask = (p_v >= lo) & (p_v < hi if i < n_bins - 1 else p_v <= hi)
            n = mask.sum()
            if n == 0:
                continue
            avg_p = float(p_v[mask].mean())
            avg_y = float(y_v[mask].mean())
            ece += (n / total) * abs(avg_p - avg_y)
        out[cat] = float(ece)
    valid = [v for v in out.values() if v is not None]
    out["mean"] = float(np.mean(valid)) if valid else None
    return out


def compute_reliability_data(probs: pd.DataFrame, target: pd.Series, n_bins: int = N_BIN_ECE) -> pd.DataFrame:
    """reliability diagram データを返す (= category × bin × {mean_pred, actual, count})."""
    rows = []
    bins = np.linspace(0, 1, n_bins + 1)
    for cat in CATEGORIES:
        y = (target == cat).astype(float)
        p = probs[cat]
        m = p.notna() & target.notna()
        if m.sum() < 100:
            continue
        y_v = y[m].values
        p_v = p[m].values
        for i in range(n_bins):
            lo, hi = bins[i], bins[i + 1]
            mask = (p_v >= lo) & (p_v < hi if i < n_bins - 1 else p_v <= hi)
            n = mask.sum()
            if n == 0:
                rows.append({"category": cat, "bin_lo": lo, "bin_hi": hi, "count": 0, "mean_pred": None, "actual": None})
                continue
            rows.append({
                "category": cat,
                "bin_lo": float(lo),
                "bin_hi": float(hi),
                "count": int(n),
                "mean_pred": float(p_v[mask].mean()),
                "actual": float(y_v[mask].mean()),
            })
    return pd.DataFrame(rows)


def compute_pairwise_pred_error_correlations(probs_dict: dict[str, pd.DataFrame], target: pd.Series) -> dict:
    """各判定器の予測誤差 = (1 - P(target_cat)) の系列について pairwise Pearson 相関.

    判定器間の予測誤差相関が高いと ensemble 効果が薄れる (= CP1 監査 Q7 改善 1).
    """
    # error_i = 1 - P_i(target_cat)
    classifiers = ["rule", "kmeans", "hmm"]
    errors = {}
    for clf in classifiers:
        probs = probs_dict[clf]
        # 各 row で target_cat 列の確率を取り、誤差 = 1 - p
        err_series = pd.Series(index=probs.index, dtype=float)
        for cat in CATEGORIES:
            mask = (target == cat)
            err_series[mask] = 1.0 - probs.loc[mask, cat]
        errors[clf] = err_series

    pair_corr = {}
    for i in range(len(classifiers)):
        for j in range(i + 1, len(classifiers)):
            a = classifiers[i]
            b = classifiers[j]
            df_ab = pd.DataFrame({a: errors[a], b: errors[b]}).dropna()
            if len(df_ab) < 100:
                pair_corr[f"{a}_vs_{b}"] = None
                continue
            pair_corr[f"{a}_vs_{b}"] = float(df_ab[a].corr(df_ab[b]))
    return pair_corr


def compute_hmm_bic(log_likelihood: float, n_components: int, n_features: int, n_samples: int, covariance_type: str = "diag") -> float:
    """HMM の BIC を計算.

    BIC = -2 * log_likelihood + k * log(n_samples)
    HMM パラメータ数 k =
      - 開始確率: n_components - 1
      - 遷移行列: n_components * (n_components - 1)
      - 各状態の平均: n_components * n_features
      - 各状態の共分散 (diag): n_components * n_features
    """
    if covariance_type == "diag":
        cov_params = n_components * n_features
    elif covariance_type == "full":
        cov_params = n_components * n_features * (n_features + 1) // 2
    else:
        cov_params = 0
    k = (
        (n_components - 1)
        + n_components * (n_components - 1)
        + n_components * n_features
        + cov_params
    )
    bic = -2.0 * log_likelihood + k * np.log(max(n_samples, 1))
    return float(bic)


def main() -> int:
    print(f"[output dir] {OUT_DIR}")

    # ===== artifact 読み込み (= 既存統計値) =====
    kmeans_artifact = json.loads((OUT_DIR / "kmeans_classifier_artifact.json").read_text())
    hmm_artifact = json.loads((OUT_DIR / "hmm_calibrated_artifact.json").read_text())
    ensemble_artifact = json.loads((OUT_DIR / "ensemble_artifact.json").read_text())

    # ===== HMM BIC 計算 =====
    n_features_hmm = 84
    n_components_hmm = 3
    train_log_lik = hmm_artifact["log_likelihoods"]["train_2021_2024"]
    # train サンプル数 (= 1h grid drop NaN 後)
    # hmm_artifact からは取得できない → 1h grid drop NaN は train_hmm_regime.py 出力済の summary から取得
    hmm_summary = json.loads((OUT_DIR / "hmm_summary_train_2021_2024.json").read_text())
    n_samples_hmm = hmm_summary["input_shape_after_dropna"][0]
    hmm_bic = compute_hmm_bic(train_log_lik, n_components_hmm, n_features_hmm, n_samples_hmm, "diag")
    print(f"  HMM BIC (train) = {hmm_bic:.0f}")

    # ===== k-means silhouette (= train) =====
    chosen_k = kmeans_artifact["chosen_k"]
    fold_metrics = kmeans_artifact["fold_metrics"]
    sil_at_chosen = [m["metrics"][str(chosen_k)]["silhouette"] for m in fold_metrics if str(chosen_k) in m["metrics"]]
    sil_mean = float(np.mean(sil_at_chosen)) if sil_at_chosen else None
    print(f"  k-means silhouette (mean across folds at k={chosen_k}) = {sil_mean}")

    # ===== 各 dataset で評価 =====
    report = {
        "design_doc": ".claude/memory/ml_pipeline_baseline_v1.md (v2.8 §6.1.1)",
        "cp1_audit": ".claude/audits/2026-05-27_step15_regime_ensemble_design_cp1_audit_report.md",
        "target_config": target_config(),
        "hmm_summary": {
            "log_likelihood_train": train_log_lik,
            "log_likelihood_test_2025": hmm_artifact["log_likelihoods"].get("test_2025"),
            "log_likelihood_test_2026_q1": hmm_artifact["log_likelihoods"].get("test_2026_q1"),
            "bic_train": hmm_bic,
            "n_components": n_components_hmm,
            "n_features": n_features_hmm,
            "n_samples_train": n_samples_hmm,
        },
        "kmeans_summary": {
            "chosen_k": chosen_k,
            "silhouette_mean_at_chosen_k": sil_mean,
            "fold_best_ks": kmeans_artifact["fold_best_ks"],
        },
        "ensemble_summary": {
            "best_weights": ensemble_artifact["best_weights"],
            "best_f1_macro": ensemble_artifact["best_f1_macro"],
            "best_log_loss": ensemble_artifact["best_log_loss"],
            "best_accuracy": ensemble_artifact["best_accuracy"],
            "equal_weight_f1": ensemble_artifact["equal_weight_f1"],
        },
        "per_dataset": {},
    }
    all_reliability_dfs = []
    for ds in DATASETS:
        print(f"\n----- {ds} -----")
        probs = load_classifier_probs(ds)
        target_df = compute_target_for_dataset(ds)
        target = target_df["target_3class"].reindex(probs["ensemble"].index)

        ds_report = {}
        for clf_name, p in probs.items():
            brier = compute_brier_multiclass(p, target)
            ece = compute_ece(p, target)
            ds_report[clf_name] = {"brier": brier, "ece": ece}
            print(f"  {clf_name:<8}: Brier mean={brier.get('mean'):.4f}  ECE mean={ece.get('mean'):.4f}" if brier.get("mean") is not None else f"  {clf_name}: insufficient data")

            # reliability data
            rel_df = compute_reliability_data(p, target)
            rel_df["classifier"] = clf_name
            rel_df["dataset"] = ds
            all_reliability_dfs.append(rel_df)

        # 3 判定器 pairwise error 相関
        pair_corr = compute_pairwise_pred_error_correlations(probs, target)
        ds_report["pairwise_error_correlation"] = pair_corr
        print(f"  pairwise error correlation: {pair_corr}")

        report["per_dataset"][ds] = ds_report

    # reliability diagram data 保存
    if all_reliability_dfs:
        rel_full = pd.concat(all_reliability_dfs, ignore_index=True)
        rel_out = OUT_DIR / "stage1_reliability_diagram_data.parquet"
        rel_full.to_parquet(rel_out)
        print(f"\n  reliability diagram data saved: {rel_out}")

    # report 保存
    report_out = OUT_DIR / "stage1_evaluation_report.json"
    with report_out.open("w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n[DONE] report: {report_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
