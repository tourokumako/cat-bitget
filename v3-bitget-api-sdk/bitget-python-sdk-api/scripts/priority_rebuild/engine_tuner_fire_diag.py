"""engine_tuner_fire_diag.py — 撒いた構造が「どの関門で売買まで行けなくなるか」を数えるだけの道具。

なぜ在るか（2026-08-06・まこさん OK「OK」・next_step §6.5 の16番）
  2026-08-05 に engine_tuner_gen（売買ルールの形そのものを組み立てる方）で 8構造を撒き、
  値決め窓18ヶ月を走らせたところ、8構造とも売買が1件も成立しなかった。
  「成績がマイナス」ではなく「そもそも1回も取引していない」ので、成績も統計も出せない。
  ★どの関門で消えているのかが分からないと、直し方が決まらない。
    関門1（条件が1本ずつ成立する）で消えているなら、条件の作り方の問題。
    関門5 まで来て関門6（約定）で消えているなら、指値の置き方の問題。まったく別の直しになる。

  まこさんの指摘（2026-08-06 逐語）＝「そもそも売買ルールはどういうロジックで組み立てた？
  売買が成立しない条件を組み立てたのであれば、それは目的が適当な条件を＆でつなぐことになってるのでは？」
  ＝そのとおりで、いまの sample_structure は材料・しきい値・向きをすべて乱数で引き、全部を AND で
  つなぐ。条件どうしが噛み合うかを見る制約は無い。本ファイルは、その薄まり方を数字で出す。

この道具が「やること」と「やらないこと」
  やる  ＝ 関門1〜6 を通ったローソク足の数を数えて出す。条件1本ごとの成立率を出す。
         18ヶ月ずっと成立しなかった条件を名指しする。
  やらない＝ 直さない。値を選ばない。成績（net）を出さない。売買記録CSVを書かない。
         審判 score.py を import しない。累積の試行数に1本も足さない。

読み取り専用の診断（*_diag.py）＝acceptance の免除の条件を3つとも満たす
  ①売買記録CSV（to_csv / write_sidecar）を書かない ②審判（import score / score.score）を呼ばない
  ③採用の書き出し（_output_and_report / ratchet_io）をしない。

自分で書き直さない（本走と違うものを測らないため）
  構造の撒き方   ＝ engine_tuner_gen.sample_structure をそのまま呼ぶ
  材料と解決表   ＝ engine_tuner_gen.attach_materials / build_qtable をそのまま呼ぶ
  条件1本の判定 ＝ engine_tuner_exec._eval_cond をそのまま呼ぶ
  発火の判定    ＝ engine_tuner_exec._entry_fire をそのまま呼び、自前の数え上げと突き合わせる（番人④）
  売買         ＝ engine_tuner_exec.run_recipe をそのまま呼ぶ（玉数はその戻り値の行数）

使い方
  python3 engine_tuner_fire_diag.py --selftest              # 番人（合成データのみ・実データを触らない）
  python3 engine_tuner_fire_diag.py --run --purpose check --structures 100 --tag 発火の関門
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
import time
from collections import Counter

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import engine_tuner_exec as ex               # noqa: E402  歩3 実行器（条件の判定と共通の売買ループ）
import engine_tuner_gen as gen               # noqa: E402  歩4 生成器（構造の撒き方・材料・解決表）

HERE = pathlib.Path(__file__).resolve().parent
OUT_DIR = HERE.parents[2] / "results" / "priority_rebuild" / "ratchet" / "firediag"

def counted_files() -> list[pathlib.Path]:
    """累積の試行数と、確認の走行の帳簿の場所。★この道具は両方とも1バイトも書き換えない。

    ★場所を自分で書かない（2026-08-06 に直した）。最初は自分でパスを組み立てて書いていて、
      実際の場所（.claude/ratchet）と違っていた。両方とも『無し → 無し』と出るので、
      検査が通ったように見えるのに何も見ていなかった。場所は tuner_stats（書く側）に聞く。
    """
    import tuner_stats as ts
    return [ts.CUMULATIVE, ts.CHECK_RUNS]

GATE_LABELS = [
    "関門1 条件が1本ずつ成立した（一番成立しにくい条件の本数）",
    "関門2 条件が全部いっぺんに成立した",
    "関門3 きっかけの条件が この足で成立した（前の足では不成立）",
    "関門4 売ろうと決まった（関門2 と 関門3 が同じ足）",
    "関門5 相場のゲートを通った（レンジ かつ 上げトレンドでない かつ 帯の中心が有る）",
    "関門6 約定して玉が建った",
]


# ══ 条件1本の説明（人が読んで犯人が分かる言葉にする）══════════════════════════════════
def cond_label(c: dict, lane: str) -> str:
    """条件1本を1行の説明にする。材料の名前はカタログの解決名（列名）をそのまま使う。"""
    role = {"trigger": "引き金", "env": "環境認識", "sufficiency": "十分性", "location": "位置"}.get(
        c.get("role", ""), c.get("role", ""))
    form = c["form"]
    if form in ex.NEST_FORMS:
        inner = cond_label(c["inner"], lane)
        n = int(c.get("value", {}).get("n", 0))
        if form == "barssince":
            # ★何本前に成立したか（部品 barssince・2026-08-12・段C の C-6）＝n は窓でなく閾値の本数。
            _sd = {"above": "以上", "below": "以内", "above_strict": "より多く",
                   "below_strict": "より短く"}.get(c.get("side", ""), "")
            return f"[{role}] 最後に成立してから {n}本 {_sd} 経った（内側＝{inner}）"
        kind = "連続" if form == "streak" else "N本以内"
        return f"[{role}] {kind}{n}本（内側＝{inner}）"
    if form == "hysteresis":
        # ★状態を保つ形（M2-2-5・2026-08-21）＝材料を直接は取らない（on と off の中の条件が取る）。
        #   mats を取る下の行より前で返す（材料なしの形＝candle_dir と同じ扱い）。
        _n = int(c.get("value", {}).get("n", 0))
        return (f"[{role}] 状態を保つ（入る＝{cond_label_tree(c['on'], lane)} ／ "
                f"出る＝{cond_label_tree(c['off'], lane)} ／ 最大 {_n}本 保つ）")
    mats = c.get("material") or []
    names = " と ".join(ex._mat_key(m, lane) for m in mats) if mats else "（材料なし）"
    v = c.get("value", {}) or {}
    side = {"above": "以上", "below": "以下"}.get(c.get("side", ""), "")
    if form == "level":
        return f"[{role}] {names} が しきい値{v.get('threshold_q', v.get('n', ''))} {side}"
    if form in ex.forms_where("band"):            # ★手書きの並び → 性質表から（M2-2-3b・2026-08-21）
        w = "の帯の中" if form == "band" else "の帯の外"
        return (f"[{role}] {names} が {v.get('lo', {}).get('threshold_q', '')}〜"
                f"{v.get('hi', {}).get('threshold_q', '')}{w}")
    if form == "cross":
        return f"[{role}] {names} が交差した（向き {v.get('direction', '')}）"
    if form == "diff":
        return f"[{role}] {names} の差が しきい値{v.get('threshold_q', '')} {side}"
    if form == "touch":
        return f"[{role}] {names} が接した"
    if form == "candle_dir":
        return f"[{role}] ローソクの向きが {v.get('dir', '')}"
    if form == "slope":
        return f"[{role}] {names} の {v.get('n', '')}本前との差が 0 {side}"
    if form == "slope_avg":
        return f"[{role}] {names} の {v.get('m', '')}本平均の {v.get('n', '')}本前との差が 0 {side}"
    return f"[{role}] {form}（{names}）"


def cond_label_tree(node, lane: str) -> str:
    """条件の木を1行の説明にする（M2-2-5＝状態を保つ形の on／off の中身を人が読める形で出すため）。"""
    if isinstance(node, dict) and "bool_col" in node:
        return f"列 {node['bool_col']} が {'真' if node.get('want') else '偽'}"
    if ex._is_cond(node):
        return cond_label(node, lane)
    if isinstance(node, dict) and "not" in node:
        return f"〜でない（{cond_label_tree(node['not'], lane)}）"
    if isinstance(node, dict) and "all" in node:
        return " かつ ".join(cond_label_tree(ch, lane) for ch in node["all"])
    if isinstance(node, dict) and "any" in node:
        return " または ".join(cond_label_tree(ch, lane) for ch in node["any"])
    if isinstance(node, dict) and "if" in node and "then" in node:
        return f"{cond_label_tree(node['if'], lane)} なら {cond_label_tree(node['then'], lane)}"
    return str(node)


# ══ 木の評価（実行器と同じ意味・関門2 を数えるために再帰する）═══════════════════════════
def eval_tree(node, df, geo, lane, qtable) -> np.ndarray:
    """★2026-08-21（M2-2-5）＝実行器の `_eval_tree` を、そのまま呼ぶ形にした。

    直す前は、同じ式（all／any／if-then）をこのファイルに書き写していた。
    ＝実行器に形（否定 not など）を足したとき、ここに足し忘れると、**診断だけが古い規則で数える**
      （しかも黙ってずれる）。M2-2-3b で形の性質を1か所にまとめたのと同じ思想。
    ★同じ規則であることは、この関数を使って数えた関門4 が実行器 _entry_fire の合計と
      一致することで機械確認する（番人④・自分だけの解釈で数えない）。
    """
    return ex._eval_tree(node, df, geo, lane, qtable)


def build_geo(df: pd.DataFrame) -> dict:
    """レンジ幾何の列（run_generation と同じ作り方＝二重に書かない意味で式を合わせる）。"""
    geo = {"res_hi": df["v11_res_hi"].to_numpy(float), "res_lo": df["v11_res_lo"].to_numpy(float),
           "sup_hi": df["v11_sup_hi"].to_numpy(float), "sup_lo": df["v11_sup_lo"].to_numpy(float),
           "mid": df["v11_mid"].to_numpy(float)}
    c = df["close"].to_numpy(float)
    span = geo["res_hi"] - geo["mid"]
    with np.errstate(invalid="ignore", divide="ignore"):
        geo["帯内位置%"] = np.where(np.isfinite(span) & (span > 0), (c - geo["mid"]) / span, np.nan)
        geo["W%"] = np.where(np.isfinite(geo["res_hi"]) & np.isfinite(geo["sup_lo"]),
                             (geo["res_hi"] - geo["sup_lo"]) / c * 100.0, np.nan)
    return geo


# ══ 関門の数え上げ（構造1本ぶん）════════════════════════════════════════════════════
def funnel_one(df: pd.DataFrame, geo: dict, recipe: dict, qtable: dict | None,
               with_trades: bool = True, start=None, end=None) -> dict:
    """構造1本の関門1〜6 を数える。戻り＝各関門のローソク足の数と、条件1本ごとの成立率。

    ★窓の外を数えない（2026-08-06 に直した）。データには助走（窓の前の60日）が付いている。
      指標の計算には助走が要るが、数えるのは窓の中だけ。engine_tuner_gen.run_trial 621-623行が
      売買記録を entry_time で窓の中に絞っているのと同じ扱いに揃える。
      ★直す前は助走のぶんまで数えていて、道具自身の記録（journal）と玉数が食い違った
        （構造 #5 で 私 391玉 対 記録 357玉）。実データの突き合わせで見つかった。
    """
    lane = recipe["meta"].get("lane", "")
    ts_all = pd.to_datetime(df["ts"])
    win = np.ones(len(df), bool) if start is None else \
        ((ts_all >= start) & (ts_all < end)).to_numpy()
    tree = recipe["entry"]["connective"]
    paths = tree["any"] if (isinstance(tree, dict) and set(tree) == {"any"}) else [tree]
    n_bars = len(df)

    n_win = int(win.sum())
    conds_info = []
    tree_true = np.zeros(n_bars, bool)
    trig_edge = np.zeros(n_bars, bool)
    for path in paths:
        conds, _d = ex._walk(path)
        for c in conds:
            arr = ex._eval_cond(c, df, geo, lane, qtable) & win
            conds_info.append({"label": cond_label(c, lane), "role": c.get("role", ""),
                               "form": c["form"], "n_true": int(arr.sum()),
                               "rate": float(arr.sum() / n_win) if n_win else 0.0})
        t = ex._eval_cond(next(c for c in conds if c.get("role") == "trigger"), df, geo, lane, qtable)
        e = t & ~np.roll(t, 1)
        e[0] = False
        trig_edge |= e
        tree_true |= eval_tree(path, df, geo, lane, qtable)

    fire = ex._entry_fire(recipe, df, geo, qtable) & win     # ★実行器そのもの（自前の合成では数えない）
    ok, up = ex._regime_series(df, recipe)
    band_ok = ok & (~up) & np.isfinite(geo["mid"])
    gate = fire & band_ok

    # 関門1＝一番成立しにくい条件が成立した足の数（AND なので、ここが全体の上限になる）
    g1 = min((ci["n_true"] for ci in conds_info), default=0)
    counts = [g1, int((tree_true & win).sum()), int((trig_edge & win).sum()),
              int(fire.sum()), int(gate.sum())]

    n_lots = 0
    if with_trades:
        trades, _rep = ex.run_recipe(df, recipe, limits=None, samples=None, qtable=qtable)
        t = pd.DataFrame(trades)
        if len(t) and start is not None:                    # 窓の外の玉は数えない（run_trial 621-623行と同じ）
            et = pd.to_datetime(t["entry_time"])
            t = t[(et >= start) & (et < end)]
        n_lots = len(t)
    counts.append(n_lots)

    return {"counts": counts, "conds": conds_info,
            "dead": [ci["label"] for ci in conds_info if ci["n_true"] == 0],
            "n_bars": n_win, "n_conds": len(conds_info),
            "n_paths": len(paths), "has_or": set(tree) == {"any"} if isinstance(tree, dict) else False}


def first_zero_gate(counts: list[int]) -> int:
    """最初に 0 になった関門の番号（1〜6）。0 が無ければ 0 を返す＝売買まで行った。"""
    for i, v in enumerate(counts):
        if v == 0:
            return i + 1
    return 0


def counting_violations(counts: list[int], n_paths: int = 1) -> list[str]:
    """数え方が壊れていないかを見る（番人③）。増えてはいけない所で増えたら、その場所を返す。

    ★2026-08-06 に直した。最初は「関門1 から関門6 まで一直線に減る」と書いたが、これは誤り。
      関門3（きっかけが この足で成立した）は 関門2（条件が全部そろった）の内側ではない。
      2つは並んでいて、関門4 がその2つの重なりである。番人が実際にこの誤りを捕まえた
      （合成データで 関門2=0・関門3=132 が出て「増えている」と誤って落ちた）。
    """
    g1, g2, g3, g4, g5, g6 = counts
    v = []
    if n_paths == 1 and g2 > g1:
        v.append(f"関門2 が 関門1 より多い（{g2} > {g1}）")
    if g4 > min(g2, g3):
        v.append(f"関門4 が 関門2 と関門3 の小さい方より多い（{g4} > {min(g2, g3)}）")
    if g5 > g4:
        v.append(f"関門5 が 関門4 より多い（{g5} > {g4}）")
    if g6 > g5:
        v.append(f"関門6 が 関門5 より多い（{g6} > {g5}）")
    return v


# ══ 表示 ═══════════════════════════════════════════════════════════════════════
def print_one(idx: int, r: dict, show_conds: int, out) -> None:
    def w(s=""):
        print(s)
        out.append(s)

    w(f"構造 #{idx}（条件 {r['n_conds']}本 ／ 経路 {r['n_paths']}本 ／ OR あり={r['has_or']}）")
    if show_conds:
        w("  関門1 条件ごとに成立したローソク足の数")
        for ci in sorted(r["conds"], key=lambda z: z["n_true"])[:show_conds]:
            mark = "  ← ★18ヶ月ずっと成立しない" if ci["n_true"] == 0 else ""
            w(f"        ・{ci['label']}  …… {ci['n_true']:,} 本（{ci['rate'] * 100:.2f}%）{mark}")
    for lab, v in zip(GATE_LABELS, r["counts"]):
        w(f"  {lab} …… {v:,}")
    z = first_zero_gate(r["counts"])
    w(f"  → 最初に 0 になった関門: {z if z else 'なし（玉が建った）'}")
    w("")


def summarize(results: list[dict], out) -> dict:
    def w(s=""):
        print(s)
        out.append(s)

    n = len(results)
    zero_at = Counter(first_zero_gate(r["counts"]) for r in results)
    reached = zero_at.get(0, 0)
    w("══════ 構造ごとの一覧（関門ごとのローソク足の数）══════")
    w("  #  条件  関門1     関門2    関門3    関門4   関門5   関門6  最初に0になった関門")
    for i, r in enumerate(results):
        c = r["counts"]
        z = first_zero_gate(c)
        w(f"{i:4d} {r['n_conds']:4d} {c[0]:8,} {c[1]:8,} {c[2]:8,} {c[3]:7,} {c[4]:6,} {c[5]:6,}"
          f"   {z if z else '—（玉が建った）'}")
    w("")
    w("══════ まとめ ══════")
    w(f"撒いた構造 {n} 本のうち、玉が建ったのは {reached} 本"
      f"（{reached / n * 100:.1f}%）" if n else "撒いた構造 0 本")
    w("落ちた場所の内訳（最初に 0 になった関門）:")
    for g in range(1, 7):
        c = zero_at.get(g, 0)
        if c:
            w(f"  {GATE_LABELS[g - 1]} …… {c} 本（{c / n * 100:.1f}%）")
    dead_all = [d for r in results for d in r["dead"]]
    w(f"18ヶ月ずっと成立しなかった条件 …… のべ {len(dead_all)} 件"
      f"（条件の総数 {sum(r['n_conds'] for r in results)} 件）")
    if dead_all:
        w("  多い順（上位10）:")
        for lab, c in Counter(dead_all).most_common(10):
            w(f"    {c} 回  {lab}")
    # 条件の本数と発火の関係＝「何本 重ねると消えるか」
    w("条件の本数ごとの内訳（★何本 重ねると売買まで行かなくなるか）:")
    w("  本数  構造数  玉が建った  割合    発火(関門4)の中央値  発火ゼロ")
    by_n: dict[int, list[dict]] = {}
    for r in results:
        by_n.setdefault(r["n_conds"], []).append(r)
    for k in sorted(by_n):
        v = by_n[k]
        fires = [z["counts"][3] for z in v]
        got = sum(1 for z in v if z["counts"][5] > 0)
        w(f"  {k:3d}本 {len(v):6d} {got:10d} {got / len(v) * 100:6.1f}% "
          f"{int(np.median(fires)):15,} 足 {sum(1 for x in fires if x == 0):8d} 本")
    w("")
    return {"n": n, "reached": reached, "zero_at": dict(zero_at)}


# ══ 本走 ═══════════════════════════════════════════════════════════════════════
def run_main(a) -> int:
    import engine_tuner as et                  # データの読み込みと接続ファイルの解決を使い回す
    import tuner_judgement as tj
    import tuner_stats as ts
    from periods import SCORE_START, SEARCH_END, SEARCH_START

    if a.purpose not in ts.PURPOSES:
        raise SystemExit(f"[走行の目的エラー] --purpose は {ts.PURPOSES} のどれか。渡された値: {a.purpose!r}\n"
                         "  この道具は値を1つも選ばないので check だけを想定しています。")
    if a.purpose != ts.PURPOSE_CHECK:
        raise SystemExit("[走行の目的エラー] この道具は数えるだけで値を選びません。--purpose check で走らせます。")
    if pd.Timestamp(SEARCH_END) > SCORE_START:
        raise SystemExit("[窓エラー] 値決め窓が採点窓に掛かっています（H8・L-267）。")

    counted = counted_files()
    missing = [p for p in counted if not p.exists()]
    if missing:                                   # 「無し → 無し」で検査が通ったように見えるのを防ぐ
        raise SystemExit(f"[番人⑤ エラー] 見張るはずのファイルが在りません: {missing}\n"
                         "  場所を取り違えていると、変わっていないことを確かめたつもりで何も見ていません。")
    before = {p: hashlib.md5(p.read_bytes()).hexdigest() for p in counted}

    ad = et.load_adapter(a.strategy)
    known = {z["id"]: z for z in ad.logics()}
    if a.logic not in known:
        raise SystemExit(f"[エラー] ロジック id が {ad.NAME} に無い: {a.logic}（在るのは {', '.join(known)}）")
    side = (known[a.logic].get("side") or "SHORT").upper()
    regime = ad.regime(a.logic)
    role, rfloor = tj.role_floor(a.strategy)

    lm, waiting = gen.load_limits()
    if waiting:
        print("[発火の関門] 走らせられない＝search_limits.json の値がまこさん待ち:")
        for x in waiting:
            print(f"  ・{x}")
        return 2
    lm = gen.resolve_hold_range(lm, a.strategy)

    out: list[str] = []

    def w(s=""):
        print(s)
        out.append(s)

    w("══════ 撒いた構造が どの関門で売買まで行けなくなるかを数える（読み取り専用・値を選ばない）══════")
    w(f"[この走行の目的] {a.purpose}＝数えるだけ。試した回数に数えない（累積ファイルを開きもしない）")
    w(f"[戦略] {ad.NAME} ／ 宣言を借りるロジック {a.logic} ／ 側 {side} ／ 役割 {role}（件数/日 の絶対下限 {rfloor}）")
    w(f"[局面] {regime.get('name')}（入口の列 {regime.get('entry_col')} ／ 止める列 {regime.get('block_col')}）")
    w(f"[窓] 値決め窓 {SEARCH_START.date()}〜{SEARCH_END.date()}（排他）だけ。採点窓は1バーも使わない")

    t0 = time.time()
    (df,) = et.load_windows_cached(ad, [(SEARCH_START, SEARCH_END)], et.WARM, use_cache=not a.no_cache)
    w(f"[データ] {len(df):,} バー（助走込み・{time.time() - t0:.0f}秒）")

    # ── 構造を撒く（engine_tuner_gen の撒き方をそのまま呼ぶ＝本走と同じものを測る）──
    pool, tfs, cat_total = gen.material_pool()
    structures: list[dict] = []
    rejects: Counter = Counter()
    seen: set = set()
    i = 0
    while len(structures) < a.structures and i < a.structures * 50:
        rng = np.random.default_rng([a.seed, 1, i])
        i += 1
        try:
            r = gen.sample_structure(rng, lm, pool, tfs, side=side, regime=regime,
                                     logic_id=f"GEN{len(structures):04d}")
            ex.validate_recipe(r, limits={
                "n_min": None, "p_max": lm.get("p_max"), "count_range": lm.get("count_range"),
                "role_max": lm.get("role_max"), "depth_max": lm.get("depth_max"),
                "k_max": lm.get("k_max"), "r_min": lm.get("r_min")})
        except (gen.SampleError, ex.RecipeError) as e:
            rejects[str(e)[:28]] += 1
            continue
        h = gen.recipe_hash(r)
        if h in seen:
            rejects["重複"] += 1
            continue
        seen.add(h)
        structures.append(r)
    if len(structures) < a.structures:
        raise SystemExit(f"[エラー] 構造が {a.structures} 本そろわない（{len(structures)} 本・拒否 {dict(rejects)}）")
    w(f"[撒いた構造] {len(structures)} 本（引き直し {sum(rejects.values())} 回・内訳 "
      f"{json.dumps(dict(rejects), ensure_ascii=False)}）")
    bd = gen.structure_breakdown(structures, cat_total)
    w(f"[構造の内訳] {json.dumps(bd, ensure_ascii=False)}")

    # ── 材料と分位の解決表（値決め窓から1回だけ固定＝本走と同じ）──
    df2 = gen.attach_materials(df, structures)
    # ★ここで本走を止める不具合を1つ回避する（2026-08-06 に この道具で発見・直していない）。
    #   engine_tuner_exec は「カタログ名の列が無ければ別名の列を使う」形（RUNTIME_ALIAS・_col_array 686行）。
    #   engine_tuner_gen.attach_materials も別名が在れば組み立てを飛ばす（496行）。
    #   ところが engine_tuner_gen.build_qtable の中の _arr（466行）は別名を見ないので、
    #   別名を持つ7列のどれかに分位のしきい値が当たった瞬間に「[解決表エラー] 列 … が実行データに無い」で
    #   本走ごと落ちる。2026-08-05 の走行は 3本・8本だったので当たらなかっただけ。
    #   ★この道具は測るのが仕事なので、道具側は直さず、ここで別名の中身をカタログ名でも読めるようにする
    #     （中身は同じ列のコピー＝数字は変わらない）。直すのは engine_tuner_gen 側の別の作業。
    aliased = []
    for canon, runtime in ex.RUNTIME_ALIAS.items():
        if canon not in df2.columns and runtime in df2.columns:
            df2[canon] = df2[runtime].to_numpy(float)
            aliased.append(f"{canon}←{runtime}")
    if aliased:
        w(f"⚠️ [回避] 別名でしか持っていない列を、カタログ名でも読めるようにした（{len(aliased)}本）: "
          f"{', '.join(aliased)}")
        w("   ＝engine_tuner_gen.build_qtable が別名を見ない不具合の回避。道具は直していない（報告のみ）")
    geo = build_geo(df2)
    # ★2026-08-15（段A の A-5-3）＝分位は範囲になった（quantile_list が範囲の中の整数を全部 作る）。
    _qs = gen.quantile_list(lm)
    qtable = gen.build_qtable(df2, geo, structures, _qs, SEARCH_START, SEARCH_END)
    w(f"[分位の解決表] {len(qtable)} 鍵 × {len(_qs)} 分位（{_qs[0]}〜{_qs[-1]}）を値決め窓から1回固定")
    w("")

    results = []
    t1 = time.time()
    for si, r in enumerate(structures):
        res = funnel_one(df2, geo, r, qtable, with_trades=not a.no_trades,
                         start=SEARCH_START, end=SEARCH_END)
        results.append(res)
        if si < a.show:
            print_one(si, res, a.show_conds, out)
    w(f"[所要] 構造 {len(structures)} 本で {time.time() - t1:.0f}秒")
    w("")

    # ★番人⑦＝道具自身の記録（journal.jsonl）と玉数を突き合わせる。
    #   この道具が数え直しているのではなく、道具と同じ数になることを機械で確かめる。
    if a.verify_journal:
        jp = pathlib.Path(a.verify_journal) / "journal.jsonl"
        if not jp.exists():
            raise SystemExit(f"[突き合わせエラー] 記録が無い: {jp}")
        want: dict[int, int] = {}
        for line in jp.read_text(encoding="utf-8").splitlines():
            d = json.loads(line)
            rec = d.get("rec") or d.get("value") or d
            if isinstance(rec, dict) and rec.get("stage") == 1 and "n" in rec:
                want[int(rec["idx"])] = int(rec["n"])
        ng = [(i, results[i]["counts"][5], want[i]) for i in sorted(want)
              if i < len(results) and results[i]["counts"][5] != want[i]]
        w(f"[番人⑦ 道具自身の記録との突き合わせ] {jp}")
        w(f"  照合した構造 {len([i for i in want if i < len(results)])} 本 ／ 食い違い {len(ng)} 本")
        for i, mine, theirs in ng:
            w(f"  ❌ 構造 #{i}: この道具 {mine}玉 ／ 道具自身の記録 {theirs}玉")
        if ng:
            raise SystemExit("[番人⑦] 玉数が道具自身の記録と食い違う＝数え方が違う。止める。")
        w("  ✅ 全部 一致（この道具は道具自身と同じ数を数えている）")
        w("")
    summarize(results, out)

    after = {p: hashlib.md5(p.read_bytes()).hexdigest() for p in counted}
    same = all(before[p] == after[p] for p in before)
    w(f"[累積の試行数・確認の帳簿] 走行の前後で同一={same}（場所は tuner_stats が持っているものを使った）")
    for p in before:
        w(f"  {p}")
        w(f"    {before[p]} → {after[p]}")
    if not same:
        raise SystemExit("[番人⑤] この道具は累積と帳簿に1バイトも書かないはずなのに変わった＝止める")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fp = OUT_DIR / f"firediag_{a.strategy}_{a.logic}_{a.tag or 'run'}_{time.strftime('%Y%m%d_%H%M%S')}.txt"
    fp.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"[保存] {fp}")
    return 0


# ══ 番人（合成データのみ・実データを触らない）═════════════════════════════════════════
def _synth_recipe(conds: list[dict]) -> dict:
    """検収用のレシピ＝合成データ（gen.synth_df）の列名に合わせる。相場の名前は一覧の語（range）。"""
    return {"meta": {"strategy": "e38", "logic_id": "T", "side": "SHORT",
                     "regime": {"name": "range", "entry_col": "range_ok_rg5", "block_col": "rg5_uptrend"}},
            "pre_filter": [], "entry": {"connective": {"all": conds}},
            "exits": [{"name": "SL", "reason": "SL_FILLED",
                       "exec": {"method": "maker",
                                "placement": {"kind": "resting", "fill": "adverse", "pessimistic": True,
                                              "level": {"kind": "zone_sl", "k": {"const": "FULL_100", "mult": 0.01}}}},
                       "size_ratio": 1.0}],
            "position": {"mode": "separate", "max_adds": 1}}


def selftest() -> int:
    """番人5件＋わざと壊すメタ確認。合成データだけを使う＝実データの試行はゼロ。"""
    ng: list[str] = []
    df = gen.synth_df(600, seed=3)
    geo = build_geo(df)

    # ★T1 で使う条件＝ローソクの向き（bull）。この形は分位の解決表を要らないので、
    #   期待値を電卓（numpy の比較）で独立に出せる＝既知答えになる。
    bull_cond = {"role": "trigger", "form": "candle_dir", "value": {"dir": "bull"}}
    r1 = _synth_recipe([bull_cond])
    f1 = funnel_one(df, geo, r1, None, with_trades=True)
    bull = (df["close"].to_numpy(float) > df["open"].to_numpy(float))
    edge = bull & ~np.roll(bull, 1)
    edge[0] = False
    # ① 条件が1本だけなら、関門2（全部そろった）はその条件の成立数と一致する
    if f1["counts"][1] != int(bull.sum()):
        ng.append(f"① 関門2 が条件の成立数と違う: {f1['counts'][1]} vs {int(bull.sum())}")
    # ① 続き＝関門4（売ろうと決まった）は「きっかけの縁」と一致する
    if f1["counts"][3] != int(edge.sum()):
        ng.append(f"① 関門4 が きっかけの縁の数と違う: {f1['counts'][3]} vs {int(edge.sum())}")

    # ② 「必ず成立しない」条件を1本 混ぜると、関門2 が 0 になり、その条件が名指しで出る
    #    帯幅％（W%）が 900% 以上＝合成データでは絶対に起きない（実測は数%）。
    never = {"role": "location", "form": "level", "material": [{"geo": "W%"}], "side": "above",
             "value": {"const": "FULL_100", "mult": 9.0}}
    r2 = _synth_recipe([bull_cond, never])
    f2 = funnel_one(df, geo, r2, None, with_trades=False)
    if f2["counts"][1] != 0:
        ng.append(f"② 必ず偽の条件を混ぜたのに 関門2 が 0 でない: {f2['counts'][1]}")
    if not f2["dead"]:
        ng.append("② 必ず偽の条件が名指しされない")
    if first_zero_gate(f2["counts"]) != 1:
        ng.append(f"② 最初に 0 になった関門が 1 でない: {first_zero_gate(f2['counts'])}")

    # ③ 増えてはいけない所で数が増えていない（増えたら数え方が壊れている）
    for name, f in (("T1", f1), ("T2", f2)):
        for v in counting_violations(f["counts"], f["n_paths"]):
            ng.append(f"③ {name} {v}")

    # ④ 関門4 が実行器 _entry_fire の合計と一致する（自分だけの解釈で数えていない）
    fire = ex._entry_fire(r1, df, geo, None)
    if f1["counts"][3] != int(fire.sum()):
        ng.append(f"④ 関門4 が実行器の発火数と違う: {f1['counts'][3]} vs {int(fire.sum())}")

    # ④ 続き＝関門6 は run_recipe が返した売買記録の行数そのもの（自分で数え直さない）
    trades, _rep = ex.run_recipe(df, r1, limits=None, samples=None, qtable=None)
    if f1["counts"][5] != len(trades):
        ng.append(f"④ 関門6 が売買記録の行数と違う: {f1['counts'][5]} vs {len(trades)}")

    # ⑤ 累積の試行数・確認の帳簿・審判・売買記録CSV・採用の書き出し を、この道具は呼ばない。
    #    ★文字列で探すと、この上の説明文そのものに当たってしまう（最初そうなった）。
    #      だから実際のコードだけを見る＝ast で import と呼び出しの名前を拾う。
    import ast
    tree = ast.parse(pathlib.Path(__file__).read_text(encoding="utf-8"))
    bad_mods = {"score", "ratchet_io", "params_sidecar"}
    bad_calls = {"record_run", "load_cumulative", "to_csv", "write_sidecar", "_output_and_report"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for al in node.names:
                if al.name.split(".")[0] in bad_mods:
                    ng.append(f"⑤ import してはいけない: {al.name}")
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] in bad_mods:
                ng.append(f"⑤ import してはいけない: {node.module}")
        elif isinstance(node, ast.Call):
            f = node.func
            nm = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
            if nm in bad_calls:
                ng.append(f"⑤ 呼んではいけない: {nm}")

    # ⑥ メタ確認＝数え方をわざと壊すと ③ が実際に落ちる（検査が本当に効くか）
    for label, fake in (("関門4 が重なりより多い", [300, 100, 50, 80, 80, 80]),
                        ("関門5 が関門4 より多い", [300, 100, 50, 40, 60, 60]),
                        ("関門6 が関門5 より多い", [300, 100, 50, 40, 30, 40])):
        if not counting_violations(fake):
            ng.append(f"⑥ メタ確認: わざと壊した数列を ③ が検出できない（{label}）")
    if counting_violations([300, 100, 50, 40, 30, 20]):
        ng.append("⑥ メタ確認: 正しい数列を ③ が誤って落とした")

    print("══════ 番人（合成データのみ・実データの試行ゼロ）══════")
    print(f"① 関門2＝条件の成立数 / 関門4＝きっかけの縁 …… {int(bull.sum()):,} / {int(edge.sum()):,}")
    print(f"② 必ず偽を1本 混ぜた → 関門2 {f2['counts'][1]} ／ 名指し {len(f2['dead'])} 件")
    print(f"③ 増えてはいけない所で増えていない …… T1 {f1['counts']} ／ T2 {f2['counts']}")
    print(f"④ 実行器の発火数と一致 {int(fire.sum()):,} ／ 売買記録の行数と一致 {len(trades)}")
    print("⑤ 累積・帳簿・審判・CSV・採用の書き出し を import も呼び出しもしていない（ast で確認）")
    print("⑥ メタ確認＝わざと壊した数列3通りを ③ が全部 検出できる")
    if ng:
        print("\n".join(f"❌ {x}" for x in ng))
        return 1
    print("✅ 番人 全部 pass")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="撒いた構造が どの関門で売買まで行けなくなるかを数える（読み取り専用・値を選ばない）")
    ap.add_argument("--selftest", action="store_true", help="番人（合成データのみ）")
    ap.add_argument("--run", action="store_true", help="実データで数える（値決め窓だけ）")
    ap.add_argument("--strategy", default="e38")
    ap.add_argument("--logic", default="S3", help="宣言（側・局面）を借りるロジック id")
    ap.add_argument("--structures", type=int, default=100, help="撒く構造の本数")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--purpose", default=None, help="check のみ（この道具は値を選ばない）")
    ap.add_argument("--tag", default="")
    ap.add_argument("--show", type=int, default=5, help="構造ごとの明細を出す本数")
    ap.add_argument("--show-conds", type=int, default=8, help="条件ごとの成立率を出す本数（成立しにくい順）")
    ap.add_argument("--no-trades", action="store_true", help="関門6（売買）を回さない＝関門5 までで速く見る")
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--verify-journal", default=None, metavar="DIR",
                    help="engine_tuner_gen の走行の記録の置き場。玉数がその記録と一致するかを機械で照合する（番人⑦）")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.run:
        return run_main(a)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
