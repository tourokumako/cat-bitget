#!/usr/bin/env python3
"""
run_phase5_c.py — ML Phase 5-c: 質駆動 Position 採用ルール

指示書: bitget-python-sdk-api/cc_ml_design_spec.md §4 / §5 Phase 5

背景:
  Phase 5-b (FIFO) は仮テスト 2025 で 12/12 合格。
  Phase 6-b 本テスト 2026 Q1 で 2026-02 が cap=5/10/20 全部マイナス → FIFO 破綻。
  → 質駆動採用ルール (予測 MFE/MAE 比 降順) で再 Replay。

質駆動ルール:
  - 全 Entry を予測 MFE/MAE 比で降順ソート
  - 各 Entry について、Entry 時刻時点で active な持ち高 < cap なら採用
  - 「高品質 Entry を優先採用 → cap 空きがあれば」

実行範囲:
  - test 2025 (仮テスト)・cap=5/10/20
  - test 2026 Q1 (本テスト)・cap=5/10/20

入力:
  results/priority_rebuild/ml_phase4_b/entry_candidates.parquet     (test 2025 Entry + 予測)
  results/priority_rebuild/ml_phase5/trades_phase5.parquet           (test 2025 trades)
  results/priority_rebuild/ml_phase6_b/entry_candidates_2026q1.parquet
  results/priority_rebuild/ml_phase6_b/trades_2026q1.parquet

出力 (results/priority_rebuild/ml_phase5_c/):
  phase5c_log_<TS>.txt
  trades_2025_cap{N}_quality.parquet × 3
  trades_2026q1_cap{N}_quality.parquet × 3
  monthly_2025_quality.csv
  monthly_2026q1_quality.csv
  summary.md
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
OUT_DIR = REPO_ROOT / "results" / "priority_rebuild" / "ml_phase5_c"

POSITION_CAPS = (5, 10, 20)
THRESHOLD_PASS_MONTHLY = 1900.0

TS = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
LOG_PATH = OUT_DIR / f"phase5c_log_{TS}.txt"


def log(msg: str) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{now}] {msg}"
    print(line, flush=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")


def join_trades_with_predictions(
    trades_path: Path, candidates_path: Path
) -> pd.DataFrame:
    """trades に entry_candidates の predicted_MFE/MAE を結合。"""
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
    """時系列順採用 + 同 timestamp 内 pred_ratio 優先 (L-182 fix)

    旧実装: 期間全体 pred_ratio 降順ソート → ループが時系列順でなく、未来 entry が
            active に紛れて過去の判断を覆す = 未来情報 leak 同等のバグ。
    新実装: entry_ts 昇順 (= 時系列順) + 同 timestamp 内のみ pred_ratio 降順 (優先度)。
            active カウントは過去採用 entry のみで構成され、未来情報を参照しない。

    高速化: 5m bar timeline 上に active カウント numpy 配列を持ち、O(N × K_avg)。
    """
    df = df.copy()
    df = df.dropna(subset=["pred_ratio"]).reset_index(drop=True)
    # entry_ts 昇順 (時系列) + 同 timestamp 内 pred_ratio 降順 (同時刻複数候補時の優先度)
    df = df.sort_values(["entry_ts", "pred_ratio"], ascending=[True, False]).reset_index(drop=True)

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


def main() -> None:
    t0 = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log("=== Phase 5-c START ===")

    # ===== test 2025 (仮テスト) =====
    log("--- test 2025 ---")
    trades_25 = join_trades_with_predictions(
        P5_DIR / "trades_phase5.parquet",
        P4B_DIR / "entry_candidates.parquet",
    )
    log(f"  trades 25 joined: {len(trades_25):,}")
    nan_ratio = trades_25["pred_ratio"].isna().sum()
    log(f"  NaN ratio: {nan_ratio}")

    monthly_25_all = []
    for cap in POSITION_CAPS:
        t_c = time.time()
        df_taken = replay_quality_priority(trades_25, cap)
        m = monthly_pnl(df_taken)
        m["cap"] = cap
        monthly_25_all.append(m)
        total = df_taken["pnl_usd"].sum()
        passn = int(m["pass_1900"].sum())
        log(f"  cap={cap}: n={len(df_taken):,} total=${total:,.0f} pass={passn}/12 elapsed={time.time()-t_c:.1f}s")
        df_taken.to_parquet(OUT_DIR / f"trades_2025_cap{cap}_quality.parquet")
    df_m25 = pd.concat(monthly_25_all, ignore_index=True)
    df_m25.to_csv(OUT_DIR / "monthly_2025_quality.csv", index=False)
    log("saved monthly_2025_quality.csv")

    # ===== test 2026 Q1 (本テスト) =====
    log("--- test 2026 Q1 ---")
    trades_26 = join_trades_with_predictions(
        P6B_DIR / "trades_2026q1.parquet",
        P6B_DIR / "entry_candidates_2026q1.parquet",
    )
    log(f"  trades 26 joined: {len(trades_26):,}")

    monthly_26_all = []
    for cap in POSITION_CAPS:
        t_c = time.time()
        df_taken = replay_quality_priority(trades_26, cap)
        m = monthly_pnl(df_taken)
        m["cap"] = cap
        monthly_26_all.append(m)
        total = df_taken["pnl_usd"].sum()
        passn = int(m["pass_1900"].sum())
        log(f"  cap={cap}: n={len(df_taken):,} total=${total:,.0f} pass={passn}/3 elapsed={time.time()-t_c:.1f}s")
        df_taken.to_parquet(OUT_DIR / f"trades_2026q1_cap{cap}_quality.parquet")
    df_m26 = pd.concat(monthly_26_all, ignore_index=True)
    df_m26.to_csv(OUT_DIR / "monthly_2026q1_quality.csv", index=False)
    log("saved monthly_2026q1_quality.csv")

    elapsed = time.time() - t0
    log(f"=== Phase 5-c END (elapsed={elapsed/60:.2f} min) ===")
    write_summary(elapsed, df_m25, df_m26)


def write_summary(elapsed: float, df_m25: pd.DataFrame, df_m26: pd.DataFrame) -> None:
    md = []
    md.append("# Phase 5-c — 質駆動 Position 採用ルール\n\n")
    md.append(f"- 実行 TS: {TS}\n")
    md.append(f"- 所要: {elapsed/60:.2f} 分\n")
    md.append("- 採用ルール: 全 Entry を `predicted_MFE / predicted_MAE` 降順ソート\n")
    md.append("              → 各 Entry の entry_ts 時点で active < cap なら採用\n\n")

    md.append("## 再現コマンド\n\n")
    md.append("```\npython3 scripts/priority_rebuild/run_phase5_c.py\n```\n\n")

    md.append("## test 2025 (仮テスト) cap 別\n\n")
    md.append("| cap | total ($) | monthly avg ($) | pass $1,900 |\n|---|---|---|---|\n")
    for cap in POSITION_CAPS:
        sub = df_m25[df_m25.cap == cap]
        total = sub["pnl_sum"].sum()
        avg = total / 12
        passn = int(sub["pass_1900"].sum())
        md.append(f"| {cap} | {total:,.0f} | {avg:,.0f} | {passn}/12 |\n")

    md.append("\n## test 2026 Q1 (本テスト) cap 別\n\n")
    md.append("| cap | total ($) | monthly avg ($) | pass $1,900 |\n|---|---|---|---|\n")
    for cap in POSITION_CAPS:
        sub = df_m26[df_m26.cap == cap]
        total = sub["pnl_sum"].sum()
        avg = total / 3
        passn = int(sub["pass_1900"].sum())
        md.append(f"| {cap} | {total:,.0f} | {avg:,.0f} | {passn}/3 |\n")

    md.append("\n## test 2026 Q1 月次内訳\n\n")
    md.append("| month | cap | n | pnl_sum ($) | win | pass $1,900 |\n|---|---|---|---|---|---|\n")
    for _, r in df_m26.iterrows():
        md.append(
            f"| {r['month']} | {int(r['cap'])} | {int(r['n']):,} | {r['pnl_sum']:,.0f} | "
            f"{r['win_rate']*100:.1f}% | {'✅' if r['pass_1900'] else '❌'} |\n"
        )

    md.append("\n## 注記\n\n")
    md.append("- FIFO 採用との比較は monthly_pnl.csv (Phase 5-b/6-b) と並べて確認\n")
    md.append("- 採用順序: entry_ts 昇順 (時系列) + 同 timestamp 内のみ pred_ratio 降順 (L-182 fix)\n")
    md.append("- 過去の判断を未来情報で覆さない実装 (旧版の期間全体ソートは leak バグだった)\n")

    with open(OUT_DIR / "summary.md", "w") as f:
        f.write("".join(md))


if __name__ == "__main__":
    main()
