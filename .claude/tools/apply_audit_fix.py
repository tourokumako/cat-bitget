#!/usr/bin/env python3
"""apply_audit_fix.py — 監査結果の「修正の指示」を、実物に当てる。

設計書＝.claude/state/acceptance.md（iter audit-autofix-apply-20260916・まこさん承認 2026-09-16）。

まこさん指示（逐語 2026-09-14）
  「その監査が書いた修正方法の通りに修正をするように自動生成をしろっていってんだよ。」
  「設計書の修正だけではない。実装データの修正をする場合もある。他にもあらゆる修正指示を出せて、
   それに対して自動で対応出来る状態にしろ。意味分かる？矮小化するな。」

なぜ要るか
  監査結果は 102回目にテンプレの形になった（1件ずつ6つの欄）。しかし欄のとおりに当てる
  プログラムが無く、当てる作業が私（CC）の手に残っていた。100回目は同じ作業で照合を9回 繰り返し、
  約4時間54分と agent 約359万トークンを使った（まこさんの逐語「これは詐欺行為である」）。

使い方
  python3 .claude/tools/apply_audit_fix.py --report <監査結果.md> --severity Critical,Major[,Minor,Process] [--dry]
    --dry を付けると、当てずに「当たるか」だけを確かめて一覧を出す。

何をするか（設計書 4-4）
  1. 監査結果を読み、修正の指示を番号の順に並べる（読み取りは gen_audit_docs.item_fields）
  2. --severity に当たる重さの件だけに絞る
  3. 全件を先に確かめる（当てる前に）＝状態が「確定」／対象のファイルが実在／
     直す前の文字がちょうど1か所／根拠の抜き書きの行が実物と合う
  4. 1件でも合わなければ、1件も当てずに一覧を出して rc=1（半分だけ当たった状態を作らない）
  5. 全件が確かめられたら、番号の順に当てる
  6. 当てた件数と、走らせるコマンドの件の一覧を画面に出す

止めて まこさんに報告するのは2つだけ（設計書 4-5）
  ①直す前の文字か根拠の抜き書きが実物と合わない ②状態が「未決」か「案が複数」

書かない相手（設計書 4-16）
  承認の印・凍結の記録・hook・道具そのもの（守りを1本で外せる道を作らないため）。
  監査が「hook を直せ」と書いたときは、当てずに一覧へ出す＝私が Write ツールで直す
  （そのとき承認ゲートと土台ゲートが効く）。

限界（正直に）
  ①当てた後の文が正しいかは見ない（監査が書いた文字をそのまま入れる）。
  ②この道具そのものを書き替えれば守りを外せる（承認ゲートの相手・git diff には出る）。
  ③同じ事実を書いたほかの場所を揃えるのは、いまも人の手（恒久72番の2番）。
  ④恒久71番＝壊すプログラムと自己テストは付けない（まこさん決定 2026-09-16「３作らなくてよい」）。
"""

from __future__ import annotations

import argparse
import os
import re
import sys

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
SDK = os.path.join(ROOT, "v3-bitget-api-sdk", "bitget-python-sdk-api")
sys.path.insert(0, os.path.join(ROOT, ".claude", "tools"))

import gen_audit_docs as g                                    # noqa: E402

SEVERITIES = ("Critical", "Major", "Minor", "Process")
# ★書かない相手（設計書 4-16）＝守りの仕組み。監査が名指ししても当てない。
NEVER_WRITE = (
    ".claude/hooks/", ".claude/tools/", ".claude/breaks/",
    "acceptance.approved", "verify_tool.approved", "design_approved.json",
    "_frozen.json", ".breaks.json", ".dirty.json", "h2_pass.json", "g2_pass.json",
)
EVID_RE = re.compile(r"(\S+):(\d+)[^「]*「(.*)」\s*$")


def repo_path(p: str) -> str:
    """監査が書いたパスを、実物の場所に直す。"""
    p = (p or "").strip().strip("`")
    if p.startswith("SDK/"):
        return os.path.join(SDK, p[4:])
    cand = os.path.join(ROOT, p)
    if os.path.exists(cand):
        return cand
    return os.path.join(SDK, p)


def never_write(rel: str) -> bool:
    return any(k in (rel or "") for k in NEVER_WRITE)


def read_fixes(report_text: str) -> list:
    """監査結果から、修正の指示を番号の順に読む。★読み取りは gen_audit_docs.item_fields。"""
    out = []
    body, _ = g.split_mark(report_text)
    _, secs = g.split_sections(body)
    for head, lines in secs:
        kind = g.kind_of(head.split(". ", 1)[-1], g.RESULT_KIND)
        if kind not in ("修正", "プロセス"):
            continue
        text = "\n".join(lines)
        sev = ""
        for chunk in re.split(r"^### ", text, flags=re.M)[1:]:
            name = chunk.split("\n", 1)[0].strip()
            if name in SEVERITIES:
                sev = name
            parts = re.split(r"^#### 修正 (\d+)[ \t]*$", chunk, flags=re.M)
            for num, block in zip(parts[1::2], parts[2::2]):
                f = g.item_fields(num, block)
                f["重さ"] = sev
                out.append(f)
    out.sort(key=lambda f: int(f["番号"]))
    return out


def check_one(f: dict, chosen: dict = None) -> tuple:
    """1件が当てられるかを確かめる。戻り＝(当てられるか, 理由, 実物の中身)。

    ★chosen＝`--choose` で まこさんが決めた件（{番号: 案の記号 or "確定"}）。
      設計書 audit-autofix-apply-20260916 の 4-9・4-5・完成の条件 AUDIT-3。
    """
    chosen = chosen or {}
    num, rel = f["番号"], (f["対象のファイル"] or "")
    fourth = f["4つ目"]
    pick = chosen.get(num)
    if f["状態"] != "確定" and pick is None:
        return False, f"状態が「{f['状態']}」＝まこさんが決めるまで当てない", ""
    if pick and pick != "確定":
        if not any(a == pick for a, _k, _b in fourth):
            have = "・".join(sorted({a for a, _k, _b in fourth if a})) or "（案の記号が無い）"
            return False, f"--choose で {pick} を選んだが、この件に その案が無い（在るのは {have}）", ""
    if any(k == "走らせるコマンド" for _, k, _ in fourth):
        return False, "走らせるコマンド（当てずに、打つべきコマンドとして出す）", ""
    if never_write(rel):
        return False, f"守りの仕組みなので当てない（{rel}）＝私が Write ツールで直す", ""
    path = repo_path(rel)
    if not os.path.isfile(path):
        return False, f"対象のファイルが実在しない（{rel}）", ""
    cur = open(path, encoding="utf-8").read()
    before = f["直す前の文字"]
    if before is None:
        return False, "直す前の文字の囲みが無い", ""
    # ★2026-09-16＝もう当て終わっているかを、先に見る。
    #   なぜ要るか＝「足す文字」の件と、直した後の文字が直す前の文字を含む件は、
    #   当てた後も「直す前の文字」がちょうど1か所 残る＝二重に当たる。
    #   実測＝修正 9・13・21（足す文字）と 43（"…selftest" → "…selftest, \"stage_candidates\""）。
    for _a, kind, body in fourth:
        if not body:
            continue
        done = (before + body) if kind == "足す文字" else body
        if kind in ("直した後の文字", "足す文字") and done.strip() and done in cur:
            return False, "もう当て終わっている（直した後の文字が実物に在る）", cur
    n = cur.count(before)
    if n == 0:
        # ★2026-09-16＝もう当て終わっている件を見分ける。
        #   「直した後の文字」が実物に在れば、この件は当て済み（実物と合わない件に数えない）。
        #   直す前＝当て済みの件も「0か所」として全件を止めたので、2回目のコマンドが必ず落ちた。
        for _a, kind, body in fourth:
            if kind in ("直した後の文字", "足す文字") and body and body.strip() in cur:
                return False, "もう当て終わっている（直した後の文字が実物に在る）", cur
    if n != 1:
        return False, f"直す前の文字が実物に {n} か所（ちょうど1か所であること）", cur
    ok, why = check_evidence(f)
    if not ok:
        return False, why, cur
    return True, "", cur


def check_evidence(f: dict) -> tuple:
    """根拠の抜き書き「ファイル名:行番号「その行の逐語」」が、実物のその行と合うか。"""
    ev = (f["根拠の抜き書き"] or "").strip()
    m = EVID_RE.search(ev)
    if not m:
        return True, ""                       # 形が違うものは form の側が見る（ここでは通す）
    name, line, quote = m.group(1).strip("`"), int(m.group(2)), m.group(3)
    # ★2026-09-24（設計書 iter="audit-fix-evidence-backtick-20260924"・まこさん決定「案A」）
    #   ＝逐語の外側の1組のバッククォートを外す（ファイル名と同じ扱い）。
    #   実測（CP40）＝監査が20件とも逐語を「`…`」で囲んで書き、5件が「実物と合わない」になって
    #     1件も当てられなかった。テンプレは囲む・囲まないを決めておらず、形の検査（hook 11）は通す。
    #   ★外すのは先頭と末尾が両方 バッククォートのときだけ（行の中のバッククォートは残す）。
    if len(quote) >= 2 and quote[0] == "`" and quote[-1] == "`":
        quote = quote[1:-1]
    # ★2026-09-16＝根拠のファイル名が、対象のファイルと同じ名前なら、対象のパスを使う。
    #   なぜ＝監査は作業場の写しを見て行番号を書く。同じ名前の本物を見ると、別の行が入っている。
    #   実測＝修正7 の根拠 acceptance_src.json:61 が、いまの ratchet の元データと合わなかった。
    tgt = repo_path(f["対象のファイル"] or "")
    if os.path.basename(tgt) == os.path.basename(name):
        return _cmp_line(tgt, name, line, quote)
    path = repo_path(name)
    if not os.path.isfile(path):
        # ★2026-09-16＝監査の作業場（audits の下）に在る写しを掴まないようにする。
        #   実測＝engine_tuner_gen.py は5か所に在り、4か所が監査の写し（mirror）だった。
        #   写しを見ると、同じ行番号でも別の行が入っていて「実物と合わない」と誤って言う。
        for r, _d, fs in os.walk(ROOT):
            if any(k in r for k in (".git", "__pycache__", os.sep + "audits" + os.sep)):
                continue
            if os.path.basename(name) in fs:
                path = os.path.join(r, os.path.basename(name))
                break
    return _cmp_line(path, name, line, quote)


def _cmp_line(path: str, name: str, line: int, quote: str) -> tuple:
    """そのファイルの その行が、書いてある逐語と合うか。"""
    if not os.path.isfile(path):
        return True, ""                       # 置き場を探せないものは見ない（限界）
    lines = open(path, encoding="utf-8").read().splitlines()
    if not (1 <= line <= len(lines)):
        return False, f"根拠の行が無い（{name} は全{len(lines)}行・書いてあるのは {line} 行）"
    if quote.strip() and quote.strip() not in lines[line - 1]:
        # ★2026-09-16＝同じ文が別の行に在れば、行番号がずれただけ（中身は合っている）。
        #   なぜ要るか＝監査が読んだ後に、そのファイルへ行を足すと行番号が動く。
        #   実測＝修正31 の根拠の行が、私が今日15行 足したことで動いていた。
        hits = [i + 1 for i, s in enumerate(lines) if quote.strip() in s]
        if hits:
            return True, f"（行番号のずれ＝{name} の {line} 行 → {hits[0]} 行。中身は合っている）"
        return False, (f"根拠の行が実物と合わない（{name}:{line}）\n"
                       f"       書いてある: {quote.strip()[:60]}\n"
                       f"       実物      : {lines[line - 1].strip()[:60]}")
    return True, ""


def apply_one(f: dict, cur: str, pick: str = "") -> tuple:
    """1件を当てる。戻り＝(当てた後の中身, 何をしたか)。

    ★pick＝`--choose` で選んだ案の記号（例＝"B"）。案が複数の件は、その案だけを当てる。
    """
    before = f["直す前の文字"]
    plans = f["4つ目"]
    if pick and pick != "確定":
        plans = [(a, k, b) for a, k, b in plans if a == pick]
    for a, kind, body in plans:
        if kind == "直した後の文字":
            return cur.replace(before, body, 1), ("置き替えた" + (f"（案{a}）" if a else ""))
        if kind == "足す文字":
            return cur.replace(before, before + body, 1), ("足した" + (f"（案{a}）" if a else ""))
        if kind == "消す文字":
            return cur.replace(before, before.replace(body, "", 1), 1), ("消した" + (f"（案{a}）" if a else ""))
    return cur, "何もしなかった"


def main() -> int:
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--report", default="")
    ap.add_argument("--severity", default="")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--choose", default="")
    ap.add_argument("--only", default="")
    ap.add_argument("-h", "--help", action="store_true")
    a = ap.parse_args()
    if a.help or not a.report or not a.severity:
        print(__doc__)
        return 2
    if not os.path.isfile(a.report):
        print(f"❌ 監査結果がありません: {a.report}")
        return 1
    want = [s.strip() for s in a.severity.split(",") if s.strip()]
    bad = [s for s in want if s not in SEVERITIES]
    if bad:
        print(f"❌ 知らない重さ: {bad}（{'・'.join(SEVERITIES)} から選ぶ）")
        return 1

    text = open(a.report, encoding="utf-8").read()
    errs = g.form_errors(text)
    if errs:
        print(f"❌ 監査結果がテンプレの形ではありません（{len(errs)} 件）＝当てません")
        for e in errs[:10]:
            print(f"   ❌ {e}")
        return 1

    all_fixes = read_fixes(text)
    # ★--choose＝まこさんが決めた件（{番号: 案の記号 or "確定"}）。書いていない番号は当てない。
    chosen = {}
    for pair in [x.strip() for x in a.choose.split(",") if x.strip()]:
        if "=" not in pair:
            print(f"❌ --choose の書き方が違う（<番号>=<案の記号 または 確定>）: {pair}")
            return 1
        num, pick = [t.strip() for t in pair.split("=", 1)]
        if num not in {f["番号"] for f in all_fixes}:
            print(f"❌ --choose に書いた番号が、監査結果に無い: {num}")
            return 1
        chosen[num] = pick
    if chosen:
        print(f"— まこさんが決めた件: {'・'.join(f'{k}={v}' for k, v in sorted(chosen.items(), key=lambda x: int(x[0])))}")

    # ★--only＝この番号だけを当てる（まこさんが件ごとに決めたときに使う。書かなければ重さで選ぶ）。
    only = {x.strip() for x in a.only.split(",") if x.strip()}
    for num in only:
        if num not in {f["番号"] for f in all_fixes}:
            print(f"❌ --only に書いた番号が、監査結果に無い: {num}")
            return 1
    fixes = [f for f in all_fixes if f["重さ"] in want and (not only or f["番号"] in only)]
    if only:
        print(f"— 当てる番号を絞った: 修正 {'・'.join(sorted(only, key=int))}")
    print(f"— 監査結果: {os.path.relpath(a.report, ROOT)}")
    print(f"— 当てる重さ: {'・'.join(want)} ／ 当たる件: {len(fixes)} 件")

    ready, stopped = [], []
    for f in fixes:
        ok, why, cur = check_one(f, chosen)
        (ready if ok else stopped).append((f, why, cur))

    for f, why, _c in stopped:
        print(f"   ⏸ 修正 {f['番号']}（{f['重さ']}）: {why}")

    # ★「実物と合わない」だけが、全件を止める理由（設計書 4-5）。
    #   状態が未決・案が複数／走らせるコマンド／守りの仕組みは、当てないだけで、ほかの件は当てる。
    hard = [x for x in stopped
            if not x[1].startswith(("状態が", "走らせるコマンド", "守りの仕組みなので",
                                    "もう当て終わっている", "--choose で"))]
    if hard:
        print(f"\n❌ 実物と合わない件が {len(hard)} 件 あるので、1件も当てません（先に全件を確かめる形）")
        return 1
    if a.dry:
        nums = "・".join(f["番号"] for f, _w, _c in ready) or "（無し）"
        print(f"\n✅ --dry: 当たる {len(ready)} 件（修正 {nums}）／"
              f"当てない {len(stopped)} 件（実物と合わない件は0）")
        return 0

    done = 0
    for f, _w, _c in ready:
        path = repo_path(f["対象のファイル"])
        # ★2026-09-16＝当てる直前に読み直す。
        #   直す前＝確かめたときの中身を使っていたので、同じファイルに2件 当てると
        #   後の1件が前の1件を消した（実測＝置き替えた行が、次の件の書き込みで戻った）。
        cur = open(path, encoding="utf-8").read()
        new, what = apply_one(f, cur, chosen.get(f["番号"], ""))
        if new == cur:
            print(f"   ⏸ 修正 {f['番号']}: 中身が変わらなかった（当てていない）")
            continue
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(new)
        done += 1
        print(f"   ✅ 修正 {f['番号']}（{f['重さ']}）: {what} → {os.path.relpath(path, ROOT)}")
    print(f"\n✅ 当てた {done} 件／当てなかった {len(stopped)} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
