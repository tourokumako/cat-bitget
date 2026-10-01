#!/usr/bin/env python3
# enforce_audit_docs.py — hook 10（監査の依頼書）と hook 11（監査の結果）の本体（2026-09-15 まこさん指示・新設）
#
# まこさんの指示（逐語 2026-09-15）
#   「じゃあ、監査の依頼書と結果で項目をそろえて、テンプレ以外では書かないように強制すればいいじゃん。」
#   流れの「強制hook作成✕３ 1.監査依頼書をテンプレから自動生成 2.監査結果をテンプレから自動生成
#     3.監査結果のテンプレから自動生成で修正する」のうち、1 と 2（3 は修正項目を当てるプログラムができてから）。
#
# なぜ要るか
#   監査レポート CP37 を監査結果のテンプレに当てはめたら、齟齬とヌケモレが多数出た（worklog 20260915 §11）。
#   依頼書は CC が手で書き、結果は依頼書ごとに CC が手で書いた出力の指示に従っていた。
#
# 何を止めるか
#   request（hook 10・enforce_audit_request_gen.sh から呼ぶ）
#     ①SDK/.claude/audits/inputs/<名前>_audit_request.md への Write・Edit・MultiEdit を全部 止める
#       ＝依頼書は .claude/tools/gen_audit_docs.py request でしか作れない（手で書けない・直せない）。
#     ②Bash で「_audit_request.md」を含む断片のうち、読むだけのコマンドでも gen_audit_docs.py でもないものを止める。
#   report（hook 11・enforce_audit_report_form.sh から呼ぶ）
#     ①SDK/.claude/audits/<名前>_audit_report.md への Edit・MultiEdit と、既に在るファイルへの Write を止める
#       ＝一度出した結果は書き替えない（あとから取り下げを書き足す道も無くなる）。
#     ②新しい結果の Write は、中身が次の全部を満たすときだけ通す
#       ・gen_audit_docs.py result の目印が在り、目印の依頼書が inputs の依頼書である
#       ・gen_audit_docs.check_lines（依頼書と1対1で対応）に ❌ が無い
#       ・gen_audit_docs.form_errors（修正の指示の6つの欄・書けないもの・「<監査が書く>」の残り）が0件
#     ③Bash で「_audit_report.md」を含む断片は、request の②と同じ判定。
#   ★判定の中身は gen_audit_docs.py の関数を呼ぶ（2か所に書き写さない）。
#
# 解除: 無し（2026-08-16 まこさん指示「じゃあ強制解除できない状態にしろ」で全廃）。
#
# 限界（正直に）
#   ①Bash のコマンドの文字に名前が出てこない書き方（変数で組み立てる・別の .py の中で書く）はすり抜ける。
#   ②gen_audit_docs.py そのものを書き替えれば、道具の照らしを外せる（git diff には出る）。
#   ③中身の文が正しいかは見ない（見るのは形と対応だけ）。
#   ④「取り下げ」など書けないものの語を、所見の説明の中で普通に使っても止まる。
#   ⑤この hook のファイル自体を書き換えれば無効にできる（明示の違反）。
#
# 試し方: python3 .claude/hooks/enforce_audit_docs.py <request|report> --try <hook の入力の json を書いたファイル>

import json
import os
import re
import sys

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
sys.path.insert(0, os.path.join(ROOT, ".claude", "tools"))

import gen_audit_docs as g                                     # noqa: E402

REQ_RE = re.compile(r"/\.claude/audits/inputs/[^/_][^/]*_audit_request\.md$")
REP_RE = re.compile(r"/\.claude/audits/[^/]+_audit_report\.md$")
READONLY = ("cat", "grep", "rg", "ls", "wc", "head", "tail", "diff", "shasum", "stat", "find", "awk", "sed", "git")
GIT_OK = ("status", "log", "diff", "show", "add", "commit", "ls-files", "grep", "rev-parse", "cat-file")
FIND_RUN = ("-exec", "-execdir", "-ok", "-okdir", "-delete", "-fprint", "-fprintf", "-fls")
TOOL = "gen_audit_docs.py"
# ★2026-09-16（設計書 audit-autofix-apply-20260916・まこさん承認）＝監査結果を読む道具を1本 足した。
#   `apply_audit_fix.py` は監査結果を**読むだけ**で、結果ファイルには1バイトも書かない
#   （書く先は監査結果の「対象のファイル」の欄。守りの仕組みには道具の側で書かない）。
# ★2026-10-01（142回目・まこさん「チェック項目を見直しすべきでは？」→ 案に「それならばOK」）＝出す前の見直し表の道具を足した。
#   `gen_review.py` は依頼書・結果を**読むだけ**で、書く先は見直し表の置き場（.claude/state/reviews/・cp<N>_work/）だけ。
TOOLS = (TOOL, "apply_audit_fix.py", "gen_review.py")


def abs_path(p: str, cwd: str) -> str:
    if not p:
        return ""
    return os.path.realpath(p if os.path.isabs(p) else os.path.join(cwd or ROOT, p))


def bash_bad_parts(cmd: str, word: str) -> list:
    """word を含む断片のうち、読むだけのコマンドでも gen_audit_docs.py でもないものを返す。"""
    bad = []
    for seg in re.split(r"[;\n]|&&|\|\|", cmd):
        for part in seg.split("|"):
            if word not in part:
                continue
            for tgt in re.findall(r"\d*>>?\s*([^\s;&|]+)", part):
                if tgt not in ("/dev/null", "&1", "&2", "&-"):
                    bad.append(part.strip())
                    break
            else:
                toks = part.split()
                while toks and re.match(r"^[A-Za-z_][A-Za-z_0-9]*=", toks[0]):
                    toks.pop(0)
                if not toks:
                    continue
                head = toks[0].rsplit("/", 1)[-1]
                if re.match(r"^python[0-9.]*$", head):
                    args = [t for t in toks[1:] if not t.startswith("-")]
                    if not (args and args[0].rsplit("/", 1)[-1] in TOOLS):
                        bad.append(part.strip())
                elif head not in READONLY:
                    bad.append(part.strip())
                elif head == "sed" and any(t.startswith("-i") or t == "--in-place" for t in toks):
                    bad.append(part.strip())
                elif head == "find" and any(t in FIND_RUN for t in toks):
                    bad.append(part.strip())
                elif head == "git":
                    rest = [t for t in toks[1:] if not t.startswith("-")]
                    if not rest or rest[0] not in GIT_OK:
                        bad.append(part.strip())
    return bad


def say(lines: list) -> int:
    for ln in lines:
        print(ln, file=sys.stderr)
    return 2


def gate_request(tool: str, ti: dict, cwd: str) -> int:
    if tool in ("Write", "Edit", "MultiEdit"):
        p = abs_path(ti.get("file_path", ""), cwd)
        if not REQ_RE.search(p):
            return 0
        return say([
            "🔒 [hook 10・監査の依頼書は道具でしか作れない] 依頼書を Write / Edit で書こうとしています。",
            "   まこさん指示 2026-09-15「監査の依頼書と結果で項目をそろえて、テンプレ以外では書かないように強制すればいいじゃん。」",
            "   ＝依頼書は、元データ（文だけを書いた .md）から道具で作ります。依頼書そのものは手で書けず、直せません。",
            "   対処＝ python3 .claude/tools/gen_audit_docs.py request <元データ.md> <依頼書.md>",
            "   直すときは元データを直して、道具で作り直します（道具が上書きするのは、道具が作ったまま書き替えられておらず、結果ファイルがまだ無い依頼書だけ）。",
        ])
    if tool == "Bash":
        bad = bash_bad_parts(ti.get("command") or "", "_audit_request.md")
        if bad:
            return say(["🔒 [hook 10・監査の依頼書は道具でしか作れない] Bash で依頼書に触る、読むだけでないコマンドがあります。",
                        *[f"   ❌ {b}" for b in bad],
                        "   通るもの＝読むだけのコマンド（cat・grep・ls・wc・head・tail・diff・shasum・stat・find・awk・sed（-i なし）・git の読む語と add・commit）",
                        "             と python3 .claude/tools/gen_audit_docs.py。"])
    return 0


def gate_report(tool: str, ti: dict, cwd: str) -> int:
    if tool in ("Write", "Edit", "MultiEdit"):
        p = abs_path(ti.get("file_path", ""), cwd)
        if not REP_RE.search(p):
            return 0
        head = ["🔒 [hook 11・監査の結果はテンプレの形でしか書けない]",
                "   まこさん指示 2026-09-15「監査の依頼書と結果で項目をそろえて、テンプレ以外では書かないように強制すればいいじゃん。」"]
        if tool != "Write":
            return say(head + ["   一度出した結果ファイルは、Edit で書き替えられません（あとから取り下げを書き足す道も止めています）。"])
        if os.path.exists(p):
            return say(head + ["   既に在る結果ファイルは、上書きできません。"])
        content = ti.get("content") or ""
        errs = []
        _, mark = g.split_mark(content)
        req_rel = mark.get("request")
        if not req_rel:
            errs.append("結果に gen_audit_docs の目印が無い（python3 .claude/tools/gen_audit_docs.py result で作った骨組みから書いていない）")
        else:
            req = os.path.join(g.ROOT, req_rel)
            if not os.path.isfile(req):
                errs.append(f"目印の依頼書が無い: {req_rel}")
            else:
                if not REQ_RE.search(os.path.realpath(req)):
                    errs.append(f"目印の依頼書が inputs の依頼書ではない: {req_rel}")
                errs += [ln[2:] for ln in g.check_lines(req, content) if ln.startswith("❌ ")]
        errs += g.form_errors(content)
        # ★2026-10-01（142回目・まこさん「監査結果を出す前に見直しチェックをさせる強制の内容も怪しいので、再度確認→修正すべきなのでは？」
        #   → 案に「それならばOK」）＝形だけでなく、出す前の見直し表（gen_review.py）が、この中身の全項目（見出し）を
        #   ①意味が通じるか ②実物と合うか（根拠＝ファイル名:行番号・実在する行）③争点に合うか で埋めているかを照らす。
        #   表の置き場＝SDK/.claude/audits/cp<N>_work/cp<N>_result.review.md（作業場の結果と同じ表）。
        try:
            import gen_review                                     # noqa: E402
            ng_r, _refs = gen_review.check(p, text=content)
        except Exception as e:                                    # noqa: BLE001
            ng_r = [f"見直し表を照らせない（{type(e).__name__}: {e}）"]
        errs += [f"見直し表: {x}" for x in ng_r]
        if errs:
            return say(head + ["   結果の中身が、テンプレの形と依頼書との対応・出す前の見直し表を満たしていません。"]
                       + [f"   ❌ {e}" for e in errs]
                       + ["   書く前の確かめ方＝作業場に書いてから python3 .claude/tools/gen_audit_docs.py check <依頼書> <結果> と form <結果>",
                          "   見直し表＝python3 .claude/tools/gen_review.py --skeleton <作業場の結果> → 全部の行を埋める → --check <作業場の結果>"])
        return 0
    if tool == "Bash":
        bad = bash_bad_parts(ti.get("command") or "", "_audit_report.md")
        if bad:
            return say(["🔒 [hook 11・監査の結果はテンプレの形でしか書けない] Bash で結果ファイルに触る、読むだけでないコマンドがあります。",
                        *[f"   ❌ {b}" for b in bad],
                        "   結果ファイルは Write で1回だけ書きます（中身は hook 11 が照らします）。"])
    return 0


def main(mode: str, raw: str) -> int:
    try:
        data = json.loads(raw)
    except Exception:
        return 0                                   # 読めない入力では止めない（fail-open）
    tool = data.get("tool_name") or ""
    ti = data.get("tool_input") or {}
    cwd = data.get("cwd") or ROOT
    if mode == "request":
        return gate_request(tool, ti, cwd)
    if mode == "report":
        return gate_report(tool, ti, cwd)
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[2] == "--try":
        # 試しのときだけ＝tool_input の "content_file" に書いたファイルの中身を content に入れる（長い中身を json に書かないため）
        _d = json.load(open(sys.argv[3], encoding="utf-8"))
        _ti = _d.get("tool_input") or {}
        if "content_file" in _ti:
            _ti["content"] = open(os.path.join(ROOT, _ti.pop("content_file")), encoding="utf-8").read()
        sys.exit(main(sys.argv[1], json.dumps(_d, ensure_ascii=False)))
    if len(sys.argv) == 2:
        sys.exit(main(sys.argv[1], sys.stdin.read()))
    print("使い方: enforce_audit_docs.py <request|report> [--try <json>]", file=sys.stderr)
    sys.exit(0)
