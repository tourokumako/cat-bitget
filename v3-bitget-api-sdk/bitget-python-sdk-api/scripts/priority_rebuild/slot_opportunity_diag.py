#!/usr/bin/env python3
"""slot_opportunity_diag.py — トレード数の天井の実測（read-only 診断・正本ツール）

まこさん承認 2026-07-24「別の戦略でも汎用的に、正確に計測できるツールに昇格できるのであれば、作成してOK」で、
段0 の使い捨て probe（scratchpad/slot_opportunity_probe.py＝1回きり・対象CSV/cap/過去数字の直書きあり）を
正本ツールへ昇格したもの。旧 probe は今後使わない。

出すもの
--------------------------------------------------------------------------
 (a) スロット占有: 売買記録から5分グリッドの同時保有 size を積み、満杯の時間比率を出す。
     どの戦略の売買記録CSVでも使える（必要列: side / size_btc / entry_time / exit_time）。
 (b) 機会の在庫: レンジ∩帯ありバーを 上端到達 / down近似天井到達 / 届かない戻り / 下端到達 / どれもなし に分割。
     レンジ系戦略用（レンジ判定は e37_scalp の計器 _load/_rg5_frames を import 再利用＝自前で再実装しない）。
     レンジを使わない戦略は --no-inventory で省略する。
 (c) ゲートの削り: 本ツールでは出さない。エンジン走行 print の発火カウンタの逐語を worklog に貼る運用。
     旧 probe はここに過去走行の数字をコードへ直書きしていた＝正確でないので廃止。

守ること
--------------------------------------------------------------------------
 - read-only＝CSV を書かない・score を呼ばない・金額を出さない（時間比率とバー数のみ）。
 - 期間は periods.py の採点窓のみ（fast-mode §8.5 / H8・手打ち禁止）。
 - cap の値・対象CSVはコードに焼かない＝引数で渡し、使った値を出力の先頭に全部印字する。
 - ⚠️ あたり付け専用＝数字を設計の固定値に焼かない（L-330）。採否は score.py 採点窓のみ。

使い方
--------------------------------------------------------------------------
  python3 slot_opportunity_diag.py <trades_csv> --short-cap-btc 0.024 --long-cap-btc 0.024
  python3 slot_opportunity_diag.py <trades_csv> --short-cap-btc 0.06 --no-inventory   # 非レンジ戦略
  python3 slot_opportunity_diag.py --selftest
"""
from __future__ import annotations

import argparse
import sys

import numpy as np
import pandas as pd

from periods import SCORE_START, SCORE_END   # 期間は periods.py が唯一の正本（H8）

REQ_COLS = ["side", "size_btc", "entry_time", "exit_time"]
EPS = 1e-9


# ══ (a) スロット占有（汎用＝どの戦略の売買記録でも）═══════════════════════
def occupancy(tr: pd.DataFrame, grid_index: pd.DatetimeIndex) -> dict[str, pd.Series]:
    """5分グリッドごとの同時保有 size（BTC）。行単位＝部分決済や add は行が期間を分担する前提。"""
    total = pd.Series(0.0, index=grid_index)
    per_side = {"SHORT": pd.Series(0.0, index=grid_index),
                "LONG": pd.Series(0.0, index=grid_index)}
    for _, r in tr.iterrows():
        seg = (grid_index >= r.entry_time) & (grid_index < r.exit_time)
        total[seg] += r.size_btc
        if r.side in per_side:
            per_side[r.side][seg] += r.size_btc
    return {"total": total, "SHORT": per_side["SHORT"], "LONG": per_side["LONG"]}


def print_occupancy(occ: dict, short_cap: float | None, long_cap: float | None,
                    total_cap: float | None) -> pd.Series:
    print("\n■ (a) スロット占有（採点窓・5分グリッド・売買記録の実測）")
    gs, gl, grid = occ["SHORT"], occ["LONG"], occ["total"]
    s_full = pd.Series(False, index=grid.index)
    print(f"   ショート保有>0 の時間比率: {(gs > EPS).mean()*100:.1f}%")
    print(f"   ロング保有>0 の時間比率: {(gl > EPS).mean()*100:.1f}%")
    if short_cap is not None:
        s_full = gs >= short_cap - EPS
        print(f"   ショート満杯（cap {short_cap} BTC・引数指定）の時間比率: {s_full.mean()*100:.2f}%")
    if long_cap is not None:
        l_full = gl >= long_cap - EPS
        print(f"   ロング満杯（cap {long_cap} BTC・引数指定）の時間比率: {l_full.mean()*100:.2f}%")
    if total_cap is not None:
        print(f"   合計満杯（cap {total_cap} BTC・引数指定）の時間比率: {(grid >= total_cap - EPS).mean()*100:.2f}%")
    print(f"   同時保有 size 分布（BTC）: 中央 {grid.median():.3f} / q90 {grid.quantile(0.9):.3f}"
          f" / 最大 {grid.max():.3f}")
    return s_full


# ══ (b) 機会の在庫（レンジ系戦略用＝RG 計器を import 再利用）═══════════════
def inventory(ts_w, h, l, rng_w, res_lo_w, res_hi_w, sup_lo_w, sup_hi_w,
              days: int, s_full: pd.Series, down_ceiling_bars: int) -> None:
    roll_hi = pd.Series(h, index=ts_w).rolling(down_ceiling_bars).max().shift(1).to_numpy()  # 当バー除く＝H2
    mid = (res_lo_w + sup_hi_w) / 2.0
    zone_ok = np.isfinite(res_hi_w) & np.isfinite(sup_hi_w)
    r_and = rng_w & zone_ok
    touch_top = r_and & (h >= res_hi_w)
    touch_dn_top = r_and & ~touch_top & (h >= roll_hi)
    pullback = r_and & ~touch_top & ~touch_dn_top & (h >= mid)
    touch_bot = r_and & (l <= sup_hi_w)
    none_ = r_and & ~touch_top & ~touch_dn_top & ~pullback & ~touch_bot
    nb = int(r_and.sum())
    print("\n■ (b) 機会の在庫（採点窓のレンジ∩帯ありバーの分割・近似＝在庫の桁の把握用）")
    print(f"   レンジ∩帯あり: {nb} バー（全 {len(ts_w)} バーの {nb/len(ts_w)*100:.1f}%・{nb/days:.0f} バー/日）")
    for name, mask in [("上端 res_hi 到達（S1圏）", touch_top),
                       (f"down近似天井（直近{down_ceiling_bars}本高値）到達", touch_dn_top),
                       ("届かない戻り（mid以上・S2在庫）", pullback),
                       ("下端 sup_hi 到達（L1圏・重複可）", touch_bot),
                       ("どれもなし", none_)]:
        n = int(mask.sum())
        print(f"   {name:<28} {n:>6} バー（{n/max(nb,1)*100:>5.1f}% / {n/days:>6.1f} バー/日）")
    if s_full.any():
        full_at_top = int((touch_top | touch_dn_top)[np.asarray(s_full)].sum())
        print(f"   天井到達 ∩ ショート満杯（機会が来たが建てられない）: {full_at_top} バー"
              f"（{full_at_top/days:.1f} バー/日）")


# ══ 本体 ════════════════════════════════════════════════════════════════
def main(a) -> None:
    end_excl = SCORE_END + pd.Timedelta(days=1)
    tr = pd.read_csv(a.trades_csv, parse_dates=["entry_time", "exit_time"])
    missing = [c for c in REQ_COLS if c not in tr.columns]
    if missing:
        raise SystemExit(f"[入力] 売買記録に必要列が無い: {missing}（この CSV は本ツール対象外）")
    tr = tr[(tr.entry_time >= SCORE_START) & (tr.entry_time < end_excl)].copy()

    print("#" * 100)
    print("# トレード数の天井の実測（slot_opportunity_diag・read-only）")
    print(f"# 期間: {SCORE_START:%Y-%m-%d} 〜 {SCORE_END:%Y-%m-%d}（periods.py 採点窓・変更不可）")
    print(f"# 売買記録: {a.trades_csv}（期間内 {len(tr)} 行・引数指定）")
    print(f"# cap: ショート {a.short_cap_btc} / ロング {a.long_cap_btc} / 合計 {a.total_cap_btc}（BTC・引数指定＝コードに焼かない）")
    print(f"# (b) 機会の在庫: {'省略（--no-inventory）' if a.no_inventory else f'出す（down近似天井=直近{a.down_ceiling_bars}本高値）'}")
    print("# ⚠️ あたり付け専用＝値を設計に焼かない（L-330）。採否は score.py 採点窓。金額は出さない。")
    print("#" * 100)

    if a.no_inventory:
        grid_index = pd.date_range(SCORE_START, end_excl, freq="5min", inclusive="left")
        days = (grid_index.max() - grid_index.min()).days + 1
        occ = occupancy(tr, grid_index)
        print_occupancy(occ, a.short_cap_btc, a.long_cap_btc, a.total_cap_btc)
        print(f"\n[集計] {days} 日・{len(grid_index)} グリッド")
        return

    import e37_scalp as e37   # レンジ計器の正本を再利用（自前再実装しない）
    print("[load] 5分足＋レンジ判定（e37._load / _rg5_frames を再利用）...", flush=True)
    df = e37._load(0)
    _z1h, up, rng, res_lo, res_hi, sup_lo, sup_hi = e37._rg5_frames(df, adaptive_k=e37.V25_K)
    ts = pd.DatetimeIndex(df["ts"])
    m = (ts >= SCORE_START) & (ts < end_excl)
    ts_w = ts[m]
    h = df["high"].to_numpy(float)[m]
    l = df["low"].to_numpy(float)[m]
    days = (ts_w.max() - ts_w.min()).days + 1
    print(f"[trades] {len(tr)} 約定行 / {days} 日")

    occ = occupancy(tr, ts_w)
    s_full = print_occupancy(occ, a.short_cap_btc, a.long_cap_btc, a.total_cap_btc)
    inventory(ts_w, h, l, rng[np.asarray(m)], res_lo[np.asarray(m)], res_hi[np.asarray(m)],
              sup_lo[np.asarray(m)], sup_hi[np.asarray(m)], days, s_full, a.down_ceiling_bars)
    print("\n■ (c) ゲートの削り: 本ツールでは出さない＝エンジン走行 print の発火カウンタの逐語を worklog に貼る"
          "（過去数字のコード直書きは廃止）")
    print("\n⚠️ あたり付け専用＝優先順位の根拠にのみ使う・値を焼かない（L-330）・採否は採点窓 score.py")


# ══ 自己検査 ════════════════════════════════════════════════════════════
def selftest() -> None:
    """守ると言っていることを機械で確かめる＋占有計算の既知答えテスト。"""
    import ast
    import inspect
    ng = []
    src = inspect.getsource(sys.modules[__name__])
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr in ("to_csv", "to_parquet", "write_sidecar"):
            ng.append(f"read-only なのに書き出しを呼んでいる: {node.func.attr}")
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mods = [x.name for x in node.names] + ([node.module] if isinstance(node, ast.ImportFrom) else [])
            if any(mm and mm.split(".")[0] == "score" for mm in mods):
                ng.append("read-only なのに score を import している")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr == "Timestamp" and node.args \
                and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
            ng.append(f"期間を手打ちしている: pd.Timestamp('{node.args[0].value}')")
    _from_periods = {n for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
                     and node.module == "periods" for n in [x.name for x in node.names]}
    for need in ("SCORE_START", "SCORE_END"):
        if need not in _from_periods:
            ng.append(f"{need} を periods.py から import していない")
    # 旧 probe の直書き（cap・対象CSV）が計測経路に残っていないか
    # ⚠️ src 全体を見ると selftest 自身の検査文字列・既知答えテストに自己一致する（observe_diag 2026-07-21 実測の型）
    #    ＝計測経路（main/occupancy/print_occupancy/inventory）のソースだけを見る
    _meas_src = "".join(inspect.getsource(f) for f in (main, occupancy, print_occupancy, inventory))
    for lit in ("0.024", "trades_e37"):
        if lit in _meas_src:
            ng.append(f"計測経路に直書きが残っている: {lit}")
    # 既知答えテスト＝占有計算（2玉が30分重なる合成データ）
    idx = pd.date_range(SCORE_START, periods=24, freq="5min")     # 2時間
    tr = pd.DataFrame([
        {"side": "SHORT", "size_btc": 0.012,
         "entry_time": idx[0], "exit_time": idx[12]},              # 0〜60分（12グリッド）
        {"side": "SHORT", "size_btc": 0.012,
         "entry_time": idx[6], "exit_time": idx[18]},              # 30〜90分（12グリッド）
    ])
    occ = occupancy(tr, idx)
    # 重なり＝30〜60分の6グリッドで 0.024。満杯比率＝6/24=25%
    if abs((occ["SHORT"] >= 0.024 - EPS).mean() - 6 / 24) > 1e-12:
        ng.append(f"占有の既知答えが合わない: 満杯比率 {(occ['SHORT'] >= 0.024 - EPS).mean():.4f} ≠ 0.25")
    if abs(occ["SHORT"].max() - 0.024) > 1e-12 or abs(occ["total"].max() - 0.024) > 1e-12:
        ng.append("占有の最大値が合わない")
    if occ["LONG"].max() > EPS:
        ng.append("LONG に足していないのに占有が出ている")
    print("=" * 80)
    print("slot_opportunity_diag 自己検査")
    print("=" * 80)
    if ng:
        for x in ng:
            print(f"  ❌ {x}")
        raise SystemExit(1)
    print("  ✅ 全部 pass（read-only / 期間は periods 正本 / cap・CSV 直書きなし / 占有の既知答え一致）")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        ap = argparse.ArgumentParser(description="トレード数の天井の実測（read-only 診断・金額を出さない）")
        ap.add_argument("trades_csv", help="売買記録CSV（side/size_btc/entry_time/exit_time 必須）")
        ap.add_argument("--short-cap-btc", type=float, default=None, help="ショート枠の cap（BTC）＝満杯判定に使う")
        ap.add_argument("--long-cap-btc", type=float, default=None, help="ロング枠の cap（BTC）")
        ap.add_argument("--total-cap-btc", type=float, default=None, help="合計の cap（BTC）")
        ap.add_argument("--down-ceiling-bars", type=int, default=12,
                        help="down 型の近似天井＝直近何本の高値か（既定12＝1時間・近似の注記つきで印字）")
        ap.add_argument("--no-inventory", action="store_true",
                        help="(b) 機会の在庫を省略（レンジ判定を使わない戦略用）")
        main(ap.parse_args())
