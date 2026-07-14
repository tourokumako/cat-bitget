"""rg5_upper_feasible_diag.py — read-only 診断（診断レーン・CSV/score なし・print のみ）

まこさん要望「レンジ上端でエントリーできるように」の実現可能性を測る。
問い: 価格(high)は帯のどこまで届くか？ 上端トリガにしたら件数は残るか（v19 の二の舞を避ける）？
測る: range_ok バーで high の帯内位置 pos_of_high=(high-res_lo)/(res_hi-res_lo)（0=帯下端 res_lo / 1=帯上端 res_hi）。
      各トリガ水準（res_lo / 帯中央 / クラスタ上端=res_hi/1.0015 / res_hi）に high が届くバー割合＝件数の目安。
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
df = e37._apply_rg5_to_5m(df.reset_index(drop=True))
# 採点窓に限定（periods 正本の採点窓 2025-06-01〜2026-03-01 と同じ範囲）
sc = df[(df["ts"] >= "2025-06-01") & (df["ts"] < "2026-03-01")].copy()
r = sc[sc["range_ok_v11"] & sc["v11_res_lo"].notna() & sc["v11_res_hi"].notna()].copy()
print(f"[採点窓] range_ok バー数 = {len(r)}")

high = r["high"].to_numpy(float)
res_lo = r["v11_res_lo"].to_numpy(float); res_hi = r["v11_res_hi"].to_numpy(float)
band = res_hi - res_lo
pos_high = np.where(band > 0, (high - res_lo) / band, np.nan)   # high の帯内位置
r["pos_high"] = pos_high

pv = r["pos_high"].dropna()
print(f"\n[high の帯内位置 pos_of_high]（0=帯下端 res_lo / 1=帯上端 res_hi）")
print(f"  中央={pv.median():.2f} / 平均={pv.mean():.2f} / 25-75%ile=[{pv.quantile(.25):.2f}, {pv.quantile(.75):.2f}]")

cluster_top = res_hi / 1.0015    # padding 前のクラスタ最高＝実際の抵抗
levels = {
    "res_lo(帯下端=現行トリガ)": res_lo,
    "帯中央(res_lo+0.5*幅)": res_lo + 0.5 * band,
    "帯70%(res_lo+0.7*幅)": res_lo + 0.7 * band,
    "クラスタ上端(実抵抗=res_hi/1.0015)": cluster_top,
    "res_hi(padding込・v19)": res_hi,
}
base = (high >= res_lo).sum()
print(f"\n[各トリガ水準に high が届く range_ok バー割合]（res_lo 到達=100% 基準＝件数の目安）")
for name, lv in levels.items():
    n = int((high >= lv).sum())
    print(f"  {name:32s}: {n:5d} バー ({n/len(r)*100:5.1f}% of range_ok / {n/base*100:5.1f}% of res_lo到達)")

# 上端トリガ（帯70%）の玉が下弦トリガよりどれだけ真抵抗に近いか（位置改善の目安）
print(f"\n[参考] 帯70% で入れた時の『真の抵抗 res_hi からの下落%』中央 = "
      f"{np.nanmedian((res_hi - (res_lo+0.7*band))/(res_lo+0.7*band)*100):.3f}%  "
      f"（現行 res_lo は {np.nanmedian((res_hi-res_lo)/res_lo*100):.3f}%）")
print("\n[done] read-only 診断")
