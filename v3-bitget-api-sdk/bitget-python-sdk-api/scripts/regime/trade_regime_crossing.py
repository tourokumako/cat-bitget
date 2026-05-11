"""trade_regime_crossing.py — trade と 4h 教師 regime 境界の整合性検証

問い: trade の保持時間中に 4h 教師ラベルの run 切替点 (boundary) が含まれるか
目的: 「regime 先行 → Priority 最適化」作戦が時間軸的に成立するかを定量化

入力:
  - results/replay/replay_BTCUSDT-5m-2025-04-01_03-31_365d.csv (1,157 trade)
  - data/regime_samples_4h*.csv (まこさん肉眼 4h 教師ラベル・4 ファイル)

境界 (boundary) 定義 (既存 4h 教師ラベルのみ):
  - 連続する 2 つの labeled 4h バーで label が変わる地点
  - timestamp 間隔 = 4h であること (時間飛びは boundary としない)
  - boundary timestamp = 後者のバー timestamp

trade 分類:
  - LABELED: trade の [entry_time, exit_time] 周辺に labeled 4h バーが存在
    - CROSSING: trade 区間内 (entry_time, exit_time] に boundary が 1 個以上
    - NON_CROSSING: boundary が 0 個
  - UNLABELED: trade 周辺に labeled 4h バーなし (判定不能)

集計:
  - 跨ぎ率 (全体 / Priority 別 / regime 別 / side 別)
  - net_usd 分布 (crossing vs non-crossing)
  - hold_min × crossing 確率

出力:
  - results/regime_research/trade_regime_crossing.md
  - results/regime_research/trade_regime_crossing.csv (機械可読・per-trade)
  - dashboard/data/trade_regime_crossing.json (タブ⑭ 用)

判断分岐 (まこさん指示):
  - 跨がない確率 90%+ → 作戦継続
  - 70-90%   → 部分問題
  - 50% 以下 → 根本見直し
"""

import json
from pathlib import Path
import pandas as pd
import numpy as np

BASE = Path(__file__).parent.parent.parent
DATA_DIR = BASE / "data"
RESULTS_DIR = BASE / "results" / "regime_research"
DASH_DATA_DIR = BASE / "dashboard" / "data"

REPLAY_CSV = BASE / "results/replay/replay_BTCUSDT-5m-2025-04-01_03-31_365d.csv"
LABEL_FILES_4H = [
    DATA_DIR / "regime_samples_4h_2022.csv",
    DATA_DIR / "regime_samples_4h_2023.csv",
    DATA_DIR / "regime_samples_4h_2024.csv",
    DATA_DIR / "regime_samples_4h.csv",  # 2025
]

OUT_MD = RESULTS_DIR / "trade_regime_crossing.md"
OUT_CSV = RESULTS_DIR / "trade_regime_crossing.csv"
OUT_DASH_JSON = DASH_DATA_DIR / "trade_regime_crossing.json"


def load_4h_labels() -> pd.DataFrame:
    dfs = []
    for f in LABEL_FILES_4H:
        d = pd.read_csv(f)
        d["timestamp_utc"] = pd.to_datetime(d["timestamp_utc"], utc=True)
        dfs.append(d)
    full = pd.concat(dfs, ignore_index=True).sort_values("timestamp_utc").reset_index(drop=True)
    full["label"] = full["label"].fillna("")
    return full


def compute_boundary_ts(labels_4h: pd.DataFrame) -> pd.Series:
    """連続 labeled 4h バーで label が変わる地点の timestamp 列を返す。"""
    df = labels_4h[labels_4h["label"] != ""].reset_index(drop=True)
    delta_expected = pd.Timedelta(hours=4)
    tol = pd.Timedelta(seconds=1)
    ts = []
    for i in range(1, len(df)):
        gap = df["timestamp_utc"].iloc[i] - df["timestamp_utc"].iloc[i - 1]
        if abs(gap - delta_expected) <= tol and df["label"].iloc[i] != df["label"].iloc[i - 1]:
            ts.append(df["timestamp_utc"].iloc[i])
    return pd.Series(ts).sort_values().reset_index(drop=True)


def labeled_bar_set(labels_4h: pd.DataFrame) -> pd.Series:
    """labeled 4h バーの timestamp 列。"""
    return labels_4h.loc[labels_4h["label"] != "", "timestamp_utc"].reset_index(drop=True)


def classify_trades(trades: pd.DataFrame, boundaries: pd.Series, labels_4h: pd.DataFrame,
                    max_label_distance_h: float = 24.0) -> pd.DataFrame:
    """各 trade を 2 種類の判定で分類:

    STRICT: trade 区間 (entry, exit] に boundary が含まれるか
      - LABELED:CROSSING / LABELED:NON_CROSSING / UNLABELED
      - has_label_nearby: [entry - 4h, exit + 4h] に labeled バー有無

    IMPLIED: trade entry 直前の labeled バーと exit 直後の labeled バーの label 比較
      - 両側とも max_label_distance_h 以内に labeled バーが存在することを条件
      - IMPLIED_CROSSING / IMPLIED_NON_CROSSING / IMPLIED_UNDETERMINED
    """
    trades = trades.copy()
    trades["entry_ts"] = pd.to_datetime(trades["entry_time"], utc=True)
    trades["exit_ts"] = pd.to_datetime(trades["exit_time"], utc=True)

    b_arr = boundaries.values
    labeled = labels_4h[labels_4h["label"] != ""].reset_index(drop=True)
    lb_ts_arr = labeled["timestamp_utc"].values
    lb_label_arr = labeled["label"].values

    boundary_count = np.zeros(len(trades), dtype=int)
    has_label_nearby = np.zeros(len(trades), dtype=bool)
    label_before = np.array([""] * len(trades), dtype=object)
    label_after = np.array([""] * len(trades), dtype=object)
    delta4 = pd.Timedelta(hours=4)
    delta_max = pd.Timedelta(hours=max_label_distance_h)

    for i, (e, x) in enumerate(zip(trades["entry_ts"].values, trades["exit_ts"].values)):
        # STRICT 用
        boundary_count[i] = int(((b_arr > e) & (b_arr <= x)).sum())
        has_label_nearby[i] = bool(((lb_ts_arr >= (e - delta4)) & (lb_ts_arr <= (x + delta4))).any())

        # IMPLIED 用: entry 直前と exit 直後の labeled バー
        before_mask = (lb_ts_arr <= e) & (lb_ts_arr >= (e - delta_max))
        after_mask = (lb_ts_arr >= x) & (lb_ts_arr <= (x + delta_max))
        if before_mask.any():
            idx = np.where(before_mask)[0][-1]  # 最も entry に近い (最後)
            label_before[i] = lb_label_arr[idx]
        if after_mask.any():
            idx = np.where(after_mask)[0][0]  # 最も exit に近い (最初)
            label_after[i] = lb_label_arr[idx]

    trades["boundary_count"] = boundary_count
    trades["has_label_nearby"] = has_label_nearby
    trades["label_before"] = label_before
    trades["label_after"] = label_after

    def strict(row):
        if not row["has_label_nearby"]:
            return "UNLABELED"
        return "CROSSING" if row["boundary_count"] >= 1 else "NON_CROSSING"

    def implied(row):
        if row["label_before"] == "" or row["label_after"] == "":
            return "IMPLIED_UNDETERMINED"
        return "IMPLIED_CROSSING" if row["label_before"] != row["label_after"] else "IMPLIED_NON_CROSSING"

    trades["crossing_status"] = trades.apply(strict, axis=1)
    trades["implied_status"] = trades.apply(implied, axis=1)
    return trades


def ratio_table(trades: pd.DataFrame, by: str, status_col: str = "implied_status") -> pd.DataFrame:
    """by 別の crossing / non_crossing / undetermined 件数と比率 (IMPLIED 基準)。"""
    if status_col == "crossing_status":
        cross_val, non_val, undet_val = "CROSSING", "NON_CROSSING", "UNLABELED"
    else:
        cross_val, non_val, undet_val = "IMPLIED_CROSSING", "IMPLIED_NON_CROSSING", "IMPLIED_UNDETERMINED"
    rows = []
    for key, sub in trades.groupby(by, dropna=False):
        n = len(sub)
        n_cross = int((sub[status_col] == cross_val).sum())
        n_non = int((sub[status_col] == non_val).sum())
        n_undet = int((sub[status_col] == undet_val).sum())
        n_decided = n_cross + n_non
        rows.append({
            "key": str(key),
            "n_trades": n,
            "n_undetermined": n_undet,
            "n_decided": n_decided,
            "n_crossing": n_cross,
            "n_non_crossing": n_non,
            "non_crossing_pct": (n_non / n_decided * 100) if n_decided > 0 else float("nan"),
            "crossing_pct": (n_cross / n_decided * 100) if n_decided > 0 else float("nan"),
            "net_crossing": float(sub.loc[sub[status_col] == cross_val, "net_usd"].sum()),
            "net_non_crossing": float(sub.loc[sub[status_col] == non_val, "net_usd"].sum()),
            "net_undetermined": float(sub.loc[sub[status_col] == undet_val, "net_usd"].sum()),
        })
    return pd.DataFrame(rows)


def net_distribution(trades: pd.DataFrame, status: str, status_col: str = "implied_status") -> dict:
    sub = trades[trades[status_col] == status]["net_usd"]
    if len(sub) == 0:
        return {"n": 0}
    return {
        "n": int(len(sub)),
        "sum": float(sub.sum()),
        "mean": float(sub.mean()),
        "median": float(sub.median()),
        "p25": float(sub.quantile(0.25)),
        "p75": float(sub.quantile(0.75)),
        "min": float(sub.min()),
        "max": float(sub.max()),
        "win_rate": float((sub > 0).mean()),
    }


def hold_bucket(trades: pd.DataFrame, status_col: str = "implied_status") -> list:
    """hold_min bucket 別 crossing 確率 (IMPLIED 基準)。"""
    if status_col == "crossing_status":
        cross_val, non_val = "CROSSING", "NON_CROSSING"
    else:
        cross_val, non_val = "IMPLIED_CROSSING", "IMPLIED_NON_CROSSING"
    bins = [0, 15, 30, 60, 120, 240, 480, 999999]
    labels = ["≤15m", "15-30m", "30-60m", "1-2h", "2-4h", "4-8h", ">8h"]
    cuts = pd.cut(trades["hold_min"], bins=bins, labels=labels, right=True, include_lowest=True)
    rows = []
    for lab in labels:
        sub = trades[cuts == lab]
        if len(sub) == 0:
            rows.append({"bucket": lab, "n": 0})
            continue
        n_decided = ((sub[status_col] == cross_val) | (sub[status_col] == non_val)).sum()
        n_cross = (sub[status_col] == cross_val).sum()
        rows.append({
            "bucket": lab,
            "n": int(len(sub)),
            "n_decided": int(n_decided),
            "n_crossing": int(n_cross),
            "crossing_pct": (n_cross / n_decided * 100) if n_decided > 0 else float("nan"),
            "net_total": float(sub["net_usd"].sum()),
        })
    return rows


def fmt_pct(x):
    if pd.isna(x) or x is None:
        return "—"
    return f"{x:.1f}%"


def fmt_usd(x):
    if pd.isna(x) or x is None:
        return "—"
    sign = "+" if x >= 0 else "−"
    return f"{sign}${abs(x):.2f}"


def main():
    print(f"[load] replay: {REPLAY_CSV}")
    trades = pd.read_csv(REPLAY_CSV)
    print(f"  trades: {len(trades)}")

    print("[load] 4h teacher labels")
    labels_4h = load_4h_labels()
    n_labeled = int((labels_4h["label"] != "").sum())
    print(f"  4h bars total: {len(labels_4h)} / labeled: {n_labeled}")

    print("[compute] boundary timestamps")
    boundaries = compute_boundary_ts(labels_4h)
    print(f"  boundaries: {len(boundaries)}")

    print("[classify] trades (STRICT + IMPLIED 並列)")
    trades = classify_trades(trades, boundaries, labels_4h, max_label_distance_h=24.0)
    print(f"  STRICT counts:  {trades['crossing_status'].value_counts().to_dict()}")
    print(f"  IMPLIED counts: {trades['implied_status'].value_counts().to_dict()}")

    # ── STRICT 集計 ──
    s_cross = int((trades["crossing_status"] == "CROSSING").sum())
    s_non = int((trades["crossing_status"] == "NON_CROSSING").sum())
    s_unl = int((trades["crossing_status"] == "UNLABELED").sum())
    s_decided = s_cross + s_non
    s_non_pct = (s_non / s_decided * 100) if s_decided > 0 else float("nan")
    s_cross_pct = (s_cross / s_decided * 100) if s_decided > 0 else float("nan")

    # ── IMPLIED 集計 (主軸) ──
    overall_cross = int((trades["implied_status"] == "IMPLIED_CROSSING").sum())
    overall_non = int((trades["implied_status"] == "IMPLIED_NON_CROSSING").sum())
    overall_unl = int((trades["implied_status"] == "IMPLIED_UNDETERMINED").sum())
    overall_labeled = overall_cross + overall_non
    overall_non_pct = (overall_non / overall_labeled * 100) if overall_labeled > 0 else float("nan")
    overall_cross_pct = (overall_cross / overall_labeled * 100) if overall_labeled > 0 else float("nan")

    print()
    print(f"[result STRICT]  decided {s_decided} (cross {s_cross} / non {s_non}) / unlabeled {s_unl}")
    if s_decided > 0:
        print(f"  CROSSING: {s_cross_pct:.1f}% / NON_CROSSING: {s_non_pct:.1f}%")
    print(f"[result IMPLIED] decided {overall_labeled} (cross {overall_cross} / non {overall_non}) / undetermined {overall_unl}")
    if overall_labeled > 0:
        print(f"  CROSSING: {overall_cross_pct:.1f}% / NON_CROSSING: {overall_non_pct:.1f}%")

    by_priority = ratio_table(trades, "priority")
    by_regime = ratio_table(trades, "regime")
    by_side = ratio_table(trades, "side")

    net_cross = net_distribution(trades, "IMPLIED_CROSSING")
    net_non = net_distribution(trades, "IMPLIED_NON_CROSSING")
    net_unl = net_distribution(trades, "IMPLIED_UNDETERMINED")

    holds = hold_bucket(trades)

    # ── md 出力 ──
    md = []
    md.append("# trade × regime 境界 整合性検証 (4h 教師)\n")
    md.append(f"- replay 入力: `{REPLAY_CSV.relative_to(BASE)}` (trades: {len(trades)})")
    md.append(f"- 4h 教師ラベル: 4 ファイル (2022-2025) / labeled bars: {n_labeled}")
    md.append(f"- boundary 定義: 連続 4h labeled バーで label 変化 (delta=4h)")
    md.append(f"- 検出された boundary 数: {len(boundaries)}")
    md.append("- 分類: LABELED:CROSSING / LABELED:NON_CROSSING / UNLABELED (周辺に labeled バーなし)")
    md.append("")

    md.append("## 判定方式の併記 (2 種)")
    md.append("")
    md.append("- **STRICT**: trade 区間 (entry, exit] に 4h boundary timestamp が含まれるか")
    md.append("  - 教師ラベル密度に依存。trade が短いほど検出されにくい (本データ median 15min)")
    md.append("- **IMPLIED**: trade entry 直前 24h 以内の labeled バー vs exit 直後 24h 以内の labeled バーで label 比較")
    md.append("  - boundary が unlabeled gap に隠れた場合も検出可能")
    md.append("")

    md.append("## 全体結果 (STRICT)")
    md.append("")
    md.append("| 分類 | 件数 | 全体比 | decided 内比 |")
    md.append("|---|---:|---:|---:|")
    md.append(f"| CROSSING | {s_cross} | {s_cross/len(trades)*100:.1f}% | {s_cross_pct:.1f}% |")
    md.append(f"| NON_CROSSING | {s_non} | {s_non/len(trades)*100:.1f}% | **{s_non_pct:.1f}%** |")
    md.append(f"| UNLABELED | {s_unl} | {s_unl/len(trades)*100:.1f}% | — |")
    md.append("")

    md.append("## 全体結果 (IMPLIED・主軸)")
    md.append("")
    md.append("| 分類 | 件数 | 全体比 | decided 内比 |")
    md.append("|---|---:|---:|---:|")
    md.append(f"| IMPLIED_CROSSING | {overall_cross} | {overall_cross/len(trades)*100:.1f}% | {overall_cross_pct:.1f}% |")
    md.append(f"| IMPLIED_NON_CROSSING | {overall_non} | {overall_non/len(trades)*100:.1f}% | **{overall_non_pct:.1f}%** |")
    md.append(f"| IMPLIED_UNDETERMINED | {overall_unl} | {overall_unl/len(trades)*100:.1f}% | — |")
    md.append(f"| 合計 | {len(trades)} | 100.0% | — |")
    md.append("")

    md.append("### 判断分岐 (まこさん指示・IMPLIED 主軸)")
    md.append("")
    md.append("- 跨がない確率 90%+ → 作戦継続")
    md.append("- 70-90%   → 部分問題")
    md.append("- 50% 以下 → 根本見直し")
    md.append(f"- **実測 IMPLIED_NON_CROSSING (decided 内): {overall_non_pct:.1f}%**")
    md.append("")

    md.append("## net_usd 分布 (IMPLIED crossing vs non-crossing vs undetermined)")
    md.append("")
    md.append("| 分類 | n | sum | mean | median | P25 | P75 | min | max | win rate |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for status, d in [("IMPLIED_CROSSING", net_cross), ("IMPLIED_NON_CROSSING", net_non), ("IMPLIED_UNDETERMINED", net_unl)]:
        if d.get("n", 0) == 0:
            md.append(f"| {status} | 0 | — | — | — | — | — | — | — | — |")
            continue
        md.append(f"| {status} | {d['n']} | {fmt_usd(d['sum'])} | {fmt_usd(d['mean'])} | {fmt_usd(d['median'])} | {fmt_usd(d['p25'])} | {fmt_usd(d['p75'])} | {fmt_usd(d['min'])} | {fmt_usd(d['max'])} | {fmt_pct(d['win_rate']*100)} |")
    md.append("")

    md.append("## Priority 別 跨ぎ率")
    md.append("")
    md.append("| Priority | 全 trade | labeled | crossing | non_crossing | non_crossing % | NET cross | NET non |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for _, r in by_priority.iterrows():
        md.append(f"| P{r['key']} | {r['n_trades']} | {r['n_decided']} | {r['n_crossing']} | {r['n_non_crossing']} | {fmt_pct(r['non_crossing_pct'])} | {fmt_usd(r['net_crossing'])} | {fmt_usd(r['net_non_crossing'])} |")
    md.append("")

    md.append("## regime (entry時) 別 跨ぎ率")
    md.append("")
    md.append("| regime | 全 trade | labeled | crossing | non_crossing | non_crossing % | NET cross | NET non |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for _, r in by_regime.iterrows():
        md.append(f"| {r['key']} | {r['n_trades']} | {r['n_decided']} | {r['n_crossing']} | {r['n_non_crossing']} | {fmt_pct(r['non_crossing_pct'])} | {fmt_usd(r['net_crossing'])} | {fmt_usd(r['net_non_crossing'])} |")
    md.append("")

    md.append("## side 別 跨ぎ率")
    md.append("")
    md.append("| side | 全 trade | labeled | crossing | non_crossing | non_crossing % | NET cross | NET non |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for _, r in by_side.iterrows():
        md.append(f"| {r['key']} | {r['n_trades']} | {r['n_decided']} | {r['n_crossing']} | {r['n_non_crossing']} | {fmt_pct(r['non_crossing_pct'])} | {fmt_usd(r['net_crossing'])} | {fmt_usd(r['net_non_crossing'])} |")
    md.append("")

    md.append("## hold_min バケット × 跨ぎ率")
    md.append("")
    md.append("| hold バケット | n | labeled | crossing | crossing % | NET total |")
    md.append("|---|---:|---:|---:|---:|---:|")
    for r in holds:
        if r["n"] == 0:
            md.append(f"| {r['bucket']} | 0 | 0 | — | — | — |")
            continue
        md.append(f"| {r['bucket']} | {r['n']} | {r.get('n_decided', 0)} | {r.get('n_crossing', 0)} | {fmt_pct(r.get('crossing_pct'))} | {fmt_usd(r['net_total'])} |")
    md.append("")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    DASH_DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print(f"[done] md: {OUT_MD}")

    # ── csv: per-trade ──
    out_cols = ["entry_time", "exit_time", "side", "priority", "regime",
                "hold_min", "net_usd", "crossing_status",
                "boundary_count", "has_label_nearby"]
    trades[out_cols].to_csv(OUT_CSV, index=False)
    print(f"[done] csv: {OUT_CSV}")

    # ── ダッシュボード JSON ──
    def _serialize_df(df):
        return df.replace({np.nan: None}).to_dict(orient="records")

    dash = {
        "version": "trade_regime_crossing_v1",
        "input": {
            "replay_csv": str(REPLAY_CSV.relative_to(BASE)),
            "n_trades": int(len(trades)),
            "n_4h_labeled_bars": int(n_labeled),
            "n_boundaries": int(len(boundaries)),
        },
        "overall_implied": {
            "n_total": int(len(trades)),
            "n_decided": int(overall_labeled),
            "n_undetermined": int(overall_unl),
            "n_crossing": int(overall_cross),
            "n_non_crossing": int(overall_non),
            "non_crossing_pct": (None if pd.isna(overall_non_pct) else overall_non_pct),
            "crossing_pct": (None if pd.isna(overall_cross_pct) else overall_cross_pct),
        },
        "overall_strict": {
            "n_total": int(len(trades)),
            "n_decided": int(s_decided),
            "n_unlabeled": int(s_unl),
            "n_crossing": int(s_cross),
            "n_non_crossing": int(s_non),
            "non_crossing_pct": (None if pd.isna(s_non_pct) else s_non_pct),
            "crossing_pct": (None if pd.isna(s_cross_pct) else s_cross_pct),
        },
        "net_dist_implied": {
            "IMPLIED_CROSSING": net_cross,
            "IMPLIED_NON_CROSSING": net_non,
            "IMPLIED_UNDETERMINED": net_unl,
        },
        "by_priority": _serialize_df(by_priority),
        "by_regime": _serialize_df(by_regime),
        "by_side": _serialize_df(by_side),
        "by_hold_bucket": holds,
        "judgment_brackets": {
            "90+": "作戦継続",
            "70-90": "部分問題",
            "<=50": "根本見直し",
        },
    }
    with open(OUT_DASH_JSON, "w") as f:
        json.dump(dash, f, indent=2, ensure_ascii=False, default=str)
    print(f"[done] dashboard json: {OUT_DASH_JSON}")

    print()
    print(f"[summary] NON_CROSSING (labeled 内): {overall_non_pct:.1f}% / CROSSING: {overall_cross_pct:.1f}% / UNLABELED: {overall_unl}")
    print(f"[summary] NET CROSSING:     {fmt_usd(net_cross.get('sum', 0))} (n={net_cross.get('n', 0)})")
    print(f"[summary] NET NON_CROSSING: {fmt_usd(net_non.get('sum', 0))} (n={net_non.get('n', 0)})")
    print(f"[summary] NET UNLABELED:    {fmt_usd(net_unl.get('sum', 0))} (n={net_unl.get('n', 0)})")


if __name__ == "__main__":
    main()
