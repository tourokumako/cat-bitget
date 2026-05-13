#!/usr/bin/env python3
"""
run_phase5_e_funding_estimate.py — Phase 5-e: Funding Rate 概算控除

背景:
  Bitget USDT Perp は 8h 毎 funding 精算 (00:00 / 08:00 / 16:00 UTC)。
  Phase 4-b/5/6-b/5-d は funding 未控除 → PnL 過大評価の可能性。
  → 固定率 0.01%/8h で概算控除し、$1,900/月 合格ラインへの影響を確認。

精算ルール (Bitget USDT-FUTURES BTCUSDT 仕様):
  - funding 発生時刻: trade 持続区間 (entry_ts, exit_ts] に含まれる UTC 00:00/08:00/16:00
  - funding 金額 = position_value × funding_rate
    position_value = pos_size_btc × entry_price
    funding_rate = 0.0001 (=0.01%/8h・概算固定値)
  - 符号: BTC は通常 funding > 0 で LONG 支払い / SHORT 受取
    pnl_after = pnl_orig - dir × funding_count × pos_value × rate
    (dir = +1 LONG, -1 SHORT)

スコープ:
  Phase 5-d 出力 (cap=1/2/3/5 × 2025/2026Q1) 計 8 ファイルに対し
  funding 控除 → 月次集計 → 合格判定再評価

入力:
  results/priority_rebuild/ml_phase5_d/trades_{2025,2026q1}_cap{1,2,3,5}_recalc.parquet
  data/BTCUSDT-5m-2021-04-01_03-31_1826d.csv (entry_price 補完用)

出力 (results/priority_rebuild/ml_phase5_e/):
  trades_{2025,2026q1}_cap{N}_funding.parquet × 8
  monthly_{2025,2026q1}_funding.csv
  summary.md
  phase5e_log_<TS>.txt

再現コマンド:
  python3 scripts/priority_rebuild/run_phase5_e_funding_estimate.py
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
P5D_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase5_d"
OUT_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase5_e"
OHLC_CSV = REPO_ROOT / "data" / "BTCUSDT-5m-2021-04-01_03-31_1826d.csv"

POSITION_CAPS = (1, 2, 3, 5)
FUNDING_RATE_PER_8H = 0.0001  # 0.01%/8h (Bitget BTCUSDT 概算固定)
THRESHOLD_PASS_MONTHLY = 1900.0

TS = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
LOG_PATH = OUT_DIR / f"phase5e_log_{TS}.txt"


def log(msg: str) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{now}] {msg}"
    print(line, flush=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")


def load_close_lookup() -> pd.Series:
    """OHLC CSV の close を timestamp index で返す (entry_price 補完用)"""
    df = pd.read_csv(OHLC_CSV)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df.set_index("timestamp")["close"]


def count_funding_events(entry_ts: pd.Series, exit_ts: pd.Series) -> np.ndarray:
    """trade 持続区間 (entry_ts, exit_ts] に含まれる UTC 00/08/16 時の数を bulk 計算。

    各 trade で funding hour ( = 8h 周期 ) を切り取る式:
      n = floor(exit / 8h) - floor(entry / 8h)
    境界扱い: entry_ts ちょうどに UTC 0/8/16h が来た場合は含めない (>)
              exit_ts ちょうどに来た場合は含める (≤)
    """
    entry_sec = entry_ts.astype("int64") // 10**9
    exit_sec = exit_ts.astype("int64") // 10**9
    period_sec = 8 * 3600
    # floor 除算: entry_sec / 8h と exit_sec / 8h
    # (entry, exit] 範囲: floor(exit / period) - floor((entry) / period) は
    #   entry 自身が境界なら除外、exit 境界なら含める…これだと不一致なので
    # 安全策: n = floor((exit - 1) / period) - floor((entry - 1) / period)
    # (a, b] と表現: floor((b-1) / p) - floor((a-1) / p) ではなく
    # 直接: floor(exit / period) - floor(entry / period) は
    #   (entry が境界 = false 含む, exit 境界 = true 含む)
    # ここで「(entry_ts, exit_ts]」を期待 (entry時点は funding免除・exit時点は含む)
    n = (exit_sec // period_sec) - (entry_sec // period_sec)
    return n.astype(np.int32).values


def apply_funding(df: pd.DataFrame, close_lookup: pd.Series) -> pd.DataFrame:
    """trade に entry_price 補完 → funding event 数 × pos_value × rate を控除"""
    df = df.copy()
    df["entry_ts"] = pd.to_datetime(df["entry_ts"])
    df["exit_ts"] = pd.to_datetime(df["exit_ts"])

    # entry_price 補完 (close_lookup から)
    ep = close_lookup.reindex(df["entry_ts"]).values
    df["entry_price"] = ep
    # 万一 NaN (timestamp 不一致) があれば直近 close で補完
    if pd.isna(df["entry_price"]).any():
        # backward fill
        merged = pd.merge_asof(
            df.sort_values("entry_ts")[["entry_ts"]],
            close_lookup.rename("close").reset_index(),
            left_on="entry_ts",
            right_on="timestamp",
            direction="backward",
        )
        df = df.sort_values("entry_ts").reset_index(drop=True)
        df["entry_price"] = merged["close"].values

    # funding 計算
    df["funding_events"] = count_funding_events(df["entry_ts"], df["exit_ts"])
    df["position_value_usd"] = df["pos_size_btc"] * df["entry_price"]
    df["funding_per_trade_usd"] = (
        df["funding_events"] * df["position_value_usd"] * FUNDING_RATE_PER_8H
    )

    # 符号: LONG = -funding, SHORT = +funding
    direction = np.where(df["side"] == "LONG", -1.0, +1.0)
    df["pnl_usd_before_funding"] = df["pnl_usd"]
    df["pnl_usd"] = df["pnl_usd"] + direction * df["funding_per_trade_usd"]
    df["pnl_diff_funding"] = df["pnl_usd"] - df["pnl_usd_before_funding"]
    return df.sort_values("entry_ts").reset_index(drop=True)


def monthly_pnl(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["month"] = pd.to_datetime(df["entry_ts"]).dt.to_period("M").astype(str)
    agg = (
        df.groupby("month", sort=True)
        .agg(
            n=("pnl_usd", "size"),
            pnl_sum=("pnl_usd", "sum"),
            pnl_before_funding=("pnl_usd_before_funding", "sum"),
            funding_total=("funding_per_trade_usd", "sum"),
            win_rate=("pnl_usd", lambda x: (x > 0).mean()),
        )
        .reset_index()
    )
    agg["pass_1900"] = agg["pnl_sum"] >= THRESHOLD_PASS_MONTHLY
    return agg


def process_period(period_label: str, monthly_period_count: int, close_lookup: pd.Series) -> pd.DataFrame:
    log(f"--- {period_label} ---")
    monthly_all = []
    for cap in POSITION_CAPS:
        in_path = P5D_DIR / f"trades_{period_label}_cap{cap}_recalc.parquet"
        df_in = pd.read_parquet(in_path)
        n_in = len(df_in)

        df_funded = apply_funding(df_in, close_lookup)

        # LONG/SHORT 内訳 (funding 影響の方向確認)
        long_funding = df_funded.loc[df_funded["side"] == "LONG", "funding_per_trade_usd"].sum()
        short_funding = df_funded.loc[df_funded["side"] == "SHORT", "funding_per_trade_usd"].sum()
        long_n = (df_funded["side"] == "LONG").sum()
        short_n = (df_funded["side"] == "SHORT").sum()

        total_before = df_funded["pnl_usd_before_funding"].sum()
        total_after = df_funded["pnl_usd"].sum()
        funding_net = total_after - total_before
        avg_events = df_funded["funding_events"].mean()

        m = monthly_pnl(df_funded)
        m["cap"] = cap
        monthly_all.append(m)
        passn = int(m["pass_1900"].sum())

        log(
            f"  cap={cap}: n={n_in:,} | before=${total_before:,.0f} -> after=${total_after:,.0f} "
            f"| funding_net=${funding_net:+,.0f} "
            f"| monthly_avg=${total_after/monthly_period_count:,.0f} "
            f"| pass={passn}/{monthly_period_count}"
        )
        log(
            f"          LONG n={long_n:,} fund_paid=${long_funding:,.0f} | "
            f"SHORT n={short_n:,} fund_recv=${short_funding:,.0f} | "
            f"avg_events/trade={avg_events:.2f}"
        )

        out_path = OUT_DIR / f"trades_{period_label}_cap{cap}_funding.parquet"
        df_funded.to_parquet(out_path)

    df_m = pd.concat(monthly_all, ignore_index=True)
    df_m.to_csv(OUT_DIR / f"monthly_{period_label}_funding.csv", index=False)
    log(f"saved monthly_{period_label}_funding.csv")
    return df_m


def main() -> None:
    t0 = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log("=== Phase 5-e START ===")
    log(f"FUNDING_RATE_PER_8H = {FUNDING_RATE_PER_8H} (固定・概算)")
    log(f"POSITION_CAPS = {POSITION_CAPS}")

    log("loading OHLC close lookup ...")
    close_lookup = load_close_lookup()
    log(f"  close_lookup: {len(close_lookup):,} bars")

    df_m25 = process_period("2025", 12, close_lookup)
    df_m26 = process_period("2026q1", 3, close_lookup)

    elapsed = time.time() - t0
    log(f"=== Phase 5-e END (elapsed={elapsed/60:.2f} min) ===")
    write_summary(elapsed, df_m25, df_m26)


def write_summary(elapsed: float, df_m25: pd.DataFrame, df_m26: pd.DataFrame) -> None:
    md = []
    md.append("# Phase 5-e — Funding Rate 概算控除\n\n")
    md.append(f"- 実行 TS: {TS}\n")
    md.append(f"- 所要: {elapsed/60:.2f} 分\n")
    md.append(f"- Funding 率: {FUNDING_RATE_PER_8H} (= 0.01%/8h・Bitget BTCUSDT 概算固定値)\n")
    md.append(f"- Funding 発生: 持続区間 (entry_ts, exit_ts] の UTC 00:00 / 08:00 / 16:00\n")
    md.append("- 符号: LONG = -funding (支払い) / SHORT = +funding (受取)\n")
    md.append("- 入力: Phase 5-d の trades_{period}_cap{N}_recalc.parquet\n\n")

    md.append("## 再現コマンド\n\n")
    md.append("```\npython3 scripts/priority_rebuild/run_phase5_e_funding_estimate.py\n```\n\n")

    def cap_table(df_m: pd.DataFrame, n_months: int, label: str) -> str:
        lines = [f"## {label} cap 別 (funding 控除後)\n\n"]
        lines.append("| cap | n | before ($) | after ($) | funding ($) | monthly avg ($) | pass $1,900 |\n")
        lines.append("|---|---|---|---|---|---|---|\n")
        for cap in POSITION_CAPS:
            sub = df_m[df_m["cap"] == cap]
            n_trades = sub["n"].sum()
            before = sub["pnl_before_funding"].sum()
            after = sub["pnl_sum"].sum()
            funding = sub["funding_total"].sum()
            avg = after / n_months if n_months else 0
            passn = int(sub["pass_1900"].sum())
            lines.append(
                f"| {cap} | {int(n_trades):,} | {before:,.0f} | {after:,.0f} | "
                f"{after - before:+,.0f} | {avg:,.0f} | {passn}/{n_months} |\n"
            )
        return "".join(lines) + "\n"

    md.append(cap_table(df_m25, 12, "test 2025 (仮テスト)"))
    md.append(cap_table(df_m26, 3, "test 2026 Q1 (本テスト)"))

    md.append("## test 2025 月次内訳 (funding 控除後)\n\n")
    md.append("| month | cap | n | before ($) | funding ($) | after ($) | pass $1,900 |\n")
    md.append("|---|---|---|---|---|---|---|\n")
    for _, r in df_m25.iterrows():
        md.append(
            f"| {r['month']} | {int(r['cap'])} | {int(r['n']):,} | "
            f"{r['pnl_before_funding']:,.0f} | {-r['funding_total']:+,.0f} | "
            f"{r['pnl_sum']:,.0f} | {'✅' if r['pass_1900'] else '❌'} |\n"
        )

    md.append("\n## test 2026 Q1 月次内訳 (funding 控除後)\n\n")
    md.append("| month | cap | n | before ($) | funding ($) | after ($) | pass $1,900 |\n")
    md.append("|---|---|---|---|---|---|---|\n")
    for _, r in df_m26.iterrows():
        md.append(
            f"| {r['month']} | {int(r['cap'])} | {int(r['n']):,} | "
            f"{r['pnl_before_funding']:,.0f} | {-r['funding_total']:+,.0f} | "
            f"{r['pnl_sum']:,.0f} | {'✅' if r['pass_1900'] else '❌'} |\n"
        )

    md.append("\n## 注記\n\n")
    md.append("- funding 率は 0.01%/8h 固定の概算。実際は時期で変動 (BTC は通常 0〜0.03%/8h)。\n")
    md.append("- LONG 多めなら funding 控除がマイナス効く・SHORT 多めならプラスに効く。\n")
    md.append("- 厳密化が必要なら Bitget API の funding history で trade 毎に再計算 (案 B)。\n")
    md.append("- funding 列: funding ($) は LONG/SHORT 合計の純影響 (符号は trade ごとの side による)。\n")

    with open(OUT_DIR / "summary.md", "w") as f:
        f.write("".join(md))


if __name__ == "__main__":
    main()
