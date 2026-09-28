#!/usr/bin/env python3
"""enforce_no_false_claim.py — 返信の嘘の型を、形で止める（Stop hook）。

2026-09-28（132回目）まこさん指示（逐語）＝「とにかく、虚偽発言できないようにしろ」
  → 表の8行と、文ごとの出どころの決まりを見て「じゃあ、上記強制入れて、効果あるのか見てみるわ」。
  ★これは 2026-08-24 の まこさんの決定（会話の決まりは強制しない・permanent_rules.md §0）を、まこさんが変えたもの。

止めるもの（表の8行・今日の嘘の型から作った）
  R1 出どころ    断定の段落に、出どころの印（ファイルと行・URL・§の節・記録の N行目・まこさんの引用・
                  「わからない」「私の導出」「調べていない」）が1つも無い
  R2 作った引用  まこさんの言葉として「」で書いた引用が、やり取りの記録にも記録のファイルにも無い
  R2b 開いていない行  「ファイル名:行番号」とリンクの #L が、この会話で開いていない行を指す
  R3 決まった・済  「決まった」「済」「確かめた」「分かった」がある文に、出どころの印が無い
  R4 数          「N つ」「N 件」などの直後の箇条書きに、出どころの印の無い項目がある
  R5 同意        「はい」「賛成」「そのとおり」で始まる返信の最初の段落に、根拠の印も「まこさんの言葉だから」も無い
  R6 前の記述    結論のある返信なのに、このターンで worklog かやり取りの記録を検索した記録が無い
  R7 反対の材料  結論のある返信に「反対の材料」が無い
  R8 worklog が先  結論のある返信なのに、このターンで worklog を書いた記録が無い
  「結論のある返信」＝「私の答え」「私の案」「結論」「おすすめ」「推奨」のどれかがある返信。

限界（正直に）
  - 形しか見ない。出どころを付けても中身が嘘なら通る。開いた行の読み違い・片側だけの材料は、印さえあれば通る。
  - 向きを変えたか（約束5）は見ない。
  - 正しい文まで止めることがある（2026-08-24 に語の検査を外した前例）。止めるのは1回のやり取りにつき2回まで。
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import enforce_checked_edit as ce  # noqa: E402

ROOT = ce.ROOT
SDK = ce.SDK
MEM = Path.home() / ".claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget/memory"
CORPUS_DIRS = [ROOT / ".claude/state", ROOT / ".claude/rules", SDK / ".claude/ratchet",
               SDK / ".claude/rules", SDK / ".claude/memory", MEM]
COUNT = ROOT / ".claude/state/no_false_claim_count.json"
MAX_BLOCKS = 2
MAX_FILE = 8_000_000

QUOTE_RE = re.compile(r"まこさん[^「」\n]{0,20}「([^「」]{2,400})」")
LINK_RE = re.compile(r"\]\(([^)#\s]+)#L(\d+)(?:-L(\d+))?\)")
CUT_RE = re.compile(r"…+|（略）|\.\.\.")
SRC_RE = re.compile(
    r"[\w\-.]+\.[A-Za-z][A-Za-z0-9]{0,9}:\d+|#L\d+|https?://|§\s?\d|\d+\s?行目|記録の\s?\d+|"
    r"わからない|分からない|私の導出|調べていない|まこさんの言葉だから|コマンドの出力|まこさん[^「」\n]{0,20}「")
SURE_RE = re.compile(r"決まった|決まりました|決まっています|✅済|(?<![未])済(?:み|です|でした|にし)|確かめた|確かめました|分かった|分かりました")
COUNT_HEAD_RE = re.compile(r"\d+\s?(?:つ|件|個|本|か所)")
ITEM_RE = re.compile(r"^\s*(?:[-*・]|\d+[.．)）])\s+")
AGREE_RE = re.compile(r"^(?:受け取り方[^\n]*\n+)?\s*(?:はい|賛成|そのとおり|その通り)")
CONC_RE = re.compile(r"私の答え|私の案|結論|おすすめ|推奨")
DECL_RE = re.compile(r"^(?:受け取り方|【|★)")


def norm(s: str) -> str:
    return re.sub(r"[\s　]+", "", s.replace("\\n", ""))


def is_hook_feedback(c) -> bool:
    return isinstance(c, str) and re.match(r"^\S+ hook feedback:", c.strip()) is not None


def read_rows(path: str) -> list:
    try:
        return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    except Exception:
        return []


def user_text(r) -> str:
    if r.get("type") != "user" or r.get("isSidechain") is True:
        return ""
    c = (r.get("message") or {}).get("content")
    if isinstance(c, str):
        return "" if is_hook_feedback(c) else c
    if isinstance(c, list):
        return "\n".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
    return ""


def turn_bounds(rows: list):
    """（直前の まこさんの発言の位置, 差し戻しの後の起点）。"""
    last = -1
    for i, r in enumerate(rows):
        if user_text(r).strip():
            last = i
    start = last
    for i, r in enumerate(rows):
        if i > last and r.get("type") == "user" and is_hook_feedback((r.get("message") or {}).get("content")):
            start = i
    return last, start


def last_reply(rows: list):
    """（差し戻しの後に私が書いた本文の全部, 直前の まこさんの発言の uuid）。"""
    last, start = turn_bounds(rows)
    uid = rows[last].get("uuid") if last >= 0 else None
    parts = []
    for r in rows[start + 1:]:
        if r.get("type") != "assistant" or r.get("isSidechain") is True:
            continue
        for b in (r.get("message") or {}).get("content") or []:
            if isinstance(b, dict) and b.get("type") == "text" and b.get("text", "").strip():
                parts.append(b["text"])
    return "\n".join(parts), uid


def turn_tools(rows: list) -> list:
    """このターン（直前の まこさんの発言の後）の道具の呼び出し（名前, 入力）。"""
    last, _ = turn_bounds(rows)
    out = []
    for r in rows[last + 1:]:
        if r.get("type") != "assistant" or r.get("isSidechain") is True:
            continue
        for b in (r.get("message") or {}).get("content") or []:
            if isinstance(b, dict) and b.get("type") == "tool_use":
                out.append((b.get("name"), b.get("input") or {}))
    return out


def corpus(rows: list) -> str:
    out = [norm(user_text(r)) for r in rows]
    for d in CORPUS_DIRS:
        if not d.is_dir():
            continue
        for dp, dns, fns in os.walk(d):
            dns[:] = [x for x in dns if x not in ce.SKIP_DIRS and x != "sessions"]
            for fn in fns:
                if not fn.endswith(".md"):
                    continue
                p = Path(dp) / fn
                try:
                    if p.stat().st_size > MAX_FILE:
                        continue
                    out.append(norm(p.read_text(encoding="utf-8", errors="ignore")))
                except Exception:
                    continue
    return "\n".join(out)


# ---------------- 文の分け方 ----------------

def strip_code(text: str) -> str:
    return re.sub(r"```.*?```", "", text, flags=re.S)


def paragraphs(text: str) -> list:
    out = []
    for p in re.split(r"\n\s*\n", strip_code(text)):
        p = p.strip()
        if p:
            out.append(p)
    return out


def sentences(text: str) -> list:
    return [s for s in re.split(r"(?<=[。？！?])|\n", strip_code(text)) if s.strip()]


def has_src(s: str) -> bool:
    return SRC_RE.search(s) is not None


# ---------------- 検査 ----------------

def check_quotes(text: str, body: str) -> list:
    ng = []
    for m in QUOTE_RE.finditer(text):
        q = m.group(1)
        pieces = [x for x in (norm(y) for y in CUT_RE.split(q)) if len(x) >= 4]
        if pieces and any(x not in body for x in pieces):
            ng.append(f"R2 まこさんの言葉として書いた「{q[:60]}」が、やり取りの記録にも記録のファイルにも無い")
    return ng


def cites_in(text: str) -> set:
    out = {(b, n, raw) for b, n, raw in ce.citations(text)}
    for m in LINK_RE.finditer(text):
        out.add((Path(m.group(1)).name, int(m.group(2)), m.group(0)))
    return out


def check_cites(text: str, uses, results) -> list:
    ng = []
    for base, line, raw in sorted(cites_in(text)):
        ps = ce.find_files(base)
        if not ps:
            continue
        n_lines = 0
        for p in ps:
            try:
                with open(p, "rb") as fh:
                    n_lines = max(n_lines, sum(1 for _ in fh))
            except Exception:
                continue
        if line > n_lines:
            ng.append(f"R2b {raw}＝{base} は全{n_lines}行で、その行は無い")
        elif not ce.opened(base, line, uses, results):
            ng.append(f"R2b {raw}＝この会話で {base} の {max(1, line - ce.WINDOW)}〜{line + ce.WINDOW} 行を開いた記録が無い")
    return ng


def check_r1(text: str) -> list:
    ng = []
    for p in paragraphs(text):
        first = p.splitlines()[0]
        if first.startswith("#") or first.startswith(">") or DECL_RE.match(first):
            continue
        if len(norm(p)) < 40:
            continue
        if re.search(r"[？?]\s*$", p) or re.search(r"か。\s*$", p):
            continue
        if not has_src(p):
            ng.append(f"R1 出どころの印が無い段落＝「{norm(p)[:40]}…」（確かめた物の位置・「私の導出」・「わからない」のどれかを付ける）")
    return ng


def check_r3(text: str) -> list:
    ng = []
    # ★2026-09-28 直し＝ToDo の4行の型（【ToDo】全N件。M件 ✅済…）は ToDo ゲートが求める形で、
    #   出どころは表の各行の「記録」の欄に在る＝「【」で始まる行は見ない（見ると、決まった形を書くたびに止まる）。
    body = "\n".join(ln for ln in strip_code(text).splitlines() if not ln.lstrip().startswith("【"))
    for s in sentences(body):
        if SURE_RE.search(s) and not has_src(s):
            ng.append(f"R3 「決まった・済・確かめた・分かった」の文に根拠の位置が無い＝「{norm(s)[:40]}」")
    return ng


def check_r4(text: str) -> list:
    ng = []
    lines = strip_code(text).splitlines()
    for i, ln in enumerate(lines):
        if not COUNT_HEAD_RE.search(ln) or ITEM_RE.match(ln):
            continue
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        while j < len(lines) and ITEM_RE.match(lines[j]):
            if not has_src(lines[j]):
                ng.append(f"R4 数を挙げた後の項目に出どころが無い＝「{norm(lines[j])[:40]}」")
            j += 1
    return ng


def check_r5(text: str) -> list:
    t = text.strip()
    if not AGREE_RE.match(t):
        return []
    ps = paragraphs(t)
    head = ps[0] if ps else t
    if DECL_RE.match(head) and len(ps) > 1:
        head = head + "\n" + ps[1]
    if has_src(head):
        return []
    return ["R5 同意で始まる返信の最初の段落に、根拠の位置も「まこさんの言葉だから」も無い"]


def is_conclusion(text: str) -> bool:
    return CONC_RE.search(strip_code(text)) is not None


def check_r7(text: str) -> list:
    if is_conclusion(text) and "反対の材料" not in text:
        return ["R7 結論のある返信に「反対の材料」が無い"]
    return []


def check_turn(text: str, tools: list) -> list:
    if not is_conclusion(text):
        return []
    ng = []
    searched = wrote = False
    for name, inp in tools:
        s = json.dumps(inp, ensure_ascii=False)
        if name in ("Grep", "Read") or (name == "Bash" and re.search(r"\bgrep\b|\bsed -n\b", s)):
            if "session_worklog" in s or ".jsonl" in s:
                searched = True
        if name in ("Edit", "Write", "MultiEdit") and "session_worklog" in s:
            wrote = True
    if not searched:
        ng.append("R6 結論のある返信なのに、このターンで worklog かやり取りの記録を検索した記録が無い（前の記述と食い違わないか）")
    if not wrote:
        ng.append("R8 結論のある返信なのに、このターンで worklog を書いた記録が無い（worklog が先・チャットはその写し）")
    return ng


def judge_text(text: str, body: str | None = None, rows: list | None = None) -> list:
    """返信の本文だけで見られる検査（R1・R2・R3・R4・R5・R7）。"""
    ng = []
    ng += check_r1(text)
    if QUOTE_RE.search(text):
        ng += check_quotes(text, body if body is not None else corpus(rows or []))
    ng += check_r3(text)
    ng += check_r4(text)
    ng += check_r5(text)
    ng += check_r7(text)
    return ng


def judge(text: str, rows: list, path: str) -> list:
    ng = judge_text(text, rows=rows)
    if cites_in(text):
        uses, results = ce.load_transcript(path)
        ng += check_cites(text, uses, results)
    ng += check_turn(text, turn_tools(rows))
    return ng


def blocked_count(uid) -> int:
    try:
        d = json.load(open(COUNT, encoding="utf-8"))
        return d.get("n", 0) if d.get("uuid") == uid else 0
    except Exception:
        return 0


def record_block(uid, n) -> None:
    try:
        json.dump({"uuid": uid, "n": n}, open(COUNT, "w", encoding="utf-8"))
    except Exception:
        pass


def hook_main() -> int:
    try:
        data = json.loads(sys.stdin.read())
    except Exception:
        return 0
    path = data.get("transcript_path") or ""
    if not path or not os.path.exists(path):
        return 0
    rows = read_rows(path)
    text, uid = last_reply(rows)
    if not text.strip():
        return 0
    ng = judge(text, rows, path)
    if not ng:
        return 0
    n = blocked_count(uid)
    e = sys.stderr
    if n >= MAX_BLOCKS:
        print(f"⚠️ [嘘の型の検査] {MAX_BLOCKS} 回 止めたので通します。残っている所:", file=e)
        for x in ng:
            print(f"   ・{x}", file=e)
        return 0
    record_block(uid, n + 1)
    print("🔒 [嘘の型の検査・Stop hook] まこさん指示 2026-09-28「とにかく、虚偽発言できないようにしろ」「上記強制入れて、効果あるのか見てみるわ」。", file=e)
    print(f"   いまの返信に {len(ng)} 件（全部 一度に出しています）:", file=e)
    for x in ng:
        print(f"   ・{x}", file=e)
    print("対処: 出どころを付ける（確かめた物の位置）／「私の導出」「わからない」と書く／在るふりをしない。", file=e)
    print("      直した所だけを短く出す（前の返信を貼り直さない）。", file=e)
    return 2


# ---------------- 試し ----------------

def selftest() -> int:
    rows = [{"type": "user", "message": {"content": "この数字の値はあとで変更して、答えを作り直せるようにすること"}}]
    body = corpus(rows)
    long_ = "いまの札は、窓の中央値で切っているので、どの期間でも半分がレンジになる作りになっています。"
    uses = [("u1", "Read", {"file_path": str(HERE / "enforce_no_false_claim.py"), "offset": 30, "limit": 20})]
    cases = [
        ("T1 在る引用は通る", check_quotes("まこさん「この数字の値はあとで変更して」", body) == []),
        ("T2 作った引用は止まる", len(check_quotes("まこさんの逐語＝「役割は2つに固定する」", body)) == 1),
        ("T3 …で切った引用は断片で見る", check_quotes("まこさん「この数字の値は…答えを作り直せる」", body) == []),
        ("T4 開いていない行は止まる", len(check_cites("enforce_no_false_claim.py:40", [], {})) == 1),
        ("T5 開いた行は通る", check_cites("enforce_no_false_claim.py:40", uses, {}) == []),
        ("T6 無い行は止まる", len(check_cites("enforce_no_false_claim.py:99999", uses, {})) == 1),
        ("T7 R1 出どころの無い段落は止まる", len(check_r1(long_)) == 1),
        ("T8 R1 行番号があれば通る", check_r1(long_ + "（observe_diag.py:5831）") == []),
        ("T9 R1 私の導出と書けば通る", check_r1(long_ + "ここは私の導出です。") == []),
        ("T10 R1 短い段落と問いは見ない", check_r1("はい。") == [] and check_r1(long_[:-1] + "ですか？") == []),
        ("T11 R3 決まった に根拠が無いと止まる", len(check_r3("札の定義は決まりました。")) == 1),
        ("T12 R3 位置があれば通る", check_r3("札の定義は決まりました（記録の 1415行目）。") == []),
        ("T13 R4 数の後の項目に出どころが無いと止まる", len(check_r4("理由は2つです。\n- 常に半分\n- 幅を見ない")) == 2),
        ("T14 R4 出どころがあれば通る", check_r4("理由は1つです。\n- 常に半分（§34）") == []),
        ("T15 R5 根拠の無い同意は止まる", len(check_r5("はい。そのとおりにします。")) == 1),
        ("T16 R5 まこさんの言葉だからと書けば通る", check_r5("はい。まこさんの言葉だから、そうします。") == []),
        ("T17 R7 結論に反対の材料が無いと止まる", len(check_r7("私の答えはAです。")) == 1),
        ("T18 R7 反対の材料があれば通る", check_r7("私の答えはAです。反対の材料は1つ。") == []),
        ("T19 R6・R8 結論なのに検索も worklog も無いと2件", len(check_turn("私の答えはA", [])) == 2),
        ("T20 R6・R8 grep と Edit があれば通る",
         check_turn("私の答えはA", [("Bash", {"command": "grep -n x .claude/state/session_worklog_20260928.md"}),
                                   ("Edit", {"file_path": "/x/session_worklog_20260928.md"})]) == []),
    ]
    ok = 0
    for name, good in cases:
        print(f"  {'✅' if good else '❌'} {name}")
        ok += good
    print(f"selftest {ok}/{len(cases)} pass")
    return 0 if ok == len(cases) else 1


def scan(tp: str) -> int:
    """記録の中の私の返信を全部、本文だけで見られる検査に掛ける（止めない・効き目を数えるため）。"""
    rs = read_rows(tp)
    body = corpus(rs)
    per: dict = {}
    n_reply = n_hit = 0
    for i, r in enumerate(rs):
        if r.get("type") != "assistant" or r.get("isSidechain") is True:
            continue
        for b in (r.get("message") or {}).get("content") or []:
            if isinstance(b, dict) and b.get("type") == "text" and len(b.get("text", "")) > 40:
                n_reply += 1
                ng = judge_text(b["text"], body=body)
                if ng:
                    n_hit += 1
                for x in ng:
                    k = x.split()[0]
                    per[k] = per.get(k, 0) + 1
    print(f"返信 {n_reply} 本のうち、1件以上 当たった返信 {n_hit} 本")
    for k in sorted(per):
        print(f"  {k}: {per[k]} 件")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    if "--scan" in sys.argv:
        sys.exit(scan(sys.argv[sys.argv.index("--scan") + 1]))
    if "--try" in sys.argv:
        i = sys.argv.index("--try")
        txt, tp = sys.argv[i + 1], sys.argv[i + 2]
        for x in judge(txt, read_rows(tp), tp) or ["（止める所なし）"]:
            print(x)
        sys.exit(0)
    sys.exit(hook_main())
