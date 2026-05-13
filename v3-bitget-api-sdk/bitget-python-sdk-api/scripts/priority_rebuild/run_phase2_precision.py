"""
Phase 2 精度判定 (4 指標合格条件・cc_ml_design_spec §1.6 commit b14be88 準拠)

入力:
  - results/priority_rebuild/labels_mfe_mae_test_2025.parquet (実測 MFE/MAE × 105,120 行)
  - results/priority_rebuild/ml_phase1/predictions_test2025.parquet (予測値 16 ラベル × 105,120 行)
  - results/priority_rebuild/ml_phase1/entry_thresholds.json (K 窓別 q90/q95/q99 閾値)
  - results/priority_rebuild/ml_phase1/label_distribution_stats.json (train ラベル分布 std)
  - results/priority_rebuild/ml_phase1/training_summary.csv (16 ラベル valid_rmse)

出力 (results/priority_rebuild/ml_phase2/):
  - phase2_summary.json
  - net_quality_24combinations.csv
  - rmse_sanity_16labels.csv
  - mfe_mae_ratio_24combinations.csv
  - old_leak_comparison.csv

# === Phase 2 計算定義 (cc_ml_design_spec §1.6 commit b14be88 準拠) ===
#
# 1. lift% 計算:
#    分母 = 全 5min 足 (test 2025) の MFE/MAE 平均
#    分子 = q90/q95/q99 フィルタ後 5min 足の MFE/MAE 平均
#    lift% = (分子 - 分母) / 分母 * 100
#
# 2. net_quality = MFE_lift% - MAE_lift% (lift% 差分)
#
# 3. 24 組合せの重み付け = q90/q95/q99 の Entry 件数加重平均
#    weighted_avg = Σ(net_quality[i] × Entry_count[i]) / Σ(Entry_count[i])
#
# 4. 計算対象期間 = 仮テスト 2025-01-01 〜 2025-12-31 (105,120 行)
#
# 5. Entry threshold = entry_thresholds.json (Phase 1 で生成済) を使用
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
LABEL_DIST_STATS = PHASE1_DIR / "label_distribution_stats.json"
TRAINING_SUMMARY = PHASE1_DIR / "training_summary.csv"

OUT_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

K_WINDOWS = [12, 24, 48, 96]
SIDES = ["LONG", "SHORT"]
QUANTILES = ["q90", "q95", "q99"]

# 4 指標合格基準 (cc_ml_design_spec §1.6)
CRITERION_1_WEIGHTED_AVG_MIN = 10.0
CRITERION_1_POSITIVE_MIN = 20
CRITERION_2_NET_QUALITY_MIN = -50.0
CRITERION_3_RMSE_RATIO_MAX = 1.5
CRITERION_3_PASS_COUNT = 14
CRITERION_4_MFE_MAE_RATIO_MIN = 1.0
CRITERION_4_PASS_COUNT = 20

# 旧 leak 由来実績 (参考値・cc_phase2_execute.md Step 0-5)
OLD_LEAK_REFERENCE = {
    "q99_net_quality_24combo_avg": 80.65,
    "top1_importance_share_phase1": 0.106,
    "top1_importance_share_phase3a": 0.027,
    "K96_SHORT_q99_mfe_mae_ratio": 0.986,
}


def log(msg):
    """timestamped log line to stdout."""
    ts = datetime.now().isoformat(timespec="seconds")
    print(f"[{ts}] {msg}", flush=True)


def load_inputs():
    log("loading inputs ...")
    df_labels = pd.read_parquet(LABELS_TEST).sort_index()
    df_preds = pd.read_parquet(PREDS_TEST).sort_index()
    with open(ENTRY_THRESHOLDS) as f:
        thresholds = json.load(f)
    with open(LABEL_DIST_STATS) as f:
        label_stats = json.load(f)
    train_summary = pd.read_csv(TRAINING_SUMMARY)

    assert len(df_labels) == len(df_preds), \
        f"row mismatch: labels={len(df_labels)} preds={len(df_preds)}"
    assert df_labels.index.equals(df_preds.index), "index mismatch (timestamps don't align)"
    log(f"  labels: rows={len(df_labels)} cols={len(df_labels.columns)}")
    log(f"  preds:  rows={len(df_preds)} cols={len(df_preds.columns)}")
    log(f"  period: {df_labels.index.min()} 〜 {df_labels.index.max()}")
    return df_labels, df_preds, thresholds, label_stats, train_summary


def compute_pred_ratio(df_preds, K, side):
    """予測値 MFE / MAE を返す (Entry 判定用)。"""
    mfe_col = f"{side}_MFE_K{K}"
    mae_col = f"{side}_MAE_K{K}"
    pred_mfe = df_preds[mfe_col]
    pred_mae = df_preds[mae_col].clip(lower=1e-9)
    return pred_mfe / pred_mae


def compute_net_quality(df_labels, df_preds, thresholds):
    """24 組合せ別 net_quality を返す。

    Returns:
      DataFrame with columns:
        K, side, q, threshold, n_fire, fire_rate,
        global_mean_real_MFE, global_mean_real_MAE,
        filtered_mean_real_MFE, filtered_mean_real_MAE,
        MFE_lift_pct, MAE_lift_pct, net_quality_pp
    """
    rows = []
    for K in K_WINDOWS:
        for side in SIDES:
            mfe_col = f"{side}_MFE_K{K}"
            mae_col = f"{side}_MAE_K{K}"
            real_mfe = df_labels[mfe_col]
            real_mae = df_labels[mae_col]
            valid = real_mfe.notna() & real_mae.notna()
            global_mean_mfe = real_mfe[valid].mean()
            global_mean_mae = real_mae[valid].mean()

            pred_ratio = compute_pred_ratio(df_preds, K, side)
            for q in QUANTILES:
                thr = thresholds[f"K{K}"][side][q]
                fire = (pred_ratio >= thr) & valid
                n_fire = int(fire.sum())
                if n_fire == 0:
                    rows.append({
                        "K": K, "side": side, "q": q, "threshold": thr,
                        "n_fire": 0, "fire_rate": 0.0,
                        "global_mean_real_MFE": global_mean_mfe,
                        "global_mean_real_MAE": global_mean_mae,
                        "filtered_mean_real_MFE": np.nan,
                        "filtered_mean_real_MAE": np.nan,
                        "MFE_lift_pct": np.nan,
                        "MAE_lift_pct": np.nan,
                        "net_quality_pp": np.nan,
                    })
                    continue
                f_mfe = real_mfe[fire].mean()
                f_mae = real_mae[fire].mean()
                mfe_lift = (f_mfe / global_mean_mfe - 1.0) * 100.0
                mae_lift = (f_mae / global_mean_mae - 1.0) * 100.0
                net_q = mfe_lift - mae_lift
                rows.append({
                    "K": K, "side": side, "q": q, "threshold": thr,
                    "n_fire": n_fire, "fire_rate": n_fire / int(valid.sum()),
                    "global_mean_real_MFE": global_mean_mfe,
                    "global_mean_real_MAE": global_mean_mae,
                    "filtered_mean_real_MFE": f_mfe,
                    "filtered_mean_real_MAE": f_mae,
                    "MFE_lift_pct": mfe_lift,
                    "MAE_lift_pct": mae_lift,
                    "net_quality_pp": net_q,
                })
    return pd.DataFrame(rows)


def compute_rmse_sanity(label_stats, train_summary):
    """16 ラベル valid_rmse / label_std."""
    rows = []
    for _, row in train_summary.iterrows():
        label = row["label"]
        valid_rmse = float(row["valid_rmse"])
        label_std = float(label_stats[label]["std"])
        rmse_ratio = valid_rmse / label_std
        rows.append({
            "label": label,
            "valid_rmse": valid_rmse,
            "label_std": label_std,
            "rmse_ratio": rmse_ratio,
            "pass": bool(rmse_ratio < CRITERION_3_RMSE_RATIO_MAX),
        })
    return pd.DataFrame(rows)


def judge_criteria(df_nq, df_rmse):
    """4 指標 PASS/FAIL 判定."""
    # 指標 1: weighted avg net_quality (q99 only, 24 組合せ全体)
    # spec: "q99 net_quality (24 組合せ件数加重平均)" + "24 組合せ中 20 組以上で > 0"
    #       -> 24 組合せは q90/q95/q99 × K × side のすべて (注記より)
    df_all = df_nq.dropna(subset=["net_quality_pp"])
    if len(df_all) == 0:
        return {}, {}
    weighted_sum = (df_all["net_quality_pp"] * df_all["n_fire"]).sum()
    total_fire = df_all["n_fire"].sum()
    weighted_avg = weighted_sum / total_fire if total_fire > 0 else float("nan")
    n_positive = int((df_all["net_quality_pp"] > 0).sum())
    n_combos = len(df_all)

    c1_avg_pass = bool(weighted_avg > CRITERION_1_WEIGHTED_AVG_MIN)
    c1_pos_pass = bool(n_positive >= CRITERION_1_POSITIVE_MIN)
    c1_pass = c1_avg_pass and c1_pos_pass

    # 指標 2: net_quality 最小値 > -50pp
    min_nq = float(df_all["net_quality_pp"].min())
    min_row = df_all.loc[df_all["net_quality_pp"].idxmin()]
    c2_pass = bool(min_nq > CRITERION_2_NET_QUALITY_MIN)

    # 指標 3: 16 ラベル中 14 以上で valid_rmse / label_std < 1.5
    n_rmse_pass = int(df_rmse["pass"].sum())
    c3_pass = bool(n_rmse_pass >= CRITERION_3_PASS_COUNT)

    # 指標 4: 24 組合せ中 20 以上で mean_real_MFE / mean_real_MAE > 1.0
    df_all = df_all.assign(
        mfe_mae_ratio=df_all["filtered_mean_real_MFE"] / df_all["filtered_mean_real_MAE"]
    )
    n_mfe_mae_pass = int((df_all["mfe_mae_ratio"] > CRITERION_4_MFE_MAE_RATIO_MIN).sum())
    c4_pass = bool(n_mfe_mae_pass >= CRITERION_4_PASS_COUNT)

    summary = {
        "criterion_1_weighted_avg_net_quality": {
            "value_pp": float(weighted_avg),
            "threshold_pp": CRITERION_1_WEIGHTED_AVG_MIN,
            "positive_count": n_positive,
            "positive_threshold": CRITERION_1_POSITIVE_MIN,
            "n_combinations": n_combos,
            "pass_avg": c1_avg_pass,
            "pass_positive": c1_pos_pass,
            "pass": c1_pass,
        },
        "criterion_2_min_net_quality": {
            "value_pp": min_nq,
            "threshold_pp": CRITERION_2_NET_QUALITY_MIN,
            "min_combination": {
                "K": int(min_row["K"]),
                "side": str(min_row["side"]),
                "q": str(min_row["q"]),
            },
            "pass": c2_pass,
        },
        "criterion_3_rmse_ratio": {
            "n_pass": n_rmse_pass,
            "n_total": int(len(df_rmse)),
            "threshold_ratio": CRITERION_3_RMSE_RATIO_MAX,
            "threshold_count": CRITERION_3_PASS_COUNT,
            "pass": c3_pass,
        },
        "criterion_4_mfe_mae_ratio": {
            "n_pass": n_mfe_mae_pass,
            "n_total": int(len(df_all)),
            "threshold_ratio": CRITERION_4_MFE_MAE_RATIO_MIN,
            "threshold_count": CRITERION_4_PASS_COUNT,
            "pass": c4_pass,
        },
        "overall_pass": c1_pass and c2_pass and c3_pass and c4_pass,
    }
    return summary, df_all


def k96_short_q99_inverse_check(df_nq):
    """K96 SHORT q99 個別チェック (旧 leak で MFE=880.32 < MAE=892.80・逆行)."""
    row = df_nq[(df_nq.K == 96) & (df_nq.side == "SHORT") & (df_nq.q == "q99")].iloc[0]
    mfe = row["filtered_mean_real_MFE"]
    mae = row["filtered_mean_real_MAE"]
    ratio = mfe / mae if mae > 0 else float("nan")
    nq_pp = row["net_quality_pp"]
    if ratio > 1.10:
        verdict = "✅維持"
    elif ratio > 0.90:
        verdict = "⚠️逆行 (旧 leak 由来と同水準)"
    else:
        verdict = "❌大幅悪化"
    return {
        "mean_real_MFE": float(mfe),
        "mean_real_MAE": float(mae),
        "mfe_mae_ratio": float(ratio),
        "net_quality_pp": float(nq_pp),
        "verdict": verdict,
    }


def old_leak_comparison(summary, k96):
    """旧 leak 実績 vs 新 leak-free 比較."""
    new_q99_avg_24combo = summary["criterion_1_weighted_avg_net_quality"]["value_pp"]
    rows = [
        {
            "metric": "q99 net_quality 24組合せ加重平均",
            "old_leak": OLD_LEAK_REFERENCE["q99_net_quality_24combo_avg"],
            "new_leak_free": new_q99_avg_24combo,
            "delta": new_q99_avg_24combo - OLD_LEAK_REFERENCE["q99_net_quality_24combo_avg"],
            "flag": "⚠️" if abs(new_q99_avg_24combo - OLD_LEAK_REFERENCE["q99_net_quality_24combo_avg"]) > 50 else "✅",
        },
        {
            "metric": "K96 SHORT q99 MFE/MAE 比",
            "old_leak": OLD_LEAK_REFERENCE["K96_SHORT_q99_mfe_mae_ratio"],
            "new_leak_free": k96["mfe_mae_ratio"],
            "delta": k96["mfe_mae_ratio"] - OLD_LEAK_REFERENCE["K96_SHORT_q99_mfe_mae_ratio"],
            "flag": "⚠️" if abs(k96["mfe_mae_ratio"] - OLD_LEAK_REFERENCE["K96_SHORT_q99_mfe_mae_ratio"]) > 0.5 else "✅",
        },
    ]
    return pd.DataFrame(rows)


def main():
    t0 = datetime.now()
    log(f"Phase 2 precision judgment START at {t0.isoformat()}")
    df_labels, df_preds, thresholds, label_stats, train_summary = load_inputs()

    log("computing net_quality for 24 combinations ...")
    df_nq = compute_net_quality(df_labels, df_preds, thresholds)

    log("computing rmse_sanity for 16 labels ...")
    df_rmse = compute_rmse_sanity(label_stats, train_summary)

    log("judging 4 criteria ...")
    summary, df_all = judge_criteria(df_nq, df_rmse)

    log("K96 SHORT q99 reversal check ...")
    k96 = k96_short_q99_inverse_check(df_nq)
    summary["k96_short_q99_check"] = k96

    log("old leak comparison ...")
    df_compare = old_leak_comparison(summary, k96)

    # MFE/MAE ratio table (24 組合せ)
    df_mfe_mae = df_all[["K", "side", "q", "filtered_mean_real_MFE", "filtered_mean_real_MAE", "mfe_mae_ratio"]].copy()
    df_mfe_mae["pass"] = df_mfe_mae["mfe_mae_ratio"] > CRITERION_4_MFE_MAE_RATIO_MIN

    # save outputs
    log("saving outputs ...")
    df_nq.to_csv(OUT_DIR / "net_quality_24combinations.csv", index=False)
    df_rmse.to_csv(OUT_DIR / "rmse_sanity_16labels.csv", index=False)
    df_mfe_mae.to_csv(OUT_DIR / "mfe_mae_ratio_24combinations.csv", index=False)
    df_compare.to_csv(OUT_DIR / "old_leak_comparison.csv", index=False)
    with open(OUT_DIR / "phase2_summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)

    # console summary
    print()
    print("=" * 70)
    print("Phase 2 結果サマリー")
    print("=" * 70)
    c1 = summary["criterion_1_weighted_avg_net_quality"]
    c2 = summary["criterion_2_min_net_quality"]
    c3 = summary["criterion_3_rmse_ratio"]
    c4 = summary["criterion_4_mfe_mae_ratio"]
    print(f"指標1 (q99 net_quality 加重平均): {c1['value_pp']:+.2f}pp (threshold > {c1['threshold_pp']:.1f}pp) / positive {c1['positive_count']}/{c1['n_combinations']} (threshold >= {c1['positive_threshold']}) → {'✅PASS' if c1['pass'] else '❌FAIL'}")
    print(f"指標2 (net_quality 最小値):       {c2['value_pp']:+.2f}pp at K{c2['min_combination']['K']} {c2['min_combination']['side']} {c2['min_combination']['q']} (threshold > {c2['threshold_pp']:.1f}pp) → {'✅PASS' if c2['pass'] else '❌FAIL'}")
    print(f"指標3 (RMSE 比率 < 1.5):          {c3['n_pass']}/{c3['n_total']} (threshold >= {c3['threshold_count']}) → {'✅PASS' if c3['pass'] else '❌FAIL'}")
    print(f"指標4 (MFE/MAE 比 > 1.0):         {c4['n_pass']}/{c4['n_total']} (threshold >= {c4['threshold_count']}) → {'✅PASS' if c4['pass'] else '❌FAIL'}")
    print()
    print(f"全体: {'✅ ALL PASS → Phase 3 進める' if summary['overall_pass'] else '❌ 1件以上 FAIL → まこさん協議'}")
    print()
    print(f"K96 SHORT q99: MFE={k96['mean_real_MFE']:.2f} MAE={k96['mean_real_MAE']:.2f} ratio={k96['mfe_mae_ratio']:.3f} {k96['verdict']}")
    print()
    print("旧 leak 比較:")
    print(df_compare.to_string(index=False))
    print()

    t1 = datetime.now()
    log(f"Phase 2 precision judgment END at {t1.isoformat()} (elapsed {(t1-t0).total_seconds():.1f}s)")
    return 0 if summary["overall_pass"] else 2  # exit code 2 = 1件以上 FAIL


if __name__ == "__main__":
    sys.exit(main())
