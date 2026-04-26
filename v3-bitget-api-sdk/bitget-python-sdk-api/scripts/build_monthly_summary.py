"""Ground Truth タブ用の月別サマリ JSON を生成する。

入力: data/BTCUSDT-5m-2025-04-01_03-31_365d.csv
出力: dashboard/data/monthly_summary.json

各月について:
  - 暦月単位の OHLC（月足ローソク1本）
  - 月内の日足ローソク（30本前後）
  - 月内 ADX/ATR/騰落率/レンジ% 等の判定補助数値
  - 現行 regime ラベル（_build_regime_map と同じロジック・参考表示）

肉眼判定の根拠を残すため、判定に使う数値は全て JSON に含める。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = REPO_ROOT / "data" / "BTCUSDT-5m-2025-04-01_03-31_365d.csv"
OUT_PATH = REPO_ROOT / "dashboard" / "data" / "monthly_summary.json"
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
    daily = df_5m.resample("D").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}
    ).dropna()
    return daily


def _resample_monthly(df_5m: pd.DataFrame) -> pd.DataFrame:
    monthly = df_5m.resample("MS").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}
    ).dropna()
    return monthly


def _compute_daily_regime(df_5m: pd.DataFrame) -> pd.Series:
    """現行 _build_regime_map と同一ロジック（look-ahead 有り版・参考表示用）。"""
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


def _compute_daily_adx_atr(df_5m: pd.DataFrame) -> pd.DataFrame:
    """日足 ADX_14 / ATR_14 を計算（判定補助の月内平均で使う）。"""
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
    monthly = _resample_monthly(df_5m)
    daily_regime = _compute_daily_regime(df_5m)
    daily_ind = _compute_daily_adx_atr(df_5m)

    months_out = []
    for ts, row in monthly.iterrows():
        month_key = ts.strftime("%Y-%m")
        m_open = float(row["open"])
        m_close = float(row["close"])
        m_high = float(row["high"])
        m_low = float(row["low"])
        return_pct = (m_close - m_open) / m_open * 100.0 if m_open else 0.0
        range_pct = (m_high - m_low) / m_open * 100.0 if m_open else 0.0

        mask = (df_5m.index.year == ts.year) & (df_5m.index.month == ts.month)
        df_month = df_5m[mask]
        if df_month.empty:
            continue
        d_in_month = _resample_daily(df_month)
        daily_candles = [
            {
                "date": idx.strftime("%Y-%m-%d"),
                "o": float(r["open"]),
                "h": float(r["high"]),
                "l": float(r["low"]),
                "c": float(r["close"]),
            }
            for idx, r in d_in_month.iterrows()
        ]

        # 月内 regime ラベル分布（現行・参考表示用）
        regime_counts: dict = {}
        if not daily_regime.empty:
            mlabels = daily_regime[(daily_regime.index.year == ts.year) & (daily_regime.index.month == ts.month)]
            for v in mlabels.tolist():
                regime_counts[v] = regime_counts.get(v, 0) + 1

        # 月内 ADX/ATR 平均（参考値）
        adx_mean = None
        atr_mean = None
        if not daily_ind.empty:
            mind = daily_ind[(daily_ind.index.year == ts.year) & (daily_ind.index.month == ts.month)]
            if not mind.empty:
                adx_mean = float(mind["adx"].dropna().mean()) if mind["adx"].notna().any() else None
                atr_mean = float(mind["atr"].dropna().mean()) if mind["atr"].notna().any() else None

        # 月内高値日 / 安値日
        high_day = df_month["high"].idxmax()
        low_day = df_month["low"].idxmin()

        months_out.append({
            "month": month_key,
            "monthly_candle": {
                "o": m_open, "h": m_high, "l": m_low, "c": m_close,
            },
            "return_pct": round(return_pct, 2),
            "range_pct": round(range_pct, 2),
            "high_day": high_day.strftime("%Y-%m-%d"),
            "low_day": low_day.strftime("%Y-%m-%d"),
            "adx_mean": round(adx_mean, 2) if adx_mean is not None else None,
            "atr_mean": round(atr_mean, 2) if atr_mean is not None else None,
            "current_regime_distribution": regime_counts,
            "daily_candles": daily_candles,
        })

    return {
        "source_csv": str(csv_path.relative_to(REPO_ROOT)),
        "months": months_out,
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
    print(f"[build_monthly_summary] {len(out['months'])} months → {OUT_PATH}")


if __name__ == "__main__":
    main()
