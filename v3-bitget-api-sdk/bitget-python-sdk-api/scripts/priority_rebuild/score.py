#!/usr/bin/env python3
"""score.py — 味見の機械（審判）: 売買記録 → 手数料込み net を月いくらで返す

役割（選手と審判の分離）:
  これは「審判」。戦略（ML / 手動）が出した売買記録を受け取り、正しいコストで
  「1 ヶ月いくら net で儲けたか」を **数字 1 つ**で返すだけ。戦略のロジックは一切含まない。
  どんな戦略でも、同じこの審判に通して比較する（＝固定した1つのスコアボード）。

入力 CSV に必要な列:
  entry_time, exit_time, side(LONG/SHORT), size_btc, entry_price, exit_price, exit_reason

コスト（eval_engine の確定値を流用・exchange_spec.md audit#19）:
  entry = 指値 maker / exit = TP_FILLED は maker・それ以外は成行 taker + slippage /
  funding = 保有中の 8h 境界(00/08/16 UTC)ごと dir×size×mark×rate（LONG 払い・SHORT 受取）。
  net = gross − entry_fee − exit_fee − slippage − funding。

正しさの担保:
  コスト定数と funding 境界計算は eval_engine（既知答えテスト T1-T5 pass 済）から import。
  実行時に「再計算した gross/fee が CSV の値と一致するか」を自己検算で出す（審判がデータを
  正しく読めている証拠）→ そのうえで CSV に欠けている slippage+funding を足した分が地面の差。
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eval_engine as ee  # noqa: E402  確定コスト定数 + funding 境界計算（検証済み計器）

# TP_FILLED と SL_FILLED は placePosTpsl 指値（maker）= run_once_v9.py L320-348 で executePrice=triggerPrice 確認済
# （手動は手数料負け回避で entry/exit とも maker 優先）。成行 taker は TIME / TRAIL_EXIT / MFE_STALE_CUT /
# STOCH_REVERSE 等の能動クローズ（close_market_order）のみ。
MAKER_EXIT_REASONS = {"TP_FILLED", "SL_FILLED"}


def _funding_for_trade(entry_ts: pd.Timestamp, exit_ts: pd.Timestamp,
                       direction: int, size: float, mark: float) -> float:
    """保有期間中の funding 合計（LONG 払い=正で控除 / SHORT 受取=負で加算）。
    mark は近似として entry_price を使用（funding は極小・$2000 ポジ×0.0002%/8h≒$0.004/回）。"""
    from datetime import timezone
    e = entry_ts.to_pydatetime().replace(tzinfo=timezone.utc)
    x = exit_ts.to_pydatetime().replace(tzinfo=timezone.utc)
    cost = 0.0
    for _ in ee._funding_boundaries(e, x):
        cost += direction * size * mark * ee.FUNDING_RATE_8H
    return cost


def score(df: pd.DataFrame) -> dict:
    df = df.copy()
    df["entry_time"] = pd.to_datetime(df["entry_time"])
    df["exit_time"] = pd.to_datetime(df["exit_time"])
    df["dir"] = np.where(df["side"].str.upper() == "LONG", 1, -1)

    recomputed = []
    for _, r in df.iterrows():
        size = float(r["size_btc"]); ep = float(r["entry_price"]); xp = float(r["exit_price"])
        d = int(r["dir"]); reason = str(r["exit_reason"])
        gross = size * (xp - ep) * d
        entry_fee = ep * size * ee.MAKER_FEE                       # entry は常に指値 maker
        is_taker = reason not in MAKER_EXIT_REASONS
        exit_fee = xp * size * (ee.TAKER_FEE if is_taker else ee.MAKER_FEE)
        slippage = (xp * size * ee.SLIPPAGE) if is_taker else 0.0  # 成行のみ
        funding = _funding_for_trade(r["entry_time"], r["exit_time"], d, size, ep)
        net = gross - entry_fee - exit_fee - slippage - funding
        recomputed.append((gross, entry_fee + exit_fee, slippage, funding, net))

    rc = pd.DataFrame(recomputed, columns=["gross", "fee", "slippage", "funding", "net"])
    df = pd.concat([df.reset_index(drop=True), rc], axis=1)
    df["month"] = df["entry_time"].dt.strftime("%Y-%m")

    monthly = df.groupby("month")["net"].agg(["sum", "count"]).rename(
        columns={"sum": "net_usd", "count": "n"})
    n_months = len(monthly)
    total = float(df["net"].sum())

    # 自己検算: 再計算 gross/fee が CSV の既存列と一致するか（審判が正しく読めている証拠）
    selfcheck = {}
    if "gross_usd" in df.columns:
        selfcheck["gross_diff_max"] = float((df["gross"] - df["gross_usd"]).abs().max())
    if "fee_usd" in df.columns:
        selfcheck["fee_diff_max"] = float((df["fee"] - df["fee_usd"]).abs().max())
    if "net_usd" in df.columns:
        selfcheck["csv_net_total"] = float(df["net_usd"].sum())  # CSV(slippage/funding 抜き)の net

    return {"monthly": monthly, "n_months": n_months, "total": total,
            "monthly_avg": total / n_months if n_months else 0.0,
            "n_trades": len(df), "selfcheck": selfcheck,
            "slippage_total": float(df["slippage"].sum()),
            "funding_total": float(df["funding"].sum())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trades_csv", help="売買記録 CSV（entry/exit/side/size/price/exit_reason 列）")
    ap.add_argument("--start", default=None, help="採点開始日 YYYY-MM-DD（entry_time で絞る・含む）")
    ap.add_argument("--end", default=None, help="採点終了日 YYYY-MM-DD（含む）")
    a = ap.parse_args()

    df = pd.read_csv(a.trades_csv)
    if a.start or a.end:
        et = pd.to_datetime(df["entry_time"])
        if a.start:
            df = df[et >= pd.Timestamp(a.start)]
        if a.end:
            df = df[pd.to_datetime(df["entry_time"]) < pd.Timestamp(a.end) + pd.Timedelta(days=1)]
        df = df.reset_index(drop=True)
        print(f"[期間フィルタ] {a.start or '最初'} 〜 {a.end or '最後'} → {len(df)} trades")
    res = score(df)

    print("=" * 64)
    print(f"審判（味見の機械）: {Path(a.trades_csv).name}")
    print(f"取引数 {res['n_trades']} / 期間 {res['n_months']} ヶ月")
    print("=" * 64)
    print(res["monthly"].to_string())
    print("-" * 64)
    print(f"★ 月平均 net = ${res['monthly_avg']:.2f}/月   （合計 ${res['total']:.2f}）")
    print("-" * 64)
    sc = res["selfcheck"]
    if "csv_net_total" in sc:
        print(f"[自己検算] gross 最大差 ${sc.get('gross_diff_max', float('nan')):.4f} / "
              f"fee 最大差 ${sc.get('fee_diff_max', float('nan')):.4f}  (≒0 なら審判は CSV を正しく読めている)")
        print(f"[地面の差] CSV net 合計 ${sc['csv_net_total']:.2f}  →  審判 net 合計 ${res['total']:.2f}  "
              f"(差 = 追加した slippage ${res['slippage_total']:.2f} + funding ${res['funding_total']:.2f})")


if __name__ == "__main__":
    main()
