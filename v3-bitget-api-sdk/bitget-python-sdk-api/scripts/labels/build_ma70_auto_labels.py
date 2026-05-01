"""build_ma70_auto_labels.py — 日足MA70基準で 4h 自動ラベルを生成

定義（確信ゾーンのみラベル付与・残りは空白）:
    ratio = close / MA70 - 1
    ma70_slope_5d = MA70(t) / MA70(t-5) - 1

    ratio >  +UPDN_DELTA                                       → uptrend
    ratio < -UPDN_DELTA                                        → downtrend
    |ratio| < RG_RATIO AND |ma70_slope_5d| < RG_SLOPE          → range
    上記いずれにも該当しない                                   → 空白

    その日の判定を当日の全 4h バー（6本）に割り当てる。

実行:
    # Step 1: 統計と分布を確認
    python3 scripts/build_ma70_auto_labels.py --stats

    # Step 2: 既定値で 2022〜2024 の CSV を上書き
    python3 scripts/build_ma70_auto_labels.py --apply --years 2022,2023,2024
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_CSV = REPO_ROOT / "data" / "BTCUSDT-5m-2021-04-01_03-31_1826d.csv"
DATA_DIR = REPO_ROOT / "data"
BACKUP_DIR = DATA_DIR / "regime_label_backups"

UPDN_DELTA = 0.075   # |ratio| > これで up/dn 確信
RG_RATIO = 0.015     # |ratio| < これで MA70 近傍
RG_SLOPE = 0.005     # |ma70_5d_slope| < これで MA70 が横ばい


def load_daily() -> pd.DataFrame:
    df = pd.read_csv(INPUT_CSV)
    df["dt"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.set_index("dt").sort_index()
    daily = df["close"].resample("1D", label="left", closed="left").last().dropna()
    daily = daily.to_frame("close")
    daily["ma70"] = daily["close"].rolling(70).mean()
    daily["ratio"] = daily["close"] / daily["ma70"] - 1
    daily["ma70_slope_5d"] = daily["ma70"] / daily["ma70"].shift(5) - 1
    return daily


def label_daily(
    daily: pd.DataFrame,
    updn_delta: float = UPDN_DELTA,
    rg_ratio: float = RG_RATIO,
    rg_slope: float = RG_SLOPE,
) -> pd.Series:
    """確信ゾーンのみラベル付与・残りは空白"""
    lab = pd.Series("", index=daily.index, dtype="object")
    valid = daily["ratio"].notna() & daily["ma70_slope_5d"].notna()
    r = daily["ratio"]
    s = daily["ma70_slope_5d"]
    lab[valid & (r > updn_delta)] = "uptrend"
    lab[valid & (r < -updn_delta)] = "downtrend"
    rg_mask = valid & (r.abs() < rg_ratio) & (s.abs() < rg_slope)
    lab[rg_mask] = "range"
    return lab


def expand_to_4h(daily_labels: pd.Series, year: int) -> pd.DataFrame:
    period_start = pd.Timestamp(f"{year}-01-01", tz="UTC")
    period_end = pd.Timestamp(f"{year + 1}-01-01", tz="UTC")
    idx_4h = pd.date_range(period_start, period_end, freq="4h", inclusive="left", tz="UTC")
    rows = []
    daily_idx_utc = daily_labels.index.tz_convert("UTC") if daily_labels.index.tz else daily_labels.index.tz_localize("UTC")
    daily_aligned = pd.Series(daily_labels.values, index=daily_idx_utc.normalize())
    for ts in idx_4h:
        day_key = ts.normalize()
        lab = daily_aligned.get(day_key, "")
        rows.append((ts.strftime("%Y-%m-%dT%H:%M:%SZ"), lab if isinstance(lab, str) else ""))
    return pd.DataFrame(rows, columns=["timestamp_utc", "label"])


def labels_csv_path(year: int) -> Path:
    if year == 2025:
        return DATA_DIR / "regime_samples_4h.csv"
    return DATA_DIR / f"regime_samples_4h_{year}.csv"


def backup_csv(path: Path) -> None:
    if not path.exists():
        return
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    dst = BACKUP_DIR / f"{path.stem}_{ts}.csv"
    dst.write_bytes(path.read_bytes())
    print(f"  [backup] {path.name} → {dst.relative_to(REPO_ROOT)}")


def write_csv(df: pd.DataFrame, year: int) -> None:
    path = labels_csv_path(year)
    backup_csv(path)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["timestamp_utc", "label"])
        for _, row in df.iterrows():
            w.writerow([row["timestamp_utc"], row["label"]])
    dist = df["label"].value_counts(dropna=False).to_dict()
    print(f"  [save] {path.name}  rows={len(df):,}  dist={dist}")


def cmd_stats() -> None:
    daily = load_daily()
    r = daily["ratio"].dropna()
    s = daily["ma70_slope_5d"].dropna()
    print("\n=== close / MA70 - 1 全期間統計（日足）===")
    print(f"  n={len(r):,}  mean={r.mean():+.4f}  std={r.std():.4f}")
    print(f"  min={r.min():+.4f}  max={r.max():+.4f}")
    pcts = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    print("  ratio percentiles:", "  ".join(f"p{p}={np.percentile(r, p):+.4f}" for p in pcts))
    print(f"\n=== ma70_slope_5d 統計 ===")
    print(f"  n={len(s):,}  mean={s.mean():+.4f}  std={s.std():.4f}")
    print("  slope percentiles:", "  ".join(f"p{p}={np.percentile(s, p):+.4f}" for p in pcts))

    print(f"\n=== 確信ゾーン定義（既定値）===")
    print(f"  uptrend  : ratio > +{UPDN_DELTA}")
    print(f"  downtrend: ratio < -{UPDN_DELTA}")
    print(f"  range    : |ratio| < {RG_RATIO} AND |ma70_slope_5d| < {RG_SLOPE}")
    print(f"  それ以外 : 空白")

    lab = label_daily(daily)

    print(f"\n=== 年別ラベル分布（4hバー数換算）===")
    print(f"  {'year':<6} {'total':>6}  {'dn':>5} {'rg':>5} {'up':>5} {'空白':>5}  {'付与率':>7}")
    for y in (2022, 2023, 2024, 2025):
        mask = lab.index.year == y
        sub = lab[mask]
        if len(sub) == 0:
            continue
        n = len(sub)
        dn = (sub == "downtrend").sum()
        rg = (sub == "range").sum()
        up = (sub == "uptrend").sum()
        bl = (sub == "").sum()
        labeled = n - bl
        rate = labeled / n * 100 if n > 0 else 0
        # 4h バー換算（×6）
        print(f"  {y:<6} {n*6:>6}  {dn*6:>5} {rg*6:>5} {up*6:>5} {bl*6:>5}  {rate:>6.1f}%")

    print("\n（既知の歴史: 2022 ≒ 大下落 / 2023 ≒ レンジ→上昇 / 2024 ≒ 上昇支配 / 2025 = 教師既存ラベルあり）")


def cmd_apply(years: list[int]) -> None:
    daily = load_daily()
    daily_lab = label_daily(daily)
    print(f"\n=== 確信ゾーン定義で年別 CSV 上書き ===")
    print(f"  uptrend > +{UPDN_DELTA} / downtrend < -{UPDN_DELTA}")
    print(f"  range : |ratio| < {RG_RATIO} AND |slope_5d| < {RG_SLOPE}")
    for y in years:
        df_4h = expand_to_4h(daily_lab, y)
        write_csv(df_4h, y)
    print("\n次のステップ（自動ではやらない）:")
    for y in years:
        print(f"  python3 scripts/build_regime_samples_4h_dashboard_json.py --year {y}")
    print("  → サーバ再起動 → タブ⑫で確認")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--stats", action="store_true", help="統計と分布を出す")
    p.add_argument("--apply", action="store_true", help="既定の確信ゾーンで CSV 上書き")
    p.add_argument("--years", type=str, default="2022,2023,2024",
                   help="対象年（カンマ区切り・既定: 2022,2023,2024）")
    args = p.parse_args()

    if args.stats:
        cmd_stats()
        return
    if not args.apply:
        p.error("--stats か --apply のどちらかを指定してください")
    years = [int(y) for y in args.years.split(",")]
    cmd_apply(years)


if __name__ == "__main__":
    main()
