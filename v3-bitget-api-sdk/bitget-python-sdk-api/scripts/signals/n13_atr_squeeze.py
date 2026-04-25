"""
N13 — ATRスクイーズ脱出（ボラティリティ収縮 → 拡張ブレイク）

条件:
  atr_short = ATR(14)
  atr_long  = SMA(atr_short, 50)
  squeeze   : atr_short[i-1] < atr_long[i-1] × SQ_RATIO   (ボラ収縮中)
  expand    : atr_short[i]   > atr_short[i-1] × EXP_RATIO  (ボラ急拡張)
  方向       : close[i] > close[i-1] → LONG / close[i] < close[i-1] → SHORT
"""
from __future__ import annotations

import pandas as pd
import ta

SQ_RATIO = 0.7
EXP_RATIO = 1.3


def detect(df: pd.DataFrame) -> pd.DataFrame:
    work = df[["timestamp", "open", "high", "low", "close"]].copy()
    work["atr"] = ta.volatility.AverageTrueRange(
        work["high"], work["low"], work["close"], window=14
    ).average_true_range()
    work["atr_long"] = work["atr"].rolling(50).mean()
    work["prev_atr"] = work["atr"].shift(1)
    work["prev_atr_long"] = work["atr_long"].shift(1)
    work["prev_close"] = work["close"].shift(1)

    squeezed = work["prev_atr"] < (work["prev_atr_long"] * SQ_RATIO)
    expanded = work["atr"] > (work["prev_atr"] * EXP_RATIO)
    long_cond = squeezed & expanded & (work["close"] > work["prev_close"])
    short_cond = squeezed & expanded & (work["close"] < work["prev_close"])

    rows = []
    for _, r in work[long_cond].iterrows():
        rows.append({"entry_time": r["timestamp"], "side": "LONG", "entry_price": float(r["close"])})
    for _, r in work[short_cond].iterrows():
        rows.append({"entry_time": r["timestamp"], "side": "SHORT", "entry_price": float(r["close"])})

    if not rows:
        return pd.DataFrame(columns=["entry_time", "side", "entry_price"])
    return pd.DataFrame(rows).sort_values("entry_time").reset_index(drop=True)
