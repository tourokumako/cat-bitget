#!/usr/bin/env python3
"""
run_phase5_b.py — ML Phase 5-b: Position 同時保有上限導入で再 Replay

指示書: bitget-python-sdk-api/cc_ml_design_spec.md §4 / §5 Phase 5
背景: Phase 5 で max concurrent=298 → 現実運用不可。
      上限 N を入れて月次 NET 変化を見る (3 段階比較)。

ロジック:
  - Phase 5 trades_phase5 を Entry 時刻順に並べる
  - 各 Entry について 「現在の同時保有数 < N なら採用、超えてたら却下」
  - FIFO (early-arrival 採用) ・LONG/SHORT 区別なし (total cap)
  - cap ∈ {5, 10, 20}

入力:
  results/priority_rebuild/ml_phase5/trades_phase5.parquet

出力 (results/priority_rebuild/ml_phase5_b/):
  phase5b_log_<TS>.txt
  trades_cap{N}.parquet × 3              採用された Entry
  monthly_pnl_cap{N}.csv × 3
  summary.md
  monthly_pnl_comparison.png             4 案 (none/5/10/20) の月次比較
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
P5_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase5"
OUT_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase5_b"

TRADES_PATH = P5_DIR / "trades_phase5.parquet"

POSITION_CAPS = (5, 10, 20)
THRESHOLD_PASS_MONTHLY = 1900.0
WITHDRAW_LINE_MONTHLY = 500.0

TS = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
LOG_PATH = OUT_DIR / f"phase5b_log_{TS}.txt"


def log(msg: str) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{now}] {msg}"
    print(line, flush=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")


def replay_with_cap(df_trades: pd.DataFrame, cap: int) -> pd.DataFrame:
    """同時保有上限 cap で FIFO 採用。"""
    df = df_trades.sort_values("entry_ts").reset_index(drop=True)
    entry_ts = df["entry_ts"].values
    exit_ts = df["exit_ts"].values
    n = len(df)
    taken = np.zeros(n, dtype=bool)
    # active: ヒープ的な優先度キューでもいいが、シンプルに list で前から sweep
    active_exits: list[np.datetime64] = []
    for i in range(n):
        et = entry_ts[i]
        # 期限切れ除去
        active_exits = [e for e in active_exits if e > et]
        if len(active_exits) < cap:
            taken[i] = True
            active_exits.append(exit_ts[i])
    df["taken"] = taken
    return df


def monthly_pnl(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["month"] = pd.to_datetime(df["entry_ts"]).dt.to_period("M").astype(str)
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


def main() -> None:
    t0 = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log("=== Phase 5-b START ===")

    df_trades = pd.read_parquet(TRADES_PATH)
    df_trades["entry_ts"] = pd.to_datetime(df_trades["entry_ts"])
    df_trades["exit_ts"] = pd.to_datetime(df_trades["exit_ts"])
    log(f"  trades loaded: {len(df_trades):,}")

    results: dict[int, dict] = {}

    # Phase 5 (no cap) も比較対象に含める
    monthly_none = monthly_pnl(df_trades)
    monthly_none.to_csv(OUT_DIR / "monthly_pnl_cap_none.csv", index=False)
    results[0] = dict(
        cap="none",
        n_taken=len(df_trades),
        pnl_total=float(df_trades["pnl_usd"].sum()),
        pnl_monthly=monthly_none,
        pass_1900_count=int(monthly_none["pass_1900"].sum()),
    )

    for cap in POSITION_CAPS:
        log(f"--- cap = {cap} ---")
        t_c = time.time()
        df_capped = replay_with_cap(df_trades, cap)
        df_taken = df_capped[df_capped["taken"]].copy()
        n_taken = len(df_taken)
        n_rejected = (~df_capped["taken"]).sum()
        pnl_total = float(df_taken["pnl_usd"].sum())
        win = (df_taken["pnl_usd"] > 0).mean()
        log(f"  taken={n_taken:,} rejected={n_rejected:,} pnl_total=${pnl_total:,.0f} win={win*100:.1f}% elapsed={time.time()-t_c:.1f}s")

        df_taken.to_parquet(OUT_DIR / f"trades_cap{cap}.parquet")
        monthly = monthly_pnl(df_taken)
        monthly.to_csv(OUT_DIR / f"monthly_pnl_cap{cap}.csv", index=False)
        pass_1900 = int(monthly["pass_1900"].sum())
        log(f"  monthly pass $1,900: {pass_1900}/12")
        results[cap] = dict(
            cap=cap,
            n_taken=n_taken,
            n_rejected=int(n_rejected),
            pnl_total=pnl_total,
            pnl_monthly=monthly,
            pass_1900_count=pass_1900,
        )

    # 月次比較プロット
    fig, ax = plt.subplots(figsize=(14, 7))
    months = results[0]["pnl_monthly"]["month"].tolist()
    x = np.arange(len(months))
    width = 0.2
    labels = ["no cap", "cap 5", "cap 10", "cap 20"]
    for i, (key, label) in enumerate(zip([0, 5, 10, 20], labels)):
        m = results[key]["pnl_monthly"]
        ax.bar(x + (i - 1.5) * width, m["pnl_sum"], width, label=label)
    ax.axhline(THRESHOLD_PASS_MONTHLY, color="black", linestyle="--", linewidth=1, label="$1,900 pass")
    ax.axhline(WITHDRAW_LINE_MONTHLY, color="gray", linestyle=":", linewidth=1, label="$500 withdraw")
    ax.set_xticks(x)
    ax.set_xticklabels(months, rotation=45)
    ax.set_ylabel("USD")
    ax.set_title("Phase 5-b — Monthly PnL by Position Cap")
    ax.set_yscale("symlog")
    ax.legend()
    plt.tight_layout()
    plt.savefig(OUT_DIR / "monthly_pnl_comparison.png", dpi=110)
    plt.close(fig)

    elapsed = time.time() - t0
    log(f"=== Phase 5-b END (elapsed={elapsed/60:.2f} min) ===")
    write_summary(results, elapsed)


def write_summary(results: dict, elapsed: float) -> None:
    md = []
    md.append("# Phase 5-b — Position 同時保有上限導入 比較\n\n")
    md.append(f"- 実行 TS: {TS}\n")
    md.append(f"- 所要: {elapsed/60:.2f} 分\n\n")
    md.append("## サマリー\n\n")
    md.append("| cap | n_taken | n_rejected | pnl_total ($) | monthly_avg ($) | pass $1,900 | min month ($) |\n")
    md.append("|---|---|---|---|---|---|---|\n")
    for key in (0, 5, 10, 20):
        r = results[key]
        label = "no cap" if key == 0 else f"{key}"
        rejected = r.get("n_rejected", 0)
        monthly_avg = r["pnl_total"] / 12.0
        min_month_pnl = r["pnl_monthly"]["pnl_sum"].min()
        md.append(
            f"| {label} | {r['n_taken']:,} | {rejected:,} | "
            f"{r['pnl_total']:,.0f} | {monthly_avg:,.0f} | "
            f"{r['pass_1900_count']}/12 | {min_month_pnl:,.0f} |\n"
        )

    md.append("\n## 各 cap の月次内訳\n\n")
    for key in (0, 5, 10, 20):
        label = "no cap" if key == 0 else f"cap {key}"
        md.append(f"### {label}\n\n")
        m = results[key]["pnl_monthly"]
        md.append("| month | n | pnl_sum ($) | win | pass $1,900 |\n|---|---|---|---|---|\n")
        for _, r in m.iterrows():
            md.append(
                f"| {r['month']} | {int(r['n']):,} | {r['pnl_sum']:,.0f} | "
                f"{r['win_rate']*100:.1f}% | {'✅' if r['pass_1900'] else '❌'} |\n"
            )
        md.append("\n")

    md.append("## 採用ルール\n\n")
    md.append("- FIFO (early-arrival 採用)・LONG/SHORT 区別なし (total cap)\n")
    md.append("- Phase 5 の trades を Entry 時刻順に並べ、現在 active < cap なら採用\n")
    md.append("- 質的優先 (PnL 高い順 / Cluster 優先) は試していない (将来検討)\n")
    md.append("\n## 注記\n\n")
    md.append("- 約定モデル: 楽観 (Phase 5 と同じ)\n")
    md.append("- Position 制限ありの場合、現実証拠金: cap × 0.12 BTC × 価格\n")
    md.append("- 例: cap=10 / 100k USD/BTC → 同時保有最大 $120,000 ポジション\n")

    with open(OUT_DIR / "summary.md", "w") as f:
        f.write("".join(md))


if __name__ == "__main__":
    main()
