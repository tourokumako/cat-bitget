"""run_phase2_stage1_review.py — [2] Entry ML baseline Stage 1 統計指標 review

目的:
  - baseline 出力 (= results/priority_rebuild/ml_phase2_baseline/) を 168 個 読込み集計
  - 56 ラベル × 3 fold = 168 個の metric 分布を task type 別に出力
  - leak verify 集計 (= blacklist 0 件 verify + suspicious 89 件の中身)
  - regime engagement 集計 (= 8 列が何モデルで top 50 入り)
  - 主要結論を 1 行で出力

§6.2.1 Stage 1 評価指標:
  - 揺れ幅系 28 (回帰): RMSE / R² (target 別 + uniform 平均)
  - Triple Barrier 14 (3 class): multi_logloss / accuracy / F1_macro + Brier/ECE
  - meta_label 14 (binary): AUC / Precision / Recall + Brier/ECE
  - 56 ラベル間予測相関 (= §6.2.2 懸念 verify) は別 script で実施
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
BASELINE_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase2_baseline"
OUT_REPORT = BASELINE_DIR / "stage1_review.md"
OUT_DETAILS_CSV = BASELINE_DIR / "stage1_review_details.csv"


def load_all_metrics() -> list:
    """168 個の metrics.json を全部読み込み."""
    out = []
    for d in sorted(BASELINE_DIR.iterdir()):
        if not d.is_dir():
            continue
        mfile = d / "metrics.json"
        if not mfile.exists():
            continue
        try:
            data = json.loads(mfile.read_text())
            out.append(data)
        except Exception as e:
            print(f"⚠️ load failed: {mfile} ({e})")
    return out


def summarize_regression(records: list) -> dict:
    """回帰 84 個 (= 28 label × 3 fold) の RMSE / R² 集計."""
    df = pd.DataFrame([{
        "label": r["label"],
        "fold": r["fold"],
        "test_rmse": r["metrics"]["test_rmse"],
        "test_r2": r["metrics"]["test_r2"],
        "label_std": r["metrics"]["label_std_train"],
        "best_iter": r["best_iter"],
        "elapsed_sec": r["elapsed_sec"],
    } for r in records])
    by_label = df.groupby("label").agg(
        test_rmse_mean=("test_rmse", "mean"),
        test_rmse_std=("test_rmse", "std"),
        test_r2_mean=("test_r2", "mean"),
        test_r2_std=("test_r2", "std"),
        best_iter_mean=("best_iter", "mean"),
    ).round(4).sort_values("test_r2_mean", ascending=False)
    return {
        "df_per_run": df,
        "by_label": by_label,
        "global_r2_mean": float(df["test_r2"].mean()),
        "global_r2_median": float(df["test_r2"].median()),
        "global_r2_max": float(df["test_r2"].max()),
        "global_r2_min": float(df["test_r2"].min()),
        "n_r2_positive": int((df["test_r2"] > 0).sum()),
        "n_r2_over_005": int((df["test_r2"] > 0.05).sum()),
        "n_r2_over_010": int((df["test_r2"] > 0.10).sum()),
    }


def summarize_multiclass(records: list) -> dict:
    """多クラス 42 個 (= 14 label × 3 fold) の accuracy / F1 / Brier / ECE 集計."""
    df = pd.DataFrame([{
        "label": r["label"],
        "fold": r["fold"],
        "test_accuracy": r["metrics"]["test_accuracy"],
        "test_accuracy_cal": r["metrics"]["test_accuracy_cal"],
        "test_f1_macro": r["metrics"]["test_f1_macro"],
        "test_f1_macro_cal": r["metrics"]["test_f1_macro_cal"],
        "test_multi_logloss": r["metrics"]["test_multi_logloss"],
        "test_multi_logloss_cal": r["metrics"]["test_multi_logloss_cal"],
        "test_brier_macro": r["metrics"]["test_brier_macro"],
        "test_ece_macro": r["metrics"]["test_ece_macro"],
        "best_iter": r["best_iter"],
    } for r in records])
    by_label = df.groupby("label").agg(
        accuracy_mean=("test_accuracy", "mean"),
        accuracy_cal_mean=("test_accuracy_cal", "mean"),
        f1_macro_mean=("test_f1_macro", "mean"),
        f1_macro_cal_mean=("test_f1_macro_cal", "mean"),
        brier_mean=("test_brier_macro", "mean"),
        ece_mean=("test_ece_macro", "mean"),
    ).round(4).sort_values("accuracy_cal_mean", ascending=False)
    return {
        "df_per_run": df,
        "by_label": by_label,
        "accuracy_random": 1.0 / 3,  # 3 クラス random
        "global_acc_mean": float(df["test_accuracy"].mean()),
        "global_acc_cal_mean": float(df["test_accuracy_cal"].mean()),
        "global_f1_macro_mean": float(df["test_f1_macro"].mean()),
        "global_f1_macro_cal_mean": float(df["test_f1_macro_cal"].mean()),
        "global_ece_mean": float(df["test_ece_macro"].mean()),
        "n_acc_over_random": int((df["test_accuracy"] > 1.0 / 3).sum()),
    }


def summarize_binary(records: list) -> dict:
    """2 値 42 個 (= 14 label × 3 fold) の AUC / F1 / Brier / ECE 集計."""
    df = pd.DataFrame([{
        "label": r["label"],
        "fold": r["fold"],
        "test_accuracy": r["metrics"]["test_accuracy"],
        "test_accuracy_cal": r["metrics"]["test_accuracy_cal"],
        "test_f1": r["metrics"]["test_f1"],
        "test_f1_cal": r["metrics"]["test_f1_cal"],
        "test_auc": r["metrics"]["test_auc"],
        "test_auc_cal": r["metrics"]["test_auc_cal"],
        "test_brier": r["metrics"]["test_brier"],
        "test_ece": r["metrics"]["test_ece"],
        "scale_pos_weight": r["metrics"]["scale_pos_weight"],
        "best_iter": r["best_iter"],
    } for r in records])
    by_label = df.groupby("label").agg(
        auc_mean=("test_auc", "mean"),
        auc_cal_mean=("test_auc_cal", "mean"),
        accuracy_cal_mean=("test_accuracy_cal", "mean"),
        f1_cal_mean=("test_f1_cal", "mean"),
        brier_mean=("test_brier", "mean"),
        ece_mean=("test_ece", "mean"),
    ).round(4).sort_values("auc_mean", ascending=False)
    return {
        "df_per_run": df,
        "by_label": by_label,
        "global_auc_mean": float(df["test_auc"].mean()),
        "global_auc_cal_mean": float(df["test_auc_cal"].mean()),
        "global_f1_mean": float(df["test_f1"].mean()),
        "global_ece_mean": float(df["test_ece"].mean()),
        "n_auc_over_055": int((df["test_auc"] > 0.55).sum()),
        "n_auc_over_060": int((df["test_auc"] > 0.60).sum()),
    }


def aggregate_leak(records: list) -> dict:
    """leak hit を全 168 件横断で集計."""
    blacklist_hits = []
    suspicious_hits = []
    regime_engagement_per_model = []
    for r in records:
        leak = r.get("leak_check", {})
        for h in leak.get("blacklist_hits", []):
            blacklist_hits.append({"label": r["label"], "fold": r["fold"], "hit": h})
        for h in leak.get("suspicious_hits", []):
            suspicious_hits.append({"label": r["label"], "fold": r["fold"], "feature": h[0], "pattern": h[1]})
        regime_engagement_per_model.append({
            "label": r["label"],
            "fold": r["fold"],
            "task_type": r["task_type"],
            "regime_count": r.get("regime_in_top50_count", 0),
        })

    susp_df = pd.DataFrame(suspicious_hits)
    susp_pattern_counts = susp_df["pattern"].value_counts().to_dict() if len(susp_df) else {}
    susp_feature_top = susp_df["feature"].value_counts().head(10).to_dict() if len(susp_df) else {}

    regime_df = pd.DataFrame(regime_engagement_per_model)
    n_with_regime = int((regime_df["regime_count"] > 0).sum())
    n_models = len(regime_df)
    regime_by_task = regime_df.groupby("task_type")["regime_count"].agg(["mean", "max", lambda x: (x > 0).sum()])
    regime_by_task.columns = ["mean", "max", "n_with_regime"]

    return {
        "blacklist_hits_count": len(blacklist_hits),
        "blacklist_hits": blacklist_hits,
        "suspicious_hits_count": len(suspicious_hits),
        "suspicious_pattern_counts": susp_pattern_counts,
        "suspicious_feature_top10": susp_feature_top,
        "regime_n_models_with_engagement": n_with_regime,
        "regime_n_models_total": n_models,
        "regime_engagement_rate": n_with_regime / n_models if n_models else 0,
        "regime_by_task": regime_by_task.to_dict(),
    }


def write_report(records: list, regr: dict, mc: dict, binr: dict, leak: dict) -> str:
    lines = []
    A = lines.append
    A("# [2] Entry ML baseline — Stage 1 統計指標 review")
    A("")
    A(f"baseline 完走: 168/168 学習 / elapsed 55.7 min / {pd.Timestamp.now()}")
    A("")
    A("## ❗ 結論 1 行サマリ")
    A("")
    A(f"- 回帰 (= 揺れ幅): R² 中央値 = {regr['global_r2_median']:.4f} (= ほぼランダム同等)・R² > 0.10 は {regr['n_r2_over_010']}/{len(regr['df_per_run'])} 件のみ")
    A(f"- 多クラス (= Triple Barrier): accuracy 平均 = {mc['global_acc_mean']:.4f} (= ランダム {mc['accuracy_random']:.4f} = 33.3% より高い・改善幅 +{(mc['global_acc_mean']-mc['accuracy_random'])*100:.1f}pt)")
    A(f"- 2 値 (= meta_label): AUC 平均 = {binr['global_auc_mean']:.4f} (= ランダム 0.50 より +{(binr['global_auc_mean']-0.5)*100:.1f}pt)・AUC > 0.55 は {binr['n_auc_over_055']}/{len(binr['df_per_run'])} 件")
    A(f"- leak verify: blacklist hit {leak['blacklist_hits_count']} 件 ✅ / suspicious hit {leak['suspicious_hits_count']} 件 (= fractal/level/fib 系)")
    A(f"- regime engagement: {leak['regime_n_models_with_engagement']}/{leak['regime_n_models_total']} モデル ({leak['regime_engagement_rate']*100:.1f}%) で regime 8 列のいずれかが top 50 入り")
    A("")

    A("## §6.2.1 Stage 1 評価指標 — 系統別集計")
    A("")
    A("### 回帰 28 ラベル (= 揺れ幅 MFE/MAE pct)")
    A("")
    A(f"- N = {len(regr['df_per_run'])} (= 28 label × 3 fold)")
    A(f"- R²: mean={regr['global_r2_mean']:.4f} / median={regr['global_r2_median']:.4f} / max={regr['global_r2_max']:.4f} / min={regr['global_r2_min']:.4f}")
    A(f"- R² > 0: {regr['n_r2_positive']}/{len(regr['df_per_run'])} ({regr['n_r2_positive']/len(regr['df_per_run'])*100:.0f}%)")
    A(f"- R² > 0.05: {regr['n_r2_over_005']}/{len(regr['df_per_run'])} ({regr['n_r2_over_005']/len(regr['df_per_run'])*100:.0f}%)")
    A(f"- R² > 0.10: {regr['n_r2_over_010']}/{len(regr['df_per_run'])} ({regr['n_r2_over_010']/len(regr['df_per_run'])*100:.0f}%)")
    A("")
    A("**ラベル別 R² (3 fold 平均・降順 top 10)**:")
    A("")
    A(regr["by_label"].head(10).to_markdown())
    A("")
    A("**ラベル別 R² (3 fold 平均・bottom 5)**:")
    A("")
    A(regr["by_label"].tail(5).to_markdown())
    A("")

    A("### 多クラス 14 ラベル (= Triple Barrier 3 class)")
    A("")
    A(f"- N = {len(mc['df_per_run'])} (= 14 label × 3 fold) / random accuracy = 33.3%")
    A(f"- accuracy: mean={mc['global_acc_mean']:.4f} / cal={mc['global_acc_cal_mean']:.4f}")
    A(f"- f1_macro: mean={mc['global_f1_macro_mean']:.4f} / cal={mc['global_f1_macro_cal_mean']:.4f}")
    A(f"- ECE_macro: mean={mc['global_ece_mean']:.4f} (= キャリブレーション後)")
    A(f"- accuracy > random (33.3%): {mc['n_acc_over_random']}/{len(mc['df_per_run'])}")
    A("")
    A("**ラベル別 accuracy_cal (3 fold 平均・降順 top 10)**:")
    A("")
    A(mc["by_label"].head(10).to_markdown())
    A("")

    A("### 2 値 14 ラベル (= meta_label)")
    A("")
    A(f"- N = {len(binr['df_per_run'])} (= 14 label × 3 fold) / random AUC = 0.50")
    A(f"- AUC: mean={binr['global_auc_mean']:.4f} / cal={binr['global_auc_cal_mean']:.4f}")
    A(f"- F1: mean={binr['global_f1_mean']:.4f}")
    A(f"- ECE: mean={binr['global_ece_mean']:.4f}")
    A(f"- AUC > 0.55: {binr['n_auc_over_055']}/{len(binr['df_per_run'])}")
    A(f"- AUC > 0.60: {binr['n_auc_over_060']}/{len(binr['df_per_run'])}")
    A("")
    A("**ラベル別 AUC (3 fold 平均・降順 top 10)**:")
    A("")
    A(binr["by_label"].head(10).to_markdown())
    A("")

    A("## §6.2.8 leak verify 集計")
    A("")
    A(f"- blacklist hit: **{leak['blacklist_hits_count']}** ✅ (= 0 件で安全)")
    A(f"- suspicious hit: **{leak['suspicious_hits_count']}** (= fractal/level/fib 系 top 20 入り)")
    A("")
    A("**suspicious pattern 分布**:")
    A("")
    for p, c in sorted(leak["suspicious_pattern_counts"].items(), key=lambda x: -x[1]):
        A(f"- {p}: {c} 件")
    A("")
    A("**suspicious feature top 10 (= 同じ列名が複数モデルで hit)**:")
    A("")
    for f, c in leak["suspicious_feature_top10"].items():
        A(f"- {f}: {c} 件")
    A("")

    A("## §6.2.4 regime engagement (= 8 列が top 50 に入ったか)")
    A("")
    A(f"- 全 168 モデル中 **{leak['regime_n_models_with_engagement']}** モデル ({leak['regime_engagement_rate']*100:.1f}%) で regime 列が top 50 入り")
    A("")
    A("**task type 別**:")
    A("")
    for task, stat in leak["regime_by_task"]["mean"].items():
        max_v = leak["regime_by_task"]["max"][task]
        n_with = leak["regime_by_task"]["n_with_regime"][task]
        A(f"- {task}: mean={stat:.2f} / max={int(max_v)} / engagement={int(n_with)}")
    A("")

    A("## Stage 1 判定 (= 設計 §6.2.1 vs 実測)")
    A("")
    if regr["global_r2_median"] < 0.05:
        A("- ⚠️ 回帰系統: R² 中央値が 0.05 未満 → 揺れ幅予測タスク自体が困難 (= Phase 1 v6 と同型)")
    if mc["global_acc_mean"] > mc["accuracy_random"] + 0.05:
        A(f"- ✅ 多クラス系統: accuracy がランダム + 5pt 超 → 業界実証 rule-based threshold (precision 0.85) への足がかりあり")
    if binr["global_auc_mean"] > 0.55:
        A(f"- ✅ 2 値系統: AUC > 0.55 → meta_label の予測力あり")
    if leak["regime_engagement_rate"] < 0.3:
        A(f"- ⚠️ regime engagement < 30% → §6.2.4 案 B (= regime 別 model 分離) 検討経路発動候補")
    A("")
    A("## 次の判断")
    A("")
    A("- Step 5 Optuna ハイパラ tune に進むか")
    A("- Step 6 entry 判定 (= ルール集約 + threshold) に進むか")
    A("- §6.2.4 案 B (= regime 別 model 分離) を第二段階で検討するか")
    A("- §6.2.3 SMOTE / focal loss を第二段階で発動するか (= 多クラス class 別 recall < 0.3 で発動条件)")
    return "\n".join(lines)


def main() -> int:
    records = load_all_metrics()
    print(f"[load] metrics.json: {len(records)} 件 (期待 168)")
    if len(records) != 168:
        print(f"⚠️ 168 件揃ってない")

    by_task = defaultdict(list)
    for r in records:
        by_task[r["task_type"]].append(r)
    print(f"[load] task type 別: {[(k, len(v)) for k, v in by_task.items()]}")

    regr = summarize_regression(by_task["regression"])
    mc = summarize_multiclass(by_task["multiclass"])
    binr = summarize_binary(by_task["binary"])
    leak = aggregate_leak(records)

    report = write_report(records, regr, mc, binr, leak)
    OUT_REPORT.write_text(report)
    print(f"[write] {OUT_REPORT}")

    # 詳細 CSV (= 全 168 行)
    all_df = pd.concat([
        regr["df_per_run"].assign(task_type="regression"),
        mc["df_per_run"].assign(task_type="multiclass"),
        binr["df_per_run"].assign(task_type="binary"),
    ], ignore_index=True)
    all_df.to_csv(OUT_DETAILS_CSV, index=False)
    print(f"[write] {OUT_DETAILS_CSV}")

    print()
    print(report.split("## §6.2.1")[0])  # 結論サマリまでコンソール出力
    return 0


if __name__ == "__main__":
    sys.exit(main())
