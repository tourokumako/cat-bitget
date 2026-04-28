"""build_regime_samples_4h_dashboard_json.py — 4h サンプルラベル UI 用 JSON ビルド

入力:
  - data/BTCUSDT-5m-2021-04-01_03-31_1826d.csv (5m OHLCV)
  - data/regime_samples_4h.csv (既存ラベル・無ければ空ラベル2190行で新規作成)

出力:
  - dashboard/data/regime_samples_4h.json
    {
      "bars":   [{"timestamp_utc": "...", "open": 93000, "close": 93500}, ...],
      "labels": {"2025-01-01T00:00:00Z": "uptrend", ...}
    }

期間: 2025-01-01T00:00:00Z 〜 2025-12-31T20:00:00Z（4h バー × 2190 個）
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT_CSV = REPO_ROOT / "data" / "BTCUSDT-5m-2021-04-01_03-31_1826d.csv"
LABELS_CSV = REPO_ROOT / "data" / "regime_samples_4h.csv"
OUT_JSON = REPO_ROOT / "dashboard" / "data" / "regime_samples_4h.json"

PERIOD_START = "2025-01-01T00:00:00Z"
PERIOD_END = "2026-01-01T00:00:00Z"
VALID_LABELS = {"", "downtrend", "range", "uptrend"}


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


def init_labels_csv(timestamps: list[str]) -> dict[str, str]:
    LABELS_CSV.parent.mkdir(parents=True, exist_ok=True)
    with LABELS_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["timestamp_utc", "label"])
        for ts in timestamps:
            w.writerow([ts, ""])
    print(f"[init] {LABELS_CSV.relative_to(REPO_ROOT)}  rows={len(timestamps):,} (empty labels)")
    return {ts: "" for ts in timestamps}


def load_labels_csv(timestamps: list[str]) -> dict[str, str]:
    if not LABELS_CSV.exists():
        return init_labels_csv(timestamps)
    out: dict[str, str] = {ts: "" for ts in timestamps}
    with LABELS_CSV.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            ts = row.get("timestamp_utc", "")
            lab = row.get("label", "") or ""
            if lab not in VALID_LABELS:
                raise ValueError(f"invalid label in CSV: {lab!r} at {ts}")
            if ts in out:
                out[ts] = lab
    print(f"[load] {LABELS_CSV.relative_to(REPO_ROOT)}  filled={sum(1 for v in out.values() if v):,}")
    return out


def main() -> None:
    print(f"[load] {INPUT_CSV.name}")
    df_4h = resample_4h(INPUT_CSV, PERIOD_START, PERIOD_END)
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
    labels = load_labels_csv(timestamps)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps({"bars": bars, "labels": labels}, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"[save] {OUT_JSON.relative_to(REPO_ROOT)}  bars={len(bars):,}  labeled={sum(1 for v in labels.values() if v):,}")
    print("[done]")


if __name__ == "__main__":
    main()
