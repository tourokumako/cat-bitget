"""
N2 — BB Trap（ボリンジャーバンド 上抜け Trap SHORT / 下抜け Trap LONG）

反発系。直前足で BB を突き抜けたがすぐ戻した（ダマシ）を拾う。

条件:
  period=20, stdev=2.0
  上抜け Trap SHORT:
      prev.high > bb_upper[i-1]
      close[i]  < bb_upper[i]
      close[i]  < open[i]           (陰線で戻り確定)
  下抜け Trap LONG:
      prev.low  < bb_lower[i-1]
      close[i]  > bb_lower[i]
      close[i]  > open[i]           (陽線で戻り確定)
"""
from __future__ import annotations

import pandas as pd
import ta

BB_PERIOD = 20
BB_STDEV = 2.0


def detect(df: pd.DataFrame) -> pd.DataFrame:
    bb = ta.volatility.BollingerBands(df["close"], window=BB_PERIOD, window_dev=BB_STDEV)
    work = df[["timestamp", "open", "high", "low", "close"]].copy()
    work["bb_upper"] = bb.bollinger_hband()
    work["bb_lower"] = bb.bollinger_lband()
    work["prev_high"] = work["high"].shift(1)
    work["prev_low"] = work["low"].shift(1)
    work["prev_upper"] = work["bb_upper"].shift(1)
    work["prev_lower"] = work["bb_lower"].shift(1)

    short_cond = (
        (work["prev_high"] > work["prev_upper"])
        & (work["close"] < work["bb_upper"])
        & (work["close"] < work["open"])
    )
    long_cond = (
        (work["prev_low"] < work["prev_lower"])
        & (work["close"] > work["bb_lower"])
        & (work["close"] > work["open"])
    )

    rows = []
    for _, r in work[short_cond].iterrows():
        rows.append({"entry_time": r["timestamp"], "side": "SHORT", "entry_price": float(r["close"])})
    for _, r in work[long_cond].iterrows():
        rows.append({"entry_time": r["timestamp"], "side": "LONG", "entry_price": float(r["close"])})

    if not rows:
        return pd.DataFrame(columns=["entry_time", "side", "entry_price"])
    return pd.DataFrame(rows).sort_values("entry_time").reset_index(drop=True)
