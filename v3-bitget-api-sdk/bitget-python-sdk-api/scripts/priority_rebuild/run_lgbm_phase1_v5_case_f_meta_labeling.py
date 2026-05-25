"""
run_lgbm_phase1_v5_case_f_meta_labeling.py — 案 f Meta-Labeling 2 段階 (Phase 1 v6)

Phase 1 v6 で案 f を 8 組合せ × 5 fold で学習し、final_tp_precision で合否判定。
Lopez de Prado AFML Ch.3 「Meta-Labeling」標準実装:
  Primary (Triple Barrier multiclass・案 e と同じ) で Entry signal を出し、
  Secondary (binary classifier) で「primary entry の質」を判定。
  Final entry = Primary entry AND Secondary > 0.6 (cc_ml_design_spec L86).

学習方法 (phase_flow_v4 §2 L172 + cc_ml_design_spec §1.5.1 L86):
- Primary: 案 e と同じ (Triple Barrier multiclass・SL=0/TIME=1/TP=2)
- Secondary: binary (meta_label = 1 if TP first else 0・Phase 0 v3.1 生成済)
- 学習モデル数: 2 model × 8 (K, side) × 5 fold (実 3 fold) = 48 model
- Secondary 学習データ: Primary-predicted-entry の subset のみ (= フィルタ後)
- ハイパラ: 案 a/b/c/e 同等 (num_leaves=31 / learning_rate=0.05 / random_state=42)
- early_stopping=50・末尾 10% を valid

評価 (cc_ml_design_spec §1.5.1):
- primary_tp_precision: case_e と同じ (TP class proba > 0.4 で TB == +1 率) — 参考
- **final_tp_precision**: (Primary entry ∩ Secondary > 0.6) で TB == +1 率 (主指標)
- precision_lift: final - primary (Meta-Labeling の効果計測)

合格判定:
- 8 組合せ中 6+ で final_tp_precision > 0.5 → 案 f 採用候補

CLI:
- --smoke: sample.parquet / K=12 LONG / n_estimators=50
- --full: train_2021_2024.parquet / 8 組合せ / n_estimators=1000
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

import lightgbm as lgb
from sklearn.model_selection import TimeSeriesSplit

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
    EARLY_STOPPING_ROUNDS,
    VALID_TAIL_FRACTION,
    _build_train_valid_split,
    _check_fractal_leak,
    _get_top20_feature_importance,
)

CASE_NAME = "f_meta_labeling"
OUT_BASE_F = OUT_BASE / "_case_f_meta_labeling"

# Phase 1 v6 合格閾値 (cc_ml_design_spec §1.5.1)
TP_PRECISION_THRESHOLD = 0.5

# Primary (Triple Barrier multiclass) 設定 — 案 e と同じ
PRIMARY_PROBA_THRESHOLD = 0.4  # TP class proba > 0.4 で primary entry
CLASS_SL = 0    # 元 -1
CLASS_TIME = 1  # 元  0
CLASS_TP = 2    # 元 +1
NUM_CLASSES = 3
TRIPLE_BARRIER_MAP = {-1.0: CLASS_SL, 0.0: CLASS_TIME, 1.0: CLASS_TP}

# Secondary (binary meta-labeler) 設定 — cc_ml_design_spec L86 案 f
SECONDARY_PROBA_THRESHOLD = 0.6

# AFML Ch.3 (Lopez de Prado) + Hudson & Thames mlfinlab 標準実装:
# Primary を inner TimeSeriesSplit で out-of-fold predict → Secondary 学習データ生成
# (in-sample contamination 防止・監査 §6 提案 1 反映・2026-05-25 修正)
INNER_CV_N_SPLITS = 3

LGBM_PARAMS_PRIMARY: Dict[str, object] = {
    "objective": "multiclass",
    "num_class": NUM_CLASSES,
    "metric": "multi_logloss",
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

LGBM_PARAMS_SECONDARY: Dict[str, object] = {
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


@dataclass
class FoldResultMetaLabeling:
    fold_idx: int
    K: int
    side: str
    n_train_inner: int
    n_valid: int
    n_test: int
    # Primary stats
    primary_class_dist_train: Dict[str, float] = field(default_factory=dict)
    primary_entry_train_count: int = 0
    primary_entry_test_count: int = 0
    primary_tp_precision_test: float = float("nan")
    primary_elapsed_sec: float = 0.0
    # Secondary stats
    secondary_n_train: int = 0  # Primary-entry train samples
    secondary_positive_rate_train: float = float("nan")  # meta_label==1 率
    secondary_elapsed_sec: float = 0.0
    secondary_classes_present: bool = True
    # Final (Meta-Labeling 結果)
    final_entry_count: int = 0
    final_tp_precision: float = float("nan")
    precision_lift: float = float("nan")  # final - primary
    train_start: str = ""
    train_end: str = ""
    test_start: str = ""
    test_end: str = ""


@dataclass
class ComboSummaryMetaLabeling:
    K: int
    side: str
    fold_results: List[FoldResultMetaLabeling] = field(default_factory=list)
    primary_tp_precision_mean: float = float("nan")
    final_tp_precision_mean: float = float("nan")
    precision_lift_mean: float = float("nan")
    pass_final_tp_precision: bool = False


def encode_triple_barrier(y_raw: pd.Series) -> pd.Series:
    """{-1, 0, +1} → {0, 1, 2}."""
    encoded = y_raw.map(TRIPLE_BARRIER_MAP)
    if encoded.isna().any():
        raise ValueError(
            f"Unexpected triple_barrier values: {y_raw[encoded.isna()].unique()}"
        )
    return encoded.astype(np.int64)


def _train_primary_multiclass(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_valid: pd.DataFrame,
    y_valid: pd.Series,
    n_estimators: int,
) -> Tuple[lgb.LGBMClassifier, Dict[int, int]]:
    """Primary: Triple Barrier multiclass (案 e と同等)."""
    params = dict(LGBM_PARAMS_PRIMARY)
    params["n_estimators"] = n_estimators

    model = lgb.LGBMClassifier(**params)
    model.fit(
        X_train,
        y_train,
        eval_set=[(X_valid, y_valid)],
        eval_metric="multi_logloss",
        callbacks=[lgb.early_stopping(EARLY_STOPPING_ROUNDS, verbose=False)],
    )
    class_to_col = {int(c): i for i, c in enumerate(model.classes_)}
    return model, class_to_col


def _get_primary_entry_mask(
    model: lgb.LGBMClassifier,
    class_to_col: Dict[int, int],
    X: pd.DataFrame,
    proba_threshold: float = PRIMARY_PROBA_THRESHOLD,
) -> np.ndarray:
    """Primary が TP class proba > threshold と判定した sample mask (boolean array)."""
    if CLASS_TP not in class_to_col:
        return np.zeros(len(X), dtype=bool)
    pred_proba = model.predict_proba(X)
    col_tp = class_to_col[CLASS_TP]
    return pred_proba[:, col_tp] > proba_threshold


def _generate_oof_primary_entry_mask(
    X_tr: pd.DataFrame,
    y_tb_tr: pd.Series,
    n_estimators: int,
    proba_threshold: float = PRIMARY_PROBA_THRESHOLD,
    n_inner_splits: int = INNER_CV_N_SPLITS,
) -> np.ndarray:
    """Inner TimeSeriesSplit で Primary out-of-fold predict → entry mask 生成.

    AFML Ch.3 + Hudson & Thames mlfinlab 標準: Primary を CV out-of-fold で
    predict することで、Secondary 学習データを primary in-sample contamination
    から保護する (= primary が secondary の学習データを「未来情報」として
    見ない構造)。

    最初の inner fold の train_size 未満は predict 不能 (TimeSeriesSplit 仕様)
    のため False mask = primary entry 対象外 (安全側) として扱う。
    """
    n = len(X_tr)
    oof_p_tp = np.full(n, np.nan, dtype=np.float64)

    tscv = TimeSeriesSplit(n_splits=n_inner_splits)

    for inner_train_idx, inner_test_idx in tscv.split(X_tr):
        train_idx_fit, valid_idx_fit = _build_train_valid_split(
            inner_train_idx, VALID_TAIL_FRACTION
        )
        X_inner_fit = X_tr.iloc[train_idx_fit]
        y_inner_fit = y_tb_tr.iloc[train_idx_fit]
        X_inner_va = X_tr.iloc[valid_idx_fit]
        y_inner_va = y_tb_tr.iloc[valid_idx_fit]
        X_inner_te = X_tr.iloc[inner_test_idx]

        inner_model, inner_class_to_col = _train_primary_multiclass(
            X_inner_fit, y_inner_fit, X_inner_va, y_inner_va, n_estimators
        )

        if CLASS_TP in inner_class_to_col:
            inner_proba = inner_model.predict_proba(X_inner_te)
            col_tp = inner_class_to_col[CLASS_TP]
            oof_p_tp[inner_test_idx] = inner_proba[:, col_tp]

    # NaN (= 最初の inner fold 前) は False (= primary entry 対象外)
    return np.where(np.isnan(oof_p_tp), False, oof_p_tp > proba_threshold)


def _train_secondary_binary(
    X_train_filtered: pd.DataFrame,
    y_train_filtered: pd.Series,
    X_valid_filtered: pd.DataFrame,
    y_valid_filtered: pd.Series,
    n_estimators: int,
    scale_pos_weight: float,
) -> Optional[lgb.LGBMClassifier]:
    """Secondary: binary classifier on primary-entry filtered subset.

    Returns None if filtered training data has < 2 classes (can't train binary).
    """
    if y_train_filtered.nunique() < 2:
        return None
    params = dict(LGBM_PARAMS_SECONDARY)
    params["n_estimators"] = n_estimators
    params["scale_pos_weight"] = scale_pos_weight

    model = lgb.LGBMClassifier(**params)
    fit_kwargs: Dict[str, object] = {
        "callbacks": [lgb.early_stopping(EARLY_STOPPING_ROUNDS, verbose=False)],
        "eval_metric": "binary_logloss",
    }
    if len(X_valid_filtered) > 0 and y_valid_filtered.nunique() >= 2:
        fit_kwargs["eval_set"] = [(X_valid_filtered, y_valid_filtered)]
    model.fit(X_train_filtered, y_train_filtered, **fit_kwargs)
    return model


def _process_fold_combo(
    fold_idx: int,
    K: int,
    side: str,
    X: pd.DataFrame,
    y_dict: Dict[str, pd.DataFrame],
    index: pd.DatetimeIndex,
    train_idx: np.ndarray,
    test_idx: np.ndarray,
    n_estimators: int,
    out_base: Path,
    is_first_label: bool,
) -> FoldResultMetaLabeling:
    """1 fold × 1 (K, side) combo の Meta-Labeling 学習 + 評価."""
    train_idx_inner, valid_idx = _build_train_valid_split(
        train_idx, VALID_TAIL_FRACTION
    )

    X_tr = X.iloc[train_idx_inner]
    X_va = X.iloc[valid_idx]
    X_te = X.iloc[test_idx]

    # Triple Barrier ラベル (Primary 用・encode)
    tb_col = f"triple_barrier_label_{side}_K{K}"
    y_tb_all = encode_triple_barrier(y_dict["triple_barrier_label"][tb_col])
    y_tb_tr = y_tb_all.iloc[train_idx_inner]
    y_tb_va = y_tb_all.iloc[valid_idx]
    y_tb_te = y_tb_all.iloc[test_idx]

    # Meta-label (Secondary 用・pre-built・0/1)
    ml_col = f"meta_label_{side}_K{K}"
    y_ml_all = y_dict["meta_label"][ml_col].astype(np.int64)
    y_ml_tr = y_ml_all.iloc[train_idx_inner]
    y_ml_va = y_ml_all.iloc[valid_idx]

    # 元 TB raw value (== +1 判定用・TP first 正解)
    y_tb_raw_te = y_dict["triple_barrier_label"][tb_col].iloc[test_idx].values

    def _class_dist(s: pd.Series) -> Dict[str, float]:
        total = len(s)
        return {
            "SL": float((s == CLASS_SL).sum() / total),
            "TIME": float((s == CLASS_TIME).sum() / total),
            "TP": float((s == CLASS_TP).sum() / total),
        }

    dist_tr_primary = _class_dist(y_tb_tr)

    print(
        f"\n  K={K} side={side} fold {fold_idx}: "
        f"n_train_inner={len(train_idx_inner)} n_valid={len(valid_idx)} n_test={len(test_idx)}"
    )
    print(
        f"    [primary] class_dist_tr: SL={dist_tr_primary['SL']:.3f} "
        f"TIME={dist_tr_primary['TIME']:.3f} TP={dist_tr_primary['TP']:.3f}"
    )

    # ----- Step 1: Primary 学習 -----
    t0 = time.time()
    primary_model, class_to_col = _train_primary_multiclass(
        X_tr, y_tb_tr, X_va, y_tb_va, n_estimators
    )
    primary_elapsed = time.time() - t0

    # Primary feature_importance + fractal guard (1 label 目のみ)
    fi_top20 = _get_top20_feature_importance(primary_model, X.columns.tolist())
    if is_first_label:
        early_fi_dir = out_base / "_early_fi_for_guard_review"
        early_fi_dir.mkdir(parents=True, exist_ok=True)
        early_fi_path = early_fi_dir / f"fi_top20_K{K}_{side}_META_PRIMARY.csv"
        fi_top20.to_csv(early_fi_path, index=False)
        print(f"[guard early save] {early_fi_path}")
        _check_fractal_leak(
            fi_top20,
            K,
            side,
            target="META_PRIMARY",
            parquet_df=X,
            importance_csv_path=early_fi_path,
            full_rank_dir=early_fi_dir,
        )

    # Primary entry mask:
    # - train: OOF (inner TimeSeriesSplit) で in-sample contamination 回避 (AFML 標準)
    # - valid/test: final primary model (train_inner 全体で fit) で predict
    primary_entry_train = _generate_oof_primary_entry_mask(
        X_tr, y_tb_tr, n_estimators
    )
    primary_entry_valid = _get_primary_entry_mask(primary_model, class_to_col, X_va)
    primary_entry_test = _get_primary_entry_mask(primary_model, class_to_col, X_te)

    n_pe_tr = int(primary_entry_train.sum())
    n_pe_te = int(primary_entry_test.sum())

    # primary_tp_precision (案 e と同等・参考)
    if n_pe_te == 0:
        primary_tp_precision = float("nan")
    else:
        primary_tp_correct = (y_tb_te.values == CLASS_TP)
        primary_tp_precision = float(
            (primary_entry_test & primary_tp_correct).sum() / n_pe_te
        )

    print(
        f"    [primary] elapsed={primary_elapsed:.1f}s "
        f"entry_train={n_pe_tr} entry_test={n_pe_te} "
        f"tp_precision={primary_tp_precision:.3f}"
    )

    # ----- Step 2: Secondary 学習 (filtered subset) -----
    X_tr_filtered = X_tr.iloc[primary_entry_train]
    y_ml_tr_filtered = y_ml_tr.iloc[primary_entry_train]
    X_va_filtered = X_va.iloc[primary_entry_valid]
    y_ml_va_filtered = y_ml_va.iloc[primary_entry_valid]

    secondary_n_train = len(X_tr_filtered)
    if secondary_n_train < 10:
        # primary entry がほぼゼロ → Secondary 学習不能
        print(
            f"    [secondary] SKIP: filtered train size={secondary_n_train} too small"
        )
        return FoldResultMetaLabeling(
            fold_idx=fold_idx,
            K=K,
            side=side,
            n_train_inner=len(train_idx_inner),
            n_valid=len(valid_idx),
            n_test=len(test_idx),
            primary_class_dist_train=dist_tr_primary,
            primary_entry_train_count=n_pe_tr,
            primary_entry_test_count=n_pe_te,
            primary_tp_precision_test=primary_tp_precision,
            primary_elapsed_sec=primary_elapsed,
            secondary_n_train=secondary_n_train,
            secondary_classes_present=False,
            final_entry_count=0,
            train_start=str(index[train_idx_inner][0])
            if len(train_idx_inner) > 0 else "",
            train_end=str(index[train_idx_inner][-1])
            if len(train_idx_inner) > 0 else "",
            test_start=str(index[test_idx][0]) if len(test_idx) > 0 else "",
            test_end=str(index[test_idx][-1]) if len(test_idx) > 0 else "",
        )

    pos_rate_secondary = float(y_ml_tr_filtered.mean())
    n_neg = int((y_ml_tr_filtered == 0).sum())
    n_pos = int((y_ml_tr_filtered == 1).sum())
    scale_pos_weight = float(n_neg / max(n_pos, 1))

    print(
        f"    [secondary] n_train_filtered={secondary_n_train} "
        f"pos_rate={pos_rate_secondary:.3f} spw={scale_pos_weight:.2f}"
    )

    t1 = time.time()
    secondary_model = _train_secondary_binary(
        X_tr_filtered,
        y_ml_tr_filtered,
        X_va_filtered,
        y_ml_va_filtered,
        n_estimators,
        scale_pos_weight,
    )
    secondary_elapsed = time.time() - t1

    if secondary_model is None:
        print(f"    [secondary] SKIP: filtered y has only 1 class")
        return FoldResultMetaLabeling(
            fold_idx=fold_idx,
            K=K,
            side=side,
            n_train_inner=len(train_idx_inner),
            n_valid=len(valid_idx),
            n_test=len(test_idx),
            primary_class_dist_train=dist_tr_primary,
            primary_entry_train_count=n_pe_tr,
            primary_entry_test_count=n_pe_te,
            primary_tp_precision_test=primary_tp_precision,
            primary_elapsed_sec=primary_elapsed,
            secondary_n_train=secondary_n_train,
            secondary_positive_rate_train=pos_rate_secondary,
            secondary_elapsed_sec=secondary_elapsed,
            secondary_classes_present=False,
            final_entry_count=0,
            train_start=str(index[train_idx_inner][0])
            if len(train_idx_inner) > 0 else "",
            train_end=str(index[train_idx_inner][-1])
            if len(train_idx_inner) > 0 else "",
            test_start=str(index[test_idx][0]) if len(test_idx) > 0 else "",
            test_end=str(index[test_idx][-1]) if len(test_idx) > 0 else "",
        )

    # ----- Step 3: Final entry = primary & (secondary > 0.6) -----
    X_te_filtered = X_te.iloc[primary_entry_test]
    if len(X_te_filtered) == 0:
        final_tp_precision = float("nan")
        n_final = 0
    else:
        sec_proba = secondary_model.predict_proba(X_te_filtered)[:, 1]
        keep_mask = sec_proba > SECONDARY_PROBA_THRESHOLD

        # Final entry mask in full test index space
        final_entry_test = np.zeros(len(X_te), dtype=bool)
        # primary_entry_test indices → keep_mask
        pe_test_indices = np.where(primary_entry_test)[0]
        kept_indices = pe_test_indices[keep_mask]
        final_entry_test[kept_indices] = True

        n_final = int(final_entry_test.sum())
        if n_final == 0:
            final_tp_precision = float("nan")
        else:
            tp_correct = (y_tb_raw_te == 1.0)
            final_tp_precision = float(
                (final_entry_test & tp_correct).sum() / n_final
            )

    precision_lift = final_tp_precision - primary_tp_precision

    print(
        f"    [secondary] elapsed={secondary_elapsed:.1f}s "
        f"final_entry={n_final} final_tp_precision={final_tp_precision:.3f} "
        f"lift={precision_lift:+.3f}"
    )

    return FoldResultMetaLabeling(
        fold_idx=fold_idx,
        K=K,
        side=side,
        n_train_inner=len(train_idx_inner),
        n_valid=len(valid_idx),
        n_test=len(test_idx),
        primary_class_dist_train=dist_tr_primary,
        primary_entry_train_count=n_pe_tr,
        primary_entry_test_count=n_pe_te,
        primary_tp_precision_test=primary_tp_precision,
        primary_elapsed_sec=primary_elapsed,
        secondary_n_train=secondary_n_train,
        secondary_positive_rate_train=pos_rate_secondary,
        secondary_elapsed_sec=secondary_elapsed,
        secondary_classes_present=True,
        final_entry_count=n_final,
        final_tp_precision=final_tp_precision,
        precision_lift=precision_lift,
        train_start=str(index[train_idx_inner][0])
        if len(train_idx_inner) > 0 else "",
        train_end=str(index[train_idx_inner][-1])
        if len(train_idx_inner) > 0 else "",
        test_start=str(index[test_idx][0]) if len(test_idx) > 0 else "",
        test_end=str(index[test_idx][-1]) if len(test_idx) > 0 else "",
    )


def train_case_f_meta_labeling(
    parquet_path: Path,
    k_values: Tuple[int, ...] = K_DEFAULT_LIST,
    sides: Tuple[str, ...] = SIDES_DEFAULT,
    n_splits: int = 5,
    min_train_splits: int = 2,
    n_estimators: int = 1000,
    out_base: Path = OUT_BASE_F,
) -> Dict[str, ComboSummaryMetaLabeling]:
    """8 (K × side) × 5 fold で案 f Meta-Labeling 学習 + final_tp_precision 評価."""
    out_base.mkdir(parents=True, exist_ok=True)
    t_start = time.time()
    print("\n=== case_f meta_labeling 開始 (Phase 1 v6・final_tp_precision 主指標) ===")
    print(f"parquet: {parquet_path}")
    print(
        f"k={k_values} sides={sides} n_splits={n_splits} "
        f"n_estimators={n_estimators} early_stopping={EARLY_STOPPING_ROUNDS}"
    )
    print(f"lightgbm: {lgb.__version__}")
    print(
        f"閾値: final_tp_precision > {TP_PRECISION_THRESHOLD} "
        f"/ primary_proba > {PRIMARY_PROBA_THRESHOLD} "
        f"/ secondary_proba > {SECONDARY_PROBA_THRESHOLD}"
    )

    X, y_dict, idx = load_parquet_with_blacklist(parquet_path)
    print(f"X shape: {X.shape} / index range: {idx[0]} ~ {idx[-1]}")

    cv = prepare_purged_cv(n_splits=n_splits, min_train_splits=min_train_splits)
    all_combos: Dict[str, ComboSummaryMetaLabeling] = {}
    first_label_done = False

    for K in k_values:
        for side in sides:
            combo_key = f"K{K}_{side}"
            print(f"\n--- 組合せ {combo_key} ---")
            combo_summary = ComboSummaryMetaLabeling(K=K, side=side)

            for fold_idx, (train_idx, test_idx) in enumerate(
                split_with_purging(cv, X, idx, K)
            ):
                fold_result = _process_fold_combo(
                    fold_idx=fold_idx,
                    K=K,
                    side=side,
                    X=X,
                    y_dict=y_dict,
                    index=idx,
                    train_idx=train_idx,
                    test_idx=test_idx,
                    n_estimators=n_estimators,
                    out_base=out_base,
                    is_first_label=(not first_label_done),
                )
                combo_summary.fold_results.append(fold_result)
                first_label_done = True

            primaries = [
                r.primary_tp_precision_test
                for r in combo_summary.fold_results
                if not np.isnan(r.primary_tp_precision_test)
            ]
            finals = [
                r.final_tp_precision
                for r in combo_summary.fold_results
                if not np.isnan(r.final_tp_precision)
            ]
            lifts = [
                r.precision_lift
                for r in combo_summary.fold_results
                if not np.isnan(r.precision_lift)
            ]
            combo_summary.primary_tp_precision_mean = (
                float(np.mean(primaries)) if primaries else float("nan")
            )
            combo_summary.final_tp_precision_mean = (
                float(np.mean(finals)) if finals else float("nan")
            )
            combo_summary.precision_lift_mean = (
                float(np.mean(lifts)) if lifts else float("nan")
            )
            combo_summary.pass_final_tp_precision = (
                combo_summary.final_tp_precision_mean > TP_PRECISION_THRESHOLD
            )

            print(
                f"  {combo_key} 集約: "
                f"primary_tp={combo_summary.primary_tp_precision_mean:.3f} "
                f"final_tp={combo_summary.final_tp_precision_mean:.3f}"
                f"(p={combo_summary.pass_final_tp_precision}) "
                f"lift={combo_summary.precision_lift_mean:+.3f}"
            )
            all_combos[combo_key] = combo_summary

    elapsed_total = time.time() - t_start
    n_combos_pass = sum(
        1 for c in all_combos.values() if c.pass_final_tp_precision
    )
    summary_data: Dict[str, object] = {
        "case_name": CASE_NAME,
        "parquet": parquet_path.name,
        "k_values": list(k_values),
        "sides": list(sides),
        "n_splits": n_splits,
        "n_estimators_max": n_estimators,
        "early_stopping_rounds": EARLY_STOPPING_ROUNDS,
        "lightgbm_version": lgb.__version__,
        "tp_precision_threshold": TP_PRECISION_THRESHOLD,
        "primary_proba_threshold": PRIMARY_PROBA_THRESHOLD,
        "secondary_proba_threshold": SECONDARY_PROBA_THRESHOLD,
        "label_definition": (
            "Primary: triple_barrier_label_{side}_K{K} encoded {SL=0,TIME=1,TP=2} (案 e と同じ). "
            "Secondary: meta_label_{side}_K{K} (pre-built・0/1・TP first 正解). "
            "Secondary は primary-predicted-entry filtered subset で学習."
        ),
        "combos": {
            k: {
                "K": v.K,
                "side": v.side,
                "primary_tp_precision_mean": v.primary_tp_precision_mean,
                "final_tp_precision_mean": v.final_tp_precision_mean,
                "precision_lift_mean": v.precision_lift_mean,
                "pass_final_tp_precision": v.pass_final_tp_precision,
                "folds": [asdict(r) for r in v.fold_results],
            }
            for k, v in all_combos.items()
        },
        "combos_pass": n_combos_pass,
        "n_combos_total": len(all_combos),
        "phase1_v6_overall_pass": n_combos_pass >= 6,
        "elapsed_sec": elapsed_total,
        "timestamp": datetime.now().isoformat(),
    }
    summary_path = out_base / f"case_f_meta_labeling_summary_{parquet_path.stem}.json"
    summary_path.write_text(
        json.dumps(summary_data, indent=2, ensure_ascii=False, default=str)
    )

    print("\n=== case_f 完了 ===")
    print(f"elapsed_total: {elapsed_total:.1f}s ({elapsed_total/60:.1f} min)")
    print(
        f"combos_pass (final_tp > {TP_PRECISION_THRESHOLD}): "
        f"{n_combos_pass}/{len(all_combos)} (>= 6 で Phase 1 v6 案 f 採用候補)"
    )
    print(f"summary saved: {summary_path}")
    return all_combos


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="case_f meta_labeling (Phase 1 v6・final_tp_precision 主指標)"
    )
    p.add_argument(
        "--smoke",
        action="store_true",
        help="sample.parquet / K=12 LONG / n_estimators=50",
    )
    p.add_argument(
        "--full",
        action="store_true",
        help="train_2021_2024.parquet / 8 (K, side) / n_estimators=1000",
    )
    p.add_argument(
        "--n-estimators", type=int, default=None, help="LightGBM n_estimators 上書き"
    )
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    if not (args.smoke or args.full):
        print("ERROR: --smoke or --full required", file=sys.stderr)
        return 1
    if args.smoke:
        parquet_path = PARQUET_DIR / "labels_mfe_mae_pct_sample.parquet"
        k_values: Tuple[int, ...] = (12,)
        sides: Tuple[str, ...] = ("LONG",)
        n_estimators = args.n_estimators or 50
    else:
        parquet_path = PARQUET_DIR / "labels_mfe_mae_pct_train_2021_2024.parquet"
        k_values = K_DEFAULT_LIST
        sides = SIDES_DEFAULT
        n_estimators = args.n_estimators or 1000

    train_case_f_meta_labeling(
        parquet_path=parquet_path,
        k_values=k_values,
        sides=sides,
        n_estimators=n_estimators,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
