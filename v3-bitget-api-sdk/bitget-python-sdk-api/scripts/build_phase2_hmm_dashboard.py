"""ダッシュボード ⑧ HMMレジーム検証タブ用 JSON 生成。

入力:
  results/phase2_hmm_final_states.csv（採択モデルの状態列・1778日）
  results/phase2_hmm_final_summary.json（採択モデル詳細）
  data/BTCUSDT-5m-2020-01-01_2024-12-31_5y.csv（日次close用）

出力: dashboard/data/phase2_hmm.json

内容:
  - adopted_config / metrics / state_summary
  - daily: 1778日 [date, label, return, close]（visualization用）
  - monthly: 月別 [date, label_share, mean_return, dominant_label]
  - return_histograms_per_state: 各状態のリターン分布（30 bin）
  - transition_summary: 状態遷移確率（採択モデルから）
"""
from __future__ import annotations

import json
import pickle
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
STATES_CSV = REPO_ROOT / "results" / "phase2_hmm_final_states.csv"
SUMMARY_JSON = REPO_ROOT / "results" / "phase2_hmm_final_summary.json"
MODEL_PATH = REPO_ROOT / "models" / "hmm_final.pkl"
RAW_PATH = REPO_ROOT / "data" / "BTCUSDT-5m-2020-01-01_2024-12-31_5y.csv"
OUT_PATH = REPO_ROOT / "dashboard" / "data" / "phase2_hmm.json"

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
        raise SystemExit(f"missing: {STATES_CSV}（先に phase2_hmm_finalize.py 実行）")
    if not SUMMARY_JSON.exists():
        raise SystemExit(f"missing: {SUMMARY_JSON}")
    if not MODEL_PATH.exists():
        raise SystemExit(f"missing: {MODEL_PATH}")

    states_df = pd.read_csv(STATES_CSV, parse_dates=["date"])
    states_df["date"] = states_df["date"].dt.normalize()
    summary = json.loads(SUMMARY_JSON.read_text())
    with open(MODEL_PATH, "rb") as f:
        bundle = pickle.load(f)

    daily_close = load_daily_close()
    states_df = states_df.merge(
        daily_close.rename("close"), left_on="date", right_index=True, how="left"
    )

    # daily 配列
    daily = []
    for _, row in states_df.iterrows():
        daily.append({
            "date": row["date"].strftime("%Y-%m-%d"),
            "label": row["state_label"],
            "state_id": int(row["state_id"]),
            "ret_pct": round(float(row["daily_return_pct"]), 4),
            "close": round(float(row["close"]), 2) if pd.notna(row["close"]) else None,
        })

    # 月別集計
    states_df["ym"] = states_df["date"].dt.to_period("M").dt.to_timestamp()
    monthly = []
    for ym, grp in states_df.groupby("ym"):
        share = grp["state_label"].value_counts(normalize=True).to_dict()
        share = {k: round(float(v), 4) for k, v in share.items()}
        dominant = max(share, key=share.get)
        monthly.append({
            "date": ym.strftime("%Y-%m"),
            "n_days": int(len(grp)),
            "mean_ret_pct": round(float(grp["daily_return_pct"].mean()), 4),
            "label_share": share,
            "dominant_label": dominant,
        })

    # 状態別 リターンヒストグラム
    return_histograms = {}
    for label, grp in states_df.groupby("state_label"):
        rets = grp["daily_return_pct"].dropna().values
        if len(rets) < 2:
            continue
        counts, edges = np.histogram(rets, bins=N_BINS)
        return_histograms[label] = {
            "n": int(len(rets)),
            "bin_edges": [round(float(e), 3) for e in edges],
            "counts": [int(c) for c in counts],
            "mean": round(float(np.mean(rets)), 4),
            "median": round(float(np.median(rets)), 4),
            "std": round(float(np.std(rets)), 4),
        }

    # 遷移確率行列
    transmat = bundle["model"].transmat_
    labels_map = bundle["labels"]
    n_states = len(labels_map)
    label_order = [labels_map[i] for i in range(n_states)]
    transition = {
        "labels_in_order": label_order,
        "matrix": [[round(float(p), 4) for p in row] for row in transmat],
    }

    out = {
        "adopted_config": summary["adopted_config"],
        "metrics": summary["metrics"],
        "criteria_B": summary["criteria_B"],
        "pass_check": summary["pass_check"],
        "state_summary": summary["state_summary"],
        "search_stats": summary["search_stats"],
        "label_id_map": summary["label_id_map"],
        "period": {
            "start": str(states_df["date"].min().date()),
            "end": str(states_df["date"].max().date()),
            "n_days": int(len(states_df)),
        },
        "daily": daily,
        "monthly": monthly,
        "return_histograms_per_state": return_histograms,
        "transition": transition,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"→ {OUT_PATH}（{len(daily)}日 × {len(return_histograms)}状態）")


if __name__ == "__main__":
    main()
