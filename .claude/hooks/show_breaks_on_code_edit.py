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
  ③ ★2026-10-17（184回目・まこさん「CC の案：要として、誤報を無くす直しをする」）＝①の壊すプログラムから、
     承認のときと同じ関数（run_breaks.extract_targets）で「相手のファイル」と「探す文字」を取り出し、
     直す前と直した後の中身で数える。直す前は壊せた（ちょうど1か所・全部を消す形と最初の1か所を使う形は1か所以上）のに、
     直した後は壊せなくなる物だけを当たりにする（直す前は③'だけで見たので、同じ文字の別の行を直しても止めた＝b48）。
  ③' 探す文字を取り出せない壊すプログラムと、直した後の中身を作れない（old_string が無い）ときは、いままでどおり、
     ②の行の文字が壊すプログラムの中に在るかを探す（\\ を外した形でも探す＝python の文字列や sed の中で \" \' と
     エスケープされている場合に当てるため）。
  ④ 当たれば、壊すプログラムの名前と当たった行（③は数も）を出して1回だけ止める（rc=2）。
     同じ中身（ファイル・壊すプログラム・行）の2回目は通す。見せた記録は
     .claude/state/sessions/<id>/break_edit_shown.json に hook が書く。

限界（正直に）
  ① Bash（sed -i・python）で直すと見ない。
  ② 壊すプログラムが相手を変数の組み立て（"$PR/$NAME"）で書き、basename が文字として無いと見ない。
  ③ 探す文字を取り出せない壊すプログラム（式で探す・相手を決められない＝2026-10-17 に35本）は③'の見方のまま
     ＝同じ文字の別の行を直しても止める誤報と、行の一部だけで探す場合の見落としが残る。
  ④ 見せるだけで、壊すプログラムを直したかは見ない（それは仕組み1の後半＝探す文字がいまのコードに
     ちょうど1か所あるかを数える検査で見る）。直す前から探す文字が0か所の物（もう壊れている物）も、ここでは止めない。
  ⑤ 試し方＝--selftest（S1〜S5・2026-10-17 に足した）と --try <hook の入力の json>。
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
BREAKS = ROOT / ".claude/breaks"
STATE = ROOT / ".claude/state/sessions"
MIN_LEN = 8
sys.path.insert(0, str(ROOT / ".claude/tools"))


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


def find_hits(path: Path, lines: list[str], breaks: list[Path] | None = None) -> list[tuple[str, str]]:
    """(壊すプログラムの名前, 当たった行) の一覧。breaks を渡すと、その壊すプログラムだけを見る。"""
    found = []
    for b in (breaks if breaks is not None else breaks_naming(path.name)):
        try:
            txt = b.read_text(encoding="utf-8")
        except Exception:
            continue
        flat = txt.replace("\\", "")
        for t in lines:
            if t in txt or t.replace("\\", "") in flat:
                found.append((b.name, t))
    return found


def after_text(tool: str, ti: dict, before: str) -> str | None:
    """直した後の中身。作れないとき（old_string が無い）は None。"""
    if tool == "Write":
        return str(ti.get("content") or "")
    edits = ti.get("edits") if tool == "MultiEdit" else [ti]
    s = before
    for e in edits or []:
        old, new = str(e.get("old_string") or ""), str(e.get("new_string") or "")
        if not old or old not in s:
            return None
        s = s.replace(old, new) if e.get("replace_all") else s.replace(old, new, 1)
    return s


def _n(srch: dict, text: str) -> int:
    if srch["kind"] == "文字":
        return text.count(srch["text"])
    try:
        return len(re.findall(srch["text"], text, srch["flags"]))
    except re.error:
        return 0


def _ok(srch: dict, n: int) -> bool:
    """壊せるか（run_breaks.count_targets と同じ＝ちょうど1か所・全部を消す形と最初の1か所を使う形は1か所以上）。"""
    return n == 1 or (n > 1 and bool(srch.get("all") or srch.get("first")))


def precise_hits(path: Path, tool: str, ti: dict, lines: list[str],
                 breaks: list[Path] | None = None) -> list[tuple[str, str]]:
    """★2026-10-17（184回目・まこさん「CC の案：要として、誤報を無くす直しをする」）＝直した後に壊せなくなる壊すプログラムだけを返す。
    探す文字を取り出せない壊すプログラムと、直した後の中身を作れないときは、いままでどおり消える行の文字で見る（find_hits）。
    直す前は消える行の文字だけで見たので、同じ文字の別の行を直しただけでも止めた（2026-10-17 の b48）。"""
    import run_breaks as rb
    try:
        before = path.read_text(encoding="utf-8")
    except Exception:
        before = ""
    after = after_text(tool, ti, before)
    lib = BREAKS / "lib.sh"
    lib_text = lib.read_text(encoding="utf-8", errors="ignore") if lib.exists() else ""
    me = os.path.realpath(path)
    found, rough = [], []
    for b in (breaks if breaks is not None else breaks_naming(path.name)):
        try:
            items = [it for it in rb.extract_targets(b, lib_text)
                     if it.get("target") and os.path.realpath(it["target"]) == me]
        except Exception:
            items = []
        srchs = [s for it in items for s in it["searches"]]
        if not srchs or after is None:
            rough.append(b)
            continue
        for s in srchs:
            n0, n1 = _n(s, before), _n(s, after)
            if _ok(s, n0) and not _ok(s, n1):
                found.append((b.name, f"{s['text'][:80]}（直す前 {n0} か所 → 直した後 {n1} か所）"))
    return found + (find_hits(path, lines, rough) if rough else [])


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
    # ★2026-10-18（監査 CP79 の修正）＝消える行が8文字未満でも、探す文字の数え直し（precise_hits）は走らせる。
    #   直す前は lines が空だと見ずに通したので、7文字以下の old_string で探す文字を壊す Edit が通った（b48 の相手で実測）。
    hits = precise_hits(path, tool, ti, lines)
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


def selftest() -> int:
    """★2026-10-17＝precise_hits を、一時の置き場の見本のコードと見本の壊すプログラムで試す（本物には書かない）。"""
    import shutil
    import tempfile
    d = Path(tempfile.mkdtemp(prefix="sb_selftest_"))
    code = d / "x_code.py"
    body = ("def a():\n    target_line_here()\n    next_line()\n\n"
            "def b():\n    target_line_here()\n    other()\n")
    code.write_text(body, encoding="utf-8")
    head = f'T="{code}"\npython3 - "$T" <<\'PYEOF\'\nimport sys\np = sys.argv[1]\ns = open(p, encoding="utf-8").read()\n'
    ba = d / "ba.sh"                                 # 探す文字を取り出せる壊すプログラム（a の2行を探す）
    ba.write_text(head + "old = 'target_line_here()\\n    next_line()\\n'\n"
                  "if s.count(old) != 1:\n    raise SystemExit(1)\nPYEOF\n", encoding="utf-8")
    bb = d / "bb.sh"                                 # 探す文字を取り出せない壊すプログラム（式で探す）
    bb.write_text(head + "# 探す行: target_line_here()\nx = 'target' + '_line_here()'\n"
                  "s = s.replace(x, 'z', 1)\nPYEOF\n", encoding="utf-8")

    def run(tool, ti, breaks):
        return precise_hits(code, tool, ti, removed_lines(pairs_of(tool, ti, code)), breaks)
    E = lambda o, n: {"old_string": o, "new_string": n}            # noqa: E731
    cases = [
        ("S1 探す文字を消す Edit → 止まる",
         run("Edit", E("    target_line_here()\n    next_line()", "    renamed()\n    next_line()"), [ba]), True),
        ("S2 同じ文字の別の行だけを直す Edit（探す文字は1か所のまま）→ 通る",
         run("Edit", E("    target_line_here()\n    other()", "    changed()\n    other()"), [ba]), False),
        ("S3 探す文字を取り出せない壊すプログラムで、消える行の文字が中に在る → 止まる（いままでどおり）",
         run("Edit", E("    target_line_here()\n    other()", "    changed()\n    other()"), [bb]), True),
        ("S4 Write で探す文字を消す → 止まる", run("Write", {"content": "def a():\n    pass\n"}, [ba]), True),
        ("S5 old_string がファイルに無い Edit → いままでどおりの見方（消える行の文字が中に在れば止まる）",
         run("Edit", E("    target_line_here()\n    zzz()", "    y()"), [ba]), True),        ("S6 7文字の old_string（消える行の一覧は空）で探す文字を壊す Edit → 止まる（2026-10-18・監査 CP79）",
         run("Edit", E("line_he", "line_XX"), [ba]), True),
    ]
    ng = 0
    for nm, got, want in cases:
        ok = bool(got) == want
        ng += not ok
        print(f"  {'✅' if ok else '❌'} {nm}" + ("" if ok else f" ← {got}"))
    shutil.rmtree(d, ignore_errors=True)
    print(f"自己テスト {len(cases) - ng}/{len(cases)}")
    return 1 if ng else 0


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--selftest":
        sys.exit(selftest())
    if len(sys.argv) == 3 and sys.argv[1] == "--try":
        sys.exit(main(Path(sys.argv[2]).read_text(encoding="utf-8")))
    sys.exit(main(sys.stdin.read()))
