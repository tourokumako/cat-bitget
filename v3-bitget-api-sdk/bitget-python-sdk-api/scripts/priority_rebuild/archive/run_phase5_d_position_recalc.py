#!/usr/bin/env python3
"""
run_phase5_d_position_recalc.py — Phase 5-d: ポジションサイズ正解版で再計算

背景:
  Phase 4-b/5/6-b は POS_SIZE_BTC = 0.12 を「1 ポジションあたり」として計算。
  → 正解は「全ポジション合計上限 0.12 BTC」。cap=N なら 1 ポジション = 0.12/N。
  → 採用 trade の pnl_usd を 1/cap 倍にスケールするだけで PnL は線形に再現
     (手数料も同率縮小なので NET の線形性は完全)

スコープ:
  cap=1/2/3/5 (cap=10/20 は同時保有 0.012/0.006 BTC で現実非対応 → 今回不要)

ロジック:
  1. Phase 5-c と同じ質駆動採用 (predicted MFE/MAE 比 降順 + active < cap)
  2. 採用 trade の pnl_usd を 1/cap 倍にスケール
  3. 月次集計 → $1,900 判定

入力:
  results/priority_rebuild/ml_phase5/trades_phase5.parquet
  results/priority_rebuild/ml_phase4_b/entry_candidates.parquet
  results/priority_rebuild/ml_phase6_b/trades_2026q1.parquet
  results/priority_rebuild/ml_phase6_b/entry_candidates_2026q1.parquet

出力 (results/priority_rebuild/ml_phase5_d/):
  trades_2025_cap{1,2,3,5}_recalc.parquet
  trades_2026q1_cap{1,2,3,5}_recalc.parquet
  monthly_2025_recalc.csv
  monthly_2026q1_recalc.csv
  summary.md
  phase5d_log_<TS>.txt

再現コマンド:
  python3 scripts/priority_rebuild/run_phase5_d_position_recalc.py
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
P4B_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase4_b"
P5_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase5"
P6B_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase6_b"
P5C_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase5_c"
OUT_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase5_d"

POSITION_CAPS = (1, 2, 3, 5)
POS_TOTAL_BTC = 0.12  # 全ポジション合計上限
THRESHOLD_PASS_MONTHLY = 1900.0

TS = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
LOG_PATH = OUT_DIR / f"phase5d_log_{TS}.txt"


def log(msg: str) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{now}] {msg}"
    print(line, flush=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")


def join_trades_with_predictions(trades_path: Path, candidates_path: Path) -> pd.DataFrame:
    """trades に entry_candidates の predicted_MFE/MAE を結合 (Phase 5-c と同一)"""
    trades = pd.read_parquet(trades_path)
    candidates = pd.read_parquet(candidates_path)
    if "timestamp" in candidates.columns:
        candidates = candidates.rename(columns={"timestamp": "entry_ts"})
    trades["entry_ts"] = pd.to_datetime(trades["entry_ts"])
    candidates["entry_ts"] = pd.to_datetime(candidates["entry_ts"])
    if "exit_ts" in trades.columns:
        trades["exit_ts"] = pd.to_datetime(trades["exit_ts"])
    joined = trades.merge(
        candidates[["entry_ts", "K", "side", "predicted_MFE", "predicted_MAE"]],
        on=["entry_ts", "K", "side"],
        how="left",
    )
    joined["pred_ratio"] = joined["predicted_MFE"] / joined["predicted_MAE"].replace(0, np.nan)
    return joined


def replay_quality_priority(df: pd.DataFrame, cap: int) -> pd.DataFrame:
    """質駆動採用: predicted ratio 降順 + active < cap (Phase 5-c と同一)"""
    df = df.copy()
    df = df.dropna(subset=["pred_ratio"]).reset_index(drop=True)
    df = df.sort_values("pred_ratio", ascending=False).reset_index(drop=True)

    base_ts = pd.Timestamp(df["entry_ts"].min())
    df["entry_bar"] = ((df["entry_ts"] - base_ts).dt.total_seconds() / 300).astype(int)
    df["exit_bar"] = ((df["exit_ts"] - base_ts).dt.total_seconds() / 300).astype(int)
    n_bars = int(df["exit_bar"].max()) + 2

    active = np.zeros(n_bars, dtype=np.int32)
    entry_bar = df["entry_bar"].values
    exit_bar = df["exit_bar"].values
    n = len(df)
    taken = np.zeros(n, dtype=bool)

    for i in range(n):
        eb = int(entry_bar[i])
        xb = int(exit_bar[i])
        if eb < 0 or eb >= n_bars:
            continue
        if active[eb] < cap:
            taken[i] = True
            end = min(xb + 1, n_bars)
            if end > eb:
                active[eb:end] += 1

    df_taken = df[taken].copy()
    return df_taken.sort_values("entry_ts").reset_index(drop=True)


def recompute_with_new_size(df_taken: pd.DataFrame, cap: int) -> pd.DataFrame:
    """既存 pnl_usd は POS=0.12 想定 → 新 POS=0.12/cap なので 1/cap 倍に線形スケール"""
    df = df_taken.copy()
    df["pnl_usd_orig"] = df["pnl_usd"]
    df["pnl_usd"] = df["pnl_usd"] / cap
    df["pos_size_btc"] = POS_TOTAL_BTC / cap
    return df


def monthly_pnl(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["month"] = pd.to_datetime(df["entry_ts"]).dt.to_period("M").astype(str)
    agg = (
        df.groupby("month", sort=True)
        .agg(
            n=("pnl_usd", "size"),
            pnl_sum=("pnl_usd", "sum"),
            win_rate=("pnl_usd", lambda x: (x > 0).mean()),
        )
        .reset_index()
    )
    agg["pass_1900"] = agg["pnl_sum"] >= THRESHOLD_PASS_MONTHLY
    return agg


def sanity_check_vs_phase5c(df_recalc_cap5: pd.DataFrame, period_label: str) -> None:
    """Phase 5-d cap=5 月次 × 5 = Phase 5-c cap=5 月次 と一致するか確認"""
    p5c_path = P5C_DIR / f"monthly_{period_label}_quality.csv"
    if not p5c_path.exists():
        log(f"  [sanity] {p5c_path.name} not found, skip")
        return
    p5c = pd.read_csv(p5c_path)
    p5c_cap5 = p5c[p5c["cap"] == 5].set_index("month")["pnl_sum"]

    m_new = monthly_pnl(df_recalc_cap5).set_index("month")["pnl_sum"]
    m_new_scaled_back = m_new * 5  # Phase 5-d cap=5 PnL × 5 = Phase 5-c cap=5 PnL
    common = m_new_scaled_back.index.intersection(p5c_cap5.index)
    diffs = (m_new_scaled_back.loc[common] - p5c_cap5.loc[common]).abs()
    max_diff = diffs.max()
    log(f"  [sanity {period_label}] Phase 5-c cap=5 月次 vs Phase 5-d cap=5 × 5: max diff = ${max_diff:.2f}")
    if max_diff > 1.0:
        log(f"  [sanity {period_label}] ⚠️  MISMATCH (>$1)")
    else:
        log(f"  [sanity {period_label}] ✅ MATCH (within $1)")


def main() -> None:
    t0 = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log("=== Phase 5-d START ===")
    log(f"POSITION_CAPS={POSITION_CAPS} / POS_TOTAL_BTC={POS_TOTAL_BTC} (合計上限)")

    # ===== test 2025 (仮テスト) =====
    log("--- test 2025 ---")
    trades_25 = join_trades_with_predictions(
        P5_DIR / "trades_phase5.parquet",
        P4B_DIR / "entry_candidates.parquet",
    )
    log(f"  trades 25 joined: {len(trades_25):,}")
    log(f"  NaN ratio: {trades_25['pred_ratio'].isna().sum()}")

    monthly_25_all = []
    df_25_cap5 = None
    for cap in POSITION_CAPS:
        t_c = time.time()
        df_taken = replay_quality_priority(trades_25, cap)
        df_recalc = recompute_with_new_size(df_taken, cap)
        m = monthly_pnl(df_recalc)
        m["cap"] = cap
        monthly_25_all.append(m)
        total = df_recalc["pnl_usd"].sum()
        passn = int(m["pass_1900"].sum())
        n_months = len(m)
        log(
            f"  cap={cap}: n={len(df_recalc):,} total=${total:,.0f} "
            f"monthly_avg=${total/n_months:,.0f} pass={passn}/{n_months} "
            f"size={POS_TOTAL_BTC/cap:.4f}BTC elapsed={time.time()-t_c:.1f}s"
        )
        df_recalc.to_parquet(OUT_DIR / f"trades_2025_cap{cap}_recalc.parquet")
        if cap == 5:
            df_25_cap5 = df_recalc

    df_m25 = pd.concat(monthly_25_all, ignore_index=True)
    df_m25.to_csv(OUT_DIR / "monthly_2025_recalc.csv", index=False)
    log("saved monthly_2025_recalc.csv")
    if df_25_cap5 is not None:
        sanity_check_vs_phase5c(df_25_cap5, "2025")

    # ===== test 2026 Q1 (本テスト) =====
    log("--- test 2026 Q1 ---")
    trades_26 = join_trades_with_predictions(
        P6B_DIR / "trades_2026q1.parquet",
        P6B_DIR / "entry_candidates_2026q1.parquet",
    )
    log(f"  trades 26 joined: {len(trades_26):,}")

    monthly_26_all = []
    df_26_cap5 = None
    for cap in POSITION_CAPS:
        t_c = time.time()
        df_taken = replay_quality_priority(trades_26, cap)
        df_recalc = recompute_with_new_size(df_taken, cap)
        m = monthly_pnl(df_recalc)
        m["cap"] = cap
        monthly_26_all.append(m)
        total = df_recalc["pnl_usd"].sum()
        passn = int(m["pass_1900"].sum())
        n_months = len(m)
        log(
            f"  cap={cap}: n={len(df_recalc):,} total=${total:,.0f} "
            f"monthly_avg=${total/n_months:,.0f} pass={passn}/{n_months} "
            f"size={POS_TOTAL_BTC/cap:.4f}BTC elapsed={time.time()-t_c:.1f}s"
        )
        df_recalc.to_parquet(OUT_DIR / f"trades_2026q1_cap{cap}_recalc.parquet")
        if cap == 5:
            df_26_cap5 = df_recalc

    df_m26 = pd.concat(monthly_26_all, ignore_index=True)
    df_m26.to_csv(OUT_DIR / "monthly_2026q1_recalc.csv", index=False)
    log("saved monthly_2026q1_recalc.csv")
    if df_26_cap5 is not None:
        sanity_check_vs_phase5c(df_26_cap5, "2026q1")

    elapsed = time.time() - t0
    log(f"=== Phase 5-d END (elapsed={elapsed/60:.2f} min) ===")
    write_summary(elapsed, df_m25, df_m26)


def write_summary(elapsed: float, df_m25: pd.DataFrame, df_m26: pd.DataFrame) -> None:
    md = []
    md.append("# Phase 5-d — ポジションサイズ正解版 再計算\n\n")
    md.append(f"- 実行 TS: {TS}\n")
    md.append(f"- 所要: {elapsed/60:.2f} 分\n")
    md.append(f"- 設定: POS_TOTAL_BTC = {POS_TOTAL_BTC} (全ポジション合計上限)\n")
    md.append(f"- 1 ポジションあたり: 0.12 / cap BTC\n")
    md.append("- 採用ルール: Phase 5-c と同一 (predicted MFE/MAE 比 降順 + active < cap)\n")
    md.append("- PnL: Phase 5-c の trades.pnl_usd を 1/cap 倍 (線形スケーリング)\n\n")

    md.append("## 再現コマンド\n\n")
    md.append("```\npython3 scripts/priority_rebuild/run_phase5_d_position_recalc.py\n```\n\n")

    md.append("## test 2025 (仮テスト) cap 別\n\n")
    md.append("| cap | 1pos (BTC) | n | total ($) | monthly avg ($) | pass $1,900 |\n")
    md.append("|---|---|---|---|---|---|\n")
    for cap in POSITION_CAPS:
        sub = df_m25[df_m25["cap"] == cap]
        n_trades = sub["n"].sum()
        total = sub["pnl_sum"].sum()
        n_m = len(sub)
        avg = total / n_m if n_m else 0
        passn = int(sub["pass_1900"].sum())
        md.append(
            f"| {cap} | {POS_TOTAL_BTC/cap:.4f} | {int(n_trades):,} | "
            f"{total:,.0f} | {avg:,.0f} | {passn}/{n_m} |\n"
        )

    md.append("\n## test 2026 Q1 (本テスト) cap 別\n\n")
    md.append("| cap | 1pos (BTC) | n | total ($) | monthly avg ($) | pass $1,900 |\n")
    md.append("|---|---|---|---|---|---|\n")
    for cap in POSITION_CAPS:
        sub = df_m26[df_m26["cap"] == cap]
        n_trades = sub["n"].sum()
        total = sub["pnl_sum"].sum()
        n_m = len(sub)
        avg = total / n_m if n_m else 0
        passn = int(sub["pass_1900"].sum())
        md.append(
            f"| {cap} | {POS_TOTAL_BTC/cap:.4f} | {int(n_trades):,} | "
            f"{total:,.0f} | {avg:,.0f} | {passn}/{n_m} |\n"
        )

    md.append("\n## test 2025 月次内訳\n\n")
    md.append("| month | cap | n | pnl_sum ($) | win | pass $1,900 |\n|---|---|---|---|---|---|\n")
    for _, r in df_m25.iterrows():
        md.append(
            f"| {r['month']} | {int(r['cap'])} | {int(r['n']):,} | {r['pnl_sum']:,.0f} | "
            f"{r['win_rate']*100:.1f}% | {'✅' if r['pass_1900'] else '❌'} |\n"
        )

    md.append("\n## test 2026 Q1 月次内訳\n\n")
    md.append("| month | cap | n | pnl_sum ($) | win | pass $1,900 |\n|---|---|---|---|---|---|\n")
    for _, r in df_m26.iterrows():
        md.append(
            f"| {r['month']} | {int(r['cap'])} | {int(r['n']):,} | {r['pnl_sum']:,.0f} | "
            f"{r['win_rate']*100:.1f}% | {'✅' if r['pass_1900'] else '❌'} |\n"
        )

    md.append("\n## 注記\n\n")
    md.append("- Phase 5-c cap=5 月次 × 5 = Phase 5-d cap=5 月次 (sanity check 通過確認はログ参照)\n")
    md.append("- 採用 trade 数は cap ごとに変わる (cap=1 は先頭ポジ exit まで次採用なし)\n")
    md.append("- Funding Rate は未控除 (Phase 5-d-2 で別途試算)\n")

    with open(OUT_DIR / "summary.md", "w") as f:
        f.write("".join(md))


if __name__ == "__main__":
    main()
