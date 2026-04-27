"""粒度内集約 / 粒度間集約 → 日次 predict label を生成"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .loader import IndicatorSpec, Recipe

LABEL_FROM_DIR = {1: "uptrend", 0: "range", -1: "downtrend"}


def _indicator_directional_score(
    panel_value: float,
    ind: IndicatorSpec,
    threshold: dict[str, float],
) -> tuple[int, float]:
    """1 指標を (方向 ∈ {-1, 0, +1}, 強度 ∈ [0, 1]) に変換。

    指標の意味論:
    - ma_slope: 値 > +th → +1 / < -th → -1 / else 0、強度=1
    - ma_dev / price_ma_diff: 同上
    - adx: 強度のみ（方向情報なし）。値 > th → 強度 1、else 0、方向 0
    - di_diff: 値 > +th → +1 / < -th → -1 / else 0
    - rsi: > 60 → +1、< 40 → -1、else 0（範囲は閾値で調整可・暫定固定）
    - macd_hist: > 0 → +1、< 0 → -1、else 0
    - stoch_k: > 80 → -1（買われすぎ→反転）、< 20 → +1、else 0（暫定）
    - atr_pct / bb_width / volume_z: 強度のみ（方向 0、閾値超で強度 1）
    - bb_pos: > +1σ → +1 / < -1σ → -1 / else 0
    - obv_slope: > 0 → +1 / < 0 → -1 / else 0
    - macd_cross: TODO（未対応）
    """
    if pd.isna(panel_value):
        return 0, 0.0

    name = ind.name
    th = threshold.get(ind.key, 0.0)

    if name in ("ma_slope", "ma_dev", "price_ma_diff", "di_diff", "macd_hist", "obv_slope"):
        if panel_value > th:
            return 1, 1.0
        if panel_value < -th:
            return -1, 1.0
        return 0, 1.0

    if name == "adx":
        return 0, (1.0 if panel_value > th else 0.0)

    if name == "rsi":
        if panel_value > 60.0:
            return 1, 1.0
        if panel_value < 40.0:
            return -1, 1.0
        return 0, 1.0

    if name == "stoch_k":
        if panel_value < 20.0:
            return 1, 1.0
        if panel_value > 80.0:
            return -1, 1.0
        return 0, 1.0

    if name == "bb_pos":
        if panel_value > 0.5:
            return 1, 1.0
        if panel_value < -0.5:
            return -1, 1.0
        return 0, 1.0

    if name in ("atr_pct", "bb_width", "volume_z"):
        return 0, (1.0 if panel_value > th else 0.0)

    return 0, 0.0


def _aggregate_intra(
    inds: list[IndicatorSpec],
    panel_row: pd.Series,
    method: str,
    threshold: dict[str, float],
) -> int:
    """粒度内の複数指標 → 単一方向 ∈ {-1, 0, +1}。"""
    pairs = [_indicator_directional_score(panel_row.get(ind.key, np.nan), ind, threshold) for ind in inds]
    dirs = [d for d, _ in pairs]
    strengths = [s for _, s in pairs]

    if method == "vote":
        s = sum(dirs)
        return 1 if s > 0 else (-1 if s < 0 else 0)

    if method == "weighted_sum":
        s = sum(d * w for d, w in zip(dirs, strengths))
        if s > 0:
            return 1
        if s < 0:
            return -1
        return 0

    if method == "and_chain":
        if all(d == 1 for d in dirs):
            return 1
        if all(d == -1 for d in dirs):
            return -1
        return 0

    if method == "or_chain":
        if any(d == 1 for d in dirs):
            return 1
        if any(d == -1 for d in dirs):
            return -1
        return 0

    if method == "score":
        # 強度のみ加算（方向情報がない指標群向け）。方向は別途 cross で決める前提。
        return 0 if sum(strengths) == 0 else (1 if sum(d * s for d, s in zip(dirs, strengths)) > 0 else (-1 if sum(d * s for d, s in zip(dirs, strengths)) < 0 else 0))

    raise ValueError(f"unknown aggregation_intra: {method}")


def _label_from_dir(d: int) -> str:
    return LABEL_FROM_DIR[d]


def predict_with_recipe(
    recipe: Recipe,
    panels: dict[str, pd.DataFrame],
    threshold: dict[str, float],
    eval_dates: pd.DatetimeIndex,
) -> pd.Series:
    """eval_dates の各日に対し predict label を返す。"""
    inds_by_tf = recipe.indicators_by_tf()
    out = pd.Series(index=eval_dates, dtype=object)

    for ts in eval_dates:
        date = ts.date() if hasattr(ts, "date") else ts
        tf_dirs: dict[str, int] = {}

        for tf in recipe.timeframes:
            inds = inds_by_tf.get(tf, [])
            panel = panels[tf]

            if tf == "M_dom":
                month_period = pd.Period(date, freq="M")
                row = panel.loc[panel.index == month_period]
                if row.empty:
                    tf_dirs[tf] = 0
                    continue
                lab = row.iloc[0]["human_label_m_dom"]
                tf_dirs[tf] = {"uptrend": 1, "range": 0, "downtrend": -1}.get(lab, 0)
                continue

            ts_idx = pd.Timestamp(date)
            asof = panel.index.asof(ts_idx)
            if pd.isna(asof):
                tf_dirs[tf] = 0
                continue
            row = panel.loc[asof]
            tf_dirs[tf] = _aggregate_intra(inds, row, recipe.aggregation_intra, threshold)

        # 粒度間集約
        if recipe.aggregation_cross is None or len(recipe.timeframes) == 1:
            d = list(tf_dirs.values())[0] if tf_dirs else 0
        elif recipe.aggregation_cross == "multi_vote":
            s = sum(tf_dirs.values())
            d = 1 if s > 0 else (-1 if s < 0 else 0)
        elif recipe.aggregation_cross == "hierarchical":
            # 上位粒度から見て確定（±1）ならそれを採用、range なら次の粒度へ
            d = 0
            for tf in recipe.timeframes:
                v = tf_dirs.get(tf, 0)
                if v != 0:
                    d = v
                    break
        elif recipe.aggregation_cross == "weighted_sum":
            d = 1 if sum(tf_dirs.values()) > 0 else (-1 if sum(tf_dirs.values()) < 0 else 0)
        elif recipe.aggregation_cross == "and_chain":
            vals = list(tf_dirs.values())
            if vals and all(v == 1 for v in vals):
                d = 1
            elif vals and all(v == -1 for v in vals):
                d = -1
            else:
                d = 0
        else:
            raise ValueError(f"unknown aggregation_cross: {recipe.aggregation_cross}")

        out.loc[ts] = _label_from_dir(d)

    return out


def expand_grid(recipe: Recipe, mode: str) -> list[dict[str, float]]:
    """threshold combos のリスト。default モードは 1点、full モードは grid 直積。"""
    if mode == "default" or not recipe.threshold_grid:
        return [dict(recipe.threshold_default)]

    keys = list(recipe.threshold_grid.keys())
    from itertools import product

    out: list[dict[str, float]] = []
    for vals in product(*[recipe.threshold_grid[k] for k in keys]):
        combo = dict(recipe.threshold_default)
        for k, v in zip(keys, vals):
            combo[k] = v
        out.append(combo)
    return out
