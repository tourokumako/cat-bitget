#!/usr/bin/env python3
"""count_items — 数を数える道具（ToDo の273番・恒久の決まり83番）。

まこさん 2026-11-05「今後あらゆる場面での数の数え間違いをふせぐように言ったんだけど」「ok」。

使い方＝1行に1件を出す命令を --cmd に渡す。数えるのはこの道具で、命令の中では数えない。
  1回だけ数える
    python3 .claude/tools/count_items.py --session <id> --what 値 --label "RSI の閾値の値" \
        --cmd 'jq ... file' --check '別の jq や grep ... file'
  作業の前後を同じ条件で比べる
    作業の前＝ ... --before <名前> --expect-diff -1 --what 行 --label … --cmd … --check …
    作業の後＝ ... --after <名前>   （命令・単位は前に登録した物を使う。変えられない）

止めるもの（どれも数を出さず、記録もしない）
  ・--check が無い、--cmd と同じ、エラーの表示を捨てる、命令の中で数える
  ・命令が失敗した、エラーの表示が出た
  ・結果が0行（--zero-check の別の探し方でも0行のときだけ、0と出す）
  ・null の行が在る（無い欄の名前を読むと null になる）
  ・--what と行の中身が合わない（値＝全部 数／ファイル＝全部 在るパス）
  ・--cmd と --check の数が違う（違う行を出す）
  ・作業の後の差が、予定の差と違う（増えた行と減った行を出す）

止まった後＝原因を調べて数え直す。通るまで、その数を書かない。直せないときは「数えられなかった」と理由を報告する。
止められないもの＝2つの命令が同じ誤りをしているとき。--what が正しいのに相手を間違えたとき。
数えた行の実物を画面に出すので、そこは人が読んで確かめる。
"""
import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WHATS = ("値", "項目", "行", "ファイル", "件")
SHOW = 3
DIFF_SHOW = 5
TIMEOUT = 300

# 命令の中で数えると、何を数えたかが行として残らない（2026-11-05 の閾値の項目の数の誤りの形）。
COUNTING = re.compile(r"\blength\b|\bwc\b|\bgrep\s+(-\w*c\w*|--count)\b|\buniq\s+-\w*c|\bcount\b")
# エラーの表示を捨てると、失敗が黙って0になる（2026-11-05 の jq の文法エラーの形）。
HIDING = re.compile(r"2>\s*/dev/null|2>&1\s*>\s*/dev/null|&>\s*/dev/null|\|\|\s*true")
WRITING = re.compile(r"(?<![0-9&])>|\btee\b|\brm\b|\bmv\b|\bcp\b|\bsed\s+-i\b")


class Stop(Exception):
    """数を出さずに止める理由。"""


def lint(name: str, cmd: str) -> None:
    if COUNTING.search(cmd):
        raise Stop(f"{name} の中で数えている（length・wc・grep -c など）。1行に1件を出す命令にする")
    if HIDING.search(cmd):
        raise Stop(f"{name} がエラーの表示を捨てている")
    if WRITING.search(cmd):
        raise Stop(f"{name} に書き込みが在る。読むだけの命令にする")


def run(cmd: str) -> list:
    try:
        p = subprocess.run(["bash", "-c", "set -o pipefail; " + cmd], cwd=ROOT, capture_output=True,
                           text=True, timeout=TIMEOUT)
    except subprocess.TimeoutExpired as e:
        raise Stop(f"{TIMEOUT}秒で終わらなかった: {cmd}") from e
    rows = [s for s in p.stdout.splitlines() if s.strip()]
    if p.stderr.strip():
        raise Stop(f"エラーの表示が出た: {p.stderr.strip()[:300]}")
    if p.returncode not in (0, 1) or (p.returncode == 1 and rows):
        raise Stop(f"命令が失敗した（rc={p.returncode}）: {cmd}")
    return rows


def check_kind(what: str, rows: list) -> None:
    nulls = [s for s in rows if s.strip() == "null"]
    if nulls:
        raise Stop(f"null の行が {len(nulls)} 行在る。無い欄の名前を読んでいないかを実物で確かめる。空の行を除くなら、命令の中で除く")
    if what == "値":
        bad = [s for s in rows if not re.fullmatch(r"-?\d+(\.\d+)?([eE][-+]?\d+)?", s.strip())]
        if bad:
            raise Stop(f"「値」と指定したのに、数でない行が {len(bad)} 行在る（例＝{bad[0][:80]!r}）")
    if what == "ファイル":
        bad = [s for s in rows if not (ROOT / s.strip()).exists()]
        if bad:
            raise Stop(f"「ファイル」と指定したのに、在るパスでない行が {len(bad)} 行在る（例＝{bad[0][:80]!r}）")


def only_in(a: list, b: list) -> list:
    return list((Counter(a) - Counter(b)).elements())


def show_diff(name_a: str, a: list, name_b: str, b: list) -> str:
    out = []
    for nm, rows in ((name_a, only_in(a, b)), (name_b, only_in(b, a))):
        if rows:
            out.append(f"{nm}だけに在る行 {len(rows)} 行")
            out.extend(f"    {s[:160]}" for s in rows[:DIFF_SHOW])
    return "\n".join(out)


def measure(what: str, cmd: str, check: str, zero_check: str | None) -> list:
    if cmd.strip() == check.strip():
        raise Stop("--cmd と --check が同じ命令。別のやり方で数える")
    for name, c in (("--cmd", cmd), ("--check", check), ("--zero-check", zero_check)):
        if c:
            lint(name, c)
    rows, other = run(cmd), run(check)
    if not rows and not other:
        if not zero_check:
            raise Stop("結果が0行。名前と探す場所を実物で確かめる。本当に0なら --zero-check に別の探し方を渡す")
        if zero_check.strip() in (cmd.strip(), check.strip()):
            raise Stop("--zero-check が前の命令と同じ")
        z = run(zero_check)
        if z:
            raise Stop(f"--zero-check で {len(z)} 行 当たった。0ではない（例＝{z[0][:80]!r}）")
        return rows
    for r in (rows, other):
        check_kind(what, r)
    if len(rows) != len(other):
        raise Stop(f"数が違う＝--cmd {len(rows)}・--check {len(other)}。違う行を実物で確かめる\n"
                   + show_diff("--cmd ", rows, "--check ", other))
    return rows


def state_dir(session: str) -> Path:
    p = ROOT / ".claude/state/sessions" / session
    p.mkdir(parents=True, exist_ok=True)
    return p


def record(session: str, row: dict) -> None:
    with (state_dir(session) / "counted.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({**row, "時刻": datetime.now(timezone.utc).isoformat(timespec="seconds")}, ensure_ascii=False) + "\n")


def load_before(session: str) -> dict:
    p = state_dir(session) / "count_before.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def report(label: str, what: str, cmd: str, check: str, rows: list) -> None:
    print(f"{label}＝{len(rows)} {what}（2通りで一致）")
    print(f"  命令＝{cmd}")
    print(f"  別の命令＝{check}")
    for s in rows[:SHOW]:
        print(f"  実物＝{s[:160]}")
    if len(rows) > SHOW:
        print(f"  実物＝…ほか {len(rows) - SHOW} 行")


def do_before(a) -> int:
    if a.expect_diff is None:
        raise Stop("--before には --expect-diff（作業で増減する予定の数）が要る。減るならマイナス、変わらないなら 0")
    rows = measure(a.what, a.cmd, a.check, a.zero_check)
    saved = load_before(a.session)
    if a.before in saved:
        raise Stop(f"「{a.before}」は登録済み。前の数を書き替えない。別の名前にする")
    saved[a.before] = {"what": a.what, "label": a.label, "cmd": a.cmd, "check": a.check, "zero_check": a.zero_check,
                       "expect": a.expect_diff, "rows": rows}
    (state_dir(a.session) / "count_before.json").write_text(json.dumps(saved, ensure_ascii=False), encoding="utf-8")
    report(f"作業の前｜{a.label}", a.what, a.cmd, a.check, rows)
    print(f"  予定の差＝{a.expect_diff:+d}")
    record(a.session, {"数": len(rows), "何": a.what, "名前": a.label, "命令": a.cmd, "別の命令": a.check, "段": "前"})
    return 0


def do_after(a) -> int:
    if a.cmd or a.check or a.what or a.label or a.expect_diff is not None:
        raise Stop("--after は、前に登録した命令と単位をそのまま使う。--cmd・--check・--what・--label・--expect-diff を渡さない")
    b = load_before(a.session).get(a.after)
    if b is None:
        raise Stop(f"「{a.after}」は登録されていない。作業の前に --before で数える")
    rows = measure(b["what"], b["cmd"], b["check"], b["zero_check"])
    before = b["rows"]
    diff = len(rows) - len(before)
    print(f"作業の後｜{b['label']}＝前 {len(before)}・後 {len(rows)}・差 {diff:+d}（予定 {b['expect']:+d}）")
    moved = show_diff("後", rows, "前", before)
    if moved:
        print(moved)
    if diff != b["expect"]:
        raise Stop(f"差が予定と違う＝差 {diff:+d}・予定 {b['expect']:+d}。上の行を実物で確かめる")
    for n, stage in ((len(rows), "後"), (abs(diff), "差")):
        record(a.session, {"数": n, "何": b["what"], "名前": b["label"], "命令": b["cmd"], "別の命令": b["check"], "段": stage})
    return 0


def do_once(a) -> int:
    rows = measure(a.what, a.cmd, a.check, a.zero_check)
    report(a.label, a.what, a.cmd, a.check, rows)
    record(a.session, {"数": len(rows), "何": a.what, "名前": a.label, "命令": a.cmd, "別の命令": a.check})
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="数を数える道具（恒久の決まり83番）")
    ap.add_argument("--session", required=True)
    ap.add_argument("--what", choices=WHATS, help="何を1と数えるか")
    ap.add_argument("--label", help="何の数か（報告に書く言葉）")
    ap.add_argument("--cmd", help="1行に1件を出す読むだけの命令")
    ap.add_argument("--check", help="同じ物を別のやり方で出す読むだけの命令")
    ap.add_argument("--zero-check", dest="zero_check", help="結果が0行のときだけ使う、さらに別の探し方")
    ap.add_argument("--before", metavar="名前", help="作業の前に、数え方を登録して数える")
    ap.add_argument("--after", metavar="名前", help="作業の後に、登録した数え方で数えて差を出す")
    ap.add_argument("--expect-diff", dest="expect_diff", type=int, help="--before と一緒に＝作業で増減する予定の数")
    a = ap.parse_args()
    try:
        if a.after:
            return do_after(a)
        if not (a.what and a.label and a.cmd and a.check):
            raise Stop("--what・--label・--cmd・--check が要る")
        return do_before(a) if a.before else do_once(a)
    except Stop as e:
        print(f"🔒 [count_items] 数を出しません＝{e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
