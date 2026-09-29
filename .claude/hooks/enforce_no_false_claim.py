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

2026-09-29（133回目）まこさん指示（逐語）＝「手抜きができないように強制しろ」「お前の大好きな手抜きが出来ないように強制しろ」。
  ★足した2つ（その日の手抜きの実例から作った＝worklog 20260929 §44・§45）
  R9 出す前に試す  返信の文（空白を除いて40文字以上の塊）が、同じやり取りの中で、それより前に --try に渡した
                  下書きに含まれていなければ止める。＝出してから止められて直す・試した後に書き替えて出す、を止める。
  R10 渡す前に読む  返信が設計書（acceptance.md）か監査の依頼書（*_audit_request.md）の名前を書くとき、
                  そのファイルの全行を、ファイルの最後の書き替えより後に Read した記録が無ければ止める。
                  ＝読まずに渡す・読まずに「合っている」と書く、を止める。
  ★まこさんの定義（逐語 2026-09-29）＝「そもそも手抜きとは私の依頼に対して１００％以下で返すことはすべて手抜きなんだよ。」
    「お前は常に私の依頼に対して１００％以上のものを返すべき」。R9・R10 は返信の形だけを見ていた（まこさん「強制自体が手抜き」）。
    だから、出来上がりを渡すときと、「できた」と言うときを止める2つを足した。
  R11 渡す前に節ごとに見る  設計書か依頼書を渡す返信（「チェックしてください」「監査を起動」「渡します」「承認をお願い」ほか）は、
                  その文書の見出し（## ・### ・####）の全部について、見た結果を1行ずつ書いた記録
                  （.claude/state/sessions/<セッション>/review_<文書の名前>.md・文書の最後の書き替えより後に書いたもの）が要る。
                  見出しが1つでも記録に無い・「問題あり」の行が1つでも残っていれば止める＝問題を残したまま渡せない。
  R12 できたと言う前に測る  「完了」「できました」「直しました」「作りました」「100%」「証明しました」を書く返信は、
                  このやり取りの最後の書き替え（Write・Edit・MultiEdit）より後に、確かめのコマンド
                  （--selftest・--verify・--check・--measure-only・--dry）を走らせた記録が要る。
                  その最後の確かめが通っていない（道具のエラー・❌・「N/M pass」で N と M が違う）ときも止める。

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
    body = "\n".join(ln for ln in strip_code(text).splitlines()
                     if not ln.lstrip().startswith("【"))
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


# ---------------- R9・R10（2026-09-29 追加）----------------

TRY_MIN = 40
DOC_RE = re.compile(r"(?<![\w\-.])(acceptance\.md|[\w\-.]+_audit_request\.md)")


def reply_blocks(rows: list) -> list:
    """差し戻しの後に私が書いた本文の塊（記録の位置, 文）。"""
    _, start = turn_bounds(rows)
    out = []
    for i, r in enumerate(rows):
        if i <= start or r.get("type") != "assistant" or r.get("isSidechain") is True:
            continue
        for b in (r.get("message") or {}).get("content") or []:
            if isinstance(b, dict) and b.get("type") == "text" and b.get("text", "").strip():
                out.append((i, b["text"]))
    return out


def try_drafts(rows: list) -> list:
    """直前の まこさんの発言の後に --try に渡した下書き（記録の位置, 空白を除いた文）。"""
    import shlex
    last, _ = turn_bounds(rows)
    out = []
    for i, r in enumerate(rows):
        if i <= last or r.get("type") != "assistant" or r.get("isSidechain") is True:
            continue
        for b in (r.get("message") or {}).get("content") or []:
            if not (isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "Bash"):
                continue
            cmd = str((b.get("input") or {}).get("command") or "")
            if "enforce_no_false_claim.py" not in cmd or "--try" not in cmd:
                continue
            try:
                toks = shlex.split(cmd)
            except ValueError:
                continue
            for k, t in enumerate(toks[:-1]):
                if t == "--try":
                    # ★2026-09-29＝シェルの二重引用符の中で「\`」と書いたバッククォートは、shlex では「\」が残る。
                    #   返信の側と同じく、囲み（```）を外してから比べる（直す前は、囲みの在る返信が全部 R9 に当たった）
                    #   ★本文に「\`」をそのまま書く返信もある（直した直後に当たった）ので、置き換えない形も一緒に持つ
                    out.append((i, norm(strip_code(toks[k + 1].replace("\\`", "`")))))
                    out.append((i, norm(strip_code(toks[k + 1]))))
    return out


def check_r9(blocks: list, drafts: list) -> list:
    ng = []
    for i, t in blocks:
        n = norm(strip_code(t))
        if len(n) < TRY_MIN:
            continue
        if not any(j < i and n in d for j, d in drafts):
            ng.append(f"R9 出す前に --try に通していない文＝「{n[:40]}…」"
                      "（この文を含む下書きを、出す前に --try に通す。通した後に書き替えたら、もう一度 通す）")
    return ng


def _ts(r) -> float:
    from datetime import datetime
    try:
        return datetime.fromisoformat(str(r.get("timestamp", "")).replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0


def doc_paths(base: str) -> list:
    if base == "acceptance.md":
        p = ROOT / ".claude/state/acceptance.md"
        return [p] if p.exists() else []
    p = SDK / ".claude/audits/inputs" / base
    return [p] if p.exists() else []


def read_cover(rows: list, path: Path, after: float) -> set:
    """after より後に Read で開いた行の番号の集まり（offset と limit から数える）。"""
    got: set = set()
    for r in rows:
        if r.get("type") != "assistant" or r.get("isSidechain") is True or _ts(r) <= after:
            continue
        for b in (r.get("message") or {}).get("content") or []:
            if not (isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "Read"):
                continue
            inp = b.get("input") or {}
            try:
                if Path(str(inp.get("file_path", ""))).resolve() != path.resolve():
                    continue
            except Exception:
                continue
            off = int(inp.get("offset") or 1)
            lim = int(inp.get("limit") or 2000)
            got.update(range(max(1, off), off + lim))
    return got


def check_r10(text: str, rows: list, paths=None) -> list:
    ng = []
    for base in sorted(set(DOC_RE.findall(strip_code(text)))):
        for p in (paths or doc_paths)(base):
            try:
                with open(p, "rb") as fh:
                    n_lines = sum(1 for _ in fh)
                mt = p.stat().st_mtime
            except Exception:
                continue
            miss = [k for k in range(1, n_lines + 1) if k not in read_cover(rows, p, mt)]
            if miss:
                ng.append(f"R10 {base} に触れたのに、最後の書き替えの後に全行を Read していない"
                          f"（全{n_lines}行のうち読んでいない行 {len(miss)} 行・最初は {miss[0]} 行目）")
    return ng


HAND_RE = re.compile(r"チェックしてください|確認してください|監査を起動|渡します|お渡しします|承認をお願い|approve_impl")
CLAIM_RE = re.compile(r"完了|できました|直しました|作りました|100\s?%|１００％|証明しました")
PROOF_RE = re.compile(r"--selftest|--verify|--check|--measure-only|--dry\b")
HEAD_RE = re.compile(r"^(#{2,4})\s+(.+?)\s*$")


def doc_headings(path: Path) -> list:
    """文書の見出し（## ・### ・####）の文。囲み（``` と ~~~）の中は数えない。"""
    out, fence = [], None
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except Exception:
        return out
    for ln in lines:
        s = ln.strip()
        if s.startswith("```") or s == "~~~":
            mark = s[:3]
            fence = None if fence == mark else (fence or mark)
            continue
        if fence:
            continue
        m = HEAD_RE.match(ln)
        if m:
            out.append(m.group(2))
    return out


def review_path(sid: str, base: str, rdir: Path = None) -> Path:
    return (rdir or ROOT / ".claude/state/sessions" / (sid or "_nosession")) / f"review_{base}"


def check_r11(text: str, sid: str, paths=None, rdir: Path = None) -> list:
    body = strip_code(text)
    if not HAND_RE.search(body):
        return []
    ng = []
    for base in sorted(set(DOC_RE.findall(body))):
        for p in (paths or doc_paths)(base):
            rp = review_path(sid, base, rdir)
            if not rp.exists():
                ng.append(f"R11 {base} を渡すのに、節ごとに見た記録が無い（{rp}）")
                continue
            try:
                if rp.stat().st_mtime <= p.stat().st_mtime:
                    ng.append(f"R11 {base} の節ごとの記録が、文書の最後の書き替えより前のもの（見直していない）")
                    continue
                rv = open(rp, encoding="utf-8").read()
            except Exception:
                continue
            miss = [h for h in doc_headings(p) if norm(h) not in norm(rv)]
            bad = [ln for ln in rv.splitlines() if "問題あり" in ln]
            if miss:
                ng.append(f"R11 {base} の見出しのうち、見た記録に無いもの {len(miss)} 個（最初＝「{miss[0][:40]}」）")
            if bad:
                ng.append(f"R11 {base} に「問題あり」が {len(bad)} 行 残ったまま渡そうとしている（最初＝「{norm(bad[0])[:40]}」）")
    return ng


def check_r12(text: str, rows: list) -> list:
    if not CLAIM_RE.search(strip_code(text)):
        return []
    last, _ = turn_bounds(rows)
    last_edit, last_proof, proof_id = -1, -1, None
    results: dict = {}
    for r in rows:
        if r.get("type") != "user":
            continue
        c = (r.get("message") or {}).get("content")
        for b in c if isinstance(c, list) else []:
            if isinstance(b, dict) and b.get("type") == "tool_result":
                body = b.get("content")
                if isinstance(body, list):
                    body = "\n".join(x.get("text", "") for x in body if isinstance(x, dict))
                results[b.get("tool_use_id")] = (bool(b.get("is_error")), str(body or ""))
    for i, r in enumerate(rows):
        if i <= last or r.get("type") != "assistant" or r.get("isSidechain") is True:
            continue
        for b in (r.get("message") or {}).get("content") or []:
            if not (isinstance(b, dict) and b.get("type") == "tool_use"):
                continue
            name, inp = b.get("name"), b.get("input") or {}
            if name in ("Write", "Edit", "MultiEdit") and "session_worklog" not in str(inp.get("file_path", "")) \
                    and "/sessions/" not in str(inp.get("file_path", "")) and "chat_draft" not in str(inp.get("file_path", "")):
                last_edit = i
            if name == "Bash" and PROOF_RE.search(str(inp.get("command", ""))) and "--try" not in str(inp.get("command", "")):
                last_proof, proof_id = i, b.get("id")
    if last_edit >= 0 and last_proof <= last_edit:
        return ["R12 「できた」と書いたのに、このやり取りの最後の書き替えより後に、確かめのコマンド"
                "（--selftest・--verify・--check・--measure-only・--dry）を走らせた記録が無い"]
    # ★2026-09-29 追加（走らせたかだけを見るのは手抜き）＝最後の確かめが通っていなければ止める
    err, out = results.get(proof_id, (False, ""))
    if proof_id and (err or "❌" in out or re.search(r"Exit code [1-9]", out) or re.search(r"\b\d+/\d+ pass", out)
                     and not all(a == b for a, b in re.findall(r"\b(\d+)/(\d+) pass", out))):
        return ["R12 「できた」と書いたのに、最後の確かめのコマンドが通っていない（失敗・❌・pass の数が足りない）"]
    return []


# ★2026-09-29＝R13・R14（依頼の台帳）は削除した。まこさん指示（逐語）「トークンの無駄になるだけの強制は削除しろ」
#   「この意味のない強制を削除しろっていってんの」。発言のたびに作業を止め、番号だらけの行を返信に入れさせた（worklog §56・§57）。


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


def judge(text: str, rows: list, path: str, hook: bool = False, sid: str = "") -> list:
    ng = judge_text(text, rows=rows)
    if cites_in(text):
        uses, results = ce.load_transcript(path)
        ng += check_cites(text, uses, results)
    ng += check_turn(text, turn_tools(rows))
    ng += check_r10(text, rows)
    ng += check_r11(text, sid or Path(path).stem)
    ng += check_r12(text, rows)
    if hook:
        # ★R9 は出した後の記録を見る（--try のときは、試している文そのものなので見ない）
        ng += check_r9(reply_blocks(rows), try_drafts(rows))
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
    ng = judge(text, rows, path, hook=True, sid=str(data.get("session_id") or ""))
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
    # ★R9〜R12（2026-09-29）の試し＝まこさん指示「手抜きができないように強制しろ」
    import tempfile
    import time as _t
    from datetime import datetime, timezone

    def _row(i_ts, blocks):
        ts = datetime.fromtimestamp(i_ts, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        return {"type": "assistant", "timestamp": ts, "message": {"content": blocks}}

    def _tool(name, inp):
        return {"type": "tool_use", "name": name, "input": inp}

    tmpd = Path(tempfile.mkdtemp(prefix="_nfc_selftest_", dir=str(ROOT / ".claude/state")))
    try:
        doc = tmpd / "acceptance.md"
        doc.write_text("# 題\n## 1｜概要\n本文\n### 1-1 小見出し\n```\n## 囲みの中\n```\n", encoding="utf-8")
        mt = doc.stat().st_mtime
        pf = lambda base: [doc] if base == "acceptance.md" else []  # noqa: E731
        n_doc = len(doc.read_text(encoding="utf-8").splitlines())
        rd_all = [_row(mt + 5, [_tool("Read", {"file_path": str(doc)})])]
        rd_half = [_row(mt + 5, [_tool("Read", {"file_path": str(doc), "offset": 1, "limit": 2})])]
        rd_old = [_row(mt - 5, [_tool("Read", {"file_path": str(doc)})])]
        rv = tmpd / "review_acceptance.md"
        cases += [
            ("T21 R9 試していない長い文は止まる",
             [x[:2] for x in check_r9([(5, long_)], [])] == ["R9"]),
            ("T22 R9 前に試した下書きに含まれれば通る", check_r9([(5, long_)], [(3, norm("前置き" + long_))]) == []),
            ("T23 R9 試した後に書き替えると止まる",
             [x[:2] for x in check_r9([(5, long_ + "あとから足した文です。")], [(3, norm(long_))])] == ["R9"]),
            ("T24 R9 出した後に試しても止まる", [x[:2] for x in check_r9([(5, long_)], [(7, norm(long_))])] == ["R9"]),
            ("T25 R10 書き替えの後に全行を読めば通る", check_r10("acceptance.md を見た", rd_all, pf) == [] and n_doc == 7),
            ("T26 R10 一部しか読まないと止まる（読んでいない行＝3〜7行目の5行）",
             any("読んでいない行 5 行・最初は 3 行目" in x for x in check_r10("acceptance.md を見た", rd_half, pf))),
            ("T27 R10 書き替えの前に読んだだけだと止まる（7行とも読んでいない扱い）",
             any("読んでいない行 7 行" in x for x in check_r10("acceptance.md を見た", rd_old, pf))),
        ]
        hand = "acceptance.md をチェックしてください"
        _r28 = check_r11(hand, "s", pf, tmpd)
        cases.append(("T28 R11 記録が無いと止まる（理由＝記録が無い）", len(_r28) == 1 and "見た記録が無い" in _r28[0]))
        _t.sleep(0.02)
        rv.write_text("- 1｜概要：問題なし\n- 1-1 小見出し：問題なし\n", encoding="utf-8")
        _r29 = check_r11(hand, "s", pf, tmpd)
        if _r29:
            print(f"   （T29 の止め＝{_r29}）")
        cases.append(("T29 R11 見出しを全部 見て問題なしなら通る（囲みの中は数えない）", _r29 == []))
        rv.write_text("- 1｜概要：問題なし\n", encoding="utf-8")
        _r30 = check_r11(hand, "s", pf, tmpd)
        cases.append(("T30 R11 見出しが記録に無いと止まる（理由＝見た記録に無い）",
                      len(_r30) == 1 and "見た記録に無いもの 1 個" in _r30[0] and "1-1" in _r30[0]))
        rv.write_text("- 1｜概要：問題なし\n- 1-1 小見出し：問題あり（数字が無い）\n", encoding="utf-8")
        _r31 = check_r11(hand, "s", pf, tmpd)
        cases.append(("T31 R11 問題ありが残ると止まる（理由＝問題ありが残る）",
                      len(_r31) == 1 and "問題あり」が 1 行" in _r31[0]))
        cases.append(("T32 R11 渡す言葉が無ければ見ない", check_r11("acceptance.md を読みます", "s", pf, tmpd) == []))
        _t.sleep(0.02)
        doc.write_text(doc.read_text(encoding="utf-8") + "## 2｜足した節\n", encoding="utf-8")
        rv.write_text("- 1｜概要：問題なし\n- 1-1 小見出し：問題なし\n- 2｜足した節：問題なし\n", encoding="utf-8")
        _t.sleep(0.02)
        doc.write_text(doc.read_text(encoding="utf-8") + "本文を足した\n", encoding="utf-8")
        _r33 = check_r11(hand, "s", pf, tmpd)
        cases.append(("T33 R11 文書を後から書き替えると、古い記録では止まる（理由＝書き替えより前の記録）",
                      len(_r33) == 1 and "最後の書き替えより前" in _r33[0]))
        cases.append(("T28b R11 記録の名前は review_<文書の名前>（.md を2回 付けない）",
                      review_path("s", "acceptance.md", tmpd).name == "review_acceptance.md"))
        user = {"type": "user", "message": {"content": "やって"}}
        ed = _row(0, [_tool("Edit", {"file_path": "/x/tool.py"})])
        pr = _row(0, [dict(_tool("Bash", {"command": "python3 tool.py --selftest"}), id="p1")])
        pr_ok = {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "p1",
                                                          "content": "selftest 5/5 pass"}]}}
        pr_ng = {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "p1",
                                                          "content": "❌ T3\nselftest 4/5 pass"}]}}
        cases.append(("T37 R12 最後の確かめが通っていないと止まる（4/5 pass）",
                      any("通っていない" in x for x in check_r12("できました", [user, ed, pr, pr_ng]))))
        cases.append(("T38 R12 最後の確かめが通っていれば通る（5/5 pass）", check_r12("できました", [user, ed, pr, pr_ok]) == []))
        trow =[{"type": "user", "message": {"content": "直して"}},
                {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash", "input": {
                    "command": "python3 enforce_no_false_claim.py --try \"" + long_ + "\n\\`\\`\\`\n台帳の1行\n\\`\\`\\`\" x.jsonl"}}]}}]
        cases.append(("T45 R9 下書きの中の「\\`」と囲みを、返信と同じに読む",
                      check_r9([(9, long_ + "\n```\n台帳の1行\n```")], try_drafts(trow)) == []))
        trow2 = [{"type": "user", "message": {"content": "直して"}},
                 {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash", "input": {
                     "command": "python3 enforce_no_false_claim.py --try \"" + long_ + "下書きの「\\`」と書いた。\" x.jsonl"}}]}}]
        cases.append(("T46 R9 本文に「\\`」をそのまま書いた返信も、試した下書きと合う",
                      check_r9([(9, long_ + "下書きの「\\`」と書いた。")], try_drafts(trow2)) == []))
        cases += [
            ("T34 R12 書き替えの後に確かめれば「できました」は通る", check_r12("できました", [user, ed, pr]) == []),
            ("T35 R12 確かめの後に書き替えると止まる", [x[:3] for x in check_r12("直しました", [user, pr, ed])] == ["R12"]),
            ("T36 R12 できたと書かなければ見ない", check_r12("読みます", [user, ed]) == []),
        ]
    finally:
        import shutil
        shutil.rmtree(tmpd, ignore_errors=True)
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
