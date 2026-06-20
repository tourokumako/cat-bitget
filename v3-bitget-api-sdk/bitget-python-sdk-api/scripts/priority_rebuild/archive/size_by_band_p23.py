#!/usr/bin/env python3
"""size_by_band_p23.py — E7 最初の一手（ML無し）: P23 を bb傾き×ATR% の帯でサイズを振る

狙い（レバー確認）:
  E6 診断で「P23 の net は『下げがどこまで伸びるか』で決まる／入口指標(bb傾き・ATR%)は
  それを単調に示すのに ○× 分類は盲目(prob フラット)」と判明。
  → まず ML 無しで、強い下げ(bb傾き急)×高ボラ(ATR% 大)の手を厚く、横ばい・低ボラを薄く
     サイズを振り直すだけで、V9 手書き P23 の net($1943) を超えるか = サイジングのレバーが
     あるかを安く確認する。効けば次段で MFE(payoff) 学習に置き換えて精度を上げる。

設計（V9 不変・side/add/出口は V9 のまま・size だけ変える）:
  - 入力 baseline = trades_p23_full_test.csv（V9 手書き P23 の採点期間 481 件＝$1943 の集合）
  - 帯の閾値は【学習期間 <2025-04 の候補】から決め、採点期間に適用（採点を覗かない=H2/H8 leak回避）
  - 特徴量は pct 化（bb_slope/entry_price, atr/entry_price）= 価格非依存(H6)
  - size_mult は【事前固定】2.0/1.0/0.5（結果を見て動かさない=過剰最適化(類型C)回避）
  - per-trade size を [0.0001, 0.12] に clip（最小注文 H9 / 合計上限 H1）を assert で物理確認

判定: 出力 CSV を score.py（固定審判）に通し、地面 V9 手書き $1943 と比較。
"""
from __future__ import annotations
import os
import sys
import pandas as pd
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
RATCHET = os.path.join(ROOT, "results", "priority_rebuild", "ratchet")

BASELINE = os.path.join(RATCHET, "trades_p23_full_test.csv")   # V9手書きP23・採点481件
CANDID = os.path.join(RATCHET, "p23_candidates_full.csv")      # 全期間2045（閾値算出に学習期間を使う）
OUT = os.path.join(RATCHET, "trades_p23_bandsize_test.csv")

SCORE_START = pd.Timestamp("2025-04-01")   # 採点開始（これ未満=学習期間）
SIZE_CAP = 0.12        # H1 合計上限（P23 は基本1ポジ運用＝per-trade 上限と同じ）
SIZE_MIN = 0.0001      # H9 最小注文
# size_mult は事前固定（結果を見て動かさない）
MULT_STRONG = 2.0
MULT_MID = 1.0
MULT_WEAK = 0.5


def pct_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["bb_slope_pct"] = df["bb_mid_slope_at_entry"] / df["entry_price"] * 100.0   # H6 価格非依存
    df["atr_pct"] = df["atr_14"] / df["entry_price"] * 100.0
    return df


def main():
    base = pd.read_csv(BASELINE)
    base["entry_time"] = pd.to_datetime(base["entry_time"])
    base = base[(base.entry_time >= SCORE_START) &
                (base.entry_time <= pd.Timestamp("2025-12-31"))].reset_index(drop=True)
    base = pct_features(base)

    cand = pd.read_csv(CANDID)
    cand["entry_time"] = pd.to_datetime(cand["entry_time"])
    train = cand[cand.entry_time < SCORE_START].copy()
    train = pct_features(train)

    # H8/H2 leak assert: 閾値は学習期間のみから。学習末 < 採点始 を物理確認。
    assert train["entry_time"].max() < SCORE_START, "leak: 学習データが採点期間に侵入"

    # 帯の閾値（学習期間の分位・事前固定）。bb_slope_pct は負に大きいほど強い下げ。
    bb_p33 = train["bb_slope_pct"].quantile(0.33)   # これ以下=強い下げ
    bb_p67 = train["bb_slope_pct"].quantile(0.67)   # これ以上=横ばい/上げ寄り
    atr_p33 = train["atr_pct"].quantile(0.33)       # これ以下=低ボラ
    atr_p67 = train["atr_pct"].quantile(0.67)       # これ以上=高ボラ

    def band_mult(r):
        strong_dn = r["bb_slope_pct"] <= bb_p33
        high_vol = r["atr_pct"] >= atr_p67
        weak_dn = r["bb_slope_pct"] >= bb_p67
        low_vol = r["atr_pct"] <= atr_p33
        if strong_dn and high_vol:      # 強い下げ＋高ボラ → 厚く
            return MULT_STRONG
        if weak_dn or low_vol:          # 横ばい/上げ寄り or 低ボラ → 薄く
            return MULT_WEAK
        return MULT_MID

    base["size_mult"] = base.apply(band_mult, axis=1)
    old_size = base["size_btc"].copy()
    base["size_btc"] = (old_size * base["size_mult"]).clip(SIZE_MIN, SIZE_CAP)

    # B（物理停止）: H1 合計上限 / H9 最小注文
    assert base["size_btc"].max() <= SIZE_CAP + 1e-9, "H1 違反: size > 0.12"
    assert base["size_btc"].min() >= SIZE_MIN - 1e-12, "H9 違反: size < 0.0001"

    # gross/fee/net も size 比例で更新（score.py 自己検算が通るように・netは審判が再計算）
    ratio = base["size_btc"] / old_size
    for c in ["gross_usd", "fee_usd", "net_usd", "mfe_usd", "mae_usd"]:
        if c in base.columns:
            base[c] = base[c] * ratio

    base.to_csv(OUT, index=False)

    # 報告用サマリ（レバーが reallocation か単なる増し玉かを見分ける control）
    exp_old = float(old_size.sum())
    exp_new = float(base["size_btc"].sum())
    print("=" * 60)
    print(f"閾値(学習): bb_slope_pct p33={bb_p33:.5f} p67={bb_p67:.5f} / atr_pct p33={atr_p33:.4f} p67={atr_p67:.4f}")
    print(f"帯別件数: 厚(2.0)={int((base.size_mult==2.0).sum())} "
          f"中(1.0)={int((base.size_mult==1.0).sum())} 薄(0.5)={int((base.size_mult==0.5).sum())} / 計{len(base)}")
    print(f"平均倍率={base.size_mult.mean():.3f}  総BTC建玉 {exp_old:.3f} → {exp_new:.3f} "
          f"(比 {exp_new/exp_old:.3f}: 1.0付近なら配分替え/大きいなら増し玉)")
    print(f"clip で 0.12 頭打ちした件数: {int((base.size_btc>=SIZE_CAP-1e-9).sum())}")
    print(f"CSV net 合計(参考・slippage/funding 抜き): ${base.net_usd.sum():.1f}  (baseline $2017.8)")
    print(f"出力: {OUT}")


if __name__ == "__main__":
    main()
