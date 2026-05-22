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
    f["close_vs_tenkan_pct"] = (c - f["ichimoku_tenkan"]) / f["ichimoku_tenkan"] * 100  # 2026-05-19 追加・価格非依存性 #4
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

    # Phase 0 v3.1 Step 4 §2.1 #1 A-1 欠損指標補完 (2026-05-22)
    # RCI 4 種 (cat/indicators.py calculate_rci 流用) + RSI(21) + RSI_slope + BB_slope
    from cat.indicators import calculate_rci

    # RCI(7) / RCI(9) / RCI(26) / RCI(52)
    for w in (7, 9, 26, 52):
        f[f"rci_{w}"] = calculate_rci(c, w)

    # RSI(21) — build_indicators の rsi14/rsi7 と同じ Wilder EMA パターン
    delta = c.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain_21 = gain.ewm(alpha=1 / 21, adjust=False).mean()
    avg_loss_21 = loss.ewm(alpha=1 / 21, adjust=False).mean()
    rs_21 = avg_gain_21 / avg_loss_21.replace(0, np.nan)
    f["rsi21"] = 100 - (100 / (1 + rs_21))

    # RSI_slope (rsi14 14 bar 変化・既存 rsi14 列前提)
    if "rsi14" in f.columns:
        f["rsi14_slope_14b"] = f["rsi14"] - f["rsi14"].shift(14)

    # BB_slope (bb_width_pct 20 bar 変化・既存 bb_width_pct 列前提)
    if "bb_width_pct" in f.columns:
        f["bb_width_slope_20b"] = f["bb_width_pct"] - f["bb_width_pct"].shift(20)

    # Phase 0 v3.1 Step 4 §2.1 #2 まこさん発振系 3 件 (2026-05-22・+18 列)
    # RSI ROC 5 bar (RSI 自体が pct なので diff = 変化率)
    if "rsi14" in f.columns:
        f["rsi14_roc_5b"] = f["rsi14"] - f["rsi14"].shift(5)
    # Stoch K-D 差分 (cross 検出用)
    if "stoch_k" in f.columns and "stoch_d" in f.columns:
        f["stoch_kd_diff"] = f["stoch_k"] - f["stoch_d"]
    # MACD ヒストグラム slope 5 bar
    if "macd_hist" in f.columns:
        f["macd_hist_slope_5b"] = f["macd_hist"] - f["macd_hist"].shift(5)

    # Phase 0 v3.1 Step 4 §2.1 #8 A-3 パラメータ並列展開 (2026-05-22・+96 列)
    import ta as _ta

    # RSI parallel: rsi9 / rsi28 (rsi21 は §2.1 #1 で対応済・rsi14/rsi7 は build_indicators 既存)
    _delta = c.diff()
    _gain = _delta.clip(lower=0)
    _loss = -_delta.clip(upper=0)
    for _w in (9, 28):
        _ag = _gain.ewm(alpha=1 / _w, adjust=False).mean()
        _al = _loss.ewm(alpha=1 / _w, adjust=False).mean()
        _rs = _ag / _al.replace(0, np.nan)
        f[f"rsi{_w}"] = 100 - (100 / (1 + _rs))

    # ADX parallel: adx7 / adx21 (build_indicators の adx14 と並列)
    # ta library は data size < window の時 IndexError → 安全に NaN 列で埋める (sample 用)
    for _w in (7, 21):
        try:
            f[f"adx{_w}"] = _ta.trend.ADXIndicator(high=h, low=l, close=c, window=_w).adx()
        except (IndexError, ValueError):
            f[f"adx{_w}"] = pd.Series(np.nan, index=c.index)

    # BB parallel: window=10 / 50 (build_indicators の window=20 と並列・pct 化)
    for _w in (10, 50):
        try:
            _bb = _ta.volatility.BollingerBands(close=c, window=_w)
            _upper = _bb.bollinger_hband()
            _lower = _bb.bollinger_lband()
            _width = _upper - _lower
            f[f"bb_width_pct_w{_w}"] = (_width / c) * 100
            f[f"bb_pct_b_w{_w}"] = (c - _lower) / _width.replace(0, np.nan)
        except (IndexError, ValueError):
            f[f"bb_width_pct_w{_w}"] = pd.Series(np.nan, index=c.index)
            f[f"bb_pct_b_w{_w}"] = pd.Series(np.nan, index=c.index)

    # MACD parallel: 短期 (5,13,5) + 長期 (19,39,9)・全 pct 化 (price 非依存性)
    for _tag, (_fast, _slow, _sig) in [("short", (5, 13, 5)), ("long", (19, 39, 9))]:
        try:
            _m = _ta.trend.MACD(close=c, window_fast=_fast, window_slow=_slow, window_sign=_sig)
            _line = _m.macd()
            _sig_ser = _m.macd_signal()
            _hist = _m.macd_diff()
            f[f"macd_line_pct_{_tag}"] = (_line / c) * 100
            f[f"macd_signal_pct_{_tag}"] = (_sig_ser / c) * 100
            f[f"macd_hist_pct_{_tag}"] = (_hist / c) * 100
            f[f"macd_hist_change_pct_{_tag}"] = ((_hist - _hist.shift(1)) / c) * 100
        except (IndexError, ValueError):
            for _name in ("line", "signal", "hist", "hist_change"):
                f[f"macd_{_name}_pct_{_tag}"] = pd.Series(np.nan, index=c.index)

    # Phase 0 v3.1 Step 4 §2.2 #14 SMC 手書き簡略 (2026-05-22・+40 列)
    # smart-money-concepts ライブラリ PyPI 不存在のため手書き実装:
    # - BOS (Break of Structure): rolling 20 bar の high/low break
    # - FVG (Fair Value Gap): 3 bar pattern (i: low > i-2: high など)
    # - Order Block displacement pct: 直近 swing からの移動 pct
    # 厳密な SMC (joshyattridge/smart-money-concepts) は Phase 4-b で再評価候補
    _rh20_smc = h.rolling(20, min_periods=5).max()
    _rl20_smc = l.rolling(20, min_periods=5).min()
    f["bos_up_bool"] = (c > _rh20_smc.shift(1)).astype(np.int8)
    f["bos_down_bool"] = (c < _rl20_smc.shift(1)).astype(np.int8)
    f["fvg_up_bool"] = (l > h.shift(2)).astype(np.int8)
    f["fvg_down_bool"] = (h < l.shift(2)).astype(np.int8)
    f["ob_displacement_up_pct"] = ((c - _rl20_smc.shift(1)) / c * 100).clip(lower=0)

    # Phase 0 v3.1 Step 4 §2.3 #17 Supply/Demand Zone 簡略 (2026-05-22・+24 列)
    # rolling 50 bar swing high/low をベースに Supply/Demand 距離 + zone 幅
    # 厳密な swing 検出 (pivot fractal) は Phase 4-b で再評価候補
    _rh50_sd = h.rolling(50, min_periods=10).max()
    _rl50_sd = l.rolling(50, min_periods=10).min()
    f["dist_to_supply_50b_pct"] = (_rh50_sd - c) / c * 100
    f["dist_to_demand_50b_pct"] = (c - _rl50_sd) / c * 100
    f["zone_range_50b_pct"] = (_rh50_sd - _rl50_sd) / c * 100

    # Phase 0 v3.1 Step 4 §2.1 #9 cat_v9 共通フィルタ + 主要閾値距離 pct (2026-05-22・+56 列)
    # cat/indicators.py compute_indicators の location_prev / entry_risk_score / entry_ok_long を再現
    # + RSI 70/30, Stoch 80/20, ADX 25 の閾値距離 pct (自己実現的閾値・データ駆動再検討用)
    _rh20 = h.rolling(20, min_periods=1).max()
    _rl20 = l.rolling(20, min_periods=1).min()
    _loc_denom = (_rh20 - _rl20).replace(0, np.nan)
    f["location_prev_20b"] = ((c - _rl20) / _loc_denom).shift(1).fillna(0.5)
    _vola_20 = c.rolling(20, min_periods=5).std()
    f["entry_risk_score_20b"] = (_vola_20 / c).clip(lower=0)
    # cat_v9 default 閾値 (cat/indicators.py L84-86)
    f["entry_ok_long_v9_bool"] = (
        (f["location_prev_20b"] <= 0.9)
        & (f["entry_risk_score_20b"] <= 0.3398)
        & (f["entry_risk_score_20b"] >= 0.0007)
    ).astype(np.int8)
    # SHORT 側は対称想定 (location 高 + 同 risk 範囲)
    f["entry_ok_short_v9_bool"] = (
        (f["location_prev_20b"] >= 0.1)
        & (f["entry_risk_score_20b"] <= 0.3398)
        & (f["entry_risk_score_20b"] >= 0.0007)
    ).astype(np.int8)

    # 主要閾値距離 pct (連続値・自己実現的閾値の連続値併存・LightGBM 分岐学習用)
    if "rsi14" in f.columns:
        f["rsi14_dist_70_pct"] = (f["rsi14"] - 70.0) / 70.0 * 100
        f["rsi14_dist_30_pct"] = (f["rsi14"] - 30.0) / 30.0 * 100
    else:
        f["rsi14_dist_70_pct"] = pd.Series(np.nan, index=c.index)
        f["rsi14_dist_30_pct"] = pd.Series(np.nan, index=c.index)
    if "stoch_k" in f.columns:
        f["stoch_k_dist_80_pct"] = (f["stoch_k"] - 80.0) / 80.0 * 100
        f["stoch_k_dist_20_pct"] = (f["stoch_k"] - 20.0) / 20.0 * 100
    else:
        f["stoch_k_dist_80_pct"] = pd.Series(np.nan, index=c.index)
        f["stoch_k_dist_20_pct"] = pd.Series(np.nan, index=c.index)
    if "adx14" in f.columns:
        f["adx14_dist_25_pct"] = (f["adx14"] - 25.0) / 25.0 * 100
    else:
        f["adx14_dist_25_pct"] = pd.Series(np.nan, index=c.index)

    # Phase 0 v3.1 Step 4 §2.1 #3 業界カタログ追加 (2026-05-22・ta library 経由・+80 列想定)
    # pandas-ta-classic で 200+ 個別選定は工数大のため、ta library (既使用) で代表 10 indicator 選定。
    # 全 8 TF で計算・try/except で size 不足対応。
    _industry_indicators = [
        ("trix_14", lambda: _ta.trend.TRIXIndicator(close=c, window=14).trix()),
        ("aroon_up_25", lambda: _ta.trend.AroonIndicator(high=h, low=l, window=25).aroon_up()),
        ("aroon_down_25", lambda: _ta.trend.AroonIndicator(high=h, low=l, window=25).aroon_down()),
        ("vortex_pos_14", lambda: _ta.trend.VortexIndicator(high=h, low=l, close=c, window=14).vortex_indicator_pos()),
        ("vortex_neg_14", lambda: _ta.trend.VortexIndicator(high=h, low=l, close=c, window=14).vortex_indicator_neg()),
        ("tsi_25_13", lambda: _ta.momentum.TSIIndicator(close=c, window_slow=25, window_fast=13).tsi()),
        ("uo_7_14_28", lambda: _ta.momentum.UltimateOscillator(high=h, low=l, close=c, window1=7, window2=14, window3=28).ultimate_oscillator()),
        ("ao", lambda: _ta.momentum.AwesomeOscillatorIndicator(high=h, low=l).awesome_oscillator()),
        ("ppo", lambda: _ta.momentum.PercentagePriceOscillator(close=c, window_slow=26, window_fast=12, window_sign=9).ppo()),
        ("ulcer_index_14", lambda: _ta.volatility.UlcerIndex(close=c, window=14).ulcer_index()),
        ("force_index_13", lambda: _ta.volume.ForceIndexIndicator(close=c, volume=v, window=13).force_index()),
        ("eom_14", lambda: _ta.volume.EaseOfMovementIndicator(high=h, low=l, volume=v, window=14).ease_of_movement()),
        ("nvi", lambda: _ta.volume.NegativeVolumeIndexIndicator(close=c, volume=v).negative_volume_index()),
    ]
    for _name, _fn in _industry_indicators:
        try:
            f[_name] = _fn()
        except (IndexError, ValueError, AttributeError):
            f[_name] = pd.Series(np.nan, index=c.index)

    # Phase 0 v3.1 Step 4 §2.1 #6 Fractional differentiation 自前実装 (2026-05-22・+64 列)
    # Lopez de Prado AFML Ch.5: w_0 = 1 / w_k = -w_{k-1} × (d - k + 1) / k
    # past-only weighted sum (look-ahead 防止・各 i で過去 N bar のみ参照)
    def _fracdiff_weights(d, threshold=1e-4, max_size=2000):
        wts = [1.0]
        for _k in range(1, max_size):
            _wk = -wts[-1] * (d - _k + 1) / _k
            if abs(_wk) < threshold:
                break
            wts.append(_wk)
        return np.array(wts)

    def _fracdiff_series(series, d, threshold=1e-4):
        _w = _fracdiff_weights(d, threshold)
        _n = len(_w)
        _arr = series.to_numpy(dtype=np.float64)
        if _n >= len(_arr):
            return pd.Series(np.nan, index=series.index)
        _w_rev = _w[::-1]  # w[0] が最新・w[k] が k bar 過去 → reverse して dot 内積
        _result = np.full(len(_arr), np.nan)
        for _i in range(_n - 1, len(_arr)):
            _window = _arr[_i - _n + 1 : _i + 1]
            if not np.isnan(_window).any():
                _result[_i] = np.dot(_w_rev, _window)
        return pd.Series(_result, index=series.index, dtype=np.float32)

    for _d in (0.3, 0.5):
        _d_tag = int(_d * 10)
        for _series_name, _series in [("close", c), ("high", h), ("low", l), ("volume", v)]:
            f[f"fracdiff_{_series_name}_d{_d_tag}"] = _fracdiff_series(_series, _d)

    # Phase 0 v3.1 Step 4 §2.3 #20 Candlestick patterns 62 種 (2026-05-22・5m TF 主体・+62 列)
    # pandas-ta-classic の DataFrame extension で 62 patterns 一括計算 (TA-Lib ベース)
    # 値: -100 (bearish) / 0 (none) / +100 (bullish)・LightGBM 自動分岐学習
    # 注意: 以後 build_labels_pct.py は .venv/bin/python3 経由必須 (pandas-ta-classic 依存)
    try:
        import pandas_ta_classic as _ta_cl  # noqa: F401 (DataFrame extension 登録副作用)
        _cdl_df = df.ta.cdl_pattern(name="all")
        if _cdl_df is not None and not _cdl_df.empty:
            for _col in _cdl_df.columns:
                f[_col.lower()] = _cdl_df[_col].astype(np.int8)
    except (ImportError, ValueError, TypeError, IndexError, AttributeError):
        pass  # pandas-ta-classic 不在 or データ不足時 skip

    # Phase 0 v3.1 Step 4 §2.2 #15 Chandelier Exit (2026-05-22・+12 列)
    # CE_long = Highest High(22) - 3×ATR(22) / CE_short = Lowest Low(22) + 3×ATR(22)
    # USD 絶対値は pruned 登録せず・距離 pct のみ登録 (price 非依存性遵守)
    _tr22 = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    _atr22 = _tr22.ewm(alpha=1 / 22, adjust=False).mean()
    _ce_long = h.rolling(22).max() - 3 * _atr22
    _ce_short = l.rolling(22).min() + 3 * _atr22
    f["dist_to_ce_long_pct"] = (c - _ce_long) / c * 100
    f["dist_to_ce_short_pct"] = (_ce_short - c) / c * 100

    # Phase 0 v3.1 Step 4 §2.2 #16 Fib Extension (2026-05-22・+18 列)
    # rolling 50 bar swing range × {1.27, 1.61, 2.61}・swing_high 起点
    _swing_h_50 = h.rolling(50).max()
    _swing_l_50 = l.rolling(50).min()
    _swing_range = _swing_h_50 - _swing_l_50
    for _ext_pct in (127, 161, 261):
        _ratio = (_ext_pct / 100.0) - 1.0  # 1.27 → 0.27 above swing_high
        _level = _swing_h_50 + _swing_range * _ratio
        f[f"dist_to_fib_ext_{_ext_pct}_pct"] = (_level - c) / c * 100

    # Phase 0 v3.1 Step 4 §2.3 #18 KDJ J 線 (2026-05-22・+18 列)
    # J = 3K - 2D (Stoch K/D 既存)・3 層 (連続 value + 連続 zscore + Adaptive bool)
    if "stoch_k" in f.columns and "stoch_d" in f.columns:
        _kdj_j = 3 * f["stoch_k"] - 2 * f["stoch_d"]
        f["kdj_j_value"] = _kdj_j
        _kdj_mean = _kdj_j.rolling(100, min_periods=20).mean()
        _kdj_std = _kdj_j.rolling(100, min_periods=20).std()
        f["kdj_j_zscore_100b"] = (_kdj_j - _kdj_mean) / _kdj_std.replace(0, np.nan)
        f["kdj_j_overbought_adaptive_z2"] = (f["kdj_j_zscore_100b"] > 2).astype(np.int8)
    else:
        f["kdj_j_value"] = pd.Series(np.nan, index=c.index)
        f["kdj_j_zscore_100b"] = pd.Series(np.nan, index=c.index)
        f["kdj_j_overbought_adaptive_z2"] = pd.Series(0, index=c.index, dtype=np.int8)

    # Phase 0 v3.1 Step 4 §2.2 #13 BB Squeeze + Band Walk (2026-05-22・+30 列)
    # 3 層併存 (連続値 + Adaptive bool + 自己実現的 bool)
    try:
        _bb20 = _ta.volatility.BollingerBands(close=c, window=20)
        _bb_upper = _bb20.bollinger_hband()
        _bb_lower = _bb20.bollinger_lband()
        f["close_vs_bb_upper_dist_pct"] = (c - _bb_upper) / c * 100
        f["close_vs_bb_lower_dist_pct"] = (c - _bb_lower) / c * 100
    except (IndexError, ValueError):
        f["close_vs_bb_upper_dist_pct"] = pd.Series(np.nan, index=c.index)
        f["close_vs_bb_lower_dist_pct"] = pd.Series(np.nan, index=c.index)

    if "bb_width_pct" in f.columns:
        f["bb_bw_rolling_p20_100b"] = f["bb_width_pct"].rolling(100, min_periods=20).quantile(0.20)
        f["bb_squeeze_adaptive_p20"] = (f["bb_width_pct"] < f["bb_bw_rolling_p20_100b"]).astype(np.int8)
        # 自己実現的閾値 5% (BTC 実測適合・ナレッジベース v3 §I.6.2 整合・10% は削除済)
        f["bb_squeeze_sf_5pct"] = (f["bb_width_pct"] < 5.0).astype(np.int8)
    else:
        f["bb_bw_rolling_p20_100b"] = pd.Series(np.nan, index=c.index)
        f["bb_squeeze_adaptive_p20"] = pd.Series(0, index=c.index, dtype=np.int8)
        f["bb_squeeze_sf_5pct"] = pd.Series(0, index=c.index, dtype=np.int8)

    # Phase 0 v3.1 Step 4 §2.1 #11 Divergence bool 簡略実装 (2026-05-22・+36 列)
    # Regular Bull (反転示唆): price 下落 + osc 上昇 / Regular Bear: price 上昇 + osc 下落
    # Hidden は pivot 検出が必要なため Phase 4-b で再評価候補 (簡略実装では Regular のみ)
    _div_N = 14
    _oscs = ["rsi14", "stoch_k", "macd_hist_pct"]
    _pc = c - c.shift(_div_N)
    for _osc_name in _oscs:
        if _osc_name in f.columns:
            _oc = f[_osc_name] - f[_osc_name].shift(_div_N)
            f[f"div_{_osc_name}_reg_bull_{_div_N}b"] = ((_pc < 0) & (_oc > 0)).astype(np.int8)
            f[f"div_{_osc_name}_reg_bear_{_div_N}b"] = ((_pc > 0) & (_oc < 0)).astype(np.int8)
        else:
            f[f"div_{_osc_name}_reg_bull_{_div_N}b"] = pd.Series(0, index=c.index, dtype=np.int8)
            f[f"div_{_osc_name}_reg_bear_{_div_N}b"] = pd.Series(0, index=c.index, dtype=np.int8)

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
