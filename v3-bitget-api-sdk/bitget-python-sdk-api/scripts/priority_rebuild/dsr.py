"""
Deflated Sharpe Ratio (DSR) - Bailey + Lopez de Prado (2014)

Reference:
    Bailey, D. H., & Lopez de Prado, M. (2014).
    "The Deflated Sharpe Ratio: Correcting for Selection Bias,
     Backtest Overfitting and Non-Normality."
    Journal of Portfolio Management, 40(5), 94-107.
    SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551
    PDF:  https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf

Formulas (paper Eqs. 5, 9):

    SR0  = sqrt(V[SR]) * ( (1 - gamma) * Phi^-1(1 - 1/N)
                          +     gamma  * Phi^-1(1 - 1/(N*e)) )

    DSR_z  = (SR_hat - SR0) * sqrt(T - 1)
             / sqrt(1 - gamma_3 * SR_hat + (gamma_4 + 2) / 4 * SR_hat^2)
                              # ^ gamma_4 is EXCESS kurtosis (Fisher); the paper
                              # writes (g4_tot - 1)/4 with TOTAL kurtosis g4_tot
                              # = excess + 3, so (g4_tot - 1)/4 = (excess + 2)/4.

    DSR_p  = Phi(DSR_z)                # paper-canonical (probabilistic) form

Where:
    gamma    = Euler-Mascheroni constant (~0.5772156649)
    e        = Euler's number
    Phi      = standard normal CDF
    Phi^-1   = standard normal inverse CDF (quantile)
    N        = number of independent backtest trials
    T        = sample size (number of returns)
    V[SR]    = variance of the SR estimates across N trials
    SR_hat   = observed Sharpe Ratio of the candidate strategy
    gamma_3  = skewness of returns (Fisher / sample skewness)
    gamma_4  = EXCESS kurtosis of returns (Fisher, normal = 0)
               -- matches scipy.stats.kurtosis(fisher=True) default

Two output forms:
    - dsr_zscore : raw z-score (Eq. 9 numerator/denominator) - matches
                   mlfinlab convention. cc_ml_design_spec §1.5.1 threshold
                   "DSR > 1.0" refers to this form (1-sigma significance).
    - dsr_probability : CDF-applied probability in [0, 1] - paper-canonical
                        (deflated probabilistic Sharpe ratio).

Validation example (marti.ai 2018, reproducing paper):
    SR=2.5, N=100, T=1250, V[SR]=0.5, skew=-3, excess_kurt=10
    => dsr_probability ≈ 0.8997
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.stats import kurtosis as scipy_kurtosis
from scipy.stats import norm
from scipy.stats import skew as scipy_skew


EULER_MASCHERONI = 0.5772156649015329


@dataclass(frozen=True)
class DSRResult:
    """DSR + all intermediate statistics (Step D §3.1 spec)."""

    dsr_zscore: float
    dsr_probability: float
    sr_hat: float
    sr_expected_max: float
    sigma_sr: float
    skew: float
    excess_kurtosis: float
    sample_size: int
    n_trials: int
    sr_variance: float

    def as_dict(self) -> dict:
        return {
            "dsr_zscore": self.dsr_zscore,
            "dsr_probability": self.dsr_probability,
            "sr_hat": self.sr_hat,
            "sr_expected_max": self.sr_expected_max,
            "sigma_sr": self.sigma_sr,
            "skew": self.skew,
            "excess_kurtosis": self.excess_kurtosis,
            "sample_size": self.sample_size,
            "n_trials": self.n_trials,
            "sr_variance": self.sr_variance,
        }


def sharpe_ratio(returns: np.ndarray, ddof: int = 1) -> float:
    """Per-period Sharpe Ratio (assuming zero risk-free rate)."""
    r = np.asarray(returns, dtype=np.float64)
    std = r.std(ddof=ddof)
    if std == 0.0:
        return 0.0
    return float(r.mean() / std)


def expected_max_sharpe(sr_variance: float, n_trials: int) -> float:
    """Eq. 5: expected maximum SR across N independent trials under H0."""
    if n_trials < 2:
        raise ValueError(f"n_trials must be >= 2, got {n_trials}")
    if sr_variance < 0:
        raise ValueError(f"sr_variance must be >= 0, got {sr_variance}")
    sigma = math.sqrt(sr_variance)
    a = norm.ppf(1.0 - 1.0 / n_trials)
    b = norm.ppf(1.0 - 1.0 / (n_trials * math.e))
    return float(sigma * ((1.0 - EULER_MASCHERONI) * a + EULER_MASCHERONI * b))


def sigma_sr_estimate(sr_hat: float, skewness: float, excess_kurt: float, sample_size: int) -> float:
    """Eq. 9 denominator: Mertens-form standard error of SR estimate.

    Bailey-Lopez de Prado 2014 / Mertens 2002 form (with TOTAL kurtosis g4_tot):
        sigma_hat(SR) = sqrt( (1 - g3*SR + (g4_tot - 1)/4 * SR^2) / (T - 1) )

    We pass excess kurtosis (Fisher) here; conversion: g4_tot = excess_kurt + 3,
    so (g4_tot - 1)/4 = (excess_kurt + 2)/4. For Gaussian (excess_kurt=0) this
    reduces to (1 + 0.5*SR^2)/(T-1) = Lo (2002) closed form.
    """
    if sample_size < 2:
        raise ValueError(f"sample_size must be >= 2, got {sample_size}")
    inner = 1.0 - skewness * sr_hat + (excess_kurt + 2.0) / 4.0 * sr_hat**2
    if inner <= 0:
        raise ValueError(
            f"sigma_SR denominator non-positive ({inner:.6f}). "
            f"Inputs: SR={sr_hat}, skew={skewness}, excess_kurt={excess_kurt}. "
            f"Check moment estimates for outliers."
        )
    return float(math.sqrt(inner / (sample_size - 1)))


def compute_dsr_from_stats(
    sr_hat: float,
    sample_size: int,
    n_trials: int,
    sr_variance: float,
    skewness: float,
    excess_kurtosis: float,
) -> DSRResult:
    """DSR from pre-computed moments.

    Args:
        sr_hat: observed Sharpe Ratio (same period as returns; not annualized
            unless variance/skew/kurt are also annualized-consistent).
        sample_size: T, number of return observations.
        n_trials: N, number of independent trials in the grid search.
        sr_variance: V[SR], cross-trial variance of SR estimates.
        skewness: gamma_3, sample skewness of returns.
        excess_kurtosis: gamma_4, EXCESS kurtosis (Fisher, normal = 0).
    """
    sr_star = expected_max_sharpe(sr_variance, n_trials)
    sigma = sigma_sr_estimate(sr_hat, skewness, excess_kurtosis, sample_size)
    z = (sr_hat - sr_star) / sigma
    p = float(norm.cdf(z))
    return DSRResult(
        dsr_zscore=float(z),
        dsr_probability=p,
        sr_hat=float(sr_hat),
        sr_expected_max=float(sr_star),
        sigma_sr=float(sigma),
        skew=float(skewness),
        excess_kurtosis=float(excess_kurtosis),
        sample_size=int(sample_size),
        n_trials=int(n_trials),
        sr_variance=float(sr_variance),
    )


def compute_dsr_from_returns(
    returns: np.ndarray,
    n_trials: int,
    sr_variance: float,
) -> DSRResult:
    """DSR from a returns array; skew/kurt/SR estimated from sample.

    Args:
        returns: 1-D array of per-period returns.
        n_trials: N, number of independent trials in the grid search.
        sr_variance: V[SR], cross-trial variance of SR estimates. Must be
            supplied by the caller (cannot be inferred from a single series).
    """
    r = np.asarray(returns, dtype=np.float64)
    if r.ndim != 1:
        raise ValueError(f"returns must be 1-D, got shape {r.shape}")
    t = r.shape[0]
    sr = sharpe_ratio(r, ddof=1)
    g3 = float(scipy_skew(r, bias=False))
    g4 = float(scipy_kurtosis(r, fisher=True, bias=False))
    return compute_dsr_from_stats(
        sr_hat=sr,
        sample_size=t,
        n_trials=n_trials,
        sr_variance=sr_variance,
        skewness=g3,
        excess_kurtosis=g4,
    )


__all__ = [
    "EULER_MASCHERONI",
    "DSRResult",
    "sharpe_ratio",
    "expected_max_sharpe",
    "sigma_sr_estimate",
    "compute_dsr_from_stats",
    "compute_dsr_from_returns",
]
