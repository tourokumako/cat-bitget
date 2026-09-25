#!/usr/bin/env python3
"""count_before.py — 監査 cp42 の結果の修正の指示を、本物のファイルに対して数える（読むだけ・何も書かない）。

見るもの（1件ずつ）
  ①「直す前の文字」が、本物の対象のファイルの中に、ちょうど1か所か（なし の件は飛ばす）
  ②「根拠の抜き書き」の「ファイル名:行番号「逐語」」が、本物のその行に在るか
読み取りは写しの gen_audit_docs（本物と同じ中身・根のパスの1行だけ違う）の item_fields と read の仕組みを使う。
"""
import os
import re
import sys

REAL = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
SDK = os.path.join(REAL, "v3-bitget-api-sdk", "bitget-python-sdk-api")
MIRROR_TOOLS = os.path.join(SDK, ".claude", "audits", "cp42_work", "mirror", ".claude", "tools")
sys.path.insert(0, MIRROR_TOOLS)
import gen_audit_docs as g        # noqa: E402

EVID_RE = re.compile(r"(\S+):(\d+)[^「]*「(.*)」\s*$")


def real_path(p):
    p = (p or "").strip().strip("`")
    if p.startswith("SDK/"):
        return os.path.join(SDK, p[4:])
    c = os.path.join(REAL, p)
    return c if os.path.exists(c) else os.path.join(SDK, p)


def fixes_of(text):
    body, _ = g.split_mark(text)
    _, secs = g.split_sections(body)
    out = []
    for head, lines in secs:
        chunk_all = "\n".join(lines)
        sev = ""
        for chunk in re.split(r"^### ", chunk_all, flags=re.M)[1:]:
            name = chunk.split("\n", 1)[0].strip()
            if name in ("Critical", "Major", "Minor", "Process"):
                sev = name
            parts = re.split(r"^#### 修正 (\d+)[ \t]*$", chunk, flags=re.M)
            for num, block in zip(parts[1::2], parts[2::2]):
                f = g.item_fields(num, block)
                f["重さ"] = sev
                out.append(f)
    return sorted(out, key=lambda f: int(f["番号"]))


def main(path):
    text = open(path, encoding="utf-8").read()
    bad = 0
    for f in fixes_of(text):
        num, tgt = f["番号"], f["対象のファイル"]
        before = f["直す前の文字"]
        kinds = [k for _a, k, _b in f["4つ目"]]
        rp = real_path(tgt)
        if "走らせるコマンド" in kinds:
            c = "（コマンドの件・数えない）"
        elif not os.path.isfile(rp):
            c = f"❌ 対象のファイルが無い（{rp}）"
            bad += 1
        else:
            n = open(rp, encoding="utf-8").read().count(before or "\0never\0")
            c = f"{n} か所" + ("" if n == 1 else "  ❌")
            bad += (n != 1)
        ev = (f["根拠の抜き書き"] or "").strip()
        m = EVID_RE.search(ev)
        if not m:
            e = "❌ 根拠の抜き書きが「ファイル名:行番号「逐語」」の形でない"
            bad += 1
        else:
            name, line, quote = m.group(1).strip("`"), int(m.group(2)), m.group(3)
            if len(quote) >= 2 and quote[0] == "`" and quote[-1] == "`":
                quote = quote[1:-1]
            ep = real_path(name)
            if not os.path.isfile(ep):
                e = f"❌ 根拠のファイルが無い（{name}）"
                bad += 1
            else:
                ls = open(ep, encoding="utf-8").read().splitlines()
                if 1 <= line <= len(ls) and quote.strip() in ls[line - 1]:
                    e = f"根拠 {os.path.basename(name)}:{line} 合う"
                else:
                    hits = [i + 1 for i, s in enumerate(ls) if quote.strip() and quote.strip() in s]
                    e = (f"❌ 根拠 {os.path.basename(name)}:{line} 合わない（同じ文の在る行={hits[:3]}）")
                    bad += 1
        print(f"修正 {num:>2}（{f['重さ']:<8}・{f['状態']}・{'/'.join(kinds)}）{os.path.basename(tgt or '')}: 直す前={c} ／ {e}")
    print(f"\n❌ の件数: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
