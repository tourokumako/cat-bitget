#!/usr/bin/env python3
"""gen_s22_fidelity.py — 短い期間で測った成績の順位が、全期間の順位と合うかを測る。

なぜ作るか
----------
まこさんの説明（2026-09-10）＝「あまり時間をかけずにまとめて検索可能であれば、まとめたほうが良い」。
そこで私が出した案＝**束を大量に作り、短い期間で測って悪い半分を落とす**（外の逐語＝
"evaluates their performance and throws away the worst half"）。

★この案の前提＝**短い期間で測った成績の順位が、全期間の順位とだいたい同じであること。**
  合わなければ、短い期間で捨てた束が、本当は良かったことになる。**だから先に測る。**

何をするか
----------
  1. 束を N本 組む（`regime_r9_diag` の --build と同じやり方＝順位から・値だけ範囲から）。
  2. **正解の印（強さ）は、値決め窓の全期間で1回だけ作る。**
     ★短い期間で作り直さない＝印は窓の中央値で切るので、期間を変えると印そのものが変わり、
       「順位が変わったのは束のせいか、印のせいか」が分けられなくなる。
  3. 各束の判定の列を全期間で作り、**先頭から f 割だけ切り出して**③（実はトレンドだった割合）を出す。
  4. 全期間の順位と、切り出した期間の順位の**順位相関**（スピアマン）を出す。

  --run N   束を N本 組んで測り、画面に出す
  --write N 同じことをして s22_fidelity.md に書く

★売買は1件も回さない（`--no-trades` 相当＝run_recipe も score も呼ばない）。値決め窓だけ（H8）。
★式は `regime_r9_diag` から import して使う（同じ式を2か所に書かない）。
★この道具は文書を作るだけ＝設計書と承認は要らない（恒久の決まり71番）。

限界（正直に）
  ・切り出すのは**先頭から**。値決め窓の後半で測ると別の結果になりうる（未確認）。
  ・束の数が少ないと順位相関は当てにならない。N は指定で増やせる。
  ・需給の列が入った束は走らせると止まる（next_step §6 の167番）＝その束は飛ばして数える。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SDK = ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api"
PRIORITY = SDK / "scripts" / "priority_rebuild"
RATCHET = SDK / ".claude" / "ratchet"

DEST = RATCHET / "s22_fidelity.md"

FRACTIONS = (1 / 64, 1 / 16, 1 / 4, 1.0)      # 切り出す割合（最後の 1.0 が全期間）
SEED = 7                                       # 既定（53 は需給が入って止まる＝§6 の167番）


def _load():
    sys.path.insert(0, str(PRIORITY))
    import engine_tuner as et
    import engine_tuner_exec as ex
    import engine_tuner_gen as gen
    import regime_r9_diag as r9
    from periods import SEARCH_END, SEARCH_START
    ad = et.load_adapter("e38")
    df, = et.load_windows_cached(ad, [(SEARCH_START, SEARCH_END)], et.WARM)
    return df, ad, et, ex, gen, r9, SEARCH_START, SEARCH_END


def build_bundles(gen, ex, ad, n: int, seed: int) -> tuple:
    """束を n本 組む。戻り＝(レシピの並び, 飛ばした件数と理由)。"""
    pool, tfs, _ = gen.material_pool()
    lm, _w = gen.load_limits()
    lm = gen.resolve_hold_range(lm, "e38")
    lim = {"n_min": None, "p_max": lm.get("p_max"), "count_range": lm.get("count_range"),
           "role_max": lm.get("role_max"), "depth_max": lm.get("depth_max"),
           "k_max": lm.get("k_max"), "r_min": lm.get("r_min")}
    regime = ad.regime("S2")
    out, skipped = [], []
    i = tries = 0
    while len(out) < n and tries < n * 20:
        rng = np.random.default_rng([seed, 1, tries])
        tries += 1
        try:
            r = gen.sample_structure(rng, lm, pool, tfs, side="SHORT", regime=regime,
                                     logic_id=f"F_{i}", build_regime=True, regime_order_n=i)
            gen.validate_drawn(r, limits=lim)
        except (gen.SampleError, ex.RecipeError) as e:
            skipped.append(f"案 {i}: {str(e)[:60]}")
            continue
        out.append(r)
        i += 1
    return out, skipped


def measure(n: int, seed: int) -> dict:
    """短い期間と全期間の③を、束ごとに出す。"""
    import pandas as pd
    df, ad, et, ex, gen, r9, start, end = _load()
    recipes, skipped = build_bundles(gen, ex, ad, n, seed)

    ts = pd.to_datetime(df["ts"])
    win = ((ts >= pd.Timestamp(start)) & (ts < pd.Timestamp(end))).to_numpy()
    df_win = df.loc[win].reset_index(drop=True)
    labels = r9._labels_for(df_win)               # ★全期間で1回だけ作る
    geo = gen._geo_of(df)
    horizons = sorted(labels.keys())

    rows, failed = [], []
    for rec in recipes:
        bd = rec["meta"]["regime"]["build"]
        out_col = bd["entry"]["out_col"]
        try:
            qt = r9._qtable(df, geo, [rec], start, end)
            d2 = df.copy()
            d2.attrs = {}
            ex.build_regime_columns(d2, rec, geo, qt)
            col_full = d2[out_col].to_numpy(bool)[win]
        except (SystemExit, ex.RecipeError) as e:
            failed.append(f"{rec['meta'].get('logic_id')}: {str(e)[:60]}")
            continue
        r = {"id": rec["meta"].get("logic_id")}
        for h in horizons:
            strong, usable = labels[h]
            for f in FRACTIONS:
                k = int(len(col_full) * f)
                r[f"h{h}_f{f:.5f}"] = r9.r9_trend_share(col_full[:k], strong[:k], usable[:k])
        r["share_full"] = r9.r9_share(col_full)
        rows.append(r)
    return {"rows": rows, "skipped": skipped, "failed": failed,
            "bars": int(win.sum()), "horizons": horizons, "n_asked": n, "seed": seed}


def breakdown(n: int, seed: int) -> dict:
    """束1本を測る時間の内訳を出す（★2026-09-10・まこさん「よい」）。

    なぜ要るか＝実測は「束1本 9.6秒」だけで、**中で何に時間が行っているかを誰も測っていない**。
    §2.2 の共通4（列を1回 作って閾値は一括比較）が効くかどうかは、内訳が分からないと言えない。
    """
    import time

    import pandas as pd
    t0 = time.perf_counter()
    df, ad, et, ex, gen, r9, start, end = _load()
    t_load = time.perf_counter() - t0

    t0 = time.perf_counter()
    recipes, skipped = build_bundles(gen, ex, ad, n, seed)
    t_build = time.perf_counter() - t0

    ts = pd.to_datetime(df["ts"])
    win = ((ts >= pd.Timestamp(start)) & (ts < pd.Timestamp(end))).to_numpy()
    t0 = time.perf_counter()
    labels = r9._labels_for(df.loc[win].reset_index(drop=True))
    t_labels = time.perf_counter() - t0
    geo = gen._geo_of(df)

    t_qtable = t_cols = t_score = 0.0
    ok = 0
    for rec in recipes:
        out_col = rec["meta"]["regime"]["build"]["entry"]["out_col"]
        try:
            t0 = time.perf_counter()
            qt = r9._qtable(df, geo, [rec], start, end)
            t_qtable += time.perf_counter() - t0
            d2 = df.copy()
            d2.attrs = {}
            t0 = time.perf_counter()
            ex.build_regime_columns(d2, rec, geo, qt)
            t_cols += time.perf_counter() - t0
            col = d2[out_col].to_numpy(bool)[win]
            t0 = time.perf_counter()
            for h, (s, u) in labels.items():
                r9.r9_trend_share(col, s, u)
            r9.r9_share(col)
            t_score += time.perf_counter() - t0
            ok += 1
        except (SystemExit, ex.RecipeError):
            continue
    return {"n_ok": ok, "n_asked": n, "seed": seed, "bars": int(win.sum()),
            "load": t_load, "build": t_build, "labels": t_labels,
            "qtable": t_qtable, "cols": t_cols, "score": t_score}


def build_breakdown(b: dict) -> str:
    ok = max(b["n_ok"], 1)
    per = {"分位の解決表を作る": b["qtable"] / ok,
           "判定の列を作る": b["cols"] / ok,
           "成績（③と①）を出す": b["score"] / ok}
    total_per = sum(per.values())
    L = []
    add = L.append
    add("# 束1本を測る時間の内訳")
    add("")
    add("**★この表はプログラムが作ります（手で書き換えない）。**"
        "出どころ＝`gen_s22_fidelity.py --breakdown N` の実測。")
    add("")
    add("**なぜ在るか**＝実測は「束1本 9.6秒」だけで、**中で何に時間が行っているかを誰も測っていません**でした。"
        "§2.2 の共通の決まり（列を1回 作って閾値は一括比較）が効くかどうかは、内訳が分からないと言えません。")
    add("")
    add(f"**測った束＝{b['n_ok']} 本**（頼んだ {b['n_asked']} 本・種 {b['seed']}）／"
        f"**値決め窓＝{b['bars']:,} 本**")
    add("")
    add("## 1回だけかかるもの（束の数に関係しない）")
    add("")
    add("| 何 | 秒 |")
    add("|---|---|")
    add(f"| データを読む（キャッシュが効くと短い） | **{b['load']:.2f}** |")
    add(f"| 束を {b['n_asked']} 本 組む | **{b['build']:.2f}** |")
    add(f"| 正解の印を作る | **{b['labels']:.2f}** |")
    add("")
    add("## 束1本あたり（束の数だけ増える）")
    add("")
    add("| 何 | 秒／本 | 割合 |")
    add("|---|---|---|")
    for k, v in sorted(per.items(), key=lambda x: -x[1]):
        add(f"| {k} | **{v:.2f}** | {v / total_per:.0%} |")
    add(f"| **合計** | **{total_per:.2f}** | 100% |")
    add("")
    add("## 読み方")
    add("")
    add("**★「判定の列を作る」が大きければ、§2.2 の共通の決まり（列を1回 作って使い回す）が効きます。**"
        "同じ材料を使う束どうしで、列の作り直しを省けるからです。")
    add("")
    add("**★「成績を出す」が大きければ、列を使い回しても縮みません。**")
    add("")
    return "\n".join(L)


def count_keys(n: int, seed: int) -> dict:
    """束が使う「分位の鍵」を、1本ずつ渡した場合とまとめて渡した場合で数える。

    なぜ要るか（2026-09-10・まこさん OK）＝時間の99%は「その分位が実際にいくつか」を計算する所。
    その計算は**鍵ごとに1回**で済む（`build_qtable` は複数のレシピをまとめて受ける作り）。
    **いまは診断が束を1本ずつ渡しているので、同じ鍵を何度も計算し直している。**
    ★まとめて渡すとどれだけ減るかは、鍵が重なる度合いで決まる＝それを数える。
    """
    df, ad, et, ex, gen, r9, start, end = _load()
    recipes, skipped = build_bundles(gen, ex, ad, n, seed)
    per = [len(gen.needed_qkeys([r])) for r in recipes]
    allk = gen.needed_qkeys(recipes)
    return {"n": len(recipes), "n_asked": n, "seed": seed, "skipped": len(skipped),
            "per": per, "sum_per": sum(per), "uniq": len(allk)}


def build_keys(k: dict) -> str:
    n = max(k["n"], 1)
    avg = k["sum_per"] / n
    save = (1 - k["uniq"] / k["sum_per"]) if k["sum_per"] else 0.0
    L = []
    add = L.append
    add("# 束が使う「分位の鍵」は、どれだけ重なるか")
    add("")
    add("**★この表はプログラムが作ります（手で書き換えない）。**"
        "出どころ＝`gen_s22_fidelity.py --keys N` の実測。")
    add("")
    add("**なぜ在るか**＝束1本を測る時間の**99%**は、"
        "「その分位が実際にいくつか」を計算する所に行っています（`s22_breakdown.md`）。"
        "**その計算は鍵ごとに1回で済みます。**"
        "いまは束を1本ずつ渡しているので、同じ鍵を何度も計算し直しています。")
    add("")
    add(f"**測った束＝{k['n']} 本**（頼んだ {k['n_asked']} 本・種 {k['seed']}"
        f"・組めなかった案 {k['skipped']} 件）")
    add("")
    add("| 何 | 数 |")
    add("|---|---|")
    add(f"| 束1本が使う鍵（平均） | **{avg:.1f}** |")
    add(f"| 1本ずつ渡したときの合計（いまの形） | **{k['sum_per']}** |")
    add(f"| まとめて渡したときの種類（重複を除く） | **{k['uniq']}** |")
    add(f"| **減る割合** | **{save:.1%}** |")
    add("")
    add("## 時間に直すと")
    add("")
    add("**★1つの鍵を計算する時間**＝`s22_breakdown.md` の実測（束1本 2.77秒）を、"
        f"束1本が使う鍵の数（{avg:.1f}）で割って **約 {2.77 / avg:.2f} 秒**。")
    add("")
    add("| | 鍵の数 | 時間 |")
    add("|---|---|---|")
    add(f"| いまの形（1本ずつ） | {k['sum_per']} | **{k['sum_per'] * (2.77 / avg):.0f} 秒** |")
    add(f"| まとめて渡す形 | {k['uniq']} | **{k['uniq'] * (2.77 / avg):.0f} 秒** |")
    add("")
    add("**★これは測った束の数での話です。**束を増やすと、鍵の重なりは変わります"
        "（同じ材料を使う束が増えるほど、重なりも増える見込み）。")
    add("")
    return "\n".join(L)


def key_time(n: int, seed: int) -> dict:
    """鍵1つ 0.36秒 の中身を、①列を作る ②分位81段を出す に分けて測る。

    ★仮説（2026-09-10）＝`build_qtable`（2928行）は分位を **1段ずつ81回** 計算している
      （`{q: float(np.quantile(s, ...)) for q in grid}`）。**1回でまとめて出せるはず。**
      それが本当なら、ここが縮む。
    """
    import time

    import numpy as _np
    import pandas as pd
    df, ad, et, ex, gen, r9, start, end = _load()
    recipes, _sk = build_bundles(gen, ex, ad, n, seed)
    keys = gen.needed_qkeys(recipes)
    geo = gen._geo_of(df)
    lm, _w = gen.load_limits()
    grid = gen.quantile_list(lm)
    ts = pd.to_datetime(df["ts"])
    mask = ((ts >= start) & (ts < end)).to_numpy()

    rows = []
    for key, specs in list(keys.items()):
        if len(specs) != 1:                      # 材料2本の組みは、この測りでは飛ばす
            continue
        name, pre = specs[0]
        ex._MAT_MEMO["sig"], ex._MAT_MEMO["v"] = None, {}   # 覚えている分を消す＝初回の時間を測る
        t0 = time.perf_counter()
        try:
            if name in geo:
                a = _np.asarray(geo[name], float)
            elif name in df.columns:
                a = df[name].to_numpy(float)
            else:
                a = ex.material_array(df, name)
            if pre:
                a = ex._apply_pre(a, pre, df)
        except (Exception, SystemExit):
            # ★需給の列（時間足を持たない）はここで止まる＝§6 の167番。その鍵は飛ばす。
            continue
        t_col = time.perf_counter() - t0
        s = a[mask]
        s = s[_np.isfinite(s)]
        if not len(s):
            continue
        t0 = time.perf_counter()                 # いまの形＝81回 呼ぶ
        _one = {q: float(_np.quantile(s, int(q.lstrip("q")) / 100.0)) for q in grid}
        t_q_one = time.perf_counter() - t0
        t0 = time.perf_counter()                 # まとめる形＝1回で配列を渡す
        _all = _np.quantile(s, [int(q.lstrip("q")) / 100.0 for q in grid])
        t_q_all = time.perf_counter() - t0
        tf = name.rsplit("__", 1)[1] if "__" in name else "（時間足なし）"
        rows.append({"key": key, "tf": tf, "t_col": t_col,
                     "t_q_one": t_q_one, "t_q_all": t_q_all, "bars": len(s)})
    return {"rows": rows, "n_bundles": len(recipes), "n_keys": len(keys), "grid": len(grid)}


def build_keytime(res: dict) -> str:
    import statistics as st
    rows = res["rows"]
    if not rows:
        return "# 鍵1つの中身｜測れた鍵が0件"
    col = st.median(r["t_col"] for r in rows)
    q1 = st.median(r["t_q_one"] for r in rows)
    qa = st.median(r["t_q_all"] for r in rows)
    by_tf: dict = {}
    for r in rows:
        by_tf.setdefault(r["tf"], []).append(r["t_col"])
    L = []
    add = L.append
    add("# 鍵1つを解くのに、何に時間が行っているか")
    add("")
    add("**★この表はプログラムが作ります（手で書き換えない）。**"
        "出どころ＝`gen_s22_fidelity.py --keytime N` の実測。")
    add("")
    add(f"**測れた鍵＝{len(rows)} 件**（束 {res['n_bundles']} 本が使う鍵 {res['n_keys']} 件のうち、"
        "材料1本のもの）／**分位の段数＝" + str(res["grid"]) + "**")
    add("")
    add("## 中身（中央値）")
    add("")
    add("| 何 | 秒 | 割合 |")
    add("|---|---|---|")
    tot = col + q1
    add(f"| **材料の列を作る** | **{col:.3f}** | {col / tot:.0%} |")
    add(f"| **分位を1段ずつ81回 計算する（いまの形）** | **{q1:.3f}** | {q1 / tot:.0%} |")
    add(f"| （参考）分位を1回でまとめて計算する | {qa:.4f} | — |")
    add("")
    if q1 > 0:
        add(f"**★分位をまとめて計算すると {q1 / qa:.0f}分の1 になります**"
            f"（{q1:.3f}秒 → {qa:.4f}秒）。")
    add("")
    add("## 時間足ごとの「列を作る」時間（中央値）")
    add("")
    add("| 時間足 | 件数 | 秒 |")
    add("|---|---|---|")
    for tf, vals in sorted(by_tf.items(), key=lambda x: -st.median(x[1])):
        add(f"| {tf} | {len(vals)} | **{st.median(vals):.3f}** |")
    add("")
    add("**★列を作る時間が大きければ、そこが壁です。**"
        "**分位の計算が大きければ、まとめて計算するだけで縮みます。**")
    add("")
    return "\n".join(L)


def spearman(a: list, b: list) -> float:
    """順位相関（スピアマン）。片方が全部 同じ値、または2本未満なら nan。"""
    import numpy as _np
    x, y = [], []
    for p, q in zip(a, b):
        if p == p and q == q:                     # nan を除く
            x.append(p)
            y.append(q)
    if len(x) < 2:
        return float("nan")
    rx = _np.argsort(_np.argsort(_np.asarray(x, float)))
    ry = _np.argsort(_np.argsort(_np.asarray(y, float)))
    if rx.std() == 0 or ry.std() == 0:
        return float("nan")
    return float(_np.corrcoef(rx, ry)[0, 1])


def build(res: dict) -> str:
    rows = res["rows"]
    L = []
    add = L.append
    add("# 短い期間で測った順位は、全期間の順位と合うか")
    add("")
    add("**★この表はプログラムが作ります（手で書き換えない）。**"
        "出どころ＝`gen_s22_fidelity.py --write N` の実測。")
    add("")
    add("**なぜ在るか**＝「束を大量に作り、短い期間で測って悪い半分を落とす」案の**前提**を確かめるため。"
        "**合わなければ、その案は使えません。**")
    add("")
    add(f"**測った束＝{len(rows)} 本**（頼んだ {res['n_asked']} 本・種 {res['seed']}）／"
        f"**値決め窓＝{res['bars']:,} 本**")
    if res["skipped"]:
        add("")
        add(f"**組めなかった案＝{len(res['skipped'])} 件**（同じ番号で引き直した）")
    if res["failed"]:
        add("")
        add(f"**走らせて止まった束＝{len(res['failed'])} 件**")
        for f in res["failed"]:
            add(f"  - {f}")
    add("")
    add("**★正解の印は、値決め窓の全期間で1回だけ作りました。**"
        "短い期間で作り直すと、印そのものが変わって比べられなくなるためです。")
    add("")
    for h in res["horizons"]:
        add(f"## 先を見る本数＝{h} 本")
        add("")
        add("| 束 | 64分の1 | 16分の1 | 4分の1 | 全期間 |")
        add("|---|---|---|---|---|")
        for r in rows:
            cells = []
            for f in FRACTIONS:
                v = r.get(f"h{h}_f{f:.5f}")
                cells.append(f"{v:.1%}" if v == v else "nan")
            add(f"| {r['id']} | " + " | ".join(cells) + " |")
        add("")
        full = [r.get(f"h{h}_f{1.0:.5f}") for r in rows]
        add("**順位の合い方（全期間と比べた順位相関・1.0 なら順位が完全に同じ）**")
        add("")
        add("| 切り出した期間 | 順位相関 |")
        add("|---|---|")
        for f in FRACTIONS[:-1]:
            part = [r.get(f"h{h}_f{f:.5f}") for r in rows]
            s = spearman(part, full)
            add(f"| {1 / f:.0f}分の1 | **{s:.3f}**" + (" |" if s == s else "（測れない）|"))
        add("")
    add("## 読み方")
    add("")
    add("**順位相関が 1.0 に近ければ、短い期間で落としても、全期間で良い束を捨てません。**"
        "**0 に近ければ、短い期間の成績は当てになりません。**")
    add("")
    add("**★この表は数字を出すだけです。**「使える／使えない」の判定はしていません。")
    add("")
    return "\n".join(L)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--run", type=int, default=None, help="束を N本 組んで測り、画面に出す")
    p.add_argument("--write", type=int, default=None, help="同じことをして s22_fidelity.md に書く")
    p.add_argument("--breakdown", type=int, default=None, help="束1本を測る時間の内訳を出す")
    p.add_argument("--keys", type=int, default=None, help="束が使う分位の鍵が、どれだけ重なるかを数える")
    p.add_argument("--keytime", type=int, default=None, help="鍵1つを解く時間を、列づくりと分位計算に分ける")
    p.add_argument("--seed", type=int, default=SEED)
    a = p.parse_args()
    if getattr(a, "keytime", None):
        body = build_keytime(key_time(a.keytime, a.seed))
        (RATCHET / "s22_keytime.md").write_text(body, encoding="utf-8")
        print(body)
        print(f"\n✅ 書いた: {RATCHET / 's22_keytime.md'}")
        return 0
    if getattr(a, "keys", None):
        body = build_keys(count_keys(a.keys, a.seed))
        (RATCHET / "s22_keys.md").write_text(body, encoding="utf-8")
        print(body)
        print(f"\n✅ 書いた: {RATCHET / 's22_keys.md'}")
        return 0
    if a.breakdown:
        body = build_breakdown(breakdown(a.breakdown, a.seed))
        (RATCHET / "s22_breakdown.md").write_text(body, encoding="utf-8")
        print(body)
        print(f"\n✅ 書いた: {RATCHET / 's22_breakdown.md'}")
        return 0
    n = a.run or a.write
    if not n:
        p.print_help()
        return 0
    body = build(measure(n, a.seed))
    if a.write:
        DEST.write_text(body, encoding="utf-8")
        print(f"✅ --write 完了: {DEST}（{len(body.splitlines())}行）")
    else:
        print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
