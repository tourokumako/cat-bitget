#!/usr/bin/env python3
# require_trial_before_proposal.py — 設計書の案（【4-0 …】のような見出しの節）を出す前に、試しの設計書で全部の検査を通させる（Stop hook）
#
# まこさん指示（2026-09-30・逐語）＝「なんども同じ確認してるけど、一回の確認で全部のミスを見つけられるようにしろ」
#   「すべて当てずっぽうで当たるまでやり続けるから遅いんだよ。わかる？」「一回の確認ですべて完全に修正できるように強制しろ」
#
# なぜ要るか（worklog 20260930 §44〜§49）＝私は案を出して OK をいただいてから、初めて道具で設計書を作って検査にかけていた。
#   そのため OK のたびに次の穴が見つかり、作り直し・OK・承認が何回も要った（工事 cp53-fix-20260930 で4回）。
# 何をするか＝このターンの返信に、設計書の案の見出し（行の頭の【数字…】）が在れば、
#   ①trial_design.py の記録（.claude/state/sessions/<セッション>/trial_last.json）が在る
#   ②その記録が ok（試しの設計書が作れ、承認の前の検査の A群0件・古い事実の語0件）
#   ③返信の案の節の行が全部、その記録の下書きに在る（試したものと違う案を出していない）
#   の3つがそろわなければ、ターンを終われない。
# 限界（正直に）＝見出しの形（行の頭の【数字】）でしか案を見分けない。古い事実の語は私が選ぶ。中身の正しさは見ない。
import json
import re
import sys
from pathlib import Path

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
HEAD_RE = re.compile(r"^\s*【(\d+(?:-\d+[A-Za-z]?)?)\s[^】]*】\s*$")


def proposal_lines(text: str) -> list:
    out, inside, fence = [], False, False
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("```"):
            fence = not fence
            if inside:
                out.append(s)
            continue
        if HEAD_RE.match(ln):
            inside = True
            out.append(s)
            continue
        if inside and not fence and (s.startswith("**") or s.startswith("---") or s.startswith("#")):
            inside = False
            continue
        if inside and s:
            out.append(s)
    return out


def check(text: str, sid: str) -> list:
    lines = proposal_lines(text)
    if not lines:
        return []
    rp = Path(ROOT) / ".claude/state/sessions" / (sid or "_nosession") / "trial_last.json"
    how = (f"python3 {ROOT}/.claude/hooks/trial_design.py --work <工事名> --draft <案の下書き.txt> "
           f"--session {sid} --stale <古い事実の語をカンマで>")
    if not rp.exists():
        return [f"案を出す前に、試しの設計書で全部の検査を通していない（記録が無い）。走らせる: {how}"]
    rec = json.loads(rp.read_text(encoding="utf-8"))
    bad = []
    if not rec.get("ok"):
        bad.append(f"試しの設計書が検査を通っていない（A群 {len(rec.get('a_bad') or [])} 件・古い語 {len(rec.get('stale') or [])} 件）。直して走らせ直す: {how}")
    have = {ln.strip() for ln in (rec.get("draft") or "").splitlines() if ln.strip()}
    miss = [ln for ln in lines if ln not in have]
    if miss:
        bad.append(f"返信の案の行のうち {len(miss)} 行が、試した下書きに無い（最初＝「{miss[0][:60]}」）。案を下書きに書いて試し直す: {how}")
    return bad


def main() -> int:
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except Exception:                                        # noqa: BLE001
        return 0
    sys.path.insert(0, ROOT + "/.claude/hooks")
    import require_design_check_before_approval as rd
    text = rd._turn_text(data)
    try:
        body = json.loads(text.split("\n", 1)[0]) if text.startswith("{") else None
        if body is not None:
            text = text.split("\n", 1)[1] if "\n" in text else ""
    except Exception:                                        # noqa: BLE001
        pass
    bad = check(text, data.get("session_id") or "")
    if not bad:
        return 0
    print("🔒 [案を出す前の試し] 設計書の案を、試しの設計書で全部の検査に通してから出してください"
          "（まこさん指示 2026-09-30「一回の確認ですべて完全に修正できるように強制しろ」）:", file=sys.stderr)
    for b in bad:
        print("   " + b, file=sys.stderr)
    return 2


if __name__ == "__main__":
    if "--try" in sys.argv:
        i = sys.argv.index("--try")
        for b in check(Path(sys.argv[i + 1]).read_text(encoding="utf-8"), sys.argv[i + 2]) or ["（止める所なし）"]:
            print(b)
        sys.exit(0)
    sys.exit(main())
