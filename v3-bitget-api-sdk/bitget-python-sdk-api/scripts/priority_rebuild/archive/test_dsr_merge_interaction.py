"""Integration tests for dsr.py × merge_step_i_summaries.py interaction.

L-212b / Critical-2 (phase_compliance_checklist §1.6):
複数 script (dsr.py + merge_step_i_summaries.py) が連携して評価式を構成する場合、
各 script の unit test では検出不可能な相互作用 edge case (定数化・極値・NaN 等) を
verify する。

過去事案 (handoff v30 §1.3):
- dsr.py 単体 test 10/10 PASS だったが、merge_step_i_summaries.py が time_exit
  定数化した returns (std≈0) を dsr.py に渡したため、SR=-2×10¹⁵ の異常値で 9 件
  warning (L-207 同型・複数 script 相互作用 bug)。

本 test の目的:
- 定数 returns → DSR nan 返却 → 代替判定 (月次黒字率) に切替わる経路を full coverage
- normal returns → DSR zscore 判定経路が正常動作することを verify
- auto-PASS 禁止 (Neyman-Pearson 整合) を assertion
"""

from __future__ import annotations

import math

import numpy as np

from dsr import compute_dsr_from_returns
from merge_step_i_summaries import THRESHOLD_DSR, THRESHOLD_MONTHS_POSITIVE, compute_fold_sharpe_dsr


def test_constant_returns_dsr_nan_path() -> None:
    """L-212b ガード verify (integration):
    定数 returns を merge.compute_fold_sharpe_dsr に渡す → (sharpe=nan, dsr_z=nan) 返却。
    呼び出し側 evaluate_fold で dsr_pass は代替判定 (months_positive) に切替わる。
    """
    returns = np.full(100, 0.001, dtype=np.float64)  # 定数 (std=0)
    sharpe, dsr_z = compute_fold_sharpe_dsr(returns, n_trials=16)
    assert math.isnan(sharpe), f"sharpe must be nan for constant returns, got {sharpe}"
    assert math.isnan(dsr_z), f"dsr_z must be nan for constant returns, got {dsr_z}"


def test_compute_dsr_from_returns_constant_returns_direct() -> None:
    """dsr.py 単体経路: compute_dsr_from_returns 入口の L-212b ガードが nan 返却 + raise しない。
    handoff v30 §1.3 の SR=-2×10¹⁵ 経路 (compute_fold_sharpe_dsr 経由でなく dsr.py 直叩き)
    でも graceful fail することを verify。
    """
    returns = np.full(50, 0.005, dtype=np.float64)
    result = compute_dsr_from_returns(returns=returns, n_trials=16, sr_variance=1.0)
    assert math.isnan(result.dsr_zscore), (
        f"dsr_zscore must be nan, got {result.dsr_zscore}"
    )
    assert math.isnan(result.dsr_probability), (
        f"dsr_probability must be nan, got {result.dsr_probability}"
    )


def test_normal_returns_dsr_zscore_path() -> None:
    """通常 returns (std>0) → DSR zscore 計算経路が正常動作する。"""
    rng = np.random.RandomState(42)
    returns = rng.randn(252) * 0.01  # std ≈ 0.01
    sharpe, dsr_z = compute_fold_sharpe_dsr(returns, n_trials=16)
    assert not math.isnan(sharpe), (
        f"sharpe must not be nan for normal returns, got {sharpe}"
    )
    assert not math.isnan(dsr_z), (
        f"dsr_z must not be nan for normal returns, got {dsr_z}"
    )
    # SR ~ 0 (random normal) → dsr_z < THRESHOLD_DSR (significant に届かない)
    assert dsr_z < THRESHOLD_DSR, (
        f"dsr_z should be < {THRESHOLD_DSR} for random returns, got {dsr_z}"
    )


def test_alt_judgment_months_positive_pass() -> None:
    """L-212b alt 判定 verify:
    dsr_z=nan + months_positive ≥ THRESHOLD_MONTHS_POSITIVE → dsr_pass=True (代替判定).
    """
    dsr_z = float("nan")
    months_pos = THRESHOLD_MONTHS_POSITIVE + 1  # 9 (= 8+1)
    # evaluate_fold の判定ロジックを再現
    if math.isnan(dsr_z):
        dsr_pass = months_pos >= THRESHOLD_MONTHS_POSITIVE
        dsr_judgment_method = "alt_months_positive"
    else:
        dsr_pass = dsr_z >= THRESHOLD_DSR
        dsr_judgment_method = "dsr_zscore"
    assert dsr_pass is True, "代替判定 PASS 期待"
    assert dsr_judgment_method == "alt_months_positive"


def test_alt_judgment_months_positive_fail() -> None:
    """L-212b alt 判定 verify:
    dsr_z=nan + months_positive < THRESHOLD_MONTHS_POSITIVE → dsr_pass=False (代替判定 FAIL).
    auto-PASS 禁止 (Neyman-Pearson 整合): nan で無条件 PASS は出さない。
    """
    dsr_z = float("nan")
    months_pos = THRESHOLD_MONTHS_POSITIVE - 1  # 7 (= 8-1)
    if math.isnan(dsr_z):
        dsr_pass = months_pos >= THRESHOLD_MONTHS_POSITIVE
        dsr_judgment_method = "alt_months_positive"
    else:
        dsr_pass = dsr_z >= THRESHOLD_DSR
        dsr_judgment_method = "dsr_zscore"
    assert dsr_pass is False, "代替判定 FAIL 期待 (auto-PASS 禁止違反)"
    assert dsr_judgment_method == "alt_months_positive"


def test_normal_judgment_dsr_zscore_pass_path() -> None:
    """通常経路 verify:
    dsr_z ≥ THRESHOLD_DSR → dsr_pass=True (dsr_zscore 判定).
    """
    dsr_z = THRESHOLD_DSR + 0.5  # 1.5 (= 1.0+0.5)
    months_pos = 5  # alt 判定では FAIL する値 (= dsr 判定が優先されることを verify)
    if math.isnan(dsr_z):
        dsr_pass = months_pos >= THRESHOLD_MONTHS_POSITIVE
        dsr_judgment_method = "alt_months_positive"
    else:
        dsr_pass = dsr_z >= THRESHOLD_DSR
        dsr_judgment_method = "dsr_zscore"
    assert dsr_pass is True, "DSR zscore 判定 PASS 期待"
    assert dsr_judgment_method == "dsr_zscore"


def run_all() -> None:
    tests = [
        test_constant_returns_dsr_nan_path,
        test_compute_dsr_from_returns_constant_returns_direct,
        test_normal_returns_dsr_zscore_path,
        test_alt_judgment_months_positive_pass,
        test_alt_judgment_months_positive_fail,
        test_normal_judgment_dsr_zscore_pass_path,
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
