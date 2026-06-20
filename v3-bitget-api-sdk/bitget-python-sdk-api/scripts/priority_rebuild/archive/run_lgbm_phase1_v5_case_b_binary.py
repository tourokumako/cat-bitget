"""
run_lgbm_phase1_v5_case_b_binary.py — 案 b Entry Binary (Phase 1 v6・3 指標 Exit 非依存)

Phase 1 v6 (L-217 整合) で案 b を 8 組合せ (K=12/24/48/96 × LONG/SHORT) × 5 fold で
学習し、3 指標のうち 2 指標 (entropy lift / TP Precision) で合否判定する。
Direction Accuracy は案 c (multiclass) のみ・案 b は対象外。

学習方法 (phase_flow_v4 §2 L189-199 整合):
- objective: LightGBM binary (1/0 二値分類)
- 学習モデル数: 8 組合せ × 5 fold = 40 model (1 model per combo per fold)
- entry_label 定義: side_MFE_pct_K{K} >= |side_MAE_pct_K{K}| なら 1 else 0
  CC 独立判断: phase_flow_v4 §2 L194 の K=12 既定値 (MFE>0.5% AND MAE>-0.3%) は K=12 のみで
  8 組合せに不適用・代わりに比率ベース ≥ 1.0 で K 不変・8 組合せ統一を採用 (まこさん事前合意済)。
  既知トレードオフ: positive_rate が ~50% 近辺で class imbalance が弱まり scale_pos_weight の
  寄与が小さくなる。spec の「50:1〜100:1」想定とは乖離するが、Phase 1 比較目的では
  「8 組合せで対称」を優先。後続フェーズ (Phase 4-b-2) で本確定。
- scale_pos_weight: (y==0).sum() / max((y==1).sum(),1) で fold ごと算出
- ハイパラ: 案 a 同等 (num_leaves=31 / learning_rate=0.05 / random_state=42)
- early_stopping=50・末尾 10% を valid (時系列 split・L-183 教訓)

評価 (Phase 1 v6・cc_ml_design_spec §1.5.1):
- entropy lift > 10% (compute_entropy_lift 既存・num_classes=2)
- TP Precision > 0.5 (pred_proba>0.5 ∩ triple_barrier_label_{side}_K{K}==+1)

合格判定 (cc_ml_design_spec §1.5.1 L96-100):
- 8 組合せ中 6+ 組合せで 2 指標 ALL PASS → 案 b 採用候補

verify 義務 (phase_compliance_checklist §Phase 1):
- 1.1 時系列 valid split (末尾 10%・_build_train_valid_split 流用)
- 1.2 early_stopping=50 / random_state=42
- 1.3 feature_importance top20 出力
- 1.4 fractal blacklist 3 段階運用 (_check_fractal_leak 流用)
- 1.5 lightgbm / sklearn version log
- Phase -1 blacklist 64 列 drop (load_parquet_with_blacklist 自動)

CLI:
- --smoke: sample.parquet / K=12 LONG / n_estimators=50 / ~数分
- --full: train_2021_2024.parquet / 8 組合せ × 5 fold / n_estimators=1000
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

CASE_NAME = "b_binary"
OUT_BASE_B = OUT_BASE / "_case_b_binary"

# Phase 1 v6 合格閾値 (cc_ml_design_spec §1.5.1)
# compute_entropy_lift は 0.0-1.0 範囲 (= 1 - logloss/log(num_classes)) を返す
# 「> 10%」= 0.10 で比較
ENTROPY_LIFT_THRESHOLD = 0.10
TP_PRECISION_THRESHOLD = 0.5
# cc_ml_design_spec §1.5.1 L86 案 b 0/1 化 default = proba > 0.5
# 本確定は Phase 4-b-2 (3 方式並列)
PROBA_THRESHOLD_DEFAULT = 0.5

# LightGBM binary params (案 a regression と同一ハイパラ + objective=binary)
LGBM_PARAMS_BINARY: Dict[str, object] = {
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
class FoldResultBinary:
    fold_idx: int
    K: int
    side: str
    n_train: int
    n_valid: int
    n_test: int
    positive_rate_train: float
    positive_rate_test: float
    scale_pos_weight: float
    train_logloss: float
    valid_logloss: float
    test_logloss: float
    entropy_lift_test: float  # 0.0-1.0 範囲 (例: 0.12 = 12% lift)
    tp_precision_test: float
    n_predicted_entry: int
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    elapsed_sec: float
    warnings: List[str] = field(default_factory=list)


@dataclass
class ComboSummaryBinary:
    K: int
    side: str
    fold_results: List[FoldResultBinary] = field(default_factory=list)
    entropy_lift_mean: float = float("nan")
    tp_precision_mean: float = float("nan")
    pass_entropy_lift: bool = False
    pass_tp_precision: bool = False
    pass_both: bool = False


def build_binary_label(y_mfe: pd.Series, y_mae: pd.Series) -> pd.Series:
    """entry_label = 1 if MFE_pct >= |MAE_pct| else 0

    CC 独立判断 (まこさん事前合意済):
    - phase_flow_v4 §2 L194 の K=12 既定値 (MFE>0.5% AND MAE>-0.3%) は K=12 のみで
      K=24/48/96 では MFE/MAE 分布が拡大するため適用不可。
    - 代わりに「比率 ≥ 1.0」(= MFE 絶対値が MAE 絶対値以上) で K 不変・8 組合せ統一。
    - 案 a の「予測比 ≥ 1.5」(phase_flow_v4 L181) との対称性 (案 a は予測値の比・案 b は実値の比)。
    """
    return (y_mfe >= y_mae.abs()).astype(int)


def _safe_logloss(
    y_true: np.ndarray, y_proba: np.ndarray, eps: float = 1e-15
) -> float:
    yp = np.clip(y_proba, eps, 1.0 - eps)
    return float(
        -np.mean(y_true * np.log(yp) + (1 - y_true) * np.log(1.0 - yp))
    )


def _train_binary_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_valid: pd.DataFrame,
    y_valid: pd.Series,
    n_estimators: int,
    scale_pos_weight: float,
) -> Tuple[lgb.LGBMClassifier, float, float]:
    """LGBMClassifier binary 1 model 学習 + train/valid logloss 算出."""
    params = dict(LGBM_PARAMS_BINARY)
    params["n_estimators"] = n_estimators
    params["scale_pos_weight"] = scale_pos_weight

    model = lgb.LGBMClassifier(**params)
    model.fit(
        X_train,
        y_train,
        eval_set=[(X_valid, y_valid)],
        eval_metric="binary_logloss",
        callbacks=[lgb.early_stopping(EARLY_STOPPING_ROUNDS, verbose=False)],
    )

    pred_train_proba = model.predict_proba(X_train)[:, 1]
    train_logloss = _safe_logloss(y_train.values, pred_train_proba)
    if hasattr(model, "best_score_") and model.best_score_:
        valid_logloss = float(model.best_score_["valid_0"]["binary_logloss"])
    else:
        pred_valid_proba = model.predict_proba(X_valid)[:, 1]
        valid_logloss = _safe_logloss(y_valid.values, pred_valid_proba)
    return model, train_logloss, valid_logloss


def _compute_tp_precision(
    y_pred_proba: np.ndarray,
    triple_barrier_label: np.ndarray,
    threshold: float = PROBA_THRESHOLD_DEFAULT,
) -> Tuple[float, int]:
    """TP Precision = (pred_entry ∩ triple_barrier==+1) / pred_entry.

    Returns: (precision, n_predicted_entry)
    """
    pred_entry = y_pred_proba > threshold
    n_pred = int(pred_entry.sum())
    if n_pred == 0:
        return float("nan"), 0
    tp_correct = triple_barrier_label == 1
    precision = float((pred_entry & tp_correct).sum() / n_pred)
    return precision, n_pred


def _process_fold(
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
) -> FoldResultBinary:
    """1 fold × 1 (K, side) の学習 + 評価."""
    train_idx_inner, valid_idx = _build_train_valid_split(
        train_idx, VALID_TAIL_FRACTION
    )

    X_tr = X.iloc[train_idx_inner]
    X_va = X.iloc[valid_idx]
    X_te = X.iloc[test_idx]

    mfe_col = f"{side}_MFE_pct_K{K}"
    mae_col = f"{side}_MAE_pct_K{K}"
    mfe_all = y_dict[f"{side}_MFE_pct"][mfe_col]
    mae_all = y_dict[f"{side}_MAE_pct"][mae_col]
    y_all = build_binary_label(mfe_all, mae_all)

    y_tr = y_all.iloc[train_idx_inner]
    y_va = y_all.iloc[valid_idx]
    y_te = y_all.iloc[test_idx]

    n_neg = int((y_tr == 0).sum())
    n_pos = int((y_tr == 1).sum())
    scale_pos_weight = float(n_neg / max(n_pos, 1))
    pos_rate_tr = float(y_tr.mean())
    pos_rate_te = float(y_te.mean())

    print(
        f"  fold {fold_idx}: "
        f"n_train_inner={len(train_idx_inner)} n_valid={len(valid_idx)} n_test={len(test_idx)} "
        f"pos_rate_tr={pos_rate_tr:.3f} pos_rate_te={pos_rate_te:.3f} spw={scale_pos_weight:.2f}"
    )

    t0 = time.time()
    model, train_logloss, valid_logloss = _train_binary_model(
        X_tr, y_tr, X_va, y_va, n_estimators, scale_pos_weight
    )
    elapsed = time.time() - t0

    pred_te_proba = model.predict_proba(X_te)[:, 1]
    test_logloss = _safe_logloss(y_te.values, pred_te_proba)
    entropy_lift = compute_entropy_lift(y_te.values, pred_te_proba, num_classes=2)

    tb_col = f"triple_barrier_label_{side}_K{K}"
    tb_labels = y_dict["triple_barrier_label"][tb_col].iloc[test_idx].values
    tp_precision, n_pred_entry = _compute_tp_precision(
        pred_te_proba, tb_labels, PROBA_THRESHOLD_DEFAULT
    )

    fi_top20 = _get_top20_feature_importance(model, X.columns.tolist())
    if is_first_label:
        early_fi_dir = out_base / "_early_fi_for_guard_review"
        early_fi_dir.mkdir(parents=True, exist_ok=True)
        early_fi_path = early_fi_dir / f"fi_top20_K{K}_{side}_BINARY.csv"
        fi_top20.to_csv(early_fi_path, index=False)
        print(f"[guard early save] {early_fi_path}")
        _check_fractal_leak(
            fi_top20,
            K,
            side,
            target="BINARY",
            parquet_df=X,
            importance_csv_path=early_fi_path,
            full_rank_dir=early_fi_dir,
        )

    train_ts = index[train_idx_inner]
    test_ts = index[test_idx]

    print(
        f"    elapsed={elapsed:.1f}s "
        f"train_ll={train_logloss:.4f} valid_ll={valid_logloss:.4f} test_ll={test_logloss:.4f} "
        f"entropy_lift={entropy_lift:.3f} tp_precision={tp_precision:.3f} (n_pred={n_pred_entry})"
    )

    return FoldResultBinary(
        fold_idx=fold_idx,
        K=K,
        side=side,
        n_train=len(train_idx_inner),
        n_valid=len(valid_idx),
        n_test=len(test_idx),
        positive_rate_train=pos_rate_tr,
        positive_rate_test=pos_rate_te,
        scale_pos_weight=scale_pos_weight,
        train_logloss=train_logloss,
        valid_logloss=valid_logloss,
        test_logloss=test_logloss,
        entropy_lift_test=float(entropy_lift),
        tp_precision_test=tp_precision,
        n_predicted_entry=n_pred_entry,
        train_start=str(train_ts[0]) if len(train_ts) > 0 else "",
        train_end=str(train_ts[-1]) if len(train_ts) > 0 else "",
        test_start=str(test_ts[0]) if len(test_ts) > 0 else "",
        test_end=str(test_ts[-1]) if len(test_ts) > 0 else "",
        elapsed_sec=elapsed,
    )


def train_case_b_binary(
    parquet_path: Path,
    k_values: Tuple[int, ...] = K_DEFAULT_LIST,
    sides: Tuple[str, ...] = SIDES_DEFAULT,
    n_splits: int = 5,
    min_train_splits: int = 2,
    n_estimators: int = 1000,
    out_base: Path = OUT_BASE_B,
) -> Dict[str, ComboSummaryBinary]:
    """8 組合せ × 5 fold で案 b binary 学習 + 2 指標評価."""
    out_base.mkdir(parents=True, exist_ok=True)
    t_start = time.time()
    print("\n=== case_b binary 開始 (Phase 1 v6・3 指標 Exit 非依存・案 b は 2 指標適用) ===")
    print(f"parquet: {parquet_path}")
    print(
        f"k={k_values} sides={sides} n_splits={n_splits} "
        f"n_estimators={n_estimators} early_stopping={EARLY_STOPPING_ROUNDS}"
    )
    print(f"lightgbm: {lgb.__version__}")

    X, y_dict, idx = load_parquet_with_blacklist(parquet_path)
    print(f"X shape: {X.shape} / index range: {idx[0]} ~ {idx[-1]}")

    cv = prepare_purged_cv(n_splits=n_splits, min_train_splits=min_train_splits)
    all_combos: Dict[str, ComboSummaryBinary] = {}
    first_label_done = False

    for K in k_values:
        for side in sides:
            combo_key = f"K{K}_{side}"
            print(f"\n--- 組合せ {combo_key} ---")
            combo_summary = ComboSummaryBinary(K=K, side=side)

            for fold_idx, (train_idx, test_idx) in enumerate(
                split_with_purging(cv, X, idx, K)
            ):
                fold_result = _process_fold(
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
                f"entropy_lift_mean={combo_summary.entropy_lift_mean:.3f} "
                f"(pass={combo_summary.pass_entropy_lift}) "
                f"tp_precision_mean={combo_summary.tp_precision_mean:.3f} "
                f"(pass={combo_summary.pass_tp_precision}) "
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
        "proba_threshold": PROBA_THRESHOLD_DEFAULT,
        "label_definition": "entry_label = 1 if side_MFE_pct_K{K} >= |side_MAE_pct_K{K}| else 0",
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
    summary_path = out_base / f"case_b_binary_summary_{parquet_path.stem}.json"
    summary_path.write_text(
        json.dumps(summary_data, indent=2, ensure_ascii=False, default=str)
    )

    print("\n=== case_b 完了 ===")
    print(f"elapsed_total: {elapsed_total:.1f}s ({elapsed_total/60:.1f} min)")
    print(
        f"combos_pass_both: {n_combos_pass_both}/{len(all_combos)} "
        f"(>= 6 で Phase 1 v6 案 b 採用候補)"
    )
    print(f"summary saved: {summary_path}")
    return all_combos


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="case_b binary (Phase 1 v6・3 指標 Exit 非依存・案 b は 2 指標)"
    )
    p.add_argument(
        "--smoke",
        action="store_true",
        help="sample.parquet / K=12 LONG / n_estimators=50",
    )
    p.add_argument(
        "--full",
        action="store_true",
        help="train_2021_2024.parquet / 8 組合せ / n_estimators=1000",
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

    train_case_b_binary(
        parquet_path=parquet_path,
        k_values=k_values,
        sides=sides,
        n_estimators=n_estimators,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
