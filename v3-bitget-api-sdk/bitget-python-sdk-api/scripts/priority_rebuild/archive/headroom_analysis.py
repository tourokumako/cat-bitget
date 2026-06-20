#!/usr/bin/env python3
"""headroom_analysis.py — 旧 P1-P24 月次 $370 頭打ち原因分析

仕様: .claude/memory/headroom_analysis_spec.md (§1-§8)
入力:
  results/replay/replay_BTCUSDT-5m-2025-04-01_03-31_365d.csv  (1,157 trade)
  results/priority_rebuild/labels_mfe_mae_test_2025.parquet   (2025 / 105,120 bar)
  config/cat_params_v9.json
出力:
  results/priority_rebuild/headroom_step1_trade_decomp.csv
  results/priority_rebuild/headroom_step2_entry_quality.csv
  results/priority_rebuild/headroom_step3_position.csv
  results/priority_rebuild/headroom_step4_virtual_exit.csv
  results/priority_rebuild/headroom_analysis_summary.md
"""
import json
import math
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

REPO = Path(__file__).resolve().parents[2]
REPLAY_CSV = REPO / "results/replay/replay_BTCUSDT-5m-2025-04-01_03-31_365d.csv"
PARQUET_TEST = REPO / "results/priority_rebuild/labels_mfe_mae_test_2025.parquet"
CFG_PATH = REPO / "config/cat_params_v9.json"
OUT_DIR = REPO / "results/priority_rebuild"
DASH_DATA_DIR = REPO / "dashboard/data"
PASS_LINE_MONTH = 1900.0

# Will be populated during step4 to feed dashboard JSON
MONTHLY_SERIES = {}

K_LIST = [12, 24, 48, 96]
SIDE_LIST = ["LONG", "SHORT"]
LABEL_COLS = [f"{s}_{m}_K{k}" for s in SIDE_LIST for m in ["MFE", "MAE"] for k in K_LIST]


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


# ─────────────────────────────────────────────────────────────────────
# Load
# ─────────────────────────────────────────────────────────────────────
def load_inputs():
    log("Loading replay CSV")
    trades = pd.read_csv(REPLAY_CSV, parse_dates=["entry_time", "exit_time"])
    log(f"  trades: {len(trades)} rows | NET sum: ${trades['net_usd'].sum():.2f}")

    log("Loading parquet test (close + 16 labels only)")
    par = pd.read_parquet(PARQUET_TEST, columns=["close"] + LABEL_COLS)
    log(f"  parquet: {len(par)} bars | range {par.index.min()} → {par.index.max()}")

    cfg = json.loads(CFG_PATH.read_text())
    fee = cfg.get("FEE_RATE_MAKER", 0.00014)
    log(f"  FEE_RATE_MAKER: {fee}")

    return trades, par, fee


# ─────────────────────────────────────────────────────────────────────
# Step 1: trade-level decomposition
# ─────────────────────────────────────────────────────────────────────
def step1_decompose(trades: pd.DataFrame) -> pd.DataFrame:
    log("Step 1: trade-level decomposition")
    rows = []

    def agg(df, axis_name, bucket_series):
        df2 = df.assign(_bk=bucket_series)
        for bucket, g in df2.groupby("_bk", dropna=False, observed=True):
            rows.append({
                "axis_name": axis_name,
                "bucket": str(bucket),
                "n_trades": len(g),
                "net_usd_sum": round(g["net_usd"].sum(), 2),
                "net_usd_median": round(g["net_usd"].median(), 4),
                "mfe_usd_median": round(g["mfe_usd"].median(), 4),
                "mae_usd_median": round(g["mae_usd"].median(), 4),
                "hold_min_median": round(g["hold_min"].median(), 1),
                "mfe_minus_net_median": round((g["mfe_usd"] - g["net_usd"]).median(), 4),
            })

    agg(trades, "exit_reason", trades["exit_reason"])
    agg(trades, "side", trades["side"])
    agg(trades, "regime", trades["regime"])
    agg(trades, "priority", trades["priority"])
    agg(trades, "priority_x_side", trades["priority"].astype(str) + "-" + trades["side"])
    agg(trades, "priority_x_side_x_regime",
        trades["priority"].astype(str) + "-" + trades["side"] + "-" + trades["regime"].astype(str))
    agg(trades, "entry_hour", trades["entry_hour"])
    agg(trades, "entry_weekday", trades["entry_weekday"])

    adx_buck = pd.cut(trades["adx_at_entry"], bins=[0, 15, 20, 25, 30, 40, 200],
                      labels=["<15", "15-20", "20-25", "25-30", "30-40", "≥40"])
    agg(trades, "adx_bucket", adx_buck)

    bbw_buck = pd.cut(trades["bb_width_at_entry"], bins=[0, 0.005, 0.01, 0.015, 0.02, 1],
                      labels=["<0.5%", "0.5-1%", "1-1.5%", "1.5-2%", "≥2%"])
    agg(trades, "bb_width_bucket", bbw_buck)

    atr_buck = pd.cut(trades["atr_14"], bins=[0, 100, 150, 200, 300, 5000],
                      labels=["<100", "100-150", "150-200", "200-300", "≥300"])
    agg(trades, "atr14_bucket", atr_buck)

    hold_buck = pd.cut(trades["hold_min"], bins=[-1, 0, 30, 60, 120, 240, 480, 100000],
                       labels=["instant", "0-30", "30-60", "60-120", "120-240", "240-480", "≥480"])
    agg(trades, "hold_min_bucket", hold_buck)

    df = pd.DataFrame(rows)
    out = OUT_DIR / "headroom_step1_trade_decomp.csv"
    df.to_csv(out, index=False)
    log(f"  wrote {out} ({len(df)} rows)")
    return df


# ─────────────────────────────────────────────────────────────────────
# Join: replay entries with parquet labels (matched subset only)
# ─────────────────────────────────────────────────────────────────────
def join_with_labels(trades: pd.DataFrame, par: pd.DataFrame):
    par_reset = par.reset_index().rename(columns={"timestamp": "_pq_ts", "close": "_pq_close"})
    joined = trades.merge(par_reset, left_on="entry_time", right_on="_pq_ts", how="left")
    matched = joined["_pq_close"].notna()
    log(f"  matched with parquet: {matched.sum()} / {len(trades)} ({100*matched.mean():.1f}%)")
    return joined, matched


# ─────────────────────────────────────────────────────────────────────
# Step 2: Entry quality vs random / all-bar / top-N%
# ─────────────────────────────────────────────────────────────────────
def step2_entry_quality(joined: pd.DataFrame, matched_mask: pd.Series,
                        par: pd.DataFrame, rng_seed: int = 42) -> pd.DataFrame:
    log("Step 2: entry quality benchmark")
    rng = np.random.default_rng(rng_seed)
    matched = joined[matched_mask].copy()

    rows = []
    for K in K_LIST:
        for side in SIDE_LIST:
            mfe_col = f"{side}_MFE_K{K}"
            mae_col = f"{side}_MAE_K{K}"

            old_grp = matched[matched["side"] == side]
            n_old = len(old_grp)
            if n_old == 0:
                continue

            old_mfe_pct = (old_grp[mfe_col] / old_grp["_pq_close"]).dropna()
            old_mae_pct = (old_grp[mae_col] / old_grp["_pq_close"]).dropna()

            all_mfe_pct = (par[mfe_col] / par["close"]).dropna()
            all_mae_pct = (par[mae_col] / par["close"]).dropna()

            idx = rng.choice(len(par), size=n_old, replace=False)
            rnd_mfe_pct = (par[mfe_col].iloc[idx] / par["close"].iloc[idx]).dropna()
            rnd_mae_pct = (par[mae_col].iloc[idx] / par["close"].iloc[idx]).dropna()

            def make_row(group_label, mfe_s, mae_s, n_val, extra=None):
                mfe_med = mfe_s.median()
                mae_med = mae_s.median()
                row = {
                    "K": K,
                    "side": side,
                    "group": group_label,
                    "mfe_pct_median": round(float(mfe_med), 6),
                    "mae_pct_median": round(float(mae_med), 6),
                    "ratio_mfe_over_mae": round(float(mfe_med / mae_med), 4) if mae_med > 0 else None,
                    "n": int(n_val),
                }
                if extra:
                    row.update(extra)
                return row

            _, p_mfe = mannwhitneyu(old_mfe_pct, rnd_mfe_pct, alternative="greater")
            _, p_mae = mannwhitneyu(old_mae_pct, rnd_mae_pct, alternative="less")
            rows.append(make_row("old_p1_p24", old_mfe_pct, old_mae_pct, n_old, {
                "mw_u_pvalue_mfe_vs_random": round(float(p_mfe), 6),
                "mw_u_pvalue_mae_vs_random": round(float(p_mae), 6),
            }))
            rows.append(make_row("random_baseline", rnd_mfe_pct, rnd_mae_pct, n_old))
            rows.append(make_row("all_bar", all_mfe_pct, all_mae_pct, len(par)))

            for pct in [5, 10, 20]:
                thresh = all_mfe_pct.quantile(1 - pct / 100)
                m = all_mfe_pct >= thresh
                rows.append(make_row(f"top{pct}pct_mfe",
                                     all_mfe_pct[m], all_mae_pct[m], int(m.sum())))

    df = pd.DataFrame(rows)
    out = OUT_DIR / "headroom_step2_entry_quality.csv"
    df.to_csv(out, index=False)
    log(f"  wrote {out} ({len(df)} rows)")
    return df


# ─────────────────────────────────────────────────────────────────────
# Step 3: Position-level
# ─────────────────────────────────────────────────────────────────────
def step3_position(trades: pd.DataFrame) -> pd.DataFrame:
    log("Step 3: position-level")
    rows = []

    # Daily trade count
    daily = trades.groupby(trades["entry_time"].dt.date).size()
    rows.append({
        "axis": "trades_per_day", "bucket": "global", "n_obs": len(daily),
        "max": int(daily.max()), "median": float(daily.median()),
        "min": int(daily.min()),
        "p25": float(daily.quantile(0.25)), "p75": float(daily.quantile(0.75)),
    })

    # Concurrent positions via event sweep
    events = []
    for _, r in trades[["entry_time", "exit_time"]].iterrows():
        events.append((r["entry_time"], +1))
        events.append((r["exit_time"], -1))
    events.sort(key=lambda x: (x[0], -x[1]))
    open_n = 0
    open_snap = []
    for _, delta in events:
        open_n += delta
        open_snap.append(open_n)
    snaps = pd.Series(open_snap)
    rows.append({
        "axis": "concurrent_positions", "bucket": "global", "n_obs": len(snaps),
        "max": int(snaps.max()), "median": float(snaps.median()),
        "min": int(snaps.min()),
        "p25": float(snaps.quantile(0.25)), "p75": float(snaps.quantile(0.75)),
    })

    # Concurrent by side
    for sd in SIDE_LIST:
        sub = trades[trades["side"] == sd]
        ev = []
        for _, r in sub[["entry_time", "exit_time"]].iterrows():
            ev.append((r["entry_time"], +1))
            ev.append((r["exit_time"], -1))
        ev.sort(key=lambda x: (x[0], -x[1]))
        n = 0
        sn = []
        for _, d in ev:
            n += d
            sn.append(n)
        s = pd.Series(sn) if sn else pd.Series([0])
        rows.append({
            "axis": "concurrent_positions_by_side", "bucket": sd, "n_obs": len(s),
            "max": int(s.max()), "median": float(s.median()),
            "min": int(s.min()),
            "p25": float(s.quantile(0.25)), "p75": float(s.quantile(0.75)),
        })

    # Priority×side allocation
    for (p, sd), g in trades.groupby(["priority", "side"]):
        rows.append({
            "axis": "priority_x_side_alloc",
            "bucket": f"P{p}-{sd}",
            "n_trades": len(g),
            "size_btc_mean": round(float(g["size_btc"].mean()), 4),
            "net_usd_sum": round(float(g["net_usd"].sum()), 2),
            "net_usd_mean": round(float(g["net_usd"].mean()), 4),
            "net_usd_median": round(float(g["net_usd"].median()), 4),
        })

    # Missed-fire: not derivable from current artifacts
    rows.append({
        "axis": "missed_fire", "bucket": "N/A",
        "note": "Replay log not retained; counts of skipped entries (due to existing position) not derivable from CSV alone. Would require re-run of replay_csv.py with logging.",
    })

    df = pd.DataFrame(rows)
    out = OUT_DIR / "headroom_step3_position.csv"
    df.to_csv(out, index=False)
    log(f"  wrote {out} ({len(df)} rows)")
    return df


# ─────────────────────────────────────────────────────────────────────
# Step 4: Virtual Exit
# ─────────────────────────────────────────────────────────────────────
def step4_virtual_exit(trades: pd.DataFrame, joined: pd.DataFrame,
                       matched_mask: pd.Series, par: pd.DataFrame, fee_rate: float) -> pd.DataFrame:
    log("Step 4: virtual exit")
    rows = []

    # Baseline (actual replay)
    trades_m = trades.assign(ym=trades["entry_time"].dt.to_period("M"))
    base_monthly = trades_m.groupby("ym")["net_usd"].sum()
    MONTHLY_SERIES["baseline_actual"] = {str(k): round(float(v), 2) for k, v in base_monthly.items()}
    rows.append({
        "pattern_id": "baseline_actual",
        "pattern_label": "Actual replay (P1-P24 current params)",
        "net_sum_total": round(float(trades["net_usd"].sum()), 2),
        "n_trades_used": len(trades),
        "n_months": len(base_monthly),
        "monthly_avg": round(float(base_monthly.mean()), 2),
        "worst_month_net": round(float(base_monthly.min()), 2),
        "best_month_net": round(float(base_monthly.max()), 2),
        "n_months_above_1900": int((base_monthly >= PASS_LINE_MONTH).sum()),
        "all_12mo_pass_1900": bool((base_monthly >= PASS_LINE_MONTH).all()),
        "approx_note": "actual replay output (no approximation)",
    })

    # Matched subset (for K-window patterns)
    j = joined[matched_mask].copy()
    j["ym"] = j["entry_time"].dt.to_period("M")
    n_matched = len(j)

    # Compute close at t+K via parquet shift, then merge back
    close_K = pd.DataFrame(index=par.index)
    for K in K_LIST:
        close_K[f"close_K{K}"] = par["close"].shift(-K)
    j = j.merge(close_K.reset_index().rename(columns={"timestamp": "_pq_ts"}),
                on="_pq_ts", how="left", suffixes=("", "_y"))

    # For each row, get this side's MFE/MAE col values
    def side_label(row, m, K):
        return row[f"{row['side']}_{m}_K{K}"]

    # Pattern: Perfect Exit at K (theoretical max within K window)
    for K in K_LIST:
        gross = j.apply(lambda r: r[f"{r['side']}_MFE_K{K}"] * r["size_btc"]
                        if pd.notna(r[f"{r['side']}_MFE_K{K}"]) else np.nan, axis=1)
        gross = gross.clip(lower=0)  # negative MFE → no profit (held to close)
        net = gross - j["fee_usd"]
        m = j.assign(net=net).groupby("ym")["net"].sum()
        MONTHLY_SERIES[f"perfect_exit_K{K}"] = {str(k): round(float(v), 2) for k, v in m.items()}
        rows.append({
            "pattern_id": f"perfect_exit_K{K}",
            "pattern_label": f"Take K={K}-window MFE as gross (theoretical max)",
            "net_sum_total": round(float(net.sum()), 2),
            "n_trades_used": n_matched,
            "n_months": len(m),
            "monthly_avg": round(float(m.mean()), 2),
            "worst_month_net": round(float(m.min()), 2),
            "best_month_net": round(float(m.max()), 2),
            "n_months_above_1900": int((m >= PASS_LINE_MONTH).sum()),
            "all_12mo_pass_1900": bool((m >= PASS_LINE_MONTH).all()),
            "approx_note": "matched subset only (2025 / no 2026-Q1). Negative MFE clipped to 0.",
        })

    # Pattern: TP/SL combos
    # MFE/MAE-pct medians for old P1-P24 by side & K → use as base
    j_pct = j.copy()
    for K in K_LIST:
        for side in SIDE_LIST:
            j_pct.loc[j_pct["side"] == side, f"_mfe_pct_K{K}"] = (
                j_pct.loc[j_pct["side"] == side, f"{side}_MFE_K{K}"] /
                j_pct.loc[j_pct["side"] == side, "_pq_close"]
            )
            j_pct.loc[j_pct["side"] == side, f"_mae_pct_K{K}"] = (
                j_pct.loc[j_pct["side"] == side, f"{side}_MAE_K{K}"] /
                j_pct.loc[j_pct["side"] == side, "_pq_close"]
            )

    def simulate_tpsl(K, tp_pct, sl_pct, assume="conservative"):
        """Per-trade TP/SL using K-window MFE/MAE.
        assume='conservative': if both TP and SL hit in window, assume SL hit first (worst case).
        assume='optimistic': assume TP first.
        If neither hits: use close at t+K (time exit).
        """
        out_rows = []
        for _, r in j_pct.iterrows():
            side = r["side"]
            mfe_pct = r[f"_mfe_pct_K{K}"]
            mae_pct = r[f"_mae_pct_K{K}"]
            ep = r["_pq_close"]
            sz = r["size_btc"]
            if pd.isna(mfe_pct) or pd.isna(mae_pct) or pd.isna(ep):
                out_rows.append({"ym": r["ym"], "net": np.nan})
                continue
            tp_hit = mfe_pct >= tp_pct
            sl_hit = mae_pct >= sl_pct
            if tp_hit and sl_hit:
                gross = -sl_pct * ep * sz if assume == "conservative" else tp_pct * ep * sz
            elif tp_hit:
                gross = tp_pct * ep * sz
            elif sl_hit:
                gross = -sl_pct * ep * sz
            else:
                close_K_val = r.get(f"close_K{K}")
                if pd.isna(close_K_val):
                    out_rows.append({"ym": r["ym"], "net": np.nan})
                    continue
                if side == "LONG":
                    gross = (close_K_val - ep) * sz
                else:
                    gross = (ep - close_K_val) * sz
            net = gross - r["fee_usd"]
            out_rows.append({"ym": r["ym"], "net": net})
        return pd.DataFrame(out_rows)

    # Use side-aggregated median MFE/MAE pct as anchor
    # For each K, base TP/SL = median MFE/MAE pct × {0.5, 0.7, 0.9, 1.0}
    for K in [12, 24, 48, 96]:
        # combine LONG+SHORT median (they're broadly comparable in pct)
        all_mfe_pct = pd.concat([
            j_pct.loc[j_pct["side"] == "LONG", f"_mfe_pct_K{K}"],
            j_pct.loc[j_pct["side"] == "SHORT", f"_mfe_pct_K{K}"],
        ]).dropna()
        all_mae_pct = pd.concat([
            j_pct.loc[j_pct["side"] == "LONG", f"_mae_pct_K{K}"],
            j_pct.loc[j_pct["side"] == "SHORT", f"_mae_pct_K{K}"],
        ]).dropna()
        mfe_med = float(all_mfe_pct.median())
        mae_med = float(all_mae_pct.median())

        for tp_f, sl_f in [(0.5, 0.5), (0.7, 0.7), (0.9, 0.9), (1.0, 1.0), (0.7, 0.5), (0.9, 0.5)]:
            tp_pct = mfe_med * tp_f
            sl_pct = mae_med * sl_f
            for assume in ["conservative", "optimistic"]:
                sim = simulate_tpsl(K, tp_pct, sl_pct, assume=assume)
                m = sim.groupby("ym")["net"].sum()
                rows.append({
                    "pattern_id": f"tpsl_K{K}_tp{tp_f}_sl{sl_f}_{assume}",
                    "pattern_label": f"K={K} TP={tp_pct:.4f} (={tp_f}×median MFE) SL={sl_pct:.4f} (={sl_f}×median MAE) | assume={assume}",
                    "net_sum_total": round(float(sim["net"].sum()), 2),
                    "n_trades_used": int(sim["net"].notna().sum()),
                    "n_months": len(m),
                    "monthly_avg": round(float(m.mean()), 2),
                    "worst_month_net": round(float(m.min()), 2),
                    "best_month_net": round(float(m.max()), 2),
                    "n_months_above_1900": int((m >= PASS_LINE_MONTH).sum()),
                    "all_12mo_pass_1900": bool((m >= PASS_LINE_MONTH).all()),
                    "approx_note": "matched subset / order-of-touch unknown / 'conservative'=SL-first if both hit, 'optimistic'=TP-first.",
                })

    # Pattern: time exit at K only (no TP/SL)
    for K in K_LIST:
        def calc(r):
            close_K_val = r.get(f"close_K{K}")
            ep = r["_pq_close"]
            if pd.isna(close_K_val) or pd.isna(ep):
                return np.nan
            if r["side"] == "LONG":
                gross = (close_K_val - ep) * r["size_btc"]
            else:
                gross = (ep - close_K_val) * r["size_btc"]
            return gross - r["fee_usd"]
        net = j.apply(calc, axis=1)
        m = j.assign(net=net).groupby("ym")["net"].sum()
        MONTHLY_SERIES[f"time_exit_K{K}"] = {str(k): round(float(v), 2) for k, v in m.items()}
        rows.append({
            "pattern_id": f"time_exit_K{K}",
            "pattern_label": f"Pure time exit at K={K} bars (close-to-close, no TP/SL)",
            "net_sum_total": round(float(net.sum()), 2),
            "n_trades_used": int(net.notna().sum()),
            "n_months": len(m),
            "monthly_avg": round(float(m.mean()), 2),
            "worst_month_net": round(float(m.min()), 2),
            "best_month_net": round(float(m.max()), 2),
            "n_months_above_1900": int((m >= PASS_LINE_MONTH).sum()),
            "all_12mo_pass_1900": bool((m >= PASS_LINE_MONTH).all()),
            "approx_note": "matched subset only.",
        })

    df = pd.DataFrame(rows)
    out = OUT_DIR / "headroom_step4_virtual_exit.csv"
    df.to_csv(out, index=False)
    log(f"  wrote {out} ({len(df)} rows)")
    return df


# ─────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────
def build_summary(trades, par, joined, matched_mask, s1, s2, s3, s4,
                  fee_rate, t_start, t_end):
    log("Building summary md")
    lines = []
    lines.append("# 頭打ち原因分析 結果サマリー")
    lines.append("")
    lines.append(f"生成日時: {t_end.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("仕様: [.claude/memory/headroom_analysis_spec.md](../../.claude/memory/headroom_analysis_spec.md)")
    lines.append("")
    lines.append("## §0 データ前提・カバレッジ")
    lines.append("")
    lines.append(f"- replay trade 数: **{len(trades)}** / NET 合計 **${trades['net_usd'].sum():.2f}** / 月次平均 **${trades['net_usd'].sum()/12:.2f}**")
    lines.append(f"- 期間: {trades['entry_time'].min()} → {trades['entry_time'].max()}")
    lines.append(f"- parquet test 期間: {par.index.min()} → {par.index.max()}")
    lines.append(f"- parquet マッチ trade 数: **{matched_mask.sum()} / {len(trades)} ({100*matched_mask.mean():.1f}%)** "
                 f"（2026-Q1 の {(~matched_mask).sum()} trade は parquet 未生成のため除外）")
    lines.append(f"- FEE_RATE_MAKER: {fee_rate}")
    lines.append("")

    # Step 1 highlights
    lines.append("## §1 手順1: trade レベル分解（主要数値）")
    lines.append("")
    er = s1[s1["axis_name"] == "exit_reason"].sort_values("net_usd_sum", ascending=False)
    lines.append("### exit_reason 別 NET 寄与")
    lines.append("")
    lines.append("| exit_reason | n_trades | net_usd_sum | net_usd_median | mfe_minus_net_median |")
    lines.append("|---|---:|---:|---:|---:|")
    for _, r in er.iterrows():
        lines.append(f"| {r['bucket']} | {r['n_trades']} | {r['net_usd_sum']} | {r['net_usd_median']} | {r['mfe_minus_net_median']} |")
    lines.append("")
    lines.append("### side / regime / priority 別 NET sum")
    lines.append("")
    lines.append("| axis | bucket | n_trades | net_usd_sum | net_usd_median |")
    lines.append("|---|---|---:|---:|---:|")
    for axis in ["side", "regime", "priority"]:
        sub = s1[s1["axis_name"] == axis].sort_values("net_usd_sum", ascending=False)
        for _, r in sub.iterrows():
            lines.append(f"| {axis} | {r['bucket']} | {r['n_trades']} | {r['net_usd_sum']} | {r['net_usd_median']} |")
    lines.append("")
    lines.append("### entry_hour 別 NET sum（24 行）")
    lines.append("")
    lines.append("| hour | n_trades | net_usd_sum | net_usd_median |")
    lines.append("|---:|---:|---:|---:|")
    sub = s1[s1["axis_name"] == "entry_hour"].sort_values("bucket", key=lambda x: x.astype(int))
    for _, r in sub.iterrows():
        lines.append(f"| {r['bucket']} | {r['n_trades']} | {r['net_usd_sum']} | {r['net_usd_median']} |")
    lines.append("")

    # Step 2 highlights
    lines.append("## §2 手順2: Entry 質ベンチマーク")
    lines.append("")
    lines.append("### MFE/MAE 比較（pct）")
    lines.append("")
    lines.append("| K | side | group | mfe_pct_median | mae_pct_median | ratio | n | p(mfe vs random) | p(mae vs random) |")
    lines.append("|---:|---|---|---:|---:|---:|---:|---:|---:|")
    for _, r in s2.iterrows():
        p_mfe = r.get("mw_u_pvalue_mfe_vs_random", "")
        p_mae = r.get("mw_u_pvalue_mae_vs_random", "")
        lines.append(f"| {r['K']} | {r['side']} | {r['group']} | {r['mfe_pct_median']} | {r['mae_pct_median']} | {r['ratio_mfe_over_mae']} | {r['n']} | {p_mfe} | {p_mae} |")
    lines.append("")

    # Step 3 highlights
    lines.append("## §3 手順3: Position レベル")
    lines.append("")
    lines.append("| axis | bucket | n_trades / n_obs | max | median | min | net_usd_sum |")
    lines.append("|---|---|---:|---:|---:|---:|---:|")
    for _, r in s3.iterrows():
        n_val = r.get("n_trades", r.get("n_obs", ""))
        mx = r.get("max", "")
        md = r.get("median", "")
        mn = r.get("min", "")
        ns = r.get("net_usd_sum", "")
        bucket = r.get("bucket", "")
        if pd.isna(bucket):
            bucket = ""
        lines.append(f"| {r['axis']} | {bucket} | {n_val} | {mx} | {md} | {mn} | {ns} |")
    lines.append("")

    # Step 4 highlights
    lines.append("## §4 手順4: 仮想 Exit シミュレーション")
    lines.append("")
    lines.append("（matched subset = 733 trade / 2025-04-01 → 2025-12-31 のみ。2026-Q1 の 424 trade は parquet 未生成のため除外。実 Replay との完全一致でない近似計算前提）")
    lines.append("")
    lines.append("| pattern_id | net_sum_total | monthly_avg | worst_month | best_month | n_months_above_1900 | all_12mo_pass_1900 | n_trades |")
    lines.append("|---|---:|---:|---:|---:|---:|:---:|---:|")
    for _, r in s4.iterrows():
        lines.append(f"| {r['pattern_id']} | {r['net_sum_total']} | {r['monthly_avg']} | {r['worst_month_net']} | {r['best_month_net']} | {r['n_months_above_1900']} | {r['all_12mo_pass_1900']} | {r['n_trades_used']} |")
    lines.append("")

    # Conclusion (data-driven)
    lines.append("## §5 結論パターン判定（データ駆動）")
    lines.append("")
    # Use median p-values for old_p1_p24 vs random (mfe)
    old_p1 = s2[s2["group"] == "old_p1_p24"]
    p_mfe_med = float(old_p1["mw_u_pvalue_mfe_vs_random"].median())
    p_mae_med = float(old_p1["mw_u_pvalue_mae_vs_random"].median())
    perfect_K24 = s4[s4["pattern_id"] == "perfect_exit_K24"].iloc[0]
    perfect_K96 = s4[s4["pattern_id"] == "perfect_exit_K96"].iloc[0]
    best_pattern = s4.sort_values("monthly_avg", ascending=False).iloc[0]
    baseline = s4[s4["pattern_id"] == "baseline_actual"].iloc[0]
    lines.append(f"- Entry 質（p-value 中央値）: mfe-vs-random p={p_mfe_med:.4f} / mae-vs-random p={p_mae_med:.4f}")
    lines.append(f"  - p<0.05 なら旧 P1-P24 Entry は random より統計的に有意に良い（mfe 大 or mae 小）")
    lines.append(f"- 仮想 Exit 改善余地: monthly_avg 最高パターン = `{best_pattern['pattern_id']}` / monthly_avg ${best_pattern['monthly_avg']}（baseline ${baseline['monthly_avg']}）")
    lines.append(f"- Perfect K=24 月次平均: ${perfect_K24['monthly_avg']} / Perfect K=96 月次平均: ${perfect_K96['monthly_avg']}")
    lines.append(f"- 合格ライン $1,900/月 を全 12 ヶ月クリアするパターン: {int(s4['all_12mo_pass_1900'].sum())} / {len(s4)}")
    lines.append("")
    lines.append("### 判定マトリクス（仕様書 §5）")
    lines.append("")
    lines.append("| 判定軸 | 観測値 | 該当 |")
    lines.append("|---|---|---|")
    entry_ok = "YES" if p_mfe_med < 0.05 else "NO"
    perfect_pass = "YES" if bool(perfect_K96["all_12mo_pass_1900"]) else "NO"
    any_pattern_pass = "YES" if int(s4["all_12mo_pass_1900"].sum()) > 0 else "NO"
    lines.append(f"| Entry 質 random より良い？ | p_mfe_median={p_mfe_med:.4f} | {entry_ok} |")
    lines.append(f"| 完璧 K=96 Exit で全月 $1,900 達成？ | worst={perfect_K96['worst_month_net']} | {perfect_pass} |")
    lines.append(f"| いずれかの仮想 Exit で全月 $1,900 達成？ | n_pass={int(s4['all_12mo_pass_1900'].sum())} | {any_pattern_pass} |")
    lines.append("")
    # Data-driven conclusion
    if perfect_pass == "NO":
        verdict = ("**構造的限界の可能性**: 完璧 K=96 Exit でも全月 $1,900 を満たさない。"
                   "→ 旧 P1-P24 Entry の MFE 総量上限が合格ラインに届かない。"
                   "A-2 大枠ドラフトでは Entry 規則そのものの再設計（新 Priority 並立・MTF 組合せ最適化）が必要。")
    elif entry_ok == "NO":
        verdict = ("**Entry 規則精度不足の可能性**: 完璧 Exit で合格ラインに届くが、Entry 質が random と区別できない。"
                   "→ A-2 大枠ドラフトでは Entry 規則の精度向上を主軸（ML を Entry 側に投入）。")
    elif any_pattern_pass == "YES":
        verdict = ("**Exit 設計改善の可能性**: Entry 質は機能している + 仮想 Exit パターンで合格ライン到達例あり。"
                   "→ A-2 大枠ドラフトでは Exit 設計を主軸（ML を Exit 側に投入）。")
    else:
        verdict = ("**Entry+Exit 両方の改善余地**: Entry 質は機能しているが、現実的 Exit パラメータで合格ライン未到達。"
                   "→ A-2 大枠ドラフトでは Entry/Exit 両方に ML を投入する設計検討。")
    lines.append(f"**データ駆動の暫定判定**: {verdict}")
    lines.append("")
    lines.append("> 注: 上記は本仕様 §5 マトリクスの機械的マッピング。最終判定は Web Claude / まこさんが本サマリー + ダッシュボードを確認の上で決定。")
    lines.append("")

    # Footer: 必須証跡
    lines.append("## §6 成果物ファイル一覧")
    lines.append("")
    for fn in ["headroom_step1_trade_decomp.csv",
               "headroom_step2_entry_quality.csv",
               "headroom_step3_position.csv",
               "headroom_step4_virtual_exit.csv"]:
        p = OUT_DIR / fn
        if p.exists():
            sz = p.stat().st_size
            mt = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            n_lines = sum(1 for _ in open(p))
            lines.append(f"- [{fn}](./{fn}) — {n_lines} 行 / {sz} bytes / 更新 {mt}")
    lines.append("")

    lines.append("## §7 実行ログ")
    lines.append("")
    lines.append(f"- コマンド: `python3 scripts/priority_rebuild/headroom_analysis.py`")
    lines.append(f"- 開始時刻: {t_start.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- 終了時刻: {t_end.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- 所要時間: {(t_end - t_start).total_seconds():.1f} 秒")
    lines.append(f"- 入力 replay CSV: {REPLAY_CSV.relative_to(REPO)}")
    lines.append(f"- 入力 parquet: {PARQUET_TEST.relative_to(REPO)}")
    lines.append("")

    out = OUT_DIR / "headroom_analysis_summary.md"
    out.write_text("\n".join(lines))
    log(f"  wrote {out}")
    return out


def build_dashboard_json(trades, par, matched_mask, s1, s2, s3, s4, fee, t_end):
    """Write dashboard/data/headroom_analysis.json for tab ⑮."""
    log("Building dashboard JSON")
    DASH_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Verdict (mirrors summary md logic)
    old_p1 = s2[s2["group"] == "old_p1_p24"]
    p_mfe_med = float(old_p1["mw_u_pvalue_mfe_vs_random"].median())
    p_mae_med = float(old_p1["mw_u_pvalue_mae_vs_random"].median())
    perfect_K96 = s4[s4["pattern_id"] == "perfect_exit_K96"].iloc[0]
    entry_ok = bool(p_mfe_med < 0.05)
    perfect_pass = bool(perfect_K96["all_12mo_pass_1900"])
    any_pass = int(s4["all_12mo_pass_1900"].sum()) > 0
    if not perfect_pass:
        verdict_label = "構造的限界の可能性"
        verdict_detail = (
            "完璧 K=96 Exit でも全月 $1,900 不達。Entry 規則そのものの再設計が必要。"
            f" worst_month={perfect_K96['worst_month_net']}"
        )
    elif not entry_ok:
        verdict_label = "Entry 規則精度不足の可能性"
        verdict_detail = "完璧 Exit で合格ラインに届くが Entry 質が random と区別できない。ML を Entry 側に投入。"
    elif any_pass:
        verdict_label = "Exit 設計改善の可能性"
        verdict_detail = "Entry 質は機能 + 仮想 Exit パターンで合格ライン到達例あり。ML を Exit 側に投入。"
    else:
        verdict_label = "Entry+Exit 両方の改善余地"
        verdict_detail = "Entry 質は機能しているが現実的 Exit で合格ライン未到達。ML を両方に投入。"

    def df_records(df):
        return df.where(df.notna(), None).to_dict(orient="records")

    data = {
        "meta": {
            "generated_at": t_end.strftime("%Y-%m-%d %H:%M:%S"),
            "spec_path": ".claude/memory/headroom_analysis_spec.md",
            "replay_csv": str(REPLAY_CSV.relative_to(REPO)),
            "parquet_test": str(PARQUET_TEST.relative_to(REPO)),
            "replay_n": int(len(trades)),
            "replay_net": round(float(trades["net_usd"].sum()), 2),
            "replay_monthly_avg": round(float(trades["net_usd"].sum()) / 12, 2),
            "replay_start": str(trades["entry_time"].min()),
            "replay_end": str(trades["entry_time"].max()),
            "parquet_start": str(par.index.min()),
            "parquet_end": str(par.index.max()),
            "matched_n": int(matched_mask.sum()),
            "matched_pct": round(100 * float(matched_mask.mean()), 2),
            "fee_rate_maker": fee,
            "pass_line_month": PASS_LINE_MONTH,
        },
        "step1": {
            "exit_reason": df_records(s1[s1["axis_name"] == "exit_reason"]),
            "side": df_records(s1[s1["axis_name"] == "side"]),
            "regime": df_records(s1[s1["axis_name"] == "regime"]),
            "priority": df_records(s1[s1["axis_name"] == "priority"]),
            "priority_x_side": df_records(s1[s1["axis_name"] == "priority_x_side"]),
            "entry_hour": df_records(s1[s1["axis_name"] == "entry_hour"]),
            "entry_weekday": df_records(s1[s1["axis_name"] == "entry_weekday"]),
            "adx_bucket": df_records(s1[s1["axis_name"] == "adx_bucket"]),
            "bb_width_bucket": df_records(s1[s1["axis_name"] == "bb_width_bucket"]),
            "atr14_bucket": df_records(s1[s1["axis_name"] == "atr14_bucket"]),
            "hold_min_bucket": df_records(s1[s1["axis_name"] == "hold_min_bucket"]),
        },
        "step2": df_records(s2),
        "step3": {
            "trades_per_day": df_records(s3[s3["axis"] == "trades_per_day"]),
            "concurrent_positions": df_records(s3[s3["axis"] == "concurrent_positions"]),
            "concurrent_positions_by_side": df_records(s3[s3["axis"] == "concurrent_positions_by_side"]),
            "priority_x_side_alloc": df_records(s3[s3["axis"] == "priority_x_side_alloc"]),
            "missed_fire": df_records(s3[s3["axis"] == "missed_fire"]),
        },
        "step4": {
            "rows": df_records(s4),
            "monthly_series": MONTHLY_SERIES,
        },
        "verdict": {
            "entry_quality_ok": entry_ok,
            "p_mfe_vs_random_median": round(p_mfe_med, 6),
            "p_mae_vs_random_median": round(p_mae_med, 6),
            "perfect_k96_all_12mo_pass": perfect_pass,
            "perfect_k96_worst_month": float(perfect_K96["worst_month_net"]),
            "any_pattern_all_12mo_pass": any_pass,
            "n_patterns_all_pass": int(s4["all_12mo_pass_1900"].sum()),
            "n_patterns_total": int(len(s4)),
            "verdict_label": verdict_label,
            "verdict_detail": verdict_detail,
        },
    }
    def clean_nan(obj):
        if isinstance(obj, dict):
            return {k: clean_nan(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [clean_nan(v) for v in obj]
        if isinstance(obj, float) and math.isnan(obj):
            return None
        return obj

    out = DASH_DATA_DIR / "headroom_analysis.json"
    out.write_text(json.dumps(clean_nan(data), ensure_ascii=False, indent=2, allow_nan=False))
    log(f"  wrote {out}")


def main():
    t_start = datetime.now()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    trades, par, fee = load_inputs()
    joined, matched_mask = join_with_labels(trades, par)

    s1 = step1_decompose(trades)
    s2 = step2_entry_quality(joined, matched_mask, par)
    s3 = step3_position(trades)
    s4 = step4_virtual_exit(trades, joined, matched_mask, par, fee)

    t_end = datetime.now()
    build_summary(trades, par, joined, matched_mask, s1, s2, s3, s4, fee, t_start, t_end)
    build_dashboard_json(trades, par, matched_mask, s1, s2, s3, s4, fee, t_end)
    log(f"DONE in {(t_end - t_start).total_seconds():.1f}s")


if __name__ == "__main__":
    main()
