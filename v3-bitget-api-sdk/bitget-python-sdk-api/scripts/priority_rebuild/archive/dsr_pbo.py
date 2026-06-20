#!/usr/bin/env python3
"""
dsr_pbo.py — 評価基盤 項目F: Deflated Sharpe Ratio + Probability of Backtest Overfitting（自前）

位置づけ:
  ml_pipeline_baseline_v1.md §0.8⑤ / §6「評価基盤 詳細設計 F」の実装。
  「たくさん戦略/設定を試して、たまたま良かっただけ」を本物のエッジと取り違えるのを防ぐ
  多重検定補正の計器。これが無いと「月次 net ≥ $1,900」がデータスヌーピングの産物でも合格に見える。

  - **DSR（Deflated Sharpe Ratio・Bailey & López de Prado 2014）**: 観測 Sharpe を
    ①選択バイアス（N 回試した中の最大）②非正規性（歪度/尖度）③サンプル長 で補正し、
    「真の Sharpe > ベンチマーク である確率」を返す。合格 = DSR > 0.95。
  - **PBO（Bailey et al. 2015・CSCV）**: 時系列を S ブロックに割り、全 C(S,S/2) 通りで
    IS/OOS を組み替え、「IS で最良の戦略が OOS で中央値未満に落ちる確率」。合格 = PBO < 0.5。

合格 = 月次 net ≥ $1,900（A の計器で測る）+ DSR > 0.95 + PBO < 0.5。

なぜ自前か: mlfinlab は商用有償+3.11非対応で除外（baseline §6 v3.15）。式は公開
  （Bailey & LdP 論文・AFML Ch.8/11）。scipy.stats のみ使用。自前 + 既知答えテストで証明（L-242）。

参照: Bailey & López de Prado "The Deflated Sharpe Ratio" (2014, SSRN 2460551) /
      Bailey et al. "The Probability of Backtest Overfitting" (2015) / AFML Ch.8, Ch.11
"""

from __future__ import annotations

from itertools import combinations

import numpy as np
from scipy.stats import norm, skew, kurtosis, rankdata

_EULER_GAMMA = 0.5772156649015329


def per_period_sharpe(returns: np.ndarray) -> float:
    """1 期あたり Sharpe = mean / std（ddof=1）。std=0 は 0 を返す。"""
    r = np.asarray(returns, dtype=np.float64)
    sd = r.std(ddof=1)
    if sd == 0 or not np.isfinite(sd):
        return 0.0
    return float(r.mean() / sd)


def expected_max_sharpe(sr_variance: float, n_trials: int) -> float:
    """N 回の独立試行（真のスキル 0）で期待される最大 Sharpe（DSR の deflation ベンチマーク）。

    SR0 = sqrt(V) * [ (1-γ)·Z⁻¹(1 - 1/N) + γ·Z⁻¹(1 - 1/N·e⁻¹) ]   (Bailey & LdP 2014)
    """
    if n_trials <= 1:
        return 0.0  # 試行 1 回（選択なし）→ deflation なし
    v = max(sr_variance, 0.0)
    z1 = norm.ppf(1.0 - 1.0 / n_trials)
    z2 = norm.ppf(1.0 - 1.0 / n_trials * np.e ** -1)
    return float(np.sqrt(v) * ((1.0 - _EULER_GAMMA) * z1 + _EULER_GAMMA * z2))


def probabilistic_sharpe_ratio(sr: float, sr_benchmark: float, T: int,
                               skew_: float, kurt_: float) -> float:
    """PSR: 観測 Sharpe が benchmark を超える確率（非正規性・サンプル長補正・AFML Ch.8）。

    PSR = Φ( (SR − SR*)·√(T−1) / √(1 − γ3·SR + (γ4−1)/4·SR²) )
    （γ3=歪度・γ4=尖度[正規=3]）
    """
    denom = np.sqrt(max(1.0 - skew_ * sr + (kurt_ - 1.0) / 4.0 * sr ** 2, 1e-12))
    return float(norm.cdf((sr - sr_benchmark) * np.sqrt(T - 1) / denom))


def deflated_sharpe_ratio(best_returns: np.ndarray, sr_estimates: np.ndarray,
                          n_trials: int | None = None, T: int | None = None) -> dict:
    """選択された（最良）戦略の Deflated Sharpe Ratio。

    Args:
        best_returns: 選ばれた戦略の 1 期リターン列
        sr_estimates: 試した全戦略の per-period Sharpe（分散 V と試行数 N の推定用）
        n_trials: 試行数 N（省略時 len(sr_estimates)）。**過少申告すると DSR が過大化**（既知答え F2）。
        T: サンプル長（省略時 len(best_returns)）
    Returns:
        {"dsr", "sr", "sr0", "n_trials", "T"}・dsr>0.95 で合格。
    """
    r = np.asarray(best_returns, dtype=np.float64)
    if T is None:
        T = len(r)
    if n_trials is None:
        n_trials = len(sr_estimates)
    sr = per_period_sharpe(r)
    v = float(np.var(np.asarray(sr_estimates, dtype=np.float64), ddof=1)) if len(sr_estimates) > 1 else 0.0
    sr0 = expected_max_sharpe(v, n_trials)
    sk = float(skew(r))
    ku = float(kurtosis(r, fisher=False))  # 正規=3
    dsr = probabilistic_sharpe_ratio(sr, sr0, T, sk, ku)
    return {"dsr": dsr, "sr": sr, "sr0": sr0, "n_trials": int(n_trials), "T": int(T)}


def pbo_cscv(perf_matrix: np.ndarray, n_blocks: int = 10) -> dict:
    """CSCV による Probability of Backtest Overfitting（Bailey et al. 2015）。

    Args:
        perf_matrix: shape (T, N)・T 期 × N 戦略の 1 期リターン
        n_blocks: 分割ブロック数 S（偶数）。全 C(S, S/2) 通りで IS/OOS を組み替える。
    Returns:
        {"pbo", "n_combos"}・pbo<0.5 で合格（IS 最良が OOS でも上位＝過学習でない）。
    """
    M = np.asarray(perf_matrix, dtype=np.float64)
    T, N = M.shape
    if n_blocks % 2 != 0:
        raise ValueError("n_blocks は偶数")
    blocks = np.array_split(np.arange(T), n_blocks)
    ids = list(range(n_blocks))
    logits = []
    for is_sel in combinations(ids, n_blocks // 2):
        is_rows = np.concatenate([blocks[b] for b in is_sel])
        oos_rows = np.concatenate([blocks[b] for b in ids if b not in is_sel])
        sr_is = np.array([per_period_sharpe(M[is_rows, j]) for j in range(N)])
        sr_oos = np.array([per_period_sharpe(M[oos_rows, j]) for j in range(N)])
        n_star = int(np.argmax(sr_is))                 # IS で最良の戦略
        ranks = rankdata(sr_oos)                        # 1..N（大きいほど OOS 良好）
        w = ranks[n_star] / (N + 1.0)                   # OOS 相対順位 (0,1)
        w = min(max(w, 1e-6), 1.0 - 1e-6)
        logits.append(np.log(w / (1.0 - w)))            # logit ≤ 0 → OOS で中央値未満（過学習）
    logits = np.array(logits)
    return {"pbo": float(np.mean(logits <= 0.0)), "n_combos": int(len(logits))}
