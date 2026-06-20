"""
run_lgbm_phase1_v5_case_a_rmse.py — Phase 1 v5.1 案 a (14 ラベル独立 RMSE)

Phase 1 v5.1 学習方法再設計 (Layer 配分逆転確定版・8 組合せ評価) の案 a 実装.
16 LightGBM Regressor (LONG/SHORT × MFE/MAE × K={12,24,48,96}) × 5 fold = 80 学習.

正本:
- Phase 1 v5.1 指示書: .claude/instructions/2026-05-22_phase1_layer_inversion_instruction.md
- cc_ml_design_spec.md §1.5.1 v5.1 (5 指標 + 6+ 組合せ ALL PASS)
- phase_flow_v4_with_recovery.md L151 (閾値 1.5 = 比較ベースライン・Phase 4-b-2 本確定)
- phase_compliance_checklist.md §1.4 (feature_importance top20 fractal/level/fib ガード)

設計判断 (cc_role §1.5):
- TP first 0/1 化: pred_MFE / max(pred_MAE, 1e-6) >= 1.5 (LONG/SHORT 共通・両者 pct 正値)
- TP first 正解: triple_barrier_label_{LONG,SHORT}_K{K} == +1 (全案統一)
- train/valid 分離: Purged CV の train_idx 末尾 10% を valid (embargo gap 内で起きない)
- feature_importance ガード: K=12 LONG_MFE 学習完了直後・top20 fractal/level/fib hit → sys.exit(1)
- W1/W2 警告: MFE 側 train_rmse/valid_rmse/label_std で判定 (caller 責務・runner v5.1)
- returns_per_trade: TP first=1 trade のみ・pred_MFE pct/100 を return (Phase 4-b 前の暫定)

CLI:
- --smoke: sample.parquet / K=(12,) / side=("LONG",) / n_estimators=50 → 2 model × 5 fold = 10 学習
- --full: train_2021_2024.parquet / K=(12,24,48,96) / side=("LONG","SHORT") / n_estimators=1000 → 80 学習
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error

import lightgbm as lgb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_phase1_v5_purged_kfold import (  # noqa: E402
    K_DEFAULT_LIST,
    OUT_BASE,
    PARQUET_DIR,
    SIDES_DEFAULT,
    CaseSummary,
    FoldMetrics,
    aggregate_8_combinations_to_summary,
    compute_fold_metrics,
    load_parquet_with_blacklist,
    prepare_purged_cv,
    save_fold_results,
    split_with_purging,
)
from verify_top20_features_leak import (  # noqa: E402
    verify_double_N_suffix_match,
    verify_importance_dominance,
    verify_lag1_shift_invariance,
    verify_tail_nan_pattern,
)

CASE_NAME = "a_rmse"

# phase_flow_v4_with_recovery.md L151 既定値 (改善期待しない・比較用ベースライン)
# 本確定は Phase 4-b-2 (3 方式並列: 固定 / cluster 別 quantile / rolling 365d q90/q95/q99)
DEFAULT_RATIO_THRESHOLD = 1.5

# DSR selection bias 補正用 n_trials (Step G CP2 監査 C1 反映・2026-05-22)
# 旧 6 (案数のみ) → 48 (6 案 × 8 組合せ = K=4 × side=2)
# Phase 1 採用判定は実質 48 軸の selection 空間で「6+ 組合せ ALL PASS」を見るため、
# n_trials=6 は SR0 を過少推定して DSR を甘く出す方向の bias を持つ。
# Phase 4-b-2 grid 拡張時にさらに拡張予定 (cc_ml_design_spec §1.5.1)。
DEFAULT_N_TRIALS = 48

# Cost-deducted return parameters (Step G CP2 監査 C2 反映・2026-05-22)
# Maker fee (exchange_spec.md 確定値) 往復 + 暫定 slippage (phase_compliance 未確定項目)
# 往復 fee = 2 × 0.00014 = 0.00028 / slippage = 0.00005 (暫定 0.005%)
# pred_MFE/100 (decimal) からこの cost (decimal) を控除して net return とする
# Phase 4-b で実 Exit 設計後に実約定価格 + 実 slippage に置換予定
MAKER_FEE_ROUND_TRIP = 2 * 0.00014
SLIPPAGE_ESTIMATE = 0.00005
TOTAL_COST_PER_TRADE = MAKER_FEE_ROUND_TRIP + SLIPPAGE_ESTIMATE  # = 0.00033 (= 0.033%)

# phase_compliance_checklist.md §1.4 fractal/level/fib 系 blacklist パターン
# top1-20 hit → sys.exit(1) (即停止・leak 残存疑い)
FRACTAL_FIB_LEVEL_PATTERNS: Tuple[str, ...] = (
    "dist_to_fib_v2_",
    "resistance_distance_",
    "support_distance_",
    "nearest_level_",
)

# LightGBM ハイパラ (指示書 §3 + cc_ml_design_spec §1.5.1 整合)
LGBM_PARAMS_DEFAULT: Dict[str, object] = {
    "objective": "regression",
    "metric": "rmse",
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

EARLY_STOPPING_ROUNDS = 50
VALID_TAIL_FRACTION = 0.10  # train_idx 末尾 10% を valid に分離


def _build_train_valid_split(
    train_idx: np.ndarray,
    valid_tail_fraction: float = VALID_TAIL_FRACTION,
) -> Tuple[np.ndarray, np.ndarray]:
    """Purged CV の train_idx を train (前半 90%) + valid (末尾 10%) に分離.

    Purged CV は test との embargo gap を保証するが、train_idx 内部は時系列順.
    末尾 10% を valid に切り出すことで「最新の train」を early stopping 用に使う.
    """
    n = len(train_idx)
    n_valid = max(1, int(n * valid_tail_fraction))
    n_train_inner = n - n_valid
    if n_train_inner < 1:
        raise ValueError(
            f"train split too small: n={n}, n_valid={n_valid}, n_train_inner={n_train_inner}"
        )
    return train_idx[:n_train_inner], train_idx[n_train_inner:]


def _check_fractal_leak(
    feature_importance_top20: pd.DataFrame,
    K: int,
    side: str,
    target: str,
    parquet_df: Optional[pd.DataFrame] = None,
    importance_csv_path: Optional[Path] = None,
    full_rank_dir: Optional[Path] = None,
) -> None:
    """phase_compliance_checklist §1.4 ガード (2026-05-22 Z 案改訂).

    top1-20 hit 検出時の運用 (3 段階運用):
    - (a-1) 物理 leak verify 4 項目セット 全 PASS → 警告ログ + full_rank 記録 + 続行
    - (a-2) 1 項目でも FAIL or SKIP → 即停止 sys.exit(1)
    - hit なし → 通常運用 (今まで通り)

    1 ラベル目 (K=12 LONG_MFE) で必ず呼ぶ. 他は記録のみ.

    Args:
        feature_importance_top20: 学習済み feature_importance top20 (DataFrame[feature, importance])
        K: ラベル K 値
        side: "LONG" / "SHORT"
        target: "MFE" / "MAE"
        parquet_df: lag-1 / 末尾 NaN verify 用 (None ならガード簡略・FAIL 扱い)
        importance_csv_path: (iv) importance verify 用 csv パス
        full_rank_dir: hit 列の full_rank 記録先 (省略時は OUT_BASE/_early_fi_for_guard_review/)
    """
    hits = [
        feat
        for feat in feature_importance_top20["feature"].tolist()
        if any(pattern in feat for pattern in FRACTAL_FIB_LEVEL_PATTERNS)
    ]
    if not hits:
        print(f"[guard] phase_compliance §1.4 OK (no fractal/level/fib in top20) K={K} {side}_{target}")
        return

    # hit 検出 → 物理 leak verify 4 項目セット実行
    print(f"\n[guard a] FRACTAL/LEVEL/FIB hit detected (K={K} {side}_{target}): {hits}")
    print(f"[guard a] phase_compliance §1.4 (Z 案・2026-05-22 改訂): "
          f"物理 leak verify 4 項目セット実行・全 PASS で続行可")

    if parquet_df is None:
        print(
            f"\n!!! GUARD FAIL: parquet_df not provided (cannot run verify (i)(ii)) !!!\n"
            f"hits: {hits}\nsys.exit(1)"
        )
        sys.exit(1)

    hit_features = tuple(hits)
    # (i) lag-1 shift
    r_i = verify_lag1_shift_invariance(parquet_df, hit_features)
    pass_i = all(
        v.get("judgment", "").startswith("PASS")
        for v in r_i.values()
        if "error" not in v
    )
    # (ii) 末尾 K NaN
    r_ii = verify_tail_nan_pattern(parquet_df, hit_features, K=K)
    pass_ii = all(
        v.get("judgment", "").startswith("PASS")
        for v in r_ii.values()
        if "error" not in v
    )
    # (iii) 二重 N
    r_iii = verify_double_N_suffix_match(hit_features)
    pass_iii = all(
        v.get("judgment", "").startswith("PASS")
        for v in r_iii.values()
        if "error" not in v and "FAIL" not in v.get("judgment", "")
    )
    # (iv) importance dominance
    r_iv = verify_importance_dominance(importance_csv_path, hit_features)
    pass_iv = r_iv.get("judgment", "").startswith("PASS")

    print(f"  (i) lag-1 shift:        {'PASS' if pass_i else 'FAIL'}")
    print(f"  (ii) tail NaN:          {'PASS' if pass_ii else 'FAIL'}")
    print(f"  (iii) double N match:   {'PASS' if pass_iii else 'FAIL'}")
    print(f"  (iv) importance:        {'PASS' if pass_iv else 'FAIL/SKIP'}")

    overall = pass_i and pass_ii and pass_iii and pass_iv

    # full_rank 記録 (a-1 / a-2 共通)
    if full_rank_dir is None:
        full_rank_dir = OUT_BASE / "_early_fi_for_guard_review"
    full_rank_dir.mkdir(parents=True, exist_ok=True)
    full_rank_path = full_rank_dir / f"full_rank_K{K}_{side}_{target}.csv"
    fi_df = feature_importance_top20.copy()
    fi_df["hit_blacklist"] = fi_df["feature"].apply(
        lambda x: any(p in x for p in FRACTAL_FIB_LEVEL_PATTERNS)
    )
    fi_df.to_csv(full_rank_path, index=False)
    print(f"[guard a] full_rank saved: {full_rank_path}")

    if overall:
        # (a-1) 全 PASS → 警告ログ + 続行
        print(
            f"\n[guard a-1] ✅ 物理 leak verify 全 4 項目 PASS\n"
            f"  → false positive 確定 (本物の強い予測子)・警告ログ + 続行\n"
            f"  hits: {hits}\n"
            f"  phase_compliance §1.4 Z 案運用 (2026-05-22 改訂) 適用"
        )
        return
    else:
        # (a-2) 1 項目でも FAIL → sys.exit(1)
        print(
            f"\n!!! GUARD FAIL (a-2): 1 項目以上 FAIL/SKIP !!!\n"
            f"  (i)={'PASS' if pass_i else 'FAIL'} "
            f"(ii)={'PASS' if pass_ii else 'FAIL'} "
            f"(iii)={'PASS' if pass_iii else 'FAIL'} "
            f"(iv)={'PASS' if pass_iv else 'FAIL/SKIP'}\n"
            f"  hits: {hits}\n"
            f"  原因調査必須・sys.exit(1)"
        )
        sys.exit(1)


def _train_one_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_valid: pd.DataFrame,
    y_valid: pd.Series,
    n_estimators: int,
    extra_params: Optional[Dict[str, object]] = None,
) -> Tuple[lgb.LGBMRegressor, float, float, float]:
    """LGBMRegressor 1 model 学習 + train/valid RMSE + label_std 算出."""
    params = dict(LGBM_PARAMS_DEFAULT)
    if extra_params:
        params.update(extra_params)
    params["n_estimators"] = n_estimators

    model = lgb.LGBMRegressor(**params)
    model.fit(
        X_train,
        y_train,
        eval_set=[(X_valid, y_valid)],
        eval_metric="rmse",
        callbacks=[lgb.early_stopping(EARLY_STOPPING_ROUNDS, verbose=False)],
    )

    pred_train = model.predict(X_train)
    train_rmse = float(np.sqrt(mean_squared_error(y_train, pred_train)))

    # best_score_ は eval_set 0 番 (valid) の rmse を保持
    if hasattr(model, "best_score_") and model.best_score_:
        valid_rmse = float(model.best_score_["valid_0"]["rmse"])
    else:
        pred_valid = model.predict(X_valid)
        valid_rmse = float(np.sqrt(mean_squared_error(y_valid, pred_valid)))

    label_std = float(y_train.std())
    return model, train_rmse, valid_rmse, label_std


def _get_top20_feature_importance(
    model: lgb.LGBMRegressor,
    feature_names: List[str],
) -> pd.DataFrame:
    """feature_importance_ top20 を DataFrame で返す."""
    fi = model.feature_importances_
    df = pd.DataFrame({"feature": feature_names, "importance": fi})
    return df.sort_values("importance", ascending=False).head(20).reset_index(drop=True)


def _train_one_fold_one_combination(
    case_name: str,
    fold_idx: int,
    K: int,
    side: str,
    X: pd.DataFrame,
    y_dict: Dict[str, pd.DataFrame],
    train_idx_inner: np.ndarray,
    valid_idx: np.ndarray,
    test_idx: np.ndarray,
    n_estimators: int,
    ratio_threshold: float,
    out_base: Path,
    is_first_label: bool,
) -> Tuple[FoldMetrics, pd.Series, pd.DataFrame]:
    """1 fold × 1 組合せ (K × side) の MFE/MAE 2 model 学習 + 評価 + 保存.

    Returns:
        FoldMetrics (case_name="a_rmse")
        returns_per_trade (TP first=1 trade のみ・pred_MFE/100)
        predictions DataFrame (保存用)
    """
    X_tr = X.iloc[train_idx_inner]
    X_va = X.iloc[valid_idx]
    X_te = X.iloc[test_idx]

    # MFE model
    mfe_col = f"{side}_MFE_pct_K{K}"
    y_mfe_tr = y_dict[f"{side}_MFE_pct"][mfe_col].iloc[train_idx_inner]
    y_mfe_va = y_dict[f"{side}_MFE_pct"][mfe_col].iloc[valid_idx]

    t0 = time.time()
    model_mfe, train_rmse_mfe, valid_rmse_mfe, label_std_mfe = _train_one_model(
        X_tr, y_mfe_tr, X_va, y_mfe_va, n_estimators
    )
    elapsed_mfe = time.time() - t0
    pred_mfe = model_mfe.predict(X_te)

    # feature_importance top20 — 全 16 model 取得・ガード判定は 1 ラベル目のみ
    fi_top20_mfe = _get_top20_feature_importance(model_mfe, X.columns.tolist())
    if is_first_label:
        # ガード発動前に early save (verify_top20 (iv) 用 + 監査エビデンス)
        early_fi_dir = out_base / "_early_fi_for_guard_review"
        early_fi_dir.mkdir(parents=True, exist_ok=True)
        early_fi_path = early_fi_dir / f"fi_top20_K{K}_{side}_MFE.csv"
        fi_top20_mfe.to_csv(early_fi_path, index=False)
        print(f"[guard early save] {early_fi_path}")
        # Z 案 (2026-05-22 phase_compliance §1.4 改訂): 物理 leak verify 4 項目セット呼出
        # X (特徴量 DataFrame) を parquet_df として渡す (lag-1 / 末尾 NaN verify 用)
        _check_fractal_leak(
            fi_top20_mfe,
            K,
            side,
            "MFE",
            parquet_df=X,
            importance_csv_path=early_fi_path,
            full_rank_dir=early_fi_dir,
        )

    # MAE model
    mae_col = f"{side}_MAE_pct_K{K}"
    y_mae_tr = y_dict[f"{side}_MAE_pct"][mae_col].iloc[train_idx_inner]
    y_mae_va = y_dict[f"{side}_MAE_pct"][mae_col].iloc[valid_idx]

    t1 = time.time()
    model_mae, train_rmse_mae, valid_rmse_mae, label_std_mae = _train_one_model(
        X_tr, y_mae_tr, X_va, y_mae_va, n_estimators
    )
    elapsed_mae = time.time() - t1
    pred_mae = model_mae.predict(X_te)

    fi_top20_mae = _get_top20_feature_importance(model_mae, X.columns.tolist())

    # TP first 0/1 化 (LONG/SHORT 共通・pred_MFE / max(pred_MAE, 1e-6) >= 1.5)
    ratio = pred_mfe / np.maximum(pred_mae, 1e-6)
    y_pred_tp = (ratio >= ratio_threshold).astype(int)

    # TP first 正解 (triple_barrier_label_{side}_K{K} == +1)
    tb_col = f"triple_barrier_label_{side}_K{K}"
    y_true_tp = (y_dict["triple_barrier_label"][tb_col].iloc[test_idx] == 1).astype(int).values

    # returns_per_trade (TP first=1 予測 trade のみ・pred_MFE/100 - cost を return ratio)
    # Step G CP2 監査 C2 反映: cost-deducted return で関所 C 同型問題 (コスト控除前数値の Sharpe 投入) 回避
    # cost = 往復 maker fee 0.00028 + 暫定 slippage 0.00005 = 0.00033 (= 0.033%)
    test_index = X.index[test_idx]
    mask = y_pred_tp == 1
    if mask.sum() > 0:
        returns_per_trade = pd.Series(
            pred_mfe[mask] / 100.0 - TOTAL_COST_PER_TRADE,
            index=test_index[mask],
            name="return",
        )
    else:
        returns_per_trade = pd.Series([], dtype=float, name="return")

    # train_range / test_range
    train_range = (X.index[train_idx_inner[0]], X.index[train_idx_inner[-1]])
    test_range = (X.index[test_idx[0]], X.index[test_idx[-1]])

    # FoldMetrics (W1/W2 警告は MFE 側で判定・MAE 側は extra に格納)
    fm = compute_fold_metrics(
        case_name=case_name,
        fold_idx=fold_idx,
        K=K,
        side=side,
        y_true_tp_first=y_true_tp,
        y_pred_tp_first=y_pred_tp,
        y_prob=None,
        num_classes=0,  # regression
        returns_per_trade=returns_per_trade,
        train_range=train_range,
        test_range=test_range,
        n_train=len(train_idx_inner),
        n_test=len(test_idx),
        train_rmse=train_rmse_mfe,
        valid_rmse=valid_rmse_mfe,
        label_std=label_std_mfe,
        extra={
            "train_rmse_mae": train_rmse_mae,
            "valid_rmse_mae": valid_rmse_mae,
            "label_std_mae": label_std_mae,
            "n_valid": len(valid_idx),
            "ratio_threshold": ratio_threshold,
            "n_tp_first_predicted": int(mask.sum()),
            "n_tp_first_true": int(y_true_tp.sum()),
            "elapsed_mfe_sec": elapsed_mfe,
            "elapsed_mae_sec": elapsed_mae,
            "best_iter_mfe": int(model_mfe.best_iteration_ or n_estimators),
            "best_iter_mae": int(model_mae.best_iteration_ or n_estimators),
        },
    )

    # predictions DataFrame (保存用)
    predictions = pd.DataFrame(
        {
            "pred_mfe": pred_mfe,
            "pred_mae": pred_mae,
            "ratio_mfe_over_mae": ratio,
            "y_pred_tp_first": y_pred_tp,
            "y_true_tp_first": y_true_tp,
            "true_mfe": y_dict[f"{side}_MFE_pct"][mfe_col].iloc[test_idx].values,
            "true_mae": y_dict[f"{side}_MAE_pct"][mae_col].iloc[test_idx].values,
        },
        index=test_index,
    )

    # save (case_a_rmse_K{K}_{side}_fold_{i})
    sub_case = f"{case_name}_K{K}_{side}"
    log_text = (
        f"=== Phase 1 v5.1 案 a fold={fold_idx} K={K} side={side} ===\n"
        f"train: n={len(train_idx_inner)} range=[{train_range[0]}, {train_range[1]}]\n"
        f"valid: n={len(valid_idx)} (tail 10% of train_idx)\n"
        f"test:  n={len(test_idx)} range=[{test_range[0]}, {test_range[1]}]\n"
        f"MFE: train_rmse={train_rmse_mfe:.4f} valid_rmse={valid_rmse_mfe:.4f} "
        f"label_std={label_std_mfe:.4f} best_iter={model_mfe.best_iteration_} "
        f"elapsed={elapsed_mfe:.1f}s\n"
        f"MAE: train_rmse={train_rmse_mae:.4f} valid_rmse={valid_rmse_mae:.4f} "
        f"label_std={label_std_mae:.4f} best_iter={model_mae.best_iteration_} "
        f"elapsed={elapsed_mae:.1f}s\n"
        f"TP first: pred=1 n={int(mask.sum())} / "
        f"true=1 n={int(y_true_tp.sum())} / total n={len(y_true_tp)}\n"
        f"warnings: {fm.warnings}\n"
    )
    out_dir = save_fold_results(
        case_name=sub_case,
        fold_idx=fold_idx,
        metrics=fm,
        predictions=predictions,
        feature_importance_top20=fi_top20_mfe,
        log_text=log_text,
        returns_per_trade=returns_per_trade,
        out_base=out_base,
    )
    # MAE 側 feature_importance も保存 (Phase 2 で参照)
    fi_top20_mae.to_csv(out_dir / "feature_importance_top20_MAE.csv", index=False)

    print(
        f"[fold {fold_idx} K={K} {side}] "
        f"tp_precision={fm.tp_precision:.3f} "
        f"sim_pnl_months={fm.sim_pnl_months_positive} "
        f"sim_pnl_year_usd={fm.sim_pnl_year_usd:.1f} "
        f"sharpe={fm.fold_sharpe:.3f} "
        f"warnings={len(fm.warnings)}"
    )

    return fm, returns_per_trade, predictions


def _detect_anomaly_smell(combination_results: dict, out_base: Path) -> Dict[str, List[str]]:
    """関所 A 異常値スメル 4 条件検出 (Step G CP2 監査 C2 反映・2026-05-22).

    false_positive_incident_policy.md §5 関所 A の 4 条件を per-combination で検査:
      ① 勝率 > 70%
      ② 月次 NET > $3,800 (= 年間 $45,600 超で月次相当を超える可能性)
      ③ IS-OOS Sharpe > 3 倍乖離 (max/min ratio in fold sharpes)
      ④ DD < 月次 NET の 10% (fold_metrics に DD 未実装のため skip + warning)

    1 つ以上ヒット → 「異常値・要調査」記録 + summary JSON に anomaly_smell flag 追記。
    Mid-run sys.exit はしない (長時間 run 完走優先・最終判定で要 まこさん確認)。

    Returns:
        {combination_key: [trigger description, ...]} (空 dict = 異常値なし)
    """
    detections: Dict[str, List[str]] = {}
    for (K, side), (fold_metrics, _returns) in combination_results.items():
        combo_key = f"K{K}_{side}"
        triggers: List[str] = []

        # ① 勝率 > 70% (per-fold max)
        tp_p_values = [m.tp_precision for m in fold_metrics if not np.isnan(m.tp_precision)]
        if tp_p_values and max(tp_p_values) > 0.70:
            triggers.append(
                f"① 勝率 > 70%: max={max(tp_p_values):.3f} (folds={tp_p_values})"
            )

        # ② 月次 NET > $3,800 (per-fold sim_pnl_year_usd > $45,600 = $3,800 × 12)
        sim_pnl_year_values = [
            m.sim_pnl_year_usd
            for m in fold_metrics
            if not np.isnan(m.sim_pnl_year_usd)
        ]
        if sim_pnl_year_values and max(sim_pnl_year_values) > 45600.0:
            max_year = max(sim_pnl_year_values)
            triggers.append(
                f"② 月次 NET > $3,800: max year=${max_year:.0f} "
                f"(月次相当=${max_year/12:.0f})"
            )

        # ③ IS-OOS Sharpe > 3 倍乖離 (max/min ratio・正値 sharpes 限定)
        sharpes_pos = [
            m.fold_sharpe
            for m in fold_metrics
            if not np.isnan(m.fold_sharpe) and m.fold_sharpe > 0
        ]
        if len(sharpes_pos) >= 2:
            ratio = max(sharpes_pos) / min(sharpes_pos)
            if ratio > 3.0:
                triggers.append(
                    f"③ IS-OOS Sharpe > 3 倍乖離: max/min={ratio:.2f} "
                    f"(sharpes={[round(s, 3) for s in sharpes_pos]})"
                )

        # ④ DD 未実装 (本走で fold_metrics に max_drawdown 追加要件)
        # 現状はトリガ条件 skip · 別 trigger として「DD verify 未実装」を 1 件記録
        # (異常値なしと混同しないため・将来 implement 時に削除)
        # → false positive 減らすため skip 自体を anomaly trigger に含めない (informational only)

        if triggers:
            detections[combo_key] = triggers

    # summary JSON に flag 追記 (existing 書き込み済み summary を read-modify-write)
    summary_path = out_base / "phase1_v5_summary.json"
    if summary_path.exists():
        try:
            with open(summary_path) as f:
                summary_data = json.load(f)
            if "a_rmse" in summary_data.get("cases", {}):
                summary_data["cases"]["a_rmse"]["anomaly_smell_detected"] = bool(detections)
                summary_data["cases"]["a_rmse"]["anomaly_smell_per_combination"] = detections
                summary_data["cases"]["a_rmse"]["anomaly_smell_note"] = (
                    "false_positive §5 関所 A: ④ DD は fold_metrics 未実装で skip。"
                    "①②③ のうち 1 つ以上ヒット → 「異常値・要調査」記録 (Step G CP2 監査 C2 反映・2026-05-22)"
                )
                with open(summary_path, "w") as f:
                    json.dump(summary_data, f, indent=2, default=str)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[warn] summary JSON 更新失敗: {e}", file=sys.stderr)

    return detections


def train_case_a(
    parquet_path: Path,
    k_values: Tuple[int, ...] = K_DEFAULT_LIST,
    sides: Tuple[str, ...] = SIDES_DEFAULT,
    smoke_mode: bool = False,
    n_estimators: int = 1000,
    ratio_threshold: float = DEFAULT_RATIO_THRESHOLD,
    n_trials: int = DEFAULT_N_TRIALS,
    n_splits: int = 5,
    min_train_splits: int = 2,
    out_base: Path = OUT_BASE,
    verbose: bool = True,
) -> CaseSummary:
    """Phase 1 v5.1 案 a (14 ラベル独立 RMSE) — 8 組合せ評価.

    Args:
        parquet_path: train parquet (results/priority_rebuild/labels_mfe_mae_pct_*.parquet)
        k_values: K 値リスト (v5.1 既定 = (12, 24, 48, 96))
        sides: ("LONG", "SHORT")
        smoke_mode: True で軽量設定 (デバッグ用 log のみ・実行設定は CLI で制御)
        n_estimators: LightGBM n_estimators (smoke=50 / full=1000 推奨)
        ratio_threshold: TP first 0/1 化 (pred_MFE/pred_MAE >= ratio_threshold)
        n_trials: DSR selection bias 補正用 (Phase 1 v5.1 = 6 案並列)
        n_splits: Purged WalkForwardCV n_splits (既定 5)
        out_base: 出力先 (results/priority_rebuild/ml_phase1_v5/)
    """
    t_start = time.time()
    print(f"\n=== Phase 1 v5.1 案 a (a_rmse) 学習開始 ===")
    print(f"parquet: {parquet_path}")
    print(f"K values: {k_values} / sides: {sides}")
    print(f"smoke_mode: {smoke_mode} / n_estimators: {n_estimators}")
    print(f"ratio_threshold: {ratio_threshold} (phase_flow_v4 L151 既定)")
    print(f"n_splits: {n_splits} / min_train_splits: {min_train_splits} / n_trials: {n_trials}")
    print(f"out_base: {out_base}")

    # 1. parquet load + blacklist drop + label 分離
    X, y_dict, idx = load_parquet_with_blacklist(parquet_path)
    print(f"X shape: {X.shape} / index range: {idx[0]} ~ {idx[-1]}")

    # 2. Purged WalkForwardCV 準備 (全組合せ共通)
    cv = prepare_purged_cv(n_splits=n_splits, min_train_splits=min_train_splits)
    print(f"PurgedWalkForwardCV: n_splits={n_splits} min_train_splits={min_train_splits}\n")

    # 3. 8 組合せ × 5 fold loop
    combination_results: Dict[Tuple[int, str], Tuple[List[FoldMetrics], pd.Series]] = {}
    first_label_done = False  # 1 ラベル目 (K_min, LONG) で fractal ガード判定

    for K in k_values:
        for side in sides:
            print(f"\n--- 組合せ K={K} side={side} ---")
            fold_metrics_list: List[FoldMetrics] = []
            returns_per_trade_list: List[pd.Series] = []

            # Purged CV split は組合せ (K) ごとに eval_times = index + K * 5min を渡す
            for fold_idx, (train_idx, test_idx) in enumerate(
                split_with_purging(cv, X, idx, K)
            ):
                # train/valid 分離 (Purged の train_idx 末尾 10% を valid)
                train_idx_inner, valid_idx = _build_train_valid_split(
                    train_idx, VALID_TAIL_FRACTION
                )
                # embargo gap verify
                assert valid_idx[-1] < test_idx[0], (
                    f"valid embargo violation: valid_idx[-1]={valid_idx[-1]} >= "
                    f"test_idx[0]={test_idx[0]}"
                )

                # 1 ラベル目 = K の最小値かつ side="LONG" で fractal ガード判定
                is_first_label = (K == min(k_values)) and (side == "LONG") and (not first_label_done)

                fm, returns_per_trade, _predictions = _train_one_fold_one_combination(
                    case_name=CASE_NAME,
                    fold_idx=fold_idx,
                    K=K,
                    side=side,
                    X=X,
                    y_dict=y_dict,
                    train_idx_inner=train_idx_inner,
                    valid_idx=valid_idx,
                    test_idx=test_idx,
                    n_estimators=n_estimators,
                    ratio_threshold=ratio_threshold,
                    out_base=out_base,
                    is_first_label=is_first_label,
                )
                if is_first_label:
                    first_label_done = True

                fold_metrics_list.append(fm)
                returns_per_trade_list.append(returns_per_trade)

            # 組合せ単位 returns 統合
            if returns_per_trade_list:
                returns_combined = pd.concat(returns_per_trade_list).sort_index()
            else:
                returns_combined = pd.Series([], dtype=float, name="return")

            combination_results[(K, side)] = (fold_metrics_list, returns_combined)

    # 4. 8 組合せ統合 + §4.1 v5.1 合格判定
    print(f"\n=== 8 組合せ統合 + §4.1 合格判定 ===")
    case_summary = aggregate_8_combinations_to_summary(
        case_name=CASE_NAME,
        combination_results=combination_results,
        n_trials=n_trials,
        out_base=out_base,
    )

    # 5. 関所 A 異常値スメル 4 条件検出 (Step G CP2 監査 C2 反映・2026-05-22)
    print(f"\n=== 関所 A 異常値スメル 4 条件 verify (false_positive §5) ===")
    anomaly_detections = _detect_anomaly_smell(combination_results, out_base)
    if anomaly_detections:
        print(f"⚠️  異常値スメル検出: {len(anomaly_detections)} / {len(combination_results)} 組合せ")
        for combo_key, triggers in anomaly_detections.items():
            print(f"  [{combo_key}] ヒット {len(triggers)} 件:")
            for trig in triggers:
                print(f"    - {trig}")
        print(
            "→ false_positive §5 関所 A 義務: 「合格」と書かず「**異常値・要調査**」記録。\n"
            "→ summary JSON `anomaly_smell_detected: true` 追記済。\n"
            "→ まこさん再監査経路 (再 CP2 / 独立評価) 推奨 (cc_role §1.2)。"
        )
    else:
        print("✅ 異常値スメル なし (①②③ 全 セーフ・④ DD は fold_metrics 未実装で skip)")

    elapsed_total = time.time() - t_start
    print(
        f"\n=== 案 a 完了 ===\n"
        f"n_combinations: {case_summary.n_combinations}\n"
        f"n_combinations_all_pass: {case_summary.n_combinations_all_pass}\n"
        f"all_pass_combinations: {case_summary.all_pass_combinations}\n"
        f"meets_6plus_criteria: {case_summary.meets_6plus_criteria}\n"
        f"layer3_investigation_needed: {case_summary.layer3_investigation_needed}\n"
        f"elapsed: {elapsed_total/60:.1f} min\n"
    )
    return case_summary


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Phase 1 v5.1 案 a (14 ラベル独立 RMSE) — 8 組合せ評価"
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="smoke mode: sample.parquet + K=(12,) + side=(LONG,) + n_estimators=50 (10 学習・約 30-60 分)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="full mode: train_2021_2024.parquet + K=(12,24,48,96) + side=(LONG,SHORT) + n_estimators=1000 (80 学習・約 5-6 時間)",
    )
    parser.add_argument(
        "--parquet",
        type=Path,
        default=None,
        help="parquet 明示指定 (smoke / full の代わり)",
    )
    parser.add_argument(
        "--n-estimators",
        type=int,
        default=None,
        help="LightGBM n_estimators (smoke=50 / full=1000)",
    )
    parser.add_argument(
        "--k",
        type=int,
        nargs="+",
        default=None,
        help="K 値リスト (例: --k 12 24 48 96)",
    )
    parser.add_argument(
        "--side",
        type=str,
        nargs="+",
        default=None,
        choices=["LONG", "SHORT"],
        help='side リスト (例: --side LONG SHORT)',
    )
    parser.add_argument(
        "--n-splits",
        type=int,
        default=5,
        help="Purged WalkForwardCV n_splits (既定 5)",
    )
    parser.add_argument(
        "--min-train-splits",
        type=int,
        default=2,
        help=(
            "Purged WalkForwardCV min_train_splits (既定 2)・smoke で n_splits=3 時は 1 指定必須 "
            "(strict <: min_train_splits < n_splits - n_test_splits)"
        ),
    )
    parser.add_argument(
        "--ratio-threshold",
        type=float,
        default=DEFAULT_RATIO_THRESHOLD,
        help=f"TP first 閾値 (phase_flow_v4 L151 既定 {DEFAULT_RATIO_THRESHOLD})",
    )
    parser.add_argument(
        "--n-trials",
        type=int,
        default=DEFAULT_N_TRIALS,
        help=f"DSR n_trials (Phase 1 v5.1 = {DEFAULT_N_TRIALS} 案並列)",
    )
    parser.add_argument(
        "--out-base",
        type=Path,
        default=OUT_BASE,
        help=f"出力先 ({OUT_BASE})",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    if args.smoke and args.full:
        print("ERROR: --smoke と --full は同時指定不可")
        return 2
    if not args.smoke and not args.full and args.parquet is None:
        print("ERROR: --smoke / --full / --parquet のいずれか必須")
        return 2

    if args.parquet is not None:
        parquet_path = args.parquet
        k_values = tuple(args.k) if args.k else K_DEFAULT_LIST
        sides = tuple(args.side) if args.side else SIDES_DEFAULT
        n_estimators = args.n_estimators if args.n_estimators is not None else 1000
        smoke_mode = False
    elif args.smoke:
        parquet_path = PARQUET_DIR / "labels_mfe_mae_pct_sample.parquet"
        k_values = tuple(args.k) if args.k else (12,)
        sides = tuple(args.side) if args.side else ("LONG",)
        n_estimators = args.n_estimators if args.n_estimators is not None else 50
        smoke_mode = True
    else:  # full
        parquet_path = PARQUET_DIR / "labels_mfe_mae_pct_train_2021_2024.parquet"
        k_values = tuple(args.k) if args.k else K_DEFAULT_LIST
        sides = tuple(args.side) if args.side else SIDES_DEFAULT
        n_estimators = args.n_estimators if args.n_estimators is not None else 1000
        smoke_mode = False

    if not parquet_path.exists():
        print(f"ERROR: parquet not found: {parquet_path}")
        return 2

    print(f"=====Phase 1 v5.1 案 a START {datetime.now().isoformat()} =====")
    case_summary = train_case_a(
        parquet_path=parquet_path,
        k_values=k_values,
        sides=sides,
        smoke_mode=smoke_mode,
        n_estimators=n_estimators,
        ratio_threshold=args.ratio_threshold,
        n_trials=args.n_trials,
        n_splits=args.n_splits,
        min_train_splits=args.min_train_splits,
        out_base=args.out_base,
    )
    print(f"=====Phase 1 v5.1 案 a END {datetime.now().isoformat()} =====")
    # exit code: 6+ 組合せ ALL PASS → 0 / 未満 → 1 (Layer 3 投入判定)
    return 0 if case_summary.meets_6plus_criteria else 1


if __name__ == "__main__":
    sys.exit(main())
