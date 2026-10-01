#!/usr/bin/env python3
"""gen_review.py — 出す前の見直し表（2026-10-01・142回目 新設）

まこさん指示（逐語 2026-10-01）＝「現状強制では、監査依頼書のチェックがほぼ出来ていないので、チェック項目を見直しすべきでは？」
  「他、設計書や、監査結果を出す前に見直しチェックをさせる強制の内容も怪しいので、再度確認→修正すべきなのでは？」→ 案に「それならばOK」。

なぜ要るか
  いまの強制は、設計書・監査依頼書・監査結果の「形」（検査を通るか・数が合うか・読んだか）しか見ない。
  142回目の監査依頼書 cp57 は、どの強制も通ったのに、問い2 が自動生成の物差しのまま・パスの基準が食い違い・
  争点と関係しない一般観点が残っていた（worklog 20261001 §29〜§32）。
  ＝項目ごとに「意味が通じるか」「実物と合うか」「この依頼の争点に合うか」を、書いた人が根拠つきで見直す表を作らせる。

項目の拾い方（★書く人が項目を選ばない＝抜けが出ない）
  文書の行の頭が「## 」「### 」「#### 」の見出し（コードの囲み ``` の中は除く）と、「- **問いN**」の行を、全部 項目にする。

表の形（置き場＝review_path）
  1行目＝目印 <!-- gen_review doc=<パス> doc_sha256=<文書のハッシュ値> items=<数> -->
  「争点: …」の行＝この文書が答える争点（依頼書なら結論を決める問い・設計書なら やることの表の一文）
  表＝| # | 項目 | ①意味が通じるか | ②実物と合うか（根拠＝ファイル名:行番号） | ③争点に合うか | 判定 |
  判定＝「OK」「直した」「該当なし（理由）」のどれかで始める。

照らすこと（--check・1件でも在れば rc=1）
  ①目印の doc_sha256 が、いまの文書と同じ（表は文書のいまの版について書いたもの）
  ②争点の行が埋まっている ③文書の項目が全部 表に在る ④どの行にも「<書く>」が残っていない・3つの欄と判定が空でない
  ⑤判定が決めた3つの言葉で始まる ⑥②の欄に「ファイル名:行番号」が1つ以上（判定が該当なしの行は無くてよい）
  ⑦その「ファイル名:行番号」のファイルが在り、行番号がそのファイルの行数の中
  ★根拠の行を、文書を書き換えた後に開いたかは、この道具ではなく hook（require_read_used）が会話の記録で見る。
限界（正直に）＝見直しの判断が正しいかは見ない。項目を飛ばさないこと・項目ごとに実在する根拠を書いたことまで。

使い方
  python3 .claude/tools/gen_review.py --skeleton <文書>   # 表の骨組みを書く（在れば項目の行の中身は残し、足りない項目を足す）
  python3 .claude/tools/gen_review.py --check <文書>      # 表を照らす
  python3 .claude/tools/gen_review.py --items <文書>      # 項目の一覧を出す
  python3 .claude/tools/gen_review.py --selftest
"""
from __future__ import annotations

import glob
import hashlib
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SDK = os.path.join(ROOT, "v3-bitget-api-sdk", "bitget-python-sdk-api")
AUDITS = os.path.join(SDK, ".claude", "audits")
REVIEWS = os.path.join(ROOT, ".claude", "state", "reviews")
MARK = "<!-- gen_review"
PLACE = "<書く>"
VERDICTS = ("OK", "直した", "該当なし")
HEAD = "| # | 項目 | ①意味が通じるか | ②実物と合うか（根拠＝ファイル名:行番号） | ③争点に合うか | 判定 |"
REF_RE = re.compile(r"([A-Za-z0-9_.\-/一-龥ぁ-んァ-ヶー]+\.(?:py|md|json|sh|txt|jsonl|csv)):(\d+)")
ITEM_RE = re.compile(r"^(#{2,4} .+|- \*\*問い\d+\*\*.*)$")
SEARCH_DIRS = (os.path.join(ROOT, ".claude"), os.path.join(SDK, ".claude"), os.path.join(SDK, "scripts"))


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def items(text: str) -> list:
    """文書の項目（見出しと「- **問いN**」の行）を出てきた順に返す。コードの囲みの中は除く。"""
    out, fence = [], False
    for ln in text.splitlines():
        if ln.startswith("```"):
            fence = not fence
            continue
        if not fence and ITEM_RE.match(ln):
            key = _key(ln)
            if key not in out:
                out.append(key)
    return out


def _key(ln: str) -> str:
    """表の「項目」の欄に入れる形（| を使わない・長すぎる行は先頭80文字）。"""
    s = ln.strip().replace("|", "／")
    return s if len(s) <= 80 else s[:80] + "…"


def review_path(doc: str) -> str:
    """表の置き場。監査結果は作業場（cp<N>_work/cp<N>_result.review.md）、それ以外は .claude/state/reviews/。
    ★監査は結果を作業場（cp<N>_work/ の中）で埋めてから、結果ファイル（…_cp<N>_audit_report.md）に Write で1回だけ書く。
      作業場の結果と結果ファイルが同じ表を指すように、どちらも cp<N> の番号で1つの置き場にする（中身が同じなら doc_sha256 も同じ）。"""
    b = os.path.basename(doc)
    m = re.search(r"_(cp\d+)_audit_report\.md$", b) or re.search(r"/audits/(cp\d+)_work/", os.path.realpath(doc))
    if m:
        return os.path.join(AUDITS, f"{m.group(1)}_work", f"{m.group(1)}_result.review.md")
    return os.path.join(REVIEWS, b[:-3] + ".review.md")


def _rows(review: str) -> dict:
    """表の行を {項目: [①, ②, ③, 判定]} で返す。"""
    out = {}
    for ln in review.splitlines():
        if not ln.startswith("| ") or ln.startswith(HEAD[:8]) or re.match(r"^\|[-| ]+\|$", ln):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) >= 6 and cells[0].isdigit():
            out[cells[1]] = cells[2:6]
    return out


def skeleton(doc: str, text: str | None = None, old: str | None = None) -> str:
    """表の骨組み。old（前の表）が在れば、同じ項目の行の中身と争点の行を残す。"""
    text = open(doc, encoding="utf-8").read() if text is None else text
    its = items(text)
    prev = _rows(old or "")
    issue = next((ln for ln in (old or "").splitlines() if ln.startswith("争点: ")), f"争点: {PLACE}")
    L = [f"{MARK} doc={os.path.relpath(os.path.realpath(doc), ROOT)} doc_sha256={sha(text)} items={len(its)} -->",
         f"# 見直し表｜{os.path.basename(doc)}",
         "",
         "★この表の項目は gen_review.py が文書から全部 書き出した（書く人は項目を選ばない）。"
         "各行に ①意味が通じるか ②実物と合うか（根拠＝ファイル名:行番号・実際に開いて確かめた行）③争点に合うか を書き、"
         "判定を「OK」「直した」「該当なし（理由）」で始める。",
         "",
         issue,
         "",
         HEAD,
         "|---|---|---|---|---|---|"]
    for i, it in enumerate(its, 1):
        c = prev.get(it, [PLACE, PLACE, PLACE, PLACE])
        L.append(f"| {i} | {it} | {c[0]} | {c[1]} | {c[2]} | {c[3]} |")
    return "\n".join(L) + "\n"


def _resolve(name: str, doc: str) -> str | None:
    """「ファイル名」から実物のパスを探す（パスつきなら根か SDK から・名前だけなら文書と同じ名前か、決まった置き場を探す）。"""
    if "/" in name:
        for base in (ROOT, SDK):
            p = os.path.join(base, name)
            if os.path.isfile(p):
                return p
        return None
    if os.path.basename(doc) == name:
        return doc
    for d in SEARCH_DIRS:
        hit = glob.glob(os.path.join(d, "**", name), recursive=True)
        hit = [h for h in hit if "/audits/cp" not in h or "_work/" not in h]
        if hit:
            return hit[0]
    return None


def check(doc: str, text: str | None = None, review: str | None = None) -> tuple:
    """表を照らす。戻り＝(止める理由の一覧, 根拠の一覧 [(実物のパス, 行番号)])。"""
    text = open(doc, encoding="utf-8").read() if text is None else text
    rp = review_path(doc)
    if review is None:
        if not os.path.isfile(rp):
            return [f"見直し表が無い（{os.path.relpath(rp, ROOT)}）＝python3 .claude/tools/gen_review.py --skeleton {os.path.relpath(doc, ROOT)} で骨組みを作り、全部の行を埋める"], []
        review = open(rp, encoding="utf-8").read()
    ng, refs = [], []
    m = re.search(r"doc_sha256=([0-9a-f]{64})", review.splitlines()[0] if review else "")
    if not m or m.group(1) != sha(text):
        ng.append("見直し表が、文書のいまの版について書いたものではない（doc_sha256 が違う）＝文書を書き換えた後に、--skeleton で表を作り直して見直す")
    iss = next((ln for ln in review.splitlines() if ln.startswith("争点: ")), "")
    if not iss or PLACE in iss or not iss[len("争点: "):].strip():
        ng.append("「争点: 」の行が埋まっていない（依頼書なら結論を決める問い・設計書なら やることの表の一文）")
    rows = _rows(review)
    for it in items(text):
        if it not in rows:
            ng.append(f"項目が表に無い: {it}")
            continue
        c = rows[it]
        if any(PLACE in x or not x for x in c):
            ng.append(f"埋まっていない欄が在る: {it}")
            continue
        if not c[3].startswith(VERDICTS):
            ng.append(f"判定が「OK」「直した」「該当なし（理由）」で始まらない: {it}（{c[3][:20]}）")
        found = REF_RE.findall(c[1])
        if not found and not c[3].startswith("該当なし"):
            ng.append(f"②の欄に根拠の「ファイル名:行番号」が無い: {it}")
        for name, line in found:
            p = _resolve(name, doc)
            if not p:
                ng.append(f"根拠のファイルが見つからない: {name}（{it}）")
                continue
            n = sum(1 for _ in open(p, encoding="utf-8", errors="replace"))
            if not (1 <= int(line) <= n):
                ng.append(f"根拠の行番号がファイルの行数の外: {name}:{line}（{n} 行・{it}）")
                continue
            refs.append((os.path.realpath(p), int(line)))
    return ng, refs


def selftest() -> int:
    d = tempfile.mkdtemp(prefix="gen_review_selftest_")
    doc = os.path.join(d, "x_cp1_audit_request.md")
    body = "# 題\n\n## 節A\n\n- **問い1**＝何か\n\n```\n## 囲みの中\n```\n\n### 小節B\n本文\n"
    open(doc, "w", encoding="utf-8").write(body)
    its = items(body)
    sk = skeleton(doc, body)

    def fill(s, ev="x_cp1_audit_request.md:3", vd="OK"):
        return s.replace(f"争点: {PLACE}", "争点: 実装が設計書のとおりか").replace(
            f"| {PLACE} | {PLACE} | {PLACE} | {PLACE} |", f"| 通じる | {ev} 実物と合う | 合う | {vd} |")
    cases = [
        ("T1 項目は見出しと問いだけ・囲みの中は拾わない", its == ["## 節A", "- **問い1**＝何か", "### 小節B"], True),
        ("T2 骨組みのままは止まる", not check(doc, body, sk)[0], False),
        ("T3 全部 埋めて根拠が実在 → 通る", not check(doc, body, fill(sk))[0], True),
        ("T4 文書を書き換えた後の古い表は止まる", not check(doc, body + "\n## 節C\n", fill(sk))[0], False),
        ("T5 根拠の行番号がファイルの外 → 止まる", not check(doc, body, fill(sk, ev="x_cp1_audit_request.md:999"))[0], False),
        ("T6 根拠が無い（該当なしでない）→ 止まる", not check(doc, body, fill(sk, ev="見た"))[0], False),
        ("T7 該当なし（理由）なら根拠が無くても通る", not check(doc, body, fill(sk, ev="—", vd="該当なし（争点に関係しない）"))[0], True),
        ("T8 判定が決めた言葉でない → 止まる", not check(doc, body, fill(sk, vd="たぶん大丈夫"))[0], False),
        ("T9 作り直しで前の行の中身を残し、増えた項目だけ <書く> になる",
         ("| 通じる |" in skeleton(doc, body + "\n## 節C\n", fill(sk)) and PLACE in skeleton(doc, body + "\n## 節C\n", fill(sk))), True),
    ]
    bad = 0
    for name, got, want in cases:
        ok = got == want
        bad += not ok
        print(f"  {'✅' if ok else '❌'} {name}")
    os.remove(doc)
    os.rmdir(d)
    print(f"自己テスト {len(cases) - bad}/{len(cases)}")
    return 1 if bad else 0


def main(argv: list) -> int:
    if "--selftest" in argv:
        return selftest()
    for flag in ("--skeleton", "--check", "--items"):
        if flag in argv:
            doc = os.path.abspath(argv[argv.index(flag) + 1])
            if not os.path.isfile(doc):
                print(f"❌ 文書が無い: {doc}")
                return 1
            if flag == "--items":
                for i, it in enumerate(items(open(doc, encoding="utf-8").read()), 1):
                    print(f"{i}\t{it}")
                return 0
            rp = review_path(doc)
            if flag == "--skeleton":
                old = open(rp, encoding="utf-8").read() if os.path.isfile(rp) else None
                os.makedirs(os.path.dirname(rp), exist_ok=True)
                open(rp, "w", encoding="utf-8").write(skeleton(doc, old=old))
                n_left = open(rp, encoding="utf-8").read().count(PLACE)
                print(f"✅ 見直し表の骨組みを書いた: {os.path.relpath(rp, ROOT)}（項目 {len(items(open(doc, encoding='utf-8').read()))}・埋める所 {n_left}）")
                return 0
            ng, refs = check(doc)
            for x in ng:
                print(f"❌ {x}")
            print(f"{'✅' if not ng else '❌'} 見直し表の照らし: 止める理由 {len(ng)} 件・根拠 {len(refs)} 件（{os.path.relpath(rp, ROOT)}）")
            return 1 if ng else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
