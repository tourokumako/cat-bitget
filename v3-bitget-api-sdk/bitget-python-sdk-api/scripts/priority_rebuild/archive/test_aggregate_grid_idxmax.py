"""Tests for _aggregate_grid_idxmax (run_lgbm_phase1_v5_case_a_v2.py).

Step I-2.8: 集約ロジック (train PnL idxmax) の edge case verify.
L-207 教訓: 失敗境界 (empty / tied / NaN / 全 zero / 空 DatetimeIndex) を必ず含める.
"""

from __future__ import annotations

import math

import pandas as pd

from run_lgbm_phase1_v5_case_a_v2 import (
    MethodFoldMetrics,
    MethodGridResult,
    _aggregate_grid_idxmax,
)


# ---------- helpers ----------

def _make_grid(
    method: str = "fixed_tp",
    fold_idx: int = 0,
    K: int = 12,
    side: str = "LONG",
    tp_pct: float | None = 0.5,
    sl_pct: float | None = 0.5,
    N: int | None = None,
    train_pnl: float = 0.0,
    test_pnl: float = 0.0,
    test_months_positive: int = 0,
    n_train: int = 0,
    n_test: int = 0,
) -> MethodGridResult:
    return MethodGridResult(
        method=method,
        fold_idx=fold_idx,
        K=K,
        side=side,
        tp_pct=tp_pct,
        sl_pct=sl_pct,
        N=N,
        train_sim_pnl_year_usd=train_pnl,
        test_sim_pnl_year_usd=test_pnl,
        test_months_positive=test_months_positive,
        n_train=n_train,
        n_test=n_test,
    )


def _make_ts(start: str = "2025-01-01", n: int = 10, freq: str = "5min") -> pd.DatetimeIndex:
    return pd.date_range(start=start, periods=n, freq=freq)


# ---------- tests ----------

def test_empty_grid_returns_warning() -> None:
    """L-207 失敗境界: 空入力 → warning + デフォルト値."""
    train_ts = _make_ts()
    test_ts = _make_ts(start="2025-02-01")

    out = _aggregate_grid_idxmax(
        grid_results=[],
        method="fixed_tp",
        fold_idx=0,
        K=12,
        side="LONG",
        train_ts=train_ts,
        test_ts=test_ts,
    )
    assert isinstance(out, MethodFoldMetrics)
    assert out.warnings == ["no valid grid result"]
    assert out.method == "fixed_tp"
    assert out.fold_idx == 0
    assert out.K == 12
    assert out.side == "LONG"
    assert out.best_tp_pct is None
    assert out.best_sl_pct is None
    assert out.best_N is None
    assert out.test_sim_pnl_year_usd == 0.0
    assert out.test_months_positive == 0
    assert out.n_train == 0
    assert out.n_test == 0
    assert out.all_grid_results == []


def test_single_grid_returns_that_grid() -> None:
    """正常境界: 1 要素 → そのまま転記."""
    g = _make_grid(tp_pct=0.8, sl_pct=0.5, train_pnl=123.45, test_pnl=67.89, n_train=100, n_test=20)
    train_ts = _make_ts()
    test_ts = _make_ts(start="2025-02-01")

    out = _aggregate_grid_idxmax(
        grid_results=[g],
        method="fixed_tp",
        fold_idx=1,
        K=24,
        side="SHORT",
        train_ts=train_ts,
        test_ts=test_ts,
    )
    assert out.best_tp_pct == 0.8
    assert out.best_sl_pct == 0.5
    assert out.best_N is None
    assert out.test_sim_pnl_year_usd == 67.89
    assert out.n_train == 100
    assert out.n_test == 20
    assert len(out.all_grid_results) == 1


def test_multiple_distinct_picks_max_train_pnl() -> None:
    """正常: train PnL [100, 500, 300] → idx=1 採用."""
    grids = [
        _make_grid(tp_pct=0.3, train_pnl=100.0, test_pnl=10.0),
        _make_grid(tp_pct=0.5, train_pnl=500.0, test_pnl=50.0),
        _make_grid(tp_pct=0.8, train_pnl=300.0, test_pnl=30.0),
    ]
    out = _aggregate_grid_idxmax(
        grid_results=grids,
        method="fixed_tp",
        fold_idx=0, K=12, side="LONG",
        train_ts=_make_ts(), test_ts=_make_ts(start="2025-02-01"),
    )
    assert out.best_tp_pct == 0.5
    assert out.test_sim_pnl_year_usd == 50.0


def test_tied_train_pnl_returns_first() -> None:
    """L-207 失敗境界: 同点 train PnL → numpy.argmax 仕様で最初の max を返す."""
    grids = [
        _make_grid(tp_pct=0.3, train_pnl=500.0, test_pnl=10.0),
        _make_grid(tp_pct=0.5, train_pnl=500.0, test_pnl=99.0),  # 同点だが skip される
        _make_grid(tp_pct=0.8, train_pnl=300.0, test_pnl=30.0),
    ]
    out = _aggregate_grid_idxmax(
        grid_results=grids,
        method="fixed_tp",
        fold_idx=0, K=12, side="LONG",
        train_ts=_make_ts(), test_ts=_make_ts(start="2025-02-01"),
    )
    assert out.best_tp_pct == 0.3
    assert out.test_sim_pnl_year_usd == 10.0


def test_all_negative_picks_least_negative() -> None:
    """正常: 全負値 train PnL → 最大 (最小負値) を採用."""
    grids = [
        _make_grid(tp_pct=0.3, train_pnl=-100.0, test_pnl=-5.0),
        _make_grid(tp_pct=0.5, train_pnl=-50.0, test_pnl=-2.0),
        _make_grid(tp_pct=0.8, train_pnl=-200.0, test_pnl=-10.0),
    ]
    out = _aggregate_grid_idxmax(
        grid_results=grids,
        method="fixed_tp",
        fold_idx=0, K=12, side="LONG",
        train_ts=_make_ts(), test_ts=_make_ts(start="2025-02-01"),
    )
    assert out.best_tp_pct == 0.5
    assert out.test_sim_pnl_year_usd == -2.0


def test_all_zero_picks_first() -> None:
    """L-207 失敗境界: 全 zero → idx=0 (np.argmax 仕様)."""
    grids = [
        _make_grid(tp_pct=0.3, train_pnl=0.0, test_pnl=1.0),
        _make_grid(tp_pct=0.5, train_pnl=0.0, test_pnl=2.0),
        _make_grid(tp_pct=0.8, train_pnl=0.0, test_pnl=3.0),
    ]
    out = _aggregate_grid_idxmax(
        grid_results=grids,
        method="fixed_tp",
        fold_idx=0, K=12, side="LONG",
        train_ts=_make_ts(), test_ts=_make_ts(start="2025-02-01"),
    )
    assert out.best_tp_pct == 0.3
    assert out.test_sim_pnl_year_usd == 1.0


def test_fields_preserved_from_best_grid() -> None:
    """正常: best grid の全 field が MethodFoldMetrics に転記される."""
    grids = [
        _make_grid(tp_pct=0.3, sl_pct=0.5, train_pnl=100.0, test_pnl=10.0, n_train=50, n_test=10, test_months_positive=2),
        _make_grid(
            tp_pct=1.2, sl_pct=0.8, train_pnl=999.0, test_pnl=42.0,
            n_train=200, n_test=40, test_months_positive=8,
        ),
        _make_grid(tp_pct=0.5, sl_pct=0.3, train_pnl=300.0, test_pnl=20.0, n_train=100, n_test=20, test_months_positive=4),
    ]
    out = _aggregate_grid_idxmax(
        grid_results=grids,
        method="fixed_tp",
        fold_idx=2, K=48, side="SHORT",
        train_ts=_make_ts(), test_ts=_make_ts(start="2025-02-01"),
    )
    # best grid (idx=1) の値が転記されている
    assert out.best_tp_pct == 1.2
    assert out.best_sl_pct == 0.8
    assert out.test_sim_pnl_year_usd == 42.0
    assert out.n_train == 200
    assert out.n_test == 40
    assert out.test_months_positive == 8
    # method / fold_idx / K / side は引数からそのまま
    assert out.method == "fixed_tp"
    assert out.fold_idx == 2
    assert out.K == 48
    assert out.side == "SHORT"
    # all_grid_results に 3 件 全保持
    assert len(out.all_grid_results) == 3


def test_train_test_ts_metadata_correct() -> None:
    """正常: train_ts / test_ts の最初/最後が文字列化される."""
    train_ts = pd.date_range(start="2024-01-15", periods=100, freq="5min")
    test_ts = pd.date_range(start="2025-03-01", periods=50, freq="5min")
    g = _make_grid(train_pnl=100.0, test_pnl=10.0)

    out = _aggregate_grid_idxmax(
        grid_results=[g],
        method="time_exit",
        fold_idx=0, K=12, side="LONG",
        train_ts=train_ts, test_ts=test_ts,
    )
    assert out.train_start == str(train_ts[0])
    assert out.train_end == str(train_ts[-1])
    assert out.test_start == str(test_ts[0])
    assert out.test_end == str(test_ts[-1])
    # 期待値の sanity check
    assert "2024-01-15" in out.train_start
    assert "2025-03-01" in out.test_start


def test_empty_train_test_ts_handled() -> None:
    """L-207 失敗境界: 空 DatetimeIndex → train_start/end = "" になる."""
    g = _make_grid(train_pnl=100.0, test_pnl=10.0)
    empty_ts = pd.DatetimeIndex([])

    out = _aggregate_grid_idxmax(
        grid_results=[g],
        method="fixed_tp",
        fold_idx=0, K=12, side="LONG",
        train_ts=empty_ts, test_ts=empty_ts,
    )
    assert out.train_start == ""
    assert out.train_end == ""
    assert out.test_start == ""
    assert out.test_end == ""
    # grid 自体は採用されている
    assert out.test_sim_pnl_year_usd == 10.0


def test_nan_in_train_pnl_documents_current_behavior() -> None:
    """L-207 失敗境界: NaN 混入時の np.argmax 挙動を document.

    np.argmax は NaN を最大として扱う (NaN との比較は常に False のため、
    最初の NaN index を返す)。これは現実装の隠れた問題で、将来 NaN guard
    を追加する際に本 test が明示的失敗してリグレッションを検出する。

    現状の挙動: NaN を含む場合、最初の NaN の idx を best として採用する。
    """
    grids = [
        _make_grid(tp_pct=0.3, train_pnl=100.0, test_pnl=10.0),
        _make_grid(tp_pct=0.5, train_pnl=float("nan"), test_pnl=999.0),
        _make_grid(tp_pct=0.8, train_pnl=300.0, test_pnl=30.0),
    ]
    out = _aggregate_grid_idxmax(
        grid_results=grids,
        method="fixed_tp",
        fold_idx=0, K=12, side="LONG",
        train_ts=_make_ts(), test_ts=_make_ts(start="2025-02-01"),
    )
    # 現実装: np.argmax は NaN の idx=1 を返す
    assert out.best_tp_pct == 0.5
    assert out.test_sim_pnl_year_usd == 999.0
    assert math.isnan(out.all_grid_results[1].train_sim_pnl_year_usd)


def run_all() -> None:
    tests = [
        test_empty_grid_returns_warning,
        test_single_grid_returns_that_grid,
        test_multiple_distinct_picks_max_train_pnl,
        test_tied_train_pnl_returns_first,
        test_all_negative_picks_least_negative,
        test_all_zero_picks_first,
        test_fields_preserved_from_best_grid,
        test_train_test_ts_metadata_correct,
        test_empty_train_test_ts_handled,
        test_nan_in_train_pnl_documents_current_behavior,
    ]
    failures = 0
    for t in tests:
        try:
            print(f"[RUN ] {t.__name__}")
            t()
            print(f"[PASS] {t.__name__}")
        except Exception as e:
            failures += 1
            print(f"[FAIL] {t.__name__}: {e}")
    print(f"\n{len(tests) - failures}/{len(tests)} tests passed")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    run_all()
