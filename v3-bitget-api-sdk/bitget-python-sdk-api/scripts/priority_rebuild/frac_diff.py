#!/usr/bin/env python3
"""
frac_diff.py — 評価基盤 項目E: 分数階差分（fractional differentiation）自前・AFML Ch.5

位置づけ:
  ml_pipeline_baseline_v1.md §0.8⑥ / §6「評価基盤 詳細設計 E」の実装。
  生 close は非定常（学習 $30k-60k → 本番 $100k+ で別の価格域）。普通の階差（リターン化=d=1）
  は定常にするが「記憶（水準情報）」を全部壊す。分数階差分は d∈[0,1] の中間で
  「定常化しつつ記憶を最大限残す」。d* = 定常になる最小の d（ADF p<0.05）。

  これにより「close>$48,000」のような生水準の決定木分岐（学習域でしか意味を持たず本番で無効）を
  排除し、価格域をまたいで比較可能な特徴に変換する。

なぜ自前か: mlfinlab は商用有償+3.11非対応で除外（baseline §6 v3.15）。`fracdiff` パッケージも
  本 venv 未インストール。アルゴリズムは AFML Ch.5（固定幅窓・snippet 5.3）の公開知識。
  定常性判定は既存 statsmodels.adfuller を使用（新規依存を増やさない）。自前 + 既知答えテスト
  で正しさを数学的に証明（L-242）。

参照: Lopez de Prado "Advances in Financial Machine Learning" Ch.5 (snippets 5.1-5.5)
"""

from __future__ import annotations

import numpy as np
from statsmodels.tsa.stattools import adfuller


def get_weights_ffd(d: float, thres: float = 1e-5) -> np.ndarray:
    """固定幅窓 fracdiff の重み（AFML snippet 5.3）。

    w_k = -w_{k-1} * (d - k + 1) / k を |w_k| < thres まで生成。
    返り値は古い順→新しい順（w[-1]=1.0 が最新 bar に掛かる）。

    既知の値: d=0 → [1.0] / d=1 → [-1.0, 1.0]（= 1階差）/ w[-1]=1.0・w[-2]=-d。
    """
    w = [1.0]
    k = 1
    while True:
        w_ = -w[-1] * (d - k + 1) / k
        if abs(w_) < thres:
            break
        w.append(w_)
        k += 1
    return np.array(w[::-1], dtype=np.float64)


def fracdiff_ffd(series: np.ndarray, d: float, thres: float = 1e-5) -> np.ndarray:
    """固定幅窓の分数階差分を返す（先頭 width 本は NaN）。

    out[i] = Σ_j w[j] * series[i-width+j]（width = len(w)-1）。
    """
    series = np.asarray(series, dtype=np.float64)
    w = get_weights_ffd(d, thres)
    width = len(w) - 1
    out = np.full(len(series), np.nan, dtype=np.float64)
    if width == 0:  # d=0 → 恒等
        return series.copy()
    for i in range(width, len(series)):
        out[i] = float(np.dot(w, series[i - width:i + 1]))
    return out


def adf_pvalue(series: np.ndarray) -> float:
    """ADF（拡張Dickey-Fuller）検定の p 値。p<0.05 で「単位根を棄却＝定常」。"""
    s = np.asarray(series, dtype=np.float64)
    s = s[~np.isnan(s)]
    if len(s) < 20 or np.allclose(s, s[0]):
        return 1.0  # 検定不能/定数 → 非定常扱い
    return float(adfuller(s, autolag="AIC")[1])


def find_min_d(series: np.ndarray, d_grid: np.ndarray | None = None,
               p_thresh: float = 0.05, thres: float = 1e-5) -> tuple[float, float]:
    """定常（ADF p<p_thresh）になる最小の d* をグリッド探索（AFML 図5.x の手法）。

    Returns:
        (d_star, pvalue_at_d_star)。grid 内で見つからなければ (grid 末尾, その p 値)。
    ⚠️ d はハードコードせず必ずデータ駆動で探索する（baseline §6 E・生 close 域依存を避ける）。
    """
    if d_grid is None:
        d_grid = np.round(np.arange(0.0, 1.0001, 0.05), 4)
    last_p = 1.0
    for d in d_grid:
        p = adf_pvalue(fracdiff_ffd(series, float(d), thres))
        last_p = p
        if p < p_thresh:
            return float(d), p
    return float(d_grid[-1]), last_p
