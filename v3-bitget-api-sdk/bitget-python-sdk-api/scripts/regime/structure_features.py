"""structure_features.py — 段階1-C 構造的特徴量計算

カテゴリ C-1〜C-4 の関数群。窓 N に依存する構造データを OHLCV から計算する。

C-1 レジサポライン (5点 fractal + タッチ回数・タッチ閾値感度分析)
C-2 ピボットポイント (クラシック・同軸前1バー)
C-3 出来高クラスタ (VPVR: POC/VAH/VAL・ビン×VA比率感度分析)
C-4 フィボナッチ・リトレースメント (直近スイング)

感度パラメータ (メタ分析で評価):
  TOUCH_THRESHOLDS: [0.003, 0.005, 0.010, 0.020] (C-1 のみ)
  VOLUME_BIN_COUNTS: [20, 50, 100]               (C-3 のみ)
  VA_RATIOS: [0.60, 0.70, 0.80]                  (C-3 のみ)
  N_CANDIDATES: [50, 100, 200]                   (C-1/C-3/C-4)

カラム命名:
  C-1: resistance_distance_pct_N{N}
       support_distance_pct_N{N}
       nearest_level_distance_pct_N{N}
       nearest_level_touch_count_N{N}_t{thr}    (thr=030/050/100/200)
  C-2: dist_to_PP_pct, dist_to_R1_pct, dist_to_R2_pct,
       dist_to_S1_pct, dist_to_S2_pct, pivot_zone
  C-3: dist_to_POC_pct_N{N}_b{B}                  (VA 非依存)
       dist_to_VAH_pct_N{N}_b{B}_va{VA}
       dist_to_VAL_pct_N{N}_b{B}_va{VA}
       inside_value_area_N{N}_b{B}_va{VA}
  C-4: dist_to_fib_{382/500/618/786}_pct_N{N}
       nearest_fib_distance_pct_N{N}
"""

from __future__ import annotations
import numpy as np
import pandas as pd

# ── 感度パラメータ ─────────────────────────────────
TOUCH_THRESHOLDS = [0.003, 0.005, 0.010, 0.020]   # 0.3% / 0.5% / 1.0% / 2.0%
VOLUME_BIN_COUNTS = [20, 50, 100]
VA_RATIOS = [0.60, 0.70, 0.80]
N_CANDIDATES = [50, 100, 200]


# ── C-1: レジサポライン (5点 fractal + タッチ感度) ───────

def _detect_fractals(df: pd.DataFrame):
    """5点 fractal で resistance/support の局所 pivot を検出 (look-ahead フリー)。
    Returns: (is_res, is_sup, pivot_high, pivot_low)
      is_res[i]=True → i バー終了時点で確定済 (実ピーク bar は i-2)
      pivot_high[i] = h[i-2] (is_res[i]=True のとき)
    L-179 leak 修正: j バーピボットを j+2 バーで確定として記録し、未来参照を遮断。
    """
    h = df["high"].values
    l = df["low"].values
    n = len(df)
    is_res = np.zeros(n, dtype=bool)
    is_sup = np.zeros(n, dtype=bool)
    pivot_high = np.full(n, np.nan)
    pivot_low = np.full(n, np.nan)
    for j in range(2, n - 2):
        if (h[j] > h[j-1] and h[j] > h[j-2] and
            h[j] > h[j+1] and h[j] > h[j+2]):
            is_res[j+2] = True
            pivot_high[j+2] = h[j]
        if (l[j] < l[j-1] and l[j] < l[j-2] and
            l[j] < l[j+1] and l[j] < l[j+2]):
            is_sup[j+2] = True
            pivot_low[j+2] = l[j]
    return is_res, is_sup, pivot_high, pivot_low


def compute_c1_features(df: pd.DataFrame, N: int) -> pd.DataFrame:
    """C-1 全特徴量を1度計算。タッチ感度4水準 × 距離3系列 = 7カラム。"""
    is_res, is_sup, pivot_high, pivot_low = _detect_fractals(df)
    close = df["close"].values
    n = len(df)

    res_dist = np.full(n, np.nan)
    sup_dist = np.full(n, np.nan)
    nearest_dist = np.full(n, np.nan)
    nearest_level = np.full(n, np.nan)

    for i in range(N, n):
        start = max(0, i - N + 1)
        end = i + 1
        res_prices = pivot_high[start:end][is_res[start:end]]
        sup_prices = pivot_low[start:end][is_sup[start:end]]
        c = close[i]

        r_min = None
        if len(res_prices) > 0:
            res_above = res_prices[res_prices > c]
            if len(res_above) > 0:
                r_min = float(np.min(res_above))
                res_dist[i] = (r_min - c) / c * 100

        s_max = None
        if len(sup_prices) > 0:
            sup_below = sup_prices[sup_prices < c]
            if len(sup_below) > 0:
                s_max = float(np.max(sup_below))
                sup_dist[i] = (c - s_max) / c * 100

        candidates = []
        if r_min is not None:
            candidates.append(((r_min - c) / c * 100, r_min))
        if s_max is not None:
            candidates.append(((c - s_max) / c * 100, s_max))
        if candidates:
            d, lvl = min(candidates, key=lambda x: x[0])
            nearest_dist[i] = d
            nearest_level[i] = lvl

    out = pd.DataFrame(index=df.index)
    out[f"resistance_distance_pct_N{N}"] = res_dist
    out[f"support_distance_pct_N{N}"] = sup_dist
    out[f"nearest_level_distance_pct_N{N}"] = nearest_dist

    # touch_count: 各タッチ閾値で再計算 (距離の対称%)
    for thr in TOUCH_THRESHOLDS:
        thr_label = f"t{int(thr * 10000):03d}"  # 0.003→t030 / 0.020→t200
        touch_count = np.full(n, np.nan)
        for i in range(N, n):
            lvl = nearest_level[i]
            if np.isnan(lvl):
                continue
            tol = abs(lvl) * thr
            past = close[max(0, i - N + 1):i + 1]
            touch_count[i] = ((past >= lvl - tol) & (past <= lvl + tol)).sum()
        out[f"nearest_level_touch_count_N{N}_{thr_label}"] = touch_count

    return out


# ── C-2: ピボット (同軸前1バー・N 非依存) ─────────────────

def compute_c2_features(df: pd.DataFrame) -> pd.DataFrame:
    """前1バーの H/L/C でクラシックピボット計算。"""
    h_prev = df["high"].shift(1)
    l_prev = df["low"].shift(1)
    c_prev = df["close"].shift(1)

    pp = (h_prev + l_prev + c_prev) / 3
    r1 = 2 * pp - l_prev
    s1 = 2 * pp - h_prev
    r2 = pp + (h_prev - l_prev)
    s2 = pp - (h_prev - l_prev)

    c = df["close"]
    out = pd.DataFrame(index=df.index)
    out["dist_to_PP_pct"] = (c - pp) / c * 100
    out["dist_to_R1_pct"] = (r1 - c) / c * 100
    out["dist_to_R2_pct"] = (r2 - c) / c * 100
    out["dist_to_S1_pct"] = (c - s1) / c * 100
    out["dist_to_S2_pct"] = (c - s2) / c * 100

    # pivot_zone: -2 (S2 below) / -1 (S1〜S2) / 0 (S1〜R1) / 1 (R1〜R2) / 2 (R2 above)
    zone = pd.Series(np.nan, index=df.index)
    zone[c < s2] = -2
    zone[(c >= s2) & (c < s1)] = -1
    zone[(c >= s1) & (c < r1)] = 0
    zone[(c >= r1) & (c < r2)] = 1
    zone[c >= r2] = 2
    out["pivot_zone"] = zone
    return out


# ── C-3: 出来高クラスタ (VPVR) ──────────────────────

def _volume_profile_one(prices_low: np.ndarray, prices_high: np.ndarray,
                        volumes: np.ndarray, n_bins: int, va_ratio: float):
    """1ウィンドウの volume profile を計算。
    Returns: (poc_price, vah_price, val_price) — 失敗時 (None, None, None)
    """
    if len(volumes) == 0 or volumes.sum() == 0:
        return None, None, None
    p_min = float(prices_low.min())
    p_max = float(prices_high.max())
    if p_max - p_min < 1e-9:
        return None, None, None
    bin_edges = np.linspace(p_min, p_max, n_bins + 1)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    rep_prices = (prices_low + prices_high) / 2
    bin_volume, _ = np.histogram(rep_prices, bins=bin_edges, weights=volumes)
    if bin_volume.sum() == 0:
        return None, None, None

    poc_idx = int(np.argmax(bin_volume))
    poc_price = float(bin_centers[poc_idx])

    target = bin_volume.sum() * va_ratio
    cum = bin_volume[poc_idx]
    lo = poc_idx
    hi = poc_idx
    while cum < target and (lo > 0 or hi < n_bins - 1):
        left_v = bin_volume[lo - 1] if lo > 0 else -1.0
        right_v = bin_volume[hi + 1] if hi < n_bins - 1 else -1.0
        if left_v >= right_v:
            lo -= 1
            cum += bin_volume[lo]
        else:
            hi += 1
            cum += bin_volume[hi]
    val_price = float(bin_centers[lo])
    vah_price = float(bin_centers[hi])
    return poc_price, vah_price, val_price


def compute_c3_features(df: pd.DataFrame, N: int) -> pd.DataFrame:
    """C-3 全特徴量。ビン数3 × VA比率3 = 9 設定 + POC (VA 非依存) ビン3。"""
    h = df["high"].values
    l = df["low"].values
    c = df["close"].values
    v = df["volume"].values
    n = len(df)

    out = pd.DataFrame(index=df.index)

    for n_bins in VOLUME_BIN_COUNTS:
        poc_arr = np.full(n, np.nan)
        vah_arrs = {va: np.full(n, np.nan) for va in VA_RATIOS}
        val_arrs = {va: np.full(n, np.nan) for va in VA_RATIOS}
        in_va_arrs = {va: np.full(n, np.nan) for va in VA_RATIOS}

        for i in range(N, n):
            window_l = l[i - N + 1:i + 1]
            window_h = h[i - N + 1:i + 1]
            window_v = v[i - N + 1:i + 1]
            poc_p, _, _ = _volume_profile_one(window_l, window_h, window_v, n_bins, 0.7)
            if poc_p is not None:
                poc_arr[i] = poc_p
            for va in VA_RATIOS:
                _, vah_p, val_p = _volume_profile_one(window_l, window_h, window_v, n_bins, va)
                if vah_p is not None and val_p is not None:
                    vah_arrs[va][i] = vah_p
                    val_arrs[va][i] = val_p
                    in_va_arrs[va][i] = 1 if (val_p <= c[i] <= vah_p) else 0

        out[f"dist_to_POC_pct_N{N}_b{n_bins:03d}"] = (c - poc_arr) / c * 100
        for va in VA_RATIOS:
            va_label = f"va{int(va * 100):02d}"
            out[f"dist_to_VAH_pct_N{N}_b{n_bins:03d}_{va_label}"] = (vah_arrs[va] - c) / c * 100
            out[f"dist_to_VAL_pct_N{N}_b{n_bins:03d}_{va_label}"] = (c - val_arrs[va]) / c * 100
            out[f"inside_value_area_N{N}_b{n_bins:03d}_{va_label}"] = in_va_arrs[va]
    return out


# ── C-4: フィボナッチ (直近スイング) ───────────────────

def compute_c4_features(df: pd.DataFrame, N: int) -> pd.DataFrame:
    """直近スイングフィボ。最後極値の方向で fib 計算。"""
    h = df["high"].values
    l = df["low"].values
    c = df["close"].values
    n = len(df)

    fib382 = np.full(n, np.nan)
    fib500 = np.full(n, np.nan)
    fib618 = np.full(n, np.nan)
    fib786 = np.full(n, np.nan)
    nearest_dist = np.full(n, np.nan)

    for i in range(N, n):
        win_h = h[i - N + 1:i + 1]
        win_l = l[i - N + 1:i + 1]
        max_idx = int(np.argmax(win_h))
        min_idx = int(np.argmin(win_l))
        max_p = float(win_h[max_idx])
        min_p = float(win_l[min_idx])
        if max_p - min_p < 1e-9:
            continue
        rng = max_p - min_p
        if max_idx > min_idx:
            # 直近上昇後の retracement (high から下に %)
            f382 = max_p - rng * 0.382
            f500 = max_p - rng * 0.500
            f618 = max_p - rng * 0.618
            f786 = max_p - rng * 0.786
        else:
            # 直近下降後の retracement (low から上に %)
            f382 = min_p + rng * 0.382
            f500 = min_p + rng * 0.500
            f618 = min_p + rng * 0.618
            f786 = min_p + rng * 0.786
        fib382[i] = f382
        fib500[i] = f500
        fib618[i] = f618
        fib786[i] = f786
        levels = np.array([f382, f500, f618, f786])
        diffs_pct = (levels - c[i]) / c[i] * 100
        nearest_dist[i] = float(diffs_pct[int(np.argmin(np.abs(diffs_pct)))])

    out = pd.DataFrame(index=df.index)
    out[f"dist_to_fib_382_pct_N{N}"] = (c - fib382) / c * 100
    out[f"dist_to_fib_500_pct_N{N}"] = (c - fib500) / c * 100
    out[f"dist_to_fib_618_pct_N{N}"] = (c - fib618) / c * 100
    out[f"dist_to_fib_786_pct_N{N}"] = (c - fib786) / c * 100
    out[f"nearest_fib_distance_pct_N{N}"] = nearest_dist
    return out


# ── C-4 v2: 5点 fractal でスイング検出 ──────────────────

def compute_c4_v2_features(df: pd.DataFrame, N: int) -> pd.DataFrame:
    """C-4 改良版: 5点 fractal で確定済みスイングのみ使用。
    look-ahead 完全防止 (中央バー j で確定する fractal は j ≤ i-2)。
    過去 N バー内の最後の swing high と swing low を抽出 → 後勝ちで retracement 方向決定。
    fractal が見つからないバーは NaN。
    """
    is_res, is_sup, pivot_high, pivot_low = _detect_fractals(df)
    c = df["close"].values
    n = len(df)

    fib382 = np.full(n, np.nan)
    fib500 = np.full(n, np.nan)
    fib618 = np.full(n, np.nan)
    fib786 = np.full(n, np.nan)
    nearest_dist = np.full(n, np.nan)

    for i in range(N, n):
        start = max(0, i - N + 1)
        end = i + 1
        win_res_idx = np.where(is_res[start:end])[0]
        win_sup_idx = np.where(is_sup[start:end])[0]
        if len(win_res_idx) == 0 or len(win_sup_idx) == 0:
            continue
        last_res_local = int(win_res_idx[-1])
        last_sup_local = int(win_sup_idx[-1])
        last_res_p = float(pivot_high[start + last_res_local])
        last_sup_p = float(pivot_low[start + last_sup_local])
        if last_res_p - last_sup_p < 1e-9:
            continue
        rng = last_res_p - last_sup_p
        if last_res_local > last_sup_local:
            f382 = last_res_p - rng * 0.382
            f500 = last_res_p - rng * 0.500
            f618 = last_res_p - rng * 0.618
            f786 = last_res_p - rng * 0.786
        else:
            f382 = last_sup_p + rng * 0.382
            f500 = last_sup_p + rng * 0.500
            f618 = last_sup_p + rng * 0.618
            f786 = last_sup_p + rng * 0.786
        fib382[i] = f382
        fib500[i] = f500
        fib618[i] = f618
        fib786[i] = f786
        levels = np.array([f382, f500, f618, f786])
        diffs_pct = (levels - c[i]) / c[i] * 100
        nearest_dist[i] = float(diffs_pct[int(np.argmin(np.abs(diffs_pct)))])

    out = pd.DataFrame(index=df.index)
    out[f"dist_to_fib_v2_382_pct_N{N}"] = (c - fib382) / c * 100
    out[f"dist_to_fib_v2_500_pct_N{N}"] = (c - fib500) / c * 100
    out[f"dist_to_fib_v2_618_pct_N{N}"] = (c - fib618) / c * 100
    out[f"dist_to_fib_v2_786_pct_N{N}"] = (c - fib786) / c * 100
    out[f"nearest_fib_v2_distance_pct_N{N}"] = nearest_dist
    return out


# ── 統合関数 ─────────────────────────────────────

def compute_features_for_N(df: pd.DataFrame, N: int) -> pd.DataFrame:
    """N に依存する C-1 / C-3 / C-4 / C-4 v2 を計算。"""
    return pd.concat([
        compute_c1_features(df, N),
        compute_c3_features(df, N),
        compute_c4_features(df, N),
        compute_c4_v2_features(df, N),
    ], axis=1)


def compute_c2_only(df: pd.DataFrame) -> pd.DataFrame:
    """N 非依存の C-2 を計算。"""
    return compute_c2_features(df)


def category_of_column(col: str) -> str:
    """カラム名からカテゴリ判定。"""
    if (col.startswith("resistance_distance") or col.startswith("support_distance")
            or col.startswith("nearest_level")):
        return "C1_resistsupp"
    if (col.startswith("dist_to_PP") or col.startswith("dist_to_R")
            or col.startswith("dist_to_S") or col == "pivot_zone"):
        return "C2_pivot"
    if (col.startswith("dist_to_POC") or col.startswith("dist_to_VAH")
            or col.startswith("dist_to_VAL") or col.startswith("inside_value_area")):
        return "C3_volume"
    if col.startswith("dist_to_fib_v2") or col.startswith("nearest_fib_v2"):
        return "C4_fib_v2"
    if col.startswith("dist_to_fib") or col.startswith("nearest_fib"):
        return "C4_fib"
    return "unknown"


def base_feature_name(col: str) -> str:
    """カラム名から N/感度パラメータを除いた基本名を返す。"""
    parts = col.split("_N")
    return parts[0] if len(parts) > 1 else col
