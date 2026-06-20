#!/usr/bin/env python3
"""
leak_regime_check.py — 評価基盤 leak/regime チェック（自前）

位置づけ:
  ml_pipeline_baseline_v1.md §0.8⑥ / §6「評価基盤 詳細設計 leak/regime」の実装。
  評価エンジンの最後の関所。2 つの不正を機械的に検出する:

  1. **leak（未来参照）**: Prime Directive（§0.3・false_positive §0-1 類型A）違反の検出。
     - 静的: 特徴量計算コードの `shift(-)` / `center=True` / 未来 index 参照を grep。
     - 因果性: 特徴量を「時点 t までのデータ」で計算した値が、未来 bar を含めて計算しても
       不変か（不変でなければ未来を参照している＝leak）。コードコメントを信用せず実装で verify。
  2. **regime 類型D（時代依存）**: 成績が特定の年/局面に偏っていないか（false_positive §2 類型D）。
     例: SHORT エッジが 2023 下落相場だけ → ベスト年を除くとエッジ消失 → 時代依存。

なぜ自前か: 外部 lib 不要の単純なチェック。自前 + 既知答えテストで証明（L-242）。

参照: false_positive_incident_policy §0-1/§2類型A/D・feedback_ml_leak_mandatory_check・AFML Ch.7
"""

from __future__ import annotations

import re
from typing import Callable

import numpy as np

# 未来参照の危険パターン（静的スキャン用）
_LEAK_PATTERNS = {
    "negative_shift": re.compile(r"\.shift\(\s*-"),          # .shift(-N) = 未来参照
    "center_rolling": re.compile(r"center\s*=\s*True"),       # 中央寄せ rolling = 未来を含む
    "future_index": re.compile(r"\[\s*[ijk]\s*\+\s*[1-9]"),   # [i+1], [j+2] 等の未来 index
    "future_iloc": re.compile(r"\.iloc\[\s*\w+\s*\+\s*[1-9]"),  # .iloc[i+1] 等
}


def scan_leak_patterns(code: str) -> dict[str, list[int]]:
    """コード文字列を行走査し、未来参照パターンに当たった行番号を返す。

    Returns:
        {パターン名: [行番号,...]}。全カテゴリ空なら leak パターンなし。
    ⚠️ コメントの「look-ahead 防止」を信用せず、実装の現物を grep する（L-180）。
    """
    hits: dict[str, list[int]] = {k: [] for k in _LEAK_PATTERNS}
    for lineno, line in enumerate(code.splitlines(), start=1):
        for name, pat in _LEAK_PATTERNS.items():
            if pat.search(line):
                hits[name].append(lineno)
    return {k: v for k, v in hits.items() if v}


def future_dependence_positions(feature_fn: Callable[[np.ndarray], np.ndarray],
                                series: np.ndarray,
                                test_positions: list[int] | None = None) -> list[int]:
    """因果性テスト: feature[i] が時点 i までのデータだけで決まるか検証。

    feature_fn(series) の i 番目の値と、feature_fn(series[:i+1])（未来を切り落とし）の
    i 番目の値が一致しなければ、その特徴量は未来 bar を参照している＝leak。

    Returns:
        leak が検出された position のリスト（空なら leak なし）。
    """
    series = np.asarray(series, dtype=np.float64)
    n = len(series)
    full = np.asarray(feature_fn(series), dtype=np.float64)
    if test_positions is None:
        # 端を避けて中間を広くサンプリング
        test_positions = list(range(max(1, n // 10), n - 1))
    leaks = []
    for i in test_positions:
        trunc = np.asarray(feature_fn(series[:i + 1]), dtype=np.float64)
        a, b = full[i], trunc[i]
        same = (np.isnan(a) and np.isnan(b)) or np.isclose(a, b, equal_nan=True)
        if not same:
            leaks.append(i)
    return leaks


def assess_temporal_dependence(returns: np.ndarray, year_labels: np.ndarray,
                               collapse_frac: float = 0.25) -> dict:
    """regime 類型D（時代依存）の検出: ベスト年を除いてエッジが残るか。

    Args:
        returns: 1 トレード/期あたりのリターン
        year_labels: 各リターンの年（または regime）ラベル
        collapse_frac: ベスト期を除いたエッジが「全体の何割未満」に崩れたら時代依存とするか（既定 0.25）
    Returns:
        {"overall_mean", "per_year_mean", "best_period", "mean_without_best",
         "is_time_dependent", "profitable_year_frac"}
        is_time_dependent=True → 全体は黒字だがベスト年を抜くとエッジが大幅に崩れる（類型D・要警戒）。
    """
    returns = np.asarray(returns, dtype=np.float64)
    year_labels = np.asarray(year_labels)
    years = np.unique(year_labels)
    per_year = {y: float(returns[year_labels == y].mean()) for y in years}
    overall = float(returns.mean())
    best = max(per_year, key=per_year.get)
    mask = year_labels != best
    mean_wo_best = float(returns[mask].mean()) if mask.any() else 0.0
    prof_frac = float(np.mean([v > 0 for v in per_year.values()]))
    # 全体は黒字だが、最良の 1 期を抜くとエッジが全体の collapse_frac 未満に崩壊 → 時代依存
    # （単純な「≤0」は端値で脆いため、エッジ崩壊率で判定）
    is_td = (overall > 0) and (mean_wo_best < collapse_frac * overall)
    return {
        "overall_mean": overall,
        "per_year_mean": {str(k): v for k, v in per_year.items()},
        "best_period": str(best),
        "mean_without_best": mean_wo_best,
        "is_time_dependent": bool(is_td),
        "profitable_year_frac": prof_frac,
    }
