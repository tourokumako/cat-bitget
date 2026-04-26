"""
build_dashboard_json.py — dashboard/data/*.json を自動生成

入力:
    results/replay_summary_<dataset>.json   (regime_days・サマリの正本)
    results/replay_<dataset>.csv            (trade 詳細)
    .claude/memory/signal_ledger.md         (シグナルマッピング §2)

設計方針:
    - regime_days は summary.json から取得（OHLCV 由来の正確値）
    - trade 集計は CSV から（per-trade 詳細はサマリに無いため）
    - summary.json が無い場合のみ CSV unique-date で近似（警告を出す）
    → 「手動でハードコードした値」は持たない。Replay 実行時に summary.json が生成され、
       build はそれを読むだけで再現性確保。

Replay 側で summary.json を生成するコマンド:
    python3 runner/replay_csv.py data/<ohlcv>.csv --regime \\
        --out-summary-json results/replay_summary_<dataset>.json
    python3 runner/replay_csv.py --summary results/replay_<dataset>.csv \\
        --out-summary-json results/replay_summary_<dataset>.json

使い方:
    python3 scripts/build_dashboard_json.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
DATASET = "BTCUSDT-5m-2025-04-01_03-31_365d"
REPLAY_CSV = REPO / "results" / f"replay_{DATASET}.csv"
SUMMARY_JSON = REPO / "results" / f"replay_summary_{DATASET}.json"
OHLCV_CSV = REPO / "data" / f"{DATASET}.csv"
LEDGER_MD = REPO / ".claude" / "memory" / "signal_ledger.md"
OUT_DIR = REPO / "dashboard" / "data"

GOAL_PER_DAY = 60.0
PRICE_RESAMPLE = "30min"   # OHLCV を価格チャート用にダウンサンプリング


def _load_summary_or_warn() -> dict | None:
    if not SUMMARY_JSON.exists():
        print(
            f"[build_dashboard_json] WARNING: {SUMMARY_JSON.name} not found.\n"
            f"  → regime_days を CSV unique-date で近似します（不正確）。\n"
            f"  → 正確な値にするには Replay を以下で再実行してください:\n"
            f"     python3 runner/replay_csv.py --summary {REPLAY_CSV.name} \\\n"
            f"         --out-summary-json {SUMMARY_JSON.name}\n",
            file=sys.stderr,
        )
        return None
    return json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))


def build_progress() -> dict:
    df = pd.read_csv(REPLAY_CSV)
    summary = _load_summary_or_warn()

    if summary:
        regime_days = summary["regime_days"]
        n_days = summary["n_days"]
        source = summary.get("source_csv", REPLAY_CSV.name)
        regime_days_source = "summary.json"
    else:
        df["_date"] = df["entry_time"].astype(str).str[:10]
        regime_days = {
            str(rg): int(df[df["regime"] == rg]["_date"].nunique())
            for rg in df["regime"].dropna().unique()
            if rg
        }
        n_days = int(df["_date"].nunique())
        source = REPLAY_CSV.name
        regime_days_source = "csv-unique-date (近似)"

    by_regime = df.groupby("regime")["net_usd"].sum().to_dict()
    by_priority = (
        df.groupby(["priority", "regime"])
        .agg(net=("net_usd", "sum"), trades=("net_usd", "size"))
        .reset_index()
    )

    regime_summary = []
    for regime, days in sorted(regime_days.items()):
        net = float(by_regime.get(regime, 0.0))
        per_rg = net / days if days else 0.0
        per_total = net / n_days if n_days else 0.0
        regime_summary.append(
            {
                "regime": regime,
                "days": int(days),
                "net_usd": round(net, 2),
                "per_regime_day": round(per_rg, 2),
                "per_total_day": round(per_total, 2),
            }
        )

    priority_rows = []
    for _, row in by_priority.iterrows():
        regime = row["regime"]
        days = regime_days.get(regime, 0)
        per_day = row["net"] / days if days else 0.0
        priority_rows.append(
            {
                "priority": int(row["priority"]),
                "regime": regime,
                "trades": int(row["trades"]),
                "net_usd": round(float(row["net"]), 2),
                "per_regime_day": round(per_day, 2),
            }
        )

    total_net = float(df["net_usd"].sum())
    per_total_day = total_net / n_days if n_days else 0.0

    return {
        "source_csv": source,
        "regime_days_source": regime_days_source,
        "period_days": int(n_days),
        "goal_per_day": GOAL_PER_DAY,
        "current_per_day": round(per_total_day, 2),
        "gap_per_day": round(GOAL_PER_DAY - per_total_day, 2),
        "total_net_usd": round(total_net, 2),
        "trade_count": int(len(df)),
        "regimes": regime_summary,
        "priorities": priority_rows,
    }


def parse_mapping_table(text: str) -> list[dict]:
    """signal_ledger.md §2 のマッピング表を抽出する。"""
    start = text.find("## §2")
    if start < 0:
        return []
    section = text[start : text.find("\n## §3", start) if "\n## §3" in text else len(text)]
    rows = []
    header_seen = False
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not cells or len(cells) < 8:
            continue
        if cells[0].startswith("---") or set(cells[0]) <= {":", "-"}:
            continue
        if cells[0] == "ID":
            header_seen = True
            continue
        if not header_seen:
            continue
        if not re.match(r"^[A-H]\d+$", cells[0]):
            continue
        rows.append(
            {
                "id": cells[0],
                "name": cells[1],
                "dt_long": cells[2],
                "dt_short": cells[3],
                "rg_long": cells[4],
                "rg_short": cells[5],
                "up_long": cells[6],
                "up_short": cells[7],
                "memo": cells[8] if len(cells) > 8 else "",
            }
        )
    return rows


def build_signals() -> dict:
    text = LEDGER_MD.read_text(encoding="utf-8")
    return {
        "source": LEDGER_MD.name,
        "legend": [
            {"symbol": "◎", "label": "本命候補（未検証）", "css": "mark-bull"},
            {"symbol": "○", "label": "補助候補（未検証）", "css": "mark-aux"},
            {"symbol": "△", "label": "条件次第", "css": "mark-cond"},
            {"symbol": "×", "label": "不適", "css": "mark-na"},
            {"symbol": "?", "label": "未評価", "css": "mark-tbd"},
            {"symbol": "✅", "label": "稼働中", "css": "mark-live"},
            {"symbol": "❌", "label": "検証済 NO-GO", "css": "mark-nogo"},
            {"symbol": "⚠", "label": "WARN", "css": "mark-warn"},
        ],
        "rows": parse_mapping_table(text),
    }


def build_fires() -> dict:
    df = pd.read_csv(REPLAY_CSV)
    df["entry_time"] = pd.to_datetime(df["entry_time"])
    df["exit_time"] = pd.to_datetime(df["exit_time"])
    cols = [
        "entry_time", "exit_time", "side", "priority", "regime",
        "entry_price", "exit_price",
        "exit_reason", "hold_min", "net_usd", "mfe_usd", "mae_usd",
    ]
    fires = df[cols].copy()
    fires["entry_time"] = fires["entry_time"].dt.strftime("%Y-%m-%d %H:%M")
    fires["exit_time"] = fires["exit_time"].dt.strftime("%Y-%m-%d %H:%M")
    fires["priority"] = fires["priority"].astype(int)
    return {
        "source_csv": REPLAY_CSV.name,
        "trade_count": len(fires),
        "trades": fires.to_dict(orient="records"),
    }


def build_prices() -> dict:
    """OHLCV を 30分足にダウンサンプリングして価格ライン用 JSON を作る。"""
    df = pd.read_csv(OHLCV_CSV)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.set_index("timestamp").sort_index()
    resampled = df[["close"]].resample(PRICE_RESAMPLE).last().dropna().reset_index()
    return {
        "source_csv": OHLCV_CSV.name,
        "resample": PRICE_RESAMPLE,
        "bars": [
            {"t": r.timestamp.strftime("%Y-%m-%d %H:%M"), "c": round(float(r.close), 2)}
            for r in resampled.itertuples()
        ],
    }


def build_regime_timeline() -> dict:
    """replay_csv._build_regime_map（日足版・現行採用）を呼び出して日次 regime を取得する。

    Phase 2 hourly+hys36h は採用条件未達でロールバック (2026-04-25)。
    """
    sys.path.insert(0, str(REPO))
    try:
        from runner.replay_csv import _build_regime_map  # type: ignore
    except Exception as e:
        print(f"[build] regime_timeline: import failed ({e})", file=sys.stderr)
        return {"source": "fallback", "days": []}

    rmap = _build_regime_map(str(OHLCV_CSV))
    days = sorted(rmap.items(), key=lambda kv: kv[0])
    return {
        "source": OHLCV_CSV.name,
        "method": "daily MA70+slope+ADX (current production)",
        "days": [{"date": ts.strftime("%Y-%m-%d"), "regime": rg} for ts, rg in days],
    }


def main() -> None:
    if not REPLAY_CSV.exists():
        raise FileNotFoundError(f"Replay CSV not found: {REPLAY_CSV}")
    if not LEDGER_MD.exists():
        raise FileNotFoundError(f"signal_ledger.md not found: {LEDGER_MD}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    progress = build_progress()
    signals = build_signals()
    fires = build_fires()
    prices = build_prices() if OHLCV_CSV.exists() else {"bars": []}
    timeline = build_regime_timeline() if OHLCV_CSV.exists() else {"days": []}

    (OUT_DIR / "progress.json").write_text(
        json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT_DIR / "signals.json").write_text(
        json.dumps(signals, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT_DIR / "fires.json").write_text(
        json.dumps(fires, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT_DIR / "prices.json").write_text(
        json.dumps(prices, ensure_ascii=False), encoding="utf-8"
    )
    (OUT_DIR / "regime_timeline.json").write_text(
        json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(
        f"progress.json: total={progress['current_per_day']}/day "
        f"gap={progress['gap_per_day']} "
        f"trades={progress['trade_count']} "
        f"regime_days_source={progress['regime_days_source']}"
    )
    print(f"signals.json: {len(signals['rows'])} rows")
    print(f"fires.json: {fires['trade_count']} trades")
    print(f"prices.json: {len(prices.get('bars', []))} bars ({PRICE_RESAMPLE})")
    print(f"regime_timeline.json: {len(timeline.get('days', []))} days")


if __name__ == "__main__":
    main()
