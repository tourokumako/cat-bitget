#!/usr/bin/env python3
# enforce_checked_edit.py — PreToolUse on Write／Edit／MultiEdit（2026-09-14 まこさん指示・新設）
#
# まこさんの指示（逐語 2026-09-14）
#   「実物を開いて確かめていない直しは、書きません。
#    直したら、同じ事実を書いている場所を全部 grep して揃えてから出します。
#    照合を「0件になるまで」繰り返す形は作りません。
#    上記をできないように強制しろ」
#   「上記をできないではなく、上記のやり方をやるようにしろということだけど。」
#
# なぜ要るか
#   監査 cp37 の反映で、私（CC）は指摘された場所だけを直し、同じ事実を書いたほかの場所を grep せず、
#   書いた文を実物のコードで確かめないまま照合に出すことを8回 繰り返した（worklog 20260914 §47〜§56）。
#   「やめます」は守れない（違反の記録で CC が自分で気づいて止まったのは25件中1件）ので、やり方を機械でやらせる。
#
# この hook がやらせること（3つ目の「照合を繰り返さない」は limit_repeat_verification.py）
#   1. 実物を開いて確かめる
#      書き足す文に新しく出てくる「ファイル名:行番号」（`gen:`・`exec:`・`r9:`・`kb:` の略も）について、
#      この会話で その行の前後5行を実際に開いた記録が在るかを、やり取りの記録から探す。
#      開いた記録＝Read の範囲（offset・limit）／Bash の `sed -n 'A,Bp'` の範囲／Bash の grep -n などの出力に出た行番号。
#      記録が無い引用が1つでも在れば止める＝先に開かせる。サブエージェントが開いた分は数えない。
#   2. 同じ事実を揃える
#      Edit で消す文の中の「数＋単位（21本・15個 など）」「ファイル名:行番号」「§A〜§B」が、
#      直した後のファイルのほかの場所にまだ在れば、その場所を hook が全部 出して1回 止める＝grep を hook がやって見せる。
#      同じ中身をもう一度 書くときは通す（見せた記録は hook 自身が書く・CC は書けない）。
#
# 見る相手
#   Write／Edit／MultiEdit で直す、あらゆるファイル（まこさん指示 2026-09-14「設計書の元データと監査の依頼書を
#   直すとき限定ではない。あらゆる修正対応のとき」）。★最初は元データと依頼書だけに狭めて作っていた。
#
# 解除: 無し（合言葉は 2026-08-16 に全廃）。
#
# 限界（正直に）
#   ①「開いたか」は見るが、読んだ中身を正しく書いたかは見ない。
#   ②行番号を書かない主張（「この関数は law だけを出す」など）は見ない。
#   ③2 は「残っている場所を見せる」まで。揃えたかは見ない（歴史の文として残してよい場合と区別できないため）。
#   ④数・行番号・節の範囲以外の言い方で書いた同じ事実は拾わない。
#   ⑤この hook のファイル自体を書き換えれば無効にできる（明示の違反）。
#   ⑥Bash で書き替える直し（プログラムの --write など）は見ない（Write／Edit／MultiEdit だけ）。
#   ⑦置き場所を探せないファイル名の引用は見ない（探すのはリポジトリ全体・.git と __pycache__ を除く。拡張子は問わない）。
#
# 試し方: python3 .claude/hooks/enforce_checked_edit.py --try <hook の入力の json を書いたファイル>

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
SDK = ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api"
STATE = ROOT / ".claude/state/sessions"
ALIAS = {"gen": "engine_tuner_gen.py", "exec": "engine_tuner_exec.py",
         "r9": "regime_r9_diag.py", "kb": "gen_regime_kb.py"}
SEARCH_ROOTS = [ROOT]                              # リポジトリ全体（データ・結果・記録のファイルも含む）
SKIP_DIRS = {".git", "__pycache__", "node_modules"}
WINDOW = 5

# ★拡張子で絞らない（まこさん指摘 2026-09-14「行番号の引用も.mdファイルまで？？ 他のデータファイルは確認しないのか？」）
CITE_RE = re.compile(r"(?<![\w.])([A-Za-z0-9_][\w\-.]*\.[A-Za-z][A-Za-z0-9]{0,9}):(\d+)(?:〜(\d+))?")
ALIAS_RE = re.compile(r"(?<![\w/.:\-])(gen|exec|r9|kb):(\d+)(?:〜(\d+))?")
COUNT_RE = re.compile(r"(?<!\d)\d+(?:本|件|個|行|回|秒|か所|つ)")
SECT_RE = re.compile(r"§\d+〜§\d+")


def is_target(p: str) -> bool:
    return bool(p)                                 # あらゆるファイル（まこさん指示 2026-09-14）


def citations(text: str) -> set:
    out = set()
    for m in CITE_RE.finditer(text):
        out.add((m.group(1), int(m.group(2)), m.group(0)))
    for m in ALIAS_RE.finditer(text):
        out.add((ALIAS[m.group(1)], int(m.group(2)), m.group(0)))
    return out


_INDEX: dict = {}


def find_files(base: str) -> list:
    """ファイル名から置き場所を全部 探す（同じ名前が複数あれば全部・最初に呼ばれたときに1回だけ一覧を作る）。"""
    if not _INDEX:
        import os
        for r in SEARCH_ROOTS:
            for dp, dns, fns in os.walk(r):
                dns[:] = [d for d in dns if d not in SKIP_DIRS]
                for fn in fns:
                    _INDEX.setdefault(fn, []).append(Path(dp) / fn)
        _INDEX.setdefault("", [])
    return _INDEX.get(base, [])


def load_transcript(path: str):
    """やり取りの記録から、本体（サブエージェントでない）の道具の呼び出しと結果を読む。"""
    uses, results = [], {}
    try:
        f = open(path, encoding="utf-8")
    except Exception:
        return uses, results
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
                if b.get("type") == "tool_use":
                    uses.append((b.get("id"), b.get("name"), b.get("input") or {}))
                elif b.get("type") == "tool_result":
                    t = b.get("content")
                    if isinstance(t, list):
                        t = "\n".join(x.get("text", "") for x in t if isinstance(x, dict))
                    results[b.get("tool_use_id")] = t if isinstance(t, str) else ""
    return uses, results


def opened(base: str, line: int, uses, results) -> bool:
    """この会話で base の line の前後5行を開いた記録が在るか。"""
    for uid, name, inp in uses:
        if name == "Read":
            if Path(str(inp.get("file_path") or "")).name != base:
                continue
            off = int(inp.get("offset") or 1)
            lim = int(inp.get("limit") or 2000)
            if off - WINDOW <= line <= off + lim - 1 + WINDOW:
                return True
        elif name == "Bash":
            cmd = str(inp.get("command") or "")
            if base not in cmd:
                continue
            for a, b in re.findall(r"(\d+),(\d+)p", cmd):
                if int(a) - WINDOW <= line <= int(b) + WINDOW:
                    return True
            for a in re.findall(r"(?<![\d,])(\d+)p", cmd):
                if abs(int(a) - line) <= WINDOW:
                    return True
            for m in re.finditer(r"(?m)^(?:[^\s:]+:)?(\d+)[:\-]", results.get(uid, "")):
                if abs(int(m.group(1)) - line) <= WINDOW:
                    return True
    return False


def pairs_of(tool: str, ti: dict, path: Path):
    if tool == "Edit":
        return [(ti.get("old_string") or "", ti.get("new_string") or "", bool(ti.get("replace_all")))]
    if tool == "MultiEdit":
        return [(e.get("old_string") or "", e.get("new_string") or "", bool(e.get("replace_all")))
                for e in (ti.get("edits") or [])]
    cur = path.read_text(encoding="utf-8") if path.is_file() else ""
    return [(cur, ti.get("content") or "", False)]


def check_opened(pairs, transcript: str) -> list:
    """1. 新しく書き足す行番号の引用を、開いて確かめたか。"""
    new_cites = set()
    for old, new, _ in pairs:
        old_keys = {(b, n) for b, n, _ in citations(old)}
        new_cites |= {c for c in citations(new) if (c[0], c[1]) not in old_keys}
    if not new_cites:
        return []
    uses, results = load_transcript(transcript)
    ng = []
    for base, line, raw in sorted(new_cites):
        ps = find_files(base)
        if not ps:
            continue                               # 置き場を探せないファイルは見ない（限界）
        n_lines = 0
        for p in ps:
            try:
                with open(p, "rb") as fh:
                    n_lines = max(n_lines, sum(1 for _ in fh))
            except Exception:
                continue
        if line > n_lines:
            ng.append(f"`{raw}`＝{base} は全{n_lines}行なので、その行は無い")
        elif not opened(base, line, uses, results):
            ng.append(f"`{raw}`＝この会話で {base} の {max(1, line - WINDOW)}〜{line + WINDOW} 行を開いた記録が無い")
    return ng


def _toks(s: str) -> set:
    return set(COUNT_RE.findall(s)) | set(SECT_RE.findall(s)) | {c[2] for c in citations(s)}


def check_same_fact(pairs, path: Path, sid: str) -> list:
    """2. 消す文の数・行番号・節の範囲が、直した後のほかの場所に残っていないか。"""
    if not path.is_file():
        return []
    after = path.read_text(encoding="utf-8")
    removed = set()
    for old, new, rall in pairs:
        if old and old in after:
            after = after.replace(old, new) if rall else after.replace(old, new, 1)
        removed |= _toks(old) - _toks(new)
    if not removed:
        return []
    lines = after.splitlines()
    left = []
    for t in sorted(removed):
        pat = re.compile(r"(?<![\d\w])" + re.escape(t) + r"(?!\d)")
        hits = [i + 1 for i, s in enumerate(lines) if pat.search(s)]
        if hits:
            left.append((t, hits))
    if not left:
        return []
    key = hashlib.sha256(json.dumps([str(path), left], ensure_ascii=False).encode()).hexdigest()
    shown_p = STATE / (sid or "no-session") / "checked_edit_shown.json"
    try:
        shown = set(json.loads(shown_p.read_text(encoding="utf-8")))
    except Exception:
        shown = set()
    if key in shown:
        return []                                  # 同じ中身は見せ済み＝2回目は通す
    shown.add(key)
    try:
        shown_p.parent.mkdir(parents=True, exist_ok=True)
        shown_p.write_text(json.dumps(sorted(shown)), encoding="utf-8")
    except Exception:
        pass
    return [f"消す「{t}」が、直した後も {len(hits)} か所に残る（{path.name} の {', '.join(map(str, hits[:12]))} 行）"
            for t, hits in left]


def main(raw: str) -> int:
    try:
        data = json.loads(raw)
    except Exception:
        return 0                                   # 読めない入力では止めない（fail-open）
    if data.get("agent_type"):
        return 0                                   # サブエージェントは見ない
    tool = data.get("tool_name", "")
    if tool not in ("Write", "Edit", "MultiEdit"):
        return 0
    ti = data.get("tool_input") or {}
    fp = str(ti.get("file_path") or "")
    if not is_target(fp):
        return 0
    path = Path(fp)
    pairs = pairs_of(tool, ti, path)
    e = sys.stderr
    tp = str(data.get("transcript_path") or "")
    ng1 = check_opened(pairs, tp)
    if ng1 and not tp:
        print("🔒 [確かめてから直すゲート] session_id も transcript_path も無い＝開いた記録を数えられない", file=e)
        return 2
    if ng1:

        print("🔒 [確かめてから直すゲート] 実物を開いて確かめていない行番号を、書こうとしています"
              "（まこさん指示 2026-09-14「実物を開いて確かめていない直しは、書きません」）。", file=e)
        for x in ng1:
            print(f"   ❌ {x}", file=e)
        print("   ＝先にその行を Read（offset・limit）か sed -n 'A,Bp' で開き、書く中身が実物と合うか確かめてから、"
              "同じ直しをもう一度 書いてください。", file=e)
        return 2
    ng2 = check_same_fact(pairs, path, str(data.get("session_id") or ""))
    if ng2:
        print("🔒 [同じ事実を揃えるゲート] 消す数・行番号・節の範囲と同じ文字が、ほかの場所にまだ在ります"
              "（まこさん指示 2026-09-14「直したら、同じ事実を書いている場所を全部 grep して揃えてから出します」）。", file=e)
        for x in ng2:
            print(f"   ⚠️ {x}", file=e)
        print("   ＝その行を開き、同じ事実なら同じ直しを入れてください。歴史の文などで残してよいなら、"
              "同じ直しをもう一度 書けば通ります（この一覧は1回だけ出します）。", file=e)
        return 2
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--try":
        sys.exit(main(Path(sys.argv[2]).read_text(encoding="utf-8")))
    sys.exit(main(sys.stdin.read()))
