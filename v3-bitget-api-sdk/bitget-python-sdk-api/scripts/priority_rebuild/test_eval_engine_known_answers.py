#!/usr/bin/env python3
"""
test_eval_engine_known_answers.py — eval_engine.py 項目A の既知答えテスト T1-T5

位置づけ:
  ml_pipeline_baseline_v1.md §6「評価基盤 詳細設計 A」の既知答えテスト。
  「答えが数学的に分かりきった問題」を計器に解かせ、正解を返せば計器は正しい（L-242）。
  まこさんは技術を知らなくても、このテストが全 pass する事実だけ見れば計器を信用できる。

  ⚠️ 計器が正しい ≠ 戦略が儲かる。テストは「正直に測れること」のみ証明する。

既知答え（baseline §6 A）:
  T1 コインフリップ売買 → net ≒ −往復コスト（必ず負）
  T2 指値が limit に届かない → entry 0 件（取引不成立）
  T3 同 bar で TP・SL 両到達 → SL を記録（不利側先着）
  T4 SL を gap で飛び越え → open 価格で約定（sl 価格でない）
  T5 8h 超保有（funding 境界を跨ぐ）→ funding 控除あり / 跨がなければ 0

実行:
  $SDK/.venv311/bin/python3 scripts/priority_rebuild/test_eval_engine_known_answers.py
  全 pass で exit 0・1 つでも fail で exit 1。
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

import numpy as np

from eval_engine import (
    LONG, SHORT, MAKER_FEE, TAKER_FEE, SLIPPAGE, FUNDING_RATE_8H,
    simulate_trade, assert_position_cap, TradeResult,
)


def _ts_array(start: str, n: int, step_min: int = 5) -> np.ndarray:
    """start(UTC ISO) から step_min 刻みで n 本の np.datetime64 配列を作る。"""
    t0 = np.datetime64(start)
    return t0 + np.arange(n) * np.timedelta64(step_min, "m")


_results: list[tuple[str, bool, str]] = []


def _check(name: str, cond: bool, detail: str) -> None:
    _results.append((name, cond, detail))
    mark = "✅ PASS" if cond else "❌ FAIL"
    print(f"  {mark}  {name}: {detail}")


# ── T1: コインフリップ → net ≒ −往復コスト（必ず負）────────────────────────
def test_t1_coinflip_negative() -> None:
    """ランダムウォーク価格 × ランダム方向 × 広い TP/SL（必ず TIME_EXIT）。
    粗利の期待値は 0（マルチンゲール）→ net 平均はコスト分だけ必ずマイナス。"""
    rng = np.random.default_rng(42)
    n = 5000
    # ランダムウォーク close（0.1% std/bar）。
    # 約定 bar を i+1 に確定させる（low/high が必ず limit に届く）ことで
    # 「最初に limit に触れた bar を選ぶ」エントリー選択バイアスを除去し、
    # 粗利期待 ≒ 0 の純粋なコインフリップにする（→ net は往復コスト分だけ負）。
    rets = rng.normal(0.0, 0.001, n)
    closes = 100.0 * np.exp(np.cumsum(rets))
    highs = closes * 1.001   # SHORT limit(close×1.0001) に必ず届く
    lows = closes * 0.999    # LONG  limit(close×0.9999) に必ず届く
    opens = closes.copy()
    # funding を避けるため同一 8h 窓内に収める（5min × 6000 本だと跨ぐので step=1分で短時間に）
    ts = _ts_array("2026-01-01T00:00:00", n, step_min=1)

    size = 0.024
    nets = []
    n_filled = 0
    for i in range(0, n - 10, 7):
        direction = LONG if rng.random() < 0.5 else SHORT
        r = simulate_trade(
            signal_idx=i, direction=direction, size_btc=size,
            opens=opens, highs=highs, lows=lows, closes=closes, timestamps=ts,
            tp_pct=0.50, sl_pct=0.50,  # 広い → 必ず TIME_EXIT
            max_hold_bars=3,
        )
        if r is not None:
            nets.append(r.net)
            n_filled += 1

    mean_net = float(np.mean(nets))
    # 期待コスト/件 ≒ price×size×(maker[entry] + taker[exit TIME] + slippage)
    price = 100.0
    exp_cost = price * size * (MAKER_FEE + TAKER_FEE + SLIPPAGE)
    ratio = mean_net / (-exp_cost)
    _check("T1 コインフリップ → net 平均が負",
           mean_net < 0,
           f"mean_net={mean_net:.5f} USD < 0（filled {n_filled} 件）")
    _check("T1 net 平均 ≒ −往復コスト",
           0.5 < ratio < 1.6,
           f"mean_net/(−exp_cost)={ratio:.2f}（exp_cost/件={exp_cost:.5f}・粗利期待0の検算）")


# ── T2: 指値 limit 不到達 → entry 0 件 ──────────────────────────────────────
def test_t2_no_fill() -> None:
    """LONG シグナル後に価格が上昇のみ → low が limit(=close×0.9999) に届かず約定しない。"""
    closes = np.array([100.0, 100.5, 101.0, 101.5, 102.0])
    lows = np.array([99.9, 100.4, 100.9, 101.4, 101.9])  # 全て limit 99.99 超
    highs = closes * 1.001
    opens = closes.copy()
    ts = _ts_array("2026-01-01T09:00:00", len(closes))

    r = simulate_trade(
        signal_idx=0, direction=LONG, size_btc=0.024,
        opens=opens, highs=highs, lows=lows, closes=closes, timestamps=ts,
        tp_pct=0.01, sl_pct=0.01, max_hold_bars=3, ttl=3,
    )
    _check("T2 limit 不到達 → 取引不成立(None)",
           r is None,
           f"limit={100.0*0.9999:.4f} / 後続 low 最小={lows[1:4].min():.2f} → return={r}")


# ── T3: 同 bar TP・SL 両到達 → SL 記録 ──────────────────────────────────────
def test_t3_both_hit_sl_wins() -> None:
    """fill 後の bar で high≥tp かつ low≤sl の両方到達 → 不利側 SL を先着記録。"""
    # idx0 signal close=100 / idx1 で fill(low 99→limit99.99) / idx2 で TP・SL 両到達
    closes = np.array([100.0, 99.5, 100.0, 100.0])
    lows = np.array([99.8, 99.0, 98.0, 99.0])     # idx2 low=98 ≤ sl
    highs = np.array([100.2, 100.0, 101.0, 100.5])  # idx2 high=101 ≥ tp
    opens = np.array([100.0, 99.9, 99.5, 100.0])    # idx2 open=99.5（sl 98.99 より上＝gapなし）
    ts = _ts_array("2026-01-01T09:00:00", len(closes))

    r = simulate_trade(
        signal_idx=0, direction=LONG, size_btc=0.024,
        opens=opens, highs=highs, lows=lows, closes=closes, timestamps=ts,
        tp_pct=0.01, sl_pct=0.01, max_hold_bars=3, ttl=3,
    )
    sl_price = (100.0 * 0.9999) * 0.99
    ok = (r is not None) and (r.exit_reason == "SL")
    _check("T3 同 bar TP・SL 両到達 → SL 記録",
           ok,
           f"exit_reason={'None' if r is None else r.exit_reason}（sl={sl_price:.4f}・gap なしで sl 約定想定）")


# ── T4: SL gap 飛び越え → open 約定 ─────────────────────────────────────────
def test_t4_gap_fills_at_open() -> None:
    """fill 後の bar が SL を gap down で飛び越え（open < sl）→ open 価格で約定（sl でない）。"""
    closes = np.array([100.0, 99.5, 97.0, 97.0])
    lows = np.array([99.8, 99.0, 96.5, 97.0])     # idx2 low=96.5 ≤ sl
    highs = np.array([100.2, 100.0, 98.0, 97.5])
    opens = np.array([100.0, 99.9, 98.0, 97.0])    # idx2 open=98.0 < sl 98.99 → gap
    ts = _ts_array("2026-01-01T09:00:00", len(closes))

    entry = 100.0 * 0.9999
    sl_price = entry * 0.99  # ≒ 98.9901
    r = simulate_trade(
        signal_idx=0, direction=LONG, size_btc=0.024,
        opens=opens, highs=highs, lows=lows, closes=closes, timestamps=ts,
        tp_pct=0.05, sl_pct=0.01, max_hold_bars=3, ttl=3,
    )
    ok = (r is not None) and r.exit_reason == "SL" and abs(r.exit_price - 98.0) < 1e-9 and r.exit_price < sl_price
    _check("T4 SL gap → open 約定（sl 価格でない）",
           ok,
           f"exit_price={'None' if r is None else f'{r.exit_price:.4f}'} / open=98.00 / sl={sl_price:.4f}")


# ── T5: 8h 超保有 → funding 控除 / 跨がなければ 0 ───────────────────────────
def test_t5_funding() -> None:
    """funding 精算境界(08:00 UTC)を跨ぐトレードは funding 控除あり・跨がなければ 0。"""
    n = 40
    closes = np.full(n, 100.0)
    highs = np.full(n, 100.02)
    lows = np.full(n, 99.98)   # limit 99.99 に届く → 必ず約定
    opens = np.full(n, 100.0)

    size = 0.024
    # --- A: 07:00 発注 → fill 07:05 → 30 本保有(~09:35) で 08:00 を跨ぐ ---
    ts_a = _ts_array("2026-01-01T07:00:00", n)
    ra = simulate_trade(
        signal_idx=0, direction=LONG, size_btc=size,
        opens=opens, highs=highs, lows=lows, closes=closes, timestamps=ts_a,
        tp_pct=0.50, sl_pct=0.50, max_hold_bars=30,  # 広 TP/SL → TIME_EXIT
    )
    # --- B: 09:00 発注 → 同一 8h 窓内(08:00-16:00)で完結 → 境界跨がず ---
    ts_b = _ts_array("2026-01-01T09:00:00", n)
    rb = simulate_trade(
        signal_idx=0, direction=LONG, size_btc=size,
        opens=opens, highs=highs, lows=lows, closes=closes, timestamps=ts_b,
        tp_pct=0.50, sl_pct=0.50, max_hold_bars=30,
    )
    exp_funding = LONG * size * 100.0 * FUNDING_RATE_8H  # 1 境界分
    a_ok = ra is not None and abs(ra.funding_cost - exp_funding) < 1e-12 and ra.funding_cost > 0
    b_ok = rb is not None and rb.funding_cost == 0.0
    _check("T5 8h 跨ぎ → funding 控除あり(LONG 払い)",
           a_ok,
           f"A.funding_cost={'None' if ra is None else f'{ra.funding_cost:.8f}'} / 期待={exp_funding:.8f}")
    _check("T5 同一 8h 窓内 → funding 0",
           b_ok,
           f"B.funding_cost={'None' if rb is None else rb.funding_cost}")


# ── 補助: 0.12 BTC 上限 assert ──────────────────────────────────────────────
def test_position_cap() -> None:
    ok_total = assert_position_cap([0.04, 0.04, 0.04])  # =0.12 → OK
    over = False
    try:
        assert_position_cap([0.06, 0.06, 0.01])  # =0.13 → 違反
    except AssertionError:
        over = True
    _check("CAP 合計 0.12 BTC ちょうど → OK", abs(ok_total - 0.12) < 1e-12, f"sum={ok_total}")
    _check("CAP 合計 0.13 BTC → AssertionError", over, "0.13 BTC で例外送出")


def main() -> int:
    print("=" * 60)
    print("eval_engine.py 既知答えテスト T1-T5（計器の正しさ＝数学的事実で証明）")
    print("=" * 60)
    print("\n[T1] コインフリップ → net ≒ −往復コスト（必ず負）")
    test_t1_coinflip_negative()
    print("\n[T2] 指値 limit 不到達 → entry 0 件")
    test_t2_no_fill()
    print("\n[T3] 同 bar TP・SL 両到達 → SL 記録")
    test_t3_both_hit_sl_wins()
    print("\n[T4] SL gap 飛び越え → open 約定")
    test_t4_gap_fills_at_open()
    print("\n[T5] 8h 超保有 → funding 控除")
    test_t5_funding()
    print("\n[補助] 0.12 BTC 上限 assert")
    test_position_cap()

    n_pass = sum(1 for _, ok, _ in _results if ok)
    n_total = len(_results)
    print("\n" + "=" * 60)
    print(f"結果: {n_pass} / {n_total} pass")
    print("=" * 60)
    if n_pass == n_total:
        print("✅ 全 pass — 計器（約定/コスト 項目A）は正しく測れている")
        return 0
    print("❌ FAIL あり — 計器に誤り。下記を修正:")
    for name, ok, detail in _results:
        if not ok:
            print(f"   - {name}: {detail}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
