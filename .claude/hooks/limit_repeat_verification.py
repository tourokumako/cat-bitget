#!/usr/bin/env python3
# limit_repeat_verification.py — PreToolUse on Agent（2026-09-14 まこさん指示・新設）
#
# まこさんの指示（逐語 2026-09-14）
#   「照合を「0件になるまで」繰り返す形は作りません。」を「やるようにしろ」
#   （前の文＝「トークンの無駄なので、こんな無駄なことやめてほしい」
#            「確認をせずに同じミスを繰り返してトークンを無駄にすることをやめてほしい」）
#
# なぜ要るか
#   監査 cp37 の反映で、私（CC）は同じ設計書の照合を別の agent に9回 頼んだ（1回 約44万〜51万トークン）。
#   自分で確かめる代わりに、agent に間違いを探させていた（worklog 20260914 §47〜§56）。
#
# 役割（2026-10-17・まこさんが確かめた文）＝答え合わせを1回 頼んだら、あとは自分で確かめて直し切る。
#   それでも足りないと思ったら、もう一度 頼む前に まこさんに報告し、もう一度 確かめるかを まこさんに決めていただく。
#   この流れを守らせる。直しを確実にする働きは無い（それは恒久72番の1・2＝実物を開く・同じ事実を grep で揃える）。
#
# 何をやらせるか
#   照合の agent（依頼文に「照合」「確かめる係」「反映しているか」「独立に確かめ」を含むもの）を、
#   同じ相手（依頼文に名指ししたファイル名が1つでも重なる・名指しが無ければ「名指しなし」どうし）について、
#   このセッションで2回目に走らせようとしたら止める。
#   ★数え方＝いま出そうとしている依頼も数える（PreToolUse の時点で記録に入っている・2026-09-24 に本物で確かめた）。
#     結果がエラーの依頼（止められた・拒まれた＝走っていない）は数えない（2026-10-17）。
#   ★相手は設計書に限らない（まこさん指示 2026-09-14「あらゆる修正対応で以下を守るようにしろ」）。
#   ＝1回 照合したら、結果と直したことを まこさんに報告させる。もう一度 確かめるかは まこさんが決める
#     （まこさんが別のセッションで監査を起動する形＝cc_role §1.4.5 の「監査立ち上げの別セッション化」と同じ）。
#
# 回数「1回」は私（CC）の案（「0件になるまで繰り返さない」のいちばん狭い形）。変えるのは まこさん（MAX_PER_SESSION）。
# 解除: 無し（合言葉は 2026-08-16 に全廃）。
#
# 限界（正直に）
#   ①依頼文に上の語もパスも書かなければ数えない（言い方を変えればすり抜ける）。
#   ②セッションを変えれば数え直しになる。
#   ③この hook のファイル自体を書き換えれば無効にできる（明示の違反）。
#   ④走り始めてから途中でエラーになった Agent も数えない（トークンは使っている）。
#
# 試し方: python3 .claude/hooks/limit_repeat_verification.py --try <hook の入力の json を書いたファイル>
#         python3 .claude/hooks/limit_repeat_verification.py --selftest（S1〜S4）

import json
import re
import sys
from pathlib import Path

MAX_PER_SESSION = 1
KEYWORDS = ("照合", "確かめる係", "反映しているか", "独立に確かめ")
TARGET_RE = re.compile(r"[\w./\-]+\.(?:py|sh|json|md|csv)")


def is_verification(inp: dict) -> set:
    text = f"{inp.get('description') or ''}\n{inp.get('prompt') or ''}"
    if not any(k in text for k in KEYWORDS):
        return set()
    return {Path(t).name for t in TARGET_RE.findall(text)} or {"（名指しなし）"}


def past_count(transcript: str, targets: set) -> int:
    """同じ相手の照合の Agent の数（いま出そうとしている依頼も含む＝PreToolUse の時点で記録に入っている）。
    ★2026-10-17（185回目）＝結果がエラーの依頼（hook に止められた・許可の判定で拒まれた＝Agent は走っていない）は数えない。"""
    hits, failed = [], set()
    try:
        f = open(transcript, encoding="utf-8")
    except Exception:
        return 0
    with f:
        for ln in f:
            try:
                o = json.loads(ln)
            except Exception:
                continue
            if o.get("isSidechain") is True:
                continue
            c = (o.get("message") or {}).get("content")
            if not isinstance(c, list):
                continue
            for b in c:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "tool_use" and b.get("name") == "Agent":
                    if is_verification(b.get("input") or {}) & targets:
                        hits.append(b.get("id"))
                elif b.get("type") == "tool_result" and b.get("is_error") is True:
                    failed.add(b.get("tool_use_id"))
    return sum(1 for i in hits if i not in failed)


def main(raw: str) -> int:
    try:
        data = json.loads(raw)
    except Exception:
        return 0                                   # 読めない入力では止めない（fail-open）
    if data.get("agent_type"):
        return 0                                   # サブエージェントの中は見ない
    if data.get("tool_name") != "Agent":
        return 0
    targets = is_verification(data.get("tool_input") or {})
    if not targets:
        return 0
    n = past_count(str(data.get("transcript_path") or ""), targets)
    if n <= MAX_PER_SESSION:
        return 0
    e = sys.stderr
    print("🔒 [照合は1回まで] 同じ相手の照合を、このセッションで既に "
          f"{n} 回 頼んでいます（相手＝{', '.join(sorted(targets))}）。", file=e)
    print("   まこさん指示 2026-09-14「照合を「0件になるまで」繰り返す形は作りません」"
          "「トークンの無駄なので、こんな無駄なことやめてほしい」。", file=e)
    print("   ＝もう一度 照合に出す前に、1回目の結果と、自分で実物を開いて確かめて直したことを まこさんに報告してください。"
          "もう一度 確かめるかは まこさんが決めます（別のセッションで監査を起動する形）。", file=e)
    return 2


def selftest() -> int:
    """S1 1回目は通る／S2 走った依頼の後の2回目は止まる／S3 止められて走らなかった依頼の後の出し直しは通る／
    S4 照合の語が無い依頼は通る（2026-10-17）。"""
    import contextlib
    import io
    import tempfile
    kw = {"description": "acceptance.md の照合", "prompt": "acceptance.md を照合して"}
    use = json.dumps({"type": "assistant", "message": {"content": [
        {"type": "tool_use", "id": "{id}", "name": "Agent", "input": kw}]}}, ensure_ascii=False)
    err = json.dumps({"type": "user", "message": {"content": [
        {"type": "tool_result", "tool_use_id": "{id}", "is_error": True, "content": "止めた"}]}}, ensure_ascii=False)
    cases = [
        ("S1 1回目は通る", [use.replace("{id}", "now")], kw, 0),
        ("S2 走った依頼の後の2回目は止まる", [use.replace("{id}", "a"), use.replace("{id}", "now")], kw, 2),
        ("S3 止められた依頼の後の出し直しは通る",
         [use.replace("{id}", "a"), err.replace("{id}", "a"), use.replace("{id}", "now")], kw, 0),
        ("S4 照合の語が無い依頼は通る", [use.replace("{id}", "a"), use.replace("{id}", "now")],
         {"description": "調べ", "prompt": "acceptance.md を読んで要約して"}, 0),
    ]
    ng = []
    with tempfile.TemporaryDirectory() as d:
        for name, lines, inp, want in cases:
            tr = Path(d) / "t.jsonl"
            tr.write_text("\n".join(lines) + "\n", encoding="utf-8")
            raw = json.dumps({"session_id": "s", "tool_name": "Agent", "transcript_path": str(tr), "tool_input": inp},
                             ensure_ascii=False)
            with contextlib.redirect_stderr(io.StringIO()):
                got = main(raw)
            print(f"{'✅' if got == want else '❌'} {name}（期待 {want}・結果 {got}）")
            if got != want:
                ng.append(name)
    print(f"selftest {len(cases) - len(ng)}/{len(cases)}")
    return 1 if ng else 0


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--selftest":
        sys.exit(selftest())
    if len(sys.argv) == 3 and sys.argv[1] == "--try":
        sys.exit(main(Path(sys.argv[2]).read_text(encoding="utf-8")))
    sys.exit(main(sys.stdin.read()))
