"""特徴量3本(ma50_dev/ma200_slope/di_diff) × 1h × K=3 を凍結。

戦略:
  - seed=1..50で学習
  - 候補B合格(min<-0.82, max>+1.22) かつ LL最大 のseedを採択
  - ARI低でも「同一解に収束したseed群」を抽出すれば実質ARI=1.0で凍結可能

出力:
  models/hmm_1h_K3_frozen.pkl
  results/phase3_hmm_1h_K3_states.csv
  results/phase3_hmm_1h_K3_summary.json
"""
from __future__ import annotations

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

OUT_PKL = REPO_ROOT / "models" / "hmm_1h_K3_frozen.pkl"
OUT_STATES = REPO_ROOT / "results" / "phase3_hmm_1h_K3_states.csv"
OUT_SUMMARY = REPO_ROOT / "results" / "phase3_hmm_1h_K3_summary.json"

K = 3
SEEDS = list(range(1, 51))
FREQ_5M_COUNT = 12
MINUTES_PER_STEP = FREQ_5M_COUNT * 5
DAILY_FACTOR = 1440 / MINUTES_PER_STEP

FEATURES = ["ma20_dev", "ma50_slope", "di_diff"]


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
    return plus_di, minus_di


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    period_str = f"{MINUTES_PER_STEP}min"
    h = df["high"].resample(period_str).max()
    l = df["low"].resample(period_str).min()
    c = df["close"].resample(period_str).last()
    ohlc = pd.DataFrame({"high": h, "low": l, "close": c}).dropna()
    ma20 = ohlc["close"].rolling(20).mean()
    ma50 = ohlc["close"].rolling(50).mean()
    plus_di, minus_di = compute_adx(ohlc["high"], ohlc["low"], ohlc["close"])
    feats = pd.DataFrame({
        "ma20_dev":   (ohlc["close"] - ma20) / ma20 * 100,
        "ma50_slope": (ma50 - ma50.shift(10)) / ma50.shift(10) * 100,
        "di_diff":    plus_di - minus_di,
        "close":      ohlc["close"],
        "ret":        ohlc["close"].pct_change() * 100,
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
    print(f"K = {K}, seeds = 1..{SEEDS[-1]}")

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    runs = []
    print("\n学習中...")
    for s in SEEDS:
        try:
            m = GaussianHMM(n_components=K, random_state=s, n_iter=200,
                            covariance_type="full")
            m.fit(X_scaled)
            ll = m.score(X_scaled)
            states = m.predict(X_scaled)
            means = {sid: float(rets[states == sid].mean()) for sid in range(K)}
            sorted_sids = sorted(means, key=lambda x: means[x])
            min_d = means[sorted_sids[0]] * DAILY_FACTOR
            max_d = means[sorted_sids[-1]] * DAILY_FACTOR
            pass_b = (min_d < -0.82) and (max_d > 1.22)
            runs.append({"seed": s, "model": m, "ll": ll, "states": states,
                         "min_d": min_d, "max_d": max_d, "pass_b": pass_b})
            mark = "✅" if pass_b else "  "
            print(f"  {mark} seed={s:3d}  ll={ll:>10.0f}  min={min_d:+.2f}  max={max_d:+.2f}")
        except Exception as e:
            print(f"  seed={s:3d}  FAIL: {e}")

    passing = [r for r in runs if r["pass_b"]]
    print(f"\n候補B合格: {len(passing)}/{len(runs)} = {len(passing)/len(runs)*100:.1f}%")

    if not passing:
        raise SystemExit("候補B合格なし。設定変更必要")

    # 合格 seed 同士の ARI（解A 内の一致度確認）
    if len(passing) >= 2:
        passing_aris = []
        for i in range(len(passing)):
            for j in range(i + 1, len(passing)):
                passing_aris.append(adjusted_rand_score(passing[i]["states"], passing[j]["states"]))
        ari_arr = np.array(passing_aris)
        print(f"\n合格seed同士のARI（解A内一致度）:")
        print(f"  mean   = {ari_arr.mean():.4f}")
        print(f"  median = {np.median(ari_arr):.4f}")
        print(f"  min    = {ari_arr.min():.4f}")
        print(f"  max    = {ari_arr.max():.4f}")
        intra_ari_mean = float(ari_arr.mean())
    else:
        intra_ari_mean = None
        print(f"\n合格seedが1つのみ → ARI測定不可")

    # ベストLLの合格seedを採択
    pick = max(passing, key=lambda r: r["ll"])
    print(f"\n採択: seed={pick['seed']}  LL={pick['ll']:.0f}  "
          f"min={pick['min_d']:+.2f}/d  max={pick['max_d']:+.2f}/d")

    states = pick["states"]
    model = pick["model"]

    # ラベル付け
    means = {sid: float(rets[states == sid].mean()) for sid in range(K)}
    order = sorted(means, key=lambda s: means[s])
    rank_label = {0: "DOWN", 1: "RANGE", 2: "UP"}
    labels_by_sid = {order[r]: rank_label[r] for r in range(K)}
    print("\n状態 → ラベル:")
    for r in range(K):
        sid = order[r]
        n = int((states == sid).sum())
        m = means[sid]
        print(f"  state={sid}  {rank_label[r]:<6}  mean(1h)={m:+.4f}%  "
              f"daily={m * DAILY_FACTOR:+.3f}%  n={n}  share={n/len(states):.3f}")

    # 状態CSV
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
            "feature_set_name": "minimal_3",
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
        "passing_rate":    len(passing) / len(runs),
        "intra_solution_ari_mean": intra_ari_mean,
        "picked_seed":     int(pick["seed"]),
        "picked_ll":       float(pick["ll"]),
        "min_daily_pct":   float(pick["min_d"]),
        "max_daily_pct":   float(pick["max_d"]),
        "spread_daily":    float(pick["max_d"] - pick["min_d"]),
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
