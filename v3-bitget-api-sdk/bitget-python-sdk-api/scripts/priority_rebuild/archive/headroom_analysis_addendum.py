#!/usr/bin/env python3
"""headroom_analysis_addendum.py — 0-β: 構造的限界 vs Entry網羅性不足 の切り分け

仕様: .claude/memory/headroom_analysis_addendum_spec.md (§1-§6)
出力:
  results/priority_rebuild/headroom_step5_monthly_breakdown.csv
  results/priority_rebuild/headroom_step6_worst_best_month_detail.csv
  results/priority_rebuild/headroom_step7_long_diagnosis.csv
  results/priority_rebuild/headroom_step8_missed_fire.csv  (N/A + 理由)
  results/priority_rebuild/headroom_analysis_addendum_summary.md
"""
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

# Reuse base loader from 0-α script
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from headroom_analysis import (  # type: ignore
    LABEL_COLS, K_LIST, SIDE_LIST, PASS_LINE_MONTH,
    REPO, OUT_DIR, log, load_inputs, join_with_labels,
)


def step5_monthly_breakdown(trades: pd.DataFrame, joined: pd.DataFrame,
                            matched_mask: pd.Series) -> pd.DataFrame:
    log("Step 5: monthly breakdown")
    trades_m = trades.assign(ym=trades["entry_time"].dt.to_period("M").astype(str))
    base_grp = trades_m.groupby("ym")

    j = joined[matched_mask].copy()
    j["ym"] = j["entry_time"].dt.to_period("M").astype(str)

    # perfect_K96 net per matched trade
    def perfect_K96_row(r):
        v = r[f"{r['side']}_MFE_K96"]
        if pd.isna(v):
            return np.nan
        return max(0.0, float(v)) * float(r["size_btc"]) - float(r["fee_usd"])
    j["_p96_net"] = j.apply(perfect_K96_row, axis=1)

    # time_exit_K96 net per matched trade
    par_close = joined["_pq_close"]  # entry-bar close
    # We need close at t+96. Recompute via parquet shift.
    # Easiest: load par again and shift here.
    par = pd.read_parquet(REPO / "results/priority_rebuild/labels_mfe_mae_test_2025.parquet",
                          columns=["close"])
    par["close_K96"] = par["close"].shift(-96)
    par_reset = par.reset_index().rename(columns={"timestamp": "_pq_ts"})
    j = j.merge(par_reset[["_pq_ts", "close_K96"]], on="_pq_ts", how="left",
                suffixes=("", "_dup"))

    def time_K96_net(r):
        ep = r["_pq_close"]
        cK = r["close_K96"]
        if pd.isna(ep) or pd.isna(cK):
            return np.nan
        sign = 1 if r["side"] == "LONG" else -1
        gross = sign * (cK - ep) * float(r["size_btc"])
        return gross - float(r["fee_usd"])
    j["_t96_net"] = j.apply(time_K96_net, axis=1)

    matched_grp = j.groupby("ym")

    months = sorted(base_grp.groups.keys())
    rows = []
    for ym in months:
        bg = base_grp.get_group(ym)
        mg = matched_grp.get_group(ym) if ym in matched_grp.groups else None
        rows.append({
            "year_month": ym,
            "baseline_n_trades": int(len(bg)),
            "baseline_net_sum": round(float(bg["net_usd"].sum()), 2),
            "baseline_net_per_trade": round(float(bg["net_usd"].sum() / len(bg)), 4) if len(bg) else None,
            "matched_n_trades": int(len(mg)) if mg is not None else 0,
            "perfect_K96_net_sum": round(float(mg["_p96_net"].sum()), 2) if mg is not None else 0.0,
            "perfect_K96_net_per_trade": round(float(mg["_p96_net"].sum() / len(mg)), 4) if mg is not None and len(mg) > 0 else None,
            "time_exit_K96_net_sum": round(float(mg["_t96_net"].sum()), 2) if mg is not None else 0.0,
            "baseline_above_1900": bool(bg["net_usd"].sum() >= PASS_LINE_MONTH),
            "perfect_K96_above_1900": bool(mg is not None and mg["_p96_net"].sum() >= PASS_LINE_MONTH),
        })

    df = pd.DataFrame(rows)
    out = OUT_DIR / "headroom_step5_monthly_breakdown.csv"
    df.to_csv(out, index=False)
    log(f"  wrote {out} ({len(df)} rows)")
    return df, j  # j has _p96_net for step 6


def step6_worst_best_month_detail(j_p96: pd.DataFrame, par: pd.DataFrame) -> pd.DataFrame:
    log("Step 6: worst/best month detail (perfect_K96 basis)")
    # Auto-detect worst and best month from perfect_K96 monthly NET (matched subset)
    monthly_net = j_p96.groupby("ym")["_p96_net"].sum()
    worst_ym = str(monthly_net.idxmin())
    best_ym = str(monthly_net.idxmax())
    log(f"  worst month: {worst_ym} (${monthly_net.min():.2f}) / best month: {best_ym} (${monthly_net.max():.2f})")

    rows = []
    for label, ym in [("worst", worst_ym), ("best", best_ym)]:
        sub = j_p96[j_p96["ym"] == ym].copy()
        # Trade count
        rows.append({
            "label": label, "year_month": ym, "axis": "trade_count", "bucket": "all",
            "n_trades": int(len(sub)),
            "net_usd_sum": round(float(sub["net_usd"].sum()), 2),
            "perfect_K96_net_sum": round(float(sub["_p96_net"].sum()), 2),
        })
        # side distribution
        for sd, g in sub.groupby("side"):
            rows.append({
                "label": label, "year_month": ym, "axis": "side", "bucket": sd,
                "n_trades": int(len(g)),
                "net_usd_sum": round(float(g["net_usd"].sum()), 2),
                "perfect_K96_net_sum": round(float(g["_p96_net"].sum()), 2),
            })
        # regime distribution
        for rg, g in sub.groupby("regime"):
            rows.append({
                "label": label, "year_month": ym, "axis": "regime", "bucket": str(rg),
                "n_trades": int(len(g)),
                "net_usd_sum": round(float(g["net_usd"].sum()), 2),
                "perfect_K96_net_sum": round(float(g["_p96_net"].sum()), 2),
            })
        # hour distribution (bucketed: 0-6 / 6-12 / 12-18 / 18-24)
        hour_buck = pd.cut(sub["entry_hour"], bins=[-1, 5, 11, 17, 23],
                           labels=["00-05", "06-11", "12-17", "18-23"])
        for hb, g in sub.assign(_hb=hour_buck).groupby("_hb", observed=True):
            rows.append({
                "label": label, "year_month": ym, "axis": "hour_bucket", "bucket": str(hb),
                "n_trades": int(len(g)),
                "net_usd_sum": round(float(g["net_usd"].sum()), 2),
                "perfect_K96_net_sum": round(float(g["_p96_net"].sum()), 2),
            })
        # priority × side distribution
        for (p, sd), g in sub.groupby(["priority", "side"]):
            rows.append({
                "label": label, "year_month": ym, "axis": "priority_x_side",
                "bucket": f"P{p}-{sd}",
                "n_trades": int(len(g)),
                "net_usd_sum": round(float(g["net_usd"].sum()), 2),
                "perfect_K96_net_sum": round(float(g["_p96_net"].sum()), 2),
            })
        # Market state from parquet (price range / ATR median from replay)
        ym_period = pd.Period(ym, freq="M")
        par_m = par[(par.index.to_period("M") == ym_period)]
        if len(par_m) > 0:
            pmin = float(par_m["close"].min())
            pmax = float(par_m["close"].max())
            prange = pmax - pmin
            range_pct = round(100 * prange / pmin, 2) if pmin > 0 else None
            rows.append({
                "label": label, "year_month": ym, "axis": "market_state",
                "bucket": "btc_price_range",
                "value": f"${pmin:.0f}-${pmax:.0f}",
                "range_pct": range_pct,
                "n_bars": int(len(par_m)),
            })
        atr_med = float(sub["atr_14"].median()) if len(sub) > 0 else None
        rows.append({
            "label": label, "year_month": ym, "axis": "market_state",
            "bucket": "atr_14_median_at_entry",
            "value": round(atr_med, 2) if atr_med is not None else None,
            "n_trades": int(len(sub)),
        })

    df = pd.DataFrame(rows)
    out = OUT_DIR / "headroom_step6_worst_best_month_detail.csv"
    df.to_csv(out, index=False)
    log(f"  wrote {out} ({len(df)} rows)")
    return df, worst_ym, best_ym


def step7_long_diagnosis(trades: pd.DataFrame, joined: pd.DataFrame,
                          matched_mask: pd.Series) -> pd.DataFrame:
    log("Step 7: LONG diagnosis")
    long_trades = trades[trades["side"] == "LONG"].copy()
    rows = []

    # MFE loss summary
    loss = long_trades["mfe_usd"] - long_trades["net_usd"]
    rows.append({
        "axis": "mfe_minus_net", "bucket": "all_LONG",
        "n": int(len(long_trades)),
        "median": round(float(loss.median()), 4),
        "mean": round(float(loss.mean()), 4),
        "p25": round(float(loss.quantile(0.25)), 4),
        "p75": round(float(loss.quantile(0.75)), 4),
        "p90": round(float(loss.quantile(0.90)), 4),
        "max": round(float(loss.max()), 4),
    })

    # exit_reason breakdown for LONG
    for er, g in long_trades.groupby("exit_reason"):
        rows.append({
            "axis": "exit_reason", "bucket": str(er),
            "n": int(len(g)),
            "net_usd_sum": round(float(g["net_usd"].sum()), 2),
            "net_usd_median": round(float(g["net_usd"].median()), 4),
            "mfe_usd_median": round(float(g["mfe_usd"].median()), 4),
            "mfe_minus_net_median": round(float((g["mfe_usd"] - g["net_usd"]).median()), 4),
            "hold_min_median": round(float(g["hold_min"].median()), 1),
        })

    # hold_min distribution for LONG
    hold_buck = pd.cut(long_trades["hold_min"],
                       bins=[-1, 0, 30, 60, 120, 240, 480, 100000],
                       labels=["instant", "0-30", "30-60", "60-120", "120-240", "240-480", "≥480"])
    for hb, g in long_trades.assign(_hb=hold_buck).groupby("_hb", observed=True):
        rows.append({
            "axis": "hold_min_bucket", "bucket": str(hb),
            "n": int(len(g)),
            "net_usd_sum": round(float(g["net_usd"].sum()), 2),
            "net_usd_median": round(float(g["net_usd"].median()), 4),
            "mfe_minus_net_median": round(float((g["mfe_usd"] - g["net_usd"]).median()), 4),
        })

    # LONG-only perfect Exit simulation (matched subset)
    j_long = joined[matched_mask & (joined["side"] == "LONG")].copy()
    for K in K_LIST:
        col = f"LONG_MFE_K{K}"
        gross = (j_long[col].clip(lower=0) * j_long["size_btc"])
        net = gross - j_long["fee_usd"]
        rows.append({
            "axis": "long_perfect_exit", "bucket": f"K={K}",
            "n": int(len(j_long)),
            "net_sum": round(float(net.sum()), 2),
            "net_mean": round(float(net.mean()), 4),
            "net_median": round(float(net.median()), 4),
        })

    # LONG perfect K=96 monthly check (matched LONG only)
    j_long["ym"] = j_long["entry_time"].dt.to_period("M").astype(str)
    j_long["_long_p96_net"] = (j_long["LONG_MFE_K96"].clip(lower=0) * j_long["size_btc"]) - j_long["fee_usd"]
    monthly = j_long.groupby("ym")["_long_p96_net"].sum()
    rows.append({
        "axis": "long_perfect_K96_monthly", "bucket": "summary",
        "n_months": int(len(monthly)),
        "net_sum": round(float(monthly.sum()), 2),
        "monthly_mean": round(float(monthly.mean()), 2),
        "monthly_min": round(float(monthly.min()), 2),
        "monthly_max": round(float(monthly.max()), 2),
        "n_months_above_1900": int((monthly >= PASS_LINE_MONTH).sum()),
    })

    df = pd.DataFrame(rows)
    out = OUT_DIR / "headroom_step7_long_diagnosis.csv"
    df.to_csv(out, index=False)
    log(f"  wrote {out} ({len(df)} rows)")
    return df


def step8_missed_fire() -> pd.DataFrame:
    log("Step 8: missed_fire (N/A)")
    rows = [{
        "axis": "missed_fire",
        "status": "N/A",
        "reason": "replay_csv.py の出力には Entry 条件成立だが発火しなかった bar のログが含まれていない。"
                  "再 Replay + logging 改修が必要だが、本タスクのスコープ外（仕様書 §2 追加4 / "
                  "2026-05-13 まこさん指示 Option A）",
        "alternatives": "(B) replay_csv.py 再実行で logging 追加（runner 改修必要・半日〜1日）/"
                        " (C) cat_v9_decider シグナル発火を別途計算 → entry_time と照合して間接推定（1日）",
    }]
    df = pd.DataFrame(rows)
    out = OUT_DIR / "headroom_step8_missed_fire.csv"
    df.to_csv(out, index=False)
    log(f"  wrote {out} ({len(df)} rows)")
    return df


def build_summary(s5, s6, s7, s8, worst_ym, best_ym, trades, t_start, t_end):
    log("Building addendum summary md")
    lines = []
    lines.append("# 頭打ち原因分析 追加分析 結果サマリー (0-β)")
    lines.append("")
    lines.append(f"生成日時: {t_end.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("仕様: [.claude/memory/headroom_analysis_addendum_spec.md](../../.claude/memory/headroom_analysis_addendum_spec.md)")
    lines.append("前提: [headroom_analysis_summary.md](headroom_analysis_summary.md) 完了済")
    lines.append("")
    lines.append("## §0 データ前提")
    lines.append("")
    lines.append(f"- replay trade 数: {len(trades)} / matched (2025 parquet) 733 trade")
    lines.append("- baseline 12 ヶ月（2025-04 → 2026-03）/ matched subset 9 ヶ月（2025-04 → 2025-12）")
    lines.append("")

    # §1 monthly breakdown
    lines.append("## §1 追加1: 月別 trade 数 / NET 分布（step5）")
    lines.append("")
    lines.append("| year_month | baseline_n | baseline_net | matched_n | perfect_K96_net | time_K96_net | baseline_pass$1900 | perfect_K96_pass$1900 |")
    lines.append("|---|---:|---:|---:|---:|---:|:---:|:---:|")
    for _, r in s5.iterrows():
        lines.append(f"| {r['year_month']} | {r['baseline_n_trades']} | ${r['baseline_net_sum']:.2f} | {r['matched_n_trades']} | ${r['perfect_K96_net_sum']:.2f} | ${r['time_exit_K96_net_sum']:.2f} | {'✅' if r['baseline_above_1900'] else '❌'} | {'✅' if r['perfect_K96_above_1900'] else '❌'} |")
    lines.append("")
    n_pass_perfect = int(s5["perfect_K96_above_1900"].sum())
    n_total = len(s5)
    n_pass_baseline = int(s5["baseline_above_1900"].sum())
    lines.append(f"**月別合格カウント**: baseline {n_pass_baseline}/{n_total} ヶ月 ≥ $1,900 / perfect_K96 {n_pass_perfect}/{n_total} ヶ月")
    lines.append("")

    # §2 worst-best detail
    lines.append(f"## §2 追加2: worst month / best month 詳細（step6）")
    lines.append("")
    lines.append(f"- **worst month**: {worst_ym}（perfect_K96 で最低）")
    lines.append(f"- **best month**: {best_ym}（perfect_K96 で最高）")
    lines.append("")
    for label in ["worst", "best"]:
        ym = worst_ym if label == "worst" else best_ym
        sub = s6[s6["label"] == label]
        lines.append(f"### {label} ({ym})")
        lines.append("")
        lines.append("| axis | bucket | n_trades | baseline_net | perfect_K96_net |")
        lines.append("|---|---|---:|---:|---:|")
        for _, r in sub.iterrows():
            n = r.get("n_trades", "")
            bn = r.get("net_usd_sum", "")
            pn = r.get("perfect_K96_net_sum", "")
            extra = ""
            if pd.notna(r.get("value", None)):
                extra = f" ({r.get('value')})"
            lines.append(f"| {r['axis']} | {r['bucket']}{extra} | {n} | {bn} | {pn} |")
        lines.append("")

    # §3 LONG diagnosis
    lines.append("## §3 追加3: LONG 原因分離（step7）")
    lines.append("")
    lines.append("### exit_reason 別 LONG 性能")
    lines.append("")
    lines.append("| exit_reason | n | net_sum | net_median | mfe_median | mfe-net 取りこぼし | hold_min median |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for _, r in s7[s7["axis"] == "exit_reason"].iterrows():
        lines.append(f"| {r['bucket']} | {r['n']} | ${r['net_usd_sum']} | ${r['net_usd_median']} | ${r['mfe_usd_median']} | ${r['mfe_minus_net_median']} | {r['hold_min_median']} |")
    lines.append("")
    lines.append("### LONG hold_min 分布")
    lines.append("")
    lines.append("| hold_min | n | net_sum | net_median | mfe-net 取りこぼし |")
    lines.append("|---|---:|---:|---:|---:|")
    for _, r in s7[s7["axis"] == "hold_min_bucket"].iterrows():
        lines.append(f"| {r['bucket']} | {r['n']} | ${r['net_usd_sum']} | ${r['net_usd_median']} | ${r['mfe_minus_net_median']} |")
    lines.append("")
    lines.append("### LONG 完璧 Exit シミュレーション")
    lines.append("")
    lines.append("| K | n | net_sum | net_mean | net_median |")
    lines.append("|---|---:|---:|---:|---:|")
    for _, r in s7[s7["axis"] == "long_perfect_exit"].iterrows():
        lines.append(f"| {r['bucket']} | {r['n']} | ${r['net_sum']} | ${r['net_mean']} | ${r['net_median']} |")
    lines.append("")
    long_p96_monthly = s7[s7["axis"] == "long_perfect_K96_monthly"].iloc[0]
    lines.append(f"**LONG only 完璧 K=96 Exit 月別**: 月数={long_p96_monthly['n_months']} / NET=${long_p96_monthly['net_sum']:.2f} / 月次平均=${long_p96_monthly['monthly_mean']:.2f} / 月最低=${long_p96_monthly['monthly_min']:.2f} / 月最高=${long_p96_monthly['monthly_max']:.2f} / 月 ≥$1,900 = {long_p96_monthly['n_months_above_1900']} ヶ月")
    lines.append("")

    # §4 missed_fire
    lines.append("## §4 追加4: missed_fire（step8）")
    lines.append("")
    s8_row = s8.iloc[0]
    lines.append(f"**status**: {s8_row['status']}")
    lines.append("")
    lines.append(f"**reason**: {s8_row['reason']}")
    lines.append("")
    lines.append(f"**alternatives**: {s8_row['alternatives']}")
    lines.append("")

    # §5 判定パターン
    lines.append("## §5 結論パターン判定（データ駆動）")
    lines.append("")
    worst_sub = s6[(s6["label"] == "worst") & (s6["axis"] == "trade_count")].iloc[0]
    best_sub = s6[(s6["label"] == "best") & (s6["axis"] == "trade_count")].iloc[0]
    worst_n = int(worst_sub["n_trades"])
    best_n = int(best_sub["n_trades"])
    matched_median_per_month = int(s5["matched_n_trades"].median())
    long_p96_monthly_mean = long_p96_monthly["monthly_mean"]

    lines.append(f"- worst month ({worst_ym}) matched trade 数: **{worst_n}** / 月別 matched 中央値: {matched_median_per_month}")
    lines.append(f"- best month ({best_ym}) matched trade 数: **{best_n}**")
    lines.append(f"- LONG 完璧 K=96 月次平均: ${long_p96_monthly_mean:.2f}（合格ライン $1,900）")
    lines.append("")
    lines.append("### 判定マトリクス（仕様書 §3）")
    lines.append("")
    lines.append("| 観察パターン | 観測値 | 該当 |")
    lines.append("|---|---|---|")
    # 1. worst month trade極小
    worst_extreme = "YES" if worst_n < matched_median_per_month / 4 else "NO"
    lines.append(f"| worst month の trade 数が極端に少ない | worst={worst_n} / median={matched_median_per_month} | {worst_extreme} |")
    # 2. LONG perfect でも稼げない
    long_perfect_fail = "YES" if long_p96_monthly_mean < PASS_LINE_MONTH else "NO"
    lines.append(f"| LONG 完璧 Exit でも合格ライン未達 | LONG-only monthly_mean=${long_p96_monthly_mean:.2f} | {long_perfect_fail} |")
    # 3. missed_fire 判定不能
    lines.append("| missed_fire が多い | 抽出不可（Option A） | 判定不能 |")
    lines.append("")

    # Verdict
    if worst_extreme == "YES":
        verdict = "**構造的限界**: worst month の trade 数が極端に少なく、その月は完璧 Exit でも届かない。Entry 規則の月次安定発火（新 Priority 並立）が必要。"
    elif long_perfect_fail == "YES":
        verdict = "**LONG Entry規則が悪い**: LONG 完璧 Exit でも合格ラインに届かず、LONG Entry 自体が SHORT と質的に違う可能性。LONG 用の新 Entry 規則設計が必要。"
    else:
        verdict = "**LONG Exit設計が悪い**: LONG 完璧 Exit で合格ラインに届くが現実 Exit で取りこぼしている。LONG 用 Exit 設計の改善が必要。"
    lines.append(f"**データ駆動の暫定判定**: {verdict}")
    lines.append("")
    lines.append("> 注: 本仕様 §3 マトリクスの機械的マッピング。最終判定は Web Claude / まこさんがサマリー全体を確認の上で決定。")
    lines.append("")

    # §6 成果物
    lines.append("## §6 成果物ファイル一覧")
    lines.append("")
    for fn in ["headroom_step5_monthly_breakdown.csv",
               "headroom_step6_worst_best_month_detail.csv",
               "headroom_step7_long_diagnosis.csv",
               "headroom_step8_missed_fire.csv"]:
        p = OUT_DIR / fn
        if p.exists():
            sz = p.stat().st_size
            mt = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            n_lines = sum(1 for _ in open(p))
            lines.append(f"- [{fn}](./{fn}) — {n_lines} 行 / {sz} bytes / 更新 {mt}")
    lines.append("")

    # §7 実行ログ
    lines.append("## §7 実行ログ")
    lines.append("")
    lines.append("- コマンド: `python3 scripts/priority_rebuild/headroom_analysis_addendum.py`")
    lines.append(f"- 開始: {t_start.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- 終了: {t_end.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- 所要: {(t_end - t_start).total_seconds():.1f} 秒")
    lines.append("")

    out = OUT_DIR / "headroom_analysis_addendum_summary.md"
    out.write_text("\n".join(lines))
    log(f"  wrote {out}")


def main():
    t_start = datetime.now()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    trades, par, fee = load_inputs()
    joined, matched_mask = join_with_labels(trades, par)

    s5, j_p96 = step5_monthly_breakdown(trades, joined, matched_mask)
    s6, worst_ym, best_ym = step6_worst_best_month_detail(j_p96, par)
    s7 = step7_long_diagnosis(trades, joined, matched_mask)
    s8 = step8_missed_fire()

    t_end = datetime.now()
    build_summary(s5, s6, s7, s8, worst_ym, best_ym, trades, t_start, t_end)
    log(f"DONE in {(t_end - t_start).total_seconds():.1f}s")


if __name__ == "__main__":
    main()
