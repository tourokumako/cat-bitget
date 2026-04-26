"""Phase 0: BTC 日次リターン分布の統計算出 → 判定基準のデータ駆動決定。

入力: data/BTCUSDT-5m-2020-01-01_2024-12-31_5y.csv（5年分5m足）
出力: 標準出力 + results/phase0_return_distribution.json

目的:
  「UPTREND/DOWNTREND/RANGE」の判定基準を、適当な数字ではなく
  実データの分布から決める。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "data" / "BTCUSDT-5m-2020-01-01_2024-12-31_5y.csv"
OUT_PATH = REPO_ROOT / "results" / "phase0_return_distribution.json"


def main() -> None:
    if not CSV_PATH.exists():
        # 5年データ取得失敗時は365日CSVで代替
        alt = REPO_ROOT / "data" / "BTCUSDT-5m-2025-04-01_03-31_365d.csv"
        if alt.exists():
            print(f"[fallback] 5年CSVなし → 365日CSVで代替算出: {alt.name}")
            csv_path = alt
        else:
            raise SystemExit(f"CSV not found")
    else:
        csv_path = CSV_PATH

    print(f"[phase0] 読み込み: {csv_path.name}")
    df = pd.read_csv(csv_path)
    df["ts"] = pd.to_datetime(df["timestamp"])
    for c in ("open", "high", "low", "close"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.set_index("ts").sort_index()

    daily = df.resample("D").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    print(f"  日足: {len(daily)} 日 ({daily.index.min().date()} 〜 {daily.index.max().date()})")

    # 日次リターン（log return ではなく単純リターン: (close[t] - close[t-1]) / close[t-1] * 100）
    daily["ret_1d"] = daily["close"].pct_change() * 100
    rets = daily["ret_1d"].dropna()

    print(f"\n=== 日次リターン分布（5年分・{len(rets)} 日） ===")
    print(f"  平均（mean）       : {rets.mean():+.3f}%")
    print(f"  中央値（median）   : {rets.median():+.3f}%")
    print(f"  標準偏差（std）    : {rets.std():.3f}%")
    print(f"  最小（min）        : {rets.min():+.2f}%")
    print(f"  最大（max）        : {rets.max():+.2f}%")
    print()
    print(f"  パーセンタイル:")
    for p in (5, 10, 25, 33, 50, 67, 75, 90, 95):
        v = rets.quantile(p / 100)
        print(f"    {p:>3d}% : {v:+7.3f}%")

    # 合格基準のデータ駆動候補
    print(f"\n=== 判定基準の候補（データ駆動） ===")

    # 候補A: パーセンタイルベース（上位33% / 下位33% / 中央34%）
    upper_33 = rets.quantile(2/3)
    lower_33 = rets.quantile(1/3)
    print(f"\n  [候補A: 三分位ベース]")
    print(f"    UPTREND判定時 平均 > {upper_33:+.3f}% (上位33%閾値)")
    print(f"    DOWNTREND判定時 平均 < {lower_33:+.3f}% (下位33%閾値)")
    print(f"    → 各状態が「平均的な日より明らかに上/下」を要求")

    # 候補B: 平均±0.3σ
    mu = rets.mean()
    sigma = rets.std()
    print(f"\n  [候補B: 平均±0.3σ]")
    print(f"    UPTREND判定時 平均 > {mu + 0.3 * sigma:+.3f}%")
    print(f"    DOWNTREND判定時 平均 < {mu - 0.3 * sigma:+.3f}%")
    print(f"    RANGE判定時 |平均| < {0.1 * sigma:.3f}% (0.1σ)")

    # 候補C: 平均±0.5σ（厳しめ）
    print(f"\n  [候補C: 平均±0.5σ・厳しめ]")
    print(f"    UPTREND判定時 平均 > {mu + 0.5 * sigma:+.3f}%")
    print(f"    DOWNTREND判定時 平均 < {mu - 0.5 * sigma:+.3f}%")

    # 候補D: 単純な絶対値（私が最初に出した±0.20%は妥当か？）
    print(f"\n  [候補D: 絶対値 ±0.20%（私の初期案・参考）]")
    print(f"    現状の閾値: ±0.20%")
    print(f"    平均との比較: 平均 {mu:+.3f}% / σ {sigma:.3f}%")
    print(f"    σ比: 0.2 / σ = {0.2 / sigma:.2f}σ")
    pct_above_02 = (rets > 0.2).mean() * 100
    pct_below_neg02 = (rets < -0.2).mean() * 100
    print(f"    閾値超え割合: ret > +0.2% は {pct_above_02:.1f}% / ret < -0.2% は {pct_below_neg02:.1f}%")

    out = {
        "n_days": len(rets),
        "period": f"{daily.index.min().date()} 〜 {daily.index.max().date()}",
        "stats": {
            "mean": float(rets.mean()),
            "median": float(rets.median()),
            "std": float(rets.std()),
            "min": float(rets.min()),
            "max": float(rets.max()),
        },
        "percentiles": {f"p{p}": float(rets.quantile(p / 100)) for p in (5, 10, 25, 33, 50, 67, 75, 90, 95)},
        "criteria_candidates": {
            "A_tritile": {
                "uptrend_min": float(upper_33),
                "downtrend_max": float(lower_33),
                "logic": "上位/下位33%閾値",
            },
            "B_mean_03sigma": {
                "uptrend_min": float(mu + 0.3 * sigma),
                "downtrend_max": float(mu - 0.3 * sigma),
                "range_max_abs": float(0.1 * sigma),
                "logic": "平均±0.3σ",
            },
            "C_mean_05sigma": {
                "uptrend_min": float(mu + 0.5 * sigma),
                "downtrend_max": float(mu - 0.5 * sigma),
                "logic": "平均±0.5σ・厳しめ",
            },
            "D_initial_proposal": {
                "uptrend_min": 0.20,
                "downtrend_max": -0.20,
                "logic": "私の初期案・根拠なし",
                "sigma_ratio": float(0.2 / sigma),
            },
        },
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n→ {OUT_PATH}")


if __name__ == "__main__":
    main()
