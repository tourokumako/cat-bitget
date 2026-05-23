"""
run_lgbm_phase1_v5_case_a_v2_v3.py — Step I-4.1 Critical-1 修正版 (time_exit 予測装置化)

Step I-4.1 仕様書 v2 (`.claude/instructions/2026-05-23_step_i4_1_case_a_v2_v3_critical1_spec.md`) の
Critical-1 修正実装。前身 case_a_v2 (Step I-3 で 0/16 ALL PASS の構造的欠陥が発覚) を別ファイル
として保護したまま、time_exit method を **予測装置** として復活させる修正版。

case_a_v2 からの変更点 (3 箇所):
1. time_exit grid を N × TP_PCT = 12 grid に拡張 (旧 N 2 grid のみ)
2. time_exit method 呼び出しで tp_hit_prob (実 Classifier 出力) を渡す (旧 dummy 0.5)
3. C2 ガード追加 (|TP_PCT - time_exit_median| < 0.05% は naive baseline 再演リスクで skip)

期待動作:
- fold 内 returns 分散が非ゼロ (L-212c 関所 B 拡張: 評価式の予測装置性宣言)
- DSR 計算が正常動作 (L-212b dsr × time_exit 定数化相互作用 解消方向)

事前条件 (I-2.1 / I-2.2 で生成済の artifact が必要):
- I-2.1: results/.../ml_phase1_v5/_tp_hit_classifier/tp_hit_classifier_predictions_*.parquet
- I-2.2: results/.../ml_phase1_v5/_phase4b_train_constants/time_exit_return_median_*.json

CLI:
- --smoke: sample.parquet / K=12 LONG / TP_PCT=(0.5,) / SL_PCT=(0.5,) / N=K のみ
- --full: train_2021_2024.parquet / 8 組合せ × full grid
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_phase1_v5_purged_kfold import (  # noqa: E402
    K_DEFAULT_LIST,
    OUT_BASE,
    PARQUET_DIR,
    SIDES_DEFAULT,
    DEFAULT_COST_PER_TRADE,
    DEFAULT_POSITION_SIZE_BTC,
    DEFAULT_BTC_PRICE_AVG,
    compute_simulated_pnl_v2,
    load_parquet_with_blacklist,
    prepare_purged_cv,
    split_with_purging,
)
from run_lgbm_phase1_v5_case_a_rmse import (  # noqa: E402
    _build_train_valid_split,
    _train_one_model,
    VALID_TAIL_FRACTION,
)

CASE_NAME_V3 = "a_rmse_v2_v3"

# 仕様書 §3.2 grid
TP_PCT_GRID: Tuple[float, ...] = (0.3, 0.5, 0.8, 1.2, 1.8, 2.5, 3.0, 3.5)
SL_PCT_GRID: Tuple[float, ...] = (0.3, 0.5, 0.8, 1.0, 1.2, 1.5)
N_RATIOS: Tuple[float, ...] = (0.5, 1.0)

OUT_BASE_V3 = OUT_BASE / "_case_a_v2_v3"
TP_HIT_PREDICTIONS_DIR = OUT_BASE / "_tp_hit_classifier"
TIME_EXIT_CONSTANTS_DIR = OUT_BASE / "_phase4b_train_constants"


@dataclass
class MethodGridResult:
    """1 method × 1 grid (TP_PCT, SL_pct) or N の sim_pnl 結果."""

    method: str  # "fixed_tp" / "time_exit"
    fold_idx: int
    K: int
    side: str
    tp_pct: Optional[float] = None       # method=fixed_tp で使用
    sl_pct: Optional[float] = None       # method=fixed_tp で使用
    N: Optional[int] = None              # method=time_exit で使用
    train_sim_pnl_year_usd: float = 0.0  # train_idx_inner の sim_pnl (idxmax 集約用)
    test_sim_pnl_year_usd: float = 0.0
    test_months_positive: int = 0
    train_mean_return: float = 0.0
    test_mean_return: float = 0.0
    n_train: int = 0
    n_test: int = 0
    tp_hit_prob_mean: float = float("nan")
    time_exit_return_median: float = float("nan")


@dataclass
class MethodFoldMetrics:
    """1 fold × 1 組合せ (K × side) × 1 method の集約結果 (train PnL idxmax)."""

    method: str
    fold_idx: int
    K: int
    side: str
    # 集約後の grid 値
    best_tp_pct: Optional[float] = None
    best_sl_pct: Optional[float] = None
    best_N: Optional[int] = None
    # test 評価
    test_sim_pnl_year_usd: float = 0.0
    test_months_positive: int = 0
    n_train: int = 0
    n_test: int = 0
    train_start: str = ""
    train_end: str = ""
    test_start: str = ""
    test_end: str = ""
    # 全 grid 結果 (記録のみ・M2 集約後の monitor 用)
    all_grid_results: List[MethodGridResult] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def _load_tp_hit_predictions(
    predictions_path: Path,
) -> pd.DataFrame:
    """I-2.1 で生成した tp_hit_classifier_predictions_*.parquet をロード.

    Columns: trade_ts, TP_PCT, tp_hit_prob, tp_hit_true, fold_idx, K, side
    """
    if not predictions_path.exists():
        raise FileNotFoundError(
            f"tp_hit_predictions parquet not found: {predictions_path}\n"
            f"  → I-2.1 (run_tp_hit_classifier.py) を先に実行してください"
        )
    df = pd.read_parquet(predictions_path)
    required = {"trade_ts", "TP_PCT", "tp_hit_prob", "fold_idx", "K", "side"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"tp_hit_predictions missing columns: {missing}")
    df["trade_ts"] = pd.to_datetime(df["trade_ts"])
    return df


def _load_time_exit_medians(
    index_path: Path,
) -> Dict[Tuple[int, str, int], float]:
    """I-2.2 で生成した time_exit_return_median_INDEX_*.json をロード.

    Returns:
        {(K, side, N): median_pct}
    """
    if not index_path.exists():
        raise FileNotFoundError(
            f"time_exit INDEX json not found: {index_path}\n"
            f"  → I-2.2 (compute_phase4b_train_constants.py) を先に実行してください"
        )
    with open(index_path) as f:
        idx_data = json.load(f)
    median_matrix = idx_data.get("median_pct_matrix", {})
    out: Dict[Tuple[int, str, int], float] = {}
    for key, median_pct in median_matrix.items():
        # key 形式: "K12_LONG_N6"
        parts = key.split("_")
        K = int(parts[0][1:])  # "K12" → 12
        side = parts[1]
        N = int(parts[2][1:])  # "N6" → 6
        out[(K, side, N)] = float(median_pct)
    return out


def _compute_v2_pnl_per_fold(
    fold_idx: int,
    K: int,
    side: str,
    train_idx_inner: np.ndarray,
    test_idx: np.ndarray,
    X_index: pd.DatetimeIndex,
    tp_hit_df_combo_fold: pd.DataFrame,
    time_exit_medians: Dict[Tuple[int, str, int], float],
    tp_pct_grid: Tuple[float, ...] = TP_PCT_GRID,
    sl_pct_grid: Tuple[float, ...] = SL_PCT_GRID,
    n_ratios: Tuple[float, ...] = N_RATIOS,
    cost_per_trade: float = DEFAULT_COST_PER_TRADE,
    position_size_btc: float = DEFAULT_POSITION_SIZE_BTC,
    btc_price_avg: float = DEFAULT_BTC_PRICE_AVG,
) -> Tuple[MethodFoldMetrics, MethodFoldMetrics]:
    """1 fold × 1 組合せ (K × side) × 2 method × full grid の sim_pnl 計算 + train PnL idxmax 集約.

    Returns:
        (fixed_tp_metrics, time_exit_metrics)
    """
    test_ts = X_index[test_idx]
    train_ts = X_index[train_idx_inner]
    test_ts_set = set(test_ts)

    # --- method (a) fixed_tp: TP_PCT × SL_pct grid ---
    fixed_tp_grids: List[MethodGridResult] = []
    for tp_pct in tp_pct_grid:
        # この (K, side, fold_idx, TP_PCT) の tp_hit_prob を抽出
        df_tp = tp_hit_df_combo_fold[tp_hit_df_combo_fold["TP_PCT"] == tp_pct]
        if df_tp.empty:
            continue
        df_tp_indexed = df_tp.set_index("trade_ts")["tp_hit_prob"]
        # train/test 別に取り出し
        # I-2.1 predictions は test_idx 範囲のみ保存している。train tp_hit_prob 計算には
        # 各 fold の test 範囲外 (= 他 fold の test 範囲) の予測値が必要
        # 暫定対処: train_ts 範囲の tp_hit_prob を「他 fold の予測値が使えるなら使う」方式
        train_probs = df_tp_indexed.reindex(train_ts)
        test_probs = df_tp_indexed.reindex(test_ts)
        # NaN を mean で埋める (他 fold 予測値ない場合・暫定)
        if train_probs.isna().any():
            train_probs = train_probs.fillna(train_probs.mean() if not train_probs.dropna().empty else 0.5)
        if test_probs.isna().any():
            # 全部 NaN の可能性 (= predictions 不在) → skip
            if test_probs.isna().all():
                continue
            test_probs = test_probs.fillna(test_probs.mean())

        for sl_pct in sl_pct_grid:
            # train sim_pnl (idxmax 集約用)
            _, train_year_usd, train_diag = compute_simulated_pnl_v2(
                tp_hit_prob=train_probs,
                tp_pct=tp_pct,
                sl_pct=sl_pct,
                time_exit_return_median=0.0,  # unused for fixed_tp
                method="fixed_tp",
                cost_per_trade=cost_per_trade,
                position_size_btc=position_size_btc,
                btc_price_avg=btc_price_avg,
            )
            # test sim_pnl
            test_mp, test_year_usd, test_diag = compute_simulated_pnl_v2(
                tp_hit_prob=test_probs,
                tp_pct=tp_pct,
                sl_pct=sl_pct,
                time_exit_return_median=0.0,
                method="fixed_tp",
                cost_per_trade=cost_per_trade,
                position_size_btc=position_size_btc,
                btc_price_avg=btc_price_avg,
            )
            fixed_tp_grids.append(MethodGridResult(
                method="fixed_tp",
                fold_idx=fold_idx,
                K=K,
                side=side,
                tp_pct=tp_pct,
                sl_pct=sl_pct,
                train_sim_pnl_year_usd=train_year_usd,
                test_sim_pnl_year_usd=test_year_usd,
                test_months_positive=test_mp,
                train_mean_return=float(train_diag.get("mean_return", 0.0)),
                test_mean_return=float(test_diag.get("mean_return", 0.0)),
                n_train=int(train_diag.get("n_trades", 0)),
                n_test=int(test_diag.get("n_trades", 0)),
                tp_hit_prob_mean=float(test_diag.get("tp_hit_prob_mean", float("nan"))),
            ))

    # --- method (c) time_exit: N × TP_PCT grid (Critical-1 修正・予測装置化) ---
    # 旧式 (N grid のみ・dummy 0.5 tp_hit_prob・tp_pct=0.0) は naive baseline (L-212c)
    # 新式: tp_pct grid (6) × N grid (2) = 12 grid + 実 tp_hit_prob ロード + C2 ガード
    time_exit_grids: List[MethodGridResult] = []
    for tp_pct in tp_pct_grid:
        # この (K, side, fold_idx, TP_PCT) の tp_hit_prob を抽出 (fixed_tp と同じロジック)
        df_tp = tp_hit_df_combo_fold[tp_hit_df_combo_fold["TP_PCT"] == tp_pct]
        if df_tp.empty:
            print(f"[warn] time_exit: tp_hit_prob not found for TP_PCT={tp_pct} — skip")
            continue
        df_tp_indexed = df_tp.set_index("trade_ts")["tp_hit_prob"]
        train_probs = df_tp_indexed.reindex(train_ts)
        test_probs = df_tp_indexed.reindex(test_ts)
        if train_probs.isna().any():
            train_probs = train_probs.fillna(train_probs.mean() if not train_probs.dropna().empty else 0.5)
        if test_probs.isna().any():
            if test_probs.isna().all():
                continue
            test_probs = test_probs.fillna(test_probs.mean())

        for ratio in n_ratios:
            N = max(1, int(K * ratio))
            median_pct = time_exit_medians.get((K, side, N))
            if median_pct is None:
                print(
                    f"[warn] time_exit_median not found for (K={K}, side={side}, N={N}) — skip"
                )
                continue
            # C2 ガード: TP_PCT ≒ median 重複時は skip + warning (naive baseline 再演リスク)
            # 現実には Step I-3.2 実測 median ≦ 0.03% で発動しない想定 (safety net)
            if abs((tp_pct / 100.0) - (median_pct / 100.0)) < 5e-4:
                print(
                    f"[warn] C2 ガード発動 (K={K} {side} N={N} tp_pct={tp_pct}% "
                    f"median={median_pct:.4f}%) — naive baseline 再演リスクで skip"
                )
                continue
            # train sim_pnl (idxmax 集約用)
            _, train_year_usd, train_diag = compute_simulated_pnl_v2(
                tp_hit_prob=train_probs,
                tp_pct=tp_pct,         # NEW: 実 tp_pct (旧 dummy 0.0)
                sl_pct=0.0,            # time_exit method では未使用
                time_exit_return_median=median_pct,
                method="time_exit",
                cost_per_trade=cost_per_trade,
                position_size_btc=position_size_btc,
                btc_price_avg=btc_price_avg,
            )
            # test sim_pnl
            test_mp, test_year_usd, test_diag = compute_simulated_pnl_v2(
                tp_hit_prob=test_probs,
                tp_pct=tp_pct,
                sl_pct=0.0,
                time_exit_return_median=median_pct,
                method="time_exit",
                cost_per_trade=cost_per_trade,
                position_size_btc=position_size_btc,
                btc_price_avg=btc_price_avg,
            )
            time_exit_grids.append(MethodGridResult(
                method="time_exit",
                fold_idx=fold_idx,
                K=K,
                side=side,
                tp_pct=tp_pct,         # NEW: tp_pct 保持 (idxmax 集約後の記録用)
                sl_pct=None,           # time_exit method では未使用
                N=N,
                train_sim_pnl_year_usd=train_year_usd,
                test_sim_pnl_year_usd=test_year_usd,
                test_months_positive=test_mp,
                train_mean_return=float(train_diag.get("mean_return", 0.0)),
                test_mean_return=float(test_diag.get("mean_return", 0.0)),
                n_train=int(train_diag.get("n_trades", 0)),
                n_test=int(test_diag.get("n_trades", 0)),
                tp_hit_prob_mean=float(test_diag.get("tp_hit_prob_mean", float("nan"))),
                time_exit_return_median=median_pct,
            ))

    # train PnL idxmax で grid 集約 (M2 反映)
    fixed_tp_metrics = _aggregate_grid_idxmax(
        grid_results=fixed_tp_grids,
        method="fixed_tp",
        fold_idx=fold_idx, K=K, side=side,
        train_ts=train_ts, test_ts=test_ts,
    )
    time_exit_metrics = _aggregate_grid_idxmax(
        grid_results=time_exit_grids,
        method="time_exit",
        fold_idx=fold_idx, K=K, side=side,
        train_ts=train_ts, test_ts=test_ts,
    )
    return fixed_tp_metrics, time_exit_metrics


def _aggregate_grid_idxmax(
    grid_results: List[MethodGridResult],
    method: str,
    fold_idx: int,
    K: int,
    side: str,
    train_ts: pd.DatetimeIndex,
    test_ts: pd.DatetimeIndex,
) -> MethodFoldMetrics:
    """train PnL idxmax で grid 集約 (M2 反映)."""
    if not grid_results:
        return MethodFoldMetrics(
            method=method, fold_idx=fold_idx, K=K, side=side,
            warnings=["no valid grid result"],
        )
    # train sim_pnl 最大の grid を選択
    best_idx = int(np.argmax([g.train_sim_pnl_year_usd for g in grid_results]))
    best = grid_results[best_idx]
    return MethodFoldMetrics(
        method=method,
        fold_idx=fold_idx,
        K=K,
        side=side,
        best_tp_pct=best.tp_pct,
        best_sl_pct=best.sl_pct,
        best_N=best.N,
        test_sim_pnl_year_usd=best.test_sim_pnl_year_usd,
        test_months_positive=best.test_months_positive,
        n_train=best.n_train,
        n_test=best.n_test,
        train_start=str(train_ts[0]) if len(train_ts) > 0 else "",
        train_end=str(train_ts[-1]) if len(train_ts) > 0 else "",
        test_start=str(test_ts[0]) if len(test_ts) > 0 else "",
        test_end=str(test_ts[-1]) if len(test_ts) > 0 else "",
        all_grid_results=grid_results,
    )


def train_case_a_v2_v3(
    parquet_path: Path,
    tp_hit_predictions_path: Path,
    time_exit_index_path: Path,
    k_values: Tuple[int, ...] = K_DEFAULT_LIST,
    sides: Tuple[str, ...] = SIDES_DEFAULT,
    tp_pct_grid: Tuple[float, ...] = TP_PCT_GRID,
    sl_pct_grid: Tuple[float, ...] = SL_PCT_GRID,
    n_ratios: Tuple[float, ...] = N_RATIOS,
    n_splits: int = 5,
    min_train_splits: int = 2,
    out_base: Path = OUT_BASE_V3,
) -> Dict[str, Dict[str, List[MethodFoldMetrics]]]:
    """case_a v2 統合: 8 組合せ × 5 fold × 2 method × grid 集約 → method 別 sim_pnl 出力."""
    out_base.mkdir(parents=True, exist_ok=True)
    t_start = time.time()
    print(f"\n=== case_a v2 (2 method 並列・grid idxmax 集約) 開始 (Step I-2.4) ===")
    print(f"parquet: {parquet_path}")
    print(f"tp_hit_predictions: {tp_hit_predictions_path}")
    print(f"time_exit_index:    {time_exit_index_path}")
    print(f"k={k_values} sides={sides}")
    print(f"tp_pct_grid={tp_pct_grid} sl_pct_grid={sl_pct_grid} n_ratios={n_ratios}")

    # 1. artifact load
    tp_hit_df = _load_tp_hit_predictions(tp_hit_predictions_path)
    print(f"[load] tp_hit predictions: {len(tp_hit_df)} rows")
    time_exit_medians = _load_time_exit_medians(time_exit_index_path)
    print(f"[load] time_exit medians: {len(time_exit_medians)} entries")

    # 2. parquet load
    X, y_dict, idx = load_parquet_with_blacklist(parquet_path)
    print(f"X shape: {X.shape} / index range: {idx[0]} ~ {idx[-1]}")

    # 3. 8 組合せ × 5 fold loop
    cv = prepare_purged_cv(n_splits=n_splits, min_train_splits=min_train_splits)
    all_results: Dict[str, Dict[str, List[MethodFoldMetrics]]] = {}
    # 構造: {combo_key: {method: [fold_metrics_list]}}

    for K in k_values:
        for side in sides:
            combo_key = f"K{K}_{side}"
            print(f"\n--- 組合せ {combo_key} ---")
            all_results[combo_key] = {"fixed_tp": [], "time_exit": []}

            # この (K, side) の tp_hit_df subset
            df_combo = tp_hit_df[(tp_hit_df["K"] == K) & (tp_hit_df["side"] == side)]
            if df_combo.empty:
                print(f"  [warn] tp_hit_predictions に (K={K}, side={side}) なし — skip")
                continue

            for fold_idx, (train_idx, test_idx) in enumerate(
                split_with_purging(cv, X, idx, K)
            ):
                train_idx_inner, _valid_idx = _build_train_valid_split(
                    train_idx, VALID_TAIL_FRACTION
                )
                # この fold の tp_hit subset
                df_fold = df_combo[df_combo["fold_idx"] == fold_idx]
                if df_fold.empty:
                    print(f"  [warn] fold {fold_idx}: tp_hit_predictions なし — skip")
                    continue

                fixed_tp_fm, time_exit_fm = _compute_v2_pnl_per_fold(
                    fold_idx=fold_idx,
                    K=K, side=side,
                    train_idx_inner=train_idx_inner,
                    test_idx=test_idx,
                    X_index=idx,
                    tp_hit_df_combo_fold=df_fold,
                    time_exit_medians=time_exit_medians,
                    tp_pct_grid=tp_pct_grid,
                    sl_pct_grid=sl_pct_grid,
                    n_ratios=n_ratios,
                )
                all_results[combo_key]["fixed_tp"].append(fixed_tp_fm)
                all_results[combo_key]["time_exit"].append(time_exit_fm)
                print(
                    f"  fold {fold_idx}: "
                    f"fixed_tp test_pnl=${fixed_tp_fm.test_sim_pnl_year_usd:.0f} "
                    f"(TP={fixed_tp_fm.best_tp_pct}% SL={fixed_tp_fm.best_sl_pct}%) | "
                    f"time_exit test_pnl=${time_exit_fm.test_sim_pnl_year_usd:.0f} "
                    f"(N={time_exit_fm.best_N})"
                )

    # 4. 統合 summary JSON 出力
    elapsed_total = time.time() - t_start
    summary_path = out_base / f"case_a_v2_v3_summary_{parquet_path.stem}.json"
    summary_data: Dict[str, object] = {
        "case_name": CASE_NAME_V3,
        "parquet": parquet_path.name,
        "tp_hit_predictions": str(tp_hit_predictions_path),
        "time_exit_index": str(time_exit_index_path),
        "k_values": list(k_values),
        "sides": list(sides),
        "tp_pct_grid": list(tp_pct_grid),
        "sl_pct_grid": list(sl_pct_grid),
        "n_ratios": list(n_ratios),
        "elapsed_sec": elapsed_total,
        "timestamp": datetime.now().isoformat(),
        "combinations": {
            combo_key: {
                method: [asdict(fm) for fm in fms]
                for method, fms in method_dict.items()
            }
            for combo_key, method_dict in all_results.items()
        },
    }
    # method 別 月次相当 NET 算出 (異常値スメル ② 検出用)
    anomaly_smell_per_combination: Dict[str, Dict[str, List[str]]] = {}
    for combo_key, method_dict in all_results.items():
        anomaly_smell_per_combination[combo_key] = {}
        for method, fms in method_dict.items():
            year_usds = [fm.test_sim_pnl_year_usd for fm in fms]
            if not year_usds:
                continue
            max_year = max(year_usds)
            if max_year > 45600.0:  # 月次相当 > $3,800
                anomaly_smell_per_combination[combo_key][method] = [
                    f"② 月次 NET > $3,800: max year=${max_year:.0f} "
                    f"(月次相当=${max_year/12:.0f})"
                ]
    summary_data["anomaly_smell_per_combination"] = anomaly_smell_per_combination
    summary_data["anomaly_smell_detected"] = bool(
        any(v for v in anomaly_smell_per_combination.values())
    )

    with open(summary_path, "w") as f:
        json.dump(summary_data, f, indent=2, default=str)
    print(f"\n[save] summary: {summary_path}")

    print(f"\n=== case_a v2 完了 ===")
    print(f"elapsed: {elapsed_total/60:.1f} min")
    print(f"anomaly_smell_detected: {summary_data['anomaly_smell_detected']}")
    if summary_data["anomaly_smell_detected"]:
        print(f"異常値スメル ② ヒット組合せ × method:")
        for combo_key, method_dict in anomaly_smell_per_combination.items():
            for method, triggers in method_dict.items():
                if triggers:
                    print(f"  [{combo_key} / {method}] {triggers[0]}")
    else:
        print("✅ 異常値スメル ② 全 8 組合せ × 2 method で セーフ (関所 A v2 達成)")

    return all_results


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Step I-2.4: case_a v2 (2 method 並列・grid idxmax 集約)"
    )
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--parquet", type=Path, default=None)
    parser.add_argument(
        "--tp-hit-predictions",
        type=Path,
        default=None,
        help="I-2.1 predictions parquet 明示指定",
    )
    parser.add_argument(
        "--time-exit-index",
        type=Path,
        default=None,
        help="I-2.2 INDEX JSON 明示指定",
    )
    parser.add_argument("--k", type=int, nargs="+", default=None)
    parser.add_argument("--side", type=str, nargs="+", default=None, choices=["LONG", "SHORT"])
    parser.add_argument("--tp-pct", type=float, nargs="+", default=None)
    parser.add_argument("--sl-pct", type=float, nargs="+", default=None)
    parser.add_argument("--n-ratios", type=float, nargs="+", default=None)
    parser.add_argument("--n-splits", type=int, default=5)
    parser.add_argument("--min-train-splits", type=int, default=2)
    parser.add_argument("--out-base", type=Path, default=OUT_BASE_V3)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    if args.parquet:
        parquet_path = args.parquet
    elif args.smoke:
        parquet_path = PARQUET_DIR / "labels_mfe_mae_pct_sample.parquet"
    elif args.full:
        parquet_path = PARQUET_DIR / "labels_mfe_mae_pct_train_2021_2024.parquet"
    else:
        print("[ERROR] --smoke / --full / --parquet のいずれか必須", file=sys.stderr)
        return 2

    suffix = "sample" if "sample" in parquet_path.name else "train_2021_2024"

    if args.tp_hit_predictions:
        tp_hit_path = args.tp_hit_predictions
    else:
        tp_hit_path = TP_HIT_PREDICTIONS_DIR / f"tp_hit_classifier_predictions_{suffix}.parquet"
    if args.time_exit_index:
        time_exit_path = args.time_exit_index
    else:
        time_exit_path = TIME_EXIT_CONSTANTS_DIR / f"time_exit_return_median_INDEX_{suffix}.json"

    if args.smoke:
        k_values = tuple(args.k) if args.k else (12,)
        sides = tuple(args.side) if args.side else ("LONG",)
        tp_pct_grid = tuple(args.tp_pct) if args.tp_pct else (0.5,)
        sl_pct_grid = tuple(args.sl_pct) if args.sl_pct else (0.5,)
        n_ratios = tuple(args.n_ratios) if args.n_ratios else (1.0,)
        min_train_splits = args.min_train_splits if args.min_train_splits is not None else 1
        n_splits = args.n_splits if args.n_splits is not None else 3
    else:
        k_values = tuple(args.k) if args.k else K_DEFAULT_LIST
        sides = tuple(args.side) if args.side else SIDES_DEFAULT
        tp_pct_grid = tuple(args.tp_pct) if args.tp_pct else TP_PCT_GRID
        sl_pct_grid = tuple(args.sl_pct) if args.sl_pct else SL_PCT_GRID
        n_ratios = tuple(args.n_ratios) if args.n_ratios else N_RATIOS
        min_train_splits = args.min_train_splits if args.min_train_splits is not None else 2
        n_splits = args.n_splits if args.n_splits is not None else 5

    print(f"[run] mode: {'smoke' if args.smoke else ('full' if args.full else 'explicit')}")
    print(f"[run] start: {datetime.now().isoformat()}")

    try:
        train_case_a_v2_v3(
            parquet_path=parquet_path,
            tp_hit_predictions_path=tp_hit_path,
            time_exit_index_path=time_exit_path,
            k_values=k_values,
            sides=sides,
            tp_pct_grid=tp_pct_grid,
            sl_pct_grid=sl_pct_grid,
            n_ratios=n_ratios,
            n_splits=n_splits,
            min_train_splits=min_train_splits,
            out_base=args.out_base,
        )
    except Exception as e:
        import traceback
        print(f"[ERROR] {type(e).__name__}: {e}", file=sys.stderr)
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
