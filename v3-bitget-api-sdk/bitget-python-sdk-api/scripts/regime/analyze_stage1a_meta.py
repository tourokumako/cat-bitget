"""analyze_stage1a_meta.py — 段階1-A 着手前のメタ分析

目的: 段階1-A 本実装の N・時間軸・対象指標を「データから」決めるための事前分析。

3つの処理:
  1. 自己相関分析: 各指標 × 各時間軸で lag 1〜24 の自己相関 → 推奨 N 候補
  2. ラベル分離度: 教師ラベル全体での up/rg/dn 間 Q1〜Q3 重複度
  3. パターン特異性: 切替点 198 件の t=0 値で 6遷移パターン間の分離度

各処理で 0.3 / 0.5 / 0.7 の3閾値で感度分析を併記する（先験排除）。

入力:
  - data/regime_samples_4h_*.csv (教師ラベル)
  - data/BTCUSDT-5m-2021-04-01_03-31_1826d.csv (OHLCV)
出力:
  - results/regime_label_analysis/stage1a_meta_analysis.md
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import pandas as pd
import numpy as np

from analyze_regime_label_features import (
    build_indicators_extended,
    attach_indicators,
)
from analyze_vshape_indicators import resample_ohlcv
from analyze_transition_indicators import (
    load_labels,
    run_length_encode,
    extract_transitions,
    attach_all_indicators_dict,
)

BASE = Path(__file__).parent.parent.parent
DATA_5M = BASE / "data/BTCUSDT-5m-2021-04-01_03-31_1826d.csv"
OUT_DIR = BASE / "results/regime_label_analysis"
OUT_MD = OUT_DIR / "stage1a_meta_analysis.md"

TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h", "1d"]
AC_THRESHOLDS = [0.7, 0.5, 0.3]
OVERLAP_THRESHOLDS = [0.3, 0.5, 0.7]
MAX_LAG = 24

# カテゴリ定義（段階1-A 対象指標）
CATEGORIES = {
    "1_trend": [
        "sma_20", "sma_50", "close_vs_sma20_pct", "close_vs_sma50_pct",
        "close_vs_ema20_pct", "close_vs_ema50_pct", "close_vs_ema200_pct",
        "ichimoku_tenkan", "ichimoku_kijun", "close_vs_kijun_pct",
        "close_above_cloud", "close_below_cloud",
        "close_vs_st_upper_pct", "close_vs_st_lower_pct",
        "macd_hist",
        "macd_line", "macd_signal", "macd_hist_change",  # B+A 層追加
    ],
    "2_momentum": [
        "rsi14", "rsi7", "stoch_k", "stoch_d", "williams_r",
        "roc_10", "roc_20", "cci_20",
        "momentum_10b", "div_rsi14_14b", "div_macd_14b",  # A 層追加
    ],
    "3_volatility": [
        "atr14_pct", "bb_pct_b", "bb_width_pct", "bb_width_rank_50b",
        "close_vs_keltner_upper_pct", "close_vs_keltner_lower_pct",
        "realized_vol_20b", "realized_vol_rank_50b",
        "zscore_return_20b", "zscore_return_50b", "abs_return_3sigma_20b",  # A 層追加
        "donchian_width_pct_20",  # C 層追加
    ],
    "4_adx_dmi": [
        "adx14", "di_diff",
        "di_plus", "di_minus",  # B 層追加
    ],
    "5_volume": [
        "volume_rank_50b", "volume_ratio_20b", "obv_slope_10b",
        "close_vs_vwap20_pct", "mfi_14", "cmf_20",
    ],
    "6_priceaction": [
        "bullish_streak", "bearish_streak", "body_ratio",
        "upper_wick_ratio", "lower_wick_ratio",
        "new_high_streak_5b", "new_low_streak_5b",  # A 層追加
        "pinbar_top", "pinbar_bottom",  # A 層追加
        "bullish_engulfing", "bearish_engulfing",  # A 層追加
    ],
    "7_position": [
        "close_to_high_pct", "close_to_low_pct",
        "pivot_position_50b", "pivot_position_100b",
        "donchian_position_20",  # C 層追加
    ],
    "8_mtf": [
        "mtf_slope_align_3way",  # C 層追加 (新カテゴリ)
    ],
}
ALL_INDICATORS = [c for cat in CATEGORIES.values() for c in cat]


# ── 処理 1: 自己相関 ──────────────────────────────────

def autocorrelation_analysis(features_per_tf: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """指標 × 時間軸 × lag の自己相関を返す。"""
    rows = []
    for tf, feat in features_per_tf.items():
        for ind in ALL_INDICATORS:
            if ind not in feat.columns:
                continue
            s = feat[ind].dropna()
            if len(s) < MAX_LAG * 2:
                continue
            row = {"indicator": ind, "tf": tf}
            for lag in [1, 3, 6, 12, 24]:
                row[f"ac_lag{lag}"] = s.autocorr(lag=lag)
            for thr in AC_THRESHOLDS:
                first_below = None
                for lag in range(1, MAX_LAG + 1):
                    val = s.autocorr(lag=lag)
                    if pd.notna(val) and abs(val) < thr:
                        first_below = lag
                        break
                row[f"first_below_{thr}"] = first_below
            rows.append(row)
    return pd.DataFrame(rows)


# ── 処理 2: ラベル分離度（t=0 単点・全教師ラベル） ──────────────

def overlap_3way(values_by_label: dict[str, pd.Series]) -> dict:
    """3ラベルの (Q1, Q3) IQR の重複度を計算。"""
    quartiles = {}
    for lbl, s in values_by_label.items():
        if len(s) < 10:
            quartiles[lbl] = (np.nan, np.nan)
        else:
            quartiles[lbl] = (s.quantile(0.25), s.quantile(0.75))
    qs = list(quartiles.values())
    if any(pd.isna(q[0]) or pd.isna(q[1]) for q in qs):
        return {"overlap_ratio": np.nan, **quartiles}
    q1_max = max(q[0] for q in qs)
    q3_min = min(q[1] for q in qs)
    intersection = max(0.0, q3_min - q1_max)
    q3_max = max(q[1] for q in qs)
    q1_min = min(q[0] for q in qs)
    union = q3_max - q1_min
    if union <= 0:
        ratio = 1.0
    else:
        ratio = intersection / union
    return {"overlap_ratio": ratio, **quartiles}


def label_separation_analysis(labels_attached: pd.DataFrame) -> pd.DataFrame:
    """教師ラベル単位で 3ラベル間 IQR 重複度を全 (指標 × 時間軸) で計算。"""
    rows = []
    for ind in ALL_INDICATORS:
        for tf in TIMEFRAMES:
            col = f"{ind}__{tf}"
            if col not in labels_attached.columns:
                continue
            by_label = {
                "up": labels_attached[labels_attached["label_norm"] == "up"][col].dropna(),
                "rg": labels_attached[labels_attached["label_norm"] == "rg"][col].dropna(),
                "dn": labels_attached[labels_attached["label_norm"] == "dn"][col].dropna(),
            }
            res = overlap_3way(by_label)
            rows.append({
                "indicator": ind,
                "tf": tf,
                "overlap_ratio": res["overlap_ratio"],
                "up_q1": res.get("up", (np.nan, np.nan))[0],
                "up_q3": res.get("up", (np.nan, np.nan))[1],
                "rg_q1": res.get("rg", (np.nan, np.nan))[0],
                "rg_q3": res.get("rg", (np.nan, np.nan))[1],
                "dn_q1": res.get("dn", (np.nan, np.nan))[0],
                "dn_q3": res.get("dn", (np.nan, np.nan))[1],
            })
    return pd.DataFrame(rows)


# ── 処理 3: パターン特異性（t=0 単点・切替点 198） ───────────

def overlap_pair(s1: pd.Series, s2: pd.Series) -> float:
    if len(s1) < 5 or len(s2) < 5:
        return np.nan
    a1, a3 = s1.quantile(0.25), s1.quantile(0.75)
    b1, b3 = s2.quantile(0.25), s2.quantile(0.75)
    if any(pd.isna(x) for x in [a1, a3, b1, b3]):
        return np.nan
    inter = max(0.0, min(a3, b3) - max(a1, b1))
    union = max(a3, b3) - min(a1, b1)
    if union <= 0:
        return 1.0
    return inter / union


def pattern_specificity_analysis(labels_attached: pd.DataFrame, transitions: list) -> pd.DataFrame:
    """切替点 t=0 値で 6遷移パターン間の Q1〜Q3 重複度を測る。"""
    pattern_rows = []
    for ev in transitions:
        t = ev["t_idx"]
        row = {
            "pattern": f"{ev['prev']}->{ev['cur']}",
            **{c: labels_attached.iloc[t][c] for c in labels_attached.columns
               if c.endswith(tuple(f"__{tf}" for tf in TIMEFRAMES))},
        }
        pattern_rows.append(row)
    df = pd.DataFrame(pattern_rows)

    patterns = ["up->dn", "dn->up", "up->rg", "rg->up", "rg->dn", "dn->rg"]
    rows = []
    for ind in ALL_INDICATORS:
        for tf in TIMEFRAMES:
            col = f"{ind}__{tf}"
            if col not in df.columns:
                continue
            by_pattern = {p: df[df["pattern"] == p][col].dropna() for p in patterns}
            for target in patterns:
                others = [s for p, s in by_pattern.items() if p != target]
                if len(by_pattern[target]) < 5:
                    continue
                overlaps = [overlap_pair(by_pattern[target], o) for o in others]
                overlaps = [o for o in overlaps if pd.notna(o)]
                if not overlaps:
                    continue
                rows.append({
                    "pattern": target,
                    "indicator": ind,
                    "tf": tf,
                    "n": len(by_pattern[target]),
                    "mean_overlap_vs_others": float(np.mean(overlaps)),
                    "max_overlap_vs_others": float(np.max(overlaps)),
                    "min_overlap_vs_others": float(np.min(overlaps)),
                })
    return pd.DataFrame(rows)


# ── md 出力 ───────────────────────────────────────

def fmt(x, decimals=3):
    if pd.isna(x):
        return "—"
    if isinstance(x, (int, np.integer)):
        return str(x)
    if abs(x) >= 100:
        return f"{x:.1f}"
    if abs(x) >= 10:
        return f"{x:.2f}"
    return f"{x:.{decimals}f}"


def write_md(ac_df: pd.DataFrame, sep_df: pd.DataFrame, spec_df: pd.DataFrame, out_path: Path):
    lines = []
    lines.append("# 段階1-A メタ分析: N・時間軸・対象指標をデータから決める")
    lines.append("")
    lines.append("段階1-A 本実装の前に、以下 3点をデータで決めるための事前分析。")
    lines.append("- N（過去バー数）: 自己相関で独立観測窓を測る")
    lines.append("- 時間軸: ラベル分離度で軸別の判定力を測る")
    lines.append("- 対象指標: ラベル分離度 + パターン特異性で絞る")
    lines.append("")
    lines.append("各処理で複数閾値の感度分析を併記。**閾値選択はまこさんが見て判断する**。")
    lines.append("")
    lines.append("---")
    lines.append("")

    # === 処理 1: 自己相関 ===
    lines.append("## 処理 1: 自己相関分析（N の根拠）")
    lines.append("")
    lines.append(f"各指標 × 各時間軸で lag 1〜{MAX_LAG} の Pearson 自己相関を計算。")
    lines.append("「自己相関が閾値を初めて切る lag」を **推奨 N 候補** とする。")
    lines.append("")
    lines.append("### 1-A. 全指標 × 全時間軸 × 主要 lag の自己相関")
    lines.append("")
    lines.append("| Indicator | TF | lag1 | lag3 | lag6 | lag12 | lag24 | first<0.7 | first<0.5 | first<0.3 |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for cat_id, cat_inds in CATEGORIES.items():
        for ind in cat_inds:
            for tf in TIMEFRAMES:
                r = ac_df[(ac_df["indicator"] == ind) & (ac_df["tf"] == tf)]
                if r.empty:
                    continue
                row = r.iloc[0]
                lines.append(
                    f"| `{ind}` | {tf} | "
                    f"{fmt(row['ac_lag1'])} | {fmt(row['ac_lag3'])} | {fmt(row['ac_lag6'])} | "
                    f"{fmt(row['ac_lag12'])} | {fmt(row['ac_lag24'])} | "
                    f"{fmt(row['first_below_0.7'])} | {fmt(row['first_below_0.5'])} | "
                    f"{fmt(row['first_below_0.3'])} |"
                )
    lines.append("")

    lines.append("### 1-B. 時間軸別の N 推奨値（first<0.5 切り lag の中央値）")
    lines.append("")
    lines.append("| TF | カテゴリ | first<0.7 中央値 | first<0.5 中央値 | first<0.3 中央値 |")
    lines.append("|---|---|---:|---:|---:|")
    for tf in TIMEFRAMES:
        for cat_id, cat_inds in CATEGORIES.items():
            sub = ac_df[(ac_df["tf"] == tf) & (ac_df["indicator"].isin(cat_inds))]
            if sub.empty:
                continue
            lines.append(
                f"| {tf} | {cat_id} | "
                f"{fmt(sub['first_below_0.7'].median())} | "
                f"{fmt(sub['first_below_0.5'].median())} | "
                f"{fmt(sub['first_below_0.3'].median())} |"
            )
    lines.append("")
    lines.append("**読み方**: 「first<0.5」中央値が 6 なら、その軸/カテゴリでは過去 6 bar 取れば独立な情報が得られる。")
    lines.append("")
    lines.append("---")
    lines.append("")

    # === 処理 2: ラベル分離度 ===
    lines.append("## 処理 2: ラベル分離度（時間軸・指標選定の根拠）")
    lines.append("")
    lines.append("教師ラベル全 4,745 バー（4h）の up/rg/dn 別 Q1〜Q3 IQR の重複度。")
    lines.append("**重複度 = 3ラベル IQR の積集合幅 / 合集合幅**。0=完全分離 / 1=完全重複。")
    lines.append("")
    lines.append("### 2-A. 重複度ランキング（小さい=分離が鋭い・上位 30）")
    lines.append("")
    lines.append("| Rank | Indicator | TF | overlap | up Q1〜Q3 | rg Q1〜Q3 | dn Q1〜Q3 |")
    lines.append("|---:|---|---|---:|---|---|---|")
    sep_sorted = sep_df.dropna(subset=["overlap_ratio"]).sort_values("overlap_ratio").reset_index(drop=True)
    for i, r in sep_sorted.head(30).iterrows():
        lines.append(
            f"| {i+1} | `{r['indicator']}` | {r['tf']} | {fmt(r['overlap_ratio'])} | "
            f"[{fmt(r['up_q1'])}, {fmt(r['up_q3'])}] | "
            f"[{fmt(r['rg_q1'])}, {fmt(r['rg_q3'])}] | "
            f"[{fmt(r['dn_q1'])}, {fmt(r['dn_q3'])}] |"
        )
    lines.append("")

    lines.append("### 2-B. 重複度閾値別 合格指標数（感度分析）")
    lines.append("")
    lines.append("| 重複度閾値 | 合格 (指標×軸) | 全体に占める割合 |")
    lines.append("|---|---:|---:|")
    total_sep = sep_df["overlap_ratio"].notna().sum()
    for thr in OVERLAP_THRESHOLDS:
        n = (sep_df["overlap_ratio"] < thr).sum()
        lines.append(f"| < {thr} | {n} | {n / total_sep * 100:.1f}% |")
    lines.append("")

    lines.append("### 2-C. 時間軸別 合格指標数（重複度 < 0.5 基準）")
    lines.append("")
    lines.append("| TF | 合格指標数 | 全体（指標数） |")
    lines.append("|---|---:|---:|")
    for tf in TIMEFRAMES:
        sub = sep_df[sep_df["tf"] == tf]
        n_pass = (sub["overlap_ratio"] < 0.5).sum()
        n_total = sub["overlap_ratio"].notna().sum()
        lines.append(f"| {tf} | {n_pass} | {n_total} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # === 処理 3: パターン特異性 ===
    lines.append("## 処理 3: パターン特異性（t=0 単点・切替点 198 件）")
    lines.append("")
    lines.append("各遷移パターン (n=15-63) の t=0 値が、他 5 パターンと比べてどれだけ離れているか。")
    lines.append("**mean_overlap_vs_others** = 自パターン IQR と 他5パターン IQR の重複度の平均。")
    lines.append("小さい = そのパターン特有の値帯にある = 判定材料になりうる。")
    lines.append("")
    lines.append("### 3-A. 各パターンで mean_overlap が小さい指標 top 5")
    lines.append("")
    patterns = ["up->dn", "dn->up", "up->rg", "rg->up", "rg->dn", "dn->rg"]
    for p in patterns:
        sub = spec_df[spec_df["pattern"] == p].dropna(subset=["mean_overlap_vs_others"])
        sub = sub.sort_values("mean_overlap_vs_others")
        lines.append(f"#### {p} (n={int(sub['n'].iloc[0]) if len(sub)>0 else 0})")
        lines.append("")
        lines.append("| Rank | Indicator | TF | mean_overlap | min_overlap | max_overlap |")
        lines.append("|---:|---|---|---:|---:|---:|")
        for i, r in sub.head(5).iterrows():
            lines.append(
                f"| {i+1} | `{r['indicator']}` | {r['tf']} | "
                f"{fmt(r['mean_overlap_vs_others'])} | "
                f"{fmt(r['min_overlap_vs_others'])} | "
                f"{fmt(r['max_overlap_vs_others'])} |"
            )
        lines.append("")

    lines.append("### 3-B. 重複度閾値別 合格 (パターン × 指標 × 軸) 数")
    lines.append("")
    lines.append("| mean_overlap 閾値 | 合格件数 |")
    lines.append("|---|---:|")
    total_spec = spec_df["mean_overlap_vs_others"].notna().sum()
    for thr in OVERLAP_THRESHOLDS:
        n = (spec_df["mean_overlap_vs_others"] < thr).sum()
        lines.append(f"| < {thr} | {n} ({n / total_spec * 100:.1f}%) |")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## まこさんが決めるべきこと")
    lines.append("")
    lines.append("1. **N の閾値**: 自己相関 0.3 / 0.5 / 0.7 のどれを「独立観測窓」基準にするか")
    lines.append("2. **重複度の閾値**: ラベル分離度 / パターン特異性で 0.3 / 0.5 / 0.7 のどれを合格ラインにするか")
    lines.append("3. **対象軸**: 処理 2-C を見て 5m/1h/4h/1d のどれに絞るか（あるいは全て使うか）")
    lines.append("4. **対象指標**: 処理 2-A + 処理 3-A を見て段階1-A の対象指標を決める")
    lines.append("")
    lines.append("これらが決まれば段階1-A 本実装の対象が確定する。")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))


# ── メイン ─────────────────────────────────────

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

    print("指標計算...")
    features_per_tf = {tf: build_indicators_extended(all_dfs[tf]) for tf in TIMEFRAMES if tf in all_dfs}

    print("attach...")
    labels_attached = attach_all_indicators_dict(labels, features_per_tf)

    print("処理 1: 自己相関分析...")
    ac_df = autocorrelation_analysis(features_per_tf)
    print(f"  行数: {len(ac_df)}")

    print("処理 2: ラベル分離度...")
    sep_df = label_separation_analysis(labels_attached)
    print(f"  行数: {len(sep_df)}")

    print("処理 3: パターン特異性...")
    spec_df = pattern_specificity_analysis(labels_attached, transitions)
    print(f"  行数: {len(spec_df)}")

    print(f"md 出力: {OUT_MD}")
    write_md(ac_df, sep_df, spec_df, OUT_MD)
    print("DONE")


if __name__ == "__main__":
    main()
