#!/usr/bin/env python3
"""require_work_declaration — ToDo の1件を始める前に、宣言と まこさんの返事を求める（2026-10-12 新設・172回目）。

まこさん指示（逐語 2026-10-12）＝「読んだのかを確認するためにも、作業を始める前に、作業内容、目的、経緯、ゴールを宣言するように強制する」
流れ（まこさん・同日・逐語）＝「必読読んで→todo書いて→そのtodoでこれから始める作業に対し【作業内容、目的、経緯、ゴール】を宣言するという流れだよね」
返事を待つか（まこさん・同日・逐語）＝「入れる」。

決まり（3つ。全部そろえば最初から通る。そろわなければ、何回 打っても通らない＝「1回 止まれば通る」作りは入れない）
  1. このセッションの ToDo（.claude/state/sessions/<セッションの id>/session_todo.md）に「★いまここ」の行が、ちょうど1つ在る。
  2. その番号の宣言が、CC の返信に在る。形＝「【宣言】ToDo の N番」と、【作業内容】【目的】【経緯】【ゴール】の4つ（どれも中身つき）。
  3. その宣言より後に、まこさんの発言が在る（hook の差し戻しの文・途中で止めた印は数えない）。
止めるもの＝Write・Edit・MultiEdit・NotebookEdit・読むだけでない Bash・Agent。
止めないもの＝読む操作／検査だけの実行（--selftest・--verify・--check・--help・--dry・try_hooks.py・next_move.py。--write の付く物は除く）／
  セッションの置き場（ToDo）・worklog・memory・計画のファイルへの書き込み／サブエージェント／記録が読めないとき／
  引き継ぎの文書の元データ（next_step_src.json）への書き込みと、next_step を作り直す操作（tidy_next_step.py）。

なぜこの形か（worklog 20261001 §14）＝前の ToDo の hook（enforce_todo_declaration）は、7日で232回 止め、うち96回は同じ操作の繰り返しで通った。
  原因＝①全文を画面に出すために必ず1回 止まる ②同じ返信の中の貼り付けを、hook が読めないことが在る ③書き替えるたびに、貼る手続きと証拠のファイルが要る。
  この hook は、宣言を「前の返信」に書かせ、まこさんの返事の後に作業を始める形＝①②③が起きない。証拠のファイルも要らない。

限界（正直に）＝宣言の中身が正しいかは見ない（まこさんが読む）。CC が「★いまここ」を動かさずに別の作業をすれば、止まらない。
  ToDo の番号を付け替えると、前の番号の宣言が別の行に当たる＝セッションの中で番号を付け替えない（行は末尾に足す）。

使い方: （hook）標準入力に PreToolUse の JSON ／ --selftest 見本の記録で、止まる場合と通る場合を試す
"""
import json
import pathlib
import re
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from require_check_after_failure import ACT_TOOLS, is_read  # 読むだけの判定を、動いている hook と同じものにする

ROOT = HERE.parent.parent
SESSIONS = ROOT / ".claude" / "state" / "sessions"
# ★2026-10-12（172回目）＝引き継ぎの文書の元データ（next_step_src.json）も、記録と同じ扱いで通す。
#   なぜ＝1件が済んで「★いまここ」を次の番号へ移した後に、締めの手順（ToDo の表を写す → next_step を作り直す）が打てなくなるため。
FREE = ("/.claude/plans/", "session_worklog_", "/.claude/state/sessions/", "/memory/", "/.claude/state/next_step_src.json")
NOT_USER = ("Stop hook feedback", "<task-notification>", "<system-reminder>", "This session is being continued",
            "[Request interrupted")
HEADS = ("【作業内容】", "【目的】", "【経緯】", "【ゴール】")
DECL_RE = re.compile(r"【宣言】\s*ToDo\s*の?\s*(\d+)\s*番")
DOING = "★いまここ"
CHECK_ONLY = re.compile(r"--selftest|--verify|--check|--help|--dry\b|py_compile|try_hooks\.py|next_move\.py")
MIN_BODY = 8                                   # 見出しの後の中身の字数の下限（見出しだけの宣言を通さない）
FILE_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")


def session_id(d: dict):
    sid = d.get("session_id")
    if not (isinstance(sid, str) and sid.strip()):
        tp = str(d.get("transcript_path") or "")
        sid = pathlib.Path(tp).name[:-6] if tp.endswith(".jsonl") else ""
    sid = re.sub(r"[^A-Za-z0-9._-]", "_", (sid or "").strip()).lstrip(".")
    return sid or None


def doing_numbers(todo_text: str) -> list:
    """ToDo の表の、状態が「★いまここ」の行の番号の一覧（表の形＝| 番号 | やること | 状態 | 記録 |）。"""
    out = []
    for line in todo_text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) >= 3 and re.fullmatch(r"\d+", cells[0]) and cells[2] == DOING:
            out.append(cells[0])
    return out


def events(path: pathlib.Path) -> list:
    """戻り＝[("user", None) | ("say", CC の返信の文)] を、記録の順に。サブエージェントの行は数えない。"""
    out = []
    for line in path.open(encoding="utf-8", errors="replace"):
        try:
            o = json.loads(line)
        except Exception:
            continue
        if not isinstance(o, dict) or o.get("isSidechain"):
            continue
        if o.get("type") == "user":
            c = (o.get("message") or {}).get("content")
            if isinstance(c, str):
                texts = [c]
            elif isinstance(c, list):
                texts = [b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text"]
            else:
                texts = []
            if any(t.strip() and not t.lstrip().startswith(NOT_USER) for t in texts):
                out.append(("user", None))
        elif o.get("type") == "assistant":
            for b in (o.get("message") or {}).get("content") or []:
                if isinstance(b, dict) and b.get("type") == "text" and b.get("text"):
                    out.append(("say", b["text"]))
    return out


def decl_problems(text: str, num: str):
    """1つの返信の文が、num 番の宣言として足りているか。戻り＝足りない所の一覧（空＝足りている）／None＝num 番の宣言ではない。"""
    hits = [m for m in DECL_RE.finditer(text) if m.group(1) == num]
    if not hits:
        return None
    body = text[hits[-1].start():]
    pos = [(h, body.find(h)) for h in HEADS]
    probs = []
    for h, p in pos:
        if p < 0:
            probs.append(f"{h} が無い")
            continue
        nxt = min([q for _, q in pos if q > p] + [len(body)])
        if len(re.sub(r"\s", "", body[p + len(h):nxt])) < MIN_BODY:
            probs.append(f"{h} の中身が {MIN_BODY} 字より短い")
    return probs


def check(transcript: pathlib.Path, todo: pathlib.Path):
    """止める理由（文）を返す。通すときは None。"""
    if not todo.exists():
        return f"このセッションの ToDo が無い（{todo}）。ToDo を書き、いまやる1件に「{DOING}」を付ける"
    nums = doing_numbers(todo.read_text(encoding="utf-8", errors="replace"))
    if len(nums) != 1:
        return f"ToDo の「{DOING}」が {len(nums)} 件（ちょうど1件にする）＝{todo}"
    num = nums[0]
    ev = events(transcript)
    last = None                                # いちばん新しい num 番の宣言の（場所, 足りない所）
    for i, e in enumerate(ev):
        if e[0] != "say":
            continue
        probs = decl_problems(e[1], num)
        if probs is None:
            continue
        if not probs and any(x[0] == "user" for x in ev[i + 1:]):
            return None                        # 足りている宣言が在り、その後に まこさんの発言が在る
        last = (i, probs)
    if last is None:
        return f"ToDo の {num}番の宣言が、CC の返信に無い"
    if last[1]:
        return f"ToDo の {num}番の宣言が足りない＝" + "／".join(last[1])
    return f"ToDo の {num}番の宣言の後に、まこさんの返事が まだ無い"


def gate(d: dict):
    """止める理由（文）を返す。通すときは None。"""
    if d.get("agent_type"):
        return None                            # サブエージェントは通す
    name, inp = d.get("tool_name"), d.get("tool_input") or {}
    if name not in ACT_TOOLS or is_read(name, inp):
        return None
    p = str(inp.get("file_path") or inp.get("notebook_path") or "")
    if name in FILE_TOOLS and any(k in p for k in FREE):
        return None
    if name == "Bash":
        cmd = str(inp.get("command", ""))
        if re.search(r"\bpython[0-9.]*\s", cmd) and CHECK_ONLY.search(cmd) and "--write" not in cmd:
            return None                        # 検査だけの実行は通す
        if re.search(r"\bpython[0-9.]*\s+\S*tidy_next_step\.py(\s|$)", cmd):
            return None                        # ★2026-10-12＝引き継ぎの文書（next_step）を作り直す操作は、記録と同じ扱いで通す
    tp, sid = d.get("transcript_path"), session_id(d)
    if not tp or not sid or not pathlib.Path(tp).exists():
        return None                            # 記録が読めないときは止めない（判定できないため）
    return check(pathlib.Path(tp), SESSIONS / sid / "session_todo.md")


def hook() -> int:
    try:
        d = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return 0
    reason = gate(d if isinstance(d, dict) else {})
    if not reason:
        return 0
    print(f"🔒 [宣言が無い・hook require_work_declaration] {reason}\n"
          "   ToDo の1件を始める前に、返信に次の形で宣言を書き、まこさんの返事の後に作業を始めてください"
          "（まこさん指示 2026-10-12）。\n"
          "     【宣言】ToDo の N番\n     【作業内容】…\n     【目的】…\n     【経緯】…\n     【ゴール】…\n"
          "   止めないもの＝読む操作・検査だけの実行・ToDo と worklog と memory への書き込み。\n"
          "   同じ操作を打ち直しても通りません（宣言と返事がそろうまで）。", file=sys.stderr)
    return 2


# ── 見本の記録で試す ─────────────────────────────────────────────
def _say(t):
    return json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": t}]}}, ensure_ascii=False)


def _user(t):
    return json.dumps({"type": "user", "message": {"content": t}}, ensure_ascii=False)


def _result():
    return json.dumps({"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok"}]}},
                      ensure_ascii=False)


def selftest() -> int:
    decl3 = ("【宣言】ToDo の 3番\n【作業内容】設計書の元の形の直す所を一覧にする\n【目的】どの工事でも同じ形で設計書を作れるようにする\n"
             "【経緯】171回目に項目の表が固まり、172回目に続きを進める\n【ゴール】直す所の一覧を返信に出して止まる")
    todo3 = "| 番号 | やること | 状態 | 記録 |\n|---|---|---|---|\n| 2 | 前の件 | ✅済 | §1 |\n| 3 | いまの件 | ★いまここ | — |\n| 4 | 次の件 | まだ | — |\n"
    ng = 0
    with tempfile.TemporaryDirectory() as td:
        tdp = pathlib.Path(td)
        tr, todo = tdp / "t.jsonl", tdp / "session_todo.md"

        def run(name, lines, todo_text, want_block, d=None):
            nonlocal ng
            tr.write_text("\n".join(lines) + "\n", encoding="utf-8")
            if todo_text is None:
                todo.unlink(missing_ok=True)
            else:
                todo.write_text(todo_text, encoding="utf-8")
            got = check(tr, todo) if d is None else gate(d)
            ok = bool(got) == want_block
            ng += 0 if ok else 1
            print(f"  {'✅' if ok else '❌'} {name}＝{'止まる' if got else '通る'}" + (f"（{got[:50]}）" if got else ""))

        run("T1 ToDo が無い → 止まる", [_user("始めて")], None, True)
        run("T2 宣言が無い → 止まる", [_user("始めて"), _say("読みました")], todo3, True)
        run("T3 宣言は在るが、返事が無い → 止まる", [_user("始めて"), _say(decl3)], todo3, True)
        run("T4 宣言の後に返事が在る → 通る", [_user("始めて"), _say(decl3), _user("OK")], todo3, False)
        run("T5 別の番号の宣言 → 止まる", [_user("始めて"), _say(decl3.replace("3番", "2番")), _user("OK")], todo3, True)
        run("T6 ゴールが無い宣言 → 止まる", [_say(decl3.split("【ゴール】")[0]), _user("OK")], todo3, True)
        run("T7 見出しだけの宣言 → 止まる",
            [_say("【宣言】ToDo の 3番\n【作業内容】\n【目的】\n【経緯】\n【ゴール】"), _user("OK")], todo3, True)
        run("T8 宣言の後が、道具の結果と hook の差し戻しだけ → 止まる",
            [_say(decl3), _result(), _user("Stop hook feedback: やり直し")], todo3, True)
        run("T9 ★いまここ が2件 → 止まる", [_say(decl3), _user("OK")], todo3.replace("まだ", "★いまここ"), True)
        base = {"transcript_path": str(tr), "session_id": "x"}
        run("T10 読むだけの Bash → 通る", [_user("始めて")], None, False,
            dict(base, tool_name="Bash", tool_input={"command": "grep -n abc file.md"}))
        run("T11 ToDo のファイルへの書き込み → 通る", [_user("始めて")], None, False,
            dict(base, tool_name="Write", tool_input={"file_path": str(SESSIONS / "x" / "session_todo.md")}))
        run("T12 検査だけの実行 → 通る", [_user("始めて")], None, False,
            dict(base, tool_name="Bash", tool_input={"command": "python3 .claude/tools/tidy_next_step.py --selftest"}))
        run("T13 宣言なしで、ふつうのファイルへの書き込み → 止まる", [_user("始めて")], None, True,
            dict(base, tool_name="Edit", tool_input={"file_path": "/tmp/a.py"}))
    print(f"  {'✅' if not ng else '❌'} 見本の記録で試した 13件のうち、期待と違う {ng} 件")
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else hook())
