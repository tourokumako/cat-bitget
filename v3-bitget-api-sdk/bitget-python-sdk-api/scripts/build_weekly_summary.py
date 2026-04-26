"""Ground Truth タブ用の週別サマリ JSON を生成する（案B 週単位）。

入力: data/BTCUSDT-5m-2025-04-01_03-31_365d.csv
出力: dashboard/data/weekly_summary.json

各週について:
  - ISO月曜起点の OHLC（週足ローソク1本）
  - 週内の日足ローソク（最大7本）
  - 騰落率/レンジ%/週内ADX/ATR平均
  - 現行 regime ラベル分布（参考表示）
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = REPO_ROOT / "data" / "BTCUSDT-5m-2025-04-01_03-31_365d.csv"
OUT_PATH = REPO_ROOT / "dashboard" / "data" / "weekly_summary.json"
DAILY_WARMUP = REPO_ROOT / "data" / "warmup" / "daily_warmup_BTCUSDT.csv"


def _load_5m(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    if "timestamp_ms" in df.columns:
        df["ts"] = pd.to_datetime(df["timestamp_ms"], unit="ms")
    elif "timestamp" in df.columns:
        df["ts"] = pd.to_datetime(df["timestamp"])
    else:
        raise SystemExit(f"timestamp / timestamp_ms 列が見つからない: {csv_path}")
    for c in ("open", "high", "low", "close"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.set_index("ts").sort_index()


def _resample_daily(df_5m: pd.DataFrame) -> pd.DataFrame:
    return df_5m.resample("D").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}
    ).dropna()


def _resample_weekly(df_5m: pd.DataFrame) -> pd.DataFrame:
    """ISO週: 月曜始まり。pandas の 'W-SUN' は日曜終わり = 月曜始まり週。"""
    return df_5m.resample("W-SUN", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}
    ).dropna()


def _compute_daily_regime(df_5m: pd.DataFrame) -> pd.Series:
    try:
        import ta
    except ImportError:
        return pd.Series(dtype=str)

    daily = _resample_daily(df_5m)
    if DAILY_WARMUP.exists():
        dw = pd.read_csv(DAILY_WARMUP)
        dw["ts"] = pd.to_datetime(dw["timestamp"])
        for c in ("close", "high", "low"):
            dw[c] = pd.to_numeric(dw[c], errors="coerce")
        dw = dw.set_index("ts").sort_index()
        combined = pd.concat([dw[["close", "high", "low"]], daily[["close", "high", "low"]]])
        combined = combined[~combined.index.duplicated(keep="last")].sort_index()
    else:
        combined = daily[["close", "high", "low"]].copy()

    combined["ma70"] = combined["close"].rolling(70, min_periods=70).mean()
    combined["ma70_slope"] = combined["ma70"].diff(5)
    adx_obj = ta.trend.ADXIndicator(combined["high"], combined["low"], combined["close"], window=14)
    combined["adx"] = adx_obj.adx()

    def _classify(row):
        if any(pd.isna(row[k]) for k in ("ma70", "ma70_slope", "adx", "close")):
            return "unknown"
        if row["adx"] < 20:
            return "range"
        if row["ma70_slope"] > 0 and row["close"] > row["ma70"]:
            return "uptrend"
        if row["ma70_slope"] < 0 and row["close"] < row["ma70"]:
            return "downtrend"
        return "mixed"

    return combined.apply(_classify, axis=1)


def _compute_daily_indicators(df_5m: pd.DataFrame) -> pd.DataFrame:
    try:
        import ta
    except ImportError:
        return pd.DataFrame()
    daily = _resample_daily(df_5m)
    adx = ta.trend.ADXIndicator(daily["high"], daily["low"], daily["close"], window=14)
    atr = ta.volatility.AverageTrueRange(daily["high"], daily["low"], daily["close"], window=14)
    daily["adx"] = adx.adx()
    daily["atr"] = atr.average_true_range()
    return daily


def build(csv_path: Path) -> dict:
    df_5m = _load_5m(csv_path)
    weekly = _resample_weekly(df_5m)
    daily_regime = _compute_daily_regime(df_5m)
    daily_ind = _compute_daily_indicators(df_5m)

    weeks_out = []
    for ts, row in weekly.iterrows():
        week_start = ts.normalize()
        week_end = week_start + pd.Timedelta(days=6)
        w_open = float(row["open"])
        w_close = float(row["close"])
        w_high = float(row["high"])
        w_low = float(row["low"])
        return_pct = (w_close - w_open) / w_open * 100.0 if w_open else 0.0
        range_pct = (w_high - w_low) / w_open * 100.0 if w_open else 0.0

        mask = (df_5m.index >= week_start) & (df_5m.index < week_start + pd.Timedelta(days=7))
        df_week = df_5m[mask]
        if df_week.empty:
            continue
        d_in_week = _resample_daily(df_week)
        daily_candles = [
            {"date": idx.strftime("%Y-%m-%d"), "o": float(r["open"]), "h": float(r["high"]),
             "l": float(r["low"]), "c": float(r["close"])}
            for idx, r in d_in_week.iterrows()
        ]

        regime_counts: dict = {}
        if not daily_regime.empty:
            wlabels = daily_regime[(daily_regime.index >= week_start) &
                                    (daily_regime.index < week_start + pd.Timedelta(days=7))]
            for v in wlabels.tolist():
                regime_counts[v] = regime_counts.get(v, 0) + 1

        adx_mean = atr_mean = None
        if not daily_ind.empty:
            wind = daily_ind[(daily_ind.index >= week_start) &
                             (daily_ind.index < week_start + pd.Timedelta(days=7))]
            if not wind.empty:
                adx_mean = float(wind["adx"].dropna().mean()) if wind["adx"].notna().any() else None
                atr_mean = float(wind["atr"].dropna().mean()) if wind["atr"].notna().any() else None

        weeks_out.append({
            "week_start": week_start.strftime("%Y-%m-%d"),
            "week_end": week_end.strftime("%Y-%m-%d"),
            "weekly_candle": {"o": w_open, "h": w_high, "l": w_low, "c": w_close},
            "return_pct": round(return_pct, 2),
            "range_pct": round(range_pct, 2),
            "adx_mean": round(adx_mean, 2) if adx_mean is not None else None,
            "atr_mean": round(atr_mean, 2) if atr_mean is not None else None,
            "current_regime_distribution": regime_counts,
            "daily_candles": daily_candles,
        })

    return {
        "source_csv": str(csv_path.relative_to(REPO_ROOT)),
        "weeks": weeks_out,
    }


def main() -> None:
    csv_path = DEFAULT_CSV
    if len(sys.argv) >= 2:
        csv_path = Path(sys.argv[1]).resolve()
    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path}")

    out = build(csv_path)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[build_weekly_summary] {len(out['weeks'])} weeks → {OUT_PATH}")


if __name__ == "__main__":
    main()
