"""
check_hourly_regime.py — 1時間足ベースの regime 判定を試作・既存日足版と比較

既存ロジック (_build_regime_map @ runner/replay_csv.py:813) を 1h足ベースに置き換えた
試作版。副作用なし（dashboard/data 等は更新しない）。

確認ポイント:
  1. 2025-04 の +10.6% 上昇月で UP 判定が出るか（日足版は UP=0日）
  2. 2026-03 の +3.8% 上昇月で DT → UP に切り替わるか
  3. ヒステリシス（連続12h 同regime でコミット）でフリップが日次相当に収まるか
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pandas as pd
import ta

REPO = Path(__file__).resolve().parent.parent
OHLCV = REPO / "data" / "BTCUSDT-5m-2025-04-01_03-31_365d.csv"
EXISTING_TIMELINE = REPO / "dashboard" / "data" / "regime_timeline.json"

MA_PERIOD = 70
SLOPE_LAG = 5
ADX_PERIOD = 14
ADX_RANGE_THRESH = 20
HYST_CANDIDATES = [12, 18, 24, 36, 48]   # スイープ対象


def classify(row) -> str:
    if any(pd.isna(v) for v in [row.ma70, row.ma70_slope, row.adx, row.close]):
        return "unknown"
    if row.adx < ADX_RANGE_THRESH:
        return "range"
    if row.ma70_slope > 0 and row.close > row.ma70:
        return "uptrend"
    if row.ma70_slope < 0 and row.close < row.ma70:
        return "downtrend"
    return "mixed"


def apply_hysteresis(raw: pd.Series, n: int) -> pd.Series:
    """連続n本 同regime ラベルが続いたらコミット、それ以外は前期間継続。"""
    out = raw.copy().to_list()
    raw_list = raw.to_list()
    last_committed = "unknown"
    for i in range(len(raw_list)):
        if i < n - 1:
            out[i] = raw_list[i]
            last_committed = raw_list[i]
            continue
        window = raw_list[i - n + 1 : i + 1]
        if len(set(window)) == 1 and window[0] != "unknown":
            last_committed = window[0]
            out[i] = last_committed
        else:
            out[i] = last_committed
    return pd.Series(out, index=raw.index)


def count_mismatches(hourly: pd.DataFrame) -> int:
    """月別「明らかな騰落と regime が逆」の件数を返す。"""
    mm = 0
    hourly = hourly.copy()
    hourly["month"] = hourly.index.strftime("%Y-%m")
    for m in sorted(hourly["month"].unique()):
        sub = hourly[hourly["month"] == m]
        if len(sub) < 2:
            continue
        rg_count = Counter(sub["regime"])
        top = rg_count.most_common(1)[0][0]
        p0, p1 = sub["close"].iloc[0], sub["close"].iloc[-1]
        ret = (p1 / p0 - 1) * 100
        if top == "uptrend" and ret < -2: mm += 1
        elif top == "downtrend" and ret > 2: mm += 1
        elif top == "range" and abs(ret) > 8: mm += 1
    return mm


def daily_flips(hourly: pd.DataFrame) -> tuple[int, int]:
    """日内最頻regime ベースの日次切替回数 + 時間粒度の切替回数。"""
    daily = hourly.groupby(hourly.index.normalize())["regime"].agg(
        lambda s: s.value_counts().index[0]
    ).tolist()
    flips_d = sum(1 for i in range(1, len(daily)) if daily[i] != daily[i - 1])
    rl = hourly["regime"].tolist()
    flips_h = sum(1 for i in range(1, len(rl)) if rl[i] != rl[i - 1])
    return flips_d, flips_h


def per_month_top(hourly: pd.DataFrame) -> dict:
    """月別の支配 regime + ret 文字列を返す（表示用）。"""
    out = {}
    h2 = hourly.copy()
    h2["month"] = h2.index.strftime("%Y-%m")
    for m in sorted(h2["month"].unique()):
        sub = h2[h2["month"] == m]
        if len(sub) < 2: continue
        rg_count = Counter(sub["regime"])
        top = rg_count.most_common(1)[0][0]
        p0, p1 = sub["close"].iloc[0], sub["close"].iloc[-1]
        ret = (p1 / p0 - 1) * 100
        out[m] = (top, ret)
    return out


def main() -> None:
    df = pd.read_csv(OHLCV)
    df["ts"] = pd.to_datetime(df["timestamp"])
    df = df.set_index("ts").sort_index()

    hourly = df.resample("1h").agg({"close": "last", "high": "max", "low": "min"}).dropna()
    hourly["ma70"] = hourly["close"].rolling(MA_PERIOD, min_periods=MA_PERIOD).mean()
    hourly["ma70_slope"] = hourly["ma70"].diff(SLOPE_LAG)
    adx = ta.trend.ADXIndicator(hourly["high"], hourly["low"], hourly["close"], window=ADX_PERIOD)
    hourly["adx"] = adx.adx()
    hourly["regime_raw"] = hourly.apply(classify, axis=1)

    # 既存日足の参考データ
    old_top = {}
    if EXISTING_TIMELINE.exists():
        existing = json.load(open(EXISTING_TIMELINE))["days"]
        from collections import defaultdict
        bym = defaultdict(list)
        for d in existing:
            bym[d["date"][:7]].append(d["regime"])
        for m, vs in bym.items():
            old_top[m] = Counter(vs).most_common(1)[0][0]

    # --- スイープ実行
    print("=" * 110)
    print(f"{'HYST(h)':<8} {'mismatches':<11} {'日次切替':<9} {'h切替':<7} {'分布(日内最頻ベース)':<60}")
    print("-" * 110)
    results = {}
    for h in HYST_CANDIDATES:
        col = f"regime_h{h}"
        hourly[col] = apply_hysteresis(hourly["regime_raw"], h)
        tmp = hourly.rename(columns={col: "regime"})
        mm = count_mismatches(tmp)
        flips_d, flips_h = daily_flips(tmp)
        # 分布
        daily_top = tmp.groupby(tmp.index.normalize())["regime"].agg(
            lambda s: s.value_counts().index[0]
        )
        dist = Counter(daily_top)
        dist_s = " ".join(f"{k[:2].upper()}{v}" for k, v in sorted(dist.items(), key=lambda x: -x[1]))
        results[h] = (mm, flips_d, flips_h, dict(dist), tmp)
        print(f"{h:<8} {mm:<11} {flips_d:<9} {flips_h:<7} {dist_s}")

    print()
    print(f"※ 旧（日足）の参考値: mismatches=2, 日次切替=24, 分布=DO143 RA127 UP66 MI29")

    # --- 月別の比較表（推奨候補1つを詳細表示）
    best = min(results.items(), key=lambda kv: (kv[1][0], abs(kv[1][1] - 24)))
    h_best, (mm, fd, fh, dist, tmp) = best
    print()
    print("=" * 110)
    print(f"【推奨候補: ヒステリシス {h_best}h】月別 騰落率 vs 支配regime（時間単位）")
    print(f"{'month':<8} {'ret':>7}  {'旧支配':<10} {'新支配':<10}  時間内訳")
    print("-" * 90)
    h2 = tmp.copy()
    h2["month"] = h2.index.strftime("%Y-%m")
    for m in sorted(h2["month"].unique()):
        sub = h2[h2["month"] == m]
        if len(sub) < 2: continue
        rg_count = Counter(sub["regime"])
        top = rg_count.most_common(1)[0][0]
        p0, p1 = sub["close"].iloc[0], sub["close"].iloc[-1]
        ret = (p1 / p0 - 1) * 100
        rg_str = " ".join(f"{k[:2].upper()}{v}h" for k, v in sorted(rg_count.items(), key=lambda x: -x[1]))
        flag = ""
        if top == "uptrend" and ret < -2: flag = " ←MISMATCH"
        elif top == "downtrend" and ret > 2: flag = " ←MISMATCH"
        elif top == "range" and abs(ret) > 8: flag = " ←MISMATCH"
        print(f"{m:<8} {ret:>+6.1f}%  {old_top.get(m,'-'):<10} {top:<10}  {rg_str}{flag}")


if __name__ == "__main__":
    main()
