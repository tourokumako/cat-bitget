"""ダッシュボード ⑨タブ用 HMM 1h K=3 JSON生成。

入力:
  results/phase3_hmm_1h_K3_states.csv（43,598行・1h単位）
  results/phase3_hmm_1h_K3_summary.json
  models/hmm_1h_K3_frozen.pkl

出力: dashboard/data/phase3_hmm.json

内容:
  - config / state_summary / transition / labels
  - hourly: 1h刻み 状態時系列（時系列チャート用 daily downsample）
  - daily: 各日の支配状態（24時間中で最頻ラベル）+ 日次close/return
  - monthly: 月別支配ラベル / ラベル share / 月平均日次リターン
  - return_histograms_per_state: 1hリターン分布
"""
from __future__ import annotations

import json
import pickle
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
STATES_CSV = REPO_ROOT / "results" / "phase3_hmm_1h_K3_states.csv"
SUMMARY_JSON = REPO_ROOT / "results" / "phase3_hmm_1h_K3_summary.json"
MODEL_PATH = REPO_ROOT / "models" / "hmm_1h_K3_frozen.pkl"
RAW_PATH = REPO_ROOT / "data" / "BTCUSDT-5m-2020-01-01_2024-12-31_5y.csv"
OUT_PATH = REPO_ROOT / "dashboard" / "data" / "phase3_hmm.json"

N_BINS = 30


def load_daily_close() -> pd.Series:
    df = pd.read_csv(RAW_PATH)
    df["ts"] = pd.to_datetime(df["timestamp"])
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    daily = df.set_index("ts")["close"].resample("D").last().dropna()
    daily.index = daily.index.normalize()
    return daily


def main() -> None:
    if not STATES_CSV.exists():
        raise SystemExit(f"missing: {STATES_CSV}")

    states_df = pd.read_csv(STATES_CSV, parse_dates=["ts"])
    summary = json.loads(SUMMARY_JSON.read_text())
    with open(MODEL_PATH, "rb") as f:
        bundle = pickle.load(f)

    # ---- daily 集約: 各日の支配状態（24時間中最頻ラベル） ----
    states_df["date"] = states_df["ts"].dt.normalize()
    daily_close = load_daily_close()

    daily_records = []
    for date, grp in states_df.groupby("date"):
        labels = grp["label"]
        dominant = labels.value_counts().idxmax()
        share = float(labels.value_counts(normalize=True).max())
        # その日の各ラベルの share
        share_per_label = labels.value_counts(normalize=True).to_dict()
        share_per_label = {k: round(float(v), 3) for k, v in share_per_label.items()}
        close_v = daily_close.get(date)
        daily_records.append({
            "date":            date.strftime("%Y-%m-%d"),
            "dominant":        dominant,
            "dominant_share":  round(share, 3),
            "share":           share_per_label,
            "n_hours":         int(len(grp)),
            "mean_ret_pct":    round(float(grp["ret_1h"].mean() * 24), 4),
            "close":           round(float(close_v), 2) if close_v is not None and pd.notna(close_v) else None,
        })

    # ---- 月別集約 ----
    states_df["ym"] = states_df["ts"].dt.to_period("M").dt.to_timestamp()
    monthly_records = []
    for ym, grp in states_df.groupby("ym"):
        share = grp["label"].value_counts(normalize=True).to_dict()
        share = {k: round(float(v), 4) for k, v in share.items()}
        dominant = max(share, key=share.get)
        monthly_records.append({
            "date":         ym.strftime("%Y-%m"),
            "n_hours":      int(len(grp)),
            "mean_ret_pct_per_h": round(float(grp["ret_1h"].mean()), 4),
            "label_share":  share,
            "dominant":     dominant,
        })

    # ---- 状態別 1h リターンヒストグラム ----
    return_histograms = {}
    for label, grp in states_df.groupby("label"):
        rets = grp["ret_1h"].dropna().values
        if len(rets) < 2:
            continue
        counts, edges = np.histogram(rets, bins=N_BINS)
        return_histograms[label] = {
            "n":          int(len(rets)),
            "bin_edges":  [round(float(e), 4) for e in edges],
            "counts":     [int(c) for c in counts],
            "mean":       round(float(np.mean(rets)), 4),
            "median":     round(float(np.median(rets)), 4),
            "std":        round(float(np.std(rets)), 4),
        }

    # ---- 遷移確率 ----
    transmat = bundle["model"].transmat_
    labels_map = bundle["labels"]
    n_states = len(labels_map)
    label_order = [labels_map[i] for i in range(n_states)]
    transition = {
        "labels_in_order": label_order,
        "matrix": [[round(float(p), 4) for p in row] for row in transmat],
    }

    out = {
        "config": {
            **bundle["config"],
            "picked_seed": bundle["picked_seed"],
            "picked_ll":   bundle["picked_ll"],
        },
        "summary":     summary,
        "labels_by_sid": {str(k): v for k, v in labels_map.items()},
        "period": {
            "start":   str(states_df["ts"].min()),
            "end":     str(states_df["ts"].max()),
            "n_hours": int(len(states_df)),
            "n_days":  int(len(daily_records)),
        },
        "daily":       daily_records,
        "monthly":     monthly_records,
        "return_histograms_per_state": return_histograms,
        "transition":  transition,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"→ {OUT_PATH}")
    print(f"  daily: {len(daily_records)} 日")
    print(f"  monthly: {len(monthly_records)} ヶ月")
    print(f"  states: {list(return_histograms.keys())}")


if __name__ == "__main__":
    main()
