#!/usr/bin/env python3
"""e33_phase0_range_meanrev.py — E33 Phase 0: レンジ相場の両サイド平均回帰 素エッジ測定

狙い（まこさん GO 2026-06-13・設計は当セッションのチャット）:
  V9 にレンジ専用ロジックが無い（レンジ regime は寄与ほぼなし・ledger L22）。全月$1,900 の壁は
  「SHORT 柱は下げ相場でしか稼げない＝レンジ月が空く」こと。そこを埋める平均回帰（両サイド）に
  薄い方向エッジが有るか・どの条件で立つかを、採点を消費せず学習期間だけで安く確認する（E28 流）。

設計（baseup: technical KB §2.2/§4 ＋ WebSearch 2026-06-13）:
  - レンジ判定 = V9 の既存 daily regime をそのまま流用（自前定義しない＝V9踏襲・leak-safe=前日まで）。
    replay_csv._build_regime_map_v3(..., lookahead_safe=True)。range = 日足 ADX<20 ∩ BB幅<6%。
  - エントリー（両サイド・平均回帰）: LONG=BB下限タッチ(pctB≤0.05)∩RSI(9)売られすぎ／
    SHORT=BB上限タッチ(pctB≥0.95)∩RSI(9)買われすぎ。閾値は代表値（§6.2 で木が学習・固定値選定でない）。
  - 出口（計測用）: TP=ATR×倍率（中心回帰の代理）／SL=ATR×倍率（レンジ外＝ブレイク）。判定は
    per-trade「利確 vs 損切りレース率 vs 無エッジ基準 SL/(TP+SL)」（勝率は小TP広SLで機械的に上がるので無効）。
  - リスクゲート: ①TP がコスト床(0.20%)未満の狭すぎレンジは除外（手数料負け回避・report skipped）
    ②確定レンジ＋逆張りで絞る＝E10「低ボラ全部入れ−$6,006」にしない ③pct/比率特徴のみ(H6) ④per-trade size0.024=cap自然遵守(H1)。

★注記:
  - 学習 2021-04〜2024-12 のみ（TRAIN_END=2025-01-01）。採点(2025-06〜)/封印(2026-03〜) 不参照(H8)。
  - 約定・コストは eval_engine（maker/taker/slip/funding 控除後・既知答えテスト済・改造せず import のみ）。
  - leak-safe: 5m 指標は rolling（過去のみ・shift(-)/center なし）／signal bar i の close 確定後に発注
    （eval_engine は i+1 約定）／daily regime は lookahead_safe=True（前日まで）。
  - score.py/precheck.py は呼ばない（Phase 0=per-trade 素エッジ・連続モード採点は次段 Phase 2）。
"""
from __future__ import annotations
import argparse
import pathlib
import sys

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # eval_engine
sys.path.insert(0, str(ROOT / "runner"))                            # replay_csv（regime 流用）
import eval_engine as ee          # noqa: E402
import ta                          # noqa: E402

CSV = ROOT / "data" / "BTCUSDT-5m-2021-04-01_03-31_1826d_V9FULL_safe.csv"
RATCHET = ROOT / "results" / "priority_rebuild" / "ratchet"
TRAIN_END = pd.Timestamp("2025-01-01")   # 学習のみ・採点/封印 不参照

SIZE = 0.024
BB_N = 20
BB_STD = 2.0
RSI_N = 9            # 5m 定番（technical KB §4.2）
ATR_N = 14
PCTB_LO = 0.05      # BB 下限タッチ（pctB≤）
PCTB_HI = 0.95      # BB 上限タッチ（pctB≥）
RSI_OS = 30.0       # 売られすぎ（代表値・木が学習§6.2）
RSI_OB = 70.0       # 買われすぎ
TP_MULT = 1.0       # TP=ATR×（中心回帰の代理）
SL_MULT = 1.2       # SL=ATR×（レンジ外＝ブレイク）
HOLD_5M = 24        # 時間切れ 2h（平均回帰は速い）
TP_FLOOR = 0.0020   # コスト床（往復 maker 0.028% を ~7倍・狭すぎレンジは除外）


def add_indicators(df):
    """5m 上で BB(pctB) / RSI(9) / ATR% を leak-safe（rolling=過去のみ）に計算。"""
    c = df.close
    bb = ta.volatility.BollingerBands(c, window=BB_N, window_dev=BB_STD)
    hb, lb = bb.bollinger_hband(), bb.bollinger_lband()
    df["pctb"] = (c - lb) / (hb - lb)
    df["rsi"] = ta.momentum.RSIIndicator(c, window=RSI_N).rsi()
    pc = c.shift(1)
    tr = np.maximum(df.high - df.low, np.maximum((df.high - pc).abs(), (df.low - pc).abs()))
    df["atr_pct"] = tr.rolling(ATR_N).mean() / c
    return df


def measure(label, side, fired, opens, highs, lows, closes, tss):
    """発火 5m bar → eval_engine 前向き sim（per-trade・コスト+funding 控除後）。
    TP=ATR×TP_MULT / SL=ATR×SL_MULT。TP<コスト床は除外（狭すぎレンジ）。"""
    n = len(closes)
    nets, bench_sum, wins, filled, skipped_floor = [], 0.0, 0, 0, 0
    gross = fee = 0.0
    reasons, yr_net, records = {}, {}, []
    for _, r in fired.iterrows():
        si = int(r.idx)
        if si < BB_N + ATR_N or si >= n - HOLD_5M - 2:
            continue
        ap = float(r.atr_pct)
        if not np.isfinite(ap) or ap <= 0:
            continue
        tp_pct = ap * TP_MULT
        sl_pct = ap * SL_MULT
        if tp_pct < TP_FLOOR:          # 狭すぎレンジ＝手数料負け回避（リスクゲート①）
            skipped_floor += 1
            continue
        tr = ee.simulate_trade(si, side, SIZE, opens, highs, lows, closes, tss,
                               tp_pct=tp_pct, sl_pct=sl_pct, max_hold_bars=HOLD_5M, entry_type="maker")
        if tr is None:
            continue
        filled += 1
        nets.append(tr.net)
        gross += tr.gross
        fee += tr.fee
        wins += int(tr.net > 0)
        bench_sum += sl_pct / (tp_pct + sl_pct)
        reasons[tr.exit_reason] = reasons.get(tr.exit_reason, 0) + 1
        y = int(pd.Timestamp(r.ts).year)
        yr_net[y] = yr_net.get(y, 0.0) + tr.net
        records.append({"label": label, "side": "LONG" if side == ee.LONG else "SHORT",
                        "sig_time": r.ts, "exit_reason": tr.exit_reason,
                        "tp_pct": round(tp_pct, 5), "sl_pct": round(sl_pct, 5),
                        "net_usd": round(tr.net, 4), "gross_usd": round(tr.gross, 4),
                        "fee_usd": round(tr.fee, 4), "year": y})
    if filled == 0:
        return {"filled": 0, "skipped_floor": skipped_floor}, []
    nets = np.array(nets)
    tp_cnt, sl_cnt = reasons.get("TP", 0), reasons.get("SL", 0)
    tp_race = tp_cnt / (tp_cnt + sl_cnt) if (tp_cnt + sl_cnt) else float("nan")
    return {"filled": filled, "skipped_floor": skipped_floor, "exp_net": float(nets.mean()),
            "total_net": float(nets.sum()), "winrate": wins / filled, "tp_race": tp_race,
            "rw_bench": bench_sum / filled, "gross": gross, "fee": fee, "reasons": reasons,
            "yr_net": {k: round(yr_net[k], 0) for k in sorted(yr_net)}}, records


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    print("=" * 90)
    print("[E33 Phase 0] レンジ両サイド平均回帰 素エッジ（eval_engine per-trade・学習期間 2021-04〜2024-12）")
    df = pd.read_csv(CSV)
    df["ts"] = pd.to_datetime(df["timestamp"])
    opens = df.open.to_numpy(float); highs = df.high.to_numpy(float)
    lows = df.low.to_numpy(float); closes = df.close.to_numpy(float)
    tss = df.ts.to_numpy()
    print(f"  価格: {CSV.name}（{len(df)}本・{df.ts.iloc[0].date()}〜{df.ts.iloc[-1].date()}）")
    print(f"  計器: maker {ee.MAKER_FEE} / taker {ee.TAKER_FEE} / slip {ee.SLIPPAGE} / funding {ee.FUNDING_RATE_8H}/8h / size {SIZE}")
    print(f"  出口: TP=ATR×{TP_MULT}(maker) / SL=ATR×{SL_MULT} / 時間切れ {HOLD_5M*5//60}h / コスト床 {TP_FLOOR:.2%}")

    # ── V9 daily regime（流用・leak-safe=前日まで）──────────────────────────────
    import replay_csv as rc   # noqa: E402（保護ファイルだが import のみ＝発注/main は呼ばない）
    regime_map = rc._build_regime_map_v3(str(CSV), lookahead_safe=True)
    if not regime_map:
        print("❌ regime_map 空（ta 不在 等）→ 中断"); sys.exit(1)
    df = add_indicators(df)
    df["idx"] = np.arange(len(df))
    df["day"] = df.ts.dt.normalize()
    df["regime"] = df.day.map(regime_map).fillna("unknown")
    dist = df.regime.value_counts().to_dict()
    print(f"  [自己検査] 5m バーの regime 分布（全期間）: {dist}")

    tr_df = df[df.ts < TRAIN_END].reset_index(drop=True)   # 学習期間のみ（H8）
    rdist = tr_df.regime.value_counts().to_dict()
    print(f"  [自己検査] 学習期間の regime 分布: {rdist}")
    print("=" * 90)

    in_range = tr_df.regime == "range"
    in_nontrend = tr_df.regime.isin(["range", "mixed"])
    long_bb = tr_df.pctb <= PCTB_LO
    short_bb = tr_df.pctb >= PCTB_HI
    long_bbrsi = long_bb & (tr_df.rsi <= RSI_OS)
    short_bbrsi = short_bb & (tr_df.rsi >= RSI_OB)

    variants = [
        ("range  LONG : BB下限∩RSI≤30", in_range & long_bbrsi, ee.LONG),
        ("range  SHORT: BB上限∩RSI≥70", in_range & short_bbrsi, ee.SHORT),
        ("range  LONG : BB下限のみ",     in_range & long_bb,    ee.LONG),
        ("range  SHORT: BB上限のみ",     in_range & short_bb,   ee.SHORT),
        ("非trend LONG : BB下限∩RSI≤30", in_nontrend & long_bbrsi, ee.LONG),
        ("非trend SHORT: BB上限∩RSI≥70", in_nontrend & short_bbrsi, ee.SHORT),
    ]

    results, all_recs = {}, []
    for label, mask, side in variants:
        sel = tr_df[mask.fillna(False)][["idx", "ts", "atr_pct"]]
        if args.smoke:
            sel = sel.iloc[::7]
        r, recs = measure(label, side, sel, opens, highs, lows, closes, tss)
        if r["filled"] == 0:
            print(f"\n■ {label}: 発火 {len(sel)} / 約定 0（コスト床除外 {r['skipped_floor']}）")
            continue
        results[label] = r
        all_recs.extend(recs)
        edge = r["exp_net"] > 0 and r["tp_race"] > r["rw_bench"]
        verdict = "✅ 素エッジあり" if edge else "❌ なし"
        print(f"\n■ {label}: 発火 {len(sel)} / 約定 {r['filled']}（コスト床除外 {r['skipped_floor']}）")
        print(f"  期待値 net/件 {r['exp_net']:+.3f} USD / 勝率 {r['winrate']:.1%}"
              f" / レース率 {r['tp_race']:.1%} vs 無エッジ基準 {r['rw_bench']:.1%}  → {verdict}")
        print(f"  total net {r['total_net']:+.0f} / gross {r['gross']:+.0f} / 手数料 {r['fee']:.0f} / 出口別 {r['reasons']}")
        print(f"  年別 net {r['yr_net']}")

    if all_recs and not args.smoke and results:
        rec_df = pd.DataFrame(all_recs)
        fcsv = RATCHET / "e33_phase0_range_meanrev_trades.csv"
        rec_df.to_csv(fcsv, index=False)
        print(f"\n[保存] per-trade {len(rec_df)}件 → results/priority_rebuild/ratchet/{fcsv.name}")

    print("\n" + "=" * 90)
    print("[総括] 素エッジあり（exp_net>0 ∩ レース率>無エッジ基準）:")
    hit = [(k, r) for k, r in results.items()
           if r.get("exp_net", -1) > 0 and r.get("tp_race", 0) > r.get("rw_bench", 1)]
    if hit:
        for k, r in sorted(hit, key=lambda x: -x[1]["exp_net"]):
            print(f"  ✅ {k}: {r['exp_net']:+.3f}/件・{r['filled']}件・レース率{r['tp_race']:.0%}(基準{r['rw_bench']:.0%})・年別 {r['yr_net']}")
        print("  → エッジ候補あり。次=連続モード新窓地面(Phase 2・要 GO)＋全期間ロバスト性ゲート(E30)。")
    else:
        print("  なし＝確定レンジ内の素朴な平均回帰には 5m 由来の方向エッジが立たず（道具/条件の再設計か打ち切り）。")
    print("=" * 90)


if __name__ == "__main__":
    main()
