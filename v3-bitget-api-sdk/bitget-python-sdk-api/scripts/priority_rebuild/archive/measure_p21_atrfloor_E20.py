#!/usr/bin/env python3
"""measure_p21_atrfloor_E20.py — E20: P21 ATR 床の価格非依存化（USD 150 → ATR% 床・veto 層）

設計（まこさん GO 2026-06-12・ledger E0.4 改善欄）:
  P21_ATR14_MIN=150 は USD 絶対値で、BTC 価格上昇とともに実効 % 床が薄まる（$40k 時代 0.375% →
  $100k 時代 0.15%）＝V9 手書き値の中の価格依存。Entry シグナル時点の atr_14/close×100 が
  床未満なら発注しない veto 層（V9 不変・check_entry_priority の後段）で床を % に直す。

候補（§5・事前宣言）: ATR% 床 {0.15, 0.20, 0.25}。
選定ルール（事前宣言）: 学習期間（2021-04〜2024-12・score.py 採点＝trail maker 新計器）net 最大、
  かつ 2024 年（直近年）が no-veto 比で非劣化。どれも no-veto を超えなければレバーを閉じる（正直に）。
採点: 選定 1 案のみ 採点期間 2025-04〜12 を score.py で 1 回（新地面 $2,697.32 と比較）。

実装（自作 net 計算なし・V9 不変）:
  連続モードの wrapper ループ＝rc.run() の処理順を 1 対 1 で複製（pending TTL2・fill=翌バー high≥limit・
  SHORT limit=Decimal(close)×1.0001・add なし P21）。position 寿命は train_p21_exit_E19.simulate_exit
  （rc._check_exits_replay/_record_trade・Phase1 で地面 4,175 件完全一致 済）。
  自己検査 = veto なし（--selfcheck）で地面 CSV と (entry_time/exit_time/exit_reason/net) 全件完全一致。

H 照合: H1=P21 単独 0.06・同時保有 1 ポジ（実測 assert）／H2=veto は t 時点の atr_14/close のみ／
H6=床は %（価格非依存）／H8=選定は学習期間のみ・採点 1 回／H13=judge 不変（score.py を呼ぶだけ）／
H16=1変更（Entry の ATR 床のみ・Exit/サイズ/add 不変）。
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
from strategies.cat_v9_decider import check_entry_priority   # noqa: E402  V9 判定（import のみ）

GROUND_CSV = ROOT / "results" / "priority_rebuild" / "ratchet" / "trades_p21_E16_ground.csv"
OUT_DIR    = ROOT / "results" / "priority_rebuild" / "ratchet"
FLOORS     = (0.15, 0.20, 0.25)   # ATR% 床候補（事前宣言）
PEND_FIELDS = ("adx_at_entry", "bb_mid_slope_at_entry", "rsi_at_entry", "rsi_slope_at_entry",
               "stoch_k_at_entry", "stoch_d_at_entry", "bb_width_at_entry")
SIG_COLS = {"adx_at_entry": "adx", "bb_mid_slope_at_entry": "bb_mid_slope", "rsi_at_entry": "rsi_short",
            "rsi_slope_at_entry": "rsi_slope_short", "stoch_k_at_entry": "stoch_k",
            "stoch_d_at_entry": "stoch_d", "bb_width_at_entry": "bb_width"}


def run_continuous_veto(df, arrs, p21: dict, atr_floor_pct):
    """rc.run() の P21 単独・連続モードを 1 対 1 で複製し、entry シグナル時点に ATR% veto を挟む。"""
    ts_a, cl_a, hi_a, lo_a = arrs
    n = len(df)
    bar_ms = int(ts_a[1] - ts_a[0])
    idx_of_ts = {int(t): k for k, t in enumerate(ts_a)}
    atr_a = df["atr_14"].to_numpy(dtype=float)
    assert "atr_14" in df.columns, "atr_14 列が無い（停止）"

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
                    break   # データ末尾まで未決済（地面に FORCE 行なし＝発生しない想定・発生したら件数不一致で検出）
                trades.append(t)
                # 再開 = exit バー（rc.run() は同バー step6 で次のエントリー判定可）
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
                atr_pct = atr_a[i] / cl_a[i] * 100.0
                if atr_floor_pct is not None and atr_pct < atr_floor_pct:
                    n_veto += 1
                else:
                    pending = {"limit_price": float(Decimal(str(cl_a[i])) * Decimal("1.0001")),
                               "placed_bar_ms": ts_ms}
                    for f, col in SIG_COLS.items():
                        pending[f] = float(df.at[i, col]) if col in df.columns else float("nan")
        i += 1
    return trades, n_sig, n_veto


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selfcheck", action="store_true", help="veto なしで地面 CSV と全件一致を検査")
    args = ap.parse_args()

    base = rc._load_params()
    p21 = dict(base)
    for k in list(p21):
        if k.startswith("ENABLE_P") and k.endswith(("_LONG", "_SHORT")):
            p21[k] = (k == "ENABLE_P21_SHORT")

    print(f"[load] OHLCV preload: {gen.OHLCV_CSV.name}")
    df, _ = rc.preload(str(gen.OHLCV_CSV), p21)
    arrs = (df["timestamp_ms"].to_numpy(dtype=np.int64), df["close"].to_numpy(dtype=float),
            df["high_raw"].to_numpy(dtype=float), df["low_raw"].to_numpy(dtype=float))

    if args.selfcheck:
        g = pd.read_csv(GROUND_CSV)
        trades, n_sig, n_veto = run_continuous_veto(df, arrs, p21, None)
        d = pd.DataFrame(trades)
        print(f"[selfcheck] wrapper {len(d)} 件 vs 地面 {len(g)} 件 / シグナル {n_sig} / veto {n_veto}")
        assert len(d) == len(g), f"件数不一致 {len(d)} vs {len(g)}（停止）"
        ng = 0
        for a, b in zip(d.itertuples(), g.itertuples()):
            ok = (a.entry_time == b.entry_time and a.exit_time == b.exit_time
                  and a.exit_reason == b.exit_reason and abs(float(a.net_usd) - float(b.net_usd)) <= 0.01)
            if not ok:
                ng += 1
                if ng <= 5:
                    print(f"  [不一致] {a.entry_time} vs {b.entry_time} / {a.exit_reason} vs {b.exit_reason}")
        assert ng == 0, f"自己検査 FAIL: {ng} 件不一致（停止）"
        # H1: P21 単独＝同時保有は常に 1 ポジ 0.06（entry/exit の重なりが無いことを実測）
        et = pd.to_datetime(d["entry_time"]).values
        xt = pd.to_datetime(d["exit_time"]).values
        assert all(et[k + 1] >= xt[k] for k in range(len(d) - 1)), "同時保有を検出（連続モード破れ・停止）"
        print("[selfcheck] ✅ veto なし wrapper = 地面 CSV 全件完全一致・同時保有なし（H1）")
        return

    for floor in FLOORS:
        trades, n_sig, n_veto = run_continuous_veto(df, arrs, p21, floor)
        d = pd.DataFrame(trades)
        out = OUT_DIR / f"trades_p21_E20_floor{str(floor).replace('.', '')}.csv"
        d.to_csv(out, index=False)
        print(f"[floor {floor}%] シグナル {n_sig} / veto {n_veto} ({n_veto/max(n_sig,1)*100:.1f}%) "
              f"/ トレード {len(d)} 件 → {out.name}")
    print("→ 次: 各 floor を score.py で学習期間（2021-04-01〜2024-12-31）採点し、事前宣言ルールで 1 案選定")


if __name__ == "__main__":
    main()
