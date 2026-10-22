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
#     ＋案の見出しが在る最初の返信から後ろの、全部の行が下書きに在る（2026-10-22＝案と同じ返信に、試していない文を混ぜない）
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
        # ★2026-10-17（188回目・まこさん「直す」）＝囲み（```）の中の見出しは、説明や手順の例なので案の見出しと数えない。
        #   直す前は、CC が問題点の説明で囲みの中に見出しの例を書いただけで「試しの記録が無い」と止めた。
        #   OK された案の逐語のファイル 271本で、囲みの外の案の見出しは320行・囲みの中は0行（本物の案を見落とさない）。
        if not fence and HEAD_RE.match(ln):
            inside = True
            out.append(s)
            continue
        # ★2026-10-01＝案の最後の見出し【外部検索】で、案の行を数えるのを止める（直す前は、案を出した後に同じターンで
        #   書いた返信の文まで案の行と数え、試した下書きに無いとして返信を止め続けた）
        if inside and not fence and (s.startswith("**") or s.startswith("---") or s.startswith("#")
                                     or s.startswith("【外部検索】")):
            inside = False
            continue
        if inside and s:
            out.append(s)
    return out


def check(text: str, sid: str, blocks: list | None = None) -> list:
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
    draft = rec.get("draft") or ""
    have = {ln.strip() for ln in draft.splitlines() if ln.strip()}
    miss = [i for i, ln in enumerate(lines) if ln not in have]
    if miss:
        # ★2026-10-17（188回目・まこさん「何度も同じ確認を繰り返さないための修正は上記でよい」「１は修正する」）
        #   直す前＝案の後ろに書いた報告の文（例「worklog に書きました」）でも「下書きに足して試し直す」と案内した。
        #   案は変わっていないのに12〜17分の試しを走らせ直させ（直近30日の止め15回のうち9回）、しかも報告の文が
        #   設計書に写る形になった（gen_acceptance.py は、最後の見出しより後ろの行もその節に写す＝:358-371）。
        #   直した後＝試した案の行が全部 返信に在り、合わない行が全部 その後ろ（下書きと合う最後の行より後ろ）なら、
        #   後ろの文を消して出し直すよう案内し、試しは走らせ直させない。止める範囲は変えない。
        tried = proposal_lines(draft)
        matched = [i for i, ln in enumerate(lines) if ln in have]
        trailing = bool(tried) and set(tried) <= set(lines) and bool(matched) and min(miss) > max(matched)
        first = lines[miss[0]][:60]
        if trailing:
            bad.append(f"案の後ろに、試した下書きに無い文が {len(miss)} 行ある（最初＝「{first}」）。案の中身は試したとおり。"
                       "後ろの文を消して、案だけをもう一度出す。試しは走らせ直さない（報告は案より前に書く。"
                       "案の後ろの文は、設計書を作るプログラムがその節の中身として写す）")
        else:
            bad.append(f"返信の案の行のうち {len(miss)} 行が、試した下書きに無い（最初＝「{first}」）。案を下書きに書いて試し直す: {how}")
    # ★2026-10-22（204回目・まこさん「進めてよい」）＝案の見出しが在る最初の返信から後ろの、全部の行を照らす。
    #   直す前＝最初の案の見出しより前の行（いまの工程・報告）を照らさなかった。CC が同じ返信の先頭に【いまの工程】【次】を
    #   書き、gen_acceptance.py が OK の後に「知らない見出し」で止まった（まこさんの OK が1回むだになった）。
    #   それより前の返信（道具を呼ぶ合間の文）は、逐語に選ばないので照らさない。
    if blocks:
        k0 = next((i for i, b in enumerate(blocks) if proposal_lines(b)), None)
        inner = set(lines)
        extra = [] if k0 is None else [ln.strip() for b in blocks[k0:] for ln in b.splitlines()
                                       if ln.strip() and ln.strip() not in have and ln.strip() not in inner]
        if extra:
            bad.append(f"案と同じ返信の中に、試した下書きに無い文が {len(extra)} 行ある（最初＝「{extra[0][:60]}」）。"
                       f"返信の全文（いまの工程・報告・案）を1つの下書きに書いて試し直し、通った下書きを1文字も変えずに出す: {how}")
    return bad


def turn_blocks(data) -> list:
    """このターンの CC の返信を、返信ごとに分けて返す（範囲の決め方は require_design_check_before_approval._turn_text と同じ）。"""
    path = data.get("transcript_path") or ""
    if not path:
        return []
    sys.path.insert(0, ROOT + "/.claude/hooks")
    try:
        import require_design_check_before_approval as rd
        from enforce_chat_writing import last_chat_text      # noqa: E402
        _text, uid = last_chat_text(path)
        rows = rd._load_rows(path)
    except Exception:                                        # noqa: BLE001
        return []
    start = next((i for i, r in enumerate(rows) if uid and r.get("uuid") == uid), -1)
    for i, r in enumerate(rows):
        if i > start and r.get("type") == "user":
            c = (r.get("message") or {}).get("content")
            if isinstance(c, str) and re.match(r"^\S+ hook feedback:", c.strip()):
                start = i
    return [b.get("text") or "" for r in rows[start + 1:] if r.get("type") == "assistant"
            for b in (r.get("message") or {}).get("content") or [] if isinstance(b, dict) and b.get("type") == "text"]


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
    bad = check(text, data.get("session_id") or "", turn_blocks(data))
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
        _t = Path(sys.argv[i + 1]).read_text(encoding="utf-8")
        for b in check(_t, sys.argv[i + 2], [_t]) or ["（止める所なし）"]:
            print(b)
        sys.exit(0)
    sys.exit(main())
