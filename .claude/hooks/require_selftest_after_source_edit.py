#!/usr/bin/env python3
"""require_selftest_after_source_edit.py — テンプレや元データを書き替えたら、それを読む道具の自己テストを走らせるまでターンを終われなくする。

まこさん指示 2026-09-16（逐語）＝「この３つのミスを繰り返さない仕組みを作れ」。
next_step §0-2 の仕組み2・教訓 L-604。

なぜ要るか（L-604・102〜103回目）
  2026-09-15 に監査のテンプレ `_template.md` の見出しを変えた。古い依頼書の道具 gen_audit_request.py は
  テンプレの見出しを一覧で持っていたので、自己テストが落ちるようになった。変えたときに、このテンプレを
  読む道具を探さなかった。翌日、監査に出す前のチェックが NG を出して初めて分かった。

2つの口
  post（PostToolUse on Write／Edit／MultiEdit）
    ① 書き替えたファイルが「テンプレか元データ」なら（下の is_source）、そのファイル名（basename）を
       .claude/tools・.claude/hooks・SDK の scripts/priority_rebuild の .py から探す。
    ② その中で自己テストの旗（"--selftest" の文字）を持つ道具を一覧にし、書き替えた時刻と一緒に
       .claude/state/sessions/<id>/selftest_pending.json に記録する。一覧を画面に出す（rc=2＝知らせるだけ・
       書き替えはもう済んでいる）。
  stop（Stop）
    ③ 記録の道具ごとに、書き替えた時刻より後に「その道具の名前と --selftest を含む Bash のコマンド」を
       私が打ったかを、やり取りの記録（transcript）から探す。打っていれば記録から消す。
    ④ 1本でも残っていれば、打つコマンドの一覧を出してターンを終われなくする（rc=2）。
       ★落ちた自己テストでも「打った」は数える＝落ちたまま終われなくなる行き止まりは作らない。
         落ちた結果を報告するのは私の仕事（ここは見ない）。

テンプレか元データ（is_source）
  名前に template を含む（.py・.sh を除く）／または .json（.claude/state/sessions の中と settings*.json を除く）。

限界（正直に）
  ① Bash（sed -i・gen の --write）で書き替えると見ない（Write／Edit／MultiEdit だけ）。
  ② 道具がファイル名を文字で持たず、組み立てて読むと見つからない。
  ③ 自己テストの結果（通ったか）は見ない。打ったかだけ。
  ④ 一覧（tuple・list・set）の要素として名前を持ち、その一覧から実際に読む道具は見つからない（2026-10-17 の直しの裏側）。

★2026-10-17（183回目・まこさん「このCCの案で修正してOK」「よい」・直す前と後の行＝.claude/state/hook_fix_proposals/
  require_selftest_after_source_edit_20261017.md）＝直近7日で知らせ 317回・止め 5回（5回とも自己テストは通った）を数え、
  ①同じ道具の知らせは、まだ走らせていない間は1回だけにした ②読む道具は、コードの中の文字の値（説明の文と一覧の要素を除く）で
  探すようにした ③リポジトリの外の一時ファイルを元データとして扱わないようにした ④--selftest を足した。
  直す前の説明は「恒久71番＝BOT の中身でない道具なので、壊すプログラムと自己テストは付けない」だったが、
  恒久76番（hook の直しは、同じミスが二度と起きない状態に）を受けて自己テストを足した。

使い方: （hook）post ／ stop を引数に、標準入力に hook の JSON ／ --selftest ／ --try <post|stop> <JSON のファイル> ／
       --readers <ファイル名>…（そのファイルを読む道具の一覧を出すだけ・何も書かない）
"""

from __future__ import annotations

import ast
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
SDK = ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api"
STATE = ROOT / ".claude/state/sessions"
READER_DIRS = [ROOT / ".claude/tools", ROOT / ".claude/hooks", SDK / "scripts/priority_rebuild"]
SELFTEST = '"--selftest"'


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def is_source(path: Path) -> bool:
    s = str(path)
    # ★2026-10-17（183回目）＝リポジトリの外（作業場 scratchpad・/tmp）のファイルは元データでない。直す前は、作業場の
    #   vrc/meta.json を書き替えたときに、「.meta.json」を持つ道具2本を挙げた。
    if not s.startswith(str(ROOT) + "/"):
        return False
    if "/.claude/state/sessions/" in s:
        return False
    if path.suffix in (".py", ".sh"):
        return False
    if "template" in path.name.lower():
        return True
    return path.suffix == ".json" and not path.name.startswith("settings")


def names_path(tree, name: str) -> bool:
    """★2026-10-17（183回目・まこさん「このCCの案で修正してOK」）＝コードの中の文字の値（説明の文〔docstring〕を除く）が、
      そのファイル名そのもの（"m2_todo.json"）か、「/」の後ろがそのファイル名（".../m2_todo.json"）のときだけ数える。
      一覧（tuple・list・set）の要素は数えない（名前を「止めない置き場の一覧」に持つだけの道具を外すため）。
      直す前は本文の文字で探し、説明の文の名前・別のファイル名の一部・一覧の中の名前まで数えた（直近7日で17組のうち4組）。"""
    docs = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.body:
            b = n.body[0]
            if isinstance(b, ast.Expr) and isinstance(b.value, ast.Constant) and isinstance(b.value.value, str):
                docs.add(id(b.value))
    in_coll = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Tuple, ast.List, ast.Set)):
            in_coll.update(id(e) for e in n.elts)
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs and id(n) not in in_coll:
            v = n.value.strip()
            if v == name or v.endswith("/" + name):
                return True
    return False


def readers_with_selftest(name: str, dirs: list | None = None) -> list[str]:
    out = []
    for d in (READER_DIRS if dirs is None else dirs):
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.py")):
            if p.name == Path(__file__).name:
                continue                           # この hook 自身は説明の文に名前を持つだけ＝数えない
            try:
                txt = p.read_text(encoding="utf-8")
            except Exception:
                continue
            if SELFTEST not in txt:
                continue
            try:
                hit = names_path(ast.parse(txt), name)
            except SyntaxError:
                hit = name in txt                  # 読めない .py は、直す前と同じ文字の探し方に戻す（見落とさない側）
            if hit:
                out.append(str(p))
    return out


def pending_path(sid: str) -> Path:
    return STATE / (sid or "no-session") / "selftest_pending.json"


def load(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save(p: Path, d: dict) -> None:
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:
        pass


def post(data: dict) -> int:
    if data.get("agent_type"):
        return 0
    if data.get("tool_name") not in ("Write", "Edit", "MultiEdit"):
        return 0
    fp = str((data.get("tool_input") or {}).get("file_path") or "")
    if not fp or not is_source(Path(fp)):
        return 0
    readers = readers_with_selftest(Path(fp).name)
    if not readers:
        return 0
    p = pending_path(str(data.get("session_id") or ""))
    d = load(p)
    t = now_iso()
    new = [r for r in readers if r not in d]      # ★2026-10-17（183回目）＝まだ走らせていない道具は知らせ直さない
    for r in readers:
        e = d.get(r) or {"sources": [], "since": t}
        if fp not in e["sources"]:
            e["sources"].append(fp)
        e["since"] = t                             # 書き替えるたびに、その後の走行を求め直す（止めは今までどおり）
        d[r] = e
    save(p, d)
    if not new:
        return 0
    print(f"📋 [自己テストを求める記録] {Path(fp).name} を読む道具のうち、自己テストを持つもの {len(new)} 本を記録しました"
          "（まこさん指示 2026-09-16・L-604）。ターンを終える前に、全部 走らせてください:", file=sys.stderr)
    for r in new:
        print(f"   python3 {r} --selftest", file=sys.stderr)
    return 2


def commands_since(transcript: str, since: str) -> list[str]:
    cmds = []
    try:
        with open(transcript, encoding="utf-8") as f:
            for line in f:
                try:
                    o = json.loads(line)
                except Exception:
                    continue
                if o.get("type") != "assistant" or str(o.get("timestamp") or "") < since:
                    continue
                for c in (o.get("message") or {}).get("content") or []:
                    if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") == "Bash":
                        cmds.append(str((c.get("input") or {}).get("command") or ""))
    except Exception:
        pass
    return cmds


def stop(data: dict) -> int:
    p = pending_path(str(data.get("session_id") or ""))
    d = load(p)
    if not d:
        return 0
    tr = str(data.get("transcript_path") or "")
    left = {}
    for r, e in d.items():
        if not Path(r).is_file():
            continue
        name = Path(r).name
        # ★2026-10-18（監査 CP80）＝python でその道具を --selftest つきで走らせたコマンドだけを数える
        #   （直す前は grep -c -- "--selftest" <道具> のように、名前と旗の文字が在るだけで「走らせた」と数えた）
        ran = re.compile(r"\bpython[0-9.]*\s+(?:-\S+\s+)*\S*" + re.escape(name) + r"\b[^;&|\n]*\s--selftest\b")
        if any(ran.search(c) for c in commands_since(tr, e.get("since", ""))):
            continue
        left[r] = e
    save(p, left)
    if not left:
        return 0
    print("🔒 [自己テストを走らせるゲート] テンプレや元データを書き替えたのに、それを読む道具の自己テストをまだ走らせていません"
          "（まこさん指示 2026-09-16「この３つのミスを繰り返さない仕組みを作れ」・L-604）。", file=sys.stderr)
    for r, e in left.items():
        srcs = "・".join(Path(s).name for s in e.get("sources", []))
        print(f"   ❌ python3 {r} --selftest   （書き替えたもの: {srcs}）", file=sys.stderr)
    print("   ＝全部 走らせてから終えてください。落ちたら、その結果を報告してください（落ちても「走らせた」は数えます）。",
          file=sys.stderr)
    return 2


def main(mode: str, raw: str) -> int:
    try:
        data = json.loads(raw)
    except Exception:
        return 0                                   # 読めない入力では止めない（fail-open）
    return post(data) if mode == "post" else stop(data)


def selftest() -> int:
    """★2026-10-17（183回目）＝読む道具の見分け6件・元データの見分け2件・知らせの出し方2件。作り物の .py と記録は
      一時フォルダに置く（本物の記録は書き替えない）。"""
    import tempfile
    bad = total = 0

    def ok(nm, got, want):
        nonlocal bad, total
        total += 1
        good = got == want
        bad += not good
        print(f"  {'✅' if good else '❌'} {nm}（{got}）")
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        files = {
            "r1.py": 'X = ROOT / "m2_todo.json"\nF = "--selftest"\n',
            "r2.py": '"""m2_todo.json を読む、と説明に書くだけ"""\nF = "--selftest"\n',
            "r3.py": 'X = "x/auditor_template.md"\nF = "--selftest"\n',
            "r4.py": 'FREE = ("/.claude/state/next_step_src.json",)\nF = "--selftest"\n',
            "r5.py": 'import os\nX = os.path.join(A, "inputs", "_template.md")\nF = "--selftest"\n',
            "r6.py": 'X = ROOT / "m2_todo.json"\n',
        }
        for n, body in files.items():
            (t / n).write_text(body, encoding="utf-8")

        def found(name, f):
            return str(t / f) in readers_with_selftest(name, [t])
        ok("R1 ROOT / \"m2_todo.json\" を持つ → 数える", found("m2_todo.json", "r1.py"), True)
        ok("R2 説明の文にだけ在る → 数えない", found("m2_todo.json", "r2.py"), False)
        ok("R3 別のファイル名の一部（auditor_template.md）→ 数えない", found("_template.md", "r3.py"), False)
        ok("R4 一覧の要素だけ → 数えない", found("next_step_src.json", "r4.py"), False)
        ok("R5 os.path.join の引数 → 数える", found("_template.md", "r5.py"), True)
        ok("R6 --selftest を持たない → 数えない", found("m2_todo.json", "r6.py"), False)
    ok("I1 リポジトリの外の一時ファイル → 元データでない", is_source(Path("/private/tmp/x/vrc/meta.json")), False)
    ok("I2 リポジトリの中の m2_todo.json → 元データ", is_source(SDK / ".claude/ratchet/m2_todo.json"), True)
    # 知らせの出し方（本物の post を、作り物のセッションの置き場で通す）
    sid = "_selftest_require_selftest_after_source_edit"
    pend = pending_path(sid)
    import shutil
    shutil.rmtree(pend.parent, ignore_errors=True)
    try:
        src = str(ROOT / ".claude/state/next_step_src.json")
        data = {"tool_name": "Edit", "tool_input": {"file_path": src}, "session_id": sid}
        import contextlib
        import io
        with contextlib.redirect_stderr(io.StringIO()):
            first = post(data)
            before = load(pend)
            second = post(data)
        after = load(pend)
        ok("P0 1回目の書き替え → 知らせる（rc=2）", first, 2)
        ok("P1 まだ走らせていない間の2回目 → 知らせない（rc=0）", second, 0)
        ok("P1 2回目でも記録の時刻は新しくする",
           all(after[r]["since"] >= before[r]["since"] for r in before) and bool(before), True)
        d = load(pend)
        r0 = next(iter(d))
        d.pop(r0)
        save(pend, d)
        with contextlib.redirect_stderr(io.StringIO()) as buf:
            third = post(data)
        ok("P2 新しく加わった道具が在る → その道具だけ知らせる（rc=2）",
           (third, r0 in buf.getvalue(), sum(1 for r in d if r in buf.getvalue())), (2, True, 0))
    finally:
        shutil.rmtree(pend.parent, ignore_errors=True)
    print(f"自己テスト {total - bad}/{total}")
    return 1 if bad else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    if len(sys.argv) >= 3 and sys.argv[1] == "--readers":    # 読む道具の一覧を出すだけ（何も書かない・2026-10-17）
        for nm in sys.argv[2:]:
            print(nm + " → " + "・".join(Path(r).name for r in readers_with_selftest(nm)))
        sys.exit(0)
    if len(sys.argv) == 4 and sys.argv[1] == "--try":
        sys.exit(main(sys.argv[2], Path(sys.argv[3]).read_text(encoding="utf-8")))
    if len(sys.argv) == 2 and sys.argv[1] in ("post", "stop"):
        sys.exit(main(sys.argv[1], sys.stdin.read()))
    sys.exit(0)
