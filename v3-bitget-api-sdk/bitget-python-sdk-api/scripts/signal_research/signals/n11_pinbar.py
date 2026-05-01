"""
N11 — ピンバー反転キャンドル

長いヒゲと小さい実体で反転を示唆するパターン。

条件:
  body  = |close - open|
  range = high - low
  upper_wick = high - max(open, close)
  lower_wick = min(open, close) - low
  body / range <= BODY_RATIO_MAX (default 0.3)
  range > 0
  SHORT (上ヒゲ ピンバー): upper_wick / range >= WICK_RATIO_MIN (default 0.6)
  LONG  (下ヒゲ ピンバー): lower_wick / range >= WICK_RATIO_MIN (default 0.6)
"""
from __future__ import annotations

import pandas as pd

BODY_RATIO_MAX = 0.3
WICK_RATIO_MIN = 0.6


def detect(df: pd.DataFrame) -> pd.DataFrame:
    work = df[["timestamp", "open", "high", "low", "close"]].copy()
    body = (work["close"] - work["open"]).abs()
    rng = work["high"] - work["low"]
    rng = rng.where(rng > 0)
    upper_wick = work["high"] - work[["open", "close"]].max(axis=1)
    lower_wick = work[["open", "close"]].min(axis=1) - work["low"]

    body_ratio = body / rng
    upper_ratio = upper_wick / rng
    lower_ratio = lower_wick / rng

    short_cond = (body_ratio <= BODY_RATIO_MAX) & (upper_ratio >= WICK_RATIO_MIN)
    long_cond = (body_ratio <= BODY_RATIO_MAX) & (lower_ratio >= WICK_RATIO_MIN)

    rows = []
    for _, r in work[short_cond].iterrows():
        rows.append({"entry_time": r["timestamp"], "side": "SHORT", "entry_price": float(r["close"])})
    for _, r in work[long_cond].iterrows():
        rows.append({"entry_time": r["timestamp"], "side": "LONG", "entry_price": float(r["close"])})

    if not rows:
        return pd.DataFrame(columns=["entry_time", "side", "entry_price"])
    return pd.DataFrame(rows).sort_values("entry_time").reset_index(drop=True)
