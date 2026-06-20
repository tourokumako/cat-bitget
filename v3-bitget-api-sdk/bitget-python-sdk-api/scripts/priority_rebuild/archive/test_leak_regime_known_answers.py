#!/usr/bin/env python3
"""
test_leak_regime_known_answers.py — leak_regime_check.py の既知答えテスト L1-L3 / R1-R2

位置づけ:
  ml_pipeline_baseline_v1.md §6「評価基盤 詳細設計 leak/regime」の既知答えテスト（L-242）。

既知答え:
  L1 クリーンな特徴（過去 rolling）→ 因果性テストで leak 0 件
  L2 リーク特徴（shift(-1) で未来参照）→ 因果性テストで leak 検出（>0）
  L3 静的スキャン: shift(-1)/center=True/未来index を含むコード→検出 / クリーンコード→0
  R1 時代依存（エッジが 1 年だけ）→ is_time_dependent=True
  R2 頑健（全年でエッジ）→ is_time_dependent=False

実行:
  $SDK/.venv311/bin/python3 scripts/priority_rebuild/test_leak_regime_known_answers.py
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from leak_regime_check import (
    scan_leak_patterns, future_dependence_positions, assess_temporal_dependence,
)

_results: list[tuple[str, bool, str]] = []


def _check(name: str, cond: bool, detail: str) -> None:
    _results.append((name, cond, detail))
    print(f"  {'✅ PASS' if cond else '❌ FAIL'}  {name}: {detail}")


# 特徴量関数（テスト用）
def _clean_feature(arr: np.ndarray) -> np.ndarray:
    """過去 5 本の移動平均（時点 i は arr[:i+1] のみ使用＝leak なし）。"""
    s = pd.Series(arr)
    return s.rolling(5, min_periods=1).mean().to_numpy()


def _leaky_feature(arr: np.ndarray) -> np.ndarray:
    """未来 1 本を参照する特徴（shift(-1)＝leak）。"""
    s = pd.Series(arr)
    return s.shift(-1).to_numpy()


# ── L1: クリーン特徴 → leak 0 件 ───────────────────────────────────────────
def test_l1_clean_no_leak() -> None:
    rng = np.random.default_rng(1)
    x = np.cumsum(rng.normal(0, 1, 200))
    leaks = future_dependence_positions(_clean_feature, x)
    _check("L1 クリーン特徴(過去rolling) → 因果性 leak 0",
           len(leaks) == 0, f"leak 検出={len(leaks)} 件（期待 0）")


# ── L2: リーク特徴 → leak 検出 ─────────────────────────────────────────────
def test_l2_leaky_detected() -> None:
    rng = np.random.default_rng(2)
    x = np.cumsum(rng.normal(0, 1, 200))
    leaks = future_dependence_positions(_leaky_feature, x)
    _check("L2 リーク特徴(shift(-1)) → 因果性 leak 検出",
           len(leaks) > 0, f"leak 検出={len(leaks)} 件（>0・未来参照を捕捉）")


# ── L3: 静的スキャン ───────────────────────────────────────────────────────
def test_l3_static_scan() -> None:
    leaky_code = (
        "fut = close.shift(-3)\n"
        "ma = close.rolling(20, center=True).mean()\n"
        "val = arr[i + 2]\n"
    )
    clean_code = (
        "fut = close.shift(1)\n"
        "ma = close.rolling(20).mean()\n"
        "val = arr[i - 2]\n"
    )
    hits_leaky = scan_leak_patterns(leaky_code)
    hits_clean = scan_leak_patterns(clean_code)
    ok = (len(hits_leaky) >= 3) and (len(hits_clean) == 0)
    _check("L3 静的スキャン: 危険コード検出 / クリーン 0",
           ok, f"leaky hits={ {k: v for k, v in hits_leaky.items()} } / clean hits={hits_clean}")


# ── R1: 時代依存（1 年だけエッジ）→ 検出 ──────────────────────────────────
def test_r1_time_dependent_detected() -> None:
    rng = np.random.default_rng(3)
    years = np.repeat([2021, 2022, 2023, 2024, 2025], 200)
    rets = rng.normal(0.0, 0.01, len(years))          # 全年ほぼ 0
    rets[years == 2023] += 0.02                        # 2023 だけ強い正エッジ
    res = assess_temporal_dependence(rets, years)
    ok = res["is_time_dependent"] and res["best_period"] == "2023"
    _check("R1 エッジが 2023 だけ → 時代依存(類型D) 検出",
           ok, f"overall={res['overall_mean']:.4f} / best={res['best_period']} / "
               f"除外後={res['mean_without_best']:.4f} / TD={res['is_time_dependent']}")


# ── R2: 頑健（全年でエッジ）→ 非検出 ───────────────────────────────────────
def test_r2_robust_not_flagged() -> None:
    rng = np.random.default_rng(4)
    years = np.repeat([2021, 2022, 2023, 2024, 2025], 200)
    rets = rng.normal(0.005, 0.01, len(years))         # 全年で一貫した正エッジ
    res = assess_temporal_dependence(rets, years)
    ok = (not res["is_time_dependent"]) and res["mean_without_best"] > 0
    _check("R2 全年でエッジ → 時代依存でない（頑健）",
           ok, f"overall={res['overall_mean']:.4f} / 除外後={res['mean_without_best']:.4f} / "
               f"黒字年率={res['profitable_year_frac']:.2f} / TD={res['is_time_dependent']}")


def main() -> int:
    print("=" * 60)
    print("leak_regime_check.py 既知答えテスト L1-L3 / R1-R2（計器の正しさ）")
    print("=" * 60)
    print("\n[L1] クリーン特徴 → leak 0")
    test_l1_clean_no_leak()
    print("\n[L2] リーク特徴 → leak 検出")
    test_l2_leaky_detected()
    print("\n[L3] 静的スキャン")
    test_l3_static_scan()
    print("\n[R1] 時代依存 → 検出")
    test_r1_time_dependent_detected()
    print("\n[R2] 頑健 → 非検出")
    test_r2_robust_not_flagged()

    n_pass = sum(1 for _, ok, _ in _results if ok)
    n_total = len(_results)
    print("\n" + "=" * 60)
    print(f"結果: {n_pass} / {n_total} pass")
    print("=" * 60)
    if n_pass == n_total:
        print("✅ 全 pass — 計器（leak/regime チェック）は正しく測れている")
        return 0
    print("❌ FAIL あり:")
    for name, ok, detail in _results:
        if not ok:
            print(f"   - {name}: {detail}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
