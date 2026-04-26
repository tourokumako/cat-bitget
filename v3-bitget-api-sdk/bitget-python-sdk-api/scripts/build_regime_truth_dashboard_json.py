"""ダッシュボード「⑤ Ground Truth 検証」用JSON生成。

入力:
  data/regime_ground_truth_daily.csv（365日・機械ラベル）
  data/regime_ground_truth.csv（53週・肉眼判定・並走比較用）
  data/BTCUSDT-5m-2025-04-01_03-31_365d.csv（日足close系列）

出力:
  dashboard/data/regime_truth_daily.json
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
GT_DAILY_PATH = REPO_ROOT / "data" / "regime_ground_truth_daily.csv"
GT_DAILY_HUMAN_PATH = REPO_ROOT / "data" / "regime_ground_truth_daily_human.csv"
GT_WEEKLY_PATH = REPO_ROOT / "data" / "regime_ground_truth.csv"
CSV_5M_PATH = REPO_ROOT / "data" / "BTCUSDT-5m-2025-04-01_03-31_365d.csv"
OUT_PATH = REPO_ROOT / "dashboard" / "data" / "regime_truth_daily.json"


def _load_daily_close() -> pd.DataFrame:
    df = pd.read_csv(CSV_5M_PATH)
    df["ts"] = pd.to_datetime(df["timestamp"])
    for c in ("open", "high", "low", "close"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.set_index("ts").sort_index()
    return df.resample("D").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()


def main() -> None:
    daily_price = _load_daily_close()

    # 機械ラベル
    ml_rows = []
    with GT_DAILY_PATH.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            ml_rows.append(r)

    # 日付→価格 dict
    price_by_date = {idx.strftime("%Y-%m-%d"): {"o": float(r["open"]), "h": float(r["high"]),
                                                  "l": float(r["low"]), "c": float(r["close"])}
                     for idx, r in daily_price.iterrows()}

    days = []
    for r in ml_rows:
        date = r["date"]
        p = price_by_date.get(date)
        if not p:
            continue
        days.append({
            "date": date,
            "label": r["label"],
            "direction_score": r["direction_score"],
            "ichimoku": r["ichimoku"],
            "adx": r["adx"],
            "bb_width_pct": r["bb_width_pct"],
            "bb_median": r["bb_median"],
            "note": r["note"],
            "close": p["c"],
        })

    # 月別サマリ
    monthly = {}
    for d in days:
        m = d["date"][:7]
        if m not in monthly:
            monthly[m] = {"month": m, "uptrend": 0, "downtrend": 0, "range": 0, "warmup": 0, "total": 0}
        if d["label"] == "uptrend":
            monthly[m]["uptrend"] += 1
        elif d["label"] == "downtrend":
            monthly[m]["downtrend"] += 1
        elif d["label"] == "range":
            monthly[m]["range"] += 1
        else:
            monthly[m]["warmup"] += 1
        monthly[m]["total"] += 1

    # 肉眼ラベル（週単位）
    weekly = []
    if GT_WEEKLY_PATH.exists():
        with GT_WEEKLY_PATH.open(encoding="utf-8") as f:
            for r in csv.DictReader(f):
                weekly.append({
                    "week_start": r.get("week_start", ""),
                    "label": (r.get("label") or "").strip(),
                    "note": (r.get("note") or "").strip(),
                })

    # 機械ラベル全体分布
    label_counts = {"uptrend": 0, "downtrend": 0, "range": 0, "warmup": 0}
    for d in days:
        if d["label"] == "uptrend":
            label_counts["uptrend"] += 1
        elif d["label"] == "downtrend":
            label_counts["downtrend"] += 1
        elif d["label"] == "range":
            label_counts["range"] += 1
        else:
            label_counts["warmup"] += 1

    # 肉眼日次ラベル（初期値・上書きOK）
    human_daily: dict = {}
    if GT_DAILY_HUMAN_PATH.exists():
        with GT_DAILY_HUMAN_PATH.open(encoding="utf-8") as f:
            for r in csv.DictReader(f):
                d = (r.get("date") or "").strip()
                lab = (r.get("label") or "").strip()
                note = (r.get("note") or "").strip()
                if d:
                    human_daily[d] = {"label": lab, "note": note}

    out = {
        "n_days": len(days),
        "label_counts": label_counts,
        "days": days,
        "monthly_summary": list(monthly.values()),
        "weekly_human_labels": weekly,
        "daily_human_labels": human_daily,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[build_regime_truth_dashboard_json] {len(days)} days → {OUT_PATH}")
    print(f"  分布: {label_counts}")


if __name__ == "__main__":
    main()
