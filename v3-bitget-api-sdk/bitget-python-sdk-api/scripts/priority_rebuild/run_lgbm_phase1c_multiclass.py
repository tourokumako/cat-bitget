"""run_lgbm_phase1c_multiclass.py — Phase 1-c Triple Barrier 3-class multiclass 学習

指示書: .claude/instructions/2026-05-21_phase1c_triple_barrier_multiclass.md
案 α 採用 (まこさん 2026-05-21 承認・Stage 1 健全性判定):
学習対象 = K=6/12/24 のみ (長期 K は TIME クラス消滅で除外)

実行方法:
    python3 scripts/priority_rebuild/run_lgbm_phase1c_multiclass.py            # 全 3 K
    python3 scripts/priority_rebuild/run_lgbm_phase1c_multiclass.py --smoke    # K=12 smoke test のみ
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

import lightgbm as lgb

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from utils.leak_check import (  # noqa: E402
    check_future_ref_multiclass,
    check_label_correlation,
    check_shift1_guard,
    check_top1_dominance,
    write_report,
)

CONFIG_PATH = REPO_ROOT / "configs" / "phase1c_multiclass.yaml"

# Phase 1-a 流用の drop 列 (28 ラベル列 + close)
LONG_LABELS = [f"LONG_{side}_pct_K{K}" for side in ["MFE", "MAE"] for K in [6, 12, 24, 48, 96, 144, 288]]
SHORT_LABELS = [f"SHORT_{side}_pct_K{K}" for side in ["MFE", "MAE"] for K in [6, 12, 24, 48, 96, 144, 288]]
DROP_COLS_OTHER = ["close"]  # is_maintenance 2026-05-22 削除 (L-196 整合・Bitget 24/7 取引)


def log_line(log_f, msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    log_f.write(line + "\n")
    log_f.flush()


def load_config() -> dict:
    with CONFIG_PATH.open() as f:
        return yaml.safe_load(f)


def load_blacklist(cfg: dict) -> list[str]:
    bl_path = REPO_ROOT / cfg["paths"]["blacklist"]
    cols = [s.strip() for s in bl_path.read_text(encoding="utf-8").splitlines() if s.strip() and not s.strip().startswith("#")]
    assert len(cols) == 48, f"blacklist 個数異常: {len(cols)}"
    return cols


def merge_features_labels(cfg: dict, dataset: str, log_f) -> pd.DataFrame:
    """features parquet と Triple Barrier ラベル parquet を merge."""
    key_features = "features_train" if dataset == "train" else "features_test"
    key_labels = "tb_labels_train" if dataset == "train" else "tb_labels_test"
    fp = REPO_ROOT / cfg["paths"][key_features]
    lp = REPO_ROOT / cfg["paths"][key_labels]
    log_line(log_f, f"  features: {fp.relative_to(REPO_ROOT)}")
    features = pd.read_parquet(fp)
    log_line(log_f, f"  labels:   {lp.relative_to(REPO_ROOT)}")
    K_targets = cfg["k_targets"]
    label_cols = [f"triple_barrier_K{K}" for K in K_targets]
    tb = pd.read_parquet(lp, columns=label_cols)
    assert features.index.equals(tb.index), f"{dataset} features と labels の index 不一致"
    out = features.join(tb)
    log_line(log_f, f"  merged shape={out.shape}")
    return out


def make_drop_cols(blacklist: list[str], K_targets: list[int]) -> list[str]:
    label_cols = [f"triple_barrier_K{K}" for K in K_targets]
    return list(set(LONG_LABELS + SHORT_LABELS + DROP_COLS_OTHER + blacklist + label_cols))


def split_train_valid(train: pd.DataFrame, cfg: dict, log_f) -> tuple[pd.DataFrame, pd.DataFrame]:
    n = len(train)
    valid_ratio = cfg["split"]["valid_ratio"]
    purge = cfg["split"]["purge_bars"]
    split_idx = int(n * (1.0 - valid_ratio))
    valid_df = train.iloc[split_idx:].copy()
    train_df = train.iloc[: split_idx - purge].copy()
    log_line(log_f, f"  train rows={len(train_df):,} valid rows={len(valid_df):,} purge={purge}")
    return train_df, valid_df


def make_hparams(cfg: dict) -> dict:
    lp = cfg["lightgbm"]
    return dict(
        objective=lp["objective"],
        num_class=lp["num_class"],
        metric=lp["metric"],
        boosting_type=lp["boosting_type"],
        num_leaves=lp["num_leaves"],
        max_depth=lp["max_depth"],
        min_data_in_leaf=lp["min_data_in_leaf"],
        learning_rate=lp["learning_rate"],
        feature_fraction=lp["feature_fraction"],
        bagging_fraction=lp["bagging_fraction"],
        bagging_freq=lp["bagging_freq"],
        n_estimators=lp["n_estimators"],
        random_state=lp["random_state"],
        bagging_seed=lp["bagging_seed"],
        feature_fraction_seed=lp["feature_fraction_seed"],
        data_random_seed=lp["data_random_seed"],
        n_jobs=lp["n_jobs"],
        verbose=lp["verbose"],
    )


def compute_precision_at_threshold(y_true: np.ndarray, proba: np.ndarray, cls: int, threshold: float) -> tuple[float, int, int]:
    """class=cls の Precision を proba[:, cls] > threshold のサブセットで計算."""
    mask = proba[:, cls] > threshold
    n_pos = int(mask.sum())
    if n_pos == 0:
        return 0.0, 0, 0
    correct = int((y_true[mask] == cls).sum())
    return correct / n_pos, correct, n_pos


def train_one_k(
    K: int,
    train_df: pd.DataFrame,
    valid_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feat: list[str],
    hparams: dict,
    early_stopping: int,
    models_dir: Path,
    precision_threshold: float,
    log_f,
) -> tuple[dict, pd.DataFrame, np.ndarray, dict, dict, dict]:
    t0 = time.time()
    label = f"triple_barrier_K{K}"
    mask_tr = train_df[label] >= 0
    mask_va = valid_df[label] >= 0
    X_tr, y_tr = train_df.loc[mask_tr, feat], train_df.loc[mask_tr, label].astype(int)
    X_va, y_va = valid_df.loc[mask_va, feat], valid_df.loc[mask_va, label].astype(int)
    X_te = test_df[feat]

    model = lgb.LGBMClassifier(**hparams)
    model.fit(
        X_tr,
        y_tr,
        eval_set=[(X_tr, y_tr), (X_va, y_va)],
        eval_names=["train", "valid"],
        callbacks=[lgb.early_stopping(early_stopping, verbose=False), lgb.log_evaluation(100)],
    )
    model.booster_.save_model(str(models_dir / f"triple_barrier_K{K}.txt"))

    train_logloss = float(model.best_score_["train"]["multi_logloss"])
    valid_logloss = float(model.best_score_["valid"]["multi_logloss"])

    # 予測 (test 2025): softmax 確率 (n, 3)
    pred_proba_test = model.predict_proba(X_te)
    # valid 用 (Precision 計算)
    pred_proba_va = model.predict_proba(X_va)

    # Precision / Recall (each class)
    precision_per_cls = {}
    for cls in [0, 1, 2]:
        prec, n_correct, n_pos = compute_precision_at_threshold(
            y_va.to_numpy(), pred_proba_va, cls, precision_threshold
        )
        precision_per_cls[cls] = {"precision": prec, "n_correct": n_correct, "n_predicted": n_pos}

    # Recall (class 別)
    recall_per_cls = {}
    y_va_arr = y_va.to_numpy()
    pred_class = pred_proba_va.argmax(axis=1)
    for cls in [0, 1, 2]:
        cls_mask = y_va_arr == cls
        n_true = int(cls_mask.sum())
        n_recalled = int(((pred_class == cls) & cls_mask).sum())
        recall_per_cls[cls] = {"recall": n_recalled / n_true if n_true > 0 else 0.0, "n_true": n_true, "n_recalled": n_recalled}

    # feature_importance top20 (gain)
    fi = pd.DataFrame({
        "feature": model.booster_.feature_name(),
        "importance_gain": model.booster_.feature_importance(importance_type="gain"),
    }).sort_values("importance_gain", ascending=False).head(20).reset_index(drop=True)
    fi["K"] = K
    fi["rank"] = range(1, len(fi) + 1)

    # leak check (#1 / #3)
    leak_1 = check_future_ref_multiclass(fi, K)
    leak_3 = check_top1_dominance(fi, f"K{K}")

    summary_row = {
        "K": K,
        "best_iter": int(model.best_iteration_),
        "train_logloss": train_logloss,
        "valid_logloss": valid_logloss,
        "n_train": int(mask_tr.sum()),
        "n_valid": int(mask_va.sum()),
        "elapsed_sec": round(time.time() - t0, 1),
        "valid_class_balance": {int(c): int((y_va == c).sum()) for c in [0, 1, 2]},
    }
    leak_row = {"check_1_future_ref": leak_1, "check_3_top1_dominance": leak_3}

    pr_data = {
        "K": K,
        "precision_threshold": precision_threshold,
        "precision_per_class": precision_per_cls,
        "recall_per_class": recall_per_cls,
    }
    return summary_row, fi, pred_proba_test, leak_row, pr_data, {"y_va": y_va_arr, "proba_va": pred_proba_va}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true", help="K=12 smoke test のみ")
    parser.add_argument("--out-suffix", default="", help="出力ディレクトリ末尾 suffix")
    args = parser.parse_args()

    cfg = load_config()
    out_dir = REPO_ROOT / cfg["paths"]["output_dir"]
    if args.out_suffix:
        out_dir = out_dir.parent / f"{out_dir.name}{args.out_suffix}"
    models_dir = out_dir / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "execution_log_phase1c_multiclass.txt"

    with log_path.open("w", encoding="utf-8") as log_f:
        log_line(log_f, f"START phase1c_multiclass  out_dir={out_dir.relative_to(REPO_ROOT)}")
        log_line(log_f, f"lgbm={lgb.__version__}  pandas={pd.__version__}")

        # 1. データ load + 期間境界 verify
        train = merge_features_labels(cfg, "train", log_f)
        test = merge_features_labels(cfg, "test", log_f)
        assert train.index.max() < test.index.min(), "train_max >= test_min → leak risk"
        log_line(log_f, f"train ts: {train.index.min()} .. {train.index.max()}")
        log_line(log_f, f"test  ts: {test.index.min()} .. {test.index.max()}")

        # 2. blacklist + feature list
        blacklist = load_blacklist(cfg)
        K_targets = cfg["k_targets"]
        drop_cols = make_drop_cols(blacklist, K_targets)
        feat = [c for c in train.columns if c not in drop_cols]
        log_line(log_f, f"feature count = {len(feat)} (期待 1414)")
        assert len(feat) == 1414, f"feature 個数異常 {len(feat)}"

        # 3. split
        train_df, valid_df = split_train_valid(train, cfg, log_f)

        # 4. 学習対象
        if args.smoke:
            ks = [12]
        else:
            ks = K_targets
        log_line(log_f, f"K_targets = {ks}")
        hparams = make_hparams(cfg)
        early_stopping = cfg["lightgbm"]["early_stopping_rounds"]
        precision_threshold = cfg["precision_threshold"]

        # 5. 7 K (or 1 K smoke) ループ
        summary_rows = []
        fi_frames = []
        pred_test_dict: dict[str, np.ndarray] = {"timestamp": test.index.to_numpy()}
        leak_per_k = {}
        pr_per_k = {}

        for K in ks:
            log_line(log_f, f"--- training K={K} ---")
            summary_row, fi, pred_proba, leak_row, pr_data, _va_data = train_one_k(
                K, train_df, valid_df, test, feat, hparams, early_stopping, models_dir, precision_threshold, log_f,
            )
            summary_rows.append(summary_row)
            fi_frames.append(fi)
            for cls, name in enumerate(["P_SL", "P_TIME", "P_TP"]):
                pred_test_dict[f"{name}_K{K}"] = pred_proba[:, cls]
            leak_per_k[f"K{K}"] = leak_row
            pr_per_k[f"K{K}"] = pr_data

            log_line(
                log_f,
                f"  K={K} done | best_iter={summary_row['best_iter']} "
                f"valid_logloss={summary_row['valid_logloss']:.4f} elapsed={summary_row['elapsed_sec']}s "
                f"top1={leak_row['check_3_top1_dominance'].get('top1_feature')} "
                f"top1_pct={leak_row['check_3_top1_dominance'].get('top1_pct')}",
            )
            log_line(log_f, "  top20 features:")
            for _, row in fi.iterrows():
                log_line(log_f, f"    rank={int(row['rank']):>2} imp={float(row['importance_gain']):>12,.1f} {row['feature']}")
            log_line(log_f, f"  precision (P>0.5) per class: SL={pr_data['precision_per_class'][0]['precision']:.4f} "
                            f"TIME={pr_data['precision_per_class'][1]['precision']:.4f} "
                            f"TP={pr_data['precision_per_class'][2]['precision']:.4f}")

        # 6. ラベル間 correlation (#4)
        if len(ks) >= 2:
            label_cols = [f"triple_barrier_K{K}" for K in ks]
            leak_4 = check_label_correlation(valid_df, label_cols)
        else:
            leak_4 = {"status": "SKIP", "reason": "single K run"}
        log_line(log_f, f"check_4_label_correlation: {leak_4['status']}")

        # 7. 出力
        pd.DataFrame(summary_rows).to_csv(out_dir / "training_summary.csv", index=False)
        pd.concat(fi_frames).to_csv(out_dir / "feature_importance_top20_multiclass.csv", index=False)

        # predictions parquet
        pred_df = pd.DataFrame({k: v for k, v in pred_test_dict.items() if k != "timestamp"},
                                index=pd.DatetimeIndex(pred_test_dict["timestamp"], name="timestamp"))
        pred_df.to_parquet(out_dir / "predictions_multiclass_test_2025.parquet")

        # precision_recall_K{K}.csv (each K)
        for K in ks:
            pr = pr_per_k[f"K{K}"]
            rows = []
            for cls, name in enumerate(["SL", "TIME", "TP"]):
                p = pr["precision_per_class"][cls]
                r = pr["recall_per_class"][cls]
                rows.append({"class": name, "precision": p["precision"], "n_predicted": p["n_predicted"],
                             "n_correct": p["n_correct"], "recall": r["recall"], "n_true": r["n_true"],
                             "n_recalled": r["n_recalled"]})
            pd.DataFrame(rows).to_csv(out_dir / f"precision_recall_K{K}.csv", index=False)

        # leak_check_report
        leak_report = {
            "phase": "phase1c_multiclass",
            "K_targets": ks,
            "per_K_checks": leak_per_k,
            "check_4_label_correlation_global": leak_4,
            "shift1_guard_note": (
                "Phase 0 v3 Step 5 commit 34777ef 4 種 grep 0 hit + Step 5..HEAD 差分ゼロ verify (Phase 1-a と同じ・本タスクも特徴量計算スクリプト変更なし)"
            ),
        }
        write_report(out_dir / "leak_check_report.json", leak_report)

        # STOP 条件評価 (logloss < 0.95)
        stop_reasons = []
        for r in summary_rows:
            if not np.isfinite(r["valid_logloss"]):
                stop_reasons.append(f"K={r['K']}: NaN/Inf logloss")
            if r["valid_logloss"] >= 0.95:
                stop_reasons.append(f"K={r['K']}: logloss={r['valid_logloss']:.4f} ≥ 0.95")
        for k, lk in leak_per_k.items():
            if lk["check_1_future_ref"]["status"] == "FAIL":
                stop_reasons.append(f"{k}: future_ref FAIL")

        if stop_reasons:
            log_line(log_f, "STOP 条件該当:")
            for r in stop_reasons:
                log_line(log_f, f"  - {r}")
        else:
            log_line(log_f, "✅ STOP 条件該当なし")

        log_line(log_f, f"END phase1c_multiclass  out_dir={out_dir.relative_to(REPO_ROOT)}")

    print(f"\n=== DONE ===\nout_dir = {out_dir.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
