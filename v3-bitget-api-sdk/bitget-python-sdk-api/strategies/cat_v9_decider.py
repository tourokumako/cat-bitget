"""
cat_v9_decider.py — V9 エントリー判断（SDK import 禁止）

移植元: cat-swing-sniper/strategies/CAT_v9_regime.py
  - preprocess()         : 入力判断に必要な指標のみ計算（バックテスト専用列は除外）
  - compute_p22_probe()  : 原本と完全一致
  - check_entry_priority(): 原本と完全一致
  - decide()             : snapshot dict → decision dict（新規追加）
"""
from __future__ import annotations

import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import ta

from cat.indicators import ensure_ema20


# ---------------------------------------------------------------------------
# RCI（CAT_v9_regime.py と完全一致）
# ---------------------------------------------------------------------------
def calculate_rci(series: pd.Series, window: int) -> pd.Series:
    """価格系列に対して RCI（順位相関指数）を計算します。"""
    rci_values: List[float] = [np.nan] * len(series)
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


# ---------------------------------------------------------------------------
# preprocess（エントリー判断に必要な指標のみ。バックテスト固有列は除外）
# 除外: ema_5, rsi_long/slope_long, real_body, lower_wick, is_bullish,
#       bull2, risk_quartile, is_flat_market, entry_ok_short, stoch_k_prev
# ---------------------------------------------------------------------------
def preprocess(df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    """エントリー判断に必要なテクニカル指標と派生列を計算します。"""
    required_cols = ["open", "high", "low", "close", "timestamp"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"preprocess(): missing required columns: {missing}")

    df = df.copy()
    df.reset_index(drop=True, inplace=True)

    df["close"] = pd.to_numeric(df["close"], errors="coerce")

    # RCI
    df["rci_9"] = calculate_rci(df["close"], 9).astype(float)
    for period in [7, 52]:
        df[f"rci_{period}"] = calculate_rci(df["close"], period).astype(float)

    # ボリンジャーバンドと傾き
    bb = ta.volatility.BollingerBands(close=df["close"], window=20)
    df["bb_middle"] = bb.bollinger_mavg()
    df["bb_sigma2_upper"] = bb.bollinger_hband()
    df["bb_sigma2_lower"] = bb.bollinger_lband()
    df["bb_width"] = (df["bb_sigma2_upper"] - df["bb_sigma2_lower"]) / df["bb_middle"]
    df["bb_mid_slope"] = df["bb_middle"] - df["bb_middle"].shift(1)

    # ADX
    adx = ta.trend.ADXIndicator(df["high"], df["low"], df["close"], window=14)
    df["adx"] = adx.adx()

    # atr_14: 単純平均ATR（replay_csv._calc_entry_states と同じ計算）
    _tr = pd.DataFrame({
        "hl":  df["high"] - df["low"],
        "hpc": (df["high"] - df["close"].shift(1)).abs(),
        "lpc": (df["low"]  - df["close"].shift(1)).abs(),
    }).max(axis=1)
    df["atr_14"] = _tr.rolling(window=14, min_periods=1).mean()

    # EMA20
    ensure_ema20(df)

    # RSI short（P24用）
    short_rsi_period = int(params.get("SHORT_RSI_PERIOD", 21))
    short_rsi_slope_n = int(params.get("SHORT_RSI_SLOPE_N", 3))
    df["rsi_short"] = ta.momentum.RSIIndicator(df["close"], window=short_rsi_period).rsi()
    df["rsi_slope_short"] = df["rsi_short"].diff(short_rsi_slope_n).fillna(0)

    # MACD（P1/P21用）
    _macd_fast = int(params.get("P1_MACD_FAST", 9))
    _macd_slow = int(params.get("P1_MACD_SLOW", 17))
    _macd_sign = int(params.get("P1_MACD_SIGNAL", 7))
    _macd_ind = ta.trend.MACD(
        df["close"],
        window_fast=_macd_fast,
        window_slow=_macd_slow,
        window_sign=_macd_sign,
    )
    df["macd"]        = _macd_ind.macd()
    df["macd_signal"] = _macd_ind.macd_signal()

    # ストキャスティクス（P2/P23用）
    stoch = ta.momentum.StochasticOscillator(
        df["high"], df["low"], df["close"], window=14, smooth_window=3
    )
    df["stoch_k"] = stoch.stoch()
    df["stoch_d"] = stoch.stoch_signal()

    # 直近レンジ内での位置（前のバー）
    n_look = 20
    recent_high = df["high"].rolling(window=n_look, min_periods=1).max()
    recent_low = df["low"].rolling(window=n_look, min_periods=1).min()
    location_denominator = (recent_high - recent_low).replace(0, np.nan)
    df["location_prev"] = (
        (df["close"] - recent_low) / location_denominator
    ).shift(1).fillna(0.5)

    # 相対的エントリーリスク
    vola = df["close"].rolling(window=20, min_periods=5).std()
    df["entry_risk_score"] = (vola / df["close"]).clip(lower=0)

    # エントリーフィルタ
    df["filter_location_passed_long"] = df["location_prev"] <= float(
        params.get("LONG_LOCATION_THRESH", 0.9)
    )
    df["filter_location_passed_short"] = df["location_prev"] <= float(
        params.get("SHORT_LOCATION_THRESH", 0.9)
    )
    df["filter_riskscore_passed_long"] = df["entry_risk_score"] <= float(
        params.get("LONG_RISK_THRESH", 0.3398)
    )
    df["filter_riskscore_passed_short"] = df["entry_risk_score"] <= float(
        params.get("SHORT_RISK_THRESH", 0.3398)
    )
    df["filter_riskscore_lower_passed_long"] = df["entry_risk_score"] >= float(
        params.get("LONG_RISKSCORE_LOWER_THRESH", 0.0007)
    )

    # 最終的な entry_ok_long フラグ
    df["entry_ok_long"] = (
        df["filter_location_passed_long"]
        & df["filter_riskscore_passed_long"]
        & df["filter_riskscore_lower_passed_long"]
    )

    # EMA20 保証（ensure_ema20 で作成済みのはずだが念のため）
    if "ema_20" not in df.columns:
        df["ema_20"] = ta.trend.EMAIndicator(close=df["close"], window=20).ema_indicator()

    return df


# ---------------------------------------------------------------------------
# compute_p22_probe（CAT_v9_regime.py と完全一致）
# ---------------------------------------------------------------------------
def compute_p22_probe(i, df, params):
    """P22の各条件を評価してブールdictで返す（外部検証用）"""
    out = {
        "rci_cross": False,
        "bb_upper_touch": False,
        "mid_down_ok": False,
        "rci52_hot_eval": False,
        "adx_ok_p22": False,
        "risk_ok_p22": False,
    }

    need_cols = ("rci_7", "rci_9", "rci_52", "bb_mid_slope", "high", "bb_sigma2_upper")
    if not hasattr(df, "columns"):
        return out
    if any(c not in df.columns for c in need_cols):
        return out
    if (i is None) or (i < 0) or (i >= len(df)):
        return out

    try:
        rci_7  = df.at[i, "rci_7"]
        rci_9  = df.at[i, "rci_9"]
        rci_52 = df.at[i, "rci_52"]
        bb_mid_slope  = df.at[i, "bb_mid_slope"]
        high_now      = df.at[i, "high"]
        bb_upper_now  = df.at[i, "bb_sigma2_upper"]
        adx_now       = df.at[i, "adx"] if "adx" in df.columns else None
    except Exception:
        return out
    if i <= 0:
        return out

    # 1本前
    rci_7_prev    = df.at[i - 1, "rci_7"]
    rci_9_prev    = df.at[i - 1, "rci_9"]
    high_prev     = df.at[i - 1, "high"]
    bb_upper_prev = df.at[i - 1, "bb_sigma2_upper"]

    # RCIデッドクロス
    if (
        pd.notna(rci_7_prev) and pd.notna(rci_9_prev)
        and pd.notna(rci_7) and pd.notna(rci_9)
    ):
        out["rci_cross"] = (rci_7_prev >= rci_9_prev) and (rci_7 <= rci_9)

    # BB上限タッチ（直近2本）
    eps_abs, eps_rel = 1e-8, 1.2e-3
    touch_now = (
        pd.notna(high_now) and pd.notna(bb_upper_now)
        and high_now >= bb_upper_now * (1 - eps_rel) - eps_abs
    )
    touch_prev = (
        pd.notna(high_prev) and pd.notna(bb_upper_prev)
        and high_prev >= bb_upper_prev * (1 - eps_rel) - eps_abs
    )
    out["bb_upper_touch"] = bool(touch_now or touch_prev)

    # ミドル下向き（NaN許容）
    out["mid_down_ok"] = (pd.isna(bb_mid_slope) or bb_mid_slope <= 0.02)

    # RCI52ホット
    thr_rci52 = float(params.get("P22_RCI52_MIN", 55.0))
    out["rci52_hot_eval"] = (pd.notna(rci_52) and rci_52 > thr_rci52)

    # ADX/RISK
    thr_adx = float(params.get("P22_ADX_MIN", 22.0))
    out["adx_ok_p22"] = (adx_now is not None) and pd.notna(adx_now) and (adx_now >= thr_adx)
    out["risk_ok_p22"] = bool(df.at[i, "filter_riskscore_passed_short"])

    return out


# ---------------------------------------------------------------------------
# check_entry_priority（CAT_v9_regime.py と完全一致）
# ---------------------------------------------------------------------------
def check_entry_priority(i: int, df: pd.DataFrame, params: Dict[str, Any] = None) -> Optional[int]:
    row = df.iloc[i]
    get = lambda col: df.at[i, col] if col in df.columns else np.nan

    # P4コア条件プローブ
    p4_core_ok = False
    try:
        bb_mid_slope = get("bb_mid_slope")
        close = get("close")
        ema20 = get("ema_20")
        if params is not None:
            p4_slope_min = float(params.get("P4_BB_MID_SLOPE_MIN", 0.0))
            lookback_pullback = int(params.get("P4_PULLBACK_LOOKBACK", 5))
            p4_ema_tol = float(params.get("P4_EMA_TOL", 0.001))
        else:
            p4_slope_min = 0.0
            lookback_pullback = 5
            p4_ema_tol = 0.001

        trend_ok_probe = (
            pd.notna(bb_mid_slope)
            and bb_mid_slope > p4_slope_min
            and pd.notna(close)
            and pd.notna(ema20)
            and close >= ema20
        )

        pullback_ok_probe = False
        for k in range(1, lookback_pullback + 1):
            j = i - k
            if j < 0:
                break
            low_j = df.at[j, "low"]
            ema20_j = df.at[j, "ema_20"]
            bb_mid_j = df.at[j, "bb_middle"]
            if pd.notna(low_j) and (
                (pd.notna(ema20_j) and low_j <= ema20_j)
                or (pd.notna(bb_mid_j) and low_j <= bb_mid_j)
            ):
                pullback_ok_probe = True
                break

        candle_ok_probe = (get("close") >= get("open"))
        p4_core_ok = bool(trend_ok_probe and pullback_ok_probe and candle_ok_probe)
    except Exception:
        p4_core_ok = False

    # 必須カラム確認
    required_cols = [
        "close", "open", "low",
        "ema_20", "bb_middle", "bb_mid_slope",
        "adx",
        "stoch_k", "stoch_d",
        "rci_7", "rci_9",
        "bb_sigma2_lower",
    ]
    if any(c not in df.columns for c in required_cols):
        return None

    close = row["close"]
    open_ = row["open"]
    low = row["low"]

    ema20 = row["ema_20"]
    bb_middle = row["bb_middle"]
    bb_mid_slope = row["bb_mid_slope"]
    adx = row["adx"]

    stoch_k = row["stoch_k"]
    stoch_d = row["stoch_d"]

    rci_7 = row["rci_7"]
    rci_9 = row["rci_9"]
    bb_lower = row["bb_sigma2_lower"]

    # 1本前の値
    if i > 0:
        prev = df.iloc[i - 1]
        ema20_prev = prev.get("ema_20", np.nan)
        rci_7_prev = prev.get("rci_7", np.nan)
        rci_9_prev = prev.get("rci_9", np.nan)
        low_prev = prev.get("low", np.nan)
        bb_lower_prev = prev.get("bb_sigma2_lower", np.nan)
    else:
        ema20_prev = np.nan
        rci_7_prev = np.nan
        rci_9_prev = np.nan
        low_prev = np.nan
        bb_lower_prev = np.nan

    bullish = pd.notna(close) and pd.notna(open_) and (close > open_)
    mid_up_ok = (pd.isna(bb_mid_slope) or bb_mid_slope >= 0.0)

    # =========================
    # 優先度 3（LONG・stoch ゴールデンクロス: P23-SHORTのミラー）[LONG側TOP]
    # =========================
    if params.get("ENABLE_P3_LONG", False) and (
        i >= 2
        and df["stoch_k"].iloc[i - 2] < df["stoch_d"].iloc[i - 2]
        and df["stoch_k"].iloc[i - 1] < df["stoch_d"].iloc[i - 1]
        and df["stoch_k"].iloc[i] > df["stoch_d"].iloc[i]
        and (df["stoch_k"].iloc[i] - df["stoch_d"].iloc[i]) > 0.3
        and df["close"].iloc[i] >= df["open"].iloc[i]
        and df["bb_mid_slope"].iloc[i] > float(params.get("P3_BB_MID_SLOPE_MIN", 10.0))
        and get("adx") >= float(params.get("P3_ADX_MIN", 30.0))
        and get("adx") < float(params.get("P3_ADX_MAX", 50.0))
        and get("atr_14") >= float(params.get("P3_ATR14_MIN", 250.0))
    ):
        return 3

    # =========================
    # 優先度 4（LONG）
    # =========================
    if "close" not in df.columns or "open" not in df.columns:
        return None

    required_cols = [
        "low",
        "ema_20",
        "bb_middle",
        "bb_mid_slope",
    ]
    for col in required_cols:
        if col not in df.columns:
            return None

    row = df.iloc[i]

    close = row["close"]
    open_ = row["open"]
    ema20 = row["ema_20"]
    bb_mid = row["bb_middle"]
    bb_mid_slope = row["bb_mid_slope"]

    if params is not None:
        lookback_pullback = int(params.get("P4_PULLBACK_LOOKBACK", 5))
        p4_ema_tol = float(params.get("P4_EMA_TOL", 0.001))
        p4_bb_mid_slope_min = float(params.get("P4_BB_MID_SLOPE_MIN", 0.0))
        p4_bb_mid_slope_mean5_min = float(params.get("P4_BB_MID_SLOPE_MEAN5_MIN", 0.0))
    else:
        lookback_pullback = 5
        p4_ema_tol = 0.001
        p4_bb_mid_slope_min = 0.0
        p4_bb_mid_slope_mean5_min = 0.0

    # 直近5バーの bb_mid_slope 平均
    _slope_window = df.iloc[max(0, i - 4):i + 1]["bb_mid_slope"]
    slope_mean_5 = float(_slope_window.mean()) if len(_slope_window) > 0 else 0.0

    if lookback_pullback < 1:
        lookback_pullback = 1

    pullback_ok = False
    for k in range(1, lookback_pullback + 1):
        j = i - k
        if j < 0:
            break

        low_j = df.at[j, "low"]
        ema20_j = df.at[j, "ema_20"]
        bb_mid_j = df.at[j, "bb_middle"]

        if pd.notna(low_j):
            ema_hit = pd.notna(ema20_j) and low_j <= ema20_j * (1.0 + p4_ema_tol)
            mid_hit = pd.notna(bb_mid_j) and low_j <= bb_mid_j * (1.0 + p4_ema_tol)
            if ema_hit or mid_hit:
                pullback_ok = True
                break

    # 順張り位置
    trend_ok = (
        pd.notna(close)
        and pd.notna(ema20)
        and close >= ema20
    )

    # 継続性
    cont_ok = (
        pd.notna(bb_mid_slope)
        and bb_mid_slope >= p4_bb_mid_slope_min
        and slope_mean_5 >= p4_bb_mid_slope_mean5_min
    )

    # 勢い（陽線または同値）
    candle_ok = (
        pd.notna(close)
        and pd.notna(open_)
        and close >= open_
    )

    entry_ok_flag = bool(row.get("entry_ok_long", True))

    if params.get("ENABLE_P4_LONG", True) \
            and pullback_ok and trend_ok and cont_ok and candle_ok and entry_ok_flag \
            and get("rsi_short") <= float(params.get("P4_RSI_MAX", 100.0)) \
            and get("atr_14") >= float(params.get("P4_ATR14_MIN", 0.0)) \
            and get("atr_14") <= float(params.get("P4_ATR14_MAX", 999999.0)) \
            and not (float(params.get("P4_ADX_EXCL_MIN", 0.0)) <= get("adx") < float(params.get("P4_ADX_EXCL_MAX", 0.0))):
        return 4

    # =========================
    # 優先度 2（LONG）
    # =========================
    stoch_cross = (
        i >= 2
        and pd.notna(df.at[i - 2, "stoch_k"]) and pd.notna(df.at[i - 2, "stoch_d"])
        and pd.notna(df.at[i - 1, "stoch_k"]) and pd.notna(df.at[i - 1, "stoch_d"])
        and pd.notna(get("stoch_k")) and pd.notna(get("stoch_d"))
        and pd.notna(get("open")) and pd.notna(get("close"))
        and df.at[i - 2, "stoch_k"] < df.at[i - 2, "stoch_d"]
        and df.at[i - 1, "stoch_k"] < df.at[i - 1, "stoch_d"]
        and get("stoch_k") > get("stoch_d")
        and (get("stoch_k") - get("stoch_d")) > float(params.get("P2_STOCH_GAP_MIN", 0.3))
        and get("close") >= get("open")
    )

    if params.get("ENABLE_P2_LONG", True) and (stoch_cross
            and get("stoch_k") >= float(params.get("P2_STOCH_K_MIN", 0.0))
            and get("adx") >= float(params.get("P2_ADX_MIN", 0.0))
            and get("adx") <= float(params.get("P2_ADX_MAX", 999999.0))
            and get("rsi_short") >= float(params.get("P2_RSI_MIN", 0.0))
            and get("atr_14") >= float(params.get("P2_ATR14_MIN", 0.0))
            and get("atr_14") <= float(params.get("P2_ATR14_MAX", 999999.0))
            and not (float(params.get("P2_ADX_EXCL_MIN", 0.0)) <= get("adx") < float(params.get("P2_ADX_EXCL_MAX", 0.0)))):
        return 2

    # =========================
    # 優先度 23（SHORT・stoch デッドクロス）[SHORT側TOP]
    # =========================
    if params.get("ENABLE_P23_SHORT", False) and (
        i >= 2
        and df["stoch_k"].iloc[i - 2] > df["stoch_d"].iloc[i - 2]
        and df["stoch_k"].iloc[i - 1] > df["stoch_d"].iloc[i - 1]
        and df["stoch_k"].iloc[i] < df["stoch_d"].iloc[i]
        and df["stoch_k"].iloc[i] <= float(params.get("P23_STOCH_K_MAX", 999.0))
        and (df["stoch_d"].iloc[i] - df["stoch_k"].iloc[i]) > 0.3
        and df["close"].iloc[i] <= df["open"].iloc[i]
        and df["bb_mid_slope"].iloc[i] < float(params.get("P23_BB_MID_SLOPE_MAX", 0.0))
        and get("adx") >= float(params.get("P23_ADX_MIN", 0.0))
        and get("adx") < float(params.get("P23_ADX_MAX", 9999.0))
        and get("atr_14") >= float(params.get("P23_ATR14_MIN", 0.0))
    ):
        return 23

    # =========================
    # 優先度 22（SHORT）
    # =========================
    probe = compute_p22_probe(i, df, params)

    cross_mid = (probe["rci_cross"] and probe["bb_upper_touch"] and probe["mid_down_ok"])
    core_gate = (cross_mid or probe["rci52_hot_eval"])

    _p22_slope_max = float(params.get("P22_SHORT_BB_MID_SLOPE_MAX", 999.0))
    _p22_slope_val = df.at[i, "bb_mid_slope"] if "bb_mid_slope" in df.columns else np.nan
    _p22_slope_ok = pd.isna(_p22_slope_val) or (float(_p22_slope_val) <= _p22_slope_max)

    _p22_bb_width_max = float(params.get("P22_SHORT_BB_WIDTH_MAX", 999.0))
    _p22_bb_width_val = df.at[i, "bb_width"] if "bb_width" in df.columns else np.nan
    _p22_bb_width_ok = pd.isna(_p22_bb_width_val) or (float(_p22_bb_width_val) <= _p22_bb_width_max)

    if params.get("ENABLE_P22_SHORT", True) and core_gate and probe["adx_ok_p22"] and probe["risk_ok_p22"] and _p22_slope_ok and _p22_bb_width_ok:
        return 22

    _p22_adx_relax_min = float(params.get("P22_ADX_RELAX_MIN", 0.0))
    _p22_adx_val = df.at[i, "adx"] if "adx" in df.columns else np.nan
    _p22_adx_relax_ok = pd.isna(_p22_adx_val) or (float(_p22_adx_val) >= _p22_adx_relax_min)
    if (params.get("ENABLE_P22_SHORT", True) and int(params.get("P22_RELAX_FINAL", 1)) == 1 and core_gate and _p22_slope_ok and _p22_bb_width_ok
            and _p22_adx_relax_ok):
        return 22

    # =========================
    # 優先度 24（SHORT）
    # =========================
    if params.get("ENABLE_P24_SHORT", False):
        _p24_rsi_min   = float(params.get("P24_RSI_MIN",        65.0))
        _p24_slope_max = float(params.get("P24_BB_SLOPE_MAX",   50.0))
        _p24_stoch_min = float(params.get("P24_STOCH_MIN",      60.0))
        _p24_rsi_val   = df.at[i, "rsi_short"]       if "rsi_short"       in df.columns else np.nan
        _p24_rsi_slope = df.at[i, "rsi_slope_short"] if "rsi_slope_short" in df.columns else np.nan
        _p24_slope_val = df.at[i, "bb_mid_slope"]    if "bb_mid_slope"    in df.columns else np.nan
        _p24_sk_val    = df.at[i, "stoch_k"]         if "stoch_k"         in df.columns else np.nan
        _p24_close     = df.at[i, "close"]           if "close"           in df.columns else np.nan
        _p24_open      = df.at[i, "open"]            if "open"            in df.columns else np.nan
        if (
            pd.notna(_p24_rsi_val)   and _p24_rsi_val   > _p24_rsi_min
            and pd.notna(_p24_rsi_slope) and _p24_rsi_slope < 0.0
            and pd.notna(_p24_slope_val) and _p24_slope_val < _p24_slope_max
            and pd.notna(_p24_sk_val)    and _p24_sk_val   > _p24_stoch_min
            and pd.notna(_p24_close) and pd.notna(_p24_open) and _p24_close < _p24_open
            and get("atr_14") >= float(params.get("P24_ATR14_MIN", 0.0))
        ):
            return 24

    # =========================
    # 優先度 1（LONG・スキャル: MACD ゴールデンクロス）
    # =========================
    if params.get("ENABLE_P1_LONG", False) and i > 0:
        _p1_macd_prev = df.at[i - 1, "macd"]        if "macd"        in df.columns else float("nan")
        _p1_msig_prev = df.at[i - 1, "macd_signal"] if "macd_signal" in df.columns else float("nan")
        _p1_macd = get("macd"); _p1_msig = get("macd_signal")
        _p1_adx  = get("adx");  _p1_atr  = get("atr_14")
        if (pd.notna(_p1_macd_prev) and pd.notna(_p1_msig_prev)
                and pd.notna(_p1_macd) and pd.notna(_p1_msig)
                and _p1_macd_prev <= _p1_msig_prev
                and _p1_macd > _p1_msig
                and pd.notna(_p1_adx) and _p1_adx >= float(params.get("P1_ADX_MIN", 22.0))
                and pd.notna(_p1_atr)
                and _p1_atr >= float(params.get("P1_ATR14_MIN", 60.0))
                and _p1_atr <= float(params.get("P1_ATR14_MAX", 150.0))):
            return 1

    # =========================
    # 優先度 21（SHORT・スキャル: MACD デッドクロス）
    # =========================
    if params.get("ENABLE_P21_SHORT", False) and i > 0:
        _p21_macd_prev = df.at[i - 1, "macd"]        if "macd"        in df.columns else float("nan")
        _p21_msig_prev = df.at[i - 1, "macd_signal"] if "macd_signal" in df.columns else float("nan")
        _p21_macd = get("macd"); _p21_msig = get("macd_signal")
        _p21_adx  = get("adx");  _p21_atr  = get("atr_14")
        if (pd.notna(_p21_macd_prev) and pd.notna(_p21_msig_prev)
                and pd.notna(_p21_macd) and pd.notna(_p21_msig)
                and _p21_macd_prev >= _p21_msig_prev
                and _p21_macd < _p21_msig
                and pd.notna(_p21_adx) and _p21_adx >= float(params.get("P21_ADX_MIN", 22.0))
                and pd.notna(_p21_atr)
                and _p21_atr >= float(params.get("P21_ATR14_MIN", 60.0))
                and _p21_atr <= float(params.get("P21_ATR14_MAX", 9999))):
            return 21

    return None


# ---------------------------------------------------------------------------
# decide（新規：snapshot dict → decision dict）
# ---------------------------------------------------------------------------
_LONG_PRIORITIES  = (1, 2, 3, 4)
_SHORT_PRIORITIES = (21, 22, 23, 24)


def decide(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """
    snapshot dict からエントリー判断を返す（発注・Exit は runner の責務）。

    入力:
        snapshot["candles_5m"]: [[ts_ms, open, high, low, close, vol, quoteVol], ...]
        snapshot["params"]    : cat_params_v9.json の内容

    返却:
        {
            "action"        : "ENTER" | "NOOP" | "STOP",
            "reason"        : str,
            "side"          : "LONG" | "SHORT",
            "entry_priority": int | None,
            "material"      : dict,   # ENTERのとき
        }
    """
    params = snapshot.get("params") or {}
    if not isinstance(params, dict):
        params = {}

    candles_5m = snapshot.get("candles_5m") or []
    if not isinstance(candles_5m, list) or len(candles_5m) < 30:
        return {
            "action": "STOP",
            "reason": "cat_v9_decider: insufficient candles_5m (<30)",
            "side": "LONG",
        }

    # Bitget API 形式 [ts_ms, open, high, low, close, vol, quoteVol] → DataFrame
    rows = []
    for row in candles_5m:
        if not isinstance(row, list) or len(row) < 5:
            continue
        try:
            rows.append({
                "timestamp": pd.to_datetime(int(row[0]), unit="ms"),
                "open":   float(row[1]),
                "high":   float(row[2]),
                "low":    float(row[3]),
                "close":  float(row[4]),
                "volume": float(row[5]) if len(row) > 5 else 0.0,
            })
        except Exception:
            continue

    if len(rows) < 30:
        return {
            "action": "STOP",
            "reason": "cat_v9_decider: candles parse failed (<30 valid rows)",
            "side": "LONG",
        }

    df = pd.DataFrame(rows)
    df = df.sort_values("timestamp").reset_index(drop=True)

    try:
        df = preprocess(df, params)
    except Exception as e:
        return {
            "action": "STOP",
            "reason": f"cat_v9_decider: preprocess failed: {e}",
            "side": "LONG",
        }

    i = len(df) - 1

    try:
        priority = check_entry_priority(i, df, params)
    except Exception as e:
        return {
            "action": "STOP",
            "reason": f"cat_v9_decider: check_entry_priority failed: {e}",
            "side": "LONG",
        }

    if priority is None:
        # NOOP: デバッグ用に最終足の主要値を残す
        row = df.iloc[i]
        return {
            "action": "NOOP",
            "reason": "cat_v9_decider:no_entry",
            "side": "LONG",
            "debug": {
                "close":        _safe_float(row.get("close")),
                "open":         _safe_float(row.get("open")),
                "bb_mid_slope": _safe_float(row.get("bb_mid_slope")),
                "adx":          _safe_float(row.get("adx")),
                "ema_20":       _safe_float(row.get("ema_20")),
                "stoch_k":      _safe_float(row.get("stoch_k")),
                "stoch_d":      _safe_float(row.get("stoch_d")),
                "rci_7":        _safe_float(row.get("rci_7")),
                "rci_9":        _safe_float(row.get("rci_9")),
                "entry_ok_long": bool(row.get("entry_ok_long", False)),
            },
        }

    side = "LONG" if priority in _LONG_PRIORITIES else "SHORT"
    material = _build_material(priority, i, df, params)

    return {
        "action":         "ENTER",
        "reason":         f"cat_v9_decider:p{priority}",
        "side":           side,
        "entry_priority": int(priority),
        "material":       material,
    }


def _safe_float(v: Any) -> Any:
    try:
        f = float(v)
        return None if (f != f) else f  # NaN → None
    except Exception:
        return None


def _build_material(priority: int, i: int, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
    """発火した priority の成立材料（証跡用）"""
    row = df.iloc[i]
    g = lambda col: _safe_float(df.at[i, col] if col in df.columns else float("nan"))

    if priority == 1:
        return {
            "macd":        g("macd"),
            "macd_signal": g("macd_signal"),
            "adx":         g("adx"),
            "atr_14":      g("atr_14"),
            "P1_ADX_MIN":  float(params.get("P1_ADX_MIN", 22.0)),
        }

    if priority == 21:
        return {
            "macd":         g("macd"),
            "macd_signal":  g("macd_signal"),
            "adx":          g("adx"),
            "atr_14":       g("atr_14"),
            "P21_ADX_MIN":  float(params.get("P21_ADX_MIN", 22.0)),
        }

    if priority == 4:
        lookback = int(params.get("P4_PULLBACK_LOOKBACK", 5))
        p4_ema_tol = float(params.get("P4_EMA_TOL", 0.001))
        _slope_window = df.iloc[max(0, i - 4):i + 1]["bb_mid_slope"]
        slope_mean_5 = float(_slope_window.mean()) if len(_slope_window) > 0 else float("nan")
        return {
            "close":             g("close"),
            "open":              g("open"),
            "ema_20":            g("ema_20"),
            "bb_mid_slope":      g("bb_mid_slope"),
            "slope_mean_5":      _safe_float(slope_mean_5),
            "P4_BB_MID_SLOPE_MIN": float(params.get("P4_BB_MID_SLOPE_MIN", 0.0)),
            "P4_BB_MID_SLOPE_MEAN5_MIN": float(params.get("P4_BB_MID_SLOPE_MEAN5_MIN", 0.0)),
            "entry_ok_long":     bool(row.get("entry_ok_long", False)),
        }

    if priority == 2:
        return {
            "stoch_k":      g("stoch_k"),
            "stoch_d":      g("stoch_d"),
            "stoch_k_prev": _safe_float(df.at[i - 1, "stoch_k"] if i > 0 else float("nan")),
            "stoch_d_prev": _safe_float(df.at[i - 1, "stoch_d"] if i > 0 else float("nan")),
            "diff":         _safe_float((g("stoch_k") or 0.0) - (g("stoch_d") or 0.0)),
            "P2_STOCH_GAP_MIN": float(params.get("P2_STOCH_GAP_MIN", 0.3)),
        }

    if priority == 22:
        probe = compute_p22_probe(i, df, params)
        return {
            "probe":        probe,
            "bb_mid_slope": g("bb_mid_slope"),
            "bb_width":     g("bb_width"),
            "rci_7":        g("rci_7"),
            "rci_9":        g("rci_9"),
            "rci_52":       g("rci_52"),
            "adx":          g("adx"),
        }

    if priority == 3:
        k0 = g("stoch_k")
        d0 = g("stoch_d")
        return {
            "stoch_k": k0,
            "stoch_d": d0,
            "gap":     _safe_float((k0 or 0.0) - (d0 or 0.0)),
            "bullish": bool((g("close") or 0.0) >= (g("open") or 0.0)),
        }

    if priority == 23:
        k0 = g("stoch_k")
        d0 = g("stoch_d")
        return {
            "stoch_k": k0,
            "stoch_d": d0,
            "gap":     _safe_float((d0 or 0.0) - (k0 or 0.0)),
            "bearish": bool((g("close") or 0.0) <= (g("open") or 0.0)),
        }

    if priority == 24:
        return {
            "rsi_short":       g("rsi_short"),
            "rsi_slope_short": g("rsi_slope_short"),
            "stoch_k":         g("stoch_k"),
            "bb_mid_slope":    g("bb_mid_slope"),
            "close":           g("close"),
            "open":            g("open"),
            "P24_RSI_MIN":     float(params.get("P24_RSI_MIN", 65.0)),
            "P24_STOCH_MIN":   float(params.get("P24_STOCH_MIN", 60.0)),
        }

    return {}
