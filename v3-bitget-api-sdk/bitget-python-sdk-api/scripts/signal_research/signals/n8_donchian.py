"""
N8 — Donchian ブレイクアウト（20本高値/安値ブレイク）

順張り系。

条件:
  period = 20
  LONG  : close[i] > max(high[i-period:i])     (直近20本の最高値を更新)
  SHORT : close[i] < min(low[i-period:i])      (直近20本の最安値を更新)
"""
from __future__ import annotations

import pandas as pd

DONCHIAN_PERIOD = 20


def detect(df: pd.DataFrame) -> pd.DataFrame:
    work = df[["timestamp", "open", "high", "low", "close"]].copy()
    work["donch_high"] = work["high"].shift(1).rolling(DONCHIAN_PERIOD).max()
    work["donch_low"] = work["low"].shift(1).rolling(DONCHIAN_PERIOD).min()

    long_cond = work["close"] > work["donch_high"]
    short_cond = work["close"] < work["donch_low"]

    rows = []
    for _, r in work[long_cond].iterrows():
        rows.append({"entry_time": r["timestamp"], "side": "LONG", "entry_price": float(r["close"])})
    for _, r in work[short_cond].iterrows():
        rows.append({"entry_time": r["timestamp"], "side": "SHORT", "entry_price": float(r["close"])})

    if not rows:
        return pd.DataFrame(columns=["entry_time", "side", "entry_price"])
    return pd.DataFrame(rows).sort_values("entry_time").reset_index(drop=True)
