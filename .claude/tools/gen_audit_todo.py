#!/usr/bin/env python3
"""gen_audit_todo.py — 監査レポートから「直す対象」を機械で抜き出して設計書へ差し込む。

まこさん指示 2026-09-02（逐語）
  ・「全部自動生成で、お前が手打ちするな」
  ・「勝手なことしないように全部自動生成しろ」
  ・「勝手な解釈もするな」
  ・「監査の内容を読んでそのとおりに修正するだけじゃん」
  ・「毎回同じミスを繰り返すの禁止。きもちわる」

なぜ要るか（実測・79回目の 2026-09-02）
  CC は監査 cp13 の「直す対象」を、1日に3回 数え間違えた。
    1回目 §6-A の方針3つを外して「11件」と言った（本文は「この監査は、次の3つを求める」）
    2回目 番号を機械で数えて「56件」と言った（S-・E-・抜け道は A- の根拠で、重なっている）
    3回目 1つの返信の中で、3件を挙げた直後に「11件のまま」と書いた
  根っこ＝CC は文書を「中身」でなく「形」（表か・番号が振ってあるか）で拾う。
  ＝CC が数える限り、また外れる。だから CC は数えない。この道具が監査レポートから抜き出す。

何を抜き出すか（★監査レポートの節の見出しだけを見る。CC が選り分けない）
  §6-A 方針            → 表の行
  §6-B 個別の直し       → 表の行（A-1〜A-8）
  §7  プロセス欠陥対策  → 表の行（P-1〜P-3）

★やらないこと（「勝手な解釈もするな」）
  ・根拠の番号（S-・E-・抜け道・I-3 の枝・Q6 の案）を「どの直しで塞ぐか」に紐づけない。
    その対応は監査レポートに書かれていない＝CC の解釈になる。抜き出すのは監査の逐語だけ。
  ・件数を丸めない・言い換えない・要約しない。表の行をそのまま写す。

使い方
  python3 .claude/tools/gen_audit_todo.py --show   <監査レポート>
  python3 .claude/tools/gen_audit_todo.py --write  <監査レポート> <設計書>
  python3 .claude/tools/gen_audit_todo.py --verify <監査レポート> <設計書>
  python3 .claude/tools/gen_audit_todo.py --selftest

限界（正直に書く）
  ①監査レポートの節の見出しの書き方が変わると、抜き出せない（そのときは止まる＝黙って0件にしない）。
  ②抜き出すのは表の行だけ。表の外に書かれた指示（例＝§6-B の下の注記）は入らない。
  ③この道具自身を書き換えれば無効にできる（git diff には出る）。
"""

from __future__ import annotations

import hashlib
import re
import sys

MARK_START = "<!-- AUDIT_TODO_START hash="
MARK_END = "<!-- AUDIT_TODO_END -->"

# ★どの節から抜き出すか。見出しの探し方だけを書く（中身の選り分けはしない）。
#   ★止める見出しに「####」を入れる理由（2026-09-02 実測）＝§6-A の下には 6-A-1〜6-A-4 の
#     小見出しが在り、そこにも表が在る。「###」だけで切ると、方針3件が 17件 になった。
#
# ★2026-09-03 追加＝監査レポートごとに §6 の見出しの形が違う（cp14 で実測して分かった）。
#   cp13＝「### 6-A 方針」「### 6-B 個別の直し」の2本に分かれている。
#   cp14＝「## 6. 改善方向性（6件）」の1本で、小見出しが無い。
#   だから「型」を2つ持ち、レポートを見てどちらかを選ぶ（choose_variant）。
#   ★選び方は「### 6-A の見出しが在るか」だけ＝中身は1文字も読まない（勝手な解釈をしない）。
#   ★どちらの型でも節が切り出せなければ、今までどおり止まる（黙って0件にしない＝限界①）。
VARIANT_CP13 = "cp13型（6-A／6-B に分かれている）"
VARIANT_CP14 = "cp14型（§6 が1本）"
VARIANTS = {
    VARIANT_CP13: (
        ("方針（§6-A）", r"^###\s*6-A\s", r"^####\s|^###\s|^##\s"),
        ("個別の直し（§6-B）", r"^###\s*6-B\s", r"^####\s|^###\s|^##\s"),
        ("プロセス欠陥対策（§7）", r"^##\s*7\.\s", r"^####\s|^###\s|^##\s"),
    ),
    VARIANT_CP14: (
        ("改善方向性（§6）", r"^##\s*6\.\s", r"^####\s|^###\s|^##\s"),
        ("プロセス欠陥対策（§7）", r"^##\s*7\.\s", r"^####\s|^###\s|^##\s"),
    ),
}
VARIANT_MARK = r"^###\s*6-A\s"   # この見出しが在れば cp13型


def choose_variant(text: str) -> tuple[str, tuple]:
    """監査レポートの見出しを見て、どの型で読むかを決める（中身は読まない）。"""
    for ln in text.splitlines():
        if re.match(VARIANT_MARK, ln):
            return VARIANT_CP13, VARIANTS[VARIANT_CP13]
    return VARIANT_CP14, VARIANTS[VARIANT_CP14]


def section_text(text: str, head_pat: str, stop_pat: str) -> str:
    """見出しから次の見出しまでを切り出す。見出しが見つからなければ空を返す。"""
    lines = text.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if re.match(head_pat, ln):
            start = i + 1
            break
    if start is None:
        return ""
    for j in range(start, len(lines)):
        if re.match(stop_pat, lines[j]):
            return "\n".join(lines[start:j])
    return "\n".join(lines[start:])


def table_rows(chunk: str) -> list[list[str]]:
    """表の行だけを返す（見出しの行と区切りの行は外す）。"""
    out: list[list[str]] = []
    for ln in chunk.splitlines():
        s = ln.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 2:
            continue
        if set(cells[0]) <= set("-: "):          # 区切りの行
            continue
        if cells[0] in ("#", "番号"):            # 見出しの行
            continue
        out.append(cells)
    return out


def collect(audit_md: str) -> tuple[list[tuple[str, str, str]], list[str]]:
    """(節の名前, 番号, 中身) の一覧と、見つからなかった節の名前を返す。"""
    text = open(audit_md, encoding="utf-8").read()
    _variant, sections = choose_variant(text)
    items: list[tuple[str, str, str]] = []
    missing: list[str] = []
    for name, head, stop in sections:
        chunk = section_text(text, head, stop)
        if not chunk.strip():
            missing.append(name)
            continue
        rows = table_rows(chunk)
        if not rows:
            missing.append(name)
            continue
        for cells in rows:
            no = re.sub(r"\*+", "", cells[0]).strip()
            body = " ／ ".join(c for c in cells[1:] if c)
            items.append((name, no, body))
    return items, missing


def build_block(audit_md: str) -> str:
    """設計書へ差し込む本文を作る（★CC は1文字も手で書かない）。"""
    items, missing = collect(audit_md)
    if missing:
        raise SystemExit(f"[STOP] 監査レポートから節を切り出せませんでした: {missing}\n"
                         f"  ＝見出しの書き方が変わった疑い。黙って0件にせず止めます（限界①）。")
    per = {}
    for name, _no, _b in items:
        per[name] = per.get(name, 0) + 1
    variant, _sections = choose_variant(open(audit_md, encoding="utf-8").read())
    lines = [
        "**★この表は `.claude/tools/gen_audit_todo.py` が監査レポートから機械で作ります。手で書き換えないでください。**",
        "",
        f"**出どころ**＝`{audit_md}`（見出しの型＝{variant}）",
        "",
        "| 監査の節 | 番号 | 監査に書いてあること（逐語） |",
        "|---|---|---|",
    ]
    for name, no, body in items:
        lines.append(f"| {name} | {no} | {body} |")
    lines.append("")
    lines.append(f"**合計 {len(items)} 件**（"
                 + "／".join(f"{k} {v}件" for k, v in per.items()) + "）")
    return "\n".join(lines)


def swap(design_md: str, block: str) -> str:
    """設計書のマーカーの間を、作った本文で置き換える。"""
    doc = open(design_md, encoding="utf-8").read()
    h = hashlib.sha256(block.encode("utf-8")).hexdigest()[:16]
    new = f"{MARK_START}{h} ここは gen_audit_todo.py が作ります＝手で書き換えない -->\n{block}\n{MARK_END}"
    pat = re.compile(re.escape(MARK_START) + r"[0-9a-f]*[^>]*-->.*?" + re.escape(MARK_END), re.S)
    if not pat.search(doc):
        raise SystemExit("[STOP] 設計書に差し込む場所がありません。次の2行を置いてください:\n"
                         f"  {MARK_START}0 -->\n  {MARK_END}")
    return pat.sub(lambda _m: new, doc)


def verify(audit_md: str, design_md: str) -> int:
    """設計書の中身が、監査レポートから作ったものと同じか。"""
    block = build_block(audit_md)
    h = hashlib.sha256(block.encode("utf-8")).hexdigest()[:16]
    doc = open(design_md, encoding="utf-8").read()
    m = re.search(re.escape(MARK_START) + r"([0-9a-f]+)", doc)
    if not m:
        print("❌ 設計書に目印がありません（--write で作ります）")
        return 1
    if m.group(1) != h:
        print(f"❌ 設計書の中身が、監査レポートと合いません（設計書 {m.group(1)} ／ いま {h}）")
        print("   ＝手で書き換えた疑い。--write で作り直してください。")
        return 1
    body = re.search(re.escape(MARK_START) + r"[0-9a-f]+[^>]*-->\n(.*?)\n" + re.escape(MARK_END),
                     doc, re.S)
    if body is None or body.group(1) != block:
        print("❌ 目印は合っていますが、本文が書き換えられています。")
        return 1
    n = len(collect(audit_md)[0])
    print(f"✅ 設計書と監査レポートが一致（{n} 件・hash {h}）")
    return 0


def selftest() -> int:
    """わざと壊して止まるか試すテスト。"""
    import os
    import tempfile
    ng: list[str] = []
    sample = (
        "### 6-A 方針（★個別の直しより先に読むこと）\n\n"
        "| # | 求めること |\n|---|---|\n"
        "| 1 | あ |\n| 2 | い |\n| 3 | う |\n\n"
        "### 6-B 個別の直し（8件）\n\n"
        "| # | 優先度 | 提案 |\n|---|---|---|\n"
        "| **A-1** | Critical | え |\n| **A-2** | Critical | お |\n\n"
        "## 7. CC プロセス欠陥対策（3件）\n\n"
        "| # | 型 | 提案 |\n|---|---|---|\n"
        "| **P-1** | か | き |\n"
    )
    with tempfile.TemporaryDirectory() as td:
        a = os.path.join(td, "audit.md")
        open(a, "w", encoding="utf-8").write(sample)

        items, missing = collect(a)
        ok1 = (not missing and len(items) == 6)
        print(f"  {'✅' if ok1 else '❌'} T1 3つの節から全部 抜ける（{len(items)}件・欠け {missing}）")
        if not ok1:
            ng.append("T1")

        b = os.path.join(td, "audit2.md")
        # ★壊し方＝見出しから「6-A」そのものを消す（「6-A ほうしん」だと見出しに一致してしまい、
        #   壊れていないのと同じだった＝2026-09-02 に実測して直した）
        open(b, "w", encoding="utf-8").write(
            sample.replace("### 6-A 方針（★個別の直しより先に読むこと）", "### 方針"))
        try:
            build_block(b)
            print("  ❌ T2 節が無いのに止まらなかった")
            ng.append("T2")
        except SystemExit:
            print("  ✅ T2 節が無ければ止まる（黙って0件にしない）")

        d = os.path.join(td, "design.md")
        open(d, "w", encoding="utf-8").write(f"# 設計書\n\n{MARK_START}0 -->\n{MARK_END}\n")
        # ★先に中身を作ってから書く（open(w) を先に評価するとファイルが空になり、
        #   swap が空のファイルを読んで落ちた＝2026-09-02 に実測して直した）
        filled = swap(d, build_block(a))
        open(d, "w", encoding="utf-8").write(filled)
        rc_ok = verify(a, d)
        doc = open(d, encoding="utf-8").read().replace("| 方針（§6-A） | 1 | あ |",
                                                       "| 方針（§6-A） | 1 | あ（手で足した） |")
        open(d, "w", encoding="utf-8").write(doc)
        rc_ng = verify(a, d)
        ok3 = (rc_ok == 0 and rc_ng == 1)
        print(f"  {'✅' if ok3 else '❌'} T3 手で書き換えると落ちる（作った直後 {rc_ok} ／ 書き換えた後 {rc_ng}）")
        if not ok3:
            ng.append("T3")

        # ★2026-09-03 追加＝cp14 の見出しの形（§6 が1本・6-A/6-B が無い）でも抜けるか
        sample14 = (
            "## 6. 改善方向性（6件）\n\n"
            "| # | 優先度 | 提案 | なぜ |\n|---|---|---|---|\n"
            "| **B-1** | Critical | あ | い |\n"
            "| **B-2** | Major | う | え |\n\n"
            "## 7. CC プロセス欠陥対策（3件）\n\n"
            "| # | 型 | 何が起きたか | 提案 |\n|---|---|---|---|\n"
            "| **P-4** | お | か | き |\n"
        )
        c = os.path.join(td, "audit14.md")
        open(c, "w", encoding="utf-8").write(sample14)
        v14, _ = choose_variant(sample14)
        items14, missing14 = collect(c)
        ok4 = (v14 == VARIANT_CP14 and not missing14 and len(items14) == 3)
        print(f"  {'✅' if ok4 else '❌'} T4 cp14 の見出しでも抜ける"
              f"（型 {v14}・{len(items14)}件・欠け {missing14}）")
        if not ok4:
            ng.append("T4")

        # ★cp13 の見本を cp13型と判定するか（型の選び方が逆になっていないか）
        v13, _ = choose_variant(sample)
        ok5 = (v13 == VARIANT_CP13)
        print(f"  {'✅' if ok5 else '❌'} T5 cp13 の見本は cp13型と判定する（{v13}）")
        if not ok5:
            ng.append("T5")

        # ★cp14型でも §7 が無ければ止まる（黙って0件にしない）
        e = os.path.join(td, "audit14b.md")
        open(e, "w", encoding="utf-8").write(
            sample14.replace("## 7. CC プロセス欠陥対策（3件）", "## おわり"))
        try:
            build_block(e)
            print("  ❌ T6 cp14型で §7 が無いのに止まらなかった")
            ng.append("T6")
        except SystemExit:
            print("  ✅ T6 cp14型でも §7 が無ければ止まる")

    print(f"{'❌' if ng else '✅'} 番人 {6 - len(ng)}/6 pass")
    return 1 if ng else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    if "--show" in sys.argv:
        print(build_block(sys.argv[sys.argv.index("--show") + 1]))
        sys.exit(0)
    if "--write" in sys.argv:
        i = sys.argv.index("--write")
        _a, _d = sys.argv[i + 1], sys.argv[i + 2]
        # ★先に中身を作ってから書く（2026-09-02 の事故）。
        #   直す前＝open(_d, "w") が先に評価されて設計書が空になり、その後 swap が空のファイルを
        #   読んで落ちた。＝本物の設計書を1本 消した。番人の T3 で同じ形を直したのに、
        #   ここ（本体）を直していなかった。
        _filled = swap(_d, build_block(_a))
        open(_d, "w", encoding="utf-8").write(_filled)
        print(f"✅ 設計書へ差し込みました: {_d}")
        sys.exit(0)
    if "--verify" in sys.argv:
        i = sys.argv.index("--verify")
        sys.exit(verify(sys.argv[i + 1], sys.argv[i + 2]))
    print(__doc__)
    sys.exit(2)
