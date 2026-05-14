"""
Phase 2 Step 1 構造的原因 短期診断
(指示書: .claude/instructions/2026-05-14_phase2_step1_diagnosis.md)

3 項目を既存 CSV / parquet から分析:
  1-1. K96 SHORT q99 逆行 1,660件 の時期分布
  1-2. K12 LONG MFE_lift マイナスの mechanism
  1-3. q90/q95/q99 発火 timestamp 重複率

注: 指示書中の python コード片は generic prefix `pred_*` 使用だが、
実 parquet 列名は prefix なし (`LONG_MFE_K12` 等)。
閾値は entry_thresholds.json (Phase 2 と同じ・1,660 件再現するため) を使用。
"""

import json
import sys
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
LABELS_TEST = REPO_ROOT / "results" / "priority_rebuild" / "labels_mfe_mae_test_2025.parquet"
PHASE1_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase1"
PREDS_TEST = PHASE1_DIR / "predictions_test2025.parquet"
ENTRY_THRESHOLDS = PHASE1_DIR / "entry_thresholds.json"
FEAT_IMP_K12_LONG_MFE = PHASE1_DIR / "feature_importance_full_rank_LONG_MFE_K12.csv"

OUT_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

K_WINDOWS = [12, 24, 48, 96]
SIDES = ["LONG", "SHORT"]
QUANTILES = ["q90", "q95", "q99"]


def log(msg):
    ts = datetime.now().isoformat(timespec="seconds")
    print(f"[{ts}] {msg}", flush=True)


def fired_mask(df_preds, K, side, q_thr):
    """予測 MFE/MAE 比が q_thr 以上の行マスク."""
    mfe = df_preds[f"{side}_MFE_K{K}"]
    mae = df_preds[f"{side}_MAE_K{K}"].clip(lower=1e-9)
    ratio = mfe / mae
    return ratio >= q_thr


def step_1_1(df_preds, df_labels, thresholds):
    """K96 SHORT q99 逆行 1,660件 月別分布."""
    log("Step 1-1: K96 SHORT q99 monthly distribution ...")
    K, side, q = 96, "SHORT", "q99"
    thr = thresholds[f"K{K}"][side][q]
    mask = fired_mask(df_preds, K, side, thr)
    fired_ts = df_preds.index[mask]
    n = len(fired_ts)
    log(f"  K{K} {side} {q} threshold={thr:.4f} n_fire={n}")
    real_mfe = df_labels.loc[fired_ts, f"{side}_MFE_K{K}"]
    real_mae = df_labels.loc[fired_ts, f"{side}_MAE_K{K}"]
    df_fired = pd.DataFrame({
        "real_MFE": real_mfe.values,
        "real_MAE": real_mae.values,
    }, index=fired_ts)
    df_fired["month"] = df_fired.index.to_period("M")
    rows = []
    for month, g in df_fired.groupby("month"):
        rows.append({
            "month": str(month),
            "n": len(g),
            "real_MFE_mean": float(g["real_MFE"].mean()),
            "real_MAE_mean": float(g["real_MAE"].mean()),
            "MFE_MAE_ratio": float(g["real_MFE"].mean() / g["real_MAE"].mean()),
            "share_pct": len(g) / n * 100,
        })
    df_out = pd.DataFrame(rows)
    df_out.to_csv(OUT_DIR / "step1_1_k96_short_q99_monthly.csv", index=False)
    return df_out, n


def step_1_2(df_preds, df_labels, thresholds, K=12, side="LONG"):
    """K12 LONG MFE_lift マイナスの mechanism (top 重要度指標の発火 vs 全体比較)."""
    log(f"Step 1-2: K{K} {side} mechanism (top 重要度指標の発火 vs 全体) ...")
    imp = pd.read_csv(FEAT_IMP_K12_LONG_MFE)
    imp_top = imp.head(10).copy()
    log(f"  top 10 features for {side}_MFE_K{K}:")
    print(imp_top.to_string(index=False))

    thr_q99 = thresholds[f"K{K}"][side]["q99"]
    mask_q99 = fired_mask(df_preds, K, side, thr_q99)
    log(f"  K{K} {side} q99 threshold={thr_q99:.4f} n_fire={mask_q99.sum()}")

    # 特徴量は labels parquet に同居 (1,432 features + 16 labels + 1 close)
    feat_cols = imp_top["feature"].tolist()
    rows = []
    for feat in feat_cols:
        if feat not in df_labels.columns:
            log(f"  WARN: feature {feat} not in labels parquet")
            continue
        col = df_labels[feat]
        fired_mean = float(col[mask_q99].mean())
        all_mean = float(col.mean())
        denom = abs(all_mean) if abs(all_mean) > 1e-9 else 1e-9
        lift_pct = (fired_mean - all_mean) / denom * 100
        rows.append({
            "feature": feat,
            "importance": float(imp_top[imp_top["feature"] == feat]["importance"].iloc[0]),
            "all_mean": all_mean,
            "fired_mean (q99)": fired_mean,
            "lift_pct (q99 vs all)": lift_pct,
        })
    df_out = pd.DataFrame(rows)
    df_out.to_csv(OUT_DIR / "step1_2_k12_long_mechanism.csv", index=False)
    log(f"  saved step1_2 with {len(df_out)} rows")
    return df_out


def step_1_3(df_preds, thresholds):
    """q90/q95/q99 発火 timestamp の包含率."""
    log("Step 1-3: q overlap ...")
    rows = []
    for K in K_WINDOWS:
        for side in SIDES:
            thr_q90 = thresholds[f"K{K}"][side]["q90"]
            thr_q95 = thresholds[f"K{K}"][side]["q95"]
            thr_q99 = thresholds[f"K{K}"][side]["q99"]
            m90 = fired_mask(df_preds, K, side, thr_q90)
            m95 = fired_mask(df_preds, K, side, thr_q95)
            m99 = fired_mask(df_preds, K, side, thr_q99)
            s90 = set(df_preds.index[m90])
            s95 = set(df_preds.index[m95])
            s99 = set(df_preds.index[m99])
            q99_in_q95 = (len(s99 & s95) / len(s99) * 100) if len(s99) > 0 else float("nan")
            q99_in_q90 = (len(s99 & s90) / len(s99) * 100) if len(s99) > 0 else float("nan")
            q95_in_q90 = (len(s95 & s90) / len(s95) * 100) if len(s95) > 0 else float("nan")
            rows.append({
                "K": K, "side": side,
                "n_q90": len(s90),
                "n_q95": len(s95),
                "n_q99": len(s99),
                "q99_in_q95_pct": q99_in_q95,
                "q99_in_q90_pct": q99_in_q90,
                "q95_in_q90_pct": q95_in_q90,
            })
    df_out = pd.DataFrame(rows)
    df_out.to_csv(OUT_DIR / "step1_3_q_overlap.csv", index=False)
    return df_out


def main():
    t0 = datetime.now()
    log(f"Phase 2 Step 1 diagnosis START at {t0.isoformat()}")
    log("loading inputs ...")
    df_preds = pd.read_parquet(PREDS_TEST).sort_index()
    df_labels = pd.read_parquet(LABELS_TEST).sort_index()
    with open(ENTRY_THRESHOLDS) as f:
        thresholds = json.load(f)
    log(f"  preds rows={len(df_preds)} cols={len(df_preds.columns)}")
    log(f"  labels rows={len(df_labels)} cols={len(df_labels.columns)}")
    assert df_preds.index.equals(df_labels.index), "preds/labels index mismatch"

    # === Step 1-1 ===
    df_1_1, n_k96_short_q99 = step_1_1(df_preds, df_labels, thresholds)
    print()
    print("=" * 70)
    print(f"Step 1-1: K96 SHORT q99 monthly distribution (total n={n_k96_short_q99})")
    print("=" * 70)
    print(df_1_1.to_string(index=False))
    # 集中度判定
    max_share = df_1_1["share_pct"].max()
    if max_share > 50:
        verdict_11 = f"⚠️ 1ヶ月集中 (max={max_share:.1f}%) → 特定イベント起因"
    elif df_1_1.sort_values("share_pct", ascending=False).head(4)["share_pct"].sum() > 70:
        verdict_11 = f"⚠️ 3-4ヶ月集中 (top4={df_1_1.sort_values('share_pct', ascending=False).head(4)['share_pct'].sum():.1f}%) → 暴騰局面集中"
    else:
        verdict_11 = f"分散 (max={max_share:.1f}%) → 構造的問題"
    print(f"\n判定: {verdict_11}")

    # === Step 1-2 ===
    df_1_2 = step_1_2(df_preds, df_labels, thresholds)
    print()
    print("=" * 70)
    print("Step 1-2: K12 LONG q99 発火足 vs 全足 (top 10 importance 特徴量)")
    print("=" * 70)
    print(df_1_2.to_string(index=False))

    # === Step 1-3 ===
    df_1_3 = step_1_3(df_preds, thresholds)
    print()
    print("=" * 70)
    print("Step 1-3: q90/q95/q99 発火 timestamp 包含率 (16 labels)")
    print("=" * 70)
    print(df_1_3.to_string(index=False))
    min_q99_in_q90 = df_1_3["q99_in_q90_pct"].min()
    if min_q99_in_q90 >= 99.5:
        verdict_13 = f"全 100% (完全包含) — q別取扱は閾値選択"
    elif min_q99_in_q90 >= 50:
        verdict_13 = f"部分一致 ({min_q99_in_q90:.1f}% 最低) — 案B は別の足採用を意味する・spec 改訂要"
    else:
        verdict_13 = f"50% 未満 — 独立シグナル混在・別 cluster 化要"
    print(f"\n判定: {verdict_13}")

    t1 = datetime.now()
    log(f"Phase 2 Step 1 diagnosis END at {t1.isoformat()} (elapsed {(t1-t0).total_seconds():.1f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
