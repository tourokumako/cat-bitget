#!/usr/bin/env python3
"""gen_core_requirements.py — 固定で載せる文（要件定義・工事の流れ・設計書の監査が要る物）の正本を、逐語のファイルから作る。

まこさん指示（2026-10-12・逐語のファイル＝verbatim/requirements-core-20261012/ の ok_requirements_core_20261012・ok_work_flow_20261012・
ok_design_audit_scope_20261012・ok_fix_plan_abc_20261012）＝要件定義と工事の流れを、設計書・next_step・監査の依頼書の上部に、
固定で毎回 載せる。絶対に消さない。

★2026-10-18（192回目・ToDo の52番・まこさん決定「同じデータから自動生成してるはずなので、元の文書の内容との齟齬がないなら元も要約してよい」）
  ＝正本を要約にした。要約は、CC が出し まこさんが「OK」した文（逐語のファイル okd_summary_20261018・OK＝ok_summary_20261018）。
  全文は core_requirements_full.md に残す。要約の中の まこさんの言葉（「」の行と、機能要件の6行）が、全文の逐語に
  1文字も違わずに在ることを --verify が照らす（齟齬が無いことを機械で確かめる）。
  なぜ要約か（まこさんの逐語の要点）＝「CATの要件に沿って目的を達成するための制作をするという視点を忘れるので、書いている。
  …インプットしやすいよう文字数を減らし、要約すべき」。実測＝固定の文を入れた後の監査5本で、要件定義を根拠に使ったのは
  問いが指した所だけ（CP75・CP77 は15〜16行、CP76・CP78 は2〜5行）。
  2段＝いつも載せる芯（1・2・3・7・8・10）と、売買のロジックに触る工事のときだけ足す部分（4・5・6・9）。

なぜ要るか
  2026-09-29・30 に CC が、依頼書を作るプログラムを直して、設計書の監査から「設計の中身が正しいか」を外した。目標と要件から
  考えずに直したためで、2026-10-12 まで、設計の中身を実装の前に CC 以外が確かめた工事が無かった（session_worklog_20261012.md §7〜§9）。
  目標・要件・工事の流れを、文書を作るたびに必ず目に入る所へ、プログラムで載せる。

何をするか
  1. まこさんが OK した文を、逐語のファイル（やり取りの記録からプログラムが写した物）から切り出す。CC は文を書かない。
  2. 正本（.claude/rules/core_requirements.md＝要約・毎セッション 自動で読み込まれる置き場）と、全文（core_requirements_full.md）に書く。
  3. ほかのプログラム（設計書・依頼書・next_step を作る物）は、embed_lines() で正本（要約）を読んで写す。
     正本が無い・逐語のファイルから作り直した物と1文字でも違う・要約の まこさんの言葉が全文に無いときは、止まる（fail-closed）。
  4. 設計書の監査の要件ごとの問い（R）は、requirement_items() が全文から組む（要約から組むと問いが減る）。

使い方
  python3 .claude/tools/gen_core_requirements.py --write       # 正本（要約）と全文の2本を、逐語のファイルから作り直す
  python3 .claude/tools/gen_core_requirements.py --verify      # 2本が作り直した物と同じか・要約の まこさんの言葉が全文に在るか（違えば終了コード 1）
  python3 .claude/tools/gen_core_requirements.py --print       # 要約を画面に出す（書かない）
  python3 .claude/tools/gen_core_requirements.py --print-full  # 全文を画面に出す（書かない）
  python3 .claude/tools/gen_core_requirements.py --items       # 設計書が1行ずつ照らす要件の一覧（全文から）

限り（正直に）
  ①逐語のファイルそのものを書き替えられたら、このプログラムには分からない（gen_verbatim.py --verify が、記録の発言と照らす）。
  ②見出しの行と、頭の説明の4行は、このプログラムの中の決まった文（まこさんの逐語ではない）。
  ③齟齬の照らしは、「」の中の文と機能要件の6行だけ。要約の地の文（CC が縮めた文）が全文の意味と合うかは、まこさんの目。
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
WORK = "requirements-core-20261012"
SRC = ROOT / ".claude" / "state" / "verbatim" / WORK
OUT = ROOT / ".claude" / "rules" / "core_requirements.md"              # 要約（正本・自動で読み込まれる）
OUT_FULL = ROOT / ".claude" / "rules" / "core_requirements_full.md"    # 全文（参照用・要件ごとの問い R の元）
HEAD = "<!-- CORE_REQUIREMENTS gen_core_requirements.py が逐語のファイルから作った＝手で書き換えない -->"
HEAD_FULL = "<!-- CORE_REQUIREMENTS_FULL gen_core_requirements.py が逐語のファイルから作った＝手で書き換えない -->"

# 切り出す所＝（逐語のファイル, 始まりの行の頭, 終わりの行の頭〔この行は入れない〕, 上に付ける見出し〔None＝付けない〕）
PARTS = (
    ("okd_requirements_core_20261012.txt", "# 要件定義（CAT プロジェクトと engine_tuner の目的と要件）", "---", None),
    ("okd_work_flow_20261012.txt", "## 流れ（", "## いま起きていること",
     "# 工事の流れ（やることリストの1件を進める順）"),
    ("okd_design_audit_scope_20261012.txt", "| 直す物 | 設計書の監査 |", "2行目は、私の考えです",
     "# 設計書の監査が要る物・要らない物"),
)
DECISION = "ok_design_audit_scope_20261012.txt"          # 上の3つ目の表を決定にした、まこさんの発言
# ★2026-10-18＝要約（まこさんが OK した CC の文）。「■ 1. 」の行から、囲みの終わり「```」の手前まで。
SUMMARY = "okd_summary_20261018.txt"
SUMMARY_OK = "ok_summary_20261018.txt"
SUMMARY_START = "■ 1. "
SUMMARY_END = "```"
CORE_SECTIONS = ("1", "2", "3", "7", "8", "10")            # いつも載せる芯
ENGINE_SECTIONS = ("4", "5", "6", "9")                      # 売買のロジックに触る工事のときだけ足す


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


# ───────────── 全文 ─────────────

def build_full_lines() -> list:
    """全文（core_requirements_full.md）の全部の行を、逐語のファイルから作る。"""
    names = "・".join(p[0] for p in PARTS)
    out = [HEAD_FULL,
           "# 要件定義と工事の流れ（全文・固定・消さない）",
           "",
           "★この文書は、まこさんが OK した文を、プログラムが逐語のファイルから写した物です。"
           "見出しの3行と、この説明の4行だけが、プログラムの中の決まった文です。",
           f"★出どころ＝`.claude/state/verbatim/{WORK}/` の {names}"
           f"（記録の発言との照らし＝`python3 .claude/tools/gen_verbatim.py --verify {WORK}/<名前>`）。",
           "★作り直し＝`python3 .claude/tools/gen_core_requirements.py --write`。検出＝`--verify`。",
           "★毎回 載せる物は、この全文の要約（`.claude/rules/core_requirements.md`）です。設計書の監査の要件ごとの問いは、この全文から組みます。",
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


def build_full_text() -> str:
    return "\n".join(build_full_lines())


# ───────────── 要約 ─────────────

def summary_sections() -> list:
    """要約の逐語のファイルから、節（番号, 題, 本文の行）を10個 返す。「■ N. 題」の行で分ける。"""
    lines = _read(SUMMARY)
    i0 = next((i for i, ln in enumerate(lines) if ln.startswith(SUMMARY_START)), None)
    if i0 is None:
        raise CoreError(f"[gen_core_requirements] {SUMMARY} に、始まりの行「{SUMMARY_START}」が無い（fail-closed）")
    i1 = next((i for i in range(i0 + 1, len(lines)) if lines[i].startswith(SUMMARY_END)), None)
    if i1 is None:
        raise CoreError(f"[gen_core_requirements] {SUMMARY} に、終わりの行「{SUMMARY_END}」が無い（fail-closed）")
    out, cur = [], None
    for ln in lines[i0:i1]:
        m = re.match(r"^■ (\d+)\. (.+)$", ln)
        if m:
            cur = [m.group(1), m.group(2).strip(), []]
            out.append(cur)
        elif cur is not None:
            cur[2].append(ln)
    for sec in out:
        while sec[2] and not sec[2][-1].strip():
            sec[2].pop()
        while sec[2] and not sec[2][0].strip():
            sec[2].pop(0)
    nums = [s[0] for s in out]
    if nums != [str(i) for i in range(1, 11)]:
        raise CoreError(f"[gen_core_requirements] 要約の節が 1〜10 の順でない（{nums}・fail-closed）")
    if set(CORE_SECTIONS) | set(ENGINE_SECTIONS) != set(nums):
        raise CoreError("[gen_core_requirements] 芯と追加の節の分け方が、要約の節と合わない（fail-closed）")
    return out


def build_lines() -> list:
    """正本（要約・core_requirements.md）の全部の行を、要約の逐語のファイルから作る。"""
    out = [HEAD,
           "# 要件定義と工事の流れ（固定・毎回 読む・消さない）",       # ★題は変えない（設計書・next_step・依頼書が、この題を「固定の文が在る目印」にしている）
           "",
           f"★この文書は、まこさんが OK した要約（2026-10-18・逐語のファイル `{SUMMARY}`・OK の発言＝`{SUMMARY_OK}`）を、"
           "プログラムが写した物です。見出しの行と、この説明の4行だけが、プログラムの中の決まった文です。",
           f"★全文＝`.claude/rules/{OUT_FULL.name}`（同じプログラムが逐語のファイルから作る）。要約の中の まこさんの言葉"
           "（「」の行と、機能要件の6行）が全文に1文字も違わずに在ることを、`--verify` が照らします。",
           "★作り直し＝`python3 .claude/tools/gen_core_requirements.py --write`。検出＝`--verify`。",
           "★設計書・監査の依頼書・next_step の上部には、それぞれを作るプログラムが、この要約を写して載せます"
           f"（いつも載せるのは {'・'.join(CORE_SECTIONS)}。売買のロジックに触る工事では {'・'.join(ENGINE_SECTIONS)} も足します）。"
           "この文書が無い・逐語のファイルと違うときは、どのプログラムも文書を作らずに止まります。",
           ""]
    for num, title, body in summary_sections():
        out += [f"## {num}. {title}"] + body + [""]
    return out


def build_text() -> str:
    return "\n".join(build_lines())


def _norm(s: str) -> str:
    """照らすために、空白と太字の印（*）を外す。"""
    return re.sub(r"[\s*]", "", s)


def summary_mismatch() -> list:
    """要約の中の まこさんの言葉（「」の中の文と、機能要件の6行と、機能要件の1文）が、全文に在るかを照らす。無い物を文で返す。"""
    full = _norm(build_full_text())
    bad = []
    for num, _title, body in summary_sections():
        for ln in body:
            for q in re.findall(r"「([^」]+)」", ln):
                if _norm(q) not in full:
                    bad.append(f"要約の {num} の「{q[:40]}」が、全文の逐語に無い")
            if num == "3" and ln.strip():
                if _norm(ln) not in full:
                    bad.append(f"要約の 3（機能要件）の行「{ln[:40]}」が、全文の逐語に無い")
    return bad


def problems() -> list:
    """正本（要約）と全文が、逐語のファイルから作り直した物と同じか。要約の まこさんの言葉が全文に在るか。違いを文で返す（空なら同じ）。"""
    out = []
    for path, want in ((OUT, build_text()), (OUT_FULL, build_full_text())):
        if not path.is_file():
            out.append(f"正本が無い: {path}（python3 .claude/tools/gen_core_requirements.py --write で作る）")
            continue
        got = path.read_text(encoding="utf-8")
        if got != want:
            a, b = got.splitlines(), want.splitlines()
            n = next((i for i, (x, y) in enumerate(zip(a, b), 1) if x != y), min(len(a), len(b)) + 1)
            out.append(f"{path.name} が、逐語のファイルから作り直した物と違う（{n} 行目から・正本 {len(a)} 行／作り直し {len(b)} 行）"
                       "＝手で書き換えられた疑い。--write で作り直す")
    out += summary_mismatch()
    return out


def embed_lines(tier: str = "all") -> list:
    """ほかの文書の中に載せる形の行を返す。正本が無い・違うときは止まる（fail-closed）。

    tier＝"all"（10節 全部）／"core"（芯の 1・2・3・7・8・10 だけ＝売買のロジックに触らない工事の依頼書）。
    見出しの行（# で始まる行）は、載せる先の文書の見出しの並びを壊さないように、太字の行に変える。文は変えない。
    """
    ng = problems()
    if ng:
        raise CoreError("[gen_core_requirements] 固定で載せる文の正本が使えない（fail-closed）:\n  " + "\n  ".join(ng))
    if tier not in ("all", "core"):
        raise CoreError(f"[gen_core_requirements] tier は all か core（{tier}）")
    keep = None if tier == "all" else set(CORE_SECTIONS)
    out = []
    skip = False
    for ln in OUT.read_text(encoding="utf-8").splitlines():
        if ln == HEAD:
            continue
        m = re.match(r"^## (\d+)\. ", ln)
        if m:
            skip = keep is not None and m.group(1) not in keep
        if skip:
            continue
        if ln.startswith("#"):
            out.append(f"**■ {ln.lstrip('#').strip()}**")
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
    """設計書が1行ずつ照らす要件（番号, 名前）を、全文から並べる（2026-10-12・直し方の案 A-4）。

    全文の「# 要件定義（…）」の部分の見出し（## N. 名前）から作る。要件が増えたら、行も増える。
    ★2026-10-18＝要約でなく全文から組む（要約から組むと、問いが減る）。
    正本が無い・逐語のファイルと違うときは止まる（fail-closed）。
    """
    ng = problems()
    if ng:
        raise CoreError("[gen_core_requirements] 固定で載せる文の正本が使えない（fail-closed）:\n  " + "\n  ".join(ng))
    lines = OUT_FULL.read_text(encoding="utf-8").splitlines()
    i0 = next((i for i, ln in enumerate(lines) if ln.startswith("# 要件定義（")), None)
    if i0 is None:
        raise CoreError("[gen_core_requirements] 全文に「# 要件定義（…）」の見出しが無い（fail-closed）")
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
        raise CoreError(f"[gen_core_requirements] 全文から照らす要件を読めない（{len(items)} 件・fail-closed）")
    return items


def main(argv: list) -> int:
    if "--items" in argv:
        for no, name in requirement_items():
            print(f"{no}\t{name}")
        return 0
    if "--print" in argv:
        print(build_text())
        return 0
    if "--print-full" in argv:
        print(build_full_text())
        return 0
    if "--write" in argv:
        ng = summary_mismatch()
        if ng:
            for x in ng:
                print(f"❌ {x}")
            print("❌ 書かなかった（要約の まこさんの言葉が、全文の逐語に無い）")
            return 1
        for path, text in ((OUT, build_text()), (OUT_FULL, build_full_text())):
            path.write_text(text, encoding="utf-8")
            print(f"✅ --write: {path.relative_to(ROOT)}（{len(text.splitlines())} 行）")
        return 0
    if "--verify" in argv:
        ng = problems()
        for x in ng:
            print(f"❌ {x}")
        if not ng:
            print(f"✅ --verify: 正本（要約）と全文は、逐語のファイルから作り直した物と同じ。要約の まこさんの言葉は全文に在る"
                  f"（{OUT.relative_to(ROOT)}・{OUT_FULL.relative_to(ROOT)}）")
        return 1 if ng else 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
