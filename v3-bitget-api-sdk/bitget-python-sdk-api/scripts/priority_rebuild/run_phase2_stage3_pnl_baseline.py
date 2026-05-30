"""run_phase2_stage3_pnl_baseline.py — Exit 最小版 PnL ベースライン(Stage 3 感度測定の地面)

2026-05-31 execlog 0章「合意した修正方針」step 2 の最初の一手。
業界 verify 済(2026-05-31 WebSearch): ルールベース Exit を先に baseline 化 → 後で ML 化。
Tom Basso「Exit/サイズは Entry より重要・薄い Entry でも良い管理で利益」。

何を測るか:
  前段が発火した entry に、**最小版の固定 Exit**(TP=2×ATR / SL=1.5×ATR / 時間切れ K 本)を当てたときの
  1 取引あたり NET% と月別の符号・安定性。$ 換算は cap/sizing(工程[3])次第なので出さない
  (naive 月次$は cap 無視で過大 = 関所A 異常値誤報を招く)。per-trade edge が正で安定かを先に見る。

PnL 規約(/tmp/stage3_pnl_probe.py 流用 + TIME を実リターンに精緻化):
  - TP(+1): +2.0×atr_pct  / SL(-1): -1.5×atr_pct  (Triple Barrier ラベルが結果を内包)
  - TIME(0): close[t+K]/close[t]-1 の実リターン × 方向符号(probe の 0 近似を精緻化)
  - 往復コスト 0.038% = (maker 0.014% + slip 0.005%) × 2 を控除
  - K=12(1時間相当・meta 保有ホライズンと一致)

入力:
  - 発火 entry: results/priority_rebuild/metalabel_dataset/metalabel_{period}.parquet
  - TB ラベル/atr/close: labels_mfe_mae_pct_{period}.parquet (timestamp index)
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
RES = REPO_ROOT / "results" / "priority_rebuild"
META_DIR = RES / "metalabel_dataset"
LABELS = {
    "train_2021_2024": RES / "labels_mfe_mae_pct_train_2021_2024.parquet",
    "test_2025": RES / "labels_mfe_mae_pct_test_2025.parquet",
    "test_2026_q1": RES / "labels_mfe_mae_pct_test_2026_q1.parquet",
}
TP_MULT, SL_MULT = 2.0, 1.5
COST_PCT = (0.00014 + 0.00005) * 2 * 100  # = 0.038% 往復
K = 12


def per_trade_pnl(period: str) -> pd.DataFrame:
    fired = pd.read_parquet(META_DIR / f"metalabel_{period}.parquet")
    fired["ts"] = pd.to_datetime(fired["entry_id"])

    lab = pd.read_parquet(LABELS[period], columns=[
        "close", "atr14_pct__5m",
        f"triple_barrier_label_LONG_K{K}", f"triple_barrier_label_SHORT_K{K}"])
    lab = lab.sort_index()
    # 時間切れ Exit の実リターン(% ・close は連続 5m bar 前提・Phase 0 で連続性 verify 済)
    lab["fwd_ret_pct"] = (lab["close"].shift(-K) / lab["close"] - 1.0) * 100.0

    df = fired.set_index("ts").join(
        lab[["atr14_pct__5m", "fwd_ret_pct",
             f"triple_barrier_label_LONG_K{K}", f"triple_barrier_label_SHORT_K{K}"]],
        how="left")
    df = df.dropna(subset=["atr14_pct__5m"]).copy()

    is_long = df["primary_side"].values == "LONG"
    tb = np.where(is_long, df[f"triple_barrier_label_LONG_K{K}"].values,
                  df[f"triple_barrier_label_SHORT_K{K}"].values)
    atr = df["atr14_pct__5m"].values
    dir_sign = np.where(is_long, 1.0, -1.0)
    time_ret = df["fwd_ret_pct"].values * dir_sign   # TIME 決済の実損益(方向符号)

    gross = np.where(tb == 1, TP_MULT * atr,
             np.where(tb == -1, -SL_MULT * atr, time_ret))
    df["net_pct"] = gross - COST_PCT
    df["outcome"] = np.where(tb == 1, "TP", np.where(tb == -1, "SL", "TIME"))
    return df


def report(period: str) -> None:
    df = per_trade_pnl(period)
    n = len(df)
    oc = df["outcome"].value_counts().to_dict()
    mean_net = df["net_pct"].mean()
    pos_rate = (df["net_pct"] > 0).mean()
    print(f"\n=== {period} ===")
    print(f"  発火 {n:,} | 結果 TP {oc.get('TP',0):,} / SL {oc.get('SL',0):,} / TIME {oc.get('TIME',0):,}")
    print(f"  1取引あたり NET% 平均 = {mean_net:+.4f}%  (>0 の取引割合 {100*pos_rate:.1f}%)")
    print(f"  方向別 NET%: LONG {df[df.primary_side=='LONG']['net_pct'].mean():+.4f}% / "
          f"SHORT {df[df.primary_side=='SHORT']['net_pct'].mean():+.4f}%")
    # 月別の符号・安定性
    m = df.copy(); m["month"] = m.index.to_period("M")
    g = m.groupby("month")["net_pct"].agg(["count", "mean"])
    g["mean"] = (g["mean"]).round(4)
    pos_months = (g["mean"] > 0).sum()
    print(f"  月数 {len(g)} | per-trade平均NET%が正の月 {pos_months}/{len(g)} | "
          f"月平均取引数 {g['count'].mean():.0f}")
    print(g.to_string())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--period", type=str, default=None, help="train_2021_2024 / test_2025 / test_2026_q1")
    args = ap.parse_args()
    periods = [args.period] if args.period else list(LABELS.keys())
    for p in periods:
        report(p)
    print("\n注: 固定 Exit(TP2ATR/SL1.5ATR/時間切れK12)・全発火 entry・flat(cap/sizing 無視)。"
          "\n    $ 換算は工程[3] sizing/cap で行う(naive 月次$は cap 無視で過大なため出さない)。"
          "\n    まず per-trade NET% が正で月別安定かを見る = Exit 最小版の地面。")


if __name__ == "__main__":
    main()
