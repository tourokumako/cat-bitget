"""run_phase2_optuna_tune.py — [2] Entry ML §6.2.6 Optuna ハイパラ tune (3 系統共通)

目的:
  - §6.2.6 設計通り Optuna 30 trials × 3 系統別 tune
  - 各系統で代表 1 ラベル × fold 0 のみ評価 (= 計算コスト優先・系統内全 ラベルに best params 共通適用)
  - 出力: best_params_per_task.json (= regression / multiclass / binary それぞれの best params)

探索範囲 (= §6.2.6 業界 range):
  - num_leaves: 15-127
  - learning_rate: 0.01-0.1 (log scale)
  - min_child_samples: 20-100
  - max_depth: -1 (無制限) or 3-10 (= categorical)
  - reg_alpha: 0.0-1.0 (= L1 正則化)
  - reg_lambda: 0.0-1.0 (= L2 正則化)
  - early_stopping_rounds: 50 固定 (= tune 対象外)

代表ラベル (= 3 系統別):
  - regression: LONG_MFE_pct_K12
  - multiclass: triple_barrier_label_LONG_K12
  - binary: meta_label_LONG_K12

Optuna 設定:
  - sampler: TPE (= Tree-structured Parzen Estimator・default)
  - pruner: MedianPruner (= 中央値以下を早期打ち切り)
  - direction: minimize (= 各系統の objective metric 最小化)

scoring metric (= 系統別):
  - regression: valid_rmse 最小化
  - multiclass: valid_multi_logloss 最小化
  - binary: valid_binary_logloss 最小化

実行コマンド:
  .venv311/bin/python -m scripts.priority_rebuild.run_phase2_optuna_tune

出力:
  - results/priority_rebuild/ml_phase2_optuna/best_params_per_task.json
  - results/priority_rebuild/ml_phase2_optuna/study_{regression,multiclass,binary}.pkl
  - results/priority_rebuild/ml_phase2_optuna/optuna_run.log

所要: 30 trials × 約 3 分 × 3 系統 = 約 4.5 時間想定
"""

import argparse
import json
import sys
import time
from pathlib import Path

import joblib
import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd
from optuna.pruners import MedianPruner
from optuna.samplers import TPESampler
from sklearn.metrics import log_loss, mean_squared_error

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.priority_rebuild.run_phase1_v5_purged_kfold import (  # noqa: E402
    load_parquet_with_blacklist,
    prepare_purged_cv,
    split_with_purging,
)
from scripts.priority_rebuild.run_phase2_entry_ml_baseline import (  # noqa: E402
    merge_regime_columns,
    compute_class_weight,
    compute_scale_pos_weight,
    encode_tb_label,
    PARQUET_TRAIN,
    PARQUET_REGIME,
    LABEL_K_MAX,
    N_SPLITS,
    VALID_TAIL_FRACTION,
    EARLY_STOPPING_ROUNDS,
)

OUT_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase2_optuna"

# 代表ラベル (= 3 系統別)
REPRESENTATIVE_LABELS = {
    "regression": "LONG_MFE_pct_K12",
    "multiclass": "triple_barrier_label_LONG_K12",
    "binary": "meta_label_LONG_K12",
}

N_TRIALS = 30
TUNE_FOLD = 0


# ============== Optuna objective 関数 ==============

def _suggest_params(trial) -> dict:
    """Optuna trial から共通ハイパラ提案 (= §6.2.6 範囲)."""
    max_depth_choice = trial.suggest_categorical("max_depth_mode", ["unlimited", "limited"])
    if max_depth_choice == "unlimited":
        max_depth = -1
    else:
        max_depth = trial.suggest_int("max_depth_value", 3, 10)
    return {
        "num_leaves": trial.suggest_int("num_leaves", 15, 127),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.1, log=True),
        "min_child_samples": trial.suggest_int("min_child_samples", 20, 100),
        "max_depth": max_depth,
        "reg_alpha": trial.suggest_float("reg_alpha", 0.0, 1.0),
        "reg_lambda": trial.suggest_float("reg_lambda", 0.0, 1.0),
        "n_estimators": 1000,
        "random_state": 42,
        "n_jobs": -1,
        "verbose": -1,
    }


def make_objective_regression(X_tr, y_tr, X_va, y_va):
    def objective(trial):
        params = {**_suggest_params(trial), "objective": "regression", "metric": "rmse"}
        model = lgb.LGBMRegressor(**params)
        model.fit(X_tr, y_tr,
                  eval_set=[(X_va, y_va)], eval_metric="rmse",
                  callbacks=[lgb.early_stopping(EARLY_STOPPING_ROUNDS, verbose=False)])
        pred_va = model.predict(X_va)
        return float(np.sqrt(mean_squared_error(y_va, pred_va)))
    return objective


def make_objective_multiclass(X_tr, y_tr, X_va, y_va):
    y_tr_e = encode_tb_label(y_tr)
    y_va_e = encode_tb_label(y_va)
    class_w = compute_class_weight(y_tr_e)

    def objective(trial):
        params = {**_suggest_params(trial),
                  "objective": "multiclass", "metric": "multi_logloss",
                  "num_class": 3, "class_weight": class_w}
        model = lgb.LGBMClassifier(**params)
        model.fit(X_tr, y_tr_e,
                  eval_set=[(X_va, y_va_e)], eval_metric="multi_logloss",
                  callbacks=[lgb.early_stopping(EARLY_STOPPING_ROUNDS, verbose=False)])
        pred_proba = model.predict_proba(X_va)
        return float(log_loss(y_va_e, pred_proba, labels=[0, 1, 2]))
    return objective


def make_objective_binary(X_tr, y_tr, X_va, y_va):
    y_tr_i = y_tr.astype(int)
    y_va_i = y_va.astype(int)
    spw = compute_scale_pos_weight(y_tr_i)

    def objective(trial):
        params = {**_suggest_params(trial),
                  "objective": "binary", "metric": "binary_logloss",
                  "scale_pos_weight": spw}
        model = lgb.LGBMClassifier(**params)
        model.fit(X_tr, y_tr_i,
                  eval_set=[(X_va, y_va_i)], eval_metric="binary_logloss",
                  callbacks=[lgb.early_stopping(EARLY_STOPPING_ROUNDS, verbose=False)])
        pred_proba = model.predict_proba(X_va)[:, 1]
        return float(log_loss(y_va_i, pred_proba))
    return objective


OBJECTIVE_FACTORIES = {
    "regression": make_objective_regression,
    "multiclass": make_objective_multiclass,
    "binary": make_objective_binary,
}


# ============== Data prep (= 共通) ==============

def prepare_fold_data(label_name: str, X: pd.DataFrame, y_dict: dict,
                       index: pd.DatetimeIndex, fold_splits: list, fold_idx: int) -> tuple:
    """fold データ準備 (train_inner / valid / test 分割 + NaN drop)."""
    # y_target 抽出
    y_target = None
    for prefix, df in y_dict.items():
        if label_name in df.columns:
            y_target = df[label_name]
            break
    if y_target is None:
        raise KeyError(f"label not found: {label_name}")

    train_idx, test_idx = fold_splits[fold_idx]
    n_train = len(train_idx)
    n_valid = int(n_train * VALID_TAIL_FRACTION)
    train_inner = train_idx[:n_train - n_valid]
    valid_idx = train_idx[n_train - n_valid:]

    X_tr, y_tr = X.iloc[train_inner], y_target.iloc[train_inner]
    X_va, y_va = X.iloc[valid_idx], y_target.iloc[valid_idx]
    mask_tr = ~y_tr.isnull()
    mask_va = ~y_va.isnull()
    X_tr, y_tr = X_tr.loc[mask_tr], y_tr.loc[mask_tr]
    X_va, y_va = X_va.loc[mask_va], y_va.loc[mask_va]
    return X_tr, y_tr, X_va, y_va


# ============== main ==============

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="[2] Entry ML Optuna tune (3 task systems)")
    p.add_argument("--n-trials", type=int, default=N_TRIALS,
                   help=f"Optuna trials per system (default: {N_TRIALS})")
    p.add_argument("--task", type=str, choices=["regression", "multiclass", "binary"],
                   default=None, help="特定 task のみ tune (= 動作確認用)")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    t_start = time.time()
    print(f"[start] Optuna tune ({pd.Timestamp.now()}) / n_trials={args.n_trials}")

    # 1. load data (= baseline と同様)
    print(f"[step 1] load parquet: {PARQUET_TRAIN.name}")
    X, y_dict, index = load_parquet_with_blacklist(PARQUET_TRAIN, verbose=True)
    print(f"[step 2] merge regime: {PARQUET_REGIME.name}")
    X = merge_regime_columns(X, PARQUET_REGIME)
    print(f"[step 2] X shape: {X.shape}")

    # 2. CV split (= K_max=288 統一)
    print(f"[step 3] prepare_purged_cv n_splits={N_SPLITS} K_embargo={LABEL_K_MAX}")
    cv = prepare_purged_cv(n_splits=N_SPLITS)
    fold_splits = list(split_with_purging(cv, X, index, K=LABEL_K_MAX))
    print(f"[step 3] fold yielded: {len(fold_splits)}")

    # 3. 3 系統別 Optuna tune
    target_tasks = [args.task] if args.task else ["regression", "multiclass", "binary"]
    results = {}
    for task in target_tasks:
        label = REPRESENTATIVE_LABELS[task]
        print(f"\n[step 4-{task}] tune task={task} representative={label} fold={TUNE_FOLD}")
        t_task = time.time()

        X_tr, y_tr, X_va, y_va = prepare_fold_data(
            label, X, y_dict, index, fold_splits, TUNE_FOLD,
        )
        print(f"  data: train={len(X_tr):,} valid={len(X_va):,}")

        objective = OBJECTIVE_FACTORIES[task](X_tr, y_tr, X_va, y_va)
        study = optuna.create_study(
            direction="minimize",
            sampler=TPESampler(seed=42),
            pruner=MedianPruner(n_startup_trials=5, n_warmup_steps=10),
            study_name=f"phase2_{task}",
        )
        study.optimize(objective, n_trials=args.n_trials, show_progress_bar=False)
        elapsed_task = time.time() - t_task
        print(f"  done: best={study.best_value:.6f} elapsed={elapsed_task:.0f}s ({elapsed_task/60:.1f}min)")
        print(f"  best_params: {study.best_params}")

        # study artifact 保存
        joblib.dump(study, OUT_DIR / f"study_{task}.pkl")

        # best params 正規化 (= max_depth_mode/value を実 max_depth に変換)
        bp = dict(study.best_params)
        if bp.get("max_depth_mode") == "unlimited":
            max_depth = -1
        else:
            max_depth = bp.get("max_depth_value", -1)
        bp_clean = {
            "num_leaves": bp["num_leaves"],
            "learning_rate": bp["learning_rate"],
            "min_child_samples": bp["min_child_samples"],
            "max_depth": max_depth,
            "reg_alpha": bp["reg_alpha"],
            "reg_lambda": bp["reg_lambda"],
        }
        results[task] = {
            "best_params": bp_clean,
            "best_value": float(study.best_value),
            "n_trials": args.n_trials,
            "representative_label": label,
            "tune_fold": TUNE_FOLD,
            "elapsed_sec": elapsed_task,
            "all_trials_values": [t.value for t in study.trials if t.value is not None],
        }

    # 4. JSON 出力
    out_json = OUT_DIR / "best_params_per_task.json"
    out_json.write_text(json.dumps(results, indent=2, default=str))
    elapsed_total = time.time() - t_start
    print(f"\n[done] total elapsed: {elapsed_total:.0f}s ({elapsed_total/60:.1f}min = {elapsed_total/3600:.2f}h)")
    print(f"[done] best_params: {out_json}")

    # summary print
    print("\n=== best params summary ===")
    for task, r in results.items():
        print(f"{task}: best_value={r['best_value']:.6f} params={r['best_params']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
