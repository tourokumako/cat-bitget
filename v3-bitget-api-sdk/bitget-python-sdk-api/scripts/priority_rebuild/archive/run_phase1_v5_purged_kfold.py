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

# Phase 1 合格基準 5 指標 (cc_ml_design_spec §1.5.1 v5.1 / 指示書 §4)
PASS_ENTROPY_LIFT = 0.10
PASS_TP_PRECISION = 0.50
PASS_DIRECTION_ACC = 0.55
PASS_SIM_PNL_MONTHS = 8
PASS_SIM_PNL_YEAR_USD = 500.0
PASS_DSR_ZSCORE = 1.0

# v5.1: 8 組合せ評価 (K=12/24/48/96 × LONG/SHORT) + 6+ 組合せ ALL PASS 合格判定
K_DEFAULT_LIST: Tuple[int, ...] = (12, 24, 48, 96)
SIDES_DEFAULT: Tuple[str, ...] = ("LONG", "SHORT")
COMBINATION_PASS_COUNT_REQUIRED = 6  # cc_ml_design_spec §1.5.1 v5.1: 8 組合せ中 6 以上で ALL PASS

# train/valid 乖離 warning 閾値 (指示書 §4.2 W1/W2)
WARN_TRAIN_RMSE_LABEL_STD_RATIO = 0.10  # train_rmse / label_std < 0.10 で leak 疑い
WARN_VALID_TRAIN_RATIO = 3.0  # valid_rmse > train_rmse * 3.0 で overfit/leak 疑い


@dataclass
class FoldMetrics:
    """fold 単位の 4 指標 + 警告 (DSR は aggregate で算出するためここには含めない・v5.1 拡張)."""

    case_name: str
    fold_idx: int
    K: int
    side: str  # v5.1: "LONG" / "SHORT"
    entropy_lift: float
    tp_precision: float  # 正解 = triple_barrier_label_{LONG,SHORT}_K{K} == +1
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
    # v5.1: train/valid RMSE + label_std (W1/W2 警告計算用・regression のみ)
    train_rmse: Optional[float] = None
    valid_rmse: Optional[float] = None
    label_std: Optional[float] = None
    warnings: List[str] = field(default_factory=list)
    extra: Dict[str, float] = field(default_factory=dict)


@dataclass
class CombinationSummary:
    """1 組合せ (K × side) 内の 5 fold 統合 + 組合せ単位 pass 判定."""

    case_name: str
    K: int
    side: str
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
    pass_per_metric: Dict[str, bool]
    all_pass: bool
    warnings: List[str] = field(default_factory=list)


@dataclass
class CaseSummary:
    """8 組合せ統合 + §4.1 v5.1 合格判定 (6+ 組合せ ALL PASS)."""

    case_name: str
    n_combinations: int  # 通常 8 (K=4 × side=2)
    combinations: Dict[str, Dict] = field(default_factory=dict)  # key: "K12_LONG" 等
    n_combinations_all_pass: int = 0
    all_pass_combinations: List[str] = field(default_factory=list)
    meets_6plus_criteria: bool = False  # 6 組合せ以上で ALL PASS なら合格
    dsr_n_trials: int = 6  # Phase 1 v5.1 は 6 案並列 (Phase 4-b-2 で grid 拡張時に更新)
    layer3_investigation_needed: bool = True


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
    """naive simulated PnL (旧式・Step H まで使用・Step I 以降は v2 推奨).

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


# Step I-2.3 改修: Phase 4-b 仕様の最小スコープ部分を Phase 1 評価式に前倒し
# 仕様書 v2.1 §7.1 参照
# Step G CP2 監査 C2 反映 + CP3.5 監査 C1/C2 反映
DEFAULT_COST_PER_TRADE = 0.00033  # = 往復 maker fee 0.00028 + 暫定 slippage 0.00005
DEFAULT_POSITION_SIZE_BTC = 0.024
DEFAULT_BTC_PRICE_AVG = 50000.0
VALID_METHODS_V2: Tuple[str, ...] = ("fixed_tp", "time_exit")


def compute_simulated_pnl_v2(
    tp_hit_prob: pd.Series,
    tp_pct: float,
    sl_pct: float,
    time_exit_return_median: float,
    method: str,
    pred_MFE: Optional[pd.Series] = None,
    cost_per_trade: float = DEFAULT_COST_PER_TRADE,
    position_size_btc: float = DEFAULT_POSITION_SIZE_BTC,
    btc_price_avg: float = DEFAULT_BTC_PRICE_AVG,
) -> Tuple[int, float, Dict[str, float]]:
    """Phase 4-b 前倒し簡易評価式 (仕様書 v2.1 §7.1・統計式近似・bar-level 不使用).

    旧式 (compute_simulated_pnl) との差分:
    - TP 約定率を 100% 想定 → tp_hit_prob (Classifier 出力 0-1) で重み付け
    - TP 価格を pred_MFE 由来 → 固定 TP_PCT (定数) に変更 (3 重楽観仮定 (1)(3) を物理的に解消)
    - method 別計算 (fixed_tp / time_exit) で 2 並列評価可能

    Args:
        tp_hit_prob: §2 Classifier 出力 (Series・index=trade timestamp・値=0-1 確率)
        tp_pct: §3 固定 TP_PCT (% 単位・例: 0.5 = 0.5%)
        sl_pct: §3 固定 SL_pct (% 単位・例: 0.5)
        time_exit_return_median: §5 train 期間 median (% 単位・artifact からロード)
        method: "fixed_tp" or "time_exit"
        pred_MFE: 未使用 (PnL 計算には流入しない・Classifier 特徴量にのみ使用・引数として残置・診断目的)
        cost_per_trade: 往復 fee + slippage (0.00033 = 0.033%)
        position_size_btc: per-position サイズ (0.024 = 0.024 BTC = 0.12/5 暫定)
        btc_price_avg: BTC 平均価格 (= position_usd 換算用・50000)

    Returns:
        months_positive: トレードがあった月のうちプラス月数
        year_usd: 年間 NET ($)
        diagnostics: 計算詳細 (mean return / cost / method 等)
    """
    if method not in VALID_METHODS_V2:
        raise ValueError(
            f"method must be one of {VALID_METHODS_V2}, got: {method}"
        )
    if tp_hit_prob.empty:
        return 0, 0.0, {
            "method": method,
            "n_trades": 0,
            "mean_return": 0.0,
            "cost_per_trade": cost_per_trade,
            "tp_pct": tp_pct,
            "sl_pct": sl_pct,
            "time_exit_return_median": time_exit_return_median,
        }
    if not isinstance(tp_hit_prob.index, pd.DatetimeIndex):
        raise TypeError("tp_hit_prob.index must be DatetimeIndex")

    # 各 method の return per trade (decimal ratio・pct/100)
    if method == "fixed_tp":
        # 期待値式: E[return] = p × TP - (1-p) × SL - cost
        # TP_PCT / SL_pct は事前固定定数 (pred_MFE 由来なし・3 重楽観 (1)(3) 解消)
        # M2: tp_pct 必須 (対称ガード・dummy 0.0 渡し検出・L-181 設計転換時旧経路混入防止)
        if tp_pct is None or tp_pct <= 0.0:
            raise ValueError(
                "fixed_tp method requires positive tp_pct (M2 対称ガード)"
            )
        returns_per_trade = (
            tp_hit_prob * (tp_pct / 100.0)
            - (1.0 - tp_hit_prob) * (sl_pct / 100.0)
            - cost_per_trade
        )
    elif method == "time_exit":
        # Critical-1 修正 (L-212c): 旧式 (定数 broadcast) は naive baseline で fold 内分散ゼロ
        # 新式 E[return] = p × TP_PCT + (1-p) × time_exit_median - cost (予測装置化)
        # tp_hit_prob[i] が線形係数 (TP_PCT - time_exit_median)/100 で returns に伝播
        # M2: tp_pct 必須 (dummy 0.0 渡し禁止)
        if tp_pct is None or tp_pct <= 0.0:
            raise ValueError(
                "time_exit method requires positive tp_pct "
                "(Critical-1 修正・L-212c 予測装置化)"
            )
        # C2: TP_PCT ≒ median 重複ガード (naive baseline 再演グリッド除外・safety net)
        # 現実には Step I-3.2 実測 median ≦ 0.03% で発動しない想定
        if abs((tp_pct / 100.0) - (time_exit_return_median / 100.0)) < 5e-4:
            raise ValueError(
                f"time_exit naive baseline 再演リスク: "
                f"|tp_pct - time_exit_return_median| = "
                f"{abs(tp_pct - time_exit_return_median):.4f}% < 0.05% "
                f"(C2 ガード)"
            )
        returns_per_trade = (
            tp_hit_prob * (tp_pct / 100.0)
            + (1.0 - tp_hit_prob) * (time_exit_return_median / 100.0)
            - cost_per_trade
        )
        returns_per_trade.name = f"return_v2_{method}"
    # 月次集計
    monthly = returns_per_trade.groupby(
        returns_per_trade.index.to_period("M")
    ).sum()
    months_positive = int((monthly > 0).sum())
    position_usd = position_size_btc * btc_price_avg
    year_usd = float(returns_per_trade.sum() * position_usd)

    diagnostics: Dict[str, float] = {
        "n_trades": int(len(returns_per_trade)),
        "mean_return": float(returns_per_trade.mean()),
        "std_return": float(returns_per_trade.std()) if len(returns_per_trade) > 1 else 0.0,
        "tp_hit_prob_mean": float(tp_hit_prob.mean()),
        "tp_hit_prob_std": float(tp_hit_prob.std()) if len(tp_hit_prob) > 1 else 0.0,
        "tp_pct": tp_pct,
        "sl_pct": sl_pct,
        "time_exit_return_median": time_exit_return_median,
        "cost_per_trade": cost_per_trade,
        "position_size_btc": position_size_btc,
        "btc_price_avg": btc_price_avg,
        # method はファイル末尾に str で配置するため別途
    }
    # method を str として diagnostics に追加 (Dict[str, float] 型違反だが返却用)
    diagnostics_with_method: Dict[str, object] = dict(diagnostics)
    diagnostics_with_method["method"] = method
    return months_positive, year_usd, diagnostics_with_method  # type: ignore[return-value]


def compute_fold_metrics(
    case_name: str,
    fold_idx: int,
    K: int,
    side: str,
    y_true_tp_first: np.ndarray,
    y_pred_tp_first: np.ndarray,
    y_prob: Optional[np.ndarray],
    num_classes: int,
    returns_per_trade: pd.Series,
    train_range: Tuple[pd.Timestamp, pd.Timestamp],
    test_range: Tuple[pd.Timestamp, pd.Timestamp],
    n_train: int,
    n_test: int,
    direction_y_true: Optional[np.ndarray] = None,
    direction_y_pred: Optional[np.ndarray] = None,
    train_rmse: Optional[float] = None,
    valid_rmse: Optional[float] = None,
    label_std: Optional[float] = None,
    extra: Optional[Dict[str, float]] = None,
) -> FoldMetrics:
    """fold 単位の 4 指標 + Sharpe + W1/W2 警告を計算 (DSR は aggregate で・v5.1).

    Args:
        side: "LONG" / "SHORT" (v5.1 で 8 組合せ評価対応)
        y_true_tp_first: TP first 正解 (triple_barrier_label_{side}_K{K} == +1 を 0/1 化)
        y_pred_tp_first: case 別 0/1 化済 (caller responsibility):
            - 案 a: (予測 MFE / |予測 MAE|) >= 1.5
            - 案 b: predict_proba > 0.5
            - 案 c: LONG class prob > 0.4 (LONG 側) / SHORT class prob > 0.4 (SHORT 側)
            - 案 d: 予測強度 top 10%
            - 案 e: +1 class prob > 0.4
            - 案 f: Primary +1 ∧ Secondary > 0.6
        y_prob: entropy_lift 計算用 (regression は None → entropy_lift=NaN)
        num_classes: entropy_lift 計算用 (regression は 0 or 1)
        direction_y_true/direction_y_pred: 案 c のみ・multiclass 3-way 正解と予測
        train_rmse/valid_rmse/label_std: W1/W2 警告計算用 (regression のみ)
    """
    warnings: List[str] = []

    # 1. entropy lift
    if y_prob is not None and num_classes >= 2:
        e_lift = compute_entropy_lift(y_true_tp_first.astype(int), y_prob, num_classes)
    else:
        e_lift = float("nan")

    # 2. TP Precision (TP first 正解 vs case 別 0/1 化予測・全案統一)
    if len(y_pred_tp_first) == 0 or int(np.sum(y_pred_tp_first)) == 0:
        tp_p = 0.0
    else:
        tp_p = float(
            precision_score(
                y_true_tp_first.astype(int),
                y_pred_tp_first.astype(int),
                zero_division=0.0,
            )
        )

    # 3. Direction Accuracy (案 c のみ・別 array で渡される)
    if direction_y_true is not None and direction_y_pred is not None:
        direction_acc = float(accuracy_score(direction_y_true, direction_y_pred))
    else:
        direction_acc = None

    # 4. Simulated PnL
    months_pos, year_usd = compute_simulated_pnl(returns_per_trade)

    # fold Sharpe (DSR 入力用)
    if not returns_per_trade.empty and len(returns_per_trade) >= 2:
        fold_sharpe = float(sharpe_ratio(returns_per_trade.values))
    else:
        fold_sharpe = float("nan")

    # W1/W2 警告検出 (指示書 §4.2)
    if (
        train_rmse is not None
        and label_std is not None
        and label_std > 0
    ):
        ratio_w1 = train_rmse / label_std
        if ratio_w1 < WARN_TRAIN_RMSE_LABEL_STD_RATIO:
            warnings.append(
                f"W1: train_rmse/label_std = {ratio_w1:.4f} < "
                f"{WARN_TRAIN_RMSE_LABEL_STD_RATIO} (leak suspicion・L-179 fractal 教訓)"
            )
    if (
        train_rmse is not None
        and valid_rmse is not None
        and train_rmse > 0
    ):
        ratio_w2 = valid_rmse / train_rmse
        if ratio_w2 > WARN_VALID_TRAIN_RATIO:
            warnings.append(
                f"W2: valid_rmse/train_rmse = {ratio_w2:.2f} > "
                f"{WARN_VALID_TRAIN_RATIO} (overfit/leak suspicion)"
            )

    return FoldMetrics(
        case_name=case_name,
        fold_idx=fold_idx,
        K=K,
        side=side,
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
        train_rmse=train_rmse,
        valid_rmse=valid_rmse,
        label_std=label_std,
        warnings=warnings,
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


def _mean_clean(values: Iterable[float]) -> float:
    """NaN / None を除いた平均."""
    clean = [
        v for v in values
        if v is not None and not (isinstance(v, float) and np.isnan(v))
    ]
    return float(np.mean(clean)) if clean else float("nan")


def aggregate_combination_to_summary(
    case_name: str,
    K: int,
    side: str,
    fold_metrics: List[FoldMetrics],
    returns_all_folds: pd.Series,
    n_trials: int,
) -> CombinationSummary:
    """1 組合せ (K × side) の 5 fold 統合 + DSR + 組合せ単位 pass 判定 (v5.1).

    Args:
        fold_metrics: この組合せ内の 5 fold 分の FoldMetrics
        returns_all_folds: 同組合せの 5 fold 統合 trade returns
        n_trials: DSR selection bias 補正用 (case 単位で全組合せ共通)
    """
    if not fold_metrics:
        raise ValueError(f"fold_metrics empty for case={case_name} K={K} side={side}")

    e_lift_mean = _mean_clean(m.entropy_lift for m in fold_metrics)
    tp_p_mean = _mean_clean(m.tp_precision for m in fold_metrics)
    direction_vals = [m.direction_accuracy for m in fold_metrics
                      if m.direction_accuracy is not None]
    direction_mean = _mean_clean(direction_vals) if direction_vals else None
    months_mean = _mean_clean(m.sim_pnl_months_positive for m in fold_metrics)
    year_usd_mean = _mean_clean(m.sim_pnl_year_usd for m in fold_metrics)
    fold_sharpe_mean = _mean_clean(m.fold_sharpe for m in fold_metrics)

    valid_sharpes = [m.fold_sharpe for m in fold_metrics if not np.isnan(m.fold_sharpe)]
    fold_sharpe_var = (
        float(np.var(valid_sharpes, ddof=1)) if len(valid_sharpes) >= 2 else float("nan")
    )

    # DSR (組合せ単位・5 fold 統合 returns + fold-Sharpe variance を sr_variance に)
    if (
        not returns_all_folds.empty
        and len(returns_all_folds) >= 30
        and not np.isnan(fold_sharpe_var)
        and fold_sharpe_var > 0
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

    # 組合せ単位 5 指標 pass 判定
    passes = {
        "entropy_lift": bool(
            np.isnan(e_lift_mean) or e_lift_mean > PASS_ENTROPY_LIFT
        ),  # regression (NaN) は entropy_lift 適用外として PASS 扱い
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

    # 全 fold の警告を収集 (組合せ単位)
    all_warnings = [w for m in fold_metrics for w in m.warnings]

    return CombinationSummary(
        case_name=case_name,
        K=K,
        side=side,
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
        pass_per_metric=passes,
        all_pass=all_pass,
        warnings=all_warnings,
    )


def aggregate_8_combinations_to_summary(
    case_name: str,
    combination_results: Dict[Tuple[int, str], Tuple[List[FoldMetrics], pd.Series]],
    n_trials: int = 6,
    out_base: Path = OUT_BASE,
) -> CaseSummary:
    """8 組合せ統合 + §4.1 v5.1 合格判定 (6+ 組合せ ALL PASS) → phase1_v5_summary.json 追記.

    Args:
        combination_results: dict[(K, side)] -> (fold_metrics_list, returns_series)
            通常 K=12/24/48/96 × side="LONG"/"SHORT" = 8 組合せ
        n_trials: DSR selection bias 補正用 (Phase 1 v5.1 = 6 案・Phase 4-b-2 で拡張)
        out_base: 出力先 (phase1_v5_summary.json 配置)

    cc_ml_design_spec §1.5.1 v5.1 合格判定:
    - 8 組合せ中 COMBINATION_PASS_COUNT_REQUIRED (6) 以上で 5 指標 ALL PASS → 採用案
    - 6 未満 → Layer 3 投入判定
    """
    if not combination_results:
        raise ValueError(f"combination_results empty for case={case_name}")

    combinations_dict: Dict[str, Dict] = {}
    all_pass_combos: List[str] = []
    n_all_pass = 0

    for (K, side), (fold_metrics, returns_series) in combination_results.items():
        combo_key = f"K{K}_{side}"
        combo_summary = aggregate_combination_to_summary(
            case_name=case_name,
            K=K,
            side=side,
            fold_metrics=fold_metrics,
            returns_all_folds=returns_series,
            n_trials=n_trials,
        )
        combinations_dict[combo_key] = {
            "summary": asdict(combo_summary),
            "fold_metrics": [asdict(m) for m in fold_metrics],
        }
        if combo_summary.all_pass:
            n_all_pass += 1
            all_pass_combos.append(combo_key)

    meets_criteria = n_all_pass >= COMBINATION_PASS_COUNT_REQUIRED

    case_summary = CaseSummary(
        case_name=case_name,
        n_combinations=len(combination_results),
        combinations=combinations_dict,
        n_combinations_all_pass=n_all_pass,
        all_pass_combinations=all_pass_combos,
        meets_6plus_criteria=meets_criteria,
        dsr_n_trials=n_trials,
        layer3_investigation_needed=not meets_criteria,
    )

    # phase1_v5_summary.json 追記
    out_base.mkdir(parents=True, exist_ok=True)
    summary_path = out_base / "phase1_v5_summary.json"
    if summary_path.exists():
        full = json.loads(summary_path.read_text(encoding="utf-8"))
    else:
        full = {"cases": {}, "meta": {
            "spec_version": "v5.1",
            "combination_pass_count_required": COMBINATION_PASS_COUNT_REQUIRED,
            "K_default_list": list(K_DEFAULT_LIST),
            "sides_default": list(SIDES_DEFAULT),
        }}
    full["cases"][case_name] = asdict(case_summary)
    full["updated_at"] = pd.Timestamp.now().isoformat()
    summary_path.write_text(
        json.dumps(full, indent=2, default=str), encoding="utf-8"
    )

    return case_summary


def _self_check() -> int:
    """import smoke + 簡易 API verify (v5.1 対応・CI 不要・stand-alone 動作確認)."""
    print("=== run_phase1_v5_purged_kfold.py self_check (v5.1) ===")
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

    # v5.1 compute_fold_metrics smoke (regression case_a 想定)
    y_true_tb = rng.integers(0, 2, size=100).astype(int)  # triple_barrier 正解
    y_pred_tp = rng.integers(0, 2, size=100).astype(int)  # case 別 0/1 化済
    returns_dummy = pd.Series(
        rng.normal(0.005, 0.02, size=50),
        index=pd.date_range("2021-04-02", periods=50, freq="6h"),
    )
    fm = compute_fold_metrics(
        case_name="smoke_a",
        fold_idx=0,
        K=12,
        side="LONG",
        y_true_tp_first=y_true_tb,
        y_pred_tp_first=y_pred_tp,
        y_prob=None,
        num_classes=0,
        returns_per_trade=returns_dummy,
        train_range=(idx[0], idx[399]),
        test_range=(idx[400], idx[499]),
        n_train=400,
        n_test=100,
        train_rmse=0.5,
        valid_rmse=0.6,
        label_std=2.0,  # ratio_w1 = 0.5/2.0 = 0.25 > 0.10 → W1 出ない
    )
    print(f"FoldMetrics v5.1 smoke OK: case={fm.case_name} K={fm.K} side={fm.side} "
          f"tp_precision={fm.tp_precision:.3f} warnings={fm.warnings}")

    # W1 警告検出 smoke (train_rmse 異常低)
    fm_w1 = compute_fold_metrics(
        case_name="smoke_w1",
        fold_idx=0,
        K=12,
        side="LONG",
        y_true_tp_first=y_true_tb,
        y_pred_tp_first=y_pred_tp,
        y_prob=None,
        num_classes=0,
        returns_per_trade=returns_dummy,
        train_range=(idx[0], idx[399]),
        test_range=(idx[400], idx[499]),
        n_train=400,
        n_test=100,
        train_rmse=0.05,  # ratio_w1 = 0.05/2.0 = 0.025 < 0.10 → W1 出る
        valid_rmse=0.20,  # ratio_w2 = 0.20/0.05 = 4.0 > 3.0 → W2 も出る
        label_std=2.0,
    )
    assert any("W1" in w for w in fm_w1.warnings), "W1 not triggered"
    assert any("W2" in w for w in fm_w1.warnings), "W2 not triggered"
    print(f"W1/W2 warning smoke OK: {fm_w1.warnings}")

    # aggregate_8_combinations_to_summary smoke (2 組合せ・実 IO 副作用なし)
    fm_combo_a = [
        FoldMetrics(
            case_name="smoke_agg", fold_idx=i, K=12, side="LONG",
            entropy_lift=float("nan"), tp_precision=0.55,
            direction_accuracy=None, sim_pnl_months_positive=10,
            sim_pnl_year_usd=600.0, fold_sharpe=1.5,
            n_train=300, n_test=100,
            train_start=str(idx[0]), train_end=str(idx[399]),
            test_start=str(idx[400]), test_end=str(idx[499]),
        )
        for i in range(5)
    ]
    fm_combo_b = [
        FoldMetrics(
            case_name="smoke_agg", fold_idx=i, K=24, side="SHORT",
            entropy_lift=float("nan"), tp_precision=0.30,  # FAIL (< 0.50)
            direction_accuracy=None, sim_pnl_months_positive=10,
            sim_pnl_year_usd=600.0, fold_sharpe=1.5,
            n_train=300, n_test=100,
            train_start=str(idx[0]), train_end=str(idx[399]),
            test_start=str(idx[400]), test_end=str(idx[499]),
        )
        for i in range(5)
    ]
    returns_a = pd.Series(
        rng.normal(0.005, 0.02, size=60),
        index=pd.date_range("2021-04-02", periods=60, freq="6h"),
    )
    returns_b = pd.Series(
        rng.normal(0.005, 0.02, size=60),
        index=pd.date_range("2021-04-02", periods=60, freq="6h"),
    )
    # 実 IO 回避: 一時 out_base で実行
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        case_summary = aggregate_8_combinations_to_summary(
            case_name="smoke_agg",
            combination_results={
                (12, "LONG"): (fm_combo_a, returns_a),
                (24, "SHORT"): (fm_combo_b, returns_b),
            },
            n_trials=6,
            out_base=Path(tmp),
        )
    print(
        f"aggregate smoke OK: n_combinations={case_summary.n_combinations} "
        f"n_all_pass={case_summary.n_combinations_all_pass} "
        f"meets_6plus={case_summary.meets_6plus_criteria}"
    )
    assert case_summary.n_combinations == 2
    assert case_summary.meets_6plus_criteria is False  # 2 組合せのみ・6 未満

    print(f"OUT_BASE: {OUT_BASE}")
    print("=== self_check PASS ===")
    return 0


if __name__ == "__main__":
    sys.exit(_self_check())
