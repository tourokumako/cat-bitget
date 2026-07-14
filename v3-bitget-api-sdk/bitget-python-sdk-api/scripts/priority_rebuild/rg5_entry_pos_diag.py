"""rg5_entry_pos_diag.py — read-only 診断（診断レーン・売買記録CSV/score を出さない・print/集計のみ）

目的（まこさん問い #1・2026-07-16）: E37 v24 は「レンジのレジーム判定の範囲内でエントリーしてるはずなのに、
なぜレンジ下端でエントリーしちゃうのか」を数字で確定する。
機構仮説（コード確定済み）: 入口は上端 res_lo 到達で武装（arm）するが、実際に建てるのは stoch DC が出たバーの
close（e37 L2165/L2170）。武装〜発火の間に価格が上端から下がるため、建値が下端寄りになる。

方法: 実走と同じ RG-v5 帯（e37._apply_rg5_to_5m）を candle から再計算し、各エントリーの建値が帯の
どこ（上端 res_lo=1.0 〜 下端 sup_hi=0.0）に居るかを実測。ATR%帯別・勝敗別に集計。
"""
import sys, pathlib
import numpy as np
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import e37_range_scalp as e37  # 実走と同じ帯計算 _apply_rg5_to_5m を再利用（コピー禁止）

BASE = HERE.parent.parent  # bitget-python-sdk-api
CANDLE = BASE / "data" / "BTCUSDT-5m-2024-09-01_2026-02-28_slice_V9FULL_safe.csv"
TRADES = BASE / "results" / "priority_rebuild" / "ratchet" / "trades_e37_range_scalp_v24_044_score.csv"

# --- candle 読み・RG-v5 帯を再計算（実走と同一関数） ---
df = pd.read_csv(CANDLE)
df["ts"] = pd.to_datetime(df["timestamp"])
df = df.reset_index(drop=True)
df = e37._apply_rg5_to_5m(df)  # v11_res_lo/res_hi/sup_lo/sup_hi/mid, range_ok_v11 を付与
bands = df[["ts", "v11_res_lo", "v11_res_hi", "v11_sup_lo", "v11_sup_hi", "v11_mid", "range_ok_v11"]].copy()
bands["ts5"] = bands["ts"].dt.floor("5min")

# --- trades 読み・新規エントリー（position ごと最初の行）に絞る ---
tr = pd.read_csv(TRADES)
tr["entry_time"] = pd.to_datetime(tr["entry_time"])
tr["ts5"] = tr["entry_time"].dt.floor("5min")
print(f"[read] trades 全行={len(tr)} / uniq position_id={tr['position_id'].nunique()}")
# position ごと最初の entry（add_count 最小）を新規エントリーとする
tr = tr.sort_values(["position_id", "add_count", "entry_time"]).groupby("position_id", as_index=False).first()
print(f"[read] 新規エントリー（position 単位）={len(tr)}")

m = tr.merge(bands[["ts5", "v11_res_lo", "v11_res_hi", "v11_sup_lo", "v11_sup_hi", "v11_mid", "range_ok_v11"]],
             on="ts5", how="left")
cov = m["v11_res_lo"].notna().mean()
print(f"[merge] 帯が引けたエントリー割合={cov:.1%}（低いと candle 期間/warmup 不足）")
m = m[m["v11_res_lo"].notna() & m["v11_sup_hi"].notna()].copy()
# 実走との整合サニティ: range_ok_v11 が True のはず
print(f"[sanity] 再計算 range_ok_v11=True の割合={m['range_ok_v11'].mean():.1%}（実走は range 内でのみ発火＝高いはず）")

ep = m["entry_price"].to_numpy(float)
res_lo = m["v11_res_lo"].to_numpy(float)   # レジスタンス帯の下端（high>=res_lo で武装＝発火の基準）
res_hi = m["v11_res_hi"].to_numpy(float)   # レジスタンス帯の上端＝真の抵抗（価格が実際に反落する所）
sup_hi = m["v11_sup_hi"].to_numpy(float)   # サポート帯の上端＝チャネル下端（TP2 ターゲット側）
# ★正しい pos: サポート上端 sup_hi 〜 真の抵抗 res_hi で測る（1.0=真の抵抗res_hi / 0.0=サポート）
chan = res_hi - sup_hi
pos = np.where(chan > 0, (ep - sup_hi) / chan, np.nan)
m["pos_in_range"] = pos
# 真の抵抗 res_hi からどれだけ下で建てたか（%）＝下弦の度合い（正=res_hi の下で売っている）
m["gap_below_res_hi_pct"] = (res_hi - ep) / ep * 100.0
# レジスタンス帯そのものの幅（%）＝帯が広いほど res_lo で発火＝下弦になりやすい
m["res_band_width_pct"] = (res_hi - res_lo) / ep * 100.0
# 建値が res_lo(帯下端) すら下回っているか（武装→下落→DC の型）
m["below_res_lo"] = ep < res_lo

m["atr_pct"] = m["atr_14"] / m["entry_price"] * 100.0
m["win"] = m["net_usd"] > 0

def band(a):
    if a < 0.15: return "1_<0.15(平坦)"
    if a < 0.20: return "2_0.15-0.2"
    if a < 0.30: return "3_0.2-0.3"
    if a < 0.40: return "4_0.3-0.4"
    return "5_>=0.4(有ボラ)"
m["atr_band"] = m["atr_pct"].map(band)

v = m[m["pos_in_range"].notna()].copy()
print(f"\n========= 建値の位置（★真の抵抗 res_hi 基準・1.0=真の抵抗 res_hi / 0.0=サポート sup_hi）=========")
print(f"対象 {len(v)} 件（帯・位置が有効）")
print(f"pos_in_range  中央値={v['pos_in_range'].median():.2f} / 平均={v['pos_in_range'].mean():.2f}")
print(f"  真抵抗寄り(pos>=0.8)={ (v['pos_in_range']>=0.8).mean():.1%} / "
      f"中〜下弦(pos<0.66)={ (v['pos_in_range']<0.66).mean():.1%} / "
      f"はっきり下弦(pos<0.5)={ (v['pos_in_range']<0.5).mean():.1%}")
print(f"真の抵抗 res_hi からの下落幅（%・正=res_hi の下で売っている＝下弦）中央={v['gap_below_res_hi_pct'].median():.3f}% / 平均={v['gap_below_res_hi_pct'].mean():.3f}%")
print(f"レジスタンス帯の幅（res_hi-res_lo %）中央={v['res_band_width_pct'].median():.3f}%（広いほど res_lo 発火＝下弦になる）")
print(f"建値が res_lo(帯下端)すら下回る割合（武装→下落→DC 型）={v['below_res_lo'].mean():.1%}")

print(f"\n---- ATR%帯 × 建値位置(res_hi基準)・net ----")
g = v.groupby("atr_band").agg(件数=("net_usd","size"), net=("net_usd","sum"),
                              pos中央=("pos_in_range","median"),
                              下弦率_pos_lt_0_66=("pos_in_range", lambda s: (s<0.66).mean()),
                              res_hi下落中央=("gap_below_res_hi_pct","median"),
                              帯幅中央=("res_band_width_pct","median")).round(3)
print(g.to_string())

print(f"\n---- 勝敗 × 建値位置(res_hi基準) ----")
g2 = v.groupby("win").agg(件数=("net_usd","size"), net=("net_usd","sum"),
                          pos中央=("pos_in_range","median"),
                          res_hi下落中央=("gap_below_res_hi_pct","median"),
                          帯幅中央=("res_band_width_pct","median"),
                          stochK中央=("stoch_k_at_entry","median")).round(3)
print(g2.to_string())

# --- 轢かれ（SHORT なのに上へ動いた）: mae(逆行=上)>mfe(順行=下) の割合 ---
if "mae_usd" in m.columns and "mfe_usd" in m.columns:
    mm = m[np.isfinite(m["mae_usd"]) & np.isfinite(m["mfe_usd"])].copy()
    run_over = (mm["mae_usd"].abs() > mm["mfe_usd"].abs())
    print(f"\n---- 轢かれ率（|mae 逆行=上| > |mfe 順行=下|＝入った後に上へ動いた玉）----")
    print(f"全体 轢かれ率={run_over.mean():.1%}（{run_over.sum()}/{len(mm)}）")
    mm["atr_band"] = mm["atr_pct"].map(band) if "atr_pct" in mm else None
    mm["atr_pct"] = mm["atr_14"]/mm["entry_price"]*100.0
    mm["atr_band"] = mm["atr_pct"].map(band)
    print(mm.groupby("atr_band").apply(
        lambda s: pd.Series({"件数": len(s), "轢かれ率": (s["mae_usd"].abs()>s["mfe_usd"].abs()).mean()}),
        include_groups=False).round(3).to_string())
print("\n[done] read-only 診断（CSV/score 出力なし）")
