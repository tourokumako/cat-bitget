"""Multi-TF 指標 precompute。5m OHLCV を resample してから ta で各指標を計算する。"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import ta

from .loader import IndicatorSpec, Recipe

PANDAS_TF_RULE = {
    "5m": "5min",
    "15m": "15min",
    "1h": "1h",
    "4h": "4h",
    "D": "1D",
    "W": "1W",
    "M": "1ME",
}


def load_ohlcv_5m(csv_path: Path | str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.set_index("timestamp").sort_index()
    for c in ("open", "high", "low", "close", "volume"):
        df[c] = pd.to_numeric(df[c])
    return df


def load_human_labels(csv_path: Path | str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df = df.set_index("date")
    df["label"] = df["label"].astype(str).str.strip()
    df = df[df["label"].isin({"downtrend", "range", "uptrend"})]
    return df


def resample_ohlcv(df_5m: pd.DataFrame, tf: str) -> pd.DataFrame:
    if tf == "5m":
        return df_5m.copy()
    rule = PANDAS_TF_RULE[tf]
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    out = df_5m.resample(rule, label="right", closed="right").agg(agg).dropna()
    return out


def _compute_one_indicator(df: pd.DataFrame, ind: IndicatorSpec) -> pd.Series:
    name = ind.name
    if name == "ma_slope":
        period = int(ind.period or 70)
        lookback = int(ind.lookback or 5)
        ma = df["close"].rolling(window=period, min_periods=period).mean()
        return (ma - ma.shift(lookback)) / ma.shift(lookback) * 100
    if name == "ma_dev":
        period = int(ind.period or 50)
        ma = df["close"].rolling(window=period, min_periods=period).mean()
        return (df["close"] - ma) / ma * 100
    if name == "price_ma_diff":
        period = int(ind.period or 200)
        ma = df["close"].rolling(window=period, min_periods=period).mean()
        return df["close"] - ma
    if name == "adx":
        period = int(ind.period or 14)
        return ta.trend.ADXIndicator(df["high"], df["low"], df["close"], window=period).adx()
    if name == "di_diff":
        period = int(ind.period or 14)
        a = ta.trend.ADXIndicator(df["high"], df["low"], df["close"], window=period)
        return a.adx_pos() - a.adx_neg()
    if name == "rsi":
        period = int(ind.period or 14)
        return ta.momentum.RSIIndicator(df["close"], window=period).rsi()
    if name == "macd_hist":
        return ta.trend.MACD(df["close"]).macd_diff()
    if name == "stoch_k":
        period = int(ind.period or 14)
        return ta.momentum.StochasticOscillator(df["high"], df["low"], df["close"], window=period, smooth_window=3).stoch()
    if name == "atr_pct":
        period = int(ind.period or 14)
        atr = ta.volatility.AverageTrueRange(df["high"], df["low"], df["close"], window=period).average_true_range()
        return atr / df["close"] * 100
    if name == "bb_pos":
        period = int(ind.period or 20)
        bb = ta.volatility.BollingerBands(df["close"], window=period)
        return (df["close"] - bb.bollinger_mavg()) / (bb.bollinger_hband() - bb.bollinger_lband() + 1e-12)
    if name == "bb_width":
        period = int(ind.period or 20)
        bb = ta.volatility.BollingerBands(df["close"], window=period)
        return (bb.bollinger_hband() - bb.bollinger_lband()) / df["close"] * 100
    if name == "volume_z":
        period = int(ind.period or 20)
        m = df["volume"].rolling(period).mean()
        s = df["volume"].rolling(period).std()
        return (df["volume"] - m) / (s + 1e-12)
    if name == "obv_slope":
        lookback = int(ind.lookback or 5)
        obv = ta.volume.OnBalanceVolumeIndicator(df["close"], df["volume"]).on_balance_volume()
        return obv - obv.shift(lookback)
    if name == "ichimoku_cloud_pos":
        high9 = df["high"].rolling(9).max()
        low9 = df["low"].rolling(9).min()
        high26 = df["high"].rolling(26).max()
        low26 = df["low"].rolling(26).min()
        high52 = df["high"].rolling(52).max()
        low52 = df["low"].rolling(52).min()
        tenkan = (high9 + low9) / 2
        kijun = (high26 + low26) / 2
        senkou_a = ((tenkan + kijun) / 2).shift(26)
        senkou_b = ((high52 + low52) / 2).shift(26)
        cloud_mid = (senkou_a + senkou_b) / 2
        return (df["close"] - cloud_mid) / cloud_mid * 100
    if name == "ichimoku_tk_diff":
        tenkan = (df["high"].rolling(9).max() + df["low"].rolling(9).min()) / 2
        kijun = (df["high"].rolling(26).max() + df["low"].rolling(26).min()) / 2
        return (tenkan - kijun) / df["close"] * 100
    if name == "ichimoku_chikou":
        return (df["close"] - df["close"].shift(26)) / df["close"].shift(26) * 100
    raise ValueError(f"unknown indicator: {name}")


def precompute_panels(
    df_5m: pd.DataFrame,
    recipes: list[Recipe],
    labels_human: pd.DataFrame | None = None,
) -> dict[str, pd.DataFrame]:
    """各 TF の OHLCV + 必要指標を持つ panel を作る。M_dom は label 由来なので別経路。"""
    needed_tf_to_inds: dict[str, list[IndicatorSpec]] = {}
    for r in recipes:
        for ind in r.indicators:
            needed_tf_to_inds.setdefault(ind.tf, []).append(ind)

    panels: dict[str, pd.DataFrame] = {}
    for tf, inds in needed_tf_to_inds.items():
        if tf == "M_dom":
            if labels_human is None or labels_human.empty:
                raise ValueError("M_dom 指標は human ラベル必須")
            month = pd.to_datetime(labels_human.index).to_period("M")
            mode = labels_human.assign(month=month).groupby("month")["label"].agg(
                lambda s: s.value_counts().idxmax()
            )
            panels[tf] = pd.DataFrame({"human_label_m_dom": mode})
            continue

        df_tf = resample_ohlcv(df_5m, tf)
        for ind in inds:
            col = ind.key
            if col not in df_tf.columns:
                df_tf[col] = _compute_one_indicator(df_tf, ind)
        panels[tf] = df_tf

    return panels
