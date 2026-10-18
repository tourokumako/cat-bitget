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
     ★2026-10-17（185回目）＝お願いの返信は、いまの工事の文書へのリンク（設計書・読むもの宣言・その工事の依頼書と
       手書きの文書）と、お願いの語の、両方が在るときだけ（直す前は、どちらか一方で止め、10回とも関係の無い返信を止めた）。
       監査のセッション（require_read_used._auditor_session）では止めない。
  4. 止めるのは、まこさんの同じ発言に対して2回まで。3回目は理由を出して通す（2026-10-01 に止まり続ける hook が進行を妨げた＝worklog 20261001 §4〜§6）。
限界（正直に）
  ・お願いかどうかは、語とリンクで見る（形の見分けは残る）。段の見分けと条件は next_move.py が実物から読む＝そちらは形に依らない。
  ・リンクを書かずに、言葉だけで OK をお願いする返信は見ない（2026-10-17 から）。相談のセッションは見分けていない。
  ・条件は「走らせて落ちたか」まで。中身が正しいかは見ない（見直し表・監査・まこさんの目）。
  ・恒久71番＝読むための hook。壊すプログラムと自己テストは付けない。--try <記録> で、過去の記録に対して何が止まるかを出して確かめる。
使い方: （hook）標準入力に Stop の JSON ／ --try <やり取りの記録 .jsonl> [--work <工事名>]（何も止めない・何も書かない）
        ／ --selftest（お願いの返信の見分け方 S1〜S6・2026-10-17）
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


def auto_fix(f: dict, cur: int) -> list:
    """プログラムが直せる物は、止めずに直す（★2026-10-11・まこさん「修正対応をした状態で確認に出すようにすべき」「OK」）。戻り＝直した物の文の一覧。
    ①A12 の仮当ての控え＝require_design_check_before_approval._a12_leftover（戻せる物は、その中で戻す）
    ②hook の一覧＝gen_hook_list.py --verify が落ちたら --write
    ③見直し表の骨組み＝段4（設計書）・段8（依頼書）で、表が無ければ gen_review.py --skeleton（在る表は触らない＝中身は私が埋める）
    まこさんの手が要る物（コミット・承認）は直せない＝条件の ❌ として出す。"""
    import subprocess
    done = []
    try:
        import require_design_check_before_approval as rd
        before = os.path.isdir(rd.BK_DIR)
        rd._a12_leftover()
        if before and not os.path.isdir(rd.BK_DIR):
            done.append("A12 の仮当ての控えを戻した")
    except Exception as e:                                   # noqa: BLE001
        done.append(f"A12 の控えの確かめが走らない＝{type(e).__name__} {e}")
    try:
        r = subprocess.run(["python3", ".claude/tools/gen_hook_list.py", "--verify"], capture_output=True, text=True, timeout=60, cwd=ROOT)
        if r.returncode != 0:
            w = subprocess.run(["python3", ".claude/tools/gen_hook_list.py", "--write"], capture_output=True, text=True, timeout=60, cwd=ROOT)
            done.append("hook の一覧を作り直した（gen_hook_list.py --write）" + ("" if w.returncode == 0 else "＝落ちた"))
    except Exception as e:                                   # noqa: BLE001
        done.append(f"hook の一覧の照らしが走らない＝{type(e).__name__} {e}")
    doc = None
    if cur == 4:
        doc = os.path.join(ROOT, ".claude/state/acceptance.md")
    elif cur == 8 and f["audit"]["impl"]["request"]:
        doc = str(f["audit"]["impl"]["request"])
    if doc and os.path.isfile(doc):
        try:
            import gen_review
            if not os.path.isfile(gen_review.review_path(doc)):
                r = subprocess.run(["python3", ".claude/tools/gen_review.py", "--skeleton", doc], capture_output=True, text=True, timeout=60, cwd=ROOT)
                done.append(f"見直し表の骨組みを作った（gen_review.py --skeleton {os.path.basename(doc)}）" + ("" if r.returncode == 0 else "＝落ちた"))
        except Exception as e:                               # noqa: BLE001
            done.append(f"見直し表の骨組みが作れない＝{type(e).__name__} {e}")
    return done


def stage_fails(work: str, session: str, fix: bool = True) -> tuple:
    """(いまの段の名前, ❌ の条件の一覧, 直した物の一覧)。流れが最後まで済んでいれば ("", [], [])。"""
    import next_move as nm
    f = nm.facts(work, session)
    st = nm.steps(f)
    cur = next((i for i, x in enumerate(st) if not x[1]), None)
    if cur is None:
        return "", [], []
    fixed = auto_fix(f, cur) if fix else []
    bad = [text for ok, text in nm.conditions(f, cur) if ok is False]
    return st[cur][0], bad, fixed


APPLY_RE = re.compile(r"apply_audit_fix\.py\b.*--(design|report)\b")


def pre() -> int:
    """PreToolUse（Bash）＝当てる道具（apply_audit_fix.py --design／--report・--dry を除く）を打つ直前に、当てる前の条件を見る。"""
    try:
        d = json.loads(sys.stdin.read() or "{}")
    except Exception:                                        # noqa: BLE001
        return 0
    cmd = (d.get("tool_input") or {}).get("command") or ""
    if not APPLY_RE.search(cmd) or "--dry" in cmd:
        return 0
    work = current_work()
    if not work:
        return 0
    tp = d.get("transcript_path") or ""
    session = d.get("session_id") or (os.path.basename(tp)[:-6] if tp else "")
    try:
        stage, bad, fixed = stage_fails(work, session)
    except Exception as e:                                   # noqa: BLE001
        print(f"[段の条件] 工事 {work} の印を読めない＝{type(e).__name__} {e}（止めない）", file=sys.stderr)
        return 0
    for x in fixed:
        print("[段の条件] 直した＝" + x, file=sys.stderr)
    if not bad:
        return 0
    e = sys.stderr
    print(f"🔒 [段の条件・当てる前] 工事 {work} の いまの段「{stage}」で、当てる前の条件が ❌ のまま、当てる道具を打とうとしている", file=e)
    for b in bad:
        print("   ❌ " + b, file=e)
    print("   まこさんの指示（2026-10-11）「修正対応をした状態で確認に出すようにすべき」＝当てる前に、当てた後に走る照らしを通しておく", file=e)
    print("   対処＝❌ を直してから（コミットと承認は まこさんの OK）、python3 .claude/tools/next_move.py --work " + work + " で ✅ を確かめて打つ", file=e)
    return 2


LINK_ANY_RE = re.compile(r"\]\(([^)\s]+)\)")


def work_links(text: str, work: str) -> list:
    """返信の中の、いまの工事の文書へのリンク（★2026-10-17・185回目）。"""
    names = {work, work.replace("-", "_")} if work else set()
    out = []
    for link in LINK_ANY_RE.findall(text or ""):
        base = os.path.basename(link.split("#")[0])
        if base in ("acceptance.md", "design_read_plan.md"):
            out.append(link)
        elif ("_audit_request.md" in base or "監査依頼の手書き" in link) and any(n and n in link for n in names):
            out.append(link)
    return out


def is_ask(text: str, work: str) -> bool:
    """お願いの返信＝いまの工事の文書へのリンクと、お願いの語の両方が在る（★2026-10-17・185回目）。
    直す前は、どちらか一方で「お願い」と見た＝工事と関係の無い返信も止めた（10月11日・12日の10回）。"""
    return bool(ASK_RE.search(text or "")) and bool(work_links(text, work))


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
    import require_design_check_before_approval as rd
    from enforce_chat_writing import last_chat_text
    from require_read_used import _auditor_session
    # ★2026-10-18（監査 CP81）＝監査のセッションか・お願いの返信かを先に見る。直す前は stage_fails（auto_fix が gen_hook_list.py --write と
    #   gen_review.py --skeleton で本物のファイルを書く）を、止めないターンでも監査のセッションでも毎ターン走らせていた。
    if _auditor_session(rd._load_rows(tp)):
        return 0                                             # ★2026-10-17＝監査のセッションでは止めない（段は、メインの工事の物）
    text = rd._turn_text(d)
    if not is_ask(text, work):
        return 0
    try:
        stage, bad, fixed = stage_fails(work, session)
    except Exception as e:                                   # noqa: BLE001
        print(f"[段の条件] 工事 {work} の印を読めない＝{type(e).__name__} {e}（止めない）", file=sys.stderr)
        return 0
    for x in fixed:
        print("[段の条件] 直した＝" + x, file=sys.stderr)
    if not bad:
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
    stage, bad, _fixed = stage_fails(work, session, fix=False)   # --try は何も書かない＝直しも走らせない
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
                in_ask += int(is_ask("\n".join(cur), work))
            cur = []
        elif r.get("type") == "assistant":
            for b in (r.get("message") or {}).get("content") or []:
                if isinstance(b, dict) and b.get("type") == "text":
                    cur.append(b.get("text") or "")
    if cur:
        turns += 1
        in_ask += int(is_ask("\n".join(cur), work))
    print(f"返信の区切り {turns} 回のうち、お願いの返信と見る物 {in_ask} 回。❌ が在る状態なら、その {in_ask} 回が止まる（同じ発言につき2回まで）")
    return 0


def selftest() -> int:
    """お願いの返信の見分け方（★2026-10-17・185回目）。S1〜S5＝is_ask／S6＝監査のセッションの見分け方。"""
    from require_read_used import _auditor_session
    w = "k4-reference-known-20261011"
    acc = "[設計書](.claude/state/acceptance.md)"
    req_now = "[依頼書](SDK/.claude/audits/inputs/2026-10-12_k4_reference_known_20261011_design_cp74_audit_request.md)"
    req_other = "[依頼書](SDK/.claude/audits/inputs/2026-10-13_design_doc_gen_form_20261013_impl_cp78_audit_request.md)"
    cases = [
        ("S1 いまの工事の設計書へのリンク＋お願いの語＝お願い", is_ask(f"{acc} の承認をお願いします", w), True),
        ("S2 お願いの語だけ＝お願いでない", is_ask("要・過剰・不要のどれにするか決めてください", w), False),
        ("S3 リンクだけの報告＝お願いでない", is_ask(f"{acc} を作り直しました", w), False),
        ("S4 ほかの工事の依頼書＋お願いの語＝お願いでない", is_ask(f"{req_other} を見ていただけますか", w), False),
        ("S5 いまの工事の依頼書（_ の形）＋お願いの語＝お願い", is_ask(f"{req_now} を見ていただけますか", w), True),
        ("S6 最初の発言が「監査して」のセッション＝監査のセッション",
         _auditor_session([{"type": "user", "message": {"content": "監査して 実装の監査の依頼書 CP76"}}]), True),
    ]
    ng = 0
    for name, got, want in cases:
        print(f"{'✅' if got == want else '❌'} {name}（期待 {want}・結果 {got}）")
        ng += int(got != want)
    print(f"selftest {len(cases) - ng}/{len(cases)}")
    return 1 if ng else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    if sys.argv[1:] and sys.argv[1] == "pre":
        sys.exit(pre())
    if "--try" in sys.argv:
        i = sys.argv.index("--try")
        w = sys.argv[sys.argv.index("--work") + 1] if "--work" in sys.argv else ""
        sys.exit(try_transcript(sys.argv[i + 1], w))
    sys.exit(hook())
