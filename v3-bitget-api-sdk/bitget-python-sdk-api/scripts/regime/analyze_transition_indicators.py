"""analyze_transition_indicators.py — Step 1 メイン: 切替点前後の指標挙動分析

教師ラベル(4h)の直接遷移点について、前後 24h ウィンドウの指標分布を集計する。

対象遷移パターン: up↔dn, up↔rg, rg↔dn の 6 種（同ラベル復帰・blank 跨ぎは除外）
サブセット: 全 / 短命前run (up≤4bar / rg≤6bar / dn≤4bar) / 通常前run (それより長い)
時間軸: 5m / 1h / 4h / 1d
集計: 切替点ごとに前24h中央値・t=0値・後24h中央値を算出 → コホート中央値

出力: results/regime_label_analysis/transition_indicator_main.md
副作用なし（ラベル/OHLCV読むだけ・結果は md のみ）
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

BASE = Path(__file__).parent.parent.parent
DATA_5M = BASE / "data/BTCUSDT-5m-2021-04-01_03-31_1826d.csv"
LABEL_FILES = [
    BASE / "data/regime_samples_4h_2022.csv",
    BASE / "data/regime_samples_4h_2023.csv",
    BASE / "data/regime_samples_4h_2024.csv",
    BASE / "data/regime_samples_4h.csv",
]
OUT_DIR = BASE / "results/regime_label_analysis"
OUT_MD = OUT_DIR / "transition_indicator_main.md"

WINDOW_BARS = 6  # 24h / 4h-bar
SHORT_THRESHOLD = {"up": 4, "rg": 6, "dn": 4}
LABEL_NORMALIZE = {"uptrend": "up", "range": "rg", "downtrend": "dn"}

PATTERNS = [
    ("up", "dn"),
    ("dn", "up"),
    ("up", "rg"),
    ("rg", "up"),
    ("rg", "dn"),
    ("dn", "rg"),
]

# カテゴリ定義（既存 single_indicator_distribution.md の指標を分類）
CATEGORIES = {
    "1_trend": [
        "sma_20", "sma_50", "close_vs_sma20_pct", "close_vs_sma50_pct",
        "close_vs_ema20_pct", "close_vs_ema50_pct", "close_vs_ema200_pct",
        "ichimoku_tenkan", "ichimoku_kijun", "close_vs_kijun_pct",
        "close_above_cloud", "close_below_cloud",
        "close_vs_st_upper_pct", "close_vs_st_lower_pct",
        "macd_hist", "macd_hist_change",
    ],
    "2_momentum": [
        "rsi14", "rsi7", "stoch_k", "stoch_d", "williams_r",
        "roc_10", "roc_20", "cci_20", "momentum_10b",
    ],
    "3_volatility": [
        "atr14_pct", "bb_pct_b", "bb_width_pct", "bb_width_rank_50b",
        "close_vs_keltner_upper_pct", "close_vs_keltner_lower_pct",
        "realized_vol_20b", "realized_vol_rank_50b", "abs_return_3sigma_20b",
    ],
    "4_adx_dmi": ["adx14", "di_diff"],
    "5_volume": [
        "volume_rank_50b", "volume_ratio_20b", "obv_slope_10b",
        "vwap_20", "close_vs_vwap20_pct", "mfi_14", "cmf_20",
    ],
    "6_priceaction": [
        "bullish_streak", "bearish_streak", "body_ratio",
        "upper_wick_ratio", "lower_wick_ratio",
        "pinbar_top", "pinbar_bottom",
        "bullish_engulfing", "bearish_engulfing",
        "new_high_streak_5b", "new_low_streak_5b",
    ],
    "7_position": [
        "close_to_high_pct", "close_to_low_pct",
        "pivot_position_50b", "pivot_position_100b",
    ],
    "8_misc": [
        "zscore_return_20b", "zscore_return_50b",
        "div_macd_14b", "div_rsi14_14b",
    ],
}
CATEGORY_NAMES = {
    "1_trend": "トレンド系",
    "2_momentum": "モメンタム系",
    "3_volatility": "ボラティリティ系",
    "4_adx_dmi": "方向性強度系 (ADX/DMI)",
    "5_volume": "出来高系",
    "6_priceaction": "プライスアクション系",
    "7_position": "価格位置系",
    "8_misc": "その他（参考）",
}
TIMEFRAMES = ["5m", "1h", "4h", "1d"]


def load_labels() -> pd.DataFrame:
    frames = []
    for p in LABEL_FILES:
        df = pd.read_csv(p, parse_dates=["timestamp_utc"])
        frames.append(df)
    out = pd.concat(frames, ignore_index=True).sort_values("timestamp_utc").reset_index(drop=True)
    out["timestamp_utc"] = out["timestamp_utc"].dt.tz_localize(None)
    out["label_raw"] = out["label"].fillna("").astype(str).str.strip()
    out["label_norm"] = out["label_raw"].map(
        lambda x: LABEL_NORMALIZE.get(x, x) if x else "blank"
    )
    return out


def run_length_encode(labels: list[str]) -> list[tuple[str, int, int, int]]:
    runs = []
    if not labels:
        return runs
    cur, start = labels[0], 0
    for i in range(1, len(labels)):
        if labels[i] != cur:
            runs.append((cur, start, i - 1, i - start))
            cur = labels[i]
            start = i
    runs.append((cur, start, len(labels) - 1, len(labels) - start))
    return runs


def extract_transitions(runs):
    """直接切替点を抽出。
    返り値: list of dict(prev, cur, prev_len, cur_len, t_idx, prev_start, cur_end, subset)
    subset: "short" if prev_len <= SHORT_THRESHOLD[prev] else "normal"
    """
    out = []
    for i in range(1, len(runs)):
        prev_label, prev_start, prev_end, prev_len = runs[i - 1]
        cur_label, cur_start, cur_end, cur_len = runs[i]
        if prev_label in ("blank",) or cur_label in ("blank",):
            continue
        if prev_label == cur_label:
            continue
        thr = SHORT_THRESHOLD.get(prev_label, 99)
        subset = "short" if prev_len <= thr else "normal"
        out.append({
            "prev": prev_label,
            "cur": cur_label,
            "prev_len": prev_len,
            "cur_len": cur_len,
            "t_idx": cur_start,
            "prev_start": prev_start,
            "prev_end": prev_end,
            "cur_end": cur_end,
            "subset": subset,
        })
    return out


def attach_all_indicators(labels_df, feat5m, feat1h, feat4h, feat1d):
    """labels_df の timestamp_utc に対し、4軸指標を merge_asof で結合。"""
    labels_df = labels_df.copy()
    labels_df["ts_5m"] = labels_df["timestamp_utc"] + pd.Timedelta(minutes=235)
    labels_df["ts_1h"] = labels_df["timestamp_utc"] + pd.Timedelta(hours=3)
    labels_df["ts_4h"] = labels_df["timestamp_utc"]
    labels_df["ts_1d"] = labels_df["timestamp_utc"].dt.floor("1D")
    labels_df = attach_indicators(labels_df, feat5m, "ts_5m", "5m")
    labels_df = attach_indicators(labels_df, feat1h, "ts_1h", "1h")
    labels_df = attach_indicators(labels_df, feat4h, "ts_4h", "4h")
    labels_df = attach_indicators(labels_df, feat1d, "ts_1d", "1d")
    return labels_df


def per_event_window_medians(labels_df, transitions, indicator_cols):
    """各切替点について「前24h中央値・t=0値・後24h中央値」を算出。
    返り値: list[dict] 各切替点 × 各指標カラムの3値。
    """
    rows = []
    n_bars = len(labels_df)
    for ev in transitions:
        t = ev["t_idx"]
        pre_lo = max(ev["prev_start"], t - WINDOW_BARS)
        pre_hi = t  # exclusive
        post_lo = t  # inclusive
        post_hi = min(ev["cur_end"] + 1, t + WINDOW_BARS)
        if pre_lo >= pre_hi or post_lo >= post_hi:
            continue
        pre_block = labels_df.iloc[pre_lo:pre_hi]
        t0_block = labels_df.iloc[t:t + 1]
        post_block = labels_df.iloc[post_lo:post_hi]
        for col in indicator_cols:
            pre_v = pre_block[col].median(skipna=True)
            t0_v = t0_block[col].iloc[0] if col in t0_block.columns else np.nan
            post_v = post_block[col].median(skipna=True)
            rows.append({
                "pattern": f"{ev['prev']}->{ev['cur']}",
                "subset": ev["subset"],
                "indicator": col,
                "pre_median": pre_v,
                "t0_value": t0_v,
                "post_median": post_v,
                "delta": (post_v - pre_v) if pd.notna(pre_v) and pd.notna(post_v) else np.nan,
            })
    return pd.DataFrame(rows)


def cohort_aggregate(per_event_df):
    """切替点コホートごとに各指標の median を取る → 表に展開可能な形に。"""
    if per_event_df.empty:
        return pd.DataFrame()
    grp = per_event_df.groupby(["pattern", "subset", "indicator"]).agg(
        n=("pre_median", lambda x: x.notna().sum()),
        pre_median=("pre_median", "median"),
        t0_value=("t0_value", "median"),
        post_median=("post_median", "median"),
        delta=("delta", "median"),
    ).reset_index()
    return grp


def fmt_number(x):
    if pd.isna(x):
        return "—"
    if abs(x) >= 1000:
        return f"{x:.0f}"
    if abs(x) >= 10:
        return f"{x:.2f}"
    return f"{x:.3f}"


def write_md(per_event_df, cohort_df, transition_counts, out_path):
    lines = []
    lines.append("# Step 1 メイン: 切替点前後の指標挙動")
    lines.append("")
    lines.append("教師ラベル(4h)の直接切替点について、前後 24h ウィンドウの指標挙動を集計。")
    lines.append("")
    lines.append("## 設計（v2）")
    lines.append("")
    lines.append("- **切替点 t=0**: 後 run の冒頭バー（4h バー）")
    lines.append("- **前ウィンドウ**: t-6 〜 t-1（24h・4h×6 bar・前 run が短い場合は短縮）")
    lines.append("- **後ウィンドウ**: t+0 〜 t+5（24h・後 run が短い場合は短縮）")
    lines.append("- **集計**: 各切替点で per-event 中央値 → コホート中央値の二段集計")
    lines.append("- **対象**: 直接切替（隣接 run が非blank・異ラベル）のみ。同ラベル復帰・blank 跨ぎは除外")
    lines.append(f"- **短命/通常閾値**: up≤{SHORT_THRESHOLD['up']}bar / rg≤{SHORT_THRESHOLD['rg']}bar / dn≤{SHORT_THRESHOLD['dn']}bar（前 run 長で判定）")
    lines.append("")

    lines.append("## 全体サマリ: 切替点件数")
    lines.append("")
    lines.append("| pattern | total | short (前run短命) | normal (前run通常) |")
    lines.append("|---|---:|---:|---:|")
    for prev, cur in PATTERNS:
        key = f"{prev}->{cur}"
        tot = transition_counts.get((key, "all"), 0)
        sh = transition_counts.get((key, "short"), 0)
        no = transition_counts.get((key, "normal"), 0)
        lines.append(f"| {prev} → {cur} | {tot} | {sh} | {no} |")
    lines.append("")

    lines.append("各セル: `pre / t0 / post (Δ=post-pre)`")
    lines.append("")

    for cat_id, cat_name in CATEGORY_NAMES.items():
        lines.append(f"## カテゴリ {cat_id.split('_')[0]}: {cat_name}")
        lines.append("")
        bases = CATEGORIES.get(cat_id, [])
        if not bases:
            lines.append("(対象指標なし)")
            continue

        for prev, cur in PATTERNS:
            key = f"{prev}->{cur}"
            lines.append(f"### {prev} → {cur}")
            lines.append("")

            for subset_label, subset_jp in [("all", "全"), ("short", "短命前run"), ("normal", "通常前run")]:
                if subset_label == "all":
                    sub = cohort_df[cohort_df["pattern"] == key]
                else:
                    sub = cohort_df[(cohort_df["pattern"] == key) & (cohort_df["subset"] == subset_label)]
                n = transition_counts.get((key, subset_label), 0)
                lines.append(f"#### {subset_jp} (n={n})")
                lines.append("")
                if n == 0:
                    lines.append("(切替点なし)")
                    lines.append("")
                    continue

                # 軸ヘッダ作成
                header = ["Indicator"] + [f"{tf}: pre / t0 / post (Δ)" for tf in TIMEFRAMES]
                lines.append("| " + " | ".join(header) + " |")
                lines.append("|" + "|".join(["---"] * len(header)) + "|")
                for base in bases:
                    row = [f"`{base}`"]
                    for tf in TIMEFRAMES:
                        col = f"{base}__{tf}"
                        cell = sub[sub["indicator"] == col]
                        if subset_label == "all" and not cell.empty:
                            # all は subsetをまとめて再計算する: per_event_df を再集計
                            ev_sub = per_event_df[(per_event_df["pattern"] == key) & (per_event_df["indicator"] == col)]
                            if ev_sub.empty:
                                row.append("—")
                                continue
                            pre = ev_sub["pre_median"].median()
                            t0 = ev_sub["t0_value"].median()
                            post = ev_sub["post_median"].median()
                            d = post - pre if pd.notna(pre) and pd.notna(post) else np.nan
                            row.append(f"{fmt_number(pre)} / {fmt_number(t0)} / {fmt_number(post)} ({fmt_number(d)})")
                        elif cell.empty:
                            row.append("—")
                        else:
                            r = cell.iloc[0]
                            row.append(
                                f"{fmt_number(r['pre_median'])} / {fmt_number(r['t0_value'])} / "
                                f"{fmt_number(r['post_median'])} ({fmt_number(r['delta'])})"
                            )
                    lines.append("| " + " | ".join(row) + " |")
                lines.append("")
        lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))


def main():
    print("教師ラベル読み込み...")
    labels = load_labels()
    print(f"  全 4h バー: {len(labels)}")
    print(f"  ラベル分布: {labels['label_norm'].value_counts().to_dict()}")

    print("run-length encoding...")
    runs = run_length_encode(labels["label_norm"].tolist())
    print(f"  run 数: {len(runs)}")

    print("直接切替点抽出...")
    transitions = extract_transitions(runs)
    print(f"  切替点数: {len(transitions)}")

    # サマリカウント
    transition_counts = {}
    for ev in transitions:
        key = f"{ev['prev']}->{ev['cur']}"
        transition_counts[(key, "all")] = transition_counts.get((key, "all"), 0) + 1
        transition_counts[(key, ev["subset"])] = transition_counts.get((key, ev["subset"]), 0) + 1
    print("  パターン件数:")
    for prev, cur in PATTERNS:
        k = f"{prev}->{cur}"
        print(f"    {k}: total={transition_counts.get((k,'all'),0)} short={transition_counts.get((k,'short'),0)} normal={transition_counts.get((k,'normal'),0)}")

    print("OHLCV 読み込み + resample...")
    df5m = pd.read_csv(DATA_5M, parse_dates=["timestamp"]).set_index("timestamp").sort_index()
    df1h = resample_ohlcv(df5m, "1h")
    df4h = resample_ohlcv(df5m, "4h")
    df1d = resample_ohlcv(df5m, "1D")

    print("指標計算 (4軸)...")
    feat5m = build_indicators_extended(df5m)
    feat1h = build_indicators_extended(df1h)
    feat4h = build_indicators_extended(df4h)
    feat1d = build_indicators_extended(df1d)
    print(f"  カラム数: 5m={len(feat5m.columns)}")

    print("ラベルバーへ指標 attach...")
    labels_attached = attach_all_indicators(labels, feat5m, feat1h, feat4h, feat1d)
    indicator_cols = [c for c in labels_attached.columns if c.endswith(("__5m", "__1h", "__4h", "__1d"))]
    print(f"  指標カラム数: {len(indicator_cols)}")

    print("per-event ウィンドウ集計...")
    per_event_df = per_event_window_medians(labels_attached, transitions, indicator_cols)
    print(f"  per-event 行数: {len(per_event_df)}")

    print("コホート集計...")
    cohort_df = cohort_aggregate(per_event_df)
    print(f"  コホート行数: {len(cohort_df)}")

    print(f"md 出力: {OUT_MD}")
    write_md(per_event_df, cohort_df, transition_counts, OUT_MD)
    print("DONE")


if __name__ == "__main__":
    main()
