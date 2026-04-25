"""
N9 — MACD ゼロライン回帰（ヒストグラム転換）

順張り→反転点を MACDヒスト 符号転換 + シグナル線方向で拾う。

条件:
  fast=12, slow=26, signal=9
  LONG : macd_diff[i-1] < 0 and macd_diff[i] > 0   (ヒスト 0 上抜け)
  SHORT: macd_diff[i-1] > 0 and macd_diff[i] < 0   (ヒスト 0 下抜け)
"""
from __future__ import annotations

import pandas as pd
import ta


def detect(df: pd.DataFrame) -> pd.DataFrame:
    macd = ta.trend.MACD(df["close"], window_slow=26, window_fast=12, window_sign=9)
    work = df[["timestamp", "open", "high", "low", "close"]].copy()
    work["hist"] = macd.macd_diff()
    work["prev_hist"] = work["hist"].shift(1)

    long_cond = (work["prev_hist"] < 0) & (work["hist"] > 0)
    short_cond = (work["prev_hist"] > 0) & (work["hist"] < 0)

    rows = []
    for _, r in work[long_cond].iterrows():
        rows.append({"entry_time": r["timestamp"], "side": "LONG", "entry_price": float(r["close"])})
    for _, r in work[short_cond].iterrows():
        rows.append({"entry_time": r["timestamp"], "side": "SHORT", "entry_price": float(r["close"])})

    if not rows:
        return pd.DataFrame(columns=["entry_time", "side", "entry_price"])
    return pd.DataFrame(rows).sort_values("entry_time").reset_index(drop=True)
