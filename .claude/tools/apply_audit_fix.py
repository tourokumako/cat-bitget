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
  python3 .claude/tools/apply_audit_fix.py --design [<設計書.md>] [--dry]
    ★2026-09-24（設計書 impl-instruction-apply-20260924・まこさん承認）＝設計書の「4-20 実装の指示」を当てる口。
    --report と同時には受けない。当てる前に、承認の印（.claude/state/acceptance.approved）と設計書の
    ハッシュ値を照らし、合わなければ1件も当てない。欄の形は gen_audit_docs.item_errors で見る。
    対象のファイルが設計書の TARGET／NEW_FILE に無い件は当てない。当てなかった件が1件でも在れば終了コードは 1。
  python3 .claude/tools/apply_audit_fix.py --selftest
    見本の設計書と見本のコードを一時の置き場に作り、設計書 4-19 の場面を測る（本物には1バイトも書かない）。

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
import json
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
    # ★2026-09-24（監査 CP41 の修正 1・A1-a）＝hook の登録そのもの。1回の書き込みで hook を全部 外せる穴を塞ぐ。
    ".claude/settings.json", ".claude/settings.local.json",
)
EVID_RE = re.compile(r"(\S+):(\d+)[^「]*「(.*)」\s*$")
# ★2026-09-24（設計書 impl-instruction-apply-20260924）＝設計書を当てる口が読むもの
APPROVED = os.path.join(ROOT, ".claude", "state", "acceptance.approved")     # 承認の印（設計書の sha256）
DESIGN = os.path.join(ROOT, ".claude", "state", "acceptance.md")            # 既定の設計書
SRC_JSON = os.path.join(SDK, ".claude", "ratchet", "acceptance_src.json")   # 設計書の元データ（実装の指示の中身の正本）
IMPL_HEAD_RE = re.compile(r"^### 4-20 .*$", re.M)                            # 設計書の「実装の指示」の節の見出し


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


# ══ 設計書の「実装の指示」を当てる口（2026-09-24・設計書 impl-instruction-apply-20260924）══════════

def read_design_blocks(design_text: str) -> list:
    """設計書から「4-20 実装の指示」の節を切り出し、[(番号, 1件の塊), …] を返す。節が無ければ空。"""
    m = IMPL_HEAD_RE.search(design_text)
    if not m:
        return []
    rest = design_text[m.end():]
    nxt = re.search(r"^#{1,3} ", rest, re.M)             # 次の見出し（### 4-A や ## 5）まで。#### は件の見出しなので飛ばさない
    sec = rest[:nxt.start()] if nxt else rest
    parts = re.split(r"^#### 実装 (\d+)[ \t]*$", sec, flags=re.M)
    return list(zip(parts[1::2], parts[2::2]))


def read_design_fixes(design_text: str) -> list:
    """設計書の「実装の指示」を、監査結果の修正と同じ形（item_fields の戻り）で番号の順に読む。重さは空。"""
    out = []
    for num, block in read_design_blocks(design_text):
        f = g.item_fields(num, block)                     # ★読み取りは監査結果と同じ1か所
        f["重さ"] = ""
        out.append(f)
    out.sort(key=lambda f: int(f["番号"]))
    return out


def approved_ok(design_path: str, mark_path: str = None) -> tuple:
    """承認の印の値と、設計書の sha256 が同じか。戻り＝(同じか, 理由)。印が無い・空・違う＝全部 いいえ（fail-closed）。"""
    import hashlib
    mark_path = mark_path or APPROVED
    if not os.path.isfile(design_path):
        return False, f"設計書が無い（{design_path}）"
    if not os.path.isfile(mark_path):
        return False, "承認の印が無い"
    want = open(mark_path, encoding="utf-8").read().strip()
    if not want:
        return False, "承認の印が空"
    now = hashlib.sha256(open(design_path, "rb").read()).hexdigest()
    if want != now:
        return False, f"承認の印（{want[:16]}…）と設計書（{now[:16]}…）が違う＝承認の後に設計書が変わった"
    return True, ""


def design_targets(design_text: str) -> set:
    """設計書の TARGET: と NEW_FILE: に書いたファイルの集合（当ててよい相手）。"""
    out = set()
    for ln in design_text.splitlines():
        if ln.startswith("TARGET:") or ln.startswith("NEW_FILE:"):
            for p in ln.split(":", 1)[1].split(","):
                p = p.strip().strip("`")
                if p:
                    out.add(os.path.normpath(p))
    return out


def impl_src_mismatch(fixes: list, src_path: str) -> list:
    """設計書から読んだ実装の指示が、元データの `実装の指示` と1文字も違わないか。違いを文で返す。

    ★なぜ要るか（監査 CP41 の A3-d）＝囲みの中に囲みの記号（チルダ3つ）が入ると、読み取りが内側で
      黙って切れ、切れた文字が実物に書かれた。元データと突き合わせれば、切れた読み取りは必ず違いになる。
    """
    try:
        d = json.load(open(src_path, encoding="utf-8"))
    except Exception as e:                                # noqa: BLE001
        return [f"元データが読めない（{src_path}・{e}）"]
    items = d.get("実装の指示") or []
    if len(items) != len(fixes):
        return [f"元データの実装の指示は {len(items)} 件、設計書から読めたのは {len(fixes)} 件"]
    bad = []
    for it, f in zip(items, fixes):
        num = str(it.get("番号", "")) or f["番号"]
        if str(it.get("番号")) != f["番号"]:
            bad.append(f"実装 {f['番号']}: 番号が元データ（{it.get('番号')}）と違う")
        if (it.get("直す前の文字") or "") != (f["直す前の文字"] or ""):
            bad.append(f"実装 {num}: 直す前の文字が元データと違う（囲みの中で読み取りが切れた疑い）")
        bodies = [b for _a, _k, b in f["4つ目"]]
        if str(it.get("中身") or "") not in bodies:
            bad.append(f"実装 {num}: 中身（4つ目の欄）が元データと違う（囲みの中で読み取りが切れた疑い）")
    return bad


def _recheck(f: dict, cur: str) -> bool:
    """当てる直前に、いまの中身（前の件を当てた後）でも「直す前の文字がちょうど1か所」かを見る。

    ★なぜ要るか（監査 CP41 の A2-b・実測）＝全件の確かめは当てる前の中身に対して行う。先の件を当てると
      中身が変わり、後の件の「直す前の文字」が消えることがある。直す前は そのまま進んで rc=0 だった。
    """
    before = f["直す前の文字"] or ""
    return bool(before) and cur.count(before) == 1


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


def main(argv: list = None, approved_path: str = None) -> int:
    """★argv と approved_path は自己テストが渡す（本物の呼び出しでは None＝コマンドの引数と本物の印）。"""
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--report", default="")
    ap.add_argument("--severity", default="")
    ap.add_argument("--design", nargs="?", const=DESIGN, default="")
    ap.add_argument("--src", default=SRC_JSON)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--choose", default="")
    ap.add_argument("--only", default="")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("-h", "--help", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.report and a.design:
        print("❌ --report と --design は同時に渡せません（どちらか1つにしてください）")
        return 2
    design_mode = bool(a.design)
    if a.help or (not design_mode and (not a.report or not a.severity)):
        print(__doc__)
        return 2
    want: list = []
    targets: set = set()
    if design_mode:
        # ★設計書を当てる道（設計書 4-4 の 1〜4）＝承認の印 → 節の切り出し → 欄の形 → 元データとの突き合わせ
        print(f"設計書: {a.design}")
        ok, why = approved_ok(a.design, approved_path)
        print(f"承認の印と一致: {'はい' if ok else 'いいえ'}{'' if ok else '（' + why + '）'}")
        if not ok:
            print("❌ 承認の印と設計書が合わないので、1件も当てません")
            return 1
        text = open(a.design, encoding="utf-8").read()
        blocks = read_design_blocks(text)
        errs = []
        for num, block in blocks:
            errs += g.item_errors(num, block)                # ★欄の形は監査結果と同じ検査
        if errs:
            print(f"❌ 実装の指示の欄が6つの形になっていません（{len(errs)} 件）＝1件も当てません")
            for e in errs[:10]:
                print(f"   ❌ {e}")
            return 1
        all_fixes = read_design_fixes(text)
        if not all_fixes:
            print("— 設計書に実装の指示が0件（4-20 の節が無いか、空）＝当てるものがありません")
            return 0
        bad = impl_src_mismatch(all_fixes, a.src)
        if bad:
            print(f"❌ 設計書から読んだ実装の指示が、元データと合いません（{len(bad)} 件）＝1件も当てません")
            for e in bad[:10]:
                print(f"   ❌ {e}")
            return 1
        targets = design_targets(text)
    else:
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
    fixes = [f for f in all_fixes if (design_mode or f["重さ"] in want) and (not only or f["番号"] in only)]
    if only:
        print(f"— 当てる番号を絞った: 修正 {'・'.join(sorted(only, key=int))}")
    if design_mode:
        print(f"— 設計書の実装の指示: {len(fixes)} 件（当ててよい相手＝TARGET／NEW_FILE の {len(targets)} 本）")
    else:
        print(f"— 監査結果: {os.path.relpath(a.report, ROOT)}")
        print(f"— 当てる重さ: {'・'.join(want)} ／ 当たる件: {len(fixes)} 件")

    ready, stopped = [], []
    for f in fixes:
        ok, why, cur = check_one(f, chosen)
        # ★設計書の道だけ（設計書 4-4 の 9）＝対象のファイルが TARGET／NEW_FILE に無ければ当てない
        if ok and design_mode:
            rel = os.path.normpath((f["対象のファイル"] or "").strip().strip("`"))
            if rel not in targets:
                ok, why, cur = False, f"TARGET の外（設計書の TARGET／NEW_FILE に無い: {rel}）", cur
        (ready if ok else stopped).append((f, why, cur))

    for f, why, _c in stopped:
        print(f"   ⏸ 修正 {f['番号']}（{f['重さ']}）: {why}")

    # ★「実物と合わない」だけが、全件を止める理由（設計書 4-5）。
    #   状態が未決・案が複数／走らせるコマンド／守りの仕組みは、当てないだけで、ほかの件は当てる。
    hard = [x for x in stopped
            if not x[1].startswith(("状態が", "走らせるコマンド", "守りの仕組みなので",
                                    "もう当て終わっている", "--choose で", "TARGET の外"))]
    if hard:
        print(f"\n❌ 実物と合わない件が {len(hard)} 件 あるので、1件も当てません（先に全件を確かめる形）")
        return 1
    if a.dry:
        nums = "・".join(f["番号"] for f, _w, _c in ready) or "（無し）"
        print(f"\n✅ --dry: 当たる {len(ready)} 件（修正 {nums}）／"
              f"当てない {len(stopped)} 件（実物と合わない件は0）")
        return 1 if (design_mode and stopped) else 0

    # ★2026-09-24（監査 CP41 の A2・修正 3）＝全件を先に「当てた後の中身」で確かめてから、まとめて書く。
    #   直す前＝1件ずつ読み直して書いていた。同じファイルに2件 当てて、先の件が後の件の「直す前の文字」を
    #   消すと、先の件だけ当たって rc=0 になった（監査が実測）。
    #   いま＝ファイルごとに中身を1回 読み、番号の順に中身の上で当てる。当てる直前に「直す前の文字が
    #   ちょうど1か所」を いまの中身で見直し、1件でも合わなければ 1バイトも書かずに rc=1（git apply と同じ）。
    mem: dict = {}
    plan: list = []
    for f, _w, _c in ready:
        path = repo_path(f["対象のファイル"])
        if path not in mem:
            mem[path] = open(path, encoding="utf-8").read()
        cur = mem[path]
        if not _recheck(f, cur):
            print(f"\n❌ 修正 {f['番号']}: 先の件を当てた後の中身では「直す前の文字」がちょうど1か所ではありません"
                  f"＝実物と合わない件が在るので、1件も当てません（半分だけ当たった状態を作らない）")
            return 1
        new, what = apply_one(f, cur, chosen.get(f["番号"], ""))
        if new == cur:
            print(f"   ⏸ 修正 {f['番号']}: 中身が変わらなかった（当てていない）")
            stopped.append((f, "中身が変わらなかった", cur))
            continue
        mem[path] = new
        plan.append((f, what, path))
    done = 0
    for path, new in mem.items():
        if any(p == path for _f, _what, p in plan):
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(new)
    for f, what, path in plan:
        done += 1
        print(f"   ✅ 修正 {f['番号']}（{f['重さ'] or '設計書'}）: {what} → {os.path.relpath(path, ROOT)}")
    print(f"\n✅ 当てた {done} 件／当てなかった {len(stopped)} 件")
    # ★設計書の道（設計書 4-4 の 10）＝当てなかった件が1件でも在れば rc=1（当て忘れを機械で見つける）
    return 1 if (design_mode and stopped) else 0


# ══ 自己テスト（設計書 4-19 の場面・本物には1バイトも書かない）═══════════════════════════════

def selftest() -> int:
    """見本の設計書と見本のコードを一時の置き場に作り、設計書 4-19 の場面を測る。

    ★終了コード 1 のときは、落ちた場面を「❌ …」で画面に出す（壊すプログラム b101・b102 が照らす文字）。
    """
    import hashlib
    import shutil
    import tempfile
    sys.path.insert(0, os.path.join(ROOT, ".claude", "tools"))
    import gen_acceptance as ga                            # ★節を作る側（build_impl）と同じ形かを測る
    from contextlib import redirect_stdout
    import io

    def run(argv, mark):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(argv, approved_path=mark)
        return rc, buf.getvalue()

    def item(num, rel, before, kind, body, ev, state="確定"):
        return {"番号": num, "対象のファイル": rel, "直す箇所": "1-1", "直す前の文字": before,
                "種類": kind, "中身": body, "根拠の抜き書き": ev, "状態": state}

    def design(items, target_rel, src_path):
        d = {"実装の指示": items}
        open(src_path, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False))
        sec = ga.build_impl(d)
        return ("<!-- ARC iter=\"selftest\" -->\n# 設計書｜見本\n\n"
                f"TARGET: {target_rel}\n\n## 4｜設計の中身\n\n### 4-20 実装の指示（見本）\n\n"
                + sec + "\n### 4-A この節に何を書いたか（一覧）\n\n| a |\n")

    def mark_of(md_path, mark_path, text=None):
        text = text if text is not None else open(md_path, "rb").read()
        open(mark_path, "w", encoding="utf-8").write(hashlib.sha256(text).hexdigest())

    ok = total = 0
    fails: list = []
    tmp = tempfile.mkdtemp(prefix="_selftest_impl_apply_", dir=os.path.join(ROOT, ".claude", "state"))
    try:
        rel = os.path.relpath(os.path.join(tmp, "sample.py"), ROOT)
        code = os.path.join(tmp, "sample.py")
        md = os.path.join(tmp, "design.md")
        mark = os.path.join(tmp, "approved")
        srcj = os.path.join(tmp, "src.json")
        ev = f"{rel}:1「x = 1」"

        def fresh(items, target_rel=None, body_text="x = 1\n"):
            open(code, "w", encoding="utf-8").write(body_text)
            txt = design(items, target_rel or rel, srcj)
            open(md, "w", encoding="utf-8").write(txt)
            mark_of(md, mark)

        # T1（完成の条件 #1）＝節を作る側の出力が、欄の検査で食い違い0件。指示が無ければ空
        total += 1
        d1 = {"実装の指示": [item(1, rel, "x = 1", "直した後の文字", "x = 2", ev)]}
        blocks = read_design_blocks("### 4-20 見本\n\n" + ga.build_impl(d1) + "\n### 4-A\n")
        e1 = []
        for num, block in blocks:
            e1 += g.item_errors(num, block)
        if not e1 and len(blocks) == 1 and ga.build_impl({}) == "":
            ok += 1
            print(f"   T{total} 節を作る側の出力が6つの欄の形（食い違い0件・空なら出ない） → pass")
        else:
            fails.append(f"❌ 節の形 T{total}: {e1 or '塊の数が違う／空でも出る'}")

        # T2 --dry で当たる1件が出る
        total += 1
        fresh([item(1, rel, "x = 1", "直した後の文字", "x = 2", ev)])
        rc, out = run(["--design", md, "--src", srcj, "--dry"], mark)
        if rc == 0 and "当たる 1 件" in out and open(code).read() == "x = 1\n":
            ok += 1
            print(f"   T{total} --design --dry で当たる1件が出る → pass")
        else:
            fails.append(f"❌ --dry T{total}: rc={rc} {out[-200:]}")

        # T3 --dry なしで見本のコードが変わる
        total += 1
        rc, out = run(["--design", md, "--src", srcj], mark)
        if rc == 0 and open(code).read() == "x = 2\n":
            ok += 1
            print(f"   T{total} 当てると見本のコードが x = 2 になる → pass")
        else:
            fails.append(f"❌ 当てる T{total}: rc={rc} code={open(code).read()!r}")

        # T4（完成の条件 #3）＝承認の印を1文字 変えると、1件も当たらない
        total += 1
        fresh([item(1, rel, "x = 1", "直した後の文字", "x = 2", ev)])
        open(mark, "w", encoding="utf-8").write("0" * 64)
        rc, out = run(["--design", md, "--src", srcj], mark)
        if rc == 1 and "承認の印と一致: いいえ" in out and open(code).read() == "x = 1\n":
            ok += 1
            print(f"   T{total} 承認の印が違うと1件も当たらない → pass")
        else:
            fails.append(f"❌ 承認の印 T{total}: 印が違うのに当たった／止まらない（rc={rc}）")

        # T5 「状態」の行を消すと、形の食い違いで止まる
        total += 1
        fresh([item(1, rel, "x = 1", "直した後の文字", "x = 2", ev)])
        txt = open(md, encoding="utf-8").read().replace("状態: 確定\n", "")
        open(md, "w", encoding="utf-8").write(txt)
        mark_of(md, mark)
        rc, out = run(["--design", md, "--src", srcj], mark)
        if rc == 1 and "6つの形になっていません" in out and open(code).read() == "x = 1\n":
            ok += 1
            print(f"   T{total} 欄の形が違うと1件も当たらない → pass")
        else:
            fails.append(f"❌ 欄の形 T{total}: rc={rc}")

        # T6 監査結果を当てる道（--report）が、いままでどおり通る（本物の監査結果を --dry で）
        #   ★測るのは「読み取り → テンプレの形の検査 → 全件の確かめ」の段まで通ること。
        #     当たるかどうかは実物の状態に依る（当てた後に実物が動くと「合わない」が正しい答え）ので見ない
        #     （2026-09-24 に実測＝完成の条件のコマンドを直した後、修正 8 が「合わない」になって T6 が落ちた）。
        total += 1
        rep = os.path.join(SDK, ".claude", "audits",
                           "2026-09-24_impl_instruction_design_cp41_audit_report.md")
        rc, out = run(["--report", rep, "--severity", "Critical,Major", "--dry"], None)
        if rc in (0, 1) and "— 当てる重さ:" in out and "テンプレの形ではありません" not in out:
            ok += 1
            print(f"   T{total} --report の道が通る（読み取り・形の検査・全件の確かめまで） → pass")
        else:
            fails.append(f"❌ --report T{total}: rc={rc} {out[-200:]}")

        # T7（完成の条件 #4）＝同じファイルに2件・先の件が後の件の「直す前の文字」を消す → 1件も当たらず rc=1
        total += 1
        fresh([item(1, rel, "x = 1\ny = 2", "直した後の文字", "x = 9", ev),
               item(2, rel, "y = 2", "直した後の文字", "y = 3", ev)], body_text="x = 1\ny = 2\n")
        rc, out = run(["--design", md, "--src", srcj], mark)
        if rc == 1 and open(code).read() == "x = 1\ny = 2\n":
            ok += 1
            print(f"   T{total} 先の件が後の件を消すと、1件も当たらず rc=1 → pass")
        else:
            fails.append(f"❌ 実物と合わない件 T{total}: 半分だけ当たった／rc={rc} code={open(code).read()!r}")

        # T8 対象が守りの仕組み（NEVER_WRITE）なら当てず、一覧に出て rc=1
        total += 1
        guard_rel = ".claude/settings.json"
        fresh([item(1, guard_rel, "x = 1", "直した後の文字", "x = 2", ev)], target_rel=guard_rel)
        rc, out = run(["--design", md, "--src", srcj], mark)
        if rc == 1 and "守りの仕組みなので当てない" in out:
            ok += 1
            print(f"   T{total} 守りの仕組みは当てず一覧に出る（rc=1） → pass")
        else:
            fails.append(f"❌ 守りの仕組み T{total}: rc={rc} {out[-200:]}")

        # T9 対象が TARGET／NEW_FILE に無いなら当てず、一覧に出て rc=1
        total += 1
        fresh([item(1, rel, "x = 1", "直した後の文字", "x = 2", ev)], target_rel="scripts/priority_rebuild/other.py")
        rc, out = run(["--design", md, "--src", srcj], mark)
        if rc == 1 and "TARGET の外" in out and open(code).read() == "x = 1\n":
            ok += 1
            print(f"   T{total} TARGET の外は当てず一覧に出る（rc=1） → pass")
        else:
            fails.append(f"❌ TARGET の外 T{total}: rc={rc} code={open(code).read()!r}")

        # T10 中身に囲みの記号（チルダ3つ）が入ると、元データと合わず1件も当たらない
        total += 1
        fresh([item(1, rel, "x = 1", "直した後の文字", "x = 2\n~~~\nz = 0", ev)])
        rc, out = run(["--design", md, "--src", srcj], mark)
        if rc == 1 and "元データと合いません" in out and open(code).read() == "x = 1\n":
            ok += 1
            print(f"   T{total} 囲みの記号が中身に在ると止まる → pass")
        else:
            fails.append(f"❌ 囲みの記号 T{total}: rc={rc} code={open(code).read()!r}")

        # T11 承認の印が空なら止まる（fail-closed）
        total += 1
        fresh([item(1, rel, "x = 1", "直した後の文字", "x = 2", ev)])
        open(mark, "w", encoding="utf-8").write("")
        rc, out = run(["--design", md, "--src", srcj], mark)
        if rc == 1 and "承認の印が空" in out and open(code).read() == "x = 1\n":
            ok += 1
            print(f"   T{total} 承認の印が空なら止まる → pass")
        else:
            fails.append(f"❌ 承認の印 T{total}: 空の印で止まらない（rc={rc}）")

        # T12 --report と --design を同時に渡すと止まる
        total += 1
        rc, out = run(["--report", md, "--design", md], mark)
        if rc == 2:
            ok += 1
            print(f"   T{total} --report と --design の同時指定で止まる → pass")
        else:
            fails.append(f"❌ 同時指定 T{total}: rc={rc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    for x in fails:
        print(x)
    print(f"\n{'✅' if ok == total else '❌'} selftest {ok}/{total} pass")
    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(main())
