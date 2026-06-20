"""run_phase2_entry_ml_smoke.py — [2] Entry ML smoke test (1 fold × 1 ラベル × LightGBM default)

目的:
  - §6.2 設計 (ml_pipeline_baseline_v1.md §6.2) の実装着手前 smoke test
  - 1 fold × 1 ラベル (LONG_MFE_pct_K12) で動作確認 + 所要時間実測 + leak 4 点 verify 経路確認
  - 本走 (= 56 ラベル × 5 fold × Optuna 30 trials) の時間試算精度を上げる

設計引継ぎ (§6.2 から):
  - 入力: Phase 0 v3.1 既存 parquet (= 2,604 列 blacklist 後) + regime 8 列 (= prob 4 + one-hot 4)
  - CV: Walk-Forward Purged K-Fold 5 fold (= 既存 helper `prepare_purged_cv` 流用)
  - embargo: t1 = bar_timestamp + K * bar_freq (= AFML mlfinpy 同型・既存 `compute_t1_vertical_barrier`)
  - 既存 helper を最大流用 (= run_phase1_v5_purged_kfold.load_parquet_with_blacklist 等)

smoke test 限定構成:
  - 1 fold (= fold 0 のみ・5 fold 全走の 1/5 時間)
  - 1 ラベル (= LONG_MFE_pct_K12・スキャル 1h・代表)
  - LightGBM default + early_stopping=50 (= §6.2.6 業界 range の中央値)
  - feature_importance top 20 出力 + blacklist 混入 + 怪しい列名検出 (= leak 4 点 verify 経路)
  - regime 8 列が top 50 に含まれるか verify (= §6.2.4 論点 2 引継ぎ機能性 verify)

実行コマンド:
  .venv311/bin/python -m scripts.priority_rebuild.run_phase2_entry_ml_smoke

出力:
  - results/priority_rebuild/ml_phase2_smoke/smoke_run.log (= stdout 全捕捉・実行コマンド経由)
  - results/priority_rebuild/ml_phase2_smoke/smoke_summary.json (= 主要メトリクス + elapsed_sec)
  - results/priority_rebuild/ml_phase2_smoke/feature_importance_top20.csv
"""

import json
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, r2_score

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.priority_rebuild.run_phase1_v5_purged_kfold import (  # noqa: E402
    load_parquet_with_blacklist,
    prepare_purged_cv,
    split_with_purging,
)

# 入出力 path
PARQUET_TRAIN = REPO_ROOT / "results" / "priority_rebuild" / "labels_mfe_mae_pct_train_2021_2024.parquet"
PARQUET_REGIME = REPO_ROOT / "results" / "regime_step1" / "regime_predictions_train_2021_2024.parquet"
OUT_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase2_smoke"

# smoke test 設定 (= §6.2 設計の subset)
SMOKE_K = 12  # K=12 = スキャル 1h horizon (= cat_v9 P1/P3 整合)
SMOKE_LABEL_PREFIX = "LONG_MFE_pct"
SMOKE_TARGET = f"{SMOKE_LABEL_PREFIX}_K{SMOKE_K}"
SMOKE_FOLD = 0  # fold 0 のみ
N_SPLITS = 5
VALID_TAIL_FRACTION = 0.10  # train_idx 末尾 10% を valid

# regime 入力列 (= §6.2.4 論点 4 引継ぎ・object 型 regime_label / regime_volatility_level は smoke 除外)
REGIME_COLS = [
    "regime_prob_up",
    "regime_prob_down",
    "regime_prob_range",
    "regime_confidence",
    "regime_is_uptrend",
    "regime_is_downtrend",
    "regime_is_range",
    "regime_is_unclear",
]

# leak verify: 怪しい列名 pattern (= §6.2.8 項目 5 拡張)
SUSPICIOUS_PATTERNS = ["fractal", "pivot", "resistance", "support", "future", "look_ahead"]

# LightGBM default hyperparameters (= §6.2.6 業界 range の中央値)
LGB_DEFAULT_PARAMS = {
    "objective": "regression",
    "metric": "rmse",
    "num_leaves": 31,  # default
    "learning_rate": 0.05,
    "min_child_samples": 20,
    "n_estimators": 1000,
    "max_depth": -1,
    "reg_alpha": 0.0,
    "reg_lambda": 0.0,
    "random_state": 42,
    "n_jobs": -1,
    "verbose": -1,
}
EARLY_STOPPING_ROUNDS = 50


def merge_regime_columns(X: pd.DataFrame, regime_path: Path) -> pd.DataFrame:
    """regime parquet を timestamp で left join. 既存 X の index に reindex."""
    df_r = pd.read_parquet(regime_path)
    missing = [c for c in REGIME_COLS if c not in df_r.columns]
    if missing:
        raise KeyError(f"regime parquet missing columns: {missing}")
    df_r_keep = df_r[REGIME_COLS]
    # reindex で X.index に合わせる (= causal alignment は §6.1.6 で実装済 = ここでは単純 reindex)
    df_r_aligned = df_r_keep.reindex(X.index)
    n_null = df_r_aligned.isnull().any(axis=1).sum()
    print(f"[merge] regime columns added: {len(REGIME_COLS)} cols / null rows after reindex: {n_null:,}")
    return pd.concat([X, df_r_aligned], axis=1)


def verify_leak_in_top20(fi_df: pd.DataFrame) -> dict:
    """feature_importance top 20 の blacklist 混入 + 怪しい列名検出."""
    BLACKLIST_FAMILIES = (
        "sma_20", "sma_50", "ichimoku_kijun", "ichimoku_tenkan",
        "macd_line", "macd_signal", "macd_hist", "macd_hist_change",
    )
    top20 = fi_df.head(20)
    blacklist_hits = []
    for c in top20["feature"]:
        for f in BLACKLIST_FAMILIES:
            if c.startswith(f + "__"):
                blacklist_hits.append((c, f))
                break
    suspicious_hits = []
    for c in top20["feature"]:
        for p in SUSPICIOUS_PATTERNS:
            if p in c.lower():
                suspicious_hits.append((c, p))
                break
    return {
        "blacklist_hits_count": len(blacklist_hits),
        "blacklist_hits": blacklist_hits,
        "suspicious_hits_count": len(suspicious_hits),
        "suspicious_hits": suspicious_hits,
    }


def verify_regime_in_top50(fi_df: pd.DataFrame) -> dict:
    """regime 8 列が feature_importance top 50 に含まれるか verify (= §6.2.4 論点 2)."""
    top50 = fi_df.head(50)["feature"].tolist()
    regime_in_top50 = [c for c in REGIME_COLS if c in top50]
    return {
        "regime_in_top50_count": len(regime_in_top50),
        "regime_in_top50": regime_in_top50,
        "regime_total_count": len(REGIME_COLS),
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    print(f"[start] smoke test")
    print(f"[config] target={SMOKE_TARGET} fold={SMOKE_FOLD}/{N_SPLITS} K={SMOKE_K}")
    print(f"[config] LightGBM default params: {LGB_DEFAULT_PARAMS}")

    # 1. parquet load + Phase -1 blacklist drop + 56 ラベル分離
    print(f"[step 1] load parquet: {PARQUET_TRAIN.name}")
    X, y_dict, index = load_parquet_with_blacklist(PARQUET_TRAIN, verbose=True)
    print(f"[step 1] X shape (before regime merge): {X.shape}")

    # 2. regime 8 列 merge (= §6.2.4 論点 4)
    print(f"[step 2] merge regime columns from {PARQUET_REGIME.name}")
    X = merge_regime_columns(X, PARQUET_REGIME)
    print(f"[step 2] X shape (after regime merge): {X.shape}")

    # 3. target 抽出
    if SMOKE_LABEL_PREFIX not in y_dict:
        raise KeyError(f"label prefix {SMOKE_LABEL_PREFIX!r} not in y_dict (keys={list(y_dict.keys())})")
    y_target = y_dict[SMOKE_LABEL_PREFIX][SMOKE_TARGET]
    print(f"[step 3] target column: {SMOKE_TARGET} (dtype={y_target.dtype} / NaN={y_target.isnull().sum():,})")

    # 4. Purged K-Fold 5 fold + fold 0 取得
    print(f"[step 4] prepare_purged_cv n_splits={N_SPLITS}")
    cv = prepare_purged_cv(n_splits=N_SPLITS)
    fold_splits = list(split_with_purging(cv, X, index, K=SMOKE_K))
    print(f"[step 4] total folds yielded: {len(fold_splits)}")
    if SMOKE_FOLD >= len(fold_splits):
        raise IndexError(f"fold {SMOKE_FOLD} requested but only {len(fold_splits)} folds yielded")
    train_idx, test_idx = fold_splits[SMOKE_FOLD]
    print(f"[step 4] fold {SMOKE_FOLD}: train={len(train_idx):,} test={len(test_idx):,}")
    print(f"[step 4] train range: {index[train_idx[0]]} ... {index[train_idx[-1]]}")
    print(f"[step 4] test range:  {index[test_idx[0]]} ... {index[test_idx[-1]]}")

    # 5. train_idx 末尾 10% を valid に分離 (= 既存 phase1_v5 流儀)
    n_train = len(train_idx)
    n_valid = int(n_train * VALID_TAIL_FRACTION)
    n_train_inner = n_train - n_valid
    train_inner = train_idx[:n_train_inner]
    valid_idx = train_idx[n_train_inner:]
    print(f"[step 5] train_inner={len(train_inner):,} / valid={len(valid_idx):,}")

    # 6. X / y 切り出し + NaN 除外 (= target NaN は学習対象外)
    X_tr = X.iloc[train_inner]
    X_va = X.iloc[valid_idx]
    X_te = X.iloc[test_idx]
    y_tr = y_target.iloc[train_inner]
    y_va = y_target.iloc[valid_idx]
    y_te = y_target.iloc[test_idx]

    mask_tr = ~y_tr.isnull()
    mask_va = ~y_va.isnull()
    mask_te = ~y_te.isnull()
    X_tr, y_tr = X_tr.loc[mask_tr], y_tr.loc[mask_tr]
    X_va, y_va = X_va.loc[mask_va], y_va.loc[mask_va]
    X_te, y_te = X_te.loc[mask_te], y_te.loc[mask_te]
    print(f"[step 6] after NaN drop: train={len(X_tr):,} valid={len(X_va):,} test={len(X_te):,}")

    # 7. LightGBM 学習
    print(f"[step 7] LightGBM training (early_stopping={EARLY_STOPPING_ROUNDS})")
    t_fit = time.time()
    model = lgb.LGBMRegressor(**LGB_DEFAULT_PARAMS)
    model.fit(
        X_tr, y_tr,
        eval_set=[(X_va, y_va)],
        eval_metric="rmse",
        callbacks=[lgb.early_stopping(stopping_rounds=EARLY_STOPPING_ROUNDS, verbose=False)],
    )
    elapsed_fit = time.time() - t_fit
    best_iter = model.best_iteration_
    print(f"[step 7] best_iter={best_iter} elapsed_fit={elapsed_fit:.2f}s")

    # 8. predict + metrics
    pred_tr = model.predict(X_tr)
    pred_va = model.predict(X_va)
    pred_te = model.predict(X_te)
    train_rmse = float(np.sqrt(mean_squared_error(y_tr, pred_tr)))
    valid_rmse = float(np.sqrt(mean_squared_error(y_va, pred_va)))
    test_rmse = float(np.sqrt(mean_squared_error(y_te, pred_te)))
    train_r2 = float(r2_score(y_tr, pred_tr))
    valid_r2 = float(r2_score(y_va, pred_va))
    test_r2 = float(r2_score(y_te, pred_te))
    label_std = float(y_tr.std())
    print(f"[step 8] train_rmse={train_rmse:.4f} / valid_rmse={valid_rmse:.4f} / test_rmse={test_rmse:.4f} (label_std={label_std:.4f})")
    print(f"[step 8] train_r2  ={train_r2:.4f} / valid_r2  ={valid_r2:.4f} / test_r2  ={test_r2:.4f}")

    # 9. feature_importance top 20 + leak verify + regime engagement verify
    fi = pd.DataFrame({
        "feature": X_tr.columns.tolist(),
        "importance": model.feature_importances_,
    }).sort_values("importance", ascending=False).reset_index(drop=True)
    fi.to_csv(OUT_DIR / "feature_importance_top20.csv", index=False)
    leak_check = verify_leak_in_top20(fi)
    regime_check = verify_regime_in_top50(fi)
    print(f"[step 9] feature_importance top 5:")
    for _, row in fi.head(5).iterrows():
        print(f"  {row['feature']}: {row['importance']}")
    print(f"[step 9] leak verify: blacklist hits={leak_check['blacklist_hits_count']} / suspicious hits={leak_check['suspicious_hits_count']}")
    if leak_check["blacklist_hits_count"] > 0:
        print(f"[step 9] ⚠️ BLACKLIST HIT: {leak_check['blacklist_hits']}")
    if leak_check["suspicious_hits_count"] > 0:
        print(f"[step 9] ⚠️ SUSPICIOUS HIT: {leak_check['suspicious_hits']}")
    print(f"[step 9] regime in top50: {regime_check['regime_in_top50_count']}/{regime_check['regime_total_count']} -> {regime_check['regime_in_top50']}")

    # 10. summary 出力
    total_elapsed = time.time() - t0
    summary = {
        "target": SMOKE_TARGET,
        "K": SMOKE_K,
        "fold": SMOKE_FOLD,
        "n_splits": N_SPLITS,
        "X_shape_with_regime": list(X.shape),
        "n_train_inner": int(len(X_tr)),
        "n_valid": int(len(X_va)),
        "n_test": int(len(X_te)),
        "best_iter": int(best_iter) if best_iter else None,
        "train_rmse": train_rmse,
        "valid_rmse": valid_rmse,
        "test_rmse": test_rmse,
        "train_r2": train_r2,
        "valid_r2": valid_r2,
        "test_r2": test_r2,
        "label_std": label_std,
        "elapsed_fit_sec": elapsed_fit,
        "elapsed_total_sec": total_elapsed,
        "leak_check": leak_check,
        "regime_check": regime_check,
        "lgb_params": LGB_DEFAULT_PARAMS,
    }
    out_summary = OUT_DIR / "smoke_summary.json"
    out_summary.write_text(json.dumps(summary, indent=2, default=str))
    print(f"[done] elapsed_total={total_elapsed:.2f}s -> {out_summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
