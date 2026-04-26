"""HMM 系統探索: 特徴量セット × 粒度 × 状態数 = 27パターン総当たり。

特徴量セット:
  A=方向性強化  : ret, ma50_dev, ma200_slope, adx, di_diff
  B=ボラ強化    : atr_14_pct, atr_50_pct, bb_width_20, vol_7, vol_30
  C=複合         : ret, ma50_dev, adx, atr_14_pct, bb_width_20

粒度: 1h / 4h / 1d
状態数: 3 / 4 / 5

各パターン:
  - multi-init seed=1..5 で学習
  - 最良 LL のモデルを選択
  - 状態をリターン平均でランク → 最低/最高 state のリターン平均を記録
  - 評価軸: 分離度 = (max_state_daily_ret - min_state_daily_ret)
  - 候補B合格: 最低state daily < -0.82% AND 最高state daily > +1.22%

出力:
  results/phase3_grid_search_summary.csv
  results/phase3_grid_search_summary.json
"""
from __future__ import annotations

import json
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from sklearn.preprocessing import StandardScaler

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = REPO_ROOT / "data" / "BTCUSDT-5m-2020-01-01_2024-12-31_5y.csv"
OUT_CSV = REPO_ROOT / "results" / "phase3_grid_search_summary.csv"
OUT_JSON = REPO_ROOT / "results" / "phase3_grid_search_summary.json"

FREQ_TO_5M_COUNT = {"1h": 12, "4h": 48, "1d": 288}
N_STATES_LIST = [3, 4, 5]
SEEDS = list(range(1, 6))

DAILY_UP_THRESH = 1.22
DAILY_DOWN_THRESH = -0.82


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
    return adx, plus_di, minus_di, atr


def resample_ohlc(df: pd.DataFrame, k: int) -> pd.DataFrame:
    period_str = f"{k * 5}min"
    o = df["open"].resample(period_str).first()
    h = df["high"].resample(period_str).max()
    l = df["low"].resample(period_str).min()
    c = df["close"].resample(period_str).last()
    v = df["volume"].resample(period_str).sum()
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": v}).dropna()


def compute_all_features(ohlc: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=ohlc.index)
    c, h, l, v = ohlc["close"], ohlc["high"], ohlc["low"], ohlc["volume"]
    rets = c.pct_change() * 100
    out["ret"] = rets

    ma50 = c.rolling(50).mean()
    ma200 = c.rolling(200).mean()
    out["ma50_dev"] = (c - ma50) / ma50 * 100
    out["ma200_slope"] = (ma200 - ma200.shift(20)) / ma200.shift(20) * 100

    adx, plus_di, minus_di, atr = compute_adx(h, l, c, period=14)
    out["adx"] = adx
    out["di_diff"] = plus_di - minus_di

    out["atr_14_pct"] = atr / c * 100
    _, _, _, atr50 = compute_adx(h, l, c, period=50)
    out["atr_50_pct"] = atr50 / c * 100

    bb_mid = c.rolling(20).mean()
    bb_std = c.rolling(20).std()
    out["bb_width_20"] = (bb_mid + 2 * bb_std - (bb_mid - 2 * bb_std)) / bb_mid * 100

    out["vol_7"] = rets.rolling(7).std()
    out["vol_30"] = rets.rolling(30).std()
    return out


FEATURE_SETS = {
    "A_direction": ["ret", "ma50_dev", "ma200_slope", "adx", "di_diff"],
    "B_volatility": ["atr_14_pct", "atr_50_pct", "bb_width_20", "vol_7", "vol_30"],
    "C_combined": ["ret", "ma50_dev", "adx", "atr_14_pct", "bb_width_20"],
}


def fit_best(X_scaled: np.ndarray, n_states: int, seeds: list[int]):
    best = None
    for s in seeds:
        try:
            m = GaussianHMM(n_components=n_states, random_state=s,
                            n_iter=200, covariance_type="full")
            m.fit(X_scaled)
            ll = m.score(X_scaled)
            if best is None or ll > best["ll"]:
                best = {"seed": s, "model": m, "ll": ll,
                        "states": m.predict(X_scaled)}
        except Exception:
            continue
    return best


def evaluate_separation(states: np.ndarray, rets: np.ndarray, minutes_per_step: int) -> dict:
    """各状態のリターン平均 → 最低/最高を抽出 → daily換算で分離度を算出."""
    state_ret = {}
    for s in np.unique(states):
        r = rets[states == s]
        state_ret[int(s)] = {
            "mean_period_pct": float(r.mean()),
            "n": int(len(r)),
        }
    daily_factor = 1440 / minutes_per_step
    means = [v["mean_period_pct"] for v in state_ret.values()]
    min_v, max_v = min(means), max(means)
    min_daily = min_v * daily_factor
    max_daily = max_v * daily_factor
    pass_b = (min_daily < DAILY_DOWN_THRESH) and (max_daily > DAILY_UP_THRESH)
    return {
        "state_returns":  state_ret,
        "min_period_pct": float(min_v),
        "max_period_pct": float(max_v),
        "min_daily_pct":  float(min_daily),
        "max_daily_pct":  float(max_daily),
        "spread_daily":   float(max_daily - min_daily),
        "pass_candidate_B": bool(pass_b),
    }


def main() -> None:
    df = pd.read_csv(RAW_PATH)
    df["ts"] = pd.to_datetime(df["timestamp"])
    for c in ("open", "high", "low", "close", "volume"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.sort_values("ts").dropna(subset=["close"]).set_index("ts")

    feature_cache = {}
    for freq, k in FREQ_TO_5M_COUNT.items():
        ohlc = resample_ohlc(df, k)
        feature_cache[freq] = (k * 5, compute_all_features(ohlc).dropna())
        print(f"[{freq}] {len(feature_cache[freq][1]):>7,} samples")

    rows = []
    print("\n--- 27パターン探索 ---")
    print(f"{'feat':<14} {'freq':<5} {'K':<3} {'pass':<5} "
          f"{'min_d%':>9} {'max_d%':>9} {'spread':>8} {'ll':>14}")
    print("-" * 80)

    for feat_name, freq, n_states in product(FEATURE_SETS, FREQ_TO_5M_COUNT, N_STATES_LIST):
        cols = FEATURE_SETS[feat_name]
        minutes_per_step, all_feats = feature_cache[freq]
        sub = all_feats[cols + (["ret"] if "ret" not in cols else [])].dropna()
        X = sub[cols].values
        rets = sub["ret"].values

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        best = fit_best(X_scaled, n_states, SEEDS)
        if best is None:
            print(f"{feat_name:<14} {freq:<5} {n_states:<3}  FAIL")
            continue

        sep = evaluate_separation(best["states"], rets, minutes_per_step)
        rows.append({
            "feature_set": feat_name,
            "freq":        freq,
            "n_states":    n_states,
            "n_samples":   int(len(X_scaled)),
            "best_seed":   int(best["seed"]),
            "ll":          float(best["ll"]),
            **sep,
        })
        flag = "✅" if sep["pass_candidate_B"] else " "
        print(f"{feat_name:<14} {freq:<5} {n_states:<3} {flag:<5} "
              f"{sep['min_daily_pct']:>9.3f} {sep['max_daily_pct']:>9.3f} "
              f"{sep['spread_daily']:>8.3f} {best['ll']:>14.0f}")

    print("-" * 80)

    # 上位5件: spread_daily 降順
    top = sorted(rows, key=lambda r: r["spread_daily"], reverse=True)[:5]
    print("\n=== 分離度 spread_daily Top 5 ===")
    for r in top:
        flag = "✅" if r["pass_candidate_B"] else "❌"
        print(f"  {flag} {r['feature_set']:<14} {r['freq']:<3} K={r['n_states']}  "
              f"min={r['min_daily_pct']:+.2f}%  max={r['max_daily_pct']:+.2f}%  "
              f"spread={r['spread_daily']:.2f}%")

    passed = [r for r in rows if r["pass_candidate_B"]]
    print(f"\n候補B合格: {len(passed)}/{len(rows)}")
    if passed:
        print("\n=== 候補B合格パターン（採択候補） ===")
        for r in sorted(passed, key=lambda r: r["spread_daily"], reverse=True):
            print(f"  ✅ {r['feature_set']:<14} {r['freq']:<3} K={r['n_states']}  "
                  f"spread={r['spread_daily']:.2f}%  seed={r['best_seed']}")

    # 出力
    pd.DataFrame([{
        "feature_set": r["feature_set"], "freq": r["freq"], "n_states": r["n_states"],
        "n_samples": r["n_samples"], "best_seed": r["best_seed"], "ll": r["ll"],
        "min_daily_pct": r["min_daily_pct"], "max_daily_pct": r["max_daily_pct"],
        "spread_daily": r["spread_daily"], "pass_candidate_B": r["pass_candidate_B"],
    } for r in rows]).to_csv(OUT_CSV, index=False)
    OUT_JSON.write_text(json.dumps(rows, indent=2, ensure_ascii=False, default=str))
    print(f"\n→ {OUT_CSV}")
    print(f"→ {OUT_JSON}")


if __name__ == "__main__":
    main()
