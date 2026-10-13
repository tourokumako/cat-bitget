#!/usr/bin/env python3
"""gen_core_requirements.py — 固定で載せる文（要件定義・工事の流れ・設計書の監査が要る物）の正本を、逐語のファイルから作る。

まこさん指示（2026-10-12・逐語のファイル＝verbatim/requirements-core-20261012/ の ok_requirements_core_20261012・ok_work_flow_20261012・
ok_design_audit_scope_20261012・ok_fix_plan_abc_20261012）＝要件定義と工事の流れを、設計書・next_step・監査の依頼書の上部に、
固定で毎回 載せる。絶対に消さない。

なぜ要るか
  2026-09-29・30 に CC が、依頼書を作るプログラムを直して、設計書の監査から「設計の中身が正しいか」を外した。目標と要件から
  考えずに直したためで、2026-10-12 まで、設計の中身を実装の前に CC 以外が確かめた工事が無かった（session_worklog_20261012.md §7〜§9）。
  目標・要件・工事の流れを、文書を作るたびに必ず目に入る所へ、プログラムで載せる。

何をするか
  1. まこさんが OK した文を、逐語のファイル（やり取りの記録からプログラムが写した物）から切り出す。CC は文を書かない。
  2. 正本（.claude/rules/core_requirements.md＝毎セッション 自動で読み込まれる置き場）に書く。
  3. ほかのプログラム（設計書・依頼書・next_step を作る物）は、embed_lines() で正本を読んで写す。
     正本が無い・逐語のファイルから作り直した物と1文字でも違うときは、止まる（fail-closed）。

使い方
  python3 .claude/tools/gen_core_requirements.py --write    # 正本を逐語のファイルから作り直す
  python3 .claude/tools/gen_core_requirements.py --verify   # 正本が、逐語のファイルから作り直した物と同じかを確かめる（違えば終了コード 1）
  python3 .claude/tools/gen_core_requirements.py --print    # 作り直した物を画面に出す（書かない）

限り（正直に）
  ①逐語のファイルそのものを書き替えられたら、このプログラムには分からない（gen_verbatim.py --verify が、記録の発言と照らす）。
  ②見出しの3行と、頭の説明の4行は、このプログラムの中の決まった文（まこさんの逐語ではない）。
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
WORK = "requirements-core-20261012"
SRC = ROOT / ".claude" / "state" / "verbatim" / WORK
OUT = ROOT / ".claude" / "rules" / "core_requirements.md"
HEAD = "<!-- CORE_REQUIREMENTS gen_core_requirements.py が逐語のファイルから作った＝手で書き換えない -->"

# 切り出す所＝（逐語のファイル, 始まりの行の頭, 終わりの行の頭〔この行は入れない〕, 上に付ける見出し〔None＝付けない〕）
PARTS = (
    ("okd_requirements_core_20261012.txt", "# 要件定義（CAT プロジェクトと engine_tuner の目的と要件）", "---", None),
    ("okd_work_flow_20261012.txt", "## 流れ（", "## いま起きていること",
     "# 工事の流れ（やることリストの1件を進める順）"),
    ("okd_design_audit_scope_20261012.txt", "| 直す物 | 設計書の監査 |", "2行目は、私の考えです",
     "# 設計書の監査が要る物・要らない物"),
)
DECISION = "ok_design_audit_scope_20261012.txt"          # 上の3つ目の表を決定にした、まこさんの発言


class CoreError(SystemExit):
    pass


def _read(name: str) -> list:
    p = SRC / name
    if not p.is_file():
        raise CoreError(f"[gen_core_requirements] 逐語のファイルが無い（fail-closed）: {p}")
    return p.read_text(encoding="utf-8").splitlines()


def _cut(name: str, start: str, end: str) -> list:
    """逐語のファイルから、start で始まる行から、その後の end で始まる行の手前までを返す。前後の空の行は落とす。"""
    lines = _read(name)
    i0 = next((i for i, ln in enumerate(lines) if ln.startswith(start)), None)
    if i0 is None:
        raise CoreError(f"[gen_core_requirements] {name} に、始まりの行「{start}」が無い（fail-closed）")
    i1 = next((i for i in range(i0 + 1, len(lines)) if lines[i].startswith(end)), None)
    if i1 is None:
        raise CoreError(f"[gen_core_requirements] {name} に、終わりの行「{end}」が無い（fail-closed）")
    out = lines[i0:i1]
    while out and not out[-1].strip():
        out.pop()
    return out


def build_lines() -> list:
    """正本の全部の行を、逐語のファイルから作る。"""
    names = "・".join(p[0] for p in PARTS)
    out = [HEAD,
           "# 要件定義と工事の流れ（固定・毎回 読む・消さない）",
           "",
           "★この文書は、まこさんが OK した文を、プログラムが逐語のファイルから写した物です。"
           "見出しの3行と、この説明の4行だけが、プログラムの中の決まった文です。",
           f"★出どころ＝`.claude/state/verbatim/{WORK}/` の {names}"
           f"（記録の発言との照らし＝`python3 .claude/tools/gen_verbatim.py --verify {WORK}/<名前>`）。",
           "★作り直し＝`python3 .claude/tools/gen_core_requirements.py --write`。検出＝`--verify`。",
           "★設計書・監査の依頼書・next_step の上部には、それぞれを作るプログラムが、この文書を写して載せます。"
           "この文書が無い・逐語のファイルと違うときは、どのプログラムも文書を作らずに止まります。",
           ""]
    for name, start, end, title in PARTS:
        if title:
            out += [title, ""]
        out += _cut(name, start, end)
        out.append("")
    dec = [ln.strip() for ln in _read(DECISION) if ln.strip()]
    if not dec:
        raise CoreError(f"[gen_core_requirements] {DECISION} が空（fail-closed）")
    out.append(f"まこさんの決定（逐語 2026-10-12）＝「{'／'.join(dec)}」")
    out.append("")
    return out


def build_text() -> str:
    return "\n".join(build_lines())


def problems() -> list:
    """正本が、逐語のファイルから作り直した物と同じかを見る。違いを文で返す（空なら同じ）。"""
    want = build_text()
    if not OUT.is_file():
        return [f"正本が無い: {OUT}（python3 .claude/tools/gen_core_requirements.py --write で作る）"]
    got = OUT.read_text(encoding="utf-8")
    if got != want:
        a, b = got.splitlines(), want.splitlines()
        n = next((i for i, (x, y) in enumerate(zip(a, b), 1) if x != y), min(len(a), len(b)) + 1)
        return [f"正本が、逐語のファイルから作り直した物と違う（{n} 行目から・正本 {len(a)} 行／作り直し {len(b)} 行）"
                "＝手で書き換えられた疑い。--write で作り直す"]
    return []


def embed_lines() -> list:
    """ほかの文書の中に載せる形の行を返す。正本が無い・違うときは止まる（fail-closed）。

    見出しの行（# で始まる行）は、載せる先の文書の見出しの並びを壊さないように、太字の行に変える。文は変えない。
    """
    ng = problems()
    if ng:
        raise CoreError("[gen_core_requirements] 固定で載せる文の正本が使えない（fail-closed）:\n  " + "\n  ".join(ng))
    out = []
    in_code = False
    for ln in OUT.read_text(encoding="utf-8").splitlines():
        if ln == HEAD:
            continue
        if ln.startswith("```"):
            in_code = not in_code
        if not in_code and ln.startswith("#"):
            body = ln.lstrip("#").strip()
            out.append(f"**■ {body}**")
        else:
            out.append(ln)
    while out and not out[-1].strip():
        out.pop()
    return out


# 要件定義のうち、見出し1つを1行として照らす節の番号（3 は機能要件の6行・8 は作ってはいけないものの2行に分ける。
# 5＝言葉の定義・9＝CC の言葉・10＝いまの実物との違い、は照らす行にしない）
ONE_ROW_OLD = ("1", "2", "4", "6", "7")
# ★2026-10-13（工事 design-doc-gen-form-20261013）＝新しい形の設計書の索引は、5・9・10 も行にする（別セッションの監査 2026-10-12 の M-12）。
#   いままでの形の設計書（案の【0-R】と照らす）は、ONE_ROW_OLD のまま＝承認済みの設計書は変わらない。
ONE_ROW = ("1", "2", "4", "5", "6", "7", "9", "10")


def requirement_items(full: bool = False) -> list:
    """設計書が1行ずつ照らす要件（番号, 名前）を、正本から並べる（2026-10-12・直し方の案 A-4）。

    正本の「# 要件定義（…）」の部分の見出し（## N. 名前）から作る。要件が増えたら、行も増える。
    正本が無い・逐語のファイルと違うときは止まる（fail-closed）。
    """
    ng = problems()
    if ng:
        raise CoreError("[gen_core_requirements] 固定で載せる文の正本が使えない（fail-closed）:\n  " + "\n  ".join(ng))
    lines = OUT.read_text(encoding="utf-8").splitlines()
    i0 = next((i for i, ln in enumerate(lines) if ln.startswith("# 要件定義（")), None)
    if i0 is None:
        raise CoreError("[gen_core_requirements] 正本に「# 要件定義（…）」の見出しが無い（fail-closed）")
    i1 = next((i for i in range(i0 + 1, len(lines)) if lines[i].startswith("# ")), len(lines))
    items, sec = [], None
    for ln in lines[i0 + 1:i1]:
        m = re.match(r"^## (\d+)\. (.+)$", ln)
        if m:
            sec = m.group(1)
            if sec in (ONE_ROW if full else ONE_ROW_OLD):
                items.append((sec, m.group(2).strip()))
            continue
        if sec == "3":
            m3 = re.match(r"^\| (\d+) \| (.+?)\s*$", ln)
            if m3:
                items.append((f"3-{m3.group(1)}", m3.group(2).replace("*", "").strip()))
        elif sec == "8":
            m8 = re.match(r"^(\d+)\. (.+)$", ln)
            if m8:
                items.append((f"8-{m8.group(1)}", m8.group(2).strip()))
    if len(items) < len(ONE_ROW if full else ONE_ROW_OLD):
        raise CoreError(f"[gen_core_requirements] 正本から照らす要件を読めない（{len(items)} 件・fail-closed）")
    return items


def main(argv: list) -> int:
    if "--items" in argv:
        for no, name in requirement_items():
            print(f"{no}\t{name}")
        return 0
    if "--print" in argv:
        print(build_text())
        return 0
    if "--write" in argv:
        text = build_text()
        OUT.write_text(text, encoding="utf-8")
        print(f"✅ --write: {OUT.relative_to(ROOT)}（{len(text.splitlines())} 行）")
        return 0
    if "--verify" in argv:
        ng = problems()
        for x in ng:
            print(f"❌ {x}")
        if not ng:
            print(f"✅ --verify: 正本は、逐語のファイルから作り直した物と同じ（{OUT.relative_to(ROOT)}）")
        return 1 if ng else 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
