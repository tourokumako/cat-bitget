#!/usr/bin/env python3
"""plain_ja_check.py — 文書の中から、読み直す候補の文を出す（公用文作成の考え方の「文の書き方」に沿って）。

まこさん指示（2026-10-21・逐語）
  「日本語の文法に沿って書いてよ。主語、述語、目的語、形容詞、とか文法ってわかる？」
  「私が決めた4つの決まり（「＝」・括弧・「・」・100字）で見ています→無意味だと思うのでやめてほしい。
   公用文作成の考え方の項目に置き替え」
  「チャットの文章も以下ルールを徹底してほしい」（基準の正本＝.claude/rules/chat_writing_rules.md の A2）

このプログラムがすること
  文化審議会の「公用文作成の考え方」（2022年1月の建議）は、「文の書き方」として13項目を挙げている。
  このプログラムは、13項目のうち、機械で数えられる項目だけについて、読み直す候補の文を出す。
  合否は決めない（終了コードはいつも 0）。候補の文を読んで直すかどうかは、文を書いた人が決める。

  見る項目（番号は、chat_writing_rules.md の A2 の13項目の順）
    1番「一文を短くする。」＝建議の解説の目安「50〜60字ほどになったら読みにくくなっていないか意識する」から、60字を超える文
    3番「三つ以上の情報を並べるときには、箇条書を利用する。」＝1つの文に「・」で3つ以上の語を並べた文
    6番「接続助詞や中止法を多用しない。」＝1つの文に、接続助詞の「が、」が2回以上ある文
    7番「同じ助詞を連続して使わない。」＝「の」でつないだ語が3つ以上続く文（例＝AのBのCの）
    9番「受身形をむやみに使わない。」＝1つの文に、受身の「され」「られ」が2回以上ある文
    10番「二重否定はどうしても必要なとき以外には使わない。」＝「ないわけではない」などの言い方がある文

  機械では数えられない項目（文を書いた人が1文ずつ読んで確かめる）
    2番（一文の論点は一つ）・4番（語順）・5番（主語と述語の関係）・8番（修飾節の順）・11番と12番（係り方）・13番（読点）。

見ない所（文ではない物・まこさんの言葉）
  ``` と ~~~ で囲んだ所／`…` の中／<!-- … --> の目印／「…」の中／要件定義の固定の文の節／
  プログラムが実物から写したデータの囲み（材料・成績表・乱数・関数の行・設定・hook の項目）／表の区切りの行。

使い方
  python3 .claude/tools/plain_ja_check.py <文書.md>      # 読み直す候補の文を全部 出す
  python3 .claude/tools/plain_ja_check.py --selftest
"""
from __future__ import annotations

import re
import sys

LEN_HINT = 60
DATA_BLOCKS = ("MATERIALS", "RANKING", "RANDOM", "CODEREF", "SPEC", "CHECKLIST", "LAWS", "STAGES")
SKIP_SECTION_HEADS = ("## 要件定義と工事の流れ",)
DOUBLE_NEG = ("ないわけではない", "ないわけでもない", "なくはない", "なくもない", "ないことはない", "ないこともない",
              "ないとは限らない", "ないではない")
NO_CHAIN = re.compile(r"の[^、。の\s]{1,12}の[^、。の\s]{1,12}の")


def _strip_inline(s: str) -> str:
    s = re.sub(r"`[^`]*`", "", s)
    s = re.sub(r"<!--.*?-->", "", s)
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r"「[^「」]*」", "「」", s)
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    return s.replace("**", "")


def _units(line: str) -> list:
    t = line.strip()
    if t.startswith("|"):
        if re.fullmatch(r"\|[\s\-:|]*\|?", t):
            return []
        return [c.strip() for c in t.strip("|").split("|")]
    return [re.sub(r"^(?:[-*]\s+|\d+\.\s+|>\s*)", "", t)]


def _sentence_hints(sent: str) -> list:
    out = []
    n = len(sent.strip())
    if n > LEN_HINT:
        out.append(f"1番（一文を短くする）＝{n}字")
    if sent.count("・") >= 2:
        out.append("3番（三つ以上は箇条書）＝「・」で3つ以上を並べている")
    if sent.count("が、") >= 2:
        out.append("6番（接続助詞を多用しない）＝「が、」が2回以上")
    if NO_CHAIN.search(sent):
        out.append("7番（同じ助詞を連続しない）＝「の」が3つ以上続く")
    if len(re.findall(r"(?:され|られ)", sent)) >= 2:
        out.append("9番（受身形をむやみに使わない）＝受身が2回以上")
    if any(w in sent for w in DOUBLE_NEG):
        out.append("10番（二重否定）")
    return out


def hints(text: str) -> list:
    """戻り＝[(行番号, 項目, 文の頭)]。"""
    out = []
    fence = None
    skip_sec = False
    data_blk = None
    for no, ln in enumerate(text.splitlines(), 1):
        f = re.match(r"^\s*(```|~~~)", ln)
        if f:
            fence = None if fence == f.group(1) else (fence or f.group(1))
            continue
        if fence:
            continue
        m = re.search(r"<!-- ACC_([A-Z_]+)_START", ln)
        if m and m.group(1) in DATA_BLOCKS:
            data_blk = m.group(1)
            continue
        if data_blk:
            if f"<!-- ACC_{data_blk}_END" in ln:
                data_blk = None
            continue
        if ln.startswith("## "):
            skip_sec = ln.startswith(SKIP_SECTION_HEADS)
        if skip_sec or ln.startswith("#"):
            continue
        for unit in _units(ln):
            for sent in [x for x in re.split(r"(?<=。)", _strip_inline(unit)) if x.strip()]:
                for h in _sentence_hints(sent):
                    out.append((no, h, sent.strip()[:40]))
    return out


def check_file(path: str) -> int:
    hs = hints(open(path, encoding="utf-8").read())
    for no, h, head in hs:
        print(f"・{path}:{no}  {h}  「{head}…」")
    print(f"読み直す候補 {len(hs)} 件（{path}）。主語と述語の関係・係り方は、1文ずつ読んで確かめる")
    return 0


def selftest() -> int:
    ok = total = 0

    def case(name: str, cond: bool) -> None:
        nonlocal ok, total
        total += 1
        ok += bool(cond)
        print(f"   {'✅' if cond else '❌'} T{total} {name}")

    def has(text: str, key: str) -> bool:
        return any(h.startswith(key) for _n, h, _s in hints(text))
    good = ("この工事の設計書は、プログラムが作ります。\n"
            "ただし、設計書の中の7つの項目は、CC が手で文を書きます。\n"
            "監査人は、次の2つを確かめてください。\n")
    # ★W01 の例の2文目「設計書の中の7つの項目は」は、「の」が3つ続く（7番）。プログラムは、この1件だけを候補に出す
    _g = hints(good)
    case("まこさんが OK した書き方の文（W01 の例）は、「の」が3つ続く1件（7番）だけを候補に出す",
         len(_g) == 1 and _g[0][0] == 2 and _g[0][1].startswith("7番"))
    case("60字を超える文を、1番の候補に出す", has("あ" * 61 + "。", "1番"))
    case("「・」で3つ以上を並べた文を、3番の候補に出す", has("材料・設定・時間足を見る。", "3番"))
    case("「が、」が2回ある文を、6番の候補に出す", has("見たが、無かったが、続けた。", "6番"))
    case("「の」が3つ続く文を、7番の候補に出す", has("設計書の元の表の行を見る。", "7番"))
    case("受身が2回ある文を、9番の候補に出す", has("値が書き替えられ、表が作り直された。", "9番"))
    case("二重否定の文を、10番の候補に出す", has("使えないわけではない。", "10番"))
    case("「」の中・`…` の中・コードの囲み・要件定義の節・データの囲みは見ない",
         hints("まこさんは「" + "あ" * 70 + "」と言った。\n`a・b・c`\n```\n" + "い" * 80 + "\n```\n"
               "## 要件定義と工事の流れ（固定）\n- " + "う" * 80 + "\n## 次\n"
               "<!-- ACC_SPEC_START hash=x -->\n" + "え" * 80 + "\n<!-- ACC_SPEC_END -->\n") == [])
    print(f"\n{'✅' if ok == total else '❌'} selftest {ok}/{total} pass")
    return 0 if ok == total else 1


if __name__ == "__main__":
    a = sys.argv[1:]
    if a == ["--selftest"]:
        sys.exit(selftest())
    if len(a) == 1:
        sys.exit(check_file(a[0]))
    print(__doc__)
    sys.exit(2)
