#!/usr/bin/env python3
"""
test_dsr_pbo_known_answers.py — dsr_pbo.py 項目F の既知答えテスト F1-F6

位置づけ:
  ml_pipeline_baseline_v1.md §6「評価基盤 詳細設計 F」の既知答えテスト（L-242）。

既知答え（baseline §6 F・Bailey & LdP）:
  F1 ノイズ多数の中の best を選んでも DSR は低い（< 0.95・選択運は有意でない）
  F2 N を過少申告すると DSR が過大化（同じ best で N=2 の DSR > N=50 の DSR）
  F3 本物のエッジ（単一戦略・選択なし）→ DSR 高い（> 0.95・deflation で潰れない）
  F4 DSR は N が増えるほど低下（多重検定の罰）
  F5 PBO: ノイズ多数 → PBO ≈ 0.5（過学習・IS best は OOS で運任せ）
  F6 PBO: 本物のエッジが 1 本混在 → PBO 低い（< 0.5・IS best が OOS でも上位）

実行:
  $SDK/.venv311/bin/python3 scripts/priority_rebuild/test_dsr_pbo_known_answers.py
"""

from __future__ import annotations

import sys

import numpy as np

from dsr_pbo import (
    per_period_sharpe, deflated_sharpe_ratio, pbo_cscv,
)

_results: list[tuple[str, bool, str]] = []


def _check(name: str, cond: bool, detail: str) -> None:
    _results.append((name, cond, detail))
    print(f"  {'✅ PASS' if cond else '❌ FAIL'}  {name}: {detail}")


def _noise_strategies(n_strat: int, T: int, seed: int) -> np.ndarray:
    """T×N の純ノイズ（真のスキル 0）リターン行列。"""
    rng = np.random.default_rng(seed)
    return rng.normal(0.0, 0.01, size=(T, n_strat))


# ── F1: ノイズ多数の best → DSR 低い ───────────────────────────────────────
def test_f1_noise_best_low_dsr() -> None:
    M = _noise_strategies(n_strat=50, T=500, seed=10)
    srs = np.array([per_period_sharpe(M[:, j]) for j in range(M.shape[1])])
    best = int(np.argmax(srs))
    res = deflated_sharpe_ratio(M[:, best], srs, n_trials=50)
    _check("F1 ノイズ 50 本の best → DSR < 0.95（不合格＝正）",
           res["dsr"] < 0.95,
           f"best SR={res['sr']:.4f} / SR0={res['sr0']:.4f} / DSR={res['dsr']:.3f}")


# ── F2: N 過少申告 → DSR 過大 ──────────────────────────────────────────────
def test_f2_underreport_n_inflates_dsr() -> None:
    M = _noise_strategies(n_strat=50, T=500, seed=10)
    srs = np.array([per_period_sharpe(M[:, j]) for j in range(M.shape[1])])
    best = int(np.argmax(srs))
    dsr_true = deflated_sharpe_ratio(M[:, best], srs, n_trials=50)["dsr"]
    dsr_under = deflated_sharpe_ratio(M[:, best], srs, n_trials=2)["dsr"]  # 過少申告
    _check("F2 N 過少申告(50→2) → DSR 過大化を検出",
           dsr_under > dsr_true,
           f"DSR(N=2)={dsr_under:.3f} > DSR(N=50)={dsr_true:.3f}")


# ── F3: 本物のエッジ（単一） → DSR 高い ───────────────────────────────────
def test_f3_real_edge_high_dsr() -> None:
    rng = np.random.default_rng(11)
    # per-period SR ≒ 0.15（mean 0.0015 / std 0.01）・選択なし（N=1）
    r = rng.normal(0.0015, 0.01, size=500)
    res = deflated_sharpe_ratio(r, np.array([per_period_sharpe(r)]), n_trials=1)
    _check("F3 本物エッジ(単一・N=1) → DSR > 0.95（合格）",
           res["dsr"] > 0.95,
           f"SR={res['sr']:.4f} / SR0={res['sr0']:.4f}(deflation なし) / DSR={res['dsr']:.3f}")


# ── F4: DSR は N が増えるほど低下 ──────────────────────────────────────────
def test_f4_dsr_monotonic_in_n() -> None:
    M = _noise_strategies(n_strat=200, T=500, seed=12)
    srs = np.array([per_period_sharpe(M[:, j]) for j in range(M.shape[1])])
    best = int(np.argmax(srs))
    d5 = deflated_sharpe_ratio(M[:, best], srs, n_trials=5)["dsr"]
    d20 = deflated_sharpe_ratio(M[:, best], srs, n_trials=20)["dsr"]
    d100 = deflated_sharpe_ratio(M[:, best], srs, n_trials=100)["dsr"]
    _check("F4 DSR は N 増で単調低下（多重検定の罰）",
           d5 >= d20 >= d100,
           f"DSR(N=5)={d5:.3f} ≥ (N=20)={d20:.3f} ≥ (N=100)={d100:.3f}")


# ── F5: PBO ノイズ → ≈ 0.5 ─────────────────────────────────────────────────
def test_f5_pbo_noise_high() -> None:
    """ノイズ戦略（真のスキル 0）の PBO は理論上 ≈ 0.5（IS 最良が OOS で運任せ）。
    注: 単一サンプルでは分散が大きい（0.3〜0.8）ため複数 seed 平均で測る。
    また N が小さく T が長いと「持続的な見かけ上の勝者」が出て PBO が下がるので、
    過学習が顕在化する N=100 / T=200（戦略数 >> 有効サンプル）で評価する。"""
    pbos = []
    for seed in range(8):
        M = _noise_strategies(n_strat=100, T=200, seed=100 + seed)
        pbos.append(pbo_cscv(M, n_blocks=10)["pbo"])
    mean_pbo = float(np.mean(pbos))
    _check("F5 PBO ノイズ(N=100,T=200) → 平均 ≈ 0.5（過学習・不合格）",
           0.40 <= mean_pbo <= 0.60,
           f"PBO 平均={mean_pbo:.3f}（8 seed・各 {[round(p,2) for p in pbos]}・期待 ≒0.5）")


# ── F6: PBO 本物エッジ混在 → 低い ─────────────────────────────────────────
def test_f6_pbo_with_real_edge_low() -> None:
    rng = np.random.default_rng(14)
    T, N = 600, 20
    M = rng.normal(0.0, 0.01, size=(T, N))
    M[:, 0] = rng.normal(0.0020, 0.01, size=T)  # 1 本だけ本物の正ドリフト（全期間一貫）
    res = pbo_cscv(M, n_blocks=10)
    _check("F6 PBO 本物エッジ 1 本混在 → < 0.5（IS best が OOS でも上位）",
           res["pbo"] < 0.5,
           f"PBO={res['pbo']:.3f}（{res['n_combos']} 通り・期待 低）")


def main() -> int:
    print("=" * 60)
    print("dsr_pbo.py 既知答えテスト F1-F6（計器の正しさ＝数学的事実）")
    print("=" * 60)
    print("\n[F1] ノイズ best → DSR 低")
    test_f1_noise_best_low_dsr()
    print("\n[F2] N 過少申告 → DSR 過大")
    test_f2_underreport_n_inflates_dsr()
    print("\n[F3] 本物エッジ → DSR 高")
    test_f3_real_edge_high_dsr()
    print("\n[F4] DSR は N 増で低下")
    test_f4_dsr_monotonic_in_n()
    print("\n[F5] PBO ノイズ → ≒0.5")
    test_f5_pbo_noise_high()
    print("\n[F6] PBO 本物エッジ混在 → 低")
    test_f6_pbo_with_real_edge_low()

    n_pass = sum(1 for _, ok, _ in _results if ok)
    n_total = len(_results)
    print("\n" + "=" * 60)
    print(f"結果: {n_pass} / {n_total} pass")
    print("=" * 60)
    if n_pass == n_total:
        print("✅ 全 pass — 計器（DSR + PBO 項目F）は正しく測れている")
        return 0
    print("❌ FAIL あり:")
    for name, ok, detail in _results:
        if not ok:
            print(f"   - {name}: {detail}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
