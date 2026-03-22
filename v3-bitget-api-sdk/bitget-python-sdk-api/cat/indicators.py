import pandas as pd
import numpy as np
import ta

def calculate_rci(series: pd.Series, window: int) -> pd.Series:
    """RCI（順位相関指数）"""
    rci_values = [np.nan] * len(series)
    for i in range(window - 1, len(series)):
        price_window = series.iloc[i - window + 1 : i + 1]
        if price_window.isnull().any():
            continue
        time_rank = pd.Series(range(1, window + 1)).rank().values
        price_rank = price_window.rank().values
        d = time_rank - price_rank
        d2 = np.sum(d ** 2)
        rci = (1 - (6 * d2) / (window * (window**2 - 1))) * 100
        rci_values[i] = float(rci)
    return pd.Series(rci_values, index=series.index, dtype=float)

def ensure_ema20(df: pd.DataFrame) -> None:
    """ema_20 を一度だけ作る（既存があれば何もしない）"""
    if "ema_20" not in df.columns:
        df["ema_20"] = ta.trend.EMAIndicator(close=df["close"], window=20).ema_indicator()

def ensure_bb_columns(df: pd.DataFrame, window: int = 20, ndev: float = 2.0) -> None:
    """BBのミドル/上下/幅/傾きを保証（既存列は尊重）"""
    bb = ta.volatility.BollingerBands(close=df["close"], window=window, window_dev=ndev)

    if "bb_mid" not in df.columns:
        df["bb_mid"] = bb.bollinger_mavg()
    if "bb_middle" not in df.columns:   # 互換名
        df["bb_middle"] = df["bb_mid"]

    if "bb_upper" not in df.columns:
        df["bb_upper"] = bb.bollinger_hband()
    if "bb_lower" not in df.columns:
        df["bb_lower"] = bb.bollinger_lband()

    if "bb_width" not in df.columns:
        df["bb_width"] = df["bb_upper"] - df["bb_lower"]
    if "bb_width_pct" not in df.columns:
        df["bb_width_pct"] = df["bb_width"] / df["close"]

    if "bb_mid_slope" not in df.columns:
        df["bb_mid_slope"] = df["bb_mid"].diff()
    if "bb_middle_slope" not in df.columns:  # 互換名
        df["bb_middle_slope"] = df["bb_mid_slope"]

def compute_indicators(df: pd.DataFrame, params: dict | None = None) -> pd.DataFrame:
    """
    指標計算の入口（EMA20 → BB → RCI）。
    呼び出し側はこれだけ使えばOK。
    """
    if params is None:
        params = {}

    # EMA20
    ensure_ema20(df)

    # BB（ミドル/上下/幅/傾き）
    bb_window = int(params.get("BB_WINDOW", 20))
    bb_ndev   = float(params.get("BB_NDEV", 2.0))
    ensure_bb_columns(df, window=bb_window, ndev=bb_ndev)

    # RCI 群
    rci_windows = params.get("RCI_WINDOWS", [7, 9, 26, 52])
    for w in rci_windows:
        col = f"rci_{int(w)}"
        if col not in df.columns:
            df[col] = calculate_rci(df["close"], int(w))

    # --- entry_ok_long (v8 準拠) ---
    # location_prev: 直近 20 本レンジ内での位置（前バー値）
    n_look = 20
    recent_high = df["high"].rolling(window=n_look, min_periods=1).max()
    recent_low  = df["low"].rolling(window=n_look, min_periods=1).min()
    loc_denom = (recent_high - recent_low).replace(0, np.nan)
    df["location_prev"] = ((df["close"] - recent_low) / loc_denom).shift(1).fillna(0.5)

    # entry_risk_score: 直近 20 本ボラティリティ / close
    vola = df["close"].rolling(window=20, min_periods=5).std()
    df["entry_risk_score"] = (vola / df["close"]).clip(lower=0)

    loc_thresh   = float(params.get("LONG_LOCATION_THRESH", 0.9))
    risk_thresh  = float(params.get("LONG_RISK_THRESH", 0.3398))
    risk_lower   = float(params.get("LONG_RISKSCORE_LOWER_THRESH", 0.0007))
    df["entry_ok_long"] = (
        (df["location_prev"]   <= loc_thresh)
        & (df["entry_risk_score"] <= risk_thresh)
        & (df["entry_risk_score"] >= risk_lower)
    )

    return df
