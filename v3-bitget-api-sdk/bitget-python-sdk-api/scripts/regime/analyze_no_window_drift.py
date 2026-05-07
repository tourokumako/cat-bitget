"""analyze_no_window_drift.py — 窓なし指標のドリフト検証 + #6 代表 datetime 抽出

【目的1】窓なし指標 6セルについて、t=0 値と t-1 / t-2 / t-5 の差分を集計。
  「t=0 値が切替前から既に同じ値だった」可能性を検証する。
  対象セル:
    - up→dn   pivot_position_100b 1h
    - dn→up   bullish_streak       1d
    - up→rg   bearish_streak       1d
    - up→rg   pivot_position_100b  1h
    - rg→dn   close_to_low_pct     1d
    - dn→rg   close_to_low_pct     1d

【目的2】#6 dn→up close_vs_keltner_upper_pct 4h について、
  代表 datetime を抽出（中央値付近 + 極値）してチャート目視確認用に提示。

出力: results/regime_label_analysis/no_window_drift_audit.md
副作用なし。
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
)

BASE = Path(__file__).parent.parent.parent
DATA_5M = BASE / "data/BTCUSDT-5m-2021-04-01_03-31_1826d.csv"
OUT_DIR = BASE / "results/regime_label_analysis"
OUT_MD = OUT_DIR / "no_window_drift_audit.md"

# 窓なし指標 6セル
NO_WINDOW_CELLS = [
    ("up->dn", "pivot_position_100b", "1h"),
    ("dn->up", "bullish_streak", "1d"),
    ("up->rg", "bearish_streak", "1d"),
    ("up->rg", "pivot_position_100b", "1h"),
    ("rg->dn", "close_to_low_pct", "1d"),
    ("dn->rg", "close_to_low_pct", "1d"),
]

TF_OFFSET = {
    "1h": pd.Timedelta(hours=1),
    "4h": pd.Timedelta(hours=4),
    "1d": pd.Timedelta(days=1),
}
LAGS = [1, 2, 5]


def get_value_at(series: pd.Series, ts: pd.Timestamp) -> float:
    """tz-naive timestamp で series.asof を呼ぶ。"""
    if isinstance(ts, pd.Timestamp) and ts.tzinfo is not None:
        ts = ts.tz_localize(None)
    try:
        return series.asof(ts)
    except KeyError:
        return np.nan


def fmt(x, dec=3):
    if pd.isna(x):
        return "—"
    if abs(x) >= 1000:
        return f"{x:.0f}"
    if abs(x) >= 100:
        return f"{x:.1f}"
    if abs(x) >= 10:
        return f"{x:.2f}"
    return f"{x:.{dec}f}"


def main():
    print("ラベル + 切替点抽出...")
    labels = load_labels()
    runs = run_length_encode(labels["label_norm"].tolist())
    transitions = extract_transitions(runs)
    labels_ts = labels["timestamp_utc"].dt.tz_localize(None).reset_index(drop=True)
    print(f"  切替点数: {len(transitions)}")

    print("OHLCV resample + 指標計算 (1h/4h/1d)...")
    df5m = pd.read_csv(DATA_5M, parse_dates=["timestamp"]).set_index("timestamp").sort_index()
    df1h = resample_ohlcv(df5m, "1h")
    df4h = resample_ohlcv(df5m, "4h")
    df1d = resample_ohlcv(df5m, "1D")
    feats = {
        "1h": build_indicators_extended(df1h),
        "4h": build_indicators_extended(df4h),
        "1d": build_indicators_extended(df1d),
    }

    # === 目的1: 窓なし指標ドリフト ===
    drift_results = []
    for pattern, ind, tf in NO_WINDOW_CELLS:
        prev, cur = pattern.split("->")
        target_tx = [ev for ev in transitions if ev["prev"] == prev and ev["cur"] == cur]
        if not target_tx:
            continue
        feat_df = feats[tf]
        if ind not in feat_df.columns:
            continue
        s = feat_df[ind]
        offset = TF_OFFSET[tf]

        rows_for_cell = []
        for ev in target_tx:
            t = ev["t_idx"]
            t_ts = labels_ts.iloc[t]
            v_t0 = get_value_at(s, t_ts)
            row = {"t_ts": t_ts, "t0": v_t0}
            for lag in LAGS:
                v_lag = get_value_at(s, t_ts - lag * offset)
                row[f"t-{lag}"] = v_lag
                row[f"diff_{lag}"] = (v_t0 - v_lag) if pd.notna(v_t0) and pd.notna(v_lag) else np.nan
            rows_for_cell.append(row)
        df_c = pd.DataFrame(rows_for_cell)
        drift_results.append({
            "pattern": pattern,
            "indicator": ind,
            "tf": tf,
            "n": len(df_c),
            "df": df_c,
        })

    # === 目的2: #6 datetime 抽出 ===
    sample6_pat = "dn->up"
    sample6_ind = "close_vs_keltner_upper_pct"
    sample6_tf = "4h"
    sample6_tx = [ev for ev in transitions if ev["prev"] == "dn" and ev["cur"] == "up"]
    feat6 = feats[sample6_tf]
    s6 = feat6[sample6_ind]
    offset6 = TF_OFFSET[sample6_tf]
    sample6_rows = []
    for ev in sample6_tx:
        t = ev["t_idx"]
        t_ts = labels_ts.iloc[t]
        v_t0 = get_value_at(s6, t_ts)
        v_t_minus_1 = get_value_at(s6, t_ts - 1 * offset6)
        v_t_minus_2 = get_value_at(s6, t_ts - 2 * offset6)
        # 価格情報
        ohlc_t = df4h.asof(t_ts) if t_ts >= df4h.index[0] else None
        sample6_rows.append({
            "t_ts": t_ts,
            "t0_keltner": v_t0,
            "t-1": v_t_minus_1,
            "t-2": v_t_minus_2,
            "close_at_t0": ohlc_t["close"] if ohlc_t is not None else np.nan,
            "prev_len": ev["prev_len"],
            "cur_len": ev["cur_len"],
        })
    df6 = pd.DataFrame(sample6_rows).dropna(subset=["t0_keltner"])

    # === md 出力 ===
    lines = []
    lines.append("# 窓なし指標ドリフト検証 + #6 代表 datetime")
    lines.append("")
    lines.append("段階1-A の B（肉眼確認）追加検証。")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## 目的1: 窓なし指標 6セルのドリフト検証")
    lines.append("")
    lines.append("各セルについて切替点 t=0 値と過去 t-1 / t-2 / t-5 値の差分（cohort 中央値・Q1/Q3）を集計。")
    lines.append("差分の中央値が **小さい** ＝「切替前から既に同じ値だった」可能性高い。")
    lines.append("差分の中央値が **大きい** ＝「切替点で値が変わった」 → 判定材料として価値あり。")
    lines.append("")
    lines.append("| Cell (pattern × ind × tf) | n | t=0 中央値 | t-1 中央値 (Δ vs t0) | t-2 中央値 (Δ vs t0) | t-5 中央値 (Δ vs t0) |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for r in drift_results:
        df_c = r["df"]
        t0_med = df_c["t0"].median()
        tm1_med = df_c["t-1"].median()
        tm2_med = df_c["t-2"].median()
        tm5_med = df_c["t-5"].median()
        d1_med = df_c["diff_1"].median()
        d2_med = df_c["diff_2"].median()
        d5_med = df_c["diff_5"].median()
        d1_q1 = df_c["diff_1"].quantile(0.25)
        d1_q3 = df_c["diff_1"].quantile(0.75)
        d5_q1 = df_c["diff_5"].quantile(0.25)
        d5_q3 = df_c["diff_5"].quantile(0.75)
        lines.append(
            f"| {r['pattern']} × `{r['indicator']}` × {r['tf']} | {r['n']} | "
            f"{fmt(t0_med)} | "
            f"{fmt(tm1_med)} (Δ={fmt(d1_med)}) | "
            f"{fmt(tm2_med)} (Δ={fmt(d2_med)}) | "
            f"{fmt(tm5_med)} (Δ={fmt(d5_med)}) |"
        )
    lines.append("")

    lines.append("### 各セルの差分分布（より詳細）")
    lines.append("")
    for r in drift_results:
        df_c = r["df"]
        lines.append(f"#### {r['pattern']} × `{r['indicator']}` × {r['tf']} (n={r['n']})")
        lines.append("")
        lines.append("| 比較 | Δ 中央値 | Δ Q1 | Δ Q3 | |Δ| 中央値 |")
        lines.append("|---|---:|---:|---:|---:|")
        for lag in LAGS:
            d = df_c[f"diff_{lag}"].dropna()
            abs_d = d.abs()
            lines.append(
                f"| t=0 vs t-{lag} | {fmt(d.median())} | {fmt(d.quantile(0.25))} | {fmt(d.quantile(0.75))} | {fmt(abs_d.median())} |"
            )
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 目的2: #6 dn→up close_vs_keltner_upper_pct 4h 代表 datetime")
    lines.append("")
    lines.append("「slope=-0.31 でまだ下落継続中」という違和感の検証用。実チャートで以下の datetime を確認する。")
    lines.append("")
    lines.append(f"全 dn→up 切替点 n={len(df6)}。t0_keltner の分布:")
    lines.append("")
    lines.append(f"- 中央値: **{fmt(df6['t0_keltner'].median())}**")
    lines.append(f"- Q1: {fmt(df6['t0_keltner'].quantile(0.25))} / Q3: {fmt(df6['t0_keltner'].quantile(0.75))}")
    lines.append(f"- min: {fmt(df6['t0_keltner'].min())} / max: {fmt(df6['t0_keltner'].max())}")
    lines.append("")
    lines.append("### 代表 datetime（中央値付近 3件 + 極値 3件）")
    lines.append("")

    # 中央値付近: median から距離が小さい順
    df6 = df6.copy()
    median_v = df6["t0_keltner"].median()
    df6["dist_to_median"] = (df6["t0_keltner"] - median_v).abs()
    near_median = df6.nsmallest(3, "dist_to_median")
    lowest = df6.nsmallest(3, "t0_keltner")  # 最も下方乖離が大きいもの
    highest = df6.nlargest(3, "t0_keltner")  # 0 に最も近い (=上方ブレイク寄り)

    def sample_table(label, df):
        out = [f"#### {label}", ""]
        out.append("| datetime (UTC) | t0_keltner | t-1 | t-2 | close@t0 | prev_run長 | cur_run長 |")
        out.append("|---|---:|---:|---:|---:|---:|---:|")
        for _, r in df.iterrows():
            ts = r["t_ts"]
            ts_str = ts.strftime("%Y-%m-%d %H:%M") if isinstance(ts, pd.Timestamp) else str(ts)
            out.append(
                f"| {ts_str} | {fmt(r['t0_keltner'])} | {fmt(r['t-1'])} | {fmt(r['t-2'])} | "
                f"{fmt(r['close_at_t0'])} | {int(r['prev_len'])}bar | {int(r['cur_len'])}bar |"
            )
        out.append("")
        return out

    lines.extend(sample_table("中央値付近 3件（最も典型的）", near_median))
    lines.extend(sample_table("極値: 最も下方乖離が大きい 3件（疑念の根本）", lowest))
    lines.extend(sample_table("極値: 最も 0 に近い 3件（上方ブレイク寄り）", highest))

    lines.append("### チャート確認の観点")
    lines.append("")
    lines.append("- 中央値付近: 「dn→up と判断した瞬間」の実際の価格挙動が、Keltner 上限から大きく下方乖離している絵か")
    lines.append("- 最も下方乖離が大きい 3件: dn の最終局面で売り叩かれた後の底打ちか / それとも切替判定が早すぎたケースか")
    lines.append("- 最も 0 に近い 3件: ある程度反発してから dn→up と判定された絵か")
    lines.append("")
    lines.append("### 解釈の選択肢")
    lines.append("")
    lines.append("a. **底打ち根拠として有効**: dn の最終局面で売り叩かれた所を底打ちとして判定 → 採用候補（逆張り根拠）")
    lines.append("b. **メタスコアの罠**: 他5パターンとの相対距離だけで合格しただけで、絶対値としての判定力は薄い → 不採用")
    lines.append("c. **判定が早すぎた事例の混入**: n=63 中で実際にはまだ dn 継続だったケースが混じっている → サブセット分けて再評価")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines))
    print(f"WROTE: {OUT_MD}")


if __name__ == "__main__":
    main()
