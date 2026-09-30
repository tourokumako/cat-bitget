#!/bin/bash
# EXPECT_RC: 1
# MEANS: その検査が落ちた（守りが働いた）
# EXPECT_MSG: いまの状態で --verify が ❌
# b73 — 関数の行番号を実物から出すのをやめ、固定の数字に戻すと、自己テストが落ちるか
#   守っているもの＝設計書 gen-acceptance-tool-20260909 の完成の条件 #2
#     （行番号が def_lines から出ている＝手で写さない・恒久の決まり69番）
#   壊し方＝build_coderef が実物から引いてくる行番号を、固定の数字に置き換える。
#   期待＝壊すと囲みの中身が正本と食い違うので、T1（いまの状態で --verify）が落ち、
#         --selftest の終了コードが 1 になる。壊さなければ 8/8 pass で 0。
source "$(dirname "$0")/lib.sh"

GEN="$ROOT/.claude/tools/gen_acceptance.py"
guard "$GEN"

# 壊す＝行番号を実物から引くのをやめ、固定の数字にする
python3 - "$GEN" <<'PYEOF'
import re
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
m = re.search(r'^def build_coderef\(d: dict\) -> str:\n(    """.*?"""\n)?', s, re.S | re.M)
if not m:
    sys.exit("壊す相手の関数が見つからない: build_coderef")
# 先頭で、実物から引いた行番号を捨てて固定の数字を返す形にする
inject = m.group(0) + '    return "| 名前 | 定義の行 |\\n|---|---|\\n| 手で写した見本 | 9999 |\\n"\n'
open(p, 'w', encoding='utf-8').write(s[:m.start()] + inject + s[m.end():])
PYEOF

# 測る＝自己テストの終了コード（8件そろわなければ 1）
measure python3 "$GEN" --selftest
finish
