"""regime_label_run_length.py — 既存 regime ラベルの連続区間長分布

問い: regime ラベルの「持続」は分単位か時間単位か日単位か
目的: 単一ラベル方式の限界（Frame 1）を判定する材料

ラベル元 (2 系統並列・絞り込まない):
  A. まこさん肉眼ラベル 4h
     入力: data/regime_samples_4h.csv + 同_2022/2023/2024.csv (合計 4 ファイル)
     非空ラベル: 4,745 バー (2022-2025)
  B. v14 自動ラベル 1h (5m 単位は未生成)
     入力: dashboard/regime_prototype/predictions_v14_1h.json (43,812 行 / 5 年)

run-length 定義 (既存ラベルそのまま・独自定義追加なし):
  - 時系列順で連続する同ラベルバーを 1 run とする
  - タイムスタンプ間隔がラベル粒度 (4h or 1h) と一致する場合のみ run 連続
  - 未ラベルバー / 時間飛び は run 区切り

集計次元 (絞り込まない):
  - 全体 + label 別 (uptrend / downtrend / range)
  - median / P25 / P75 / P90 / P99 / max / mean / count (時間単位)

出力:
  - results/regime_research/regime_label_run_length.md
  - results/regime_research/regime_label_run_length.csv (機械可読)
  - dashboard/data/regime_label_run_length.json (タブ⑬ 用)
"""

import json
from pathlib import Path
import pandas as pd
import numpy as np

BASE = Path(__file__).parent.parent.parent
DATA_DIR = BASE / "data"
RESULTS_DIR = BASE / "results" / "regime_research"
DASH_DATA_DIR = BASE / "dashboard" / "data"

OUT_MD = RESULTS_DIR / "regime_label_run_length.md"
OUT_CSV = RESULTS_DIR / "regime_label_run_length.csv"
OUT_DASH_JSON = DASH_DATA_DIR / "regime_label_run_length.json"

LABEL_FILES_4H = [
    DATA_DIR / "regime_samples_4h_2022.csv",
    DATA_DIR / "regime_samples_4h_2023.csv",
    DATA_DIR / "regime_samples_4h_2024.csv",
    DATA_DIR / "regime_samples_4h.csv",  # 2025
]
V14_JSON = BASE / "dashboard" / "regime_prototype" / "predictions_v14_1h.json"


def load_labels_4h() -> pd.DataFrame:
    dfs = []
    for f in LABEL_FILES_4H:
        df = pd.read_csv(f)
        df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True)
        dfs.append(df)
    full = pd.concat(dfs, ignore_index=True).sort_values("timestamp_utc").reset_index(drop=True)
    full["label"] = full["label"].fillna("")
    return full


def load_labels_v14() -> pd.DataFrame:
    with open(V14_JSON) as f:
        data = json.load(f)
    rows = data["rows"]
    df = pd.DataFrame(rows, columns=["ts_ms", "price", "label", "override"])
    df["timestamp_utc"] = pd.to_datetime(df["ts_ms"], unit="ms", utc=True)
    df["label"] = df["label"].fillna("")
    df = df.sort_values("timestamp_utc").reset_index(drop=True)
    return df[["timestamp_utc", "label"]]


def compute_runs(df: pd.DataFrame, granularity_hours: float) -> pd.DataFrame:
    """連続同ラベル区間を抽出。
    - 空ラベルは run 区切り
    - タイムスタンプ間隔が granularity と一致しない場合も run 区切り (時間飛び)
    """
    if len(df) == 0:
        return pd.DataFrame(columns=["start_ts", "end_ts", "label", "n_bars", "duration_h"])

    delta_expected = pd.Timedelta(hours=granularity_hours)
    delta_tolerance = pd.Timedelta(seconds=1)

    runs = []
    cur_label = df["label"].iloc[0]
    cur_start = df["timestamp_utc"].iloc[0]
    cur_count = 1
    prev_ts = cur_start

    for i in range(1, len(df)):
        ts = df["timestamp_utc"].iloc[i]
        lab = df["label"].iloc[i]
        gap = ts - prev_ts
        contiguous = abs(gap - delta_expected) <= delta_tolerance

        if (lab == cur_label) and contiguous and (cur_label != ""):
            cur_count += 1
        else:
            if cur_label != "":
                runs.append({
                    "start_ts": cur_start,
                    "end_ts": prev_ts,
                    "label": cur_label,
                    "n_bars": cur_count,
                    "duration_h": cur_count * granularity_hours,
                })
            cur_label = lab
            cur_start = ts
            cur_count = 1
        prev_ts = ts

    # 末尾
    if cur_label != "":
        runs.append({
            "start_ts": cur_start,
            "end_ts": prev_ts,
            "label": cur_label,
            "n_bars": cur_count,
            "duration_h": cur_count * granularity_hours,
        })

    return pd.DataFrame(runs)


def stats_for_runs(runs: pd.DataFrame) -> dict:
    if len(runs) == 0:
        return {"n": 0}
    d = runs["duration_h"]
    return {
        "n": len(runs),
        "median_h": float(d.median()),
        "mean_h": float(d.mean()),
        "p25_h": float(d.quantile(0.25)),
        "p75_h": float(d.quantile(0.75)),
        "p90_h": float(d.quantile(0.90)),
        "p99_h": float(d.quantile(0.99)),
        "max_h": float(d.max()),
        "min_h": float(d.min()),
    }


def histogram_buckets(runs: pd.DataFrame) -> list:
    """ダッシュボード用ヒストグラム (時間単位 bin)."""
    if len(runs) == 0:
        return []
    bins = [0, 4, 8, 12, 24, 48, 72, 168, 336, 720, 999999]  # 4h/8h/12h/1d/2d/3d/1w/2w/1M/それ以上
    labels = ["≤4h", "4-8h", "8-12h", "12-24h", "1-2d", "2-3d", "3-7d", "1-2w", "2w-1M", ">1M"]
    cuts = pd.cut(runs["duration_h"], bins=bins, labels=labels, right=True)
    counts = cuts.value_counts().reindex(labels, fill_value=0)
    return [{"bucket": lab, "count": int(counts.get(lab, 0))} for lab in labels]


def fmt_h(x):
    if pd.isna(x):
        return "—"
    if x >= 24:
        return f"{x:.1f}h ({x/24:.1f}d)"
    return f"{x:.1f}h"


def main():
    print("[load] 4h teacher labels")
    df_4h = load_labels_4h()
    n_4h_total = len(df_4h)
    n_4h_labeled = (df_4h["label"] != "").sum()
    print(f"  total bars: {n_4h_total} / labeled: {n_4h_labeled}")

    print("[load] v14 1h auto labels")
    df_v14 = load_labels_v14()
    n_v14_total = len(df_v14)
    n_v14_labeled = (df_v14["label"] != "").sum()
    print(f"  total bars: {n_v14_total} / labeled: {n_v14_labeled}")
    print(f"  v14 unique labels: {sorted(df_v14['label'].unique())}")

    print("[compute] runs 4h")
    runs_4h = compute_runs(df_4h, granularity_hours=4.0)
    print(f"  total runs: {len(runs_4h)}")

    print("[compute] runs v14 1h")
    runs_v14 = compute_runs(df_v14, granularity_hours=1.0)
    print(f"  total runs: {len(runs_v14)}")

    LABELS_OF_INTEREST = ["uptrend", "downtrend", "range"]

    md = []
    md.append("# regime ラベル 連続区間長 (run-length) 分布\n")
    md.append("- 集計対象 A: まこさん肉眼ラベル 4h (2022-2025)")
    md.append(f"  - 入力: 4 ファイル (regime_samples_4h_2022/2023/2024.csv + regime_samples_4h.csv)")
    md.append(f"  - 全 4h バー: {n_4h_total} / ラベル付き: {n_4h_labeled}")
    md.append("- 集計対象 B: v14 自動ラベル 1h")
    md.append(f"  - 入力: dashboard/regime_prototype/predictions_v14_1h.json")
    md.append(f"  - 全 1h バー: {n_v14_total} / ラベル付き: {n_v14_labeled}")
    md.append("- run 定義: 時系列順で連続する同ラベル + timestamp 間隔=粒度 (4h or 1h)")
    md.append("- 空ラベル / 時間飛び は run 区切り\n")

    csv_rows = []

    # === 4h ===
    md.append("## A. 4h 教師ラベル run-length")
    md.append("")
    md.append("| ラベル | run 数 | median | mean | P25 | P75 | P90 | P99 | max | min |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")

    s = stats_for_runs(runs_4h)
    md.append(f"| **全体** | {s['n']} | {fmt_h(s.get('median_h'))} | {fmt_h(s.get('mean_h'))} | {fmt_h(s.get('p25_h'))} | {fmt_h(s.get('p75_h'))} | {fmt_h(s.get('p90_h'))} | {fmt_h(s.get('p99_h'))} | {fmt_h(s.get('max_h'))} | {fmt_h(s.get('min_h'))} |")
    csv_rows.append({"source": "4h_teacher", "label": "ALL", **s})

    for lab in LABELS_OF_INTEREST:
        sub = runs_4h[runs_4h["label"] == lab]
        s = stats_for_runs(sub)
        if s["n"] == 0:
            md.append(f"| {lab} | 0 | — | — | — | — | — | — | — | — |")
        else:
            md.append(f"| {lab} | {s['n']} | {fmt_h(s.get('median_h'))} | {fmt_h(s.get('mean_h'))} | {fmt_h(s.get('p25_h'))} | {fmt_h(s.get('p75_h'))} | {fmt_h(s.get('p90_h'))} | {fmt_h(s.get('p99_h'))} | {fmt_h(s.get('max_h'))} | {fmt_h(s.get('min_h'))} |")
        csv_rows.append({"source": "4h_teacher", "label": lab, **s})
    md.append("")

    # === v14 ===
    md.append("## B. v14 1h 自動ラベル run-length")
    md.append("")
    md.append("| ラベル | run 数 | median | mean | P25 | P75 | P90 | P99 | max | min |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")

    s = stats_for_runs(runs_v14)
    md.append(f"| **全体** | {s['n']} | {fmt_h(s.get('median_h'))} | {fmt_h(s.get('mean_h'))} | {fmt_h(s.get('p25_h'))} | {fmt_h(s.get('p75_h'))} | {fmt_h(s.get('p90_h'))} | {fmt_h(s.get('p99_h'))} | {fmt_h(s.get('max_h'))} | {fmt_h(s.get('min_h'))} |")
    csv_rows.append({"source": "v14_auto_1h", "label": "ALL", **s})

    for lab in LABELS_OF_INTEREST:
        sub = runs_v14[runs_v14["label"] == lab]
        s = stats_for_runs(sub)
        if s["n"] == 0:
            md.append(f"| {lab} | 0 | — | — | — | — | — | — | — | — |")
        else:
            md.append(f"| {lab} | {s['n']} | {fmt_h(s.get('median_h'))} | {fmt_h(s.get('mean_h'))} | {fmt_h(s.get('p25_h'))} | {fmt_h(s.get('p75_h'))} | {fmt_h(s.get('p90_h'))} | {fmt_h(s.get('p99_h'))} | {fmt_h(s.get('max_h'))} | {fmt_h(s.get('min_h'))} |")
        csv_rows.append({"source": "v14_auto_1h", "label": lab, **s})
    md.append("")

    # ヒストグラム (md にも併記)
    md.append("## ヒストグラム bin (時間)")
    md.append("")
    md.append("| bin | 4h 全体 | 4h up | 4h dn | 4h rg | v14 全体 | v14 up | v14 dn | v14 rg |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")

    bins = [0, 4, 8, 12, 24, 48, 72, 168, 336, 720, 999999]
    bin_labels = ["≤4h", "4-8h", "8-12h", "12-24h", "1-2d", "2-3d", "3-7d", "1-2w", "2w-1M", ">1M"]

    def hist(runs, bin_filter=None):
        if bin_filter is not None:
            runs = runs[runs["label"] == bin_filter]
        if len(runs) == 0:
            return {l: 0 for l in bin_labels}
        cuts = pd.cut(runs["duration_h"], bins=bins, labels=bin_labels, right=True)
        return {l: int((cuts == l).sum()) for l in bin_labels}

    h_4h_all = hist(runs_4h)
    h_4h_up = hist(runs_4h, "uptrend")
    h_4h_dn = hist(runs_4h, "downtrend")
    h_4h_rg = hist(runs_4h, "range")
    h_v14_all = hist(runs_v14)
    h_v14_up = hist(runs_v14, "uptrend")
    h_v14_dn = hist(runs_v14, "downtrend")
    h_v14_rg = hist(runs_v14, "range")

    for lab in bin_labels:
        md.append(f"| {lab} | {h_4h_all[lab]} | {h_4h_up[lab]} | {h_4h_dn[lab]} | {h_4h_rg[lab]} | {h_v14_all[lab]} | {h_v14_up[lab]} | {h_v14_dn[lab]} | {h_v14_rg[lab]} |")
    md.append("")

    # 判定指標
    s_4h = stats_for_runs(runs_4h)
    s_v14 = stats_for_runs(runs_v14)
    md.append("## 判定指標 (Frame 1: 単一ラベル方式の限界)")
    md.append("")
    md.append(f"- 4h 教師 全体 median: **{fmt_h(s_4h.get('median_h'))}**")
    md.append(f"- v14 自動 全体 median: **{fmt_h(s_v14.get('median_h'))}**")
    md.append("- 判定:")
    md.append("  - median が時間〜日オーダー → Frame 1 撤回 (単一ラベル方式は妥当)")
    md.append("  - median が分〜時間未満オーダー → Frame 1 有効 (限界論復活)")
    md.append("- まこさん視認: タブ⑬ ヒストグラムで「短い区間が支配的か / 長い区間が支配的か」最終確認")
    md.append("")

    # 出力
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    DASH_DATA_DIR.mkdir(parents=True, exist_ok=True)

    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print(f"[done] md: {OUT_MD}")

    pd.DataFrame(csv_rows).to_csv(OUT_CSV, index=False)
    print(f"[done] csv: {OUT_CSV}")

    # ダッシュボード用 JSON
    dash_data = {
        "version": "regime_label_run_length_v1",
        "source_a": {
            "name": "4h 教師ラベル (まこさん肉眼)",
            "input_files": [str(f.relative_to(BASE)) for f in LABEL_FILES_4H],
            "n_bars_total": int(n_4h_total),
            "n_bars_labeled": int(n_4h_labeled),
            "stats": {
                "ALL": stats_for_runs(runs_4h),
                "uptrend": stats_for_runs(runs_4h[runs_4h["label"] == "uptrend"]),
                "downtrend": stats_for_runs(runs_4h[runs_4h["label"] == "downtrend"]),
                "range": stats_for_runs(runs_4h[runs_4h["label"] == "range"]),
            },
            "histogram": {
                "bin_labels": bin_labels,
                "ALL": [h_4h_all[l] for l in bin_labels],
                "uptrend": [h_4h_up[l] for l in bin_labels],
                "downtrend": [h_4h_dn[l] for l in bin_labels],
                "range": [h_4h_rg[l] for l in bin_labels],
            },
        },
        "source_b": {
            "name": "v14 自動ラベル 1h",
            "input_file": str(V14_JSON.relative_to(BASE)),
            "n_bars_total": int(n_v14_total),
            "n_bars_labeled": int(n_v14_labeled),
            "stats": {
                "ALL": stats_for_runs(runs_v14),
                "uptrend": stats_for_runs(runs_v14[runs_v14["label"] == "uptrend"]),
                "downtrend": stats_for_runs(runs_v14[runs_v14["label"] == "downtrend"]),
                "range": stats_for_runs(runs_v14[runs_v14["label"] == "range"]),
            },
            "histogram": {
                "bin_labels": bin_labels,
                "ALL": [h_v14_all[l] for l in bin_labels],
                "uptrend": [h_v14_up[l] for l in bin_labels],
                "downtrend": [h_v14_dn[l] for l in bin_labels],
                "range": [h_v14_rg[l] for l in bin_labels],
            },
        },
    }
    with open(OUT_DASH_JSON, "w") as f:
        json.dump(dash_data, f, indent=2, ensure_ascii=False)
    print(f"[done] dashboard json: {OUT_DASH_JSON}")

    print()
    print(f"[summary] 4h teacher median: {fmt_h(s_4h.get('median_h'))} / mean: {fmt_h(s_4h.get('mean_h'))} / runs: {s_4h['n']}")
    print(f"[summary] v14 1h auto  median: {fmt_h(s_v14.get('median_h'))} / mean: {fmt_h(s_v14.get('mean_h'))} / runs: {s_v14['n']}")


if __name__ == "__main__":
    main()
