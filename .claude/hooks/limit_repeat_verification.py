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
# 何をやらせるか
#   照合の agent（依頼文に「照合」「確かめる係」「反映しているか」「独立に確かめ」を含むもの）を、
#   同じ相手（依頼文に名指ししたファイル名が1つでも重なる・名指しが無ければ「名指しなし」どうし）について、
#   このセッションで2回目に走らせようとしたら止める。
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
#
# 試し方: python3 .claude/hooks/limit_repeat_verification.py --try <hook の入力の json を書いたファイル>

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
    n = 0
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
                if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "Agent":
                    if is_verification(b.get("input") or {}) & targets:
                        n += 1
    return n


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
    if n < MAX_PER_SESSION:
        return 0
    e = sys.stderr
    print("🔒 [照合は1回まで] 同じ相手の照合を、このセッションで既に "
          f"{n} 回 頼んでいます（相手＝{', '.join(sorted(targets))}）。", file=e)
    print("   まこさん指示 2026-09-14「照合を「0件になるまで」繰り返す形は作りません」"
          "「トークンの無駄なので、こんな無駄なことやめてほしい」。", file=e)
    print("   ＝もう一度 照合に出す前に、1回目の結果と、自分で実物を開いて確かめて直したことを まこさんに報告してください。"
          "もう一度 確かめるかは まこさんが決めます（別のセッションで監査を起動する形）。", file=e)
    return 2


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--try":
        sys.exit(main(Path(sys.argv[2]).read_text(encoding="utf-8")))
    sys.exit(main(sys.stdin.read()))
