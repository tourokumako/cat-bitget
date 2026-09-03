#!/usr/bin/env python3
"""gen_impl_functions.py — 設計書の impl_functions を、実物から機械で作る。

まこさん指示 2026-09-02（逐語）＝「全部自動生成で、お前が手打ちするな」「勝手な解釈もするな」。

なぜ要るか
  設計書の impl_functions（この実装で作る・変える関数の一覧）を CC が手で書くと、
  ①書き忘れる ②実装に合わせて後から書き換えられる。
  この道具は verify_design_contract.touched_functions（HEAD の版と いまの版を構文木で比べる）
  の結果を、そのまま json にして出す。CC は1文字も手で書かない。

使い方
  python3 .claude/tools/gen_impl_functions.py <ファイル> [<ファイル> ...]
    → 設計書の DESIGN_CONTRACT に貼る json を、そのまま画面に出す。

限界（正直に書く）
  ①出るのは「HEAD と比べて変わった関数」だけ。まだ触っていない関数は出ない
    （＝これから作る関数は、実装した後にこの道具で取り直す）。
  ②commit すると差分がゼロになり、何も出ない。
  ③この道具自身を書き換えれば無効にできる（git diff には出る）。
"""

from __future__ import annotations

import json
import os
import sys

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
_PR = os.path.join(ROOT, "v3-bitget-api-sdk", "bitget-python-sdk-api",
                   "scripts", "priority_rebuild")
sys.path.insert(0, _PR)

from verify_design_contract import touched_functions      # noqa: E402


def rel_of(path: str) -> str:
    """設計書に書く形（リポジトリからの相対）に直す。"""
    p = os.path.realpath(path)
    for base, prefix in ((_PR, "scripts/priority_rebuild/"),
                         (os.path.join(ROOT, ".claude", "tools"), ".claude/tools/"),
                         (os.path.join(ROOT, ".claude", "hooks"), ".claude/hooks/")):
        if p.startswith(os.path.realpath(base) + os.sep):
            return prefix + os.path.basename(p)
    return os.path.relpath(p, ROOT)


def main(paths: list) -> int:
    if not paths:
        print(__doc__)
        return 2
    out = {}
    for p in paths:
        if not os.path.exists(p):
            print(f"[STOP] ファイルがありません: {p}", file=sys.stderr)
            return 1
        out[rel_of(p)] = sorted(touched_functions(p))
    print(json.dumps({"impl_functions": out}, ensure_ascii=False, indent=4))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
