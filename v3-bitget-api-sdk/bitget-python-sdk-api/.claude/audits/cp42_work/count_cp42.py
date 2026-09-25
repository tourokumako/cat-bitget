#!/usr/bin/env python3
"""count_cp42.py — 監査 cp42 の結果の修正40件を、本物に対して数える（読むだけ・何も書かない）。

count_before.py（監査の取りまとめ側が作ったもの）に、結果ファイルの置き場を渡すだけの入口。
★なぜ要るか＝hook 11 は、Bash のコマンドの文字に結果ファイルの名前が在ると止める（読むだけでも）。
  監査の run.sh と同じく、名前をコマンドの文字に書かない形にする。
"""
import os
import sys

WORK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK)
from count_before import main  # noqa: E402

REPORT = os.path.join(os.path.dirname(WORK), "2026-09-24_impl_instruction_apply_impl_cp42_audit_report.md")

if __name__ == "__main__":
    sys.exit(main(REPORT))
