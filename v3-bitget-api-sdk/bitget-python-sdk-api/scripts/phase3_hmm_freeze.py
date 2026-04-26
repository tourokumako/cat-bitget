"""指定粒度（デフォルト1h）で HMM(n=3) を multi-init 学習し、安定性判定→凍結。

手順:
  1. 5分足を指定粒度にリサンプル → 4特徴量
  2. seed 1..N_INITS で HMM学習
  3. 各 seed の状態系列をペアワイズ Adjusted Rand Index (ARI) 比較
  4. 平均ARI ≥ 0.7 → 安定 / 中央値 seed を選んで .pkl 凍結
     平均ARI < 0.7 → 不安定（15mに落とす判断材料）

使い方:
  python3 scripts/phase3_hmm_freeze.py            # デフォルト 1h
  python3 scripts/phase3_hmm_freeze.py --freq 15m
  python3 scripts/phase3_hmm_freeze.py --freq 1h --inits 30
"""
from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from sklearn.metrics import adjusted_rand_score
from sklearn.preprocessing import StandardScaler

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = REPO_ROOT / "data" / "BTCUSDT-5m-2020-01-01_2024-12-31_5y.csv"

FREQ_TO_5M_COUNT = {
    "5m": 1, "15m": 3, "30m": 6,
    "1h": 12, "2h": 24, "4h": 48, "8h": 96, "1d": 288,
}

N_STATES = 3
DEFAULT_INITS = 20
STABILITY_THRESHOLD = 0.7


def resample_features(close_5m: pd.Series, k: int) -> pd.DataFrame:
    period_str = f"{k * 5}min"
    px = close_5m.resample(period_str).last().dropna()
    rets = px.pct_change() * 100
    ma20 = px.rolling(20).mean()
    feats = pd.DataFrame({
        "ret":      rets,
        "ma20_dev": (px - ma20) / ma20 * 100,
        "vol_7":    rets.rolling(7).std(),
        "skew_30":  rets.rolling(30).skew(),
    }, index=px.index)
    return feats.dropna()


def fit_one(X_scaled: np.ndarray, seed: int) -> tuple[GaussianHMM, np.ndarray, float]:
    model = GaussianHMM(
        n_components=N_STATES, random_state=seed, n_iter=200,
        covariance_type="full",
    )
    model.fit(X_scaled)
    return model, model.predict(X_scaled), model.score(X_scaled)


def label_states_by_return(states: np.ndarray, rets: np.ndarray) -> dict:
    """状態を期間リターン平均でランク付けして DOWN/RANGE/UP に命名."""
    means = {s: float(rets[states == s].mean()) for s in range(N_STATES)}
    order = sorted(means, key=lambda s: means[s])  # 低い→高い
    return {order[0]: "DOWN", order[1]: "RANGE", order[2]: "UP"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freq", default="1h", choices=list(FREQ_TO_5M_COUNT))
    parser.add_argument("--inits", type=int, default=DEFAULT_INITS)
    args = parser.parse_args()

    k = FREQ_TO_5M_COUNT[args.freq]
    print(f"粒度: {args.freq} (5m足×{k})  / multi-init: seed 1..{args.inits}")

    df = pd.read_csv(RAW_PATH)
    df["ts"] = pd.to_datetime(df["timestamp"])
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.sort_values("ts").dropna(subset=["close"]).set_index("ts")

    feats = resample_features(df["close"], k)
    feature_cols = ["ret", "ma20_dev", "vol_7", "skew_30"]
    X = feats[feature_cols].values
    rets = feats["ret"].values
    print(f"n_samples = {len(X):,}")

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print("\n学習中...")
    runs = []
    for s in range(1, args.inits + 1):
        try:
            model, states, ll = fit_one(X_scaled, s)
            runs.append({"seed": s, "model": model, "states": states, "ll": ll})
            print(f"  seed={s:3d}  ll={ll:>14.2f}")
        except Exception as e:
            print(f"  seed={s:3d}  FAIL: {e}")

    if len(runs) < 2:
        raise SystemExit("学習成功 seed が 2 未満。粒度を変更してください")

    print("\nペアワイズ ARI（同じ状態系列か = 安定性）:")
    n = len(runs)
    aris = []
    for i in range(n):
        for j in range(i + 1, n):
            ari = adjusted_rand_score(runs[i]["states"], runs[j]["states"])
            aris.append(ari)
    aris_arr = np.array(aris)
    mean_ari = float(aris_arr.mean())
    median_ari = float(np.median(aris_arr))
    p25 = float(np.percentile(aris_arr, 25))
    p75 = float(np.percentile(aris_arr, 75))
    print(f"  mean   = {mean_ari:.3f}")
    print(f"  median = {median_ari:.3f}")
    print(f"  p25-p75 = {p25:.3f} - {p75:.3f}")
    print(f"  pairs  = {len(aris_arr)}")

    stable = mean_ari >= STABILITY_THRESHOLD
    verdict = "✅ 安定（凍結に進めます）" if stable else "⚠️  不安定（粒度を細かく / 特徴量見直し推奨）"
    print(f"\n安定性判定（しきい値 {STABILITY_THRESHOLD}）: {verdict}")

    # 中央値LL の seed を採択
    runs_sorted_by_ll = sorted(runs, key=lambda r: r["ll"])
    pick = runs_sorted_by_ll[len(runs_sorted_by_ll) // 2]
    states_pick = pick["states"]
    labels = label_states_by_return(states_pick, rets)

    print(f"\n採択 seed = {pick['seed']} (LL={pick['ll']:.2f})")
    print("状態 → ラベル（リターン平均ランク順）:")
    for sid in range(N_STATES):
        m = float(rets[states_pick == sid].mean())
        nrun = int((states_pick == sid).sum())
        print(f"  state {sid}: {labels[sid]:<6} mean_ret_pct={m:+.4f}  n={nrun}")

    summary = {
        "freq":            args.freq,
        "minutes_per_step": k * 5,
        "n_inits":         args.inits,
        "n_samples":       len(X),
        "feature_cols":    feature_cols,
        "ari_mean":        mean_ari,
        "ari_median":      median_ari,
        "ari_p25":         p25,
        "ari_p75":         p75,
        "stable":          bool(stable),
        "stability_threshold": STABILITY_THRESHOLD,
        "picked_seed":     int(pick["seed"]),
        "picked_ll":       float(pick["ll"]),
        "labels":          {str(k_): v for k_, v in labels.items()},
        "state_summary":   {
            labels[sid]: {
                "mean_ret_pct": float(rets[states_pick == sid].mean()),
                "n":            int((states_pick == sid).sum()),
            }
            for sid in range(N_STATES)
        },
    }

    out_summary = REPO_ROOT / "results" / f"phase3_hmm_{args.freq}_summary.json"
    out_summary.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"\n→ {out_summary}")

    if stable:
        bundle = {
            "config":    {"freq": args.freq, "n_states": N_STATES, "feature_cols": feature_cols},
            "model":     pick["model"],
            "scaler":    scaler,
            "labels":    {int(k_): v for k_, v in labels.items()},
            "summary":   summary,
        }
        out_pkl = REPO_ROOT / "models" / f"hmm_{args.freq}_frozen.pkl"
        out_pkl.parent.mkdir(parents=True, exist_ok=True)
        with open(out_pkl, "wb") as f:
            pickle.dump(bundle, f)
        print(f"→ {out_pkl}")
    else:
        print(f"\n⚠️  凍結保存をスキップ。粒度を細かく（例 --freq 15m）して再試行してください。")


if __name__ == "__main__":
    main()
