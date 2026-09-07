#!/bin/bash
# b45 — 土台ゲートの「測るだけの口を通す」判定を消すと、その口が止まるか
#
#   守っているもの＝next_step §6 の150番（設計書 iter="approval-audit-plumbing-20260907" の
#     完成の条件 #5）。監査 cp27 の別枠 6-2。
#   何を守るか＝壊すプログラムを走らせ直せるのが まこさんだけ、という状態を直した。
#     土台ゲート（require_acceptance_before_impl.sh の _readonly_seg）は、
#     run_breaks.py を「--measure-only か --selftest が在り、--freeze・--out が無い」ときだけ通す。
#     その判定が消えると、CC も監査も測り直せない状態に戻る。
#   壊し方＝その判定の枝を消す。
#   測るもの＝hook 自身に、測るだけの口のコマンドを渡して呼ぶ（lib.sh の measure_hook）。
#   期待＝壊すと hook が止めて終了コードが 2 になる。
#
# ★なぜ hook を直に呼ぶか＝壊すプログラムは PreToolUse の外で走るので、
#   コマンドを走らせても hook は掛からない。だから hook そのものに入力を渡して測る。
#
# ★時間について（b35 の事故の教訓）＝承認のときの打ち切りは 120秒。実測（2026-09-07）＝1秒未満。
#
# 限界（正直に書く）
#   ①壊すのは判定の枝1つだけ（通す一覧そのものを書き換える壊し方は、この1本では測れない）
#   ②hook が返す文言は見ない（終了コードだけを見る）
#   ③このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）

source "$(dirname "$0")/lib.sh"

H="$ROOT/.claude/hooks/require_acceptance_before_impl.sh"
guard "$H"

python3 - "$H" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
before = s
s = s.replace(
    "        if (_args and _args[0].rsplit('/', 1)[-1] == 'run_breaks.py'\n"
    "                and ('--measure-only' in _toks or '--selftest' in _toks)\n"
    "                and not any(_t.startswith('--freeze') or _t.startswith('--out')\n"
    "                            for _t in _toks)):\n"
    "            return True\n",
    '')
if s == before:
    raise SystemExit("壊す対象の行が見つからない（b45 の前提が変わった）")
open(p, 'w', encoding='utf-8').write(s)
PYEOF

# 測る＝hook に「測るだけの口のコマンド」を渡す。壊すと止めて 2 になる
measure_hook "$H" '{"tool_name":"Bash","tool_input":{"command":"python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/run_breaks.py --measure-only --check-frozen"}}'
finish
