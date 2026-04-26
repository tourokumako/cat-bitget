"""Mom 1h(10) 単体ルール判定 — ベースライン

入力: BTCUSDT-5m-2020-01-01_2024-12-31_5y.csv (5m足5年分)
処理: 5m → 1h リサンプリング → Mom%(10) 算出 → 閾値判定

判定ルール:
  mom_pct = (close - close.shift(10)) / close.shift(10) * 100
  slope   = mom_pct - mom_pct.shift(1)
  if mom_pct > +THR and slope > 0: UP
  elif mom_pct < -THR and slope < 0: DOWN
  else: RANGE

評価:
  候補B: UP > +1.22%/d, DOWN < -0.82%/d, RANGE |0.34%|内
  状態継続中央値 3-30日

CLI:
  python scripts/regime_mom_1h.py            # デフォルト閾値 0.5%
  python scripts/regime_mom_1h.py --thr 0.8  # 閾値変更
  python scripts/regime_mom_1h.py --hist     # ヒストグラム/パーセンタイルのみ
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = REPO_ROOT / "data" / "BTCUSDT-5m-2020-01-01_2024-12-31_5y.csv"

OUT_STATES = REPO_ROOT / "results" / "regime_mom_1h_states.csv"
OUT_SUMMARY = REPO_ROOT / "results" / "regime_mom_1h_summary.json"

MOM_PERIOD = 10
HOURS_PER_DAY = 24


def load_1h_ohlc() -> pd.DataFrame:
    df = pd.read_csv(RAW_PATH)
    df["ts"] = pd.to_datetime(df["timestamp"])
    for c in ("open", "high", "low", "close"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.sort_values("ts").dropna(subset=["close"]).set_index("ts")

    h = df["high"].resample("60min").max()
    l = df["low"].resample("60min").min()
    c = df["close"].resample("60min").last()
    o = df["open"].resample("60min").first()
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c}).dropna()


def compute_mom(ohlc: pd.DataFrame) -> pd.DataFrame:
    close = ohlc["close"]
    mom_abs = close - close.shift(MOM_PERIOD)
    mom_pct = mom_abs / close.shift(MOM_PERIOD) * 100
    slope = mom_pct - mom_pct.shift(1)
    ret_1h = close.pct_change() * 100
    return pd.DataFrame({
        "close":   close,
        "mom_abs": mom_abs,
        "mom_pct": mom_pct,
        "slope":   slope,
        "ret_1h":  ret_1h,
    }).dropna()


def print_histogram(feats: pd.DataFrame) -> None:
    m = feats["mom_pct"]
    print("\n== Mom%(10) 1h 分布 (5年・43k+本) ==")
    print(f"  count   = {len(m):,}")
    print(f"  mean    = {m.mean():+.4f}%")
    print(f"  std     = {m.std():.4f}%")
    print(f"  min     = {m.min():+.4f}%")
    print(f"  max     = {m.max():+.4f}%")
    print()
    print("  パーセンタイル:")
    for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]:
        print(f"    {p:>3}% = {np.percentile(m, p):+.4f}%")
    print()
    print("  閾値別 RANGE 比率（|mom_pct| < THR の割合）:")
    for thr in [0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0]:
        rng = float((m.abs() < thr).mean() * 100)
        up_strict = float(((m > thr) & (feats["slope"] > 0)).mean() * 100)
        dn_strict = float(((m < -thr) & (feats["slope"] < 0)).mean() * 100)
        print(f"    THR=±{thr:>4.2f}%  RANGE={rng:5.1f}%  "
              f"UP(slope+)={up_strict:5.1f}%  DOWN(slope-)={dn_strict:5.1f}%  "
              f"NEUTRAL残={100-rng-up_strict-dn_strict:5.1f}%")


def classify(feats: pd.DataFrame, thr: float) -> pd.Series:
    m = feats["mom_pct"]
    s = feats["slope"]
    state = pd.Series("RANGE", index=feats.index)
    state[(m > thr) & (s > 0)] = "UP"
    state[(m < -thr) & (s < 0)] = "DOWN"
    return state


def evaluate(feats: pd.DataFrame, state: pd.Series, thr: float) -> dict:
    feats = feats.copy()
    feats["state"] = state
    daily = feats[["ret_1h", "state"]].copy()
    daily["date"] = daily.index.normalize()
    daily_state = daily.groupby("date")["state"].agg(
        lambda s: s.value_counts().idxmax())
    daily_ret = daily.groupby("date")["ret_1h"].sum()
    by_state = pd.DataFrame({"state": daily_state, "ret_d": daily_ret}).dropna()

    summary = {"thr_pct": thr, "n_hours": int(len(feats)), "n_days": int(len(by_state))}
    state_stats = {}
    for s in ["UP", "RANGE", "DOWN"]:
        sub = by_state[by_state["state"] == s]["ret_d"]
        state_stats[s] = {
            "n_days":    int(len(sub)),
            "share_pct": float(len(sub) / len(by_state) * 100) if len(by_state) else 0,
            "mean_d_pct": float(sub.mean()) if len(sub) else 0,
            "median_d_pct": float(sub.median()) if len(sub) else 0,
        }
    summary["state_daily"] = state_stats

    runs = []
    cur = None
    cnt = 0
    for s in state.values:
        if s == cur:
            cnt += 1
        else:
            if cur is not None:
                runs.append((cur, cnt))
            cur = s
            cnt = 1
    if cur is not None:
        runs.append((cur, cnt))
    runs_h = pd.DataFrame(runs, columns=["state", "len_h"])
    cont = {}
    for s in ["UP", "RANGE", "DOWN"]:
        sub = runs_h[runs_h["state"] == s]["len_h"]
        cont[s] = {
            "n_runs": int(len(sub)),
            "median_hours": float(sub.median()) if len(sub) else 0,
            "median_days": float(sub.median() / HOURS_PER_DAY) if len(sub) else 0,
            "max_hours": int(sub.max()) if len(sub) else 0,
        }
    summary["continuity"] = cont

    pb_up = state_stats["UP"]["mean_d_pct"] > 1.22
    pb_dn = state_stats["DOWN"]["mean_d_pct"] < -0.82
    pb_rg = abs(state_stats["RANGE"]["mean_d_pct"]) < 0.34
    summary["candidate_b"] = {
        "UP_pass":    bool(pb_up),
        "DOWN_pass":  bool(pb_dn),
        "RANGE_pass": bool(pb_rg),
        "all_pass":   bool(pb_up and pb_dn and pb_rg),
    }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--thr", type=float, default=0.5,
                        help="判定閾値（mom_pct の絶対値%・default 0.5）")
    parser.add_argument("--hist", action="store_true",
                        help="ヒストグラム/パーセンタイルのみ表示して終了")
    args = parser.parse_args()

    print(f"== regime_mom_1h.py ==")
    print(f"  入力: {RAW_PATH.name}")
    ohlc = load_1h_ohlc()
    print(f"  1h足: {len(ohlc):,} 本 ({ohlc.index[0]} 〜 {ohlc.index[-1]})")

    feats = compute_mom(ohlc)
    print(f"  Mom%(10) 算出後: {len(feats):,} 本")

    print_histogram(feats)
    if args.hist:
        return

    print(f"\n== 判定実行 (THR=±{args.thr}%) ==")
    state = classify(feats, args.thr)
    summary = evaluate(feats, state, args.thr)

    sd = summary["state_daily"]
    cb = summary["candidate_b"]
    cn = summary["continuity"]
    print(f"\n  状態分布 (日単位・優勢状態):")
    for s in ["UP", "RANGE", "DOWN"]:
        st = sd[s]
        print(f"    {s:<5}  n={st['n_days']:>4} ({st['share_pct']:>5.1f}%)  "
              f"mean={st['mean_d_pct']:+.3f}%/d  median={st['median_d_pct']:+.3f}%/d")
    print(f"\n  継続中央値:")
    for s in ["UP", "RANGE", "DOWN"]:
        c = cn[s]
        print(f"    {s:<5}  n_runs={c['n_runs']:>5}  "
              f"median={c['median_hours']:>5.1f}h ({c['median_days']:.2f}d)  "
              f"max={c['max_hours']:>4}h")
    print(f"\n  候補B判定:")
    print(f"    UP    >+1.22%/d : {sd['UP']['mean_d_pct']:+.3f} → {'✅' if cb['UP_pass'] else '❌'}")
    print(f"    DOWN  <-0.82%/d : {sd['DOWN']['mean_d_pct']:+.3f} → {'✅' if cb['DOWN_pass'] else '❌'}")
    print(f"    RANGE  |0.34%| : {sd['RANGE']['mean_d_pct']:+.3f} → {'✅' if cb['RANGE_pass'] else '❌'}")
    print(f"    総合: {'✅ 合格' if cb['all_pass'] else '❌ 不合格'}")

    out_df = pd.DataFrame({
        "ts":      feats.index,
        "close":   feats["close"].values,
        "mom_pct": feats["mom_pct"].values,
        "slope":   feats["slope"].values,
        "state":   state.values,
    })
    OUT_STATES.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT_STATES, index=False)
    OUT_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"\n  → {OUT_STATES.relative_to(REPO_ROOT)}")
    print(f"  → {OUT_SUMMARY.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
