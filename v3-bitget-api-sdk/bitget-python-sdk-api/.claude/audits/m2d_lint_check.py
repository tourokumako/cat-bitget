#!/usr/bin/env python3
"""m2d_lint_check.py — 生成器の静的検査（T25＝lint_provenance）を、同じ関数を呼んで単独で走らせる（2026-09-07）

なぜ在るか:
  `engine_tuner_gen.py --lint-provenance` は「確認のための走行」の旗の一覧に無く、設計↔実装ゲートが止める。
  T25 が ❌ になったとき、どの行が数えられたかを見るには、同じ関数（lint_provenance）を呼ぶ道が要る。
  ★読むだけ。何も書かない。判定は engine_tuner_gen.lint_provenance そのもの（書き写さない）。

使い方:
  python3 .claude/audits/m2d_lint_check.py
"""
from __future__ import annotations

import pathlib
import sys

SDK = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SDK / "scripts/priority_rebuild"))
import engine_tuner_gen as gen  # noqa: E402

if __name__ == "__main__":
    sys.exit(gen.lint_provenance(verbose=True))
