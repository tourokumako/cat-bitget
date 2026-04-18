#!/usr/bin/env python3
"""
runner/macd_edge_check.py — P1/P21新規設計 シグナルエッジ検証
  5m足 + MACD(12,26,9) + MFE_STALE/TIME_EXIT優先・SL遠め設計

Exit優先順位: TP → MFE_STALE → TIME_EXIT → SL（セーフティネット）

使い方:
    python3 runner/macd_edge_check.py [csv_path]
"""
from __future__ import annotations
import sys
import pathlib
import pandas as pd
import numpy as np
import ta

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_DEFAULT_CSV = str(_ROOT / "data" / "BTCUSDT-5m-2026-01-01_04-01_combined_90d.csv")

# ============================================================
# パラメータ（P1/P21 新規設計・ベース値）
# ============================================================
MACD_FAST   = 12
MACD_SLOW   = 26
MACD_SIGNAL = 9

BB_PERIOD = 20
BB_STD    = 2.0

# Exit設計（P4/P22/P23設計思想を踏襲）
TP_BB_RATIO       = 1.0    # TP = BB半幅 × ratio（動的）
TP_MIN_PCT        = 0.0003 # 最低TP: 手数料負けしない下限（fee=$1.41 / pos=$5040 = 0.028%）
SL_PCT            = 0.030  # SL = 3.0%固定（セーフティネット・MAE分布92.2%カバー）

MFE_GATE_PCT   = 0.05  # TRAIL_EXITゲート: MFEがこの%に達してから trail_stop_price を設定
TRAIL_RATIO    = 0.8   # trail_stop_price = entry × (1 + MFE% × TRAIL_RATIO)
                       # 例: MFE=0.35% → trail_stop = entry×(1+0.35%×0.8) = entry×1.0028

TIME_EXIT_BARS     = 96    # 最大保有: 96バー（8時間）

POSITION_BTC = 0.06
FEE_RATE     = 0.00014 * 2  # 往復maker

ADX_MIN = 20.0
# ============================================================


def simulate(csv_path: str) -> None:
    print(f"CSV: {csv_path}")
    df = pd.read_csv(csv_path)
    if "timestamp_ms" in df.columns:
        df = df.rename(columns={"timestamp_ms": "timestamp"})
    df = df.sort_values("timestamp").reset_index(drop=True)

    macd_ind = ta.trend.MACD(df["close"], window_fast=MACD_FAST,
                              window_slow=MACD_SLOW, window_sign=MACD_SIGNAL)
    df["macd"]   = macd_ind.macd()
    df["macd_s"] = macd_ind.macd_signal()

    bb_ind = ta.volatility.BollingerBands(df["close"], window=BB_PERIOD, window_dev=BB_STD)
    df["bb_upper"] = bb_ind.bollinger_hband()
    df["bb_lower"] = bb_ind.bollinger_lband()

    adx_ind = ta.trend.ADXIndicator(df["high"], df["low"], df["close"], window=14)
    df["adx"] = adx_ind.adx()

    ts = pd.to_datetime(df["timestamp"])
    days = (ts.iloc[-1] - ts.iloc[0]).total_seconds() / 86400
    print(f"期間: {days:.1f}日  バー数: {len(df)}")
    print(f"MACD({MACD_FAST},{MACD_SLOW},{MACD_SIGNAL})  BB({BB_PERIOD},{BB_STD})")
    print(f"TP=BB半幅×{TP_BB_RATIO}(min {TP_MIN_PCT*100:.2f}%)  SL={SL_PCT*100:.1f}%固定"
          f"  TRAIL_EXIT≥{MFE_GATE_PCT}%→ratio{TRAIL_RATIO}  TIME_EXIT={TIME_EXIT_BARS}バー  ADX≥{ADX_MIN}\n")

    results = []

    for i in range(1, len(df) - TIME_EXIT_BARS):
        if pd.isna(df.at[i, "macd"]) or pd.isna(df.at[i-1, "macd"]):
            continue
        if pd.isna(df.at[i, "bb_upper"]):
            continue

        adx = df.at[i, "adx"]
        if pd.isna(adx) or adx < ADX_MIN:
            continue

        prev_diff = df.at[i-1, "macd"] - df.at[i-1, "macd_s"]
        curr_diff = df.at[i,   "macd"] - df.at[i,   "macd_s"]
        entry = df.at[i, "close"]
        bb_half = (df.at[i, "bb_upper"] - df.at[i, "bb_lower"]) / 2

        for side, cross_ok in [("LONG",  prev_diff <= 0 and curr_diff > 0),
                                ("SHORT", prev_diff >= 0 and curr_diff < 0)]:
            if not cross_ok:
                continue

            tp_dist = max(bb_half * TP_BB_RATIO, entry * TP_MIN_PCT)
            sl_dist = entry * SL_PCT
            if tp_dist <= 0:
                continue

            if side == "LONG":
                tp_price = entry + tp_dist
                sl_price = entry - sl_dist
            else:
                tp_price = entry - tp_dist
                sl_price = entry + sl_dist

            fee = entry * POSITION_BTC * FEE_RATE
            outcome = _check_outcome(df, i, side, entry, tp_price, sl_price,
                                     tp_dist, sl_dist, fee,
                                     MFE_GATE_PCT, TRAIL_RATIO)
            outcome["side"] = side
            outcome["tp_pct"] = tp_dist / entry * 100
            outcome["sl_pct"] = sl_dist / entry * 100
            results.append(outcome)

    _report(results, days)


def _check_outcome(df, i, side, entry, tp_price, sl_price, tp_dist, sl_dist, fee,
                   mfe_gate, trail_ratio):
    max_fav_pct     = 0.0
    trail_stop_price = None
    max_adv_pct     = 0.0

    for j in range(i + 1, min(i + 1 + TIME_EXIT_BARS, len(df))):
        h = df.at[j, "high"]
        l = df.at[j, "low"]

        if side == "LONG":
            fav_pct = (h - entry) / entry * 100
            adv_pct = (entry - l) / entry * 100
        else:
            fav_pct = (entry - l) / entry * 100
            adv_pct = (h - entry) / entry * 100

        if adv_pct > max_adv_pct:
            max_adv_pct = adv_pct

        bars = j - i

        # Exit優先順位: TP → TRAIL_EXIT → SL（セーフティネット）→ TIME_EXIT

        # TP
        if (side == "LONG" and h >= tp_price) or (side == "SHORT" and l <= tp_price):
            gross = entry * POSITION_BTC * (tp_dist / entry)
            return {"result": "TP", "net": gross - fee, "bars": bars,
                    "mfe_pct": max_fav_pct, "mae_pct": max_adv_pct}

        # MFEピーク更新 → trail_stop_price を切り上げ
        if fav_pct > max_fav_pct:
            max_fav_pct = fav_pct
            if max_fav_pct >= mfe_gate:
                if side == "LONG":
                    trail_stop_price = entry * (1 + max_fav_pct / 100 * trail_ratio)
                else:
                    trail_stop_price = entry * (1 - max_fav_pct / 100 * trail_ratio)

        # TRAIL_EXIT: trail_stop_price を価格が割り込んだら確定利食い
        if trail_stop_price is not None:
            triggered = (side == "LONG" and l <= trail_stop_price) or \
                        (side == "SHORT" and h >= trail_stop_price)
            if triggered:
                if side == "LONG":
                    gross = (trail_stop_price - entry) * POSITION_BTC
                else:
                    gross = (entry - trail_stop_price) * POSITION_BTC
                return {"result": "TRAIL_EXIT", "net": gross - fee, "bars": bars,
                        "mfe_pct": max_fav_pct, "mae_pct": max_adv_pct}

        # SL（セーフティネット）
        if (side == "LONG" and l <= sl_price) or (side == "SHORT" and h >= sl_price):
            gross = -entry * POSITION_BTC * (sl_dist / entry)
            return {"result": "SL", "net": gross - fee, "bars": bars,
                    "mfe_pct": max_fav_pct, "mae_pct": max_adv_pct}

    # TIME_EXIT
    j = min(i + TIME_EXIT_BARS, len(df) - 1)
    if side == "LONG":
        gross = (df.at[j, "close"] - entry) * POSITION_BTC
    else:
        gross = (entry - df.at[j, "close"]) * POSITION_BTC
    return {"result": "TIME_EXIT", "net": gross - fee, "bars": TIME_EXIT_BARS,
            "mfe_pct": max_fav_pct, "mae_pct": max_adv_pct}


def _report(results, days):
    if not results:
        print("シグナルなし")
        return

    df_r = pd.DataFrame(results)

    for side in ["LONG", "SHORT", "合算"]:
        if side == "合算":
            sub_all = df_r
        else:
            sub_all = df_r[df_r["side"] == side]
        if sub_all.empty:
            continue

        n = len(sub_all)
        net_total = sub_all["net"].sum()
        avg_tp_pct = sub_all["tp_pct"].mean()
        avg_sl_pct = sub_all["sl_pct"].mean()
        print(f"=== {side} ===")
        print(f"  件数: {n}件  ({n/days:.1f}/day)  NET: ${net_total:.2f}  (${net_total/days:.2f}/day)")
        print(f"  avg TP幅: {avg_tp_pct:.3f}%  avg SL幅: {avg_sl_pct:.3f}%")

        for reason in ["TP", "TRAIL_EXIT", "TIME_EXIT", "SL"]:
            sub = sub_all[sub_all["result"] == reason]
            if sub.empty:
                continue
            cnt = len(sub)
            net = sub["net"].sum()
            avg_net = sub["net"].mean()
            avg_bars = sub["bars"].mean()
            avg_mfe = sub["mfe_pct"].mean()
            print(f"  [{reason}] {cnt}件 ({cnt/n:.1%})  NET: ${net:.2f}  avg: ${avg_net:.2f}/trade"
                  f"  avg保有: {avg_bars:.1f}バー  avg MFE: {avg_mfe:.3f}%")
        print()

    print(f"  TP=BB半幅×{TP_BB_RATIO}(min {TP_MIN_PCT*100:.2f}%)  SL={SL_PCT*100:.1f}%固定"
          f"  TRAIL_EXIT≥{MFE_GATE_PCT}%→ratio{TRAIL_RATIO}  TIME_EXIT={TIME_EXIT_BARS}バー  ADX≥{ADX_MIN}")


if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else _DEFAULT_CSV
    simulate(csv_path)
