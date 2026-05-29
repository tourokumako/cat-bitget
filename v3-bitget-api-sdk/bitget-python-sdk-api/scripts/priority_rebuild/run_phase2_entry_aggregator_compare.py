"""run_phase2_entry_aggregator_compare.py — Step 6 改善版: 案 A vs 案 B 比較

目的:
  - 仕様書 §6.2.7 第一段階 (z-score) の scale mismatch 問題を 2 variant で検証
  - 案 A: MFE [0,1] clip + 重み 0.4/0.3/0.3 (= 仕様書 §6.2.7 第二段階前倒し)
  - 案 B: MFE [0,1] clip + 重み 0.5/0.1/0.4 (= MFE 重み下げ・TP_prob 主導)

背景:
  - baseline で MFE 予測 R² 中央値 = -0.044 (= ランダム以下)
  - 業界実証 (= CDAR Berkeley / arxiv VAE) で MFE 直接予測は path-dependent + heavy-tail で困難
  - original 集約 (= z-score) で MFE_normalized が集約スコアの 97% を支配 → SHORT 偏り
  - 案 A: [0,1] clip で scale 整合 (= 業界 standard min-max scaling)
  - 案 B: 業界実証「MFE 困難」前提で重み下げ・TP_prob (= 業界主流 Triple Barrier) 主導

入力:
  - results/priority_rebuild/ml_phase2_baseline/{label}_fold{i}/predictions.parquet (= 168 個)
  - results/priority_rebuild/labels_mfe_mae_pct_train_2021_2024.parquet (= MFE p95 算出)

出力 (= 各 variant 別):
  - results/priority_rebuild/ml_phase2_entry_A/entry_signals_fold{i}.parquet
  - results/priority_rebuild/ml_phase2_entry_A/stage2_review.md
  - results/priority_rebuild/ml_phase2_entry_B/同上
  - results/priority_rebuild/ml_phase2_entry_compare/comparison_summary.md
"""

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]

BASELINE_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase2_baseline"
PARQUET_TRAIN = REPO_ROOT / "results" / "priority_rebuild" / "labels_mfe_mae_pct_train_2021_2024.parquet"
OUT_ROOT = REPO_ROOT / "results" / "priority_rebuild"

K_BARS = [6, 12, 24, 48, 96, 144, 288]
N_FOLDS = 3
THRESHOLD = 0.6
SL_REJECT_THRESHOLD = 0.9
K_WEIGHT = 1.0 / len(K_BARS)

CLASS_SL = 0
CLASS_TIME = 1
CLASS_TP = 2

# Variant 設定 (= 案 A / B / C / D / E)
TARGET_MONTHLY_ENTRIES = 275  # 仕様書 §2 月次 NET 目標逆算
TOTAL_MONTHS = 27  # 3 fold × 9 ヶ月

VARIANTS = {
    "A": {
        "weight_tp_prob": 0.4,
        "weight_mfe": 0.3,
        "weight_meta_yes": 0.3,
        "mfe_normalization": "minmax_p95_clip",
        "threshold": 0.6,
        "description": "案 A: MFE [0,1] clip + 重み 0.4/0.3/0.3 + threshold 0.6 (= 仕様書 §6.2.7 第二段階前倒し)",
    },
    "B": {
        "weight_tp_prob": 0.5,
        "weight_mfe": 0.1,
        "weight_meta_yes": 0.4,
        "mfe_normalization": "minmax_p95_clip",
        "threshold": 0.6,
        "description": "案 B: MFE [0,1] clip + 重み 0.5/0.1/0.4 + threshold 0.6 (= MFE 重み下げ・TP_prob 主導)",
    },
    "C": {
        "weight_tp_prob": 0.4,
        "weight_mfe": 0.3,
        "weight_meta_yes": 0.3,
        "mfe_normalization": "minmax_p95_clip",
        "threshold": 0.4,
        "description": "案 C: 案 A + threshold 0.4 (= 仕様書 §6.2.7 論点 4・月 275 件未達なら下げる)",
    },
    "D": {
        "weight_tp_prob": 0.5,
        "weight_mfe": 0.1,
        "weight_meta_yes": 0.4,
        "mfe_normalization": "minmax_p95_clip",
        "threshold": 0.4,
        "description": "案 D: 案 B + threshold 0.4 (= MFE 重み下げ + threshold 下げ)",
    },
    "E": {
        "weight_tp_prob": 0.4,
        "weight_mfe": 0.3,
        "weight_meta_yes": 0.3,
        "mfe_normalization": "minmax_p95_clip",
        "threshold": "data_driven",  # 月 275 件確保する quantile から自動算出
        "description": "案 E: 案 A + threshold data-driven (= 月 275 件確保する閾値を自動算出)",
    },
}


def load_predictions(label_name: str, fold_idx: int) -> pd.DataFrame:
    path = BASELINE_DIR / f"{label_name}_fold{fold_idx}" / "predictions.parquet"
    if not path.exists():
        raise FileNotFoundError(f"predictions.parquet missing: {path}")
    return pd.read_parquet(path)


def compute_mfe_stats() -> dict:
    """train_2021_2024 から MFE_pct の p95 + mean/std 算出 (= variant 別に切替可能)."""
    print(f"[stats] loading {PARQUET_TRAIN.name} for MFE normalization stats")
    cols = [f"{side}_MFE_pct_K{K}" for side in ["LONG", "SHORT"] for K in K_BARS]
    df = pd.read_parquet(PARQUET_TRAIN, columns=cols)
    stats = {}
    for col in cols:
        s = df[col].dropna()
        stats[col] = {
            "p95": float(s.quantile(0.95)),
            "mean": float(s.mean()),
            "std": float(s.std()),
        }
    print(f"[stats] computed for {len(cols)} cols")
    return stats


def normalize_mfe(pred_values: np.ndarray, col: str, stats: dict, method: str) -> np.ndarray:
    """MFE 予測値を variant に応じて normalize."""
    s = stats[col]
    if method == "zscore":
        return (pred_values - s["mean"]) / s["std"]
    elif method == "minmax_p95_clip":
        # p95 で割って [0, 1] にクリップ (= 業界 standard min-max scaling)
        # MFE は >= 0 を期待 (= 揺れ幅は正値) だが、ML 予測は負値も出すので [0,1] clip で吸収
        if s["p95"] <= 0:
            return np.zeros_like(pred_values)
        return np.clip(pred_values / s["p95"], 0.0, 1.0)
    else:
        raise ValueError(f"unknown mfe normalization method: {method}")


def compute_data_driven_threshold(long_score: np.ndarray, short_score: np.ndarray,
                                   target_monthly: int = TARGET_MONTHLY_ENTRIES,
                                   total_months: int = TOTAL_MONTHS) -> float:
    """月 275 件確保する quantile から threshold を自動算出.

    各 trade で max(LONG_score, SHORT_score) を取り、上位 target_pct percentile を threshold とする.
    """
    max_score = np.maximum(long_score, short_score)
    n_trades = len(max_score)
    target_entries = target_monthly * total_months
    if target_entries >= n_trades:
        return float(np.min(max_score))
    target_pct = 1.0 - target_entries / n_trades  # 上位 N% の threshold
    return float(np.quantile(max_score, target_pct))


def aggregate_one_fold(fold_idx: int, mfe_stats: dict, variant: dict,
                       precomputed_scores: dict = None) -> pd.DataFrame:
    """1 fold 分の集約 (= variant 別)."""
    weight_tp = variant["weight_tp_prob"]
    weight_mfe = variant["weight_mfe"]
    weight_meta = variant["weight_meta_yes"]
    mfe_method = variant["mfe_normalization"]

    base_label = f"triple_barrier_label_LONG_K{K_BARS[0]}"
    base_df = load_predictions(base_label, fold_idx)
    entry_ids = base_df["entry_id"].tolist()
    n_trades = len(entry_ids)

    long_scores_per_K = {}
    short_scores_per_K = {}
    long_sl_prob_per_K = {}
    short_sl_prob_per_K = {}

    for K in K_BARS:
        tb_long = load_predictions(f"triple_barrier_label_LONG_K{K}", fold_idx)
        tb_short = load_predictions(f"triple_barrier_label_SHORT_K{K}", fold_idx)
        long_tp_prob = tb_long[f"pred_proba_class{CLASS_TP}_cal"].values
        short_tp_prob = tb_short[f"pred_proba_class{CLASS_TP}_cal"].values
        long_sl_prob = tb_long[f"pred_proba_class{CLASS_SL}_cal"].values
        short_sl_prob = tb_short[f"pred_proba_class{CLASS_SL}_cal"].values
        long_sl_prob_per_K[K] = long_sl_prob
        short_sl_prob_per_K[K] = short_sl_prob

        mfe_long = load_predictions(f"LONG_MFE_pct_K{K}", fold_idx)
        mfe_short = load_predictions(f"SHORT_MFE_pct_K{K}", fold_idx)
        long_mfe_norm = normalize_mfe(mfe_long["pred"].values, f"LONG_MFE_pct_K{K}", mfe_stats, mfe_method)
        short_mfe_norm = normalize_mfe(mfe_short["pred"].values, f"SHORT_MFE_pct_K{K}", mfe_stats, mfe_method)

        meta_long = load_predictions(f"meta_label_LONG_K{K}", fold_idx)
        meta_short = load_predictions(f"meta_label_SHORT_K{K}", fold_idx)
        long_meta_yes_prob = meta_long["pred_proba_cal"].values
        short_meta_yes_prob = meta_short["pred_proba_cal"].values

        long_scores_per_K[K] = (
            long_tp_prob * weight_tp
            + long_mfe_norm * weight_mfe
            + long_meta_yes_prob * weight_meta
        )
        short_scores_per_K[K] = (
            short_tp_prob * weight_tp
            + short_mfe_norm * weight_mfe
            + short_meta_yes_prob * weight_meta
        )

    long_score = np.mean([long_scores_per_K[K] for K in K_BARS], axis=0)
    short_score = np.mean([short_scores_per_K[K] for K in K_BARS], axis=0)
    long_sl_max = np.max([long_sl_prob_per_K[K] for K in K_BARS], axis=0)
    short_sl_max = np.max([short_sl_prob_per_K[K] for K in K_BARS], axis=0)
    long_reject = long_sl_max > SL_REJECT_THRESHOLD
    short_reject = short_sl_max > SL_REJECT_THRESHOLD

    # threshold 取得 (= 固定値 or data-driven)
    raw_threshold = variant["threshold"]
    if raw_threshold == "data_driven":
        # 全 fold 統合で threshold 算出するため precomputed を受け取る
        threshold_value = precomputed_scores.get("data_driven_threshold", THRESHOLD) if precomputed_scores else THRESHOLD
    else:
        threshold_value = float(raw_threshold)

    direction = np.full(n_trades, "NONE", dtype=object)
    long_mask = (long_score > short_score) & (long_score > threshold_value) & ~long_reject
    short_mask = (short_score > long_score) & (short_score > threshold_value) & ~short_reject
    direction[long_mask] = "LONG"
    direction[short_mask] = "SHORT"

    max_score = np.maximum(np.abs(long_score), np.abs(short_score))
    max_score_safe = np.where(max_score < 1e-9, 1.0, max_score)
    confidence = np.abs(long_score - short_score) / max_score_safe

    df_out = pd.DataFrame({
        "entry_id": entry_ids,
        "fold": fold_idx,
        "direction": direction,
        "LONG_score": long_score.astype(np.float32),
        "SHORT_score": short_score.astype(np.float32),
        "confidence": confidence.astype(np.float32),
        "LONG_sl_max": long_sl_max.astype(np.float32),
        "SHORT_sl_max": short_sl_max.astype(np.float32),
        "long_reject": long_reject,
        "short_reject": short_reject,
    })
    df_out["entry_ts"] = pd.to_datetime(df_out["entry_id"])
    df_out["month"] = df_out["entry_ts"].dt.to_period("M").astype(str)
    return df_out


def compute_exit_proxy(df_all: pd.DataFrame) -> dict:
    TP_PCT = 0.005
    SL_PCT = 0.02
    FEE = 0.00014 * 2
    POSITION_USD = 2400.0
    TP_PRECISION = 0.476

    n_entries = (df_all["direction"] != "NONE").sum()
    if n_entries == 0:
        return {"n_entries": 0, "monthly_net_proxy_mean": 0.0, "month_pass_1900": 0, "total_months": 0}

    tp_gain = POSITION_USD * TP_PCT - POSITION_USD * FEE
    sl_loss = POSITION_USD * SL_PCT + POSITION_USD * FEE
    net_per_trade = TP_PRECISION * tp_gain - (1 - TP_PRECISION) * sl_loss

    monthly_entries = df_all[df_all["direction"] != "NONE"].groupby("month").size()
    monthly_net = monthly_entries * net_per_trade

    return {
        "n_entries": int(n_entries),
        "n_entries_monthly_mean": float(monthly_entries.mean()),
        "n_entries_monthly_min": float(monthly_entries.min()),
        "n_entries_monthly_max": float(monthly_entries.max()),
        "net_per_trade": float(net_per_trade),
        "monthly_net_proxy_mean": float(monthly_net.mean()),
        "monthly_net_proxy_min": float(monthly_net.min()),
        "monthly_net_proxy_max": float(monthly_net.max()),
        "month_pass_1900": int((monthly_net >= 1900).sum()),
        "total_months": int(len(monthly_net)),
    }


def build_variant_review(variant_name: str, df_all: pd.DataFrame, exit_proxy: dict, variant: dict) -> str:
    lines = []
    A = lines.append
    direction_counts = df_all["direction"].value_counts().to_dict()
    long_n = direction_counts.get("LONG", 0)
    short_n = direction_counts.get("SHORT", 0)
    none_n = direction_counts.get("NONE", 0)
    total_n = len(df_all)
    long_short_ratio = f"{long_n}:{short_n}" if short_n > 0 else f"{long_n}:0"

    A(f"# Step 6 Entry 判定 — Variant {variant_name} review")
    A("")
    A(f"集約完了: 3 fold 合計 {total_n:,} bar / {pd.Timestamp.now()}")
    A("")
    A(f"## 設定")
    A("")
    A(f"- {variant['description']}")
    A(f"- 重み: TP_prob={variant['weight_tp_prob']} / MFE={variant['weight_mfe']} / meta_yes={variant['weight_meta_yes']}")
    A(f"- MFE 正規化: {variant['mfe_normalization']}")
    A(f"- threshold: {THRESHOLD} / SL_reject: > {SL_REJECT_THRESHOLD}")
    A("")
    A("## 結論")
    A("")
    A(f"- entry 発動: **{long_n + short_n:,}** ({(long_n + short_n)/total_n*100:.2f}%) = LONG {long_n:,} + SHORT {short_n:,}")
    A(f"- LONG:SHORT 比: **{long_short_ratio}**")
    A(f"- 見送り NONE: {none_n:,} ({none_n/total_n*100:.2f}%)")
    A(f"- 月別件数: mean={exit_proxy.get('n_entries_monthly_mean', 0):.1f} / min={exit_proxy.get('n_entries_monthly_min', 0):.0f} / max={exit_proxy.get('n_entries_monthly_max', 0):.0f}")
    A(f"- Exit 抜き月次 NET proxy 平均: ${exit_proxy.get('monthly_net_proxy_mean', 0):.0f} (= 合格月 {exit_proxy.get('month_pass_1900', 0)}/{exit_proxy.get('total_months', 0)})")
    A("")
    A("## direction 分布 (= fold 別)")
    A("")
    by_fold = df_all.groupby("fold")["direction"].value_counts().unstack(fill_value=0)
    A(by_fold.to_markdown())
    A("")
    A("## score 分布")
    A("")
    A(f"- LONG_score: mean={df_all['LONG_score'].mean():.4f} / median={df_all['LONG_score'].median():.4f} / max={df_all['LONG_score'].max():.4f}")
    A(f"- SHORT_score: mean={df_all['SHORT_score'].mean():.4f} / median={df_all['SHORT_score'].median():.4f} / max={df_all['SHORT_score'].max():.4f}")
    A(f"- LONG_score > {THRESHOLD}: {(df_all['LONG_score'] > THRESHOLD).sum():,}")
    A(f"- SHORT_score > {THRESHOLD}: {(df_all['SHORT_score'] > THRESHOLD).sum():,}")
    return "\n".join(lines)


def build_comparison_summary(results: dict) -> str:
    lines = []
    A = lines.append
    A("# Step 6 集約 — A vs B + original 比較")
    A("")
    A(f"生成日時: {pd.Timestamp.now()}")
    A("")
    A("## 設計")
    A("")
    A("- **original** (= 既存 ml_phase2_entry/): MFE z-score + 重み 0.4/0.3/0.3 → scale mismatch 問題発覚")
    A("- **A**: MFE [0,1] clip (p95 base) + 重み 0.4/0.3/0.3 (= 仕様書 §6.2.7 第二段階前倒し・業界 standard min-max scaling)")
    A("- **B**: MFE [0,1] clip (p95 base) + 重み 0.5/0.1/0.4 (= 業界実証「MFE 困難」前提で重み下げ・TP_prob 主導)")
    A("")
    A("## 主要指標比較")
    A("")
    headers = "| variant | entry 件数 | LONG:SHORT | 月別 mean | 月別 max | NET proxy 平均 | 合格月 |"
    sep = "|---|---|---|---|---|---|---|"
    A(headers)
    A(sep)
    for v_name, data in results.items():
        if data is None:
            continue
        d = data["direction_counts"]
        long_n = d.get("LONG", 0)
        short_n = d.get("SHORT", 0)
        e = data["exit_proxy"]
        line = (
            f"| **{v_name}** | {long_n + short_n:,} "
            f"| {long_n}:{short_n} "
            f"| {e.get('n_entries_monthly_mean', 0):.0f} "
            f"| {e.get('n_entries_monthly_max', 0):.0f} "
            f"| ${e.get('monthly_net_proxy_mean', 0):.0f} "
            f"| {e.get('month_pass_1900', 0)}/{e.get('total_months', 0)} |"
        )
        A(line)
    A("")
    A("## score 分布比較")
    A("")
    A("| variant | LONG_score mean | SHORT_score mean | LONG_score max | SHORT_score max |")
    A("|---|---|---|---|---|")
    for v_name, data in results.items():
        if data is None:
            continue
        s = data["score_stats"]
        A(f"| **{v_name}** | {s['long_mean']:.4f} | {s['short_mean']:.4f} | {s['long_max']:.4f} | {s['short_max']:.4f} |")
    A("")
    A("## 判定")
    A("")
    A("**目標 (= §6.2.7 / §2)**:")
    A("- 月別 entry 件数 ≥ 275 件 (= 仕様書 §2 月次 NET 目標逆算)")
    A("- LONG:SHORT 偏り < 1:5 (= regime 偏り抑制目安)")
    A("- Exit 抜き NET proxy 合格月数最大化")
    A("")
    return "\n".join(lines)


def main() -> int:
    t_start = time.time()
    print(f"[start] aggregator compare ({pd.Timestamp.now()})")

    mfe_stats = compute_mfe_stats()
    results = {}

    for v_name, variant in VARIANTS.items():
        print(f"\n[variant {v_name}] {variant['description']}")
        out_dir = OUT_ROOT / f"ml_phase2_entry_{v_name}"
        out_dir.mkdir(parents=True, exist_ok=True)
        precomputed = None

        # variant E (= data-driven threshold) は 2-pass 実行
        if variant["threshold"] == "data_driven":
            print(f"  pass 1: score 算出 (= threshold 算出用)")
            all_scores = {"LONG_score": [], "SHORT_score": []}
            for fold_idx in range(N_FOLDS):
                df_tmp = aggregate_one_fold(fold_idx, mfe_stats, variant, precomputed_scores=None)
                all_scores["LONG_score"].append(df_tmp["LONG_score"].values)
                all_scores["SHORT_score"].append(df_tmp["SHORT_score"].values)
            long_all = np.concatenate(all_scores["LONG_score"])
            short_all = np.concatenate(all_scores["SHORT_score"])
            dd_threshold = compute_data_driven_threshold(long_all, short_all)
            print(f"  data-driven threshold: {dd_threshold:.4f} (= 月 {TARGET_MONTHLY_ENTRIES} 件確保ライン)")
            precomputed = {"data_driven_threshold": dd_threshold}

        all_folds = []
        for fold_idx in range(N_FOLDS):
            df_fold = aggregate_one_fold(fold_idx, mfe_stats, variant, precomputed_scores=precomputed)
            df_fold.to_parquet(out_dir / f"entry_signals_fold{fold_idx}.parquet", compression="snappy")
            dc = df_fold["direction"].value_counts().to_dict()
            print(f"  fold {fold_idx}: LONG={dc.get('LONG', 0):,} SHORT={dc.get('SHORT', 0):,} NONE={dc.get('NONE', 0):,}")
            all_folds.append(df_fold)
        df_all = pd.concat(all_folds, ignore_index=True)
        df_all.to_parquet(out_dir / "entry_signals_all_folds.parquet", compression="snappy")
        exit_proxy = compute_exit_proxy(df_all)
        review = build_variant_review(v_name, df_all, exit_proxy, variant)
        (out_dir / "stage2_review.md").write_text(review)

        results[v_name] = {
            "direction_counts": df_all["direction"].value_counts().to_dict(),
            "exit_proxy": exit_proxy,
            "score_stats": {
                "long_mean": float(df_all["LONG_score"].mean()),
                "long_max": float(df_all["LONG_score"].max()),
                "short_mean": float(df_all["SHORT_score"].mean()),
                "short_max": float(df_all["SHORT_score"].max()),
            },
        }
        print(f"  saved: {out_dir}/stage2_review.md")
        print(f"  entry total: {df_all['direction'].isin(['LONG', 'SHORT']).sum():,} "
              f"NET proxy mean: ${exit_proxy.get('monthly_net_proxy_mean', 0):.0f}")

    # 既存 original も比較に含める (= ml_phase2_entry/summary.json から load)
    original_summary_path = OUT_ROOT / "ml_phase2_entry" / "summary.json"
    if original_summary_path.exists():
        orig = json.loads(original_summary_path.read_text())
        # original の score_stats は summary.json に保存していないので近似
        orig_signals = pd.read_parquet(OUT_ROOT / "ml_phase2_entry" / "entry_signals_all_folds.parquet")
        results["original"] = {
            "direction_counts": orig["direction_counts"],
            "exit_proxy": orig["exit_proxy"],
            "score_stats": {
                "long_mean": float(orig_signals["LONG_score"].mean()),
                "long_max": float(orig_signals["LONG_score"].max()),
                "short_mean": float(orig_signals["SHORT_score"].mean()),
                "short_max": float(orig_signals["SHORT_score"].max()),
            },
        }

    # 比較 summary
    cmp_dir = OUT_ROOT / "ml_phase2_entry_compare"
    cmp_dir.mkdir(parents=True, exist_ok=True)
    comparison = build_comparison_summary(results)
    (cmp_dir / "comparison_summary.md").write_text(comparison)
    (cmp_dir / "comparison_data.json").write_text(json.dumps(results, indent=2, default=str))
    print(f"\n[done] elapsed: {time.time() - t_start:.1f}s")
    print(f"[done] comparison: {cmp_dir / 'comparison_summary.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
