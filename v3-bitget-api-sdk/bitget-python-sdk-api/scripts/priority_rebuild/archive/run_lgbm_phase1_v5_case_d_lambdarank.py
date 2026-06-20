"""
run_lgbm_phase1_v5_case_d_lambdarank.py — 案 d Ranking LambdaRank (Phase 1 v6)

Phase 1 v6 で案 d を 8 組合せ (K=12/24/48/96 × LONG/SHORT) × 5 fold で学習し、
**TP Precision @ top 10% を主指標** として合否判定 (spec の entropy_lift は LambdaRank の
score 出力に直接適用不可のため skip)。

学習方法 (phase_flow_v4 §2 L170 + cc_ml_design_spec §1.5.1 L86):
- objective: LightGBM lambdarank (ranking 学習)
- 学習モデル数: 8 (K × side) × 5 fold (実 3 fold) = 24 model
- label (relevance): MFE_pct を qcut(q=5) で 0-4 bin 化 (4 = MFE 最上位 20%)
- group: **日次グループ** (288 bar/day) — LightGBM lambdarank の 10000 row/query hard limit
  回避のため、smoke v1 で「全 train 1 group」を試したが Number of rows exceeds upper limit エラー。
  日次グループに変更 (4 年 ≈ 1460 groups × 288 ≒ 5%程度のサイズ・spec L170 「ランキング上位 N%」
  趣旨は維持・日内ランキングで実用 Entry 判定に近い構造)。
- ハイパラ: 案 a/b/c/e 同等 (num_leaves=31 / learning_rate=0.05 / random_state=42)
- early_stopping=50・末尾 10% を valid

評価 (spec 不整合のため再設計・CC 独立判断):
- entropy_lift: ❌ 適用不可 (LambdaRank score は確率でない)
- **TP Precision @ top 10%**: score 上位 10% で triple_barrier_label == +1 率 (主指標・> 0.5)
- TP Precision @ top 1%: score 上位 1% (実用 threshold 参考値)
- TP Precision @ top 5%: 補助値

合格判定:
- 8 組合せ中 6+ で TP Precision @ top 10% > 0.5 → 案 d 採用候補
- (entropy_lift skip のため案 b/c/e と判定軸が異なるが、spec L170 起案時点で
  LambdaRank の特殊性を考慮した spec 例外として処理)

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

CASE_NAME = "d_lambdarank"
OUT_BASE_D = OUT_BASE / "_case_d_lambdarank"

# Phase 1 v6 合格閾値
TP_PRECISION_THRESHOLD = 0.5  # spec § 1.5.1 主指標 (top 10% に適用)
# Top-N% percentile (採用 Entry の絞り込み)
TOP_N_PCT_PRIMARY = 10.0  # 主指標 (10% = quantile 0.90)
TOP_N_PCT_TIGHT = 1.0  # 補助 (1% = quantile 0.99・実用 threshold 参考値)
TOP_N_PCT_LOOSE = 5.0  # 補助 (5%)

# label bin (qcut q=5・relevance 0-4)
LABEL_QCUT_BINS = 5

LGBM_PARAMS_LAMBDARANK: Dict[str, object] = {
    "objective": "lambdarank",
    "metric": "ndcg",
    "eval_at": [10, 100, 1000],
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
class FoldResultLambdaRank:
    fold_idx: int
    K: int
    side: str
    n_train: int
    n_valid: int
    n_test: int
    label_dist_train: Dict[int, float] = field(default_factory=dict)
    label_dist_test: Dict[int, float] = field(default_factory=dict)
    valid_ndcg_at_10: float = float("nan")
    valid_ndcg_at_100: float = float("nan")
    tp_precision_top10pct: float = float("nan")
    tp_precision_top5pct: float = float("nan")
    tp_precision_top1pct: float = float("nan")
    n_pred_entry_top10pct: int = 0
    n_pred_entry_top5pct: int = 0
    n_pred_entry_top1pct: int = 0
    train_start: str = ""
    train_end: str = ""
    test_start: str = ""
    test_end: str = ""
    elapsed_sec: float = 0.0


@dataclass
class ComboSummaryLambdaRank:
    K: int
    side: str
    fold_results: List[FoldResultLambdaRank] = field(default_factory=list)
    tp_precision_top10pct_mean: float = float("nan")
    tp_precision_top5pct_mean: float = float("nan")
    tp_precision_top1pct_mean: float = float("nan")
    valid_ndcg_at_10_mean: float = float("nan")
    pass_tp_precision_top10pct: bool = False  # 主指標


def build_lambdarank_label(mfe_pct: pd.Series) -> pd.Series:
    """MFE_pct を qcut(q=5) で 0-4 relevance に bin 化.

    qcut は 5 分位で分割: 0 = MFE 最下位 20% / 4 = MFE 最上位 20%.
    LambdaRank の relevance label として使用 (大きいほど高 relevance = ランキング上位)。
    duplicates='drop' で同値多発時に bin 数減少を許容 (rare case)。
    """
    binned = pd.qcut(mfe_pct, q=LABEL_QCUT_BINS, labels=False, duplicates="drop")
    return binned.astype(np.int64)


def _make_daily_groups(timestamps: pd.DatetimeIndex) -> List[int]:
    """timestamps (sorted DatetimeIndex) を日次グループサイズ list に変換.

    smoke v1 fix: LightGBM lambdarank の 10000 row/query hard limit 回避.
    5min bar × 288/day → 各 group ≈ 288 << 10000.
    """
    s = pd.Series(pd.to_datetime(timestamps))
    daily_counts = s.dt.normalize().value_counts(sort=False)
    return daily_counts.astype(int).tolist()


def _compute_tp_precision_at_top_n_pct(
    score: np.ndarray,
    triple_barrier_label: np.ndarray,
    top_n_pct: float,
) -> Tuple[float, int]:
    """score 上位 N% の sample で triple_barrier_label == +1 率.

    Returns: (precision, n_predicted_entry)
    """
    if len(score) == 0:
        return float("nan"), 0
    threshold = np.quantile(score, 1.0 - top_n_pct / 100.0)
    pred_entry = score > threshold
    n_pred = int(pred_entry.sum())
    if n_pred == 0:
        return float("nan"), 0
    tp_correct = triple_barrier_label == 1
    return float((pred_entry & tp_correct).sum() / n_pred), n_pred


def _train_lambdarank_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_valid: pd.DataFrame,
    y_valid: pd.Series,
    train_timestamps: pd.DatetimeIndex,
    valid_timestamps: pd.DatetimeIndex,
    n_estimators: int,
) -> Tuple[lgb.LGBMRanker, float, float]:
    """LGBMRanker lambdarank 1 model 学習 + valid NDCG@10/@100 算出.

    group: 日次グループ (smoke v1 fix・10000 row/query hard limit 回避).
    """
    params = dict(LGBM_PARAMS_LAMBDARANK)
    params["n_estimators"] = n_estimators

    train_group = _make_daily_groups(train_timestamps)
    valid_group = _make_daily_groups(valid_timestamps)
    if sum(train_group) != len(X_train):
        raise ValueError(
            f"train_group sum {sum(train_group)} != len(X_train) {len(X_train)}"
        )
    if sum(valid_group) != len(X_valid):
        raise ValueError(
            f"valid_group sum {sum(valid_group)} != len(X_valid) {len(X_valid)}"
        )

    model = lgb.LGBMRanker(**params)
    model.fit(
        X_train,
        y_train,
        group=train_group,
        eval_set=[(X_valid, y_valid)],
        eval_group=[valid_group],
        eval_at=[10, 100],
        callbacks=[lgb.early_stopping(EARLY_STOPPING_ROUNDS, verbose=False)],
    )

    if hasattr(model, "best_score_") and model.best_score_:
        valid_scores = model.best_score_.get("valid_0", {})
        valid_ndcg_10 = float(valid_scores.get("ndcg@10", float("nan")))
        valid_ndcg_100 = float(valid_scores.get("ndcg@100", float("nan")))
    else:
        valid_ndcg_10 = float("nan")
        valid_ndcg_100 = float("nan")
    return model, valid_ndcg_10, valid_ndcg_100


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
) -> FoldResultLambdaRank:
    """1 fold × 1 (K, side) combo の学習 + TP Precision @ top N% 評価."""
    train_idx_inner, valid_idx = _build_train_valid_split(
        train_idx, VALID_TAIL_FRACTION
    )

    X_tr = X.iloc[train_idx_inner]
    X_va = X.iloc[valid_idx]
    X_te = X.iloc[test_idx]

    # MFE_pct 列で relevance label 生成 (per (K, side))
    mfe_col = f"{side}_MFE_pct_K{K}"
    mfe_all = y_dict[f"{side}_MFE_pct"][mfe_col]
    y_all = build_lambdarank_label(mfe_all)
    y_tr = y_all.iloc[train_idx_inner]
    y_va = y_all.iloc[valid_idx]

    def _label_dist(s: pd.Series) -> Dict[int, float]:
        total = len(s)
        return {int(k): float(v / total) for k, v in s.value_counts().items()}

    dist_tr = _label_dist(y_tr)
    dist_te = _label_dist(y_all.iloc[test_idx])

    print(
        f"  K={K} side={side} fold {fold_idx}: "
        f"n_train_inner={len(train_idx_inner)} n_valid={len(valid_idx)} n_test={len(test_idx)}"
    )
    dist_str = " ".join(f"{k}={v:.3f}" for k, v in sorted(dist_tr.items()))
    print(f"    label_dist_tr (qcut 5 bin): {dist_str}")

    t0 = time.time()
    model, valid_ndcg_10, valid_ndcg_100 = _train_lambdarank_model(
        X_tr, y_tr, X_va, y_va,
        train_timestamps=index[train_idx_inner],
        valid_timestamps=index[valid_idx],
        n_estimators=n_estimators,
    )
    elapsed = time.time() - t0

    # test score 出力 → top N% で TP precision
    score_te = model.predict(X_te)
    tb_col = f"triple_barrier_label_{side}_K{K}"
    tb_labels = y_dict["triple_barrier_label"][tb_col].iloc[test_idx].values

    tp_p_10, n_pred_10 = _compute_tp_precision_at_top_n_pct(
        score_te, tb_labels, TOP_N_PCT_PRIMARY
    )
    tp_p_5, n_pred_5 = _compute_tp_precision_at_top_n_pct(
        score_te, tb_labels, TOP_N_PCT_LOOSE
    )
    tp_p_1, n_pred_1 = _compute_tp_precision_at_top_n_pct(
        score_te, tb_labels, TOP_N_PCT_TIGHT
    )

    fi_top20 = _get_top20_feature_importance(model, X.columns.tolist())
    if is_first_label:
        early_fi_dir = out_base / "_early_fi_for_guard_review"
        early_fi_dir.mkdir(parents=True, exist_ok=True)
        early_fi_path = early_fi_dir / f"fi_top20_K{K}_{side}_LAMBDARANK.csv"
        fi_top20.to_csv(early_fi_path, index=False)
        print(f"[guard early save] {early_fi_path}")
        _check_fractal_leak(
            fi_top20,
            K,
            side,
            target="LAMBDARANK",
            parquet_df=X,
            importance_csv_path=early_fi_path,
            full_rank_dir=early_fi_dir,
        )

    train_ts = index[train_idx_inner]
    test_ts = index[test_idx]

    print(
        f"    elapsed={elapsed:.1f}s "
        f"valid_ndcg@10={valid_ndcg_10:.4f} valid_ndcg@100={valid_ndcg_100:.4f} "
        f"tp@top10%={tp_p_10:.3f} (n={n_pred_10}) "
        f"tp@top5%={tp_p_5:.3f} (n={n_pred_5}) "
        f"tp@top1%={tp_p_1:.3f} (n={n_pred_1})"
    )

    return FoldResultLambdaRank(
        fold_idx=fold_idx,
        K=K,
        side=side,
        n_train=len(train_idx_inner),
        n_valid=len(valid_idx),
        n_test=len(test_idx),
        label_dist_train=dist_tr,
        label_dist_test=dist_te,
        valid_ndcg_at_10=valid_ndcg_10,
        valid_ndcg_at_100=valid_ndcg_100,
        tp_precision_top10pct=tp_p_10,
        tp_precision_top5pct=tp_p_5,
        tp_precision_top1pct=tp_p_1,
        n_pred_entry_top10pct=n_pred_10,
        n_pred_entry_top5pct=n_pred_5,
        n_pred_entry_top1pct=n_pred_1,
        train_start=str(train_ts[0]) if len(train_ts) > 0 else "",
        train_end=str(train_ts[-1]) if len(train_ts) > 0 else "",
        test_start=str(test_ts[0]) if len(test_ts) > 0 else "",
        test_end=str(test_ts[-1]) if len(test_ts) > 0 else "",
        elapsed_sec=elapsed,
    )


def train_case_d_lambdarank(
    parquet_path: Path,
    k_values: Tuple[int, ...] = K_DEFAULT_LIST,
    sides: Tuple[str, ...] = SIDES_DEFAULT,
    n_splits: int = 5,
    min_train_splits: int = 2,
    n_estimators: int = 1000,
    out_base: Path = OUT_BASE_D,
) -> Dict[str, ComboSummaryLambdaRank]:
    """8 (K × side) × 5 fold で案 d lambdarank 学習 + TP Precision @ top N% 評価."""
    out_base.mkdir(parents=True, exist_ok=True)
    t_start = time.time()
    print("\n=== case_d lambdarank 開始 (Phase 1 v6・TP Precision @ top 10% 主指標) ===")
    print(f"parquet: {parquet_path}")
    print(
        f"k={k_values} sides={sides} n_splits={n_splits} "
        f"n_estimators={n_estimators} early_stopping={EARLY_STOPPING_ROUNDS}"
    )
    print(f"lightgbm: {lgb.__version__}")
    print(
        f"閾値: tp_precision @ top 10% > {TP_PRECISION_THRESHOLD} (主指標) / "
        f"top 5%, top 1% は参考値 / label qcut q={LABEL_QCUT_BINS}"
    )

    X, y_dict, idx = load_parquet_with_blacklist(parquet_path)
    print(f"X shape: {X.shape} / index range: {idx[0]} ~ {idx[-1]}")

    cv = prepare_purged_cv(n_splits=n_splits, min_train_splits=min_train_splits)
    all_combos: Dict[str, ComboSummaryLambdaRank] = {}
    first_label_done = False

    for K in k_values:
        for side in sides:
            combo_key = f"K{K}_{side}"
            print(f"\n--- 組合せ {combo_key} ---")
            combo_summary = ComboSummaryLambdaRank(K=K, side=side)

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

            tp10s = [
                r.tp_precision_top10pct
                for r in combo_summary.fold_results
                if not np.isnan(r.tp_precision_top10pct)
            ]
            tp5s = [
                r.tp_precision_top5pct
                for r in combo_summary.fold_results
                if not np.isnan(r.tp_precision_top5pct)
            ]
            tp1s = [
                r.tp_precision_top1pct
                for r in combo_summary.fold_results
                if not np.isnan(r.tp_precision_top1pct)
            ]
            ndcg10s = [
                r.valid_ndcg_at_10
                for r in combo_summary.fold_results
                if not np.isnan(r.valid_ndcg_at_10)
            ]
            combo_summary.tp_precision_top10pct_mean = (
                float(np.mean(tp10s)) if tp10s else float("nan")
            )
            combo_summary.tp_precision_top5pct_mean = (
                float(np.mean(tp5s)) if tp5s else float("nan")
            )
            combo_summary.tp_precision_top1pct_mean = (
                float(np.mean(tp1s)) if tp1s else float("nan")
            )
            combo_summary.valid_ndcg_at_10_mean = (
                float(np.mean(ndcg10s)) if ndcg10s else float("nan")
            )
            combo_summary.pass_tp_precision_top10pct = (
                combo_summary.tp_precision_top10pct_mean > TP_PRECISION_THRESHOLD
            )

            print(
                f"  {combo_key} 集約: "
                f"tp@10%={combo_summary.tp_precision_top10pct_mean:.3f}"
                f"(p={combo_summary.pass_tp_precision_top10pct}) "
                f"tp@5%={combo_summary.tp_precision_top5pct_mean:.3f} "
                f"tp@1%={combo_summary.tp_precision_top1pct_mean:.3f} "
                f"ndcg@10={combo_summary.valid_ndcg_at_10_mean:.4f}"
            )
            all_combos[combo_key] = combo_summary

    elapsed_total = time.time() - t_start
    n_combos_pass = sum(
        1 for c in all_combos.values() if c.pass_tp_precision_top10pct
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
        "top_n_pct_primary": TOP_N_PCT_PRIMARY,
        "label_definition": (
            f"MFE_{{side}}_pct_K{{K}} を qcut(q={LABEL_QCUT_BINS}) で relevance 0-4 化. "
            "group=日次グループ (smoke v1 fix・10000 row/query hard limit 回避). "
            "entropy_lift は LambdaRank score の確率非変換性から適用不可・skip."
        ),
        "combos": {
            k: {
                "K": v.K,
                "side": v.side,
                "tp_precision_top10pct_mean": v.tp_precision_top10pct_mean,
                "tp_precision_top5pct_mean": v.tp_precision_top5pct_mean,
                "tp_precision_top1pct_mean": v.tp_precision_top1pct_mean,
                "valid_ndcg_at_10_mean": v.valid_ndcg_at_10_mean,
                "pass_tp_precision_top10pct": v.pass_tp_precision_top10pct,
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
    summary_path = out_base / f"case_d_lambdarank_summary_{parquet_path.stem}.json"
    summary_path.write_text(
        json.dumps(summary_data, indent=2, ensure_ascii=False, default=str)
    )

    print("\n=== case_d 完了 ===")
    print(f"elapsed_total: {elapsed_total:.1f}s ({elapsed_total/60:.1f} min)")
    print(
        f"combos_pass (tp@10% > {TP_PRECISION_THRESHOLD}): "
        f"{n_combos_pass}/{len(all_combos)} (>= 6 で Phase 1 v6 案 d 採用候補)"
    )
    print(f"summary saved: {summary_path}")
    return all_combos


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="case_d lambdarank (Phase 1 v6・TP Precision @ top 10% 主指標)"
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

    train_case_d_lambdarank(
        parquet_path=parquet_path,
        k_values=k_values,
        sides=sides,
        n_estimators=n_estimators,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
