#!/usr/bin/env python3
"""require_counted_number — count_items.py の記録に無い数を止める（ToDo の273番・恒久の決まり83番）。

まこさん 2026-11-05「今後あらゆる場面での数の数え間違いをふせぐように言ったんだけど」「ok」。
★2026-11-05 の時点で settings.json に登録していない。過去の記録で止まる回数を測ってから決める。

止める物＝ターンの最後の返信（Stop）と、手で書く文書（PreToolUse の Write・Edit）の中の数で、
  そのセッションの .claude/state/sessions/<id>/counted.jsonl に無い物。
  まこさんの最後の発言に在る数は止めない。
外す物＝コード・引用・リンク・日付・時刻・行番号・ToDo の番号・節の番号・箇条書きの番号・英字とつながった名前。
限界＝記録の数と同じ数字なら、別の物の数でも通る。

調べの口＝--scan <やり取りの記録>…（止める回数の測定。何も止めない・書かない）。
"""
import json
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = re.compile(r"(session_worklog_\d+\.md|/acceptance\.md|_design\.md|/\.claude/instructions/.+\.md|/audits/inputs/.+\.md)$")

STRIP = [
    re.compile(r"```.*?```", re.S),                     # コード
    re.compile(r"`[^`\n]*`"),
    re.compile(r"^\s*>.*$", re.M),                      # 引用
    re.compile(r"「[^」\n]*」"),
    re.compile(r"\[[^\]\n]*\]\([^)\n]*\)"),             # リンク
    re.compile(r"https?://\S+"),
    re.compile(r"\d{4}[-/年]\d{1,2}([-/月]\d{1,2}日?)?"),   # 日付
    re.compile(r"\b\d{1,2}-\d{1,2}\b"),
    re.compile(r"\d{1,2}月\d{1,2}日|\d{1,2}月|\d{1,2}日|\d{1,2}:\d{2}(:\d{2})?|\d{1,2}時\d{0,2}分?"),
    re.compile(r"[0-9A-Za-z_.\-/%]*[A-Za-z_][0-9A-Za-z_.\-/%]*(:\d+([-〜]\d+)?)?"),     # 英字とつながった名前・ファイル名:行番号（\w は日本語も含むので使わない）
    re.compile(r"(?<![：])(?<=[^\s0-9]):\d+([-〜]\d+)?"),    # 行番号（全角の「：」は文の区切りなので外さない）
    re.compile(r"§\s*\d+(-\d+)*"),
    re.compile(r"\d+\s*(番|回目|段目|行目|章|節)"),        # 番号（数えた数ではない）
    re.compile(r"(修正|案|手順|問題点)\s*\d+"),            # 名前としての番号（まこさん 2026-11-05「ok」）
    re.compile(r"^\s*\d+[.)．]\s", re.M),                # 箇条書きの番号
    re.compile(r"^\|\s*\d+\s*\|", re.M),                 # 表の番号の欄
    re.compile(r"[①-⑳]"),
]
NUM = re.compile(r"\d+(?:[,，]\d{3})*(?:\.\d+)?")
SYSTEM = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)
FEEDBACK = "Stop hook feedback:"


def numbers_in(text: str) -> list:
    for p in STRIP:
        text = p.sub(" ", text)
    return [m.group(0).replace(",", "").replace("，", "") for m in NUM.finditer(text)]


def counted(session: str) -> set:
    p = ROOT / ".claude/state/sessions" / (session or "_nosession") / "counted.jsonl"
    if not p.exists():
        return set()
    out = set()
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            out.add(str(json.loads(line)["数"]))
        except (ValueError, KeyError, TypeError):
            continue
    return out


def _texts(content) -> list:
    if isinstance(content, str):
        return [content]
    if isinstance(content, list):
        return [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
    return []


def turns_of(path: str) -> list:
    """[(まこさんの発言, そのターンの最後の返信)]。"""
    out, user, last = [], "", ""
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get("type") == "user":
                t = "\n".join(_texts((d.get("message") or {}).get("content")))
                t = SYSTEM.sub("", t)                   # 仕組みが足す文の数を、まこさんの数に数えない
                if t.lstrip().startswith(FEEDBACK):     # hook の差し戻し＝まこさんの発言ではない。同じターンの続き
                    continue
                if t.strip() and not d.get("isMeta"):
                    if last:
                        out.append((user, last))
                    user, last = t, ""
            elif d.get("type") == "assistant":
                t = "\n".join(_texts((d.get("message") or {}).get("content")))
                if t.strip():
                    last = t
    if last:
        out.append((user, last))
    return out


def unrecorded(text: str, user: str, session: str) -> list:
    known = counted(session) | set(numbers_in(user))
    return sorted({n for n in numbers_in(text) if n not in known}, key=lambda s: float(s))


def doc_writes(path: str) -> tuple:
    """(手で書く文書への書き込みの数, そのうち数字が在る数)。"""
    n = has = 0
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get("type") != "assistant":
                continue
            c = (d.get("message") or {}).get("content")
            for b in c if isinstance(c, list) else []:
                if not (isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") in ("Write", "Edit")):
                    continue
                ti = b.get("input") or {}
                if DOCS.search(ti.get("file_path") or ""):
                    n += 1
                    has += 1 if numbers_in(ti.get("content") or ti.get("new_string") or "") else 0
    return n, has


def scan(paths: list) -> int:
    head = ("記録", "ターン", "数字が在るターン", "数字の中央値", "10以上の数字が在るターン", "表の外に数字が在るターン", "文書への書き込み", "そのうち数字が在る")
    print("\t".join(head))
    total = [0] * 6
    meds = []
    for path in paths:
        rows = turns_of(path)
        nums = [numbers_in(t) for _, t in rows]
        has = sum(1 for n in nums if n)
        big = sum(1 for n in nums if any(float(x) >= 10 for x in n))
        prose = sum(1 for _, t in rows if numbers_in("\n".join(s for s in t.splitlines() if not s.lstrip().startswith("|"))))
        med = statistics.median([len(n) for n in nums]) if nums else 0
        meds.extend(len(n) for n in nums)
        dn, dh = doc_writes(path)
        if len(paths) <= 8:
            print(f"{Path(path).name[:8]}\t{len(rows)}\t{has}\t{med}\t{big}\t{prose}\t{dn}\t{dh}")
        for i, v in enumerate((len(rows), has, big, prose, dn, dh)):
            total[i] += v
    print(f"合計（{len(paths)}本）\t{total[0]}\t{total[1]}\t{statistics.median(meds) if meds else 0}\t{total[2]}\t{total[3]}\t{total[4]}\t{total[5]}")
    return 0


def main() -> int:
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return 0
    session = data.get("session_id") or ""
    tool = data.get("tool_name")
    if tool:                                            # PreToolUse＝手で書く文書
        ti = data.get("tool_input") or {}
        if tool not in ("Write", "Edit") or not DOCS.search(ti.get("file_path") or ""):
            return 0
        text = ti.get("content") or ti.get("new_string") or ""
        user = ""
        rows = turns_of(data["transcript_path"]) if data.get("transcript_path") else []
        if rows:
            user = rows[-1][0]
    else:                                               # Stop＝ターンの最後の返信
        rows = turns_of(data["transcript_path"]) if data.get("transcript_path") else []
        if not rows:
            return 0
        user, text = rows[-1]
    bad = unrecorded(text, user, session)
    if not bad:
        return 0
    print("🔒 [数の出どころ・hook require_counted_number] count_items.py の記録に無い数が在ります＝" + "・".join(bad[:30]),
          file=sys.stderr)
    print("   python3 .claude/tools/count_items.py --session <id> --what <値か行か> --label … --cmd … --check … で数えてから書いてください（恒久の決まり83番）",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--scan":
        sys.exit(scan(sys.argv[2:]))
    sys.exit(main())
