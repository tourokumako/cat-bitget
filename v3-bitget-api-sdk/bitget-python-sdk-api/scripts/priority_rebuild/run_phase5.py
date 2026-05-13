#!/usr/bin/env python3
"""
run_phase5.py — ML Phase 5: 統合 Replay (Entry + Exit + Position)

指示書: bitget-python-sdk-api/cc_ml_design_spec.md §5 Phase 5

スコープ:
  1. Phase 4-b の exit_simulations.parquet から cluster_best_exit.csv で
     1 Entry 1 Exit を抽出 (cluster 別最良 Exit 適用)
  2. 時系列順に並べ、月次 PnL / 同時保有数推移 / 最大 DD 計算
  3. 指示書 §6 月次 $1,900 全月クリア判定
  4. §4 Position 「上限なし」維持 (第 1 弾)

Entry 重複扱い: 指示書 §4 「LONG/SHORT 同時保有許可・追加 Entry 許可」→ 全独立 Entry
fee: Phase 4-b 同様 Maker 0.00014 × round-trip (楽観・スリッページなし)

入力:
  results/priority_rebuild/ml_phase4_b/exit_simulations.parquet
  results/priority_rebuild/ml_phase4_b/cluster_best_exit.csv
  data/BTCUSDT-5m-2021-04-01_03-31_1826d.csv  (同時保有数計算用)

出力 (results/priority_rebuild/ml_phase5/):
  phase5_log_<TS>.txt
  trades_phase5.parquet                 採用された 1 Entry 1 Exit (時系列)
  monthly_pnl.csv                       月次 PnL / Entry 数 / 平均 / win 率
  concurrent_holdings.csv               時間別 同時保有数
  equity_curve.csv                      累積 PnL カーブ
  monthly_pnl.png                       月次棒グラフ
  equity_curve.png                      Equity 曲線
  concurrent_holdings.png               同時保有数推移
  summary.md
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[2]
P4B_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase4_b"
OUT_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase5"

SIMS_PATH = P4B_DIR / "exit_simulations.parquet"
BEST_PATH = P4B_DIR / "cluster_best_exit.csv"

THRESHOLD_PASS_MONTHLY = 1900.0  # 指示書 §6 合格ライン
WITHDRAW_LINE_MONTHLY = 500.0    # 指示書 §1.6 撤退ライン (ML 単独)

TS = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
LOG_PATH = OUT_DIR / f"phase5_log_{TS}.txt"


def log(msg: str) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{now}] {msg}"
    print(line, flush=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")


def load_trades() -> pd.DataFrame:
    """Phase 4-b 全シミュレーションから cluster 別最良 Exit のみ抽出。"""
    df_sim = pd.read_parquet(SIMS_PATH)
    df_best = pd.read_csv(BEST_PATH)
    log(f"  sims: {df_sim.shape} / best: {df_best.shape}")

    key_cols = ["cluster", "K", "side", "exit_type", "exit_param"]
    df = df_sim.merge(df_best[key_cols], on=key_cols, how="inner")
    log(f"  trades after merge (1 entry → 1 exit): {len(df):,}")

    # Entry index → exit_idx は bar 番号 (Phase 4-b の global idx を保持してる)
    # 時系列ソート
    df["entry_ts"] = pd.to_datetime(df["entry_ts"])
    df = df.sort_values("entry_ts").reset_index(drop=True)

    # exit_ts (bar index → timestamp に変換が必要だが、Phase 4-b で entry_ts のみ保持)
    # exit_idx を ts に戻すため、OHLC index を読み込む
    ohlc_path = REPO_ROOT / "data" / "BTCUSDT-5m-2021-04-01_03-31_1826d.csv"
    ohlc = pd.read_csv(ohlc_path, parse_dates=["timestamp"])
    ohlc = ohlc.set_index("timestamp").sort_index()
    ohlc_2025 = ohlc.loc["2025-01-01 00:00:00":"2025-12-31 23:55:00"]
    idx_to_ts = ohlc_2025.index.to_numpy()
    df["exit_ts"] = idx_to_ts[df["exit_idx"].clip(upper=len(idx_to_ts) - 1).values]
    df["exit_ts"] = pd.to_datetime(df["exit_ts"])
    df["hold_bars"] = (df["exit_ts"] - df["entry_ts"]).dt.total_seconds() / 300.0
    return df


def compute_concurrent_holdings(df: pd.DataFrame) -> pd.DataFrame:
    """各 5m bar の同時保有数 (LONG/SHORT 別) を計算。"""
    # 時間範囲: 2025-01-01 〜 2025-12-31
    bars = pd.date_range("2025-01-01", "2025-12-31 23:55:00", freq="5min")
    n_bars = len(bars)
    bar_to_idx = {ts: i for i, ts in enumerate(bars)}

    long_count = np.zeros(n_bars, dtype=np.int32)
    short_count = np.zeros(n_bars, dtype=np.int32)

    for row in df.itertuples(index=False):
        ei = bar_to_idx.get(row.entry_ts)
        xi = bar_to_idx.get(row.exit_ts, n_bars - 1)
        if ei is None:
            continue
        if row.side == "LONG":
            long_count[ei:xi + 1] += 1
        else:
            short_count[ei:xi + 1] += 1

    return pd.DataFrame(
        {
            "timestamp": bars,
            "long_held": long_count,
            "short_held": short_count,
            "total_held": long_count + short_count,
        }
    )


def compute_monthly_pnl(df: pd.DataFrame) -> pd.DataFrame:
    """月次 PnL / Entry 数 / 平均 / win 率 / pass判定。"""
    df["month"] = df["entry_ts"].dt.to_period("M").astype(str)
    agg = (
        df.groupby("month", sort=True)
        .agg(
            n=("pnl_usd", "size"),
            pnl_sum=("pnl_usd", "sum"),
            pnl_mean=("pnl_usd", "mean"),
            win_rate=("pnl_usd", lambda x: (x > 0).mean()),
        )
        .reset_index()
    )
    agg["pass_1900"] = agg["pnl_sum"] >= THRESHOLD_PASS_MONTHLY
    agg["pass_withdraw_500"] = agg["pnl_sum"] >= WITHDRAW_LINE_MONTHLY
    return agg


def compute_equity_curve(df: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    """累積 PnL (Entry 順)・最大ドローダウン計算。"""
    eq = df[["entry_ts", "pnl_usd"]].copy().sort_values("entry_ts").reset_index(drop=True)
    eq["cum_pnl"] = eq["pnl_usd"].cumsum()
    eq["peak"] = eq["cum_pnl"].cummax()
    eq["drawdown"] = eq["peak"] - eq["cum_pnl"]
    max_dd = float(eq["drawdown"].max())
    return eq, max_dd


def main() -> None:
    t0 = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log("=== Phase 5 START ===")

    log("loading trades (Phase 4-b → cluster best exit) ...")
    df_trades = load_trades()
    df_trades.to_parquet(OUT_DIR / "trades_phase5.parquet")
    log(f"saved trades_phase5.parquet ({len(df_trades):,} rows)")
    log(f"  date range: {df_trades['entry_ts'].min()} → {df_trades['entry_ts'].max()}")
    log(f"  total PnL: ${df_trades['pnl_usd'].sum():,.2f}")
    log(f"  mean PnL: ${df_trades['pnl_usd'].mean():.2f}")
    log(f"  win rate: {(df_trades['pnl_usd'] > 0).mean()*100:.1f}%")

    log("computing monthly PnL ...")
    df_monthly = compute_monthly_pnl(df_trades)
    df_monthly.to_csv(OUT_DIR / "monthly_pnl.csv", index=False)
    log("saved monthly_pnl.csv")
    log(f"  months pass $1,900: {df_monthly['pass_1900'].sum()}/12")
    log(f"  months pass $500: {df_monthly['pass_withdraw_500'].sum()}/12")
    worst_month = df_monthly.loc[df_monthly["pnl_sum"].idxmin()]
    best_month = df_monthly.loc[df_monthly["pnl_sum"].idxmax()]
    log(f"  worst month: {worst_month['month']} ${worst_month['pnl_sum']:,.0f}")
    log(f"  best  month: {best_month['month']} ${best_month['pnl_sum']:,.0f}")

    log("computing concurrent holdings ...")
    df_conc = compute_concurrent_holdings(df_trades)
    df_conc.to_csv(OUT_DIR / "concurrent_holdings.csv", index=False)
    log("saved concurrent_holdings.csv")
    log(f"  max concurrent total: {df_conc['total_held'].max()}")
    log(f"  max concurrent LONG: {df_conc['long_held'].max()}")
    log(f"  max concurrent SHORT: {df_conc['short_held'].max()}")
    log(f"  mean concurrent total: {df_conc['total_held'].mean():.1f}")

    log("computing equity curve ...")
    df_eq, max_dd = compute_equity_curve(df_trades)
    df_eq.to_csv(OUT_DIR / "equity_curve.csv", index=False)
    log(f"saved equity_curve.csv (max_dd=${max_dd:,.0f})")

    # 可視化
    log("plotting ...")
    # 月次棒グラフ
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = ["green" if v >= THRESHOLD_PASS_MONTHLY else ("orange" if v >= WITHDRAW_LINE_MONTHLY else "red")
              for v in df_monthly["pnl_sum"]]
    ax.bar(df_monthly["month"], df_monthly["pnl_sum"], color=colors)
    ax.axhline(THRESHOLD_PASS_MONTHLY, color="black", linestyle="--", linewidth=1, label=f"$1,900 合格ライン")
    ax.axhline(WITHDRAW_LINE_MONTHLY, color="gray", linestyle=":", linewidth=1, label=f"$500 撤退ライン")
    ax.set_title("Phase 5 — Monthly NET PnL (2025)")
    ax.set_ylabel("USD")
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "monthly_pnl.png", dpi=110)
    plt.close(fig)

    # Equity curve
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df_eq["entry_ts"], df_eq["cum_pnl"], label="cumulative PnL")
    ax.fill_between(df_eq["entry_ts"], df_eq["cum_pnl"], df_eq["peak"], color="red", alpha=0.2, label="drawdown")
    ax.set_title(f"Phase 5 — Equity curve (max DD ${max_dd:,.0f})")
    ax.set_ylabel("USD")
    ax.legend()
    plt.tight_layout()
    plt.savefig(OUT_DIR / "equity_curve.png", dpi=110)
    plt.close(fig)

    # 同時保有数
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(df_conc["timestamp"], df_conc["long_held"], label="LONG", color="green", linewidth=0.5)
    ax.plot(df_conc["timestamp"], df_conc["short_held"], label="SHORT", color="red", linewidth=0.5)
    ax.plot(df_conc["timestamp"], df_conc["total_held"], label="TOTAL", color="black", linewidth=0.7)
    ax.set_title("Phase 5 — Concurrent holdings (5m resolution)")
    ax.set_ylabel("# positions")
    ax.legend()
    plt.tight_layout()
    plt.savefig(OUT_DIR / "concurrent_holdings.png", dpi=110)
    plt.close(fig)

    log("plots saved")

    elapsed = time.time() - t0
    log(f"=== Phase 5 END (elapsed={elapsed/60:.2f} min) ===")
    write_summary(elapsed, df_trades, df_monthly, df_conc, max_dd)


def write_summary(
    elapsed: float,
    df_trades: pd.DataFrame,
    df_monthly: pd.DataFrame,
    df_conc: pd.DataFrame,
    max_dd: float,
) -> None:
    md = []
    md.append("# Phase 5 — 統合 Replay (Entry + Exit + Position)\n\n")
    md.append(f"- 実行 TS: {TS}\n")
    md.append(f"- 所要: {elapsed/60:.2f} 分\n")
    md.append(f"- 入力: Phase 4-b cluster 別最良 Exit\n\n")
    md.append("## 再現コマンド\n\n")
    md.append("```\npython3 scripts/priority_rebuild/run_phase5.py\n```\n\n")

    n_total = len(df_trades)
    total_pnl = df_trades["pnl_usd"].sum()
    win_rate = (df_trades["pnl_usd"] > 0).mean()
    mean_pnl = df_trades["pnl_usd"].mean()
    monthly_avg = total_pnl / 12.0

    md.append("## 全体集計\n\n")
    md.append(f"- 総 Entry 数: **{n_total:,}**\n")
    md.append(f"- 総 PnL: **${total_pnl:,.0f}**\n")
    md.append(f"- 月次平均: **${monthly_avg:,.0f}**\n")
    md.append(f"- 平均 PnL/Entry: ${mean_pnl:.2f}\n")
    md.append(f"- Win rate: {win_rate*100:.1f}%\n")
    md.append(f"- 最大 DD: **${max_dd:,.0f}**\n\n")

    pass_1900 = int(df_monthly["pass_1900"].sum())
    pass_500 = int(df_monthly["pass_withdraw_500"].sum())
    md.append("## 合格判定 (指示書 §6)\n\n")
    md.append(f"- 月次 $1,900 全月クリア: **{pass_1900}/12** {'✅ 合格' if pass_1900 == 12 else '❌ 未達月あり'}\n")
    md.append(f"- 月次 $500 全月クリア (§1.6 撤退ライン): **{pass_500}/12**\n\n")

    md.append("## 月次内訳\n\n")
    md.append("| month | n | pnl_sum ($) | pnl_mean ($) | win_rate | pass_1900 | pass_500 |\n")
    md.append("|---|---|---|---|---|---|---|\n")
    for _, r in df_monthly.iterrows():
        md.append(
            f"| {r['month']} | {int(r['n']):,} | {r['pnl_sum']:,.0f} | "
            f"{r['pnl_mean']:.2f} | {r['win_rate']*100:.1f}% | "
            f"{'✅' if r['pass_1900'] else '❌'} | "
            f"{'✅' if r['pass_withdraw_500'] else '❌'} |\n"
        )

    md.append("\n## 同時保有数統計\n\n")
    md.append(f"- max concurrent total: **{int(df_conc['total_held'].max())}**\n")
    md.append(f"- max concurrent LONG : {int(df_conc['long_held'].max())}\n")
    md.append(f"- max concurrent SHORT: {int(df_conc['short_held'].max())}\n")
    md.append(f"- mean concurrent total: {df_conc['total_held'].mean():.1f}\n\n")

    md.append("## 注記\n\n")
    md.append("- Position 同時保有上限: なし (指示書 §4 第 1 弾)\n")
    md.append("- 約定モデル: 楽観 Maker 指値 fill / fee=0.00014 × round-trip\n")
    md.append("- スリッページ・流動性制限なし\n")
    md.append("- max DD と 同時保有数が極端なら Phase 5-b で制限導入を検討\n")
    md.append("- 月次未達月があれば Phase 4 Exit 再設計 / 月次原因分析を実施\n")
    with open(OUT_DIR / "summary.md", "w") as f:
        f.write("".join(md))


if __name__ == "__main__":
    main()
