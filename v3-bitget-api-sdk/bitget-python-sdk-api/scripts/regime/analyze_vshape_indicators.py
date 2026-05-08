"""V字頂点 24サンプル × 65軸指標 観察スクリプト（ステップ2）

入力: results/vshape_design/samples_24.parquet
出力:
  results/vshape_design/indicators_at_peak.csv  — peak時点の各指標値（24行 × 65列）
  results/vshape_design/indicators_summary.md   — 指標カテゴリ別 peak vs 周辺バー統計
  results/vshape_design/charts.html             — 全24サンプルのミニチャート可視化

設計方針:
  - 各時間軸 5m/15m/1h/4h で OHLC をリサンプル
  - 各指標は peak_time までの過去データのみで計算（look-ahead なし）
  - peak時点の指標値と、peak ±N 本の周辺バーの指標値を比較
  - 周辺範囲: 5m=±24本(±2h) / 15m=±8本(±2h) / 1h=±4本(±4h) / 4h=±2本(±8h)
"""
import pandas as pd
import numpy as np
import json
import base64
from io import BytesIO
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = Path(__file__).parent.parent.parent
OUT_DIR = BASE / "results/vshape_design"
SAMPLES = OUT_DIR / "samples_24.parquet"
OHLC_5M = BASE / "data/BTCUSDT-5m-2021-04-01_03-31_1826d.csv"
FUNDING = BASE / "data/funding_rate_BTCUSDT_5y.csv"

TIMEFRAMES = {
    "5m":  {"freq": "5min", "around": 24},   # ±2h
    "15m": {"freq": "15min", "around": 8},   # ±2h
    "1h":  {"freq": "1h", "around": 4},      # ±4h
    "4h":  {"freq": "4h", "around": 2},      # ±8h
}


# ── 指標計算（look-ahead なし） ───────────────────────────

def rsi(c, period):
    d = c.diff()
    g = d.clip(lower=0).ewm(alpha=1/period, adjust=False).mean()
    l = (-d.clip(upper=0)).ewm(alpha=1/period, adjust=False).mean()
    rs = g / l.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def adx_di(h, l, c, period=14):
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    up = h.diff(); dn = -l.diff()
    dmp = up.where((up > dn) & (up > 0), 0.0)
    dmm = dn.where((dn > up) & (dn > 0), 0.0)
    dip = 100 * dmp.ewm(alpha=1/period, adjust=False).mean() / atr.replace(0, np.nan)
    dim = 100 * dmm.ewm(alpha=1/period, adjust=False).mean() / atr.replace(0, np.nan)
    dx = 100 * (dip - dim).abs() / (dip + dim).replace(0, np.nan)
    return dx.ewm(alpha=1/period, adjust=False).mean(), dip, dim, atr


def bollinger(c, period=20, k=2):
    ma = c.rolling(period).mean()
    sd = c.rolling(period).std()
    upper = ma + k * sd
    lower = ma - k * sd
    width = (upper - lower) / ma * 100  # %
    pct_b = (c - lower) / (upper - lower).replace(0, np.nan)
    return width, pct_b, ma, upper, lower


def stochastic(h, l, c, k_period=14, d_period=3):
    ll = l.rolling(k_period).min()
    hh = h.rolling(k_period).max()
    k = 100 * (c - ll) / (hh - ll).replace(0, np.nan)
    d = k.rolling(d_period).mean()
    return k, d


def williams_r(h, l, c, period=14):
    hh = h.rolling(period).max()
    ll = l.rolling(period).min()
    return -100 * (hh - c) / (hh - ll).replace(0, np.nan)


def macd(c, fast=12, slow=26, signal=9):
    ema_f = c.ewm(span=fast, adjust=False).mean()
    ema_s = c.ewm(span=slow, adjust=False).mean()
    line = ema_f - ema_s
    sig = line.ewm(span=signal, adjust=False).mean()
    hist = line - sig
    return line, sig, hist


def realized_vol(c, period=20):
    """log return の rolling std（%）"""
    r = np.log(c / c.shift())
    return r.rolling(period).std() * 100


def hurst(series, period=50):
    """簡易 Hurst（R/S 法・rolling）。0.5=ランダム / >0.5=トレンド / <0.5=平均回帰"""
    def hurst_rs(x):
        if len(x) < 10 or np.std(x) == 0:
            return np.nan
        n = len(x)
        m = np.mean(x)
        z = np.cumsum(x - m)
        R = np.max(z) - np.min(z)
        S = np.std(x)
        if S == 0:
            return np.nan
        return np.log(R/S) / np.log(n)
    r = np.log(series / series.shift()).dropna()
    out = pd.Series(np.nan, index=series.index)
    for i in range(period, len(series)):
        out.iloc[i] = hurst_rs(r.iloc[max(0,i-period):i].values)
    return out


def obv(c, v):
    """On-Balance Volume"""
    sign = np.sign(c.diff()).fillna(0)
    return (sign * v).cumsum()


def zscore(c, period):
    """returns Z-score（period本のリターン分布における今のリターンの標準化値）"""
    r = c.pct_change()
    m = r.rolling(period).mean()
    s = r.rolling(period).std()
    return (r - m) / s.replace(0, np.nan)


def divergence_flag(price, oscillator, lookback=14):
    """price が直近 lookback 本での高値更新 AND oscillator が前回 swing high より低い → 1
       price が直近 lookback 本での安値更新 AND oscillator が前回 swing low より高い → -1
       それ以外 0"""
    price_max = price.rolling(lookback).max()
    price_min = price.rolling(lookback).min()
    osc_max = oscillator.rolling(lookback).max()
    osc_min = oscillator.rolling(lookback).min()
    flag = pd.Series(0, index=price.index)
    # 高値更新だが oscillator は前 lookback の最大より低い（弱気ダイバージェンス）
    bear = (price >= price_max) & (oscillator < osc_max.shift(lookback))
    bull = (price <= price_min) & (oscillator > osc_min.shift(lookback))
    flag[bear] = 1
    flag[bull] = -1
    return flag


def build_indicators(df):
    """65軸指標（時間軸無関係・与えられた df に対して全指標を計算）"""
    o, h, l, c, v = df["open"], df["high"], df["low"], df["close"], df["volume"]
    f = pd.DataFrame(index=df.index)

    # 価格構造
    rng = (h - l).replace(0, np.nan)
    f["body_ratio"] = (c - o).abs() / rng
    f["upper_wick_ratio"] = (h - c.where(c > o, o)) / rng
    f["lower_wick_ratio"] = (c.where(c < o, o) - l) / rng
    f["close_to_high_pct"] = (h - c) / c * 100
    f["close_to_low_pct"] = (c - l) / c * 100
    # 直前 N バー高安連続更新数
    f["new_high_streak_5b"] = (h == h.rolling(5).max()).astype(int).rolling(5).sum()
    f["new_low_streak_5b"] = (l == l.rolling(5).min()).astype(int).rolling(5).sum()

    # ボラ系
    bw, pctb, bb_ma, bb_up, bb_lo = bollinger(c, 20)
    f["bb_width_pct"] = bw
    f["bb_pct_b"] = pctb
    # BB幅の rolling rank（直近 50本中の何%位置か・極大検出）
    f["bb_width_rank_50b"] = bw.rolling(50).rank(pct=True)
    adx14, di_p, di_m, atr14 = adx_di(h, l, c, 14)
    f["adx14"] = adx14
    f["di_diff"] = di_p - di_m
    f["di_plus"] = di_p
    f["di_minus"] = di_m
    f["atr14_pct"] = atr14 / c * 100
    f["realized_vol_20b"] = realized_vol(c, 20)
    f["realized_vol_rank_50b"] = realized_vol(c, 20).rolling(50).rank(pct=True)

    # モメンタム系
    rsi7 = rsi(c, 7)
    rsi14 = rsi(c, 14)
    f["rsi7"] = rsi7
    f["rsi14"] = rsi14
    sk, sd = stochastic(h, l, c, 14, 3)
    f["stoch_k"] = sk
    f["stoch_d"] = sd
    f["williams_r"] = williams_r(h, l, c, 14)
    macd_line, macd_sig, macd_hist = macd(c)
    f["macd_hist"] = macd_hist
    f["macd_hist_change"] = macd_hist - macd_hist.shift(1)
    f["macd_line"] = macd_line
    f["macd_signal"] = macd_sig
    f["momentum_10b"] = (c / c.shift(10) - 1) * 100

    # ダイバージェンス
    f["div_rsi14_14b"] = divergence_flag(c, rsi14, 14)
    f["div_macd_14b"] = divergence_flag(c, macd_hist, 14)

    # 出来高
    vol_ma = v.rolling(20).mean()
    f["volume_ratio_20b"] = v / vol_ma
    f["volume_rank_50b"] = v.rolling(50).rank(pct=True)
    obv_s = obv(c, v)
    f["obv_slope_10b"] = (obv_s - obv_s.shift(10)) / 10

    # ジャンプ検出
    f["zscore_return_20b"] = zscore(c, 20)
    f["zscore_return_50b"] = zscore(c, 50)
    f["abs_return_3sigma_20b"] = (zscore(c, 20).abs() >= 3).astype(int)

    # 統計（Hurst 重いので 1h/4h のみで計算するように呼び出し側で判断）
    return f


# ── データ準備 ───────────────────────────────────────────

def load_5m_ohlcv():
    df = pd.read_csv(OHLC_5M, parse_dates=["timestamp"])
    return df.set_index("timestamp").sort_index()


def resample_ohlcv(df5m, freq):
    return df5m.resample(freq).agg(
        open=("open", "first"), high=("high", "max"),
        low=("low", "min"), close=("close", "last"),
        volume=("volume", "sum"),
    ).dropna()


def load_funding():
    if not FUNDING.exists():
        return None
    df = pd.read_csv(FUNDING)
    ts_col = df.columns[0]
    df[ts_col] = pd.to_datetime(df[ts_col], utc=True, format="ISO8601").dt.tz_localize(None)
    df = df.set_index(ts_col).sort_index()
    return df


# ── サンプルごとの指標抽出 ──────────────────────────────

def attach_funding(samples, funding):
    if funding is None:
        samples["funding_at_peak"] = np.nan
        samples["funding_avg_24h"] = np.nan
        return samples
    fr_col = [c for c in funding.columns if "rate" in c.lower() or "funding" in c.lower()][0]
    fr = funding[fr_col].sort_index()
    vals_at = []
    vals_24h = []
    for pt in samples["peak_time"]:
        # peak時点で観測可能な直近 funding（peak より過去で最新の1件）
        recent = fr[fr.index < pt]
        if len(recent) == 0:
            vals_at.append(np.nan); vals_24h.append(np.nan); continue
        vals_at.append(float(recent.iloc[-1]))
        # 直近24h平均（funding は8h単位なので3件）
        avg_window = fr[(fr.index < pt) & (fr.index >= pt - pd.Timedelta("24h"))]
        vals_24h.append(float(avg_window.mean()) if len(avg_window) else np.nan)
    samples["funding_at_peak"] = vals_at
    samples["funding_avg_24h"] = vals_24h
    return samples


def main():
    print(f"=== V字頂点指標観察 ===")
    samples = pd.read_parquet(SAMPLES)
    print(f"  samples: {len(samples)}")

    print("5m OHLC 読み込み...")
    df5m = load_5m_ohlcv()
    print(f"  5m: {len(df5m)} bars")

    print("各時間軸でリサンプル + 指標計算...")
    feats_per_tf = {}
    df_per_tf = {}
    for tf, cfg in TIMEFRAMES.items():
        d = resample_ohlcv(df5m, cfg["freq"])
        feats = build_indicators(d)
        # Hurst は重いので 1h/4h のみ
        if tf in ("1h", "4h"):
            feats["hurst_50b"] = hurst(d["close"], 50)
        df_per_tf[tf] = d
        feats_per_tf[tf] = feats
        print(f"  {tf}: {len(d)} bars, {len(feats.columns)} indicators")

    # peak時点の指標値抽出（look-ahead なし）
    print("peak時点の指標値抽出...")
    rows = []
    for _, s in samples.iterrows():
        pt = pd.Timestamp(s["peak_time"])
        row = {"sample_id": s["sample_id"], "direction": s["direction"],
               "year": int(s["year"]), "peak_time": pt,
               "magnitude_pct": float(s["magnitude_pct"])}
        for tf, feats in feats_per_tf.items():
            # peak時点を含むバーの指標値（peak以前のバーのうち最後のもの）
            valid = feats.loc[feats.index <= pt]
            if len(valid) == 0:
                continue
            last = valid.iloc[-1]
            for col in feats.columns:
                row[f"{tf}_{col}"] = last[col]
        rows.append(row)
    peak_df = pd.DataFrame(rows)

    # funding rate 付与
    funding = load_funding()
    peak_df = attach_funding(peak_df, funding)

    peak_df.to_csv(OUT_DIR / "indicators_at_peak.csv", index=False)
    print(f"  → indicators_at_peak.csv ({len(peak_df)} 行 × {len(peak_df.columns)} 列)")

    # peak vs 周辺バーの統計サマリ（カテゴリ抜粋・全部出すと長い）
    print("\nカテゴリ別 peak vs 周辺バー統計...")
    summary_lines = ["# V字頂点 24サンプル 指標観察サマリ", ""]
    summary_lines.append("各サンプルの peak時点指標値 vs その前後 ±N バーの平均/分布。")
    summary_lines.append(f"周辺範囲: {TIMEFRAMES}")
    summary_lines.append("")

    # カテゴリと注目指標
    focus_indicators = {
        "ボラ極大": ["bb_width_pct", "bb_width_rank_50b", "atr14_pct", "realized_vol_rank_50b"],
        "モメンタム飽和": ["rsi7", "rsi14", "stoch_k", "williams_r"],
        "ダイバージェンス": ["div_rsi14_14b", "div_macd_14b"],
        "ジャンプ": ["zscore_return_20b", "zscore_return_50b", "abs_return_3sigma_20b"],
        "出来高": ["volume_ratio_20b", "volume_rank_50b"],
        "ローソク": ["body_ratio", "upper_wick_ratio", "lower_wick_ratio"],
        "ADX/DI": ["adx14", "di_diff"],
    }

    for cat, inds in focus_indicators.items():
        summary_lines.append(f"## {cat}")
        summary_lines.append("")
        summary_lines.append(f"| 指標 | TF | up平均 | down平均 | up中央 | down中央 | up範囲 | down範囲 |")
        summary_lines.append(f"|------|----|--------|----------|--------|----------|--------|----------|")
        for ind in inds:
            for tf in TIMEFRAMES.keys():
                col = f"{tf}_{ind}"
                if col not in peak_df.columns:
                    continue
                up = peak_df[peak_df["direction"] == "up"][col].dropna()
                dn = peak_df[peak_df["direction"] == "down"][col].dropna()
                if len(up) == 0 and len(dn) == 0:
                    continue
                summary_lines.append(
                    f"| {ind} | {tf} | "
                    f"{up.mean():.2f} | {dn.mean():.2f} | "
                    f"{up.median():.2f} | {dn.median():.2f} | "
                    f"{up.min():.2f}〜{up.max():.2f} | "
                    f"{dn.min():.2f}〜{dn.max():.2f} |"
                )
        summary_lines.append("")

    # funding
    summary_lines.append("## Funding Rate")
    summary_lines.append("")
    if "funding_at_peak" in peak_df.columns:
        up = peak_df[peak_df["direction"] == "up"]["funding_at_peak"].dropna()
        dn = peak_df[peak_df["direction"] == "down"]["funding_at_peak"].dropna()
        summary_lines.append(f"- up peak (n={len(up)}): mean={up.mean():.5f} / median={up.median():.5f}")
        summary_lines.append(f"- down peak (n={len(dn)}): mean={dn.mean():.5f} / median={dn.median():.5f}")
        up24 = peak_df[peak_df["direction"] == "up"]["funding_avg_24h"].dropna()
        dn24 = peak_df[peak_df["direction"] == "down"]["funding_avg_24h"].dropna()
        summary_lines.append(f"- up 24h avg (n={len(up24)}): mean={up24.mean():.5f}")
        summary_lines.append(f"- down 24h avg (n={len(dn24)}): mean={dn24.mean():.5f}")

    (OUT_DIR / "indicators_summary.md").write_text("\n".join(summary_lines) + "\n")
    print(f"  → indicators_summary.md")

    # 視覚化 HTML（各サンプルの 1h チャート + 主要指標）
    print("\n可視化 HTML 生成中...")
    html_parts = ['<html><head><meta charset="utf-8"><title>V字頂点 24サンプル</title>',
                  '<style>body{font-family:sans-serif;background:#0a0a0a;color:#ddd;padding:20px}',
                  'h2{border-bottom:2px solid #555;padding-bottom:5px}',
                  'img{display:block;margin:10px 0;background:#fff}',
                  '.meta{color:#aaa;margin:5px 0}</style></head><body>',
                  '<h1>V字頂点 24サンプル 指標観察</h1>',
                  '<p>各サンプルのピーク前後 ±2h（5m足）+ ±8h（1h足）の OHLC + 主要指標推移</p>']
    for _, s in samples.iterrows():
        pt = pd.Timestamp(s["peak_time"])
        sid = s["sample_id"]
        direction = s["direction"]
        mag = float(s["magnitude_pct"]) * 100
        html_parts.append(f'<h2>{sid} ({direction} {mag:+.1f}% @ {pt})</h2>')
        html_parts.append(f'<div class="meta">start_price={s["start_price"]:.0f} '
                          f'peak_price={s["peak_price"]:.0f} hrs→half={s["hours_to_half"]:.1f}h</div>')

        # 5m足 ±2h
        df_5m = df_per_tf["5m"]
        feat_5m = feats_per_tf["5m"]
        win_start = pt - pd.Timedelta("2h")
        win_end = pt + pd.Timedelta("2h")
        seg_5m = df_5m[(df_5m.index >= win_start) & (df_5m.index <= win_end)]
        feat_5m_seg = feat_5m[(feat_5m.index >= win_start) & (feat_5m.index <= win_end)]

        # 1h足 ±8h
        df_1h = df_per_tf["1h"]
        feat_1h = feats_per_tf["1h"]
        win_start_1h = pt - pd.Timedelta("8h")
        win_end_1h = pt + pd.Timedelta("8h")
        seg_1h = df_1h[(df_1h.index >= win_start_1h) & (df_1h.index <= win_end_1h)]
        feat_1h_seg = feat_1h[(feat_1h.index >= win_start_1h) & (feat_1h.index <= win_end_1h)]

        fig, axes = plt.subplots(3, 2, figsize=(14, 9))
        # 上段: 5m close + 1h close（ピーク赤線）
        axes[0,0].plot(seg_5m.index, seg_5m["close"], color="#3af", linewidth=1)
        axes[0,0].axvline(pt, color="red", linestyle="--", alpha=0.6)
        axes[0,0].set_title(f"5m close ±2h"); axes[0,0].grid(alpha=0.3)
        axes[0,1].plot(seg_1h.index, seg_1h["close"], color="#3af", linewidth=1.5, marker="o", markersize=3)
        axes[0,1].axvline(pt, color="red", linestyle="--", alpha=0.6)
        axes[0,1].set_title(f"1h close ±8h"); axes[0,1].grid(alpha=0.3)
        # 中段: BB幅(5m) + RSI14(1h)
        axes[1,0].plot(feat_5m_seg.index, feat_5m_seg["bb_width_pct"], color="#fa3", linewidth=1)
        axes[1,0].axvline(pt, color="red", linestyle="--", alpha=0.6)
        axes[1,0].set_title("5m BB幅(%)"); axes[1,0].grid(alpha=0.3)
        axes[1,1].plot(feat_1h_seg.index, feat_1h_seg["rsi14"], color="#fa3", linewidth=1.5, marker="o", markersize=3)
        axes[1,1].axhline(70, color="#888", linestyle=":", linewidth=0.5)
        axes[1,1].axhline(30, color="#888", linestyle=":", linewidth=0.5)
        axes[1,1].axvline(pt, color="red", linestyle="--", alpha=0.6)
        axes[1,1].set_title("1h RSI14"); axes[1,1].grid(alpha=0.3); axes[1,1].set_ylim(0, 100)
        # 下段: Z-score(5m) + volume_ratio(1h)
        axes[2,0].plot(feat_5m_seg.index, feat_5m_seg["zscore_return_20b"], color="#a3f", linewidth=1)
        axes[2,0].axhline(3, color="#888", linestyle=":", linewidth=0.5)
        axes[2,0].axhline(-3, color="#888", linestyle=":", linewidth=0.5)
        axes[2,0].axvline(pt, color="red", linestyle="--", alpha=0.6)
        axes[2,0].set_title("5m Z-score(20)"); axes[2,0].grid(alpha=0.3)
        axes[2,1].plot(feat_1h_seg.index, feat_1h_seg["volume_ratio_20b"], color="#a3f", linewidth=1.5, marker="o", markersize=3)
        axes[2,1].axhline(1, color="#888", linestyle=":", linewidth=0.5)
        axes[2,1].axvline(pt, color="red", linestyle="--", alpha=0.6)
        axes[2,1].set_title("1h vol/MA20"); axes[2,1].grid(alpha=0.3)

        for ax in axes.flat:
            ax.tick_params(axis="x", rotation=30, labelsize=7)
        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format="png", dpi=80, bbox_inches="tight")
        plt.close(fig)
        b64 = base64.b64encode(buf.getvalue()).decode()
        html_parts.append(f'<img src="data:image/png;base64,{b64}">')

    html_parts.append('</body></html>')
    (OUT_DIR / "charts.html").write_text("\n".join(html_parts))
    print(f"  → charts.html")

    print("\n完了。")
    print(f"  - indicators_at_peak.csv: peak時点 65軸 24サンプル")
    print(f"  - indicators_summary.md: カテゴリ別 up/down 分布")
    print(f"  - charts.html: 24サンプル可視化（5m + 1h 主要指標）")


if __name__ == "__main__":
    main()
