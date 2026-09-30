#!/usr/bin/env python3
"""forbid_edit_generated_docs.py — 元データから作った文書の、生成された部分への Write・Edit を止める（2026-09-17・新設）

まこさん指示 2026-09-17（逐語）＝「CCは確認せずミスを繰り返すので、手書きせざるをえないもの以外は自動生成にしてほしい」。
設計書 docs-autogen-next-step-pdca-20260917 の 4-3（まこさん決定「４つともCCのおすすめのやり方でOK」の③）。

何を止めるか
  ① .claude/state/next_step.md＝1行目に生成の目印（<!-- NEXT_STEP_GENERATED hash=…）が在れば、Write・Edit・MultiEdit を全部 止める。
     直す道＝元データ .claude/state/next_step_src.json を直して `python3 .claude/tools/tidy_next_step.py --write`。
  ② .claude/rules/pdca_flow.md＝目印 <!-- HOOK_LIST_START … --> 〜 <!-- HOOK_LIST_END --> の中に当たる直しを止める。
     Edit・MultiEdit＝消す文字（old_string）が囲みと重なれば止める。Write＝囲みの中身が変われば止める。
     囲みの外（§0・§1.5・§2〜§6・改訂ルール）は止めない（まこさん決定＝§1 の表だけ）。
     直す道＝元データ .claude/state/hook_roles.json を直して `python3 .claude/tools/gen_hook_list.py --write`。
  ③ .claude/state/acceptance.md（設計書）＝中に生成の目印（<!-- ACC_…_START hash=…）が1つでも在れば、Write・Edit・MultiEdit を全部 止める
     （2026-09-29 まこさん指示「防止策で効果があるものは対応してよい」・worklog 20260929 §76）。
     直す道＝工事のフォルダ（.claude/state/verbatim/<工事名>/）に、まこさんが OK した案を gen_verbatim.py で写す
     → `python3 .claude/tools/gen_acceptance.py --work <工事名> --write`。
     ★2026-09-30（設計書 point1-one-way-20260930-2 の W-1・W-5）＝古い元データ acceptance_src.json の道は無くした（作り方は1本）。
     なぜ＝設計書の手直しは、機械が書いた節の外（元データから写した節）に入れると --verify に捕まらない＝虚偽・改ざんの置き場になる。

止めないもの
  ・セッションの id が無い呼び方（承認のプログラムが設計書の不足を探すために hook を試しに呼ぶとき。本物の Write・Edit には必ず付く）。
  ・サブエージェント／読めない入力／本体の例外（fail-open）。★Bash での書き替えは見ない＝Stop hook の --verify がハッシュ値で止める。

限界（正直に）
  ・この hook と道具そのものを書き換えれば無効にできる（差分は git に出る）。
  ・元データの文の中身の正しさは見ない。
  ・恒久71番＝壊すプログラムと自己テストは付けない。--try で1回ずつ確かめる。
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
NEXT = ROOT / ".claude/state/next_step.md"
PDCA = ROOT / ".claude/rules/pdca_flow.md"
ACC = ROOT / ".claude/state/acceptance.md"
NEXT_MARK = "<!-- NEXT_STEP_GENERATED hash="
ACC_MARK_RE = r"<!-- ACC_[A-Za-z0-9_]+_START hash="
LIST_START = "<!-- HOOK_LIST_START hash="
LIST_END = "<!-- HOOK_LIST_END -->"


def _region(text: str) -> tuple[int, int] | None:
    s = text.find(LIST_START)
    if s < 0:
        return None
    e = text.find(LIST_END, s)
    if e < 0:
        return None
    return s, e + len(LIST_END)


def _block(msg: str) -> int:
    print(msg, file=sys.stderr)
    return 2


def check(data: dict) -> int:
    if data.get("agent_type") or not data.get("session_id"):
        return 0
    tool = data.get("tool_name", "")
    if tool not in ("Write", "Edit", "MultiEdit"):
        return 0
    ti = data.get("tool_input") or {}
    fp = str(ti.get("file_path") or "")
    if not fp:
        return 0
    path = pathlib.Path(fp)
    try:
        path = path.resolve()
    except Exception:
        pass
    if path == NEXT.resolve():
        try:
            first = NEXT.read_text(encoding="utf-8").split("\n", 1)[0]
        except Exception:
            return 0
        if first.startswith(NEXT_MARK):
            return _block(
                "🔒 [生成された文書・hook forbid_edit_generated_docs] next_step.md はプログラムが元データから作っています＝手で直せません"
                "（まこさん指示 2026-09-17「手書きせざるをえないもの以外は自動生成にしてほしい」）。\n"
                "   直す道＝元データ .claude/state/next_step_src.json を直す → python3 .claude/tools/tidy_next_step.py --write\n"
                "   （解除の合言葉はありません）")
        return 0
    if path == ACC.resolve():
        try:
            cur = ACC.read_text(encoding="utf-8")
        except Exception:
            return 0
        if re.search(ACC_MARK_RE, cur):
            return _block(
                "🔒 [生成された文書・hook forbid_edit_generated_docs] acceptance.md（設計書）はプログラムが元データから作っています＝手で直せません"
                "（まこさん指示 2026-09-29「防止策で効果があるものは対応してよい」・2026-09-17「手書きせざるをえないもの以外は自動生成にしてほしい」）。\n"
                "   直す道＝工事のフォルダ（.claude/state/verbatim/<工事名>/）に、まこさんが OK した案を gen_verbatim.py で写す"
                " → python3 .claude/tools/gen_acceptance.py --work <工事名> --write\n"
                "   （解除の合言葉はありません）")
        return 0
    if path == PDCA.resolve():
        try:
            cur = PDCA.read_text(encoding="utf-8")
        except Exception:
            return 0
        reg = _region(cur)
        if reg is None:
            return 0
        s, e = reg
        hit = False
        if tool == "Write":
            new = str(ti.get("content") or "")
            nreg = _region(new)
            hit = nreg is None or new[nreg[0]:nreg[1]] != cur[s:e]
        else:
            olds = ([str(ti.get("old_string") or "")] if tool == "Edit"
                    else [str(x.get("old_string") or "") for x in (ti.get("edits") or [])])
            for old in olds:
                if not old:
                    continue
                pos = cur.find(old)
                while pos >= 0:
                    if pos < e and pos + len(old) > s:
                        hit = True
                        break
                    pos = cur.find(old, pos + 1)
                if hit:
                    break
        if hit:
            return _block(
                "🔒 [生成された文書・hook forbid_edit_generated_docs] pdca_flow.md の §1 の hook の一覧は、"
                "プログラムが settings.json と元データから作っています＝囲みの中は手で直せません"
                "（まこさん指示 2026-09-17「手書きせざるをえないもの以外は自動生成にしてほしい」）。\n"
                "   直す道＝役割の文は .claude/state/hook_roles.json を直す（名前・タイミング・matcher は settings.json が正本）"
                " → python3 .claude/tools/gen_hook_list.py --write\n"
                "   囲みの外（§0・§1.5・§2〜§6・改訂ルール）は、いままでどおり直せます。（解除の合言葉はありません）")
        return 0
    return 0


def main(raw: str) -> int:
    try:
        data = json.loads(raw)
    except Exception:
        return 0
    try:
        return check(data)
    except Exception:
        return 0


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--try":
        sys.exit(main(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8")))
    sys.exit(main(sys.stdin.read()))
