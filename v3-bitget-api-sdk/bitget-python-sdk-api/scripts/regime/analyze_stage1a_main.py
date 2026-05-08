"""analyze_stage1a_main.py — 段階1-A 本分析

切替点 198件について、t=0 と過去 N バーの指標分布を全指標で出す。
§13 方針「分析段階では絞り込みしない」を維持し、メタ分析スコア（ラベル分離度・
パターン特異性）を併記して優先候補を ★ で示す（採否判定は段階2 で行う）。

設計:
- N: メタ分析（自己相関 < 0.5 切り中央値）からカテゴリ別に決定
  - 1_trend=7 / 2_momentum=5 / 3_volatility=10 / 4_adx_dmi=14
  - 5_volume=6 / 6_priceaction=1（窓なし・現値のみ）/ 7_position=1（窓なし）
- 時間軸: 1h / 4h / 1d（メタ分析処理2-C で 5m が最も分離悪い → 除外）
- 切替点: 直接遷移 198件（blank・同ラベル復帰は除外）
- post（未来）は使わない: t=0 と pre 窓のみ

集計（per-event → cohort）:
- t0_value: 切替バーの指標値
- pre_window_median: t-N〜t-1 の中央値
- pre_window_slope: (窓末 - 窓初) / N
- pre_window_monotonic: 過去 N バーの単調度（連続増/減の割合・0〜1）

各セルに以下を併記:
- ラベル分離度（メタ処理2）
- パターン特異性（メタ処理3 の対応パターン）
- 両方 < 0.3 で ★（優先候補マーク）

出力: results/regime_label_analysis/stage1a_main_distribution.md
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import pandas as pd
import numpy as np

from analyze_regime_label_features import build_indicators_extended
from analyze_vshape_indicators import resample_ohlcv
from analyze_transition_indicators import (
    load_labels,
    run_length_encode,
    extract_transitions,
    attach_all_indicators_dict,
)
from analyze_stage1a_meta import (
    label_separation_analysis,
    pattern_specificity_analysis,
    CATEGORIES,
    ALL_INDICATORS,
)

BASE = Path(__file__).parent.parent.parent
DATA_5M = BASE / "data/BTCUSDT-5m-2021-04-01_03-31_1826d.csv"
OUT_DIR = BASE / "results/regime_label_analysis"
OUT_MD = OUT_DIR / "stage1a_main_distribution.md"

# メタ分析処理1の結果から決定したカテゴリ別 N（自己相関<0.5 中央値）
N_BY_CATEGORY = {
    "1_trend": 7,
    "2_momentum": 5,
    "3_volatility": 10,
    "4_adx_dmi": 14,
    "5_volume": 6,
    "6_priceaction": 1,  # 窓スキップ
    "7_position": 1,     # 窓スキップ
    "8_mtf": 1,          # 窓スキップ（slope 派生指標で過去窓不要）
}
NO_WINDOW_CATEGORIES = {"6_priceaction", "7_position", "8_mtf"}

TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h", "1d"]
PATTERNS = ["up->dn", "dn->up", "up->rg", "rg->up", "rg->dn", "dn->rg"]
PRIORITY_THRESHOLD = 0.3
CATEGORY_NAMES = {
    "1_trend": "トレンド系",
    "2_momentum": "モメンタム系",
    "3_volatility": "ボラティリティ系",
    "4_adx_dmi": "方向性強度系 (ADX/DMI)",
    "5_volume": "出来高系",
    "6_priceaction": "プライスアクション系",
    "7_position": "価格位置系",
    "8_mtf": "MTF同調系",
}


def category_of(indicator: str) -> str:
    for cat_id, inds in CATEGORIES.items():
        if indicator in inds:
            return cat_id
    return "other"


def n_for_indicator(indicator: str) -> int:
    cat = category_of(indicator)
    return N_BY_CATEGORY.get(cat, 1)


def per_event_distribution(labels_df, transitions, indicator_cols):
    """切替点 t=0 と過去 N バー窓の集計値を per-event で算出。"""
    rows = []
    for ev in transitions:
        t = ev["t_idx"]
        for col in indicator_cols:
            base = col.rsplit("__", 1)[0]
            tf = col.rsplit("__", 1)[1]
            if tf not in TIMEFRAMES:
                continue
            cat = category_of(base)
            N = N_BY_CATEGORY.get(cat, 1)
            # t=0 値
            t0 = labels_df.iloc[t][col] if col in labels_df.columns else np.nan
            row = {
                "pattern": f"{ev['prev']}->{ev['cur']}",
                "indicator": base,
                "tf": tf,
                "category": cat,
                "t0_value": t0,
            }
            # 過去窓
            if cat not in NO_WINDOW_CATEGORIES:
                pre_lo = max(ev["prev_start"], t - N)
                if pre_lo < t:
                    block = labels_df.iloc[pre_lo:t][col].dropna()
                    if len(block) >= 2:
                        row["pre_median"] = block.median()
                        row["pre_min"] = block.min()
                        row["pre_max"] = block.max()
                        # slope: 窓末 - 窓初 / 期間
                        first = block.iloc[0]
                        last = block.iloc[-1]
                        row["pre_slope"] = (last - first) / max(1, len(block) - 1)
                        # monotonic: 連続増 or 連続減バーの割合
                        diffs = block.diff().dropna()
                        if len(diffs) > 0:
                            up_run = (diffs > 0).sum()
                            down_run = (diffs < 0).sum()
                            row["pre_monotonic"] = max(up_run, down_run) / len(diffs)
            rows.append(row)
    return pd.DataFrame(rows)


def cohort_summary(per_event_df: pd.DataFrame) -> pd.DataFrame:
    """per-event を pattern × indicator × tf で cohort 中央値・Q1/Q3 へ集約。"""
    if per_event_df.empty:
        return pd.DataFrame()
    agg_cols = ["t0_value", "pre_median", "pre_min", "pre_max", "pre_slope", "pre_monotonic"]
    agg_cols = [c for c in agg_cols if c in per_event_df.columns]

    rows = []
    grouped = per_event_df.groupby(["pattern", "indicator", "tf", "category"])
    for keys, sub in grouped:
        pattern, indicator, tf, category = keys
        row = {
            "pattern": pattern,
            "indicator": indicator,
            "tf": tf,
            "category": category,
            "n": len(sub),
        }
        for c in agg_cols:
            s = sub[c].dropna()
            if len(s) == 0:
                row[f"{c}_med"] = np.nan
                row[f"{c}_q1"] = np.nan
                row[f"{c}_q3"] = np.nan
            else:
                row[f"{c}_med"] = s.median()
                row[f"{c}_q1"] = s.quantile(0.25)
                row[f"{c}_q3"] = s.quantile(0.75)
        rows.append(row)
    return pd.DataFrame(rows)


def fmt(x, decimals=3):
    if pd.isna(x):
        return "—"
    if abs(x) >= 1000:
        return f"{x:.0f}"
    if abs(x) >= 100:
        return f"{x:.1f}"
    if abs(x) >= 10:
        return f"{x:.2f}"
    return f"{x:.{decimals}f}"


def fmt_q(med, q1, q3):
    return f"{fmt(med)} [{fmt(q1)}, {fmt(q3)}]"


def write_md(cohort_df: pd.DataFrame, sep_df: pd.DataFrame, spec_df: pd.DataFrame, out_path: Path):
    # メタスコアを引きやすい dict に
    sep_lookup = {(r["indicator"], r["tf"]): r["overlap_ratio"] for _, r in sep_df.iterrows()}
    spec_lookup = {(r["pattern"], r["indicator"], r["tf"]): r["mean_overlap_vs_others"]
                   for _, r in spec_df.iterrows()}

    lines = []
    lines.append("# 段階1-A 本分析: 切替点 t=0 + 過去 N バー指標分布（全指標）")
    lines.append("")
    lines.append("§13 方針「分析段階では絞り込みしない・全指標で特徴を出す」に従い、")
    lines.append(f"**全指標 × 6パターン × {len(TIMEFRAMES)}軸** の分布を出す。")
    lines.append("メタ分析スコア（ラベル分離度・パターン特異性）を併記し、")
    lines.append(f"両方 < {PRIORITY_THRESHOLD} の指標は **★** で優先候補を示す。")
    lines.append("採否判定は段階2（判定ロジック設計）で行う。")
    lines.append("")
    lines.append("## 設計")
    lines.append("")
    lines.append("- **N (過去バー数・カテゴリ別)**: メタ分析処理1（自己相関<0.5 切り中央値）から決定")
    n_table = "\n".join([f"  - {cat}: N={n}{' (窓スキップ・現値のみ)' if cat in NO_WINDOW_CATEGORIES else ''}"
                         for cat, n in N_BY_CATEGORY.items()])
    lines.append(n_table)
    lines.append(f"- **時間軸**: {' / '.join(TIMEFRAMES)}（全6軸並列・絞り込みなし）")
    lines.append("- **切替点**: 直接遷移 198件（blank・同ラベル復帰除外）")
    lines.append("- **post（未来）は使わない**: t=0 値と過去窓のみ")
    lines.append("- **★**: ラベル分離度 < 0.3 **かつ** パターン特異性 < 0.3 の指標（優先候補）")
    lines.append("")
    lines.append("各セル形式: t0=値[Q1,Q3] / pre_med=中央値[Q1,Q3] / slope=傾き / monot=単調度")
    lines.append("")
    lines.append("---")
    lines.append("")

    # === カテゴリごと × パターンごとに表を出す ===
    for cat_id, cat_name in CATEGORY_NAMES.items():
        cat_inds = CATEGORIES.get(cat_id, [])
        if not cat_inds:
            continue
        lines.append(f"## カテゴリ {cat_id.split('_')[0]}: {cat_name}")
        lines.append("")
        N = N_BY_CATEGORY.get(cat_id, 1)
        if cat_id in NO_WINDOW_CATEGORIES:
            lines.append(f"- N=1（過去窓スキップ・t=0 値のみ）")
        else:
            lines.append(f"- N={N}（過去 {N} bar の窓集計を併記）")
        lines.append("")

        for pattern in PATTERNS:
            n_events = cohort_df[(cohort_df["pattern"] == pattern) & (cohort_df["category"] == cat_id)]["n"]
            n_evt = int(n_events.iloc[0]) if len(n_events) > 0 else 0
            lines.append(f"### {pattern}  (n={n_evt})")
            lines.append("")

            if cat_id in NO_WINDOW_CATEGORIES:
                # 窓なし・t=0 のみ
                lines.append("| Indicator | TF | t0 [Q1, Q3] | sep | spec | ★ |")
                lines.append("|---|---|---|---:|---:|:-:|")
                for ind in cat_inds:
                    for tf in TIMEFRAMES:
                        sub = cohort_df[(cohort_df["pattern"] == pattern)
                                        & (cohort_df["indicator"] == ind)
                                        & (cohort_df["tf"] == tf)]
                        if sub.empty:
                            continue
                        r = sub.iloc[0]
                        sep = sep_lookup.get((ind, tf), np.nan)
                        spec = spec_lookup.get((pattern, ind, tf), np.nan)
                        star = "★" if (pd.notna(sep) and sep < PRIORITY_THRESHOLD
                                       and pd.notna(spec) and spec < PRIORITY_THRESHOLD) else ""
                        lines.append(
                            f"| `{ind}` | {tf} | "
                            f"{fmt_q(r['t0_value_med'], r['t0_value_q1'], r['t0_value_q3'])} | "
                            f"{fmt(sep)} | {fmt(spec)} | {star} |"
                        )
            else:
                # 窓あり
                lines.append("| Indicator | TF | t0 [Q1, Q3] | pre_med [Q1, Q3] | slope_med | monot_med | sep | spec | ★ |")
                lines.append("|---|---|---|---|---:|---:|---:|---:|:-:|")
                for ind in cat_inds:
                    for tf in TIMEFRAMES:
                        sub = cohort_df[(cohort_df["pattern"] == pattern)
                                        & (cohort_df["indicator"] == ind)
                                        & (cohort_df["tf"] == tf)]
                        if sub.empty:
                            continue
                        r = sub.iloc[0]
                        sep = sep_lookup.get((ind, tf), np.nan)
                        spec = spec_lookup.get((pattern, ind, tf), np.nan)
                        star = "★" if (pd.notna(sep) and sep < PRIORITY_THRESHOLD
                                       and pd.notna(spec) and spec < PRIORITY_THRESHOLD) else ""
                        slope_v = r.get("pre_slope_med", np.nan)
                        monot_v = r.get("pre_monotonic_med", np.nan)
                        lines.append(
                            f"| `{ind}` | {tf} | "
                            f"{fmt_q(r['t0_value_med'], r['t0_value_q1'], r['t0_value_q3'])} | "
                            f"{fmt_q(r.get('pre_median_med', np.nan), r.get('pre_median_q1', np.nan), r.get('pre_median_q3', np.nan))} | "
                            f"{fmt(slope_v)} | {fmt(monot_v)} | "
                            f"{fmt(sep)} | {fmt(spec)} | {star} |"
                        )
            lines.append("")
        lines.append("")

    # === ★ 優先候補一覧 ===
    lines.append("## ★ 優先候補一覧（メタスコア両方 < 0.3 のもの）")
    lines.append("")
    lines.append("段階2 の判定ロジック設計時に、まずこのリストから検討する候補。")
    lines.append("**注意**: ここは「絞り込み結果」ではなく「優先順位の参考」。")
    lines.append("段階1-A の対象は全指標であり、★ 以外も段階2 で検討対象とする。")
    lines.append("")
    star_rows = []
    for _, r in cohort_df.iterrows():
        sep = sep_lookup.get((r["indicator"], r["tf"]), np.nan)
        spec = spec_lookup.get((r["pattern"], r["indicator"], r["tf"]), np.nan)
        if pd.notna(sep) and sep < PRIORITY_THRESHOLD and pd.notna(spec) and spec < PRIORITY_THRESHOLD:
            star_rows.append({
                "pattern": r["pattern"],
                "indicator": r["indicator"],
                "tf": r["tf"],
                "sep": sep,
                "spec": spec,
                "n": r["n"],
            })
    if star_rows:
        star_df = pd.DataFrame(star_rows).sort_values(["pattern", "spec"])
        lines.append("| pattern | indicator | tf | sep | spec | n |")
        lines.append("|---|---|---|---:|---:|---:|")
        for _, r in star_df.iterrows():
            lines.append(f"| {r['pattern']} | `{r['indicator']}` | {r['tf']} | {fmt(r['sep'])} | {fmt(r['spec'])} | {int(r['n'])} |")
    else:
        lines.append("(該当なし)")
    lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))


def main():
    print("ラベル + 切替点抽出...")
    labels = load_labels()
    runs = run_length_encode(labels["label_norm"].tolist())
    transitions = extract_transitions(runs)
    print(f"  切替点数: {len(transitions)}")

    print(f"OHLCV resample + 指標計算 ({len(TIMEFRAMES)}軸)...")
    df5m = pd.read_csv(DATA_5M, parse_dates=["timestamp"]).set_index("timestamp").sort_index()
    all_dfs = {
        "5m": df5m,
        "15m": resample_ohlcv(df5m, "15min"),
        "30m": resample_ohlcv(df5m, "30min"),
        "1h": resample_ohlcv(df5m, "1h"),
        "4h": resample_ohlcv(df5m, "4h"),
        "1d": resample_ohlcv(df5m, "1D"),
    }
    feat_per_tf = {tf: build_indicators_extended(all_dfs[tf]) for tf in TIMEFRAMES if tf in all_dfs}

    print("attach...")
    labels_attached = attach_all_indicators_dict(labels, feat_per_tf)
    suffix_set = tuple(f"__{tf}" for tf in TIMEFRAMES)
    indicator_cols = [c for c in labels_attached.columns
                      if c.endswith(suffix_set)
                      and c.rsplit("__", 1)[0] in ALL_INDICATORS]
    print(f"  対象指標カラム数: {len(indicator_cols)}")

    print("per-event 分布集計...")
    per_event = per_event_distribution(labels_attached, transitions, indicator_cols)
    print(f"  per-event 行数: {len(per_event)}")

    print("cohort 集計...")
    cohort = cohort_summary(per_event)
    print(f"  cohort 行数: {len(cohort)}")

    print("メタスコア再計算（参照用）...")
    sep_df = label_separation_analysis(labels_attached)
    spec_df = pattern_specificity_analysis(labels_attached, transitions)

    print(f"md 出力: {OUT_MD}")
    write_md(cohort, sep_df, spec_df, OUT_MD)
    print("DONE")


if __name__ == "__main__":
    main()
