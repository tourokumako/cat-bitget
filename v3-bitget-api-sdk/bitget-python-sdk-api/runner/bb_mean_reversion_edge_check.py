#!/usr/bin/env python3
"""
runner/bb_mean_reversion_edge_check.py — BB Mean Reversion シグナルエッジ検証 (Step N-2)

対象: P1/P21 再構築候補
Exit設計: TP=BB半幅×ratio(動的) + TRAIL_EXIT(gate/ratio) + SL(安全網) + TIME_EXIT

シグナル候補:
  A: close <= bb_lower                    (下限突破クローズ → LONG)
  B: low <= bb_lower AND close > bb_lower (下限タッチ後回復バー → LONG)
  C: close >= bb_upper                    (上限突破クローズ → SHORT)
  D: high >= bb_upper AND close < bb_upper(上限タッチ後反落バー → SHORT)

使い方:
    python3 runner/bb_mean_reversion_edge_check.py [csv_path]
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
# Exit パラメータ（固定）
# ============================================================
BB_PERIOD       = 20
BB_STD          = 2.0
TP_BB_RATIO     = 1.0    # TP = BB半幅 × ratio
TP_MIN_PCT      = 0.0003 # 最低TP下限（手数料負けしない水準）
SL_PCT          = 0.030  # SL = 3.0%（安全網）
MFE_GATE_PCT    = 0.05   # TRAIL_EXIT ゲート（MFEがこの%に達したら trail 開始）
TRAIL_RATIO     = 0.8    # trail_stop = entry × (1 ± MFE% × TRAIL_RATIO)
TIME_EXIT_BARS  = 96     # 最大保有: 96バー = 8時間

POSITION_BTC = 0.06
FEE_RATE     = 0.00014 * 2  # 往復 maker

# ============================================================
# フィルター組み合わせ（全パターンをテスト）
# ============================================================
FILTER_COMBOS = [
    # label             adx_max  atr_min  bb_width_min
    ("フィルターなし",    999,      0,       0.000),
    ("ADX≤40",          40,       0,       0.000),
    ("ADX≤30",          30,       0,       0.000),
    ("ATR≥80",          999,      80,      0.000),
    ("ATR≥120",         999,      120,     0.000),
    ("BB幅≥0.004",       999,      0,       0.004),
    ("BB幅≥0.006",       999,      0,       0.006),
    ("ADX≤40+ATR≥80",   40,       80,      0.000),
    ("ADX≤30+ATR≥80",   30,       80,      0.000),
    ("ADX≤40+BB幅≥0.004",40,      0,       0.004),
]


def build_indicators(df: pd.DataFrame) -> pd.DataFrame:
    bb = ta.volatility.BollingerBands(df["close"], window=BB_PERIOD, window_dev=BB_STD)
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_lower"] = bb.bollinger_lband()
    df["bb_mid"]   = bb.bollinger_mavg()
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["close"]

    adx_ind = ta.trend.ADXIndicator(df["high"], df["low"], df["close"], window=14)
    df["adx"] = adx_ind.adx()

    atr_ind = ta.volatility.AverageTrueRange(df["high"], df["low"], df["close"], window=14)
    df["atr14"] = atr_ind.average_true_range()

    return df


def detect_signals(df: pd.DataFrame) -> pd.DataFrame:
    """シグナルA/B/C/Dを検出して列に追加"""
    prev_low   = df["low"].shift(1)
    prev_high  = df["high"].shift(1)
    prev_close = df["close"].shift(1)

    # A: 今バーの close が bb_lower を下抜け（前バーは上にいた）
    df["sig_A"] = (df["close"] <= df["bb_lower"]) & (prev_close > df["bb_lower"].shift(1))

    # B: 今バーの low が bb_lower タッチかつ close は bb_lower より上（下ヒゲ回復）
    df["sig_B"] = (df["low"] <= df["bb_lower"]) & (df["close"] > df["bb_lower"])

    # C: 今バーの close が bb_upper を上抜け（前バーは下にいた）
    df["sig_C"] = (df["close"] >= df["bb_upper"]) & (prev_close < df["bb_upper"].shift(1))

    # D: 今バーの high が bb_upper タッチかつ close は bb_upper より下（上ヒゲ反落）
    df["sig_D"] = (df["high"] >= df["bb_upper"]) & (df["close"] < df["bb_upper"])

    return df


def simulate_trade(df: pd.DataFrame, i: int, side: str) -> dict:
    """1トレードのシミュレーション"""
    entry = df.at[i, "close"]
    bb_upper = df.at[i, "bb_upper"]
    bb_lower = df.at[i, "bb_lower"]
    bb_half  = (bb_upper - bb_lower) / 2.0

    tp_dist = max(bb_half * TP_BB_RATIO, entry * TP_MIN_PCT)
    sl_dist = entry * SL_PCT

    if side == "LONG":
        tp_price = entry + tp_dist
        sl_price = entry - sl_dist
    else:
        tp_price = entry - tp_dist
        sl_price = entry + sl_dist

    fee = entry * POSITION_BTC * FEE_RATE
    tp_pct  = tp_dist / entry * 100
    sl_pct  = sl_dist / entry * 100

    max_fav_pct      = 0.0
    trail_stop_price = None

    n = len(df)
    for j in range(i + 1, min(i + 1 + TIME_EXIT_BARS, n)):
        h = df.at[j, "high"]
        l = df.at[j, "low"]
        bars = j - i

        if side == "LONG":
            fav_pct = (h - entry) / entry * 100
            adv_pct = (entry - l) / entry * 100
        else:
            fav_pct = (entry - l) / entry * 100
            adv_pct = (h - entry) / entry * 100

        # TP
        if (side == "LONG" and h >= tp_price) or \
           (side == "SHORT" and l <= tp_price):
            gross = entry * POSITION_BTC * (tp_dist / entry)
            return {"result": "TP", "net": gross - fee, "bars": bars,
                    "mfe_pct": max_fav_pct, "tp_pct": tp_pct, "sl_pct": sl_pct}

        # MFE 更新 → trail_stop_price を更新
        if fav_pct > max_fav_pct:
            max_fav_pct = fav_pct
            if max_fav_pct >= MFE_GATE_PCT:
                if side == "LONG":
                    trail_stop_price = entry * (1 + max_fav_pct / 100 * TRAIL_RATIO)
                else:
                    trail_stop_price = entry * (1 - max_fav_pct / 100 * TRAIL_RATIO)

        # TRAIL_EXIT
        if trail_stop_price is not None:
            hit = (side == "LONG" and l <= trail_stop_price) or \
                  (side == "SHORT" and h >= trail_stop_price)
            if hit:
                if side == "LONG":
                    gross = (trail_stop_price - entry) * POSITION_BTC
                else:
                    gross = (entry - trail_stop_price) * POSITION_BTC
                return {"result": "TRAIL_EXIT", "net": gross - fee, "bars": bars,
                        "mfe_pct": max_fav_pct, "tp_pct": tp_pct, "sl_pct": sl_pct}

        # SL（安全網）
        if (side == "LONG" and l <= sl_price) or \
           (side == "SHORT" and h >= sl_price):
            gross = -entry * POSITION_BTC * (sl_dist / entry)
            return {"result": "SL", "net": gross - fee, "bars": bars,
                    "mfe_pct": max_fav_pct, "tp_pct": tp_pct, "sl_pct": sl_pct}

    # TIME_EXIT
    j = min(i + TIME_EXIT_BARS, n - 1)
    if side == "LONG":
        gross = (df.at[j, "close"] - entry) * POSITION_BTC
    else:
        gross = (entry - df.at[j, "close"]) * POSITION_BTC
    return {"result": "TIME_EXIT", "net": gross - fee, "bars": TIME_EXIT_BARS,
            "mfe_pct": max_fav_pct, "tp_pct": tp_pct, "sl_pct": sl_pct}


def run_scenario(df: pd.DataFrame, sig_col: str, side: str,
                 adx_max: float, atr_min: float, bb_width_min: float,
                 days: float) -> dict | None:
    """シグナルcol × フィルター条件で全トレードをシミュレート"""
    results = []
    for i in range(1, len(df) - TIME_EXIT_BARS):
        if not df.at[i, sig_col]:
            continue
        adx = df.at[i, "adx"]
        atr = df.at[i, "atr14"]
        bw  = df.at[i, "bb_width"]
        if pd.isna(adx) or adx > adx_max:
            continue
        if pd.isna(atr) or atr < atr_min:
            continue
        if pd.isna(bw) or bw < bb_width_min:
            continue
        if pd.isna(df.at[i, "bb_upper"]):
            continue
        results.append(simulate_trade(df, i, side))

    if not results:
        return None

    df_r   = pd.DataFrame(results)
    n      = len(df_r)
    net90  = df_r["net"].sum()
    ev     = df_r["net"].mean()
    win_r  = (df_r["result"] == "TP").sum() / n
    trail_r= (df_r["result"] == "TRAIL_EXIT").sum() / n
    time_r = (df_r["result"] == "TIME_EXIT").sum() / n
    sl_r   = (df_r["result"] == "SL").sum() / n

    return {
        "n": n, "per_day": n / days, "net90": net90, "ev": ev,
        "win_r": win_r, "trail_r": trail_r, "time_r": time_r, "sl_r": sl_r,
        "avg_tp_pct": df_r["tp_pct"].mean(),
    }


def print_table(rows: list[dict], title: str) -> None:
    print(f"\n{'='*80}")
    print(f"【{title}】")
    print(f"{'='*80}")
    hdr = f"  {'フィルター':<22} {'件数':>5} {'/day':>5} {'NET/90d':>10} {'EV/件':>8} "
    hdr += f"{'勝率(TP)':>8} {'TRAIL':>7} {'TIME':>7} {'SL':>6} {'avgTP%':>7}"
    print(hdr)
    print("-" * 80)
    for r in rows:
        if r["res"] is None:
            print(f"  {r['label']:<22}  シグナルなし")
            continue
        res = r["res"]
        mark = ""
        if res["win_r"] >= 0.60 and res["ev"] > 0:
            mark = " ✅"
        elif res["win_r"] >= 0.50 and res["ev"] > 0:
            mark = " △"
        line = (f"  {r['label']:<22} {res['n']:>5} {res['per_day']:>5.1f} "
                f"{res['net90']:>+10.0f}$ {res['ev']:>+8.2f}$ "
                f"{res['win_r']:>7.1%} {res['trail_r']:>7.1%} "
                f"{res['time_r']:>7.1%} {res['sl_r']:>6.1%} "
                f"{res['avg_tp_pct']:>7.3f}%{mark}")
        print(line)


def main(csv_path: str) -> None:
    print(f"CSV: {csv_path}")
    df = pd.read_csv(csv_path)
    if "timestamp_ms" in df.columns:
        df = df.rename(columns={"timestamp_ms": "timestamp"})
    df = df.sort_values("timestamp").reset_index(drop=True)

    df = build_indicators(df)
    df = detect_signals(df)

    ts  = pd.to_datetime(df["timestamp"] if "timestamp" in df.columns else df.index)
    # 日数計算
    try:
        ts_series = pd.to_datetime(df["timestamp"])
        days = (ts_series.iloc[-1] - ts_series.iloc[0]).total_seconds() / 86400
    except Exception:
        days = len(df) * 5 / 60 / 24

    print(f"期間: {days:.1f}日  バー数: {len(df)}")
    print(f"BB({BB_PERIOD},{BB_STD})  TP=BB半幅×{TP_BB_RATIO}(min {TP_MIN_PCT*100:.2f}%)  "
          f"SL={SL_PCT*100:.1f}%  TRAIL_GATE={MFE_GATE_PCT}%×ratio{TRAIL_RATIO}  "
          f"TIME_EXIT={TIME_EXIT_BARS}バー({TIME_EXIT_BARS*5//60}h)  "
          f"POSITION={POSITION_BTC}BTC")

    # シグナル件数の概要
    print(f"\n--- シグナル検出数（フィルターなし）---")
    for sig, label in [("sig_A","A: close≤BB_lower (LONG)"),
                        ("sig_B","B: low≤BB_lower & close>BB_lower (LONG)"),
                        ("sig_C","C: close≥BB_upper (SHORT)"),
                        ("sig_D","D: high≥BB_upper & close<BB_upper (SHORT)")]:
        cnt = df[sig].sum()
        print(f"  {label}: {cnt}件 ({cnt/days:.1f}/day)")

    # シグナル × フィルターの全パターン実行
    for sig_col, side, title in [
        ("sig_A", "LONG",  "シグナルA: close≤BB_lower → LONG"),
        ("sig_B", "LONG",  "シグナルB: 下ヒゲBB_lower回復 → LONG"),
        ("sig_C", "SHORT", "シグナルC: close≥BB_upper → SHORT"),
        ("sig_D", "SHORT", "シグナルD: 上ヒゲBB_upper反落 → SHORT"),
    ]:
        rows = []
        for label, adx_max, atr_min, bb_width_min in FILTER_COMBOS:
            res = run_scenario(df, sig_col, side, adx_max, atr_min, bb_width_min, days)
            rows.append({"label": label, "res": res})
        print_table(rows, title)

    print(f"\n{'='*80}")
    print("判定基準: ✅ 勝率≥60% かつ EV>0  △ 勝率≥50% かつ EV>0  ⚠ EV≤0")
    print(f"{'='*80}")


if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else _DEFAULT_CSV
    main(csv_path)
