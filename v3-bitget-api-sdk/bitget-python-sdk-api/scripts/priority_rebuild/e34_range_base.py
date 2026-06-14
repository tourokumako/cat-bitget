#!/usr/bin/env python3
"""e34_range_base.py — E34 レンジBOT ベース v1（連続モード・LONG・merge+add+cap停止+単一TP中心回帰）

設計書: .claude/ratchet/e34_design.md v2（Peterson hypothesis-driven・まこさん GO 2026-06-13/14）。
アジャイル（cat_requirements §8.4・CLAUDE.md）: これは MVP ベース。連続モード score.py の月次 net = 地面
  （一発の合否でなく改善の出発点）。⛔ 1回判定で no-edge→破棄しない（L-278）。

流用（新規ロジックを足さない・H16 1変更＝正しい器を1本）:
  - 入口/指標/分位学習: e34_range_zscore_taker.py（add_indicators / add_taker / 分位・同一・5m・leak-safe）
  - merge+add+cap停止ループ: measure_ground_combined_E32b.py の _step 構造を LONG 版に移植。

出口（v1・まこさん確認 2026-06-14）:
  - TP=現バー SMA20（動く中心）へ戻ったら全ロット・指値 maker（TP_FILLED）。中心が avg×(1+コスト床) 未満は不武装
    （含み損のまま中心で即時微利確して負ける degenerate を防ぐ）。
  - SL=平均建値−1.5×ATR14・全ロット・指値 maker（SL_FILLED）。要件 H5＝SL は placePosTpsl 指値（基本 maker）。
  - 時間切れ=初回 entry から48本(4h)・全ロット・成行 taker（TIME_EXIT）＝市場成行クローズ（やむを得ない taker）。

★判定は score.py の数字だけ（本スクリプトは net 計算に eval_engine 定数を import のみ・審判が再計算）。
  CSV の net_usd/gross_usd/fee_usd は self-check 用（score.py が独立再計算し差を表示）。

H 制約照合（§4.6）:
  H1 cap0.12 … add は cap 到達で停止＋実 add タイムラインの同時保有 max を assert（score.py も物理ゲート）。
  H2 leak  … 全指標 shift(1)/asof backward（e34v1.add_indicators/add_taker）・exit 判定は約定 bar の次 bar 以降。
  H6 価格非依存 … dev_z（標準化）・分位（生値）・ATR比・pct。USD 絶対値の閾値/ラベル無し。
  H8 期間分割 … 分位は学習 <2025-01 のみ（採点 2025 不参照）。
  H9 最小注文 … unit 0.024 BTC ≥ 0.0001・1ポジ size ≥ unit（score.assert_min_order も物理ゲート）。
  H10 サイズ … unit 0.024 は比較用・cap 0.12 内。
  H15 ボラ逃げ … ラベル=方向（中心回帰の到達・二値）・ボラ(ATR)は SL/保有時間のみ・LONG 単独。
  H16 1ターン1変更 … ベース v1 を1本（add・部分決済は本番運用の正しい一式＝複数レバーでなく正しい器）。

使い方:
  python3 scripts/priority_rebuild/e34_range_base.py [--no-add] [--smoke N]
    → trades_e34_range_base.csv（全期間・採点用）+ trades_e34_range_base_train.csv（学習<2025-01・precheck 用）
  precheck.py trades_e34_range_base_train.csv --authorize trades_e34_range_base.csv
  score.py trades_e34_range_base.csv --start 2025-06-01 --end 2026-02-28   ← これが地面
"""
from __future__ import annotations
import argparse
import pathlib
import sys
from datetime import timezone

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import eval_engine as ee                       # noqa: E402  審判の確定コスト定数 + funding 境界（改造禁止・import のみ）
import e34_range_zscore_taker as e34v1         # noqa: E402  入口/指標/分位の単一ソース（v1 Phase0・import のみ）

RATCHET = ROOT / "results" / "priority_rebuild" / "ratchet"
OUT_FULL = RATCHET / "trades_e34_range_base.csv"
OUT_TRAIN = RATCHET / "trades_e34_range_base_train.csv"

# ── ベース v1 前提値（固定・単一・最良値スイープしない・hook L-267）──────────────
CAP = 0.12                       # 予算＝全建玉合計の上限（H1・CLAUDE §0-2）
UNIT = e34v1.SIZE                # 0.024 BTC（add 単位・H10）
MAX_ADDS = 5                     # cap 0.12 = unit 0.024 × 5（exchange_spec・H1）
TTL = ee.DEFAULT_TTL             # 指値 TTL 3 本（15分・約定 chance = 次 1〜3 バー）
ENTRY_OFFSET = ee.ENTRY_LIMIT_OFFSET   # LONG 指値 = close×(1−0.0001)
COST_FLOOR = e34v1.COST_FLOOR    # 0.0020（中心が avg×(1+床) 未満は TP 不武装）
SL_ATR_K = e34v1.SL_ATR_K        # 1.5
HOLD_5M = e34v1.HOLD_5M          # 48 本（4h・初回 entry 起点）
PRIORITY = 34                    # E34 識別子（precheck P0 表示用）
TRAIN_END = e34v1.TRAIN_END      # 2025-01-01（分位の学習境界・H8）
SC_START = pd.Timestamp("2025-06-01")   # 新窓 採点開始（地面）
SC_END = pd.Timestamp("2026-02-28")     # 新窓 採点終了（封印 2026-03〜05 は最終 1 回・温存）


def _funding_cost(entry_ts: pd.Timestamp, exit_ts: pd.Timestamp, size: float, mark: float) -> float:
    """保有中の 8h 境界ごと funding（LONG 払い=正で控除）。score.py._funding_for_trade と同式（mark=avg）。"""
    e = pd.Timestamp(entry_ts).to_pydatetime().replace(tzinfo=timezone.utc)
    x = pd.Timestamp(exit_ts).to_pydatetime().replace(tzinfo=timezone.utc)
    cost = 0.0
    for _ in ee._funding_boundaries(e, x):
        cost += 1 * size * mark * ee.FUNDING_RATE_8H     # dir=+1（LONG）
    return cost


def add_analysis_features(df):
    """report.py / analyze.py の帯分析が読む V9 系特徴量（E34 戦略は未使用＝分析スライス専用・leak-safe）。
    bb_mid_slope/bb_width/RSI/Stoch/ret_5 を当該足までで計算（未来参照なし）。"""
    c, h, l = df.close, df.high, df.low
    df["bb_mid_slope"] = df["sma"] - df["sma"].shift(5)                    # 中心(SMA20)の5バー傾き（USD）
    df["bb_width"] = (4 * df["std"]) / df["sma"] * 100                     # BB 幅 %
    df["ret_5"] = c.pct_change(5)
    delta = c.diff()                                                       # RSI14
    up = delta.clip(lower=0).rolling(14).mean()
    dn = (-delta.clip(upper=0)).rolling(14).mean()
    df["rsi"] = 100 - 100 / (1 + up / dn.replace(0, np.nan))
    df["rsi_slope"] = df["rsi"].diff(3)
    ll = l.rolling(14).min(); hh = h.rolling(14).max()                     # Stochastic(14,3,3)
    df["stoch_k"] = (100 * (c - ll) / (hh - ll).replace(0, np.nan)).rolling(3).mean()
    df["stoch_d"] = df["stoch_k"].rolling(3).mean()
    return df


def _record(trades, pos, exit_price, reason, exit_idx, ts_arr):
    """1 ポジ（merge 済み・全ロット）を 1 行に。コスト＝eval_engine 定数で透明計算（score.py が独立再計算）。"""
    avg = float(pos["avg"]); size = float(pos["size"])
    entry_ts = pd.Timestamp(ts_arr[pos["first_idx"]])
    exit_ts = pd.Timestamp(ts_arr[exit_idx])
    gross = (exit_price - avg) * size                    # LONG: dir=+1
    is_taker = reason not in {"TP_FILLED", "SL_FILLED", "TRAIL_EXIT"}   # score.MAKER_EXIT_REASONS と一致
    entry_fee = avg * size * ee.MAKER_FEE                 # entry は常に指値 maker（merge 行 = Σ各ロット maker と同値）
    exit_fee = exit_price * size * (ee.TAKER_FEE if is_taker else ee.MAKER_FEE)
    slip = (exit_price * size * ee.SLIPPAGE) if is_taker else 0.0
    funding = _funding_cost(entry_ts, exit_ts, size, avg)
    net = gross - entry_fee - exit_fee - slip - funding
    trades.append({
        "entry_time": entry_ts, "exit_time": exit_ts, "side": "LONG",
        "priority": PRIORITY, "regime": "range", "add_count": int(pos["add_count"]),
        "size_btc": round(size, 6), "entry_price": round(avg, 2), "exit_price": round(float(exit_price), 2),
        "exit_reason": reason,
        "hold_min": int((exit_idx - pos["first_idx"]) * 5),
        "atr_14": round(float(pos["atr_entry"]), 2),
        "adx_at_entry": round(float(pos["adx_entry"]), 3) if np.isfinite(pos["adx_entry"]) else None,
        "dev_z_at_entry": round(float(pos["devz_entry"]), 3) if np.isfinite(pos["devz_entry"]) else None,
        "taker_ls_at_entry": round(float(pos["taker_entry"]), 4) if np.isfinite(pos["taker_entry"]) else None,
        "bb_mid_slope_at_entry": round(float(pos["f_bbslope"]), 4) if np.isfinite(pos["f_bbslope"]) else None,
        "bb_width_at_entry": round(float(pos["f_bbwidth"]), 5) if np.isfinite(pos["f_bbwidth"]) else None,
        "stoch_k_at_entry": round(float(pos["f_stochk"]), 2) if np.isfinite(pos["f_stochk"]) else None,
        "stoch_d_at_entry": round(float(pos["f_stochd"]), 2) if np.isfinite(pos["f_stochd"]) else None,
        "rsi_at_entry": round(float(pos["f_rsi"]), 2) if np.isfinite(pos["f_rsi"]) else None,
        "rsi_slope_at_entry": round(float(pos["f_rsislope"]), 3) if np.isfinite(pos["f_rsislope"]) else None,
        "ret_5": round(float(pos["f_ret5"]), 5) if np.isfinite(pos["f_ret5"]) else None,
        "entry_hour": int(entry_ts.hour), "entry_weekday": int(entry_ts.weekday()),
        "mfe_usd": round((float(pos["max_high"]) - avg) * size, 4),
        "mae_usd": round((float(pos["min_low"]) - avg) * size, 4),
        "gross_usd": round(gross, 4), "fee_usd": round(entry_fee + exit_fee + slip, 4),
        "net_usd": round(net, 4),
    })


def run(df, enable_add: bool):
    """連続モード LONG ループ。merge（同サイド1ポジ・平均建値）+ cap 停止 add + 単一TP中心回帰。"""
    n = len(df)
    ts = df["ts"].to_numpy()
    o = df["open"].to_numpy(float); h = df["high"].to_numpy(float)
    l = df["low"].to_numpy(float); c = df["close"].to_numpy(float)
    sma = df["sma"].to_numpy(float); atr = df["atr"].to_numpy(float)
    adx = df["adx"].to_numpy(float); devz = df["dev_z"].to_numpy(float)
    taker = df["taker_ls"].to_numpy(float)
    entry_sig = df["entry_sig"].to_numpy(bool)
    # 分析スライス用 V9 系特徴量（戦略は未使用・記録のみ）
    bbslope = df["bb_mid_slope"].to_numpy(float); bbwidth = df["bb_width"].to_numpy(float)
    stochk = df["stoch_k"].to_numpy(float); stochd = df["stoch_d"].to_numpy(float)
    rsi = df["rsi"].to_numpy(float); rsislope = df["rsi_slope"].to_numpy(float)
    ret5 = df["ret_5"].to_numpy(float)

    trades = []
    pos = None
    pending = None            # {"limit": float, "placed_idx": int}
    add_events = []           # (ts, +unit) 実 add タイムライン（同時保有の honest 検証用）
    close_events = []         # (ts, -total)

    for i in range(n):
        oi, hi, li, ci = o[i], h[i], l[i], c[i]
        smai, atri, ts_i = sma[i], atr[i], ts[i]

        # ── 1. pending fill（LONG: low ≤ limit・約定 bar の次 bar から TTL 本）──────────
        if pending is not None:
            elapsed = i - pending["placed_idx"]
            if elapsed > TTL:
                pending = None
            elif elapsed >= 1 and li <= pending["limit"]:
                fill_p = pending["limit"]
                if pos is None:                                  # 新規（1 ロット目）
                    if np.isfinite(atri) and np.isfinite(smai):
                        sl = fill_p - SL_ATR_K * atri
                        pos = {"avg": fill_p, "size": UNIT, "add_count": 1, "first_idx": i,
                               "last_fill_idx": i,   # ★直近 fill bar（出口を fill の次 bar 以降に限る・H2）
                               "sl_price": sl, "atr_entry": atri,
                               "adx_entry": adx[i], "devz_entry": devz[i], "taker_entry": taker[i],
                               "f_bbslope": bbslope[i], "f_bbwidth": bbwidth[i],
                               "f_stochk": stochk[i], "f_stochd": stochd[i],
                               "f_rsi": rsi[i], "f_rsislope": rsislope[i], "f_ret5": ret5[i],
                               "max_high": hi, "min_low": li}
                        add_events.append((pd.Timestamp(ts_i), UNIT))
                    pending = None
                else:                                            # ADD（merge・平均建値）★cap 停止
                    if pos["size"] + UNIT > CAP + 1e-9:
                        pending = None                           # cap 到達 → add しない
                    else:
                        old_sz, old_avg = pos["size"], pos["avg"]
                        new_sz = old_sz + UNIT
                        pos["avg"] = (old_avg * old_sz + fill_p * UNIT) / new_sz
                        pos["size"] = new_sz
                        pos["add_count"] += 1
                        pos["last_fill_idx"] = i        # ★add も fill＝この bar では出口判定しない（H2）
                        if np.isfinite(atri):
                            pos["sl_price"] = pos["avg"] - SL_ATR_K * atri   # 平均建値基準で再計算
                        add_events.append((pd.Timestamp(ts_i), UNIT))
                        pending = None

        # ── 2. MFE/MAE 極値更新（記録/分析用・判定には未使用）──────────────────────
        if pos is not None:
            if hi > pos["max_high"]: pos["max_high"] = hi
            if li < pos["min_low"]: pos["min_low"] = li

        # ── 3. 出口（SL 先着 → TP → 時間切れ・★約定 bar の次 bar 以降＝eval_engine fill_idx+1 契約・H2）─────────
        if pos is not None and i > pos["last_fill_idx"]:
            avg = pos["avg"]
            # SL（LONG: low ≤ sl・gap は min(sl, open) で不利約定・指値 maker）
            if li <= pos["sl_price"]:
                exit_p = min(pos["sl_price"], oi)
                _record(trades, pos, exit_p, "SL_FILLED", i, ts)
                close_events.append((pd.Timestamp(ts_i), -pos["size"]))
                pos = None
            else:
                # TP = 現バー SMA20（動く中心）。中心が avg×(1+コスト床) 以上のときだけ武装。
                armed = np.isfinite(smai) and smai >= avg * (1.0 + COST_FLOOR)
                if armed and hi >= smai:
                    _record(trades, pos, smai, "TP_FILLED", i, ts)
                    close_events.append((pd.Timestamp(ts_i), -pos["size"]))
                    pos = None
                elif (i - pos["first_idx"]) >= HOLD_5M:           # 時間切れ（初回 entry 起点・全ロット成行）
                    _record(trades, pos, ci, "TIME_EXIT", i, ts)
                    close_events.append((pd.Timestamp(ts_i), -pos["size"]))
                    pos = None

        # ── 4. エントリー / ADD 判断（入口再発火・cap 停止は fill 時）────────────────
        if entry_sig[i] and pending is None:
            if pos is None:
                pending = {"limit": ci * (1.0 - ENTRY_OFFSET), "placed_idx": i}
            elif enable_add and pos["add_count"] < MAX_ADDS:
                pending = {"limit": ci * (1.0 - ENTRY_OFFSET), "placed_idx": i}

    # ── 期間末 強制クローズ（成行）──────────────────────────────────────────────
    if pos is not None:
        _record(trades, pos, c[n - 1], "FORCE_CLOSE_EOD", n - 1, ts)
        close_events.append((pd.Timestamp(ts[n - 1]), -pos["size"]))

    return trades, add_events, close_events


def _verify_cap(add_events, close_events):
    """実 add/決済タイムラインの同時保有 max を実測（honest・score.py の cap ゲートと二重）。"""
    ev = [(t, s) for t, s in add_events] + [(t, s) for t, s in close_events]
    ev.sort(key=lambda x: (x[0], x[1]))      # 同時刻は決済(マイナス)を先に
    cur = mx = 0.0
    for _t, s in ev:
        cur = round(cur + s, 9)
        mx = max(mx, cur)
    return mx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-add", action="store_true", help="add を無効化（§7 コンポーネント評価：入口のみ vs 入口+add）")
    ap.add_argument("--smoke", type=int, default=0, help="先頭 N バーだけで動作確認（0=全期間）")
    a = ap.parse_args()

    print("=" * 92)
    print(f"[E34 ベース v1] レンジ逆張り 連続モード LONG（add{'OFF' if a.no_add else 'ON'}・merge・cap{CAP}・単一TP中心回帰）")
    df = pd.read_csv(e34v1.CSV)
    df["ts"] = pd.to_datetime(df["timestamp"])
    df = df.reset_index(drop=True)
    if a.smoke:
        df = df.iloc[:a.smoke].reset_index(drop=True)
    df = e34v1.add_indicators(df)
    df = e34v1.add_taker(df)
    df = add_analysis_features(df)              # report/analyze の帯分析用 V9 系特徴量（戦略は未使用）
    print(f"  価格 {e34v1.CSV.name}（{len(df)}本・{df.ts.iloc[0].date()}〜{df.ts.iloc[-1].date()}）")
    print(f"  計器 maker {ee.MAKER_FEE} / taker {ee.TAKER_FEE} / slip {ee.SLIPPAGE} / funding {ee.FUNDING_RATE_8H}/8h / unit {UNIT}")

    # ── taker_ls(oi) の実被覆を verify（被覆外は asof で値がフリーズ＝S2 が定数化・地面が S2 を反映しない）──
    oi_end = pd.to_datetime(pd.read_csv(e34v1.OI_CSV, usecols=["time"])["time"]).max()
    eff_end = min(SC_END, oi_end.normalize())
    if oi_end < SC_END:
        print(f"  ⚠️ taker_ls(oi) 被覆は {oi_end.date()} まで。採点窓末 {SC_END.date()} 以降は taker フリーズ＝S2 定数化。")
        print(f"     → 地面は taker 実被覆内 2025-06-01〜{eff_end.date()} で測る（窓延長は E30 download --merge が前提）。")

    # ── 入口の分位（学習 <2025-01 の生値・覗き見なし H8）──────────────────────────
    tr = df[df.ts < TRAIN_END]
    z_thr = float(tr.dev_z.quantile(e34v1.Z_Q))
    taker_thr = float(tr.taker_ls.quantile(e34v1.TAKER_Q))
    print(f"  入口 dev_z≤q{e34v1.Z_Q}={z_thr:+.2f} ∩ taker_ls≤q{e34v1.TAKER_Q}={taker_thr:.3f} ∩ ADX{e34v1.ADX_N}≤{e34v1.ADX_MAX}")
    s1 = (df.dev_z <= z_thr) & (df.dev_z.shift(1) > z_thr)      # 行き過ぎ cross-in
    s2 = df.taker_ls <= taker_thr                               # 投げ売り枯渇
    s3 = df.adx <= e34v1.ADX_MAX                                # 非トレンド
    df["entry_sig"] = (s1 & s2 & s3).fillna(False)
    print(f"  出口 TP=中心SMA{e34v1.SMA_N}(動的) / SL=avg−{SL_ATR_K}×ATR{e34v1.ATR_N}(maker) / 時間切れ{HOLD_5M*5//60}h(taker)")
    print(f"  入口発火（全系列）: {int(df['entry_sig'].sum())} 本")

    # ── 連続モード実行 ──────────────────────────────────────────────────────────
    trades, add_ev, close_ev = run(df, enable_add=(not a.no_add))
    t = pd.DataFrame(trades)
    if len(t) == 0:
        print("  ⛔ 取引 0 件。入口が発火していない可能性 → 分位/データを確認。")
        return
    t["entry_time"] = pd.to_datetime(t["entry_time"])

    # ── 同時保有 max の honest 検証（cap 0.12）──────────────────────────────────
    mx = _verify_cap(add_ev, close_ev)
    cap_ok = mx <= CAP + 1e-9
    print(f"  [cap 検証] 実 add タイムラインの同時保有 max = {mx:.4f} BTC {'✅' if cap_ok else '⛔超過'}（予算 {CAP}）")
    assert cap_ok, f"同時保有 {mx:.4f} > cap {CAP}（停止・add 停止ロジックのバグ）"

    print(f"  連続モード約定: {len(t)}件 / 出口 {dict(t['exit_reason'].value_counts())} / add分布 {dict(t['add_count'].value_counts().sort_index())}")

    # ── 出力（全期間=採点用 + 学習<2025-01=precheck 用）────────────────────────────
    RATCHET.mkdir(parents=True, exist_ok=True)
    suffix = "_noadd" if a.no_add else ""
    out_full = OUT_FULL.with_name(OUT_FULL.stem + suffix + ".csv")
    out_train = OUT_TRAIN.with_name(OUT_TRAIN.stem.replace("_train", "") + suffix + "_train.csv")
    out_score = OUT_FULL.with_name(OUT_FULL.stem + suffix + "_score.csv")
    SEAL_START = pd.Timestamp("2026-03-01")                 # 封印 2026-03〜05 は出力に含めない（最終1回まで温存）
    t_full = t[t.entry_time < SEAL_START].reset_index(drop=True)
    n_sealed = len(t) - len(t_full)
    # 採点窓＝taker 実被覆内・clean な月境界（2025-06-01〜2025-12-31）。report/analyze/score はこれを使う。
    SCORE_END = pd.Timestamp("2026-01-01")
    t_score = t[(t.entry_time >= SC_START) & (t.entry_time < SCORE_END)].reset_index(drop=True)
    t_full.to_csv(out_full, index=False)
    t_score.to_csv(out_score, index=False)
    t[t.entry_time < TRAIN_END].reset_index(drop=True).to_csv(out_train, index=False)
    print(f"  [出力] 全期間 {out_full.name}（封印2026-03+ を {n_sealed}件除外）/ 採点窓 {out_score.name}({len(t_score)}件) / precheck {out_train.name}")

    # ── 採点窓の月別 CSV net（参考＝正式は score.py 再計算）───────────────────────
    if len(t_score):
        sm = t_score.assign(m=t_score.entry_time.dt.strftime("%Y-%m")).groupby("m")["net_usd"].agg(["count", "sum"]).round(1)
        print(f"\n  採点窓 2025-06〜2025-12 月別（CSV net・参考）:\n" + sm.to_string())
        print(f"  採点窓 合計 CSV net ${t_score.net_usd.sum():.1f} / 件 {len(t_score)} / 勝率 {(t_score.net_usd > 0).mean():.1%}")
    print("\n  → 次（判定は score.py / report.py 審判式の数字）:")
    print(f"     precheck.py {out_train.name} --authorize {out_score.name}")
    print(f"     report.py {out_score.name} --vs <前回CSV>   /   analyze.py {out_score.name}")
    print(f"     score.py {out_score} --start 2025-06-01 --end 2025-12-31   # 地面（taker 実被覆内）")
    print("=" * 92)


if __name__ == "__main__":
    main()
