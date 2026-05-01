"""
N15 — ADX上昇 + DI クロス複合（トレンド開始点）

ADX が上昇かつ DI- が DI+ を上抜け → SHORT トレンド始動
ADX が上昇かつ DI+ が DI- を上抜け → LONG  トレンド始動

条件:
  adx[i] > adx[i-1]                                (ADX上昇中)
  adx[i] >= ADX_MIN                                (default 20: 最低限のトレンド存在)
  SHORT : minus_di[i] > plus_di[i] and minus_di[i-1] <= plus_di[i-1]
  LONG  : plus_di[i]  > minus_di[i] and plus_di[i-1]  <= minus_di[i-1]
"""
from __future__ import annotations

import pandas as pd
import ta

ADX_MIN = 20.0


def detect(df: pd.DataFrame) -> pd.DataFrame:
    adx = ta.trend.ADXIndicator(df["high"], df["low"], df["close"], window=14)
    work = df[["timestamp", "open", "high", "low", "close"]].copy()
    work["adx"] = adx.adx()
    work["plus_di"] = adx.adx_pos()
    work["minus_di"] = adx.adx_neg()
    work["prev_adx"] = work["adx"].shift(1)
    work["prev_plus"] = work["plus_di"].shift(1)
    work["prev_minus"] = work["minus_di"].shift(1)

    base = (work["adx"] > work["prev_adx"]) & (work["adx"] >= ADX_MIN)
    short_cond = base & (work["minus_di"] > work["plus_di"]) & (work["prev_minus"] <= work["prev_plus"])
    long_cond = base & (work["plus_di"] > work["minus_di"]) & (work["prev_plus"] <= work["prev_minus"])

    rows = []
    for _, r in work[short_cond].iterrows():
        rows.append({"entry_time": r["timestamp"], "side": "SHORT", "entry_price": float(r["close"])})
    for _, r in work[long_cond].iterrows():
        rows.append({"entry_time": r["timestamp"], "side": "LONG", "entry_price": float(r["close"])})

    if not rows:
        return pd.DataFrame(columns=["entry_time", "side", "entry_price"])
    return pd.DataFrame(rows).sort_values("entry_time").reset_index(drop=True)
