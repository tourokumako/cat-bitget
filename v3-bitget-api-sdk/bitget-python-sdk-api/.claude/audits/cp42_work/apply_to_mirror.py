#!/usr/bin/env python3
"""apply_to_mirror.py — 監査 cp42 の結果の修正の指示を、写し（mirror）にだけ当てる（本物には書かない）。

なぜ要るか＝写しの当てる道具は、道具・壊すプログラム・hook を「守りの仕組み」として当てない（正しい動き）。
監査役が「道具の側の修正を写しに当てると自己テスト 16/16 pass」と書いたので、取りまとめ側でも同じことを
走らせて確かめるため、写しの中のファイルにだけ当てる。
使い方＝python3 apply_to_mirror.py <結果.md> <番号,番号,…>
"""
import os
import re
import sys

WORK = os.path.dirname(os.path.abspath(__file__))
M = os.path.join(WORK, "mirror")
M_SDK = os.path.join(M, "v3-bitget-api-sdk", "bitget-python-sdk-api")
sys.path.insert(0, os.path.join(M, ".claude", "tools"))
import gen_audit_docs as g        # noqa: E402
from count_before import fixes_of  # noqa: E402


def mirror_path(rel):
    rel = (rel or "").strip().strip("`")
    if rel.startswith("SDK/"):
        return os.path.join(M_SDK, rel[4:])
    p = os.path.join(M, rel)
    if not os.path.realpath(p).startswith(os.path.realpath(WORK)):
        raise SystemExit(f"❌ 写しの外を指している（{rel}）＝当てない")
    return p


def main(path, nums):
    want = {n.strip() for n in nums.split(",") if n.strip()}
    bad = 0
    for f in fixes_of(open(path, encoding="utf-8").read()):
        if f["番号"] not in want:
            continue
        p = mirror_path(f["対象のファイル"])
        cur = open(p, encoding="utf-8").read()
        before = f["直す前の文字"] or ""
        n = cur.count(before)
        if not before or n != 1:
            print(f"❌ 修正 {f['番号']}: 直す前の文字が写しに {n} か所")
            bad += 1
            continue
        kind, body = f["4つ目"][0][1], f["4つ目"][0][2]
        if kind == "直した後の文字":
            new = cur.replace(before, body, 1)
        elif kind == "足す文字":
            new = cur.replace(before, before + body, 1)
        elif kind == "消す文字":
            new = cur.replace(before, before.replace(body, "", 1), 1)
        else:
            print(f"— 修正 {f['番号']}: {kind}＝当てない")
            continue
        open(p, "w", encoding="utf-8").write(new)
        print(f"✅ 修正 {f['番号']}: {kind} → 写しの {os.path.relpath(p, M)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
