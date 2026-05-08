"""analyze_stage1b_main.py — 段階1-B 本分析

形状特徴量 (B-1〜B-5) について、切替点 198 件の t=0 値を全パターンで集計する。
§13 方針「分析段階では絞り込みしない」を維持し、メタ分析スコアを 3系統 (全件/短命/通常)
で併記して優先候補を ★ で示す。

設計:
- 対象軸: 5m / 15m / 30m / 1h / 4h / 1d (全6軸並列・絞り込みなし)
- 窓 W: W=10 を主軸 (全特徴量×全軸で計算) + W=20/W=50 で重複度 0 のものを追加
- 切替点: 直接遷移 198 件 (blank・同ラベル復帰除外)
- per-event テーブルに **prev_run カラム必須** (段階2 でフィルタ可能にする)
- メタスコア (分離度・特異性) は **全件 / 短命 / 通常 の 3系統** で併記
- ★ は subset ごとに「sep < 0.3 かつ spec_subset < 0.3」で判定

post (未来) は使わない。形状特徴量自体が過去 W バーを要約するため過去窓は不要。

出力: results/regime_label_analysis/stage1b_main_distribution.md
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import pandas as pd
import numpy as np

from analyze_transition_indicators import (
    load_labels,
    run_length_encode,
    extract_transitions,
    attach_indicators,
)
from analyze_stage1a_meta import overlap_3way, overlap_pair
from analyze_stage1b_meta import (
    resample_ohlcv,
    attach_features_to_labels,
    label_separation_analysis,
    pattern_specificity_analysis,
    SHORT_THRESHOLD,
)
from shape_features import (
    FEATURE_FUNCS,
    CATEGORY_OF_FEATURE,
    compute_all_features,
)

BASE = Path(__file__).parent.parent.parent
DATA_5M = BASE / "data/BTCUSDT-5m-2021-04-01_03-31_1826d.csv"
OUT_DIR = BASE / "results/regime_label_analysis"
OUT_MD = OUT_DIR / "stage1b_main_distribution.md"

# 対象軸 (全6軸並列)
TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h", "1d"]

# W 採用方針
W_PRIMARY = 10  # 全特徴量×全軸でこの W
W_ADDITIONAL_FROM_META = [20, 50]  # メタで重複度 0 のものだけ追加

PRIORITY_THRESHOLD = 0.3
PATTERNS = ["up->dn", "dn->up", "up->rg", "rg->up", "rg->dn", "dn->rg"]
CATEGORY_NAMES_B = {
    "B1_breakout": "B-1 高値・安値ブレイク",
    "B2_swing": "B-2 スイングポイント",
    "B3_pattern": "B-3 反発パターン (V/W字)",
    "B4_candle": "B-4 ローソク足構造",
    "B5_streak": "B-5 連続パターン",
}


def determine_target_combos(sep_df: pd.DataFrame) -> list[tuple[str, str, int]]:
    """対象 (feature, tf, W) の組み合わせを決定。
    - W=10: 全特徴量×TIMEFRAMES
    - W=20/W=50: メタ分析で重複度 0 のもののみ
    """
    combos = []
    # W=10 主軸
    for fname in FEATURE_FUNCS.keys():
        for tf in TIMEFRAMES:
            combos.append((fname, tf, W_PRIMARY))

    # W=20/W=50 で重複度 0 のもの追加
    if not sep_df.empty:
        zero_overlap = sep_df[
            (sep_df["overlap_ratio"] == 0.0)
            & (sep_df["W"].isin(W_ADDITIONAL_FROM_META))
            & (sep_df["tf"].isin(TIMEFRAMES))
        ]
        for _, r in zero_overlap.iterrows():
            combo = (r["feature"], r["tf"], int(r["W"]))
            if combo not in combos:
                combos.append(combo)

    return combos


def per_event_table(labels_attached: pd.DataFrame, transitions: list, combos: list) -> pd.DataFrame:
    """切替点 t=0 値を per-event で集計。prev_run カラム必須。"""
    rows = []
    for ev in transitions:
        t = ev["t_idx"]
        prev_thr = SHORT_THRESHOLD.get(ev["prev"], 99)
        is_short = ev["prev_len"] <= prev_thr
        subset = "short" if is_short else "normal"
        for fname, tf, W in combos:
            col = f"{fname}__{tf}_W{W}"
            if col not in labels_attached.columns:
                continue
            t0_val = labels_attached.iloc[t][col]
            rows.append({
                "pattern": f"{ev['prev']}->{ev['cur']}",
                "subset": subset,
                "feature": fname,
                "tf": tf,
                "W": W,
                "t0_value": t0_val,
                "prev_run": ev["prev_len"],
                "cur_run": ev["cur_len"],
                "category": CATEGORY_OF_FEATURE.get(fname, "other"),
            })
    return pd.DataFrame(rows)


def cohort_summary(per_event_df: pd.DataFrame) -> pd.DataFrame:
    """全件と subset 別で cohort 中央値・Q1/Q3 を出す。"""
    if per_event_df.empty:
        return pd.DataFrame()

    rows = []
    for keys, sub in per_event_df.groupby(["pattern", "feature", "tf", "W", "category"]):
        pattern, feature, tf, W, category = keys
        # 全件
        s_all = sub["t0_value"].dropna()
        # 短命のみ
        s_short = sub[sub["subset"] == "short"]["t0_value"].dropna()
        # 通常のみ
        s_normal = sub[sub["subset"] == "normal"]["t0_value"].dropna()

        row = {
            "pattern": pattern, "feature": feature, "tf": tf, "W": W, "category": category,
            "n_all": len(s_all), "n_short": len(s_short), "n_normal": len(s_normal),
            "all_med": s_all.median() if len(s_all) > 0 else np.nan,
            "all_q1": s_all.quantile(0.25) if len(s_all) > 0 else np.nan,
            "all_q3": s_all.quantile(0.75) if len(s_all) > 0 else np.nan,
            "short_med": s_short.median() if len(s_short) > 0 else np.nan,
            "short_q1": s_short.quantile(0.25) if len(s_short) > 0 else np.nan,
            "short_q3": s_short.quantile(0.75) if len(s_short) > 0 else np.nan,
            "normal_med": s_normal.median() if len(s_normal) > 0 else np.nan,
            "normal_q1": s_normal.quantile(0.25) if len(s_normal) > 0 else np.nan,
            "normal_q3": s_normal.quantile(0.75) if len(s_normal) > 0 else np.nan,
        }
        rows.append(row)
    return pd.DataFrame(rows)


def fmt(x, dec=3):
    if pd.isna(x):
        return "—"
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    if abs(x) >= 1000:
        return f"{x:.0f}"
    if abs(x) >= 100:
        return f"{x:.1f}"
    if abs(x) >= 10:
        return f"{x:.2f}"
    return f"{x:.{dec}f}"


def fmt_q(med, q1, q3):
    return f"{fmt(med)} [{fmt(q1)}, {fmt(q3)}]"


def write_md(cohort_df, sep_df, spec_dfs, per_event_df, combos, out_path):
    # メタスコア lookup
    sep_lookup = {(r["feature"], r["tf"], int(r["W"])): r["overlap_ratio"]
                  for _, r in sep_df.iterrows()}
    spec_lookups = {}
    for subset, spec_df in spec_dfs.items():
        spec_lookups[subset] = {(r["pattern"], r["feature"], r["tf"], int(r["W"])): r["mean_overlap_vs_others"]
                                for _, r in spec_df.iterrows()}

    lines = []
    lines.append("# 段階1-B 本分析: 切替点 t=0 形状特徴量分布")
    lines.append("")
    lines.append("§13 方針「分析段階では絞り込みしない」維持・全特徴量で出す。")
    lines.append("メタスコア (ラベル分離度・パターン特異性) は **全件/短命/通常 の 3系統** で併記。")
    lines.append(f"両方 < {PRIORITY_THRESHOLD} の組合せは subset 別に **★** で示す。")
    lines.append("採否判定は段階2 で行う。")
    lines.append("")
    lines.append("## 設計")
    lines.append("")
    lines.append(f"- **対象軸**: {' / '.join(TIMEFRAMES)} (全6軸並列・絞り込みなし)")
    lines.append(f"- **W**: W={W_PRIMARY} を主軸 (全特徴量×全軸) + W={W_ADDITIONAL_FROM_META} で重複度 0 のもの追加")
    lines.append(f"- **切替点**: 直接遷移 198 件 (blank・同ラベル復帰除外)")
    lines.append(f"- **post (未来) は使わない**: 形状特徴量自体が過去 W バーを要約するため過去窓不要")
    lines.append(f"- **prev_run カラム** を per-event テーブルに必ず含める (段階2 フィルタ可能化)")
    lines.append(f"- **短命/通常閾値**: up≤{SHORT_THRESHOLD['up']}/rg≤{SHORT_THRESHOLD['rg']}/dn≤{SHORT_THRESHOLD['dn']} (前 run 長で判定)")
    lines.append(f"- **対象組合せ数**: {len(combos)} (W={W_PRIMARY} で {len(FEATURE_FUNCS) * len(TIMEFRAMES)} + 追加 {len(combos) - len(FEATURE_FUNCS) * len(TIMEFRAMES)})")
    lines.append("")
    lines.append("各セル形式: `t0 中央値 [Q1, Q3]`")
    lines.append("")
    lines.append("---")
    lines.append("")

    # === カテゴリ × パターン ===
    for cat_id, cat_name in CATEGORY_NAMES_B.items():
        lines.append(f"## カテゴリ {cat_name}")
        lines.append("")
        cat_features = [f for f, c in CATEGORY_OF_FEATURE.items() if c == cat_id]
        if not cat_features:
            continue

        for pattern in PATTERNS:
            lines.append(f"### {pattern}")
            lines.append("")
            sub = cohort_df[(cohort_df["pattern"] == pattern) & (cohort_df["category"] == cat_id)]
            if sub.empty:
                lines.append("(該当なし)")
                lines.append("")
                continue

            n_all = int(sub["n_all"].iloc[0]) if len(sub) > 0 else 0
            n_short = int(sub["n_short"].iloc[0]) if len(sub) > 0 else 0
            n_normal = int(sub["n_normal"].iloc[0]) if len(sub) > 0 else 0
            lines.append(f"- 切替点件数: 全件={n_all} / 短命={n_short} / 通常={n_normal}")
            lines.append("")

            lines.append("| Feature | TF | W | All t0 [Q1,Q3] | Short t0 [Q1,Q3] | Normal t0 [Q1,Q3] | sep | spec_all | spec_short | spec_normal | ★(all/short/normal) |")
            lines.append("|---|---|---:|---|---|---|---:|---:|---:|---:|---|")
            for _, r in sub.sort_values(["feature", "tf", "W"]).iterrows():
                key = (r["feature"], r["tf"], int(r["W"]))
                sep = sep_lookup.get(key, np.nan)
                spec_all = spec_lookups["all"].get((pattern,) + key, np.nan)
                spec_short = spec_lookups["short"].get((pattern,) + key, np.nan)
                spec_normal = spec_lookups["normal"].get((pattern,) + key, np.nan)

                star_all = "★" if (pd.notna(sep) and sep < PRIORITY_THRESHOLD
                                    and pd.notna(spec_all) and spec_all < PRIORITY_THRESHOLD) else "—"
                star_short = "★" if (pd.notna(sep) and sep < PRIORITY_THRESHOLD
                                      and pd.notna(spec_short) and spec_short < PRIORITY_THRESHOLD) else "—"
                star_normal = "★" if (pd.notna(sep) and sep < PRIORITY_THRESHOLD
                                       and pd.notna(spec_normal) and spec_normal < PRIORITY_THRESHOLD) else "—"

                lines.append(
                    f"| `{r['feature']}` | {r['tf']} | {int(r['W'])} | "
                    f"{fmt_q(r['all_med'], r['all_q1'], r['all_q3'])} | "
                    f"{fmt_q(r['short_med'], r['short_q1'], r['short_q3'])} | "
                    f"{fmt_q(r['normal_med'], r['normal_q1'], r['normal_q3'])} | "
                    f"{fmt(sep)} | {fmt(spec_all)} | {fmt(spec_short)} | {fmt(spec_normal)} | "
                    f"{star_all}/{star_short}/{star_normal} |"
                )
            lines.append("")
        lines.append("")

    # === ★ 優先候補一覧 (subset 別) ===
    lines.append("## ★ 優先候補一覧 (subset 別)")
    lines.append("")
    lines.append("段階2 の判定ロジック設計時に検討する候補。段階1-A の ★ と組み合わせ可能。")
    lines.append("")
    for subset_label, subset_jp in [("all", "全件"), ("short", "短命のみ"), ("normal", "通常のみ")]:
        lines.append(f"### {subset_jp} (★)")
        lines.append("")
        star_rows = []
        for _, r in cohort_df.iterrows():
            key = (r["feature"], r["tf"], int(r["W"]))
            sep = sep_lookup.get(key, np.nan)
            spec = spec_lookups[subset_label].get((r["pattern"],) + key, np.nan)
            if pd.notna(sep) and sep < PRIORITY_THRESHOLD and pd.notna(spec) and spec < PRIORITY_THRESHOLD:
                n_col = f"n_{subset_label}"
                star_rows.append({
                    "pattern": r["pattern"],
                    "feature": r["feature"],
                    "tf": r["tf"],
                    "W": int(r["W"]),
                    "sep": sep,
                    "spec": spec,
                    "n": int(r[n_col]) if not pd.isna(r[n_col]) else 0,
                })
        if not star_rows:
            lines.append("(該当なし)")
            lines.append("")
            continue
        star_df = pd.DataFrame(star_rows).sort_values(["pattern", "spec"])
        lines.append("| pattern | feature | tf | W | sep | spec | n |")
        lines.append("|---|---|---|---:|---:|---:|---:|")
        for _, r in star_df.iterrows():
            lines.append(f"| {r['pattern']} | `{r['feature']}` | {r['tf']} | {int(r['W'])} | "
                        f"{fmt(r['sep'])} | {fmt(r['spec'])} | {int(r['n'])} |")
        lines.append("")

    # === per-event 抜粋 ===
    lines.append("## per-event テーブル抜粋 (prev_run 含む・段階2 フィルタ用)")
    lines.append("")
    lines.append(f"全行数: {len(per_event_df)}")
    lines.append("")
    lines.append("先頭 20 行のみ抜粋:")
    lines.append("")
    lines.append("| pattern | subset | feature | tf | W | t0 | prev_run | cur_run |")
    lines.append("|---|---|---|---|---:|---:|---:|---:|")
    for _, r in per_event_df.head(20).iterrows():
        lines.append(f"| {r['pattern']} | {r['subset']} | `{r['feature']}` | {r['tf']} | {int(r['W'])} | "
                    f"{fmt(r['t0_value'])} | {int(r['prev_run'])} | {int(r['cur_run'])} |")
    lines.append("")
    lines.append("(完全な per-event テーブルは段階2 でスクリプト経由で取得・本 md には抜粋のみ)")
    lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))


def main():
    print("ラベル + 切替点抽出...")
    labels = load_labels()
    runs = run_length_encode(labels["label_norm"].tolist())
    transitions = extract_transitions(runs)
    print(f"  切替点数: {len(transitions)}")

    print(f"OHLCV resample ({len(TIMEFRAMES)}軸)...")
    df5m = pd.read_csv(DATA_5M, parse_dates=["timestamp"]).set_index("timestamp").sort_index()
    all_dfs = {
        "5m": df5m,
        "15m": resample_ohlcv(df5m, "15min"),
        "30m": resample_ohlcv(df5m, "30min"),
        "1h": resample_ohlcv(df5m, "1h"),
        "4h": resample_ohlcv(df5m, "4h"),
        "1d": resample_ohlcv(df5m, "1D"),
    }
    df_per_tf = {tf: all_dfs[tf] for tf in TIMEFRAMES if tf in all_dfs}

    print("形状特徴量計算 (軸 × W)...")
    features_per_tf: dict[str, dict[int, pd.DataFrame]] = {}
    Ws_to_compute = [W_PRIMARY] + W_ADDITIONAL_FROM_META  # 10/20/50 すべて計算 (メタ結果に依存)
    for tf, df in df_per_tf.items():
        features_per_tf[tf] = {}
        for W in Ws_to_compute:
            features_per_tf[tf][W] = compute_all_features(df, W)
        print(f"  {tf} 完了")

    print("attach 教師ラベル...")
    labels_attached = attach_features_to_labels(labels, features_per_tf)

    print("メタスコア再計算 (3系統)...")
    sep_df = label_separation_analysis(labels_attached)
    spec_dfs = {}
    for subset in ["all", "short", "normal"]:
        spec_dfs[subset] = pattern_specificity_analysis(labels_attached, transitions, subset)
    print(f"  sep: {len(sep_df)} / spec_all: {len(spec_dfs['all'])} / spec_short: {len(spec_dfs['short'])} / spec_normal: {len(spec_dfs['normal'])}")

    print("対象 (feature, tf, W) 組合せ決定...")
    combos = determine_target_combos(sep_df)
    print(f"  対象組合せ数: {len(combos)}")

    print("per-event 集計...")
    per_event_df = per_event_table(labels_attached, transitions, combos)
    print(f"  per-event 行数: {len(per_event_df)}")

    print("cohort 集計...")
    cohort_df = cohort_summary(per_event_df)
    print(f"  cohort 行数: {len(cohort_df)}")

    print(f"md 出力: {OUT_MD}")
    write_md(cohort_df, sep_df, spec_dfs, per_event_df, combos, OUT_MD)
    print("DONE")


if __name__ == "__main__":
    main()
