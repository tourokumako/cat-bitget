"""inspect_teacher_distribution.py — 教師データの特徴量分布調査

「ADX高 + 半値戻し」帯の教師ラベル分布を見て、
- range 多い → モデル設計の問題
- downtrend 多い → 教師の傾向そのもの
を判別する。
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from regime_inverter import build_features, load_ohlcv

BASE = Path(__file__).resolve().parents[2]


def load_all_teacher() -> pd.DataFrame:
    csvs = {
        2025: BASE / "data/regime_samples_4h.csv",
        2024: BASE / "data/regime_samples_4h_2024.csv",
        2023: BASE / "data/regime_samples_4h_2023.csv",
        2022: BASE / "data/regime_samples_4h_2022.csv",
    }
    parts = []
    for year, path in csvs.items():
        if not path.exists():
            continue
        tmp = pd.read_csv(path, parse_dates=["timestamp_utc"])
        tmp = tmp.rename(columns={"timestamp_utc": "timestamp", "label": "human"})
        tmp["timestamp"] = tmp["timestamp"].dt.tz_localize(None)
        tmp = tmp[tmp["human"].notna() & (tmp["human"] != "")].copy()
        tmp["year"] = year
        parts.append(tmp)
    return pd.concat(parts, ignore_index=True)


def show_dist(df: pd.DataFrame, label: str) -> None:
    if len(df) == 0:
        print(f"  {label}: 該当なし")
        return
    cnt = df["human"].value_counts()
    n = len(df)
    dn = cnt.get("downtrend", 0)
    rg = cnt.get("range", 0)
    up = cnt.get("uptrend", 0)
    print(f"  {label} (n={n}): dn={dn} ({dn/n*100:.1f}%)  rg={rg} ({rg/n*100:.1f}%)  up={up} ({up/n*100:.1f}%)")


def main() -> None:
    print("4h OHLCV 読み込み + 特徴量計算...")
    df_4h = load_ohlcv("4h")
    feats = build_features(df_4h).reset_index().rename(columns={"timestamp": "timestamp"})

    print("教師データ読み込み...")
    teacher = load_all_teacher()
    train = teacher.merge(feats, on="timestamp", how="inner").dropna(
        subset=["adx14", "retrace_ratio_20b"]
    )
    print(f"  全教師: {len(train)} 件\n")

    print("=== ADX × retrace_ratio_20b 帯ごとのラベル分布 ===")
    show_dist(train, "全体")
    print()

    # ADX 帯
    for adx_lo, adx_hi, name in [(0, 25, "ADX低 <25"), (25, 50, "ADX中 25-50"),
                                   (50, 200, "ADX高 ≥50")]:
        sub = train[(train["adx14"] >= adx_lo) & (train["adx14"] < adx_hi)]
        print(f"{name} (n={len(sub)}):")
        for r_lo, r_hi, r_name in [(0, 30, "  retrace 0-30%（安値圏）"),
                                    (30, 70, "  retrace 30-70%（もみ合い圏）"),
                                    (70, 101, "  retrace 70-100%（高値圏）")]:
            ssub = sub[(sub["retrace_ratio_20b"] >= r_lo) & (sub["retrace_ratio_20b"] < r_hi)]
            show_dist(ssub, r_name)
        print()

    # 区間3 と同じ条件: ADX > 50 + retrace 30-70 + di_diff < -10
    print("=== 区間3 類似条件（ADX>50 AND retrace 30-70 AND di_diff<-10）===")
    cond = (train["adx14"] > 50) & (train["retrace_ratio_20b"] >= 30) & \
           (train["retrace_ratio_20b"] < 70) & (train["di_diff"] < -10)
    show_dist(train[cond], "該当")


if __name__ == "__main__":
    main()
