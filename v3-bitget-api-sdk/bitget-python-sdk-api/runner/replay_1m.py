#!/usr/bin/env python3
"""
runner/replay_1m.py — V10 スキャル戦略 1分足リプレイシミュレーター

使い方:
    cd v3-bitget-api-sdk/bitget-python-sdk-api
    .venv/bin/python3 runner/replay_1m.py /path/to/BTCUSDT-1m-binance-...csv

出力:
    results/replay_v10_{filename}.csv
    サマリーを標準出力に表示

設計:
    - シグナル: ストキャス(K/D/Slowing) OB/OS クロス
    - エントリー: close ± LIMIT_OFFSET_PCT 指値、TTL=PENDING_TTL_BARS
    - エグジット: TP / SL / 時間エグジット（優先順位順）
    - add なし（1エントリー1決済）
    - LONG / SHORT 同時保有可（MAX_SIDES=2）
    - 手数料: entry=maker / exit TP=maker / exit SL,TIME=taker
"""
from __future__ import annotations

import json
import pathlib
import sys
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
import numpy as np

_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_PARAMS_PATH = _ROOT / "config" / "cat_params_v10.json"
_RESULTS_DIR = _ROOT / "results"
_JST         = timezone(timedelta(hours=9))
CANDLE_WARMUP = 210  # 200EMA 安定化に必要


# ================================================================
# パラメータ読み込み
# ================================================================
def _load_params() -> Dict[str, Any]:
    with open(_PARAMS_PATH, encoding="utf-8") as f:
        return json.load(f)


# ================================================================
# CSV 読み込み
# ================================================================
def _load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    rename = {}
    for c in df.columns:
        lc = c.lower().strip()
        if lc in ("timestamp", "ts", "ts_ms", "timestamp_ms", "open_time"):
            rename[c] = "_ts_raw"
        elif lc == "open":   rename[c] = "open"
        elif lc == "high":   rename[c] = "high"
        elif lc == "low":    rename[c] = "low"
        elif lc == "close":  rename[c] = "close"
        elif lc in ("vol", "volume"): rename[c] = "volume"
    df = df.rename(columns=rename)

    ts_raw = df["_ts_raw"]
    if pd.api.types.is_numeric_dtype(ts_raw):
        sample = float(ts_raw.iloc[0])
        df["timestamp_ms"] = (ts_raw.astype(float) / 1000).astype(int) if sample > 1e15 else ts_raw.astype(int)
    else:
        df["timestamp_ms"] = (pd.to_datetime(ts_raw).astype("int64") // 1_000_000).astype(int)

    df = df.sort_values("timestamp_ms").reset_index(drop=True)
    for c in ("open", "high", "low", "close"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


# ================================================================
# 指標計算
# ================================================================
def _calc_indicators(df: pd.DataFrame, params: Dict) -> pd.DataFrame:
    k_period      = int(params["STOCH_K"])
    d_period      = int(params["STOCH_D"])
    slowing       = int(params["STOCH_SLOWING"])
    ema_period    = int(params["EMA_PERIOD"])
    ema_5m_period = int(params.get("EMA_5M_PERIOD", 200))
    bb_period     = int(params["BB_PERIOD"])
    bb_std        = float(params["BB_STD"])
    rsi_period    = int(params.get("RSI_PERIOD", 9))

    df = df.copy()

    # Stochastic
    low_min  = df["low"].rolling(k_period).min()
    high_max = df["high"].rolling(k_period).max()
    raw_k    = 100.0 * (df["close"] - low_min) / (high_max - low_min + 1e-9)
    slow_k   = raw_k.rolling(slowing).mean()
    slow_d   = slow_k.rolling(d_period).mean()

    # EMA（200 と 20）
    ema200_1m = df["close"].ewm(span=ema_period, adjust=False).mean()
    ema20_1m  = df["close"].ewm(span=20, adjust=False).mean()

    # Bollinger Bands (1m)
    bb_mid   = df["close"].rolling(bb_period).mean()
    bb_s     = df["close"].rolling(bb_period).std(ddof=0)
    bb_upper = bb_mid + bb_std * bb_s
    bb_lower = bb_mid - bb_std * bb_s

    # RSI
    delta    = df["close"].diff()
    gain     = delta.clip(lower=0).rolling(rsi_period).mean()
    loss     = (-delta.clip(upper=0)).rolling(rsi_period).mean()
    rsi      = 100 - 100 / (1 + gain / (loss + 1e-9))

    df["stoch_k"]  = slow_k
    df["stoch_d"]  = slow_d
    df["ema200"]   = ema200_1m
    df["ema20"]    = ema20_1m
    df["bb_upper"] = bb_upper
    df["bb_lower"] = bb_lower
    df["bb_mid"]   = bb_mid
    df["rsi"]      = rsi

    # 5m EMA — 1m を 5m にリサンプルして EMA 計算後、1m に前方補完でマージ
    df["datetime"] = pd.to_datetime(df["timestamp_ms"], unit="ms", utc=True)
    df5 = (
        df.set_index("datetime")["close"]
        .resample("5min")
        .last()
        .dropna()
        .to_frame()
    )
    df5["ema200_5m"] = df5["close"].ewm(span=ema_5m_period, adjust=False).mean()

    df = df.merge(
        df5[["ema200_5m"]].reset_index(),
        on="datetime",
        how="left",
    )
    df["ema200_5m"] = df["ema200_5m"].ffill()

    # 15m ADX + DMI — レジーム判定用
    adx_period = int(params.get("ADX_PERIOD", 14))
    alpha_adx  = 1.0 / adx_period
    df15 = (
        df.set_index("datetime")
        .resample("15min")
        .agg({"open": "first", "high": "max", "low": "min", "close": "last"})
        .dropna()
    )
    h15, l15, c15 = df15["high"], df15["low"], df15["close"]
    pc15 = c15.shift(1)
    ph15 = h15.shift(1)
    pl15 = l15.shift(1)
    tr15 = pd.concat([h15 - l15, (h15 - pc15).abs(), (l15 - pc15).abs()], axis=1).max(axis=1)
    raw_plus  = (h15 - ph15).clip(lower=0)
    raw_minus = (pl15 - l15).clip(lower=0)
    mask15    = raw_plus >= raw_minus
    plus_dm15  = raw_plus.where(mask15, 0.0)
    minus_dm15 = raw_minus.where(~mask15, 0.0)
    atr15      = tr15.ewm(alpha=alpha_adx, adjust=False).mean()
    plus_di15  = 100 * plus_dm15.ewm(alpha=alpha_adx, adjust=False).mean() / (atr15 + 1e-9)
    minus_di15 = 100 * minus_dm15.ewm(alpha=alpha_adx, adjust=False).mean() / (atr15 + 1e-9)
    dx15  = 100 * (plus_di15 - minus_di15).abs() / (plus_di15 + minus_di15 + 1e-9)
    adx15 = dx15.ewm(alpha=alpha_adx, adjust=False).mean()
    df15["adx_15m"]      = adx15
    df15["plus_di_15m"]  = plus_di15
    df15["minus_di_15m"] = minus_di15
    df = df.merge(
        df15[["adx_15m", "plus_di_15m", "minus_di_15m"]].reset_index(),
        on="datetime",
        how="left",
    )
    df["adx_15m"]      = df["adx_15m"].ffill()
    df["plus_di_15m"]  = df["plus_di_15m"].ffill()
    df["minus_di_15m"] = df["minus_di_15m"].ffill()

    return df


# ================================================================
# シグナル検出（Stoch K/Dクロス + RSI 過熱判定）
# ================================================================
def _detect_signals(df: pd.DataFrame, params: Dict) -> pd.DataFrame:
    rsi_ob = float(params.get("RSI_OB", 70))
    rsi_os = float(params.get("RSI_OS", 30))

    k   = df["stoch_k"]
    d   = df["stoch_d"]
    k_p = k.shift(1)
    d_p = d.shift(1)

    # Stoch K/D クロス（OS/OB条件なし）
    stoch_cross_up   = (k > d) & (k_p <= d_p)
    stoch_cross_down = (k < d) & (k_p >= d_p)

    # RSI 過熱判定 + Stoch クロス
    sig_long  = (df["rsi"] < rsi_os) & stoch_cross_up
    sig_short = (df["rsi"] > rsi_ob) & stoch_cross_down

    df = df.copy()
    df["sig_long"]  = sig_long.fillna(False)
    df["sig_short"] = sig_short.fillna(False)
    return df


# ================================================================
# 時刻フォーマット（UTC）
# ================================================================
def _ts_str(ts_ms: int) -> str:
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


# ================================================================
# トレード記録
# ================================================================
def _record_trade(trades: List, pos: Dict, exit_price: float,
                  exit_reason: str, exit_ts_ms: int, params: Dict) -> None:
    side     = pos["side"]
    entry_p  = float(pos["entry_price"])
    size_b   = float(pos["size_btc"])
    entry_ms = int(pos["entry_time"])
    hold_min = round((exit_ts_ms - entry_ms) / 60_000, 1)

    gross = (exit_price - entry_p) * size_b if side == "LONG" else (entry_p - exit_price) * size_b
    maker = float(params["FEE_RATE_MAKER"])
    # TP/SL ともに maker指値
    fee  = size_b * entry_p * maker + size_b * exit_price * maker
    net  = gross - fee

    trades.append({
        "entry_time":   _ts_str(entry_ms),
        "exit_time":    _ts_str(exit_ts_ms),
        "side":         side,
        "size_btc":     round(size_b, 4),
        "entry_price":  round(entry_p, 2),
        "exit_price":   round(exit_price, 2),
        "exit_reason":  exit_reason,
        "hold_min":     hold_min,
        "gross_usd":    round(gross, 4),
        "fee_usd":      round(fee, 4),
        "net_usd":      round(net, 4),
        "stoch_k_entry": round(float(pos.get("stoch_k_entry", float("nan"))), 2),
        "stoch_d_entry": round(float(pos.get("stoch_d_entry", float("nan"))), 2),
        "entry_hour":   int(pos.get("entry_hour", -1)),
    })


# ================================================================
# メインループ
# ================================================================
def run_replay(csv_path: str) -> List[Dict]:
    params  = _load_params()
    df_raw  = _load_csv(csv_path)
    df      = _calc_indicators(df_raw, params)
    df      = _detect_signals(df, params)

    tp_pct     = float(params["TP_PCT"])
    sl_pct     = float(params["SL_PCT"])
    size_btc   = float(params["POSITION_SIZE_BTC"])
    ttl_bars   = int(params["PENDING_TTL_BARS"])
    lim_offset = float(params["LIMIT_OFFSET_PCT"])

    # 保有中ポジション {side: pos_dict}
    positions: Dict[str, Optional[Dict]] = {"LONG": None, "SHORT": None}
    # ペンディングエントリー {side: {limit_price, ttl_remaining}}
    pending: Dict[str, Optional[Dict]]   = {"LONG": None, "SHORT": None}

    trades: List[Dict] = []
    rows  = df.to_dict("records")
    n     = len(rows)

    for i in range(CANDLE_WARMUP, n):
        row    = rows[i]
        ts_ms  = int(row["timestamp_ms"])
        hi     = float(row["high"])
        lo     = float(row["low"])
        cl     = float(row["close"])
        dt_utc = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)

        # ---- 1. pending fill 判定 ----
        for side in ("LONG", "SHORT"):
            if pending[side] is None:
                continue
            pend = pending[side]
            lp   = float(pend["limit_price"])
            filled = (side == "LONG" and lo <= lp) or (side == "SHORT" and hi >= lp)
            if filled:
                entry_price = lp
                positions[side] = {
                    "side":          side,
                    "entry_price":   entry_price,
                    "entry_time":    ts_ms,
                    "size_btc":      size_btc,
                    "tp_price":      entry_price * (1 + tp_pct) if side == "LONG" else entry_price * (1 - tp_pct),
                    "sl_price":      entry_price * (1 - sl_pct) if side == "LONG" else entry_price * (1 + sl_pct),
                    "mfe_usd":       0.0,
                    "stoch_k_entry": pend.get("stoch_k"),
                    "stoch_d_entry": pend.get("stoch_d"),
                    "entry_hour":    dt_utc.hour,
                }
                pending[side] = None
            else:
                pend["ttl"] -= 1
                if pend["ttl"] <= 0:
                    pending[side] = None  # TTL 切れキャンセル

        # ---- 2. 保有ポジションの exit 判定 ----
        for side in ("LONG", "SHORT"):
            pos = positions[side]
            if pos is None:
                continue

            entry_p  = float(pos["entry_price"])
            tp_price = float(pos["tp_price"])
            sl_price = float(pos["sl_price"])   # 0 = 無効
            entry_ms = int(pos["entry_time"])
            hold_min = (ts_ms - entry_ms) / 60_000

            # MFE 更新
            unreal = (cl - entry_p) * size_btc if side == "LONG" else (entry_p - cl) * size_btc
            pos["mfe_usd"] = max(float(pos["mfe_usd"]), unreal)

            exit_reason: Optional[str] = None
            exit_price:  float = cl

            # TP (intra-bar: LONG=high, SHORT=low)
            if side == "LONG" and hi >= tp_price:
                exit_reason = "TP_FILLED"
                exit_price  = tp_price
            elif side == "SHORT" and lo <= tp_price:
                exit_reason = "TP_FILLED"
                exit_price  = tp_price
            # SL (intra-bar) — SL_PCT=0 のとき無効
            elif sl_price > 0 and side == "LONG" and lo <= sl_price:
                exit_reason = "SL_FILLED"
                exit_price  = sl_price
            elif sl_price > 0 and side == "SHORT" and hi >= sl_price:
                exit_reason = "SL_FILLED"
                exit_price  = sl_price

            if exit_reason:
                _record_trade(trades, pos, exit_price, exit_reason, ts_ms, params)
                positions[side] = None

        # ---- 3. 新規シグナル → pending 登録 ----
        for side, sig_col in (("LONG", "sig_long"), ("SHORT", "sig_short")):
            if not row.get(sig_col, False):
                continue
            if positions[side] is not None:
                continue
            if pending[side] is not None:
                continue

            limit_price = cl * (1 - lim_offset) if side == "LONG" else cl * (1 + lim_offset)
            pending[side] = {
                "limit_price": limit_price,
                "ttl":         ttl_bars,
                "stoch_k":     row.get("stoch_k"),
                "stoch_d":     row.get("stoch_d"),
            }

    return trades


# ================================================================
# サマリー出力
# ================================================================
def _print_summary(df: pd.DataFrame, days: float) -> None:
    total = len(df)
    if total == 0:
        print("[WARN] トレードなし")
        return

    net     = df["net_usd"].sum()
    gross   = df["gross_usd"].sum()
    fee     = df["fee_usd"].sum()
    net_d   = net / days
    avg_h   = df["hold_min"].mean()

    tp_n  = (df["exit_reason"] == "TP_FILLED").sum()
    sl_n  = (df["exit_reason"] == "SL_FILLED").sum()
    tp_r  = tp_n / total * 100

    W = 56
    print(f"\n{'='*W}")
    print(f"  V10 Replay (Stoch+RSI)  [{df['entry_time'].iloc[0][:10]} 〜 {df['entry_time'].iloc[-1][:10]}]")
    print(f"{'='*W}")
    print(f"  {'トレード数':<16}: {total:,}件  ({total/days:.1f}件/日)")
    print(f"  {'NET 利益':<16}: ${net:>10,.2f}  (${net_d:>8.2f}/日)")
    print(f"  {'GROSS 利益':<16}: ${gross:>10,.2f}")
    print(f"  {'手数料合計':<16}: ${fee:>10,.2f}  (${fee/total:.3f}/件)")
    print(f"  {'平均保有時間':<16}: {avg_h:.1f}分")
    print(f"{'─'*W}")
    print(f"  {'TP/SL':<16}: TP={tp_n}件({tp_r:.1f}%)  SL={sl_n}件")
    print(f"{'─'*W}")
    for reason in ("SL_FILLED", "TP_FILLED"):
        grp = df[df["exit_reason"] == reason]
        if len(grp) == 0:
            continue
        tag = "✗" if reason != "TP_FILLED" else "✓"
        print(f"  {tag} {reason:<14}: {len(grp):5,}件  NET=${grp['net_usd'].sum():>10,.2f}"
              f"  avg=${grp['net_usd'].mean():>6.2f}/件")
    print(f"{'='*W}")


# ================================================================
# エントリポイント
# ================================================================
def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python runner/replay_1m.py <csv_path>")
        sys.exit(1)

    csv_path = sys.argv[1]
    print(f"[INFO] Replay 開始: {csv_path}")

    trades = run_replay(csv_path)
    if not trades:
        print("[WARN] トレードなし")
        return

    df     = pd.DataFrame(trades)
    df_raw = _load_csv(csv_path)
    days   = (df_raw["timestamp_ms"].max() - df_raw["timestamp_ms"].min()) / (1000 * 60 * 60 * 24)

    _print_summary(df, days)

    _RESULTS_DIR.mkdir(exist_ok=True)
    stem = pathlib.Path(csv_path).stem
    out  = _RESULTS_DIR / f"replay_v10_{stem}_regime.csv"
    df.to_csv(out, index=False)
    print(f"\n[OK] → {out}")


if __name__ == "__main__":
    main()
