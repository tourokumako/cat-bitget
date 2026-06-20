#!/usr/bin/env python3
"""
test_sample_uniqueness_known_answers.py — sample_uniqueness.py 項目C の既知答えテスト C1-C5

位置づけ:
  ml_pipeline_baseline_v1.md §6「評価基盤 詳細設計 C」の既知答えテスト。
  「答えが数学的に分かりきった問題」を計器に解かせ、正解を返せば計器は正しい（L-242）。

既知答え（baseline §6 C・AFML Ch.4）:
  C1 全ラベルが同一区間（N 本重なる）→ 平均ユニークネス = 1/N（＝重み 1/N）
  C2 ラベルが全く重ならない → 平均ユニークネス = 1.0（完全ユニーク）
  C3 部分重なり（手計算）→ 既知の値に一致
  C4 高重複 → 実効サンプル数 << N（OOS 過大評価の正体・「証拠量の錯覚」）
  C5 sequential bootstrap → standard bootstrap より平均ユニークネスが高い（debiasing）

実行:
  $SDK/.venv311/bin/python3 scripts/priority_rebuild/test_sample_uniqueness_known_answers.py
"""

from __future__ import annotations

import sys

import numpy as np

from sample_uniqueness import (
    concurrency, average_uniqueness, sample_weight_by_uniqueness,
    effective_sample_size, sequential_bootstrap, standard_bootstrap,
    _avg_uniqueness_of_sample,
)

_results: list[tuple[str, bool, str]] = []


def _check(name: str, cond: bool, detail: str) -> None:
    _results.append((name, cond, detail))
    print(f"  {'✅ PASS' if cond else '❌ FAIL'}  {name}: {detail}")


# ── C1: 全ラベル同一区間 → 平均ユニークネス = 1/N ───────────────────────────
def test_c1_identical_windows() -> None:
    """N 本のラベルが全く同じ区間 [0,9] → 各 bar で c_t=N → 各 ū = 1/N。"""
    N, L = 10, 10
    starts = np.zeros(N, dtype=np.int64)
    ends = np.full(N, L - 1, dtype=np.int64)
    u = average_uniqueness(starts, ends, n_bars=L)
    w = sample_weight_by_uniqueness(starts, ends, n_bars=L, normalize=False)
    ok = np.allclose(u, 1.0 / N) and np.allclose(w, 1.0 / N)
    _check("C1 同一区間 N 本 → ū = 1/N",
           ok, f"ū={u[0]:.4f} (期待 {1/N:.4f}) / 全 {N} 本一致={np.allclose(u, 1.0/N)}")


# ── C2: 重なりなし → 平均ユニークネス = 1.0 ─────────────────────────────────
def test_c2_no_overlap() -> None:
    """連続して重ならない 5 区間（各長 4）→ 各 bar で c_t=1 → 各 ū = 1.0。"""
    starts = np.array([0, 4, 8, 12, 16], dtype=np.int64)
    ends = np.array([3, 7, 11, 15, 19], dtype=np.int64)
    u = average_uniqueness(starts, ends, n_bars=20)
    eff = effective_sample_size(starts, ends, n_bars=20)
    ok = np.allclose(u, 1.0) and abs(eff - len(starts)) < 1e-9
    _check("C2 重なりなし → ū = 1.0",
           ok, f"ū={u} / 実効N={eff:.2f} (期待 {len(starts)})")


# ── C3: 部分重なり（手計算）─────────────────────────────────────────────────
def test_c3_partial_overlap_handcalc() -> None:
    """ラベル A=[0,3] / B=[2,5]。c=[1,1,2,2,1,1]。
    ū_A=mean(1,1,.5,.5)=0.75 / ū_B=mean(.5,.5,1,1)=0.75。"""
    starts = np.array([0, 2], dtype=np.int64)
    ends = np.array([3, 5], dtype=np.int64)
    c = concurrency(starts, ends, 6)
    u = average_uniqueness(starts, ends, n_bars=6)
    c_ok = np.array_equal(c, np.array([1, 1, 2, 2, 1, 1], dtype=float))
    u_ok = np.allclose(u, [0.75, 0.75])
    _check("C3 部分重なり 手計算一致",
           c_ok and u_ok, f"c={c.tolist()} / ū={u.round(4).tolist()} (期待 [0.75, 0.75])")


# ── C4: 高重複 → 実効サンプル数 << N（過大評価の正体）───────────────────────
def test_c4_effective_n_collapse() -> None:
    """100 本が同一区間 → 実効サンプル数 = 1.0。
    「100 個ある」と思っても独立な証拠は実質 1 個。これが OOS 過大評価の機構。"""
    N = 100
    starts = np.zeros(N, dtype=np.int64)
    ends = np.full(N, 49, dtype=np.int64)
    eff = effective_sample_size(starts, ends, n_bars=50)
    _check("C4 高重複 → 実効N=1（証拠量の錯覚を露呈）",
           abs(eff - 1.0) < 1e-9, f"N={N} だが 実効N={eff:.4f}（独立は実質 1 個分）")


# ── C5: sequential bootstrap が standard より debiasing ─────────────────────
def test_c5_seq_bootstrap_debiasing() -> None:
    """重なりの多いデータで sequential bootstrap の平均ユニークネス >
    standard（一様）bootstrap の平均ユニークネス（AFML の核心・Monte Carlo）。"""
    # 重なりが強い区間群（隣接でずらした長窓・cat-bitget の窓重複を縮小再現）
    n_bars = 60
    starts = np.arange(0, 40, 2, dtype=np.int64)        # 20 ラベル
    ends = np.minimum(starts + 18, n_bars - 1)          # 長窓で強く重なる

    seq_vals, std_vals = [], []
    for seed in range(30):
        seq = sequential_bootstrap(starts, ends, n_bars, seed=seed)
        std = standard_bootstrap(len(starts), seed=seed)
        seq_vals.append(_avg_uniqueness_of_sample(seq, starts, ends, n_bars))
        std_vals.append(_avg_uniqueness_of_sample(std, starts, ends, n_bars))
    seq_mean, std_mean = float(np.mean(seq_vals)), float(np.mean(std_vals))
    _check("C5 seq bootstrap 平均ユニークネス > standard",
           seq_mean > std_mean,
           f"seq={seq_mean:.4f} > std={std_mean:.4f}（差 {seq_mean - std_mean:+.4f}・30 seed 平均）")


def main() -> int:
    print("=" * 60)
    print("sample_uniqueness.py 既知答えテスト C1-C5（計器の正しさ＝数学的事実）")
    print("=" * 60)
    print("\n[C1] 全ラベル同一区間 → ū = 1/N")
    test_c1_identical_windows()
    print("\n[C2] 重なりなし → ū = 1.0")
    test_c2_no_overlap()
    print("\n[C3] 部分重なり（手計算）")
    test_c3_partial_overlap_handcalc()
    print("\n[C4] 高重複 → 実効サンプル数 << N")
    test_c4_effective_n_collapse()
    print("\n[C5] sequential bootstrap debiasing")
    test_c5_seq_bootstrap_debiasing()

    n_pass = sum(1 for _, ok, _ in _results if ok)
    n_total = len(_results)
    print("\n" + "=" * 60)
    print(f"結果: {n_pass} / {n_total} pass")
    print("=" * 60)
    if n_pass == n_total:
        print("✅ 全 pass — 計器（sample uniqueness 項目C）は正しく測れている")
        return 0
    print("❌ FAIL あり:")
    for name, ok, detail in _results:
        if not ok:
            print(f"   - {name}: {detail}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
