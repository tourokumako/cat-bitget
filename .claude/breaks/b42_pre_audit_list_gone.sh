#!/bin/bash
# b42 — 監査の前に走らせる一覧から1行 消すと、番人が落ちるか
#
#   守っているもの＝next_step §6 の145番・141番（設計書 iter="approval-audit-plumbing-20260907"
#     の完成の条件 #2）。
#   何を守るか＝pre_audit_check.py の CHECKS に、赤のまま放置されていた2本を入れた。
#     ①gen_audit_request.py --selftest（141番＝cp24・cp25・cp26 と3回の監査をまたいだ赤）
#     ②engine_tuner_gen.py --selftest-extra-gate（145番＝新しい検査が毎回 走らない）
#     一覧から黙って外すと、また画面に出なくなる。
#   壊し方＝CHECKS から ①の行を消す。
#   測るもの＝`pre_audit_check.py --selftest`（番人 P8 が この2本の在ることを見る）。
#   期待＝壊すと P8 が落ちて終了コードが 1 になる。
#
# ★時間について（b35 の事故の教訓）＝承認のときの打ち切りは 120秒。実測（2026-09-07）＝数秒。
#
# 限界（正直に書く）
#   ①壊すのは1行だけ（もう1本を消す壊し方は、この1本では測れない）
#   ②番人のほかの枝は見ない（終了コードだけを見る）
#   ③このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）

source "$(dirname "$0")/lib.sh"

T="$ROOT/.claude/tools/pre_audit_check.py"
guard "$T"

python3 - "$T" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
before = s
s = s.replace('    "gen_audit_request.py --selftest",\n', '', 1)
if s == before:
    raise SystemExit("壊す対象の行が見つからない（b42 の前提が変わった）")
open(p, 'w', encoding='utf-8').write(s)
PYEOF

measure python3 "$T" --selftest
finish
