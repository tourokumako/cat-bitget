"""stage3_pattern_label_to_regime.py — 段階3-2 Replay 入力用 regime label csv 生成

設計原則 (2026-05-10 確定):
  - 入力: stage3_monthly_comparison.csv (latch なし vote3 pattern_label)
  - マッピング: pattern → regime_str (移行先採用)
    up->dn → downtrend / dn->up → uptrend / up->rg → range
    rg->up → uptrend / rg->dn → downtrend / dn->rg → range / none → unknown
  - 集約方式: 日内多数決 (5m 単位 → 日次・unknown 除外多数決)
  - 出力: regime_label_daily.csv (timestamp daily / regime カラム)
  - replay_csv.py --regime-csv=path で読み込み可能な形式

実行: python3 stage3_pattern_label_to_regime.py
出力: results/regime_label_analysis/regime_label_daily.csv
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import pandas as pd
from collections import Counter

BASE = Path(__file__).parent.parent.parent
INPUT_CSV = BASE / "results/regime_label_analysis/stage3_monthly_comparison.csv"
OUT_CSV = BASE / "results/regime_label_analysis/regime_label_daily.csv"

# pattern → regime_str (移行先採用)
PATTERN_TO_REGIME = {
    "up->dn": "downtrend",
    "dn->up": "uptrend",
    "up->rg": "range",
    "rg->up": "uptrend",
    "rg->dn": "downtrend",
    "dn->rg": "range",
    "none": "unknown",
}

# 入力 csv のどの列を使うか (latch なし vote3)
VOTE_COLUMN = "vote3_judge"


def main():
    print(f"入力ロード: {INPUT_CSV}", flush=True)
    df = pd.read_csv(INPUT_CSV, parse_dates=["timestamp"])
    print(f"  行数: {len(df):,} / カラム: {list(df.columns)}", flush=True)

    if VOTE_COLUMN not in df.columns:
        raise SystemExit(f"カラム '{VOTE_COLUMN}' が入力 csv にない")

    print(f"5m → regime_str マッピング ({VOTE_COLUMN})...", flush=True)
    df["regime_5m"] = df[VOTE_COLUMN].map(PATTERN_TO_REGIME).fillna("unknown")

    print("日次多数決集約 (unknown 除外)...", flush=True)
    df["date"] = df["timestamp"].dt.date
    daily_regime = []
    for date, grp in df.groupby("date"):
        counter = Counter(grp["regime_5m"].tolist())
        non_unknown = {k: v for k, v in counter.items() if k != "unknown"}
        if non_unknown:
            top_regime = max(non_unknown.items(), key=lambda x: x[1])[0]
        else:
            top_regime = "unknown"
        daily_regime.append({"timestamp": pd.Timestamp(date), "regime": top_regime})

    out_df = pd.DataFrame(daily_regime)
    print(f"日次行数: {len(out_df):,}", flush=True)
    print(f"regime 分布: {out_df['regime'].value_counts().to_dict()}", flush=True)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT_CSV, index=False)
    print(f"出力: {OUT_CSV}", flush=True)
    print("DONE")


if __name__ == "__main__":
    main()
