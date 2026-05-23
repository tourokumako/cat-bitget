"""Step I-3.4: merge 3 並列 case_a_v2 + tp_hit_classifier summary + §4.1 v5.1 判定.

P1: K={12,24} × LONG/SHORT (4 組合せ)
P2: K=48 × LONG/SHORT (2 組合せ)
P3: K=96 × LONG/SHORT (2 組合せ・案 V で Secondary Filter に分離)

統合後 8 組合せ × 2 method (fixed_tp / time_exit) を読み込み、Primary 6 組合せ
(K=12, 24, 48 × LONG/SHORT) で §4.1 v5.1 判定 (cc_ml_design_spec §1.5.1 v5.1):
- TP Precision > 0.5 (time_exit method は不適用 → 自動 PASS)
- Simulated PnL: 12 ヶ月中 8+ ヶ月プラス + 年間 NET ≥ $500
- DSR > 1.0 (n_trials = 12 = 6 組合せ × 2 method・案 V で 16 → 12)
- entropy lift > 10% (案 a では NaN 自動 PASS 継承・M2 後送り問題は別タスク)

K=96 LONG/SHORT は別レンズ (Secondary Filter) で評価 (5m bot 運用要件と 8h 予測
ホライズン乖離・案 V 2026-05-26): raw 数値は `secondary_filter_evaluation` フィールドに
出力し CP6 監査の根拠定量化に使用する。

採用判定 (Primary 6 組合せ基準):
- method (fixed_tp) または (time_exit) のいずれかで 6 組合せ ALL PASS → Phase 2 進行
- 4-5 組合せ → Step G Major M2 + M3 統合 → 再 smoke (まこさん最終判断)
- 0-3 組合せ → 案 X (Layer 3) or 案 Z (案 b-f) (まこさんレビュー必須)

Usage:
    python scripts/priority_rebuild/merge_step_i_summaries.py
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from dsr import compute_dsr_from_returns  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
ML_PHASE1_V5 = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase1_v5"

DEFAULT_P1_CASE_A = ML_PHASE1_V5 / "_case_a_v2_p1"
DEFAULT_P2_CASE_A = ML_PHASE1_V5 / "_case_a_v2_p2"
DEFAULT_P3_CASE_A = ML_PHASE1_V5 / "_case_a_v2_p3"
DEFAULT_P1_TP = ML_PHASE1_V5 / "_tp_hit_classifier_p1"
DEFAULT_P2_TP = ML_PHASE1_V5 / "_tp_hit_classifier_p2"
DEFAULT_P3_TP = ML_PHASE1_V5 / "_tp_hit_classifier_p3"
DEFAULT_TIME_EXIT_INDEX = (
    ML_PHASE1_V5
    / "_phase4b_train_constants"
    / "time_exit_return_median_INDEX_train_2021_2024.json"
)
DEFAULT_OUT = ML_PHASE1_V5 / "_step_i_merged"

EXPECTED_COMBINATIONS = [
    "K12_LONG", "K12_SHORT",
    "K24_LONG", "K24_SHORT",
    "K48_LONG", "K48_SHORT",
    "K96_LONG", "K96_SHORT",
]

# 案 V (2026-05-26・Step I-4.4): K=96 は 5m bot 運用要件 (即時 Exit ループ) と
# 8h 予測ホライズン乖離で Primary 判定対象から除外・別レンズ (Secondary Filter) で評価
# 出力 JSON 互換のため `meets_6plus_criteria` / `meets_6plus_any_method` のキー名は維持し、
# 意味を「Primary 6 組合せ ALL PASS」に再定義する (下流 dataclass / WORKFLOW 文言互換)
K_PRIMARY_FILTER = [12, 24, 48]
K_SECONDARY = [96]
PRIMARY_COMBINATIONS = [f"K{k}_{side}" for k in K_PRIMARY_FILTER for side in ("LONG", "SHORT")]
SECONDARY_COMBINATIONS = [f"K{k}_{side}" for k in K_SECONDARY for side in ("LONG", "SHORT")]

# §4.1 v5.1 合格閾値 (cc_ml_design_spec §1.5.1 v5.1)
THRESHOLD_TP_PRECISION = 0.5
THRESHOLD_MONTHS_POSITIVE = 8
THRESHOLD_SIM_PNL_YEAR_USD = 500.0
THRESHOLD_DSR = 1.0
THRESHOLD_ENTROPY_LIFT = 0.10

# DSR n_trials (spec v2.1 §6.3・案 V で 16 → 12 = 6 組合せ × 2 method)
DSR_N_TRIALS = 12
DSR_SR_VARIANCE = 1.0  # cross-trial variance (default unit variance)

# Cost (compute_simulated_pnl_v2 default)
DEFAULT_COST_PER_TRADE = 0.00033


def load_case_a_summary(case_a_dir: Path, suffix: str) -> dict:
    fname = f"case_a_v2_summary_labels_mfe_mae_pct_{suffix}.json"
    path = case_a_dir / fname
    if not path.exists():
        print(f"[error] case_a summary not found: {path}", file=sys.stderr)
        sys.exit(2)
    with open(path) as f:
        return json.load(f)


def load_predictions(tp_dir: Path, suffix: str) -> pd.DataFrame:
    fname = f"tp_hit_classifier_predictions_{suffix}.parquet"
    path = tp_dir / fname
    if not path.exists():
        print(f"[error] predictions not found: {path}", file=sys.stderr)
        sys.exit(2)
    df = pd.read_parquet(path)
    df["trade_ts"] = pd.to_datetime(df["trade_ts"])
    return df


def load_time_exit_medians(index_path: Path) -> Dict[Tuple[int, str, int], float]:
    if not index_path.exists():
        print(f"[error] time_exit index not found: {index_path}", file=sys.stderr)
        sys.exit(2)
    with open(index_path) as f:
        idx_data = json.load(f)
    out: Dict[Tuple[int, str, int], float] = {}
    median_matrix = idx_data.get("median_pct_matrix", {})
    for key, median_pct in median_matrix.items():
        parts = key.split("_")
        K = int(parts[0][1:])
        side = parts[1]
        N = int(parts[2][1:])
        out[(K, side, N)] = float(median_pct)
    return out


def compute_tp_precision(
    predictions_df: pd.DataFrame, K: int, side: str, fold_idx: int, tp_pct: float
) -> float:
    """TP_PCT × Classifier 予測陽性のうち実際に TP hit した割合."""
    df = predictions_df[
        (predictions_df["K"] == K)
        & (predictions_df["side"] == side)
        & (predictions_df["fold_idx"] == fold_idx)
        & (predictions_df["TP_PCT"] == tp_pct)
    ]
    if df.empty or "tp_hit_true" not in df.columns:
        return float("nan")
    predicted_positive = df[df["tp_hit_prob"] > 0.5]
    if predicted_positive.empty:
        return 0.0
    return float((predicted_positive["tp_hit_true"] == 1).mean())


def reconstruct_returns_for_fold(
    fold_summary: dict,
    method: str,
    predictions_df: pd.DataFrame,
    time_exit_medians: Dict[Tuple[int, str, int], float],
    cost_per_trade: float = DEFAULT_COST_PER_TRADE,
) -> Optional[np.ndarray]:
    """1 fold × 1 method の test 期間 trade-level return 系列を再生成.

    method=fixed_tp: r = tp_hit_prob × TP_PCT/100 - (1 - tp_hit_prob) × SL_pct/100 - cost
    method=time_exit: r = median_pct/100 - cost (定数を n_test 回複製)
    """
    K = fold_summary["K"]
    side = fold_summary["side"]
    fold_idx = fold_summary["fold_idx"]

    if method == "fixed_tp":
        tp_pct = fold_summary.get("best_tp_pct")
        sl_pct = fold_summary.get("best_sl_pct")
        if tp_pct is None or sl_pct is None:
            return None
        df = predictions_df[
            (predictions_df["K"] == K)
            & (predictions_df["side"] == side)
            & (predictions_df["fold_idx"] == fold_idx)
            & (predictions_df["TP_PCT"] == tp_pct)
        ]
        if df.empty:
            return None
        p = df["tp_hit_prob"].to_numpy()
        returns = p * (tp_pct / 100.0) - (1 - p) * (sl_pct / 100.0) - cost_per_trade
        return returns
    elif method == "time_exit":
        # Critical-1 修正 (L-212c): 旧式 (定数 broadcast) は naive baseline で fold 内分散ゼロ
        # 新式 r[i] = p[i] × TP_PCT/100 + (1 - p[i]) × median_pct/100 - cost (予測装置化)
        # tp_hit_prob[i] が線形係数 (TP_PCT - median_pct)/100 で returns に伝播
        N = fold_summary.get("best_N")
        tp_pct = fold_summary.get("best_tp_pct")  # NEW: case_a_v2_v3 で記録された tp_pct
        if N is None or tp_pct is None:
            return None
        median_pct = time_exit_medians.get((K, side, N))
        if median_pct is None:
            return None
        df = predictions_df[
            (predictions_df["K"] == K)
            & (predictions_df["side"] == side)
            & (predictions_df["fold_idx"] == fold_idx)
            & (predictions_df["TP_PCT"] == tp_pct)
        ]
        if df.empty:
            return None
        p = df["tp_hit_prob"].to_numpy()
        returns = (
            p * (tp_pct / 100.0)
            + (1.0 - p) * (median_pct / 100.0)
            - cost_per_trade
        )
        return returns
    else:
        return None


def compute_fold_sharpe_dsr(
    returns: np.ndarray, n_trials: int = DSR_N_TRIALS
) -> Tuple[float, float]:
    """fold-level Sharpe (per-trade scale) + DSR z-score.

    Critical-1 修正後: 両 method (fixed_tp / time_exit) で returns 分散非ゼロが期待値。
    旧 time_exit 設計の定数 returns case (std=0) は L-212b ガード方向だが、安全側で NaN 返却を維持。
    """
    if returns is None or len(returns) < 2:
        return float("nan"), float("nan")
    finite_mask = np.isfinite(returns)
    arr = returns[finite_mask]
    if len(arr) < 2:
        return float("nan"), float("nan")
    mean = float(np.mean(arr))
    std = float(np.std(arr, ddof=1))
    # L-212b 整合: dsr.py 側ガード閾値 (std < 1e-12) と統一
    # 浮動小数点誤差 (2.18e-19 等) で std <= 0 ガードすり抜け → sharpe 異常値発生を防ぐ
    # (test_dsr_merge_interaction.py で発見・複数 script 相互作用 bug の根本対策)
    if std < 1e-12 or not np.isfinite(std):
        return float("nan"), float("nan")
    sharpe = mean / std
    try:
        dsr_result = compute_dsr_from_returns(
            returns=arr, n_trials=n_trials, sr_variance=DSR_SR_VARIANCE
        )
        dsr_z = float(dsr_result.dsr_zscore)
    except Exception as e:
        print(f"[warn] DSR computation failed: {e}", file=sys.stderr)
        dsr_z = float("nan")
    return float(sharpe), dsr_z


def evaluate_fold(
    fold_summary: dict,
    method: str,
    predictions_df: pd.DataFrame,
    time_exit_medians: Dict[Tuple[int, str, int], float],
) -> dict:
    """1 fold × 1 method で 4 指標計算 + PASS 判定."""
    # 1. tp_precision
    if method == "fixed_tp":
        tp_pct = fold_summary.get("best_tp_pct")
        if tp_pct is not None:
            tp_prec = compute_tp_precision(
                predictions_df,
                K=fold_summary["K"],
                side=fold_summary["side"],
                fold_idx=fold_summary["fold_idx"],
                tp_pct=tp_pct,
            )
        else:
            tp_prec = float("nan")
    else:
        tp_prec = float("nan")  # time_exit では不適用 → 自動 PASS

    # 2. sim_pnl
    test_sim_pnl_year = float(fold_summary.get("test_sim_pnl_year_usd", 0.0))
    months_pos = int(fold_summary.get("test_months_positive", 0))

    # 3. Sharpe + DSR
    returns = reconstruct_returns_for_fold(
        fold_summary=fold_summary,
        method=method,
        predictions_df=predictions_df,
        time_exit_medians=time_exit_medians,
    )
    fold_sharpe, dsr_z = compute_fold_sharpe_dsr(returns)

    # PASS 判定
    if method == "time_exit":
        tp_prec_pass = True  # 不適用 → 自動 PASS
    else:
        tp_prec_pass = (not np.isnan(tp_prec)) and (tp_prec >= THRESHOLD_TP_PRECISION)
    sim_pnl_pass = (months_pos >= THRESHOLD_MONTHS_POSITIVE) and (
        test_sim_pnl_year >= THRESHOLD_SIM_PNL_YEAR_USD
    )
    # L-212b / Critical-2: DSR 適用不可 (nan) のとき月次黒字率で代替判定
    # (Sortino は定数 returns で意味なし・月次黒字率を採用)
    # 閾値は sim_pnl_pass と同じ THRESHOLD_MONTHS_POSITIVE = 8 月 (12 ヶ月中)
    # = 「予測装置として機能不能だが、月次健全性で代替評価」(暫定 PASS・Phase 4-b で再評価必須)
    # auto-PASS 禁止 (L-212b 原文・Neyman-Pearson 整合): nan で無条件 PASS は出さない
    if np.isnan(dsr_z):
        dsr_pass = months_pos >= THRESHOLD_MONTHS_POSITIVE
        dsr_judgment_method = "alt_months_positive"
    else:
        dsr_pass = dsr_z >= THRESHOLD_DSR
        dsr_judgment_method = "dsr_zscore"
    entropy_pass = True  # 案 a NaN 自動 PASS 継承

    all_pass = bool(tp_prec_pass and sim_pnl_pass and dsr_pass and entropy_pass)

    return {
        "fold_idx": fold_summary.get("fold_idx"),
        "tp_precision": (None if np.isnan(tp_prec) else float(tp_prec)),
        "tp_precision_pass": bool(tp_prec_pass),
        "test_sim_pnl_year_usd": test_sim_pnl_year,
        "test_months_positive": months_pos,
        "sim_pnl_pass": bool(sim_pnl_pass),
        "fold_sharpe": (None if np.isnan(fold_sharpe) else float(fold_sharpe)),
        "dsr_zscore": (None if np.isnan(dsr_z) else float(dsr_z)),
        "dsr_pass": bool(dsr_pass),
        "dsr_judgment_method": dsr_judgment_method,  # L-212b: "dsr_zscore" or "alt_months_positive"
        "entropy_lift": None,
        "entropy_pass_auto": True,
        "all_pass": all_pass,
    }


def evaluate_combination(
    combo_key: str,
    methods_data: dict,
    predictions_df: pd.DataFrame,
    time_exit_medians: Dict[Tuple[int, str, int], float],
) -> dict:
    out: dict = {}
    for method in ("fixed_tp", "time_exit"):
        folds = methods_data.get(method, [])
        fold_results: List[dict] = []
        for f in folds:
            fold_results.append(
                evaluate_fold(
                    fold_summary=f,
                    method=method,
                    predictions_df=predictions_df,
                    time_exit_medians=time_exit_medians,
                )
            )
        n_fold = len(fold_results)
        n_pass = sum(1 for r in fold_results if r["all_pass"])
        combo_all_pass = (n_fold >= 5) and (n_pass == n_fold)
        out[method] = {
            "n_folds": n_fold,
            "n_folds_all_pass": n_pass,
            "combo_all_pass": combo_all_pass,
            "folds": fold_results,
        }
    return out


def merge_and_evaluate(
    p1_ca: dict,
    p2_ca: dict,
    p3_ca: dict,
    predictions_df: pd.DataFrame,
    time_exit_medians: Dict[Tuple[int, str, int], float],
) -> dict:
    merged: Dict[str, dict] = {}
    anomaly: Dict[str, dict] = {}

    for label, src in [("p1", p1_ca), ("p2", p2_ca), ("p3", p3_ca)]:
        for combo_key, methods_data in src.get("combinations", {}).items():
            if combo_key in merged:
                print(f"[warn] duplicate {combo_key} in {label} (skip)", file=sys.stderr)
                continue
            merged[combo_key] = {
                "evaluation": evaluate_combination(
                    combo_key=combo_key,
                    methods_data=methods_data,
                    predictions_df=predictions_df,
                    time_exit_medians=time_exit_medians,
                ),
                "raw_summary": methods_data,
            }
        anomaly.update(src.get("anomaly_smell_per_combination", {}))

    missing = [c for c in EXPECTED_COMBINATIONS if c not in merged]
    extra = [c for c in merged if c not in EXPECTED_COMBINATIONS]

    # 案 V (2026-05-26・Step I-4.4): method_summary は PRIMARY (6 組合せ) 限定集計
    # 既存キー名 (`meets_6plus_criteria` / `n_combinations_all_pass`) は下流互換のため維持し、
    # 意味を「Primary 6 組合せ ALL PASS」「Primary 内 ALL PASS 数」に再定義
    method_summary: Dict[str, dict] = {}
    secondary_summary: Dict[str, dict] = {}
    for method in ("fixed_tp", "time_exit"):
        primary_pass = sorted(
            ck for ck in PRIMARY_COMBINATIONS
            if ck in merged and merged[ck]["evaluation"][method]["combo_all_pass"]
        )
        secondary_pass = sorted(
            ck for ck in SECONDARY_COMBINATIONS
            if ck in merged and merged[ck]["evaluation"][method]["combo_all_pass"]
        )
        method_summary[method] = {
            "n_combinations_all_pass": len(primary_pass),
            "all_pass_combinations": primary_pass,
            "meets_6plus_criteria": len(primary_pass) >= 6,
            "primary_total": len(PRIMARY_COMBINATIONS),
        }
        secondary_summary[method] = {
            "n_combinations_all_pass": len(secondary_pass),
            "all_pass_combinations": secondary_pass,
            "secondary_total": len(SECONDARY_COMBINATIONS),
        }

    meets_6plus_any = any(m["meets_6plus_criteria"] for m in method_summary.values())
    n_combinations_all_pass_max = max(
        m["n_combinations_all_pass"] for m in method_summary.values()
    )

    if meets_6plus_any:
        next_action = "Phase 2 (Optuna ハイパラ調整) 進行 — CC + まこさんレビュー"
    elif 4 <= n_combinations_all_pass_max <= 5:
        next_action = "Step G Major M2 + M3 統合 → 再 smoke (まこさん最終判断)"
    else:
        next_action = "案 X (Layer 3) or 案 Z (案 b-f) — まこさんレビュー必須"

    anomaly_detected_global = any(bool(v) for v in anomaly.values())

    return {
        "step": "I-3.4 §4.1 v5.1 判定 (4 指標・案 a)",
        "spec_version": "v2.1",
        "timestamp": datetime.now().isoformat(),
        "n_combinations": len(merged),
        "missing_combinations": missing,
        "extra_combinations": extra,
        "method_summary": method_summary,
        "secondary_filter_evaluation": secondary_summary,
        "filter_design": {
            "primary_K": K_PRIMARY_FILTER,
            "secondary_K": K_SECONDARY,
            "primary_combinations": PRIMARY_COMBINATIONS,
            "secondary_combinations": SECONDARY_COMBINATIONS,
            "reason": (
                "案 V (Step I-4.4): K=96 は 5m bot 運用要件 (即時 Exit ループ) と "
                "8h 予測ホライズン乖離で Primary 判定対象から除外・別レンズ評価"
            ),
        },
        "meets_6plus_any_method": meets_6plus_any,
        "n_combinations_all_pass_max": n_combinations_all_pass_max,
        "next_action": next_action,
        "anomaly_smell_per_combination": anomaly,
        "anomaly_smell_detected": anomaly_detected_global,
        "combinations": merged,
        "thresholds": {
            "tp_precision_min": THRESHOLD_TP_PRECISION,
            "months_positive_min": THRESHOLD_MONTHS_POSITIVE,
            "sim_pnl_year_usd_min": THRESHOLD_SIM_PNL_YEAR_USD,
            "dsr_min": THRESHOLD_DSR,
            "entropy_lift_threshold": THRESHOLD_ENTROPY_LIFT,
            "entropy_lift_note": "案 a (rmse) では NaN 自動 PASS 継承 (M2 後送り問題は別タスク)",
            "dsr_n_trials": DSR_N_TRIALS,
            "dsr_sr_variance": DSR_SR_VARIANCE,
            "tp_precision_time_exit_note": "time_exit method では TP precision 不適用 → 自動 PASS",
            "cost_per_trade": DEFAULT_COST_PER_TRADE,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Step I-3.4: merge 3 並列 case_a_v2 + 4 指標判定"
    )
    parser.add_argument("--p1-case-a", type=Path, default=DEFAULT_P1_CASE_A)
    parser.add_argument("--p2-case-a", type=Path, default=DEFAULT_P2_CASE_A)
    parser.add_argument("--p3-case-a", type=Path, default=DEFAULT_P3_CASE_A)
    parser.add_argument("--p1-tp", type=Path, default=DEFAULT_P1_TP)
    parser.add_argument("--p2-tp", type=Path, default=DEFAULT_P2_TP)
    parser.add_argument("--p3-tp", type=Path, default=DEFAULT_P3_TP)
    parser.add_argument("--time-exit-index", type=Path, default=DEFAULT_TIME_EXIT_INDEX)
    parser.add_argument("--out-base", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--suffix", type=str, default="train_2021_2024")
    args = parser.parse_args()

    p1_ca = load_case_a_summary(args.p1_case_a, args.suffix)
    p2_ca = load_case_a_summary(args.p2_case_a, args.suffix)
    p3_ca = load_case_a_summary(args.p3_case_a, args.suffix)

    pred_dfs = [
        load_predictions(args.p1_tp, args.suffix),
        load_predictions(args.p2_tp, args.suffix),
        load_predictions(args.p3_tp, args.suffix),
    ]
    predictions_df = pd.concat(pred_dfs, ignore_index=True)
    print(f"[load] predictions concatenated: {len(predictions_df)} rows")

    time_exit_medians = load_time_exit_medians(args.time_exit_index)
    print(f"[load] time_exit_medians: {len(time_exit_medians)} entries")

    result = merge_and_evaluate(
        p1_ca=p1_ca,
        p2_ca=p2_ca,
        p3_ca=p3_ca,
        predictions_df=predictions_df,
        time_exit_medians=time_exit_medians,
    )

    args.out_base.mkdir(parents=True, exist_ok=True)
    out_path = args.out_base / "phase1_v5_step_i_summary_merged.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2, default=str)

    print(f"\n=== §4.1 v5.1 判定結果 ===")
    print(f"n_combinations: {result['n_combinations']}")
    if result["missing_combinations"]:
        print(f"missing: {result['missing_combinations']}")
    for method, ms in result["method_summary"].items():
        flag = "✅" if ms["meets_6plus_criteria"] else "❌"
        print(
            f"  {method:<10} ALL PASS = {ms['n_combinations_all_pass']}/8 "
            f"(6+ 基準: {flag})"
        )
        if ms["all_pass_combinations"]:
            print(f"    -> {ms['all_pass_combinations']}")
    print(f"meets_6plus_any_method: {result['meets_6plus_any_method']}")
    print(f"anomaly_smell_detected: {result['anomaly_smell_detected']}")
    print(f"次アクション: {result['next_action']}")
    print(f"\nsaved: {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
