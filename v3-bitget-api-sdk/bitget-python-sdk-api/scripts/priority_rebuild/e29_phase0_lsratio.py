#!/usr/bin/env python3
"""e29_phase0_lsratio.py — E29 Phase 0: 下げ相場 LONG 新入口＝L-S 比の極値（需給の歪み・素エッジ測定）

設計（まこさん GO 2026-06-12・E29 設計プレゼン）・本筋 strat_v9ml_design §10.19（道具変形路線）:
  E28 で唯一効いた taker_ls（成行フロー）と同族の需給シグナル＝L-S 比（口座の買い/売り比）で別の入り方を試す。
  ls_global   = 大衆の買い/売り口座比（低い＝大衆が極端にショート＝弱気・逆張り LONG の地合い）
  ls_toptrader= 上位トレーダーの買い/売り比（賢い金の向き）。
  入口（各案 per-trade・学習期間のみ・採点なし）:
    1. ls_global 極端低 cross-in × at_lows（大衆ショート過熱→逆張り LONG・standalone）
    2. 行き過ぎ1%ile ∩ ls_global 低ゾーン（行き過ぎ × 大衆ショートのフィルタ＝taker と同型）
    3. 乖離: 行き過ぎ1%ile ∩（ls_global 低 ∧ ls_toptrader 高）＝大衆ショート・上位ロング divergence
  出口/size/期間/判定は E28 と同一（ATR×1.75 maker TP / 構造SL / 4h・0.024・学習〜2024-12・採点不参照）。
  判定: per-trade「利確vs損切りレース率 vs 無エッジ基準 SL/(TP+SL)」＋年別。基準 price_q1(+0.294) と比較。

★審判(eval_engine)は import のみ・改造禁止。net は審判が出す数字。score.py/precheck は呼ばない（Phase0＝採点なし）。
"""
from __future__ import annotations
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import e28_phase0_dollarbar as e28        # noqa: E402  ドルバー/指標/measure/eval_engine 流用
import eval_engine as ee                  # noqa: E402

RAT = e28.RATCHET
TRAIN_END = e28.TRAIN_END


def add_lsratio(db):
    """ls_global / ls_toptrader を asof backward 整合（leak-safe・t 以前の最後の値）。"""
    oi = pd.read_csv(e28.OI_CSV)
    oi["time"] = pd.to_datetime(oi["time"])
    oi = oi[oi.oi_btc > 0].sort_values("time").reset_index(drop=True)
    oi_t = oi.time.to_numpy("datetime64[ns]")

    def asof(vals):
        idx = np.searchsorted(oi_t, db.ts.to_numpy("datetime64[ns]"), side="right") - 1
        idx = np.clip(idx, 0, len(vals) - 1)
        return vals[idx]

    db["ls_global"] = asof(oi.ls_global.to_numpy(float))
    db["ls_toptrader"] = asof(oi.ls_toptrader.to_numpy(float))
    return db


def main():
    print("=" * 88)
    print("[E29 Phase0] 下げ相場 LONG 新入口＝L-S 比の極値（需給の歪み・eval_engine per-trade・学習期間）")
    df = pd.read_csv(e28.CSV); df["ts"] = pd.to_datetime(df["timestamp"])
    opens, highs, lows = df.open.to_numpy(float), df.high.to_numpy(float), df.low.to_numpy(float)
    closes, tss = df.close.to_numpy(float), df.ts.to_numpy()
    db = e28.build_dollar_bars(df)
    db = e28.add_indicators(db)
    db = add_lsratio(db)
    print(f"  計器: maker {ee.MAKER_FEE} / taker {ee.TAKER_FEE} / size {e28.SIZE} / 出口 TP=ATR×{e28.TP_MULT} maker・構造SL・{e28.HOLD_5M*5//60}h")
    print(f"  ls_global 範囲 {db.ls_global.min():.2f}-{db.ls_global.max():.2f} / ls_toptrader 範囲 {db.ls_toptrader.min():.2f}-{db.ls_toptrader.max():.2f}")

    db_tr = db[db.ts < TRAIN_END].reset_index(drop=True)
    W = e28.PCT_WIN

    dev = db_tr.dev_z
    thr_d1 = dev.rolling(W, min_periods=200).quantile(0.01)
    price_q1 = (dev <= thr_d1) & (dev.shift(1) > thr_d1.shift(1))     # 行き過ぎ 1%ile cross-in（基準）
    at_lows = db_tr.close < db_tr.sma

    lsg = db_tr.ls_global
    thr_g10 = lsg.rolling(W, min_periods=200).quantile(0.10)
    thr_g25 = lsg.rolling(W, min_periods=200).quantile(0.25)
    lsg_in10 = (lsg <= thr_g10) & (lsg.shift(1) > thr_g10.shift(1))   # 大衆ショート極端 cross-in
    lsg_z25 = lsg <= thr_g25                                          # 大衆ショート ゾーン（フィルタ）
    lst = db_tr.ls_toptrader
    thr_t75 = lst.rolling(W, min_periods=200).quantile(0.75)
    lst_hi = lst >= thr_t75                                           # 上位ロング（賢い金）

    entries = [
        ("price_q1(基準・需給なし)", price_q1),
        ("案1 ls_global極端低 standalone", lsg_in10 & at_lows),
        ("案2 price_q1×ls_global低zone q0.25", price_q1 & lsg_z25),
        ("案3 price_q1×大衆short×上位long(乖離)", price_q1 & lsg_z25 & lst_hi),
    ]
    results, all_recs = {}, []
    for label, mask in entries:
        sel = db_tr[mask.fillna(False)]
        r, recs = e28.measure(label, sel, opens, highs, lows, closes, tss)
        if r is None:
            print(f"\n■ {label}: 約定 0 件")
            continue
        results[label] = r
        all_recs.extend(recs)
        verdict = "✅ 素エッジあり" if (r["exp_net"] > 0 and r["tp_race"] > r["rw_bench"]) else "❌ なし"
        print(f"\n■ {label}: 発火 {len(sel)} / 約定 {r['filled']}")
        print(f"  期待値 net/件 {r['exp_net']:+.3f} USD / 勝率 {r['winrate']:.1%}"
              f" / 利確vs損切りレース率 {r['tp_race']:.1%} vs 無エッジ基準 {r['rw_bench']:.1%}  → {verdict}")
        print(f"  出口別 {r['reasons']} / 年別 net {r['yr_net']}")

    if all_recs and results:
        rec_df = pd.DataFrame(all_recs)
        fcsv = RAT / "e29_phase0_lsratio_trades.csv"
        rec_df.to_csv(fcsv, index=False)
        print(f"\n[保存] per-trade {len(rec_df)}件 → results/priority_rebuild/ratchet/{fcsv.name}")

    print("\n" + "=" * 88)
    hit = [(k, r) for k, r in results.items() if r["exp_net"] > 0 and r["tp_race"] > r["rw_bench"]]
    if hit:
        print("[総括] 素エッジ(レース率>無エッジ基準)あり:")
        for k, r in sorted(hit, key=lambda x: -x[1]["exp_net"]):
            print(f"  ✅ {k}: {r['exp_net']:+.3f}/件・{r['filled']}件・レース率{r['tp_race']:.1%}>{r['rw_bench']:.1%}・年別 {r['yr_net']}")
        print("  → 基準 price_q1(+0.294)・taker族(+1.27) と比較。上回るなら連続モード採点(Phase2)へ。")
    else:
        print("[総括] L-S 比では素エッジ立たず（レース率<無エッジ基準）＝需給シグナルは taker_ls が本命。")
    print("=" * 88)


if __name__ == "__main__":
    main()
