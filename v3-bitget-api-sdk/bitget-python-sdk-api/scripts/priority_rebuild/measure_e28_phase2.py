#!/usr/bin/env python3
"""measure_e28_phase2.py — E28 Phase 2: 下げ相場 LONG 確定エッジを連続モードで採点用 CSV 化

設計（まこさん GO 2026-06-12・E28 Phase 2 設計プレゼン）・正本 strat_v9ml_design §10.19:
  確定エッジ（Step2）= ドルバー `行き過ぎ1%ile cross-in ∩ taker_ls ≤ 下側分位 q0.25`（逆張り確認フィルタ・+1.27/件）。
  連続モード変換 = スキャル（add なし・1ポジずつ）。発火を時刻順に走査し保有中の信号はスキップ（cap 自動遵守）。
    各エントリーを eval_engine.simulate_trade（改造禁止・import のみ）で約定/コスト/net を取得。size 0.024（add-on）。
  分位は全系列ローリング因果計算（train 固定閾値でなく各時点の trailing 窓・leak-safe・H2）。
  出力: ① 学習用 trades_e28_phase2_train.csv（entry<2025-01・precheck breakeven 用）
        ② 採点用 trades_e28_phase2_score.csv（全 trade・score.py が --start/--end で 2025-04〜12 を絞る）
  → precheck.py（breakeven）→ score.py（月次 net・採点 2025-04〜12）→ report --vs → analyze → ledger 5問。
  判定: net>0 AND P4 地面（月−$75.69）超え。封印 2026Q1 不参照。LONG は add-on（器=全 Priority 合算）。

★審判(eval_engine/score.py)は import/別実行のみ・改造禁止。net は審判が再計算（CSV の net_usd は self-check 用）。
  exit_reason は score.py 規約に map（TP→TP_FILLED/SL→SL_FILLED/TIME→TIME_EXIT・maker/taker 正判定のため）。
"""
from __future__ import annotations
import argparse
import pathlib
import sys

import numpy as np
import pandas as pd
import ta

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import e28_phase0_dollarbar as e28        # noqa: E402  ドルバー/指標/FR/OI/eval_engine 流用
import eval_engine as ee                  # noqa: E402  審判（約定/コスト/net・改造禁止）
import e29_phase0_lsratio as e29          # noqa: E402  add_lsratio（ls_global/ls_toptrader・E29）


def add_entry_indicators(db):
    """report/analyze が読む entry 指標列をドルバー上で計算（帯別分析の schema 合わせ・因果）。"""
    c, h, l = db.close, db.high, db.low
    db["rsi_at_entry"] = ta.momentum.RSIIndicator(c, 14).rsi()
    db["rsi_slope_at_entry"] = db["rsi_at_entry"].diff()
    st = ta.momentum.StochasticOscillator(h, l, c, 14, 3)
    db["stoch_k_at_entry"] = st.stoch()
    db["stoch_d_at_entry"] = st.stoch_signal()
    db["adx_at_entry"] = ta.trend.ADXIndicator(h, l, c, 14).adx()
    db["bb_mid_slope_at_entry"] = db.sma.diff()
    bb = ta.volatility.BollingerBands(c, 20)
    db["bb_width_at_entry"] = (bb.bollinger_hband() - bb.bollinger_lband()) / c
    db["ret_5"] = c.pct_change(5)
    return db

RAT = e28.RATCHET
SC_START = pd.Timestamp("2025-04-01")     # 採点開始（H8）
SC_END = pd.Timestamp("2025-12-31")       # 採点終了（封印 2026Q1 は score.py --end で除外）
TRAIN_END = pd.Timestamp("2025-01-01")    # 学習期間境界（precheck 用 train CSV）
PRIORITY = 28
SIZE = e28.SIZE
TAKER_Q = 0.25                            # taker_ls 投げ売りゾーン（Step2 確定の代表分位）
ADX_VETO_Q = 0.40                         # ADX 弱トレンド veto（下側分位未満を除外・学習で単調に負け・2026-06-12）
# eval_engine exit_reason → score.py 規約（MAKER_EXIT_REASONS={TP_FILLED,SL_FILLED,TRAIL_EXIT}）
REASON_MAP = {"TP": "TP_FILLED", "SL": "SL_FILLED", "TIME": "TIME_EXIT", "ACTIVE": "ACTIVE_CLOSE"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adxveto", action="store_true",
                    help="ADX 弱トレンド veto（ADX が下側分位未満＝弱トレンドの行き過ぎを除外・学習で単調に負け）")
    ap.add_argument("--filter", choices=["taker", "lsglobal"], default="taker",
                    help="需給フィルタ: taker=taker_ls 投げ売りゾーン(E28・既定) / lsglobal=ls_global 大衆ショートゾーン(E29)")
    args = ap.parse_args()
    suffix = {"taker": "", "lsglobal": "_lsglobal"}[args.filter] + ("_adxveto" if args.adxveto else "")
    print("=" * 88)
    print(f"[E28 Phase2] 下げ相場 LONG（行き過ぎ1%ile ∩ taker投げ売りzone{' ∩ ADX弱veto' if args.adxveto else ''}）連続モード→採点 CSV")
    df = pd.read_csv(e28.CSV); df["ts"] = pd.to_datetime(df["timestamp"])
    opens, highs, lows = df.open.to_numpy(float), df.high.to_numpy(float), df.low.to_numpy(float)
    closes, tss = df.close.to_numpy(float), df.ts.to_numpy()
    n = len(closes)
    db = e28.build_dollar_bars(df)
    db = e28.add_indicators(db)
    db = e28.add_fr(db)
    db = e28.add_oi(db)
    if args.filter == "lsglobal":
        db = e29.add_lsratio(db)
    db = add_entry_indicators(db)
    print(f"  価格 {df.ts.iloc[0].date()}〜{df.ts.iloc[-1].date()} / ドルバー {len(db)}本 / taker_ls 範囲 {db.taker_ls.min():.2f}-{db.taker_ls.max():.2f}")

    # ── 確定エッジ（全系列ローリング因果分位・leak-safe）──────────────────────
    dev = db.dev_z
    thr_d1 = dev.rolling(e28.PCT_WIN, min_periods=200).quantile(0.01)
    price_q1 = (dev <= thr_d1) & (dev.shift(1) > thr_d1.shift(1))
    if args.filter == "lsglobal":
        thr_f = db.ls_global.rolling(e28.PCT_WIN, min_periods=200).quantile(TAKER_Q)
        flt_z = db.ls_global <= thr_f                 # 大衆ショートゾーン（E29・行き過ぎへの逆張り確認）
    else:
        thr_f = db.taker_ls.rolling(e28.PCT_WIN, min_periods=200).quantile(TAKER_Q)
        flt_z = db.taker_ls <= thr_f                  # 投げ売りゾーン（E28）
    fires = (price_q1 & flt_z).fillna(False)
    if args.adxveto:
        thr_adx = db.adx_at_entry.rolling(e28.PCT_WIN, min_periods=200).quantile(ADX_VETO_Q)
        adx_ok = (db.adx_at_entry >= thr_adx).fillna(False)   # 弱トレンド（ADX 下側分位未満）を除外
        fires = fires & adx_ok
    fdb = db[fires].sort_values("idx5m").reset_index(drop=True)
    print(f"  発火（行き過ぎ1%ile ∩ {args.filter}≤q{TAKER_Q}{f' ∩ ADX≥q{ADX_VETO_Q}' if args.adxveto else ''}）: {len(fdb)}件（全系列）")

    # ── 連続モード walk（1ポジずつ・保有中はスキップ＝重なり解消・cap 自動遵守）──
    rows = []
    last_exit_idx = -1
    for _, r in fdb.iterrows():
        si = int(r.idx5m)
        if si <= last_exit_idx:                       # 保有中の信号はスキップ
            continue
        if si < e28.SMA_N or si >= n - e28.HOLD_5M - 2:
            continue
        if not (np.isfinite(r.atr_pct) and np.isfinite(r.swing_low) and r.swing_low > 0):
            continue
        tp_pct = float(r.atr_pct * e28.TP_MULT)
        sl_pct = float(np.clip((r.close - r.swing_low) / r.close, 0.005, 0.08))
        tr = ee.simulate_trade(si, ee.LONG, SIZE, opens, highs, lows, closes, tss,
                               tp_pct=tp_pct, sl_pct=sl_pct, max_hold_bars=e28.HOLD_5M, entry_type="maker")
        if tr is None:
            continue                                  # 指値 TTL 内未約定＝不成立（ポジ取らず）
        last_exit_idx = tr.exit_idx
        et = pd.Timestamp(tss[tr.fill_idx])
        # MFE/MAE（保有中 OHLC・教師/分析用・判定には未使用＝leak でない）
        seg_hi = highs[tr.fill_idx:tr.exit_idx + 1].max()
        seg_lo = lows[tr.fill_idx:tr.exit_idx + 1].min()
        rows.append({
            "entry_time": et, "exit_time": pd.Timestamp(tss[tr.exit_idx]),
            "side": "LONG", "priority": PRIORITY, "regime": "downtrend", "add_count": 0,
            "size_btc": SIZE, "entry_price": round(tr.entry_price, 2), "exit_price": round(tr.exit_price, 2),
            "exit_reason": REASON_MAP.get(tr.exit_reason, tr.exit_reason),
            "hold_min": int((tr.exit_idx - tr.fill_idx) * 5), "atr_14": round(float(r.atr), 2),
            "gross_usd": round(tr.gross, 4), "fee_usd": round(tr.fee + tr.slippage_cost, 4),
            "net_usd": round(tr.net, 4),
            "adx_at_entry": round(float(r.adx_at_entry), 3), "bb_mid_slope_at_entry": round(float(r.bb_mid_slope_at_entry), 4),
            "rsi_at_entry": round(float(r.rsi_at_entry), 2), "rsi_slope_at_entry": round(float(r.rsi_slope_at_entry), 3),
            "ret_5": round(float(r.ret_5), 5), "stoch_k_at_entry": round(float(r.stoch_k_at_entry), 2),
            "stoch_d_at_entry": round(float(r.stoch_d_at_entry), 2), "bb_width_at_entry": round(float(r.bb_width_at_entry), 5),
            "entry_hour": int(et.hour), "entry_weekday": int(et.weekday()),
            "mfe_usd": round((seg_hi - tr.entry_price) * SIZE, 4), "mae_usd": round((seg_lo - tr.entry_price) * SIZE, 4),
            "tp_diff_usd": round(tr.entry_price * tp_pct * SIZE, 4)})
    t = pd.DataFrame(rows)
    t["entry_time"] = pd.to_datetime(t["entry_time"])
    print(f"  連続モード約定: {len(t)}件 / 出口 {dict(t['exit_reason'].value_counts())}")

    train = t[t.entry_time < TRAIN_END].reset_index(drop=True)
    score = t[(t.entry_time >= SC_START) & (t.entry_time <= SC_END)].reset_index(drop=True)
    f_train = RAT / f"trades_e28_phase2{suffix}_train.csv"
    f_score = RAT / f"trades_e28_phase2{suffix}_score.csv"
    train.to_csv(f_train, index=False)
    score.to_csv(f_score, index=False)

    def _yr(x):
        return x.assign(y=x.entry_time.dt.year).groupby("y")["net_usd"].agg(["count", "sum"]).round(1).to_dict("index")
    print(f"\n  [学習用] {f_train.name}: {len(train)}件 / 年別 {_yr(train)}")
    print(f"  [採点用] {f_score.name}: {len(score)}件（2025-04〜12）")
    if len(score):
        sm = score.assign(m=score.entry_time.dt.strftime("%Y-%m")).groupby("m")["net_usd"].agg(["count", "sum"]).round(1)
        print("  採点期間 月別（CSV net・参考＝正式は score.py 再計算）:\n" + sm.to_string())
        print(f"  採点 合計 CSV net ${score.net_usd.sum():.1f} / 件 {len(score)} / 勝率 {(score.net_usd>0).mean():.1%}")
    print("\n  → 次: precheck.py（train_csv・--authorize score_csv）→ score.py（score_csv・--start 2025-04-01 --end 2025-12-31）")
    print("=" * 88)


if __name__ == "__main__":
    main()
