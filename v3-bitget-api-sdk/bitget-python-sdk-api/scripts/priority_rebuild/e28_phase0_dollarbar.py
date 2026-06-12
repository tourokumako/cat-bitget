#!/usr/bin/env python3
"""e28_phase0_dollarbar.py — E28 Phase 0 Step 1: 情報バー(ドルバー)＋行き過ぎ分位＋FR フィルタ の素エッジ測定

設計: strat_v9ml_design.md §10.19.10（microstructure/情報バー版・まこさん GO 2026-06-12）。
狙い: テクニカルを時間足のまま使う naive 版（素エッジなし）でなく、
  (a) ドルバー（close×volume 累積で1本・de Prado・時間軸ノイズ除去）
  (b) 行き過ぎの分位（ボラ調整 MA 乖離 dev_z が直近1ヶ月の下側分位に入った瞬間）で LONG
  (c) FR フィルタ（資金調達率が過熱＝ロング偏りなら拒否・data/funding_rate_BTCUSDT_5y.csv）
  出口は ATR×1.5-2.0 の maker 指値＋直近安値下 SL＋時間切れ4h。
  → eval_engine（コスト+funding 控除後・既知答えテスト済）で素エッジを測る。

★注記:
 - 信号・バリアは「ドルバー」、約定 sim は「実5mパス」（eval_engine・signal_idx=ドルバーが閉じた5m index）。
 - net は per-trade・コスト控除後（連続モード score.py 採点ではない＝Phase 2）。重なりあり。
 - 価格=Binance 5m（出来高あり）／FR=既存5y（〜2024-12＝学習期間カバー・採点2025は宿題）／OI=未取得（Step 2）。
 - 学習 〜2024-12-31 のみ・採点2025 不参照（H8）。レース率 vs 無エッジ基準 SL/(TP+SL) で方向か形かを切り分け。
審判(eval_engine)不変・import のみ。score.py/precheck.py は呼ばない。
"""
from __future__ import annotations
import argparse
import pathlib
import sys

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import eval_engine as ee   # noqa: E402

CSV = ROOT / "data" / "BTCUSDT-5m-2021-04-01_03-31_1826d_V9FULL_safe.csv"
FR_CSV = ROOT / "data" / "funding_rate_BTCUSDT_5y.csv"
OI_CSV = ROOT / "data" / "oi_BTCUSDT_5y.csv"
RATCHET = ROOT / "results" / "priority_rebuild" / "ratchet"
TRAIN_END = pd.Timestamp("2025-01-01")

SIZE = 0.024
SMA_N = 20          # ドルバーの MA 期間
ATR_M = 14          # ドルバーの ATR 期間
PCT_WIN = 1500      # 行き過ぎ分位のローリング窓（≒30日 @ 50本/日）
SWING_K = 10        # SL 用の直近スイング安値（ドルバー本数）
TP_MULT = 1.75      # 利確 = ATR × 1.75（ユーザー 1.5-2.0 の中央・単一値）
HOLD_5M = 48        # 時間切れ 4h（5m 48本）
DAILY_BARS = 50     # de Prado 目安（日あたりドルバー本数）


def build_dollar_bars(df):
    """5m OHLCV+volume → ドルバー（close×volume 累積閾値で生成）。idx5m=閉じた5m index。"""
    n = len(df)
    dv = (df.close.values * df.volume.values)
    days = max((df.ts.iloc[-1] - df.ts.iloc[0]).days, 1)
    thr = dv.sum() / (days * DAILY_BARS)
    bar_id = (np.cumsum(dv) // thr).astype(np.int64)
    gb = pd.DataFrame({"bar_id": bar_id, "pos": np.arange(n),
                       "open": df.open.values, "high": df.high.values,
                       "low": df.low.values, "close": df.close.values, "ts": df.ts.values})
    db = gb.groupby("bar_id").agg(open=("open", "first"), high=("high", "max"),
                                  low=("low", "min"), close=("close", "last"),
                                  idx5m=("pos", "last"), ts=("ts", "last")).reset_index(drop=True)
    print(f"  ドルバー {len(db)}本（閾値 ${thr:,.0f}・実測 {len(db)/days:.1f}本/日）", flush=True)
    return db


def add_indicators(db):
    """ドルバー上で SMA / ATR / dev_z（=(close−SMA)/ATR）/ swing_low を計算。"""
    c = db.close
    db["sma"] = c.rolling(SMA_N).mean()
    pc = c.shift(1)
    tr = np.maximum(db.high - db.low, np.maximum((db.high - pc).abs(), (db.low - pc).abs()))
    db["atr"] = tr.rolling(ATR_M).mean()
    db["atr_pct"] = db.atr / c
    db["dev_z"] = (c - db.sma) / db.atr                       # 行き過ぎ（負ほど売られすぎ）
    db["swing_low"] = db.low.shift(1).rolling(SWING_K).min()  # 直近スイング安値（現バー除外）
    return db


def add_fr(db):
    """FR を backward 整合（leak-safe）。fr_z=直近90点(≒30日)平均比の z スコア（過熱判定）。"""
    fr = pd.read_csv(FR_CSV)
    fr["funding_time"] = pd.to_datetime(fr["funding_time"], utc=True, format="ISO8601").dt.tz_localize(None)
    fr = fr.sort_values("funding_time").reset_index(drop=True)
    m = fr.funding_rate.rolling(90, min_periods=20).mean()
    s = fr.funding_rate.rolling(90, min_periods=20).std()
    fr["fr_z"] = (fr.funding_rate - m) / s
    db = pd.merge_asof(db.sort_values("ts"), fr[["funding_time", "funding_rate", "fr_z"]],
                       left_on="ts", right_on="funding_time", direction="backward")
    return db.reset_index(drop=True)


def add_oi(db):
    """OI/taker(5分・Binance futures)を asof 整合（backward＝leak-safe・時刻 t 以前の最後の値）。
    付ける列（すべて t 時点で取得可能・未来参照なし）:
      oi_chg   = 直近1h の OI 変化率（crude 版・参照のみ）
      oi_3h    = 過去3h の OI 累積変化率（大幅減＝清算 flush があった指標）
      oi_recent= 直近30分の OI 変化率（今もう減っていない＝flush が止まった指標）
      taker_ls = taker 買い/売り比（低い＝投げ売り・逆張り有利の需給歪み）"""
    oi = pd.read_csv(OI_CSV)
    oi["time"] = pd.to_datetime(oi["time"])
    oi = oi[oi.oi_btc > 0].sort_values("time").reset_index(drop=True)
    oi_t = oi.time.to_numpy("datetime64[ns]")
    oi_v = oi.oi_btc.to_numpy(float)
    tls_v = oi.taker_ls.to_numpy(float)

    def asof(times, vals):
        idx = np.searchsorted(oi_t, times, side="right") - 1
        idx = np.clip(idx, 0, len(vals) - 1)
        return vals[idx]

    t_now = db.ts.to_numpy("datetime64[ns]")
    oi_now = asof(t_now, oi_v)
    oi_1h = asof((db.ts - pd.Timedelta(hours=1)).to_numpy("datetime64[ns]"), oi_v)
    oi_3h = asof((db.ts - pd.Timedelta(hours=3)).to_numpy("datetime64[ns]"), oi_v)
    oi_30m = asof((db.ts - pd.Timedelta(minutes=30)).to_numpy("datetime64[ns]"), oi_v)
    db["oi_chg"] = (oi_now - oi_1h) / oi_1h
    db["oi_3h"] = (oi_now - oi_3h) / oi_3h
    db["oi_recent"] = (oi_now - oi_30m) / oi_30m
    db["taker_ls"] = asof(t_now, tls_v)
    return db


def measure(label, fired_db, opens, highs, lows, closes, tss):
    """発火ドルバー → 5m signal_idx → eval_engine 前向き sim（per-trade・コスト+funding 控除後）。"""
    n = len(closes)
    nets, filled, wins, bench_sum = [], 0, 0, 0.0
    gross = fee = 0.0
    reasons, yr_net = {}, {}
    records = []
    for _, r in fired_db.iterrows():
        si = int(r.idx5m)
        if si < SMA_N or si >= n - HOLD_5M - 2:
            continue
        if not (np.isfinite(r.atr_pct) and np.isfinite(r.swing_low) and r.swing_low > 0):
            continue
        tp_pct = float(r.atr_pct * TP_MULT)
        sl_pct = float(np.clip((r.close - r.swing_low) / r.close, 0.005, 0.08))
        tr = ee.simulate_trade(si, ee.LONG, SIZE, opens, highs, lows, closes, tss,
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
        records.append({"label": label, "sig_time": r.ts, "exit_reason": tr.exit_reason,
                        "tp_pct": round(tp_pct, 5), "sl_pct": round(sl_pct, 5),
                        "net_usd": round(tr.net, 4), "gross_usd": round(tr.gross, 4),
                        "fee_usd": round(tr.fee, 4), "year": y})
    if filled == 0:
        return None, []
    nets = np.array(nets)
    tp_cnt, sl_cnt = reasons.get("TP", 0), reasons.get("SL", 0)
    tp_race = tp_cnt / (tp_cnt + sl_cnt) if (tp_cnt + sl_cnt) else float("nan")
    # 無エッジ基準は per-trade でバリアが変動するため、SL/(TP+SL) の平均を使う
    return {"filled": filled, "exp_net": float(nets.mean()), "total_net": float(nets.sum()),
            "winrate": wins / filled, "tp_race": tp_race, "rw_bench": bench_sum / filled,
            "gross": gross, "fee": fee, "reasons": reasons,
            "yr_net": {k: round(yr_net[k], 0) for k in sorted(yr_net)}}, records


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    print("=" * 88)
    print("[E28 Phase 0 Step1] ドルバー＋行き過ぎ分位＋FR フィルタ の素エッジ（eval_engine per-trade・学習期間）")
    df = pd.read_csv(CSV)
    df["ts"] = pd.to_datetime(df["timestamp"])
    opens = df.open.to_numpy(float)
    highs = df.high.to_numpy(float)
    lows = df.low.to_numpy(float)
    closes = df.close.to_numpy(float)
    tss = df.ts.to_numpy()
    print(f"  価格: {CSV.name}（{len(df)}本・{df.ts.iloc[0].date()}〜{df.ts.iloc[-1].date()}）")
    print(f"  計器: maker {ee.MAKER_FEE} / taker {ee.TAKER_FEE} / slip {ee.SLIPPAGE} / funding {ee.FUNDING_RATE_8H}/8h / size {SIZE}")
    print(f"  出口: TP=ATR×{TP_MULT}(maker) / SL=直近安値下(構造) / 時間切れ{HOLD_5M*5//60}h / 学習〜{TRAIN_END.date()}")
    print("=" * 88)

    db = build_dollar_bars(df)
    db = add_indicators(db)
    db = add_fr(db)
    db = add_oi(db)
    db_tr = db[db.ts < TRAIN_END].reset_index(drop=True)   # 学習期間のみ

    dev = db_tr.dev_z
    thr_d1 = dev.rolling(PCT_WIN, min_periods=200).quantile(0.01)
    price_q1 = (dev <= thr_d1) & (dev.shift(1) > thr_d1.shift(1))    # 行き過ぎ 1%ile cross-in（基準）
    at_lows = db_tr.close < db_tr.sma

    # ── 案1 OI枯渇点：3h 大幅 flush が既に起き、かつ今もう減っていない（停止＝清算枯渇） ──
    #   crude 版（oi_drop=減った瞬間に発火＝落ちるナイフ）と差別化：flush の「あと」「止まり」で入る。
    thr_o3 = db_tr.oi_3h.rolling(PCT_WIN, min_periods=200).quantile(0.05)   # 3h OI 累積減の下側5%ile
    flushed = db_tr.oi_3h <= thr_o3                                          # 大幅 flush 済み
    stopped = db_tr.oi_recent >= 0                                           # 直近30分はもう減っていない
    oi_depleted = flushed & stopped                                         # 枯渇点 state
    oi_dep_in = oi_depleted & (~oi_depleted.shift(1).fillna(False))        # state への cross-in（重複発火抑制）

    # ── 案2 taker投げ売りゾーン：taker_ls が下側分位（投げ売り過熱）= 逆張り確認フィルタ ──
    #   ★確定（2026-06-12 E28 Step2）: 当初設計の「転換 cross-in」standalone は不発。
    #   効いたのは「taker_ls が下側ゾーン（売り手が成行で投げ売っている最中）に price_q1 が重なる」＝逆張りフィルタ。
    #   q0.20〜0.40 の広範囲で +1.0〜1.3/件（基準+0.294 の3-4倍）・レース率+4〜12pt・2022反転・逆方向(taker≥上側)は劣化＝方向性確認。
    #   ⚠️ 分位は学習期間で選んだ代表値（類型C 回避＝Phase 1 で木に閾値を学習させる・固定値スイープしない§6.2）。
    tls = db_tr.taker_ls
    thr_t20 = tls.rolling(PCT_WIN, min_periods=200).quantile(0.20)
    thr_t25 = tls.rolling(PCT_WIN, min_periods=200).quantile(0.25)
    tls_z20 = tls <= thr_t20
    tls_z25 = tls <= thr_t25

    entries = [
        ("price_q1(基準・OIなし)", price_q1),
        ("案1 OI枯渇点 standalone(不発・記録)", oi_dep_in & at_lows),
        ("案2f price_q1×taker投げ売りzone q0.20", price_q1 & tls_z20),
        ("案2f price_q1×taker投げ売りzone q0.25", price_q1 & tls_z25),
    ]
    results, all_recs = {}, []
    for label, mask in entries:
        sel = db_tr[mask.fillna(False)]
        if args.smoke:
            sel = sel.iloc[::5]
        r, recs = measure(label, sel, opens, highs, lows, closes, tss)
        if r is None:
            print(f"\n■ {label}: 約定 0 件")
            continue
        results[label] = r
        all_recs.extend(recs)
        verdict = "✅ 素エッジあり" if r["exp_net"] > 0 else "❌ なし"
        print(f"\n■ {label}: 発火 {len(sel)} / 約定 {r['filled']}")
        print(f"  期待値 net/件 {r['exp_net']:+.3f} USD / 勝率 {r['winrate']:.1%}"
              f" / 利確vs損切りレース率 {r['tp_race']:.1%} vs 無エッジ基準 {r['rw_bench']:.1%}  → {verdict}")
        print(f"  gross {r['gross']:+.0f} / 手数料 {r['fee']:.0f} / 出口別 {r['reasons']}")
        print(f"  年別 net {r['yr_net']}")

    if all_recs and not args.smoke and results:
        rec_df = pd.DataFrame(all_recs)
        fcsv = RATCHET / "e28_phase0_dollarbar_trades.csv"
        rec_df.to_csv(fcsv, index=False)
        print(f"\n[保存] per-trade {len(rec_df)}件 → results/priority_rebuild/ratchet/{fcsv.name}")

    print("\n" + "=" * 88)
    print("[総括] 期待値>0 の (分位, FR):")
    hit = [(k, r) for k, r in results.items() if r["exp_net"] > 0]
    if hit:
        for k, r in sorted(hit, key=lambda x: -x[1]["exp_net"]):
            print(f"  ✅ {k}: {r['exp_net']:+.3f}/件・{r['filled']}件・年別 {r['yr_net']}")
        print("  → 確定(Step2): OI枯渇=不発／taker投げ売りzone フィルタが基準+0.294 を +1.0〜1.3 に上乗せ。次=Phase 1(taker_ls 特徴量化)。")
    else:
        print("  なし＝情報バー＋行き過ぎ分位＋需給フィルタでも 5m 由来の素エッジは立たず。")
    print("=" * 88)


if __name__ == "__main__":
    main()
