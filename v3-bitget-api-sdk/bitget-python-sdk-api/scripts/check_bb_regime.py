"""
check_bb_regime.py — BB middle slope + BB幅 を組み込んだ regime 判定の検証

判定ロジック（案C）:
  ① BB幅収縮 (< BB_NARROW_PCT) → range（最優先・真のRG）
  ② MA70 slope と BB middle slope が同方向 + close vs MA70 一致 → trend
  ③ ADX < ADX_RG → range（補助）
  ④ 方向不一致 → mixed

副作用なし。dashboard/data 等は触らない。
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pandas as pd
import ta

REPO = Path(__file__).resolve().parent.parent
OHLCV = REPO / "data" / "BTCUSDT-5m-2025-04-01_03-31_365d.csv"
DAILY_WARMUP = REPO / "data" / "BTCUSDT-1d-2024-09-01_04-15_227d.csv"  # _build_regime_map と同じ warmup
EXISTING_TIMELINE = REPO / "dashboard" / "data" / "regime_timeline.json"

# パラメータ（既存採用値ベース）
MA_PERIOD = 70
SLOPE_LAG = 5
BB_PERIOD = 20
BB_STDEV = 2.0
ADX_PERIOD = 14
ADX_RANGE_THRESH = 20

# BB 関連のスイープ候補
BB_NARROW_PCT_CANDIDATES = [3.0, 4.0, 5.0, 6.0, 8.0]   # 価格に対する BB幅 %
DIVERGE_THRESH_CANDIDATES = [0, 100, 300, 500, 1000]   # bb_mid_slope の逆方向 → MIXED 判定閾値（USD）
BB_NARROW_FIXED = 6.0                                  # ロジック②検証時に固定する値


def daily_resample(ohlcv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(ohlcv_path)
    df["ts"] = pd.to_datetime(df["timestamp"])
    df = df.set_index("ts").sort_index()
    daily = df.resample("D").agg({"close": "last", "high": "max", "low": "min"}).dropna()

    # warmup 結合（既存 _build_regime_map と同じ流儀）
    if DAILY_WARMUP.exists():
        dw = pd.read_csv(DAILY_WARMUP)
        dw["ts"] = pd.to_datetime(dw["timestamp"])
        for c in ("close", "high", "low"):
            dw[c] = pd.to_numeric(dw[c], errors="coerce")
        dw = dw.set_index("ts").sort_index()
        combined = pd.concat([dw[["close", "high", "low"]], daily[["close", "high", "low"]]])
    else:
        combined = daily

    combined = combined[~combined.index.duplicated(keep="last")].sort_index()
    for c in ("close", "high", "low"):
        combined[c] = pd.to_numeric(combined[c], errors="coerce")
    return combined, daily.index.min()


def add_indicators(combined: pd.DataFrame) -> pd.DataFrame:
    combined["ma70"] = combined["close"].rolling(MA_PERIOD, min_periods=MA_PERIOD).mean()
    combined["ma70_slope"] = combined["ma70"].diff(SLOPE_LAG)

    bb = ta.volatility.BollingerBands(combined["close"], window=BB_PERIOD, window_dev=BB_STDEV)
    combined["bb_upper"] = bb.bollinger_hband()
    combined["bb_lower"] = bb.bollinger_lband()
    combined["bb_mid"] = bb.bollinger_mavg()
    combined["bb_mid_slope"] = combined["bb_mid"].diff(SLOPE_LAG)
    combined["bb_width"] = combined["bb_upper"] - combined["bb_lower"]
    combined["bb_width_pct"] = combined["bb_width"] / combined["close"] * 100  # 価格対比 %

    adx_obj = ta.trend.ADXIndicator(combined["high"], combined["low"], combined["close"], window=ADX_PERIOD)
    combined["adx"] = adx_obj.adx()
    return combined


def make_classify(bb_narrow_pct: float):
    """ロジック①: BB幅収縮 → RG / MA70+BB両合意 → trend / 不一致 → mixed"""
    def _classify(row):
        keys = ["ma70", "ma70_slope", "bb_mid_slope", "bb_width_pct", "adx", "close"]
        if any(pd.isna(row[k]) for k in keys):
            return "unknown"
        if row["bb_width_pct"] < bb_narrow_pct:
            return "range"
        ma_up = row["ma70_slope"] > 0 and row["close"] > row["ma70"]
        ma_dn = row["ma70_slope"] < 0 and row["close"] < row["ma70"]
        bb_up = row["bb_mid_slope"] > 0
        bb_dn = row["bb_mid_slope"] < 0
        if ma_up and bb_up:
            return "uptrend"
        if ma_dn and bb_dn:
            return "downtrend"
        if row["adx"] < ADX_RANGE_THRESH:
            return "range"
        return "mixed"
    return _classify


def make_classify_v3(bb_narrow_pct: float, trend_thresh: float, range_thresh: float):
    """ロジック③: スコアリング型複合判定。

    score = (close vs MA70: ±2) + (MA70 slope: ±1) + (BB middle slope: ±1)
            × (ADX≥30 なら 1.5倍 boost)
    BB幅<narrow & ADX<20 → range (最優先)
    score ≥  trend_thresh → uptrend
    score ≤ -trend_thresh → downtrend
    abs(score) ≤ range_thresh → range
    それ以外 → mixed
    """
    def _classify(row):
        keys = ["ma70", "ma70_slope", "bb_mid_slope", "bb_width_pct", "adx", "close"]
        if any(pd.isna(row[k]) for k in keys):
            return "unknown"

        # 真のRG（最優先・ボラ収縮+ADX弱）
        if row["adx"] < ADX_RANGE_THRESH and row["bb_width_pct"] < bb_narrow_pct:
            return "range"

        score = 0.0
        # 価格と MA70 の位置（最重要・±2）
        if row["close"] > row["ma70"]:
            score += 2
        elif row["close"] < row["ma70"]:
            score -= 2
        # MA70 slope（±1）
        if row["ma70_slope"] > 0:
            score += 1
        elif row["ma70_slope"] < 0:
            score -= 1
        # BB middle slope（±1）
        if row["bb_mid_slope"] > 0:
            score += 1
        elif row["bb_mid_slope"] < 0:
            score -= 1
        # ADX強で確信度ブースト
        if row["adx"] >= 30:
            score *= 1.5

        if score >= trend_thresh:
            return "uptrend"
        if score <= -trend_thresh:
            return "downtrend"
        if abs(score) <= range_thresh:
            return "range"
        return "mixed"
    return _classify


def make_classify_v2(bb_narrow_pct: float, diverge_thresh: float):
    """ロジック②: MA70 主導・BB が「明確に逆方向」のときのみ MIXED 認定（MIXED 抑制版）"""
    def _classify(row):
        keys = ["ma70", "ma70_slope", "bb_mid_slope", "bb_width_pct", "adx", "close"]
        if any(pd.isna(row[k]) for k in keys):
            return "unknown"

        ma_up = row["ma70_slope"] > 0 and row["close"] > row["ma70"]
        ma_dn = row["ma70_slope"] < 0 and row["close"] < row["ma70"]

        if ma_up:
            return "mixed" if row["bb_mid_slope"] < -diverge_thresh else "uptrend"
        if ma_dn:
            return "mixed" if row["bb_mid_slope"] > diverge_thresh else "downtrend"

        # MA70 中立 → BB幅狭 + ADX弱 で RG、それ以外 mixed
        if row["adx"] < ADX_RANGE_THRESH and row["bb_width_pct"] < bb_narrow_pct:
            return "range"
        return "mixed"
    return _classify


def evaluate(daily_df: pd.DataFrame, target_start) -> tuple[int, int, dict, dict]:
    """月別ミスマッチ・切替回数・分布・月別表を返す。"""
    df = daily_df[daily_df.index >= target_start].copy()
    df["month"] = df.index.strftime("%Y-%m")

    # mismatch 数
    mm = 0
    monthly = {}
    for m, sub in df.groupby("month"):
        if len(sub) < 2:
            continue
        rg_count = Counter(sub["regime"])
        top = rg_count.most_common(1)[0][0]
        p0, p1 = sub["close"].iloc[0], sub["close"].iloc[-1]
        ret = (p1 / p0 - 1) * 100
        is_mm = ((top == "uptrend" and ret < -2) or
                 (top == "downtrend" and ret > 2) or
                 (top == "range" and abs(ret) > 8))
        if is_mm:
            mm += 1
        monthly[m] = (top, ret, dict(rg_count), is_mm)

    # 日次切替回数
    rg_list = df["regime"].tolist()
    flips = sum(1 for i in range(1, len(rg_list)) if rg_list[i] != rg_list[i - 1])

    # 分布
    dist = dict(Counter(rg_list))

    return mm, flips, dist, monthly


def main() -> None:
    combined, target_start = daily_resample(OHLCV)
    combined = add_indicators(combined)

    # 既存日足版の参考分布
    if EXISTING_TIMELINE.exists():
        existing = json.load(open(EXISTING_TIMELINE))["days"]
        old_dist = dict(Counter(d["regime"] for d in existing))
        from collections import defaultdict
        old_top = {}
        bym = defaultdict(list)
        for d in existing:
            bym[d["date"][:7]].append(d["regime"])
        for m, vs in bym.items():
            old_top[m] = Counter(vs).most_common(1)[0][0]
    else:
        old_dist = {}
        old_top = {}

    print(f"※ 旧（日足現行・参考）分布: {old_dist}")
    print(f"※ パラメータ: MA={MA_PERIOD} slope_lag={SLOPE_LAG} BB={BB_PERIOD},{BB_STDEV} ADX={ADX_PERIOD},<{ADX_RANGE_THRESH}")

    # ロジック①: BB両合意要件あり版
    print()
    print("=" * 110)
    print("【ロジック①: BB幅収縮→RG / MA70+BB両合意→trend / 不一致→mixed】")
    print(f"{'BB_narrow_pct':<14} {'mismatches':<11} {'日次切替':<9} {'分布':<60}")
    print("-" * 110)
    for narrow in BB_NARROW_PCT_CANDIDATES:
        df = combined.copy()
        df["regime"] = df.apply(make_classify(narrow), axis=1)
        mm, flips, dist, _ = evaluate(df, target_start)
        dist_s = " ".join(f"{k[:2].upper()}{v}" for k, v in sorted(dist.items(), key=lambda x: -x[1]))
        print(f"narrow<{narrow:>5.1f}%   {mm:<11} {flips:<9} {dist_s}")

    # ロジック②: MIXED 抑制版（DIVERGE_THRESH スイープ）
    print()
    print("=" * 110)
    print(f"【ロジック②: MA70主導・BB逆方向のみMIXED（MIXED抑制版）/ BB_narrow={BB_NARROW_FIXED}% 固定】")
    print(f"{'DIVERGE':<9} {'mismatches':<11} {'日次切替':<9} {'分布':<60}")
    print("-" * 110)
    results_v2 = {}
    for div in DIVERGE_THRESH_CANDIDATES:
        df = combined.copy()
        df["regime"] = df.apply(make_classify_v2(BB_NARROW_FIXED, div), axis=1)
        mm, flips, dist, monthly = evaluate(df, target_start)
        dist_s = " ".join(f"{k[:2].upper()}{v}" for k, v in sorted(dist.items(), key=lambda x: -x[1]))
        results_v2[div] = (mm, flips, dist, monthly)
        print(f"div={div:<5} {mm:<11} {flips:<9} {dist_s}")

    # ロジック③: スコアリング型
    print()
    print("=" * 110)
    print(f"【ロジック③: スコアリング型（close±2 + MA70slope±1 + BBslope±1 × ADX>=30 boost1.5）】")
    print(f"{'閾値(T,R)':<13} {'mismatches':<11} {'日次切替':<9} {'分布':<60}")
    print("-" * 110)
    score_candidates = [(3.0, 1.0), (3.0, 2.0), (4.0, 1.0), (4.0, 2.0), (4.5, 1.5), (5.0, 2.0)]
    results_v3 = {}
    for T, R in score_candidates:
        df = combined.copy()
        df["regime"] = df.apply(make_classify_v3(BB_NARROW_FIXED, T, R), axis=1)
        mm, flips, dist, monthly = evaluate(df, target_start)
        dist_s = " ".join(f"{k[:2].upper()}{v}" for k, v in sorted(dist.items(), key=lambda x: -x[1]))
        results_v3[(T, R)] = (mm, flips, dist, monthly)
        print(f"T={T} R={R:<5} {mm:<11} {flips:<9} {dist_s}")

    # 推奨: mismatches最少 + MIXED 抑制 + 切替を許容範囲に
    def score_v3(kv):
        _, (mm, flips, dist, _) = kv
        mi = dist.get("mixed", 0)
        return (mm, mi, abs(flips - 30))

    best = min(results_v3.items(), key=score_v3)
    (T_best, R_best), (mm, fl, dist, monthly) = best

    print()
    print("=" * 110)
    print(f"【ロジック③ 推奨: trend_thresh={T_best} range_thresh={R_best}】月別比較表")
    print(f"{'month':<8} {'ret':>7}  {'旧支配':<10} {'新支配':<10}  rg内訳   {'MM?':<5}")
    print("-" * 90)
    for m in sorted(monthly.keys()):
        top, ret, rg_count, is_mm = monthly[m]
        rg_str = " ".join(f"{k[:2].upper()}{v}" for k, v in sorted(rg_count.items(), key=lambda x: -x[1]))
        flag = "←MM" if is_mm else ""
        print(f"{m:<8} {ret:>+6.1f}%  {old_top.get(m,'-'):<10} {top:<10}  {rg_str:<25} {flag}")


if __name__ == "__main__":
    main()
