"""5分足 リターン と |リターン| の自己相関でレジーム持続時間を推定。

リターンACF: 短期相関の有無（ほぼゼロが期待値・効率市場仮説）
|リターン|ACF: ボラティリティクラスタリング → レジーム持続時間の目安

出力:
  - results/phase3_acf_analysis.json
  - 標準出力: 95%信頼区間を超える最大ラグ（時間換算）
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = REPO_ROOT / "data" / "BTCUSDT-5m-2020-01-01_2024-12-31_5y.csv"
OUT_PATH = REPO_ROOT / "results" / "phase3_acf_analysis.json"

NLAGS = 2016  # 5m × 2016 = 7日


def autocorr(x: np.ndarray, nlags: int) -> np.ndarray:
    """FFTベース自己相関係数を返す（lag 0..nlags）."""
    x = x - np.mean(x)
    n = len(x)
    fft_size = 1 << (2 * n - 1).bit_length()
    f = np.fft.rfft(x, fft_size)
    acf_full = np.fft.irfft(f * np.conj(f), fft_size)[:n]
    acf_full /= acf_full[0]
    return acf_full[: nlags + 1]


def crossing_lag(acf_vals: np.ndarray, band: float) -> int:
    """ACFが信頼区間band以下に持続的に落ちる最初のラグ."""
    below = np.abs(acf_vals) < band
    # 連続して50ラグ以上 below が続いた最初の点
    win = 50
    for i in range(1, len(below) - win):
        if below[i:i + win].all():
            return i
    return len(acf_vals) - 1


def main() -> None:
    df = pd.read_csv(RAW_PATH)
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    closes = df["close"].dropna().values
    rets = np.diff(closes) / closes[:-1]
    abs_rets = np.abs(rets)

    print(f"5m candles total: {len(closes):,}")
    print(f"5m returns:       {len(rets):,}")
    print(f"period in days:   {len(closes) / 288:.0f}")
    print()

    acf_ret = autocorr(rets, NLAGS)
    acf_abs = autocorr(abs_rets, NLAGS)
    band = 1.96 / np.sqrt(len(rets))
    print(f"95% confidence band: ±{band:.4f}")
    print()

    cross_ret = crossing_lag(acf_ret, band)
    cross_abs = crossing_lag(acf_abs, band)

    print(f"リターン自己相関の消失ラグ:   "
          f"{cross_ret} step = {cross_ret * 5} 分 = {cross_ret * 5 / 60:.1f}h")
    print(f"|リターン|自己相関の消失ラグ: "
          f"{cross_abs} step = {cross_abs * 5} 分 = {cross_abs * 5 / 60:.1f}h "
          f"= {cross_abs * 5 / 1440:.1f}日")

    print("\n粒度別 ACF サマリ（abs_rets）:")
    print(f"{'粒度':<6} {'ACF平均(直近1単位)':>20}")
    for name, k in [("1h", 12), ("4h", 48), ("1d", 288)]:
        if k <= NLAGS:
            print(f"{name:<6} {acf_abs[k]:>20.4f}")

    out = {
        "n_returns": int(len(rets)),
        "confidence_band": float(band),
        "acf_returns_lag1_to_288":     [float(v) for v in acf_ret[1:289]],
        "acf_abs_returns_lag1_to_288": [float(v) for v in acf_abs[1:289]],
        "crossing_lag_5m_returns":      int(cross_ret),
        "crossing_lag_5m_abs_returns":  int(cross_abs),
        "crossing_minutes_returns":     int(cross_ret * 5),
        "crossing_minutes_abs_returns": int(cross_abs * 5),
        "abs_acf_at_1h":  float(acf_abs[12]),
        "abs_acf_at_4h":  float(acf_abs[48]),
        "abs_acf_at_8h":  float(acf_abs[96]),
        "abs_acf_at_1d":  float(acf_abs[288]),
        "abs_acf_at_3d":  float(acf_abs[864]) if 864 <= NLAGS else None,
        "abs_acf_at_7d":  float(acf_abs[2016]) if 2016 <= NLAGS else None,
    }
    OUT_PATH.write_text(json.dumps(out, indent=2))
    print(f"\n→ {OUT_PATH}")


if __name__ == "__main__":
    main()
