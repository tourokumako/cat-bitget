"""build_regime_samples_4h_dashboard_json.py — 4h サンプルラベル UI 用 JSON ビルド

入力:
  - data/BTCUSDT-5m-2021-04-01_03-31_1826d.csv (5m OHLCV)
  - data/regime_samples_4h.csv          (2025年・既存ラベル、無ければ空ラベルで新規作成)
  - data/regime_samples_4h_{year}.csv   (他の年、無ければ空ラベルで新規作成)

出力:
  - dashboard/data/regime_samples_4h.json          (2025年・後方互換)
  - dashboard/data/regime_samples_4h_{year}.json   (他の年)

使い方:
  python3 scripts/build_regime_samples_4h_dashboard_json.py           # 2025年（既定）
  python3 scripts/build_regime_samples_4h_dashboard_json.py --year 2023
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_CSV = REPO_ROOT / "data" / "BTCUSDT-5m-2021-04-01_03-31_1826d.csv"
VALID_LABELS = {"", "downtrend", "range", "uptrend"}


def labels_csv_path(year: int) -> Path:
    if year == 2025:
        return REPO_ROOT / "data" / "regime_samples_4h.csv"
    return REPO_ROOT / "data" / f"regime_samples_4h_{year}.csv"


def out_json_path(year: int) -> Path:
    if year == 2025:
        return REPO_ROOT / "dashboard" / "data" / "regime_samples_4h.json"
    return REPO_ROOT / "dashboard" / "data" / f"regime_samples_4h_{year}.json"


def resample_4h(path: Path, start: str, end: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["dt"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.set_index("dt").sort_index()
    df = df.loc[start:end]
    df_4h = df.resample("4h", label="left", closed="left").agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
    }).dropna()
    end_ts = pd.Timestamp(end)
    df_4h = df_4h[df_4h.index < end_ts]
    return df_4h


def init_labels_csv(labels_csv: Path, timestamps: list[str]) -> dict[str, str]:
    labels_csv.parent.mkdir(parents=True, exist_ok=True)
    with labels_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["timestamp_utc", "label"])
        for ts in timestamps:
            w.writerow([ts, ""])
    print(f"[init] {labels_csv.relative_to(REPO_ROOT)}  rows={len(timestamps):,} (empty labels)")
    return {ts: "" for ts in timestamps}


def load_labels_csv(labels_csv: Path, timestamps: list[str]) -> dict[str, str]:
    if not labels_csv.exists():
        return init_labels_csv(labels_csv, timestamps)
    out: dict[str, str] = {ts: "" for ts in timestamps}
    with labels_csv.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            ts = row.get("timestamp_utc", "")
            lab = row.get("label", "") or ""
            if lab not in VALID_LABELS:
                raise ValueError(f"invalid label in CSV: {lab!r} at {ts}")
            if ts in out:
                out[ts] = lab
    print(f"[load] {labels_csv.relative_to(REPO_ROOT)}  filled={sum(1 for v in out.values() if v):,}")
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2025, choices=range(2022, 2027),
                        metavar="YEAR", help="対象年（2022〜2026）")
    args = parser.parse_args()
    year = args.year

    period_start = f"{year}-01-01T00:00:00Z"
    period_end = f"{year + 1}-01-01T00:00:00Z"

    labels_csv = labels_csv_path(year)
    out_json = out_json_path(year)

    print(f"[load] {INPUT_CSV.name}  year={year}")
    df_4h = resample_4h(INPUT_CSV, period_start, period_end)
    print(f"[resample] 4h bars rows={len(df_4h):,}  {df_4h.index[0]} 〜 {df_4h.index[-1]}")

    timestamps = [ts.strftime("%Y-%m-%dT%H:%M:%SZ") for ts in df_4h.index]
    bars = [
        {
            "timestamp_utc": ts,
            "open": int(round(o)),
            "close": int(round(c)),
        }
        for ts, o, c in zip(timestamps, df_4h["open"].to_numpy(), df_4h["close"].to_numpy())
    ]
    labels = load_labels_csv(labels_csv, timestamps)

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(
        json.dumps({"bars": bars, "labels": labels}, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"[save] {out_json.relative_to(REPO_ROOT)}  bars={len(bars):,}  labeled={sum(1 for v in labels.values() if v):,}")
    print("[done]")


if __name__ == "__main__":
    main()
