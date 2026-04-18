#!/usr/bin/env python3
"""
runner/bb_exit_design_check.py — BB Mean Reversion Exit設計 比較検証

目的:
  Entry: BB バンドタッチ (Signal A/B/C/D) を固定し、
  Exit設計のバリエーションを比較して
  「TP率高・TIME_EXIT損失少・NET高」のベスト設計を特定する。

Exit設計パターン:
  E1: TRAIL gate=0.05% ratio=0.8  (現行)
  E2: TRAIL なし / TP=BB半幅×1.0 / TIME_EXIT=96bar
  E3: TRAIL gate=0.15% ratio=0.8  / TP=BB半幅×1.0
  E4: TRAIL gate=0.30% ratio=0.8  / TP=BB半幅×1.0
  E5: TRAIL なし / TP=BB半幅×1.0 / TIME_EXIT=48bar (4h)
  E6: TRAIL なし / TP=BB半幅×0.5 / TIME_EXIT=96bar  (TP近め)
  E7: TRAIL なし / TP=BB半幅×1.5 / TIME_EXIT=96bar  (TP遠め)

使い方:
    python3 runner/bb_exit_design_check.py [csv_path]
"""
from __future__ import annotations
import sys
import pathlib
from dataclasses import dataclass
from typing import Optional
import pandas as pd
import numpy as np
import ta

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_DEFAULT_CSV = str(_ROOT / "data" / "BTCUSDT-5m-2026-01-01_04-01_combined_90d.csv")

# ============================================================
# 固定パラメータ
# ============================================================
BB_PERIOD    = 20
BB_STD       = 2.0
SL_PCT       = 0.030        # SL = 3.0%（安全網・共通）
TP_MIN_PCT   = 0.0003       # 最低TP下限
POSITION_BTC = 0.06
FEE_RATE     = 0.00014 * 2  # 往復 maker
TIME_EXIT_FULL  = 96        # 8時間
TIME_EXIT_HALF  = 48        # 4時間

# ATRフィルター（L-26: atr_14のみ有効）
ATR_MIN = 80.0

# ============================================================
# Exit設計定義
# ============================================================
@dataclass
class ExitConfig:
    label: str
    tp_bb_ratio: float       # TP = BB半幅 × this
    trail_gate_pct: float    # 0.0 = TRAILなし
    trail_ratio: float       # trail_stop = entry × (1 ± mfe% × this)
    time_exit_bars: int


EXIT_CONFIGS = [
    ExitConfig("E1: TRAIL gate=0.05%",           1.0, 0.05, 0.8, TIME_EXIT_FULL),
    ExitConfig("E2: Pure TP=BB×1.0  TIME=8h",    1.0, 0.00, 0.8, TIME_EXIT_FULL),
    ExitConfig("E3: TRAIL gate=0.15%",           1.0, 0.15, 0.8, TIME_EXIT_FULL),
    ExitConfig("E4: TRAIL gate=0.30%",           1.0, 0.30, 0.8, TIME_EXIT_FULL),
    ExitConfig("E5: Pure TP=BB×1.0  TIME=4h",    1.0, 0.00, 0.8, TIME_EXIT_HALF),
    ExitConfig("E6: Pure TP=BB×0.5  TIME=8h",    0.5, 0.00, 0.8, TIME_EXIT_FULL),
    ExitConfig("E7: Pure TP=BB×1.5  TIME=8h",    1.5, 0.00, 0.8, TIME_EXIT_FULL),
]


def build_indicators(df: pd.DataFrame) -> pd.DataFrame:
    bb = ta.volatility.BollingerBands(df["close"], window=BB_PERIOD, window_dev=BB_STD)
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_lower"] = bb.bollinger_lband()
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["close"]
    atr = ta.volatility.AverageTrueRange(df["high"], df["low"], df["close"], window=14)
    df["atr14"] = atr.average_true_range()
    return df


def detect_signals(df: pd.DataFrame) -> pd.DataFrame:
    prev_close = df["close"].shift(1)
    df["sig_A"] = (df["close"] <= df["bb_lower"]) & (prev_close > df["bb_lower"].shift(1))
    df["sig_B"] = (df["low"] <= df["bb_lower"]) & (df["close"] > df["bb_lower"])
    df["sig_C"] = (df["close"] >= df["bb_upper"]) & (prev_close < df["bb_upper"].shift(1))
    df["sig_D"] = (df["high"] >= df["bb_upper"]) & (df["close"] < df["bb_upper"])
    return df


def simulate_trade(df: pd.DataFrame, i: int, side: str, cfg: ExitConfig) -> dict:
    entry     = df.at[i, "close"]
    bb_upper  = df.at[i, "bb_upper"]
    bb_lower  = df.at[i, "bb_lower"]
    bb_half   = (bb_upper - bb_lower) / 2.0

    tp_dist = max(bb_half * cfg.tp_bb_ratio, entry * TP_MIN_PCT)
    sl_dist = entry * SL_PCT
    tp_price = entry - tp_dist if side == "SHORT" else entry + tp_dist
    sl_price = entry + sl_dist if side == "SHORT" else entry - sl_dist
    fee      = entry * POSITION_BTC * FEE_RATE

    max_fav_pct      = 0.0
    trail_stop_price: Optional[float] = None
    n = len(df)

    for j in range(i + 1, min(i + 1 + cfg.time_exit_bars, n)):
        h = df.at[j, "high"]
        l = df.at[j, "low"]
        bars = j - i

        fav_pct = (entry - l) / entry * 100 if side == "SHORT" else (h - entry) / entry * 100

        # TP
        if (side == "SHORT" and l <= tp_price) or (side == "LONG" and h >= tp_price):
            gross = tp_dist * POSITION_BTC
            return {"result": "TP", "net": gross - fee, "bars": bars, "mfe_pct": max_fav_pct}

        # MFE 更新 → TRAIL gate チェック
        if fav_pct > max_fav_pct:
            max_fav_pct = fav_pct
            if cfg.trail_gate_pct > 0 and max_fav_pct >= cfg.trail_gate_pct:
                if side == "SHORT":
                    trail_stop_price = entry * (1 - max_fav_pct / 100 * cfg.trail_ratio)
                else:
                    trail_stop_price = entry * (1 + max_fav_pct / 100 * cfg.trail_ratio)

        # TRAIL_EXIT
        if trail_stop_price is not None:
            hit = (side == "SHORT" and h >= trail_stop_price) or \
                  (side == "LONG"  and l <= trail_stop_price)
            if hit:
                gross = abs(entry - trail_stop_price) * POSITION_BTC
                return {"result": "TRAIL", "net": gross - fee, "bars": bars, "mfe_pct": max_fav_pct}

        # SL
        if (side == "SHORT" and h >= sl_price) or (side == "LONG" and l <= sl_price):
            gross = -sl_dist * POSITION_BTC
            return {"result": "SL", "net": gross - fee, "bars": bars, "mfe_pct": max_fav_pct}

    # TIME_EXIT
    j = min(i + cfg.time_exit_bars, n - 1)
    gross = (entry - df.at[j, "close"]) * POSITION_BTC if side == "SHORT" \
            else (df.at[j, "close"] - entry) * POSITION_BTC
    return {"result": "TIME", "net": gross - fee, "bars": cfg.time_exit_bars, "mfe_pct": max_fav_pct}


def run_signal_exit(df: pd.DataFrame, sig_col: str, side: str,
                    cfg: ExitConfig, days: float) -> Optional[dict]:
    results = []
    for i in range(1, len(df) - TIME_EXIT_FULL):
        if not df.at[i, sig_col]:
            continue
        atr = df.at[i, "atr14"]
        if pd.isna(atr) or atr < ATR_MIN:
            continue
        if pd.isna(df.at[i, "bb_upper"]):
            continue
        results.append(simulate_trade(df, i, side, cfg))

    if not results:
        return None
    df_r = pd.DataFrame(results)
    n    = len(df_r)
    return {
        "n":        n,
        "per_day":  n / days,
        "net90":    df_r["net"].sum(),
        "ev":       df_r["net"].mean(),
        "tp_r":     (df_r["result"] == "TP").sum()    / n,
        "trail_r":  (df_r["result"] == "TRAIL").sum() / n,
        "time_r":   (df_r["result"] == "TIME").sum()  / n,
        "sl_r":     (df_r["result"] == "SL").sum()    / n,
        "tp_net":   df_r[df_r["result"] == "TP"  ]["net"].sum(),
        "time_net": df_r[df_r["result"] == "TIME"]["net"].sum(),
        "avg_hold": df_r["bars"].mean() * 5,  # bars → minutes
    }


def print_signal_table(sig_label: str, rows: list) -> None:
    print(f"\n{'='*100}")
    print(f"【{sig_label}】  ATR14≥{ATR_MIN:.0f}  SL=3.0%  pos={POSITION_BTC}BTC")
    print(f"{'='*100}")
    hdr = (f"  {'Exit設計':<30} {'件/day':>6} {'NET/90d':>10} {'EV/件':>8} "
           f"{'TP率':>7} {'TRAIL率':>7} {'TIME率':>7} {'SL率':>6} "
           f"{'TP_NET':>9} {'TIME_NET':>10} {'avgHold':>8}")
    print(hdr)
    print("-" * 100)
    best_net = max((r["res"]["net90"] for r in rows if r["res"]), default=0)
    for r in rows:
        if r["res"] is None:
            print(f"  {r['cfg'].label:<30}  シグナルなし")
            continue
        res = r["res"]
        mark = " ◀BEST" if abs(res["net90"] - best_net) < 1 else ""
        print(f"  {r['cfg'].label:<30} {res['per_day']:>6.1f} {res['net90']:>+10.0f}$ "
              f"{res['ev']:>+8.2f}$ {res['tp_r']:>7.1%} {res['trail_r']:>7.1%} "
              f"{res['time_r']:>7.1%} {res['sl_r']:>6.1%} "
              f"{res['tp_net']:>+9.0f}$ {res['time_net']:>+10.0f}$ "
              f"{res['avg_hold']:>7.1f}min{mark}")


def main(csv_path: str) -> None:
    print(f"CSV: {csv_path}")
    df = pd.read_csv(csv_path)
    if "timestamp_ms" in df.columns:
        df = df.rename(columns={"timestamp_ms": "timestamp"})
    df = df.sort_values("timestamp").reset_index(drop=True)
    df = build_indicators(df)
    df = detect_signals(df)

    try:
        ts = pd.to_datetime(df["timestamp"])
        days = (ts.iloc[-1] - ts.iloc[0]).total_seconds() / 86400
    except Exception:
        days = len(df) * 5 / 60 / 24

    print(f"期間: {days:.1f}日  バー数: {len(df)}")
    print(f"BB({BB_PERIOD},{BB_STD})  SL={SL_PCT*100:.1f}%  ATR≥{ATR_MIN:.0f}  POSITION={POSITION_BTC}BTC")
    print(f"\n[Exit設計7パターン × シグナル4種 × ATR≥{ATR_MIN:.0f}固定]")

    for sig_col, side, sig_label in [
        ("sig_A", "LONG",  "Signal A: close≤BB_lower → LONG"),
        ("sig_B", "LONG",  "Signal B: 下ヒゲBB_lower回復 → LONG"),
        ("sig_C", "SHORT", "Signal C: close≥BB_upper → SHORT"),
        ("sig_D", "SHORT", "Signal D: 上ヒゲBB_upper反落 → SHORT"),
    ]:
        rows = []
        for cfg in EXIT_CONFIGS:
            res = run_signal_exit(df, sig_col, side, cfg, days)
            rows.append({"cfg": cfg, "res": res})
        print_signal_table(sig_label, rows)

    # ベスト設計サマリー
    print(f"\n{'='*100}")
    print("【ベスト設計サマリー（NET/90d最大）】")
    print(f"{'='*100}")
    print(f"  {'シグナル':<35} {'Exit設計':<30} {'NET/90d':>10} {'TP率':>7} {'TIME率':>7} {'EV/件':>8}")
    print("-" * 100)
    for sig_col, side, sig_label in [
        ("sig_A", "LONG",  "A: close≤BB_lower (LONG)"),
        ("sig_B", "LONG",  "B: 下ヒゲBB_lower (LONG)"),
        ("sig_C", "SHORT", "C: close≥BB_upper (SHORT)"),
        ("sig_D", "SHORT", "D: 上ヒゲBB_upper (SHORT)"),
    ]:
        best_res, best_cfg = None, None
        for cfg in EXIT_CONFIGS:
            res = run_signal_exit(df, sig_col, side, cfg, days)
            if res and (best_res is None or res["net90"] > best_res["net90"]):
                best_res, best_cfg = res, cfg
        if best_res:
            print(f"  {sig_label:<35} {best_cfg.label:<30} {best_res['net90']:>+10.0f}$ "
                  f"{best_res['tp_r']:>7.1%} {best_res['time_r']:>7.1%} {best_res['ev']:>+8.2f}$")

    print(f"\n{'='*100}")
    print("判定軸: NET/90d最大 かつ TIME率低 かつ TP率高")
    print(f"{'='*100}")


if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else _DEFAULT_CSV
    main(csv_path)
