"""ダッシュボード ⑦ HMM特徴量分布タブ用 JSON 生成。

入力: results/phase1_features_daily.csv
出力: dashboard/data/phase1_features.json

内容:
  - period: 期間情報
  - features: 各特徴量の統計サマリ（mean/std/min/max/p5/p25/p50/p75/p95）
  - histograms: 各特徴量のヒストグラム（30 bin）
  - correlation: 相関行列（symmetric N×N）
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "results" / "phase1_features_daily.csv"
OUT_PATH = REPO_ROOT / "dashboard" / "data" / "phase1_features.json"

N_BINS = 30


def main() -> None:
    if not CSV_PATH.exists():
        raise SystemExit(f"CSV not found: {CSV_PATH}（先に phase1_features.py 実行）")

    df = pd.read_csv(CSV_PATH, parse_dates=["date"])
    df = df.set_index("date").sort_index()
    feat_cols = list(df.columns)
    n = len(df)

    print(f"[phase1-json] 入力: {n}行 × {len(feat_cols)}列")

    features = {}
    histograms = {}
    for col in feat_cols:
        s = df[col].dropna()
        features[col] = {
            "mean": float(s.mean()),
            "std": float(s.std()),
            "min": float(s.min()),
            "max": float(s.max()),
            "p5": float(s.quantile(0.05)),
            "p25": float(s.quantile(0.25)),
            "p50": float(s.quantile(0.50)),
            "p75": float(s.quantile(0.75)),
            "p95": float(s.quantile(0.95)),
        }
        counts, edges = np.histogram(s.values, bins=N_BINS)
        histograms[col] = {
            "bin_edges": [float(x) for x in edges],
            "counts": [int(c) for c in counts],
        }

    corr = df[feat_cols].corr().round(3)
    correlation = {
        "features": feat_cols,
        "matrix": [[float(v) for v in row] for row in corr.values],
    }

    out = {
        "period": {
            "start": df.index.min().strftime("%Y-%m-%d"),
            "end": df.index.max().strftime("%Y-%m-%d"),
            "n_days": n,
        },
        "feature_count": len(feat_cols),
        "features": features,
        "histograms": histograms,
        "correlation": correlation,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"→ {OUT_PATH}")


if __name__ == "__main__":
    main()
