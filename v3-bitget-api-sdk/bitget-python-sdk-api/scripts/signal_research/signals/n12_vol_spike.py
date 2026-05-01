"""
N12 — 出来高急増 + 陰線 SHORT（売り圧力の顕在化を拾う）

条件:
  vol_avg  = rolling mean(volume, 20)
  volume[i] >= vol_avg[i] × VOL_MULT    (default 1.5)
  close[i]  <  open[i]                  (陰線)
  close[i]  <  close[i-1]               (前足終値も割り込む・下方向確認)
"""
from __future__ import annotations

import pandas as pd

VOL_WINDOW = 20
VOL_MULT = 1.5


def detect(df: pd.DataFrame) -> pd.DataFrame:
    work = df[["timestamp", "open", "high", "low", "close", "volume"]].copy()
    work["vol_avg"] = work["volume"].rolling(VOL_WINDOW).mean()
    work["prev_close"] = work["close"].shift(1)

    cond = (
        (work["volume"] >= work["vol_avg"] * VOL_MULT)
        & (work["close"] < work["open"])
        & (work["close"] < work["prev_close"])
    )
    fires = work[cond]
    if fires.empty:
        return pd.DataFrame(columns=["entry_time", "side", "entry_price"])
    return pd.DataFrame(
        {
            "entry_time": fires["timestamp"].values,
            "side": "SHORT",
            "entry_price": fires["close"].astype(float).values,
        }
    )
