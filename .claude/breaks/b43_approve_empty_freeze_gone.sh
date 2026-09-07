#!/bin/bash
# b43 — 承認のときに「理由の無い空の impl_functions」を止める判定を消すと、番人が落ちるか
#
#   守っているもの＝next_step §6 の146番（設計書 iter="approval-audit-plumbing-20260907" の
#     完成の条件 #3）。監査 cp26 の別枠の指摘3。
#   何を守るか＝承認スクリプト（approve_impl.sh:87）は contract_for_freeze を呼び、
#     「impl_functions が空で理由が無い」なら凍結を書く前に承認を中止する（監査 cp20 の C1）。
#     その判定が消えると、空の凍結がまた書かれる（2026-09-04 に実際に2本 書かれた）。
#   壊し方＝verify_design_contract.contract_for_freeze から、その3行を消す。
#   測るもの＝`verify_design_contract.py --self-test`（番人 N17 が この判定を試す）。
#   期待＝壊すと N17 が落ちて終了コードが 1 になる。
#
# ★なぜ承認スクリプトを直に走らせないか
#   approve_impl.sh は走らせた瞬間に本物の承認の印（acceptance.approved ほか）を書く。
#   壊すプログラムの中でそれを走らせると、本物の承認の状態を書き換えてしまう。
#   だから、承認スクリプトが呼ぶ判定そのものを壊して、その番人で測る。
#
# ★時間について（b35 の事故の教訓）＝承認のときの打ち切りは 120秒。実測（2026-09-07）＝数秒。
#
# 限界（正直に書く）
#   ①壊すのは判定の3行だけ（承認スクリプトの側の呼び出しを消す壊し方は、この1本では測れない）
#   ②番人のほかの枝は見ない（終了コードだけを見る）
#   ③このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）

source "$(dirname "$0")/lib.sh"

guard "$VERIFY"

python3 - "$VERIFY" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
before = s
s = s.replace(
    '    if not fz and not obj.get("no_impl_functions_reason"):\n'
    '        return None, ("impl_functions が空なのに no_impl_functions_reason が無い"\n'
    '                      "（監査 cp20 の C1＝空を凍結しない）")\n',
    '')
if s == before:
    raise SystemExit("壊す対象の行が見つからない（b43 の前提が変わった）")
open(p, 'w', encoding='utf-8').write(s)
PYEOF

measure python3 "$VERIFY" --self-test
finish
