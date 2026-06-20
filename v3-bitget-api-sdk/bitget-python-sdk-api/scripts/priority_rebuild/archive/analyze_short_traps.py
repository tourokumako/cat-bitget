#!/usr/bin/env python3
"""analyze_short_traps.py — P21/P23(SHORT 柱)の負けが Gemini の踏み上げ罠に集中するか分析（採点なし・実データ読み）

目的（まこさん GO 2026-06-12・Gemini 意見の実データ裏取り）:
  下げ相場 LONG(E28/E29)は存在証明済の add-on＝桁が小。$1,900 主戦場は SHORT 柱(P21/P23)。
  Gemini の「踏み上げ(ショートスクイーズ)を AI に拒否させる3罠」が我々の SHORT に効くか、
  まず P21/P23 の負けトレードが罠条件に集中しているかを実データで見る（作る前の安い検証・運用枠組み）。
  罠①: マイナス FR（ショート勢が金利を払う＝ショート過熱＝スクイーズ риск）
  罠②: OI 積み上がり（過去3h で OI 増＝新規ショート大量流入）＋価格 下げ渋り
  罠③: マクロ強気（4h/日足の MA より上＝上昇トレンド中のショート）
  → 負け($)が罠条件に集中していれば拒否フィルタは正当（全月 $1,900 の最悪月対策）。
     していなければ Gemini の罠は我々の SHORT には効かない（既に regime で避けている）。

★これは分析のみ（採点・戦略 build なし）。FR/OI/MA は asof backward（leak-safe）。
"""
from __future__ import annotations
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import e28_phase0_dollarbar as e28        # noqa: E402  CSV/FR/OI パス流用

RAT = e28.RATCHET
P21 = RAT / "trades_p21_E16_ground.csv"
P23 = RAT / "trades_p23_ground_capped.csv"
SC_START, SC_END = pd.Timestamp("2025-04-01"), pd.Timestamp("2025-12-31")


def _asof(times, src_t, src_v):
    idx = np.searchsorted(src_t, times.to_numpy("datetime64[ns]"), side="right") - 1
    idx = np.clip(idx, 0, len(src_v) - 1)
    return src_v[idx]


def enrich(tr):
    """entry_time に FR / OI(3h変化) / taker_ls / ls_global / マクロMA を asof backward 結合。"""
    et = pd.to_datetime(tr["entry_time"])
    # FR
    fr = pd.read_csv(e28.FR_CSV)
    fr["t"] = pd.to_datetime(fr["funding_time"], format="ISO8601").dt.tz_localize(None)
    fr = fr.sort_values("t")
    tr["fr"] = _asof(et, fr.t.to_numpy("datetime64[ns]"), fr.funding_rate.to_numpy(float))
    # OI / taker_ls / ls_global
    oi = pd.read_csv(e28.OI_CSV); oi["time"] = pd.to_datetime(oi["time"])
    oi = oi[oi.oi_btc > 0].sort_values("time")
    oi_t = oi.time.to_numpy("datetime64[ns]")
    oi_now = _asof(et, oi_t, oi.oi_btc.to_numpy(float))
    oi_3h = _asof(et - pd.Timedelta(hours=3), oi_t, oi.oi_btc.to_numpy(float))
    tr["oi_chg_3h"] = (oi_now - oi_3h) / oi_3h
    tr["taker_ls"] = _asof(et, oi_t, oi.taker_ls.to_numpy(float))
    tr["ls_global"] = _asof(et, oi_t, oi.ls_global.to_numpy(float))
    # マクロ: 4h EMA50 / 日足 EMA50 への乖離（価格 CSV から・asof backward）
    px = pd.read_csv(e28.CSV); px["ts"] = pd.to_datetime(px["timestamp"])
    px = px.set_index("ts").sort_index()
    for tag, freq, span in [("4h", "4h", 50), ("d", "1D", 50)]:
        bars = px.close.resample(freq, label="left", closed="left").last().dropna()
        ema = bars.ewm(span=span, adjust=False).mean()
        avail = ema.index + pd.Timedelta(freq if freq != "1D" else "1D")
        em = pd.DataFrame({"avail": avail, "ema": ema.values}).sort_values("avail")
        tr[f"vs_ema_{tag}"] = (tr["entry_price"].values - _asof(et, em.avail.to_numpy("datetime64[ns]"), em.ema.to_numpy(float))) \
            / tr["entry_price"].values * 100
    return tr


def _split(tr, name, cond):
    """条件 True/False で 件数・net合計・勝率・負け($)シェア を出す。"""
    tot_loss = tr.loc[tr.net_usd < 0, "net_usd"].sum()
    out = []
    for lab, m in [(f"{name}=該当", cond), (f"{name}=非該当", ~cond)]:
        s = tr[m]
        loss = s.loc[s.net_usd < 0, "net_usd"].sum()
        out.append(f"   {lab:18s}: {len(s):4d}件 net{s.net_usd.sum():+8.0f} 勝率{(s.net_usd>0).mean():5.1%} "
                   f"負け${loss:+7.0f}（全負けの{loss/tot_loss*100 if tot_loss else 0:4.0f}%）")
    return "\n".join(out)


def analyze(path, label, p_start, p_end, pname):
    tr = pd.read_csv(path)
    et = pd.to_datetime(tr["entry_time"])
    tr = tr[(et >= p_start) & (et <= p_end)].reset_index(drop=True)
    if not len(tr):
        print(f"\n##### {label}[{pname}]: トレード 0 件"); return
    tr = enrich(tr)
    keep = tr[tr.vs_ema_4h <= 0]   # 4h veto 後（上昇トレンド中ショートを除外）
    print(f"\n{'#'*80}\n##### {label}［{pname}・{len(tr)}件・net {tr.net_usd.sum():+.0f}・勝率 {(tr.net_usd>0).mean():.1%}・負け ${tr.loc[tr.net_usd<0,'net_usd'].sum():+.0f}］")
    print("# ★罠③ マクロ強気（4h EMA50 より上＝上昇トレンド中の SHORT）— 学習でも成り立つか")
    print(_split(tr, "4h上", tr.vs_ema_4h > 0))
    print(f"# → 4h veto 後（4h上を除外）: {len(keep)}件 net {keep.net_usd.sum():+.0f}（除外前 {tr.net_usd.sum():+.0f}・差 {keep.net_usd.sum()-tr.net_usd.sum():+.0f}）")
    print("#（参考）①FR<0 / ②OI3h増 — 採点で効かなかった罠が学習でも効かないか")
    print(_split(tr, "FR<0", tr.fr < 0))
    print(_split(tr, "OI3h増", tr.oi_chg_3h > 0))


def main():
    print("="*80)
    print("[Gemini 罠③ 4h マクロ veto の学習/採点 一貫性検証] 実データ読み（採点なし・leak-safe asof）")
    print("狙い: 「4h上=net マイナス」が学習でも成り立てば veto は robust → 採点1回で適用（in-sample 回避）")
    periods = [(pd.Timestamp("2021-01-01"), pd.Timestamp("2024-12-31"), "学習2021-24"),
               (SC_START, SC_END, "採点2025-04〜12")]
    for p, lab in [(P21, "P21 SHORT(スキャル)"), (P23, "P23 SHORT(fat-tail)")]:
        if not p.exists():
            print(f"\n##### {lab}: CSV 無 {p.name}"); continue
        for ps, pe, pn in periods:
            analyze(p, lab, ps, pe, pn)
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
