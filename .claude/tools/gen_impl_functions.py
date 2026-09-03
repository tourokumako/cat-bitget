#!/usr/bin/env python3
"""gen_impl_functions.py — 設計書の impl_functions を、実物から機械で作る。

まこさん指示 2026-09-02（逐語）＝「全部自動生成で、お前が手打ちするな」「勝手な解釈もするな」。

なぜ要るか
  設計書の impl_functions（この実装で作る・変える関数の一覧）を CC が手で書くと、
  ①書き忘れる ②実装に合わせて後から書き換えられる。
  この道具は実物のファイルを読んで、その中の全関数を json にして出す。CC は1文字も手で書かない。

★2026-09-03（監査 cp16 の E-2・まこさん指定・承認 36051934db6eede3）＝出どころを変えた。
  まこさんの逐語＝「比べる相手を『gitの差分』から『ファイルの中の全関数』に変える。
    目的は ⚠️ を消すことではなく、commit してもしなくても常に ⚠️ が出るようにすること。
    ⚠️ が出続けるのが正しい状態。件数を良く見せる操作をしない。」
  直す前＝verify_design_contract.touched_functions（HEAD の版と いまの版を構文木で比べる）。
    ＝commit すると差分がゼロになり、何も出なかった（下の旧・限界②）。
    承認スクリプトの側も同じものと比べていたので、commit しただけで
    ⚠️（循環）の表示が消え、「設計書の側が出どころ」という嘘に反転していた（監査 cp16 の Q3）。
  直した後＝verify_design_contract.functions_ast（ファイルを読んで全関数を並べる）。git を見ない。

使い方
  python3 .claude/tools/gen_impl_functions.py <ファイル> [<ファイル> ...]
    → 設計書の DESIGN_CONTRACT に貼る json を、そのまま画面に出す。

限界（正直に書く）
  ①出るのは「いまファイルに在る全関数」＝この実装で触っていない関数も出る。
    ＝設計書の impl_functions は、実物と完全に一致する＝承認の画面に必ず ⚠️ が出る。
    **それが正しい状態です**（まこさんの指定）。
  ②この道具自身を書き換えれば無効にできる（git diff には出る）。
  ③（旧・2026-09-03 に解消）commit すると差分がゼロになり、何も出なかった。
"""

from __future__ import annotations

import json
import os
import sys

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
_PR = os.path.join(ROOT, "v3-bitget-api-sdk", "bitget-python-sdk-api",
                   "scripts", "priority_rebuild")
sys.path.insert(0, _PR)

from verify_design_contract import functions_ast          # noqa: E402


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
        out[rel_of(p)] = sorted(functions_ast(open(p, encoding="utf-8").read()))
    print(json.dumps({"impl_functions": out}, ensure_ascii=False, indent=4))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
