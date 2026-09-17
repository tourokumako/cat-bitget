#!/usr/bin/env python3
"""show_breaks_on_code_edit.py — コードの行を直す直前に、その行を文字で探している壊すプログラムを見せる。

まこさん指示 2026-09-16（逐語）＝「この３つのミスを繰り返さない仕組みを作れ」
  「コードを直したら、その行を探している壊すプログラムが在るかを、必ず grep」（L-605）。
next_step §0-2 の仕組み1の前半。

なぜ要るか（L-605・103回目）
  走らせる道具 run_breaks.py の lint_expect の行を直したのに、その行を文字で探して壊す
  壊すプログラム b95 の探す文字を直さなかった。承認で b95 は何も壊せず rc=0 になった。

何をするか
  ① Write／Edit／MultiEdit で直すファイルの名前（basename）を、.claude/breaks/*.sh の中から探す。
     名前が出てくる壊すプログラムだけを相手にする（名前が出てこないファイルは見ない＝止めない）。
  ② 直す前にあって直した後に無くなる行（前後の空白を除いて8文字以上）を取り出す。
  ③ その行の文字が、①の壊すプログラムの中に在るかを探す（\\ を外した形でも探す＝
     python の文字列や sed の中で \" \' とエスケープされている場合に当てるため）。
  ④ 当たれば、壊すプログラムの名前と当たった行を出して1回だけ止める（rc=2）。
     同じ中身（ファイル・壊すプログラム・行）の2回目は通す。見せた記録は
     .claude/state/sessions/<id>/break_edit_shown.json に hook が書く。

限界（正直に）
  ① Bash（sed -i・python）で直すと見ない。
  ② 壊すプログラムが相手を変数の組み立て（"$PR/$NAME"）で書き、basename が文字として無いと見ない。
  ③ 壊すプログラムが正規表現や行の一部だけで探す場合、行全体の文字では当たらない（8文字以上の行の
     全体が壊すプログラムの中に在るときだけ当たる）。
  ④ 見せるだけで、壊すプログラムを直したかは見ない（それは仕組み1の後半＝探す文字がいまのコードに
     ちょうど1か所あるかを数える検査で見る）。
  ⑤ 恒久71番＝BOT の中身でない道具なので、壊すプログラムと自己テストは付けない。--try で1回 確かめる。
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
BREAKS = ROOT / ".claude/breaks"
STATE = ROOT / ".claude/state/sessions"
MIN_LEN = 8


def pairs_of(tool: str, ti: dict, path: Path) -> list[tuple[str, str]]:
    if tool == "Edit":
        return [(str(ti.get("old_string") or ""), str(ti.get("new_string") or ""))]
    if tool == "MultiEdit":
        return [(str(e.get("old_string") or ""), str(e.get("new_string") or ""))
                for e in (ti.get("edits") or [])]
    if tool == "Write":
        try:
            before = path.read_text(encoding="utf-8")
        except Exception:
            return []
        return [(before, str(ti.get("content") or ""))]
    return []


def removed_lines(pairs: list[tuple[str, str]]) -> list[str]:
    out: list[str] = []
    for old, new in pairs:
        keep = {s.strip() for s in new.splitlines()}
        for s in old.splitlines():
            t = s.strip()
            if len(t) >= MIN_LEN and t not in keep and t not in out:
                out.append(t)
    return out


def breaks_naming(name: str) -> list[Path]:
    if not BREAKS.is_dir():
        return []
    hits = []
    for b in sorted(BREAKS.glob("*.sh")):
        if b.name == "lib.sh":
            continue
        try:
            if name in b.read_text(encoding="utf-8"):
                hits.append(b)
        except Exception:
            continue
    return hits


def find_hits(path: Path, lines: list[str]) -> list[tuple[str, str]]:
    """(壊すプログラムの名前, 当たった行) の一覧。"""
    found = []
    for b in breaks_naming(path.name):
        try:
            txt = b.read_text(encoding="utf-8")
        except Exception:
            continue
        flat = txt.replace("\\", "")
        for t in lines:
            if t in txt or t.replace("\\", "") in flat:
                found.append((b.name, t))
    return found


def first_time(sid: str, key: str) -> bool:
    p = STATE / (sid or "no-session") / "break_edit_shown.json"
    try:
        shown = set(json.loads(p.read_text(encoding="utf-8")))
    except Exception:
        shown = set()
    if key in shown:
        return False
    shown.add(key)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(sorted(shown)), encoding="utf-8")
    except Exception:
        pass
    return True


def main(raw: str) -> int:
    try:
        data = json.loads(raw)
    except Exception:
        return 0                                   # 読めない入力では止めない（fail-open）
    if data.get("agent_type"):
        return 0                                   # サブエージェントは見ない
    if not data.get("session_id"):
        # ★2026-09-17＝承認のプログラムが設計書の不足を探すために hook を試しに呼ぶとき、
        #   セッションの id が無い。そこで「見せて1回止める」を返すと、設計書の不足と数えられて
        #   承認が止まった（実測）。本物の Write・Edit には Claude Code が必ず id を付けるので、
        #   id の無い呼び方では止めない。
        return 0
    tool = data.get("tool_name", "")
    if tool not in ("Write", "Edit", "MultiEdit"):
        return 0
    ti = data.get("tool_input") or {}
    fp = str(ti.get("file_path") or "")
    if not fp:
        return 0
    path = Path(fp)
    if path.parent == BREAKS:
        return 0                                   # 壊すプログラム自身を直すときは見ない
    lines = removed_lines(pairs_of(tool, ti, path))
    if not lines:
        return 0
    hits = find_hits(path, lines)
    if not hits:
        return 0
    key = hashlib.sha256(json.dumps([fp, hits], ensure_ascii=False).encode()).hexdigest()
    if not first_time(str(data.get("session_id") or ""), key):
        return 0                                   # 同じ中身は見せ済み＝2回目は通す
    e = sys.stderr
    print("🔒 [壊すプログラムを見せるゲート] 直して消える行を、文字で探している壊すプログラムが在ります"
          "（まこさん指示 2026-09-16「この３つのミスを繰り返さない仕組みを作れ」・L-605）。", file=e)
    for name, t in hits:
        print(f"   ⚠️ {name} が探している行: {t[:120]}", file=e)
    print("   ＝この直しのあと、上の壊すプログラムの探す文字を、直した後の行に合わせてください"
          "（合わせないと、承認で何も壊せず rc=0 になります）。", file=e)
    print("   ＝確かめたら、同じ直しをもう一度 書けば通ります（この一覧は1回だけ出します）。", file=e)
    return 2


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--try":
        sys.exit(main(Path(sys.argv[2]).read_text(encoding="utf-8")))
    sys.exit(main(sys.stdin.read()))
