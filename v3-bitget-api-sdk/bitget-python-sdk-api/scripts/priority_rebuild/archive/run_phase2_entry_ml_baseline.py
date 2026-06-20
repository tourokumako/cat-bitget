"""run_phase2_entry_ml_baseline.py — [2] Entry ML baseline (= 56 ラベル × 3 fold × LightGBM default)

目的:
  - ml_pipeline_baseline_v1.md §6.2 baseline (= ハイパラ tune 抜き) 第一段階実装
  - 56 ラベル (= 揺れ幅 28 回帰 + Triple Barrier 14 多クラス + meta_label 14 二値) を全 fold で並列学習
  - Stage 1 統計指標 (= RMSE/R²/multi_logloss/F1/AUC/Brier/ECE) を 56 モデル全部について出力
  - leak verify 経路: blacklist 混入即停止 + 怪しい列名 (= fractal/pivot/resistance/support) 検出 + regime engagement

設計引継ぎ (§6.2 から):
  §6.2.1 ✅ Stage 1 評価指標 (= 統計のみ・Stage 2-4 は別 Phase)
  §6.2.2 ✅ LightGBM 56 個独立並列学習 (= stacking は Stage 3 後判定・本 baseline では LightGBM 単独)
  §6.2.3 ✅ 56 ラベル + class_weight='balanced' (Triple Barrier) + scale_pos_weight (meta_label)
         ✅ K 別 ATR_pct multiplier は Phase 0 で実装済 (= build_labels_pct.py L106-108・TP_MULT=2.0/SL_MULT=1.5 固定・K 別調整は第二段階)
  §6.2.4 ✅ 入力 2,604 列 + regime 8 列 (= prob 4 + one-hot 4) = 2,612 列
  §6.2.5 ✅ Walk-Forward Purged K-Fold 3 fold + embargo K_max=288 (= 24h = 288 bar) で全 K 統一
         📝 設計 §6.2.5 「5 fold」は yield 後 3 fold (= timeseriescv default min_train_splits=2)・本走 3 fold で進める
  §6.2.6 ❌ ハイパラ tune (Optuna) は Step 5 で別 script で実装・本 baseline は LightGBM default
  §6.2.7 ❌ entry 判定 (= ルール集約・threshold・即死 reject) は Step 6 で別 script で実装
  §6.2.8 ✅ leak 防止 (= 4 点 verify + regime causal alignment + ラベル shift(-K) 既済 + embargo K_max + blacklist drop)
         📝 fractal 4 項目セット自動実行 (verify_top20_features_leak.py 自動 invoke) は Step 5 で実装・本 baseline は「top20 fractal hit 検出 + 警告ログ」のみ

isotonic regression キャリブレーション (= §6.2.3 論点 4):
  - Triple Barrier multiclass 14: class_weight='balanced' 適用後 predict_proba → fold 別 isotonic で post-hoc キャリブレーション (= class 別に 3 ラベル独立 isotonic)
  - meta_label binary 14: scale_pos_weight 適用後 predict_proba → fold 別 isotonic (= 1 ラベル独立 isotonic)
  - 揺れ幅系 28 回帰: キャリブレーション不要

実行モード:
  --smoke           : 1 ラベル × 1 fold (= 既存 run_phase2_entry_ml_smoke.py と同等・動作確認用)
  --label LONG_MFE_pct_K12 --fold 0   : 特定 label × 特定 fold のみ実行
  (引数なし)         : 56 ラベル × 3 fold 全走 (= 約 9-10 時間 sequential)

出力:
  - results/priority_rebuild/ml_phase2_baseline/baseline_run.log
  - results/priority_rebuild/ml_phase2_baseline/{label}_fold{i}/metrics.json
  - results/priority_rebuild/ml_phase2_baseline/{label}_fold{i}/feature_importance_top20.csv
  - results/priority_rebuild/ml_phase2_baseline/{label}_fold{i}/calibrator.joblib (Triple Barrier / meta_label のみ)
  - results/priority_rebuild/ml_phase2_baseline/summary.json (= 56 モデル × 3 fold = 168 学習の集計)
  - results/priority_rebuild/ml_phase2_baseline/leak_verify.json (= blacklist + fractal hit 集計)
"""

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import (
    accuracy_score, f1_score, log_loss, mean_squared_error,
    r2_score, roc_auc_score, brier_score_loss,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.priority_rebuild.run_phase1_v5_purged_kfold import (  # noqa: E402
    load_parquet_with_blacklist,
    prepare_purged_cv,
    split_with_purging,
)

# I/O paths
PARQUET_TRAIN = REPO_ROOT / "results" / "priority_rebuild" / "labels_mfe_mae_pct_train_2021_2024.parquet"
PARQUET_REGIME = REPO_ROOT / "results" / "regime_step1" / "regime_predictions_train_2021_2024.parquet"
OUT_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase2_baseline"

# 56 ラベル定義 (§6.2.3 + Phase 0 v3.1 既存)
K_BARS = [6, 12, 24, 48, 96, 144, 288]
LABEL_K_MAX = 288  # CV embargo 計算用 (= 24h 分・全 K 統一)
LABEL_SYSTEMS = {
    "regression": {
        "prefixes": ["LONG_MFE_pct", "LONG_MAE_pct", "SHORT_MFE_pct", "SHORT_MAE_pct"],
        "n_labels": 28,
        "objective": "regression",
        "metric": "rmse",
        "imbalance": None,
        "calibration": False,
    },
    "multiclass": {
        "prefixes": ["triple_barrier_label"],
        "n_labels": 14,
        "objective": "multiclass",
        "metric": "multi_logloss",
        "imbalance": "class_weight",
        "calibration": True,  # isotonic per class
        "num_class": 3,  # SL=-1, TIME=0, TP=1 → label encode 0/1/2
    },
    "binary": {
        "prefixes": ["meta_label"],
        "n_labels": 14,
        "objective": "binary",
        "metric": "binary_logloss",
        "imbalance": "scale_pos_weight",
        "calibration": True,  # isotonic
    },
}

# regime 入力 (= §6.2.4 論点 4 「両方使う = 8 列」)
REGIME_COLS = [
    "regime_prob_up", "regime_prob_down", "regime_prob_range", "regime_confidence",
    "regime_is_uptrend", "regime_is_downtrend", "regime_is_range", "regime_is_unclear",
]

# leak verify
BLACKLIST_FAMILIES = (
    "sma_20", "sma_50", "ichimoku_kijun", "ichimoku_tenkan",
    "macd_line", "macd_signal", "macd_hist", "macd_hist_change",
)
SUSPICIOUS_PATTERNS = ["fractal", "pivot", "resistance", "support", "future", "look_ahead"]

# LightGBM default (= §6.2.6 業界 range 中央値)
LGB_DEFAULT_PARAMS_BASE = {
    "num_leaves": 31,
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
VALID_TAIL_FRACTION = 0.10
N_SPLITS = 5  # PurgedWalkForwardCV n_splits=5 → 実 yield 3 fold


# ============== ユーティリティ ==============

def merge_regime_columns(X: pd.DataFrame, regime_path: Path) -> pd.DataFrame:
    df_r = pd.read_parquet(regime_path)
    missing = [c for c in REGIME_COLS if c not in df_r.columns]
    if missing:
        raise KeyError(f"regime parquet missing columns: {missing}")
    df_r_aligned = df_r[REGIME_COLS].reindex(X.index)
    return pd.concat([X, df_r_aligned], axis=1)


def get_all_label_names(y_dict: dict) -> dict:
    """y_dict から 56 ラベル名を task_type 別に集約."""
    out = {"regression": [], "multiclass": [], "binary": []}
    for task_type, spec in LABEL_SYSTEMS.items():
        for prefix in spec["prefixes"]:
            if prefix in y_dict:
                cols = sorted(y_dict[prefix].columns.tolist())
                out[task_type].extend(cols)
    return out


def encode_tb_label(y: pd.Series) -> pd.Series:
    """Triple Barrier -1/0/1 → 0/1/2 (LightGBM multiclass 用)."""
    return (y + 1).astype(int)


def compute_class_weight(y: pd.Series) -> dict:
    """sklearn class_weight='balanced' 相当 (= n_samples / (n_classes * np.bincount))."""
    counts = y.value_counts().to_dict()
    n_total = len(y)
    n_classes = len(counts)
    return {c: n_total / (n_classes * cnt) for c, cnt in counts.items()}


def compute_scale_pos_weight(y: pd.Series) -> float:
    """binary scale_pos_weight = neg / pos."""
    pos = int((y == 1).sum())
    neg = int((y == 0).sum())
    return neg / pos if pos > 0 else 1.0


def detect_leak_hits(fi_df: pd.DataFrame, top_n: int = 20) -> dict:
    top = fi_df.head(top_n)
    blacklist_hits, suspicious_hits = [], []
    for c in top["feature"]:
        for f in BLACKLIST_FAMILIES:
            if c.startswith(f + "__"):
                blacklist_hits.append((c, f))
                break
        for p in SUSPICIOUS_PATTERNS:
            if p in c.lower():
                suspicious_hits.append((c, p))
                break
    return {
        "blacklist_hits": blacklist_hits,
        "suspicious_hits": suspicious_hits,
        "top_features": top["feature"].tolist()[:5],
    }


def regime_in_topN(fi_df: pd.DataFrame, top_n: int = 50) -> list:
    top = fi_df.head(top_n)["feature"].tolist()
    return [c for c in REGIME_COLS if c in top]


def compute_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """Expected Calibration Error (= reliability diagram 数値化)."""
    bins = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        mask = (y_prob >= bins[i]) & (y_prob < bins[i + 1])
        if i == n_bins - 1:
            mask = (y_prob >= bins[i]) & (y_prob <= bins[i + 1])
        if mask.sum() == 0:
            continue
        bin_acc = float(y_true[mask].mean())
        bin_prob = float(y_prob[mask].mean())
        ece += (mask.sum() / len(y_true)) * abs(bin_acc - bin_prob)
    return float(ece)


# ============== 学習関数 (= task_type 別) ==============

def train_one_regression(X_tr, y_tr, X_va, y_va, X_te, y_te) -> dict:
    params = {**LGB_DEFAULT_PARAMS_BASE, "objective": "regression", "metric": "rmse"}
    model = lgb.LGBMRegressor(**params)
    model.fit(X_tr, y_tr,
              eval_set=[(X_va, y_va)], eval_metric="rmse",
              callbacks=[lgb.early_stopping(EARLY_STOPPING_ROUNDS, verbose=False)])
    pred_tr = model.predict(X_tr)
    pred_va = model.predict(X_va)
    pred_te = model.predict(X_te)
    return {
        "model": model,
        "calibrator": None,
        "predictions": {
            "test_index": X_te.index,
            "y_true": np.asarray(y_te, dtype=np.float32),
            "pred": np.asarray(pred_te, dtype=np.float32),
        },
        "metrics": {
            "train_rmse": float(np.sqrt(mean_squared_error(y_tr, pred_tr))),
            "valid_rmse": float(np.sqrt(mean_squared_error(y_va, pred_va))),
            "test_rmse": float(np.sqrt(mean_squared_error(y_te, pred_te))),
            "train_r2": float(r2_score(y_tr, pred_tr)),
            "valid_r2": float(r2_score(y_va, pred_va)),
            "test_r2": float(r2_score(y_te, pred_te)),
            "label_std_train": float(y_tr.std()),
        },
        "best_iter": int(model.best_iteration_) if model.best_iteration_ else None,
    }


def train_one_multiclass(X_tr, y_tr, X_va, y_va, X_te, y_te) -> dict:
    # encode -1/0/1 → 0/1/2
    y_tr_e = encode_tb_label(y_tr)
    y_va_e = encode_tb_label(y_va)
    y_te_e = encode_tb_label(y_te)
    class_w = compute_class_weight(y_tr_e)
    params = {**LGB_DEFAULT_PARAMS_BASE,
              "objective": "multiclass", "metric": "multi_logloss",
              "num_class": 3, "class_weight": class_w}
    model = lgb.LGBMClassifier(**params)
    model.fit(X_tr, y_tr_e,
              eval_set=[(X_va, y_va_e)], eval_metric="multi_logloss",
              callbacks=[lgb.early_stopping(EARLY_STOPPING_ROUNDS, verbose=False)])
    pred_proba_va = model.predict_proba(X_va)
    pred_proba_te = model.predict_proba(X_te)

    # fold 別 isotonic regression per class (= §6.2.3 論点 4)
    calibrators = {}
    pred_proba_te_cal = np.zeros_like(pred_proba_te)
    for cls in range(3):
        iso = IsotonicRegression(out_of_bounds="clip")
        y_va_cls = (y_va_e == cls).astype(int).values
        iso.fit(pred_proba_va[:, cls], y_va_cls)
        calibrators[cls] = iso
        pred_proba_te_cal[:, cls] = iso.transform(pred_proba_te[:, cls])
    # 正規化 (= isotonic 後の確率和が 1 になるように)
    row_sum = pred_proba_te_cal.sum(axis=1, keepdims=True)
    row_sum[row_sum == 0] = 1.0
    pred_proba_te_cal = pred_proba_te_cal / row_sum

    pred_te = pred_proba_te.argmax(axis=1)
    pred_te_cal = pred_proba_te_cal.argmax(axis=1)

    # Brier / ECE (per class macro 平均)
    brier_per_class = []
    ece_per_class = []
    for cls in range(3):
        y_te_cls = (y_te_e == cls).astype(int).values
        brier_per_class.append(brier_score_loss(y_te_cls, pred_proba_te_cal[:, cls]))
        ece_per_class.append(compute_ece(y_te_cls, pred_proba_te_cal[:, cls]))

    return {
        "model": model,
        "calibrator": calibrators,
        "predictions": {
            "test_index": X_te.index,
            "y_true": np.asarray(y_te_e, dtype=np.int8),
            "pred_proba": np.asarray(pred_proba_te, dtype=np.float32),
            "pred_proba_cal": np.asarray(pred_proba_te_cal, dtype=np.float32),
        },
        "metrics": {
            "valid_multi_logloss": float(log_loss(y_va_e, pred_proba_va, labels=[0, 1, 2])),
            "test_multi_logloss": float(log_loss(y_te_e, pred_proba_te, labels=[0, 1, 2])),
            "test_multi_logloss_cal": float(log_loss(y_te_e, pred_proba_te_cal, labels=[0, 1, 2])),
            "test_accuracy": float(accuracy_score(y_te_e, pred_te)),
            "test_accuracy_cal": float(accuracy_score(y_te_e, pred_te_cal)),
            "test_f1_macro": float(f1_score(y_te_e, pred_te, average="macro")),
            "test_f1_macro_cal": float(f1_score(y_te_e, pred_te_cal, average="macro")),
            "test_brier_macro": float(np.mean(brier_per_class)),
            "test_ece_macro": float(np.mean(ece_per_class)),
            "class_weights": class_w,
            "class_dist_train": y_tr_e.value_counts().to_dict(),
        },
        "best_iter": int(model.best_iteration_) if model.best_iteration_ else None,
    }


def train_one_binary(X_tr, y_tr, X_va, y_va, X_te, y_te) -> dict:
    y_tr_i = y_tr.astype(int)
    y_va_i = y_va.astype(int)
    y_te_i = y_te.astype(int)
    spw = compute_scale_pos_weight(y_tr_i)
    params = {**LGB_DEFAULT_PARAMS_BASE,
              "objective": "binary", "metric": "binary_logloss",
              "scale_pos_weight": spw}
    model = lgb.LGBMClassifier(**params)
    model.fit(X_tr, y_tr_i,
              eval_set=[(X_va, y_va_i)], eval_metric="binary_logloss",
              callbacks=[lgb.early_stopping(EARLY_STOPPING_ROUNDS, verbose=False)])
    pred_proba_va = model.predict_proba(X_va)[:, 1]
    pred_proba_te = model.predict_proba(X_te)[:, 1]

    # fold 別 isotonic regression (= §6.2.3 論点 4)
    iso = IsotonicRegression(out_of_bounds="clip")
    iso.fit(pred_proba_va, y_va_i.values)
    pred_proba_te_cal = iso.transform(pred_proba_te)

    pred_te = (pred_proba_te > 0.5).astype(int)
    pred_te_cal = (pred_proba_te_cal > 0.5).astype(int)

    try:
        auc_te = float(roc_auc_score(y_te_i, pred_proba_te))
    except ValueError:
        auc_te = float("nan")
    try:
        auc_te_cal = float(roc_auc_score(y_te_i, pred_proba_te_cal))
    except ValueError:
        auc_te_cal = float("nan")

    return {
        "model": model,
        "calibrator": iso,
        "predictions": {
            "test_index": X_te.index,
            "y_true": np.asarray(y_te_i, dtype=np.int8),
            "pred_proba": np.asarray(pred_proba_te, dtype=np.float32),
            "pred_proba_cal": np.asarray(pred_proba_te_cal, dtype=np.float32),
        },
        "metrics": {
            "valid_binary_logloss": float(log_loss(y_va_i, pred_proba_va)),
            "test_binary_logloss": float(log_loss(y_te_i, pred_proba_te)),
            "test_binary_logloss_cal": float(log_loss(y_te_i, pred_proba_te_cal)),
            "test_accuracy": float(accuracy_score(y_te_i, pred_te)),
            "test_accuracy_cal": float(accuracy_score(y_te_i, pred_te_cal)),
            "test_f1": float(f1_score(y_te_i, pred_te)),
            "test_f1_cal": float(f1_score(y_te_i, pred_te_cal)),
            "test_auc": auc_te,
            "test_auc_cal": auc_te_cal,
            "test_brier": float(brier_score_loss(y_te_i, pred_proba_te_cal)),
            "test_ece": compute_ece(y_te_i.values, pred_proba_te_cal),
            "scale_pos_weight": spw,
            "class_dist_train": {"0": int((y_tr_i == 0).sum()), "1": int((y_tr_i == 1).sum())},
        },
        "best_iter": int(model.best_iteration_) if model.best_iteration_ else None,
    }


TRAIN_FUNCS = {
    "regression": train_one_regression,
    "multiclass": train_one_multiclass,
    "binary": train_one_binary,
}


def get_y_for_label(y_dict: dict, label_name: str) -> pd.Series:
    """label_name から該当 series を取得."""
    for prefix, df in y_dict.items():
        if label_name in df.columns:
            return df[label_name]
    raise KeyError(f"label not found: {label_name}")


def get_task_type(label_name: str) -> str:
    for task_type, spec in LABEL_SYSTEMS.items():
        if any(label_name.startswith(p) for p in spec["prefixes"]):
            return task_type
    raise ValueError(f"task_type unknown for label: {label_name}")


# ============== 1 fold × 1 label 実行 ==============

def run_one(label_name: str, fold_idx: int, X: pd.DataFrame, y_dict: dict,
            index: pd.DatetimeIndex, fold_splits: list) -> dict:
    task_type = get_task_type(label_name)

    # skip 機能 (= 既存完了済は再学習しない・PC シャットダウン等の中断復帰用)
    # 厳格化: metrics.json + predictions.parquet 両方存在で skip (= Step 6 集約用 predictions 強制)
    out_subdir = OUT_DIR / f"{label_name}_fold{fold_idx}"
    metrics_path = out_subdir / "metrics.json"
    predictions_path = out_subdir / "predictions.parquet"
    if metrics_path.exists() and predictions_path.exists():
        try:
            existing = json.loads(metrics_path.read_text())
            if "metrics" in existing and "task_type" in existing:
                existing["skipped"] = True
                return existing
        except Exception:
            pass  # 破損ファイルは再学習で上書き

    train_func = TRAIN_FUNCS[task_type]
    y_target = get_y_for_label(y_dict, label_name)

    train_idx, test_idx = fold_splits[fold_idx]
    n_train = len(train_idx)
    n_valid = int(n_train * VALID_TAIL_FRACTION)
    train_inner = train_idx[:n_train - n_valid]
    valid_idx = train_idx[n_train - n_valid:]

    X_tr, y_tr = X.iloc[train_inner], y_target.iloc[train_inner]
    X_va, y_va = X.iloc[valid_idx], y_target.iloc[valid_idx]
    X_te, y_te = X.iloc[test_idx], y_target.iloc[test_idx]

    mask_tr = ~y_tr.isnull()
    mask_va = ~y_va.isnull()
    mask_te = ~y_te.isnull()
    X_tr, y_tr = X_tr.loc[mask_tr], y_tr.loc[mask_tr]
    X_va, y_va = X_va.loc[mask_va], y_va.loc[mask_va]
    X_te, y_te = X_te.loc[mask_te], y_te.loc[mask_te]

    t0 = time.time()
    result = train_func(X_tr, y_tr, X_va, y_va, X_te, y_te)
    elapsed = time.time() - t0

    fi = pd.DataFrame({
        "feature": X_tr.columns.tolist(),
        "importance": result["model"].feature_importances_,
    }).sort_values("importance", ascending=False).reset_index(drop=True)

    leak = detect_leak_hits(fi)
    regime_top50 = regime_in_topN(fi, top_n=50)

    out_subdir = OUT_DIR / f"{label_name}_fold{fold_idx}"
    out_subdir.mkdir(parents=True, exist_ok=True)
    fi.head(20).to_csv(out_subdir / "feature_importance_top20.csv", index=False)

    if result["calibrator"] is not None:
        joblib.dump(result["calibrator"], out_subdir / "calibrator.joblib")

    # Step 6 集約用: predictions parquet 保存 (= test fold の各 trade × 予測値)
    pred_info = result["predictions"]
    pred_df_data = {
        "entry_id": pred_info["test_index"].astype(str).tolist(),
        "y_true": pred_info["y_true"],
    }
    if task_type == "regression":
        pred_df_data["pred"] = pred_info["pred"]
    elif task_type == "multiclass":
        # 3 class: class 0 = SL (label -1), class 1 = TIME (label 0), class 2 = TP (label 1)
        pp = pred_info["pred_proba"]
        ppc = pred_info["pred_proba_cal"]
        for cls in range(3):
            pred_df_data[f"pred_proba_class{cls}"] = pp[:, cls]
            pred_df_data[f"pred_proba_class{cls}_cal"] = ppc[:, cls]
    elif task_type == "binary":
        pred_df_data["pred_proba"] = pred_info["pred_proba"]
        pred_df_data["pred_proba_cal"] = pred_info["pred_proba_cal"]
    pred_df = pd.DataFrame(pred_df_data)
    pred_df.to_parquet(out_subdir / "predictions.parquet", compression="snappy")

    summary = {
        "label": label_name,
        "fold": fold_idx,
        "task_type": task_type,
        "n_train_inner": int(len(X_tr)),
        "n_valid": int(len(X_va)),
        "n_test": int(len(X_te)),
        "best_iter": result["best_iter"],
        "elapsed_sec": elapsed,
        "metrics": result["metrics"],
        "leak_check": leak,
        "regime_in_top50": regime_top50,
        "regime_in_top50_count": len(regime_top50),
    }
    (out_subdir / "metrics.json").write_text(json.dumps(summary, indent=2, default=str))

    # blacklist hit 検出時は即停止
    if len(leak["blacklist_hits"]) > 0:
        raise RuntimeError(
            f"BLACKLIST HIT in top 20 (label={label_name} fold={fold_idx}): "
            f"{leak['blacklist_hits']}"
        )
    return summary


# ============== main ==============

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="[2] Entry ML baseline (56 labels × 3 folds)")
    p.add_argument("--smoke", action="store_true",
                   help="1 label × 1 fold (= LONG_MFE_pct_K12, fold 0) のみ実行")
    p.add_argument("--label", type=str, default=None,
                   help="特定 label のみ実行 (例: LONG_MFE_pct_K12 / triple_barrier_label_LONG_K12 / meta_label_LONG_K12)")
    p.add_argument("--fold", type=int, default=None,
                   help="特定 fold のみ実行 (0/1/2)")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    t_start = time.time()
    print(f"[start] [2] Entry ML baseline ({pd.Timestamp.now()})")

    # 1. load parquet + blacklist drop + 56 ラベル分離
    print(f"[step 1] load parquet: {PARQUET_TRAIN.name}")
    X, y_dict, index = load_parquet_with_blacklist(PARQUET_TRAIN, verbose=True)

    # 2. regime 8 列 merge
    print(f"[step 2] merge regime: {PARQUET_REGIME.name}")
    X = merge_regime_columns(X, PARQUET_REGIME)
    print(f"[step 2] X shape (with regime): {X.shape}")

    # 3. CV split (= embargo K_max=288 = 24h 統一)
    print(f"[step 3] prepare_purged_cv n_splits={N_SPLITS} / K_embargo={LABEL_K_MAX}")
    cv = prepare_purged_cv(n_splits=N_SPLITS)
    fold_splits = list(split_with_purging(cv, X, index, K=LABEL_K_MAX))
    print(f"[step 3] fold yielded: {len(fold_splits)}")
    for i, (tr, te) in enumerate(fold_splits):
        print(f"  fold {i}: train={len(tr):,} test={len(te):,} | "
              f"train_range={index[tr[0]]}..{index[tr[-1]]} | "
              f"test_range={index[te[0]]}..{index[te[-1]]}")

    # 4. 学習対象決定
    label_names_per_task = get_all_label_names(y_dict)
    all_labels = (label_names_per_task["regression"]
                  + label_names_per_task["multiclass"]
                  + label_names_per_task["binary"])
    print(f"[step 4] task_type 別ラベル数: regression={len(label_names_per_task['regression'])}, "
          f"multiclass={len(label_names_per_task['multiclass'])}, binary={len(label_names_per_task['binary'])} "
          f"(total={len(all_labels)})")

    if args.smoke:
        target_labels = ["LONG_MFE_pct_K12"]
        target_folds = [0]
    elif args.label:
        target_labels = [args.label]
        target_folds = [args.fold] if args.fold is not None else list(range(len(fold_splits)))
    else:
        target_labels = all_labels
        target_folds = list(range(len(fold_splits)))
    n_runs = len(target_labels) * len(target_folds)
    print(f"[step 4] 実行対象: {len(target_labels)} labels × {len(target_folds)} folds = {n_runs} runs")

    # 5. 56 ラベル × 3 fold 学習
    summaries = []
    leak_aggregate = {"blacklist": [], "suspicious": []}
    for i, label in enumerate(target_labels):
        for fold_idx in target_folds:
            run_no = i * len(target_folds) + target_folds.index(fold_idx) + 1
            t_loop = time.time()
            try:
                summary = run_one(label, fold_idx, X, y_dict, index, fold_splits)
                summaries.append(summary)
                elapsed = time.time() - t_loop
                # 進捗報告
                pct = run_no / n_runs * 100
                eta_sec = (time.time() - t_start) / run_no * (n_runs - run_no)
                skipped_mark = " SKIP" if summary.get("skipped") else ""
                print(f"  [{run_no:3d}/{n_runs}] {pct:5.1f}% label={label} fold={fold_idx} "
                      f"task={summary['task_type']} elapsed={elapsed:.1f}s eta={eta_sec/60:.1f}min{skipped_mark}")
                # leak aggregate
                if summary["leak_check"]["suspicious_hits"]:
                    leak_aggregate["suspicious"].extend([
                        {"label": label, "fold": fold_idx, "hit": h}
                        for h in summary["leak_check"]["suspicious_hits"]
                    ])
            except Exception as e:
                print(f"  [{run_no:3d}/{n_runs}] ❌ FAILED label={label} fold={fold_idx}: {e}")
                traceback.print_exc()
                if "BLACKLIST HIT" in str(e):
                    print(f"  STOPPING due to blacklist hit (= §6.2.8 即停止)")
                    raise

    # 6. summary 集計
    out_summary = OUT_DIR / "summary.json"
    out_summary.write_text(json.dumps({
        "total_runs": len(summaries),
        "elapsed_total_sec": time.time() - t_start,
        "summaries": summaries,
    }, indent=2, default=str))
    out_leak = OUT_DIR / "leak_verify.json"
    out_leak.write_text(json.dumps(leak_aggregate, indent=2, default=str))

    elapsed_total = time.time() - t_start
    print(f"[done] {len(summaries)}/{n_runs} runs completed in {elapsed_total/60:.1f}min "
          f"(= {elapsed_total/3600:.2f}h)")
    print(f"[done] summary: {out_summary}")
    print(f"[done] leak: {out_leak}")
    print(f"[done] suspicious hits: {len(leak_aggregate['suspicious'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
