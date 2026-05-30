"""run_phase2_entry_ml_production.py — [2] Entry ML 本番モデル学習 + test 予測生成

目的 (= L-239 / WORKFLOW 改訂52 優先1):
  - baseline (CV) はデプロイ用 booster 未保存 → 本番モデルが存在しない (L-239 発覚)
  - 全 train (2021-04〜2024-12) で 56 ラベル本番モデルを 1 個ずつ最終 fit + booster 保存
  - test 2025 / 2026 Q1 に apply → 予測 parquet 生成 (= cluster / Stage 3 PnL 評価の前提データ)
  - 業界根拠: CV 後に全 train データで最終モデル再 fit してデプロイは標準
    ([ESL/TDS](https://towardsdatascience.com/how-to-do-cross-validation-effectively-1bbeb1d69ee8/))

leak verify (= Step 0 ⑥・2026-05-30 実施・全 pass):
  - #1 未来参照: production は新規 feature 計算なし (= 既存 parquet read のみ)
  - #3 timestamp 非侵入: train ≤2024-12-31 / test_2025 ≥2025-01-01 / test_2026_q1 ≥2026-01-01 完全分離
    → train 末尾 K_max=288 bar (= 24h) drop でラベルの test 期間侵入を防止
  - calibrator: valid 末尾10% で fit (= baseline L270 同様・test には fit しない)

注記 (= 2026-05-30 baseup 設計判断・/audit 検証待ち):
  - 本スクリプトは 56 ラベル全部を学習・保存する (= 学習自体は設計反転を含まない)
  - entry 判定の集約 (§6.2.7) を「決着28 限定 + TP ATR化」にする設計変更は別工程 (= 優先3)・/audit 後に確定

実行:
  --smoke   : 1 ラベル (= LONG_MFE_pct_K12) のみ (動作確認)
  --label X : 特定ラベルのみ
  (なし)    : 56 ラベル全部 (= 約 4-6h・caffeinate 必須)

出力 (= results/priority_rebuild/ml_phase2_production/):
  - {label}/booster.txt              (= LightGBM booster 本体・本番デプロイ用)
  - {label}/model.joblib             (= sklearn wrapper・再ロード + predict_proba 用)
  - {label}/calibrator.joblib        (= multiclass/binary のみ・valid fit isotonic)
  - {label}/predictions_test_2025.parquet
  - {label}/predictions_test_2026_q1.parquet
  - {label}/metrics.json
  - summary.json                     (= 56 ラベルの集計 + leak verify)
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
    accuracy_score, log_loss, mean_squared_error, r2_score,
    roc_auc_score, brier_score_loss,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

# baseline から再利用 (= 同型ロジックの重複定義を避ける)
from scripts.priority_rebuild.run_phase2_entry_ml_baseline import (  # noqa: E402
    LABEL_K_MAX, VALID_TAIL_FRACTION, EARLY_STOPPING_ROUNDS,
    LGB_DEFAULT_PARAMS_BASE,
    load_parquet_with_blacklist, merge_regime_columns,
    get_all_label_names, get_task_type, get_y_for_label,
    encode_tb_label, compute_class_weight, compute_scale_pos_weight,
    detect_leak_hits, regime_in_topN,
)

# I/O paths
PARQUET_TRAIN = REPO_ROOT / "results" / "priority_rebuild" / "labels_mfe_mae_pct_train_2021_2024.parquet"
PARQUET_REGIME_TRAIN = REPO_ROOT / "results" / "regime_step1" / "regime_predictions_train_2021_2024.parquet"
TEST_SPECS = [
    ("test_2025",
     REPO_ROOT / "results" / "priority_rebuild" / "labels_mfe_mae_pct_test_2025.parquet",
     REPO_ROOT / "results" / "regime_step1" / "regime_predictions_test_2025.parquet"),
    ("test_2026_q1",
     REPO_ROOT / "results" / "priority_rebuild" / "labels_mfe_mae_pct_test_2026_q1.parquet",
     REPO_ROOT / "results" / "regime_step1" / "regime_predictions_test_2026_q1.parquet"),
]
OUT_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase2_production"


# ============== fit (全 train) ==============

def fit_production_model(label_name, X_inner, y_inner, X_va, y_va):
    """全 train (inner) で最終 fit + valid で early stopping + calibrator(valid fit)。
    returns (model, calibrators_or_None, task_type, valid_metrics)"""
    task_type = get_task_type(label_name)

    if task_type == "regression":
        params = {**LGB_DEFAULT_PARAMS_BASE, "objective": "regression", "metric": "rmse"}
        model = lgb.LGBMRegressor(**params)
        model.fit(X_inner, y_inner, eval_set=[(X_va, y_va)], eval_metric="rmse",
                  callbacks=[lgb.early_stopping(EARLY_STOPPING_ROUNDS, verbose=False)])
        pred_va = model.predict(X_va)
        vmetrics = {
            "valid_rmse": float(np.sqrt(mean_squared_error(y_va, pred_va))),
            "valid_r2": float(r2_score(y_va, pred_va)),
            "label_std_train": float(y_inner.std()),
        }
        return model, None, task_type, vmetrics

    if task_type == "multiclass":
        y_inner_e = encode_tb_label(y_inner)
        y_va_e = encode_tb_label(y_va)
        class_w = compute_class_weight(y_inner_e)
        params = {**LGB_DEFAULT_PARAMS_BASE, "objective": "multiclass",
                  "metric": "multi_logloss", "num_class": 3, "class_weight": class_w}
        model = lgb.LGBMClassifier(**params)
        model.fit(X_inner, y_inner_e, eval_set=[(X_va, y_va_e)], eval_metric="multi_logloss",
                  callbacks=[lgb.early_stopping(EARLY_STOPPING_ROUNDS, verbose=False)])
        pred_proba_va = model.predict_proba(X_va)
        calibrators = {}
        for cls in range(3):
            iso = IsotonicRegression(out_of_bounds="clip")
            iso.fit(pred_proba_va[:, cls], (y_va_e == cls).astype(int).values)
            calibrators[cls] = iso
        vmetrics = {
            "valid_multi_logloss": float(log_loss(y_va_e, pred_proba_va, labels=[0, 1, 2])),
            "class_weights": class_w,
            "class_dist_train": y_inner_e.value_counts().to_dict(),
        }
        return model, calibrators, task_type, vmetrics

    # binary (meta_label)
    y_inner_i = y_inner.astype(int)
    y_va_i = y_va.astype(int)
    spw = compute_scale_pos_weight(y_inner_i)
    params = {**LGB_DEFAULT_PARAMS_BASE, "objective": "binary",
              "metric": "binary_logloss", "scale_pos_weight": spw}
    model = lgb.LGBMClassifier(**params)
    model.fit(X_inner, y_inner_i, eval_set=[(X_va, y_va_i)], eval_metric="binary_logloss",
              callbacks=[lgb.early_stopping(EARLY_STOPPING_ROUNDS, verbose=False)])
    pred_proba_va = model.predict_proba(X_va)[:, 1]
    iso = IsotonicRegression(out_of_bounds="clip")
    iso.fit(pred_proba_va, y_va_i.values)
    vmetrics = {"valid_scale_pos_weight": float(spw)}
    return model, {"bin": iso}, task_type, vmetrics


# ============== predict (test) ==============

def _apply_multiclass_cal(pred_proba_te, calibrators):
    out = np.zeros_like(pred_proba_te)
    for cls in range(3):
        out[:, cls] = calibrators[cls].transform(pred_proba_te[:, cls])
    row_sum = out.sum(axis=1, keepdims=True)
    row_sum[row_sum == 0] = 1.0
    return out / row_sum


def predict_test(model, calibrators, task_type, X_te, y_te):
    """test 1 期間を predict → (pred_df_dict, test_metrics)。y_te は metrics 用 (NaN は呼出側で mask 済)"""
    pred_data = {"entry_id": X_te.index.astype(str).tolist()}

    if task_type == "regression":
        pred = model.predict(X_te)
        pred_data["y_true"] = np.asarray(y_te, dtype=np.float32)
        pred_data["pred"] = np.asarray(pred, dtype=np.float32)
        tmetrics = {
            "test_rmse": float(np.sqrt(mean_squared_error(y_te, pred))),
            "test_r2": float(r2_score(y_te, pred)),
            "n_test": int(len(y_te)),
        }
        return pred_data, tmetrics

    if task_type == "multiclass":
        y_te_e = encode_tb_label(y_te)
        pp = model.predict_proba(X_te)
        ppc = _apply_multiclass_cal(pp, calibrators)
        pred_data["y_true"] = np.asarray(y_te_e, dtype=np.int8)
        for cls in range(3):
            pred_data[f"pred_proba_class{cls}"] = pp[:, cls]
            pred_data[f"pred_proba_class{cls}_cal"] = ppc[:, cls]
        tmetrics = {
            "test_multi_logloss": float(log_loss(y_te_e, pp, labels=[0, 1, 2])),
            "test_accuracy": float(accuracy_score(y_te_e, pp.argmax(axis=1))),
            "test_accuracy_cal": float(accuracy_score(y_te_e, ppc.argmax(axis=1))),
            "n_test": int(len(y_te_e)),
        }
        return pred_data, tmetrics

    # binary
    y_te_i = y_te.astype(int)
    pp = model.predict_proba(X_te)[:, 1]
    ppc = calibrators["bin"].transform(pp)
    pred_data["y_true"] = np.asarray(y_te_i, dtype=np.int8)
    pred_data["pred_proba"] = np.asarray(pp, dtype=np.float32)
    pred_data["pred_proba_cal"] = np.asarray(ppc, dtype=np.float32)
    tmetrics = {"n_test": int(len(y_te_i))}
    try:
        tmetrics["test_auc"] = float(roc_auc_score(y_te_i, pp))
        tmetrics["test_brier_cal"] = float(brier_score_loss(y_te_i, ppc))
    except ValueError:
        tmetrics["test_auc"] = None  # 単一クラスのみ等
    return pred_data, tmetrics


# ============== 1 ラベル処理 ==============

def run_one_label(label_name, X_inner, X_va, y_train_label, n_inner,
                  test_sets) -> dict:
    out_subdir = OUT_DIR / label_name
    out_subdir.mkdir(parents=True, exist_ok=True)

    # skip (= 中断復帰): booster.txt + 全 test 予測 存在で skip
    booster_path = out_subdir / "booster.txt"
    all_preds_exist = all((out_subdir / f"predictions_{name}.parquet").exists()
                          for name, _, _ in test_sets)
    if booster_path.exists() and all_preds_exist and (out_subdir / "metrics.json").exists():
        existing = json.loads((out_subdir / "metrics.json").read_text())
        existing["skipped"] = True
        return existing

    # inner / valid の y (= NaN mask)
    y_inner_full = y_train_label.iloc[:n_inner]
    y_va_full = y_train_label.iloc[n_inner:]
    m_inner = ~y_inner_full.isnull()
    m_va = ~y_va_full.isnull()
    X_in, y_in = X_inner.loc[m_inner.values], y_inner_full.loc[m_inner]
    X_v, y_v = X_va.loc[m_va.values], y_va_full.loc[m_va]

    t0 = time.time()
    model, calibrators, task_type, vmetrics = fit_production_model(label_name, X_in, y_in, X_v, y_v)
    elapsed = time.time() - t0

    # feature importance + leak ガード (= baseline 同様)
    fi = pd.DataFrame({
        "feature": X_in.columns.tolist(),
        "importance": model.feature_importances_,
    }).sort_values("importance", ascending=False).reset_index(drop=True)
    leak = detect_leak_hits(fi)
    regime_top50 = regime_in_topN(fi, top_n=50)
    fi.head(20).to_csv(out_subdir / "feature_importance_top20.csv", index=False)
    if len(leak["blacklist_hits"]) > 0:
        raise RuntimeError(f"BLACKLIST HIT in top 20 (label={label_name}): {leak['blacklist_hits']}")

    # 保存: booster + model + calibrator
    model.booster_.save_model(str(booster_path))
    joblib.dump(model, out_subdir / "model.joblib")
    if calibrators is not None:
        joblib.dump(calibrators, out_subdir / "calibrator.joblib")

    # test 2 期間 predict + 保存
    test_metrics = {}
    for name, X_te_full, y_te_dict in test_sets:
        y_te_full = get_y_for_label(y_te_dict, label_name)
        m_te = ~y_te_full.isnull()
        X_te, y_te = X_te_full.loc[m_te.values], y_te_full.loc[m_te]
        pred_data, tmetrics = predict_test(model, calibrators, task_type, X_te, y_te)
        pd.DataFrame(pred_data).to_parquet(out_subdir / f"predictions_{name}.parquet",
                                           compression="snappy")
        test_metrics[name] = tmetrics

    summary = {
        "label": label_name,
        "task_type": task_type,
        "n_inner": int(len(X_in)),
        "n_valid": int(len(X_v)),
        "best_iter": int(model.best_iteration_) if model.best_iteration_ else None,
        "elapsed_sec": elapsed,
        "valid_metrics": vmetrics,
        "test_metrics": test_metrics,
        "leak_check": leak,
        "regime_in_top50_count": len(regime_top50),
    }
    (out_subdir / "metrics.json").write_text(json.dumps(summary, indent=2, default=str))
    return summary


# ============== main ==============

def parse_args():
    p = argparse.ArgumentParser(description="[2] Entry ML 本番学習 + test 予測 (56 ラベル)")
    p.add_argument("--smoke", action="store_true", help="LONG_MFE_pct_K12 のみ")
    p.add_argument("--label", type=str, default=None, help="特定 label のみ")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    t_start = time.time()
    print(f"[start] [2] Entry ML production ({pd.Timestamp.now()})")

    # 1. train load + regime merge
    print(f"[step 1] load train: {PARQUET_TRAIN.name}")
    X_train, y_train_dict, idx_train = load_parquet_with_blacklist(PARQUET_TRAIN, verbose=True)
    X_train = merge_regime_columns(X_train, PARQUET_REGIME_TRAIN)
    print(f"[step 1] X_train (with regime): {X_train.shape} range={idx_train.min()}..{idx_train.max()}")

    # 2. embargo: train 末尾 K_max=288 bar drop (= ラベルの test 期間侵入防止・leak #3)
    emb = LABEL_K_MAX
    X_train = X_train.iloc[:-emb]
    print(f"[step 2] embargo drop tail {emb} bar → X_train: {X_train.shape}")

    # 3. inner / valid split (= 末尾 10% valid for early stopping)
    n = len(X_train)
    n_valid = int(n * VALID_TAIL_FRACTION)
    n_inner = n - n_valid
    X_inner = X_train.iloc[:n_inner]
    X_va = X_train.iloc[n_inner:]
    print(f"[step 3] inner={n_inner:,} valid={n_valid:,}")
    # y も embargo 後の長さに揃える (= iloc[:-emb])
    y_train_dict = {k: v.iloc[:-emb] for k, v in y_train_dict.items()}

    # 4. test load + regime merge
    test_sets = []
    for name, lp, rp in TEST_SPECS:
        print(f"[step 4] load {name}: {lp.name}")
        X_te, y_te_dict, idx_te = load_parquet_with_blacklist(lp, verbose=False)
        X_te = merge_regime_columns(X_te, rp)
        # 列順を train に合わせる (= 同一 feature set)
        X_te = X_te[X_inner.columns]
        print(f"[step 4] {name}: {X_te.shape} range={idx_te.min()}..{idx_te.max()}")
        test_sets.append((name, X_te, y_te_dict))

    # 5. 学習対象決定
    label_names_per_task = get_all_label_names(y_train_dict)
    all_labels = (label_names_per_task["regression"]
                  + label_names_per_task["multiclass"]
                  + label_names_per_task["binary"])
    if args.smoke:
        target_labels = ["LONG_MFE_pct_K12"]
    elif args.label:
        target_labels = [args.label]
    else:
        target_labels = all_labels
    print(f"[step 5] 学習対象: {len(target_labels)} labels")

    # 6. ラベルごと fit + predict
    summaries = []
    for i, label in enumerate(target_labels):
        t_loop = time.time()
        try:
            s = run_one_label(label, X_inner, X_va, get_y_for_label(y_train_dict, label), n_inner, test_sets)
            summaries.append(s)
            eta = (time.time() - t_start) / (i + 1) * (len(target_labels) - i - 1)
            mark = " SKIP" if s.get("skipped") else ""
            print(f"  [{i+1:2d}/{len(target_labels)}] {label} task={s['task_type']} "
                  f"elapsed={time.time()-t_loop:.1f}s eta={eta/60:.1f}min{mark}")
        except Exception as e:
            print(f"  [{i+1:2d}/{len(target_labels)}] ❌ FAILED {label}: {e}")
            traceback.print_exc()
            if "BLACKLIST HIT" in str(e):
                return 1

    # 7. summary 保存
    summary_all = {
        "n_labels": len(summaries),
        "total_elapsed_sec": time.time() - t_start,
        "train_range": f"{idx_train.min()}..{idx_train.max()}",
        "embargo_bar": emb,
        "n_inner": n_inner,
        "n_valid": n_valid,
        "labels": [s["label"] for s in summaries],
        "suspicious_any": any(s["leak_check"]["suspicious_hits"] for s in summaries),
    }
    (OUT_DIR / "summary.json").write_text(json.dumps(summary_all, indent=2, default=str))
    print(f"[done] {len(summaries)} labels / {(time.time()-t_start)/60:.1f}min → {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
