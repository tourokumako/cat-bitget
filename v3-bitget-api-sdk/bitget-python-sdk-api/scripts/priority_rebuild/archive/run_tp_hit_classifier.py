"""
run_tp_hit_classifier.py — Phase 4-b 前倒し設計 Step I-2.1 (TP 約定率 Classifier)

Step I-1 仕様書 v2.1 (`.claude/instructions/2026-05-23_phase4b_forward_design_spec.md`) の
§2 TP 約定率モデル (Classifier) 実装。Phase 1 評価式に Phase 4-b 仕様の最小スコープ部分を
前倒し組込みするための新規 LightGBM Classifier 学習スクリプト。

設計判断 (cc_role §1.5):
- ラベル: `tp_hit = 1 if {side}_MFE_pct_K{K} >= TP_PCT else 0` (option δ・MFE_pct ラベル流用)
- TP_PCT を特徴量化 (X に 1 列追加・複数 TP_PCT を sequential 連結で 1 model 学習)
- 8 組合せ (K × side) × 5 fold = 40 学習 (TP_PCT grid は特徴量化のため別学習不要)
- 評価指標: AUC + Brier score + Calibration max deviation
- leak verify: phase_compliance §1.4 Z 案ガード (case_a `_check_fractal_leak` 流用)
- 起動時 assertion: artifact_path に train_2021_2024 含み test 含まない (§8.4 (v))

CLI:
- --smoke: sample.parquet / K=12 LONG / TP_PCT=(0.5,) / n_estimators=50 (1 学習・約 1-3 分)
- --full: train_2021_2024.parquet / K=(12,24,48,96) / side=(LONG,SHORT) / TP_PCT=6 種 / n_estimators=300 (40 学習・約 1-2 時間)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss, roc_auc_score

import lightgbm as lgb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_phase1_v5_purged_kfold import (  # noqa: E402
    K_DEFAULT_LIST,
    OUT_BASE,
    PARQUET_DIR,
    SIDES_DEFAULT,
    load_parquet_with_blacklist,
    prepare_purged_cv,
    split_with_purging,
)
from run_lgbm_phase1_v5_case_a_rmse import (  # noqa: E402
    FRACTAL_FIB_LEVEL_PATTERNS,
    _build_train_valid_split,
    _check_fractal_leak,
    _get_top20_feature_importance,
    VALID_TAIL_FRACTION,
)

CASE_NAME = "tp_hit_classifier"

# 仕様書 §2.1 / §3.2 TP_PCT grid (6 段階・暫定)
TP_PCT_GRID: Tuple[float, ...] = (0.3, 0.5, 0.8, 1.2, 1.8, 2.5)

# Calibration 評価で使う bin 数 (10 bin = 0.0-1.0 を 0.1 刻み)
CALIBRATION_N_BINS = 10

EARLY_STOPPING_ROUNDS = 50

# LightGBM Classifier ハイパラ (仕様書 §2.2)
LGBM_PARAMS_DEFAULT: Dict[str, object] = {
    "objective": "binary",
    "metric": "binary_logloss",
    "boosting_type": "gbdt",
    "num_leaves": 31,
    "learning_rate": 0.05,
    "feature_fraction": 0.9,
    "bagging_fraction": 0.9,
    "bagging_freq": 5,
    "min_child_samples": 20,
    "random_state": 42,
    "n_jobs": -1,
    "verbose": -1,
}

# 出力先 (case_a と同じ OUT_BASE 配下に classifier サブフォルダ)
OUT_CLASSIFIER_BASE = OUT_BASE / "_tp_hit_classifier"


@dataclass
class ClassifierFoldMetrics:
    """1 fold × 1 組合せ (K × side) の Classifier 評価指標."""

    fold_idx: int
    K: int
    side: str
    auc: float
    brier: float
    calibration_max_dev: float
    n_train: int
    n_test: int
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    n_tp_pct_in_aug: int  # TP_PCT 数 (=6)
    extra: Dict[str, float] = field(default_factory=dict)


@dataclass
class CombinationClassifierSummary:
    """1 組合せ 5 fold 統合の Classifier 評価."""

    K: int
    side: str
    n_folds: int
    auc_mean: float
    auc_std: float
    brier_mean: float
    brier_std: float
    calibration_max_dev_mean: float
    auc_pass: bool  # auc_mean >= 0.55
    brier_pass: bool  # brier_mean <= 0.25
    calibration_pass: bool  # calibration_max_dev_mean <= 0.1
    all_pass: bool


def _build_tp_hit_labels(
    y_mfe: pd.Series,
    tp_pct: float,
) -> np.ndarray:
    """option δ ラベル定義: tp_hit = 1 if MFE_pct >= TP_PCT else 0.

    Args:
        y_mfe: {side}_MFE_pct_K{K} 列 (Series・index は trade timestamp)
        tp_pct: TP_PCT 値 (%・例: 0.5 = 0.5%)

    Returns:
        np.ndarray (0/1・shape=(len(y_mfe),))
    """
    return (y_mfe.values >= tp_pct).astype(int)


def _augment_x_with_tp_pct(
    X: pd.DataFrame,
    tp_pct_grid: Tuple[float, ...],
    indices: np.ndarray,
) -> Tuple[pd.DataFrame, List[int]]:
    """X を TP_PCT grid 数 (G) 倍に拡張 (各 TP_PCT で行を複製・TP_PCT 列追加).

    sequential 連結方式 (memory 圧迫回避のため・全 X copy を避け iloc + concat):
      X_aug = pd.concat([X.iloc[indices].assign(TP_PCT=tp) for tp in TP_PCT_GRID])

    Args:
        X: 特徴量 DataFrame (約 2,604 列)
        tp_pct_grid: TP_PCT 値の tuple (例: (0.3, 0.5, 0.8, 1.2, 1.8, 2.5))
        indices: train/valid/test の position indices (np.ndarray)

    Returns:
        X_aug: 拡張後の DataFrame (shape=(len(indices) × G, 2,605))
        original_indices_repeat: 元 indices を G 回繰り返した list (label 生成で対応)
    """
    G = len(tp_pct_grid)
    X_sub = X.iloc[indices].copy()
    X_sub["TP_PCT"] = 0.0  # placeholder (assign で TP_PCT 別に上書き)

    pieces: List[pd.DataFrame] = []
    for tp in tp_pct_grid:
        piece = X_sub.copy()
        piece["TP_PCT"] = tp
        pieces.append(piece)
    X_aug = pd.concat(pieces, axis=0, ignore_index=False)
    # 元 indices を G 回繰り返した list (label との対応用)
    original_indices_repeat = list(indices) * G
    return X_aug, original_indices_repeat


def _build_tp_hit_labels_augmented(
    y_mfe_series: pd.Series,
    indices: np.ndarray,
    tp_pct_grid: Tuple[float, ...],
) -> np.ndarray:
    """X_aug に対応する 0/1 ラベル配列 (G × len(indices),).

    Args:
        y_mfe_series: {side}_MFE_pct_K{K} 列 (Series・全長)
        indices: train/valid/test position indices
        tp_pct_grid: TP_PCT 値 tuple

    Returns:
        y_aug: np.ndarray shape=(G × len(indices),)
    """
    y_sub = y_mfe_series.iloc[indices].values
    parts: List[np.ndarray] = []
    for tp in tp_pct_grid:
        parts.append((y_sub >= tp).astype(int))
    return np.concatenate(parts)


def _train_one_classifier_fold(
    X_tr_aug: pd.DataFrame,
    y_tr_aug: np.ndarray,
    X_va_aug: pd.DataFrame,
    y_va_aug: np.ndarray,
    n_estimators: int,
) -> Tuple[lgb.LGBMClassifier, float, float]:
    """LGBMClassifier 1 fold 学習 (binary objective + early stopping).

    Returns:
        model, train_logloss, valid_logloss
    """
    params = dict(LGBM_PARAMS_DEFAULT)
    params["n_estimators"] = n_estimators

    model = lgb.LGBMClassifier(**params)
    model.fit(
        X_tr_aug,
        y_tr_aug,
        eval_set=[(X_va_aug, y_va_aug)],
        eval_metric="binary_logloss",
        callbacks=[lgb.early_stopping(EARLY_STOPPING_ROUNDS, verbose=False)],
    )

    # train logloss
    p_tr = model.predict_proba(X_tr_aug)[:, 1]
    eps = 1e-15
    p_tr_clip = np.clip(p_tr, eps, 1 - eps)
    train_ll = float(
        -(y_tr_aug * np.log(p_tr_clip) + (1 - y_tr_aug) * np.log(1 - p_tr_clip)).mean()
    )

    if hasattr(model, "best_score_") and model.best_score_:
        valid_ll = float(model.best_score_["valid_0"]["binary_logloss"])
    else:
        p_va = model.predict_proba(X_va_aug)[:, 1]
        p_va_clip = np.clip(p_va, eps, 1 - eps)
        valid_ll = float(
            -(y_va_aug * np.log(p_va_clip) + (1 - y_va_aug) * np.log(1 - p_va_clip)).mean()
        )

    return model, train_ll, valid_ll


def _classifier_metrics(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    n_bins: int = CALIBRATION_N_BINS,
) -> Dict[str, float]:
    """AUC + Brier score + Calibration max deviation.

    Returns:
        {"auc": float, "brier": float, "calibration_max_dev": float}
    """
    # AUC (両 class 揃っている時のみ・片寄り時は NaN)
    if len(np.unique(y_true)) < 2:
        auc = float("nan")
    else:
        auc = float(roc_auc_score(y_true, y_pred_proba))

    brier = float(brier_score_loss(y_true, y_pred_proba))

    # Calibration: 10 bin で y_pred 平均 vs y_true 平均が対角線に乗るか
    try:
        prob_true, prob_pred = calibration_curve(
            y_true, y_pred_proba, n_bins=n_bins, strategy="uniform"
        )
        # max deviation = max(|prob_true - prob_pred|)
        calib_max_dev = float(np.max(np.abs(prob_true - prob_pred)))
    except Exception:
        calib_max_dev = float("nan")

    return {
        "auc": auc,
        "brier": brier,
        "calibration_max_dev": calib_max_dev,
    }


def _train_one_combination(
    K: int,
    side: str,
    X: pd.DataFrame,
    y_dict: Dict[str, pd.DataFrame],
    idx: pd.DatetimeIndex,
    tp_pct_grid: Tuple[float, ...],
    n_estimators: int,
    n_splits: int,
    min_train_splits: int,
    out_base: Path,
    is_first_combination: bool,
) -> Tuple[List[ClassifierFoldMetrics], pd.Series]:
    """1 組合せ (K × side) × 5 fold の Classifier 学習統合.

    Returns:
        fold_metrics_list: 5 fold の ClassifierFoldMetrics
        tp_hit_prob_series: test trade × TP_PCT の予測確率 (multi-index で trade_ts × TP_PCT)
    """
    print(f"\n--- 組合せ K={K} side={side} ---")
    cv = prepare_purged_cv(n_splits=n_splits, min_train_splits=min_train_splits)
    mfe_col = f"{side}_MFE_pct_K{K}"
    y_mfe_series = y_dict[f"{side}_MFE_pct"][mfe_col]

    fold_metrics_list: List[ClassifierFoldMetrics] = []
    tp_hit_predictions: List[pd.DataFrame] = []
    fractal_guard_done = False

    for fold_idx, (train_idx, test_idx) in enumerate(
        split_with_purging(cv, X, idx, K)
    ):
        train_idx_inner, valid_idx = _build_train_valid_split(
            train_idx, VALID_TAIL_FRACTION
        )
        # embargo gap verify
        assert valid_idx[-1] < test_idx[0], (
            f"valid embargo violation: valid_idx[-1]={valid_idx[-1]} >= "
            f"test_idx[0]={test_idx[0]}"
        )

        # 拡張 X / y 構築
        X_tr_aug, _ = _augment_x_with_tp_pct(X, tp_pct_grid, train_idx_inner)
        y_tr_aug = _build_tp_hit_labels_augmented(y_mfe_series, train_idx_inner, tp_pct_grid)
        X_va_aug, _ = _augment_x_with_tp_pct(X, tp_pct_grid, valid_idx)
        y_va_aug = _build_tp_hit_labels_augmented(y_mfe_series, valid_idx, tp_pct_grid)
        X_te_aug, _ = _augment_x_with_tp_pct(X, tp_pct_grid, test_idx)
        y_te_aug = _build_tp_hit_labels_augmented(y_mfe_series, test_idx, tp_pct_grid)

        t0 = time.time()
        model, train_ll, valid_ll = _train_one_classifier_fold(
            X_tr_aug, y_tr_aug, X_va_aug, y_va_aug, n_estimators
        )
        elapsed = time.time() - t0

        # 1 組合せ目 & fold_idx=0 で fractal ガード判定 (case_a 同型・組合せ初回のみ)
        if is_first_combination and not fractal_guard_done:
            fi_top20 = _get_top20_feature_importance(model, X_tr_aug.columns.tolist())
            early_fi_dir = out_base / "_early_fi_for_guard_review"
            early_fi_dir.mkdir(parents=True, exist_ok=True)
            early_fi_path = early_fi_dir / f"fi_top20_classifier_K{K}_{side}.csv"
            fi_top20.to_csv(early_fi_path, index=False)
            print(f"[guard early save] {early_fi_path}")
            # X (augmented) を parquet_df として渡すと TP_PCT 列が含まれてしまうため
            # 元 X を渡す (lag-1 / 末尾 NaN verify は元 feature のみ対象)
            _check_fractal_leak(
                fi_top20,
                K,
                side,
                "TP_HIT",
                parquet_df=X,
                importance_csv_path=early_fi_path,
                full_rank_dir=early_fi_dir,
            )
            fractal_guard_done = True

        # test 予測 + 評価
        p_te = model.predict_proba(X_te_aug)[:, 1]
        metrics = _classifier_metrics(y_te_aug, p_te)

        fm = ClassifierFoldMetrics(
            fold_idx=fold_idx,
            K=K,
            side=side,
            auc=metrics["auc"],
            brier=metrics["brier"],
            calibration_max_dev=metrics["calibration_max_dev"],
            n_train=len(X_tr_aug),
            n_test=len(X_te_aug),
            train_start=str(idx[train_idx_inner[0]]),
            train_end=str(idx[train_idx_inner[-1]]),
            test_start=str(idx[test_idx[0]]),
            test_end=str(idx[test_idx[-1]]),
            n_tp_pct_in_aug=len(tp_pct_grid),
            extra={
                "train_logloss": train_ll,
                "valid_logloss": valid_ll,
                "elapsed_sec": elapsed,
                "n_valid": len(X_va_aug),
            },
        )
        fold_metrics_list.append(fm)
        print(
            f"  fold {fold_idx}: AUC={fm.auc:.4f} Brier={fm.brier:.4f} "
            f"CalibMaxDev={fm.calibration_max_dev:.4f} "
            f"n_train={fm.n_train} n_test={fm.n_test} elapsed={elapsed:.1f}s"
        )

        # test 予測値を保存 (trade_ts × TP_PCT の long-format DataFrame)
        n_test_unique = len(test_idx)
        G = len(tp_pct_grid)
        trade_ts_repeat = list(idx[test_idx]) * G
        tp_pct_repeat = [tp for tp in tp_pct_grid for _ in range(n_test_unique)]
        df_pred = pd.DataFrame({
            "trade_ts": trade_ts_repeat,
            "TP_PCT": tp_pct_repeat,
            "tp_hit_prob": p_te,
            "tp_hit_true": y_te_aug,
            "fold_idx": fold_idx,
        })
        tp_hit_predictions.append(df_pred)

    # fold 統合 predictions
    if tp_hit_predictions:
        df_all = pd.concat(tp_hit_predictions, axis=0, ignore_index=True)
    else:
        df_all = pd.DataFrame(columns=["trade_ts", "TP_PCT", "tp_hit_prob", "tp_hit_true", "fold_idx"])
    return fold_metrics_list, df_all


def _aggregate_combination_metrics(
    fold_metrics: List[ClassifierFoldMetrics],
) -> CombinationClassifierSummary:
    """5 fold 統合 → CombinationClassifierSummary (受け入れ基準 verify 込み)."""
    aucs = [m.auc for m in fold_metrics if not np.isnan(m.auc)]
    briers = [m.brier for m in fold_metrics if not np.isnan(m.brier)]
    calibs = [m.calibration_max_dev for m in fold_metrics if not np.isnan(m.calibration_max_dev)]

    auc_mean = float(np.mean(aucs)) if aucs else float("nan")
    auc_std = float(np.std(aucs)) if aucs else float("nan")
    brier_mean = float(np.mean(briers)) if briers else float("nan")
    brier_std = float(np.std(briers)) if briers else float("nan")
    calib_mean = float(np.mean(calibs)) if calibs else float("nan")

    auc_pass = (not np.isnan(auc_mean)) and (auc_mean >= 0.55)
    brier_pass = (not np.isnan(brier_mean)) and (brier_mean <= 0.25)
    calib_pass = (not np.isnan(calib_mean)) and (calib_mean <= 0.10)

    return CombinationClassifierSummary(
        K=fold_metrics[0].K if fold_metrics else 0,
        side=fold_metrics[0].side if fold_metrics else "",
        n_folds=len(fold_metrics),
        auc_mean=auc_mean,
        auc_std=auc_std,
        brier_mean=brier_mean,
        brier_std=brier_std,
        calibration_max_dev_mean=calib_mean,
        auc_pass=auc_pass,
        brier_pass=brier_pass,
        calibration_pass=calib_pass,
        all_pass=auc_pass and brier_pass and calib_pass,
    )


def train_tp_hit_classifier(
    parquet_path: Path,
    k_values: Tuple[int, ...] = K_DEFAULT_LIST,
    sides: Tuple[str, ...] = SIDES_DEFAULT,
    tp_pct_grid: Tuple[float, ...] = TP_PCT_GRID,
    n_estimators: int = 300,
    n_splits: int = 5,
    min_train_splits: int = 2,
    out_base: Path = OUT_CLASSIFIER_BASE,
) -> Dict[str, CombinationClassifierSummary]:
    """8 組合せ (K × side) × 5 fold = 40 TP 約定率 Classifier 学習統合.

    起動時 assertion: artifact_path に train_2021_2024 含み test 含まない (§8.4 (v))
    """
    # §8.4 (v) 起動時 assertion (parquet path 経由・leak verify)
    parquet_path = Path(parquet_path)
    parquet_str = str(parquet_path.resolve())
    # smoke 時の sample.parquet は train_2021_2024 を含まないため
    # smoke では assertion を skip (parquet 名で判定)
    is_full = "train_2021_2024" in parquet_path.name
    is_smoke = "sample" in parquet_path.name
    if not is_smoke:
        # full mode 想定
        assert "train_2021_2024" in parquet_str, (
            f"§8.4 (v) leak verify: parquet path must contain 'train_2021_2024': {parquet_str}"
        )
    assert "test" not in parquet_path.name, (
        f"§8.4 (v) leak verify: parquet must not be test*: {parquet_path.name}"
    )

    t_start = time.time()
    print(f"\n=== TP 約定率 Classifier 学習開始 (Step I-2.1) ===")
    print(f"parquet: {parquet_path}")
    print(f"K values: {k_values} / sides: {sides}")
    print(f"TP_PCT grid: {tp_pct_grid} ({len(tp_pct_grid)} 段階・特徴量化)")
    print(f"n_estimators: {n_estimators}")
    print(f"n_splits: {n_splits} / min_train_splits: {min_train_splits}")
    print(f"out_base: {out_base}")

    out_base.mkdir(parents=True, exist_ok=True)

    # 1. parquet load + blacklist drop + label 分離
    X, y_dict, idx = load_parquet_with_blacklist(parquet_path)
    print(f"X shape: {X.shape} / index range: {idx[0]} ~ {idx[-1]}")
    # MFE_pct ラベル存在 verify
    for side in sides:
        prefix = f"{side}_MFE_pct"
        if prefix not in y_dict:
            raise KeyError(
                f"label prefix '{prefix}' not found in y_dict. "
                f"available: {list(y_dict.keys())}"
            )
        for K in k_values:
            col = f"{side}_MFE_pct_K{K}"
            if col not in y_dict[prefix].columns:
                raise KeyError(
                    f"label column '{col}' not found in y_dict[{prefix}]. "
                    f"columns: {list(y_dict[prefix].columns)}"
                )

    # 2. 8 組合せ × 5 fold loop
    combination_results: Dict[Tuple[int, str], List[ClassifierFoldMetrics]] = {}
    all_predictions: List[pd.DataFrame] = []
    first_combination_done = False

    for K in k_values:
        for side in sides:
            is_first = not first_combination_done
            fold_metrics, df_pred = _train_one_combination(
                K=K,
                side=side,
                X=X,
                y_dict=y_dict,
                idx=idx,
                tp_pct_grid=tp_pct_grid,
                n_estimators=n_estimators,
                n_splits=n_splits,
                min_train_splits=min_train_splits,
                out_base=out_base,
                is_first_combination=is_first,
            )
            df_pred["K"] = K
            df_pred["side"] = side
            all_predictions.append(df_pred)
            combination_results[(K, side)] = fold_metrics
            first_combination_done = True

    # 3. 組合せ別 summary
    combination_summaries: Dict[str, CombinationClassifierSummary] = {}
    for (K, side), fold_metrics in combination_results.items():
        combo_key = f"K{K}_{side}"
        combination_summaries[combo_key] = _aggregate_combination_metrics(fold_metrics)

    # 4. 全体 summary JSON 出力
    elapsed_total = time.time() - t_start
    parquet_name = parquet_path.name
    suffix = "train_2021_2024" if "train_2021_2024" in parquet_name else ("sample" if is_smoke else parquet_name.replace(".parquet", ""))
    summary_path = out_base / f"tp_hit_classifier_summary_{suffix}.json"
    summary_data = {
        "case_name": CASE_NAME,
        "parquet": parquet_name,
        "k_values": list(k_values),
        "sides": list(sides),
        "tp_pct_grid": list(tp_pct_grid),
        "n_estimators": n_estimators,
        "n_splits": n_splits,
        "elapsed_sec": elapsed_total,
        "timestamp": datetime.now().isoformat(),
        "combinations": {
            combo_key: asdict(summary)
            for combo_key, summary in combination_summaries.items()
        },
        "n_combinations_all_pass": sum(
            1 for s in combination_summaries.values() if s.all_pass
        ),
        "all_pass_combinations": [
            combo_key for combo_key, s in combination_summaries.items() if s.all_pass
        ],
        "fold_metrics": {
            f"K{K}_{side}": [asdict(m) for m in fms]
            for (K, side), fms in combination_results.items()
        },
    }
    with open(summary_path, "w") as f:
        json.dump(summary_data, f, indent=2, default=str)
    print(f"\n[save] summary JSON: {summary_path}")

    # 5. predictions parquet 出力 (case_a で apply 用)
    if all_predictions:
        df_all_pred = pd.concat(all_predictions, axis=0, ignore_index=True)
        pred_path = out_base / f"tp_hit_classifier_predictions_{suffix}.parquet"
        df_all_pred.to_parquet(pred_path, index=False)
        print(f"[save] predictions parquet: {pred_path} ({len(df_all_pred)} rows)")

    print(f"\n=== TP 約定率 Classifier 学習完了 ===")
    print(f"n_combinations: {len(combination_summaries)}")
    print(
        f"n_combinations_all_pass: {summary_data['n_combinations_all_pass']} "
        f"(AUC ≥ 0.55 + Brier ≤ 0.25 + Calib max dev ≤ 0.1)"
    )
    print(f"all_pass: {summary_data['all_pass_combinations']}")
    print(f"elapsed total: {elapsed_total/60:.1f} min")

    return combination_summaries


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Step I-2.1: TP 約定率 Classifier (Phase 4-b 前倒し設計)"
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="smoke mode: sample.parquet + K=12 LONG + TP_PCT=(0.5,) + n_estimators=50",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="full mode: train_2021_2024.parquet + K=(12,24,48,96) + LONG/SHORT + 6 TP_PCT + n_estimators=300",
    )
    parser.add_argument("--parquet", type=Path, default=None, help="parquet 明示指定")
    parser.add_argument("--n-estimators", type=int, default=None)
    parser.add_argument("--k", type=int, nargs="+", default=None)
    parser.add_argument("--side", type=str, nargs="+", default=None, choices=["LONG", "SHORT"])
    parser.add_argument(
        "--tp-pct",
        type=float,
        nargs="+",
        default=None,
        help="TP_PCT grid (% 単位・例: --tp-pct 0.3 0.5 0.8 1.2 1.8 2.5)",
    )
    parser.add_argument("--n-splits", type=int, default=5)
    parser.add_argument(
        "--min-train-splits",
        type=int,
        default=2,
        help="smoke で n_splits=3 時は 1 指定推奨",
    )
    parser.add_argument("--out-base", type=Path, default=OUT_CLASSIFIER_BASE)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    # parquet 解決
    if args.parquet:
        parquet_path = args.parquet
    elif args.smoke:
        parquet_path = PARQUET_DIR / "labels_mfe_mae_pct_sample.parquet"
    elif args.full:
        parquet_path = PARQUET_DIR / "labels_mfe_mae_pct_train_2021_2024.parquet"
    else:
        print("[ERROR] --smoke / --full / --parquet のいずれか指定必須", file=sys.stderr)
        return 2

    if not parquet_path.exists():
        print(f"[ERROR] parquet not found: {parquet_path}", file=sys.stderr)
        return 2

    # smoke / full モード別の既定値
    if args.smoke:
        k_values = tuple(args.k) if args.k else (12,)
        sides = tuple(args.side) if args.side else ("LONG",)
        tp_pct_grid = tuple(args.tp_pct) if args.tp_pct else (0.5,)
        n_estimators = args.n_estimators if args.n_estimators is not None else 50
        min_train_splits = args.min_train_splits if args.min_train_splits is not None else 1
        n_splits = args.n_splits if args.n_splits is not None else 3
    else:
        k_values = tuple(args.k) if args.k else K_DEFAULT_LIST
        sides = tuple(args.side) if args.side else SIDES_DEFAULT
        tp_pct_grid = tuple(args.tp_pct) if args.tp_pct else TP_PCT_GRID
        n_estimators = args.n_estimators if args.n_estimators is not None else 300
        min_train_splits = args.min_train_splits if args.min_train_splits is not None else 2
        n_splits = args.n_splits if args.n_splits is not None else 5

    print(f"[run] mode: {'smoke' if args.smoke else ('full' if args.full else 'explicit')}")
    print(f"[run] parquet: {parquet_path}")
    print(f"[run] k_values: {k_values} / sides: {sides} / tp_pct_grid: {tp_pct_grid}")
    print(f"[run] n_estimators: {n_estimators} / n_splits: {n_splits} / min_train_splits: {min_train_splits}")
    print(f"[run] start: {datetime.now().isoformat()}")

    try:
        summaries = train_tp_hit_classifier(
            parquet_path=parquet_path,
            k_values=k_values,
            sides=sides,
            tp_pct_grid=tp_pct_grid,
            n_estimators=n_estimators,
            n_splits=n_splits,
            min_train_splits=min_train_splits,
            out_base=args.out_base,
        )
    except Exception as e:
        import traceback
        print(f"[ERROR] {type(e).__name__}: {e}", file=sys.stderr)
        traceback.print_exc()
        return 1

    n_pass = sum(1 for s in summaries.values() if s.all_pass)
    n_total = len(summaries)
    print(f"\n[final] n_combinations_all_pass: {n_pass}/{n_total}")
    return 0 if n_pass > 0 or args.smoke else 0  # smoke は警告基準・full でも 0 で終了 (判定は summary JSON 経由)


if __name__ == "__main__":
    sys.exit(main())
