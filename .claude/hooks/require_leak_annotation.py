#!/usr/bin/env python3
"""require_leak_annotation.py — PreToolUse(Write|Edit) 戦略実装への leak パターン書き込みゲート（2026-07-04 まこさん承認）

目的: H2（Prime Directive・未来参照禁止）の物理化が「実装者が自分で assert を書く」頼みだった穴を塞ぐ。
scripts/priority_rebuild/ 配下の .py に、未来参照の典型パターン（.shift(- ／ center=True）を含む行を
書こうとした瞬間、その行に明示アノテーション「# H2OK: <理由>」が無ければブロックする。
＝未来参照を書くこと自体は禁止しない（ラベル/教師生成は学習窓内で正当・H8）が、
**全ての未来参照サイトを書く瞬間に明示宣言させ、レビュー可能にする**（false_positive §0-1 の
「t 時点で取得可能と判定した根拠を1行で明示する義務」の書き込み時強制）。

対象外: basename が build_labels で始まるファイル（ラベル生成の正本＝shift(-K) が本業）・archive/ 配下・
サブエージェント。既存戦略（e35/e36/e37/strat_base）は 2026-07-04 時点で該当パターン 0 件を確認済み＝
本 hook は既存コードを壊さない（新たに書く時だけ効く）。

★2026-08-21（48回目・まこさん指示「あと、見つけたことで修正すべきものは修正してほしい」）に、
  next_step.md の「あとで直すこと」41番を直した。

  直す前の不具合＝**説明の文章（docstring）の中に書いただけで止まっていた。**
  2026-08-16 に「行内コメント（# 以降）を外してから探す」形にしたが、docstring は # で始まらないので
  外れず、41番にも「残る限界＝docstring の中の文章では今も止まる」と書いてあった。
  2026-08-09 と 2026-08-21 の2回、実際に説明の文章で止まって作業が止まった。

  直したこと＝**Python の字句解析（tokenize）で「文字列」と「コメント」を空白に置き換えてから探す。**
  ＝説明の文章・文字列の中の語では止まらず、本物のコードでは止まる。
  ①Write＝渡された全文をそのまま解析する。
  ②Edit＝いまのファイルを読んで new_string を当てはめた「直したあとの全文」を作り、それを解析する
    （断片のままだと字句解析が通らないため）。**検査するのは new_string が占める行だけ**＝
    既存行の再保存で誤発火しない（直す前と同じ考え方）。
  ③字句解析が通らないとき（ファイルが読めない・断片が当てはまらない）は、三重引用符の開け閉めを
    追う簡易版に落ちる。**簡易版でも、直す前より弱くならない**（行内コメントは外し、三重引用符の
    中も外す）。ただし断片が「途中から」始まって説明の文章の途中で切れている場合は、
    直す前と同じく止まりうる（限界）。

  ★わざと壊して止まるか試すテスト＝`python3 require_leak_annotation.py --selftest`（12件）。
  検査自身が効いているかも見る（判定の中身をわざと壊すと、テストが落ちること）。

限界: パターン網羅ではない（rolling の窓ずれ・index 演算等は検出外）＝関所 B（変数の因果性宣言）と
score.py・レビューが引き続き担保。
"""
import io
import json
import os
import re
import sys
import tokenize

ERRLOG = "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/require_leak_annotation_error.log"
PAT = re.compile(r"\.shift\(\s*-|center\s*=\s*True")


def _mask_by_tokenize(text):
    """文字列とコメントを空白に置き換えた、同じ行数のテキストを返す。字句解析が通らなければ None。

    ★行数も1行の長さも変えない＝行番号と桁がそのまま使える。
    """
    lines = text.splitlines(keepends=True)
    buf = [list(x) for x in lines]
    skip = {tokenize.STRING, tokenize.COMMENT}
    for name in ("FSTRING_MIDDLE",):                      # Python 3.12 以降の f 文字列の中身
        if hasattr(tokenize, name):
            skip.add(getattr(tokenize, name))
    try:
        for t in tokenize.generate_tokens(io.StringIO(text).readline):
            if t.type not in skip:
                continue
            (r1, c1), (r2, c2) = t.start, t.end
            for r in range(r1, r2 + 1):
                if not (1 <= r <= len(buf)):
                    continue
                row = buf[r - 1]
                a = c1 if r == r1 else 0
                b = c2 if r == r2 else len(row)
                for c in range(max(a, 0), min(b, len(row))):
                    if row[c] != "\n":
                        row[c] = " "
    except Exception:
        return None
    return ["".join(x) for x in buf]


def _mask_fallback(text):
    """字句解析が通らないとき用の簡易版＝三重引用符と1行の文字列とコメントを空白にする。

    ★直す前（# 以降を外すだけ）より弱くならない。
    """
    out = []
    open_q = None
    for line in text.splitlines():
        row = list(line)
        i = 0
        while i < len(line):
            if open_q:
                j = line.find(open_q, i)
                if j < 0:
                    for c in range(i, len(row)):
                        row[c] = " "
                    i = len(line)
                    break
                for c in range(i, j + 3):
                    row[c] = " "
                i, open_q = j + 3, None
                continue
            if line.startswith('"""', i) or line.startswith("'''", i):
                open_q = line[i:i + 3]
                for c in range(i, i + 3):
                    row[c] = " "
                i += 3
                continue
            ch = line[i]
            if ch == "#":
                for c in range(i, len(row)):
                    row[c] = " "
                i = len(line)
                break
            if ch in "\"'":
                j = i + 1
                while j < len(line):
                    if line[j] == "\\":
                        j += 2
                        continue
                    if line[j] == ch:
                        break
                    j += 1
                for c in range(i, min(j + 1, len(row))):
                    row[c] = " "
                i = j + 1
                continue
            i += 1
        out.append("".join(row))
    return out


def _after_edit(fp, old, new):
    """いまのファイルに new_string を当てはめた「直したあとの全文」と、new_string が占める行の範囲。

    当てはめられなければ (None, None)。★2か所以上 見つかるときも、どこを直すか決められないのであきらめる。
    """
    try:
        with open(fp, encoding="utf-8") as f:
            src = f.read()
    except Exception:
        return None, None
    if not old:
        return None, None
    i = src.find(old)
    if i < 0 or src.find(old, i + 1) >= 0:
        return None, None
    after = src[:i] + new + src[i + len(old):]
    first = src[:i].count("\n") + 1
    last = first + new.count("\n")
    return after, (first, last)


def find_bad(text, rng=None, masker=None):
    """未来参照が「コードとして」書かれている行を探す。戻り＝[(行番号, 行の中身), ...]。

    text＝検査する全文。rng＝(始まりの行, 終わりの行)。None なら全部の行。
    masker＝テスト用の差し替え口（通常は渡さない）。
    """
    raw = text.splitlines()
    masked = (masker or _mask_by_tokenize)(text)
    if masked is None:
        masked = _mask_fallback(text)
    bad = []
    for i, line in enumerate(raw, 1):
        if rng and not (rng[0] <= i <= rng[1]):
            continue
        code = masked[i - 1] if i - 1 < len(masked) else ""
        if PAT.search(code) and "H2OK:" not in line:
            bad.append((i, line.strip()[:120]))
    return bad


def check(d):
    """hook の判定の本体（テストから直接 呼べるように分けてある）。戻り＝[(行番号, 行の中身), ...]。"""
    if d.get("agent_type"):
        return []
    ti = d.get("tool_input", {}) or {}
    fp = ti.get("file_path", "")
    if "scripts/priority_rebuild/" not in fp or not fp.endswith(".py"):
        return []
    if "/archive/" in fp or os.path.basename(fp).startswith("build_labels"):
        return []
    c = ti.get("content")
    if c is not None:                       # Write＝渡された全文をそのまま見る
        return find_bad(c) if c else []
    new = ti.get("new_string") or ""        # Edit＝新しく書く断片だけを見る
    if not new:
        return []
    after, rng = _after_edit(fp, ti.get("old_string") or "", new)
    if after is not None:                   # 直したあとの全文を作れた＝字句解析が効く
        return find_bad(after, rng)
    return find_bad(new)                    # 作れない＝断片のまま（簡易版に落ちる）


def main():
    bad = check(json.load(sys.stdin))
    if not bad:
        return 0
    sys.stderr.write("🔒 [H2 leak アノテーションゲート] 未来参照の典型パターン（.shift(- / center=True）を含む行に「# H2OK: <理由>」がありません:\n")
    for i, line in bad[:5]:
        sys.stderr.write("  L%d: %s\n" % (i, line))
    sys.stderr.write("  → 各行に『# H2OK: <この未来参照が本番再現可能/学習窓に閉じる理由>』を付けてください（false_positive §0-1 の因果性宣言の書き込み時強制）。\n")
    sys.stderr.write("  → 理由を書けない未来参照は H2 違反＝設計から直してください（cat_requirements §4.6 H2・関所B）。\n")
    sys.stderr.write("  → 説明の文章・文字列の中に書いただけなら止まりません（2026-08-21 に直した・41番）。止まったなら、それはコードです。\n")
    return 2


# ══════════ わざと壊して止まるか試すテスト（2026-08-21 新設・まこさん指示）══════════

def _selftest():
    FP = "/x/scripts/priority_rebuild/e99_demo.py"
    S = ".shift(" + "-1)"                                  # 検査の文字列そのものを、この行に残さない
    C = "center" + "=True"
    ng = []

    def w(content, fp=FP):
        return {"tool_input": {"file_path": fp, "content": content}}

    cases = [
        # (名前, 入力, 止まるべきか)
        ("コードの未来参照は止まる",
         w("import pandas as pd\nx = df.close" + S + "\n"), True),
        ("うしろ向きの窓もコードなら止まる",
         w("y = s.rolling(5, " + C + ").mean()\n"), True),
        ("理由が書いてあれば通る",
         w("x = df.close" + S + "  # H2OK: ラベル生成・学習窓に閉じる\n"), False),
        ("行内コメントの中の語では止まらない",
         w("x = 1  # ここで " + S + " を使ってはいけない\n"), False),
        ("★説明の文章（docstring）の中の語では止まらない（41番の不具合）",
         w('def f():\n    """うしろを覗く書き方（' + S + '）も使っていません。"""\n    return 1\n'), False),
        ("★説明の文章の中の うしろ向きの窓 でも止まらない",
         w('"""窓を中央にそろえる書き方（' + C + '）は使っていません。"""\n'), False),
        ("1行の文字列の中の語では止まらない",
         w('msg = "' + S + ' は禁止です"\n'), False),
        ("説明の文章の下に本物のコードが在れば止まる",
         w('def f():\n    """' + S + ' の話。"""\n    return df.close' + S + '\n'), True),
        ("対象のフォルダの外は見ない",
         w("x = df.close" + S + "\n", fp="/x/other/e99_demo.py"), False),
        ("しまってあるフォルダ（archive）は見ない",
         w("x = df.close" + S + "\n", fp="/x/scripts/priority_rebuild/archive/e99.py"), False),
        ("ラベルを作るファイルは見ない",
         w("x = df.close" + S + "\n", fp="/x/scripts/priority_rebuild/build_labels_pct.py"), False),
        ("★書きかけの断片でも、本物のコードなら止まる（簡易版が効く）",
         {"tool_input": {"file_path": FP, "old_string": "@@ 見つからない @@",
                         "new_string": "    x = df.close" + S + "\n"}}, True),
        ("★書きかけの断片でも、説明の文章の中の語では止まらない（簡易版が効く）",
         {"tool_input": {"file_path": FP, "old_string": "@@ 見つからない @@",
                         "new_string": 'def f():\n    """' + S + ' は使っていません。"""\n    return 1\n'}}, False),
    ]
    print("=" * 72)
    print("require_leak_annotation わざと壊して止まるか試すテスト")
    print("=" * 72)
    for name, d, want in cases:
        got = bool(check(d))
        mark = "✅" if got == want else "❌"
        if got != want:
            ng.append(name)
        print(f"  {mark} {name}: 止まる={got}（期待={want}）")

    # ★テスト自身が効いているかの確かめ＝判定の中身をわざと壊すと、テストが落ちること
    print("-" * 72)
    broken = find_bad("x = df.close" + S + "\n", masker=lambda t: [" " * len(x) for x in t.splitlines()])
    if broken:
        ng.append("メタ確認：全部を空白にしても止まった＝検査が入力を見ていない")
    print(f"  {'✅' if not broken else '❌'} メタ確認1：全部を空白に置き換えると、止まらなくなる（＝本当に中身を見ている）")
    keep = PAT.pattern
    try:
        globals()["PAT"] = re.compile(r"この文字は出てこない")
        if find_bad("x = df.close" + S + "\n"):
            ng.append("メタ確認：探す形を消しても止まった")
        print("  ✅ メタ確認2：探す形を消すと、止まらなくなる（＝この形を探している）")
    finally:
        globals()["PAT"] = re.compile(keep)

    print("=" * 72)
    if ng:
        print(f"  ❌ {len(ng)} 件 落ちた: {ng}")
        return 1
    print(f"  ✅ 全部 pass（{len(cases)} 件 ＋ メタ確認2件）")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:
        try:
            with open(ERRLOG, "a") as f:
                f.write(repr(e) + "\n")
        except Exception:
            pass
        sys.exit(0)
