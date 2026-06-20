"""
run_lgbm_phase1_v5_case_c_multiclass.py — 案 c Direction Multiclass (Phase 1 v6・3 指標 Exit 非依存)

Phase 1 v6 (L-217 整合) で案 c を 4 K (= 12/24/48/96) × 5 fold で
学習し、3 指標 (entropy lift / TP Precision / Direction Accuracy) で 8 組合せ評価する。

学習方法 (phase_flow_v4 §2 L189-199 整合):
- objective: LightGBM multiclass (num_class=3 / LONG=2 / SHORT=1 / Flat=0)
- 学習モデル数: 4 K × 5 fold (実 3 fold) = 12 model (案 b の 24 model から半減)
- ラベル定義 (phase_flow_v4 §2 L194 spec 通り採用・smoke v1 で Flat=0% 不具合が出たため修正):
    LONG: LONG_MFE_pct_K{K} > 0.5%
    SHORT: SHORT_MFE_pct_K{K} > 0.5%
    両方 > 0.5%: MFE 大きい方を採用
    両方 <= 0.5%: Flat
  trade-off 受容: K=12 では Flat が多く 3 クラス成立・K=96 では Flat が少なくなる
  (8 時間で 0.5% 超えやすい) が num_class=3 で対称化。spec 著者判断を CC 独自解釈より優先。
- ハイパラ: 案 a/b 同等 (num_leaves=31 / learning_rate=0.05 / random_state=42)
- early_stopping=50・末尾 10% を valid

評価 (cc_ml_design_spec §1.5.1):
- entropy_lift > 10% (compute_entropy_lift 既存・num_classes=3・K ごと 1 値・LONG/SHORT で共有)
- TP Precision > 0.5 (side class proba > 0.4 ∩ triple_barrier_label_{side}_K{K}==+1)
- Direction Accuracy > 0.55 (案 c のみ・side class proba > 0.4 ∩ true_label==side_class)

合格判定 (cc_ml_design_spec §1.5.1 L96-100):
- 8 組合せ中 6+ 組合せで 3 指標 ALL PASS → 案 c 採用候補

CLI:
- --smoke: sample.parquet / K=12 / n_estimators=50 / ~30 秒
- --full: train_2021_2024.parquet / 4 K × 3 fold / n_estimators=1000
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
    compute_entropy_lift,
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

CASE_NAME = "c_multiclass"
OUT_BASE_C = OUT_BASE / "_case_c_multiclass"

# Phase 1 v6 合格閾値 (cc_ml_design_spec §1.5.1)
ENTROPY_LIFT_THRESHOLD = 0.10
TP_PRECISION_THRESHOLD = 0.5
DIRECTION_ACCURACY_THRESHOLD = 0.55
# cc_ml_design_spec §1.5.1 L86 案 c 0/1 化 default = class proba > 0.4
PROBA_THRESHOLD_DEFAULT = 0.4
# phase_flow_v4 §2 L194 既定 (LONG/SHORT 判定の MFE 閾値・% 単位)
MFE_THRESHOLD_PCT = 0.5

# クラスエンコーディング (LightGBM multiclass は 0-indexed integer 必須)
CLASS_FLAT = 0
CLASS_SHORT = 1
CLASS_LONG = 2
NUM_CLASSES = 3
SIDE_TO_CLASS = {"LONG": CLASS_LONG, "SHORT": CLASS_SHORT}

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
class ComboResultMulticlass:
    """1 fold × 1 K × 1 side の評価結果."""

    fold_idx: int
    K: int
    side: str
    n_test: int
    n_predicted_entry: int
    side_class_rate_test: float  # true label == side クラスの割合
    entropy_lift_test: float  # K ごと 1 値・同 K の LONG/SHORT で同値
    tp_precision_test: float
    direction_accuracy_test: float


@dataclass
class FoldKResult:
    """1 fold × 1 K の学習結果 (1 multiclass model)."""

    fold_idx: int
    K: int
    n_train: int
    n_valid: int
    n_test: int
    class_dist_train: Dict[str, float] = field(default_factory=dict)  # {LONG / SHORT / Flat: ratio}
    class_dist_test: Dict[str, float] = field(default_factory=dict)
    train_logloss: float = 0.0
    valid_logloss: float = 0.0
    test_logloss: float = 0.0
    entropy_lift_test: float = float("nan")  # K ごと 1 値
    train_start: str = ""
    train_end: str = ""
    test_start: str = ""
    test_end: str = ""
    elapsed_sec: float = 0.0
    combos: List[ComboResultMulticlass] = field(default_factory=list)


@dataclass
class ComboSummaryMulticlass:
    K: int
    side: str
    fold_results: List[ComboResultMulticlass] = field(default_factory=list)
    entropy_lift_mean: float = float("nan")
    tp_precision_mean: float = float("nan")
    direction_accuracy_mean: float = float("nan")
    pass_entropy_lift: bool = False
    pass_tp_precision: bool = False
    pass_direction_accuracy: bool = False
    pass_all: bool = False


def build_multiclass_label(
    mfe_long: pd.Series,
    mfe_short: pd.Series,
    mfe_threshold_pct: float = MFE_THRESHOLD_PCT,
) -> pd.Series:
    """ラベル: LONG=2 / SHORT=1 / Flat=0 (phase_flow_v4 §2 L194 spec).

    - LONG: mfe_long > 0.5%
    - SHORT: mfe_short > 0.5%
    - 両方 > 0.5%: MFE 大きい方を採用 (tie-break)
    - 両方 <= 0.5%: Flat

    smoke v1 (CC 独自比率基準 `MFE >= |MAE|`) で Flat=0% 不具合発生 → spec 通り採用に修正。
    """
    long_ok = (mfe_long > mfe_threshold_pct).to_numpy()
    short_ok = (mfe_short > mfe_threshold_pct).to_numpy()
    long_better = (mfe_long > mfe_short).to_numpy()

    label = np.full(len(mfe_long), CLASS_FLAT, dtype=np.int64)
    long_mask = long_ok & (~short_ok | long_better)
    label[long_mask] = CLASS_LONG
    short_mask = short_ok & (~long_ok | ~long_better) & ~long_mask
    label[short_mask] = CLASS_SHORT
    return pd.Series(label, index=mfe_long.index)


def _safe_logloss_multiclass(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    class_to_col: Dict[int, int],
    eps: float = 1e-15,
) -> float:
    """multiclass logloss with class→column index mapping.

    class_to_col: model.classes_ から導出 (LightGBM の num_class=3 と actual unique class
    が乖離する edge case 対策・smoke v1 で train_logloss=17 異常事案修正)。
    """
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
        np.log(eps),  # class が学習されていない → worst case
    )
    return float(-log_probs.mean())


def _train_multiclass_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_valid: pd.DataFrame,
    y_valid: pd.Series,
    n_estimators: int,
) -> Tuple[lgb.LGBMClassifier, Dict[int, int], float, float]:
    """LGBMClassifier multiclass 1 model 学習 + class_to_col + train/valid logloss 算出."""
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

    # smoke v1 fix: model.classes_ から column index map を作る
    # (LightGBM num_class=3 + 実 unique class < 3 の edge case で proba shape と
    # class label の対応がずれる事案対策)
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


def _compute_combo_metrics(
    fold_idx: int,
    K: int,
    side: str,
    pred_test_proba: np.ndarray,
    class_to_col: Dict[int, int],
    y_test: np.ndarray,
    triple_barrier_label: np.ndarray,
    entropy_lift_K: float,
    proba_threshold: float = PROBA_THRESHOLD_DEFAULT,
) -> ComboResultMulticlass:
    """1 (K, side) の 3 指標算出 (smoke v1 fix: class_to_col で column index 動的解決)."""
    side_class = SIDE_TO_CLASS[side]
    side_class_rate_test = float((y_test == side_class).mean())

    if side_class not in class_to_col:
        # 学習データに side class が存在しない → 予測不可
        return ComboResultMulticlass(
            fold_idx=fold_idx,
            K=K,
            side=side,
            n_test=len(y_test),
            n_predicted_entry=0,
            side_class_rate_test=side_class_rate_test,
            entropy_lift_test=float(entropy_lift_K),
            tp_precision_test=float("nan"),
            direction_accuracy_test=float("nan"),
        )

    col_idx = class_to_col[side_class]
    p_side = pred_test_proba[:, col_idx]
    pred_entry = p_side > proba_threshold
    n_pred = int(pred_entry.sum())

    if n_pred == 0:
        tp_precision = float("nan")
        direction_accuracy = float("nan")
    else:
        tp_correct = triple_barrier_label == 1
        tp_precision = float((pred_entry & tp_correct).sum() / n_pred)
        direction_correct = y_test == side_class
        direction_accuracy = float((pred_entry & direction_correct).sum() / n_pred)

    return ComboResultMulticlass(
        fold_idx=fold_idx,
        K=K,
        side=side,
        n_test=len(y_test),
        n_predicted_entry=n_pred,
        side_class_rate_test=side_class_rate_test,
        entropy_lift_test=float(entropy_lift_K),
        tp_precision_test=tp_precision,
        direction_accuracy_test=direction_accuracy,
    )


def _process_fold_K(
    fold_idx: int,
    K: int,
    X: pd.DataFrame,
    y_dict: Dict[str, pd.DataFrame],
    index: pd.DatetimeIndex,
    train_idx: np.ndarray,
    test_idx: np.ndarray,
    n_estimators: int,
    out_base: Path,
    is_first_label: bool,
    sides: Tuple[str, ...],
) -> FoldKResult:
    """1 fold × 1 K の学習 + 4 side combo 評価."""
    train_idx_inner, valid_idx = _build_train_valid_split(
        train_idx, VALID_TAIL_FRACTION
    )

    X_tr = X.iloc[train_idx_inner]
    X_va = X.iloc[valid_idx]
    X_te = X.iloc[test_idx]

    mfe_long = y_dict["LONG_MFE_pct"][f"LONG_MFE_pct_K{K}"]
    mfe_short = y_dict["SHORT_MFE_pct"][f"SHORT_MFE_pct_K{K}"]
    y_all = build_multiclass_label(mfe_long, mfe_short)

    y_tr = y_all.iloc[train_idx_inner]
    y_va = y_all.iloc[valid_idx]
    y_te = y_all.iloc[test_idx]

    def _class_dist(s: pd.Series) -> Dict[str, float]:
        total = len(s)
        return {
            "LONG": float((s == CLASS_LONG).sum() / total),
            "SHORT": float((s == CLASS_SHORT).sum() / total),
            "Flat": float((s == CLASS_FLAT).sum() / total),
        }

    dist_tr = _class_dist(y_tr)
    dist_te = _class_dist(y_te)

    print(
        f"  K={K} fold {fold_idx}: "
        f"n_train_inner={len(train_idx_inner)} n_valid={len(valid_idx)} n_test={len(test_idx)}"
    )
    print(
        f"    class_dist_tr: LONG={dist_tr['LONG']:.3f} SHORT={dist_tr['SHORT']:.3f} "
        f"Flat={dist_tr['Flat']:.3f}"
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
    # entropy_lift: model.classes_ で y_true を encode してから compute_entropy_lift に渡す
    # (compute_entropy_lift 内部の log_loss が labels=[0,1,..,num_classes-1] 想定のため)
    n_actual_classes = len(class_to_col)
    if n_actual_classes >= 2:
        # 簡略実装: my safe_logloss と log(num_classes) で lift 算出 (compute_entropy_lift 同等式)
        baseline_ll = float(np.log(n_actual_classes))
        entropy_lift_K = 1.0 - test_logloss / baseline_ll
    else:
        entropy_lift_K = float("nan")

    fi_top20 = _get_top20_feature_importance(model, X.columns.tolist())
    if is_first_label:
        early_fi_dir = out_base / "_early_fi_for_guard_review"
        early_fi_dir.mkdir(parents=True, exist_ok=True)
        early_fi_path = early_fi_dir / f"fi_top20_K{K}_MULTICLASS.csv"
        fi_top20.to_csv(early_fi_path, index=False)
        print(f"[guard early save] {early_fi_path}")
        _check_fractal_leak(
            fi_top20,
            K,
            side="ALL",
            target="MULTICLASS",
            parquet_df=X,
            importance_csv_path=early_fi_path,
            full_rank_dir=early_fi_dir,
        )

    train_ts = index[train_idx_inner]
    test_ts = index[test_idx]
    fold_K = FoldKResult(
        fold_idx=fold_idx,
        K=K,
        n_train=len(train_idx_inner),
        n_valid=len(valid_idx),
        n_test=len(test_idx),
        class_dist_train=dist_tr,
        class_dist_test=dist_te,
        train_logloss=train_logloss,
        valid_logloss=valid_logloss,
        test_logloss=test_logloss,
        entropy_lift_test=float(entropy_lift_K),
        train_start=str(train_ts[0]) if len(train_ts) > 0 else "",
        train_end=str(train_ts[-1]) if len(train_ts) > 0 else "",
        test_start=str(test_ts[0]) if len(test_ts) > 0 else "",
        test_end=str(test_ts[-1]) if len(test_ts) > 0 else "",
        elapsed_sec=elapsed,
    )

    for side in sides:
        tb_col = f"triple_barrier_label_{side}_K{K}"
        tb_labels = y_dict["triple_barrier_label"][tb_col].iloc[test_idx].values
        combo_metric = _compute_combo_metrics(
            fold_idx=fold_idx,
            K=K,
            side=side,
            pred_test_proba=pred_te_proba,
            class_to_col=class_to_col,
            y_test=y_te.values,
            triple_barrier_label=tb_labels,
            entropy_lift_K=entropy_lift_K,
        )
        fold_K.combos.append(combo_metric)
        print(
            f"    side={side}: n_pred_entry={combo_metric.n_predicted_entry} "
            f"tp_precision={combo_metric.tp_precision_test:.3f} "
            f"direction_acc={combo_metric.direction_accuracy_test:.3f}"
        )

    print(
        f"    elapsed={elapsed:.1f}s "
        f"train_ll={train_logloss:.4f} valid_ll={valid_logloss:.4f} "
        f"test_ll={test_logloss:.4f} entropy_lift={entropy_lift_K:.3f}"
    )
    return fold_K


def train_case_c_multiclass(
    parquet_path: Path,
    k_values: Tuple[int, ...] = K_DEFAULT_LIST,
    sides: Tuple[str, ...] = SIDES_DEFAULT,
    n_splits: int = 5,
    min_train_splits: int = 2,
    n_estimators: int = 1000,
    out_base: Path = OUT_BASE_C,
) -> Dict[str, ComboSummaryMulticlass]:
    """4 K × 5 fold で案 c multiclass 学習 + 3 指標 × 8 組合せ評価."""
    out_base.mkdir(parents=True, exist_ok=True)
    t_start = time.time()
    print("\n=== case_c multiclass 開始 (Phase 1 v6・3 指標 Exit 非依存) ===")
    print(f"parquet: {parquet_path}")
    print(
        f"k={k_values} sides={sides} n_splits={n_splits} "
        f"n_estimators={n_estimators} early_stopping={EARLY_STOPPING_ROUNDS}"
    )
    print(f"lightgbm: {lgb.__version__}")
    print(
        f"閾値: entropy_lift > {ENTROPY_LIFT_THRESHOLD} / "
        f"tp_precision > {TP_PRECISION_THRESHOLD} / "
        f"direction_accuracy > {DIRECTION_ACCURACY_THRESHOLD} / "
        f"proba_threshold = {PROBA_THRESHOLD_DEFAULT}"
    )

    X, y_dict, idx = load_parquet_with_blacklist(parquet_path)
    print(f"X shape: {X.shape} / index range: {idx[0]} ~ {idx[-1]}")

    cv = prepare_purged_cv(n_splits=n_splits, min_train_splits=min_train_splits)
    all_fold_K_results: List[FoldKResult] = []
    first_label_done = False

    for K in k_values:
        print(f"\n--- K={K} ---")
        for fold_idx, (train_idx, test_idx) in enumerate(
            split_with_purging(cv, X, idx, K)
        ):
            fold_K = _process_fold_K(
                fold_idx=fold_idx,
                K=K,
                X=X,
                y_dict=y_dict,
                index=idx,
                train_idx=train_idx,
                test_idx=test_idx,
                n_estimators=n_estimators,
                out_base=out_base,
                is_first_label=(not first_label_done),
                sides=sides,
            )
            all_fold_K_results.append(fold_K)
            first_label_done = True

    # 組合せ別集約 (8 combos for full / 1 combo for smoke)
    all_combos: Dict[str, ComboSummaryMulticlass] = {}
    for K in k_values:
        for side in sides:
            combo_key = f"K{K}_{side}"
            combo_summary = ComboSummaryMulticlass(K=K, side=side)
            for fold_K in all_fold_K_results:
                if fold_K.K != K:
                    continue
                for combo in fold_K.combos:
                    if combo.side == side:
                        combo_summary.fold_results.append(combo)
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
            das = [
                r.direction_accuracy_test
                for r in combo_summary.fold_results
                if not np.isnan(r.direction_accuracy_test)
            ]
            combo_summary.entropy_lift_mean = float(np.mean(els)) if els else float("nan")
            combo_summary.tp_precision_mean = float(np.mean(tps)) if tps else float("nan")
            combo_summary.direction_accuracy_mean = (
                float(np.mean(das)) if das else float("nan")
            )
            combo_summary.pass_entropy_lift = (
                combo_summary.entropy_lift_mean > ENTROPY_LIFT_THRESHOLD
            )
            combo_summary.pass_tp_precision = (
                combo_summary.tp_precision_mean > TP_PRECISION_THRESHOLD
            )
            combo_summary.pass_direction_accuracy = (
                combo_summary.direction_accuracy_mean > DIRECTION_ACCURACY_THRESHOLD
            )
            combo_summary.pass_all = (
                combo_summary.pass_entropy_lift
                and combo_summary.pass_tp_precision
                and combo_summary.pass_direction_accuracy
            )
            all_combos[combo_key] = combo_summary

    print("\n--- 集約 (8 組合せ) ---")
    for k_str, c in all_combos.items():
        print(
            f"  {k_str}: el={c.entropy_lift_mean:.3f}(p={c.pass_entropy_lift}) "
            f"tp={c.tp_precision_mean:.3f}(p={c.pass_tp_precision}) "
            f"da={c.direction_accuracy_mean:.3f}(p={c.pass_direction_accuracy}) "
            f"all={c.pass_all}"
        )

    elapsed_total = time.time() - t_start
    n_combos_pass_all = sum(1 for c in all_combos.values() if c.pass_all)
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
        "direction_accuracy_threshold": DIRECTION_ACCURACY_THRESHOLD,
        "proba_threshold": PROBA_THRESHOLD_DEFAULT,
        "label_definition": (
            "LONG=2 / SHORT=1 / Flat=0 (phase_flow_v4 §2 L194 spec・smoke v1 fix). "
            "LONG: MFE_long > 0.5%. SHORT: MFE_short > 0.5%. "
            "両 > 0.5%: MFE 大きい方採用. 両 <= 0.5%: Flat."
        ),
        "mfe_threshold_pct": MFE_THRESHOLD_PCT,
        "fold_K_results": [asdict(fk) for fk in all_fold_K_results],
        "combos": {
            k: {
                "K": v.K,
                "side": v.side,
                "entropy_lift_mean": v.entropy_lift_mean,
                "tp_precision_mean": v.tp_precision_mean,
                "direction_accuracy_mean": v.direction_accuracy_mean,
                "pass_entropy_lift": v.pass_entropy_lift,
                "pass_tp_precision": v.pass_tp_precision,
                "pass_direction_accuracy": v.pass_direction_accuracy,
                "pass_all": v.pass_all,
                "folds": [asdict(r) for r in v.fold_results],
            }
            for k, v in all_combos.items()
        },
        "combos_pass_all": n_combos_pass_all,
        "n_combos_total": len(all_combos),
        "phase1_v6_overall_pass": n_combos_pass_all >= 6,
        "elapsed_sec": elapsed_total,
        "timestamp": datetime.now().isoformat(),
    }
    summary_path = out_base / f"case_c_multiclass_summary_{parquet_path.stem}.json"
    summary_path.write_text(
        json.dumps(summary_data, indent=2, ensure_ascii=False, default=str)
    )

    print("\n=== case_c 完了 ===")
    print(f"elapsed_total: {elapsed_total:.1f}s ({elapsed_total/60:.1f} min)")
    print(
        f"combos_pass_all: {n_combos_pass_all}/{len(all_combos)} "
        f"(>= 6 で Phase 1 v6 案 c 採用候補)"
    )
    print(f"summary saved: {summary_path}")
    return all_combos


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="case_c multiclass (Phase 1 v6・3 指標 Exit 非依存)"
    )
    p.add_argument(
        "--smoke",
        action="store_true",
        help="sample.parquet / K=12 / n_estimators=50",
    )
    p.add_argument(
        "--full",
        action="store_true",
        help="train_2021_2024.parquet / 4 K × 3 fold / n_estimators=1000",
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
        sides: Tuple[str, ...] = SIDES_DEFAULT
        n_estimators = args.n_estimators or 50
    else:
        parquet_path = PARQUET_DIR / "labels_mfe_mae_pct_train_2021_2024.parquet"
        k_values = K_DEFAULT_LIST
        sides = SIDES_DEFAULT
        n_estimators = args.n_estimators or 1000

    train_case_c_multiclass(
        parquet_path=parquet_path,
        k_values=k_values,
        sides=sides,
        n_estimators=n_estimators,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
