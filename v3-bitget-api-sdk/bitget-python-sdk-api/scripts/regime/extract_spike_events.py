"""
急騰急落イベント抽出スクリプト（第1段：分析目的）

⚠️ look-ahead 含む（全期間/年別パーセンタイルで閾値決定）。
   運用組み込み時は再設計が必要（L-128 参照）。

入力 : data/BTCUSDT-5m-2021-04-01_03-31_1826d.csv
出力 : results/spike_analysis/
        - events.parquet         (主出力・全行)
        - events_top1pct.csv     (threshold 1%/0.1% タグのみ)
        - distribution.md        (統計サマリ)
        - chart_samples.html     (上位20件・近接統合・前後7日 plotly)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_CSV = REPO_ROOT / "data" / "BTCUSDT-5m-2021-04-01_03-31_1826d.csv"
OUTDIR = REPO_ROOT / "results" / "spike_analysis"  # main() で date_from に応じて上書き

BAR_MINUTES = 5
N_WINDOWS_HOURS = [1, 2, 4, 8, 12, 24]
THRESHOLD_PCTILES = [95.0, 99.0, 99.9]
END_RETRACE_PCTS = [10, 20, 30]
RETRACE_CHECKPOINTS_HOURS = [1, 4, 12, 24, 48, 72]
CLUSTER_PEAK_WINDOW_HOURS = 2
TOP_N_CHART_SAMPLES = 20

PCTILE_TO_LABEL = {95.0: "5pct", 99.0: "1pct", 99.9: "0_1pct"}


def hours_to_bars(h: float) -> int:
    return int(round(h * 60 / BAR_MINUTES))


def load_data(date_from: str | None = None) -> pd.DataFrame:
    print(f"[1/9] loading {INPUT_CSV.name} ...")
    df = pd.read_csv(INPUT_CSV)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    if date_from:
        cutoff = pd.Timestamp(date_from)
        before = len(df)
        df = df[df["timestamp"] >= cutoff].reset_index(drop=True)
        print(f"       --from {date_from}: filtered {before:,} -> {len(df):,} bars")
    df["year"] = df["timestamp"].dt.year
    print(f"       {len(df):,} bars, {df['timestamp'].min()} ~ {df['timestamp'].max()}")
    return df


def compute_returns(df: pd.DataFrame) -> dict[int, pd.Series]:
    print("[2/9] computing rolling returns for each N window ...")
    out = {}
    close = df["close"].values
    for n_h in N_WINDOWS_HOURS:
        n_bars = hours_to_bars(n_h)
        ret = np.full(len(df), np.nan)
        ret[n_bars:] = (close[n_bars:] - close[:-n_bars]) / close[:-n_bars]
        out[n_h] = pd.Series(ret, index=df.index)
        print(f"       N={n_h}h ({n_bars} bars): valid={(~np.isnan(ret)).sum():,}")
    return out


def compute_thresholds(df: pd.DataFrame, returns: dict[int, pd.Series]) -> dict:
    print("[3/9] computing percentile thresholds (yearly + all) ...")
    th = {"all": {}, "yearly": {}}
    for n_h, ret in returns.items():
        abs_ret = ret.abs().dropna()
        th["all"][n_h] = {p: float(np.percentile(abs_ret, p)) for p in THRESHOLD_PCTILES}
    th["yearly"] = {n_h: {} for n_h in N_WINDOWS_HOURS}
    years = sorted(df["year"].unique())
    for n_h, ret in returns.items():
        for y in years:
            mask = df["year"] == y
            abs_ret_y = ret[mask].abs().dropna()
            if len(abs_ret_y) == 0:
                continue
            th["yearly"][n_h][y] = {
                p: float(np.percentile(abs_ret_y, p)) for p in THRESHOLD_PCTILES
            }
    return th


def detect_events(
    df: pd.DataFrame,
    returns: dict[int, pd.Series],
    thresholds: dict,
) -> list[dict]:
    """
    各 (n_window, threshold_pct, scope, direction) で連続超過区間を1イベントに統合。
    """
    print("[4/9] detecting events ...")
    events = []
    eid = 0
    timestamps = df["timestamp"].values
    close = df["close"].values
    years = df["year"].values

    for n_h, ret in returns.items():
        n_bars = hours_to_bars(n_h)
        ret_arr = ret.values
        for pctile in THRESHOLD_PCTILES:
            for scope in ("all", "yearly"):
                if scope == "all":
                    th_value = thresholds["all"][n_h][pctile]
                    sign_arr = np.where(
                        np.abs(ret_arr) >= th_value, np.sign(ret_arr), 0
                    ).astype(int)
                    base_records = [
                        (sign_arr, th_value, np.nan)  # year=NaN
                    ]
                else:
                    base_records = []
                    for y in sorted(thresholds["yearly"][n_h].keys()):
                        th_value = thresholds["yearly"][n_h][y][pctile]
                        sub_sign = np.where(
                            (np.abs(ret_arr) >= th_value) & (years == y),
                            np.sign(ret_arr),
                            0,
                        ).astype(int)
                        base_records.append((sub_sign, th_value, y))

                for sign_arr, th_value, year_tag in base_records:
                    for direction_sign, direction_str in ((1, "up"), (-1, "down")):
                        flags = sign_arr == direction_sign
                        if not flags.any():
                            continue
                        # 連続区間検出
                        starts = []
                        ends = []
                        in_run = False
                        run_start = -1
                        for i, f in enumerate(flags):
                            if f and not in_run:
                                run_start = i
                                in_run = True
                            elif not f and in_run:
                                starts.append(run_start)
                                ends.append(i - 1)
                                in_run = False
                        if in_run:
                            starts.append(run_start)
                            ends.append(len(flags) - 1)

                        for s_idx, e_idx in zip(starts, ends):
                            seg = ret_arr[s_idx : e_idx + 1]
                            if direction_sign == 1:
                                local_peak = int(np.argmax(seg))
                            else:
                                local_peak = int(np.argmin(seg))
                            peak_idx = s_idx + local_peak
                            start_bar_idx = max(0, peak_idx - n_bars)

                            eid += 1
                            events.append(
                                {
                                    "event_id": f"evt_{eid:07d}",
                                    "n_window_hours": n_h,
                                    "threshold_pct": pctile,
                                    "threshold_value": th_value,
                                    "scope": scope,
                                    "year": year_tag,
                                    "direction": direction_str,
                                    "start_idx": start_bar_idx,
                                    "peak_idx": peak_idx,
                                    "start_time": timestamps[start_bar_idx],
                                    "peak_time": timestamps[peak_idx],
                                    "start_price": float(close[start_bar_idx]),
                                    "peak_price": float(close[peak_idx]),
                                    "magnitude_pct": float(
                                        (close[peak_idx] - close[start_bar_idx])
                                        / close[start_bar_idx]
                                    ),
                                }
                            )
    print(f"       {len(events):,} raw events")
    return events


def compute_post_peak_metrics(df: pd.DataFrame, events: list[dict]) -> pd.DataFrame:
    print("[5/9] computing post-peak metrics (end_M10/M20/M30, retrace, max_retrace) ...")
    timestamps = df["timestamp"].values
    close = df["close"].values
    n_bars = len(df)

    checkpoint_bars = {h: hours_to_bars(h) for h in RETRACE_CHECKPOINTS_HOURS}
    horizon_bars = hours_to_bars(72)

    rows = []
    for ev in events:
        peak_idx = ev["peak_idx"]
        start_price = ev["start_price"]
        peak_price = ev["peak_price"]
        diff = peak_price - start_price
        if diff == 0:
            continue
        direction = ev["direction"]

        end_times = {m: pd.NaT for m in END_RETRACE_PCTS}
        end_indices = {m: -1 for m in END_RETRACE_PCTS}

        # ピーク以降のバー範囲
        post_end = min(peak_idx + horizon_bars, n_bars - 1)
        post_slice = close[peak_idx : post_end + 1]
        # 戻し率（current が始点方向に戻るほど大）
        # direction=up: retrace = (peak - current) / (peak - start)  start<peak で diff>0
        # direction=down: retrace = (current - peak) / (start - peak) start>peak で diff<0
        if direction == "up":
            retrace_series = (peak_price - post_slice) / diff  # diff > 0
        else:
            retrace_series = (post_slice - peak_price) / (-diff)  # -diff > 0

        # end_M10/M20/M30
        for m in END_RETRACE_PCTS:
            tgt = m / 100.0
            hits = np.where(retrace_series >= tgt)[0]
            if len(hits) > 0:
                local = int(hits[0])
                end_indices[m] = peak_idx + local
                end_times[m] = timestamps[peak_idx + local]

        # retrace at checkpoints
        retrace_at = {}
        for h in RETRACE_CHECKPOINTS_HOURS:
            cp_idx = peak_idx + checkpoint_bars[h]
            if cp_idx >= n_bars:
                retrace_at[h] = np.nan
            else:
                local = checkpoint_bars[h]
                if local < len(retrace_series):
                    retrace_at[h] = float(retrace_series[local])
                else:
                    retrace_at[h] = np.nan

        # half retrace (50%)
        hits50 = np.where(retrace_series >= 0.5)[0]
        if len(hits50) > 0:
            half_retrace_time = timestamps[peak_idx + int(hits50[0])]
        else:
            half_retrace_time = pd.NaT

        # max retrace within 72h
        if len(retrace_series) > 0:
            max_local = int(np.argmax(retrace_series))
            max_retrace_pct = float(retrace_series[max_local])
            max_retrace_time = timestamps[peak_idx + max_local]
        else:
            max_retrace_pct = np.nan
            max_retrace_time = pd.NaT

        rows.append(
            {
                **{k: v for k, v in ev.items() if k not in ("start_idx", "peak_idx")},
                "end_time_M10": end_times[10],
                "end_time_M20": end_times[20],
                "end_time_M30": end_times[30],
                "retrace_1h": retrace_at[1],
                "retrace_4h": retrace_at[4],
                "retrace_12h": retrace_at[12],
                "retrace_24h": retrace_at[24],
                "retrace_48h": retrace_at[48],
                "retrace_72h": retrace_at[72],
                "half_retrace_time": half_retrace_time,
                "max_retrace_pct": max_retrace_pct,
                "max_retrace_time": max_retrace_time,
            }
        )
    out = pd.DataFrame(rows)
    print(f"       {len(out):,} events with metrics")
    return out


def assign_cluster_id(events_df: pd.DataFrame) -> pd.DataFrame:
    """同方向・ピーク時刻 ±2h を同一 cluster_id に割り当て。"""
    print("[6/9] assigning cluster_id (same direction, peak ±2h) ...")
    df = events_df.sort_values(["direction", "peak_time"]).reset_index(drop=True)
    cluster_ids = np.zeros(len(df), dtype=int)
    next_cid = 1
    last_peak_by_dir: dict[str, pd.Timestamp] = {}
    last_cid_by_dir: dict[str, int] = {}
    window = pd.Timedelta(hours=CLUSTER_PEAK_WINDOW_HOURS)
    for i, row in df.iterrows():
        d = row["direction"]
        pk = row["peak_time"]
        if d in last_peak_by_dir and (pk - last_peak_by_dir[d]) <= window:
            cluster_ids[i] = last_cid_by_dir[d]
        else:
            cluster_ids[i] = next_cid
            last_cid_by_dir[d] = next_cid
            next_cid += 1
        last_peak_by_dir[d] = pk
    df["cluster_id"] = cluster_ids
    return df


def assign_concurrent_flag(events_df: pd.DataFrame) -> pd.DataFrame:
    """ピーク後72h以内に他クラスタのイベントが発生したらTrue。"""
    print("[7/9] assigning concurrent_event_in_72h flag ...")
    df = events_df.sort_values("peak_time").reset_index(drop=True)
    peak_times = df["peak_time"].values
    cluster_ids = df["cluster_id"].values
    horizon = np.timedelta64(72, "h")
    flags = np.zeros(len(df), dtype=bool)
    n = len(df)
    for i in range(n):
        end_t = peak_times[i] + horizon
        my_cid = cluster_ids[i]
        # 後続イベントだけ見る（前方は概念的に含めない）
        j = i + 1
        while j < n and peak_times[j] <= end_t:
            if cluster_ids[j] != my_cid:
                flags[i] = True
                break
            j += 1
    df["concurrent_event_in_72h"] = flags
    return df


def lookahead_sanity_check(events_df: pd.DataFrame) -> None:
    """戻し率計算が peak_time 以降のみ参照していることを assert。"""
    bad = events_df[events_df["max_retrace_time"] < events_df["peak_time"]]
    assert len(bad) == 0, f"look-ahead violation: {len(bad)} rows have max_retrace_time before peak"
    bad2 = events_df.dropna(subset=["half_retrace_time"])
    bad2 = bad2[bad2["half_retrace_time"] < bad2["peak_time"]]
    assert len(bad2) == 0, f"look-ahead violation: {len(bad2)} rows have half_retrace_time before peak"


def write_outputs(events_df: pd.DataFrame, df: pd.DataFrame, thresholds: dict) -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)

    # 列順を整える
    columns = [
        "event_id",
        "cluster_id",
        "n_window_hours",
        "threshold_pct",
        "threshold_value",
        "scope",
        "year",
        "direction",
        "start_time",
        "peak_time",
        "end_time_M10",
        "end_time_M20",
        "end_time_M30",
        "start_price",
        "peak_price",
        "magnitude_pct",
        "retrace_1h",
        "retrace_4h",
        "retrace_12h",
        "retrace_24h",
        "retrace_48h",
        "retrace_72h",
        "half_retrace_time",
        "max_retrace_pct",
        "max_retrace_time",
        "concurrent_event_in_72h",
    ]
    events_df = events_df[columns].copy()

    print("[8/9] writing parquet + top1pct csv ...")
    parquet_path = OUTDIR / "events.parquet"
    events_df.to_parquet(parquet_path, index=False)
    print(f"       {parquet_path} ({parquet_path.stat().st_size / 1e6:.2f} MB)")

    top_csv = OUTDIR / "events_top1pct.csv"
    top_df = events_df[events_df["threshold_pct"] >= 99.0].copy()
    with open(top_csv, "w") as f:
        f.write(
            "# look-ahead 含む(全期間/年別パーセンタイル)。運用組み込み時は再設計が必要(L-128 参照)。\n"
        )
    top_df.to_csv(top_csv, mode="a", index=False)
    print(f"       {top_csv} ({top_csv.stat().st_size / 1e6:.2f} MB, {len(top_df):,} rows)")

    write_distribution_md(events_df, df, thresholds)

    # 2バリアント並行出力: strict (half<=12h) / medium (half<=24h)
    def _hours_to_half(d: pd.DataFrame) -> pd.Series:
        return (d["half_retrace_time"] - d["peak_time"]).dt.total_seconds() / 3600

    write_chart_samples_html(
        events_df, df, label="strict",
        filter_func=lambda d: d["half_retrace_time"].notna() & (_hours_to_half(d) <= 12),
    )
    write_chart_samples_html(
        events_df, df, label="medium",
        filter_func=lambda d: d["half_retrace_time"].notna() & (_hours_to_half(d) <= 24),
    )


def write_distribution_md(events_df: pd.DataFrame, df: pd.DataFrame, thresholds: dict) -> None:
    print("[8/9] writing distribution.md ...")
    md = []
    md.append("# 急騰急落イベント分布サマリ\n")
    md.append("> ⚠️ look-ahead 含む（全期間/年別パーセンタイルで閾値決定）。")
    md.append("> 運用組み込み時は再設計が必要（L-128 参照）。\n")
    md.append("## 1. 入力サマリ\n")
    md.append(f"- 入力: `{INPUT_CSV.name}`")
    md.append(f"- 期間: {df['timestamp'].min()} 〜 {df['timestamp'].max()}")
    md.append(f"- バー数: {len(df):,}")
    md.append(f"- 総イベント数: {len(events_df):,}\n")

    md.append("## 2. 閾値テーブル（|変動率| パーセンタイル）\n")
    md.append("### 2.1 全期間\n")
    md.append("| N窓 | 5%(95p) | 1%(99p) | 0.1%(99.9p) |")
    md.append("|-----|---------|---------|-------------|")
    for n_h in N_WINDOWS_HOURS:
        v = thresholds["all"][n_h]
        md.append(
            f"| {n_h}h | {v[95.0] * 100:.3f}% | {v[99.0] * 100:.3f}% | {v[99.9] * 100:.3f}% |"
        )
    md.append("")
    md.append("### 2.2 年別\n")
    years = sorted(thresholds["yearly"][N_WINDOWS_HOURS[0]].keys())
    md.append("| 年 | N窓 | 5% | 1% | 0.1% |")
    md.append("|----|-----|----|----|------|")
    for y in years:
        for n_h in N_WINDOWS_HOURS:
            v = thresholds["yearly"][n_h][y]
            md.append(
                f"| {y} | {n_h}h | {v[95.0] * 100:.3f}% | {v[99.0] * 100:.3f}% | {v[99.9] * 100:.3f}% |"
            )
    md.append("")

    md.append("## 3. イベント数（N窓 × 閾値 × 方向 × scope）\n")
    grp = (
        events_df.groupby(["n_window_hours", "threshold_pct", "scope", "direction"])
        .size()
        .reset_index(name="count")
    )
    md.append("| N窓 | 閾値 | scope | direction | 件数 |")
    md.append("|-----|------|-------|-----------|------|")
    for _, r in grp.iterrows():
        md.append(
            f"| {r['n_window_hours']}h | {r['threshold_pct']}p | {r['scope']} | {r['direction']} | {r['count']:,} |"
        )
    md.append("")

    md.append("## 4. 規模分布（|magnitude_pct|・全イベント）\n")
    mag = events_df["magnitude_pct"].abs() * 100
    md.append("| 指標 | 値 |")
    md.append("|------|------|")
    md.append(f"| 件数 | {len(mag):,} |")
    md.append(f"| 平均 | {mag.mean():.3f}% |")
    md.append(f"| median | {mag.median():.3f}% |")
    md.append(f"| p25 | {mag.quantile(0.25):.3f}% |")
    md.append(f"| p75 | {mag.quantile(0.75):.3f}% |")
    md.append(f"| p95 | {mag.quantile(0.95):.3f}% |")
    md.append(f"| max | {mag.max():.3f}% |")
    md.append("")

    md.append("## 5. 戻し率分布（M=10基準・各チェックポイント）\n")
    md.append("| 刻み | median | p25 | p75 | NaN比率 |")
    md.append("|------|--------|-----|-----|---------|")
    for h in RETRACE_CHECKPOINTS_HOURS:
        col = f"retrace_{h}h"
        s = events_df[col]
        nan_ratio = s.isna().mean() * 100
        s2 = s.dropna()
        md.append(
            f"| {h}h | {s2.median():.3f} | {s2.quantile(0.25):.3f} | {s2.quantile(0.75):.3f} | {nan_ratio:.2f}% |"
        )
    md.append("")

    md.append("## 6. half_retrace（50%）到達状況\n")
    reached = events_df["half_retrace_time"].notna()
    md.append(f"- 到達件数: {reached.sum():,} / {len(events_df):,} ({reached.mean() * 100:.2f}%)")
    if reached.any():
        td = (events_df.loc[reached, "half_retrace_time"] - events_df.loc[reached, "peak_time"])
        td_h = td.dt.total_seconds() / 3600
        md.append(f"- 到達時刻分布（peak からの時間, h）: median={td_h.median():.2f}h / p25={td_h.quantile(0.25):.2f}h / p75={td_h.quantile(0.75):.2f}h")
    md.append("")

    md.append("## 7. 年別差分\n")
    years_in_events = sorted(events_df["peak_time"].dt.year.unique().tolist())
    md.append("| 年 | 件数 | 規模 median(%) |")
    md.append("|----|------|----------------|")
    for y in years_in_events:
        sub = events_df[events_df["peak_time"].dt.year == y]
        md.append(f"| {y} | {len(sub):,} | {sub['magnitude_pct'].abs().median() * 100:.3f}% |")
    md.append("")

    md.append("## 8. concurrent_event_in_72h 比率\n")
    md.append(f"- True 比率: {events_df['concurrent_event_in_72h'].mean() * 100:.2f}%")
    md.append("")

    md_path = OUTDIR / "distribution.md"
    md_path.write_text("\n".join(md))
    print(f"       {md_path}")


def write_chart_samples_html(
    events_df: pd.DataFrame,
    df: pd.DataFrame,
    label: str = "all",
    filter_func=None,
) -> None:
    """各イベントを 2 行表示: 上=±7日 close 線（広域）/ 下=±12時間 OHLC ローソク足（ズーム）。
    filter_func: events_df を受けて bool Series を返す関数。None なら無フィルタ。"""
    out_name = f"chart_samples_{label}.html"
    print(f"[9/9] writing {out_name} (top {TOP_N_CHART_SAMPLES} events, filter={label}) ...")
    src = events_df if filter_func is None else events_df[filter_func(events_df)]
    if len(src) == 0:
        print(f"       skip: no events match filter '{label}'")
        return
    df_sorted = src.sort_values("magnitude_pct", key=lambda s: s.abs(), ascending=False)
    df_sorted = df_sorted.drop_duplicates(subset=["cluster_id"], keep="first")
    top = df_sorted.head(TOP_N_CHART_SAMPLES).reset_index(drop=True)

    timestamps = df["timestamp"]
    close = df["close"]
    open_ = df["open"]
    high = df["high"]
    low = df["low"]

    # 各イベント 2 行 (広域 / ズーム) → 合計 2N 行
    n_rows = TOP_N_CHART_SAMPLES * 2
    subplot_titles = []
    for i, row in top.iterrows():
        head = (
            f"{i + 1}. {row['direction']} {row['magnitude_pct'] * 100:+.2f}% / "
            f"N={row['n_window_hours']}h / th={row['threshold_pct']}p / peak={row['peak_time']} "
            f"/ retrace_24h={row['retrace_24h']:.2f}"
        )
        subplot_titles.append(head + "  [±7d 広域]")
        subplot_titles.append("  [±12h ズーム OHLC]")

    # row heights: 広域 0.4 / ズーム 0.6
    row_heights = []
    for _ in range(TOP_N_CHART_SAMPLES):
        row_heights.append(0.4)
        row_heights.append(0.6)

    fig = make_subplots(
        rows=n_rows, cols=1,
        subplot_titles=subplot_titles,
        vertical_spacing=0.008,
        row_heights=row_heights,
    )

    seven_days = pd.Timedelta(days=7)
    twelve_hours = pd.Timedelta(hours=12)

    for i, row in top.iterrows():
        wide_row = i * 2 + 1   # 広域
        zoom_row = i * 2 + 2   # ズーム
        peak_t = row["peak_time"]

        # 広域: ±7日 close 線
        wide_lo = peak_t - seven_days
        wide_hi = peak_t + seven_days
        wmask = (timestamps >= wide_lo) & (timestamps <= wide_hi)
        fig.add_trace(
            go.Scatter(
                x=timestamps[wmask], y=close[wmask],
                mode="lines",
                line=dict(width=1, color="#888"),
                showlegend=False,
            ),
            row=wide_row, col=1,
        )
        # 広域に peak / start を marker
        fig.add_trace(
            go.Scatter(
                x=[row["start_time"], row["peak_time"]],
                y=[row["start_price"], row["peak_price"]],
                mode="markers",
                marker=dict(color=["green", "red"], size=8, symbol=["circle", "diamond"]),
                showlegend=False,
            ),
            row=wide_row, col=1,
        )
        # 広域にズーム範囲を vrect で示す（薄黄色）
        zoom_lo = peak_t - twelve_hours
        zoom_hi = peak_t + twelve_hours
        fig.add_vrect(
            x0=zoom_lo, x1=zoom_hi,
            fillcolor="yellow", opacity=0.15, line_width=0,
            row=wide_row, col=1,
        )

        # ズーム: ±12時間 OHLC
        zmask = (timestamps >= zoom_lo) & (timestamps <= zoom_hi)
        fig.add_trace(
            go.Candlestick(
                x=timestamps[zmask],
                open=open_[zmask], high=high[zmask],
                low=low[zmask], close=close[zmask],
                increasing_line_color="#26a69a",
                decreasing_line_color="#ef5350",
                showlegend=False,
            ),
            row=zoom_row, col=1,
        )
        # ズームにマーカー（start/peak/end_M10/M20/M30/half50）
        markers = [
            (row["start_time"], row["start_price"], "start", "green"),
            (row["peak_time"], row["peak_price"], "peak", "red"),
        ]
        for col_name, color in (
            ("end_time_M10", "orange"),
            ("end_time_M20", "purple"),
            ("end_time_M30", "brown"),
        ):
            if pd.notna(row[col_name]):
                t = row[col_name]
                if zoom_lo <= t <= zoom_hi:
                    price_idx = (timestamps - t).abs().idxmin()
                    markers.append((t, close.iloc[price_idx], col_name, color))
        if pd.notna(row["half_retrace_time"]):
            t = row["half_retrace_time"]
            if zoom_lo <= t <= zoom_hi:
                price_idx = (timestamps - t).abs().idxmin()
                markers.append((t, close.iloc[price_idx], "half50", "blue"))
        for t, p, mlabel, color in markers:
            fig.add_trace(
                go.Scatter(
                    x=[t], y=[p],
                    mode="markers+text",
                    marker=dict(color=color, size=12, symbol="x"),
                    text=[mlabel], textposition="top center", showlegend=False,
                    textfont=dict(size=10, color=color),
                ),
                row=zoom_row, col=1,
            )

        # ズーム軸: range slider 無効化（plotly Candlestick 既定で出る）
        fig.update_xaxes(rangeslider_visible=False, row=zoom_row, col=1)

    # 高さ: 広域 200 + ズーム 350 = 550px / event
    fig.update_layout(
        height=550 * TOP_N_CHART_SAMPLES,
        title_text=(
            f"Spike Events ({label}): Top {TOP_N_CHART_SAMPLES} "
            f"(±7d wide / ±12h OHLC zoom, cluster deduped)"
        ),
        margin=dict(l=40, r=20, t=60, b=20),
    )
    out_html = OUTDIR / out_name
    fig.write_html(out_html, include_plotlyjs="cdn", full_html=True)
    print(f"       {out_html} ({out_html.stat().st_size / 1e6:.2f} MB)")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="急騰急落イベント抽出")
    p.add_argument(
        "--from", dest="date_from", default=None,
        help="YYYY-MM-DD 以降のデータで抽出（既定: 全期間）",
    )
    p.add_argument(
        "--reuse", action="store_true",
        help="既存 events.parquet を再利用して chart のみ再生成",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    # OUTDIR を date_from に応じて切替（既存全期間版と並存させる）
    global OUTDIR
    if args.date_from:
        suffix = args.date_from.replace("-", "")[:6]  # 例: 202301
        OUTDIR = REPO_ROOT / "results" / f"spike_analysis_from{suffix}"
    print(f"[OUTDIR] {OUTDIR}")

    df = load_data(args.date_from)
    parquet_path = OUTDIR / "events.parquet"
    reuse = args.reuse and parquet_path.exists()
    if reuse:
        print(f"[reuse] loading existing {parquet_path.name} (skipping detection)")
        events_df = pd.read_parquet(parquet_path)
        thresholds = compute_thresholds(df, compute_returns(df))
        # chart 再生成のみ
        OUTDIR.mkdir(parents=True, exist_ok=True)

        def _hours_to_half(d: pd.DataFrame) -> pd.Series:
            return (d["half_retrace_time"] - d["peak_time"]).dt.total_seconds() / 3600

        write_chart_samples_html(
            events_df, df, label="strict",
            filter_func=lambda d: d["half_retrace_time"].notna() & (_hours_to_half(d) <= 12),
        )
        write_chart_samples_html(
            events_df, df, label="medium",
            filter_func=lambda d: d["half_retrace_time"].notna() & (_hours_to_half(d) <= 24),
        )
        print("DONE (reuse mode).")
        return
    returns = compute_returns(df)
    thresholds = compute_thresholds(df, returns)
    raw_events = detect_events(df, returns, thresholds)
    events_df = compute_post_peak_metrics(df, raw_events)
    events_df = assign_cluster_id(events_df)
    events_df = assign_concurrent_flag(events_df)
    lookahead_sanity_check(events_df)
    write_outputs(events_df, df, thresholds)
    print("DONE.")


if __name__ == "__main__":
    main()
