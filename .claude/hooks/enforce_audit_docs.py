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
#         python3 .claude/hooks/enforce_audit_docs.py --selftest（Bash の見分け方と依頼書への Write・2026-10-17 に足した）

import json
import os
import re
import sys

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
sys.path.insert(0, os.path.join(ROOT, ".claude", "tools"))

import gen_audit_docs as g                                     # noqa: E402

# ★2026-10-18（監査 CP80）＝大文字と小文字を区別しない（macOS の APFS は …_AUDIT_REPORT.md が …_audit_report.md と同じファイル＝Edit で一度出した結果を書き替えられた）
REQ_RE = re.compile(r"/\.claude/audits/inputs/[^/_][^/]*_audit_request\.md$", re.I)
REP_RE = re.compile(r"/\.claude/audits/[^/]+_audit_report\.md$", re.I)
READONLY = ("cat", "grep", "rg", "ls", "wc", "head", "tail", "diff", "shasum", "stat", "find", "awk", "sed", "git", "jq",
            "cmp")   # jq と cmp＝2026-10-17（cmp は2つのファイルを比べるだけ・まこさん「含めてOK」）
GIT_OK = ("status", "log", "diff", "show", "add", "commit", "ls-files", "grep", "rev-parse", "cat-file")
FIND_RUN = ("-exec", "-execdir", "-ok", "-okdir", "-delete", "-fprint", "-fprintf", "-fls")
TOOL = "gen_audit_docs.py"
# ★2026-09-16（設計書 audit-autofix-apply-20260916・まこさん承認）＝監査結果を読む道具を1本 足した。
#   `apply_audit_fix.py` は監査結果を**読むだけ**で、結果ファイルには1バイトも書かない
#   （書く先は監査結果の「対象のファイル」の欄。守りの仕組みには道具の側で書かない）。
# ★2026-10-01（142回目・まこさん「チェック項目を見直しすべきでは？」→ 案に「それならばOK」）＝出す前の見直し表の道具を足した。
#   `gen_review.py` は依頼書・結果を**読むだけ**で、書く先は見直し表の置き場（.claude/state/reviews/・cp<N>_work/）だけ。
TOOLS = (TOOL, "apply_audit_fix.py", "gen_review.py", "try_hooks.py")   # try_hooks.py＝hook に入力を渡すだけ（2026-10-17）


def abs_path(p: str, cwd: str) -> str:
    if not p:
        return ""
    return os.path.realpath(p if os.path.isabs(p) else os.path.join(cwd or ROOT, p))


def _strip_text(cmd: str) -> str:
    """★2026-10-17（183回目）＝ヒアドキュメントの中身と引用符の中を外す（enforce_purpose_gate の strip_text と同じ外し方）。
      直す前は外さなかったので、引用符の中の空白で区切り（30日で17回）、文の中の名前で止めた（11回）。"""
    # ★2026-10-18（監査 CP79 の修正）＝引用符の中が、空白も区切りの文字（; | & < > ( ) $ ` \）も含まない1語（パス）のときは、
    #   引用符だけを外して中身を残す。中身ごと消すと、引用符で囲んだ依頼書のパス（rm -f "…_audit_request.md"）が見えなくなって通った。
    #   空白や区切りを含む中身（文・grep -E の候補 "GO|NO-GO"・sed の行の指定 '1p;5p'・試しの道具の --bash "…"）は、いままでどおり消す。
    #   ヒアドキュメントは1行目（<< の在る行）を残し、2行目から終わりの印までだけを外す。1行目まで外すと、
    #   同じ行の書き出し（cat <<'EOF' > …_audit_request.md）が見えなくなって通った。
    s = re.sub(r"(<<-?\s*[\"']?(\w+)[\"']?[^\n]*)\n.*?^\s*\2\s*$", r"\1", cmd or "", flags=re.S | re.M)

    def _q(m):
        inner = m.group(0)[1:-1]
        return inner if inner and not re.search(r"[\s;|&<>()$`\\]", inner) else m.group(0)[0] * 2

    s = re.sub(r'"[^"]*"', _q, s)
    return re.sub(r"'[^']*'", _q, s)


def _is_doc(t: str, word: str) -> bool:
    """書く先 t が、依頼書・結果ファイルそのものか（名前が word で終わり、作業の置き場 .claude/state の外）。
    ★2026-10-17＝作業の置き場の見直し表（review_<依頼書の名前>）は、名前の終わりが同じでも依頼書ではない。"""
    return t.rstrip("/").endswith(word) and ".claude/state/" not in t


def bash_bad_parts(cmd: str, word: str) -> list:
    """word を含む断片のうち、word のファイルを書き替える・消す・動かすものを返す。
    ★2026-10-17（183回目・まこさん「要だが過剰なので、CCの案で修正」）＝直す前は、word を含む断片の頭の語が
      読むだけの語か許した道具でなければ止め、書き出し（>）が在れば書く先に関わらず止めた。直近30日で hook 10 が止めた
      49回のうち47回は、依頼書に触れない操作だった。直した後＝引用符とヒアドキュメントの中を見ない・頭の time と timeout を
      読み飛ばす・書き出しは書く先が word のときだけ止める・cp は写す先が word のときだけ止める・jq を読むだけの語に足す。
      rm・mv・tee・sed -i・ほかの書く語と、許していない python の道具は、いままでどおり止める。"""
    bad = []
    s = _strip_text(cmd)
    # ★2026-10-18（監査 CP80）＝変数に入れた word のパス（D=…_audit_report.md; cp a $D）は、使う所に値を戻してから見る。
    #   直す前は、代入の区切りは頭の語が無いので飛ばし、$D を使う区切りには word の文字が無いので見ず、通った。
    for n, v in re.findall(r"(?:^|[\s;&|(])(?:export\s+)?([A-Za-z_][A-Za-z_0-9]*)=([^\s;&|]+)", s):
        if word in v:
            s = re.sub(r"\$\{?" + n + r"\}?(?![A-Za-z_0-9])", lambda _m, v=v: v, s)
    for seg in re.split(r"[;\n]|&&|\|\|", s):
        for part in seg.split("|"):
            if word not in part:
                continue
            outs = [t for t in re.findall(r"\d*>>?\s*([^\s;&|]+)", part) if t not in ("/dev/null", "&1", "&2", "&-")]
            if any(_is_doc(t, word) for t in outs):
                bad.append(part.strip())                 # 書く先が word のファイル
                continue
            body = re.sub(r"\d*>>?\s*[^\s;&|]+", " ", part)
            toks = body.split()
            while toks and re.match(r"^[A-Za-z_][A-Za-z_0-9]*=", toks[0]):
                toks.pop(0)
            while toks and toks[0] in ("time", "timeout"):
                toks.pop(0)
                if toks and re.match(r"^\d+[smh]?$", toks[0]):
                    toks.pop(0)                          # timeout の秒数
            if not toks:
                continue
            head = toks[0].rsplit("/", 1)[-1]
            args = [t for t in toks[1:] if not t.startswith("-")]
            if re.match(r"^python[0-9.]*$", head):
                if not (args and args[0].rsplit("/", 1)[-1] in TOOLS):
                    bad.append(part.strip())
            elif head == "cp":
                # ★2026-10-18（監査 CP79 の修正）＝word の名前のファイルを、依頼書の置き場（audits/inputs）か結果の置き場（audits）へ
                #   写す cp も止める（写す先が置き場のときは、名前が写す元から付くので、写す先の名前だけでは見えなかった）
                dest = args[-1].rstrip("/") if args else ""
                into_dir = (len(args) >= 2 and any(a.rstrip("/").endswith(word) for a in args[:-1])
                            and dest.endswith("/audits/inputs" if word.endswith("_request.md") else "/audits")
                            and ".claude/state/" not in dest)
                if args and (_is_doc(args[-1], word) or into_dir):
                    bad.append(part.strip())             # 写す先が word のファイルか、word の名前のファイルを置き場へ写す（写す元が word なのは読むだけ）
            elif head not in READONLY:
                bad.append(part.strip())                 # rm・mv・tee・touch・ほかの書く語
            elif head == "sed" and any(t.startswith("-i") or t == "--in-place" for t in toks):
                bad.append(part.strip())
            elif head == "find" and any(t in FIND_RUN for t in toks):
                bad.append(part.strip())
            elif head == "git":
                rest = toks[1:]
                if len(rest) >= 2 and rest[0] == "-C":
                    rest = rest[2:]                      # git -C <置き場> <命令>
                rest = [t for t in rest if not t.startswith("-")]
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
                        "   通るもの＝読むだけのコマンド（cat・grep・ls・wc・head・tail・diff・shasum・stat・find・awk・sed（-i なし）・jq・cmp・git の読む語と add・commit）",
                        "             と python3 .claude/tools/gen_audit_docs.py（apply_audit_fix.py・gen_review.py・try_hooks.py も）。頭の time と timeout は読み飛ばす。",
                        "             ヒアドキュメントの2行目から終わりの印までは見ない。引用符の中は、空白も区切りも無い1語（パス）だけ見る（監査 CP79・2026-10-18）。写す元が依頼書の cp と、依頼書でない所への書き出しも通る（2026-10-17）。"])
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


def selftest() -> int:
    """★2026-10-17（183回目）＝Bash の見分け方（bash_bad_parts）と、依頼書への Write を試す。何も書かない。"""
    req = "SDK/.claude/audits/inputs/x_audit_request.md"
    rep = "SDK/.claude/audits/x_audit_report.md"
    cases = [
        ("B1 引用符の中に空白が在る grep → 通る", f'grep -n "^### " {req}', "_audit_request.md", False),
        ("B2 ヒアドキュメントの中の名前 → 通る",
         f"cat >> .claude/state/session_worklog_x.md <<'EOF'\n- 依頼書を作った（{req}）\nEOF", "_audit_request.md", False),
        ("B3 time を付けた依頼書の道具 → 通る", f"time python3 .claude/tools/gen_audit_docs.py result {req} y", "_audit_request.md", False),
        ("B4 試しの道具の引用符の中 → 通る", f'python3 .claude/tools/try_hooks.py --session s --bash "cat > {req}"',
         "_audit_request.md", False),
        ("B5 写す元が依頼書の cp → 通る", f"cp {req} .claude/state/sessions/s/", "_audit_request.md", False),
        ("B6 写す先が依頼書の cp → 止まる", f"cp a.md {req}", "_audit_request.md", True),
        ("B7 rm -f → 止まる", f"rm -f {req}", "_audit_request.md", True),
        ("B8 依頼書への書き出し → 止まる", f"echo hi > {req}", "_audit_request.md", True),
        ("B9 sed -i → 止まる", f"sed -i '' 's/a/b/' {req}", "_audit_request.md", True),
        ("B10 mv → 止まる", f"mv {req} /tmp/", "_audit_request.md", True),
        ("B11 許していない python の道具 → 止まる", f"python3 other.py {req}", "_audit_request.md", True),
        ("B12 jq → 通る", f"jq -R . {req} | head", "_audit_request.md", False),
        ("B13 git -C の読む命令 → 通る", f"git -C /a log --oneline -- {req}", "_audit_request.md", False),
        ("B14 書く先が依頼書でない書き出し → 通る", f"grep -c a {req} > /private/tmp/n.txt", "_audit_request.md", False),
        ("B15 作業の置き場の見直し表（名前の終わりが同じ）への書き出し → 通る",
         f"sed '' {req} > .claude/state/sessions/s/review_x_audit_request.md", "_audit_request.md", False),
        ("B16 結果ファイルへ写す cp（hook 11）→ 止まる", f"cp cp60_work/cp60_result.md {rep}", "_audit_report.md", True),
        ("B17 cmp で作業場の結果と結果ファイルを比べる（hook 11）→ 通る", f"cmp cp60_work/cp60_result.md {rep}",
         "_audit_report.md", False),
        ("R1 結果ファイルへのヒアドキュメントの書き出し（hook 11）→ 止まる",
         f"cat > {rep} <<'EOF'\n中身\nEOF", "_audit_report.md", True),        # ★2026-10-18（監査 CP79 の修正）＝直す前に通っていた形（止まる側）と、直した後も通るべき形（通る側）
        ("B18 引用符で囲んだ依頼書のパスの rm → 止まる", f'rm -f "{req}"', "_audit_request.md", True),
        ("B19 ヒアドキュメントと同じ行の依頼書への書き出し → 止まる", f"cat <<'EOF' > {req}\nhi\nEOF", "_audit_request.md", True),
        ("B20 依頼書の名前のファイルを inputs の置き場へ写す cp → 止まる", "cp /tmp/x_audit_request.md SDK/.claude/audits/inputs/",
         "_audit_request.md", True),
        ("B21 引用符で囲んだ道具のパスと依頼書 → 通る", f'python3 ".claude/tools/gen_audit_docs.py" request a.md "{req}"',
         "_audit_request.md", False),
        ("B22 結果の名前のファイルを audits の置き場へ写す cp（hook 11）→ 止まる", "cp cp60_work/x_audit_report.md SDK/.claude/audits/",
         "_audit_report.md", True),
        ("B23 引用符で囲んだ依頼書への sed -i → 止まる", f"sed -i '' 's/a/b/' \"{req}\"", "_audit_request.md", True),
        ("B24 引用符で囲んだ結果ファイルへの tee（hook 11）→ 止まる", f'cat a.md | tee "{rep}"', "_audit_report.md", True),
        ("B25 引用符の中の文に依頼書の名前（worklog へ書き足す）→ 通る",
         f'echo "依頼書 {req} を作った" >> .claude/state/session_worklog_x.md', "_audit_request.md", False),
        ("B26 引用符の中の grep -E の候補（| を含む）→ 通る", f'grep -n -E "GO|CONDITIONAL-GO|NO-GO" {rep}', "_audit_report.md", False),
        ("B27 引用符の中の sed の行の指定（; を含む）→ 通る", f"sed -n '326,330p;1435p' {rep}", "_audit_report.md", False),
    ]
    ng = 0
    for nm, cmd, word, want in cases:
        got = bool(bash_bad_parts(cmd, word))
        ok = got == want
        ng += not ok
        print(f"  {'✅' if ok else '❌'} {nm}" + ("" if ok else f"（出た結果: {bash_bad_parts(cmd, word)}）"))
    import contextlib
    import io
    with contextlib.redirect_stderr(io.StringIO()):
        w = gate_request("Write", {"file_path": os.path.join(ROOT, "v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/x_audit_request.md")}, ROOT)
    ok = w == 2
    ng += not ok
    print(f"  {'✅' if ok else '❌'} W1 Write で依頼書を書く → 止まる（{w}）")
    total = len(cases) + 1
    print(f"自己テスト {total - ng}/{total}")
    return 1 if ng else 0


def replay(days: int) -> int:
    """★2026-10-17（183回目）＝直近 days 日の記録で、hook 10・11 が Bash を止めた場面に、いまの見分け方を当て直す。何も書かない。"""
    import time
    sys.path.insert(0, os.path.join(ROOT, ".claude", "hooks"))
    from transcript_rows import rows
    proj = os.path.expanduser("~/.claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget")
    cut = time.time() - days * 86400
    still, gone = [], 0
    for fn in sorted(os.listdir(proj)):
        p = os.path.join(proj, fn)
        if not fn.endswith(".jsonl") or os.path.getmtime(p) < cut:
            continue
        cmds, hit = {}, []
        for o in rows(p):
            for b in (o.get("message") or {}).get("content") or []:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "tool_use" and b.get("name") == "Bash":
                    cmds[b.get("id")] = str((b.get("input") or {}).get("command") or "")
                elif b.get("type") == "tool_result" and b.get("is_error"):
                    t = b.get("content")
                    t = " ".join(x.get("text", "") for x in t if isinstance(x, dict)) if isinstance(t, list) else str(t or "")
                    for tag, word in (("[hook 10・", "_audit_request.md"), ("[hook 11・", "_audit_report.md")):
                        if "hook error" in t and tag in t and b.get("tool_use_id") in cmds:
                            hit.append((cmds[b.get("tool_use_id")], word, tag))
        for c, w, tag in hit:
            if bash_bad_parts(c, w):
                still.append((fn[:8], tag, bash_bad_parts(c, w)[0][:140]))
            else:
                gone += 1
    print(f"直近 {days} 日に hook 10・11 が Bash を止めた {gone + len(still)} 回＝いまの見分け方なら 通る {gone} 回・止まる {len(still)} 回")
    for s in still:
        print(f"   止まる: {s[0]} {s[1]} {s[2]}")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    if len(sys.argv) == 3 and sys.argv[1] == "--replay":
        sys.exit(replay(int(sys.argv[2])))
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
