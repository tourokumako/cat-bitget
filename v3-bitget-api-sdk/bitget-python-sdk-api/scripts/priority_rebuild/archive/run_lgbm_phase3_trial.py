#!/usr/bin/env python3
"""
run_lgbm_phase3_trial.py — Phase 3 短期試行: K 窓別 num_leaves 調整

指示書: .claude/instructions/2026-05-14_phase3_short_trial.md (Web Claude 評価 + 監査#3 案E)

差分 (vs run_lgbm_phase1.py):
- num_leaves を K 窓別に変更 (K12/K24=15・K48/K96=31)
- 出力先: results/priority_rebuild/ml_phase3_trial/
- leak-pause ロジック削除 (Phase 1 で既に検証済)
- random_state / seed 系・num_threads=1 は Phase 1 と同一

旧 Phase 3-b 設定の移植 (handoff_v3 §2.1 / handoff_v4 §2)・leak 由来結果なので
保証はないが Phase 4 着手前の追加情報収集として実施。
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import lightgbm as lgb
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "results" / "priority_rebuild"
OUT_DIR = DATA_DIR / "ml_phase3_trial"
MODELS_DIR = OUT_DIR / "models"

TRAIN_PARQUET = DATA_DIR / "labels_mfe_mae_train_2021_2024.parquet"
TEST_PARQUET = DATA_DIR / "labels_mfe_mae_test_2025.parquet"

LABEL_COLS = [
    f"{side}_{kind}_K{k}"
    for k in (12, 24, 48, 96)
    for side in ("LONG", "SHORT")
    for kind in ("MFE", "MAE")
]
META_COLS = ["close"]
VALID_RATIO = 0.10
RANDOM_STATE = 42
EARLY_STOPPING_ROUNDS = 50
N_ESTIMATORS = 5000

THRESHOLD_QUANTILES = [0.90, 0.95, 0.99]

POS_SIZE_BTC = 0.12
FEE_RATE_MAKER = 0.00014
ROUND_TRIP_FEE = FEE_RATE_MAKER * 2

TS = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
LOG_PATH = OUT_DIR / f"lgbm_log_{TS}.txt"


def get_num_leaves(K: int) -> int:
    """旧 Phase 3-b 設定の移植 (handoff_v3 §2.1 / handoff_v4 §2)"""
    if K in (12, 24):
        return 15  # 短期は浅い木
    elif K in (48, 96):
        return 31  # 長期は深い木 (LightGBM デフォルト相当)
    else:
        raise ValueError(f"Unexpected K: {K}")


def log(msg: str) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{now}] {msg}"
    print(line, flush=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")


def train_one_label(
    label: str,
    K: int,
    Xt: pd.DataFrame,
    yt: pd.Series,
    Xv: pd.DataFrame,
    yv: pd.Series,
    feature_cols: list[str],
) -> tuple[lgb.LGBMRegressor, list[tuple], list[tuple], int]:
    """1 ラベル分の学習。num_leaves を K 窓別に設定。"""
    num_leaves = get_num_leaves(K)
    params = dict(
        objective="regression",
        metric="rmse",
        learning_rate=0.02,
        num_leaves=num_leaves,
        min_data_in_leaf=100,
        feature_fraction=0.7,
        bagging_fraction=0.8,
        bagging_freq=5,
        reg_lambda=0.1,
        n_estimators=N_ESTIMATORS,
        random_state=RANDOM_STATE,
        bagging_seed=42,
        data_random_seed=42,
        feature_fraction_seed=42,
        verbose=-1,
        n_jobs=1,
    )
    evals: dict = {}
    model = lgb.LGBMRegressor(**params)
    model.fit(
        Xt,
        yt,
        eval_set=[(Xt, yt), (Xv, yv)],
        eval_names=["train", "valid"],
        callbacks=[
            lgb.early_stopping(EARLY_STOPPING_ROUNDS, verbose=False),
            lgb.log_evaluation(period=0),
            lgb.record_evaluation(evals),
        ],
    )
    curves = [
        (label, it, float(tr), float(vl))
        for it, (tr, vl) in enumerate(zip(evals["train"]["rmse"], evals["valid"]["rmse"]))
    ]
    imp = pd.Series(model.feature_importances_, index=feature_cols).sort_values(ascending=False)
    importance = [
        (label, rank, feat, int(val))
        for rank, (feat, val) in enumerate(imp.head(20).items(), 1)
    ]
    return model, curves, importance, num_leaves


def extract_K(label: str) -> int:
    """ラベル名から K 窓値を抽出 (例: LONG_MFE_K12 → 12)."""
    return int(label.split("_K")[-1])


def main() -> None:
    t0 = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    log("=== ML Phase 3 Trial START (K 窓別 num_leaves) ===")
    log(f"lightgbm: {lgb.__version__}")
    log(f"train: {TRAIN_PARQUET}")
    log(f"test : {TEST_PARQUET}")
    log(f"out  : {OUT_DIR}")
    log(f"num_leaves: K12/K24=15 / K48/K96=31")

    log("loading train parquet ...")
    df_train_full = pd.read_parquet(TRAIN_PARQUET)
    log(f"  train: {df_train_full.shape} index={type(df_train_full.index).__name__}")
    log("loading test parquet ...")
    df_test = pd.read_parquet(TEST_PARQUET)
    log(f"  test : {df_test.shape}")

    feature_cols = [c for c in df_train_full.columns if c not in LABEL_COLS + META_COLS]
    log(f"feature_cols: {len(feature_cols)}")
    assert len(feature_cols) == 1432, f"expected 1432 features, got {len(feature_cols)}"

    n_total = len(df_train_full)
    n_valid = int(n_total * VALID_RATIO)
    n_train = n_total - n_valid
    log(
        f"split: train={n_train} ({df_train_full.index[0]} → {df_train_full.index[n_train-1]}) "
        f"valid={n_valid} ({df_train_full.index[n_train]} → {df_train_full.index[-1]})"
    )

    X_train_all = df_train_full.iloc[:n_train][feature_cols]
    X_valid_all = df_train_full.iloc[n_train:][feature_cols]
    X_test = df_test[feature_cols]

    training_curves: list[tuple] = []
    importance_records: list[tuple] = []
    pred_test = pd.DataFrame(index=df_test.index)
    pred_valid = pd.DataFrame(index=X_valid_all.index)

    nl_records: list[dict] = []

    for i, label in enumerate(LABEL_COLS, 1):
        t_label = time.time()
        K = extract_K(label)
        nl = get_num_leaves(K)
        log(f"--- model [{i}/16] {label} (K={K} num_leaves={nl}) ---")
        y_train = df_train_full.iloc[:n_train][label]
        y_valid = df_train_full.iloc[n_train:][label]
        mask_t = y_train.notna()
        mask_v = y_valid.notna()
        log(f"  drop NaN: train {(~mask_t).sum()}, valid {(~mask_v).sum()}")
        Xt, yt = X_train_all[mask_t], y_train[mask_t]
        Xv, yv = X_valid_all[mask_v], y_valid[mask_v]

        model, curves, importance, used_nl = train_one_label(label, K, Xt, yt, Xv, yv, feature_cols)
        training_curves.extend(curves)
        importance_records.extend(importance)
        nl_records.append(dict(label=label, K=K, num_leaves=used_nl))

        iter_df = pd.DataFrame(
            [(it, tr, vl) for _, it, tr, vl in curves],
            columns=["iter", "train_rmse", "valid_rmse"]
        )
        iter_df.to_csv(OUT_DIR / f"lgbm_{label}_iteration_log.csv", index=False)

        best_iter = model.best_iteration_
        valid_rmse_best = min(c[3] for c in curves)
        train_rmse_best = curves[best_iter][2] if best_iter < len(curves) else curves[-1][2]
        log(f"  best_iter={best_iter} valid_rmse_best={valid_rmse_best:.6f}")

        model_path = MODELS_DIR / f"lgbm_{label}.txt"
        model.booster_.save_model(str(model_path))

        top1_share = importance[0][3] / sum(int(v) for v in model.feature_importances_) if sum(model.feature_importances_) > 0 else 0
        log(f"  top1: {importance[0][2]} importance_share={top1_share:.3f}")

        pred_valid[label] = model.predict(X_valid_all)
        pred_test[label] = model.predict(X_test)
        std_t = pred_test[label].std()
        log(f"  test pred: mean={pred_test[label].mean():.4f} std={std_t:.4f}")
        log(f"  elapsed (this model): {(time.time()-t_label)/60:.2f} min")

    # save num_leaves config record
    pd.DataFrame(nl_records).to_csv(OUT_DIR / "num_leaves_config.csv", index=False)
    log("saved num_leaves_config.csv")

    pd.DataFrame(training_curves, columns=["label", "iter", "train_rmse", "valid_rmse"]).to_csv(
        OUT_DIR / "training_curves.csv", index=False
    )
    log("saved training_curves.csv")

    pd.DataFrame(importance_records, columns=["label", "rank", "feature", "importance"]).to_csv(
        OUT_DIR / "feature_importance_top20.csv", index=False
    )
    log("saved feature_importance_top20.csv")

    pred_out = pred_test.copy()
    pred_out["close"] = df_test["close"].values
    pred_out.to_parquet(OUT_DIR / "predictions_test2025.parquet")
    log("saved predictions_test2025.parquet")

    # training_summary.csv (Phase 1 と同形式・Phase 2 評価で使用)
    train_curves_df = pd.DataFrame(training_curves, columns=["label", "iter", "train_rmse", "valid_rmse"])
    rows = []
    for label in LABEL_COLS:
        sub = train_curves_df[train_curves_df.label == label]
        if sub.empty:
            continue
        best_idx = sub["valid_rmse"].idxmin()
        best_row = sub.loc[best_idx]
        valid_rmse = float(best_row["valid_rmse"])
        train_rmse = float(best_row["train_rmse"])
        ratio = valid_rmse / train_rmse if train_rmse > 0 else float("nan")
        rows.append(dict(
            label=label,
            best_iter=int(best_row["iter"]),
            n_iter=int(sub["iter"].max() + 1),
            train_rmse=train_rmse,
            valid_rmse=valid_rmse,
            乖離率=ratio,
        ))
    pd.DataFrame(rows).to_csv(OUT_DIR / "training_summary.csv", index=False)
    log("saved training_summary.csv")

    # Entry 規則閾値 (Phase 1 と同形式)
    thresholds: dict[str, dict[str, dict[str, float]]] = {}
    for k in (12, 24, 48, 96):
        thresholds[f"K{k}"] = {}
        for side in ("LONG", "SHORT"):
            pmfe = pred_valid[f"{side}_MFE_K{k}"]
            pmae = pred_valid[f"{side}_MAE_K{k}"]
            ratio = pmfe / pmae.replace(0, np.nan)
            qs = {f"q{int(q*100)}": float(ratio.quantile(q)) for q in THRESHOLD_QUANTILES}
            thresholds[f"K{k}"][side] = qs
            log(f"  thr K{k} {side}: {qs}")
    with open(OUT_DIR / "entry_thresholds.json", "w") as f:
        json.dump(thresholds, f, indent=2)
    log("saved entry_thresholds.json")

    elapsed = time.time() - t0
    log(f"=== ML Phase 3 Trial END (elapsed={elapsed/60:.1f} min) ===")


if __name__ == "__main__":
    main()
