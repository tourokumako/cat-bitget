"""A_direction × 1h で K=4 と K=5 を詳細比較。

比較軸:
  1. 安定性: seed=1..20 の ARI mean/median
  2. 各状態のリターン分布: mean / std / n
  3. 状態の持続時間分布: median / p95 ステップ
  4. 状態遷移行列
  5. 月別の支配状態数

出力:
  results/phase3_hmm_compare_k4_k5.json
  標準出力: 比較サマリ
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from sklearn.metrics import adjusted_rand_score
from sklearn.preprocessing import StandardScaler

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = REPO_ROOT / "data" / "BTCUSDT-5m-2020-01-01_2024-12-31_5y.csv"
OUT_PATH = REPO_ROOT / "results" / "phase3_hmm_compare_k4_k5.json"

K_LIST = [2, 4, 5]
SEEDS = list(range(1, 21))
FREQ_5M_COUNT = 12  # 1h
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
    }, index=ohlc.index)
    return feats.dropna()


def run_lengths(states: np.ndarray) -> list[int]:
    if len(states) == 0:
        return []
    runs, cur, n = [], states[0], 1
    for s in states[1:]:
        if s == cur:
            n += 1
        else:
            runs.append(n); cur = s; n = 1
    runs.append(n)
    return runs


def fit_seeds(X_scaled: np.ndarray, K: int, seeds: list[int]):
    runs = []
    for s in seeds:
        try:
            m = GaussianHMM(n_components=K, random_state=s, n_iter=200,
                            covariance_type="full")
            m.fit(X_scaled)
            runs.append({"seed": s, "model": m, "ll": m.score(X_scaled),
                         "states": m.predict(X_scaled)})
        except Exception:
            continue
    return runs


def pairwise_ari(runs: list[dict]) -> dict:
    aris = []
    for i in range(len(runs)):
        for j in range(i + 1, len(runs)):
            aris.append(adjusted_rand_score(runs[i]["states"], runs[j]["states"]))
    arr = np.array(aris)
    return {
        "mean":   float(arr.mean()),
        "median": float(np.median(arr)),
        "p25":    float(np.percentile(arr, 25)),
        "p75":    float(np.percentile(arr, 75)),
        "n_pairs": len(arr),
    }


def state_stats(states: np.ndarray, rets: np.ndarray, K: int) -> list[dict]:
    """状態を期間リターン平均でランク付けして詳細統計."""
    means = {s: float(rets[states == s].mean()) for s in range(K)}
    order = sorted(means, key=lambda s: means[s])  # 低い→高い
    rank_to_label = {0: "DOWN", K - 1: "UP"}
    if K == 2:
        pass  # DOWN/UPのみ
    elif K == 3:
        rank_to_label[1] = "RANGE"
    elif K == 4:
        rank_to_label[1] = "MID_DOWN"
        rank_to_label[2] = "MID_UP"
    elif K == 5:
        rank_to_label[1] = "MID_DOWN"
        rank_to_label[2] = "RANGE"
        rank_to_label[3] = "MID_UP"

    stats = []
    for rank, sid in enumerate(order):
        r = rets[states == sid]
        stats.append({
            "state_id":        int(sid),
            "rank":            rank,
            "label":           rank_to_label[rank],
            "n":               int(len(r)),
            "share":           float(len(r) / len(states)),
            "mean_period_pct": float(r.mean()),
            "std_period_pct":  float(r.std()),
            "daily_pct":       float(r.mean() * DAILY_FACTOR),
        })
    return stats


def transition_matrix(states: np.ndarray, K: int) -> list[list[float]]:
    mat = np.zeros((K, K), dtype=float)
    for a, b in zip(states[:-1], states[1:]):
        mat[a, b] += 1
    row_sums = mat.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    return (mat / row_sums).round(3).tolist()


def duration_dist(states: np.ndarray, K: int) -> dict:
    out = {}
    for s in range(K):
        runs = []
        cur_run = 0
        for st in states:
            if st == s:
                cur_run += 1
            elif cur_run > 0:
                runs.append(cur_run); cur_run = 0
        if cur_run > 0:
            runs.append(cur_run)
        if runs:
            arr = np.array(runs)
            out[s] = {
                "median_steps": float(np.median(arr)),
                "p95_steps":    float(np.percentile(arr, 95)),
                "median_hours": float(np.median(arr) * MINUTES_PER_STEP / 60),
                "p95_hours":    float(np.percentile(arr, 95) * MINUTES_PER_STEP / 60),
                "n_runs":       len(arr),
            }
    return out


def monthly_dominant(feats_index: pd.DatetimeIndex, states: np.ndarray, labels_by_sid: dict) -> dict:
    df = pd.DataFrame({"label": [labels_by_sid[int(s)] for s in states]}, index=feats_index)
    df["ym"] = df.index.to_period("M")
    out = {}
    for ym, g in df.groupby("ym"):
        share = g["label"].value_counts(normalize=True)
        out[str(ym)] = {
            "dominant": share.idxmax(),
            "share":    float(share.max()),
        }
    return out


def main() -> None:
    df = pd.read_csv(RAW_PATH)
    df["ts"] = pd.to_datetime(df["timestamp"])
    for c in ("open", "high", "low", "close"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.sort_values("ts").dropna(subset=["close"]).set_index("ts")

    feats = build_features(df)
    X = feats[FEATURES].values
    rets = feats["ret"].values
    print(f"n_samples (1h): {len(X):,}")
    print(f"features: {FEATURES}")
    print(f"seeds: {SEEDS[0]}..{SEEDS[-1]} ({len(SEEDS)})")

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    out_all = {}
    for K in K_LIST:
        print(f"\n{'='*70}\nK = {K} 学習中...\n{'='*70}")
        runs = fit_seeds(X_scaled, K, SEEDS)
        print(f"  成功 seed: {len(runs)}/{len(SEEDS)}")

        ari = pairwise_ari(runs)
        print(f"  ARI: mean={ari['mean']:.3f} median={ari['median']:.3f} "
              f"p25-p75={ari['p25']:.3f}-{ari['p75']:.3f}")

        # 中央値LLのseed採択
        runs_sorted = sorted(runs, key=lambda r: r["ll"])
        pick = runs_sorted[len(runs_sorted) // 2]
        states = pick["states"]
        print(f"  採択 seed = {pick['seed']} (LL = {pick['ll']:.0f})")

        stats = state_stats(states, rets, K)
        print(f"\n  状態別リターン分布（rank順 = リターン低→高）:")
        print(f"  {'rank':<5}{'label':<10}{'n':>8}{'share':>8}"
              f"{'mean(1h)':>12}{'daily':>10}{'std(1h)':>10}")
        for s in stats:
            print(f"  {s['rank']:<5}{s['label']:<10}{s['n']:>8}{s['share']:>8.3f}"
                  f"{s['mean_period_pct']:>12.4f}{s['daily_pct']:>10.3f}{s['std_period_pct']:>10.3f}")

        labels_by_sid = {s["state_id"]: s["label"] for s in stats}
        dur = duration_dist(states, K)
        print(f"\n  状態持続時間（中央値・p95）:")
        for sid in sorted(dur):
            label = labels_by_sid[sid]
            d = dur[sid]
            print(f"    {label:<10} median={d['median_hours']:5.1f}h  "
                  f"p95={d['p95_hours']:6.1f}h  n_runs={d['n_runs']}")

        trans = transition_matrix(states, K)
        ranked_ids = [s["state_id"] for s in stats]
        print(f"\n  状態遷移行列（rank順 ラベル）:")
        header = "        " + "".join(f"{labels_by_sid[i]:>10}" for i in ranked_ids)
        print(header)
        for i in ranked_ids:
            row = "  " + f"{labels_by_sid[i]:<8}" + "".join(
                f"{trans[i][j]:>10.3f}" for j in ranked_ids
            )
            print(row)

        monthly = monthly_dominant(feats.index, states, labels_by_sid)
        dom_counts = pd.Series([m["dominant"] for m in monthly.values()]).value_counts().to_dict()
        print(f"\n  月別支配ラベル分布（60ヶ月）: {dom_counts}")

        out_all[f"K{K}"] = {
            "ari":            ari,
            "picked_seed":    int(pick["seed"]),
            "picked_ll":      float(pick["ll"]),
            "state_stats":    stats,
            "transition":     {"order_state_ids": ranked_ids, "matrix": trans,
                               "labels_by_sid": labels_by_sid},
            "duration":       {str(k): v for k, v in dur.items()},
            "monthly_dominant_counts": dom_counts,
        }

    OUT_PATH.write_text(json.dumps(out_all, indent=2, ensure_ascii=False))
    print(f"\n→ {OUT_PATH}")


if __name__ == "__main__":
    main()
