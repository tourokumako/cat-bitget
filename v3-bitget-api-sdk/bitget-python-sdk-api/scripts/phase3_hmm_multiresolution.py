"""複数粒度（5m〜1d）で HMM(n=3) を学習・BIC比較・状態持続時間分布算出。

入力:
  data/BTCUSDT-5m-2020-01-01_2024-12-31_5y.csv

出力:
  - results/phase3_bic_comparison.json
    粒度別 BIC/AIC/n_samples/per_sample_bic
    + 状態持続時間分布（中央値・25/75/95p・最大）
  - 標準出力: BIC比較表・推奨粒度
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from sklearn.preprocessing import StandardScaler

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = REPO_ROOT / "data" / "BTCUSDT-5m-2020-01-01_2024-12-31_5y.csv"
OUT_PATH = REPO_ROOT / "results" / "phase3_bic_comparison.json"

RESOLUTIONS = {
    "5m":  1,
    "15m": 3,
    "30m": 6,
    "1h":  12,
    "2h":  24,
    "4h":  48,
    "8h":  96,
    "1d":  288,
}

N_STATES = 3
RANDOM_SEED = 42


def load_raw_data() -> pd.DataFrame:
    df = pd.read_csv(RAW_PATH)
    df["ts"] = pd.to_datetime(df["timestamp"])
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.sort_values("ts").dropna(subset=["close"])
    return df.set_index("ts")


def resample_features(close_5m: pd.Series, freq_5m_count: int) -> pd.DataFrame:
    """5分足 close を粒度別にリサンプル＆特徴量計算。

    特徴量（4本）:
      - ret: 期間リターン (%)
      - ma20_dev: MA20乖離率 (%)
      - vol_7: 直近7期間リターン標準偏差
      - skew_30: 直近30期間リターン歪度
    """
    period_min = freq_5m_count * 5
    period_str = f"{period_min}min"
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


def fit_hmm(X: np.ndarray, n_states: int = 3) -> dict:
    """HMM学習・BIC/AIC + 状態系列・持続時間分布を返す."""
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = GaussianHMM(n_components=n_states, random_state=RANDOM_SEED,
                        n_iter=200, covariance_type="full")
    model.fit(X_scaled)

    ll = model.score(X_scaled)
    n_features = X.shape[1]
    # パラメータ数: 遷移行列 K(K-1) + 平均 K*F + 共分散 K*F*(F+1)/2 + 初期分布 K-1
    n_params = (
        n_states * (n_states - 1)
        + n_states * n_features
        + n_states * n_features * (n_features + 1) // 2
        + (n_states - 1)
    )
    n = len(X_scaled)
    bic = -2 * ll + n_params * np.log(n)
    aic = -2 * ll + 2 * n_params

    states = model.predict(X_scaled)
    runs = run_lengths(states)
    if runs:
        runs_arr = np.array(runs)
        dur = {
            "median":  float(np.median(runs_arr)),
            "p25":     float(np.percentile(runs_arr, 25)),
            "p75":     float(np.percentile(runs_arr, 75)),
            "p95":     float(np.percentile(runs_arr, 95)),
            "max":     int(runs_arr.max()),
            "n_runs":  len(runs_arr),
        }
    else:
        dur = {}

    return {
        "bic":            float(bic),
        "aic":            float(aic),
        "ll":             float(ll),
        "n_params":       n_params,
        "n_samples":      n,
        "per_sample_bic": float(bic / n),
        "duration_steps": dur,
    }


def run_lengths(states: np.ndarray) -> list[int]:
    """状態系列の連続区間長を列挙."""
    if len(states) == 0:
        return []
    runs = []
    cur = states[0]
    n = 1
    for s in states[1:]:
        if s == cur:
            n += 1
        else:
            runs.append(n)
            cur = s
            n = 1
    runs.append(n)
    return runs


def main() -> None:
    df = load_raw_data()
    close = df["close"]

    results = {}
    header = (
        f"{'粒度':<6} {'n_samples':>10} {'BIC':>14} {'BIC/n':>10} "
        f"{'継続中央値':>10} {'継続p95':>10}"
    )
    print(header)
    print("-" * len(header))

    for name, count in RESOLUTIONS.items():
        feats = resample_features(close, count)
        X = feats[["ret", "ma20_dev", "vol_7", "skew_30"]].values
        m = fit_hmm(X, n_states=N_STATES)
        m["resolution"] = name
        m["minutes_per_step"] = count * 5
        results[name] = m

        dur = m["duration_steps"]
        med_min = dur["median"] * count * 5
        p95_min = dur["p95"] * count * 5
        med_str = f"{dur['median']:.0f}({fmt_min(med_min)})"
        p95_str = f"{dur['p95']:.0f}({fmt_min(p95_min)})"
        print(
            f"{name:<6} {m['n_samples']:>10d} {m['bic']:>14.0f} "
            f"{m['per_sample_bic']:>10.2f} {med_str:>10} {p95_str:>10}"
        )

    best = min(results.items(), key=lambda x: x[1]["per_sample_bic"])
    print("-" * len(header))
    print(f"\n✓ per-sample BIC 最小（最適候補）: {best[0]}")
    print(f"  per_sample_bic = {best[1]['per_sample_bic']:.4f}")
    dur = best[1]["duration_steps"]
    print(f"  状態持続中央値 = {dur['median']:.0f}step "
          f"= {fmt_min(dur['median'] * best[1]['minutes_per_step'])}")

    OUT_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\n→ {OUT_PATH}")


def fmt_min(minutes: float) -> str:
    if minutes < 60:
        return f"{minutes:.0f}m"
    if minutes < 1440:
        return f"{minutes/60:.1f}h"
    return f"{minutes/1440:.1f}d"


if __name__ == "__main__":
    main()
