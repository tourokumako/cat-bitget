#!/usr/bin/env python3
"""require_confirm_before_act — まこさんの定義の「確認」をしてから動き、確かめてから終えさせる（2026-10-01 新設・142回目に作り直し）。

まこさんの「確認」の定義（逐語 2026-10-01）＝「確認とは これからやることが正しいと、根拠をもって確かめること
そのために該当箇所を開いて、内容を把握、理解をし、正しく機能をする対処方法であるか、証拠をつかんでから対応する」。

★142回目に作り直した理由（まこさん「開くだけは確認ではない」「これを本来の目的通りの機能に修正しろ」）
  直す前は、confirm.md に私が書く3行（対象・根拠・なぜ）と、根拠のファイルを「どこかで開いた記録」だけで通した。
  私が書く文は中身が無くても書け、開く記録は直す所と関係の無いファイルでも作れた＝確認にならず、トークンだけを使わせた。

証拠にするのは記録に残る物だけ（私が書く文は証拠にしない）。まこさんの最後の発言より後だけを数える。
  pre（PreToolUse Write|Edit|MultiEdit|NotebookEdit|Bash）＝定義の「該当箇所を開いて」「証拠をつかんでから対応する」
    1. Edit・MultiEdit＝直す前の文字が在る行を、開いた範囲が含んでいる（Read の範囲か、その名前を含む読むだけの Bash）。
    2. Write・NotebookEdit で既に在るファイル＝そのファイルを開いている。
    3. Bash で .py・.sh を走らせる＝その .py・.sh を開いている。
    4. 既に在る .py・.sh を書き替える＝その前に、それを走らせて いまの働きを見ている。
    ★1〜3 は一度 外したが誤りだった＝無意味なのは関係の無い物を開かせることと、開いた中身を使わないこと。
      該当箇所を開くことは確認の中心（まこさん「なにも見ずにすべて思いつきの当てずっぽうで対応しつづけるしかできないってこと？」）。
  stop（Stop）＝定義の「正しく機能をする対処方法であるか」
    5. 書き替えた .py・.sh ごとに、最後の書き替えの後に それを走らせて成功している。無ければ終わらせない（1ターン1回）。
  定義の「内容を把握、理解」は機械に見えない＝Stop の require_read_used が、返信に「どの行を根拠にしたか」を示させる。
見ないもの＝新しく作るファイルの 1〜4／置き場・worklog・計画・memory・下書き／.py・.sh・.json 以外の書き替え／
  .py・.sh を走らせない Bash（git・jq・grep など）／Agent。
限界＝把握・理解したか・走らせ方が確かめとして十分かは見ない。

使い方: （hook）引数 pre か stop ＋ 標準入力に JSON ／ --selftest ／ --replay <日数>（直近の記録に流して数える・何も止めない）
"""
import json
import pathlib
import re
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from require_check_after_failure import is_read            # 読むだけの Bash の見分け方を同じものにする

FREE = ("/.claude/state/sessions/", "session_worklog_", "/.claude/plans/", "/memory/", "chat_draft.md")
NOT_USER = ("Stop hook feedback", "<task-notification>", "<system-reminder>", "This session is being continued")
CODE_EXT = (".py", ".sh", ".json")
RUN_EXT = (".py", ".sh")
EDIT = ("Write", "Edit", "MultiEdit", "NotebookEdit")
READ_MAX = 2000
RUN = re.compile(r"(?:^|[;&|(\s])(?:python3?|bash|sh)\s+(?:-\S+\s+)*([^\s;&|]+\.(?:py|sh))\b")


def user_text(o) -> str:
    """まこさんの発言の文（hook の差し戻しや知らせは数えない）。（require_read_used も使う）"""
    c = (o.get("message") or {}).get("content")
    if isinstance(c, str):
        return c if c.strip() and not c.lstrip().startswith(NOT_USER) else ""
    if isinstance(c, list):
        ts = [b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text"]
        return "\n".join(t for t in ts if t.strip() and not t.lstrip().startswith(NOT_USER))
    return ""


def run_target(cmd: str):
    """Bash のコマンドが走らせる .py・.sh のパス（python3・bash・sh の直後に書いた物）。無ければ None。"""
    m = RUN.search(re.sub(r"'[^']*'|\"[^\"]*\"", "", str(cmd or "")))
    return m.group(1) if m else None


def _load(path) -> list:
    objs = []
    for ln in pathlib.Path(path).open(encoding="utf-8", errors="replace"):
        try:
            objs.append(json.loads(ln))
        except Exception:
            continue
    return objs


def events(objs) -> list:
    """並び＝[("user",) | ("use", id, 名前, 入力) | ("result", id, 失敗か)]。"""
    ev = []
    for o in objs:
        if o.get("type") == "user" and user_text(o):
            ev.append(("user",))
            continue
        for b in (o.get("message") or {}).get("content") or []:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use":
                ev.append(("use", b.get("id"), b.get("name"), b.get("input") or {}))
            elif b.get("type") == "tool_result":
                ev.append(("result", b.get("tool_use_id"), bool(b.get("is_error"))))
    return ev


def since_user(ev: list) -> list:
    last = max((i for i, e in enumerate(ev) if e[0] == "user"), default=-1)
    return ev[last + 1:]


def _norm(p: str) -> str:
    try:
        return str(pathlib.Path(p).expanduser().resolve())
    except Exception:
        return str(p)


def _opened(ev: list, path: str):
    """path を開いた範囲の一覧（Read＝その範囲・読むだけの Bash でその名前を含む＝全部）。"""
    out, base = [], pathlib.Path(path).name
    for e in ev:
        if e[0] != "use":
            continue
        if e[2] == "Read" and _norm(str(e[3].get("file_path") or "")) == path:
            lo = max(int(e[3].get("offset") or 1), 1)
            out.append((lo, lo + int(e[3].get("limit") or READ_MAX) - 1))
        elif e[2] == "Bash" and is_read("Bash", e[3]) and base in str(e[3].get("command", "")):
            out.append((1, 10 ** 9))
    return out


def _ran(ev: list, path: str, start: int = 0, ok_only: bool = False) -> bool:
    failed = {e[1] for e in ev if e[0] == "result" and e[2]}
    base = pathlib.Path(path).name
    for i, e in enumerate(ev):
        if i >= start and e[0] == "use" and e[2] == "Bash":
            t = run_target(e[3].get("command"))
            if t and pathlib.Path(t).name == base and (not ok_only or e[1] not in failed):
                return True
    return False


def _span(text: str, old: str):
    i = text.find(old) if old else -1
    if i < 0:
        return None
    a = text.count("\n", 0, i) + 1
    return a, a + old.count("\n")


def check_pre(ev: list, name: str, inp: dict) -> list:
    """止める理由（空なら通す）。ev はまこさんの最後の発言より後の並び。"""
    # ★2026-10-01（142回目）＝定義の「該当箇所を開いて」＝直す行・書き替えるファイル・走らせる物を開いたかを見る（1〜3）。
    #   一度 外したが誤りだった（まこさん「お前はこれから、なにも見ずにすべて思いつきの当てずっぽうで対応しつづけるしかできないってこと？」）。
    #   無意味だったのは、関係の無い物を開かせることと、開いた中身を使わないこと。該当箇所を開くことは確認の中心。
    ng = []
    if name == "Bash":
        t = run_target(inp.get("command"))
        if not t:
            return []
        p = pathlib.Path(t) if pathlib.Path(t).is_absolute() else pathlib.Path.cwd() / t
        if p.exists() and not any(k in str(p) for k in FREE) and not _opened(ev, _norm(str(p))):
            ng.append(f"[3] {p.name} を走らせる前に、まこさんの最後の発言の後に開いていない＝走らせる物を開いて把握してから走らせる")
        return ng
    if name not in EDIT:
        return []
    fp = str(inp.get("file_path") or inp.get("notebook_path") or "")
    if not fp or any(k in fp for k in FREE) or not fp.endswith(CODE_EXT):
        return []
    p = pathlib.Path(fp)
    if not p.exists():
        return []                                         # 新しく作るファイル
    path = _norm(fp)
    ranges = _opened(ev, path)
    if name in ("Edit", "MultiEdit"):
        text = p.read_text(encoding="utf-8", errors="replace")
        olds = [inp.get("old_string")] if name == "Edit" else [x.get("old_string") for x in (inp.get("edits") or [])]
        for old in olds:
            sp = _span(text, str(old or ""))
            if sp and not any(lo <= sp[0] and sp[1] <= hi for lo, hi in ranges):
                ng.append(f"[1] {p.name} の直す行（{sp[0]}〜{sp[1]}行）を、まこさんの最後の発言の後に開いていない＝その行を開いて把握してから直す")
    elif not ranges:
        ng.append(f"[2] {p.name} を書き替える前に、まこさんの最後の発言の後に開いていない＝開いて把握してから書き替える")
    if p.suffix in RUN_EXT and not _ran(ev, path):
        ng.append(f"[4] {p.name} を直す前に、走らせて いまの働きを確かめていない＝先に走らせる（例 python3 {p} --selftest）")
    return ng


def check_stop(ev: list) -> list:
    last: dict = {}
    for i, e in enumerate(ev):
        if e[0] == "use" and e[2] in EDIT:
            fp = str(e[3].get("file_path") or e[3].get("notebook_path") or "")
            if fp.endswith(RUN_EXT) and not any(k in fp for k in FREE):
                last[_norm(fp)] = i
    return [f"{pathlib.Path(fp).name} を書き替えた後に、走らせて成功した記録が無い＝走らせて正しく働くことを確かめてから終える（{fp}）"
            for fp, i in last.items() if not _ran(ev, fp, i + 1, ok_only=True)]


def hook(mode: str) -> int:
    try:
        d = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return 0
    if d.get("agent_type"):
        return 0
    tp = d.get("transcript_path")
    if not tp or not pathlib.Path(tp).exists():
        return 0
    ev = since_user(events(_load(tp)))
    if mode == "stop":
        if d.get("stop_hook_active"):
            return 0                                       # 1つのターンで止めるのは1回だけ
        ng = check_stop(ev)
    else:
        ng = check_pre(ev, d.get("tool_name"), d.get("tool_input") or {})
    if not ng:
        return 0
    print("🔒 [確認してから動く] 該当箇所を開き、走らせて働きを確かめてから動く・終える（証拠は記録に残る開いた範囲と走らせた結果だけ）",
          file=sys.stderr)
    for x in ng:
        print("   ・" + x, file=sys.stderr)
    print("   まこさんの定義（2026-10-01）「これからやることが正しいと、根拠をもって確かめること…証拠をつかんでから対応する」",
          file=sys.stderr)
    return 2


def selftest() -> int:
    me = _norm(__file__)
    text = pathlib.Path(me).read_text(encoding="utf-8")
    old = "def _span(text: str, old: str):"
    a, b = _span(text, old)
    rd = lambda lo, hi: ("use", "x", "Read", {"file_path": me, "offset": lo, "limit": hi - lo + 1})
    run = ("use", "r1", "Bash", {"command": f"python3 {me} --selftest"})
    ed = {"file_path": me, "old_string": old, "new_string": old}
    cases = [
        ("P1 何も開かず走らせずに直す → 止まる", "pre", [], "Edit", ed, False),
        ("P2 関係の無い範囲だけ開いた → 止まる", "pre", [rd(1, 5), run], "Edit", ed, False),
        ("P3 直す行を開いたが走らせていない → 止まる", "pre", [rd(a, b)], "Edit", ed, False),
        ("P4 直す行を開き、走らせた → 通る", "pre", [rd(a, b), run, ("result", "r1", False)], "Edit", ed, True),
        ("P5 新しいファイル → 通る", "pre", [], "Write", {"file_path": me + ".zz_new.py"}, True),
        ("P6 .md は見ない → 通る", "pre", [], "Edit", {"file_path": me[:-3] + ".md", "old_string": "x"}, True),
        ("P7 開いていない .py を走らせる → 止まる", "pre", [], "Bash", {"command": f"python3 {me} --selftest"}, False),
        ("P8 開いた .py を走らせる → 通る", "pre", [rd(1, 3)], "Bash", {"command": f"python3 {me} --selftest"}, True),
        ("P9 .py を走らせない Bash → 通る", "pre", [], "Bash", {"command": "git status"}, True),
        ("S1 直した後に走らせていない → 止まる", "stop", [("use", "e", "Edit", ed)], None, None, False),
        ("S2 直した後に走らせて成功 → 通る", "stop", [("use", "e", "Edit", ed), run, ("result", "r1", False)], None, None, True),
        ("S3 直した後に走らせて失敗だけ → 止まる", "stop", [("use", "e", "Edit", ed), run, ("result", "r1", True)], None, None, False),
    ]
    bad = 0
    for nm, mode, ev, tool, inp, want in cases:
        ok = ((not check_pre(ev, tool, inp)) if mode == "pre" else (not check_stop(ev))) == want
        bad += not ok
        print(f"  {'✅' if ok else '❌'} {nm}")
    print(f"自己テスト {len(cases) - bad}/{len(cases)}")
    return 1 if bad else 0


def replay(days: int) -> int:
    """直近の記録に流して、止まる回数を数える（何も止めない）。★書き替えの前の止めは、いまのファイルで行を探すので目安。"""
    proj = pathlib.Path.home() / ".claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget"
    cut = time.time() - days * 86400
    n_act = n_pre = n_stop = n_turn = 0
    by: dict = {}
    for f in [p for p in proj.glob("*.jsonl") if p.stat().st_mtime >= cut]:
        ev = events(_load(f))
        seg: list = []
        for e in ev + [("user",)]:
            if e[0] == "user":
                if seg:
                    n_turn += 1
                    n_stop += bool(check_stop(seg))
                seg = []
                continue
            if e[0] == "use" and (e[2] in EDIT or e[2] == "Bash"):
                n_act += 1
                got = check_pre(seg, e[2], e[3])
                n_pre += bool(got)
                for x in got:
                    by[x[:3]] = by.get(x[:3], 0) + 1
            seg.append(e)
    print(f"直近 {days} 日＝書き替えと Bash {n_act} 回のうち、前で止まる {n_pre} 回／指示 {n_turn} 回のうち、終わりで止まる {n_stop} 回")
    print("  止めごと＝" + " ／ ".join(f"{k} {v}回" for k, v in sorted(by.items())))
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    if "--replay" in sys.argv:
        sys.exit(replay(int(sys.argv[sys.argv.index("--replay") + 1])))
    sys.exit(hook(sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in ("pre", "stop") else "pre"))
