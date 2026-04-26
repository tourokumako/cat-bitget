"""A_direction × 1h × K=4 を seed×50 で学習し、ベストLLモデルを凍結。

ARI が低い（0.4台）ため、ベストLLseed を採択して固定する戦略。
固定後は予測がブレない（同じ入力→同じ状態）ので、安定性問題は凍結で解決。

出力:
  models/hmm_1h_K4_frozen.pkl
  results/phase3_hmm_1h_K4_states.csv
  results/phase3_hmm_1h_K4_summary.json
"""
from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from sklearn.preprocessing import StandardScaler

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = REPO_ROOT / "data" / "BTCUSDT-5m-2020-01-01_2024-12-31_5y.csv"

OUT_PKL = REPO_ROOT / "models" / "hmm_1h_K4_frozen.pkl"
OUT_STATES = REPO_ROOT / "results" / "phase3_hmm_1h_K4_states.csv"
OUT_SUMMARY = REPO_ROOT / "results" / "phase3_hmm_1h_K4_summary.json"

K = 4
SEEDS = list(range(1, 51))
FREQ_5M_COUNT = 12
MINUTES_PER_STEP = FREQ_5M_COUNT * 5
DAILY_FACTOR = 1440 / MINUTES_PER_STEP

FEATURES = ["ret", "ma50_dev", "ma200_slope", "adx", "di_diff"]


def compute_adx(high, low, close, period=14):
    up = high.diff()
    dn = -low.diff()
    plus_dm = pd.Series(np.where((up > dn) & (up > 0), up, 0.0), index=high.index)
    minus_dm = pd.Series(np.where((dn > up) & (dn > 0), dn, 0.0), index=high.index)
    tr = pd.concat([
        (high - low),
        (high - close.shift()).abs(),
        (low - close.shift()).abs(),
    ], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / period, adjust=False).mean()
    plus_di = 100 * plus_dm.ewm(alpha=1 / period, adjust=False).mean() / atr
    minus_di = 100 * minus_dm.ewm(alpha=1 / period, adjust=False).mean() / atr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.ewm(alpha=1 / period, adjust=False).mean()
    return adx, plus_di, minus_di


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    period_str = f"{MINUTES_PER_STEP}min"
    o = df["open"].resample(period_str).first()
    h = df["high"].resample(period_str).max()
    l = df["low"].resample(period_str).min()
    c = df["close"].resample(period_str).last()
    ohlc = pd.DataFrame({"open": o, "high": h, "low": l, "close": c}).dropna()
    rets = ohlc["close"].pct_change() * 100
    ma50 = ohlc["close"].rolling(50).mean()
    ma200 = ohlc["close"].rolling(200).mean()
    adx, plus_di, minus_di = compute_adx(ohlc["high"], ohlc["low"], ohlc["close"])
    feats = pd.DataFrame({
        "ret":         rets,
        "ma50_dev":    (ohlc["close"] - ma50) / ma50 * 100,
        "ma200_slope": (ma200 - ma200.shift(20)) / ma200.shift(20) * 100,
        "adx":         adx,
        "di_diff":     plus_di - minus_di,
        "close":       ohlc["close"],
    }, index=ohlc.index).dropna()
    return feats


def main() -> None:
    df = pd.read_csv(RAW_PATH)
    df["ts"] = pd.to_datetime(df["timestamp"])
    for c in ("open", "high", "low", "close"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.sort_values("ts").dropna(subset=["close"]).set_index("ts")

    feats = build_features(df)
    X = feats[FEATURES].values
    rets = feats["ret"].values
    closes = feats["close"].values
    print(f"n_samples (1h): {len(X):,}")
    print(f"features: {FEATURES}")
    print(f"seeds: 1..{SEEDS[-1]} ({len(SEEDS)})")

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print(f"\n学習中...")
    runs = []
    for s in SEEDS:
        try:
            m = GaussianHMM(n_components=K, random_state=s, n_iter=200,
                            covariance_type="full")
            m.fit(X_scaled)
            ll = m.score(X_scaled)
            states = m.predict(X_scaled)
            # 候補B評価
            means = {sid: float(rets[states == sid].mean()) for sid in range(K)}
            sorted_sids = sorted(means, key=lambda x: means[x])
            min_d = means[sorted_sids[0]] * DAILY_FACTOR
            max_d = means[sorted_sids[-1]] * DAILY_FACTOR
            pass_b = (min_d < -0.82) and (max_d > 1.22)
            runs.append({
                "seed": s, "model": m, "ll": ll, "states": states,
                "pass_b": pass_b, "min_d": min_d, "max_d": max_d,
            })
            mark = "✅" if pass_b else "  "
            print(f"  {mark} seed={s:3d}  ll={ll:>10.0f}  min={min_d:+.2f}  max={max_d:+.2f}")
        except Exception as e:
            print(f"  seed={s:3d}  FAIL: {e}")

    passing = [r for r in runs if r["pass_b"]]
    print(f"\n候補B合格 seed: {len(passing)}/{len(runs)}")

    if not passing:
        raise SystemExit("候補B合格なし。設定変更必要")

    pick = max(passing, key=lambda r: r["ll"])
    print(f"\n採択: seed={pick['seed']}  LL={pick['ll']:.0f}  "
          f"min={pick['min_d']:+.2f}/d  max={pick['max_d']:+.2f}/d")

    states = pick["states"]
    model = pick["model"]

    # ラベル付け（リターン平均rank）
    means = {sid: float(rets[states == sid].mean()) for sid in range(K)}
    order = sorted(means, key=lambda s: means[s])
    rank_label = {0: "DOWN", 1: "MID_DOWN", 2: "MID_UP", 3: "UP"}
    labels_by_sid = {order[r]: rank_label[r] for r in range(K)}
    print("\n状態 → ラベル:")
    for r in range(K):
        sid = order[r]
        n = int((states == sid).sum())
        m = means[sid]
        print(f"  state={sid}  {rank_label[r]:<10}  mean(1h)={m:+.4f}%  "
              f"daily={m * DAILY_FACTOR:+.3f}%  n={n}  share={n/len(states):.3f}")

    # 状態CSV出力
    states_df = pd.DataFrame({
        "ts":       feats.index,
        "state_id": states,
        "label":    [labels_by_sid[s] for s in states],
        "close":    closes,
        "ret_1h":   rets,
    })
    OUT_STATES.parent.mkdir(parents=True, exist_ok=True)
    states_df.to_csv(OUT_STATES, index=False)
    print(f"\n→ {OUT_STATES}")

    # 凍結
    bundle = {
        "config": {
            "freq":             "1h",
            "minutes_per_step": MINUTES_PER_STEP,
            "n_states":         K,
            "feature_cols":     FEATURES,
            "feature_set_name": "A_direction",
        },
        "model":  model,
        "scaler": scaler,
        "labels": {int(k): v for k, v in labels_by_sid.items()},
        "picked_seed": int(pick["seed"]),
        "picked_ll":   float(pick["ll"]),
    }
    OUT_PKL.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PKL, "wb") as f:
        pickle.dump(bundle, f)
    print(f"→ {OUT_PKL}")

    summary = {
        "freq":            "1h",
        "n_states":        K,
        "n_samples":       len(X),
        "feature_cols":    FEATURES,
        "n_seeds_tried":   len(runs),
        "n_seeds_passing": len(passing),
        "picked_seed":     int(pick["seed"]),
        "picked_ll":       float(pick["ll"]),
        "min_daily_pct":   float(pick["min_d"]),
        "max_daily_pct":   float(pick["max_d"]),
        "labels_by_sid":   {str(k): v for k, v in labels_by_sid.items()},
        "state_summary": {
            labels_by_sid[sid]: {
                "n":               int((states == sid).sum()),
                "share":           float((states == sid).sum() / len(states)),
                "mean_period_pct": float(rets[states == sid].mean()),
                "daily_pct":       float(rets[states == sid].mean() * DAILY_FACTOR),
                "std_period_pct":  float(rets[states == sid].std()),
            }
            for sid in range(K)
        },
        "transition_matrix": [
            [float(p) for p in row] for row in model.transmat_
        ],
    }
    OUT_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"→ {OUT_SUMMARY}")


if __name__ == "__main__":
    main()
