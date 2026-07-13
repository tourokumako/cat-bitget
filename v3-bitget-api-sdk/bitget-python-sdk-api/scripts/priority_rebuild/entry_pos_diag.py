#!/usr/bin/env python3
"""entry_pos_diag.py — read-only 検証（診断レーン・acceptance 免除・2026-07-16 まこさん指示）

目的（まこさん指摘 2026-07-16）: 「Entry 側でレンジの下端で入ってる筋の悪い SHORT があるなら弾くべき」を
   一次データで検証。轢かれる玉(trend_caught=STOCH_REVERSE/MFE_STALE)が Entry 時点でレンジのどこ(下端/上端)で
   入っているか、下端ほど net が悪いかを両窓で見る。＝Entry フィルタの根拠づくり（弾けば trend_caught を根本削減）。

レンジ内位置 pos = (entry_price − v11_sup_hi) / (v11_res_hi − v11_sup_hi)
   0=サポート上端(レンジ下端＝筋が悪い SHORT) / 1=レジスタンス上端(レンジ上端＝筋が良い SHORT)

read-only: 戦略の実 setup を import 再利用・print のみ・売買記録CSV/score.py に不関与（診断レーン）。
   ※ 下の bin/lab は分析ヒストグラムの区切り（非戦略定数・小文字）＝戦略の固定値調整ではない。
"""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild")
from v22_gate_diag import build_setup   # noqa: E402  検証済みセットアップ（df に v11_res/sup 列を供給）

trend_exits = ("STOCH_REVERSE_EXIT", "MFE_STALE_CUT")   # 轢かれる玉
win_exits = ("PARTIAL_TP", "TP_FILLED")                 # 稼ぐ玉
base = "/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/results/priority_rebuild/ratchet/"
csvs = {"採点窓": base + "trades_e37_range_scalp_v23_043_score.csv",
        "学習窓": base + "trades_e37_range_scalp_v23_043_train.csv"}
bin_edges = [-9, 0, 0.25, 0.5, 0.75, 1.0, 9]
lab = ["<0(下端の外)", "0-0.25(下端寄り)", "0.25-0.5", "0.5-0.75", "0.75-1.0(上端寄り)", ">1.0(上端の外)"]


def main():
    print("=" * 100)
    print("E37 Entry 位置診断: 轢かれる玉はレンジの下端で入っているか（pos 0=下端/1=上端）")
    print("=" * 100)
    df, _, _ = build_setup()
    ts = df["ts"].to_numpy()
    reshi = df["v11_res_hi"].to_numpy(float)
    reslo = df["v11_res_lo"].to_numpy(float)
    suphi = df["v11_sup_hi"].to_numpy(float)
    idx_of = {pd.Timestamp(t).value: i for i, t in enumerate(ts)}

    for win, csv in csvs.items():
        d = pd.read_csv(csv, parse_dates=["entry_time"])
        pos = np.full(len(d), np.nan)
        reslo_pos = np.full(len(d), np.nan)
        for k, (_, r) in enumerate(d.iterrows()):
            i = idx_of.get(pd.Timestamp(r.entry_time).value)
            if i is None:
                continue
            rh, rl, sh = reshi[i], reslo[i], suphi[i]
            if not (np.isfinite(rh) and np.isfinite(sh)) or rh <= sh:
                continue
            pos[k] = (r.entry_price - sh) / (rh - sh)
            reslo_pos[k] = (rl - sh) / (rh - sh)   # 武装点 res_lo のレンジ内位置（設計上の入口基準）
        d["pos"] = pos
        d = d.dropna(subset=["pos"])
        print(f"\n{'='*80}\n【{win}】 {len(d)}玉（pos 計算可）／設計上の武装点 res_lo の平均位置 {np.nanmean(reslo_pos):.2f}")
        tc = d[d.exit_reason.isin(trend_exits)]
        wn = d[d.exit_reason.isin(win_exits)]
        print(f"  轢かれる玉(trend_caught) pos: 平均{tc.pos.mean():.2f} 中央{tc.pos.median():.2f}  ({len(tc)}件 net ${tc.net_usd.sum():,.0f})")
        print(f"  稼ぐ玉(PARTIAL/TP_FILLED) pos: 平均{wn.pos.mean():.2f} 中央{wn.pos.median():.2f}  ({len(wn)}件 net ${wn.net_usd.sum():,.0f})")

        d["posbin"] = pd.cut(d.pos, bin_edges, labels=lab, right=False)
        g = d.groupby("posbin", observed=False).agg(件数=("net_usd", "size"), net=("net_usd", "sum"),
                                                     平均net=("net_usd", "mean"))
        print("\n  [pos帯別 全玉]（下端ほど net が悪ければ まこさん指摘が正しい）")
        for b in lab:
            if b in g.index and g.loc[b, "件数"] > 0:
                print(f"    {b:<18} {int(g.loc[b,'件数']):>4}件  net ${g.loc[b,'net']:>7,.0f}  平均 ${g.loc[b,'平均net']:>6.2f}")

        tcb = tc.groupby(pd.cut(tc.pos, bin_edges, labels=lab, right=False), observed=False).size()
        wnb = wn.groupby(pd.cut(wn.pos, bin_edges, labels=lab, right=False), observed=False).size()
        print("\n  [pos帯別 玉種内訳]（下端に trend_caught が集中し上端に稼ぐ玉が集中すれば弾く根拠）")
        for b in lab:
            print(f"    {b:<18} trend_caught {int(tcb.get(b,0)):>4}件 / 稼ぐ玉 {int(wnb.get(b,0)):>4}件")


if __name__ == "__main__":
    main()
