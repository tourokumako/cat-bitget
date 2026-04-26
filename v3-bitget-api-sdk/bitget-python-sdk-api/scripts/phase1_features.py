"""Phase 1: HMM 入力用 特徴量計算（情報量効率版・8特徴）

入力: data/BTCUSDT-5m-2020-01-01_2024-12-31_5y.csv（5年分5m足）
出力: results/phase1_features_daily.csv（日足・1826行 × 8特徴）

冗長削減後カテゴリ（2026-04-26 改訂・|r|≥0.7 ペア排除済み）:
  A. 方向性: ma50_dev（MA50乖離率）※ ret_14d/di_diff/dist_high_30d は冗長削除
  B. 強度  : adx_14（日足ADX）
  C. 構造  : streak_max_30d（過去30日内の最大連続陽線/陰線日数の符号付き）
  D. ボラ  : atr_14_pct（ATR14/close）, bb_width_20（BB幅%）, bb_pct_b（BB内位置）
  E. その他: vol_chg_7d（7日出来高変化率）, ret_skew_30d（30日リターン歪度）

look-ahead 安全性:
  各日の特徴量は「その日の終値時点」までの情報のみで計算する。
  rolling は終値を含む過去N日。未来情報は一切混ぜない。

精度低下時は 5m 足の日中分布特徴を追加して粒度上げる方針（次セッション以降）。
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "data" / "BTCUSDT-5m-2020-01-01_2024-12-31_5y.csv"
OUT_PATH = REPO_ROOT / "results" / "phase1_features_daily.csv"


def load_daily(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["ts"] = pd.to_datetime(df["timestamp"])
    for c in ("open", "high", "low", "close", "volume"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.set_index("ts").sort_index()
    daily = df.resample("D").agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }).dropna()
    return daily


def compute_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.DataFrame:
    up = high.diff()
    dn = -low.diff()
    plus_dm = np.where((up > dn) & (up > 0), up, 0.0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = pd.concat([
        (high - low),
        (high - close.shift()).abs(),
        (low - close.shift()).abs(),
    ], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / period, adjust=False).mean()
    plus_di = 100 * pd.Series(plus_dm, index=high.index).ewm(alpha=1 / period, adjust=False).mean() / atr
    minus_di = 100 * pd.Series(minus_dm, index=high.index).ewm(alpha=1 / period, adjust=False).mean() / atr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.ewm(alpha=1 / period, adjust=False).mean()
    return pd.DataFrame({"adx": adx, "plus_di": plus_di, "minus_di": minus_di, "atr": atr})


def compute_features(daily: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=daily.index)
    close = daily["close"]
    high = daily["high"]
    low = daily["low"]
    volume = daily["volume"]

    # A. 方向性（代表1本）
    ma50 = close.rolling(50).mean()
    out["ma50_dev"] = (close - ma50) / ma50 * 100

    # B. 強度
    adx_df = compute_adx(high, low, close, period=14)
    out["adx_14"] = adx_df["adx"]

    # C. 構造: 30日内の最大連続陽線/陰線日数（符号付き・look-ahead安全）
    #   陽線続伸はプラス、陰線続落はマイナス。「持続性」を捉え方向性とは独立。
    daily_dir = np.sign(close - close.shift(1)).fillna(0).astype(int)
    pos_run = daily_dir.where(daily_dir > 0, 0).groupby((daily_dir <= 0).cumsum()).cumsum()
    neg_run = (-daily_dir).where(daily_dir < 0, 0).groupby((daily_dir >= 0).cumsum()).cumsum()
    pos_max_30 = pos_run.rolling(30).max()
    neg_max_30 = neg_run.rolling(30).max()
    out["streak_max_30d"] = np.where(
        pos_max_30 >= neg_max_30, pos_max_30, -neg_max_30
    )

    # D. ボラ
    out["atr_14_pct"] = adx_df["atr"] / close * 100
    bb_mid = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    bb_upper = bb_mid + 2 * bb_std
    bb_lower = bb_mid - 2 * bb_std
    out["bb_width_20"] = (bb_upper - bb_lower) / bb_mid * 100
    out["bb_pct_b"] = (close - bb_lower) / (bb_upper - bb_lower)

    # E. その他
    vol_ma_7 = volume.rolling(7).mean()
    out["vol_chg_7d"] = (volume - vol_ma_7) / vol_ma_7 * 100
    daily_ret = close.pct_change() * 100
    out["ret_skew_30d"] = daily_ret.rolling(30).skew()

    return out


def main() -> None:
    if not CSV_PATH.exists():
        raise SystemExit(f"CSV not found: {CSV_PATH}")

    print(f"[phase1] 読み込み: {CSV_PATH.name}")
    daily = load_daily(CSV_PATH)
    print(f"  日足: {len(daily)} 日 ({daily.index.min().date()} 〜 {daily.index.max().date()})")

    print(f"[phase1] 特徴量計算（骨組み 8 特徴）")
    feats = compute_features(daily)
    feats_clean = feats.dropna()
    print(f"  有効行: {len(feats_clean)} 日（warmup で {len(feats) - len(feats_clean)} 日除外）")

    print(f"\n=== 特徴量サマリ ===")
    print(feats_clean.describe().T[["mean", "std", "min", "50%", "max"]].round(3))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    feats_clean.to_csv(OUT_PATH, index_label="date")
    print(f"\n→ {OUT_PATH}（{len(feats_clean)}行 × {len(feats_clean.columns)}列）")


if __name__ == "__main__":
    main()
