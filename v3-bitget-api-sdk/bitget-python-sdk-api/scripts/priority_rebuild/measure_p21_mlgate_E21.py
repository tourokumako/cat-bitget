#!/usr/bin/env python3
"""measure_p21_mlgate_E21.py — E21: P21 Entry ML ゲートの連続モード検証（学習期間×年別・採点前ゲート）

目的（まこさん GO 2026-06-12・都度確認運用）:
  Phase 2 OOF（sig_time 修正版・leak 除去後）の「prob>0.5 で入る」を、独立 sim でなく
  実運用と同じ連続モード（同サイド1ポジ統合・pending TTL2・fill=翌バー）で学習期間に回し、
  年別（特に 2024）が地面（V9 床）比で非劣化かを確認する。独立 sim のプラスは連続モードで
  反転し得る（L-265・ADX50-60 の前例）ため、この確認を通るまで採点（2025-04〜12）に出さない。

実装（自作 net 計算なし・V9 不変・E20 wrapper 流儀）:
  - 連続ループ＝rc.run() の処理順 1 対 1 複製（E20 で地面 4,175 件完全一致 実証済の形を踏襲）。
  - ML ゲート＝シグナルバー i が「OOF prob>0.5 の候補集合」に無ければ発注しない（veto 層）。
    prob はバーごとの OOF（学習に使っていない fold の予測）＝学習期間内でも in-sample にならない。
  - 床外し＝P21_ATR14_MIN を 0 にして型バー全部を発火させ、ゲートは veto 層が担う。
  - 教師に無い型バー（独立 sim で不約定 2,352 本）は prob が無く veto されるが、型バーは
    連続 2 本あり得ず（MACD クロスの定義上）pending TTL2 の阻害も無いため結果は同一（中立）。

自己検査（どちらか落ちたら停止）:
  ① 素の params・veto なし → 地面 CSV と (entry_time/exit_time/exit_reason/net) 全件完全一致
  ② P21_ATR14_MIN=0 ＋ veto「atr_14<150 USD」 → 同じく地面と全件完全一致
     （＝床を params から veto 層に移しても挙動が変わらないことの機械的証明）

H 照合: H1=P21 単独 0.06・同時保有 1 ポジ実測 assert／H2=ゲートは sig バー確定値の OOF prob のみ／
H8=エントリーは学習期間のみ（prob 集合が学習期間のみ＝自動）・採点期間に触れない／
H13=judge 不変（数字は judge 式＝score.py と $1 以内一致を E21 Phase1 で実証済・正式は採点時の score.py）／
H16=1変更（Entry ゲートのみ・Exit/サイズ/add 不変）。
"""
from __future__ import annotations

import argparse
import pathlib
import sys
from decimal import Decimal

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runner"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import replay_csv as rc                          # noqa: E402  V9 リプレイ（import のみ・改造禁止）
import gen_p23_candidates as gen                 # noqa: E402  OHLCV_CSV パス参照のみ
import train_p21_exit_E19 as e19                 # noqa: E402  simulate_exit / calc_tp_price（自己検査済）
import train_p21_entry_E21 as e21                # noqa: E402  judge_net（score.py と一致 実証済）
from strategies.cat_v9_decider import check_entry_priority   # noqa: E402  V9 判定（import のみ）

GROUND_CSV = ROOT / "results" / "priority_rebuild" / "ratchet" / "trades_p21_E16_ground.csv"
OOF_CSV    = ROOT / "results" / "priority_rebuild" / "ratchet" / "p21_entry_E21_oof.csv"
OUT_CSV    = ROOT / "results" / "priority_rebuild" / "ratchet" / "trades_p21_E21_mlgate_train.csv"
TRAIN_END  = pd.Timestamp("2024-12-31 23:59:59")
PEND_FIELDS = ("adx_at_entry", "bb_mid_slope_at_entry", "rsi_at_entry", "rsi_slope_at_entry",
               "stoch_k_at_entry", "stoch_d_at_entry", "bb_width_at_entry")
SIG_COLS = {"adx_at_entry": "adx", "bb_mid_slope_at_entry": "bb_mid_slope", "rsi_at_entry": "rsi_short",
            "rsi_slope_at_entry": "rsi_slope_short", "stoch_k_at_entry": "stoch_k",
            "stoch_d_at_entry": "stoch_d", "bb_width_at_entry": "bb_width"}


def run_continuous(df, arrs, p21: dict, veto_fn):
    """rc.run() の P21 単独・連続モードを 1 対 1 で複製（E20 と同形）。veto_fn(i)=True なら発注しない。"""
    ts_a, cl_a, hi_a, lo_a = arrs
    n = len(df)
    bar_ms = int(ts_a[1] - ts_a[0])
    idx_of_ts = {int(t): k for k, t in enumerate(ts_a)}

    trades, pending = [], None
    n_sig = n_veto = 0
    i = rc.CANDLE_WARMUP
    while i < n:
        ts_ms = int(ts_a[i])

        # ---- rc.run() step1: pending TTL/fill（fill は翌バーのみ・TTL2 で取消が先）----
        if pending is not None:
            elapsed = (ts_ms - pending["placed_bar_ms"]) // bar_ms
            if elapsed >= rc.PENDING_TTL_BARS:
                pending = None
            elif hi_a[i] >= pending["limit_price"]:
                fill_p = pending["limit_price"]
                states = rc._calc_entry_states(df, i, ts_ms)
                tp = e19.calc_tp_price(df, i, fill_p, pending["adx_at_entry"], states["atr_14"], p21)
                sl = rc._calc_sl_price("SHORT", fill_p, p21, 21)
                extra = {k: pending[k] for k in PEND_FIELDS}
                extra.update({"ret_5": states["ret_5"], "atr_14": states["atr_14"],
                              "entry_hour": states["entry_hour"], "entry_weekday": states["entry_weekday"]})
                t = e19.simulate_exit(df, arrs, i, fill_p, ts_ms, tp, sl, p21, extra)
                pending = None
                if t is None:
                    break   # データ末尾まで未決済（地面に FORCE 行なし＝発生しない想定）
                trades.append(t)
                i = idx_of_ts[int(pd.Timestamp(t["exit_time"]).value // 10**6)]
                ts_ms = int(ts_a[i])

        # ---- rc.run() step6: エントリー判定（pos なし・pending なしの時だけ）----
        if pending is None:
            try:
                pri = check_entry_priority(i, df, p21)
            except Exception:
                pri = None
            if pri is not None:
                assert pri == 21, f"P21 以外が発火: {pri}（params 設定ミス・停止）"
                n_sig += 1
                if veto_fn is not None and veto_fn(i):
                    n_veto += 1
                else:
                    pending = {"limit_price": float(Decimal(str(cl_a[i])) * Decimal("1.0001")),
                               "placed_bar_ms": ts_ms}
                    for f, col in SIG_COLS.items():
                        pending[f] = float(df.at[i, col]) if col in df.columns else float("nan")
        i += 1
    return trades, n_sig, n_veto


def assert_match_ground(d: pd.DataFrame, g: pd.DataFrame, label: str):
    assert len(d) == len(g), f"{label}: 件数不一致 {len(d)} vs {len(g)}（停止）"
    ng = 0
    for a, b in zip(d.itertuples(), g.itertuples()):
        ok = (a.entry_time == b.entry_time and a.exit_time == b.exit_time
              and a.exit_reason == b.exit_reason and abs(float(a.net_usd) - float(b.net_usd)) <= 0.01)
        if not ok:
            ng += 1
            if ng <= 5:
                print(f"  [不一致] {a.entry_time} vs {b.entry_time} / {a.exit_reason} vs {b.exit_reason}")
    assert ng == 0, f"{label}: 自己検査 FAIL {ng} 件不一致（停止）"
    et = pd.to_datetime(d["entry_time"]).values
    xt = pd.to_datetime(d["exit_time"]).values
    assert all(et[k + 1] >= xt[k] for k in range(len(d) - 1)), "同時保有を検出（連続モード破れ・停止）"
    print(f"[selfcheck] ✅ {label}: 地面 CSV 全件完全一致・同時保有なし（H1）")


def yearly_judge(d: pd.DataFrame) -> pd.Series:
    """学習期間 entry のみ・judge 式（score.py と $1 以内一致 実証済・正式数字は採点時の score.py）。"""
    e = d[pd.to_datetime(d["entry_time"]) <= TRAIN_END].copy()
    e["net_j"] = [e21.judge_net(-1, float(r.entry_price), float(r.exit_price), float(r.size_btc), str(r.exit_reason))
                  for r in e.itertuples()]
    return e.groupby(pd.to_datetime(e["entry_time"]).dt.year)["net_j"].agg(["size", "sum"])


def main():
    argparse.ArgumentParser().parse_args()

    base = rc._load_params()
    p21 = dict(base)
    for k in list(p21):
        if k.startswith("ENABLE_P") and k.endswith(("_LONG", "_SHORT")):
            p21[k] = (k == "ENABLE_P21_SHORT")

    print(f"[load] OHLCV preload: {gen.OHLCV_CSV.name}")
    df, _ = rc.preload(str(gen.OHLCV_CSV), p21)
    arrs = (df["timestamp_ms"].to_numpy(dtype=np.int64), df["close"].to_numpy(dtype=float),
            df["high_raw"].to_numpy(dtype=float), df["low_raw"].to_numpy(dtype=float))
    atr_a = df["atr_14"].to_numpy(dtype=float)
    g = pd.read_csv(GROUND_CSV)

    # ---- 自己検査①: 素の params・veto なし ＝ 地面 ----
    d1, s1, v1 = run_continuous(df, arrs, p21, None)
    assert_match_ground(pd.DataFrame(d1), g, "① 素 wrapper")

    # ---- 自己検査②: 床を params から veto 層へ移しても同一 ----
    p21_open = dict(p21)
    p21_open["P21_ATR14_MIN"] = 0
    floor_usd = float(p21.get("P21_ATR14_MIN", 150))
    d2, s2, v2 = run_continuous(df, arrs, p21_open, lambda i: atr_a[i] < floor_usd)
    assert_match_ground(pd.DataFrame(d2), g, "② 床→veto 層")
    print(f"  （② シグナル {s2} / veto {v2}）")

    # ---- ML ゲート（OOF prob>0.5・学習期間のみ）----
    oof = pd.read_csv(OOF_CSV)
    allow = set(oof.loc[oof["prob"] > 0.5, "bar_i"].astype(int))
    print(f"[MLゲート] OOF prob>0.5 の候補 {len(allow)} 本（教師 {len(oof)} 本中）")
    d3, s3, v3 = run_continuous(df, arrs, p21_open, lambda i: int(i) not in allow)
    d3 = pd.DataFrame(d3)
    et = pd.to_datetime(d3["entry_time"]).values
    xt = pd.to_datetime(d3["exit_time"]).values
    assert all(et[k + 1] >= xt[k] for k in range(len(d3) - 1)), "同時保有を検出（停止）"
    d3.to_csv(OUT_CSV, index=False)
    print(f"[MLゲート] シグナル {s3} / veto {v3} / トレード {len(d3)} 件 → {OUT_CSV.name}")

    # ---- 年別比較（学習期間・judge 式）----
    ya = yearly_judge(pd.DataFrame(d1))
    yb = yearly_judge(d3)
    print("\n========== 連続モード 年別（学習期間・judge式・正式は採点時 score.py） ==========")
    print("  年   : 地面(V9床)            → MLゲート             差分")
    tot_a = tot_b = 0.0
    for y in sorted(set(ya.index) | set(yb.index)):
        a_n, a_s = (int(ya.loc[y, "size"]), float(ya.loc[y, "sum"])) if y in ya.index else (0, 0.0)
        b_n, b_s = (int(yb.loc[y, "size"]), float(yb.loc[y, "sum"])) if y in yb.index else (0, 0.0)
        tot_a += a_s
        tot_b += b_s
        print(f"  {y}: {a_n:>5}件 ${a_s:>9,.1f} → {b_n:>5}件 ${b_s:>9,.1f}   {b_s - a_s:+,.1f}")
    print(f"  合計: ${tot_a:,.1f} → ${tot_b:,.1f}   {tot_b - tot_a:+,.1f}")
    print("→ 次: 年別（特に 2024）非劣化かをまこさんに報告 → GO なら採点 2025-04〜12 を score.py で 1 回")


if __name__ == "__main__":
    main()
