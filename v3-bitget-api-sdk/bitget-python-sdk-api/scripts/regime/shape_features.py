"""shape_features.py — 段階1-B 形状特徴量計算

カテゴリ B-1〜B-5 の関数群。窓 W に依存する特徴量を OHLCV から計算する。

B-1 高値・安値ブレイク
B-2 スイングポイント
B-3 反発パターン (V字 / 逆V字 / W字 / M字)
B-4 ローソク足構造の推移
B-5 連続パターン

各関数は OHLCV DataFrame を受け取り、特徴量 Series を返す（インデックスは入力と一致）。
B-6 (フラクタル) は段階1-B 段階では未実装（後追加）。
"""

from __future__ import annotations
import numpy as np
import pandas as pd


# ── B-1: 高値・安値ブレイク ───────────────────────────

def new_high_in_W(df: pd.DataFrame, W: int) -> pd.Series:
    """当該バー high が過去 W バーの最高値か (0/1)"""
    return (df["high"] == df["high"].rolling(W, min_periods=W).max()).astype(int)


def new_low_in_W(df: pd.DataFrame, W: int) -> pd.Series:
    return (df["low"] == df["low"].rolling(W, min_periods=W).min()).astype(int)


def bars_since_new_high_W(df: pd.DataFrame, W: int) -> pd.Series:
    """最後に W バー高値ブレイクからの経過バー数"""
    flag = new_high_in_W(df, W)
    out = np.full(len(df), np.nan)
    last_idx = -1
    for i, v in enumerate(flag.values):
        if v == 1:
            last_idx = i
        out[i] = (i - last_idx) if last_idx >= 0 else np.nan
    return pd.Series(out, index=df.index)


def bars_since_new_low_W(df: pd.DataFrame, W: int) -> pd.Series:
    flag = new_low_in_W(df, W)
    out = np.full(len(df), np.nan)
    last_idx = -1
    for i, v in enumerate(flag.values):
        if v == 1:
            last_idx = i
        out[i] = (i - last_idx) if last_idx >= 0 else np.nan
    return pd.Series(out, index=df.index)


# ── B-2: スイングポイント ────────────────────────────

def swing_high_dist_pct_W(df: pd.DataFrame, W: int) -> pd.Series:
    """直近 W バーのスイング高値（max(high)）からの距離 (%)"""
    rolling_high = df["high"].rolling(W, min_periods=W).max()
    return (rolling_high - df["close"]) / df["close"].replace(0, np.nan) * 100


def swing_low_dist_pct_W(df: pd.DataFrame, W: int) -> pd.Series:
    rolling_low = df["low"].rolling(W, min_periods=W).min()
    return (df["close"] - rolling_low) / df["close"].replace(0, np.nan) * 100


def bars_since_swing_high_W(df: pd.DataFrame, W: int) -> pd.Series:
    """W バー内で最高値を打った位置からの経過バー数"""
    out = np.full(len(df), np.nan)
    h = df["high"].values
    for i in range(len(h)):
        if i < W - 1:
            continue
        win = h[i - W + 1:i + 1]
        argmax_local = np.argmax(win)
        out[i] = W - 1 - argmax_local
    return pd.Series(out, index=df.index)


def bars_since_swing_low_W(df: pd.DataFrame, W: int) -> pd.Series:
    out = np.full(len(df), np.nan)
    l = df["low"].values
    for i in range(len(l)):
        if i < W - 1:
            continue
        win = l[i - W + 1:i + 1]
        argmin_local = np.argmin(win)
        out[i] = W - 1 - argmin_local
    return pd.Series(out, index=df.index)


# ── B-3: 反発パターン (バイナリ・0/1) ──────────────────

def v_shape_in_W(df: pd.DataFrame, W: int) -> pd.Series:
    """過去 W バー内で V字反転が成立しているか。
    定義: 中央付近に最安値があり、両端の高値がそれぞれ最安値の +1% 以上。
    """
    out = np.zeros(len(df), dtype=int)
    h = df["high"].values
    l = df["low"].values
    for i in range(len(df)):
        if i < W - 1:
            continue
        win_h = h[i - W + 1:i + 1]
        win_l = l[i - W + 1:i + 1]
        argmin_local = np.argmin(win_l)
        # 中央付近 (±25%) に最安値
        if not (W * 0.25 <= argmin_local <= W * 0.75):
            continue
        min_low = win_l[argmin_local]
        # 両側それぞれの最高値が min_low の +1% 以上
        left_max = np.max(win_h[:argmin_local + 1]) if argmin_local > 0 else min_low
        right_max = np.max(win_h[argmin_local:]) if argmin_local < W - 1 else min_low
        if left_max >= min_low * 1.01 and right_max >= min_low * 1.01:
            out[i] = 1
    return pd.Series(out, index=df.index)


def inverted_v_in_W(df: pd.DataFrame, W: int) -> pd.Series:
    """逆V字: 中央付近に最高値があり、両端が -1% 以下"""
    out = np.zeros(len(df), dtype=int)
    h = df["high"].values
    l = df["low"].values
    for i in range(len(df)):
        if i < W - 1:
            continue
        win_h = h[i - W + 1:i + 1]
        win_l = l[i - W + 1:i + 1]
        argmax_local = np.argmax(win_h)
        if not (W * 0.25 <= argmax_local <= W * 0.75):
            continue
        max_high = win_h[argmax_local]
        left_min = np.min(win_l[:argmax_local + 1]) if argmax_local > 0 else max_high
        right_min = np.min(win_l[argmax_local:]) if argmax_local < W - 1 else max_high
        if left_min <= max_high * 0.99 and right_min <= max_high * 0.99:
            out[i] = 1
    return pd.Series(out, index=df.index)


def w_shape_in_W(df: pd.DataFrame, W: int) -> pd.Series:
    """W字: 過去 W バー内に 2つの底（局所最小）がある"""
    out = np.zeros(len(df), dtype=int)
    l = df["low"].values
    for i in range(len(df)):
        if i < W - 1:
            continue
        win = l[i - W + 1:i + 1]
        # 単純な局所最小カウント (両隣より小さい)
        local_mins = 0
        for j in range(1, W - 1):
            if win[j] < win[j - 1] and win[j] < win[j + 1]:
                local_mins += 1
        if local_mins >= 2:
            out[i] = 1
    return pd.Series(out, index=df.index)


def m_shape_in_W(df: pd.DataFrame, W: int) -> pd.Series:
    out = np.zeros(len(df), dtype=int)
    h = df["high"].values
    for i in range(len(df)):
        if i < W - 1:
            continue
        win = h[i - W + 1:i + 1]
        local_maxs = 0
        for j in range(1, W - 1):
            if win[j] > win[j - 1] and win[j] > win[j + 1]:
                local_maxs += 1
        if local_maxs >= 2:
            out[i] = 1
    return pd.Series(out, index=df.index)


# ── B-4: ローソク足構造の推移 ────────────────────────

def avg_upper_wick_ratio_W(df: pd.DataFrame, W: int) -> pd.Series:
    rng = (df["high"] - df["low"]).replace(0, np.nan)
    upper_wick = df["high"] - df[["open", "close"]].max(axis=1)
    return (upper_wick / rng).rolling(W, min_periods=W).mean()


def avg_lower_wick_ratio_W(df: pd.DataFrame, W: int) -> pd.Series:
    rng = (df["high"] - df["low"]).replace(0, np.nan)
    lower_wick = df[["open", "close"]].min(axis=1) - df["low"]
    return (lower_wick / rng).rolling(W, min_periods=W).mean()


def avg_body_ratio_W(df: pd.DataFrame, W: int) -> pd.Series:
    rng = (df["high"] - df["low"]).replace(0, np.nan)
    body = (df["close"] - df["open"]).abs()
    return (body / rng).rolling(W, min_periods=W).mean()


def significant_wick_count_W(df: pd.DataFrame, W: int, sigma: float = 2.0) -> pd.Series:
    """過去 W バー内で wick 長が rolling 平均+sigma を超えたバー数"""
    rng = (df["high"] - df["low"]).replace(0, np.nan)
    upper_wick = df["high"] - df[["open", "close"]].max(axis=1)
    lower_wick = df[["open", "close"]].min(axis=1) - df["low"]
    max_wick = pd.concat([upper_wick, lower_wick], axis=1).max(axis=1) / rng
    rolling_mean = max_wick.rolling(W, min_periods=W).mean()
    rolling_std = max_wick.rolling(W, min_periods=W).std()
    threshold = rolling_mean + sigma * rolling_std
    significant = (max_wick > threshold).astype(int)
    return significant.rolling(W, min_periods=W).sum()


def direction_flips_W(df: pd.DataFrame, W: int) -> pd.Series:
    """過去 W バー内で実体方向 (close-open の符号) が反転した回数"""
    direction = np.sign(df["close"] - df["open"])
    flips = (direction != direction.shift(1)).astype(int)
    return flips.rolling(W, min_periods=W).sum()


# ── B-5: 連続パターン ──────────────────────────────

def max_consecutive_new_highs_W(df: pd.DataFrame, W: int) -> pd.Series:
    """過去 W バー内の最大連続新高値更新数"""
    flag = new_high_in_W(df, max(2, W // 4)).values  # 短期 high で連続性を測る
    out = np.full(len(df), np.nan)
    for i in range(len(df)):
        if i < W - 1:
            continue
        win = flag[i - W + 1:i + 1]
        max_run = 0
        run = 0
        for v in win:
            if v == 1:
                run += 1
                max_run = max(max_run, run)
            else:
                run = 0
        out[i] = max_run
    return pd.Series(out, index=df.index)


def max_consecutive_new_lows_W(df: pd.DataFrame, W: int) -> pd.Series:
    flag = new_low_in_W(df, max(2, W // 4)).values
    out = np.full(len(df), np.nan)
    for i in range(len(df)):
        if i < W - 1:
            continue
        win = flag[i - W + 1:i + 1]
        max_run = 0
        run = 0
        for v in win:
            if v == 1:
                run += 1
                max_run = max(max_run, run)
            else:
                run = 0
        out[i] = max_run
    return pd.Series(out, index=df.index)


def body_direction_flips_W(df: pd.DataFrame, W: int) -> pd.Series:
    """direction_flips_W のエイリアス（B-4 と同じ概念だが B-5 として残す）"""
    return direction_flips_W(df, W)


# ── 統合: 全特徴量を計算 ────────────────────────────

FEATURE_FUNCS = {
    # B-1
    "new_high_in_W": new_high_in_W,
    "new_low_in_W": new_low_in_W,
    "bars_since_new_high_W": bars_since_new_high_W,
    "bars_since_new_low_W": bars_since_new_low_W,
    # B-2
    "swing_high_dist_pct_W": swing_high_dist_pct_W,
    "swing_low_dist_pct_W": swing_low_dist_pct_W,
    "bars_since_swing_high_W": bars_since_swing_high_W,
    "bars_since_swing_low_W": bars_since_swing_low_W,
    # B-3
    "v_shape_in_W": v_shape_in_W,
    "inverted_v_in_W": inverted_v_in_W,
    "w_shape_in_W": w_shape_in_W,
    "m_shape_in_W": m_shape_in_W,
    # B-4
    "avg_upper_wick_ratio_W": avg_upper_wick_ratio_W,
    "avg_lower_wick_ratio_W": avg_lower_wick_ratio_W,
    "avg_body_ratio_W": avg_body_ratio_W,
    "significant_wick_count_W": significant_wick_count_W,
    "direction_flips_W": direction_flips_W,
    # B-5
    "max_consecutive_new_highs_W": max_consecutive_new_highs_W,
    "max_consecutive_new_lows_W": max_consecutive_new_lows_W,
    "body_direction_flips_W": body_direction_flips_W,
}

CATEGORY_OF_FEATURE = {
    "new_high_in_W": "B1_breakout",
    "new_low_in_W": "B1_breakout",
    "bars_since_new_high_W": "B1_breakout",
    "bars_since_new_low_W": "B1_breakout",
    "swing_high_dist_pct_W": "B2_swing",
    "swing_low_dist_pct_W": "B2_swing",
    "bars_since_swing_high_W": "B2_swing",
    "bars_since_swing_low_W": "B2_swing",
    "v_shape_in_W": "B3_pattern",
    "inverted_v_in_W": "B3_pattern",
    "w_shape_in_W": "B3_pattern",
    "m_shape_in_W": "B3_pattern",
    "avg_upper_wick_ratio_W": "B4_candle",
    "avg_lower_wick_ratio_W": "B4_candle",
    "avg_body_ratio_W": "B4_candle",
    "significant_wick_count_W": "B4_candle",
    "direction_flips_W": "B4_candle",
    "max_consecutive_new_highs_W": "B5_streak",
    "max_consecutive_new_lows_W": "B5_streak",
    "body_direction_flips_W": "B5_streak",
}


def compute_all_features(df: pd.DataFrame, W: int) -> pd.DataFrame:
    """OHLCV df に対し W で全形状特徴量を計算。"""
    out = pd.DataFrame(index=df.index)
    for name, func in FEATURE_FUNCS.items():
        out[name] = func(df, W)
    return out
