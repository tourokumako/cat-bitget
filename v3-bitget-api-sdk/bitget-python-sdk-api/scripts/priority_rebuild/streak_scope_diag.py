#!/usr/bin/env python3
"""streak_scope_diag.py — 段3 の持続（streak）が何に掛かっているかを、値決め窓で1バーずつ比べる（M2-E-4a・読み取り専用）。

何を測るか（M2-E-4a・2026-09-20）
  いまの組む側（engine_tuner_gen.sample_regime_build）は、持続（streak・法則 R4）を「帯の条件1つ（cond_b）」に掛けている
  （cond_f の inner に cond_b を写している）。§2.2 の段3 が求めるのは「成立の連続本数」＝段1 ∩ 段2a ∩ 段2b ∩ 段2c の
  全体が n本 続くこと。この2つが同じ真偽になるかを、実物の束で1バーずつ比べて数える。

  いまの形  on_cur  ＝ A ∩ B ∩ C ∩ D ∩ G ∩ streak_n(B)          （束の hysteresis の「入る条件」そのまま）
  §2.2 の形 on_want ＝ streak_n(A ∩ B ∩ C ∩ D ∩ G)               （streak の式は実行器と同じ rolling(n).sum() >= n）
  そのあと、同じ「出る条件」と保つ上限で状態（_hold_state）にしたものも比べる。

決まり＝売買記録CSVを書かない・審判（score.py）を呼ばない・コードを直さない（違えば直し方を出すだけ・直すのは別の番号）。
       値決め窓だけ（採点窓は1バーも使わない・H8）。未来は見ない（rolling は過去 n本だけ・H2）。
       束は組む側（sample_regime_build）に出させる＝私（CC）が条件を1つも書かない。乱数は使わない（order_n＝案の番号）。

使い方:
  python3 streak_scope_diag.py --builds 3          # 案の番号 0〜2 の束で測る
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import numpy as np
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import engine_tuner_exec as ex          # noqa: E402  _eval_tree・_hold_state（改造しない）
import engine_tuner_gen as g            # noqa: E402  _regime_on_conds＝束の形の読み方の正本（M2-E-4d・束1）


def _streak(col: np.ndarray, n: int) -> np.ndarray:
    """実行器の streak と同じ式（engine_tuner_exec._eval_cond の form == "streak"）＝直近 n本 全部 真。"""
    s = pd.Series(np.asarray(col, bool).astype(float))
    return (s.rolling(n).sum() >= n).to_numpy()


def _split_on(hyst: dict, bd: dict) -> tuple[list, dict | None]:
    """hysteresis の「入る条件」から、streak の条件（F）と、成立の条件の並びを分ける。

    ★M2-E-4d（束1・2026-09-25）＝成立の条件の並びは組む側の `_regime_on_conds`（束の形の読み方の正本）で読む。
      新しい形（入る条件＝F 1つ・内側が束）なら F の内側の並び、直す前の形なら入る条件から F を除いた並び。
    """
    on_all = list((hyst.get("on") or {}).get("all") or [])
    f = [c for c in on_all if isinstance(c, dict) and c.get("form") == "streak"]
    return g._regime_on_conds(bd), (f[0] if f else None)


def _name(c: dict) -> str:
    """条件1つを短い文字にする（画面に出すだけ）。★内側が束（all）のときも読める（M2-E-4d・束1）。"""
    if "all" in c:
        return "all(" + " ∧ ".join(_name(x) for x in c["all"]) + ")"
    if "not" in c:
        return "not(" + _name(c["not"]) + ")"
    if "bool_col" in c:
        return f"bool:{c['bool_col']}"
    m = (c.get("material") or [{}])[0]
    mat = m.get("geo") or f"{m.get('family')}{m.get('param', '')}__{m.get('tf', '')}"
    return f"{c.get('form')}:{mat}:{c.get('side', '')}:{(c.get('value') or {}).get('threshold_q', '')}"


def compare(df: pd.DataFrame, bd: dict, geo: dict, qt: dict, win: np.ndarray, lane: str = "") -> dict:
    tree = bd["entry"]["tree"]
    hyst = tree["all"][0]
    if hyst.get("form") != "hysteresis":
        raise SystemExit("[streak_scope] 束の先頭が hysteresis ではない（組む側の形が変わった＝この診断の前提が崩れた）")
    rest, f = _split_on(hyst, bd)      # ★成立の並びは組む側の読み方（_regime_on_conds）から（M2-E-4d・束1）
    if f is None:
        raise SystemExit("[streak_scope] 入る条件に streak が無い（法則 R4 の形が束に入っていない）")
    n = int(f["value"]["n"])
    n_hold = int(hyst["value"]["n"])
    on_cur = ex._eval_tree(hyst["on"], df, geo, lane, qt, allow_bool_col=True)
    base = ex._eval_tree({"all": rest}, df, geo, lane, qt, allow_bool_col=True)
    on_want = _streak(base, n)
    off = ex._eval_tree(hyst["off"], df, geo, lane, qt, allow_bool_col=True)
    st_cur = ex._hold_state(on_cur, off, n_hold)
    st_want = ex._hold_state(on_want, off, n_hold)
    # 実行器が作る列（build_regime_columns）と on_cur→状態 が同じかも照らす（この診断の式の確かめ）
    d2 = df.copy()
    d2.attrs = {}
    rec = {"meta": {"lane": lane, "regime": {"name": "range", "build": bd}}}
    ex.build_regime_columns(d2, rec, geo, qt)
    st_exec = d2[bd["entry"]["out_col"]].to_numpy(bool)

    def _cnt(a):
        return int(np.asarray(a, bool)[win].sum())

    bars = int(win.sum())
    diff_on = _cnt(on_cur != on_want)
    diff_st = _cnt(st_cur != st_want)
    return {
        "streak_n": n, "hold_n": n_hold, "bars": bars,
        "streak_inner": _name(f["inner"]),
        "conds": [_name(c) for c in rest],
        "on_cur_true": _cnt(on_cur), "on_want_true": _cnt(on_want),
        "on_diff": diff_on, "on_diff_pct": round(100.0 * diff_on / bars, 3) if bars else None,
        "on_cur_true_want_false": _cnt(on_cur & ~on_want),
        "on_cur_true_want_false_pct_of_cur": (round(100.0 * _cnt(on_cur & ~on_want) / _cnt(on_cur), 2)
                                              if _cnt(on_cur) else None),
        "on_cur_false_want_true": _cnt(~on_cur & on_want),
        "state_cur_true": _cnt(st_cur), "state_want_true": _cnt(st_want),
        "state_diff": diff_st, "state_diff_pct": round(100.0 * diff_st / bars, 3) if bars else None,
        "state_cur_true_want_false": _cnt(st_cur & ~st_want),
        "state_cur_false_want_true": _cnt(~st_cur & st_want),
        "diag_matches_exec": bool(np.array_equal(st_cur[win], st_exec[win])),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="段3 の持続（streak）の掛かり方を、値決め窓で1バーずつ比べる（読み取り専用）")
    ap.add_argument("--builds", type=int, default=3, help="案の番号 0〜N-1 の束で測る")
    ap.add_argument("--strategy", default="e38")
    a = ap.parse_args()

    import engine_tuner as et
    import engine_tuner_gen as g
    from periods import SEARCH_END, SEARCH_START

    ad = et.load_adapter(a.strategy)
    df, = et.load_windows_cached(ad, [(SEARCH_START, SEARCH_END)], et.WARM)
    ts = pd.to_datetime(df["ts"])
    win = ((ts >= pd.Timestamp(SEARCH_START)) & (ts < pd.Timestamp(SEARCH_END))).to_numpy()
    geo = g._geo_of(df)
    lm, _w = g.load_limits()
    lm = g.resolve_hold_range(lm, a.strategy)
    tb = g.load_signal_table()
    pool, tfs, _ = g.material_pool()

    builds = []
    for i in range(a.builds):
        bd, draw = g.sample_regime_build(lm, pool, tfs, tb, order_n=i)
        builds.append((i, g.strip_marks(bd), draw))
    # ★解決表を作る関数（needed_qkeys）は入口の木（entry.connective）も歩く。この診断は入口を測らないので、
    #   束の最初の普通の条件を1つ置いただけの木にする（分位の鍵は束の分と同じ＝鍵が増えない）。
    def _first_plain(bd):
        for c in g._regime_on_conds(bd):      # ★成立の並び（持続の内側）から探す（M2-E-4d・束1）
            if isinstance(c, dict) and c.get("form") == "level" and "material" in c:
                return json.loads(json.dumps(c))
        raise SystemExit("[streak_scope] 束に普通の条件（level）が1つも無い")
    recipes = [{"meta": {"strategy": a.strategy, "logic_id": f"SS_{i}", "side": "SHORT",
                         "regime": {"name": "range", "entry_col": bd["entry"]["out_col"], "build": bd}},
                "pre_filter": [],
                "entry": {"connective": {"all": [_first_plain(bd)]}}}
               for i, bd, _d in builds]
    for rec in recipes:                              # 需給の材料を持つ束なら、その列を足す（regime_r9_diag.measure と同じ）
        dem = ex.demand_cols_in(rec)
        if dem:
            df = ex.attach_demand_columns(df, sorted(dem))
    qt = g.build_qtable(df, geo, recipes, g.quantile_list(lm), SEARCH_START, SEARCH_END)

    print(f"[streak_scope] 値決め窓 {SEARCH_START}〜{SEARCH_END}・束 {len(builds)}本")
    for i, bd, _d in builds:
        r = compare(df, bd, geo, qt, win)
        print(f"\n── 案 {i} ──")
        print(json.dumps(r, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
