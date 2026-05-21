"""run_lgbm_phase1a_rmse.py — Phase 1-a 14 ラベル LightGBM RMSE 学習

指示書: .claude/instructions/2026-05-21_phase1a_lgbm_rmse.md
発注: Web Claude (PM) / 実装: CC (2026-05-21)

実行方法:
    python3 scripts/priority_rebuild/run_lgbm_phase1a_rmse.py            # 全 14 ラベル
    python3 scripts/priority_rebuild/run_lgbm_phase1a_rmse.py --smoke    # 1 ラベル smoke test (LONG_MFE_pct_K6)
    python3 scripts/priority_rebuild/run_lgbm_phase1a_rmse.py --labels LONG_MFE_pct_K6 LONG_MAE_pct_K12

出力: results/priority_rebuild/ml_phase1a_rmse/ (指示書 §4.1 参照)
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
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# repo paths
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent  # .../bitget-python-sdk-api
sys.path.insert(0, str(SCRIPT_DIR))

from utils.leak_check import (  # noqa: E402
    LEARN_K_WINDOWS,
    check_future_ref,
    check_label_correlation,
    check_shift1_guard,
    check_top1_dominance,
    write_report,
)


CONFIG_PATH = REPO_ROOT / "configs" / "phase1a_rmse.yaml"

LABEL_COLS_LEARN = (
    [f"LONG_MFE_pct_K{K}" for K in LEARN_K_WINDOWS]
    + [f"LONG_MAE_pct_K{K}" for K in LEARN_K_WINDOWS]
)
LABEL_COLS_DROP_SHORT = (
    [f"SHORT_MFE_pct_K{K}" for K in LEARN_K_WINDOWS]
    + [f"SHORT_MAE_pct_K{K}" for K in LEARN_K_WINDOWS]
)
DROP_COLS_OTHER = ["close", "is_maintenance"]


def load_config() -> dict:
    with CONFIG_PATH.open() as f:
        return yaml.safe_load(f)


def load_data(cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    train = pd.read_parquet(REPO_ROOT / cfg["paths"]["parquet_train"])
    test_2025 = pd.read_parquet(REPO_ROOT / cfg["paths"]["parquet_test_2025"])

    assert train.index.name == "timestamp", f"train index_name={train.index.name}"
    assert test_2025.index.name == "timestamp", f"test_2025 index_name={test_2025.index.name}"
    assert train.index.max() < test_2025.index.min(), (
        f"train_max={train.index.max()} >= test_min={test_2025.index.min()} → leak risk"
    )
    return train, test_2025


def load_blacklist(cfg: dict) -> list[str]:
    bl_path = REPO_ROOT / cfg["paths"]["blacklist"]
    cols = []
    for line in bl_path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            cols.append(s)
    assert len(cols) == 48, f"blacklist 個数異常: {len(cols)} (期待 48)"
    return cols


def split_train_valid(train: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """末尾 valid_ratio を valid・purge_bars で valid leak 防止."""
    n = len(train)
    valid_ratio = cfg["split"]["valid_ratio"]
    purge = cfg["split"]["purge_bars"]
    split_idx = int(n * (1.0 - valid_ratio))
    valid_df = train.iloc[split_idx:].copy()
    # train 末尾 purge bars は valid の K=288 ラベル参照範囲と重複 → drop
    train_df = train.iloc[: split_idx - purge].copy()
    return train_df, valid_df


def build_feature_list(train: pd.DataFrame, blacklist: list[str]) -> list[str]:
    drop_cols = set(LABEL_COLS_LEARN + LABEL_COLS_DROP_SHORT + DROP_COLS_OTHER + blacklist)
    feat = [c for c in train.columns if c not in drop_cols]
    return feat


def make_hparams(cfg: dict) -> dict:
    lp = cfg["lightgbm"]
    return dict(
        objective=lp["objective"],
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


def train_one_label(
    label: str,
    train_df: pd.DataFrame,
    valid_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feat: list[str],
    hparams: dict,
    early_stopping: int,
    models_dir: Path,
) -> tuple[dict, pd.DataFrame, np.ndarray, dict, dict, float, dict]:
    """1 ラベル学習 + leak check + ランダム比較 + 予測値 (test 2025)."""
    t0 = time.time()

    mask_tr = train_df[label].notna()
    mask_va = valid_df[label].notna()

    X_tr = train_df.loc[mask_tr, feat]
    y_tr = train_df.loc[mask_tr, label]
    X_va = valid_df.loc[mask_va, feat]
    y_va = valid_df.loc[mask_va, label]
    X_te = test_df[feat]

    model = lgb.LGBMRegressor(**hparams)
    model.fit(
        X_tr,
        y_tr,
        eval_set=[(X_tr, y_tr), (X_va, y_va)],
        eval_names=["train", "valid"],
        callbacks=[lgb.early_stopping(early_stopping, verbose=False), lgb.log_evaluation(100)],
    )

    model.booster_.save_model(str(models_dir / f"{label}.txt"))

    train_rmse = float(model.best_score_["train"]["rmse"])
    valid_rmse = float(model.best_score_["valid"]["rmse"])
    label_std = float(y_va.std())
    rmse_ratio = (valid_rmse / label_std) if label_std > 0 else float("inf")

    # feature importance top20 (gain)
    fi = pd.DataFrame(
        {
            "feature": model.booster_.feature_name(),
            "importance_gain": model.booster_.feature_importance(importance_type="gain"),
        }
    )
    fi = fi.sort_values("importance_gain", ascending=False).head(20).reset_index(drop=True)
    fi["label"] = label
    fi["rank"] = range(1, len(fi) + 1)

    # leak check (#1 future ref + #2 shift1 guard 引用 + #3 top1 dominance)
    leak_1 = check_future_ref(fi, label)
    leak_2 = check_shift1_guard(label)
    leak_3 = check_top1_dominance(fi, label)

    # 予測値 (test 2025)
    pred = model.predict(X_te)

    # ランダム比較 (valid を shuffle)
    rng = np.random.default_rng(42)
    y_va_arr = y_va.to_numpy()
    rand_pred = rng.permutation(y_va_arr)
    ml_pred_va = model.predict(X_va)
    ml_rmse = float(np.sqrt(np.mean((ml_pred_va - y_va_arr) ** 2)))
    random_rmse = float(np.sqrt(np.mean((rand_pred - y_va_arr) ** 2)))
    lift_pct = float((random_rmse - ml_rmse) / random_rmse * 100.0) if random_rmse > 0 else 0.0
    random_row = {
        "label": label,
        "ML_RMSE": ml_rmse,
        "random_RMSE": random_rmse,
        "lift_pct": lift_pct,
    }

    summary_row = {
        "label": label,
        "best_iter": int(model.best_iteration_),
        "train_rmse": train_rmse,
        "valid_rmse": valid_rmse,
        "label_std": label_std,
        "rmse_ratio": rmse_ratio,
        "n_train": int(mask_tr.sum()),
        "n_valid": int(mask_va.sum()),
        "elapsed_sec": round(time.time() - t0, 1),
    }
    leak_row = {
        "check_1_future_ref": leak_1,
        "check_2_shift1_guard": leak_2,
        "check_3_top1_dominance": leak_3,
    }
    return summary_row, fi, pred, random_row, leak_row, time.time() - t0, {"label": label, "pred_std": float(np.std(pred))}


def save_prediction_hist(pred: np.ndarray, label: str, out_dir: Path) -> dict:
    """予測値ヒストグラム + 健全性判定."""
    pred_std = float(np.std(pred))
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(pred, bins=80)
    ax.set_title(f"{label}  (n={len(pred):,}, std={pred_std:.6f})")
    ax.set_xlabel("predicted value (pct)")
    ax.set_ylabel("count")
    out = out_dir / f"prediction_distribution_{label}.png"
    fig.tight_layout()
    fig.savefig(out, dpi=80)
    plt.close(fig)
    return {"label": label, "pred_std": pred_std, "path": str(out.relative_to(REPO_ROOT))}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true", help="1 ラベルのみ smoke test (LONG_MFE_pct_K6)")
    parser.add_argument("--labels", nargs="+", help="特定ラベルのみ学習 (区切り空白)")
    parser.add_argument(
        "--out-suffix",
        default="",
        help="出力ディレクトリ末尾 suffix (smoke 等のため・空なら本番)",
    )
    args = parser.parse_args()

    cfg = load_config()
    out_dir = REPO_ROOT / cfg["paths"]["output_dir"]
    if args.out_suffix:
        out_dir = out_dir.parent / f"{out_dir.name}{args.out_suffix}"
    models_dir = out_dir / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    log_path = out_dir / "execution_log.txt"
    log_f = log_path.open("w", encoding="utf-8")

    def log(msg: str) -> None:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        line = f"[{ts}] {msg}"
        print(line, flush=True)
        log_f.write(line + "\n")
        log_f.flush()

    log(f"START phase1a_rmse  out_dir={out_dir.relative_to(REPO_ROOT)}")
    log(f"cwd={Path.cwd()} repo_root={REPO_ROOT}")
    log(f"lgbm={lgb.__version__}  pandas={pd.__version__}  numpy={np.__version__}")

    # === 1. データ load + 期間境界 verify ===
    train, test_2025 = load_data(cfg)
    log(f"train rows={len(train):,} test_2025 rows={len(test_2025):,}")
    log(f"train ts: {train.index.min()} .. {train.index.max()}")
    log(f"test_2025 ts: {test_2025.index.min()} .. {test_2025.index.max()}")

    # === 2. blacklist load + feature list 構築 ===
    blacklist = load_blacklist(cfg)
    feat = build_feature_list(train, blacklist)
    log(f"blacklist drop count = {len(blacklist)}")
    log(f"feature count = {len(feat)} (期待 1414)")
    assert len(feat) == 1414, f"feature 個数異常: {len(feat)} ≠ 1414"

    # === 3. train / valid split (時系列・purge 適用) ===
    train_df, valid_df = split_train_valid(train, cfg)
    log(
        f"split: train_df rows={len(train_df):,} valid_df rows={len(valid_df):,} "
        f"purge_bars={cfg['split']['purge_bars']}"
    )

    # === 4. 学習対象決定 ===
    if args.smoke:
        labels_to_train = ["LONG_MFE_pct_K6"]
    elif args.labels:
        labels_to_train = args.labels
    else:
        labels_to_train = LABEL_COLS_LEARN
    log(f"labels_to_train = {labels_to_train}")

    # === 5. ハイパラ ===
    hparams = make_hparams(cfg)
    early_stopping = cfg["lightgbm"]["early_stopping_rounds"]
    log(f"hparams = {json.dumps(hparams, ensure_ascii=False)}")

    # === 6. 14 (or smoke 1) ラベル学習ループ ===
    summary_rows: list[dict] = []
    fi_frames: list[pd.DataFrame] = []
    pred_test = pd.DataFrame(index=test_2025.index)
    random_rows: list[dict] = []
    per_label_leak: dict = {}
    hist_rows: list[dict] = []

    for label in labels_to_train:
        log(f"--- training {label} ---")
        summary_row, fi, pred, random_row, leak_row, _elapsed, _ = train_one_label(
            label,
            train_df,
            valid_df,
            test_2025,
            feat,
            hparams,
            early_stopping,
            models_dir,
        )
        summary_rows.append(summary_row)
        fi_frames.append(fi)
        pred_test[label] = pred
        random_rows.append(random_row)
        per_label_leak[label] = leak_row
        hist_rows.append(save_prediction_hist(pred, label, out_dir))
        log(
            f"  done in {summary_row['elapsed_sec']}s | "
            f"train_rmse={summary_row['train_rmse']:.5f} valid_rmse={summary_row['valid_rmse']:.5f} "
            f"ratio={summary_row['rmse_ratio']:.4f} best_iter={summary_row['best_iter']} "
            f"top1={leak_row['check_3_top1_dominance'].get('top1_feature')} "
            f"top1_pct={leak_row['check_3_top1_dominance'].get('top1_pct')}"
        )
        # 1 ラベル目完了直後の review (L-179 #4) は本ラベル毎に top20 をログ出力
        log(f"  top20 features:")
        for _, row in fi.iterrows():
            log(f"    rank={int(row['rank']):>2}  imp={float(row['importance_gain']):>12,.1f}  {row['feature']}")

    # === 7. ラベル間相関 check (#4) ===
    if len(labels_to_train) >= 2:
        leak_4 = check_label_correlation(valid_df, labels_to_train)
    else:
        leak_4 = {"status": "SKIP", "reason": "single label run"}
    log(f"check_4_label_correlation: {leak_4['status']}")

    # === 8. ファイル出力 ===
    pd.DataFrame(summary_rows).to_csv(out_dir / "training_summary.csv", index=False)
    pd.concat(fi_frames).to_csv(out_dir / "feature_importance_top20.csv", index=False)
    pred_test.to_parquet(out_dir / "predictions_test_2025.parquet")
    pd.DataFrame(random_rows).to_csv(out_dir / "random_baseline_comparison.csv", index=False)

    leak_report = {
        "phase": "phase1a_rmse",
        "labels_trained": list(labels_to_train),
        "per_label_checks": per_label_leak,
        "check_4_label_correlation_global": leak_4,
        "shift1_guard_note": (
            "Phase 0 v3 Step 5 commit 34777ef で 4 種 grep 全件 0 hit 確認済 + "
            "Step 5..HEAD で特徴量計算スクリプト差分ゼロ verify 済 → "
            "本タスクでは grep 再実行せず top20 review のみ実施 (まこさん 2026-05-21 承認)"
        ),
    }
    write_report(out_dir / "leak_check_report.json", leak_report)
    pd.DataFrame(hist_rows).to_csv(out_dir / "prediction_histogram_index.csv", index=False)

    # STOP 条件評価 (指示書 §5.3)
    stop_reasons: list[str] = []
    for row in summary_rows:
        if not np.isfinite(row["train_rmse"]) or not np.isfinite(row["valid_rmse"]):
            stop_reasons.append(f"{row['label']}: NaN/Inf RMSE")
    for h in hist_rows:
        if h["pred_std"] < 1e-6:
            stop_reasons.append(f"{h['label']}: pred_std={h['pred_std']:.2e} < 1e-6 (学習失敗疑い)")
    # ラベル間 4 番 FAIL
    if leak_4.get("status") == "FAIL":
        stop_reasons.append("label_correlation > 0.99 ペア検出")
    # ラベル別 future_ref FAIL
    for lab, lk in per_label_leak.items():
        if lk["check_1_future_ref"]["status"] == "FAIL":
            stop_reasons.append(f"{lab}: future_ref violation")
    # rmse_ratio < 1.5 が 14 中 9 未満 (= 5 ラベル以上で崩壊)
    if len(summary_rows) == len(LABEL_COLS_LEARN):
        n_ok = sum(1 for r in summary_rows if r["rmse_ratio"] < 1.5)
        if n_ok < 9:
            stop_reasons.append(f"rmse_ratio<1.5 が {n_ok}/14 (要 9 以上)")
        log(f"rmse_ratio<1.5 count = {n_ok}/14")

    if stop_reasons:
        log("STOP 条件該当 (指示書 §5.3):")
        for r in stop_reasons:
            log(f"  - {r}")

    log(f"END phase1a_rmse  out_dir={out_dir.relative_to(REPO_ROOT)}")
    log_f.close()
    print(f"\n=== DONE ===\nout_dir = {out_dir.relative_to(REPO_ROOT)}\nlog = {log_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
