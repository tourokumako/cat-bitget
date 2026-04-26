"""採択モデル(hmm_final.pkl) のラベルを意味的な名前に置き換える。

旧→新（リターン順位ベース・7状態固定）:
  1位↓ = STRONG_DOWN
  2位  = WEAK_DOWN
  3位  = DRIFT_DOWN
  4位  = NEUTRAL
  5位  = DRIFT_UP
  6位  = WEAK_UP
  7位↑ = STRONG_UP

再学習なし・ラベル文字列差し替えのみ。
"""
from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

REPO_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = REPO_ROOT / "models" / "hmm_final.pkl"
FEAT_PATH = REPO_ROOT / "results" / "phase1_features_daily.csv"
RAW_PATH = REPO_ROOT / "data" / "BTCUSDT-5m-2020-01-01_2024-12-31_5y.csv"
STATES_CSV = REPO_ROOT / "results" / "phase2_hmm_final_states.csv"
SUMMARY_JSON = REPO_ROOT / "results" / "phase2_hmm_final_summary.json"

NEW_LABELS_BY_RANK = [
    "STRONG_DOWN", "WEAK_DOWN", "DRIFT_DOWN",
    "NEUTRAL",
    "DRIFT_UP", "WEAK_UP", "STRONG_UP",
]


def main() -> None:
    with open(MODEL_PATH, "rb") as f:
        bundle = pickle.load(f)

    n_states = bundle["config"]["n_states"]
    if n_states != len(NEW_LABELS_BY_RANK):
        raise SystemExit(f"n_states={n_states} != 新ラベル数={len(NEW_LABELS_BY_RANK)}")

    feats = pd.read_csv(FEAT_PATH, parse_dates=["date"]).set_index("date")
    feats.index = feats.index.normalize()
    drop_cols = bundle["config"]["drop_features"]
    feats_sub = feats.drop(columns=drop_cols)

    df = pd.read_csv(RAW_PATH)
    df["ts"] = pd.to_datetime(df["timestamp"])
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    daily_close = df.set_index("ts")["close"].resample("D").last().dropna()
    daily_close.index = daily_close.index.normalize()
    rets = daily_close.pct_change() * 100

    common = feats_sub.index.intersection(rets.index)
    feats_sub = feats_sub.loc[common]
    rets = rets.loc[common]
    keep = ~rets.isna()
    feats_sub = feats_sub[keep]
    rets = rets[keep]

    X = bundle["scaler"].transform(feats_sub.values)
    states = bundle["model"].predict(X)
    rets_arr = rets.values

    state_returns = {int(s): float(np.mean(rets_arr[states == s])) for s in range(n_states)}
    sorted_ids = [sid for sid, _ in sorted(state_returns.items(), key=lambda x: x[1])]

    new_labels: dict[int, str] = {}
    for rank, sid in enumerate(sorted_ids):
        new_labels[sid] = NEW_LABELS_BY_RANK[rank]

    print("旧→新ラベル対応:")
    old_labels = bundle["labels"]
    for sid in range(n_states):
        old = old_labels.get(sid, f"id={sid}")
        new = new_labels[sid]
        ret = state_returns[sid]
        n = int((states == sid).sum())
        print(f"  state_id={sid}  old={old:10s} → new={new:12s}  ret={ret:+7.4f}%  n={n}")

    bundle["labels"] = new_labels
    bundle["label_rename_history"] = {
        "old": {int(k): v for k, v in old_labels.items()},
        "new": {int(k): v for k, v in new_labels.items()},
        "rule": "rank by mean daily return ascending → STRONG_DOWN..STRONG_UP",
    }
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(bundle, f)
    print(f"\n→ {MODEL_PATH.name} 更新")

    states_df = pd.read_csv(STATES_CSV, parse_dates=["date"])
    states_df["state_label"] = states_df["state_id"].map(new_labels)
    states_df.to_csv(STATES_CSV, index=False)
    print(f"→ {STATES_CSV.name} 更新")

    summary = json.loads(SUMMARY_JSON.read_text())
    rename_map = {old_labels[sid]: new_labels[sid] for sid in range(n_states)}
    summary["state_summary"] = {rename_map[k]: v for k, v in summary["state_summary"].items()}
    summary["label_id_map"] = {str(k): v for k, v in new_labels.items()}
    new_pc = {}
    for k, v in summary["pass_check"].items():
        # UPTREND_ret → STRONG_UP_ret etc.
        for old_name, new_name in rename_map.items():
            if k.startswith(old_name + "_"):
                new_pc[new_name + k[len(old_name):]] = v
                break
        else:
            new_pc[k] = v
    summary["pass_check"] = new_pc
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"→ {SUMMARY_JSON.name} 更新")


if __name__ == "__main__":
    main()
