"""
run_lgbm_phase1_v5_case_e_triple_barrier.py — 案 e Triple Barrier multiclass (Phase 1 v6)

Phase 1 v6 で案 e を 8 組合せ (K=12/24/48/96 × LONG/SHORT) × 5 fold で学習し、
2 指標 (entropy_lift / TP Precision) で合否判定 (Direction Accuracy は案 c のみ)。

ラベル: Phase 0 v3.1 生成済 `triple_barrier_label_{LONG,SHORT}_K{K}` 列を使用
(値域 {-1, 0, +1} = SL first / TIME first / TP first・Lopez de Prado AFML Ch.3)。

学習方法 (phase_flow_v4 §2 L171 整合):
- objective: LightGBM multiclass (num_class=3 / SL=0 / TIME=1 / TP=2)
- 学習モデル数: 8 (K × side) × 5 fold (実 3 fold) = 24 model (案 b と同構造)
- 各 (K, side) 独立の 3 クラス分類モデル
- ハイパラ: 案 a/b/c 同等 (num_leaves=31 / learning_rate=0.05 / random_state=42)
- early_stopping=50・末尾 10% を valid

評価 (cc_ml_design_spec §1.5.1 + spec L86):
- entropy_lift > 10% (num_classes = 実際の unique class 数)
- TP Precision > 0.5 (TP class proba > 0.4 ∩ y_test == CLASS_TP)
  ⚠️ case_e の TP Precision は「学習 label と評価 label が同一」 = モデル calibration
     の自己評価。 case b/c の「外部 ground truth 比較」とは構造が異なる。

合格判定 (cc_ml_design_spec §1.5.1 L96-100):
- 8 組合せ中 6+ で 2 指標 ALL PASS → 案 e 採用候補

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
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

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
    EARLY_STOPPING_ROUNDS,
    VALID_TAIL_FRACTION,
    _build_train_valid_split,
    _check_fractal_leak,
    _get_top20_feature_importance,
)

CASE_NAME = "e_triple_barrier"
OUT_BASE_E = OUT_BASE / "_case_e_triple_barrier"

# Phase 1 v6 合格閾値 (cc_ml_design_spec §1.5.1)
ENTROPY_LIFT_THRESHOLD = 0.10
TP_PRECISION_THRESHOLD = 0.5
# cc_ml_design_spec §1.5.1 L86 案 e 0/1 化 default = +1 (TP) proba > 0.4
PROBA_THRESHOLD_DEFAULT = 0.4

# Triple Barrier 元 label {-1, 0, +1} → 0-indexed {0, 1, 2}
CLASS_SL = 0    # 元 -1
CLASS_TIME = 1  # 元  0
CLASS_TP = 2    # 元 +1 (Entry 採用対象)
NUM_CLASSES = 3

LABEL_MAP = {-1.0: CLASS_SL, 0.0: CLASS_TIME, 1.0: CLASS_TP}

LGBM_PARAMS_MULTICLASS: Dict[str, object] = {
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


@dataclass
class FoldResultTripleBarrier:
    fold_idx: int
    K: int
    side: str
    n_train: int
    n_valid: int
    n_test: int
    class_dist_train: Dict[str, float] = field(default_factory=dict)
    class_dist_test: Dict[str, float] = field(default_factory=dict)
    train_logloss: float = 0.0
    valid_logloss: float = 0.0
    test_logloss: float = 0.0
    entropy_lift_test: float = float("nan")
    tp_precision_test: float = float("nan")
    n_predicted_entry: int = 0
    n_actual_classes: int = 0
    train_start: str = ""
    train_end: str = ""
    test_start: str = ""
    test_end: str = ""
    elapsed_sec: float = 0.0


@dataclass
class ComboSummaryTripleBarrier:
    K: int
    side: str
    fold_results: List[FoldResultTripleBarrier] = field(default_factory=list)
    entropy_lift_mean: float = float("nan")
    tp_precision_mean: float = float("nan")
    pass_entropy_lift: bool = False
    pass_tp_precision: bool = False
    pass_both: bool = False


def encode_triple_barrier(y_raw: pd.Series) -> pd.Series:
    """元 {-1, 0, +1} → 0-indexed {0, 1, 2}."""
    encoded = y_raw.map(LABEL_MAP)
    if encoded.isna().any():
        raise ValueError(
            f"Unexpected triple_barrier_label values: {y_raw[encoded.isna()].unique()}"
        )
    return encoded.astype(np.int64)


def _safe_logloss_multiclass(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    class_to_col: Dict[int, int],
    eps: float = 1e-15,
) -> float:
    """multiclass logloss with class→column index mapping (case_c smoke v1 fix 流用)."""
    yp = np.clip(y_proba, eps, 1.0 - eps)
    n = len(y_true)
    col_indices = np.array(
        [class_to_col.get(int(c), -1) for c in y_true], dtype=np.int64
    )
    valid = col_indices >= 0
    safe_idx = np.where(valid, col_indices, 0)
    log_probs = np.where(
        valid,
        np.log(yp[np.arange(n), safe_idx]),
        np.log(eps),
    )
    return float(-log_probs.mean())


def _train_multiclass_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_valid: pd.DataFrame,
    y_valid: pd.Series,
    n_estimators: int,
) -> Tuple[lgb.LGBMClassifier, Dict[int, int], float, float]:
    """LGBMClassifier multiclass 1 model 学習 + class_to_col + train/valid logloss."""
    params = dict(LGBM_PARAMS_MULTICLASS)
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

    pred_train_proba = model.predict_proba(X_train)
    train_logloss = _safe_logloss_multiclass(
        y_train.values, pred_train_proba, class_to_col
    )
    if hasattr(model, "best_score_") and model.best_score_:
        valid_logloss = float(
            model.best_score_["valid_0"].get("multi_logloss", float("nan"))
        )
        if np.isnan(valid_logloss):
            pred_valid_proba = model.predict_proba(X_valid)
            valid_logloss = _safe_logloss_multiclass(
                y_valid.values, pred_valid_proba, class_to_col
            )
    else:
        pred_valid_proba = model.predict_proba(X_valid)
        valid_logloss = _safe_logloss_multiclass(
            y_valid.values, pred_valid_proba, class_to_col
        )
    return model, class_to_col, train_logloss, valid_logloss


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
) -> FoldResultTripleBarrier:
    """1 fold × 1 (K, side) combo の学習 + 2 指標評価."""
    train_idx_inner, valid_idx = _build_train_valid_split(
        train_idx, VALID_TAIL_FRACTION
    )

    X_tr = X.iloc[train_idx_inner]
    X_va = X.iloc[valid_idx]
    X_te = X.iloc[test_idx]

    tb_col = f"triple_barrier_label_{side}_K{K}"
    y_all = encode_triple_barrier(y_dict["triple_barrier_label"][tb_col])
    y_tr = y_all.iloc[train_idx_inner]
    y_va = y_all.iloc[valid_idx]
    y_te = y_all.iloc[test_idx]

    def _class_dist(s: pd.Series) -> Dict[str, float]:
        total = len(s)
        return {
            "SL": float((s == CLASS_SL).sum() / total),
            "TIME": float((s == CLASS_TIME).sum() / total),
            "TP": float((s == CLASS_TP).sum() / total),
        }

    dist_tr = _class_dist(y_tr)
    dist_te = _class_dist(y_te)

    print(
        f"  K={K} side={side} fold {fold_idx}: "
        f"n_train_inner={len(train_idx_inner)} n_valid={len(valid_idx)} n_test={len(test_idx)}"
    )
    print(
        f"    class_dist_tr: SL={dist_tr['SL']:.3f} TIME={dist_tr['TIME']:.3f} "
        f"TP={dist_tr['TP']:.3f}"
    )

    t0 = time.time()
    model, class_to_col, train_logloss, valid_logloss = _train_multiclass_model(
        X_tr, y_tr, X_va, y_va, n_estimators
    )
    elapsed = time.time() - t0

    pred_te_proba = model.predict_proba(X_te)
    test_logloss = _safe_logloss_multiclass(
        y_te.values, pred_te_proba, class_to_col
    )
    n_actual_classes = len(class_to_col)
    if n_actual_classes >= 2:
        baseline_ll = float(np.log(n_actual_classes))
        entropy_lift = 1.0 - test_logloss / baseline_ll
    else:
        entropy_lift = float("nan")

    # TP Precision: TP class proba > 0.4 ∩ y_test == CLASS_TP
    if CLASS_TP in class_to_col:
        col_tp = class_to_col[CLASS_TP]
        p_tp = pred_te_proba[:, col_tp]
        pred_entry = p_tp > PROBA_THRESHOLD_DEFAULT
        n_pred = int(pred_entry.sum())
        if n_pred == 0:
            tp_precision = float("nan")
        else:
            tp_correct = (y_te.values == CLASS_TP)
            tp_precision = float((pred_entry & tp_correct).sum() / n_pred)
    else:
        n_pred = 0
        tp_precision = float("nan")

    fi_top20 = _get_top20_feature_importance(model, X.columns.tolist())
    if is_first_label:
        early_fi_dir = out_base / "_early_fi_for_guard_review"
        early_fi_dir.mkdir(parents=True, exist_ok=True)
        early_fi_path = early_fi_dir / f"fi_top20_K{K}_{side}_TRIPLE_BARRIER.csv"
        fi_top20.to_csv(early_fi_path, index=False)
        print(f"[guard early save] {early_fi_path}")
        _check_fractal_leak(
            fi_top20,
            K,
            side,
            target="TRIPLE_BARRIER",
            parquet_df=X,
            importance_csv_path=early_fi_path,
            full_rank_dir=early_fi_dir,
        )

    train_ts = index[train_idx_inner]
    test_ts = index[test_idx]

    print(
        f"    elapsed={elapsed:.1f}s "
        f"train_ll={train_logloss:.4f} valid_ll={valid_logloss:.4f} "
        f"test_ll={test_logloss:.4f} entropy_lift={entropy_lift:.3f} "
        f"tp_precision={tp_precision:.3f} (n_pred={n_pred})"
    )

    return FoldResultTripleBarrier(
        fold_idx=fold_idx,
        K=K,
        side=side,
        n_train=len(train_idx_inner),
        n_valid=len(valid_idx),
        n_test=len(test_idx),
        class_dist_train=dist_tr,
        class_dist_test=dist_te,
        train_logloss=train_logloss,
        valid_logloss=valid_logloss,
        test_logloss=test_logloss,
        entropy_lift_test=float(entropy_lift),
        tp_precision_test=tp_precision,
        n_predicted_entry=n_pred,
        n_actual_classes=n_actual_classes,
        train_start=str(train_ts[0]) if len(train_ts) > 0 else "",
        train_end=str(train_ts[-1]) if len(train_ts) > 0 else "",
        test_start=str(test_ts[0]) if len(test_ts) > 0 else "",
        test_end=str(test_ts[-1]) if len(test_ts) > 0 else "",
        elapsed_sec=elapsed,
    )


def train_case_e_triple_barrier(
    parquet_path: Path,
    k_values: Tuple[int, ...] = K_DEFAULT_LIST,
    sides: Tuple[str, ...] = SIDES_DEFAULT,
    n_splits: int = 5,
    min_train_splits: int = 2,
    n_estimators: int = 1000,
    out_base: Path = OUT_BASE_E,
) -> Dict[str, ComboSummaryTripleBarrier]:
    """8 (K × side) × 5 fold で案 e triple barrier 学習 + 2 指標評価."""
    out_base.mkdir(parents=True, exist_ok=True)
    t_start = time.time()
    print("\n=== case_e triple_barrier 開始 (Phase 1 v6・2 指標・Direction Accuracy 非適用) ===")
    print(f"parquet: {parquet_path}")
    print(
        f"k={k_values} sides={sides} n_splits={n_splits} "
        f"n_estimators={n_estimators} early_stopping={EARLY_STOPPING_ROUNDS}"
    )
    print(f"lightgbm: {lgb.__version__}")
    print(
        f"閾値: entropy_lift > {ENTROPY_LIFT_THRESHOLD} / "
        f"tp_precision > {TP_PRECISION_THRESHOLD} / "
        f"proba_threshold (TP class) = {PROBA_THRESHOLD_DEFAULT}"
    )

    X, y_dict, idx = load_parquet_with_blacklist(parquet_path)
    print(f"X shape: {X.shape} / index range: {idx[0]} ~ {idx[-1]}")

    cv = prepare_purged_cv(n_splits=n_splits, min_train_splits=min_train_splits)
    all_combos: Dict[str, ComboSummaryTripleBarrier] = {}
    first_label_done = False

    for K in k_values:
        for side in sides:
            combo_key = f"K{K}_{side}"
            print(f"\n--- 組合せ {combo_key} ---")
            combo_summary = ComboSummaryTripleBarrier(K=K, side=side)

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

            els = [
                r.entropy_lift_test
                for r in combo_summary.fold_results
                if not np.isnan(r.entropy_lift_test)
            ]
            tps = [
                r.tp_precision_test
                for r in combo_summary.fold_results
                if not np.isnan(r.tp_precision_test)
            ]
            combo_summary.entropy_lift_mean = float(np.mean(els)) if els else float("nan")
            combo_summary.tp_precision_mean = float(np.mean(tps)) if tps else float("nan")
            combo_summary.pass_entropy_lift = (
                combo_summary.entropy_lift_mean > ENTROPY_LIFT_THRESHOLD
            )
            combo_summary.pass_tp_precision = (
                combo_summary.tp_precision_mean > TP_PRECISION_THRESHOLD
            )
            combo_summary.pass_both = (
                combo_summary.pass_entropy_lift and combo_summary.pass_tp_precision
            )

            print(
                f"  {combo_key} 集約: "
                f"el={combo_summary.entropy_lift_mean:.3f}(p={combo_summary.pass_entropy_lift}) "
                f"tp={combo_summary.tp_precision_mean:.3f}(p={combo_summary.pass_tp_precision}) "
                f"pass_both={combo_summary.pass_both}"
            )
            all_combos[combo_key] = combo_summary

    elapsed_total = time.time() - t_start
    n_combos_pass_both = sum(1 for c in all_combos.values() if c.pass_both)
    summary_data: Dict[str, object] = {
        "case_name": CASE_NAME,
        "parquet": parquet_path.name,
        "k_values": list(k_values),
        "sides": list(sides),
        "n_splits": n_splits,
        "n_estimators_max": n_estimators,
        "early_stopping_rounds": EARLY_STOPPING_ROUNDS,
        "lightgbm_version": lgb.__version__,
        "entropy_lift_threshold": ENTROPY_LIFT_THRESHOLD,
        "tp_precision_threshold": TP_PRECISION_THRESHOLD,
        "proba_threshold_tp": PROBA_THRESHOLD_DEFAULT,
        "label_definition": (
            "triple_barrier_label_{side}_K{K} (Phase 0 v3.1 生成済). "
            "SL=0 (元 -1) / TIME=1 (元 0) / TP=2 (元 +1・Entry 採用対象)."
        ),
        "combos": {
            k: {
                "K": v.K,
                "side": v.side,
                "entropy_lift_mean": v.entropy_lift_mean,
                "tp_precision_mean": v.tp_precision_mean,
                "pass_entropy_lift": v.pass_entropy_lift,
                "pass_tp_precision": v.pass_tp_precision,
                "pass_both": v.pass_both,
                "folds": [asdict(r) for r in v.fold_results],
            }
            for k, v in all_combos.items()
        },
        "combos_pass_both": n_combos_pass_both,
        "n_combos_total": len(all_combos),
        "phase1_v6_overall_pass": n_combos_pass_both >= 6,
        "elapsed_sec": elapsed_total,
        "timestamp": datetime.now().isoformat(),
    }
    summary_path = out_base / f"case_e_triple_barrier_summary_{parquet_path.stem}.json"
    summary_path.write_text(
        json.dumps(summary_data, indent=2, ensure_ascii=False, default=str)
    )

    print("\n=== case_e 完了 ===")
    print(f"elapsed_total: {elapsed_total:.1f}s ({elapsed_total/60:.1f} min)")
    print(
        f"combos_pass_both: {n_combos_pass_both}/{len(all_combos)} "
        f"(>= 6 で Phase 1 v6 案 e 採用候補)"
    )
    print(f"summary saved: {summary_path}")
    return all_combos


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="case_e triple_barrier (Phase 1 v6・2 指標・Direction Accuracy 非適用)"
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

    train_case_e_triple_barrier(
        parquet_path=parquet_path,
        k_values=k_values,
        sides=sides,
        n_estimators=n_estimators,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
