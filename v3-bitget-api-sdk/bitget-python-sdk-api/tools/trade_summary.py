#!/usr/bin/env python3
"""
tools/trade_summary.py — V9 ログからバックテスト相当の取引集計レポートを生成する

使い方:
  python tools/trade_summary.py                          # デフォルト: logs/cron.log
  python tools/trade_summary.py logs/cron.log
  python tools/trade_summary.py logs/cron.log --since "2026-03-24"
  python tools/trade_summary.py logs/cron.log --since "2026-03-24T06:00"
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))

import pandas as pd

# ── 手数料レート（cat_params_v9.json に合わせる） ──────────────────────
MAKER_RATE = 0.00014
TAKER_RATE = 0.00042

# ── Exit 理由ラベル定義 ──────────────────────────────────────────────────
TP_EXIT_REASONS     = {"TP_FILLED", "TP_OR_SL_HIT"}
SL_EXIT_REASONS     = {"SL_FILLED"}
SHALLOW_EXIT_REASONS = {"PROFIT_LOCK", "MFE_EXIT"}


def _exit_label(exit_reason: str, gross_usd: float, exit_type: str) -> str:
    """Exit理由 → 表示用カテゴリラベル"""
    if exit_reason in TP_EXIT_REASONS:
        return "TP利確"
    if exit_reason in SL_EXIT_REASONS:
        return "SL損切"
    if exit_reason == "TIME_EXIT":
        return "TIME_EXIT"
    if exit_reason in SHALLOW_EXIT_REASONS or (gross_usd > 0 and exit_type == "active"):
        return "TP浅利確_EFF"
    return exit_reason  # STAGNATION_CUT / MAE_CUT / BREAKOUT_CUT / MFE_STALE_CUT など


# ── ログパーサー ─────────────────────────────────────────────────────────

def parse_trades(log_path: Path, since_ts: int = 0) -> list[dict]:
    """
    ログファイルを1行ずつ読み、ENTRY_CONFIRMED → EXIT の対を
    1トレードとして収集して返す。

    決済未確定（ENTRY後にEXIT_TRIGGEREDが来たがCLOSE_VERIFYがまだ）や
    集計期間外は除外する。
    """
    trades: list[dict] = []
    current: dict | None = None

    with open(log_path, encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                ev = json.loads(raw)
            except Exception:
                continue

            ts    = ev.get("ts", 0)
            event = ev.get("event")

            # since フィルタ（ts が付いているイベントのみ）
            if ts and ts < since_ts:
                continue

            # ── ENTRY_CONFIRMED: トレード開始 ────────────────────────
            if event == "ENTRY_CONFIRMED":
                current = {
                    "entry_ts":    ts,
                    "side":        ev["side"],
                    "priority":    ev.get("priority"),
                    "avg_price":   float(ev["price"]),
                    "size":        float(ev["size"]),
                    "tp_price":    float(ev.get("tp") or 0),
                    "add_count":   1,
                    "exit_type":   None,
                    "exit_reason": None,
                    "exit_ts":     None,
                    "hold_min":    None,
                    "unreal_usd":  None,
                    "exit_price":  None,
                }

            # ── ADD_CONFIRMED: avg_price / size / add_count 更新 ─────
            elif event == "ADD_CONFIRMED" and current is not None:
                current["avg_price"] = float(ev["avg_price"])
                current["size"]      = float(ev["size"])
                current["tp_price"]  = float(ev.get("tp") or current["tp_price"])
                current["add_count"] = int(ev["add_count"])

            # ── EXIT_TRIGGERED: active close の P&L 情報を記録 ────────
            elif event == "EXIT_TRIGGERED" and current is not None:
                current["exit_ts"]    = ts
                current["exit_reason"] = ev["reason"]
                current["hold_min"]   = float(ev.get("hold_min") or 0)
                current["unreal_usd"] = float(ev.get("unreal_usd") or 0)
                current["exit_price"] = float(ev.get("mark_price") or current["avg_price"])
                current["exit_type"]  = "active"

            # ── CLOSE_VERIFY(complete): active close 確定 ─────────────
            elif event == "CLOSE_VERIFY" and ev.get("status") == "complete" and current is not None:
                trades.append(_finalize(current))
                current = None

            # ── EXIT_EXTERNAL: TP/SL 自動約定 ────────────────────────
            elif event == "EXIT_EXTERNAL" and current is not None:
                reason = ev.get("reason", "EXTERNAL")
                mark   = float(ev.get("mark_price") or current["avg_price"])
                tp     = float(ev.get("tp") or current["tp_price"] or 0)
                sl     = float(ev.get("sl") or 0)

                if reason == "TP_FILLED" and tp:
                    exit_price = tp
                elif reason == "SL_FILLED" and sl:
                    exit_price = sl
                else:
                    exit_price = mark

                current["exit_ts"]    = ts
                current["exit_reason"] = reason
                current["exit_price"] = exit_price
                current["exit_type"]  = "external"
                current["hold_min"]   = (ts - current["entry_ts"]) / 60_000
                trades.append(_finalize(current))
                current = None

    return trades


def _finalize(t: dict) -> dict:
    """gross / fee / net を計算してトレード dict を確定する"""
    side       = t["side"]
    avg_price  = t["avg_price"]
    size       = t["size"]
    exit_type  = t["exit_type"]
    exit_price = t["exit_price"] or avg_price

    # Gross P&L
    if exit_type == "active":
        # EXIT_TRIGGERED の unreal_usd (mark_price ベース近似)
        gross = t["unreal_usd"] or 0.0
    else:
        if side == "LONG":
            gross = (exit_price - avg_price) * size
        else:
            gross = (avg_price - exit_price) * size

    # 手数料（ラウンドトリップ近似）
    # active close: entry=maker + close=taker
    # TP/SL 約定:   entry=maker + TP/SL=maker
    if exit_type == "active":
        fee = size * exit_price * (MAKER_RATE + TAKER_RATE)
    else:
        fee = size * exit_price * MAKER_RATE * 2

    gross_usd = round(gross, 4)
    fee_usd   = round(fee, 4)
    net_usd   = round(gross - fee, 4)

    t["gross_usd"]   = gross_usd
    t["fee_usd"]     = fee_usd
    t["net_usd"]     = net_usd
    t["exit_label"]  = _exit_label(t["exit_reason"], gross_usd, exit_type)
    t["pos_size_btc"] = round(size, 4)
    return t


# ── レポート出力 ─────────────────────────────────────────────────────────

def report(trades: list[dict]) -> None:
    if not trades:
        print("集計対象のトレードが 0 件です（まだ決済が発生していない可能性があります）")
        return

    df = pd.DataFrame(trades)

    gross_total = df["gross_usd"].sum()
    fee_total   = df["fee_usd"].sum()
    net_total   = df["net_usd"].sum()
    n           = len(df)
    wins        = (df["net_usd"] > 0).sum()

    tp_n   = (df["exit_label"] == "TP利確").sum()
    sl_n   = (df["exit_label"] == "SL損切").sum()
    shal_n = (df["exit_label"] == "TP浅利確_EFF").sum()
    time_n = (df["exit_label"] == "TIME_EXIT").sum()

    sep = "=" * 62

    # ── 損益サマリー ─────────────────────────────────────────────────
    print(sep)
    print("  V9 取引集計レポート")
    print(sep)
    print()
    print("【損益サマリー】")
    print(f"  合計利益 gross       : {gross_total:+.2f} USD")
    print(f"  手数料合計           : {fee_total:.4f} USD")
    print(f"  合計利益 net         : {net_total:+.2f} USD")
    print(f"  平均利益 net/trade   : {net_total / n:+.4f} USD")
    if gross_total:
        print(f"  手数料比率           : {fee_total / abs(gross_total) * 100:.1f}%")
    else:
        print("  手数料比率           : N/A（gross=0）")
    print(f"  平均手数料 fee/trade : {fee_total / n:.4f} USD")

    # ── トレード統計 ─────────────────────────────────────────────────
    print()
    print("【トレード統計】")
    print(f"  トレード数           : {n}")
    print(f"  TP数                 : {tp_n}")
    print(f"  SL数                 : {sl_n}")
    print(f"  浅利確数             : {shal_n}")
    print(f"  TIME_EXIT数          : {time_n}")
    print(f"  勝率（net>0）        : {wins / n * 100:.1f}%")
    print(f"  平均保持時間         : {df['hold_min'].mean():.1f} min")

    # ── Priority別 損益集計 ──────────────────────────────────────────
    print()
    print("【Priority別集計（gross / fee / net）】")
    pg = (
        df.groupby("priority")
        .agg(
            trades    =("net_usd", "count"),
            gross_usd =("gross_usd", "sum"),
            fee_usd   =("fee_usd", "sum"),
            net_usd   =("net_usd", "sum"),
            mean_net_usd=("net_usd", "mean"),
        )
        .round(4)
    )
    print(pg.to_string())

    # ── Priority別 Exit理由（件数） ──────────────────────────────────
    print()
    print("【Priority別 Exit理由（件数）】")
    ct = df.pivot_table(
        index="priority", columns="exit_label",
        values="net_usd", aggfunc="count", fill_value=0,
    )
    ct.columns.name = None
    print(ct.to_string())

    # ── Priority別 Exit理由（net損益合計） ──────────────────────────
    print()
    print("【Priority別 Exit理由（損益合計 USD：net）】")
    pn = df.pivot_table(
        index="priority", columns="exit_label",
        values="net_usd", aggfunc="sum", fill_value=0.0,
    )
    pn.columns.name = None
    print(pn.round(4).to_string())

    # ── pos_size_btc ごとの add 分布 ─────────────────────────────────
    print()
    print("【pos_size_btc ごとの add（回数 / net損益）】")
    ag = df.groupby("pos_size_btc").agg(
        cnt         =("add_count", "count"),
        add_cnt_sum =("add_count", "sum"),
        add_cnt_mean=("add_count", "mean"),
        net_sum     =("net_usd", "sum"),
        net_mean    =("net_usd", "mean"),
    ).round(4)
    print(ag.to_string())

    # ── Priority × ポジションサイズ × Exit理由 詳細 ────────────────────
    print()
    print("【Priority × ポジションサイズ × Exit理由（件数 / net_sum / avg_add）】")
    detail = (
        df.groupby(["priority", "pos_size_btc", "exit_label"])
        .agg(
            件数    =("net_usd", "count"),
            net_sum =("net_usd", "sum"),
            add_mean=("add_count", "mean"),
        )
        .round(4)
    )
    print(detail.to_string())

    # ── Exit理由別 損失集計 ────────────────────────────────────────────
    print()
    print("【Exit理由別集計（件数 / net損益）】")
    er = (
        df.groupby("exit_label")
        .agg(
            件数    =("net_usd", "count"),
            net_sum =("net_usd", "sum"),
            net_mean=("net_usd", "mean"),
        )
        .round(4)
        .sort_values("net_sum")
    )
    print(er.to_string())

    print()


# ── エントリーポイント ────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="V9 取引集計レポート")
    parser.add_argument(
        "log", nargs="?",
        default="logs/cron.log",
        help="ログファイルパス（デフォルト: logs/cron.log）",
    )
    parser.add_argument(
        "--since", default=None,
        help="集計開始日時 ISO形式 例: 2026-03-24 または 2026-03-24T06:00",
    )
    args = parser.parse_args()

    since_ts = 0
    if args.since:
        dt = datetime.fromisoformat(args.since)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=JST)
        since_ts = int(dt.timestamp() * 1000)

    log_path = Path(args.log)
    if not log_path.exists():
        print(f"ログファイルが見つかりません: {log_path}", file=sys.stderr)
        sys.exit(1)

    trades = parse_trades(log_path, since_ts)
    report(trades)


if __name__ == "__main__":
    main()