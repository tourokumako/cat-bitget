"""機械生成 ground truth（日次・look-ahead禁止）。

判定ロジック:
  方向スコア（日足/4h/1h の close vs MA20 多数決）
  + 一目均衡表（日足）
  + ADX（日足14日・強度）
  + BB幅（日足20日2σ・レンジ判別）

統合:
  ADX<20 AND BB幅<中央値 → range
  方向+2以上 AND 一目上昇補強 AND ADX≥25 → uptrend（強）
  方向-2以下 AND 一目下降補強 AND ADX≥25 → downtrend（強）
  方向+2以上 AND ADX≥20 → uptrend（弱）
  方向-2以下 AND ADX≥20 → downtrend（弱）
  上記外 → range

入力: data/BTCUSDT-5m-2025-04-01_03-31_365d.csv + warmup
出力: data/regime_ground_truth_daily.csv（date,label,direction_score,ichimoku,adx,bb_width_pct,bb_median,note）
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_5M_PATH = REPO_ROOT / "data" / "BTCUSDT-5m-2025-04-01_03-31_365d.csv"
DAILY_WARMUP_PATH = REPO_ROOT / "data" / "warmup" / "daily_warmup_BTCUSDT.csv"
OUT_PATH = REPO_ROOT / "data" / "regime_ground_truth_daily.csv"


def _load_5m() -> pd.DataFrame:
    df = pd.read_csv(CSV_5M_PATH)
    df["ts"] = pd.to_datetime(df["timestamp"])
    for c in ("open", "high", "low", "close", "volume"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.set_index("ts").sort_index()


def _resample(df_5m: pd.DataFrame, rule: str) -> pd.DataFrame:
    return df_5m.resample(rule).agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}
    ).dropna()


def _load_daily_with_warmup(df_5m: pd.DataFrame) -> pd.DataFrame:
    daily = _resample(df_5m, "D")
    if DAILY_WARMUP_PATH.exists():
        dw = pd.read_csv(DAILY_WARMUP_PATH)
        dw["ts"] = pd.to_datetime(dw["timestamp"])
        for c in ("open", "high", "low", "close"):
            if c in dw.columns:
                dw[c] = pd.to_numeric(dw[c], errors="coerce")
        dw = dw.set_index("ts").sort_index()
        cols = [c for c in ("open", "high", "low", "close") if c in dw.columns]
        combined = pd.concat([dw[cols], daily[cols]])
        combined = combined[~combined.index.duplicated(keep="last")].sort_index()
        return combined
    return daily


def _ichimoku_classify(daily_seg: pd.DataFrame) -> str:
    """日足の一目均衡表で雲位置を判定（前日確定値時点）。
    返値: "up" / "down" / "neutral"
    """
    if len(daily_seg) < 52:
        return "neutral"
    high = daily_seg["high"]
    low = daily_seg["low"]
    close = daily_seg["close"]
    tenkan = (high.rolling(9).max() + low.rolling(9).min()) / 2
    kijun = (high.rolling(26).max() + low.rolling(26).min()) / 2
    span_a = ((tenkan + kijun) / 2).shift(26)
    span_b = ((high.rolling(52).max() + low.rolling(52).min()) / 2).shift(26)

    if pd.isna(tenkan.iloc[-1]) or pd.isna(kijun.iloc[-1]):
        return "neutral"
    if pd.isna(span_a.iloc[-1]) or pd.isna(span_b.iloc[-1]):
        return "neutral"

    last_close = close.iloc[-1]
    cloud_top = max(span_a.iloc[-1], span_b.iloc[-1])
    cloud_bot = min(span_a.iloc[-1], span_b.iloc[-1])

    above_cloud = last_close > cloud_top
    below_cloud = last_close < cloud_bot
    tenkan_up = tenkan.iloc[-1] > kijun.iloc[-1]
    tenkan_dn = tenkan.iloc[-1] < kijun.iloc[-1]

    if above_cloud and tenkan_up:
        return "up"
    if below_cloud and tenkan_dn:
        return "down"
    return "neutral"


def _direction_score(daily_seg: pd.DataFrame, h4_seg: pd.DataFrame, h1_seg: pd.DataFrame) -> int:
    """日足/4h/1h の close vs MA20 で多数決。+3〜-3 を返す。"""
    score = 0
    for seg in (daily_seg, h4_seg, h1_seg):
        if len(seg) < 20:
            continue
        ma20 = seg["close"].rolling(20).mean().iloc[-1]
        if pd.isna(ma20):
            continue
        last = seg["close"].iloc[-1]
        if last > ma20:
            score += 1
        elif last < ma20:
            score -= 1
    return score


def build() -> pd.DataFrame:
    df_5m = _load_5m()
    daily_full = _load_daily_with_warmup(df_5m)
    h4_full = _resample(df_5m, "4h")
    h1_full = _resample(df_5m, "1h")

    try:
        import ta
    except ImportError:
        raise SystemExit("ta library required: pip install ta")

    rows = []
    csv_dates = pd.date_range(df_5m.index.min().normalize(), df_5m.index.max().normalize(), freq="D")
    for d in csv_dates:
        # 「その日のlabel = 前日までの確定値で判定」 = look-aheadなし
        prev = d - pd.Timedelta(days=1)
        d_seg = daily_full.loc[daily_full.index <= prev]
        h4_seg = h4_full.loc[h4_full.index < d]
        h1_seg = h1_full.loc[h1_full.index < d]

        if len(d_seg) < 52 or len(h4_seg) < 20 or len(h1_seg) < 20:
            rows.append({
                "date": d.strftime("%Y-%m-%d"),
                "label": "",
                "direction_score": "",
                "ichimoku": "",
                "adx": "",
                "bb_width_pct": "",
                "bb_median": "",
                "note": "warmup_insufficient",
            })
            continue

        direction = _direction_score(d_seg, h4_seg, h1_seg)
        ichimoku = _ichimoku_classify(d_seg)

        adx_obj = ta.trend.ADXIndicator(d_seg["high"], d_seg["low"], d_seg["close"], window=14)
        adx_val = adx_obj.adx().iloc[-1]
        adx_val = float(adx_val) if pd.notna(adx_val) else 0.0

        bb = ta.volatility.BollingerBands(d_seg["close"], window=20, window_dev=2.0)
        bb_high = bb.bollinger_hband().iloc[-1]
        bb_low = bb.bollinger_lband().iloc[-1]
        last_close = d_seg["close"].iloc[-1]
        if pd.notna(bb_high) and pd.notna(bb_low) and last_close > 0:
            bb_width_pct = (bb_high - bb_low) / last_close * 100
        else:
            bb_width_pct = float("nan")

        # BB幅の中央値（過去30日の bb_width_pct の median）
        bb_widths = []
        for i in range(min(30, len(d_seg) - 20)):
            sub = d_seg.iloc[:-i] if i > 0 else d_seg
            if len(sub) < 20:
                continue
            bb_i = ta.volatility.BollingerBands(sub["close"], window=20, window_dev=2.0)
            h_i = bb_i.bollinger_hband().iloc[-1]
            l_i = bb_i.bollinger_lband().iloc[-1]
            c_i = sub["close"].iloc[-1]
            if pd.notna(h_i) and pd.notna(l_i) and c_i > 0:
                bb_widths.append((h_i - l_i) / c_i * 100)
        bb_median = float(pd.Series(bb_widths).median()) if bb_widths else float("nan")

        # 統合判定
        is_narrow = pd.notna(bb_median) and pd.notna(bb_width_pct) and bb_width_pct < bb_median
        if adx_val < 20 and is_narrow:
            label = "range"
            note = "ADX<20 AND BB狭い"
        elif direction >= 2 and ichimoku == "up" and adx_val >= 25:
            label = "uptrend"
            note = "3条件合意・強上昇"
        elif direction <= -2 and ichimoku == "down" and adx_val >= 25:
            label = "downtrend"
            note = "3条件合意・強下落"
        elif direction >= 2 and adx_val >= 20:
            label = "uptrend"
            note = "弱上昇（方向+一目orADX）"
        elif direction <= -2 and adx_val >= 20:
            label = "downtrend"
            note = "弱下落"
        else:
            label = "range"
            note = "条件不一致"

        rows.append({
            "date": d.strftime("%Y-%m-%d"),
            "label": label,
            "direction_score": direction,
            "ichimoku": ichimoku,
            "adx": round(adx_val, 2),
            "bb_width_pct": round(bb_width_pct, 3) if pd.notna(bb_width_pct) else "",
            "bb_median": round(bb_median, 3) if pd.notna(bb_median) else "",
            "note": note,
        })

    return pd.DataFrame(rows)


def main() -> None:
    df = build()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False, encoding="utf-8")
    print(f"[build_regime_ground_truth_daily] {len(df)} 日 → {OUT_PATH}")
    labeled = df[df["label"].isin(["uptrend", "downtrend", "range"])]
    print(f"\n  ラベル分布:")
    print(f"    {labeled['label'].value_counts().to_dict()}")
    if "warmup_insufficient" in df["note"].values:
        n = (df["note"] == "warmup_insufficient").sum()
        print(f"  warmup不足: {n} 日")


if __name__ == "__main__":
    main()
