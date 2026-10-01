#!/usr/bin/env python3
"""regime_r9_diag.py — 場面の判定（レンジ）について、法則 R9 の測るもの3つを出す診断（M2-5-4）。売買はしない。順位表と落ちた候補を results/ に書き、試行を数える（M2-F-2）。

2026-08-23（53回目）・まこさん承認 327e7f80008f…（受け入れ条件の C）。

法則 R9（regime_detection_kb.md §11-2・出どころ indicator_combination_kb.md §7・E37 の失敗の本体）
  ① レンジと判定した時間の割合   ＝ 値決め窓で判定が真のバー ÷ 全バー（＝言った割合）
  ② その中の玉の成績             ＝ 判定の列を entry_col に向けて run_recipe → 値決め窓の玉だけを score.score に通す
                                   → 件数・net 合計・件数/日（★net は審判の数字をそのまま出す＝この診断は計算しない。勝率は審判が返さないので出さない）
                                   ★既定では測らない（--trades を付けたときだけ＝§2.2「net は M2-L まで使わない」・M2-F-2 の (c)）
  ③ 実はトレンドだった割合       ＝ 判定が真のバーのうち、observe_diag._regime_labels の「強さ」（先 n本の ER が窓の
                                   中央値以上）が真の割合。先読み n は成績表と同じ2つ（_regime_horizons）
  ＋当たった割合（1−③）・捉えた割合（正解がレンジのうち判定が真・正解0本なら nan）・正解レンジの割合（≈50%）を出し、
    第一キー＝③の2つの先読みの平均の低さ・第二キー＝捉えた割合の平均の高さで並べる（まこさん決定 2026-09-27「１は平均でOK」）。
                                   ★未来を見る印（H2OK 注記済み）＝評価にだけ使う。判定の列や入口には入れない。

比較の行＝RG-v5（range_ok_rg5＝いまの E38 の判定）の①②③を同じ式で出す。

決まり＝売買記録CSVを書かない・_output_and_report を呼ばない・採用を書き出さない・審判（score.py）は改造しない。
        順位表と落ちた候補は results/priority_rebuild/regime_r9/ に書く（売買記録ではない・M2-F-2 の (i)(l)）。
        測る走行は tuner_stats.record_run で数える（--purpose search＝累積／check＝確認・§2.2「試行は累積」）。
        値決め窓だけで測る（採点窓は1バーも使わない・H8）。--nan-check だけ確認窓の値なしを数える（測らない・試行に数えない）。出た数字で案を選ばない（採否は M2-11・まこさん）。
        1分足・3分足を含む案が解決表の所で止まったら「測れない」と出して先へ進む（嘘の0を出さない）。

使い方（★測る走行は --purpose search か check が必須＝恒久の決まり24番・道具の確認は check）:
  python3 regime_r9_diag.py --build 3 --purpose check                   # 1位から順に束を3本 組んで測る（乱数なし・案の番号の決まった並び）
  python3 regime_r9_diag.py --recipe path.json --purpose check          # 束を持つレシピ1本を測る（玉も測るときだけ --trades）
  python3 regime_r9_diag.py --stage stage1 --purpose search             # 段の候補を全部 束にして測り、順位表と落ちた候補をファイルに書く（M2-F-8）
  python3 regime_r9_diag.py --stage stage2a --top <rank_stage1_*.json> --purpose search   # 前の段の上位 × 候補（M2-F-11〜14）
  python3 regime_r9_diag.py --sweep <rank_stage3_*.json> --purpose search  # 段4 差し戻し＝1枠ずつ入れ直して1周・良くならなくなるまで（M2-F-15）
  python3 regime_r9_diag.py --nan-check                                 # BB幅 の動く線の材料の値なしを数える（リスク8・測らない＝試行に数えない）
  python3 regime_r9_diag.py --selftest                                  # 合成データの番人（実データの試行ゼロ）
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

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


def r9_catch_share(col: np.ndarray, strong: np.ndarray, usable: np.ndarray) -> float:
    """捉えた割合（0〜1）＝正解がレンジ（強さが偽 ∧ 使える）のバーのうち、判定が真の割合（M2-F-2 の (a)）。

    ★正解が0本なら nan（嘘の0を出さない）。式の出どころ＝recall＝tp/(tp+fn)（milestones2 の M2-F 前置き3・外の一次資料で確認済み）。
    """
    col = np.asarray(col, bool)
    m = (~np.asarray(strong, bool)) & np.asarray(usable, bool)
    if not m.any():
        return float("nan")
    return float(col[m].mean())


def r9_range_share(strong: np.ndarray, usable: np.ndarray) -> float:
    """正解レンジの割合（≈50%・一緒に出す＝前置き9）＝使えるバーのうち、強さが偽（レンジだった）の割合。"""
    u = np.asarray(usable, bool)
    if not u.any():
        return float("nan")
    return float((~np.asarray(strong, bool))[u].mean())


def _nanmean(vals: list) -> float:
    """nan を除いた平均。全部 nan なら nan（並べる鍵で使う）。"""
    xs = [v for v in vals if v == v]
    return float(np.mean(xs)) if xs else float("nan")


def rank_key(r: dict) -> tuple:
    """並べる鍵＝第一キー：③（実はトレンド）の2つの先読みの平均の低さ／第二キー：捉えた割合の平均の高さ。

    ★まこさん決定 2026-09-27（逐語「１は平均でOK」）＝先24本と先288本の平均で順位をつける。
    ★nan は最後（測れない束を上位に出さない）。
    """
    _t3s = [v for k, v in r.items() if k.startswith("③")]
    # ★先読みの片方でも nan なら平均を取らない（1つだけの数字で並べない＝測れない束と同じく最後・監査 CP48）
    t3 = _nanmean(_t3s) if _t3s and all(v == v for v in _t3s) else float("nan")
    ct = _nanmean([v for k, v in r.items() if k.startswith("捉えた")])
    return (t3 if t3 == t3 else float("inf"), -(ct if ct == ct else float("-inf")))


def rank_rows(rows: list[dict], keep: int | None = None) -> tuple[list[dict], list[dict]]:
    """行を並べて順位を書き込む。keep より下は場面「成績下位」を付ける（行は消さない＝§2.2）。

    戻り＝(並べた行, 成績下位の落ちた候補)。測れない行（①が無い行）は最後に置く。
    """
    ok = [r for r in rows if "①時間の割合" in r]
    ng = [r for r in rows if "①時間の割合" not in r]
    ok.sort(key=rank_key)
    dropped = []
    k = 0
    for i, r in enumerate(ok, start=1):
        r["順位"] = i
        # ★比べる相手（RG-v5）は順位だけ付け、上位の枠（keep）を使わない・落ちた候補に数えない（束ではないため・監査 CP48）
        if str(r.get("判定", "")).startswith("RG-v5"):
            r["比べる相手"] = True
            continue
        k += 1
        if keep is not None and k > keep:
            r["dropped_by"] = "成績下位"
            dropped.append({"場面": "成績下位", "判定": r.get("判定"), "順位": i})
    return ok + ng, dropped


# ★書き先（まこさん決定 2026-09-27「了解。進めて良い」＝骨組み2）。ratchet 直下には書かない（保管運用ルール §3.1）。
OUT_DIR = HERE.parents[1] / "results" / "priority_rebuild" / "regime_r9"
# ★落ちた候補の5つの場面（M2-F-2 の (l)）。名前を散らさない（ファイルの読み手が数えるため）。
DROP_KINDS = ("組めない", "測れない", "束が無い", "関所で拒否", "成績下位")


def write_outputs(tag: str, rows: list[dict], dropped: list[dict]):
    """順位表と落ちた候補をファイルに書く（画面だけに出さない＝M2-F-2 の (i)(l)）。戻り＝2つのパス。"""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    rp = OUT_DIR / f"rank_{tag}_{stamp}.json"
    dp = OUT_DIR / f"dropped_{tag}_{stamp}.json"
    if rp.exists() or dp.exists():
        raise SystemExit(f"[R9] 同じ名前のファイルが既に在る＝上書きしない（fail-closed）: {rp.name}")
    rp.write_text(json.dumps(rows, ensure_ascii=False, indent=1, default=float) + "\n", encoding="utf-8")
    dp.write_text(json.dumps(dropped, ensure_ascii=False, indent=1, default=float) + "\n", encoding="utf-8")
    _n = {k: sum(1 for d in dropped if d.get("場面") == k) for k in DROP_KINDS}
    print(f"[書いた] 順位表 {rp} ／ 落ちた候補 {dp}（場面の内訳: {json.dumps(_n, ensure_ascii=False)}）")
    return rp, dp


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
            # ★M2-F-2 の (a)(b)(f)＝当たった（1−③・nan は nan のまま）・捉えた・正解レンジの割合を足す
            r[f"当たった(先{n}本)"] = 1.0 - r[f"③実はトレンド(先{n}本)"]
            r[f"捉えた(先{n}本)"] = r9_catch_share(col, s, u)
            r[f"正解レンジ(先{n}本)"] = r9_range_share(s, u)
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
        try:
            ex.build_regime_columns(d2, rec, geo, qt)
        except ex.RecipeError as e:
            # ★M2-F-2 の (l)＝関所（G5 ほか）の拒否を行として残す（直す前は走行ごと落ちて記録が残らなかった）
            rows.append({"判定": rec["meta"].get("logic_id"), "注": f"関所で拒否: {str(e)[:120]}"})
            continue
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
    # ★2026-09-19（設計書 m2c-width-and-stage-candidates-20260918・まこさん承認）＝
    #   段の鍵 `width`（帯の幅の枠）を受ける。候補を作るのは組む側と同じ関数
    #   （`build_width_candidates`）＝ここに絞りを書き写さない（恒久の決まり69番）。
    if stage == "width":
        cands = g.build_width_candidates(laws, table, tfs, lm)
    else:
        cands = g.build_stage_candidates(stage, laws, table, tfs, lm)
    print(f"[{stage} の候補] {len(cands)} 本（成績表の順・読むだけ・案も売買も作らない）")
    print("順位\t指標\t時間足\t列\t分離力")
    for c in cands:
        _acc = "—" if c["acc"] is None else f"{c['acc']:.3f}"
        print(f"{c['rank']}\t{c['family']}\t{c['tf']}\t{c['col']}\t{_acc}")
    return 0


def _print_rows(rows: list[dict]) -> None:
    print("\n[R9 の測るもの]（値決め窓だけ・数字は審判と印の出力・この診断は案を選ばない）")
    for r in rows:
        if "注" in r and "①時間の割合" not in r:
            print(f"  {r['判定']}: {r['注']}")
            continue
        t = r.get("②玉")
        tt = (f"②玉 {t['n']}件 net ${t['net']:+,.0f} {t['per_day']:.2f}件/日" if t and t["n"]
              else ("②玉 0件" if t is not None else "②玉 （測っていない）"))
        # ★M2-F-2＝当たった・捉えた・正解レンジも出す（順位は先頭・並べる鍵は rank_key）
        tr = " ".join(f"{k.replace('③実はトレンド', '③')}={v:.1%}" if v == v else f"{k}=nan"
                      for k, v in r.items() if k.startswith(("③", "当たった", "捉えた", "正解レンジ")))
        _rk = f"{r['順位']}位 " if r.get("順位") else ""
        print(f"  {_rk}{r['判定']}: ①{r['①時間の割合']:.2%} ／ {tt} ／ {tr}"
              + (f" ／ 成績下位" if r.get("dropped_by") == "成績下位" else "")
              + (f" ／ {r['注']}" if r.get("注") else ""))


# ══ 段ごとに測る口（M2-F-2 の (k)・M2-F-15・§2.2 の段の表）═══════════════════════════════
def _q50_width_cond(limits) -> dict:
    """段1 の帯＝レンジ幾何 W% が q50 より上（build_width_candidates の先頭＝geo が先頭・M2-F-8 の中身）。"""
    import engine_tuner_gen as g
    cw = g.build_width_candidates(g.laws_for_scene("range"), g.load_signal_table(),
                                  g.material_pool()[1], limits)
    if not (cw and "geo" in ((cw[0]["cond"].get("material") or [{}])[0])):
        raise SystemExit("[R9] 帯の幅の候補の先頭がレンジ幾何でない（法則 R7 の geo が空・fail-closed）")
    return json.loads(json.dumps(cw[0]["cond"]))


def _loosened_off(conds: list[dict], limits, frames: list | None = None) -> dict:
    """hysteresis の出る線＝sample_regime_build の E と同じ形の any（監査 CP48 で直した）。

    ★生成器の E（engine_tuner_gen.py の sample_regime_build）＝off は、A（帯の幅）と B（段1）を1段 緩めて側を返したもの（_flip_loose）と、
      C（段2a の not の中身）を1段 緩めて側は返さないもの（off_c）の any。段2b・段2c の条件は off に入れない。
      緩め方の判定は書き写さない＝生成器の _loose_q_fixed を呼ぶ。frames＝各条件の段の名前（無ければ水準の条件を全部 使う）。
    """
    import engine_tuner_gen as g
    outs = []
    for i, c in enumerate(conds):
        if frames is not None and (i >= len(frames) or frames[i] not in ("width", "stage1", "stage2a")):
            continue
        is_not = isinstance(c, dict) and "not" in c
        base = c.get("not") if is_not else c
        if not isinstance(base, dict) or base.get("form") != "level":
            continue
        q = (base.get("value") or {}).get("threshold_q")
        if not q:
            continue
        cc = json.loads(json.dumps(base))
        side = cc.get("side", "above")
        try:
            # ★2026-10-01（B-2）＝not の中身（段2a の強さ）は、緩める向きを入る線と反対にする（強さ above qX の否定で入るなら、
            #   出るのは above q(X+1)）。帯の幅と段1 は今までどおり（側を返したうえで隣の段へ）
            _ls = ("below" if side == "above" else "above") if is_not else side
            cc["value"]["threshold_q"] = g._loose_q_fixed(limits, q, _ls)
        except g.SampleError:
            continue
        if not is_not:
            # ★not の中身（段2a の強さ）は側を返さない＝生成器の off_c と同じ向き（強さが戻ったら出る）
            cc["side"] = "below" if side == "above" else "above"
        outs.append(cc)
    if not outs:
        raise SystemExit("[R9] hysteresis の出る線を1つも作れない（fail-closed）")
    return {"any": outs}


def _wrap_bundle(inner: list[dict], wrap: dict | None, limits, out_col: str, frames: list | None = None) -> dict:
    """内側の条件の一覧（＋段3 の包み）から判定の束（meta.regime.build の中身）を作る。

    wrap＝None（段1〜2c＝all で束ねるだけ）か {"持続n", "保つ上限", "role"}（段3＝
    hysteresis（on＝streak〔内側＝成立の全体・M2-E-4d と同じ〕／off＝1段 緩めた any／value＝保つ上限））。
    """
    conds = json.loads(json.dumps(inner))
    if not wrap:
        return {"entry": {"out_col": out_col, "tree": {"all": conds}}, "block": None}
    streak = {"role": wrap.get("role") or "location", "form": "streak",
              "value": {"n": int(wrap["持続n"])}, "inner": {"all": json.loads(json.dumps(conds))}}
    tree = {"all": [{"form": "hysteresis", "on": {"all": [streak]},
                     "off": _loosened_off(conds, limits, frames), "value": {"n": int(wrap["保つ上限"])}}]}
    return {"entry": {"out_col": out_col, "tree": tree}, "block": None}


def _load_top(path: str, keep: int) -> list[dict]:
    """前の段の順位表（rank_*.json）から、内側を持つ上位 keep 本を読む（fail-closed）。"""
    rows = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    tops = [r for r in rows if r.get("順位") and not r.get("dropped_by") and r.get("内側")]
    tops = sorted(tops, key=lambda r: r["順位"])[:keep]
    if not tops:
        raise SystemExit(f"[R9] 順位表 {path} に、束（内側）を持つ行が1本も無い（fail-closed）")
    return tops


def _stage_recipe(strategy: str, name: str, bd: dict) -> dict:
    """判定の束だけを持つ最小のレシピ（入口を持たない＝玉は測らない）。"""
    return {"meta": {"strategy": strategy, "logic_id": name, "side": "SHORT",
                     "regime": {"name": "range", "entry_col": bd["entry"]["out_col"], "build": bd}},
            # ★入口の木は空の all（束だけを測る・玉は測らない）。無いと build_qtable の needed_qkeys が r["entry"] で KeyError になる（監査 CP48）
            "entry": {"connective": {"all": []}}}


def _record(a, tag: str, n: int) -> None:
    """試行を数える（§2.2＝累積して DSR・PBO に数える・恒久の決まり24番＝目的は呼ぶ側が必ず宣言する）。"""
    import tuner_stats as ts
    dest, tot = ts.record_run(key=f"{a.strategy}/r9/{tag}", n_trials=int(n),
                              stamp=time.strftime("%Y-%m-%d %H:%M:%S"), purpose=a.purpose,
                              note=f"R9 の診断（{tag}・束 {n} 本・判定の成績だけ）")
    print(f"[試行] {dest} へ {n} 本（この鍵の合計 {tot}）")


def _both_sides(cands: list) -> list:
    """段1 の候補に、側を返した帯を後ろに足す（2026-10-01・工事 m2f-label-builder-stages-20261001 の B-3・監査 CP49 の修正5）。

    ★組む側は帯の向きを案の番号で上下交互に決める（engine_tuner_gen.py の sample_regime_build）が、一覧の側は
      法則が側を決めない帯で above だけ＝下側の帯が段1 で1本も測られなかった。
    """
    out = list(cands)
    for c in cands:
        cc = json.loads(json.dumps(c))
        cc["cond"]["side"] = "below" if cc["cond"].get("side", "above") == "above" else "above"
        cc["側を返した"] = True
        out.append(cc)
    return out


def _sweep_slots(cf: list, wrap) -> list:
    """差し戻しで入れ直す枠の並び＝条件の枠＋（包みが在れば）持続の枠＋（段2c の枠が無ければ）段2c を足す枠（2026-10-01・B-4）。"""
    return list(cf) + (["stage3"] if wrap else []) + ([] if "stage2c" in cf else ["stage2c+"])


def _slot_variants(tag: str, inner: list, cf: list, wrap, st: str, k: int, cands_of: dict) -> list:
    """差し戻しの1つの枠を入れ直した束の一覧＝[(名前, 内側, 包み, 枠)]（2026-10-01・B-4・監査 CP49 の修正7）。

    ★段2c の枠は「なし」（段2c の条件を外した束）も試す（§2.2 の段2c「「なし」を必ず併走」）。
    ★段2c の枠が無い束（「なし」で勝った束）は、段2c の候補を足した束を試す（段4「全候補を1枠ずつ入れ直して1周」）。
    """
    v = []
    if st == "stage2c+":
        for j, c in enumerate(cands_of["stage2c"]):
            v.append((f"{tag}_c{j}", list(inner) + [json.loads(json.dumps(c["cond"]))], wrap, list(cf) + ["stage2c"]))
        return v
    if st == "stage2c" and k < len(cf):
        v.append((f"{tag}_none", list(inner[:k]) + list(inner[k + 1:]), wrap, list(cf[:k]) + list(cf[k + 1:])))
    for j, c in enumerate(cands_of[st]):
        nm = f"{tag}_c{j}"
        if k < len(cf):
            iv = json.loads(json.dumps(inner))
            iv[k] = json.loads(json.dumps(c["cond"]))
            v.append((nm, iv, wrap, list(cf)))
        else:
            wv = dict(wrap)
            wv["持続n"] = int(c["cond"]["value"]["n"])
            v.append((nm, inner, wv, list(cf)))
    return v


def run_stage(df, a) -> int:
    """--stage＝その段の候補を全部 束にして測り、並べて、順位表と落ちた候補をファイルに書く（M2-F-8〜14）。"""
    import engine_tuner_gen as g
    from periods import SEARCH_END, SEARCH_START
    lm, _w = g.load_limits()
    lm = g.resolve_hold_range(lm, a.strategy)
    laws = g.laws_for_scene("range")
    table = g.load_signal_table()
    _pool, tfs, _ = g.material_pool()
    cands = (g.build_width_candidates(laws, table, tfs, lm) if a.stage == "width"
             else g.build_stage_candidates(a.stage, laws, table, tfs, lm))
    if a.stage == "stage1":
        cands = _both_sides(cands)               # ★2026-10-01（B-3）＝帯の下側も測る
    dropped: list[dict] = []
    if a.stage == "width":
        base = [{"判定": "（単独）", "内側": [], "枠": []}]   # 帯の候補1本だけの束（重ねる相手なし）
    elif a.stage == "stage1":
        _wc = _q50_width_cond(lm)
        # ★行の名前は束の中身から作る（設定の分位や法則の側が変わっても、名前が中身と食い違わない・監査 CP49）
        base = [{"判定": f"帯（{_wc['material'][0].get('geo')} {_wc['side']} {_wc['value']['threshold_q']}）",
                 "内側": [_wc], "枠": ["width"]}]
    else:
        if not a.top:
            raise SystemExit(f"[R9] {a.stage} には --top <前の段の順位表.json> が要る（width・stage1 だけ無しで走れる）")
        if (lm.get("stage_keep_range") or {}).get("hi") is None:
            raise SystemExit("[R9] stage_keep_range の hi が未設定＝前の段の上位を絞れない（M2-F-7 の後に走らせる・fail-closed）")
        base = _load_top(a.top, None)
    # ★渡す本数（keep）は、この段で測る束の本数に対して stage_keep_of で決める（監査 CP48）。
    #   直す前＝候補の本数で決めた＝候補1本の段2b で keep＝1（上位1本しか渡らない）・hi＝10 では stage_keep_of が止まった。
    _n_meas = len(base) * (len(cands) + (1 if a.stage == "stage2c" else 0))
    _hi = (lm.get("stage_keep_range") or {}).get("hi")
    keep = g.stage_keep_of(lm, max(_n_meas, int(_hi)) if _hi is not None else _n_meas)
    base = base[:keep]
    recipes = []
    marks = {}
    for t in base:
        # ★段2c は「なし」（3枠目を足さない束）を必ず併走する（§2.2 の段2c・M2-F-13）
        for j, c in enumerate(([None] if a.stage == "stage2c" else []) + list(cands)):
            name = f"{a.stage}_{len(recipes) + len(dropped)}"
            try:
                if a.stage == "stage3":
                    # ★保つ上限は候補の番号 j で決める＝前の束が違っても同じ候補なら同じ値（sample_regime_build の order_n と同じ組）
                    wrap = {"持続n": int(c["cond"]["value"]["n"]),
                            "保つ上限": int(g._nv_fixed(lm, "state_hold_bars_range", "n", j)["n"]),
                            "role": c["cond"].get("role")}
                    inner = list(t["内側"])
                elif c is None:
                    wrap = None
                    inner = list(t["内側"])
                else:
                    wrap = None
                    inner = list(t["内側"]) + [json.loads(json.dumps(c["cond"]))]
                # ★枠は内側と同じ並び（段3 の包みと「なし」は条件を足さない＝枠も足さない・差し戻しが読む）
                frames_in = list(t.get("枠") or []) + ([] if (a.stage == "stage3" or c is None) else [a.stage])
                bd = _wrap_bundle(inner, wrap, lm, f"regime_{name}", frames=frames_in)
            except (SystemExit, KeyError, TypeError) as e:
                dropped.append({"場面": "組めない", "判定": name, "理由": str(e)[:120]})
                continue
            if a.stage == "stage3":
                # ★完成した束だけを G7（法則の審査）に掛ける（M2-F-14）。途中の段では掛けない（中身13 の (j)）
                try:
                    ex._check_scene_rules({"name": "range", "build": g.strip_marks(bd)}, "")
                except ex.RecipeError as e:
                    dropped.append({"場面": "関所で拒否", "判定": name, "理由": f"G7: {str(e)[:120]}"})
                    continue
            recipes.append(_stage_recipe(a.strategy, name, bd))
            marks[name] = {"内側": inner, "枠": frames_in, "包み": wrap,
                           "前の束": t.get("判定"),
                           "候補": ("なし" if c is None else {k: c.get(k) for k in ("rank", "family", "tf", "col")})}
    if a.limit:
        recipes = recipes[:int(a.limit)]
    print(f"[R9] {a.stage}＝前の束 {len(base)} 本 × 候補 {len(cands)} 本 → 測る束 {len(recipes)} 本（keep={keep}）")
    rows = measure(df, recipes, SEARCH_START, SEARCH_END, with_trades=False)
    for r in rows:
        if r.get("判定") in marks:
            r.update(marks[r["判定"]])
    rows, drop_rank = rank_rows(rows, keep=keep)
    dropped += drop_rank
    dropped += [{"場面": ("関所で拒否" if str(r.get("注", "")).startswith("関所で拒否") else "測れない"),
                 "判定": r.get("判定"), "理由": r.get("注")} for r in rows if "①時間の割合" not in r]
    _print_rows(rows)
    write_outputs(a.stage, rows, dropped)
    _record(a, a.stage, len(recipes))
    return 0


def run_sweep(df, a) -> int:
    """--sweep＝段4 差し戻し（M2-F-15）＝束の1枠を、その段の全候補で入れ直して1周し、良くならなくなるまで繰り返す。"""
    import engine_tuner_gen as g
    from periods import SEARCH_END, SEARCH_START
    got = json.loads(pathlib.Path(a.sweep).read_text(encoding="utf-8"))
    rows_in = got if isinstance(got, list) else [got]
    tops = sorted([r for r in rows_in if r.get("内側") and not r.get("dropped_by")],
                  key=lambda r: (r.get("順位") is None, r.get("順位") or 0))
    if not tops:
        raise SystemExit("[R9] --sweep の順位表に、束（内側）を持つ行が1本も無い（fail-closed）")
    lm, _w = g.load_limits()
    lm = g.resolve_hold_range(lm, a.strategy)
    # ★M2-F-15＝上位（stage_keep_of の本数）の束ごとに差し戻し、最終の束を最大 keep 本 出す（監査 CP48・直す前は1位の1本だけ）
    _hi = (lm.get("stage_keep_range") or {}).get("hi")
    if _hi is None:
        # ★上端が空だと順位表の全部の行を差し戻す＝段の口（run_stage）の --top と同じく止める（監査 CP49・fail-closed）
        raise SystemExit("[R9] stage_keep_range の hi が未設定＝差し戻す束を絞れない（M2-F-7 の後に走らせる・fail-closed）")
    keep = g.stage_keep_of(lm, max(len(tops), int(_hi)))
    laws = g.laws_for_scene("range")
    table = g.load_signal_table()
    _pool, tfs, _ = g.material_pool()
    cands_of = {}
    dropped: list[dict] = []
    finals = []
    n_all = 0

    def _measure_one(tag, variants):
        recipes, marks = [], {}
        for j, (nm, iv, wv, fv) in enumerate(variants):
            try:
                bd = _wrap_bundle(iv, wv, lm, f"regime_{tag}_{j}", frames=fv)
            except (SystemExit, KeyError, TypeError) as e:
                dropped.append({"場面": "組めない", "判定": nm, "理由": str(e)[:120]})
                continue
            if wv:
                # ★段3 の包みを持つ束（完成した束）は G7 に掛ける（M2-F-14 と同じ・入れ替えで法則を破った束を残さない）
                try:
                    ex._check_scene_rules({"name": "range", "build": g.strip_marks(bd)}, "")
                except ex.RecipeError as e:
                    dropped.append({"場面": "関所で拒否", "判定": nm, "理由": f"G7: {str(e)[:120]}"})
                    continue
            recipes.append(_stage_recipe(a.strategy, nm, bd))
            marks[nm] = (iv, wv, fv)               # ★2026-10-01（B-4）＝「なし」と足す側で枠が変わるので、枠も持つ
        rows = measure(df, recipes, SEARCH_START, SEARCH_END, with_trades=False)
        rows, _ = rank_rows(rows)
        dropped.extend({"場面": ("関所で拒否" if str(r.get("注", "")).startswith("関所で拒否") else "測れない"),
                        "判定": r.get("判定"), "理由": r.get("注")} for r in rows if "①時間の割合" not in r)
        return rows, marks, len(recipes)

    for b_i, row in enumerate(tops[:keep]):
        inner = row.get("内側")
        frames = row.get("枠") or []
        wrap = row.get("包み")
        cf = list(frames[:len(inner or [])])
        if not inner or len(cf) != len(inner):
            raise SystemExit("[R9] --sweep の行に 内側 と 枠 が揃っていない（段の口が書いた順位表の行を渡す・fail-closed）")
        # ★入れ直す枠＝条件の枠（内側と同じ並び）＋段3 の包みが在れば持続（streak の本数）の枠
        # ★2026-10-01（工事 m2f-label-builder-stages-20261001 の B-4・監査 CP49 の修正7）＝段2c の枠には「なし」も試し、
        #   段2c の枠が無い束（「なし」で勝った束）には「段2c を足す」枠を足す。枠の並びは周ごとに作り直す。
        for st in _sweep_slots(cf, wrap) + ["stage2c"]:
            st0 = "stage2c" if st == "stage2c+" else st
            if st0 not in cands_of:
                cands_of[st0] = (g.build_width_candidates(laws, table, tfs, lm) if st0 == "width"
                                 else g.build_stage_candidates(st0, laws, table, tfs, lm))
        base_nm = f"sweep_b{b_i}_r0_base"
        rows0, _m0, n0 = _measure_one(f"sweep_b{b_i}_r0", [(base_nm, inner, wrap, cf)])
        best = next((r for r in rows0 if r.get("判定") == base_nm), {"判定": base_nm})
        n_all += n0
        _record(a, "sweep", n0)   # ★測った所で数える（途中で止まっても、画面とファイルに出た試行を数え落とさない・監査 CP49）
        rnd = 0
        improved = True
        while improved:
            improved = False
            rnd += 1
            for k, st in enumerate(_sweep_slots(cf, wrap)):
                variants = _slot_variants(f"sweep_b{b_i}_r{rnd}_f{k}", inner, cf, wrap, st, k, cands_of)
                rows, marks, n = _measure_one(f"sweep_b{b_i}_r{rnd}_f{k}", variants)
                n_all += n
                _record(a, "sweep", n)    # ★周・枠ごとに数える（途中で止まっても数え落とさない・監査 CP49）
                cand_best = next((r for r in rows if r.get("判定") in marks and "①時間の割合" in r), None)
                _len0 = len(cf)
                if cand_best is not None and rank_key(cand_best) < rank_key(best):
                    best = cand_best
                    inner, wrap, cf = marks[cand_best["判定"]]
                    improved = True
                write_outputs(f"sweep_b{b_i}_r{rnd}_f{k}", rows, [])
                print(f"[差し戻し] 束 {b_i}・周 {rnd}・枠 {k}（{st}）＝いまの最良 {best.get('判定')}")
                if len(cf) != _len0:
                    break                 # ★枠の数が変わった（「なし」か足す側が勝った）＝枠の並びを作り直して周の頭から
        best_row = dict(best)
        best_row["内側"] = inner
        best_row["枠"] = cf
        best_row["包み"] = wrap
        best_row["差し戻しの元"] = row.get("判定")
        finals.append(best_row)
    finals, _ = rank_rows(finals)
    write_outputs("sweep_final", finals, dropped)
    # ★試行は測った所（上の2か所）で数え済み＝ここで足すと二重になる（監査 CP49）
    print(f"[試行] 差し戻しの全体で {n_all} 本（周・枠ごとに数え済み）")
    return 0


def run_nan_check(ad, warm, a) -> int:
    """--nan-check＝BB幅 の動く線の材料の値なしの本数を、値決め窓・確認窓で数える（リスク8・まこさん決定「案1」）。

    ★測らない＝試行に数えない。窓の始まりの後に値なしが在れば終了コード1で止まって まこさんに出す。
    """
    import engine_tuner as et
    import engine_tuner_gen as g
    from periods import CONFIRM_END, CONFIRM_START, SEARCH_END, SEARCH_START
    lm, _w = g.load_limits()
    lm = g.resolve_hold_range(lm, a.strategy)
    cands = g.build_stage_candidates("stage2c", g.laws_for_scene("range"), g.load_signal_table(),
                                     g.material_pool()[1], lm)
    moving = [c for c in cands if c.get("pre_win")]
    if not moving:
        raise SystemExit("[R9] 段2c に動く線の候補が1本も無い（M2-E-4e の後のはず・fail-closed）")
    df, df_c = et.load_windows_cached(ad, [(SEARCH_START, SEARCH_END), (CONFIRM_START, CONFIRM_END)], warm)
    ng = 0
    for wname, dfx, w0, w1 in (("値決め窓", df, SEARCH_START, SEARCH_END), ("確認窓", df_c, CONFIRM_START, CONFIRM_END)):
        ts_col = pd.to_datetime(dfx["ts"])
        m = ((ts_col >= pd.Timestamp(w0)) & (ts_col < pd.Timestamp(w1))).to_numpy()
        seen = set()
        for c in moving:
            col = c["col"]
            if col in seen:
                continue
            seen.add(col)
            base = c["cond"].get("not") if "not" in c["cond"] else c["cond"]
            pre = dict(base["material"][0]["pre"])
            # ★材料は実行データの列に無い（実行器がその場で作る）＝_col_array で、前処理（動く線）まで実行器と同じ式で作る（監査 CP48）
            try:
                arr = ex._col_array(dfx, base["material"][0], g._geo_of(dfx), "")
            except ex.RecipeError as e:
                print(f"  ❌ {col}: 材料を作れない（{str(e)[:80]}）")
                ng += 1
                continue
            n_nan = int(np.isnan(arr[m]).sum())
            print(f"  {col}（窓 {pre.get('n')}本）: {wname} の値なし {n_nan} 本 ／ 窓 {int(m.sum())} 本")
            if n_nan:
                ng += 1
    if ng:
        print(f"❌ 窓の始まりの後に値なしが在る（{ng} 件）＝止まって まこさんに出す（リスク8）", file=sys.stderr)
        return 1
    print("[値なし] 値決め窓・確認窓の動く線の材料に、値なし 0 本（通った）")
    return 0


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
    # ⑥ 捉えた割合（M2-F-2 の (a)）＝全部 真→1.0／全部 偽→0.0／正解レンジ0本→nan／判定の反転で 1−x
    if r9_catch_share(col_all, strong, usable) != 1.0 or r9_catch_share(col_none, strong, usable) != 0.0:
        ng.append("⑥: 捉えた割合が 全部真→1.0・全部偽→0.0 にならない")
    if r9_catch_share(col_all, np.ones(n, bool), usable) == r9_catch_share(col_all, np.ones(n, bool), usable):
        ng.append("⑥: 正解レンジが0本なのに nan でない")
    # ⑥ の既知答え（設計書 4-19 の通しの例1）＝8本・強さが真は1・3・5・7本目・判定は2・4本目だけ真 → 0.5（監査 CP48）
    _s8 = (np.arange(8) % 2 == 0)
    _c8 = np.isin(np.arange(8), [1, 3])
    if r9_catch_share(_c8, _s8, np.ones(8, bool)) != 0.5:
        ng.append("⑥: 既知答え（8本・判定2本／正解レンジ4本＝0.5）にならない")
    # ⑥ 使えない印のバーは分母に入れない（8本目を使えないにすると 2÷3）
    if abs(r9_catch_share(_c8, _s8, np.arange(8) != 7) - 2.0 / 3.0) > 1e-12:
        ng.append("⑥: 使えない印のバーを分母から外していない")
    colX = (np.arange(n) % 3 == 0)
    cx1 = r9_catch_share(colX, strong, usable)
    cx2 = r9_catch_share(~colX, strong, usable)
    if abs((cx1 + cx2) - 1.0) > 1e-12:
        ng.append(f"⑥: 判定を反転しても 1−x にならない（x={cx1}, y={cx2}）")
    # ⑦ 乱数がこの道具に残っていない（恒久67番・構文木で見る＝説明の文には反応しない）
    for node in ast.walk(tree):
        _nm7 = node.attr if isinstance(node, ast.Attribute) else (node.id if isinstance(node, ast.Name) else None)
        if _nm7 in ("default_rng", "sample_structure", "random", "RandomState"):
            ng.append(f"⑦: 乱数の道が残っている: {_nm7} 行 {node.lineno}")
        if isinstance(node, ast.Import) and any(al.name.split(".")[-1] == "random" for al in node.names):
            ng.append(f"⑦: 乱数の import が残っている: 行 {node.lineno}")
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[-1] == "random":
            ng.append(f"⑦: 乱数の import が残っている: 行 {node.lineno}")
    # ⑧ 試行を累積に数える口（record_run）が呼ばれている（§2.2・恒久24番）
    if not any(isinstance(nd, ast.Attribute) and nd.attr == "record_run" for nd in ast.walk(tree)):
        ng.append("⑧: 試行を数える口（record_run）が1回も呼ばれていない")
    # ⑧ 測る口（main・run_stage・run_sweep）が、それぞれ試行を数える _record を呼ぶ（監査 CP48）
    for _fn8 in ("main", "run_stage", "run_sweep"):
        _d8 = [f for f in tree.body if isinstance(f, ast.FunctionDef) and f.name == _fn8]
        if not _d8 or not any(isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id == "_record" for x in ast.walk(_d8[0])):
            ng.append(f"⑧: 測る口 {_fn8} が試行を数える _record を呼んでいない")
    # ⑨ 落ちた候補の5つの場面が全部 ファイルに出る（M2-F-2 の (l)・合成＝実データゼロ）
    import tempfile
    global OUT_DIR
    _old_out = OUT_DIR
    try:
        OUT_DIR = pathlib.Path(tempfile.mkdtemp()) / "regime_r9"
        _drops = [{"場面": k, "判定": f"x{i}"} for i, k in enumerate(DROP_KINDS)]
        rp9, dp9 = write_outputs("selftest", [{"判定": "t", "①時間の割合": 0.5, "順位": 1}], _drops)
        try:
            _back = json.loads(dp9.read_text(encoding="utf-8"))
        except Exception:
            _back = []
        if sorted({d.get("場面") for d in _back}) != sorted(DROP_KINDS):
            ng.append("⑨: 落ちた候補の5つの場面が全部 ファイルに出ない")
        if not rp9.exists():
            ng.append("⑨: 順位表のファイルが書かれない")
    finally:
        OUT_DIR = _old_out
    # ⑩ 並べる鍵＝2つの先読みの平均（まこさん決定 2026-09-27「１は平均でOK」）・keep の下は成績下位
    _rA = {"判定": "A", "①時間の割合": 0.5, "③実はトレンド(先24本)": 0.48, "③実はトレンド(先288本)": 0.52,
           "捉えた(先24本)": 0.6, "捉えた(先288本)": 0.6}
    _rB = {"判定": "B", "①時間の割合": 0.5, "③実はトレンド(先24本)": 0.50, "③実はトレンド(先288本)": 0.49,
           "捉えた(先24本)": 0.6, "捉えた(先288本)": 0.6}
    _rk, _dropA = rank_rows([_rA, _rB], keep=1)
    if [_rk[0]["判定"], _rk[1]["判定"]] != ["B", "A"] or _rk[1].get("dropped_by") != "成績下位" or not _dropA:
        ng.append("⑩: 並べる鍵（2つの先読みの平均）か 成績下位 が違う")
    # ⑩ の続き（監査 CP49）＝第二キー（捉えた割合の平均の高さ）・③の先読みの片方が nan の束は最後・keep の内の行に成績下位を付けない・比べる相手（RG-v5）は keep を使わない
    _rC = {"判定": "C", "①時間の割合": 0.5, "③実はトレンド(先24本)": 0.50, "③実はトレンド(先288本)": 0.50,
           "捉えた(先24本)": 0.5, "捉えた(先288本)": 0.5}
    _rD = {"判定": "D", "①時間の割合": 0.5, "③実はトレンド(先24本)": 0.50, "③実はトレンド(先288本)": 0.50,
           "捉えた(先24本)": 0.6, "捉えた(先288本)": 0.6}
    _rE = {"判定": "E", "①時間の割合": 0.5, "③実はトレンド(先24本)": 0.48, "③実はトレンド(先288本)": float("nan"),
           "捉えた(先24本)": 0.6, "捉えた(先288本)": 0.6}
    _rG = {"判定": "RG-v5（いまの E38）", "①時間の割合": 0.5, "③実はトレンド(先24本)": 0.49, "③実はトレンド(先288本)": 0.49,
           "捉えた(先24本)": 0.6, "捉えた(先288本)": 0.6}
    _rk10, _drop10 = rank_rows([_rC, _rE, _rG, _rD], keep=1)
    if [r["判定"] for r in _rk10] != ["RG-v5（いまの E38）", "D", "C", "E"]:
        ng.append(f"⑩: 第二キー・片方 nan の束・比べる相手の並びが違う（{[r['判定'] for r in _rk10]}）")
    if (_rk10[0].get("dropped_by") or not _rk10[0].get("比べる相手") or _rk10[1].get("dropped_by")
            or [d["判定"] for d in _drop10] != ["C", "E"]):
        ng.append("⑩: keep の内の行に成績下位が付いた・比べる相手が keep を使った・落ちた候補の並びが違う")
    # ⑪ 段の口が組む束（判定の束だけ・入口の木は空）を、合成データで最後まで測れる（束を組む→解決表→列→3つの割合・関所で拒否の行・監査 CP48）
    _n11 = 2000
    _c11 = 100.0 + (np.arange(_n11) % 7)
    _df11 = pd.DataFrame({"ts": pd.date_range("2024-03-01", periods=_n11, freq="5min"), "close": _c11,
                          "v11_res_hi": _c11 * (1.0 + (np.arange(_n11) % 5) / 1000.0), "v11_res_lo": _c11,
                          "v11_sup_hi": _c11, "v11_sup_lo": _c11 * 0.99, "v11_mid": _c11})
    _w11 = {"role": "location", "form": "level", "material": [{"geo": "W%"}], "side": "above",
            "value": {"threshold_q": "q50"}}
    _rec11 = [_stage_recipe("e38", "t11_ok", _wrap_bundle([_w11], None, None, "regime_t11_ok")),
              _stage_recipe("e38", "t11_ng", _wrap_bundle([{"not": {"bool_col": "t11_no_such_col", "want": True}}],
                                                          None, None, "regime_t11_ng"))]
    try:
        # ★段3 の包み（hysteresis＝on は streak・off は _loosened_off）を持つ束も測る（監査 CP49＝直す前は包みの道が合成データでも1度も走らなかった）。
        #   持続の本数と保つ上限は、承認済みの範囲を _nv_fixed の0番で読む＝数字を作らない
        import engine_tuner_gen as _g11
        _lm11, _ = _g11.load_limits()
        _wr11 = {"持続n": int(_g11._nv_fixed(_lm11, "int_range", "n", 0)["n"]),
                 "保つ上限": int(_g11._nv_fixed(_lm11, "state_hold_bars_range", "n", 0)["n"]), "role": "location"}
        _rec11.append(_stage_recipe("e38", "t11_hy", _wrap_bundle([_w11], _wr11, _lm11, "regime_t11_hy", frames=["width"])))
        _rows11 = measure(_df11, _rec11, _df11["ts"].iloc[0], _df11["ts"].iloc[-1], with_trades=False)
        _ok11 = [r for r in _rows11 if r.get("判定") == "t11_ok" and "①時間の割合" in r and "捉えた(先24本)" in r]
        _ng11 = [r for r in _rows11 if r.get("判定") == "t11_ng" and str(r.get("注", "")).startswith("関所で拒否")]
        _hy11 = [r for r in _rows11 if r.get("判定") == "t11_hy" and "①時間の割合" in r]
        if not _ok11 or not _ng11 or not _hy11:
            ng.append(f"⑪: 段の口の束を測れない（測れた {len(_ok11)}・関所で拒否 {len(_ng11)}・包みの束 {len(_hy11)}）")
    except BaseException as _e11:
        ng.append(f"⑪: 段の口の束を測る所で止まった: {type(_e11).__name__} {str(_e11)[:80]}")
    # ⑭ 段2a の強さの否定の出る線は、入る線より緩い側（above なら1つ大きい分位）（2026-10-01・B-2）
    try:
        import engine_tuner_gen as _g14
        _lm14, _w14 = _g14.load_limits()
        _c14 = [{"not": {"role": "env", "form": "level", "material": [{"family": "ADX", "param": 14, "tf": "1h"}],
                         "side": "above", "value": {"threshold_q": "q50"}}}]
        _o14 = _loosened_off(_c14, _lm14, frames=["stage2a"])["any"][0]
        if _o14["value"]["threshold_q"] != "q51" or _o14["side"] != "above":
            ng.append(f"⑭: 強さの否定の出る線が緩い側でない（{_o14['side']} {_o14['value']['threshold_q']}）")
    except BaseException as _e14:
        ng.append(f"⑭: 出る線を作る所で止まった: {type(_e14).__name__} {str(_e14)[:80]}")
    # ⑮ 段1 は帯の上側と下側の両方を測る（2026-10-01・B-3）
    _b15 = _both_sides([{"rank": 1, "cond": {"side": "above", "value": {"threshold_q": "q50"}}}])
    if sorted(c["cond"]["side"] for c in _b15) != ["above", "below"]:
        ng.append("⑮: 段1 の候補に上側と下側の両方が無い")
    # ⑯ 差し戻しの段2c の枠に「なし」を入れ、段2c の枠が無い束には段2c を足す（2026-10-01・B-4）
    _co16 = {"stage2c": [{"cond": {"x": 1}}], "stage1": [{"cond": {"y": 1}}]}
    _v16a = _slot_variants("t", [{"a": 1}, {"b": 1}], ["stage1", "stage2c"], None, "stage2c", 1, _co16)
    _v16b = _slot_variants("t", [{"a": 1}], ["stage1"], None, "stage2c+", 1, _co16)
    if (not any(_nm.endswith("_none") and _fv == ["stage1"] for _nm, _iv, _wv, _fv in _v16a)
            or not any(_fv == ["stage1", "stage2c"] for _nm, _iv, _wv, _fv in _v16b)
            or _sweep_slots(["stage1"], None) != ["stage1", "stage2c+"]):
        ng.append("⑯: 差し戻しで段2c の「なし」か、段2c を足す束が試されない")
    # ⑤ 印の作り方が観察の道具の実物と同じ関数であること（写しを作っていない）
    import observe_diag as od
    if not hasattr(od, "_regime_labels") or not hasattr(od, "_regime_horizons"):
        ng.append("⑤: observe_diag の印の関数が見つからない")
    print(f"[selftest] ①100%/0% ／ ②反転で 1−x（x={x:.2f}）・真0本は nan ／ ③束なしは止まる ／ ④未来参照 0件 ／ ⑤印は observe_diag の関数"
          f" ／ ⑥捉えた割合（既知答え・反転・正解0本は nan）／ ⑦乱数 0件 ／ ⑧record_run ／ ⑨落ちた候補の5つの場面 ／ ⑩並べる鍵は平均 ／ ⑪段の口の束（合成データ・関所で拒否の行）")
    if ng:
        for x in ng:
            print(f"  ❌ {x}")
        return 1
    print("  ✅ 全部 pass")
    return 0


# ══ 入口 ═══════════════════════════════════════════════════════════════════════════════
def main() -> int:
    ap = argparse.ArgumentParser(description="R9 の測るもの3つと順位（売買はしない・値決め窓で測る・--nan-check だけ確認窓も数える）")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--recipe", default=None, help="判定の束を持つレシピ（json）")
    ap.add_argument("--build", type=int, default=None, help="1位から順に束を N本 組んで測る")
    # ★2026-09-27（M2-F-2）＝--seed は消した（乱数がこの道具から消えた＝束は sample_regime_build の決まった並び）。
    #   --no-trades も消した＝net を既定で測らない（§2.2・まこさん決定 2026-09-01）。測るときだけ --trades。
    ap.add_argument("--trades", action="store_true",
                    help="②（玉の成績）も測る（run_recipe＋score.score・--recipe のときだけ・既定は測らない）")
    # ★恒久の決まり24番＝走行の目的を必ず書く（道具の確認は check）。record_run は既定を持たない。
    ap.add_argument("--purpose", choices=["search", "check"], default=None,
                    help="走行の目的（search＝累積に数える／check＝確認の帳簿・測る走行で必須）")
    ap.add_argument("--strategy", default="e38")
    # ★2026-09-16（監査 cp36 の M-5）＝段ごとの候補の一覧を画面に出す旗（読むだけ）。
    ap.add_argument("--candidates", default=None,
                    help="段ごとの候補の一覧を出す（stage1／stage2a／stage2b／stage2c／stage3）")
    # ★2026-09-16（監査 cp36 の M-4）＝固定のレシピを作るための書き出しの口（読むだけ・画面に出す）。
    #   なぜ要るか＝完成の条件 AUDIT-5 は「種と乱数に依らない固定のレシピ」で測る。
    #   その元になる束を、私が手で書くのではなく、組む側（`sample_regime_build`）に出させる。
    ap.add_argument("--dump-build", type=int, default=None, metavar="N",
                    help="案 N の判定の束を JSON で画面に出す（固定のレシピを作るため・読むだけ）")
    # ★2026-09-27（M2-F-2 の (k)・M2-F-15・リスク8）＝段ごとに測る口・差し戻しの口・値なしの口。
    ap.add_argument("--stage", default=None, choices=["width", "stage1", "stage2a", "stage2b", "stage2c", "stage3"],
                    help="段の候補を全部 束にして測り、順位表と落ちた候補をファイルに書く（M2-F-8〜14）")
    ap.add_argument("--top", default=None,
                    help="前の段の順位表（rank_*.json）＝上位（stage_keep_of の本数）と候補を掛け合わせる")
    ap.add_argument("--sweep", default=None,
                    help="段4 差し戻し＝順位表（か行）の束の1枠ずつを入れ直して1周・良くならなくなるまで（M2-F-15）")
    ap.add_argument("--nan-check", action="store_true",
                    help="BB幅 の動く線の材料の値なしを数える（リスク8・まこさん決定「案1」・測らない）")
    ap.add_argument("--limit", type=int, default=None,
                    help="--stage で測る束を先頭から N本 だけにする（束1本の時間の実測のため・M2-F-5・道具の確認なので --purpose check）")
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
    if a.trades and not a.recipe:
        ap.error("--trades は --recipe のときだけ（--build・--stage の束は入口を持たない＝玉を測れない）")
    if not (a.recipe or a.build or a.stage or a.sweep or a.nan_check):
        ap.error("--recipe か --build N か --candidates <段> か --stage <段> か --sweep <順位表> か --nan-check を指定")
    if (a.recipe or a.build or a.stage or a.sweep) and not a.purpose:
        ap.error("--purpose search か check を書く（恒久の決まり24番＝道具の確認は check）")
    import engine_tuner as et
    import engine_tuner_gen as g
    from periods import SEARCH_END, SEARCH_START
    ad = et.load_adapter(a.strategy)
    # ★M2-F-2＝段2c の動く線（6か月の窓）も測る道具なので、余白を stage_warm で延ばして読む
    #   （まこさん決定 2026-09-27「余白の直し方→C」の続き・m2_todo の M2-F-2 の注意）。
    _warm = g.stage_warm(et.WARM)
    if a.nan_check:
        return run_nan_check(ad, _warm, a)
    df, = et.load_windows_cached(ad, [(SEARCH_START, SEARCH_END)], _warm)
    if a.stage:
        return run_stage(df, a)
    if a.sweep:
        return run_sweep(df, a)
    recipes = []
    dropped: list[dict] = []
    if a.recipe:
        recipes.append(json.loads(pathlib.Path(a.recipe).read_text(encoding="utf-8")))
    else:
        # ★2026-09-27（M2-F-2 の (d)）＝束は sample_regime_build（判定の束だけ・乱数0件・成績表の順位 × 案の番号の
        #   決まった並び）で組む。直す前は sample_structure（入口まで含むレシピ・細部に乱数）を rng で呼んでいた。
        #   組めない案は引き直さない（乱数が無いので引き直しても同じ）＝落ちた候補として残す（(l)）。
        pool, tfs, _ = g.material_pool()
        lm, _w = g.load_limits()
        lm = g.resolve_hold_range(lm, a.strategy)
        table = g.load_signal_table()
        for i in range(a.build):
            try:
                bd, drw = g.sample_regime_build(lm, pool, tfs, table, order_n=i)
            except (g.SampleError, ex.RecipeError) as e:
                print(f"  [組めない] 案 {i}: {str(e)[:80]}")
                dropped.append({"場面": "組めない", "判定": f"R9_{i}", "理由": str(e)[:120]})
                continue
            try:
                # ★法則（G7）に反する束は測らない（監査 CP48）。★直す前の validate_drawn と違い、G5 の形の検査は掛けない（監査 CP49）
                ex._check_scene_rules({"name": "range", "build": g.strip_marks(bd)}, "")
            except ex.RecipeError as e:
                # ★G7 の拒否は「関所で拒否」の場面に残す（段の口 run_stage と同じ名前・設計書 4-5・監査 CP49）
                print(f"  [関所で拒否] 案 {i}: {str(e)[:80]}")
                dropped.append({"場面": "関所で拒否", "判定": f"R9_{i}", "理由": f"G7: {str(e)[:120]}"})
                continue
            rec = _stage_recipe(a.strategy, f"R9_{i}", bd)
            rec["meta"]["regime_draw"] = drw
            recipes.append(rec)
    print(f"[R9] 値決め窓 {SEARCH_START}〜{SEARCH_END} ／ 束 {len(recipes)} 本 ／ 玉の成績を{'測る（run_recipe＋score.score）' if a.trades else '測らない（既定）'}")
    rows = measure(df, recipes, SEARCH_START, SEARCH_END, with_trades=a.trades)
    rows, _dr = rank_rows(rows)            # keep=None＝この口では成績下位を作らない（並べて順位を付けるだけ）
    dropped += [{"場面": ("関所で拒否" if str(r.get("注", "")).startswith("関所で拒否") else "測れない"),
                 "判定": r.get("判定"), "理由": r.get("注")} for r in rows if "①時間の割合" not in r]
    _print_rows(rows)
    write_outputs("recipe" if a.recipe else "build", rows, dropped)
    _record(a, "recipe" if a.recipe else "build", len(recipes))
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
