#!/usr/bin/env python3
"""measure_stage1_filter_edge.py — 手①: 段1 固定ロジック・フィルタの edge 測定

位置づけ（execlog 工程[2]「Entry エンジン 修正計画」手①・baseline §6.2 改訂バナー）:
  軸4（§18.5『cascade 構造不在（ML 単段 entry 判定）』cc_entry_logic_self_study.md:1574）。
  手③で判明: 手動の黒字エッジは"特徴量"でなく"特定の固定ルールの形"にある（ML が同材料から
  再抽出不可）。本スクリプトは、手動が使う"種類"の高精度セットアップを **固定ルール**で直接書き、
  「手動の勝ちパターンが正しい計器(eval_engine)で per-trade net 黒字か」を直接確認する。

  ⚠️ 手動レシピのコピーではない。テクニカルの基本セットアップ（売られすぎ反発 / 買われすぎ戻り・
  自己実現的閾値 RSI30/70・BB）で独立設計（[[feedback_priority_starting_line_only]] 整合・
  手動は"この種類で黒字"の存在証明）。

セットアップ（v1・technical_analysis §I.7 自己実現的閾値）:
  - LONG  (売られすぎ反発): rsi14<RSI_LO ∧ bb_pct_b<BB_LO ∧ adx14<ADX_MAX (レンジ)
  - SHORT (買われすぎ戻り): rsi14>RSI_HI ∧ bb_pct_b>BB_HI ∧ adx14<ADX_MAX

net の測り方: eval_engine（指値maker・不約定・SL先着/gap・taker/slippage/funding）。
  tp_pct=atr14_pct__5m×TP_MULT/100 / sl_pct=×SL_MULT/100・max_hold=K・size=0.024 BTC。

leak: 固定ルール + 既存特徴量のみ・学習なし・閾値は標準固定値(test に fit しない) → leak なし。
判定: net プラス → 土台発見（段1 に据え本建設へ）/ net マイナス → 一段大きい設計判断。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eval_engine as ee  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
CSV = REPO / "data" / "BTCUSDT-5m-bitget-2021-04-01_2026-03-31_5y.csv"
OUT_DIR = REPO / "results" / "priority_rebuild" / "primary_direction_edge"
LABELS = {
    "test_2025": REPO / "results" / "priority_rebuild" / "labels_mfe_mae_pct_test_2025.parquet",
    "test_2026_q1": REPO / "results" / "priority_rebuild" / "labels_mfe_mae_pct_test_2026_q1.parquet",
}
FEATS = ["rsi14__5m", "bb_pct_b__5m", "adx14__5m", "atr14_pct__5m",
         "stoch_k__5m", "close_vs_sma20_pct__1h", "di_plus__5m", "di_minus__5m",
         "close_vs_sma20_pct__5m"]
SIZE_BTC = 0.024


def load_bars():
    df = pd.read_csv(CSV, parse_dates=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    ts = df["timestamp"].values.astype("datetime64[ns]")
    ts_to_pos = {str(pd.Timestamp(t)): i for i, t in enumerate(ts)}
    return (df["open"].to_numpy(float), df["high"].to_numpy(float),
            df["low"].to_numpy(float), df["close"].to_numpy(float), ts, ts_to_pos)


def setups(feat: pd.DataFrame, a) -> dict:
    """固定ルールで各セットアップ該当 bar の mask を返す（原理ベース・標準閾値）。"""
    rsi, bbp, adx = feat["rsi14__5m"], feat["bb_pct_b__5m"], feat["adx14__5m"]
    stoch, h1 = feat["stoch_k__5m"], feat["close_vs_sma20_pct__1h"]
    dip, dim, sma5 = feat["di_plus__5m"], feat["di_minus__5m"], feat["close_vs_sma20_pct__5m"]
    # 基本 mean-reversion（v1）
    L_mr = (rsi < a.rsi_lo) & (bbp < a.bb_lo) & (adx < a.adx_max)
    S_mr = (rsi > a.rsi_hi) & (bbp > a.bb_hi) & (adx < a.adx_max)
    # + Stoch(20/80) + MTF（1h が支持方向）confluence
    L_mrc = L_mr & (stoch < 20) & (h1 > 0)
    S_mrc = S_mr & (stoch > 80) & (h1 < 0)
    # トレンド追随（ADX>25・押し目/戻り・cc_entry §9.1 手動も順張り使用）
    L_tf = (adx > 25) & (dip > dim) & (sma5 > 0) & (rsi > 40) & (rsi < 65)
    S_tf = (adx > 25) & (dim > dip) & (sma5 < 0) & (rsi > 35) & (rsi < 60)
    return {"LONG_mr": (L_mr, ee.LONG), "SHORT_mr": (S_mr, ee.SHORT),
            "LONG_mr+c": (L_mrc, ee.LONG), "SHORT_mr+c": (S_mrc, ee.SHORT),
            "LONG_tf": (L_tf, ee.LONG), "SHORT_tf": (S_tf, ee.SHORT)}


def measure_set(name, mask, side, feat, bars, a) -> dict:
    o, h, l, c, ts, ts_to_pos = bars
    ids = feat.index[mask.values & feat["atr14_pct__5m"].notna().values]
    nets, reasons = [], []
    months: dict[str, float] = {}
    for eid in ids:
        pos = ts_to_pos.get(eid)
        if pos is None:
            continue
        atr = float(feat.at[eid, "atr14_pct__5m"])
        tr = ee.simulate_trade(pos, side, SIZE_BTC, o, h, l, c, ts,
                               atr * a.tp_mult / 100.0, atr * a.sl_mult / 100.0,
                               max_hold_bars=a.k)
        if tr is None:
            continue
        nets.append(tr.net); reasons.append(tr.exit_reason)
        mk = str(pd.Timestamp(ts[tr.fill_idx]))[:7]
        months[mk] = months.get(mk, 0.0) + tr.net
    nets_a = np.array(nets) if nets else np.array([0.0])
    reasons_a = np.array(reasons) if reasons else np.array([""])
    n_sig = int(mask.sum())
    row = {"setup": name, "side": "LONG" if side == ee.LONG else "SHORT",
           "n_signals": n_sig, "n_filled": len(nets),
           "fill_rate": round(len(nets) / n_sig, 4) if n_sig else 0.0,
           "avg_net_per_trade": round(float(nets_a.mean()), 6),
           "median_net_per_trade": round(float(np.median(nets_a)), 6),
           "total_net": round(float(nets_a.sum()), 2),
           "win_rate_TP": round(float((reasons_a == "TP").mean()), 4),
           "sl_rate": round(float((reasons_a == "SL").mean()), 4),
           "time_rate": round(float((reasons_a == "TIME").mean()), 4),
           "monthly_net": {k: round(v, 2) for k, v in sorted(months.items())}}
    print(f"  {name:9s}({row['side']}): n={n_sig:5d} filled={len(nets):5d} "
          f"avg_net/trade={row['avg_net_per_trade']:+.6f} total={row['total_net']:+.1f} "
          f"winTP={row['win_rate_TP']:.3f}")
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--period", default="test_2025", choices=list(LABELS))
    ap.add_argument("--k", type=int, default=12)
    ap.add_argument("--tp-mult", type=float, default=1.5)
    ap.add_argument("--sl-mult", type=float, default=2.0)
    ap.add_argument("--rsi-lo", type=float, default=30.0)
    ap.add_argument("--rsi-hi", type=float, default=70.0)
    ap.add_argument("--bb-lo", type=float, default=0.10)
    ap.add_argument("--bb-hi", type=float, default=0.90)
    ap.add_argument("--adx-max", type=float, default=25.0)
    a = ap.parse_args()

    print("=" * 70)
    print(f"手① 段1固定ロジック edge | period={a.period} K={a.k} 幾何 TP×{a.tp_mult}/SL×{a.sl_mult}")
    print("setups: mr(基本 RSI/BB/ADX) / mr+c(+Stoch20/80 +1h支持) / tf(ADX>25 トレンド追随押し目)")
    print("=" * 70)

    bars = load_bars()
    feat = pd.read_parquet(LABELS[a.period], columns=FEATS)
    feat.index = feat.index.astype(str)

    rows = [measure_set(n, m, s, feat, bars, a) for n, (m, s) in setups(feat, a).items()]
    # combined
    all_net = sum(r["total_net"] for r in rows)
    all_filled = sum(r["n_filled"] for r in rows)
    combined_avg = round(all_net / all_filled, 6) if all_filled else None
    print("-" * 70)
    print(f"合算: filled={all_filled} total_net={all_net:+.1f} avg_net/trade={combined_avg}")
    print("-" * 70)

    res = {"手": "① stage1 fixed-logic filter", "period": a.period, "K": a.k,
           "geometry": f"TP×{a.tp_mult}/SL×{a.sl_mult}",
           "thresholds": {"rsi_lo": a.rsi_lo, "rsi_hi": a.rsi_hi, "bb_lo": a.bb_lo,
                          "bb_hi": a.bb_hi, "adx_max": a.adx_max},
           "setups": rows, "combined_filled": all_filled,
           "combined_total_net": round(all_net, 2), "combined_avg_net_per_trade": combined_avg,
           "verdict_hint": "固定セットアップで avg_net/trade がプラスか（手動式エッジが計器で黒字か）"}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"summary_stage1_{a.period}_K{a.k}.json"
    out.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(f"[出力] {out}")


if __name__ == "__main__":
    main()
