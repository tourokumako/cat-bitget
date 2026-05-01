"""ダッシュボード「⑤ Ground Truth 検証」用JSON生成。

入力:
  data/regime_ground_truth_daily.csv（365日・機械ラベル・並走比較用）
  data/regime_ground_truth.csv（53週・肉眼判定・並走比較用）
  data/BTCUSDT-5m-2020-01-01_2024-12-31_5y.csv（2021-04-01〜2024-12-31）
  data/BTCUSDT-1d-2024-09-01_04-15_227d.csv （2025-01-01〜2025-03-31 ギャップ埋め）
  data/BTCUSDT-5m-2025-04-01_03-31_365d.csv  （2025-04-01〜2026-03-31）

出力:
  dashboard/data/regime_truth_daily.json（1826日・5年分）
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
GT_DAILY_PATH = REPO_ROOT / "data" / "regime_ground_truth_daily.csv"
GT_DAILY_HUMAN_PATH = REPO_ROOT / "data" / "regime_ground_truth_daily_human.csv"
GT_WEEKLY_PATH = REPO_ROOT / "data" / "regime_ground_truth.csv"
CSV_5M_5Y_PATH   = REPO_ROOT / "data" / "BTCUSDT-5m-2020-01-01_2024-12-31_5y.csv"
CSV_1D_GAP_PATH  = REPO_ROOT / "data" / "BTCUSDT-1d-2024-09-01_04-15_227d.csv"
CSV_5M_365D_PATH = REPO_ROOT / "data" / "BTCUSDT-5m-2025-04-01_03-31_365d.csv"
DATE_START = "2021-04-01"
DATE_END   = "2026-03-31"
OUT_PATH = REPO_ROOT / "dashboard" / "data" / "regime_truth_daily.json"


def _load_5m_daily(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["ts"] = pd.to_datetime(df["timestamp"])
    for c in ("open", "high", "low", "close"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.set_index("ts").sort_index()
    return df.resample("D").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()


def _load_1d(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["ts"] = pd.to_datetime(df["timestamp"]).dt.normalize()
    for c in ("open", "high", "low", "close"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.set_index("ts")[["open", "high", "low", "close"]].sort_index()


def _load_daily_close() -> pd.DataFrame:
    parts = [
        _load_5m_daily(CSV_5M_5Y_PATH),
        _load_1d(CSV_1D_GAP_PATH),
        _load_5m_daily(CSV_5M_365D_PATH),
    ]
    combined = pd.concat(parts).sort_index()
    combined = combined[~combined.index.duplicated(keep="last")]
    return combined.loc[DATE_START:DATE_END]


def main() -> None:
    daily_price = _load_daily_close()

    # 機械ラベル（365日のみ・lookup dictへ）
    ml_by_date: dict = {}
    with GT_DAILY_PATH.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            ml_by_date[r["date"]] = r

    # 1826日（価格ベースで反復・機械ラベル無い日は空文字）
    days = []
    for ts, row in daily_price.iterrows():
        date = ts.strftime("%Y-%m-%d")
        ml = ml_by_date.get(date)
        if ml:
            days.append({
                "date": date, "label": ml["label"],
                "direction_score": ml["direction_score"], "ichimoku": ml["ichimoku"],
                "adx": ml["adx"], "bb_width_pct": ml["bb_width_pct"],
                "bb_median": ml["bb_median"], "note": ml["note"],
                "close": float(row["close"]),
            })
        else:
            days.append({
                "date": date, "label": "",
                "direction_score": "", "ichimoku": "",
                "adx": "", "bb_width_pct": "",
                "bb_median": "", "note": "",
                "close": float(row["close"]),
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
