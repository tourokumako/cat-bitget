"""intraday_reversal_frequency.py — 日内方向反転頻度の集計 (run-length 版)

問い: 日内 1-3 時間スパンで価格方向 (UP/DT) の反転は頻発するか
目的: regime 設計世界観 (A=持続重視 vs B=日内追随) をデータで判定する材料

方向の定義 (look-ahead なし):
  direction(t, N) = sign(close[t] - close[t-N])
  N ∈ {12=1h, 24=2h, 36=3h}
  横ばい吸収: |delta_pct| < 0.001 (=0.1%) → 0

集計方法 (run-length encoding):
  - direction 系列の連続同符号区間 (run) を抽出
  - sign != 0 の run = UP run / DT run (FLAT run は別カウント)
  - 各 run の持続時間 (分) 分布を集計
  - 1 run = 1 反転事象 (overcount しない)

出力次元 (絞り込まない):
  - run 持続時間 (分) の P25 / median / P75 / P90 (UP / DT / FLAT 別)
  - 全 run 数 / 1 日あたり transition 数
  - per-day / per-month 別

入力: data/BTCUSDT-5m-2021-04-01_03-31_1826d.csv
出力: results/regime_research/intraday_reversal_frequency.md
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

BASE = Path(__file__).parent.parent.parent
DATA_5M = BASE / "data" / "BTCUSDT-5m-2021-04-01_03-31_1826d.csv"
OUT_DIR = BASE / "results" / "regime_research"
OUT_MD = OUT_DIR / "intraday_reversal_frequency.md"

HORIZONS = [
    ("1h", 12),
    ("2h", 24),
    ("3h", 36),
]
FLAT_THRESHOLD = 0.001  # 0.1%


def compute_direction(close: pd.Series, n_bars: int, threshold: float) -> np.ndarray:
    """delta_pct = (close[t] - close[t-N]) / close[t-N]
    返り値: +1 / -1 / 0 (横ばい)。先頭 N バーは 0。"""
    prev = close.shift(n_bars)
    delta_pct = (close - prev) / prev
    direction = np.where(delta_pct > threshold, 1,
                         np.where(delta_pct < -threshold, -1, 0))
    direction[:n_bars] = 0
    return direction.astype(np.int8)


def compute_runs(direction: np.ndarray, timestamps: pd.Series, n_bars_offset: int) -> list:
    """direction 系列を run-length encoding。
    返り値: list of dict {start_ts, end_ts, sign, length_bars, length_min, start_idx, end_idx}
    n_bars_offset: direction の先頭バー (compute_direction で 0 埋めした分) を skip"""
    runs = []
    n = len(direction)
    if n <= n_bars_offset + 1:
        return runs

    cur_sign = int(direction[n_bars_offset])
    cur_start = n_bars_offset
    for i in range(n_bars_offset + 1, n):
        if int(direction[i]) != cur_sign:
            length_bars = i - cur_start
            runs.append({
                "start_idx": cur_start,
                "end_idx": i - 1,
                "sign": cur_sign,
                "length_bars": length_bars,
                "length_min": length_bars * 5,  # 5m 足
                "start_ts": timestamps.iloc[cur_start],
                "end_ts": timestamps.iloc[i - 1],
            })
            cur_sign = int(direction[i])
            cur_start = i
    # 末尾 run
    length_bars = n - cur_start
    runs.append({
        "start_idx": cur_start,
        "end_idx": n - 1,
        "sign": cur_sign,
        "length_bars": length_bars,
        "length_min": length_bars * 5,
        "start_ts": timestamps.iloc[cur_start],
        "end_ts": timestamps.iloc[n - 1],
    })
    return runs


def transitions_per_day(runs: list, total_days: int) -> dict:
    """UP↔DT, UP↔FLAT, DT↔FLAT の transition を数える。"""
    if len(runs) < 2:
        return {"up_to_dt": 0, "dt_to_up": 0, "up_to_flat": 0, "flat_to_up": 0,
                "dt_to_flat": 0, "flat_to_dt": 0, "all_signed_to_signed": 0}
    counts = {"up_to_dt": 0, "dt_to_up": 0, "up_to_flat": 0, "flat_to_up": 0,
              "dt_to_flat": 0, "flat_to_dt": 0}
    for i in range(1, len(runs)):
        prev_sign = runs[i - 1]["sign"]
        cur_sign = runs[i]["sign"]
        if prev_sign == 1 and cur_sign == -1:
            counts["up_to_dt"] += 1
        elif prev_sign == -1 and cur_sign == 1:
            counts["dt_to_up"] += 1
        elif prev_sign == 1 and cur_sign == 0:
            counts["up_to_flat"] += 1
        elif prev_sign == 0 and cur_sign == 1:
            counts["flat_to_up"] += 1
        elif prev_sign == -1 and cur_sign == 0:
            counts["dt_to_flat"] += 1
        elif prev_sign == 0 and cur_sign == -1:
            counts["flat_to_dt"] += 1
    counts["all_signed_to_signed"] = counts["up_to_dt"] + counts["dt_to_up"]
    counts["all_through_flat"] = (counts["up_to_flat"] + counts["flat_to_up"]
                                   + counts["dt_to_flat"] + counts["flat_to_dt"])
    out = {}
    for k, v in counts.items():
        out[k] = v
        out[k + "_per_day"] = v / total_days if total_days > 0 else 0.0
    return out


def run_length_stats(runs: list, sign_filter: int) -> dict:
    """指定 sign の run の持続時間 (分) 統計。"""
    lengths = [r["length_min"] for r in runs if r["sign"] == sign_filter]
    if not lengths:
        return {"n": 0, "median": float("nan"), "mean": float("nan"),
                "p25": float("nan"), "p75": float("nan"), "p90": float("nan"),
                "p99": float("nan"), "max": float("nan")}
    s = pd.Series(lengths)
    return {
        "n": len(lengths),
        "median": float(s.median()),
        "mean": float(s.mean()),
        "p25": float(s.quantile(0.25)),
        "p75": float(s.quantile(0.75)),
        "p90": float(s.quantile(0.90)),
        "p99": float(s.quantile(0.99)),
        "max": float(s.max()),
    }


def runs_per_day(runs: list, timestamps: pd.Series, sign_filter=None) -> pd.Series:
    """日付ごとの run 開始件数。sign_filter=None で全 run。"""
    if sign_filter is not None:
        target = [r for r in runs if r["sign"] == sign_filter]
    else:
        target = runs
    if not target:
        return pd.Series([], dtype=int)
    dates = [r["start_ts"].date() for r in target]
    return pd.Series(dates).value_counts().sort_index()


def runs_per_month(runs: list) -> pd.Series:
    """月別 run 開始件数。"""
    if not runs:
        return pd.Series([], dtype=int)
    months = [(r["start_ts"].year, r["start_ts"].month) for r in runs]
    return pd.Series(months).value_counts().sort_index()


def fmt_pct(x: float, digits: int = 1) -> str:
    return f"{x*100:.{digits}f}%"


def main():
    print(f"[load] {DATA_5M}")
    df = pd.read_csv(DATA_5M, parse_dates=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    print(f"  rows: {len(df):,} / period: {df['timestamp'].iloc[0]} → {df['timestamp'].iloc[-1]}")

    n_days = (df["timestamp"].iloc[-1] - df["timestamp"].iloc[0]).days + 1
    close = df["close"].astype(float)

    sections = []
    sections.append("# 日内方向反転頻度 集計 (run-length 版)\n")
    sections.append(f"- 入力: `{DATA_5M.relative_to(BASE)}`")
    sections.append(f"- 行数: {len(df):,} / 期間: {df['timestamp'].iloc[0]} → {df['timestamp'].iloc[-1]} ({n_days} 日)")
    sections.append(f"- 横ばい閾値: |delta_pct| < {FLAT_THRESHOLD*100:.2f}% → FLAT")
    sections.append("- 方向定義: direction(t, N) = sign(close[t] - close[t-N])")
    sections.append("- 集計方法: direction 系列を run-length encoding。同符号連続区間 = 1 run。")
    sections.append("- 1 run = 1 反転事象。overcount しない。\n")

    # 全N並列で集計 (絞り込まない)
    summary_rows = []
    runs_by_horizon = {}
    transitions_by_horizon = {}

    for label, n_bars in HORIZONS:
        direction = compute_direction(close, n_bars, FLAT_THRESHOLD)
        runs = compute_runs(direction, df["timestamp"], n_bars)
        runs_by_horizon[label] = runs

        up_stats = run_length_stats(runs, sign_filter=1)
        dt_stats = run_length_stats(runs, sign_filter=-1)
        flat_stats = run_length_stats(runs, sign_filter=0)

        trans = transitions_per_day(runs, n_days)
        transitions_by_horizon[label] = trans

        summary_rows.append({
            "horizon": label,
            "n_bars": n_bars,
            "n_runs_total": len(runs),
            "n_up_runs": up_stats["n"],
            "n_dt_runs": dt_stats["n"],
            "n_flat_runs": flat_stats["n"],
            "up": up_stats,
            "dt": dt_stats,
            "flat": flat_stats,
            "trans": trans,
        })

    # ── サマリ表: run length 分布 (UP/DT) ──
    sections.append("## サマリ: 方向継続時間 (分) 分布 (UP/DT 別)")
    sections.append("")
    sections.append("| Horizon | sign | run 数 | 持続時間(分) median | mean | P25 | P75 | P90 | P99 | max |")
    sections.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for r in summary_rows:
        for sign_label, sign_data in [("UP", r["up"]), ("DT", r["dt"]), ("FLAT", r["flat"])]:
            if sign_data["n"] == 0:
                continue
            sections.append(
                f"| {r['horizon']} | {sign_label} | {sign_data['n']:,} "
                f"| {sign_data['median']:.0f} | {sign_data['mean']:.0f} "
                f"| {sign_data['p25']:.0f} | {sign_data['p75']:.0f} "
                f"| {sign_data['p90']:.0f} | {sign_data['p99']:.0f} | {sign_data['max']:.0f} |"
            )
    sections.append("")

    # ── transition / day ──
    sections.append("## 1日あたり transition 数 (反転頻度)")
    sections.append("")
    sections.append("| Horizon | UP→DT/day | DT→UP/day | UP↔DT 直接/day | 経由FLAT/day | 全 transition/day |")
    sections.append("|---|---:|---:|---:|---:|---:|")
    for r in summary_rows:
        t = r["trans"]
        sections.append(
            f"| {r['horizon']} | {t['up_to_dt_per_day']:.2f} | {t['dt_to_up_per_day']:.2f} "
            f"| {t['all_signed_to_signed_per_day']:.2f} "
            f"| {t['all_through_flat_per_day']:.2f} "
            f"| {(t['all_signed_to_signed_per_day'] + t['all_through_flat_per_day']):.2f} |"
        )
    sections.append("")

    # ── A vs B 判定指標 (N=24=2h 基準) ──
    sections.append("## A 設計 vs B 設計 判定指標 (N=24=2h 基準)")
    sections.append("")
    r24 = next(r for r in summary_rows if r["horizon"] == "2h")
    up_med = r24["up"]["median"]
    dt_med = r24["dt"]["median"]
    udt_per_day = r24["trans"]["all_signed_to_signed_per_day"]
    total_trans = udt_per_day + r24["trans"]["all_through_flat_per_day"]
    sections.append(f"- UP 持続時間 median: **{up_med:.0f} 分** ({up_med/60:.1f} 時間)  (A支持 ≥180 / B支持 ≤120)")
    sections.append(f"- DT 持続時間 median: **{dt_med:.0f} 分** ({dt_med/60:.1f} 時間)  (A支持 ≥180 / B支持 ≤120)")
    sections.append(f"- UP↔DT 直接反転/day: **{udt_per_day:.2f} 回**  (A支持 ≤1 / B支持 ≥3)")
    sections.append(f"- 全 transition/day: **{total_trans:.2f} 回**")
    sections.append("")

    # ── per-day run 件数分布 (UP/DT・N=24) ──
    sections.append("## per-day run 件数分布 (N=24=2h)")
    sections.append("")
    runs_24 = runs_by_horizon["2h"]
    daily_up = runs_per_day(runs_24, df["timestamp"], sign_filter=1)
    daily_dt = runs_per_day(runs_24, df["timestamp"], sign_filter=-1)
    bins = [0, 1, 2, 3, 5, 10, 9999]
    bin_labels = ["0", "1", "2", "3-4", "5-9", "10+"]
    sections.append("| run 件数/day | UP run 日数 | UP 比率 | DT run 日数 | DT 比率 |")
    sections.append("|---:|---:|---:|---:|---:|")
    cuts_up = pd.cut(daily_up, bins=bins, labels=bin_labels, right=False)
    cuts_dt = pd.cut(daily_dt, bins=bins, labels=bin_labels, right=False)
    counts_up = cuts_up.value_counts().reindex(bin_labels, fill_value=0)
    counts_dt = cuts_dt.value_counts().reindex(bin_labels, fill_value=0)
    total_up_days = len(daily_up)
    total_dt_days = len(daily_dt)
    for lab in bin_labels:
        cu = int(counts_up.get(lab, 0))
        cd = int(counts_dt.get(lab, 0))
        pu = cu / total_up_days if total_up_days > 0 else 0
        pd_ = cd / total_dt_days if total_dt_days > 0 else 0
        sections.append(f"| {lab} | {cu} | {fmt_pct(pu)} | {cd} | {fmt_pct(pd_)} |")
    sections.append("")

    # ── 月別 transition 数 (N=24) ──
    sections.append("## 月別 UP↔DT 直接反転数 (N=24=2h・季節性確認)")
    sections.append("")
    runs_24 = runs_by_horizon["2h"]
    by_month = {}
    for i in range(1, len(runs_24)):
        prev_sign = runs_24[i - 1]["sign"]
        cur_sign = runs_24[i]["sign"]
        if (prev_sign == 1 and cur_sign == -1) or (prev_sign == -1 and cur_sign == 1):
            ts = runs_24[i]["start_ts"]
            key = (ts.year, ts.month)
            by_month[key] = by_month.get(key, 0) + 1
    sections.append("| 年-月 | UP↔DT 直接反転数 |")
    sections.append("|---|---:|")
    for key in sorted(by_month.keys()):
        sections.append(f"| {key[0]}-{key[1]:02d} | {by_month[key]} |")
    sections.append("")

    # ── 全 N の run 件数分布 ──
    for label, n_bars in HORIZONS:
        runs = runs_by_horizon[label]
        sections.append(f"## per-day run 件数分布 (N={n_bars}={label})")
        sections.append("")
        daily_up = runs_per_day(runs, df["timestamp"], sign_filter=1)
        daily_dt = runs_per_day(runs, df["timestamp"], sign_filter=-1)
        sections.append("| run 件数/day | UP 日数 | UP 比率 | DT 日数 | DT 比率 |")
        sections.append("|---:|---:|---:|---:|---:|")
        cuts_up = pd.cut(daily_up, bins=bins, labels=bin_labels, right=False)
        cuts_dt = pd.cut(daily_dt, bins=bins, labels=bin_labels, right=False)
        cu_cnt = cuts_up.value_counts().reindex(bin_labels, fill_value=0)
        cd_cnt = cuts_dt.value_counts().reindex(bin_labels, fill_value=0)
        for lab in bin_labels:
            cu = int(cu_cnt.get(lab, 0))
            cd = int(cd_cnt.get(lab, 0))
            pu = cu / len(daily_up) if len(daily_up) > 0 else 0
            pd_ = cd / len(daily_dt) if len(daily_dt) > 0 else 0
            sections.append(f"| {lab} | {cu} | {fmt_pct(pu)} | {cd} | {fmt_pct(pd_)} |")
        sections.append("")

    # 出力
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(sections), encoding="utf-8")
    print(f"[done] {OUT_MD}")
    print(f"  total runs: " + ", ".join(f"{r['horizon']}={r['n_runs_total']:,} (UP {r['n_up_runs']:,} / DT {r['n_dt_runs']:,} / FLAT {r['n_flat_runs']:,})" for r in summary_rows))
    print(f"  UP↔DT direct trans/day: " + ", ".join(f"{r['horizon']}={r['trans']['all_signed_to_signed_per_day']:.2f}" for r in summary_rows))


if __name__ == "__main__":
    main()
