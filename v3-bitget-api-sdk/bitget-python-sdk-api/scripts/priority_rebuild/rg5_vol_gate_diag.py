"""rg5_vol_gate_diag.py — read-only 診断（診断レーン・CSV/score なし・print のみ）

まこさん問い「高ボラレンジにエントリーできてない・なぜ？」を確定する。
仮説: レンジ判定(RG-v5)が高ボラバーを弾いている（range_ok=False にしている）＝頻度が上がらない根。
測る: 採点窓の全バーを ATR%帯別に、range_ok になる割合／uptrend で弾かれる割合／brk(帯外)で弾かれる割合。
"""
import sys, pathlib
import numpy as np
import pandas as pd
HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import e37_range_scalp as e37
BASE = HERE.parent.parent
CANDLE = BASE / "data" / "BTCUSDT-5m-2024-09-01_2026-02-28_slice_V9FULL_safe.csv"

df = pd.read_csv(CANDLE)
df["ts"] = pd.to_datetime(df["timestamp"])
df = df.reset_index(drop=True)
# ATR14（True Range の 14 本平均）を先に計算
h, l, c = df["high"].to_numpy(float), df["low"].to_numpy(float), df["close"].to_numpy(float)
pc = np.roll(c, 1); pc[0] = c[0]
tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
df["atr14"] = pd.Series(tr).rolling(14).mean().to_numpy()
df = e37._apply_rg5_to_5m(df)
df["atr_pct"] = df["atr14"] / df["close"] * 100.0
# brk（帯外＝レンジ離脱）と uptrend を再構成（range_ok=False の内訳）
res_hi = df["v11_res_hi"].to_numpy(float); sup_lo = df["v11_sup_lo"].to_numpy(float)
cc = df["close"].to_numpy(float)
has_zone = np.isfinite(res_hi) & np.isfinite(sup_lo)
df["brk"] = np.where(has_zone, (cc > res_hi) | (cc < sup_lo), False)
df["has_zone"] = has_zone

sc = df[(df["ts"] >= "2025-06-01") & (df["ts"] < "2026-03-01") & df["atr_pct"].notna()].copy()
def band(a):
    if a < 0.15: return "1_<0.15(平坦)"
    if a < 0.20: return "2_0.15-0.2"
    if a < 0.30: return "3_0.2-0.3"
    if a < 0.40: return "4_0.3-0.4"
    return "5_>=0.4(高ボラ)"
sc["atr_band"] = sc["atr_pct"].map(band)

print(f"[採点窓] 全バー {len(sc)}")
print(f"\n[ATR%帯別] range_ok になる割合 と 弾かれる内訳")
g = sc.groupby("atr_band").agg(
    全バー=("close","size"),
    zone有=("has_zone","mean"),
    range_ok率=("range_ok_rg5","mean"),
    uptrendで弾く=("rg5_uptrend","mean"),
    brkで弾く=("brk","mean"),
).round(3)
print(g.to_string())

print(f"\n[range_ok バスケットの ATR%構成]（入口候補が生まれるバーの偏り）")
ro = sc[sc["range_ok_rg5"]]
print((ro["atr_band"].value_counts(normalize=True).sort_index()*100).round(1).to_string())
print(f"\n[全バスケットの ATR%構成]（母集団）")
print((sc["atr_band"].value_counts(normalize=True).sort_index()*100).round(1).to_string())
print("\n[done] read-only 診断")
