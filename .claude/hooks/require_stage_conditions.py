#!/usr/bin/env python3
"""require_stage_conditions.py — 工事の「いまの段」の、まこさんにお願いする前の条件が ❌ のまま、お願いの返信でターンを終えない（Stop）。

まこさん指示（2026-10-10・逐語）＝「とにかく、自動で確認をしてミスを見つけ修正をして、完璧な状態になってから、私に確認を出すように強制できるということだよね？」
  「この強制は作って。」
なぜ要るか（検証＝session_worklog_20261010.md の §42・型 A と B）
  いままでのターンの終わりの検査は、返信の言い方や見出しの形で相手を見分けていた（案＝【数字…】の見出し・リンク＝文書の名前）。
  形が違うお願い（案をリンクだけで出した・見出しを付けずに出した・返信の文の形で出した）は見えず、まこさんの OK が2回 要った（3回）。
  ＝この hook は、返信の形でなく「工事がいまどの段か」（next_move.py が実物のファイルから読む）で見分け、その段の
    お願いの前の条件（同じ next_move.py の conditions）に ❌ が在れば、お願いの返信を止める。

決まり
  1. いまの工事＝設計書（acceptance.md）の目印 iter の名前。無ければ読むもの宣言（design_read_plan.md）の「設計書:」の名前。どちらも無ければ通す。
  2. next_move.py の steps と conditions を呼び、いまの段の条件に ❌（走らせて落ちた物）が1つも無ければ通す。
  3. ❌ が在るとき、いまの返信（まこさんの最後の発言より後・hook の差し戻しより後だけ＝2026-10-01 の _turn_text の直しと同じ）が
     お願いの返信（下の ASK_RE＝承認・OK・お願いします の語か、設計書・依頼書・手書きの文書・読むもの宣言へのリンク）なら止める（終了コード 2）。
     ★お願いの返信でなければ通す（答える・報告する返信を止めない）。
  4. 止めるのは、まこさんの同じ発言に対して2回まで。3回目は理由を出して通す（2026-10-01 に止まり続ける hook が進行を妨げた＝worklog 20261001 §4〜§6）。
限界（正直に）
  ・お願いかどうかは、語とリンクで見る（形の見分けは残る）。段の見分けと条件は next_move.py が実物から読む＝そちらは形に依らない。
  ・条件は「走らせて落ちたか」まで。中身が正しいかは見ない（見直し表・監査・まこさんの目）。
  ・恒久71番＝読むための hook。壊すプログラムと自己テストは付けない。--try <記録> で、過去の記録に対して何が止まるかを出して確かめる。
使い方: （hook）標準入力に Stop の JSON ／ --try <やり取りの記録 .jsonl> [--work <工事名>]（何も止めない・何も書かない）
"""
import json
import os
import re
import sys

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
sys.path.insert(0, ROOT + "/.claude/hooks")
sys.path.insert(0, ROOT + "/.claude/tools")

# ★お願いの語＝「承認・OK を もらう／いただく／お願いする」の形と、お願いします・打ってください ほか。
#   「OK」「承認」の1語だけでは見ない＝まこさんの決定の逐語（「OK」）を引く報告の返信まで当たるため
#   （165回目の記録で試した＝1語で見ると 51回のうち 23回が当たった）。
ASK_RE = re.compile(r"(承認|OK|オーケー)(を|の|は)?\s*(お願い|もらえ|いただ|ください|頂)|お願いします|お願いいたします|"
                    r"打ってください|決めてください|確認してください|よろしいでしょうか|見ていただけ|決めていただ")
LINK_RE = re.compile(r"\]\([^)\s]*(?:acceptance\.md|_audit_request\.md|監査依頼の手書き|design_read_plan\.md)[^)]*\)")


def current_work() -> str:
    """いまの工事の名前（設計書の目印 iter → 読むもの宣言の「設計書:」の順）。無ければ空。"""
    acc = os.path.join(ROOT, ".claude/state/acceptance.md")
    try:
        m = re.search(r'iter="([^"]+)"', open(acc, encoding="utf-8").read())
        if m:
            return m.group(1)
    except OSError:
        pass
    plan = os.path.join(ROOT, ".claude/state/design_read_plan.md")
    try:
        m = re.search(r"^設計書:\s*(\S+)", open(plan, encoding="utf-8").read(), re.M)
        return m.group(1) if m else ""
    except OSError:
        return ""


def stage_fails(work: str, session: str) -> tuple:
    """(いまの段の名前, ❌ の条件の一覧)。流れが最後まで済んでいれば ("", [])。"""
    import next_move as nm
    f = nm.facts(work, session)
    st = nm.steps(f)
    cur = next((i for i, x in enumerate(st) if not x[1]), None)
    if cur is None:
        return "", []
    bad = [text for ok, text in nm.conditions(f, cur) if ok is False]
    return st[cur][0], bad


def is_ask(text: str) -> bool:
    return bool(ASK_RE.search(text or "") or LINK_RE.search(text or ""))


def _count(session: str, uid: str) -> int:
    """まこさんの同じ発言（uid）に対して、この hook が止めた回数を1つ増やして返す。"""
    d = os.path.join(ROOT, ".claude/state/sessions", session or "_nosession")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "stage_stop.json")
    try:
        rec = json.load(open(p, encoding="utf-8"))
    except (OSError, ValueError):
        rec = {}
    rec = {uid: rec.get(uid, 0) + 1}            # 直前の発言の分だけ残す
    json.dump(rec, open(p, "w", encoding="utf-8"), ensure_ascii=False)
    return rec[uid]


def hook() -> int:
    try:
        d = json.loads(sys.stdin.read() or "{}")
    except Exception:                                        # noqa: BLE001
        return 0
    if d.get("agent_type"):
        return 0
    tp = d.get("transcript_path") or ""
    if not tp or not os.path.exists(tp):
        return 0
    work = current_work()
    if not work:
        return 0
    session = d.get("session_id") or os.path.basename(tp)[:-6]
    try:
        stage, bad = stage_fails(work, session)
    except Exception as e:                                   # noqa: BLE001
        print(f"[段の条件] 工事 {work} の印を読めない＝{type(e).__name__} {e}（止めない）", file=sys.stderr)
        return 0
    if not bad:
        return 0
    import require_design_check_before_approval as rd
    from enforce_chat_writing import last_chat_text
    text = rd._turn_text(d)
    if not is_ask(text):
        return 0
    _t, uid = last_chat_text(tp)
    n = _count(session, uid or "")
    e = sys.stderr
    if n > 2:
        print(f"[段の条件] 同じ発言に対して {n} 回目＝通す（止まり続けない）。❌ は残っている＝{' ／ '.join(bad)}", file=e)
        return 0
    print(f"🔒 [段の条件] 工事 {work} の いまの段「{stage}」で、まこさんにお願いする前の条件が ❌ のまま、お願いの返信を出そうとしている", file=e)
    for b in bad:
        print("   ❌ " + b, file=e)
    print("   まこさんの指示（2026-10-10）「完璧な状態になってから、私に確認を出すように強制」「この強制は作って」", file=e)
    print("   対処＝❌ を全部 直してから、python3 .claude/tools/next_move.py --work " + work + " で ✅ を確かめ、それから お願いを出す。", file=e)
    print("   直せないときは、お願いの語（承認・OK・お願いします）とリンクを書かずに、止まった理由を1回 報告して まこさんの答えを待つ。", file=e)
    print(f"   （この止めは同じ発言につき2回まで＝いま {n} 回目）", file=e)
    return 2


def try_transcript(tp: str, work: str = "") -> int:
    """過去の記録で、何が止まるかを出す（何も止めない・何も書かない）。"""
    import require_design_check_before_approval as rd
    work = work or current_work()
    print(f"工事＝{work or '（無い＝通す）'}")
    if not work:
        return 0
    session = os.path.basename(tp)[:-6]
    stage, bad = stage_fails(work, session)
    print(f"いまの段＝{stage or '（最後まで済）'}／❌ {len(bad)} 件" + ("".join("\n   ❌ " + b for b in bad)))
    rows = rd._load_rows(tp)
    # まこさんの発言ごとに区切り、その後の CC の返信（差し戻しより後だけ）が お願いの返信かを数える
    turns, cur, in_ask = 0, [], 0
    from enforce_chat_writing import last_chat_text  # noqa: F401  （同じ見分け方を使うことの確認）
    for r in rows:
        if r.get("type") == "user":
            c = (r.get("message") or {}).get("content")
            if isinstance(c, str) and re.match(r"^\S+ hook feedback:", c.strip()):
                cur = []
                continue
            if cur:
                turns += 1
                in_ask += int(is_ask("\n".join(cur)))
            cur = []
        elif r.get("type") == "assistant":
            for b in (r.get("message") or {}).get("content") or []:
                if isinstance(b, dict) and b.get("type") == "text":
                    cur.append(b.get("text") or "")
    if cur:
        turns += 1
        in_ask += int(is_ask("\n".join(cur)))
    print(f"返信の区切り {turns} 回のうち、お願いの返信と見る物 {in_ask} 回。❌ が在る状態なら、その {in_ask} 回が止まる（同じ発言につき2回まで）")
    return 0


if __name__ == "__main__":
    if "--try" in sys.argv:
        i = sys.argv.index("--try")
        w = sys.argv[sys.argv.index("--work") + 1] if "--work" in sys.argv else ""
        sys.exit(try_transcript(sys.argv[i + 1], w))
    sys.exit(hook())
