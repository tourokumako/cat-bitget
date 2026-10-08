#!/usr/bin/env python3
"""gen_hook_cheatsheet.py — 「hook に止められる打ち方」と「代わりの打ち方」の早見表を、試しの道具（try_hooks.py）の
実際の判定から作って出す。開始時の hook_health_check.sh が呼ぶ。

★2026-10-08（160回目・まこさん OK の案 3b）
  なぜ要るか＝159回目は、確かめずに打った操作で hook に26回 止められた（python3 -c と python3 - で4回・
  開かずに直そうとして7回・同じ種類の2回目で9回ほか）。試しの道具は76回 使っていたが、止められた操作の前には通していなかった。
  160回目にも、scratchpad の自作 .py を試さずに走らせて止められた。止められる型を、セッションの最初に表で見せる。
何をするか＝下の SAMPLES を try_hooks.run_all に渡し（記録の try_ok.json は書かない）、止めた hook の名前と1行目を表にする。
  代わりの打ち方も Bash のものは同じく試し、通るかを表に書く。結果は .claude/state/hook_cheatsheet.md に置き、
  settings.json と hooks のどれかが変わったときだけ作り直す（作り直しは約20秒・それ以外は表を出すだけ）。

使い方: python3 .claude/tools/gen_hook_cheatsheet.py [--session <id>] [--force]
限界＝試せるのは書く前・走らせる前の hook だけ（ターンの終わりの検査は、下の「試せない決まり」に文で書く）。
  セッションの状態で判定が変わる hook（開いたか・走らせたか）は、試した時点の判定になる。表は止める力を持たない。
"""
from __future__ import annotations

import glob
import hashlib
import os
import sys

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
OUT = os.path.join(ROOT, ".claude/state/hook_cheatsheet.md")
sys.path.insert(0, os.path.join(ROOT, ".claude/tools"))
import try_hooks as th  # noqa: E402


def samples(session: str) -> list:
    """（止められる打ち方の説明, 道具, 入力, 代わりの打ち方の説明, 代わりの Bash か None）"""
    sp = f"/private/tmp/claude-501/-Users-tachiharamasako-Documents-GitHub-cat-bitget/{session or 'x'}/scratchpad/probe.py"
    reps = sorted(glob.glob(os.path.join(ROOT, "v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/*_audit_report.md")))
    rep = reps[-1] if reps else "v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/x_audit_report.md"
    js = "jq 'length' .claude/state/try_ok.json"
    return [
        ("python3 -c で式を走らせる", "Bash", {"command": 'python3 -c "print(1)"'},
         "json は jq で読む", js),
        ("python3 - に heredoc で渡す", "Bash", {"command": "python3 - <<'EOF'\nprint(1)\nEOF"},
         "json は jq で読む", js),
        ("scratchpad の自作 .py を走らせる", "Bash", {"command": f"python3 {sp}"},
         "既存の道具の口（--selftest など）で確かめる。新しい計算は道具の口として足す", "python3 .claude/tools/try_hooks.py --selftest"),
        ("監査の結果ファイルを Bash で grep する", "Bash", {"command": f"grep -n Critical {rep}"},
         "Read で開く", None),
        ("直す範囲を開かず・その .py を走らせずに直す", "Edit",
         {"file_path": os.path.join(ROOT, ".claude/tools/gen_review.py"), "old_string": "import", "new_string": "import "},
         "直す範囲を Read で開き、その .py を単独のコマンド（&& でつながない）で1回 走らせ、try_hooks.py --edit で試してから直す", None),
    ]


STATIC = [
    "日付をまたいだら、worklog は新しい日付のファイルに書く（ターンの終わりの enforce_next_step_tidy.sh が止める）。",
    "試しの道具は、打つのと同じ文字で通す。&& で道具を2つつなぐと、後ろの道具は「走らせた」に数えられない。",
]


def key() -> str:
    h = hashlib.sha256(open(os.path.join(ROOT, ".claude/settings.json"), "rb").read())
    for p in sorted(glob.glob(os.path.join(ROOT, ".claude/hooks/*.sh")) + glob.glob(os.path.join(ROOT, ".claude/hooks/*.py"))
                    + [os.path.abspath(__file__), th.__file__]):
        h.update(p.encode())
        h.update(str(os.path.getmtime(p)).encode())
    return h.hexdigest()[:16]


def build(session: str) -> str:
    rows = ["| 止められる打ち方 | 止めた hook（試した結果） | 代わりの打ち方 | 代わりを試した結果 |", "|---|---|---|---|"]
    for what, tool, tin, alt, alt_cmd in samples(session):
        st = th.run_all(tool, tin, session, ROOT)
        got = "・".join(f"{n}（{(o.splitlines() or [''])[0][:60]}）" for n, o in st) if st else "止めない（通る）"
        if alt_cmd:
            st2 = th.run_all("Bash", {"command": alt_cmd}, session, ROOT)
            alt_got = "通る" if not st2 else "止められる＝" + "・".join(n for n, _ in st2)
        else:
            alt_got = "（Bash ではないので試していない）"
        rows.append(f"| {what} | {got} | {alt}{'（' + alt_cmd + '）' if alt_cmd else ''} | {alt_got} |")
    return "\n".join(rows) + "\n\n試せない決まり（ターンの終わりの検査ほか）:\n" + "\n".join("- " + s for s in STATIC) + "\n"


def main(argv: list) -> int:
    session = argv[argv.index("--session") + 1] if "--session" in argv else ""
    k = key()
    old = open(OUT, encoding="utf-8").read() if os.path.isfile(OUT) else ""
    if "--force" in argv or f"key={k}" not in old.splitlines()[0:1][0] if old else True:
        body = build(session)
        old = f"<!-- HOOK_CHEATSHEET key={k} gen_hook_cheatsheet.py が作った＝手で書き換えない -->\n" + body
        with open(OUT, "w", encoding="utf-8") as f:
            f.write(old)
    print("=== hook に止められる打ち方の早見表（試しの道具の実際の判定・" + OUT + "）===")
    print("\n".join(old.splitlines()[1:]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
