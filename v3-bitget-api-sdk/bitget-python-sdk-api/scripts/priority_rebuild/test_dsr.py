"""Tests for dsr.py — Deflated Sharpe Ratio (Bailey + Lopez de Prado 2014)."""

from __future__ import annotations

import math

import numpy as np

from dsr import (
    EULER_MASCHERONI,
    compute_dsr_from_returns,
    compute_dsr_from_stats,
    expected_max_sharpe,
    sharpe_ratio,
    sigma_sr_estimate,
)


def _approx_equal(a: float, b: float, tol: float = 1e-3) -> bool:
    return abs(a - b) <= tol


def test_euler_mascheroni_value() -> None:
    assert _approx_equal(EULER_MASCHERONI, 0.5772156649, tol=1e-9), (
        f"Euler-Mascheroni constant mismatch: {EULER_MASCHERONI}"
    )


def test_expected_max_sharpe_known_case() -> None:
    """For V[SR]=1, N=2: a = Phi^-1(0.5) = 0, b = Phi^-1(1 - 1/(2e)).
    Expected SR0 = (1-g)*0 + g*Phi^-1(1 - 1/(2e))."""
    sr_star = expected_max_sharpe(sr_variance=1.0, n_trials=2)
    from scipy.stats import norm
    b = norm.ppf(1.0 - 1.0 / (2.0 * math.e))
    expected = EULER_MASCHERONI * b
    assert _approx_equal(sr_star, expected, tol=1e-9), (
        f"expected_max_sharpe(1, 2) = {sr_star}, expected {expected}"
    )


def test_expected_max_sharpe_monotone_increasing_in_n() -> None:
    vals = [expected_max_sharpe(sr_variance=1.0, n_trials=n) for n in (2, 10, 100, 1000)]
    for i in range(len(vals) - 1):
        assert vals[i] < vals[i + 1], f"SR0 should grow with N: {vals}"


def test_paper_eq5_eq9_extreme_case() -> None:
    """Paper-faithful check at extreme inputs (also used as marti.ai 2018 case):
    SR=2.5, N=100, T=1250, V[SR]=0.5, skew=-3, excess_kurt=10.

    Hand-derivation from paper Eq. 5 / Eq. 9 (independently verified):
      SR0      = sqrt(0.5) * ((1-gamma)*Phi^-1(0.99) + gamma*Phi^-1(1-1/(100e)))
               = 0.7071 * (0.4228*2.32635 + 0.5772*2.68021) ≈ 1.78941
      inner    = 1 - (-3)*2.5 + (10-1)/4 * 2.5^2 = 22.5625
      sigma_SR = sqrt(22.5625 / 1249) ≈ 0.13440
      z        = (2.5 - 1.78941) / 0.13440 ≈ 5.287
      p        ≈ Phi(5.287) ≈ 1.0 (highly significant; ~6.3e-8 in upper tail)

    Note: marti.ai 2018 blog cites p=0.8997 for these inputs but that value
    cannot be reproduced from the paper's published formulas; the blog's
    own Python snippet, when executed, also yields p≈1.0. The 0.8997 figure
    appears to be a typo or mis-computation in the blog text. Our paper-
    faithful implementation correctly yields p≈1.0 here.
    """
    result = compute_dsr_from_stats(
        sr_hat=2.5,
        sample_size=1250,
        n_trials=100,
        sr_variance=0.5,
        skewness=-3.0,
        excess_kurtosis=10.0,
    )
    assert _approx_equal(result.sr_expected_max, 1.78941, tol=1e-4), (
        f"SR*={result.sr_expected_max}, expected 1.78941"
    )
    assert _approx_equal(result.sigma_sr, 0.13440, tol=1e-4), (
        f"sigma_SR={result.sigma_sr}, expected 0.13440"
    )
    assert _approx_equal(result.dsr_zscore, 5.287, tol=1e-2), (
        f"DSR_z={result.dsr_zscore}, expected 5.287"
    )
    assert result.dsr_probability > 0.99999, (
        f"DSR_p={result.dsr_probability}, expected > 0.99999 (highly significant)"
    )
    print(
        f"  paper Eq.5/9 extreme case: DSR_z={result.dsr_zscore:.4f}, "
        f"DSR_p={result.dsr_probability:.6f}, "
        f"SR*={result.sr_expected_max:.4f}, sigma_SR={result.sigma_sr:.6f}"
    )


def test_sigma_sr_normal_distribution_case() -> None:
    """For normal returns: skew=0, excess_kurt=0 => inner = 1 - SR^2/4.
    For SR=1, T=101: sigma = sqrt((1 - 0.25) / 100) = sqrt(0.0075) ≈ 0.08660."""
    sigma = sigma_sr_estimate(sr_hat=1.0, skewness=0.0, excess_kurt=0.0, sample_size=101)
    expected = math.sqrt(0.75 / 100)
    assert _approx_equal(sigma, expected, tol=1e-9), (
        f"sigma_SR normal case: {sigma}, expected {expected}"
    )


def test_sigma_sr_raises_on_non_positive_inner() -> None:
    """Negative skew with high SR can drive inner term negative."""
    try:
        sigma_sr_estimate(sr_hat=5.0, skewness=2.0, excess_kurt=-3.0, sample_size=100)
    except ValueError as e:
        assert "non-positive" in str(e)
        return
    raise AssertionError("sigma_sr_estimate did not raise on non-positive inner")


def test_compute_dsr_from_returns_normal_random() -> None:
    """Random normal returns: SR near 0, DSR_p should be small (not significant).
    Finite-sample skew/kurt have wider spread than ±0.5 at T=252, so we only
    assert order-of-magnitude bounds and end-to-end pipeline consistency."""
    rng = np.random.RandomState(42)
    returns = rng.randn(252) * 0.01
    result = compute_dsr_from_returns(returns=returns, n_trials=10, sr_variance=0.1)
    assert result.sample_size == 252
    assert result.n_trials == 10
    assert abs(result.skew) < 1.0
    assert abs(result.excess_kurtosis) < 2.0
    assert 0.0 <= result.dsr_probability <= 1.0
    # SR is ~0 and SR0 > 0, so DSR_p should be well below 0.5
    assert result.dsr_probability < 0.5, (
        f"DSR_p={result.dsr_probability} too high for SR~0 random returns"
    )
    print(
        f"  random normal: SR={result.sr_hat:.4f}, skew={result.skew:.4f}, "
        f"kurt={result.excess_kurtosis:.4f}, DSR_p={result.dsr_probability:.4f}"
    )


def test_sharpe_ratio_basic() -> None:
    """SR = mean / std."""
    r = np.array([0.01, 0.02, -0.01, 0.015, -0.005], dtype=np.float64)
    sr = sharpe_ratio(r, ddof=1)
    expected = r.mean() / r.std(ddof=1)
    assert _approx_equal(sr, expected, tol=1e-12)


def test_dsr_result_as_dict_completeness() -> None:
    result = compute_dsr_from_stats(
        sr_hat=1.5,
        sample_size=500,
        n_trials=50,
        sr_variance=0.3,
        skewness=-1.0,
        excess_kurtosis=5.0,
    )
    d = result.as_dict()
    expected_keys = {
        "dsr_zscore", "dsr_probability", "sr_hat", "sr_expected_max",
        "sigma_sr", "skew", "excess_kurtosis", "sample_size",
        "n_trials", "sr_variance",
    }
    assert set(d.keys()) == expected_keys, f"as_dict keys mismatch: {set(d.keys())}"


def test_expected_max_sharpe_rejects_invalid_inputs() -> None:
    try:
        expected_max_sharpe(sr_variance=1.0, n_trials=1)
    except ValueError:
        pass
    else:
        raise AssertionError("expected_max_sharpe did not reject n_trials=1")

    try:
        expected_max_sharpe(sr_variance=-0.1, n_trials=10)
    except ValueError:
        pass
    else:
        raise AssertionError("expected_max_sharpe did not reject negative sr_variance")


def run_all() -> None:
    tests = [
        test_euler_mascheroni_value,
        test_expected_max_sharpe_known_case,
        test_expected_max_sharpe_monotone_increasing_in_n,
        test_paper_eq5_eq9_extreme_case,
        test_sigma_sr_normal_distribution_case,
        test_sigma_sr_raises_on_non_positive_inner,
        test_compute_dsr_from_returns_normal_random,
        test_sharpe_ratio_basic,
        test_dsr_result_as_dict_completeness,
        test_expected_max_sharpe_rejects_invalid_inputs,
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
