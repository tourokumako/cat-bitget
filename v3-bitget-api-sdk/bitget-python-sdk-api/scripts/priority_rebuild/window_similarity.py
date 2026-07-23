#!/usr/bin/env python3
"""window_similarity_probe.py — 探索窓の抽出＝値動きの構造特徴による類似窓ランキング（まこさん OK 2026-07-23）

前回の全期間スキャン（worklog 20260721 §17）は「土台の月別成績（結果）の近さ」で選び、
v59c_162 の反転で反実証された。本 probe は成績を一切使わず、E38 のツマミが参照する次元
（ボラ・レンジ性・レンジ幅・急騰性・方向）の構造特徴 15 個で採点窓 2026-03〜06 との類似を測る。
- read-only・金額不使用・全て確定バーのみ（H2）・レンジ判定は RG-v6（v59d と同じ adaptive_k=V25_K）を import 再利用。
- 出力＝候補窓（4ヶ月幅×1ヶ月刻み・採点窓と非重複）の距離昇順 + 現行/旧探索窓の距離 + 特徴内訳。
- ⚠️ あたり付け専用＝窓の決定はまこさんのみ。構造の近さもツマミ移転の保証ではない（限界を明記）。
"""
import pathlib
import sys

import numpy as np
import pandas as pd

PR = pathlib.Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild")
sys.path.insert(0, str(PR))
import e37_scalp as e37                     # noqa: E402  _load / _rg5_frames / V25_K を再利用（コピー禁止）
from observe_diag import _adx_di, _atr      # noqa: E402  v59 と同式（Wilder）

from periods import SCORE_START, SCORE_END   # noqa: E402  期間は periods.py が唯一の正本（手打ち禁止・require_period_source）
BASE_END_EXCL = SCORE_END + pd.Timedelta(days=1)   # periods の SCORE_END は inclusive → 本 probe の窓境界は排他で使う
GRID_MONTHS = 4                             # 候補窓の幅＝採点窓と同じ4ヶ月
SPECIAL = [("現行探索窓 2025-12〜2026-02", pd.Timestamp("2025-12-01"), pd.Timestamp("2026-03-01")),
           ("旧探索窓 2022-07〜2022-12", pd.Timestamp("2022-07-01"), pd.Timestamp("2023-01-01"))]

print("[load] 5分足＋指標（全期間＝start_override で先頭から・既定は採点窓+助走のみのため）...", flush=True)
df = e37._load(0, start_override="2021-04-01")
ts = pd.DatetimeIndex(df["ts"])
h = pd.Series(df["high"].to_numpy(float), index=ts)
l = pd.Series(df["low"].to_numpy(float), index=ts)
c = pd.Series(df["close"].to_numpy(float), index=ts)

print("[rg] RG-v6 レンジ判定（v59d と同じ adaptive_k=%.2f）..." % e37.V25_K, flush=True)
_z1h, up, rng, res_lo, res_hi, sup_lo, sup_hi = e37._rg5_frames(df, adaptive_k=e37.V25_K)
up = pd.Series(up.astype(bool), index=ts)
rng = pd.Series(rng.astype(bool), index=ts)
zone = np.isfinite(res_hi) & np.isfinite(sup_lo)
W_pct = pd.Series(np.where(zone, (res_hi - sup_lo) / c.to_numpy() * 100.0, np.nan), index=ts)

print("[feat] 特徴の時系列（5m/1h/日次）...", flush=True)
atr14_pct = (_atr(h, l, c, 14) / c) * 100.0
logret = np.log(c / c.shift())
rvol20 = logret.rolling(20).std() * 100.0
_adx5, pdi14, mdi14 = _adx_di(h, l, c, 14)
did14 = pdi14 - mdi14
kij = (h.rolling(26).max() + l.rolling(26).min()) / 2.0
kij26_dev = (c / kij - 1.0) * 100.0
ret5 = c.pct_change() * 100.0

d1h = pd.DataFrame({"high": h, "low": l, "close": c}).resample("1h").agg(
    {"high": "max", "low": "min", "close": "last"}).dropna()
adx1h, _, _ = _adx_di(d1h["high"], d1h["low"], d1h["close"], 14)
ret1h = np.log(d1h["close"] / d1h["close"].shift())

day = pd.DataFrame({"high": h, "low": l, "close": c}).resample("1D").agg(
    {"high": "max", "low": "min", "close": "last"}).dropna()
day_range_pct = (day["high"] - day["low"]) / day["close"] * 100.0
day_ret = day["close"].pct_change()

FEATS = ["ATR%14中央", "ATR%14裾q90", "実現ボラ20中央", "日次値幅%中央",
         "レンジ滞在率", "uptrend率", "ADX14_1h中央", "1hリターン自己相関",
         "帯対幅W%中央", "DI差14裾q90", "基準線乖離26裾q95", "+0.5%足/日",
         "5分リターン尖度", "月次リターン%", "陽線日比率"]


def feat_vec(s: pd.Timestamp, e: pd.Timestamp) -> list:
    m5 = (ts >= s) & (ts < e)
    m1h = (d1h.index >= s) & (d1h.index < e)
    md = (day.index >= s) & (day.index < e)
    days = max((e - s).days, 1)
    months = days / 30.44
    r5 = ret5[m5]
    cw = c[m5]
    return [
        float(atr14_pct[m5].median()), float(atr14_pct[m5].quantile(0.90)),
        float(rvol20[m5].median()), float(day_range_pct[md].median()),
        float(rng[m5].mean() * 100.0), float(up[m5].mean() * 100.0),
        float(adx1h[m1h].median()), float(ret1h[m1h].autocorr(lag=1)),
        float(W_pct[m5].median()), float(did14[m5].quantile(0.90)),
        float(kij26_dev[m5].quantile(0.95)), float((r5 >= 0.5).sum() / days),
        float(r5.kurt()), float((cw.iloc[-1] / cw.iloc[0] - 1.0) * 100.0 / months),
        float((day_ret[md] > 0).mean() * 100.0),
    ]


print("[scan] 候補窓（%dヶ月幅×1ヶ月刻み・採点窓と非重複）..." % GRID_MONTHS, flush=True)
base = feat_vec(SCORE_START, BASE_END_EXCL)
rows = []
start = pd.Timestamp("2021-05-01")          # 指標・帯の暖機を考慮し最初の1ヶ月を捨てる
while start + pd.DateOffset(months=GRID_MONTHS) <= SCORE_START:   # 候補窓は採点窓と非重複（終端 ≤ SCORE_START・periods 正本）
    e_ = start + pd.DateOffset(months=GRID_MONTHS)
    rows.append((f"{start:%Y-%m}〜{(e_ - pd.DateOffset(months=1)):%Y-%m}", start, e_, feat_vec(start, e_)))
    start += pd.DateOffset(months=1)

X = np.array([r[3] for r in rows], float)
mu, sd = X.mean(axis=0), X.std(axis=0)
sd[sd == 0] = 1.0


def zdist(v):
    z = (np.array(v, float) - mu) / sd
    zb = (np.array(base, float) - mu) / sd
    return float(np.sqrt(np.nansum((z - zb) ** 2))), z - zb

res = []
for name, s, e_, v in rows:
    d, dz = zdist(v)
    res.append((d, name, v, dz))
res.sort(key=lambda x: x[0])

print("\n" + "=" * 100)
print(f"■ 基準＝採点窓 {SCORE_START:%Y-%m-%d}〜{SCORE_END:%Y-%m-%d} の構造特徴（この15次元との距離で順位づけ・periods 正本）")
print("=" * 100)
for k, v in zip(FEATS, base):
    print(f"   {k:<18} {v: .4f}")

print("\n■ 類似窓ランキング（距離昇順・全窓・成績は一切使っていない）")
print(f"   {'順位':<4}{'窓':<20}{'距離':>8}   最も遠い特徴（z差の絶対値上位3）")
for i, (d, name, v, dz) in enumerate(res, 1):
    worst = sorted(zip(FEATS, dz), key=lambda x: -abs(x[1]))[:3]
    ws = " / ".join(f"{k}{z:+.1f}" for k, z in worst)
    print(f"   {i:<4}{name:<20}{d:>8.2f}   {ws}")

print("\n■ 参考＝現行/旧の探索窓の距離（同じ物差し・窓長が違うため頻度系は/日/月で正規化済み）")
for name, s, e_ in SPECIAL:
    d, dz = zdist(feat_vec(s, e_))
    rank = sum(1 for r in res if r[0] < d) + 1
    worst = sorted(zip(FEATS, dz), key=lambda x: -abs(x[1]))[:3]
    ws = " / ".join(f"{k}{z:+.1f}" for k, z in worst)
    print(f"   {name:<28} 距離 {d:.2f}（候補内なら {rank} 位相当）   {ws}")

print("\n■ 2022〜2023 の窓の順位（まこさんの直感の照合）")
for i, (d, name, v, dz) in enumerate(res, 1):
    if name.startswith("2022") or name.startswith("2023"):
        print(f"   {i:>3} 位  {name}  距離 {d:.2f}")

print("\n■ 上位3窓の特徴内訳（基準との z 差・±0.5 以内は近い）")
for d, name, v, dz in res[:3]:
    print(f"   ── {name}（距離 {d:.2f}）")
    for k, val, z in zip(FEATS, v, dz):
        print(f"      {k:<18} {val: .4f}  (z差 {z:+.2f})")

print("\n⚠️ あたり付け専用＝窓の決定はまこさんのみ。構造の近さもツマミ移転の保証ではない＝")
print("   最終確認は選んだ窓の前半で探索→後半で確認の実測（フロー段2）。")
