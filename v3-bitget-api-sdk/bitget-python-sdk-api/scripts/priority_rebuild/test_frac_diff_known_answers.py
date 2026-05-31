#!/usr/bin/env python3
"""
test_frac_diff_known_answers.py — frac_diff.py 項目E の既知答えテスト E1-E6

位置づけ:
  ml_pipeline_baseline_v1.md §6「評価基盤 詳細設計 E」の既知答えテスト。
  答えが数学的に分かりきった問題で計器の正しさを証明（L-242）。

既知答え（baseline §6 E・AFML Ch.5）:
  E1 d=0 → 恒等（入力と一致）
  E2 d=1 → 1階差（np.diff と一致）
  E3 重みの既知値（w[-1]=1.0 / w[-2]=-d）
  E4 生 close（ランダムウォーク）は非定常（ADF p≥0.05）→ d* で定常（p<0.05）
  E5 記憶保持: 小さい d の fracdiff は生水準と相関を残す（リターン d=1 はほぼ無相関）
  E6 生 close 閾値が test 価格域で無効（学習域でしか効かない）→ fracdiff は価格域をまたいで比較可能

実行:
  $SDK/.venv311/bin/python3 scripts/priority_rebuild/test_frac_diff_known_answers.py
"""

from __future__ import annotations

import sys

import numpy as np

from frac_diff import get_weights_ffd, fracdiff_ffd, adf_pvalue, find_min_d

_results: list[tuple[str, bool, str]] = []


def _check(name: str, cond: bool, detail: str) -> None:
    _results.append((name, cond, detail))
    print(f"  {'✅ PASS' if cond else '❌ FAIL'}  {name}: {detail}")


# ── E1: d=0 → 恒等 ─────────────────────────────────────────────────────────
def test_e1_d0_identity() -> None:
    rng = np.random.default_rng(1)
    x = np.cumsum(rng.normal(0, 1, 300)) + 100.0
    out = fracdiff_ffd(x, d=0.0)
    ok = np.allclose(out, x, equal_nan=False)
    _check("E1 d=0 → 入力と一致（恒等）",
           ok, f"max|out-x|={np.max(np.abs(out - x)):.2e}")


# ── E2: d=1 → 1階差 ───────────────────────────────────────────────────────
def test_e2_d1_first_difference() -> None:
    rng = np.random.default_rng(2)
    x = np.cumsum(rng.normal(0, 1, 300)) + 100.0
    out = fracdiff_ffd(x, d=1.0)
    diff = np.diff(x)  # 長さ n-1
    ok = np.allclose(out[1:], diff, equal_nan=False) and np.isnan(out[0])
    _check("E2 d=1 → 1階差（np.diff 一致）",
           ok, f"max|out[1:]-diff|={np.nanmax(np.abs(out[1:] - diff)):.2e} / out[0]=NaN={np.isnan(out[0])}")


# ── E3: 重みの既知値 ───────────────────────────────────────────────────────
def test_e3_weights_known() -> None:
    d = 0.4
    w = get_weights_ffd(d)
    ok = abs(w[-1] - 1.0) < 1e-12 and abs(w[-2] - (-d)) < 1e-12
    _check("E3 重み w[-1]=1.0 / w[-2]=-d",
           ok, f"w[-1]={w[-1]:.4f}(期待1.0) / w[-2]={w[-2]:.4f}(期待{-d})")


# ── E4: 生 close 非定常 → d* で定常 ────────────────────────────────────────
def test_e4_nonstationary_to_stationary() -> None:
    rng = np.random.default_rng(3)
    close = np.cumsum(rng.normal(0, 1, 2000)) + 40000.0  # 生 close 風ランダムウォーク
    p_raw = adf_pvalue(close)
    d_star, p_star = find_min_d(close)
    ok = (p_raw >= 0.05) and (p_star < 0.05) and (d_star <= 1.0)
    _check("E4 生 close 非定常(ADF p≥0.05) → d* で定常(p<0.05)",
           ok, f"raw p={p_raw:.3f} / d*={d_star:.2f} で p={p_star:.4f}")


# ── E5: 記憶保持（中間 d は水準と相関・リターンはほぼ無相関）────────────────
def test_e5_memory_retention() -> None:
    # 注: d を小さくしすぎると重み窓幅が系列長を超え全 NaN になる（FFD の性質）。
    #     d=0.4 は記憶を十分残しつつ窓幅が 2000 本に収まる。
    rng = np.random.default_rng(4)
    close = np.cumsum(rng.normal(0, 1, 2000)) + 40000.0
    fd_mid = fracdiff_ffd(close, d=0.4)
    ret = fracdiff_ffd(close, d=1.0)  # = 1階差（リターン相当・記憶消失）

    def corr_with_level(y):
        m = ~np.isnan(y)
        if m.sum() < 20:
            return float("nan")
        return abs(float(np.corrcoef(close[m], y[m])[0, 1]))

    c_mid, c_ret = corr_with_level(fd_mid), corr_with_level(ret)
    ok = c_mid > c_ret and c_mid > 0.3
    _check("E5 記憶保持: 中間d fracdiff は水準と相関・d=1 は無相関",
           ok, f"corr(fd_d0.4, level)={c_mid:.3f} > corr(returns, level)={c_ret:.3f}")


# ── E6: 生 close 閾値が test 価格域で無効 → log-fracdiff は両域で定常化可能 ───
def test_e6_raw_threshold_invalid_across_regimes() -> None:
    """学習域 close≈$40k / 本番域 close≈$120k。
    生水準閾値（学習中央値）は学習では両側に分かれるが、本番では全点が上側＝分岐が退化（無効）。
    → 「生 close 閾値は価格域をまたぐと無効」を検出。
    一方 log 価格の fracdiff は両域とも d* で定常化できる（特徴として価格域をまたいで使える）。
    （注: d<1 の fracdiff は記憶保持のため水準成分を残す＝平均は 0 にならない。
      regime 不変性は「絶対平均一致」でなく「両域で定常化できる」で測る。）"""
    rng = np.random.default_rng(5)
    train_close = np.cumsum(rng.normal(0, 30, 2000)) + 40000.0   # 学習域
    test_close = np.cumsum(rng.normal(0, 30, 2000)) + 120000.0   # 本番域（別レンジ）

    thr = float(np.median(train_close))  # 学習で分割する閾値
    train_above = float(np.mean(train_close > thr))
    test_above = float(np.mean(test_close > thr))
    raw_degenerate = (0.3 < train_above < 0.7) and (test_above > 0.99)  # 学習は分割・本番は全上側

    # log 価格の fracdiff: 両域で定常化できる d* が見つかる
    _, p_tr = find_min_d(np.log(train_close))
    _, p_te = find_min_d(np.log(test_close))
    fd_both_stationary = (p_tr < 0.05) and (p_te < 0.05)

    ok = raw_degenerate and fd_both_stationary
    _check("E6 生 close 閾値は本番域で退化 → log-fracdiff は両域で定常化可能",
           ok, f"生閾値${thr:,.0f}: 学習上側{train_above:.2f}/本番上側{test_above:.2f}(退化) / "
               f"log-fracdiff 定常p 学習{p_tr:.3f}・本番{p_te:.3f}(両<0.05)")


def main() -> int:
    print("=" * 60)
    print("frac_diff.py 既知答えテスト E1-E6（計器の正しさ＝数学的事実）")
    print("=" * 60)
    print("\n[E1] d=0 → 恒等")
    test_e1_d0_identity()
    print("\n[E2] d=1 → 1階差")
    test_e2_d1_first_difference()
    print("\n[E3] 重みの既知値")
    test_e3_weights_known()
    print("\n[E4] 生close 非定常 → d* で定常")
    test_e4_nonstationary_to_stationary()
    print("\n[E5] 記憶保持")
    test_e5_memory_retention()
    print("\n[E6] 生close 閾値が本番域で無効")
    test_e6_raw_threshold_invalid_across_regimes()

    n_pass = sum(1 for _, ok, _ in _results if ok)
    n_total = len(_results)
    print("\n" + "=" * 60)
    print(f"結果: {n_pass} / {n_total} pass")
    print("=" * 60)
    if n_pass == n_total:
        print("✅ 全 pass — 計器（分数階差分 項目E）は正しく測れている")
        return 0
    print("❌ FAIL あり:")
    for name, ok, detail in _results:
        if not ok:
            print(f"   - {name}: {detail}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
