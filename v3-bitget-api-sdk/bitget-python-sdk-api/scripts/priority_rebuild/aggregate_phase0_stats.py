"""Phase 0 v3 完了報告用 統計集計スクリプト

3 parquet (train_2021_2024 / test_2025 / test_2026_q1) の以下を集計し
results/priority_rebuild/phase0_v3_stats/ に出力する:

- row_count_verify.json : 期間別行数 + 期待値との差分
- label_stats.csv       : 28 ラベル統計 (mean/std/min/max) per period × K × side × MFE/MAE
- sample_rows_K{K}.csv  : 各 K の先頭 5 行サンプル (ラベル列のみ)

注記: maintenance_flag 集計は 2026-05-22 削除済 (L-196 整合・Bitget 24/7 取引)。
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[2]
PARQ_DIR = BASE / "results" / "priority_rebuild"
OUT_DIR = PARQ_DIR / "phase0_v3_stats"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PERIODS = {
    "train_2021_2024": PARQ_DIR / "labels_mfe_mae_pct_train_2021_2024.parquet",
    "test_2025": PARQ_DIR / "labels_mfe_mae_pct_test_2025.parquet",
    "test_2026_q1": PARQ_DIR / "labels_mfe_mae_pct_test_2026_q1.parquet",
}

K_BARS = [6, 12, 24, 48, 96, 144, 288]
SIDES = ["LONG", "SHORT"]
KINDS = ["MFE", "MAE"]

EXPECTED_ROWS = {
    "train_2021_2024": 394465,
    "test_2025": 104832,
    "test_2026_q1": 25535,
}


def label_cols() -> list[str]:
    cols = []
    for side in SIDES:
        for kind in KINDS:
            for k in K_BARS:
                cols.append(f"{side}_{kind}_pct_K{k}")
    return cols


def main() -> None:
    print(f"[start] {pd.Timestamp.now()}")
    row_verify = {}
    stats_rows = []

    cols_needed = label_cols()  # is_maintenance 2026-05-22 削除 (L-196 整合)

    for name, path in PERIODS.items():
        print(f"[load] {name}: {path}")
        df = pd.read_parquet(path, columns=cols_needed)
        n_rows = len(df)
        exp = EXPECTED_ROWS[name]
        row_verify[name] = {
            "expected": exp,
            "actual": n_rows,
            "diff": n_rows - exp,
            "file_size_bytes": path.stat().st_size,
        }
        print(f"  rows: {n_rows:,} (expected {exp:,}, diff {n_rows - exp:+})")

        for col in label_cols():
            ser = df[col]
            stats_rows.append({
                "period": name,
                "label": col,
                "count": int(ser.count()),
                "mean": float(ser.mean()),
                "std": float(ser.std()),
                "min": float(ser.min()),
                "max": float(ser.max()),
                "p50": float(ser.median()),
                "p99": float(ser.quantile(0.99)),
            })

        # Sample first 5 rows per K, full period (train only — large enough)
        if name == "train_2021_2024":
            for k in K_BARS:
                cols_k = [c for c in label_cols() if c.endswith(f"_K{k}")]
                sample = df[cols_k].head(5).copy()
                sample.insert(0, "ts", df.index[:5])
                sample.to_csv(OUT_DIR / f"sample_rows_K{k:03d}.csv", index=False)

    Path(OUT_DIR / "row_count_verify.json").write_text(
        json.dumps(row_verify, indent=2, ensure_ascii=False)
    )
    # maintenance_flag.json 出力は 2026-05-22 削除 (L-196 整合)
    pd.DataFrame(stats_rows).to_csv(OUT_DIR / "label_stats.csv", index=False)

    print(f"[done] {pd.Timestamp.now()}")
    print(f"  out_dir: {OUT_DIR}")


if __name__ == "__main__":
    main()
