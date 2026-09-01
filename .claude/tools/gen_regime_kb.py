#!/usr/bin/env python3
"""regime_detection_kb.md の §11（場面ごとの相場の法則）と §12（調べた結果）を、json から機械で作る。

なぜ作ったか
------------
まこさん指示（2026-08-29・逐語）＝「前回調べた情報をすべてヌケモレなく追記すること。自動生成推奨。」
まこさん指示（同日・逐語）＝「この法則が肝になるので、明確に法則が分かるように、文書を整理して
読みやすい状態にしてほしい。現状は汚すぎて、私には解読不能なんだけど。」
手で md に書くと、次に足すときに腐る（materials.md・composition_rules.md と同じ理由）。

何をするか
----------
  --write [laws|findings|all]   元データから節を作り、KB のマーカーの中に書く（既定＝all）。
  --verify [laws|findings|all]  マーカーの中が手で書き換えられていないかを検出する。
  --selftest                    わざと壊して ❌ が出るかを試す。

★KB のマーカーの外は1文字も触らない。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RATCHET = ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet"
KB = ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/regime_detection_kb.md"

SRC = {
    "flow": RATCHET / "m2_todo.json",
    "todo": RATCHET / "m2_todo.json",
    "laws": RATCHET / "regime_laws.json",
    "findings": RATCHET / "regime_kb_findings.json",
    "premise": RATCHET / "regime_laws.json",
}
TAG = {"flow": "M2_FLOW", "todo": "M2_TODO", "laws": "KB_LAWS", "findings": "KB_FINDINGS", "premise": "M2_PREMISE"}


def _begin(kind: str, h: str) -> str:
    return f"<!-- {TAG[kind]}_START hash={h} gen_regime_kb.py が自動生成＝手で書き換えない -->"


def _begin_re(kind: str) -> re.Pattern:
    return re.compile(rf"<!-- {TAG[kind]}_START hash=([0-9a-f]{{16}}).*?-->")


def _end(kind: str) -> str:
    return f"<!-- {TAG[kind]}_END -->"


def _h(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]


def _esc(s: str) -> str:
    """表のセルに入れるとき、| を壊さないようにする。"""
    return str(s).replace("|", "／").replace("\n", " ")


def _kakeru(r: dict) -> str:
    """11-x の表の「engine_tuner で書けるか」の欄＝判定の有無から機械で出す（M2-B-2b・2026-08-30）。
    手書きの `書けるか` は、判定も置き場も無い法則にだけ使う（R1 が判定を持つのに「✕」のままだった穴を塞ぐ）。"""
    j = r.get("機械が読む判定")
    if isinstance(j, dict):
        return f"○ 判定あり（{j.get('型')}）"
    if r.get("判定の置き場"):
        return f"— 置き場＝{r['判定の置き場']}"
    return r.get("書けるか", "—")


def coverage(d: dict) -> tuple[int, list[str]]:
    """「判定を揃えた場面」の法則が、全部「機械が読む判定」か「判定の置き場」を持つかを数える（M2-B-2b の確かめ方）。
    戻り＝(1 なら ❌ あり, 表示する行)。"""
    rc, lines = 0, []
    for sc in d.get("判定を揃えた場面") or []:
        rows = [x for x in d["法則"] if x.get("場面") == sc]
        a = sum(1 for x in rows if isinstance(x.get("機械が読む判定"), dict))
        b = sum(1 for x in rows if x.get("判定の置き場") and not isinstance(x.get("機械が読む判定"), dict))
        c = len(rows) - a - b
        mark = "✅" if c == 0 and rows else "❌"
        if c or not rows:
            rc = 1
        lines.append(f"{mark} 判定を揃えた場面「{sc}」＝{len(rows)}件＝機械が読む判定 {a}件＋判定の置き場 {b}件＋どちらも無い {c}件")
    return rc, lines


def build_flow(d: dict) -> str:
    """json から §2（フロー13段）を組み立てる。

    まこさん指示（2026-08-29・逐語）＝「§2 フロー（13段）のやることの部分も狭い」。
    ★表は3列だけ（段 ／ やること ／ 状態）。長い中身は表の下の「1段ずつの説明」へ。
    """
    L: list[str] = []
    add = L.append
    flow = d["フロー"]

    add(f"# §2 フロー（{len(flow)}段）（★この節は機械が作ります・手で書き換えない）")
    add("")
    add(f"**元データ**＝`.claude/ratchet/m2_todo.json` ／ **作り方**＝`{d['_作り方']}`")
    add("")
    add("| 段 | やること | 状態 |")
    add("|---|---|---|")
    for r in flow:
        add(f"| **{r['段']}** | {_esc(r['一文'])} | {_esc(r['状態'])} |")
    add("")
    add("## 1段ずつの説明（触るファイルと、終わったと言える条件）")
    add("")
    for r in flow:
        add(f"### {r['段']}｜{r['一文']}")
        add("")
        add(f"- **触るファイル**＝{r['触るファイル']}")
        add(f"- **終わったと言える条件**＝{r['終わったと言える条件']}")
        for x in r.get("注意") or []:
            add(f"- {x}")
        add(f"- **状態**＝{r['状態']}")
        add("")

    return "\n".join(L).rstrip() + "\n"


def build_todo(d: dict) -> str:
    """json から §3（やることリスト）を組み立てる。

    まこさん指示（2026-08-29・逐語）＝「プレビューでみると、やることの横幅が狭いのを直して」。
    ★表は3列だけ（# ／ やること ／ 状態）。長い中身は表の下の「1件ずつの説明」へ。
    """
    L: list[str] = []
    add = L.append
    todos = d["やること"]
    steps = d["段"]
    intent = d["順番の意図"]

    add("# §3 やることリスト（★この節は機械が作ります・手で書き換えない）")
    add("")
    add(f"**{d['_前置き']}**")
    add("")
    add(f"**元データ**＝`.claude/ratchet/m2_todo.json` ／ **作り方**＝`{d['_作り方']}`")
    add("")

    for st in steps:
        rows = [t for t in todos if t["段"] == st["鍵"]]
        if not rows:
            continue
        note = f"（{st['注記']}）" if st["注記"] else ""
        add(f"## {st['鍵']}｜{st['見出し']}{note}｜{len(rows)}件")
        add("")

        # 段ごとの前置き（M2-B だけ持つ）
        pre = st.get("前置き")
        if pre:
            add(f"> ### {pre['見出し']}")
            add(">")
            for t in pre["本文"]:
                add(f"> {t}")
                add(">")
            add("> | 場面 | 件数 | どこで扱うか |")
            add("> |---|---|---|")
            for r in pre["扱う範囲"]:
                add(f"> | {_esc(r['場面'])} | {r['件数']} | {_esc(r['どこで扱うか'])} |")
            add(">")
            add(f"> ### {pre['性質の見出し']}")
            add(">")
            add("> | 印 | 性質 | 中身 | 部品を当てるか | 足す先 |")
            add("> |---|---|---|---|---|")
            for r in pre["性質"]:
                add(f"> | **{r['印']}** | **{_esc(r['性質'])}** | {_esc(r['中身'])} "
                    f"| **{_esc(r['部品を当てるか'])}** | {_esc(r['足す先'])} |")
            add(">")
            for t in pre["性質の注記"]:
                add(f"> {t}")
            add("")

        # ★表は3列だけ
        add("| # | やること | 状態 |")
        add("|---|---|---|")
        for t in rows:
            add(f"| **{t['番号']}** | {_esc(t['一文'])} | {_esc(t['状態'])} |")
        add("")

        add(f"### {st['鍵']} の1件ずつの説明")
        add("")
        for t in rows:
            add(f"#### {t['番号']}｜{t['一文']}")
            add("")
            add(f"- **中身**＝{t['中身']}")
            add(f"- **触るファイル**＝{t['触るファイル']}")
            add(f"- **出るもの**＝{t['出るもの']}")
            add(f"- **確かめ方**＝{t['確かめ方']}")
            if t.get("実測"):
                add(f"- **実測**＝{t['実測']}")
            for x in t.get("注意") or []:
                add(f"- {x}")
            add(f"- **状態**＝{t['状態']}")
            add("")

        # 順番の意図
        it = (intent or {}).get(st["鍵"])
        if it:
            add(f"### {st['鍵']} の順番にしている意図")
            add("")
            add(f"**（1）まとまりの分け方**＝{it['まとまりの分け方']}")
            add("")
            add("**（2）前のものが無いと次ができない関係**")
            add("")
            add("| # | 何が要るか |")
            add("|---|---|")
            for r in it["依存"]:
                add(f"| {r['番号']} | {_esc(r['何が要るか'])} |")
            add("")
            add(f"**（3）承認で止まる番号**＝{it['承認で止まる番号']}")
            add("")

    # 見出しだけの段
    rest = d["見出しだけの段"]
    add(f"## {rest['見出し']}")
    add("")
    for t in rest["一覧"]:
        add(f"- {t}")
    add("")

    return "\n".join(L).rstrip() + "\n"


def build_premise(d: dict) -> str:
    """json から「§0 読む前に知っておくこと」を組み立てる（engine_tuner_milestones2.md の冒頭）。

    まこさん指示（2026-08-29・逐語）＝「そういうことも、前提情報としてしっかり書いておいて。
    私はすべてを記憶できないし、仕組みも理解してない」。
    ★件数は機械が数える（手で書くと古くなる）。
    """
    L: list[str] = []
    add = L.append
    p = d["_読む前に知っておくこと"]
    laws = d["法則"]
    scenes = d["場面"]

    # 「機械が読む判定」を持つ法則の件数は、この正本そのものから機械で数える（M2-B0・2026-08-30）。
    #   ★それより前は composition_rules_src.json の枠を数えていた＝scene_rules ごと
    #     regime_laws.json へ移したので、数える相手も移した。
    with_j = [x for x in laws if isinstance(x, dict) and "機械が読む判定" in x]
    total = len(with_j)

    add("# §0 読む前に知っておくこと（★この節は機械が作ります・手で書き換えない）")
    add("")
    add("> **この節は、M2 の文書を読むための地図です。**ここを読めば、下のフローとやることリストの言葉が分かります。")
    add("")

    # 1
    one = p["1_法則と決まりは別のもの"]
    add("## 0-1 「相場の法則」と「読み込ませる法則」は、1つになりました（M2-B0・2026-08-30）")
    add("")
    add(f"**{one['説明']}**")
    add("")
    add("| | 相場の法則 | 読み込ませる法則 |")
    add("|---|---|---|")
    for r in one["表"]:
        add(f"| **{_esc(r['項目'])}** | {_esc(r['法則'])} | {_esc(r['決まり'])} |")
    add("")
    add(f"**いまの件数（機械が数えました）**＝相場の法則 **{len(laws)}件** ／ "
        f"うち「機械が読む判定」を持つもの **{total}件**")
    add("")
    _, _cov = coverage(d)
    if _cov:
        add("**判定を揃えた場面の数え（M2-B-2b・機械が数えました）**")
        add("")
        for ln in _cov:
            add(f"- {ln}")
        add("")

    # 相場の法則の場面ごとの件数
    add("**相場の法則の場面ごとの件数**")
    add("")
    add("| 場面 | 件数 | 番号 |")
    add("|---|---|---|")
    for s in scenes:
        rows = [x for x in laws if x["場面"] == s["鍵"]]
        nums = "・".join(x["番号"] for x in rows) if rows else "—"
        add(f"| {s['見出し']} | {len(rows)} | {nums} |")
    add("")

    # 2
    two = p["2_決まりの記号の意味"]
    add("## 0-2 機械が読む判定の記号（旧・読み込ませる法則）")
    add("")
    add(f"**{two['説明']}**")
    add("")
    add("| 記号 | 件数 | 何の判定か | どの段で扱うか |")
    add("|---|---|---|---|")
    for r in two["記号"]:
        add(f"| **{_esc(r['記号'])}** | {total} | {_esc(r['何の決まりか'])} | {_esc(r.get('どの段で扱うか', '?'))} |")
    add(f"| **合計** | **{total}** | | |")
    add("")
    if two.get("★段の分け方"):
        add(f"**★段の分け方**＝{_esc(two['★段の分け方'])}")
        add("")
    if two.get("★消した記号（2026-08-29）"):
        add(f"**★消した記号（2026-08-29）**＝{_esc(two['★消した記号（2026-08-29）'])}")
        add("")

    # 2b 「機械が読む判定」を持つ法則を1件ずつ出す（★2026-08-30・M2-B0＝正本が regime_laws.json になった）
    add(f"## 0-2b 機械が読む判定を持つ法則{total}件の全部（1件ずつ・機械が実物から書き出します）")
    add("")
    add("> **★この表の読み方（3つ・2026-08-30 の M2-B0 で直した後の実物）**")
    add("> ")
    add(f"> - **engine_tuner は、この{total}件を regime_laws.json から読み込んで審査します**"
        "（読み込み＝`engine_tuner_exec.load_regime_laws` → 審査＝G7 `_check_scene_rules`）。")
    add("> - **法則を1件 書き替えると、審査がそのとおり変わります。**読めない・知らない型・知らない形・知らない場面名・"
        "知らない系統名・知らない側・知らない性質は止まります（fail-closed）。")
    add("> - **「機械が読む判定」を持たない法則は、審査に使いません。**「判定を揃えた場面」（いま＝レンジ）の法則は、"
        "判定か「判定の置き場」（例＝R9＝regime_r9_diag.py）のどちらかを必ず持ちます（無ければ読み込みが止まる）。")
    add("")
    add("| # | 番号 | 相場の法則（一文） | 審査に使っているか | 掛かる場面 |")
    add("|---|---|---|---|---|")

    # engine の本体を読んで、読み込み口が配線されているかを機械で確かめる
    body = ""
    for nm in ("engine_tuner_gen.py", "engine_tuner_exec.py"):
        f = RATCHET.parent.parent / "scripts/priority_rebuild" / nm
        if f.exists():
            body += f.read_text(encoding="utf-8", errors="ignore")
    wired = "load_regime_laws" in body
    for i, x in enumerate(with_j, 1):
        j = x["機械が読む判定"]
        mark = "**使っている**（load_regime_laws が読む）" if wired else "**★配線が見つからない**"
        add(f"| {i} | **{_esc(str(x['番号']))}** | {_esc(str(x['一文']))} | {mark} "
            f"| {_esc('・'.join(j.get('掛かる場面', [])))} |")
    add("")
    add(f"**内訳（機械が数えました）**＝審査に使う **{total}件** ／ "
        f"持たない **{len(laws) - total}件**（合計 {len(laws)}件）")
    add("")
    add("**★判定の正本はこのファイル（regime_laws.json）です。**コードに直書きの判定は 2026-08-30（M2-B0）に消しました。")
    add("")

    # 3
    three = p["3_K-とは何か"]
    add("## 0-3 「K-」とは何か")
    add("")
    add(f"**{three['説明']}**")
    add("")
    add(f"**★「K」という文字の意味**＝{three['★Kという文字の意味']}")
    add("")
    add("| 番号 | 読み込ませる法則 | 掛かる場面 | 元になった相場の法則 |")
    add("|---|---|---|---|")
    for r in three["一覧"]:
        add(f"| **{r['番号']}** | {_esc(r['決まり'])} | {_esc(r['掛かる場面'])} | {_esc(r['元の法則'])} |")
    add("")

    # 4
    four = p["4_いまの engine_tuner は何を守っているか"]
    add("## 0-4 いまの engine_tuner は、何を守っているか")
    add("")
    add(f"**{four['説明']}**")
    add("")
    add(f"**★足りていないこと**＝{four['★足りていないこと']}")
    add("")
    add(f"**★M2-B は、この差を埋める工程です**＝{four['★M2-B は、この差を埋める工程']}")
    add("")

    # 6（2026-08-29 新設・まこさん指示「ここまでの状況を整理して書き直して」）
    six = p.get("6_engine_tuner のどこで使われているか")
    if six:
        add("## 0-6 engine_tuner の、どこで使われているか（★2026-08-30 の M2-B0 の後の実物）")
        add("")
        add(f"**{_esc(six['説明'])}**")
        add("")
        add("| 場所 | ファイルと行 | 何をしているか |")
        add("|---|---|---|")
        for r in six["使われている場所"]:
            add(f"| **{_esc(r['場所'])}** | `{_esc(r['ファイル'])}` | {_esc(r['何をしているか'])} |")
        add("")
        sym = six["★記号の対応（まこさん決定 2026-08-29）"]
        add("### ★記号の対応（まこさん決定 2026-08-29）")
        add("")
        add(f"**なぜ変えるか**＝{_esc(sym['なぜ変えるか'])}")
        add("")
        add("| いまの記号 | これからの番号 | 元になった相場の法則 | 掛かる場面 |")
        add("|---|---|---|---|")
        for r in sym["表"]:
            add(f"| {_esc(r['いまの記号'])} | **{_esc(r['これからの番号'])}** | {_esc(r['元になった相場の法則'])} "
                f"| {_esc(r['掛かる場面'])} |")
        add("")
        add(f"**複数から来ているものの決め方**＝{_esc(sym['複数から来ているものの決め方'])}")
        add("")

    # 7（2026-08-29 新設・まこさん承認「この形に変えてよい」）
    seven = p.get("7_これからの形（まこさん承認 2026-08-29）")
    if seven:
        add("## 0-7 ★いまの形（まこさん承認 2026-08-29・2026-08-30 に実装済み）")
        add("")
        add(f"**{_esc(seven['説明'])}**")
        add("")
        add(f"**まこさんの逐語**＝「{_esc(seven['まこさんの逐語'])}」")
        add("")
        add("| | いままで | これから |")
        add("|---|---|---|")
        for r in seven["表"]:
            add(f"| **{_esc(r['項目'])}** | {_esc(r['いままで'])} | {_esc(r['これから'])} |")
        add("")
        add("**この形にすると良いこと**")
        add("")
        for x in seven["この形にすると良いこと"]:
            add(f"- {_esc(x)}")
        add("")
        add(f"**★いつ変わるか**＝{_esc(seven['★いつ変わるか'])}")
        add("")
        if seven.get("★何を足せば読み込めるか"):
            add(f"**★何を足せば読み込めるか**＝{_esc(seven['★何を足せば読み込めるか'])}")
            add("")

    # 8（まこさん指示 2026-08-30「以下をmelestones2に追記しておいて」）
    eight = p.get("8_共通の相場の法則 C1〜C10（まこさん指示 2026-08-30）")
    if eight:
        add("## 0-8 共通の相場の法則 C1〜C10 の中身")
        add("")
        add(f"**{_esc(eight['説明'])}**")
        add("")
        add("| 記号 | 中身 | どの段で使うか |")
        add("|---|---|---|")
        for r in eight["一覧"]:
            add(f"| **{_esc(r['記号'])}** | {_esc(r['中身'])} | {_esc(r['どの段で使うか'])} |")
        add("")

    # 5
    add("## 0-5 よく出る言葉")
    add("")
    add("| 言葉 | 意味 |")
    add("|---|---|")
    for r in p["5_よく出る言葉"]:
        add(f"| **{_esc(r['言葉'])}** | {_esc(r['意味'])} |")
    add("")

    return "\n".join(L).rstrip() + "\n"


def build_laws(d: dict) -> str:
    """json から §11（場面ごとの相場の法則）の本文を組み立てる。

    1件を2段に分ける。
      上＝一覧の表（相場の法則を1文で・6列）
      下＝1件ずつの説明（詳しい中身・出どころ・注意）
    """
    L: list[str] = []
    add = L.append
    laws = d["法則"]
    scenes = d["場面"]
    pre = d["_前置き"]

    add("# §11 場面ごとの相場の法則の一覧（★この節は機械が作ります・手で書き換えない）")
    add("")
    add(f"**何のための一覧か**＝{pre['何のための一覧か']}")
    add("")
    add(f"**使い方**＝{pre['使い方']}")
    add("")
    add(f"**元データ**＝`.claude/ratchet/regime_laws.json` ／ **作り方**＝`{d['_作り方']}`")
    add("")
    add(f"**整理した日**＝{d['_整理した日']}｜**整理の形**＝{d['_整理の形']}")
    add("")

    # 場面ごとの件数
    add("## 11-0 何件あるか（機械が数えます）")
    add("")
    add("| 場面 | 件数 | 相場の法則の番号 |")
    add("|---|---|---|")
    for s in scenes:
        rows = [x for x in laws if x["場面"] == s["鍵"]]
        nums = "・".join(x["番号"] for x in rows) if rows else "（まだ写していません）"
        add(f"| {s['見出し']} | {len(rows)} | {nums} |")
    add(f"| **合計** | **{len(laws)}** | |")
    add("")
    add("**出どころの印（5つ）**")
    add("")
    add("| 印 | 意味 |")
    add("|---|---|")
    for r in pre["出どころの印"]:
        add(f"| 【{r['印']}】 | {_esc(r['意味'])} |")
    add("")
    add("**★この一覧に名前が出ていない指標が「レジーム判定に向かない」という意味ではありません**")
    add("")
    for i, t in enumerate(pre["この一覧に名前が出ていない指標について"], 1):
        add(f"{i}. {t}")
    add("")
    add("**調べ方と打ち切り**")
    add("")
    for t in pre["調べ方と打ち切り"]:
        add(f"- {t}")
    add("")

    # 場面ごと
    for i, s in enumerate(scenes, 1):
        rows = [x for x in laws if x["場面"] == s["鍵"]]
        if not rows:
            continue
        note = f"（{s['注記']}）" if s["注記"] else ""
        add(f"## 11-{i} {s['見出し']}{note}｜{len(rows)}件")
        add("")
        has_step = any(r.get("使う段") for r in rows)
        if has_step:
            add("| # | 相場の法則（1文） | **どの段で使うか** | 級 |")
            add("|---|---|---|---|")
            for r in rows:
                add(f"| **{r['番号']}** | {_esc(r['一文'])} | **{_esc(r.get('使う段', '—'))}** | 【{r['級']}】 |")
        else:
            add("| # | 相場の法則（1文） | 相場の何を見ているか | 級 | engine_tuner で書けるか |")
            add("|---|---|---|---|---|")
            for r in rows:
                add(f"| **{r['番号']}** | {_esc(r['一文'])} | {_esc(r['見ているもの'])} "
                    f"| 【{r['級']}】 | {_esc(_kakeru(r))} |")
        add("")
        add(f"### 11-{i} の1件ずつの説明")
        add("")
        for r in rows:
            add(f"**{r['番号']}｜{r['一文']}**")
            add("")
            add(f"- **中身**＝{r['説明']}")
            if r.get("使う段"):
                add(f"- **どの段で使うか**＝**{r['使う段']}**（{r.get('使う段の理由', '')}）")
            for t in r.get("注意") or []:
                add(f"- {t}")
            add(f"- **出どころ**＝【{r['級']}】{r['出どころ']}")
            add("")

    # 穴
    holes = d.get("穴") or []
    add(f"## 11-{len(scenes) + 1} 未収載・穴（{len(holes)}件・正直に書く）")
    add("")
    add("| # | 穴 | 中身 |")
    add("|---|---|---|")
    for r in holes:
        add(f"| {r['番号']} | **{_esc(r['穴'])}** | {_esc(r['中身'])} |")
    add("")

    # 出どころ
    srcs = d.get("出どころ_2026-08-20に新しく開いたもの") or []
    add(f"## 11-{len(scenes) + 2} 出どころ（2026-08-20 に新しく開いたもの・{len(srcs)}件）")
    add("")
    for r in srcs:
        add(f"- 【{r['級']}】[{_esc(r['名前'])}]({r['url']})")
    add("")

    return "\n".join(L).rstrip() + "\n"


def build_body(d: dict) -> str:
    """json から §12 の本文を組み立てる。"""
    L: list[str] = []
    add = L.append

    add("# §12 2026-08-29 に調べた結果（★この節は機械が作ります・手で書き換えない）")
    add("")
    add(f"**調べた日**＝{d['_調べた日']}")
    add("")
    add(f"**調べた理由**＝{d['_調べた理由']}")
    add("")
    add("**調べ方の読み込ませる法則（3つ）**")
    for i, r in enumerate(d["_決まり"], 1):
        add(f"{i}. {r}")
    add("")
    add(f"**元データ**＝`.claude/ratchet/regime_kb_findings.json` ／ **作り方**＝`{d['_作り方']}`")
    add("")
    add("---")
    add("")

    # ── A ─────────────────────────────────────────────
    a = d["A_外を調べた結果"]
    add("## 12-1 外は指標をどう整理しているか（問い4つ）")
    add("")
    add("**調べた問い**")
    for i, q in enumerate(a["_問い"], 1):
        add(f"{i}. {q}")
    add("")
    add("### 答え")
    add("")
    add("| 問い | 答え |")
    add("|---|---|")
    for r in a["答え"]:
        add(f"| {_esc(r['問い'])} | {_esc(r['答え'])} |")
    add("")
    add(f"### 一次ページを開いて取った逐語（{len(a['開けた'])}件）")
    add("")
    add("| # | 出どころ | 級 | 答える問い | 逐語（英語のまま） | うちにとっての意味 |")
    add("|---|---|---|---|---|---|")
    for i, r in enumerate(a["開けた"], 1):
        add(f"| {i} | [{_esc(r['出どころ'])}]({r['url']}) | 【{r['級']}】 | {r['答える問い']} "
            f"| {_esc(r['逐語'])} | {_esc(r['うちにとっての意味'])} |")
    add("")
    add(f"### 開けなかったもの（{len(a['開けなかった'])}件・正直に残す）")
    add("")
    add("| # | 出どころ | 理由 |")
    add("|---|---|---|")
    for i, r in enumerate(a["開けなかった"], 1):
        add(f"| {i} | [{_esc(r['出どころ'])}]({r['url']}) | {_esc(r['理由'])} |")
    add("")

    # ── B ─────────────────────────────────────────────
    b = d["B_組み合わせの根拠"]
    add("## 12-2 複数の判定を組み合わせると精度が上がるのか（問い3つ）")
    add("")
    add("**調べた問い**")
    for i, q in enumerate(b["_問い"], 1):
        add(f"{i}. {q}")
    add("")
    add("### 答え")
    add("")
    add("| 問い | 答え |")
    add("|---|---|")
    for r in b["答え"]:
        add(f"| {_esc(r['問い'])} | {_esc(r['答え'])} |")
    add("")
    add(f"### 一次ページを開いて取った逐語（{len(b['開けた'])}件）")
    add("")
    add("| # | 出どころ | 級 | 答える問い | 逐語（英語のまま） | うちにとっての意味 |")
    add("|---|---|---|---|---|---|")
    for i, r in enumerate(b["開けた"], 1):
        add(f"| {i} | [{_esc(r['出どころ'])}]({r['url']}) | 【{r['級']}】 | {r['答える問い']} "
            f"| {_esc(r['逐語'])} | {_esc(r['うちにとっての意味'])} |")
    add("")
    add(f"### 開けなかったもの（{len(b['開けなかった'])}件）")
    add("")
    add("| # | 出どころ | 理由 |")
    add("|---|---|---|")
    for i, r in enumerate(b["開けなかった"], 1):
        add(f"| {i} | [{_esc(r['出どころ'])}]({r['url']}) | {_esc(r['理由'])} |")
    add("")

    # ── C ─────────────────────────────────────────────
    c = d["C_社内の正本で確かめたこと"]
    add(f"## 12-3 社内の正本に既に在った答え（{len(c)}件）")
    add("")
    add("**★2026-08-29 の調べで分かったこと＝分類の切り方の答えは、外を調べる前から社内に在った。**")
    add("")
    add("| # | 出どころ | 級 | 逐語 | うちにとっての意味 |")
    add("|---|---|---|---|---|")
    for i, r in enumerate(c, 1):
        add(f"| {i} | {_esc(r['出どころ'])} | 【{r['級']}】 | {_esc(r['逐語'])} | {_esc(r['うちにとっての意味'])} |")
    add("")

    # ── D ─────────────────────────────────────────────
    dd = d["D_法則40件を10の型に畳んだ結果"]
    cnt = dd["件数"]
    add("## 12-4 場面ごとの相場の法則40件を、共通の型に畳めるか")
    add("")
    add(f"**{dd['_何をしたか']}**")
    add("")
    add(f"**結果＝{cnt['場面ごとの法則']}件のうち {cnt['畳めた']}件が10の型に畳めた。"
        f"畳めなかったのは {cnt['畳めなかった']}件。**")
    add("")
    add(f"{dd['_根拠']}")
    add("")
    add("| 型 | 骨格（何を測るか） | 畳める相場の法則 | 場面ごとに変わるもの |")
    add("|---|---|---|---|")
    for r in dd["型"]:
        add(f"| {r['番号']} | {_esc(r['骨格'])} | {_esc(r['畳める法則'])} | {_esc(r['場面ごとに変わるもの'])} |")
    add("")
    add(f"### 畳めなかった{len(dd['畳めなかった'])}件（理由つき）")
    add("")
    add("| 相場の法則 | 中身 | 畳めない理由 |")
    add("|---|---|---|")
    for r in dd["畳めなかった"]:
        add(f"| {r['法則']} | {_esc(r['中身'])} | {_esc(r['理由'])} |")
    add("")

    # ── E ─────────────────────────────────────────────
    e = d["E_数の実測"]
    add(f"## 12-5 数の実測（{len(e)}件・全部 プログラムで数えた）")
    add("")
    add("| # | 何を数えたか | 結果 | 出どころ |")
    add("|---|---|---|---|")
    for i, r in enumerate(e, 1):
        add(f"| {i} | {_esc(r['何を数えたか'])} | {_esc(r['結果'])} | {_esc(r['出どころ'])} |")
    add("")

    # ── G ─────────────────────────────────────────────
    g = d["G_レンジの正解の作り方"]
    add("## 12-6 「実際にレンジだったか」の正解の作り方（外の実例）")
    add("")
    add(f"**調べた日**＝{g['_調べた日']}")
    add("")
    add(f"**調べた理由**＝{g['_調べた理由']}")
    add("")
    add("**調べた問い**")
    for i, q in enumerate(g["_問い"], 1):
        add(f"{i}. {q}")
    add("")
    add(f"### 一次ページを開いて取った逐語（{len(g['開けた'])}件）")
    add("")
    add("| # | まとまり | 読み込ませる法則（何をしているか） | 級 | 逐語（英語のまま） | 開けた場所 |")
    add("|---|---|---|---|---|---|")
    for i, r in enumerate(g["開けた"], 1):
        add(f"| {i} | {_esc(r['まとまり'])} | [{_esc(r['決まり'])}]({r['url']}) | 【{r['級']}】 "
            f"| {_esc(r['逐語'])} | {_esc(r['開けた場所'])} |")
    add("")
    add(f"### 開けなかったもの（{len(g['開けなかった'])}件）")
    add("")
    add("| # | 出どころ | 理由 |")
    add("|---|---|---|")
    for i, r in enumerate(g["開けなかった"], 1):
        add(f"| {i} | [{_esc(r['出どころ'])}]({r['url']}) | {_esc(r['理由'])} |")
    add("")
    y = g["検索の要約が本文と違っていた件"]
    add("### ★検索の要約が、本文と違っていた1件（恒久の決まり43番の実例）")
    add("")
    add(f"**検索の要約に出た文**＝{y['検索の要約に出た文']}")
    add("")
    add(f"**本文を開いた結果**＝{y['本文を開いた結果']}")
    add("")
    add(f"{y['意味']}")
    add("")
    add("### いまの印と、外の作り方の違い")
    add("")
    add("| # | いまの印 | 外 | 何が変わるか |")
    add("|---|---|---|---|")
    for r in g["いまの印と外の違い"]:
        add(f"| {r['番号']} | {_esc(r['いまの印'])} | {_esc(r['外'])} | {_esc(r['何が変わるか'])} |")
    add("")
    u = g["うちが決めたこと"]
    add("### うちが決めたこと")
    add("")
    add(f"**まこさん決定**＝{u['まこさん決定']}")
    add("")
    add(f"**中身**＝{u['中身']}")
    add("")
    add(f"**判断の材料**＝{u['判断の材料']}")
    add("")
    add(f"{u['★CC の見立てが外れたこと']}")
    add("")

    # ── F ─────────────────────────────────────────────
    f = d["F_穴"]
    add(f"## 12-7 この調べで見つかった穴（{len(f)}件・正直に書く）")
    add("")
    for i, r in enumerate(f, 1):
        add(f"### 穴{i}｜{r['穴']}")
        add("")
        add(f"**中身**＝{r['中身']}")
        add("")
        add(f"**どうするか**＝{r['どうするか']}")
        add("")

    return "\n".join(L).rstrip() + "\n"


BUILDER = {"flow": build_flow, "todo": build_todo, "laws": build_laws, "findings": build_body, "premise": build_premise}
SEC = {"flow": "§2（フロー）", "todo": "§3（やることリスト）", "laws": "§11", "findings": "§12", "premise": "§0（読む前に知っておくこと）"}
# 書き込み先のファイル（premise だけ やることリストの文書へ書く）
DEST = {
    "laws": KB,
    "findings": KB,
    "premise": RATCHET / "engine_tuner_milestones2.md",
    "todo": RATCHET / "engine_tuner_milestones2.md",
    "flow": RATCHET / "engine_tuner_milestones2.md",
}


def _kinds(arg: str) -> list[str]:
    return ["premise", "flow", "todo", "laws", "findings"] if arg in ("all", None) else [arg]


def write_one(kind: str, dry: bool = False) -> int:
    d = json.loads(SRC[kind].read_text(encoding="utf-8"))
    body = BUILDER[kind](d)
    dest = DEST[kind]
    kb = dest.read_text(encoding="utf-8")
    end_mark = _end(kind)
    block = _begin(kind, _h(body)) + "\n" + body + end_mark + "\n"

    m = _begin_re(kind).search(kb)
    if m and end_mark in kb:
        start = m.start()
        end = kb.index(end_mark) + len(end_mark) + 1
        new = kb[:start] + block + kb[end:]
    else:
        new = kb.rstrip() + "\n\n---\n\n" + block

    if dry:
        print(body)
        return 0
    dest.write_text(new, encoding="utf-8")
    print(f"✅ --write 完了: {SEC[kind]} を {dest.name} に書きました"
          f"（本文 {len(body.splitlines())} 行・hash={_h(body)}）")
    return 0


def verify_one(kind: str) -> int:
    kb = DEST[kind].read_text(encoding="utf-8")
    end_mark = _end(kind)
    m = _begin_re(kind).search(kb)
    if not m or end_mark not in kb:
        print(f"❌ --verify: KB に {TAG[kind]} のマーカーがありません（--write を先に走らせる）")
        return 1
    body = kb[m.end():kb.index(end_mark)].lstrip("\n")
    now, want = _h(body), m.group(1)
    if now != want:
        print(f"❌ --verify: {SEC[kind]} が手で書き換えられています（印={want} ／ いま={now}）")
        print(f"   → 直すのは {SRC[kind].name}。直したら --write を走らせる。")
        return 1
    d = json.loads(SRC[kind].read_text(encoding="utf-8"))
    if _h(BUILDER[kind](d)) != want:
        print(f"❌ --verify: {SRC[kind].name} が変わったのに --write を走らせていません")
        return 1
    print(f"✅ --verify: {SEC[kind]} は機械が書いたままです（hash={want}）")
    return 0


def write(target: str = "all", dry: bool = False) -> int:
    rc = 0
    for k in _kinds(target):
        rc |= write_one(k, dry=dry)
    return rc


def verify(target: str = "all") -> int:
    rc = 0
    for k in _kinds(target):
        rc |= verify_one(k)
    if "laws" in _kinds(target):                       # ★M2-B-2b＝判定を揃えた場面の数え（10行すべてに判定か置き場）
        d = json.loads(SRC["laws"].read_text(encoding="utf-8"))
        crc, lines = coverage(d)
        for ln in lines:
            print(ln)
        rc |= crc
    return rc


def selftest() -> int:
    """わざと壊して ❌ が出るかを試す。KB は元に戻す。"""
    ok = 0
    total = 0
    orig = {p: p.read_text(encoding="utf-8") for p in set(DEST.values())}
    try:
        for kind in ("premise", "flow", "todo", "laws", "findings"):
            dest = DEST[kind]
            total += 1
            if verify_one(kind) == 0:
                ok += 1
                print(f"   T{total} {SEC[kind]} いまの状態は ✅ → pass")
            else:
                print(f"   T{total} {SEC[kind]} いまの状態が ❌ → fail")

            total += 1
            base = orig[dest]
            m = _begin_re(kind).search(base)
            broken = base[:m.end()] + "\nわざと足した1行\n" + base[m.end():]
            dest.write_text(broken, encoding="utf-8")
            if verify_one(kind) == 1:
                ok += 1
                print(f"   T{total} {SEC[kind]} 1行 足すと ❌ → pass")
            else:
                print(f"   T{total} {SEC[kind]} 1行 足しても ✅ のまま → fail")
            dest.write_text(base, encoding="utf-8")
    finally:
        for p, t in orig.items():
            p.write_text(t, encoding="utf-8")
    print(f"\n{'✅' if ok == total else '❌'} selftest {ok}/{total} pass")
    return 0 if ok == total else 1


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--write", nargs="?", const="all", choices=["all", "premise", "flow", "todo", "laws", "findings"])
    p.add_argument("--verify", nargs="?", const="all", choices=["all", "premise", "flow", "todo", "laws", "findings"])
    p.add_argument("--dry-run", nargs="?", const="all", choices=["all", "premise", "flow", "todo", "laws", "findings"])
    p.add_argument("--selftest", action="store_true")
    a = p.parse_args()
    if a.selftest:
        return selftest()
    if a.write:
        return write(a.write)
    if a.dry_run:
        return write(a.dry_run, dry=True)
    if a.verify:
        return verify(a.verify)
    p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
