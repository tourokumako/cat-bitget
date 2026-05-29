"""run_phase2_entry_aggregator.py — Step 6: §6.2.7 ルール集約 + threshold + 即死 reject

目的:
  - baseline 出力 168 個の predictions.parquet を集約して entry シグナル parquet を生成
  - §6.2.7 設計通りのルール集約式:
    LONG_score_K  = LONG_TP_prob_cal_K × 0.4 + LONG_MFE_pct_normalized_K × 0.3 + LONG_meta_yes_prob_cal_K × 0.3
    SHORT_score_K = 同様の SHORT 版
    LONG_score    = mean(LONG_score_K for K in [6, 12, 24, 48, 96, 144, 288])  (等重み 1/7)
    SHORT_score   = mean(SHORT_score_K for K in ...)
  - direction 排他確定 (LONG / SHORT / NONE)
  - threshold 暫定 0.6
  - 即死 reject: max(LONG_SL_prob_cal_K) > 0.9 → LONG → NONE 強制 (SHORT も同様)
  - Stage 2 review: 月次 entry 件数 + direction 分布 + confidence 分布 + Exit 抜き PnL proxy

入力:
  - results/priority_rebuild/ml_phase2_baseline/{label}_fold{i}/predictions.parquet (= 168 個)
  - results/priority_rebuild/labels_mfe_mae_pct_train_2021_2024.parquet (= MFE_pct 標準化用統計算出)

出力:
  - results/priority_rebuild/ml_phase2_entry/entry_signals_fold{i}.parquet (= fold 別・3 個)
  - results/priority_rebuild/ml_phase2_entry/entry_signals_all_folds.parquet (= 統合)
  - results/priority_rebuild/ml_phase2_entry/stage2_review.md
  - results/priority_rebuild/ml_phase2_entry/aggregator_run.log

集約パラメータ (= §6.2.7 設計値):
  - 重み TP_prob 0.4 / MFE_normalized 0.3 / meta_yes 0.3
  - threshold 0.6
  - 即死 reject SL_prob > 0.9
  - K = [6, 12, 24, 48, 96, 144, 288] (= 等重み 1/7)
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
OUT_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase2_entry"

# §6.2.7 設計値
K_BARS = [6, 12, 24, 48, 96, 144, 288]
N_FOLDS = 3
WEIGHT_TP_PROB = 0.4
WEIGHT_MFE_NORM = 0.3
WEIGHT_META_YES = 0.3
THRESHOLD = 0.6
SL_REJECT_THRESHOLD = 0.9
K_WEIGHT = 1.0 / len(K_BARS)  # 等重み 1/7

# Triple Barrier class encoding (= build_labels_pct.py L106-109 整合)
# 学習時 encoding: -1 (SL) / 0 (TIME) / 1 (TP) → encode_tb_label で 0/1/2
# class 0 = SL prob / class 1 = TIME prob / class 2 = TP prob
CLASS_SL = 0
CLASS_TIME = 1
CLASS_TP = 2


def load_predictions(label_name: str, fold_idx: int) -> pd.DataFrame:
    """1 fold/label の predictions.parquet を load."""
    path = BASELINE_DIR / f"{label_name}_fold{fold_idx}" / "predictions.parquet"
    if not path.exists():
        raise FileNotFoundError(f"predictions.parquet missing: {path}")
    return pd.read_parquet(path)


def compute_mfe_normalization_stats() -> dict:
    """train_2021_2024 parquet から MFE_pct 標準化用統計値 (mean/std) を fold 共通で算出.

    §6.2.7 設計では fold 別 mean/std で標準化と書かれているが、第一段階は train 全体で代用
    (= 「実装後 fold 別へ refine」の data-driven 経路).
    """
    print(f"[stats] loading {PARQUET_TRAIN.name} for MFE normalization stats")
    df = pd.read_parquet(PARQUET_TRAIN, columns=[
        f"{side}_MFE_pct_K{K}" for side in ["LONG", "SHORT"] for K in K_BARS
    ])
    stats = {}
    for side in ["LONG", "SHORT"]:
        for K in K_BARS:
            col = f"{side}_MFE_pct_K{K}"
            stats[col] = {
                "mean": float(df[col].mean()),
                "std": float(df[col].std()),
            }
    return stats


def aggregate_one_fold(fold_idx: int, mfe_stats: dict) -> pd.DataFrame:
    """1 fold 分の集約 → entry signal DataFrame."""
    print(f"\n[fold {fold_idx}] aggregating predictions for 56 labels")

    # base: TripleBarrier LONG_K6 を基準に entry_id 取得 (= test fold の全 trade)
    base_label = f"triple_barrier_label_LONG_K{K_BARS[0]}"
    base_df = load_predictions(base_label, fold_idx)
    entry_ids = base_df["entry_id"].tolist()
    n_trades = len(entry_ids)
    print(f"[fold {fold_idx}] base trades: {n_trades:,}")

    # K horizon 別に LONG_score_K / SHORT_score_K を計算
    long_scores_per_K = {}
    short_scores_per_K = {}
    long_sl_prob_per_K = {}
    short_sl_prob_per_K = {}

    for K in K_BARS:
        # multiclass: triple_barrier_label_LONG_K{K} / SHORT
        tb_long = load_predictions(f"triple_barrier_label_LONG_K{K}", fold_idx)
        tb_short = load_predictions(f"triple_barrier_label_SHORT_K{K}", fold_idx)
        assert tb_long["entry_id"].tolist() == entry_ids, f"entry_id mismatch: triple_barrier_label_LONG_K{K}"
        assert tb_short["entry_id"].tolist() == entry_ids, f"entry_id mismatch: triple_barrier_label_SHORT_K{K}"

        long_tp_prob = tb_long[f"pred_proba_class{CLASS_TP}_cal"].values
        short_tp_prob = tb_short[f"pred_proba_class{CLASS_TP}_cal"].values
        long_sl_prob = tb_long[f"pred_proba_class{CLASS_SL}_cal"].values
        short_sl_prob = tb_short[f"pred_proba_class{CLASS_SL}_cal"].values
        long_sl_prob_per_K[K] = long_sl_prob
        short_sl_prob_per_K[K] = short_sl_prob

        # regression: LONG_MFE_pct_K{K} → z-score 標準化
        mfe_long = load_predictions(f"LONG_MFE_pct_K{K}", fold_idx)
        mfe_short = load_predictions(f"SHORT_MFE_pct_K{K}", fold_idx)
        assert mfe_long["entry_id"].tolist() == entry_ids
        assert mfe_short["entry_id"].tolist() == entry_ids

        long_mfe_stats = mfe_stats[f"LONG_MFE_pct_K{K}"]
        short_mfe_stats = mfe_stats[f"SHORT_MFE_pct_K{K}"]
        long_mfe_norm = (mfe_long["pred"].values - long_mfe_stats["mean"]) / long_mfe_stats["std"]
        short_mfe_norm = (mfe_short["pred"].values - short_mfe_stats["mean"]) / short_mfe_stats["std"]

        # binary: meta_label_LONG_K{K} / SHORT → キャリブレーション後 positive class prob
        meta_long = load_predictions(f"meta_label_LONG_K{K}", fold_idx)
        meta_short = load_predictions(f"meta_label_SHORT_K{K}", fold_idx)
        assert meta_long["entry_id"].tolist() == entry_ids
        assert meta_short["entry_id"].tolist() == entry_ids

        long_meta_yes_prob = meta_long["pred_proba_cal"].values
        short_meta_yes_prob = meta_short["pred_proba_cal"].values

        # 集約式 (= §6.2.7)
        long_scores_per_K[K] = (
            long_tp_prob * WEIGHT_TP_PROB
            + long_mfe_norm * WEIGHT_MFE_NORM
            + long_meta_yes_prob * WEIGHT_META_YES
        )
        short_scores_per_K[K] = (
            short_tp_prob * WEIGHT_TP_PROB
            + short_mfe_norm * WEIGHT_MFE_NORM
            + short_meta_yes_prob * WEIGHT_META_YES
        )

    # 等重み 1/7 で K 平均化
    long_score = np.mean([long_scores_per_K[K] for K in K_BARS], axis=0)
    short_score = np.mean([short_scores_per_K[K] for K in K_BARS], axis=0)

    # 即死 reject: 各 K で max SL prob > 0.9 なら reject
    long_sl_max = np.max([long_sl_prob_per_K[K] for K in K_BARS], axis=0)
    short_sl_max = np.max([short_sl_prob_per_K[K] for K in K_BARS], axis=0)
    long_reject = long_sl_max > SL_REJECT_THRESHOLD
    short_reject = short_sl_max > SL_REJECT_THRESHOLD

    # direction 排他確定
    direction = np.full(n_trades, "NONE", dtype=object)
    long_mask = (long_score > short_score) & (long_score > THRESHOLD) & ~long_reject
    short_mask = (short_score > long_score) & (short_score > THRESHOLD) & ~short_reject
    direction[long_mask] = "LONG"
    direction[short_mask] = "SHORT"

    # confidence (= |LONG - SHORT| / max(LONG, SHORT))
    max_score = np.maximum(np.abs(long_score), np.abs(short_score))
    max_score_safe = np.where(max_score < 1e-9, 1.0, max_score)
    confidence = np.abs(long_score - short_score) / max_score_safe

    # reject reason
    reject_reason = np.full(n_trades, "", dtype=object)
    reject_reason[long_mask & long_reject] = "long_sl_prob>0.9"
    reject_reason[short_mask & short_reject] = "short_sl_prob>0.9"
    # threshold 未達は reject_reason 空

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
        "reject_reason": reject_reason,
    })
    # 月別 entry_id → 月 column 追加
    df_out["entry_ts"] = pd.to_datetime(df_out["entry_id"])
    df_out["month"] = df_out["entry_ts"].dt.to_period("M").astype(str)

    print(f"[fold {fold_idx}] direction dist: "
          f"LONG={(direction == 'LONG').sum():,} "
          f"SHORT={(direction == 'SHORT').sum():,} "
          f"NONE={(direction == 'NONE').sum():,}")
    print(f"[fold {fold_idx}] reject発動: long={long_reject.sum():,} short={short_reject.sum():,}")
    return df_out


def compute_exit_proxy_pnl(df_all: pd.DataFrame) -> dict:
    """§6.2.1 Stage 2 (d) Exit 抜き PnL proxy 算出 (= 固定値前提・Exit 動的化前 sanity check).

    使用固定値 (= phase_compliance / exchange_spec 確定値):
      - TP_pct 0.5% = 旧 Priority v9 平均 TP (cat_v9 経験値・[[priority_v9_trade_logic_analysis]])
      - SL_pct 2% = 旧 Priority v9 平均 SL
      - fee 0.014% × 2 = 0.028% (= Maker 適用値・exchange_spec.md L7)
      - position 0.024 BTC × $100k = $2,400 (= 1 ポジ標準サイズ・cap=5 / sum ≤ 0.12 BTC)
      - TP Precision 推定 = baseline Stage 1 多クラス accuracy 47.6%
    """
    TP_PCT = 0.005
    SL_PCT = 0.02
    FEE = 0.00014 * 2
    POSITION_USD = 2400.0

    n_entries = (df_all["direction"] != "NONE").sum()
    if n_entries == 0:
        return {"n_entries": 0, "monthly_net_proxy": 0.0, "warning": "no entries"}

    # TP Precision = baseline Stage 1 multiclass accuracy 47.6%
    tp_precision = 0.476
    tp_gain_per_trade = POSITION_USD * TP_PCT - POSITION_USD * FEE
    sl_loss_per_trade = POSITION_USD * SL_PCT + POSITION_USD * FEE
    net_per_trade = tp_precision * tp_gain_per_trade - (1 - tp_precision) * sl_loss_per_trade

    # 月別件数 → 月別 NET proxy
    monthly_entries = df_all[df_all["direction"] != "NONE"].groupby("month").size()
    monthly_net = monthly_entries * net_per_trade

    return {
        "n_entries": int(n_entries),
        "n_entries_monthly_mean": float(monthly_entries.mean()),
        "n_entries_monthly_min": float(monthly_entries.min()),
        "n_entries_monthly_max": float(monthly_entries.max()),
        "tp_precision_assumed": tp_precision,
        "tp_gain_per_trade": float(tp_gain_per_trade),
        "sl_loss_per_trade": float(sl_loss_per_trade),
        "net_per_trade": float(net_per_trade),
        "monthly_net_proxy_mean": float(monthly_net.mean()),
        "monthly_net_proxy_min": float(monthly_net.min()),
        "monthly_net_proxy_max": float(monthly_net.max()),
        "month_pass_1900": int((monthly_net >= 1900).sum()),
        "total_months": int(len(monthly_net)),
        "monthly_breakdown": {str(m): {"entries": int(monthly_entries[m]), "net_proxy": float(monthly_net[m])} for m in monthly_entries.index},
    }


def build_stage2_review(df_all: pd.DataFrame, exit_proxy: dict, mfe_stats: dict) -> str:
    """Stage 2 review summary markdown."""
    lines = []
    A = lines.append

    direction_counts = df_all["direction"].value_counts().to_dict()
    long_n = direction_counts.get("LONG", 0)
    short_n = direction_counts.get("SHORT", 0)
    none_n = direction_counts.get("NONE", 0)
    total_n = len(df_all)
    long_pct = long_n / total_n * 100
    short_pct = short_n / total_n * 100
    none_pct = none_n / total_n * 100

    n_entries = long_n + short_n
    n_entries_pct = n_entries / total_n * 100

    A("# Step 6 Entry 判定 — Stage 2 review")
    A("")
    A(f"集約完了: 3 fold 合計 {total_n:,} bar / {pd.Timestamp.now()}")
    A("")
    A("## 結論 1 行サマリ")
    A("")
    A(f"- entry 発動: **{n_entries:,}** ({n_entries_pct:.2f}%) = LONG {long_n:,} ({long_pct:.2f}%) + SHORT {short_n:,} ({short_pct:.2f}%)")
    A(f"- 見送り: NONE {none_n:,} ({none_pct:.2f}%)")
    A(f"- 月別件数: mean={exit_proxy.get('n_entries_monthly_mean', 0):.1f} / min={exit_proxy.get('n_entries_monthly_min', 0):.0f} / max={exit_proxy.get('n_entries_monthly_max', 0):.0f} (= 目標 月 275 件)")
    A(f"- Exit 抜き PnL proxy: 月次 NET 平均 ${exit_proxy.get('monthly_net_proxy_mean', 0):.0f} (= 合格 $1,900 達成月 {exit_proxy.get('month_pass_1900', 0)}/{exit_proxy.get('total_months', 0)})")
    A("")

    A("## §6.2.7 集約パラメータ")
    A("")
    A(f"- 重み: TP_prob={WEIGHT_TP_PROB} / MFE_norm={WEIGHT_MFE_NORM} / meta_yes={WEIGHT_META_YES}")
    A(f"- K 重み: 等重み 1/{len(K_BARS)} ≈ {K_WEIGHT:.4f} (= 7 horizon 平均)")
    A(f"- threshold: {THRESHOLD}")
    A(f"- 即死 reject: SL_prob > {SL_REJECT_THRESHOLD} (= 各 K max)")
    A("")

    A("## direction 分布 (= fold 別)")
    A("")
    by_fold = df_all.groupby("fold")["direction"].value_counts().unstack(fill_value=0)
    A(by_fold.to_markdown())
    A("")

    A("## confidence 分布")
    A("")
    long_short = df_all[df_all["direction"] != "NONE"]
    if len(long_short):
        conf_stats = long_short["confidence"].describe().to_dict()
        A(f"- entry 発動 trade の confidence: mean={conf_stats['mean']:.3f} / median={conf_stats['50%']:.3f} / p25={conf_stats['25%']:.3f} / p75={conf_stats['75%']:.3f}")
    else:
        A("- entry なし")
    A("")

    A("## score 分布")
    A("")
    A(f"- LONG_score: mean={df_all['LONG_score'].mean():.4f} / median={df_all['LONG_score'].median():.4f} / max={df_all['LONG_score'].max():.4f}")
    A(f"- SHORT_score: mean={df_all['SHORT_score'].mean():.4f} / median={df_all['SHORT_score'].median():.4f} / max={df_all['SHORT_score'].max():.4f}")
    A(f"- LONG_score > {THRESHOLD}: {(df_all['LONG_score'] > THRESHOLD).sum():,} ({(df_all['LONG_score'] > THRESHOLD).sum()/total_n*100:.2f}%)")
    A(f"- SHORT_score > {THRESHOLD}: {(df_all['SHORT_score'] > THRESHOLD).sum():,} ({(df_all['SHORT_score'] > THRESHOLD).sum()/total_n*100:.2f}%)")
    A("")

    A("## 即死 reject 発動")
    A("")
    A(f"- LONG reject: {df_all['long_reject'].sum():,} ({df_all['long_reject'].sum()/total_n*100:.2f}%)")
    A(f"- SHORT reject: {df_all['short_reject'].sum():,} ({df_all['short_reject'].sum()/total_n*100:.2f}%)")
    reject_actual = (df_all["reject_reason"] != "").sum()
    A(f"- 実 reject (= threshold 通過後 SL_prob 弾き): {reject_actual:,}")
    A("")

    A("## Exit 抜き PnL proxy (= §6.2.1 Stage 2 (d))")
    A("")
    A(f"- 前提: TP 0.5% / SL 2% / fee 0.014%×2 / position $2,400 / TP Precision = baseline accuracy 47.6%")
    A(f"- 1 trade あたり期待 NET: ${exit_proxy.get('net_per_trade', 0):.2f}")
    A(f"- 月次 NET proxy 平均: ${exit_proxy.get('monthly_net_proxy_mean', 0):.0f}")
    A(f"- 月次 NET proxy min/max: ${exit_proxy.get('monthly_net_proxy_min', 0):.0f} / ${exit_proxy.get('monthly_net_proxy_max', 0):.0f}")
    A(f"- 合格 $1,900 達成月: {exit_proxy.get('month_pass_1900', 0)}/{exit_proxy.get('total_months', 0)}")
    A("")
    A("**注意**: TP_pct / SL_pct / TP Precision は固定値前提。[4] Exit 多層 ML で動的化される。")
    A("")

    A("## 月別 entry 件数 + 月次 NET proxy")
    A("")
    monthly_break = exit_proxy.get("monthly_breakdown", {})
    if monthly_break:
        lines2 = ["| 月 | entry 件数 | NET proxy ($) |", "|---|---|---|"]
        for m, v in sorted(monthly_break.items()):
            lines2.append(f"| {m} | {v['entries']:,} | {v['net_proxy']:.0f} |")
        A("\n".join(lines2))
    A("")

    A("## 設計判断 (= §6.2.7 第二段階 data-driven calibrate)")
    A("")
    if exit_proxy.get('n_entries_monthly_mean', 0) < 200:
        A(f"- ⚠️ 月別 entry 件数 < 200 → threshold 0.6 → 0.5 に下げる検討対象")
    elif exit_proxy.get('n_entries_monthly_mean', 0) > 400:
        A(f"- ⚠️ 月別 entry 件数 > 400 → threshold 0.6 → 0.7 に上げる検討対象")
    if exit_proxy.get('monthly_net_proxy_mean', 0) < 1900:
        gap = 1900 - exit_proxy.get('monthly_net_proxy_mean', 0)
        A(f"- ⚠️ Exit 抜き月次 NET proxy < $1,900 (= ${gap:.0f} 不足) → [4] Exit 多層 ML で挽回が必要")
    else:
        A(f"- ✅ Exit 抜き月次 NET proxy ≥ $1,900 達成 → [4] Exit 多層 ML で更に増額")
    A("")

    A("## 次の判断")
    A("")
    A("- ✅ Step 6 集約完成 → [2.5] cluster 実装 (= §6.3 詳細設計済) に進む")
    A("- もしくは集約重み 0.4/0.3/0.3 / threshold 0.6 / 即死 reject 0.9 を data-driven calibrate")
    A("- baseline Stage 1 の R²<0 (= 揺れ幅予測逃げ) の影響を集約スコアで観測")
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    t_start = time.time()
    print(f"[start] Step 6 entry aggregator ({pd.Timestamp.now()})")

    # 1. MFE 標準化用統計値算出
    mfe_stats = compute_mfe_normalization_stats()
    print(f"[stats] MFE/MAE pct stats computed for 14 columns (LONG/SHORT × 7K)")

    # 2. fold 別集約
    all_folds = []
    for fold_idx in range(N_FOLDS):
        df_fold = aggregate_one_fold(fold_idx, mfe_stats)
        fold_out = OUT_DIR / f"entry_signals_fold{fold_idx}.parquet"
        df_fold.to_parquet(fold_out, compression="snappy")
        print(f"[fold {fold_idx}] saved: {fold_out}")
        all_folds.append(df_fold)

    # 3. 統合
    df_all = pd.concat(all_folds, ignore_index=True)
    df_all.to_parquet(OUT_DIR / "entry_signals_all_folds.parquet", compression="snappy")
    print(f"[all] total trades: {len(df_all):,}")

    # 4. Exit 抜き PnL proxy
    exit_proxy = compute_exit_proxy_pnl(df_all)
    print(f"[proxy] monthly NET mean: ${exit_proxy.get('monthly_net_proxy_mean', 0):.0f}")

    # 5. Stage 2 review markdown
    review = build_stage2_review(df_all, exit_proxy, mfe_stats)
    review_path = OUT_DIR / "stage2_review.md"
    review_path.write_text(review)
    print(f"[done] {review_path}")

    # 6. summary.json (= 機械処理用)
    summary = {
        "params": {
            "weight_tp_prob": WEIGHT_TP_PROB,
            "weight_mfe_norm": WEIGHT_MFE_NORM,
            "weight_meta_yes": WEIGHT_META_YES,
            "threshold": THRESHOLD,
            "sl_reject_threshold": SL_REJECT_THRESHOLD,
            "K_bars": K_BARS,
            "k_weight": K_WEIGHT,
        },
        "total_trades": int(len(df_all)),
        "direction_counts": df_all["direction"].value_counts().to_dict(),
        "exit_proxy": exit_proxy,
        "elapsed_sec": time.time() - t_start,
    }
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(f"[done] elapsed: {time.time() - t_start:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
