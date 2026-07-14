"""rg6_v25_entry_diag.py — read-only 診断（診断レーン・CSV/score なし・print のみ）

まこさん指摘（v25 目視）: ①レンジ判定内でのエントリー数が少なすぎる ②入っても低ボラがほとんど
③下端エントリーが改善していない ④何が改善できたのか不明。
→ v25 の実データ（RG-v6 適応帯で発火した v25_045 エントリー）で、pos(下弦度)・ATR分布・
   range_ok に対する発火密度を v24（RG-v5）と並べて、何が変わって何が変わっていないかを数字で出す。
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
V25 = BASE / "results" / "priority_rebuild" / "ratchet" / "trades_e37_range_scalp_v25_045_score.csv"

df = pd.read_csv(CANDLE); df["ts"] = pd.to_datetime(df["timestamp"]); df = df.reset_index(drop=True)
df = e37._apply_rg5_to_5m(df, adaptive_k=e37.V25_K)   # v25 実走と同じ RG-v6 適応帯
df["ts5"] = df["ts"].dt.floor("5min")
sc = df[(df["ts"] >= "2025-06-01") & (df["ts"] < "2026-03-01")]
rok = int(sc["range_ok_v11"].sum())
print(f"[採点窓] range_ok バー {rok:,}（RG-v6 適応帯）")

tr = pd.read_csv(V25); tr["entry_time"] = pd.to_datetime(tr["entry_time"]); tr["ts5"] = tr["entry_time"].dt.floor("5min")
tr = tr.sort_values(["position_id","add_count","entry_time"]).groupby("position_id", as_index=False).first()
print(f"[v25 新規エントリー（position 単位）] {len(tr)} 玉 / 発火密度 = {len(tr)/rok*100:.2f}%（range_ok バー100本あたり {len(tr)/rok*100:.2f} 玉）")

m = tr.merge(df[["ts5","v11_res_lo","v11_res_hi","v11_sup_hi","range_ok_v11"]], on="ts5", how="left")
m = m[m["v11_res_lo"].notna() & m["v11_sup_hi"].notna()].copy()
ep = m["entry_price"].to_numpy(float)
res_lo = m["v11_res_lo"].to_numpy(float); res_hi = m["v11_res_hi"].to_numpy(float); sup_hi = m["v11_sup_hi"].to_numpy(float)
chan = res_hi - sup_hi
m["pos"] = np.where(chan>0, (ep - sup_hi)/chan, np.nan)          # 1=真の抵抗 res_hi / 0=サポート
m["band_w"] = (res_hi - res_lo)/ep*100.0
m["below_res_lo"] = ep < res_lo
m["atr_pct"] = m["atr_14"]/m["entry_price"]*100.0

v = m[m["pos"].notna()]
print(f"\n[建値位置（真の抵抗 res_hi 基準）★v24 RG-v5 は pos中央0.59・下弦34%・res_lo下回り42%・帯幅0.69%だった]")
print(f"  v25 pos中央={v['pos'].median():.2f} / はっきり下弦(pos<0.5)={ (v['pos']<0.5).mean():.1%} / res_lo下回り={v['below_res_lo'].mean():.1%}")
print(f"  v25 レジスタンス帯幅 中央={v['band_w'].median():.3f}%（v24 RG-v5 は 0.69%）")

def band(a):
    if a<0.15: return "1_<0.15(平坦)"
    if a<0.20: return "2_0.15-0.2"
    if a<0.30: return "3_0.2-0.3"
    if a<0.40: return "4_0.3-0.4"
    return "5_>=0.4(高ボラ)"
m["b"] = m["atr_pct"].map(band)
print(f"\n[入口 ATR%帯の分布（v24 RG-v5 は 平坦<0.15 が 89%）]")
print((m["b"].value_counts(normalize=True).sort_index()*100).round(1).to_string())
print("\n[done] read-only 診断")
