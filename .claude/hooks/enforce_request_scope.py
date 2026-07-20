#!/usr/bin/env python3
"""enforce_request_scope.py — 判定本体（.sh から呼ばれる・python は別ファイル＝pdca_mark 無言死の教訓）。

目的（まこさん指示 2026-07-20）＝「CC が私の依頼した内容を対応するようにしてほしい」。
CC は依頼の"空白"（値の水準・対象・範囲）を勝手に埋めて別の実験を走らせる。
2026-07-20 実測＝依頼「切り方を％にしろ」に対し CC が水準 1.5% を無断で決めて本走（月−$41.30）。

判定:
  A) current_request.md が無い → exit 3（依頼を書き取っていない＝何をやるか不明のまま実行しようとしている）
  B) 実行コマンド中の「戦略フラグに渡す数値」が current_request.md の本文に文字列として無い → exit 4
     ＝まこさんが言っていない値で実験を走らせるのを止める（値の水準はまこさんが決める領域）。

限界（正直に）: current_request.md は CC が書く＝捏造できる。捏造すればまこさんが読めば分かる（逐語記録のため）。
  機械が保証するのは「依頼に無い値では走れない」だけで、依頼の写し取りの正確さはまこさんの目。
"""
import os
import re
import sys

req_path, cmd = sys.argv[1], sys.argv[2]

if not os.path.exists(req_path):
    sys.stderr.write("NO_REQUEST_FILE ")
    sys.exit(3)

try:
    req = open(req_path, encoding="utf-8", errors="ignore").read()
except OSError:
    sys.stderr.write("READ_ERROR ")
    sys.exit(3)

# 戦略フラグに渡された数値を抽出（--v58-short-sl-pct 1.5 / --v26-gap 0.5 等）。
# 真偽フラグ（値なし）と --tag（実験名）は対象外。数値を伴うものだけ＝「水準の決め打ち」を捕まえる。
pairs = re.findall(r"(--[a-z0-9-]+)[=\s]+(-?\d+(?:\.\d+)?)", cmd)
missing = []
for flag, val in pairs:
    if flag in ("--tag", "--start", "--end", "--box-tf", "--probe-start"):
        continue
    # 依頼本文に その数値が文字列として在るか（1.5 / 1.5% / +1.5 いずれの書かれ方でも拾えるよう数値そのもので照合）
    if val not in req:
        missing.append(f"{flag}={val}")

if missing:
    sys.stderr.write("VALUE_NOT_IN_REQUEST:" + ",".join(missing) + " ")
    sys.exit(4)

sys.exit(0)
