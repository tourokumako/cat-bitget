"""analyze_regime_label_features.py — Step 1-1 教師ラベル特徴分析

regime_research.md §13 Step 1 に従い、教師ラベル(up/dn/rg)に対する
各種指標の分布を分析する。

カテゴリ 1〜7 の全指標を 4時間軸 (5m/1h/4h/1d) で計算し、
ラベル別に中央値/四分位を集計して markdown で出力する。

入力:
  - data/regime_samples_4h_*.csv (4ファイル・教師ラベル)
  - data/BTCUSDT-5m-2021-04-01_03-31_1826d.csv (マスター OHLCV)

出力:
  - results/regime_label_analysis/single_indicator_distribution.md
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
import numpy as np
from pathlib import Path
from analyze_vshape_indicators import build_indicators, resample_ohlcv

BASE = Path(__file__).parent.parent.parent
DATA_5M = BASE / "data/BTCUSDT-5m-2021-04-01_03-31_1826d.csv"
LABEL_FILES = [
    BASE / "data/regime_samples_4h_2022.csv",
    BASE / "data/regime_samples_4h_2023.csv",
    BASE / "data/regime_samples_4h_2024.csv",
    BASE / "data/regime_samples_4h.csv",  # 2025
]
OUT_DIR = BASE / "results/regime_label_analysis"
OUT_MD = OUT_DIR / "single_indicator_distribution.md"


# ── 既存 build_indicators + 新規13指標 ───────────────────

def build_indicators_extended(df):
    """既存 build_indicators (約30指標) + 新規13指標。
    時間軸非依存・与えられた df に対して全指標を計算。
    """
    f = build_indicators(df)
    o, h, l, c, v = df["open"], df["high"], df["low"], df["close"], df["volume"]

    # トレンド系: SMA + EMA 乖離率
    f["sma_20"] = c.rolling(20).mean()
    f["sma_50"] = c.rolling(50).mean()
    ema_20 = c.ewm(span=20, adjust=False).mean()
    ema_50 = c.ewm(span=50, adjust=False).mean()
    ema_200 = c.ewm(span=200, adjust=False).mean()
    f["close_vs_sma20_pct"] = (c - f["sma_20"]) / f["sma_20"] * 100
    f["close_vs_sma50_pct"] = (c - f["sma_50"]) / f["sma_50"] * 100
    f["close_vs_ema20_pct"] = (c - ema_20) / ema_20 * 100
    f["close_vs_ema50_pct"] = (c - ema_50) / ema_50 * 100
    f["close_vs_ema200_pct"] = (c - ema_200) / ema_200 * 100

    # トレンド系: Ichimoku
    nine_high = h.rolling(9).max()
    nine_low = l.rolling(9).min()
    f["ichimoku_tenkan"] = (nine_high + nine_low) / 2
    twenty6_high = h.rolling(26).max()
    twenty6_low = l.rolling(26).min()
    f["ichimoku_kijun"] = (twenty6_high + twenty6_low) / 2
    senkou_a = (f["ichimoku_tenkan"] + f["ichimoku_kijun"]) / 2
    fifty2_high = h.rolling(52).max()
    fifty2_low = l.rolling(52).min()
    senkou_b = (fifty2_high + fifty2_low) / 2
    f["close_vs_kijun_pct"] = (c - f["ichimoku_kijun"]) / f["ichimoku_kijun"] * 100
    f["close_above_cloud"] = ((c > senkou_a) & (c > senkou_b)).astype(int)
    f["close_below_cloud"] = ((c < senkou_a) & (c < senkou_b)).astype(int)

    # トレンド系: SuperTrend (近似版・close vs upper/lower band)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr10 = tr.ewm(alpha=1/10, adjust=False).mean()
    hl2 = (h + l) / 2
    f["close_vs_st_upper_pct"] = (c - (hl2 + 3 * atr10)) / c * 100
    f["close_vs_st_lower_pct"] = (c - (hl2 - 3 * atr10)) / c * 100

    # モメンタム系: ROC, CCI
    f["roc_10"] = (c - c.shift(10)) / c.shift(10) * 100
    f["roc_20"] = (c - c.shift(20)) / c.shift(20) * 100
    typical = (h + l + c) / 3
    sma_typical = typical.rolling(20).mean()
    mad = typical.rolling(20).apply(lambda x: np.fabs(x - x.mean()).mean(), raw=True)
    f["cci_20"] = (typical - sma_typical) / (0.015 * mad.replace(0, np.nan))

    # ボラ系: Keltner Channel
    atr_kc = tr.ewm(alpha=1/14, adjust=False).mean()
    keltner_upper = ema_20 + 2 * atr_kc
    keltner_lower = ema_20 - 2 * atr_kc
    f["close_vs_keltner_upper_pct"] = (c - keltner_upper) / keltner_upper * 100
    f["close_vs_keltner_lower_pct"] = (c - keltner_lower) / keltner_lower * 100

    # 出来高系: VWAP, MFI, CMF
    f["vwap_20"] = (typical * v).rolling(20).sum() / v.rolling(20).sum().replace(0, np.nan)
    f["close_vs_vwap20_pct"] = (c - f["vwap_20"]) / f["vwap_20"] * 100
    raw_money_flow = typical * v
    pos_flow = raw_money_flow.where(typical > typical.shift(), 0)
    neg_flow = raw_money_flow.where(typical < typical.shift(), 0)
    pos_sum = pos_flow.rolling(14).sum()
    neg_sum = neg_flow.rolling(14).sum()
    money_ratio = pos_sum / neg_sum.replace(0, np.nan)
    f["mfi_14"] = 100 - (100 / (1 + money_ratio))
    mfm = ((c - l) - (h - c)) / (h - l).replace(0, np.nan)
    mfv = mfm * v
    f["cmf_20"] = mfv.rolling(20).sum() / v.rolling(20).sum().replace(0, np.nan)

    # プライスアクション系: 連続陽線/陰線・ピンバー・包み足
    bullish = (c > o)
    bearish = (c < o)

    def streak(s_bool):
        result = np.zeros(len(s_bool))
        cnt = 0
        for i, val in enumerate(s_bool.values):
            cnt = cnt + 1 if val else 0
            result[i] = cnt
        return pd.Series(result, index=s_bool.index)
    f["bullish_streak"] = streak(bullish)
    f["bearish_streak"] = streak(bearish)
    rng = (h - l).replace(0, np.nan)
    body = (c - o).abs()
    upper_wick = h - c.where(c > o, o)
    lower_wick = c.where(c < o, o) - l
    f["pinbar_top"] = ((upper_wick > 2 * body) & (upper_wick > 2 * lower_wick)).astype(int)
    f["pinbar_bottom"] = ((lower_wick > 2 * body) & (lower_wick > 2 * upper_wick)).astype(int)
    f["bullish_engulfing"] = (
        (c > o) & (o.shift() > c.shift()) & (c >= o.shift()) & (o <= c.shift())
    ).astype(int)
    f["bearish_engulfing"] = (
        (o > c) & (c.shift() > o.shift()) & (o >= c.shift()) & (c <= o.shift())
    ).astype(int)

    # 価格位置系: ピボット位置 (直近 50本の高安に対する現在位置)
    pivot_high50 = h.rolling(50).max()
    pivot_low50 = l.rolling(50).min()
    f["pivot_position_50b"] = (c - pivot_low50) / (pivot_high50 - pivot_low50).replace(0, np.nan)
    pivot_high100 = h.rolling(100).max()
    pivot_low100 = l.rolling(100).min()
    f["pivot_position_100b"] = (c - pivot_low100) / (pivot_high100 - pivot_low100).replace(0, np.nan)

    # ボラ系: Donchian チャネル (20バー高安レンジの幅)
    donchian_high_20 = h.rolling(20).max()
    donchian_low_20 = l.rolling(20).min()
    donchian_denom = (donchian_high_20 - donchian_low_20).replace(0, np.nan)
    f["donchian_width_pct_20"] = (donchian_high_20 - donchian_low_20) / c * 100

    # 価格位置系: Donchian 位置 (高安レンジ内の現在位置 [0,1])
    f["donchian_position_20"] = (c - donchian_low_20) / donchian_denom

    # MTF同調系: 短中長 slope の符号一致度 (単軸内 MTF 模倣)
    ma5 = c.rolling(5).mean()
    ma20 = c.rolling(20).mean()
    ma50 = c.rolling(50).mean()
    slope5 = ma5 - ma5.shift(5)
    slope20 = ma20 - ma20.shift(20)
    slope50 = ma50 - ma50.shift(50)
    sign5 = np.sign(slope5)
    sign20 = np.sign(slope20)
    sign50 = np.sign(slope50)
    align_score = (
        (sign5 == sign20).astype(int)
        + (sign20 == sign50).astype(int)
        + (sign5 == sign50).astype(int)
    ).astype(float)
    nan_mask = slope5.isna() | slope20.isna() | slope50.isna()
    f["mtf_slope_align_3way"] = align_score.where(~nan_mask, np.nan)

    return f


# ── ラベル merge_asof アタッチ ─────────────────────────

def attach_indicators(labels_df, feat_df, ts_col, suffix):
    """labels_df の各 ts_col に対応する feat_df の値を merge_asof で結合"""
    feat = feat_df.reset_index()
    ts_name = feat_df.index.name or "timestamp"
    feat = feat.rename(columns={ts_name: "_ts_join"})
    merged = pd.merge_asof(
        labels_df.sort_values(ts_col),
        feat.sort_values("_ts_join"),
        left_on=ts_col, right_on="_ts_join",
        direction="backward",
    )
    merged = merged.drop(columns=["_ts_join"])
    rename_map = {c: f"{c}__{suffix}" for c in feat_df.columns}
    return merged.rename(columns=rename_map)


# ── 集計 + markdown 出力 ────────────────────────────

def aggregate_by_label(labels):
    indicator_cols = [c for c in labels.columns if c.endswith(("__5m", "__1h", "__4h", "__1d"))]
    rows = []
    for col in indicator_cols:
        for label in ["uptrend", "range", "downtrend"]:
            vals = labels[labels["label"] == label][col].dropna()
            if len(vals) == 0:
                continue
            rows.append({
                "indicator": col,
                "label": label,
                "n": len(vals),
                "median": vals.median(),
                "q1": vals.quantile(0.25),
                "q3": vals.quantile(0.75),
            })
    return pd.DataFrame(rows)


def write_markdown(agg, path, label_totals):
    indicators = sorted(agg["indicator"].unique())
    lines = [
        "# Step 1-1 単独指標分布（ラベル別）",
        "",
        "教師ラベル(up/dn/rg)ごとの各指標の分布。各セル形式: `中央値 [Q1, Q3] (n=有効バー数)`",
        "",
        "**ラベル別 全バー数**:",
        f"- Uptrend: {label_totals.get('uptrend', 0)}",
        f"- Range: {label_totals.get('range', 0)}",
        f"- Downtrend: {label_totals.get('downtrend', 0)}",
        "",
        "各セルの `n` は当該指標で NaN を除いた有効バー数。",
        "全バー数より少ない場合は計算過程で NaN が発生（出来高系で頻発）。",
        "",
        "| Indicator | Uptrend | Range | Downtrend |",
        "|---|---|---|---|",
    ]
    for ind in indicators:
        row = [f"`{ind}`"]
        for label in ["uptrend", "range", "downtrend"]:
            r = agg[(agg["indicator"] == ind) & (agg["label"] == label)]
            if len(r) == 0:
                row.append("-")
                continue
            r = r.iloc[0]
            row.append(f"{r['median']:.3f} [{r['q1']:.3f}, {r['q3']:.3f}] (n={int(r['n'])})")
        lines.append("| " + " | ".join(row) + " |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


# ── メイン ─────────────────────────────────────

def main():
    # 1. 教師ラベル統合
    print("教師ラベル読み込み...")
    label_dfs = [pd.read_csv(p, parse_dates=["timestamp_utc"]) for p in LABEL_FILES]
    labels = pd.concat(label_dfs, ignore_index=True).sort_values("timestamp_utc").reset_index(drop=True)
    labels = labels.dropna(subset=["label"]).reset_index(drop=True)
    print(f"  ラベル付きバー: {len(labels)} (期待 4,745)")
    print(f"  分布: {labels['label'].value_counts().to_dict()}")

    # 2. 5m OHLCV 読み込み + 4時間軸 resample
    print("OHLCV 読み込み + resample...")
    df5m = pd.read_csv(DATA_5M, parse_dates=["timestamp"]).set_index("timestamp").sort_index()
    df1h = resample_ohlcv(df5m, "1h")
    df4h = resample_ohlcv(df5m, "4h")
    df1d = resample_ohlcv(df5m, "1D")
    print(f"  5m={len(df5m)} / 1h={len(df1h)} / 4h={len(df4h)} / 1d={len(df1d)}")

    # 3. 各時間軸で指標計算
    print("指標計算 5m...")
    feat5m = build_indicators_extended(df5m)
    print("指標計算 1h...")
    feat1h = build_indicators_extended(df1h)
    print("指標計算 4h...")
    feat4h = build_indicators_extended(df4h)
    print("指標計算 1d...")
    feat1d = build_indicators_extended(df1d)
    print(f"  指標数: {len(feat5m.columns)}")

    # 4. 教師ラベル timestamp に対し各時間軸の最新値を引く
    # ラベル timestamp は 4hバー開始時刻 → 区間 [t, t+4h) の最終時点を採用
    labels["timestamp_utc"] = labels["timestamp_utc"].dt.tz_localize(None)
    labels["ts_5m"] = labels["timestamp_utc"] + pd.Timedelta(minutes=235)  # 4h - 5min
    labels["ts_1h"] = labels["timestamp_utc"] + pd.Timedelta(hours=3)
    labels["ts_4h"] = labels["timestamp_utc"]
    labels["ts_1d"] = labels["timestamp_utc"].dt.floor("1D")

    print("指標アタッチ...")
    labels = attach_indicators(labels, feat5m, "ts_5m", "5m")
    labels = attach_indicators(labels, feat1h, "ts_1h", "1h")
    labels = attach_indicators(labels, feat4h, "ts_4h", "4h")
    labels = attach_indicators(labels, feat1d, "ts_1d", "1d")
    print(f"  カラム数: {len(labels.columns)}")

    # 5. ラベル別集計
    print("ラベル別集計...")
    agg = aggregate_by_label(labels)
    label_totals = labels["label"].value_counts().to_dict()

    # 6. markdown 出力
    write_markdown(agg, OUT_MD, label_totals)
    print(f"出力: {OUT_MD}")
    print(f"  指標数 × 3ラベル: {len(agg)} 行")


if __name__ == "__main__":
    main()
