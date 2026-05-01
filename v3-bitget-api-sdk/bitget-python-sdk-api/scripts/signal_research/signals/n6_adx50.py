"""
N6 — ADX50超 + DI- 優勢 SHORT（強トレンド順張り）

条件:
    adx[i]        >= ADX_MIN         (default 50)
    minus_di[i]   >  plus_di[i]      (DI- 優勢 = 下降トレンド）
    close[i]      <  open[i]          (陰線確定・ノイズ除外)

出力: entry_time, side=SHORT, entry_price=close
"""
from __future__ import annotations

import pandas as pd
import ta

ADX_MIN = 50.0


def detect(df: pd.DataFrame) -> pd.DataFrame:
    adx = ta.trend.ADXIndicator(df["high"], df["low"], df["close"], window=14)
    work = df[["timestamp", "open", "high", "low", "close"]].copy()
    work["adx"] = adx.adx()
    work["plus_di"] = adx.adx_pos()
    work["minus_di"] = adx.adx_neg()

    cond = (
        (work["adx"] >= ADX_MIN)
        & (work["minus_di"] > work["plus_di"])
        & (work["close"] < work["open"])
    )
    fires = work[cond].copy()
    if fires.empty:
        return pd.DataFrame(columns=["entry_time", "side", "entry_price"])

    return pd.DataFrame(
        {
            "entry_time": fires["timestamp"].values,
            "side": "SHORT",
            "entry_price": fires["close"].astype(float).values,
        }
    )
