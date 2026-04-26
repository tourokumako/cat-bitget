"""特徴量を3本に絞った状態で K=4 の ARI を確認する（凍結はしない）。

目的:
  特徴量 [ma50_dev, ma200_slope, di_diff] × K=4 で seed×20 学習し、
  ARI mean ≥ 0.9 を達成できるか検証する。

達成できた場合のみ次フェーズ（凍結 seed×50）に進む。
未達なら別の特徴量セットを検討する判断材料を出す。
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
OUT_PATH = REPO_ROOT / "results" / "phase3_hmm_ari_check.json"

K = 3
SEEDS = list(range(1, 21))
FREQ_5M_COUNT = 12
MINUTES_PER_STEP = FREQ_5M_COUNT * 5
DAILY_FACTOR = 1440 / MINUTES_PER_STEP

FEATURES = ["ma20_dev", "ma50_slope", "di_diff", "funding_24h_sum", "funding_zscore_30d"]
FUNDING_PATH = REPO_ROOT / "data" / "funding_rate_BTCUSDT_5y.csv"
ARI_THRESHOLD = 0.9


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
    return plus_di, minus_di, atr


def load_funding_rate() -> pd.Series:
    df = pd.read_csv(FUNDING_PATH)
    df["funding_time"] = pd.to_datetime(df["funding_time"], utc=True, format="ISO8601")
    s = df.set_index("funding_time")["funding_rate"]
    return s


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    period_str = f"{MINUTES_PER_STEP}min"
    h = df["high"].resample(period_str).max()
    l = df["low"].resample(period_str).min()
    c = df["close"].resample(period_str).last()
    ohlc = pd.DataFrame({"high": h, "low": l, "close": c}).dropna()
    if ohlc.index.tz is None:
        ohlc.index = ohlc.index.tz_localize("UTC")
    ma20 = ohlc["close"].rolling(20).mean()
    ma50 = ohlc["close"].rolling(50).mean()
    plus_di, minus_di, atr = compute_adx(ohlc["high"], ohlc["low"], ohlc["close"])

    # funding rate: 8h刻み → 1h forward fill, % スケール（×100）
    funding = load_funding_rate()
    funding_1h = funding.reindex(ohlc.index, method="ffill") * 100  # %

    # 加工特徴1: 24h(3 funding) 合計 → ロング過熱/ショート過熱 累積
    funding_24h_sum = funding_1h.rolling(24, min_periods=1).sum() / 3.0

    # 加工特徴2: 30日(720h) 移動平均からの zscore → 異常な過熱度
    funding_mean_30d = funding_1h.rolling(720, min_periods=24).mean()
    funding_std_30d  = funding_1h.rolling(720, min_periods=24).std()
    funding_zscore_30d = (funding_1h - funding_mean_30d) / funding_std_30d.replace(0, np.nan)

    feats = pd.DataFrame({
        "ma20_dev":          (ohlc["close"] - ma20) / ma20 * 100,
        "ma50_slope":        (ma50 - ma50.shift(10)) / ma50.shift(10) * 100,
        "di_diff":           plus_di - minus_di,
        "funding_24h_sum":   funding_24h_sum,
        "funding_zscore_30d": funding_zscore_30d,
        "ret":               ohlc["close"].pct_change() * 100,
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
            runs.append({"seed": s, "ll": ll, "states": states,
                         "min_d": min_d, "max_d": max_d, "pass_b": pass_b})
            mark = "✅" if pass_b else "  "
            print(f"  {mark} seed={s:3d}  ll={ll:>10.0f}  min={min_d:+.2f}  max={max_d:+.2f}")
        except Exception as e:
            print(f"  seed={s:3d}  FAIL: {e}")

    aris = []
    for i in range(len(runs)):
        for j in range(i + 1, len(runs)):
            aris.append(adjusted_rand_score(runs[i]["states"], runs[j]["states"]))
    aris_arr = np.array(aris)
    ari_mean = float(aris_arr.mean())
    ari_median = float(np.median(aris_arr))
    p25 = float(np.percentile(aris_arr, 25))
    p75 = float(np.percentile(aris_arr, 75))

    print(f"\n=== ARI 結果 ===")
    print(f"  mean   = {ari_mean:.3f}")
    print(f"  median = {ari_median:.3f}")
    print(f"  p25-p75 = {p25:.3f} - {p75:.3f}")
    print(f"  しきい値 {ARI_THRESHOLD}")

    n_pass_b = sum(1 for r in runs if r["pass_b"])
    print(f"\n  候補B合格: {n_pass_b}/{len(runs)}")

    if ari_mean >= ARI_THRESHOLD:
        print(f"\n✅ ARI ≥ {ARI_THRESHOLD}: 凍結フェーズに進める")
    else:
        print(f"\n❌ ARI < {ARI_THRESHOLD}: 凍結禁止。特徴量再検討が必要")

    out = {
        "features":     FEATURES,
        "K":            K,
        "n_samples":    len(X),
        "n_seeds":      len(SEEDS),
        "ari_mean":     ari_mean,
        "ari_median":   ari_median,
        "ari_p25":      p25,
        "ari_p75":      p75,
        "passed_threshold": ari_mean >= ARI_THRESHOLD,
        "threshold":    ARI_THRESHOLD,
        "n_candidate_B_pass": int(n_pass_b),
        "seed_results": [
            {"seed": r["seed"], "ll": r["ll"],
             "min_daily": r["min_d"], "max_daily": r["max_d"],
             "pass_b": r["pass_b"]}
            for r in runs
        ],
    }
    OUT_PATH.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\n→ {OUT_PATH}")


if __name__ == "__main__":
    main()
