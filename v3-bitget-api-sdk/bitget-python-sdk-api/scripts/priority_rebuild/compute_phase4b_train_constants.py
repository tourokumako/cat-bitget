"""
compute_phase4b_train_constants.py — Phase 4-b 前倒し設計 Step I-2.2 (time_exit_return_median artifact 生成)

Step I-1 仕様書 v2.1 (`.claude/instructions/2026-05-23_phase4b_forward_design_spec.md`) の
§5 time exit 暫定モデル実装。train 期間 (2021-04〜2024-12) のみで time_exit_return_median
定数を算出し、artifact JSON として保存する。本番推論時は artifact 経由で定数を読み込むのみ
(t+N bar の close を推論時に参照しない).

設計判断 (cc_role §1.5):
- N bar grid: (K//2, K) のみ・K×2 禁止 (phase_compliance §4b.3)
- 算定式: time_exit_return = (close[i+N] - close[i]) / close[i] × 100 (LONG・SHORT は符号反転)
  - 仕様書 §5.3 の entry は close[i] ± 0.005% slippage を持つが、parquet に open 不在 + 暫定段階で
    slippage 0.005% << median 値で無視 (Phase 4-b-1 本確定で bar-level シミュレーションで再考)
- 集約: median (mean ではなく・regime ロバスト化・§5.3 改訂)
- 月別歪度 verify: |skew| < 1.0 (§5.6・超過時 warning ログ)
- artifact 名: time_exit_return_median_train_2021_2024_K{K}_{side}_N{N}.json (phase_compliance §4a.4 整合)

CLI:
- --smoke: sample.parquet / K=12 LONG / N=(6, 12)
- --full: train_2021_2024.parquet / K=(12,24,48,96) / LONG/SHORT / N=(K//2, K) = 16 artifact
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
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_phase1_v5_purged_kfold import (  # noqa: E402
    K_DEFAULT_LIST,
    OUT_BASE,
    PARQUET_DIR,
    SIDES_DEFAULT,
)

# 仕様書 §5.2 N bar grid
N_RATIOS: Tuple[float, ...] = (0.5, 1.0)  # K//2, K のみ (K×2 禁止)

# 仕様書 §5.6 月別歪度 verify 閾値
SKEW_WARN_THRESHOLD = 1.0

OUT_CONSTANTS_BASE = OUT_BASE / "_phase4b_train_constants"


@dataclass
class TimeExitConstantSummary:
    """1 組合せ (K, side, N) の time_exit_return_median artifact 内容."""

    K: int
    side: str
    N: int
    median_pct: float            # train 期間全体 median
    mean_pct: float              # 参考値 (regime 過依存リスク確認用)
    std_pct: float               # 標準偏差
    p05_pct: float
    p25_pct: float
    p75_pct: float
    p95_pct: float
    n_trades: int                # 有効 trade 数 (i+N が範囲内)
    overall_skew: float          # 全体歪度
    monthly_skew: Dict[str, float] = field(default_factory=dict)  # 月別 (YYYY-MM): skew
    monthly_median: Dict[str, float] = field(default_factory=dict)
    monthly_n: Dict[str, int] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    train_start: str = ""
    train_end: str = ""


def _validate_parquet_path(parquet_path: Path) -> Tuple[bool, str]:
    """§8.4 (v) 起動時 assertion: artifact_path 経由で leak verify.

    smoke (sample) は skip / full (train_2021_2024) は厳格 verify.
    """
    parquet_path = Path(parquet_path)
    is_smoke = "sample" in parquet_path.name
    is_full = "train_2021_2024" in parquet_path.name
    if "test" in parquet_path.name and not is_full:
        return False, f"§8.4 (v) leak verify: parquet must not be test*: {parquet_path.name}"
    if not is_smoke and not is_full:
        return False, (
            f"§8.4 (v) leak verify: parquet path must contain 'train_2021_2024' or 'sample': "
            f"{parquet_path.name}"
        )
    return True, ""


def compute_time_exit_return_series(
    close: pd.Series,
    K: int,
    side: str,
    N: int,
) -> pd.Series:
    """time_exit_return = (close[i+N] - close[i]) / close[i] × 100 (LONG・SHORT 符号反転).

    Args:
        close: 5min close 価格 (Series・index=timestamp・全長)
        K: K 値 (label 期間・barrier・本関数では未使用だが artifact 整合性のため引数)
        side: "LONG" or "SHORT"
        N: time exit bar 数 (K//2 or K)

    Returns:
        time_exit_return: Series (index=trade timestamp i・末尾 N 行は NaN)
    """
    if N <= 0:
        raise ValueError(f"N must be positive: {N}")
    if side not in ("LONG", "SHORT"):
        raise ValueError(f"side must be LONG/SHORT: {side}")

    # close[i+N] - close[i] / close[i]
    close_shift = close.shift(-N)  # i 番目に i+N の close が来る
    pct_change = (close_shift - close) / close * 100.0
    if side == "SHORT":
        pct_change = -pct_change  # SHORT は逆方向で利益
    return pct_change.rename(f"time_exit_return_pct_K{K}_{side}_N{N}")


def compute_monthly_skew(returns: pd.Series) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, int]]:
    """月別 skew + median + 件数を返す.

    Args:
        returns: time exit return pct (NaN を含む可能性あり・index=DatetimeIndex)

    Returns:
        (monthly_skew, monthly_median, monthly_n)
    """
    if not isinstance(returns.index, pd.DatetimeIndex):
        raise TypeError("returns.index must be DatetimeIndex")
    monthly_skew: Dict[str, float] = {}
    monthly_median: Dict[str, float] = {}
    monthly_n: Dict[str, int] = {}
    # nan を除外
    returns_clean = returns.dropna()
    monthly_groups = returns_clean.groupby(returns_clean.index.to_period("M"))
    for period, group in monthly_groups:
        ym = str(period)
        n = len(group)
        if n < 5:
            # 件数少なすぎる月は skew 計算しない
            monthly_skew[ym] = float("nan")
        else:
            try:
                sk = float(stats.skew(group.values, bias=False, nan_policy="omit"))
                monthly_skew[ym] = sk
            except Exception:
                monthly_skew[ym] = float("nan")
        monthly_median[ym] = float(group.median())
        monthly_n[ym] = int(n)
    return monthly_skew, monthly_median, monthly_n


def compute_one_combination(
    close: pd.Series,
    K: int,
    side: str,
    N: int,
    train_start: pd.Timestamp,
    train_end: pd.Timestamp,
) -> TimeExitConstantSummary:
    """1 組合せ (K, side, N) の time_exit_return_median 算出 + 月別歪度 verify."""
    returns = compute_time_exit_return_series(close, K, side, N)
    # train 期間 filter
    mask = (returns.index >= train_start) & (returns.index <= train_end)
    returns_train = returns[mask].dropna()

    if returns_train.empty:
        raise ValueError(
            f"No valid train returns for K={K} side={side} N={N} "
            f"in [{train_start}, {train_end}]"
        )

    median_pct = float(returns_train.median())
    mean_pct = float(returns_train.mean())
    std_pct = float(returns_train.std())
    p05 = float(returns_train.quantile(0.05))
    p25 = float(returns_train.quantile(0.25))
    p75 = float(returns_train.quantile(0.75))
    p95 = float(returns_train.quantile(0.95))
    overall_skew = float(stats.skew(returns_train.values, bias=False, nan_policy="omit"))

    monthly_skew, monthly_median, monthly_n = compute_monthly_skew(returns_train)

    # §5.6 月別歪度 verify (|skew| > 1.0 検出時 warning)
    warnings_list: List[str] = []
    extreme_months = [
        ym
        for ym, sk in monthly_skew.items()
        if not np.isnan(sk) and abs(sk) > SKEW_WARN_THRESHOLD
    ]
    if extreme_months:
        warnings_list.append(
            f"§5.6 月別歪度 |skew| > {SKEW_WARN_THRESHOLD} 超過: "
            f"{len(extreme_months)}/{len(monthly_skew)} 月 — "
            f"first 5: {extreme_months[:5]}"
        )

    if abs(overall_skew) > SKEW_WARN_THRESHOLD:
        warnings_list.append(
            f"overall_skew |{overall_skew:.3f}| > {SKEW_WARN_THRESHOLD} — "
            f"regime 過依存 (類型 D) リスク要確認"
        )

    return TimeExitConstantSummary(
        K=K,
        side=side,
        N=N,
        median_pct=median_pct,
        mean_pct=mean_pct,
        std_pct=std_pct,
        p05_pct=p05,
        p25_pct=p25,
        p75_pct=p75,
        p95_pct=p95,
        n_trades=len(returns_train),
        overall_skew=overall_skew,
        monthly_skew=monthly_skew,
        monthly_median=monthly_median,
        monthly_n=monthly_n,
        warnings=warnings_list,
        train_start=str(train_start),
        train_end=str(train_end),
    )


def save_artifact(
    summary: TimeExitConstantSummary,
    out_dir: Path,
    parquet_suffix: str = "train_2021_2024",
) -> Path:
    """artifact JSON 保存.

    artifact 名: time_exit_return_median_{suffix}_K{K}_{side}_N{N}.json
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = (
        f"time_exit_return_median_{parquet_suffix}_"
        f"K{summary.K}_{summary.side}_N{summary.N}.json"
    )
    fpath = out_dir / fname
    with open(fpath, "w") as f:
        json.dump(asdict(summary), f, indent=2, default=str)
    return fpath


def compute_all_constants(
    parquet_path: Path,
    k_values: Tuple[int, ...] = K_DEFAULT_LIST,
    sides: Tuple[str, ...] = SIDES_DEFAULT,
    n_ratios: Tuple[float, ...] = N_RATIOS,
    train_start: Optional[str] = None,
    train_end: Optional[str] = None,
    out_base: Path = OUT_CONSTANTS_BASE,
) -> List[Path]:
    """全組合せ (K × side × N) で time_exit_return_median artifact 生成."""
    parquet_path = Path(parquet_path)
    # §8.4 (v) 起動時 assertion
    ok, err = _validate_parquet_path(parquet_path)
    if not ok:
        raise AssertionError(err)

    print(f"\n=== Phase 4-b time_exit_return_median artifact 生成開始 (Step I-2.2) ===")
    print(f"parquet: {parquet_path}")
    print(f"K values: {k_values} / sides: {sides} / N ratios: {n_ratios}")
    print(f"out_base: {out_base}")

    # parquet load (close 列のみ必要)
    df = pd.read_parquet(parquet_path, columns=["close"])
    if "close" not in df.columns:
        raise KeyError(f"'close' column not found in parquet: {parquet_path}")
    print(f"[load] parquet shape: {df.shape}")
    print(f"[load] index range: {df.index[0]} ~ {df.index[-1]}")

    # train 期間 (smoke: 全期間 / full: 2021-04 〜 2024-12)
    is_smoke = "sample" in parquet_path.name
    if train_start is None:
        ts_start = df.index[0]
    else:
        ts_start = pd.Timestamp(train_start)
    if train_end is None:
        if is_smoke:
            ts_end = df.index[-1]
        else:
            ts_end = pd.Timestamp("2024-12-31 23:55:00")
    else:
        ts_end = pd.Timestamp(train_end)

    print(f"train period: {ts_start} ~ {ts_end}")

    close = df["close"]
    parquet_suffix = "train_2021_2024" if "train_2021_2024" in parquet_path.name else (
        "sample" if is_smoke else parquet_path.name.replace(".parquet", "")
    )

    saved_files: List[Path] = []
    overall_summaries: List[TimeExitConstantSummary] = []

    for K in k_values:
        for side in sides:
            for ratio in n_ratios:
                N = max(1, int(K * ratio))
                print(f"\n--- K={K} side={side} N={N} (ratio={ratio}) ---")
                try:
                    summary = compute_one_combination(
                        close=close,
                        K=K,
                        side=side,
                        N=N,
                        train_start=ts_start,
                        train_end=ts_end,
                    )
                except ValueError as e:
                    print(f"[ERROR] {e}", file=sys.stderr)
                    continue
                fpath = save_artifact(summary, out_base, parquet_suffix)
                print(
                    f"  median_pct={summary.median_pct:+.4f}% "
                    f"mean_pct={summary.mean_pct:+.4f}% "
                    f"std_pct={summary.std_pct:.4f}% "
                    f"overall_skew={summary.overall_skew:+.3f}"
                )
                print(
                    f"  p05={summary.p05_pct:+.4f}% p25={summary.p25_pct:+.4f}% "
                    f"p75={summary.p75_pct:+.4f}% p95={summary.p95_pct:+.4f}%"
                )
                print(
                    f"  n_trades={summary.n_trades} months={len(summary.monthly_median)}"
                )
                if summary.warnings:
                    print(f"  ⚠️  warnings ({len(summary.warnings)}):")
                    for w in summary.warnings:
                        print(f"    - {w}")
                print(f"  [save] {fpath}")
                saved_files.append(fpath)
                overall_summaries.append(summary)

    # 統合 index ファイル
    index_path = out_base / f"time_exit_return_median_INDEX_{parquet_suffix}.json"
    index_data = {
        "case_name": "phase4b_time_exit_constants",
        "parquet": parquet_path.name,
        "k_values": list(k_values),
        "sides": list(sides),
        "n_ratios": list(n_ratios),
        "train_start": str(ts_start),
        "train_end": str(ts_end),
        "timestamp": datetime.now().isoformat(),
        "artifacts": [str(p.name) for p in saved_files],
        "median_pct_matrix": {
            f"K{s.K}_{s.side}_N{s.N}": s.median_pct for s in overall_summaries
        },
        "overall_skew_matrix": {
            f"K{s.K}_{s.side}_N{s.N}": s.overall_skew for s in overall_summaries
        },
        "n_trades_matrix": {
            f"K{s.K}_{s.side}_N{s.N}": s.n_trades for s in overall_summaries
        },
        "n_warnings_total": sum(len(s.warnings) for s in overall_summaries),
    }
    with open(index_path, "w") as f:
        json.dump(index_data, f, indent=2, default=str)
    print(f"\n[save] INDEX: {index_path}")

    print(f"\n=== artifact 生成完了 ===")
    print(f"  saved: {len(saved_files)} files")
    print(f"  warnings total: {index_data['n_warnings_total']}")

    return saved_files


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Step I-2.2: Phase 4-b time_exit_return_median artifact 生成"
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="smoke: sample.parquet / K=12 LONG / N=(6, 12)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="full: train_2021_2024.parquet / K=(12,24,48,96) / LONG/SHORT / N=(K//2, K) = 16 artifact",
    )
    parser.add_argument("--parquet", type=Path, default=None)
    parser.add_argument("--k", type=int, nargs="+", default=None)
    parser.add_argument("--side", type=str, nargs="+", default=None, choices=["LONG", "SHORT"])
    parser.add_argument(
        "--n-ratios",
        type=float,
        nargs="+",
        default=None,
        help="N ratios (例: --n-ratios 0.5 1.0 で K//2 + K)",
    )
    parser.add_argument("--train-start", type=str, default=None)
    parser.add_argument("--train-end", type=str, default=None)
    parser.add_argument("--out-base", type=Path, default=OUT_CONSTANTS_BASE)
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

    if not parquet_path.exists():
        print(f"[ERROR] parquet not found: {parquet_path}", file=sys.stderr)
        return 2

    if args.smoke:
        k_values = tuple(args.k) if args.k else (12,)
        sides = tuple(args.side) if args.side else ("LONG",)
        n_ratios = tuple(args.n_ratios) if args.n_ratios else N_RATIOS
    else:
        k_values = tuple(args.k) if args.k else K_DEFAULT_LIST
        sides = tuple(args.side) if args.side else SIDES_DEFAULT
        n_ratios = tuple(args.n_ratios) if args.n_ratios else N_RATIOS

    print(f"[run] mode: {'smoke' if args.smoke else ('full' if args.full else 'explicit')}")
    print(f"[run] parquet: {parquet_path}")
    print(f"[run] start: {datetime.now().isoformat()}")

    try:
        saved = compute_all_constants(
            parquet_path=parquet_path,
            k_values=k_values,
            sides=sides,
            n_ratios=n_ratios,
            train_start=args.train_start,
            train_end=args.train_end,
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
