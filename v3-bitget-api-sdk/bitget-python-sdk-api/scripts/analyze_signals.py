"""
analyze_signals.py — 共通シグナル検証エンジン

目的:
    N6〜N18 の候補シグナルを1スクリプトで効率検証する。
    L-118 対応として、既存Priority占有との重複（干渉率）を計算し、
    raw NET を discount した「調整後NET」で採用判定する。

使い方:
    python3 scripts/analyze_signals.py \\
        --signal n6_adx50 \\
        --ohlcv data/BTCUSDT-5m-2025-04-01_03-31_365d.csv \\
        --replay results/replay_BTCUSDT-5m-2025-04-01_03-31_365d.csv \\
        --side SHORT --tp 0.010 --sl 0.020 --hold-min 120 \\
        --dt-days 143 --discount 0.3

シグナル定義:
    scripts/signals/{name}.py に detect(df) -> DataFrame を実装
    （詳細は scripts/signals/_base.py）

採用判定:
    GO   : 調整後NET ≥ $3/dt-day かつ 干渉率 < 0.3
    WARN : 調整後NET ≥ $1/dt-day または 干渉率 0.3〜0.5
    NO-GO: 上記以外

出力:
    - 標準出力: サマリ表
    - .claude/memory/signal_ledger.md に1行追記
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
SIGNAL_LEDGER = REPO_ROOT / ".claude" / "memory" / "signal_ledger.md"
EXISTING_PRIORITIES = (2, 21, 23)  # 既存稼働 Priority（L-118 干渉源）
POSITION_SIZE_BTC = 0.024          # 仮想 backtest 用
FEE_RATE = 0.0002                  # maker 片側
REGIME_CHOICES = ("all", "downtrend", "range", "uptrend", "mixed")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def load_ohlcv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    ts_col = next((c for c in ("timestamp", "time", "datetime") if c in df.columns), None)
    if ts_col is None:
        raise ValueError(f"timestamp column not found in {path}")
    df["timestamp"] = pd.to_datetime(df[ts_col])
    df = df.sort_values("timestamp").reset_index(drop=True)
    for col in ("open", "high", "low", "close", "volume"):
        if col not in df.columns:
            raise ValueError(f"{col} column not found in {path}")
    return df


def load_signal(name: str):
    module = importlib.import_module(f"signals.{name}")
    if not hasattr(module, "detect"):
        raise ValueError(f"signals.{name} has no detect() function")
    return module.detect


def simulate_fires(
    df: pd.DataFrame,
    fires: pd.DataFrame,
    tp: float,
    sl: float,
    hold_min: int,
) -> pd.DataFrame:
    """固定 TP/SL/HOLD の単独 backtest（既存Priority占有は考慮しない raw 計算）"""
    bars_per_hold = hold_min // 5
    df_idx = df.set_index("timestamp")
    results = []
    for _, row in fires.iterrows():
        entry_time = pd.Timestamp(row["entry_time"])
        side = row["side"]
        entry_price = float(row["entry_price"])
        if entry_time not in df_idx.index:
            continue
        start_i = df_idx.index.get_loc(entry_time)
        end_i = min(start_i + bars_per_hold, len(df) - 1)
        future = df.iloc[start_i + 1 : end_i + 1]
        if future.empty:
            continue

        if side == "LONG":
            tp_price = entry_price * (1 + tp)
            sl_price = entry_price * (1 - sl)
            hit_tp = future[future["high"] >= tp_price]
            hit_sl = future[future["low"] <= sl_price]
        else:
            tp_price = entry_price * (1 - tp)
            sl_price = entry_price * (1 + sl)
            hit_tp = future[future["low"] <= tp_price]
            hit_sl = future[future["high"] >= sl_price]

        tp_i = hit_tp.index[0] if not hit_tp.empty else None
        sl_i = hit_sl.index[0] if not hit_sl.empty else None
        if tp_i is not None and (sl_i is None or tp_i < sl_i):
            exit_time = future.loc[tp_i, "timestamp"]
            exit_price = tp_price
            reason = "TP"
        elif sl_i is not None:
            exit_time = future.loc[sl_i, "timestamp"]
            exit_price = sl_price
            reason = "SL"
        else:
            exit_time = future.iloc[-1]["timestamp"]
            exit_price = float(future.iloc[-1]["close"])
            reason = "TIME"

        gross = POSITION_SIZE_BTC * (
            exit_price - entry_price if side == "LONG" else entry_price - exit_price
        )
        fee = POSITION_SIZE_BTC * ((entry_price + exit_price) * FEE_RATE)
        net = gross - fee
        hold = (exit_time - entry_time).total_seconds() / 60.0
        results.append(
            {
                "entry_time": entry_time,
                "exit_time": exit_time,
                "side": side,
                "exit_reason": reason,
                "hold_min": hold,
                "net_usd": net,
            }
        )
    return pd.DataFrame(results)


def compute_interference(
    trades: pd.DataFrame,
    replay_path: Path,
    priorities=EXISTING_PRIORITIES,
) -> float:
    """
    既存Priority が占有中の時刻に fire が落ちた割合（スロット干渉率）。
    0.0 = 一切衝突しない / 1.0 = 全件衝突
    """
    if trades.empty:
        return 0.0
    rep = pd.read_csv(replay_path)
    rep["entry_time"] = pd.to_datetime(rep["entry_time"])
    rep["exit_time"] = pd.to_datetime(rep["exit_time"])
    rep = rep[rep["priority"].isin(priorities)].copy()
    if rep.empty:
        return 0.0

    intervals = list(zip(rep["entry_time"].tolist(), rep["exit_time"].tolist()))
    intervals.sort()

    hit = 0
    for fire_ts in trades["entry_time"]:
        for start, end in intervals:
            if start > fire_ts:
                break
            if start <= fire_ts <= end:
                hit += 1
                break
    return hit / len(trades)


def judge(adj_net_per_day: float, interference: float) -> str:
    if adj_net_per_day >= 3.0 and interference < 0.3:
        return "GO"
    if adj_net_per_day >= 1.0 or 0.3 <= interference <= 0.5:
        return "WARN"
    return "NO-GO"


def append_ledger(row: dict) -> None:
    if not SIGNAL_LEDGER.exists():
        return
    text = SIGNAL_LEDGER.read_text()
    cols = [
        "date", "signal", "ohlcv", "replay_csv", "regime", "side", "tp_sl_hold",
        "fires_per_day", "avg_hold", "interference",
        "raw_net", "discount", "adj_net", "verdict", "memo",
    ]
    line = "| " + " | ".join(str(row.get(c, "")) for c in cols) + " |\n"
    SIGNAL_LEDGER.write_text(text.rstrip() + "\n" + line)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--signal", required=True, help="signals/{name}.py の name")
    ap.add_argument("--ohlcv", required=True, type=Path)
    ap.add_argument("--replay", required=True, type=Path)
    ap.add_argument("--side", choices=("LONG", "SHORT"), default=None,
                    help="detect 側で side を返す場合は省略可（フィルタ用）")
    ap.add_argument("--tp", type=float, required=True)
    ap.add_argument("--sl", type=float, required=True)
    ap.add_argument("--hold-min", type=int, required=True)
    ap.add_argument("--dt-days", type=float, default=None,
                    help="対象レジーム日数。--regime 指定時は自動計算可（省略推奨）")
    ap.add_argument("--regime", choices=REGIME_CHOICES, default="all",
                    help="レジーム限定（default=all・フィルタなし）")
    ap.add_argument("--discount", type=float, default=0.3,
                    help="L-118 干渉ディスカウント係数（default=0.3・安全側）")
    ap.add_argument("--memo", default="")
    args = ap.parse_args()

    sys.path.insert(0, str(Path(__file__).resolve().parent))

    df = load_ohlcv(args.ohlcv)
    detect = load_signal(args.signal)
    fires = detect(df)
    if fires.empty:
        print(f"[{args.signal}] no fires detected")
        return 0
    if args.side:
        fires = fires[fires["side"] == args.side].copy()

    regime_map = None
    regime_days = args.dt_days
    if args.regime != "all":
        from runner.replay_csv import _build_regime_map
        regime_map = _build_regime_map(str(args.ohlcv))
        target_dates = {d for d, r in regime_map.items() if r == args.regime}
        if not target_dates:
            print(f"[{args.signal}] regime={args.regime} の対象日なし")
            return 0
        fires["entry_time"] = pd.to_datetime(fires["entry_time"])
        fires_date = fires["entry_time"].dt.normalize()
        fires = fires[fires_date.isin(target_dates)].copy()
        if regime_days is None:
            regime_days = float(len(target_dates))
    if regime_days is None:
        dates = pd.to_datetime(fires["entry_time"]).dt.normalize().unique()
        regime_days = float(len(dates)) if len(dates) else 1.0

    fires = fires.reset_index(drop=True)

    trades = simulate_fires(df, fires, args.tp, args.sl, args.hold_min)
    if trades.empty:
        print(f"[{args.signal}] no simulated trades")
        return 0

    raw_net = trades["net_usd"].sum()
    raw_per_day = raw_net / regime_days
    avg_hold = trades["hold_min"].mean()
    fires_per_day = len(trades) / regime_days

    interference = compute_interference(trades, args.replay)
    adj_per_day = raw_per_day * (1.0 - interference * args.discount)
    verdict = judge(adj_per_day, interference)

    print("=" * 60)
    print(f" signal         : {args.signal}")
    print(f" ohlcv          : {args.ohlcv.name}")
    print(f" replay         : {args.replay.name}")
    print(f" regime         : {args.regime}  (days={regime_days:.0f})")
    print(f" tp/sl/hold     : {args.tp} / {args.sl} / {args.hold_min}min")
    print(f" fires/reg-day  : {fires_per_day:.2f}  (total {len(trades)})")
    print(f" avgHold        : {avg_hold:.1f} min")
    print(f" interference   : {interference:.3f}")
    print(f" raw  $/reg-day : {raw_per_day:+.2f}")
    print(f" discount       : {args.discount}")
    print(f" adj  $/reg-day : {adj_per_day:+.2f}")
    print(f" 判定            : {verdict}")
    print("=" * 60)

    append_ledger(
        {
            "date": dt.date.today().isoformat(),
            "signal": args.signal,
            "ohlcv": args.ohlcv.name,
            "replay_csv": args.replay.name,
            "regime": args.regime,
            "side": args.side or "auto",
            "tp_sl_hold": f"{args.tp}/{args.sl}/{args.hold_min}",
            "fires_per_day": f"{fires_per_day:.2f}",
            "avg_hold": f"{avg_hold:.1f}",
            "interference": f"{interference:.3f}",
            "raw_net": f"{raw_per_day:+.2f}",
            "discount": args.discount,
            "adj_net": f"{adj_per_day:+.2f}",
            "verdict": verdict,
            "memo": args.memo,
        }
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
