#!/usr/bin/env python3
"""
run_k12long_refit.py — K12 LONG MFE / K12 LONG MAE のみ num_leaves=15 で再学習

指示書: .claude/instructions/2026-05-14_phase1_k12long_refit.md

差分 (vs run_lgbm_phase1.py):
- 学習対象を K12_LONG_MFE / K12_LONG_MAE の 2 ラベルに限定
- num_leaves=15 (Phase 1 デフォルト 31 → 15)
- 出力:
  - 新モデル 2 つ (results/priority_rebuild/ml_phase1_k12long_refit/models/)
  - predictions_test2025_k12long_refit.parquet (K12 LONG 2 列のみ refit 版・他 14 列は Phase 1 維持)
  - predictions_train_2021_2024_k12long_refit.parquet (同上)
  - entry_thresholds_k12long_refit.json (K12 LONG のみ新値・他は Phase 1 維持)
- seed 系・num_threads=1 は Phase 1 と同一 (bit-exact 再現性)
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "results" / "priority_rebuild"
PHASE1_DIR = DATA_DIR / "ml_phase1"
OUT_DIR = DATA_DIR / "ml_phase1_k12long_refit"
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

# refit 対象 (K12 LONG MFE / K12 LONG MAE のみ・num_leaves=15)
REFIT_LABELS = ["LONG_MFE_K12", "LONG_MAE_K12"]
NUM_LEAVES_REFIT = 15

THRESHOLD_QUANTILES = [0.90, 0.95, 0.99]

TS = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
LOG_PATH = OUT_DIR / f"refit_log_{TS}.txt"


def log(msg: str) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{now}] {msg}"
    print(line, flush=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")


def train_label(label: str, Xt, yt, Xv, yv, feature_cols):
    params = dict(
        objective="regression",
        metric="rmse",
        learning_rate=0.02,
        num_leaves=NUM_LEAVES_REFIT,
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
        Xt, yt,
        eval_set=[(Xt, yt), (Xv, yv)],
        eval_names=["train", "valid"],
        callbacks=[
            lgb.early_stopping(EARLY_STOPPING_ROUNDS, verbose=False),
            lgb.log_evaluation(period=0),
            lgb.record_evaluation(evals),
        ],
    )
    curves = pd.DataFrame({
        "iter": range(len(evals["train"]["rmse"])),
        "train_rmse": evals["train"]["rmse"],
        "valid_rmse": evals["valid"]["rmse"],
    })
    imp = pd.Series(model.feature_importances_, index=feature_cols).sort_values(ascending=False)
    return model, curves, imp


def main() -> None:
    t0 = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    log("=== K12 LONG refit START ===")
    log(f"refit targets: {REFIT_LABELS}")
    log(f"num_leaves: {NUM_LEAVES_REFIT}")
    log(f"output: {OUT_DIR}")

    log("loading train parquet ...")
    df_train_full = pd.read_parquet(TRAIN_PARQUET)
    log(f"  train: {df_train_full.shape}")
    log("loading test parquet ...")
    df_test = pd.read_parquet(TEST_PARQUET)
    log(f"  test : {df_test.shape}")

    feature_cols = [c for c in df_train_full.columns if c not in LABEL_COLS + META_COLS]
    assert len(feature_cols) == 1432, f"expected 1432 features, got {len(feature_cols)}"

    n_total = len(df_train_full)
    n_valid = int(n_total * VALID_RATIO)
    n_train = n_total - n_valid
    log(f"split: train={n_train} / valid={n_valid}")

    X_train = df_train_full.iloc[:n_train][feature_cols]
    X_valid = df_train_full.iloc[n_train:][feature_cols]
    X_train_full = df_train_full[feature_cols]
    X_test = df_test[feature_cols]

    new_preds_test = {}
    new_preds_train = {}
    new_preds_valid = {}

    for label in REFIT_LABELS:
        t_label = time.time()
        log(f"--- training {label} (num_leaves={NUM_LEAVES_REFIT}) ---")
        y_train = df_train_full.iloc[:n_train][label]
        y_valid = df_train_full.iloc[n_train:][label]
        mask_t = y_train.notna()
        mask_v = y_valid.notna()
        Xt, yt = X_train[mask_t], y_train[mask_t]
        Xv, yv = X_valid[mask_v], y_valid[mask_v]

        model, curves, imp = train_label(label, Xt, yt, Xv, yv, feature_cols)
        elapsed = (time.time() - t_label) / 60
        best_iter = model.best_iteration_
        valid_rmse_best = curves["valid_rmse"].min()
        log(f"  best_iter={best_iter} valid_rmse_best={valid_rmse_best:.6f} elapsed={elapsed:.2f} min")

        # save model
        model_path = MODELS_DIR / f"lgbm_{label}.txt"
        model.booster_.save_model(str(model_path))
        log(f"  saved model: {model_path.name}")

        # save iteration log
        curves.to_csv(OUT_DIR / f"lgbm_{label}_iteration_log.csv", index=False)

        # save top20 importance
        imp.head(20).to_csv(OUT_DIR / f"feature_importance_top20_{label}.csv", header=["importance"])
        log(f"  top5 importance: {list(imp.head(5).items())}")

        # predict
        new_preds_test[label] = model.predict(X_test)
        new_preds_valid[label] = model.predict(X_valid)
        new_preds_train[label] = model.predict(X_train_full)
        log(f"  pred test mean={new_preds_test[label].mean():.4f} std={new_preds_test[label].std():.4f}")

    # === Phase 1 predictions と merge して新 parquet を生成 ===
    log("loading Phase 1 predictions for merge ...")
    p1_test = pd.read_parquet(PHASE1_DIR / "predictions_test2025.parquet")
    p1_train = pd.read_parquet(PHASE1_DIR / "predictions_train_2021_2024.parquet")
    log(f"  P1 test: {p1_test.shape} / P1 train: {p1_train.shape}")

    # K12 LONG MFE / MAE のみ refit 値で上書き
    refit_test = p1_test.copy()
    refit_train = p1_train.copy()
    for label in REFIT_LABELS:
        # bit-exact 確認用に旧値を一時保存
        old_test = p1_test[label].copy()
        old_train = p1_train[label].copy()
        refit_test[label] = new_preds_test[label]
        refit_train[label] = new_preds_train[label]
        log(f"  {label}: old mean={old_test.mean():.4f} → new mean={new_preds_test[label].mean():.4f}")

    # 他 14 ラベルが bit-exact 同一であることを assert
    untouched_labels = [c for c in p1_test.columns if c not in REFIT_LABELS and c != "close"]
    for lab in untouched_labels:
        assert refit_test[lab].equals(p1_test[lab]), f"untouched label {lab} differs!"
        assert refit_train[lab].equals(p1_train[lab]), f"untouched label {lab} differs (train)!"
    log(f"  ✅ untouched 14 labels bit-exact 同一確認 ({len(untouched_labels)} labels checked)")

    refit_test.to_parquet(OUT_DIR / "predictions_test2025_k12long_refit.parquet")
    refit_train.to_parquet(OUT_DIR / "predictions_train_2021_2024_k12long_refit.parquet")
    log("saved refit predictions parquets")

    # === entry_thresholds を更新 (K12 LONG のみ・他は Phase 1 維持) ===
    with open(PHASE1_DIR / "entry_thresholds.json") as f:
        thresholds = json.load(f)
    # K12 LONG の閾値を新 valid 予測値から再計算
    pmfe = pd.Series(new_preds_valid["LONG_MFE_K12"], index=X_valid.index)
    pmae = pd.Series(new_preds_valid["LONG_MAE_K12"], index=X_valid.index)
    ratio = pmfe / pmae.replace(0, np.nan)
    new_k12_long_thresholds = {f"q{int(q*100)}": float(ratio.quantile(q)) for q in THRESHOLD_QUANTILES}
    log(f"  K12 LONG thresholds (old): {thresholds['K12']['LONG']}")
    log(f"  K12 LONG thresholds (new): {new_k12_long_thresholds}")
    thresholds["K12"]["LONG"] = new_k12_long_thresholds
    with open(OUT_DIR / "entry_thresholds_k12long_refit.json", "w") as f:
        json.dump(thresholds, f, indent=2)
    log("saved entry_thresholds_k12long_refit.json (K12 LONG のみ更新・他 7 組合せは Phase 1 維持)")

    # training_summary.csv も Phase 1 と merge して新版作成
    p1_summary = pd.read_csv(PHASE1_DIR / "training_summary.csv")
    new_rows = []
    for label in REFIT_LABELS:
        sub = pd.read_csv(OUT_DIR / f"lgbm_{label}_iteration_log.csv")
        best_idx = sub["valid_rmse"].idxmin()
        new_rows.append({
            "label": label,
            "best_iter": int(sub.iloc[best_idx]["iter"]),
            "n_iter": int(sub["iter"].max() + 1),
            "train_rmse": float(sub.iloc[best_idx]["train_rmse"]),
            "valid_rmse": float(sub.iloc[best_idx]["valid_rmse"]),
            "乖離率": float(sub.iloc[best_idx]["valid_rmse"] / sub.iloc[best_idx]["train_rmse"])
            if sub.iloc[best_idx]["train_rmse"] > 0 else float("nan"),
        })
    refit_summary = p1_summary.copy()
    for r in new_rows:
        refit_summary.loc[refit_summary["label"] == r["label"],
                          ["best_iter", "n_iter", "train_rmse", "valid_rmse", "乖離率"]] = (
            r["best_iter"], r["n_iter"], r["train_rmse"], r["valid_rmse"], r["乖離率"]
        )
    # ensure "判定" column is preserved if exists (just copy from Phase 1)
    refit_summary.to_csv(OUT_DIR / "training_summary.csv", index=False)
    log("saved training_summary.csv (K12 LONG MFE/MAE のみ refit 値・他 14 は Phase 1)")

    elapsed = time.time() - t0
    log(f"=== K12 LONG refit END (elapsed={elapsed/60:.2f} min) ===")


if __name__ == "__main__":
    main()
