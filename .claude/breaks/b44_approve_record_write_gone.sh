#!/bin/bash
# EXPECT_RC: 1
# MEANS: その検査が落ちた（守りが働いた）
# b44 — 承認の「済」の材料になる記録を書く処理を消すと、番人が落ちるか
#
#   守っているもの＝next_step §6 の146番（設計書 iter="approval-audit-plumbing-20260907" の
#     完成の条件 #4）。監査 cp26 の別枠の指摘3。
#   何を守るか＝承認スクリプトは「済」を、次の2つが両方そろったときだけ書く
#     （approve_impl.sh:414-424）。①壊すプログラムの終了コードが 0 以外 ②条件のコマンドが rc=0。
#     ①の材料は run_breaks.write_record が書く記録（<iter>.breaks.json）。
#     その処理が消えると、①を測る材料が残らない＝「済」の根拠が消える。
#   壊し方＝run_breaks.write_record の中身を、何もしない形にする。
#   測るもの＝`run_breaks.py --selftest`（番人 T8 が 記録を本当に書くかを試す）。
#   期待＝壊すと T8 が落ちて終了コードが 1 になる。
#
# ★時間について（b35 の事故の教訓）＝承認のときの打ち切りは 120秒。実測（2026-09-07）＝数秒。
#
# 限界（正直に書く）
#   ①壊すのは書き込みの1か所だけ（呼び出し側を消す壊し方は、この1本では測れない）
#   ②記録の中身が正しいかは見ない（書かれたかどうかと、行の終了コードだけ）
#   ③このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）

source "$(dirname "$0")/lib.sh"

T="$ROOT/.claude/tools/run_breaks.py"
guard "$T"

python3 - "$T" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
before = s
s = s.replace(
    '    out.parent.mkdir(parents=True, exist_ok=True)\n'
    '    out.write_text(json.dumps(\n'
    '        {"_なにこれ": ("完成の条件の壊すプログラムを、承認のときに機械が走らせた記録。"\n',
    '    return\n    _dead = (\n        {"_なにこれ": ("完成の条件の壊すプログラムを、承認のときに機械が走らせた記録。"\n',
    1)
if s == before:
    raise SystemExit("壊す対象の行が見つからない（b44 の前提が変わった）")
open(p, 'w', encoding='utf-8').write(s)
PYEOF

measure python3 "$T" --selftest
finish
