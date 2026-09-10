#!/usr/bin/env python3
"""gen_s22_combi.py — §2.2 の段1〜段3 を「まとめて」回すと何通りになるかを数える。

なぜ作るか
----------
まこさんの説明（逐語 2026-09-10）＝「段ごとに検索範囲の段階をわけたのは、１，２，３を
まとてめて検索すると時間がかかるのかと想定して、分割しているが、**あまり時間をかけずに
まとめて検索可能であれば、まとめたほうが良い**」。

★分割は時間への対処であって、目的ではない。だから「まとめたら何通りか」を先に数える。
★段ごとに1つずつ確定させると、先の段で落とした候補が、後の段と組んだときに効いたか
  分からない（私が 2026-09-01 に書いた論点＝worklog 20260901 §18 の（6-3））。

何を数えるか
------------
  枡ごとの候補の数を、**実物から**数える（私が数字を作らない）。
    ①帯（R1・R3）      = 役割 location の組（種類×時間足）のうち、上位足のもの
    ②強さの否定（R5）  = 役割 env の組のうち、法則 R5 が名指しした family
    ③3枠目（R6）       = 役割 sufficiency の組のうち、法則 R6 が名指しした family ＋「なし」
    ④閾値の分位        = search_limits.json の quantile_range の幅
    ⑤続く本数 n        = search_limits.json の int_range の幅
    ⑥保つ上限          = search_limits.json の state_hold_bars_range の幅
  掛け算して、段1〜段3 をまとめて回したときの通り数を出す。

  --run    数えて画面に出す
  --write  数えて s22_combi.md に書く

fail-closed（黙って通さない）
  1. 法則ファイルが読めない → 止まる
  2. R5 か R6 が family を名指ししていない → 止まる（数を私が決めない）
  3. 成績表が読めない → 止まる

限界（正直に）
  ・数えるのは「枡ごとの候補の数」だけ。G7 が落とす分は引いていない
    （落ちる割合は走らせないと分からない）。＝この数は**上限**。
  ・時間の見積もりに使う「1本あたりの秒数」は、この道具では測らない。
    ★束1本を最後まで測った実測は、2026-09-10 時点で存在しない（stage0_timing.md は
      「1列を作る時間」と「列1本を閾値と比べる時間」だけ）。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SDK = ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api"
PRIORITY = SDK / "scripts" / "priority_rebuild"
RATCHET = SDK / ".claude" / "ratchet"

DEST = RATCHET / "s22_combi.md"
LIMITS = PRIORITY / "recipes" / "search_limits.json"

# ★絞り込みの段階で使わない時間足（まこさん決定 2026-09-10・milestones2 §2.2-3）
DROP_TFS = ("1m", "3m", "10m")


def _load():
    sys.path.insert(0, str(PRIORITY))
    import engine_tuner_gen as gen
    import engine_tuner_exec as ex
    return gen, ex


def count_slots() -> dict:
    """枡ごとの候補の数を、実物から数える。"""
    gen, ex = _load()
    laws = gen.laws_for_scene("range")
    fams_r5, _side5 = gen._law_families(laws, "R5")
    fams_r6, _side6 = gen._law_families(laws, "R6")
    if not fams_r5:
        raise SystemExit("[gen_s22_combi] R5 が family を名指ししていない（fail-closed 2）")
    if not fams_r6:
        raise SystemExit("[gen_s22_combi] R6 が family を名指ししていない（fail-closed 2）")

    table = gen.load_signal_table()
    tfs_all = list(table["tfs"])
    upper = [t for t in tfs_all if tfs_all.index(t) > tfs_all.index("5m")]
    # ★まこさん決定 2026-09-10（逐語「重い1分足・3分足・10分足は絞り込みの段階では外して良い」
    #   「レジーム判定では1分足・3分足は…レンジの状態判断には不要」）＝milestones2 §2.2-3。
    #   実測の根拠＝鍵1つを解く時間（`s22_keytime.md`）＝1m 0.460秒／3m 0.316秒／10m 0.258秒／1d 0.091秒。
    upper = [t for t in upper if t not in DROP_TFS]

    def groups(role, fams=None, tf_ok=None, label=None):
        """その役割の組（種類×時間足）を数える。fams が在ればその family だけ。"""
        out = []
        for fam, tf, lab, hor, med, ncol, col in gen.ranked_groups(role, label):
            if fams and fam not in fams:
                continue
            if tf_ok is not None and tf not in tf_ok:
                continue
            out.append((fam, tf))
        return out

    # ★2026-09-10 の直し（まこさん指摘「なんでこのようなミスが起きた？」）
    #   直す前＝`groups("location", None, upper)`＝**系統で1つも絞っていなかった**。
    #   段2a は R5 の family で、段2c は R6 の family で絞っているのに、段1 だけ絞りが無かった。
    #   なぜ起きたか＝法則 R1・R3 は「系統＝構造・位置」としか言わず、指標の名前を名指ししない。
    #     私は「法則に名指しが無いから絞らない」と判断し、**§2.2 の本文が挙げる「帯タイプ7系統」を
    #     候補の絞りとして読まなかった**（例示だと思った）。
    #   結果＝段1 の候補を 3,408本（時間足を外して 2,982本）と数え、設計書に書いた。
    #     §2.2 の想定は「約48」で、3桁 違う（milestones2:202 に、その注意を私自身が書いていた）。
    #   直し＝§2.2 の候補の一覧（`gen_stage0_match.STAGES` の段1）で絞る。
    #     ★一覧を2か所に書かない＝あちらを正本にして import する。
    sys.path.insert(0, str(ROOT / ".claude" / "tools"))
    try:
        from gen_stage0_match import STAGES as _S22_STAGES
    except Exception as e:
        raise SystemExit(f"[gen_s22_combi] §2.2 の候補の一覧を読み込めない: {e}（fail-closed 4）")
    _band_needles = [nd for _name, nd in _S22_STAGES[0][2]]
    if not _band_needles:
        raise SystemExit("[gen_s22_combi] §2.2 の段1 の候補が0件（fail-closed 4）")
    band_all = groups("location", None, upper)
    band = [g for g in band_all if any(nd in g[0] for nd in _band_needles)]
    if not band:
        raise SystemExit("[gen_s22_combi] 段1 が §2.2 の候補で1件も引けない（fail-closed 5）")
    strong = groups("env", set(fams_r5), upper, label="強さ")     # 段2a（同上）
    # ★段2c は役割 sufficiency＝型の表では全時間足。ここからも 1m/3m/10m を外す（§2.2-3）。
    third_tfs = [t for t in tfs_all if t not in DROP_TFS]
    third = groups("sufficiency", set(fams_r6), third_tfs)       # 段2c

    lim = json.loads(LIMITS.read_text(encoding="utf-8"))

    def width(key, sub=None):
        d = lim.get(key)
        if isinstance(d, dict) and sub:
            d = d.get(sub)
        if not isinstance(d, dict):
            return None, None
        lo, hi = d.get("lo"), d.get("hi")
        if lo is None or hi is None:
            return None, None
        return (int(lo), int(hi))

    q_lo, q_hi = width("quantile_range")
    n_lo, n_hi = width("int_range")
    h_lo, h_hi = width("state_hold_bars_range")

    return {
        "帯（段1・location・上位足）": len(band),
        "強さの否定（段2a・env・R5 の family・上位足）": len(strong),
        "3枠目（段2c・sufficiency・R6 の family）＋「なし」": len(third) + 1,
        "R5 が名指しした family": sorted(fams_r5),
        "R6 が名指しした family": sorted(fams_r6),
        "分位の幅（quantile_range）": (q_lo, q_hi),
        "続く本数 n（int_range）": (n_lo, n_hi),
        "保つ上限（state_hold_bars_range）": (h_lo, h_hi),
        "上位足": upper,
    }


def build(c: dict) -> str:
    band = c["帯（段1・location・上位足）"]
    strong = c["強さの否定（段2a・env・R5 の family・上位足）"]
    third = c["3枠目（段2c・sufficiency・R6 の family）＋「なし」"]
    q = c["分位の幅（quantile_range）"]
    n = c["続く本数 n（int_range）"]
    h = c["保つ上限（state_hold_bars_range）"]
    qn = (q[1] - q[0] + 1) if q[0] is not None else None
    nn = (n[1] - n[0] + 1) if n[0] is not None else None
    hn = (h[1] - h[0] + 1) if h[0] is not None else None

    L = []
    add = L.append
    add("# §2.2 の段1〜段3 を「まとめて」回すと何通りか")
    add("")
    add("**★この表はプログラムが作ります（手で書き換えない）。**"
        "出どころ＝`gen_s22_combi.py --write`。数は実物（成績表・法則ファイル・"
        "`search_limits.json`）から数えています。")
    add("")
    add("**なぜ在るか**＝まこさんの説明（2026-09-10）＝「段ごとに検索範囲の段階をわけたのは、"
        "１，２，３をまとてめて検索すると時間がかかるのかと想定して、分割しているが、"
        "**あまり時間をかけずにまとめて検索可能であれば、まとめたほうが良い**」。"
        "**だから、まとめたら何通りかを先に数えます。**")
    add("")
    add("## 枡ごとの候補の数（実物を数えた）")
    add("")
    add("| 枡 | 何を数えたか | 数 |")
    add("|---|---|---|")
    add(f"| **段1 帯** | 役割 location の組（指標の種類 × 時間足）のうち、5分足より上の足 | **{band:,}** |")
    add(f"| **段2a 強さの否定** | 役割 env の組のうち、法則 R5 が名指しした family・上位足・札「強さ」 | **{strong:,}** |")
    add(f"| **段2c 3枠目** | 役割 sufficiency の組のうち、法則 R6 が名指しした family ＋「なし」 | **{third:,}** |")
    add(f"| 段2b 向きの否定 | `rg5_uptrend` の not（1通り・承認済みの借用） | **1** |")
    add("")
    add(f"**R5 が名指しした family**＝{'・'.join(c['R5 が名指しした family'])}")
    add("")
    add(f"**R6 が名指しした family**＝{'・'.join(c['R6 が名指しした family'])}")
    add("")
    add(f"**上位足**＝{'・'.join(c['上位足'])}")
    add("")
    add("## 値の幅（`search_limits.json` の実物）")
    add("")
    add("| 何 | 範囲 | 通り |")
    add("|---|---|---|")
    add(f"| 閾値の分位（`quantile_range`） | q{q[0]}〜q{q[1]} | **{qn}** |" if qn else
        "| 閾値の分位（`quantile_range`） | **設定に無い** | — |")
    add(f"| 続く本数 n（`int_range`） | {n[0]}〜{n[1]} | **{nn}** |" if nn else
        "| 続く本数 n（`int_range`） | **設定に無い** | — |")
    add(f"| 保つ上限（`state_hold_bars_range`） | {h[0]}〜{h[1]} | **{hn}** |" if hn else
        "| 保つ上限（`state_hold_bars_range`） | **設定に無い** | — |")
    add("")
    add("## まとめて回すと何通りか（掛け算）")
    add("")
    if None in (qn, nn, hn):
        add("**★値の幅が設定に無いものが在るので、掛け算は出しません**（数を私が作らないため）。")
        add("")
        return "\n".join(L)
    materials = band * strong * third
    with_q = materials * (qn ** 3)          # 帯・強さ・3枠目 の3つの閾値
    total = with_q * nn * hn
    add(f"1. **材料の組み合わせだけ**＝{band:,} × {strong:,} × {third:,} ＝ **{materials:,} 通り**")
    add(f"2. **＋閾値の分位3つ**（帯・強さ・3枠目）＝ × {qn}³ ＝ **{with_q:,} 通り**")
    add(f"3. **＋続く本数と保つ上限**＝ × {nn} × {hn} ＝ **{total:,} 通り**")
    add("")
    add("**★この数は上限です。**G7（法則の審査）が落とす分は引いていません"
        "（落ちる割合は走らせないと分かりません）。")
    add("")
    add("## 時間の見積もりに要るもの（まだ無いもの）")
    add("")
    add("**★束1本を最後まで測った実測は、2026-09-10 時点で存在しません。**"
        "`stage0_timing.md` が測ったのは「1列を作る時間（約58ミリ秒）」と"
        "「列1本を閾値と比べて真偽にする時間（1.3〜2.0ミリ秒）」の2つだけです。"
        "**束1本＝条件5つ＋hysteresis＋G7 の審査＋R9 の3つの計算**なので、"
        "この2つからは出せません。")
    add("")
    return "\n".join(L)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--run", action="store_true", help="数えて画面に出す")
    p.add_argument("--write", action="store_true", help="数えて s22_combi.md に書く")
    a = p.parse_args()
    if not (a.run or a.write):
        p.print_help()
        return 0
    body = build(count_slots())
    if a.write:
        DEST.write_text(body, encoding="utf-8")
        print(f"✅ --write 完了: {DEST}（{len(body.splitlines())}行）")
    else:
        print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
