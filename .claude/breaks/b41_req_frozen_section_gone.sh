#!/bin/bash
# EXPECT_RC: 1
# MEANS: その検査が落ちた（守りが働いた）
# EXPECT_MSG: ❌ Q6
# b41 — 凍結ファイルから節を1つ消すと、依頼書を作れずに落ちるか
#
#   守っているもの＝next_step §6 の121番・92番・141番（設計書 iter="approval-audit-plumbing-20260907"
#     の完成の条件 #1）。
#   何を守るか＝監査の依頼書は、CC が手で書かず、凍結ファイル（CC が書ける4節）と
#     実物から機械で組み立てる。節が1つでも欠ければ、依頼書を作らせない（fail-closed）。
#     直す前＝この道具は13要素に分ける形に縛られ、複写元の見出しが正本から消えたため、
#     番人が -4/11 pass のまま cp24・cp25・cp26 と3回の監査をまたいでいた。
#   壊し方＝凍結ファイルから [SECTION:スコープ] の行を消す。
#   測るもの＝`gen_audit_request.py --selftest`。
#   期待＝壊すと落ちて終了コードが 1 になる。
#
# ★凍結ファイルは指紋で見張られている（道具の中の QUESTION_SHA）。だから消すと
#   「凍結ファイルが書き換えられた」でも落ちる＝どちらの道でも止まる。
#
# ★時間について（b35 の事故の教訓）＝承認のときの打ち切りは 120秒。実測（2026-09-07）＝2秒。
#
# 限界（正直に書く）
#   ①壊すのは節の見出し1行だけ（4節の中身を書き換える壊し方は、この1本では測れない）
#   ②番人のほかの枝は見ない（終了コードだけを見る）
#   ③このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）

source "$(dirname "$0")/lib.sh"

Q="$SDK/.claude/audits/inputs/_frozen_question_regime.md"
guard "$Q"

python3 - "$Q" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
before = s
s = s.replace("## [SECTION:スコープ]\n", "", 1)
if s == before:
    raise SystemExit("壊す対象の行が見つからない（b41 の前提が変わった）")
open(p, 'w', encoding='utf-8').write(s)
PYEOF

measure python3 "$PR/gen_audit_request.py" --selftest
finish
