#!/bin/bash
# EXPECT_RC: 1
# MEANS: 符号を取り去る前処理を一覧から消すと、T36① が「一覧に無い」で落ちた
# EXPECT_MSG: T36
# b82 — 符号を取り去る前処理を外すと、検査が落ちるか
#   守っているもの＝完成の条件 AUDIT-2（DI差・MACDヒスト%・EMA傾き を符号を取り去った大きさで比べる）
#   なぜ要るか＝まこさん指示 2026-09-10「この件、毎回忘れて、設計に入れないし、やろうとしないから、
#     絶対入れろ」。符号を取り去らないと、強い下げまで「トレンドが弱い」と数える。
#   壊し方＝実行器の前処理の一覧から `abs` の登録を消す。
#   期待＝自己テスト T36 が落ちる（終了コード 1）。
#   ★壊す対象が見つからなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

EXE="$PR/engine_tuner_exec.py"
guard "$EXE"

python3 - "$EXE" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    "abs": {"desc": "符号を取り去った大きさ（0 からの距離・窓を持たない）",'
if old not in s:
    raise SystemExit("[b82] 壊す対象の行が見つからない: " + old)
new = '    "_abs_b82_壊した": {"desc": "b82 が名前を変えた",'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/engine_tuner_gen.py" --selftest
finish
