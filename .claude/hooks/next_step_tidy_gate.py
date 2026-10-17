#!/usr/bin/env python3
"""next_step_tidy_gate.py — enforce_next_step_tidy.sh の1つ目の照らし（next_step の形）の判定
（2026-10-17・187回目・まこさん「要として３つを修正する」「OK」・直す前と後の行＝.claude/state/hook_fix_proposals/enforce_next_step_tidy_20261017.md）

なぜ在るか＝10月7日から10月17日に、この照らしは13回止めた（やり取りの記録から数えた）。
  ・教訓の件数 (l) で4回。直し方は tidy_next_step.py --write の1つだけで、CC が判断する所が無い。
    10月7日の監査人のセッションは、別のセッションが足した教訓のために3回続けて止められた。
  ・0-1 の日付 (b) で7回。7回とも、セッションの途中で日付が変わり、CC がその日の worklog を作った直後だった。
    CC は作業を中断して「いまの状態」を書き直し、締めでもう一度 書き直していた。
決まり＝
  ・通らない理由が (c) (0-b-2)・(l) 教訓の件数・(m) 監査の写し の3種類だけなら、--write を打ってから検査し直す
    （10月7日の まこさん「案 A で修正する」＝(c) だけ、を広げた）。
  ・(b) の「0-1 の日付が、いちばん新しい worklog の日付と違う」は、そのセッションの ToDo の「★いまここ」が
    締めの行（やることが「締め」で始まる行）に在るときだけ止める。見出しが無い・日付が無い、はいつでも止める。
  ・ほかの理由（CC が文を書く所）が1つでも在れば、今までどおり止める。理由の行が読めないときも止める。
防げない物＝締めをせずにセッションが切れると、0-1 は前の日付のまま残る。ToDo の無いセッションでは 0-1 の日付で止めない。

使い方＝enforce_next_step_tidy.sh が、hook の入力（JSON）を標準入力に渡して呼ぶ。exit 0＝通す／2＝止める。
        --selftest＝判定の例を当てる（本物のファイルは触らない）。
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TOOL = ROOT / ".claude" / "tools" / "tidy_next_step.py"
SESSIONS = ROOT / ".claude" / "state" / "sessions"
DOING = "★いまここ"
BULLET = re.compile(r"^\s*・")
AUTO = re.compile(r"^\s*・(\(c\) \(0-b-2\) |\(l\) |\(m\) )")                          # --write で直る3種類
# ★2026-10-18（190回目）＝next_step を組み替え、「0-1 いまの状態」は「3-1 いまの状態」になった。検査の文も「3-1 の日付」に変わったので、両方を読む。
DATE = re.compile(r"^\s*・\(b\) (?:0-1|3-1) の日付 \S+ が、いちばん新しい worklog の日付 ")      # 締めのときだけ止める


def session_id(d: dict) -> str | None:
    sid = d.get("session_id")
    if not (isinstance(sid, str) and sid.strip()):
        tp = str(d.get("transcript_path") or "")
        sid = pathlib.Path(tp).name[:-6] if tp.endswith(".jsonl") else ""
    sid = re.sub(r"[^A-Za-z0-9._-]", "_", (sid or "").strip()).lstrip(".")
    return sid or None


def closing(todo_text: str) -> bool:
    """ToDo の表（| 番号 | やること | 状態 | … |）で、状態が「★いまここ」の行の、やることが「締め」で始まるか。"""
    for line in todo_text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) >= 3 and re.fullmatch(r"\d+", cells[0]) and cells[2] == DOING and cells[1].startswith("締め"):
            return True
    return False


def judge(out: str, is_closing: bool) -> str:
    """検査の出力（通らなかったとき）から、"pass"（通す）・"write"（--write してから見直す）・"block"（止める）を決める。"""
    bl = [l for l in out.splitlines() if BULLET.match(l)]
    if not bl:
        return "block"
    keep = [l for l in bl if is_closing or not DATE.match(l)]
    if not keep:
        return "pass"
    if all(AUTO.match(l) for l in keep):
        return "write"
    return "block"


def _verify() -> tuple[str, int]:
    r = subprocess.run([sys.executable, str(TOOL), "--verify"], capture_output=True, text=True)
    return (r.stdout + r.stderr), r.returncode


def _is_closing(raw: str) -> bool:
    try:
        d = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        d = {}
    sid = session_id(d) if isinstance(d, dict) else None
    todo = SESSIONS / sid / "session_todo.md" if sid else None
    return bool(todo and todo.exists() and closing(todo.read_text(encoding="utf-8")))


def main() -> int:
    is_closing = _is_closing(sys.stdin.read())
    out, rc = _verify()
    if rc == 0:
        print(out, end="")
        return 0
    j = judge(out, is_closing)
    if j == "write":
        subprocess.run([sys.executable, str(TOOL), "--write"], capture_output=True, text=True)
        out, rc = _verify()
        if rc == 0:
            print(out, end="")
            return 0
        j = judge(out, is_closing)
    if j == "pass":
        print("（3-1 いまの状態 の日付が、いちばん新しい worklog の日付と違います。締めのときに書き直してください。いまは止めません）")
        return 0
    print(out, end="")
    return 2


# ── わざと壊して止まるか試すテスト（本物のファイルは触らない）────────────────────────
HEAD = "❌ [tidy --verify] next_step.md の形に 1 件:\n"
# 10月7日〜10月17日に実際に止めた文（やり取りの記録から写した）
R_DATE = "   ・(b) 0-1 の日付 2026-10-16 が、いちばん新しい worklog の日付 2026-10-17 と違う → 0-1 を今日の状態に書き直す"
R_LES = "   ・(l) 教訓の現役が 42 件（上限 40 件＋名指しされた物）→ `--write` で 1 件を控えへ移す"
R_C = ("   ・(c) (0-b-2) の H2 の印が json（45d6f6b65a484db9…）と違う → `--write`\n"
       "   ・(c) (0-b-2) の G2 の印が json（22cd08eb26ae523f…）と違う → `--write`\n"
       "   ・(c) (0-b-2) の H2 の時刻が json（2026-10-10 11:09:23）と違う → `--write`\n"
       "   ・(c) (0-b-2) の G2 の時刻が json（2026-10-10 11:04:19）と違う → `--write`")
R_G = ("   ・(g) 本文が元データ next_step_src.json から作ったものと違う → 元データを直して `--write`／最初に違う所＝790行目\n"
       "     作り直し＝| **253** | …")
R_M = "   ・(m) 結果が出た監査の写しが 2 個 残っている → `--write` で消す／1つ目＝v3-bitget-api-sdk/x"
R_NODATE = "   ・(b) 0-1 の見出しに日付（YYYY-MM-DD）が無い"
# ★2026-10-18（190回目）＝組み替えた後に tidy_next_step.py が出す文（3-1）
R_DATE31 = "   ・(b) 3-1 の日付 2026-10-17 が、いちばん新しい worklog の日付 2026-10-18 と違う → 3-1 いまの状態 を今日の状態に書き直す"
R_NODATE31 = "   ・(b) 3-1 いまの状態 の見出しに日付（YYYY-MM-DD）が無い"
TODO = "| 番号 | やること | 状態 | 記録 |\n|---|---|---|---|\n| 35 | hook を1本ずつ | {a} | — |\n| 41 | 締め（worklog・next_step） | {b} | — |\n"


def selftest() -> int:
    cases = [
        ("途中の回の 0-1 の日付だけ（実際に7回 止めた形）→ 通す", judge(HEAD + R_DATE, False), "pass"),
        ("締めの回の 0-1 の日付 → 止める", judge(HEAD + R_DATE, True), "block"),
        ("教訓の件数だけ（実際に4回 止めた形）→ 直してから見直す", judge(HEAD + R_LES, False), "write"),
        ("(0-b-2) の欄だけ（10月7日の案 A）→ 直してから見直す", judge(HEAD + R_C, False), "write"),
        ("監査の写しだけ → 直してから見直す", judge(HEAD + R_M, False), "write"),
        ("(0-b-2) と本文の違いが混ざる（10月10日に止めた形）→ 止める", judge(HEAD + R_C + "\n" + R_G, False), "block"),
        ("(0-b-2) と 0-1 の日付が混ざる・途中の回 → 直してから見直す", judge(HEAD + R_C + "\n" + R_DATE, False), "write"),
        ("(0-b-2) と 0-1 の日付が混ざる・締めの回 → 止める", judge(HEAD + R_C + "\n" + R_DATE, True), "block"),
        ("見出しに日付が無い・途中の回 → 止める", judge(HEAD + R_NODATE, False), "block"),
        ("組み替えた後の 3-1 の日付だけ・途中の回 → 通す", judge(HEAD + R_DATE31, False), "pass"),
        ("組み替えた後の 3-1 の日付・締めの回 → 止める", judge(HEAD + R_DATE31, True), "block"),
        ("組み替えた後の 3-1 の見出しに日付が無い → 止める", judge(HEAD + R_NODATE31, False), "block"),
        ("理由の行が読めない → 止める", judge("Traceback (most recent call last):\n  ...", False), "block"),
        ("締めの行に ★いまここ → 締め", closing(TODO.format(a="✅済", b=DOING)), True),
        ("ほかの行に ★いまここ → 締めでない", closing(TODO.format(a=DOING, b="まだ")), False),
        ("★いまここ が無い → 締めでない", closing(TODO.format(a="まだ", b="まだ")), False),
        ("セッションの id が無い入力 → 締めでない", _is_closing("{}"), False),
        ("JSON でない入力 → 締めでない", _is_closing("x"), False),
    ]
    ng = 0
    for name, got, want in cases:
        ok = got == want
        ng += 0 if ok else 1
        print(f"{'✅' if ok else '❌'} {name}（結果 {got!r}・期待 {want!r}）")
    print(f"[selftest] {len(cases) - ng}/{len(cases)}")
    return 0 if ng == 0 else 1


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        raise SystemExit(selftest())
    raise SystemExit(main())
