#!/usr/bin/env python3
"""
run_lgbm_phase1.py — ML Phase 1: LightGBM × 16 ラベル × デフォルトハイパラ

指示書: bitget-python-sdk-api/cc_ml_design_spec.md §5 Phase 1

入力 (results/priority_rebuild/):
  labels_mfe_mae_train_2021_2024.parquet  (394,573 行 × 1,449 col)
  labels_mfe_mae_test_2025.parquet        (105,120 行 × 1,449 col)
  ※ timestamp は DatetimeIndex / 1,432 特徴量 + 16 ラベル + close

出力 (results/priority_rebuild/ml_phase1/):
  lgbm_log_<TS>.txt                     §7.1 実行ログ
  models/lgbm_<label>.txt × 16          学習済みモデル
  training_curves.csv                   §7.2 学習過程
  predictions_test2025.parquet          16 予測値 × 105,120 行
  feature_importance_top20.csv          §7.6 上位 20 × 16
  prediction_histograms.png             §7.6 予測値分布
  pred_vs_real_scatter.png              §7.3 散布図
  entry_thresholds.json                 §2 データ駆動閾値
  entry_firing_rate.csv                 §7.6 発火率
  random_baseline_comparison.csv        §7.5 ランダム比較
  monthly_pnl_optimistic.csv            §7.3 楽観月次 PnL (Exit 未設計のため上限値)
  summary.md                            まとめ + §7.4 再現コマンド

技術要件 (指示書 §1.5/§7 の意図を満たす標準実装):
  - 時系列 valid split (train 末尾 10%) … リーク防止
  - early_stopping_rounds=50 … 過学習防止
  - random_state=42 … 再現性
"""

from __future__ import annotations

import json
import os
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
OUT_DIR = DATA_DIR / "ml_phase1"
MODELS_DIR = OUT_DIR / "models"

TRAIN_PARQUET = DATA_DIR / "labels_mfe_mae_train_2021_2024.parquet"
TEST_PARQUET = DATA_DIR / "labels_mfe_mae_test_2025.parquet"

LABEL_COLS = [
    f"{side}_{kind}_K{k}"
    for k in (12, 24, 48, 96)
    for side in ("LONG", "SHORT")
    for kind in ("MFE", "MAE")
]
META_COLS = ["close"]  # timestamp は DatetimeIndex
VALID_RATIO = 0.10
RANDOM_STATE = 42
EARLY_STOPPING_ROUNDS = 50
N_ESTIMATORS = 2000

THRESHOLD_QUANTILES = [0.90, 0.95, 0.99]

POS_SIZE_BTC = 0.12
FEE_RATE_MAKER = 0.00014  # V9 正本 (config/cat_params_v9.json)
ROUND_TRIP_FEE = FEE_RATE_MAKER * 2

TS = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
LOG_PATH = OUT_DIR / f"lgbm_log_{TS}.txt"


def log(msg: str) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{now}] {msg}"
    print(line, flush=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")


def train_one_label(
    label: str,
    Xt: pd.DataFrame,
    yt: pd.Series,
    Xv: pd.DataFrame,
    yv: pd.Series,
    feature_cols: list[str],
) -> tuple[lgb.LGBMRegressor, list[tuple], list[tuple]]:
    """1 ラベル分の学習。training_curves と importance Top20 のレコードを返す。"""
    params = dict(
        objective="regression",
        metric="rmse",
        learning_rate=0.05,
        n_estimators=N_ESTIMATORS,
        random_state=RANDOM_STATE,
        verbose=-1,
        n_jobs=-1,
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
    return model, curves, importance


def main() -> None:
    t0 = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    log("=== ML Phase 1 START ===")
    log(f"lightgbm: {lgb.__version__}")
    log(f"train: {TRAIN_PARQUET}")
    log(f"test : {TEST_PARQUET}")
    log(f"out  : {OUT_DIR}")

    log("loading train parquet ...")
    df_train_full = pd.read_parquet(TRAIN_PARQUET)
    log(f"  train: {df_train_full.shape} index={type(df_train_full.index).__name__}")
    log("loading test parquet ...")
    df_test = pd.read_parquet(TEST_PARQUET)
    log(f"  test : {df_test.shape}")

    feature_cols = [c for c in df_train_full.columns if c not in LABEL_COLS + META_COLS]
    log(f"feature_cols: {len(feature_cols)}")
    assert len(feature_cols) == 1432, f"expected 1432 features, got {len(feature_cols)}"

    # 時系列 valid split (末尾 10%)
    n_total = len(df_train_full)
    n_valid = int(n_total * VALID_RATIO)
    n_train = n_total - n_valid
    log(
        f"split: train={n_train} ({df_train_full.index[0]} → {df_train_full.index[n_train-1]}) "
        f"valid={n_valid} ({df_train_full.index[n_train]} → {df_train_full.index[-1]})"
    )

    X_train_all = df_train_full.iloc[:n_train][feature_cols]
    X_valid_all = df_train_full.iloc[n_train:][feature_cols]
    X_train_full = df_train_full[feature_cols]  # Phase 4-a 用 (train + valid 全期間・L-183)
    X_test = df_test[feature_cols]

    training_curves: list[tuple] = []
    importance_records: list[tuple] = []
    pred_test = pd.DataFrame(index=df_test.index)
    pred_valid = pd.DataFrame(index=X_valid_all.index)
    pred_train_all = pd.DataFrame(index=df_train_full.index)  # Phase 4-a 用

    for i, label in enumerate(LABEL_COLS, 1):
        t_label = time.time()
        log(f"--- model [{i}/16] {label} ---")
        y_train = df_train_full.iloc[:n_train][label]
        y_valid = df_train_full.iloc[n_train:][label]
        mask_t = y_train.notna()
        mask_v = y_valid.notna()
        log(f"  drop NaN: train {(~mask_t).sum()}, valid {(~mask_v).sum()}")
        Xt, yt = X_train_all[mask_t], y_train[mask_t]
        Xv, yv = X_valid_all[mask_v], y_valid[mask_v]

        model, curves, importance = train_one_label(label, Xt, yt, Xv, yv, feature_cols)
        training_curves.extend(curves)
        importance_records.extend(importance)

        # Phase 1 leak チェック pause (checklist 1.3 / L-179)
        if i == 1:
            log("=== Phase 1 leak チェック pause (1 ラベル目完了) ===")
            log(f"label: {label} / top20 feature_importance:")
            for _, rank, feat, val in importance:
                log(f"  {rank:2d}. {feat}: {val}")
            blacklist = ["dist_to_fib_v2_", "resistance_distance_", "support_distance_", "nearest_level_"]
            leak_hits = [(rank, feat) for _, rank, feat, _ in importance
                         if any(b in feat for b in blacklist)]
            if leak_hits:
                log(f"🔴 ブラックリスト top20 ヒット {len(leak_hits)} 件 (L-179):")
                for rank, feat in leak_hits:
                    log(f"  rank {rank}: {feat}")
                log("=== STOP: leak 残存疑い・ALLOW_PHASE1_CONTINUE では bypass 不可 ===")
                sys.exit(1)
            log("✅ ブラックリスト top20 0 件")
            if os.environ.get("ALLOW_PHASE1_CONTINUE") != "1":
                log("=== STOP: ALLOW_PHASE1_CONTINUE=1 が未設定 ===")
                log("  feature_importance を review してから ALLOW_PHASE1_CONTINUE=1 python3 ... で継続")
                sys.exit(0)
            log("=== ALLOW_PHASE1_CONTINUE=1 確認・継続 ===")

        best_iter = model.best_iteration_
        valid_rmse_best = min(c[3] for c in curves)
        log(f"  best_iter={best_iter} valid_rmse_best={valid_rmse_best:.6f}")

        model_path = MODELS_DIR / f"lgbm_{label}.txt"
        model.booster_.save_model(str(model_path))

        # 怠け検知: top1 偏り
        top1_feat, _, _, top1_val = importance[0][1], importance[0][2], importance[0][3], importance[0][3]
        total_imp = sum(int(model.feature_importances_[idx]) for idx, _ in enumerate(feature_cols))
        top1_share = (top1_val / total_imp) if total_imp > 0 else 0.0
        log(f"  top1: {importance[0][2]} importance_share={top1_share:.3f}")
        if top1_share >= 0.5:
            log(f"  ⚠️ top1 importance share >= 0.5 (lopsided — suspect)")

        # 予測
        pred_valid[label] = model.predict(X_valid_all)
        pred_test[label] = model.predict(X_test)
        pred_train_all[label] = model.predict(X_train_full)  # Phase 4-a 用 (L-183 data snooping 解消)
        std_t = pred_test[label].std()
        log(f"  test pred: mean={pred_test[label].mean():.4f} std={std_t:.4f}")
        if std_t < 1e-9:
            log("  ⚠️ test pred std~0 (degenerate)")
        log(f"  elapsed (this model): {(time.time()-t_label)/60:.2f} min")

    pd.DataFrame(training_curves, columns=["label", "iter", "train_rmse", "valid_rmse"]).to_csv(
        OUT_DIR / "training_curves.csv", index=False
    )
    log("saved training_curves.csv")

    pd.DataFrame(importance_records, columns=["label", "rank", "feature", "importance"]).to_csv(
        OUT_DIR / "feature_importance_top20.csv", index=False
    )
    log("saved feature_importance_top20.csv")

    # 予測値保存 (close と timestamp も含める)
    pred_out = pred_test.copy()
    pred_out["close"] = df_test["close"].values
    pred_out.to_parquet(OUT_DIR / "predictions_test2025.parquet")
    log("saved predictions_test2025.parquet")

    # Phase 4-a 用: train 2021-04〜2024-12 の予測値 (L-183 data snooping 解消)
    log("=== predict on train 2021-04〜2024-12 (Phase 4-a/4-b 用) ===")
    pred_train_out = pred_train_all.copy()
    pred_train_out["close"] = df_train_full["close"].values
    pred_train_out.to_parquet(OUT_DIR / "predictions_train_2021_2024.parquet")
    log("saved predictions_train_2021_2024.parquet")

    # 予測値ヒストグラム
    fig, axes = plt.subplots(4, 4, figsize=(20, 16))
    for ax, label in zip(axes.flat, LABEL_COLS):
        ax.hist(pred_test[label].dropna(), bins=60)
        ax.set_title(label, fontsize=9)
        ax.tick_params(labelsize=7)
    fig.suptitle("Phase 1 — Test 2025 Prediction Histograms", fontsize=14)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "prediction_histograms.png", dpi=110)
    plt.close(fig)
    log("saved prediction_histograms.png")

    # pred vs real 散布図
    fig, axes = plt.subplots(4, 4, figsize=(20, 16))
    for ax, label in zip(axes.flat, LABEL_COLS):
        x = df_test[label].values
        y = pred_test[label].values
        m = ~(np.isnan(x) | np.isnan(y))
        ax.scatter(x[m], y[m], s=2, alpha=0.2)
        lo = min(np.nanmin(x[m]), np.nanmin(y[m]))
        hi = max(np.nanmax(x[m]), np.nanmax(y[m]))
        ax.plot([lo, hi], [lo, hi], "r-", linewidth=0.5)
        ax.set_title(label, fontsize=9)
        ax.set_xlabel("real", fontsize=7)
        ax.set_ylabel("pred", fontsize=7)
        ax.tick_params(labelsize=7)
    fig.suptitle("Phase 1 — Pred vs Real (Test 2025)", fontsize=14)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "pred_vs_real_scatter.png", dpi=110)
    plt.close(fig)
    log("saved pred_vs_real_scatter.png")

    # Entry 規則閾値 (§2): valid set 予測値の MFE/MAE 比 分位点
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

    # Entry 発火率 + 実 MFE/MAE 平均 (test 2025)
    firing_records: list[dict] = []
    for k in (12, 24, 48, 96):
        for side in ("LONG", "SHORT"):
            pmfe = pred_test[f"{side}_MFE_K{k}"]
            pmae = pred_test[f"{side}_MAE_K{k}"]
            pratio = pmfe / pmae.replace(0, np.nan)
            for q in THRESHOLD_QUANTILES:
                qkey = f"q{int(q*100)}"
                thr = thresholds[f"K{k}"][side][qkey]
                mask = (pratio >= thr).fillna(False)
                n_fire = int(mask.sum())
                rate = float(mask.mean())
                real_mfe = float(df_test.loc[mask, f"{side}_MFE_K{k}"].mean()) if n_fire else float("nan")
                real_mae = float(df_test.loc[mask, f"{side}_MAE_K{k}"].mean()) if n_fire else float("nan")
                firing_records.append(
                    dict(
                        K=k, side=side, q=qkey, threshold=thr,
                        firing_rate=rate, n_fire=n_fire,
                        mean_real_MFE=real_mfe, mean_real_MAE=real_mae,
                    )
                )
                log(
                    f"  fire K{k} {side} {qkey}: rate={rate:.3%} n={n_fire} "
                    f"real_MFE={real_mfe:.2f} real_MAE={real_mae:.2f}"
                )
    pd.DataFrame(firing_records).to_csv(OUT_DIR / "entry_firing_rate.csv", index=False)
    log("saved entry_firing_rate.csv")

    # ランダム比較 (§7.5): 同数ランダム発火との実 MFE/MAE 平均
    rng = np.random.default_rng(RANDOM_STATE)
    random_records: list[dict] = []
    for rec in firing_records:
        n_fire = rec["n_fire"]
        if n_fire <= 0:
            continue
        idx = rng.choice(len(df_test), size=n_fire, replace=False)
        rmfe = float(df_test.iloc[idx][f"{rec['side']}_MFE_K{rec['K']}"].mean())
        rmae = float(df_test.iloc[idx][f"{rec['side']}_MAE_K{rec['K']}"].mean())
        random_records.append(
            dict(
                K=rec["K"], side=rec["side"], q=rec["q"], n_fire=n_fire,
                ml_real_MFE=rec["mean_real_MFE"], ml_real_MAE=rec["mean_real_MAE"],
                random_real_MFE=rmfe, random_real_MAE=rmae,
                mfe_lift=rec["mean_real_MFE"] - rmfe,
                mae_lift=rec["mean_real_MAE"] - rmae,
            )
        )
    pd.DataFrame(random_records).to_csv(OUT_DIR / "random_baseline_comparison.csv", index=False)
    log("saved random_baseline_comparison.csv")

    # 楽観月次 PnL (Exit 未設計のため上限値: Entry 時 MFE を 100% 取れた前提)
    df_test_pnl = df_test[["close"] + LABEL_COLS].copy()
    df_test_pnl["__month"] = df_test_pnl.index.to_period("M").astype(str)
    monthly_records = []
    for k in (12, 24, 48, 96):
        for side in ("LONG", "SHORT"):
            for q in THRESHOLD_QUANTILES:
                qkey = f"q{int(q*100)}"
                thr = thresholds[f"K{k}"][side][qkey]
                pmfe = pred_test[f"{side}_MFE_K{k}"]
                pmae = pred_test[f"{side}_MAE_K{k}"]
                mask = ((pmfe / pmae.replace(0, np.nan)) >= thr).fillna(False)
                df_use = df_test_pnl[mask].copy()
                real_mfe_usd = df_use[f"{side}_MFE_K{k}"]  # USD 絶対値
                fee_usd = df_use["close"] * POS_SIZE_BTC * ROUND_TRIP_FEE
                df_use["__pnl_usd"] = POS_SIZE_BTC * real_mfe_usd - fee_usd
                if df_use.empty:
                    continue
                monthly = df_use.groupby("__month")["__pnl_usd"].agg(["sum", "count"]).reset_index()
                monthly["K"] = k
                monthly["side"] = side
                monthly["q"] = qkey
                monthly.rename(columns={"sum": "pnl_usd_optimistic", "count": "n_entry"}, inplace=True)
                monthly_records.append(monthly)
    if monthly_records:
        pd.concat(monthly_records, ignore_index=True).to_csv(
            OUT_DIR / "monthly_pnl_optimistic.csv", index=False
        )
        log("saved monthly_pnl_optimistic.csv")

    elapsed = time.time() - t0
    log(f"=== ML Phase 1 END (elapsed={elapsed/60:.1f} min) ===")

    write_summary(elapsed)


def write_summary(elapsed: float) -> None:
    fi = pd.read_csv(OUT_DIR / "feature_importance_top20.csv")
    fr = pd.read_csv(OUT_DIR / "entry_firing_rate.csv")
    rb = pd.read_csv(OUT_DIR / "random_baseline_comparison.csv")
    mp_path = OUT_DIR / "monthly_pnl_optimistic.csv"
    mp = pd.read_csv(mp_path) if mp_path.exists() else pd.DataFrame()

    md: list[str] = []
    md.append("# ML Phase 1 — LightGBM × 16 ラベル × デフォルトハイパラ\n\n")
    md.append(f"- 実行 TS: {TS}\n")
    md.append(f"- 所要: {elapsed/60:.1f} 分\n")
    md.append(f"- lightgbm: {lgb.__version__}\n\n")
    md.append("## §7.4 再現コマンド\n\n")
    md.append("```\npython3 scripts/priority_rebuild/run_lgbm_phase1.py\n```\n\n")
    md.append("## 出力ファイル\n\n")
    for p in sorted(OUT_DIR.iterdir()):
        if p.is_file():
            md.append(f"- `{p.name}` ({p.stat().st_size:,} bytes)\n")
    md.append("\n## 重要度 Top 5 × 16 モデル\n\n")
    for label in LABEL_COLS:
        md.append(f"### {label}\n\n")
        rows = fi[fi.label == label].head(5)
        for _, r in rows.iterrows():
            md.append(f"- {int(r['rank']):2d}. `{r['feature']}` (imp={int(r['importance'])})\n")
        md.append("\n")
    md.append("## Entry 発火率 (test 2025)\n\n")
    md.append("| K | side | q | threshold | rate | n_fire | mean_real_MFE | mean_real_MAE |\n")
    md.append("|---|------|---|-----------|------|--------|---------------|---------------|\n")
    for _, r in fr.iterrows():
        md.append(
            f"| {int(r['K'])} | {r['side']} | {r['q']} | {r['threshold']:.4f} | "
            f"{r['firing_rate']*100:.2f}% | {int(r['n_fire'])} | "
            f"{r['mean_real_MFE']:.2f} | {r['mean_real_MAE']:.2f} |\n"
        )
    md.append("\n## ランダム比較 (§7.5)\n\n")
    md.append("| K | side | q | n_fire | ML_real_MFE | rand_real_MFE | MFE_lift |\n")
    md.append("|---|------|---|--------|-------------|---------------|----------|\n")
    for _, r in rb.iterrows():
        md.append(
            f"| {int(r['K'])} | {r['side']} | {r['q']} | {int(r['n_fire'])} | "
            f"{r['ml_real_MFE']:.2f} | {r['random_real_MFE']:.2f} | {r['mfe_lift']:.2f} |\n"
        )
    if not mp.empty:
        md.append("\n## 楽観月次 PnL (USD・上限値・Exit 未設計)\n\n")
        md.append("- ⚠️ **Exit 未設計のため Entry 時 MFE 100% 取れた前提**。実 NET ではない。\n")
        md.append("- 採否判定 (§1.6 月次 $500 / §6 月次 $1,900) は Phase 4 Exit 設計後の現実 PnL で行う。\n\n")
        for (k, side, q), g in mp.groupby(["K", "side", "q"], sort=False):
            md.append(f"### K={int(k)} {side} {q}\n\n")
            md.append("| month | pnl_usd_optimistic | n_entry |\n|---|---|---|\n")
            for _, r in g.iterrows():
                md.append(
                    f"| {r['__month']} | {r['pnl_usd_optimistic']:.2f} | {int(r['n_entry'])} |\n"
                )
            md.append("\n")
    md.append("## 注記\n\n")
    md.append("- 月次損益は **楽観上限値**。Phase 4 Exit 設計で現実値が出る。\n")
    md.append("- ダッシュボードタブ統合は別ターン（本 Phase は静的 PNG で代替）。\n")
    md.append("- 技術要件: 時系列 valid (末尾 10%) / early_stopping=50 / random_state=42。\n")
    with open(OUT_DIR / "summary.md", "w") as f:
        f.write("".join(md))


if __name__ == "__main__":
    main()
