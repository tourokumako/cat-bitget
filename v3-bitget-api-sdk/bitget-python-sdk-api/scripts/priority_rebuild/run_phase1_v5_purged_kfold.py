"""
run_phase1_v5_purged_kfold.py — Phase 1 v5 共通 Purged K-Fold CV runner

Phase 1 v5 学習方法再設計 (Layer 配分逆転確定版) の 6 案 (a-f) で共通利用する
Walk-forward Purged K-Fold 5 fold CV ライブラリ.

正本:
- Phase 1 v5 指示書: .claude/instructions/2026-05-22_phase1_layer_inversion_instruction.md
- cc_ml_design_spec.md §1.5.1 (Phase 1 合格基準 5 指標)
- phase_compliance_checklist.md §Phase -1 (blacklist 64 列・8 family × 8 TF)

公開 API:
- load_parquet_with_blacklist: parquet load + 64 列 blacklist drop + 56 ラベル分離
- compute_t1_vertical_barrier: Triple Barrier vertical barrier 時刻 (t1) 算出
- prepare_purged_cv / split_with_purging: timeseriescv.PurgedWalkForwardCV ラッパ
- compute_fold_metrics: 4 指標 (entropy_lift / TP_Precision / Direction_Acc / Sim_PnL) fold 単位
- save_fold_results: fold 結果保存 (predictions / metrics / fi_top20 / log)
- aggregate_to_summary: 5 fold 統合 + DSR 算出 (selection bias 補正) + §4.1 合格判定

設計判断:
- DSR は fold 単位ではなく aggregate で計算 (sr_variance を 5 fold 統合 SR の variance で渡す)
- t1 (vertical barrier) は parquet に未保存のため index + K*5min で runtime 算出
- 56 ラベル列を物理的に X から drop (false_positive §0-1 Prime Directive)
- 64 blacklist 列は startswith マッチで動的検出 (phase_compliance_checklist §Phase -1)
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, log_loss, precision_score
from timeseriescv.cross_validation import PurgedWalkForwardCV

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dsr import compute_dsr_from_returns, sharpe_ratio  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
PARQUET_DIR = REPO_ROOT / "results" / "priority_rebuild"
OUT_BASE = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase1_v5"

# Phase -1 blacklist 8 family × 8 TF = 64 columns
BLACKLIST_FAMILIES: Tuple[str, ...] = (
    "sma_20",
    "sma_50",
    "ichimoku_kijun",
    "ichimoku_tenkan",
    "macd_line",
    "macd_signal",
    "macd_hist",
    "macd_hist_change",
)
EXPECTED_BLACKLIST_COUNT = 64

# 56 ラベル prefix (X から物理 drop 必須・false_positive §0-1)
LABEL_PREFIXES: Tuple[str, ...] = (
    "LONG_MFE_pct",
    "LONG_MAE_pct",
    "SHORT_MFE_pct",
    "SHORT_MAE_pct",
    "triple_barrier_label",
    "meta_label",
)
EXPECTED_LABEL_COUNT = 56

# Phase 1 合格基準 5 指標 (cc_ml_design_spec §1.5.1 / 指示書 §4)
PASS_ENTROPY_LIFT = 0.10
PASS_TP_PRECISION = 0.50
PASS_DIRECTION_ACC = 0.55
PASS_SIM_PNL_MONTHS = 8
PASS_SIM_PNL_YEAR_USD = 500.0
PASS_DSR_ZSCORE = 1.0


@dataclass
class FoldMetrics:
    """fold 単位の 4 指標 (DSR は aggregate で算出するためここには含めない)."""

    case_name: str
    fold_idx: int
    K: int
    entropy_lift: float
    tp_precision: float
    direction_accuracy: Optional[float]
    sim_pnl_months_positive: int
    sim_pnl_year_usd: float
    fold_sharpe: float
    n_train: int
    n_test: int
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    extra: Dict[str, float] = field(default_factory=dict)


@dataclass
class CaseSummary:
    """5 fold 統合 + DSR + §4.1 合格判定."""

    case_name: str
    n_folds: int
    entropy_lift_mean: float
    tp_precision_mean: float
    direction_accuracy_mean: Optional[float]
    sim_pnl_months_mean: float
    sim_pnl_year_usd_mean: float
    fold_sharpe_mean: float
    fold_sharpe_variance: float
    dsr_zscore: float
    dsr_probability: float
    dsr_n_trials: int
    pass_per_metric: Dict[str, bool]
    all_pass: bool
    layer3_investigation_needed: bool


def get_blacklist_columns(df: pd.DataFrame) -> List[str]:
    """Phase -1 blacklist 64 列 (8 family × 8 TF) を返す."""
    return [
        c
        for c in df.columns
        if any(c.startswith(f + "__") for f in BLACKLIST_FAMILIES)
    ]


def get_label_columns(df: pd.DataFrame) -> Dict[str, List[str]]:
    """56 ラベル列を prefix 別に辞書化."""
    out: Dict[str, List[str]] = {}
    for prefix in LABEL_PREFIXES:
        cols = sorted([c for c in df.columns if c.startswith(prefix)])
        out[prefix] = cols
    return out


def load_parquet_with_blacklist(
    parquet_path: Path,
    verbose: bool = True,
    enforce_counts: bool = True,
) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame], pd.DatetimeIndex]:
    """parquet load + 64 列 blacklist drop + 56 ラベル分離.

    Returns:
        X: 特徴量 DataFrame (約 2,604 列)
        y_dict: ラベル DataFrame の辞書 (prefix 別)
        index: timestamp DatetimeIndex
    """
    parquet_path = Path(parquet_path)
    df = pd.read_parquet(parquet_path)
    if verbose:
        print(f"[load] parquet shape: {df.shape} ({parquet_path.name})")

    blacklist = get_blacklist_columns(df)
    label_dict = get_label_columns(df)
    label_all = [c for cols in label_dict.values() for c in cols]
    drop_cols = blacklist + label_all

    X = df.drop(columns=drop_cols)
    y_dict = {prefix: df[cols] for prefix, cols in label_dict.items() if cols}

    if verbose:
        print(f"[load] blacklist drop: {len(blacklist)} (expected {EXPECTED_BLACKLIST_COUNT})")
        print(f"[load] label drop:     {len(label_all)} (expected {EXPECTED_LABEL_COUNT})")
        print(f"[load] X shape:        {X.shape}")
        for prefix, cols in label_dict.items():
            print(f"[load]   {prefix}: {len(cols)} cols")

    if enforce_counts:
        if len(blacklist) != EXPECTED_BLACKLIST_COUNT:
            raise ValueError(
                f"Blacklist columns mismatch: expected {EXPECTED_BLACKLIST_COUNT}, "
                f"got {len(blacklist)}"
            )
        if len(label_all) != EXPECTED_LABEL_COUNT:
            raise ValueError(
                f"Label columns mismatch: expected {EXPECTED_LABEL_COUNT}, "
                f"got {len(label_all)}"
            )

    return X, y_dict, df.index


def compute_t1_vertical_barrier(
    index: pd.DatetimeIndex,
    K: int,
    bar_freq: str = "5min",
) -> pd.Series:
    """Triple Barrier の vertical barrier 時刻 (t1 = bar timestamp + K * bar_freq).

    timeseriescv.PurgedWalkForwardCV の eval_times に渡す.
    Phase 0 v3.1 で parquet 未保存のため runtime 算出 (決定的・leak フリー).
    """
    bar_delta = pd.Timedelta(bar_freq)
    t1_values = index + (K * bar_delta)
    return pd.Series(t1_values, index=index, name=f"t1_K{K}")


def prepare_purged_cv(
    n_splits: int = 5,
    n_test_splits: int = 1,
    min_train_splits: int = 2,
    max_train_splits: Optional[int] = None,
) -> PurgedWalkForwardCV:
    """timeseriescv.PurgedWalkForwardCV インスタンス生成."""
    return PurgedWalkForwardCV(
        n_splits=n_splits,
        n_test_splits=n_test_splits,
        min_train_splits=min_train_splits,
        max_train_splits=max_train_splits,
    )


def split_with_purging(
    cv: PurgedWalkForwardCV,
    X: pd.DataFrame,
    index: pd.DatetimeIndex,
    K: int,
    bar_freq: str = "5min",
) -> Iterator[Tuple[np.ndarray, np.ndarray]]:
    """Purged Walk-Forward CV split (position indices).

    pred_times = bar timestamp (index 自体)
    eval_times = vertical barrier (index + K * bar_freq)
    """
    pred_times = pd.Series(index, index=index, name="pred_times")
    eval_times = compute_t1_vertical_barrier(index, K, bar_freq)
    yield from cv.split(X, pred_times=pred_times, eval_times=eval_times)


def compute_entropy_lift(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    num_classes: int,
) -> float:
    """Entropy lift = 1 - logloss / log(num_classes).

    num_classes < 2 (regression) は NaN を返す.
    """
    if num_classes < 2:
        return float("nan")
    baseline = float(np.log(num_classes))
    eps = 1e-15
    y_prob_clipped = np.clip(y_prob, eps, 1.0 - eps)
    if y_prob_clipped.ndim == 1:
        # binary: y_prob = P(class=1)
        ll = float(
            -(
                y_true * np.log(y_prob_clipped)
                + (1 - y_true) * np.log(1.0 - y_prob_clipped)
            ).mean()
        )
    else:
        ll = float(
            log_loss(y_true, y_prob_clipped, labels=list(range(num_classes)))
        )
    return 1.0 - ll / baseline


def compute_simulated_pnl(
    returns_per_trade: pd.Series,
    position_size_btc: float = 0.024,
    btc_price_avg: float = 50000.0,
) -> Tuple[int, float]:
    """naive simulated PnL.

    returns_per_trade: trade ごとの return ratio (pct/100 not %), index は trade timestamp.

    Returns:
        months_positive: トレードがあった月のうちプラス月数
        year_usd: 年間 NET ($)
    """
    if returns_per_trade.empty:
        return 0, 0.0
    if not isinstance(returns_per_trade.index, pd.DatetimeIndex):
        raise TypeError("returns_per_trade.index must be DatetimeIndex")
    monthly = returns_per_trade.groupby(
        returns_per_trade.index.to_period("M")
    ).sum()
    months_positive = int((monthly > 0).sum())
    position_usd = position_size_btc * btc_price_avg
    year_usd = float(returns_per_trade.sum() * position_usd)
    return months_positive, year_usd


def compute_fold_metrics(
    case_name: str,
    fold_idx: int,
    K: int,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: Optional[np.ndarray],
    num_classes: int,
    returns_per_trade: pd.Series,
    train_range: Tuple[pd.Timestamp, pd.Timestamp],
    test_range: Tuple[pd.Timestamp, pd.Timestamp],
    n_train: int,
    n_test: int,
    is_direction_case: bool = False,
    extra: Optional[Dict[str, float]] = None,
) -> FoldMetrics:
    """fold 単位の 4 指標 + Sharpe を計算 (DSR は aggregate で)."""
    # 1. entropy lift
    if y_prob is not None and num_classes >= 2:
        e_lift = compute_entropy_lift(y_true, y_prob, num_classes)
    else:
        e_lift = float("nan")

    # 2. TP precision (TP first = 0/1 と仮定; 案 a は caller 側で binarize)
    if len(y_pred) == 0 or np.sum(y_pred) == 0:
        tp_p = 0.0
    else:
        tp_p = float(precision_score(y_true, y_pred, zero_division=0.0))

    # 3. Direction accuracy (案 c のみ)
    direction_acc = (
        float(accuracy_score(y_true, y_pred)) if is_direction_case else None
    )

    # 4. Simulated PnL
    months_pos, year_usd = compute_simulated_pnl(returns_per_trade)

    # fold Sharpe (DSR 入力用・aggregate で 5 fold variance を sr_variance に渡す)
    if not returns_per_trade.empty and len(returns_per_trade) >= 2:
        fold_sharpe = float(sharpe_ratio(returns_per_trade.values))
    else:
        fold_sharpe = float("nan")

    return FoldMetrics(
        case_name=case_name,
        fold_idx=fold_idx,
        K=K,
        entropy_lift=float(e_lift),
        tp_precision=tp_p,
        direction_accuracy=direction_acc,
        sim_pnl_months_positive=months_pos,
        sim_pnl_year_usd=year_usd,
        fold_sharpe=fold_sharpe,
        n_train=int(n_train),
        n_test=int(n_test),
        train_start=str(train_range[0]),
        train_end=str(train_range[1]),
        test_start=str(test_range[0]),
        test_end=str(test_range[1]),
        extra=extra or {},
    )


def save_fold_results(
    case_name: str,
    fold_idx: int,
    metrics: FoldMetrics,
    predictions: pd.DataFrame,
    feature_importance_top20: pd.DataFrame,
    log_text: str,
    returns_per_trade: Optional[pd.Series] = None,
    out_base: Path = OUT_BASE,
) -> Path:
    """fold 結果保存 (predictions / metrics / fi_top20 / log / returns)."""
    out_dir = out_base / f"case_{case_name}_fold_{fold_idx}"
    out_dir.mkdir(parents=True, exist_ok=True)

    predictions.to_parquet(out_dir / "predictions.parquet")
    feature_importance_top20.to_csv(
        out_dir / "feature_importance_top20.csv", index=False
    )
    (out_dir / "log.txt").write_text(log_text, encoding="utf-8")
    with (out_dir / "metrics.json").open("w") as f:
        json.dump(asdict(metrics), f, indent=2, default=str)

    if returns_per_trade is not None and not returns_per_trade.empty:
        returns_per_trade.to_frame(name="return").to_parquet(
            out_dir / "returns_per_trade.parquet"
        )

    return out_dir


def aggregate_to_summary(
    case_name: str,
    fold_metrics: List[FoldMetrics],
    returns_all_folds: pd.Series,
    n_trials: int,
    out_base: Path = OUT_BASE,
) -> CaseSummary:
    """5 fold 統合 + DSR 算出 + §4.1 合格判定 → phase1_v5_summary.json 追記.

    Args:
        fold_metrics: 5 fold 分の FoldMetrics
        returns_all_folds: 5 fold 統合した trade returns (DSR 計算用)
        n_trials: DSR selection bias 補正のための過去 grid 試行数
            (Phase 1 v5 では 6 案 = 6・grid search も実行する場合は試行総数)
    """
    if not fold_metrics:
        raise ValueError("fold_metrics is empty")

    def _mean(values: Iterable[float]) -> float:
        clean = [
            v for v in values if v is not None and not (isinstance(v, float) and np.isnan(v))
        ]
        return float(np.mean(clean)) if clean else float("nan")

    e_lift_mean = _mean([m.entropy_lift for m in fold_metrics])
    tp_p_mean = _mean([m.tp_precision for m in fold_metrics])
    direction_vals = [m.direction_accuracy for m in fold_metrics if m.direction_accuracy is not None]
    direction_mean = _mean(direction_vals) if direction_vals else None
    months_mean = _mean([m.sim_pnl_months_positive for m in fold_metrics])
    year_usd_mean = _mean([m.sim_pnl_year_usd for m in fold_metrics])
    fold_sharpe_mean = _mean([m.fold_sharpe for m in fold_metrics])
    fold_sharpe_var = float(
        np.var(
            [m.fold_sharpe for m in fold_metrics if not np.isnan(m.fold_sharpe)],
            ddof=1,
        )
    ) if len([m for m in fold_metrics if not np.isnan(m.fold_sharpe)]) >= 2 else float("nan")

    # DSR (5 fold 統合 returns + fold-Sharpe variance を sr_variance に渡す)
    if (
        not returns_all_folds.empty
        and len(returns_all_folds) >= 30
        and not np.isnan(fold_sharpe_var)
    ):
        dsr_result = compute_dsr_from_returns(
            returns=returns_all_folds.values,
            n_trials=n_trials,
            sr_variance=fold_sharpe_var,
        )
        dsr_z = float(dsr_result.dsr_zscore)
        dsr_p = float(dsr_result.dsr_probability)
    else:
        dsr_z = float("nan")
        dsr_p = float("nan")

    # §4.1 合格判定 (5 指標 ALL PASS = 1 件でも未達 → Layer 3 投入)
    passes = {
        "entropy_lift": bool(e_lift_mean > PASS_ENTROPY_LIFT),
        "tp_precision": bool(tp_p_mean > PASS_TP_PRECISION),
        "direction_accuracy": bool(
            direction_mean is None or direction_mean > PASS_DIRECTION_ACC
        ),
        "sim_pnl": bool(
            months_mean >= PASS_SIM_PNL_MONTHS
            and year_usd_mean >= PASS_SIM_PNL_YEAR_USD
        ),
        "dsr": bool(not np.isnan(dsr_z) and dsr_z > PASS_DSR_ZSCORE),
    }
    all_pass = all(passes.values())

    summary = CaseSummary(
        case_name=case_name,
        n_folds=len(fold_metrics),
        entropy_lift_mean=e_lift_mean,
        tp_precision_mean=tp_p_mean,
        direction_accuracy_mean=direction_mean,
        sim_pnl_months_mean=months_mean,
        sim_pnl_year_usd_mean=year_usd_mean,
        fold_sharpe_mean=fold_sharpe_mean,
        fold_sharpe_variance=fold_sharpe_var,
        dsr_zscore=dsr_z,
        dsr_probability=dsr_p,
        dsr_n_trials=n_trials,
        pass_per_metric=passes,
        all_pass=all_pass,
        layer3_investigation_needed=not all_pass,
    )

    # JSON 追記
    out_base.mkdir(parents=True, exist_ok=True)
    summary_path = out_base / "phase1_v5_summary.json"
    if summary_path.exists():
        full = json.loads(summary_path.read_text(encoding="utf-8"))
    else:
        full = {"cases": {}}
    full["cases"][case_name] = {
        "summary": asdict(summary),
        "fold_metrics": [asdict(m) for m in fold_metrics],
    }
    full["updated_at"] = pd.Timestamp.now().isoformat()
    summary_path.write_text(
        json.dumps(full, indent=2, default=str), encoding="utf-8"
    )

    return summary


def _self_check() -> int:
    """import smoke + 簡易 API verify (CI 不要・stand-alone 動作確認)."""
    print("=== run_phase1_v5_purged_kfold.py self_check ===")
    cv = prepare_purged_cv(n_splits=5)
    print(f"PurgedWalkForwardCV: {cv}")

    rng = np.random.default_rng(42)
    idx = pd.date_range("2021-04-01", periods=500, freq="5min")
    X_dummy = pd.DataFrame(rng.standard_normal((500, 5)), index=idx)
    n_folds = 0
    for fold, (tr, te) in enumerate(split_with_purging(cv, X_dummy, idx, K=12)):
        n_folds += 1
        print(f"  fold {fold}: train={len(tr)} test={len(te)}")
    assert n_folds >= 1, "No folds generated"
    print(f"split smoke OK ({n_folds} folds)")

    # FoldMetrics dataclass smoke
    fm = FoldMetrics(
        case_name="smoke",
        fold_idx=0,
        K=12,
        entropy_lift=0.15,
        tp_precision=0.55,
        direction_accuracy=None,
        sim_pnl_months_positive=9,
        sim_pnl_year_usd=600.0,
        fold_sharpe=1.2,
        n_train=300,
        n_test=100,
        train_start="2021-04-01",
        train_end="2021-04-02",
        test_start="2021-04-02",
        test_end="2021-04-03",
    )
    print(f"FoldMetrics dataclass smoke OK: {fm.case_name}")
    print(f"OUT_BASE: {OUT_BASE}")
    return 0


if __name__ == "__main__":
    sys.exit(_self_check())
