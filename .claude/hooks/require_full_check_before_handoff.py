#!/usr/bin/env python3
# require_full_check_before_handoff.py — まこさんに何かをお願いする返信・「できた」と言う返信は、
#   後で走る検査を全部 1回で走らせて全部 通った後でなければ出せない（Stop hook）
#
# まこさん指示（2026-09-30・逐語）＝「一回の確認ですべて完全に修正できるように強制しろ」
#   「承認後に修正が発生しないように、事前にミスが無いよう確認をしろ」「矮小化するな」
#
# 何をするか＝このターンの返信に、お願い（OK・承認・commit・確認・打つ・消す・貼る・よいですか）か、
#   「できた」の言い方（できました・完了・直しました・作りました）が在れば、
#   ①check_all_before_handoff.py の記録（sessions/<セッション>/handoff_check.json）が在る
#   ②その記録が、直しかけのファイル（.py・.sh・設計書・案の下書き）の最後の書き替えより後
#   ③その記録で全部 通っている
#   の3つがそろわなければ、ターンを終われない。落ちた所は記録の中身を全部 出す。
# 限界（正直に）＝お願いを言葉の形で見分ける（言い方を変えれば当たらない）。検査が無い物の正しさは見ない。
import json
import os
import re
import sys

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
ASK_RE = re.compile(r"お願いします|お願い（|OK をいただ|OKをいただ|承認のコマンド|approve_impl\.sh|commit|コミット|確認してください"
                    r"|よいですか|いかがですか|打ってください|消してください|貼ってください|できました|完了しました|直しました|作りました")


def newest_mtime(files):
    ts = [os.path.getmtime(os.path.join(ROOT, f)) for f in files if os.path.exists(os.path.join(ROOT, f))]
    for extra in (".claude/state/acceptance.md",):
        if os.path.exists(os.path.join(ROOT, extra)):
            ts.append(os.path.getmtime(os.path.join(ROOT, extra)))
    st = os.path.join(ROOT, ".claude/state")
    ts += [os.path.getmtime(os.path.join(st, f)) for f in os.listdir(st) if f.startswith("_draft_") and f.endswith(".txt")]
    return max(ts) if ts else 0.0


def check(text: str, sid: str) -> list:
    body = re.sub(r"```.*?```", "", text, flags=re.S)
    if not ASK_RE.search(body):
        return []
    sys.path.insert(0, ROOT + "/.claude/hooks")
    import check_all_before_handoff as ca
    how = f"python3 {ROOT}/.claude/hooks/check_all_before_handoff.py --session {sid}"
    rp = os.path.join(ROOT, ".claude/state/sessions", sid or "_nosession", "handoff_check.json")
    if not os.path.isfile(rp):
        return [f"お願い・「できた」の前に、後で走る検査を全部 走らせていない。走らせる: {how}"]
    rec = json.load(open(rp, encoding="utf-8"))
    bad = []
    if rec.get("time", 0) < newest_mtime(ca.changed_files()):
        bad.append(f"検査の後に、直しかけのファイルか設計書か案の下書きを書き替えた＝全部 走らせ直す: {how}")
    if not rec.get("ok"):
        bad.append(f"検査が {len(rec.get('fails') or [])} 件 落ちたまま（全部 直してから走らせ直す: {how}）:")
        bad += ["   " + x for x in rec.get("fails") or []]
    return bad


def main() -> int:
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except Exception:                                        # noqa: BLE001
        return 0
    sys.path.insert(0, ROOT + "/.claude/hooks")
    import require_design_check_before_approval as rd
    text = rd._turn_text(data)
    text = text.split("\n", 1)[1] if text.startswith("{") and "\n" in text else ("" if text.startswith("{") else text)
    bad = check(text, data.get("session_id") or "")
    if not bad:
        return 0
    print("🔒 [お願いの前の全部の検査] まこさん指示 2026-09-30「一回の確認ですべて完全に修正できるように強制しろ」"
          "「承認後に修正が発生しないように、事前にミスが無いよう確認をしろ」:", file=sys.stderr)
    for b in bad:
        print("   " + b, file=sys.stderr)
    return 2


if __name__ == "__main__":
    if "--try" in sys.argv:
        i = sys.argv.index("--try")
        for b in check(open(sys.argv[i + 1], encoding="utf-8").read(), sys.argv[i + 2]) or ["（止める所なし）"]:
            print(b)
        sys.exit(0)
    sys.exit(main())
