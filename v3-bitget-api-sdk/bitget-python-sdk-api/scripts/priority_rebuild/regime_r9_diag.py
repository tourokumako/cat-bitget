#!/usr/bin/env python3
"""regime_r9_diag.py — 場面の判定（レンジ）について、法則 R9 の測るもの3つを出す読み取り専用の診断（M2-5-4）。

2026-08-23（53回目）・まこさん承認 327e7f80008f…（受け入れ条件の C）。

法則 R9（regime_detection_kb.md §11-2・出どころ indicator_combination_kb.md §7・E37 の失敗の本体）
  ① レンジと判定した時間の割合   ＝ 値決め窓で判定が真のバー ÷ 全バー
  ② その中の玉の成績             ＝ 判定の列を entry_col に向けて run_recipe → 値決め窓の玉だけを score.score に通す
                                   → 件数・net 合計・件数/日（★net は審判の数字をそのまま出す＝この診断は計算しない。勝率は審判が返さないので出さない）
  ③ 実はトレンドだった割合       ＝ 判定が真のバーのうち、observe_diag._regime_labels の「強さ」（先 n本の ER が窓の
                                   中央値以上）が真の割合。先読み n は成績表と同じ2つ（_regime_horizons）
                                   ★未来を見る印（H2OK 注記済み）＝評価にだけ使う。判定の列や入口には入れない。

比較の行＝RG-v5（range_ok_rg5＝いまの E38 の判定）の①②③を同じ式で出す。

決まり＝売買記録CSVを書かない・_output_and_report を呼ばない・採用を書き出さない・審判（score.py）は改造しない。
        値決め窓だけ（採点窓は1バーも使わない・H8）。出た数字で案を選ばない（採否は M2-11・まこさん）。
        1分足・3分足を含む案が解決表の所で止まったら「測れない」と出して先へ進む（嘘の0を出さない）。

使い方:
  python3 regime_r9_diag.py --build 3 --seed 53        # 1位から順に束を3本 組んで測る
  python3 regime_r9_diag.py --recipe path.json         # 束を持つレシピ1本を測る
  python3 regime_r9_diag.py --selftest                 # 合成データの番人（わざと壊して止まる3件＋未来参照の grep）
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

import engine_tuner_exec as ex          # noqa: E402  build_regime_columns・run_recipe（改造しない）
import score                            # noqa: E402  審判（改造しない・import して呼ぶだけ）


# ══ 測るもの3つ（列と印から出す・データの読み方には依存しない）══════════════════════════════
def r9_share(col: np.ndarray) -> float:
    """①レンジと判定した時間の割合（0〜1）。"""
    col = np.asarray(col, bool)
    return float(col.mean()) if len(col) else float("nan")


def r9_trend_share(col: np.ndarray, strong: np.ndarray, usable: np.ndarray) -> float:
    """③実はトレンドだった割合（0〜1）＝判定が真 ∧ 印が使えるバーのうち、「強さ」の印が真の割合。"""
    col = np.asarray(col, bool)
    m = col & np.asarray(usable, bool)
    if not m.any():
        return float("nan")
    return float(np.asarray(strong, bool)[m].mean())


def r9_trades(df: pd.DataFrame, recipe: dict, entry_col: str, qtable: dict | None, start, end) -> dict:
    """②その中の玉の成績＝判定の列を entry_col に向けて走らせ、値決め窓の玉を審判に通す。

    ★build は None にする（列は呼ぶ側が build_regime_columns で既に df に作ってある。G5 の「out_col と entry_col が
      同じ名前」の上書き防止に当たらないように、宣言だけを差し替える）。
    """
    rec = json.loads(json.dumps(recipe))
    rg = rec["meta"]["regime"]
    rg["entry_col"] = str(entry_col)
    rg["build"] = None
    trades, _rep = ex.run_recipe(df, rec, qtable=qtable)
    t = pd.DataFrame(trades)
    days = max((pd.Timestamp(end) - pd.Timestamp(start)).days, 1)
    if len(t):
        et = pd.to_datetime(t["entry_time"])
        t = t[(et >= pd.Timestamp(start)) & (et < pd.Timestamp(end))].reset_index(drop=True)
    if not len(t):
        return {"n": 0, "net": 0.0, "per_day": 0.0}
    res = score.score(t)                       # ★審判の数字をそのまま（H13）
    return {"n": int(len(t)), "net": float(res["total"]),
            # ★勝率は出さない＝審判（score.score）が返さない数字で、この診断が玉の損益から計算するのは H13・§2.9① に反する
            #   （受け入れ条件 C-2 には「勝率」と書いたが、実物を確かめて外した・worklog 20260823 §9）
            "per_day": len(t) / days}


def _labels_for(df_win: pd.DataFrame) -> dict:
    """観察の道具の正解の印（強さ）を、値決め窓の close から作る。戻り＝{n: (強さ, 使える)}。"""
    import observe_diag as od
    out = {}
    for n in od._regime_horizons():
        lab = od._regime_labels(df_win[["close"]].astype(float), int(n))
        s, u = lab["強さ"]
        out[int(n)] = (s.to_numpy(bool), u.to_numpy(bool))
    return out


# ══ 実データで測る ═══════════════════════════════════════════════════════════════════
def measure(df: pd.DataFrame, recipes: list[dict], start, end, with_trades: bool = True) -> list[dict]:
    """束ごとの R9 の3つ ＋ RG-v5 の行。戻り＝1行1辞書（機械が読む形）。"""
    import engine_tuner_gen as g
    for rec in recipes:                        # fail-closed＝束の無いレシピは測らない（先に見る）
        if not ((rec.get("meta") or {}).get("regime") or {}).get("build"):
            raise SystemExit(f"[R9] レシピ {rec['meta'].get('logic_id')} に判定の束（meta.regime.build）が無い（fail-closed）")
    ts = pd.to_datetime(df["ts"])
    win = ((ts >= pd.Timestamp(start)) & (ts < pd.Timestamp(end))).to_numpy()
    labels = _labels_for(df.loc[win].reset_index(drop=True))
    geo = g._geo_of(df)
    rows = []

    def _row(name, col_full, rec, entry_col, qt, note="", df_run=None):
        col = np.asarray(col_full, bool)[win]
        r = {"判定": name, "①時間の割合": r9_share(col)}
        for n, (s, u) in labels.items():
            r[f"③実はトレンド(先{n}本)"] = r9_trend_share(col, s, u)
        if with_trades and rec is not None:
            r["②玉"] = r9_trades(df if df_run is None else df_run, rec, entry_col, qt, start, end)
        if note:
            r["注"] = note
        return r

    # ★2026-09-11（M2-E-3 の手順3・設計書の完成の条件 条件10）＝解決表を1回だけ作る。
    #   直す前＝束1本ごとに `_qtable(df, geo, [rec], …)` を呼んでいた（下のくり返しの中）。
    #   解決表の鍵は材料1本ずつに付く名前で、同じ材料はどの束から来ても同じ鍵・同じ分布になる。
    #   だから束を全部 渡すと、鍵が増えるだけ（使わない鍵が在っても、実行器は名前で引くので影響しない）。
    #   実測＝束50本が使う鍵 382件 → 重なりを除くと 251件（34.3%減・`gen_s22_fidelity.py --keys 50`）。
    #   ★止まり方が変わる＝直す前は、ある束の鍵が解けないとその束だけ「測れない」と出して次へ進んだ。
    #     まとめて作ると、その分岐に入らない。代わりに `build_qtable` の中の
    #     「有効標本がゼロで解決できない鍵は表から落とす」が効き、その鍵を使う束は実行器の G5 で拒否される。
    #     どちらも嘘の閾値は作らないが、画面に出る文言が変わる（設計書 4-13 に書いた）。
    # ★2026-09-16（監査 cp36 の M-4）＝解決表を作る前に、需給の列を足す。
    #   なぜ要るか＝入口に需給の材料（taker_ls など）を持つレシピでは、需給の列が df に無いと
    #   解決表を作る所で止まり、束が全部「測れない」になる（本走は足している＝`run_recipe` の中）。
    #   ★足すのは、レシピが実際に使っている需給の名前だけ（`demand_cols_in` が読む）。
    for _rec in recipes:
        _dem = ex.demand_cols_in(_rec)
        if _dem:
            df = ex.attach_demand_columns(df, sorted(_dem))

    qt_all = None
    qt_err = None
    if recipes:
        try:
            qt_all = _qtable(df, geo, recipes, start, end)
        except SystemExit as e:            # 73番の型（1m/3m の元データ不足など）＝全部の束を「測れない」にする
            qt_err = str(e)[:80]

    # RG-v5（比べる相手）＝いまの E38 の判定。玉は既定の宣言（entry_col=range_ok_rg5）のまま走らせる
    base_rec = recipes[0] if recipes else None
    if "range_ok_rg5" in df.columns:
        rows.append(_row("RG-v5（いまの E38）", df["range_ok_rg5"].to_numpy(bool), base_rec,
                         "range_ok_rg5", None if base_rec is None else qt_all))
    for rec in recipes:
        bd = rec["meta"]["regime"]["build"]
        out_col = bd["entry"]["out_col"]
        if qt_err is not None:
            rows.append({"判定": rec["meta"].get("logic_id"), "注": f"測れない: {qt_err}"})
            continue
        qt = qt_all                        # ★作り直さない（上で1回 作った表を使い回す）
        d2 = df.copy()
        d2.attrs = {}
        ex.build_regime_columns(d2, rec, geo, qt)
        draw = (rec.get("meta") or {}).get("regime_draw")
        rows.append(_row(rec["meta"].get("logic_id"), d2[out_col].to_numpy(bool), rec, out_col, qt,
                         note=json.dumps(draw, ensure_ascii=False) if draw else "", df_run=d2))
    return rows


def _qtable(df, geo, recipes, start, end) -> dict:
    import engine_tuner_gen as g
    lm, _w = g.load_limits()
    return g.build_qtable(df, geo, recipes, g.quantile_list(lm), start, end)


def print_stage_candidates(stage: str) -> int:
    """段ごとの候補の一覧を画面に出す（M2-E-2 の M-5・2026-09-16 新設・読むだけ）。

    なぜ要るか（監査 cp36 の M-5）＝段ごとに何が候補に出ているかを、まこさんが画面で見る口が
    1つも無かった。**案も売買も作らない。**成績表の順に並べて出すだけ。

    ★候補を作るのは `engine_tuner_gen.build_stage_candidates`（組む側と同じ関数）。
      ここに絞りを書き写さない（恒久の決まり69番）。
    """
    import engine_tuner_gen as g
    lm, _ = g.load_limits()
    lm = g.resolve_hold_range(lm, "e38")
    table = g.load_signal_table()
    _pool, tfs, _ = g.material_pool()
    laws = g.laws_for_scene("range")
    cands = g.build_stage_candidates(stage, laws, table, tfs, lm)
    print(f"[{stage} の候補] {len(cands)} 本（成績表の順・読むだけ・案も売買も作らない）")
    print("順位\t指標\t時間足\t列\t分離力")
    for c in cands:
        _acc = "—" if c["acc"] is None else f"{c['acc']:.3f}"
        print(f"{c['rank']}\t{c['family']}\t{c['tf']}\t{c['col']}\t{_acc}")
    return 0


def _print_rows(rows: list[dict]) -> None:
    print("\n[R9 の測るもの3つ]（値決め窓だけ・数字は審判と印の出力・この診断は案を選ばない）")
    for r in rows:
        if "注" in r and "①時間の割合" not in r:
            print(f"  {r['判定']}: {r['注']}")
            continue
        t = r.get("②玉")
        tt = (f"②玉 {t['n']}件 net ${t['net']:+,.0f} {t['per_day']:.2f}件/日" if t and t["n"]
              else ("②玉 0件" if t is not None else "②玉 （測っていない）"))
        tr = " ".join(f"{k.replace('③実はトレンド', '③')}={v:.1%}" if v == v else f"{k}=nan"
                      for k, v in r.items() if k.startswith("③"))
        print(f"  {r['判定']}: ①{r['①時間の割合']:.2%} ／ {tt} ／ {tr}"
              + (f" ／ {r['注']}" if r.get("注") else ""))


# ══ 番人（合成データ・実データの試行ゼロ）════════════════════════════════════════════════
def selftest() -> int:
    ng = []
    n = 2000
    col_all = np.ones(n, bool)
    col_none = np.zeros(n, bool)
    strong = (np.arange(n) % 4 == 0)
    usable = np.ones(n, bool)
    # ① 判定が全部 真なら 100%・全部 偽なら 0%
    if r9_share(col_all) != 1.0 or r9_share(col_none) != 0.0:
        ng.append("①: 全部 真で 100%・全部 偽で 0% にならない")
    # ② 印を反転させると ③ が 1−x になる（わざと壊す）
    x = r9_trend_share(col_all, strong, usable)
    y = r9_trend_share(col_all, ~strong, usable)
    if abs((x + y) - 1.0) > 1e-12 or abs(x - 0.25) > 1e-12:
        ng.append(f"②: 印を反転しても 1−x にならない（x={x}, y={y}）")
    if r9_trend_share(col_none, strong, usable) == r9_trend_share(col_none, strong, usable):   # nan は nan と等しくない
        ng.append("②: 判定が1本も真でないのに nan でない（嘘の0を出している）")
    # ③ 判定の列が無いレシピは止まる（fail-closed）
    df = pd.DataFrame({"ts": pd.date_range("2024-03-01", periods=n, freq="5min"), "close": 100.0 + np.arange(n) % 7})
    try:
        measure(df, [{"meta": {"logic_id": "x", "regime": {"name": "range", "entry_col": "range_ok_rg5", "build": None}}}],
                df["ts"].iloc[0], df["ts"].iloc[-1], with_trades=False)
        ng.append("③: 判定の束が無いレシピで止まらない")
    except SystemExit:
        pass
    # ④ 未来参照の式をこのファイルに書いていない
    import ast
    tree = ast.parse(pathlib.Path(__file__).read_text(encoding="utf-8"))
    bad4 = []
    for node in ast.walk(tree):                 # ★コードの構文木で見る＝説明文・コメントの文字には反応しない
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "shift":
            if node.args and isinstance(node.args[0], ast.UnaryOp) and isinstance(node.args[0].op, ast.USub):
                bad4.append(f"shift(-…) 行 {node.lineno}")
        if isinstance(node, ast.keyword) and node.arg == "center" and isinstance(node.value, ast.Constant) and node.value.value is True:
            bad4.append(f"center=True 行 {node.lineno}")
    if bad4:
        ng.append(f"④: 診断のコードに未来参照の式が在る: {bad4}")
    # ⑤ 印の作り方が観察の道具の実物と同じ関数であること（写しを作っていない）
    import observe_diag as od
    if not hasattr(od, "_regime_labels") or not hasattr(od, "_regime_horizons"):
        ng.append("⑤: observe_diag の印の関数が見つからない")
    print(f"[selftest] ①100%/0% ／ ②反転で 1−x（x={x:.2f}）・真0本は nan ／ ③束なしは止まる ／ ④未来参照 0件 ／ ⑤印は observe_diag の関数")
    if ng:
        for x in ng:
            print(f"  ❌ {x}")
        return 1
    print("  ✅ 全部 pass")
    return 0


# ══ 入口 ═══════════════════════════════════════════════════════════════════════════════
def main() -> int:
    ap = argparse.ArgumentParser(description="R9 の測るもの3つ（読み取り専用・値決め窓だけ）")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--recipe", default=None, help="判定の束を持つレシピ（json）")
    ap.add_argument("--build", type=int, default=None, help="1位から順に束を N本 組んで測る")
    # ★2026-09-16（監査 cp36 の M-7 の #11・別枠 S-7）＝説明を実物に合わせた。
    #   直す前の文「閾値の分位・続く長さ（範囲で探す値）の種」は、乱数で引いていた頃のもの。
    #   いまは閾値の分位も続く長さも乱数で引かない（`_thr_fixed`・`_nv_fixed`）。
    #   この種が効くのは `--build` で入口の束を組むとき（`sample_structure` の乱数）だけ。
    ap.add_argument("--seed", type=int, default=53,
                    help="--build で入口の束を組むときの種（判定の束の閾値・本数には効かない）")
    ap.add_argument("--no-trades", action="store_true", help="②（玉の成績）を測らない＝①③だけ（速い）")
    ap.add_argument("--strategy", default="e38")
    # ★2026-09-16（監査 cp36 の M-5）＝段ごとの候補の一覧を画面に出す旗（読むだけ）。
    ap.add_argument("--candidates", default=None,
                    help="段ごとの候補の一覧を出す（stage1／stage2a／stage2b／stage2c／stage3）")
    # ★2026-09-16（監査 cp36 の M-4）＝固定のレシピを作るための書き出しの口（読むだけ・画面に出す）。
    #   なぜ要るか＝完成の条件 AUDIT-5 は「種と乱数に依らない固定のレシピ」で測る。
    #   その元になる束を、私が手で書くのではなく、組む側（`sample_regime_build`）に出させる。
    ap.add_argument("--dump-build", type=int, default=None, metavar="N",
                    help="案 N の判定の束を JSON で画面に出す（固定のレシピを作るため・読むだけ）")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.candidates:
        return print_stage_candidates(a.candidates)
    if a.dump_build is not None:
        import engine_tuner_gen as g
        _lm, _ = g.load_limits()
        _lm = g.resolve_hold_range(_lm, a.strategy)
        _tb = g.load_signal_table()
        _pl, _tf, _ = g.material_pool()
        _bd, _ = g.sample_regime_build(_lm, _pl, _tf, _tb, order_n=int(a.dump_build))
        print(json.dumps(g.strip_marks(_bd), ensure_ascii=False, indent=2))
        return 0
    if not a.recipe and not a.build:
        ap.error("--recipe か --build N か --candidates <段> を指定")
    import engine_tuner as et
    import engine_tuner_gen as g
    from periods import SEARCH_END, SEARCH_START
    ad = et.load_adapter(a.strategy)
    df, = et.load_windows_cached(ad, [(SEARCH_START, SEARCH_END)], et.WARM)
    recipes = []
    if a.recipe:
        recipes.append(json.loads(pathlib.Path(a.recipe).read_text(encoding="utf-8")))
    else:
        pool, tfs, _ = g.material_pool()
        lm, _w = g.load_limits()
        lm = g.resolve_hold_range(lm, a.strategy)
        lim = {"n_min": None, "p_max": lm.get("p_max"), "count_range": lm.get("count_range"),
               "role_max": lm.get("role_max"), "depth_max": lm.get("depth_max"), "k_max": lm.get("k_max"),
               "r_min": lm.get("r_min")}
        regime = ad.regime("S2")
        i = 0
        tries = 0
        while len(recipes) < a.build and tries < a.build * 20:
            rng = np.random.default_rng([a.seed, 1, tries])
            tries += 1
            try:
                r = g.sample_structure(rng, lm, pool, tfs, side="SHORT", regime=regime, logic_id=f"R9_{i}",
                                       build_regime=True, regime_order_n=i)
                g.validate_drawn(r, limits=lim)          # ★69回目＝印を外してから検査に通す（原因A の直し・番人 T31）
            except (g.SampleError, ex.RecipeError) as e:
                print(f"  [組めない] 案 {i}: {str(e)[:80]}（同じ番号で引き直す）")
                continue
            recipes.append(r)
            i += 1
    print(f"[R9] 値決め窓 {SEARCH_START}〜{SEARCH_END} ／ 束 {len(recipes)} 本 ／ 玉の成績を{'測らない' if a.no_trades else '測る（run_recipe＋score.score）'}")
    rows = measure(df, recipes, SEARCH_START, SEARCH_END, with_trades=not a.no_trades)
    _print_rows(rows)
    print("\n[機械が読む形]")
    print(json.dumps(rows, ensure_ascii=False, default=float))
    # ★2026-09-16（監査 cp36 の M-4）＝測れない束が1本でも在れば、終了コードを 1 にする。
    #   直す前＝画面に「測れない」と出しても 0 で終わっていた＝機械には成功に見えた。
    #   ★行は全部 出したあとに返す＝画面は直す前と同じ（止まったことが機械に分かるだけ）。
    _ng = [r for r in rows if "①時間の割合" not in r]
    if _ng:
        print(f"\n❌ 測れない束が {len(_ng)} 本 あります（監査 cp36 の M-4）", file=sys.stderr)
        for r in _ng:
            print(f"   {r.get('判定')}: {r.get('注')}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
