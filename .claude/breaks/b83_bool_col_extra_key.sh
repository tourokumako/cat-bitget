#!/bin/bash
# EXPECT_RC: 1
# MEANS: 未知の鍵を弾く判定を外すと、T37b② が「未知の鍵を書いても通った」で落ちた
# EXPECT_MSG: T37b
# b83 — 真偽の列の「未知の鍵を弾く」判定を外すと、検査が落ちるか
#   守っているもの＝完成の条件 条件9（`bool_col` に `bool_col`・`want` 以外の鍵を書くと G5 で止まる）
#   出どころ＝監査 cp35 の Critical C-2（直す前の条件は実測で鳴らなかったので書き替えた）
#   壊し方＝実行器の「未知のフィールドを弾く」判定を、常に空集合にする。
#   期待＝自己テスト T37b が落ちる（終了コード 1）。
#   ★壊す対象が見つからなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

EXE="$PR/engine_tuner_exec.py"
guard "$EXE"

python3 - "$EXE" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    extra = set(c) - {"bool_col", "want"}'
if old not in s:
    raise SystemExit("[b83] 壊す対象の行が見つからない: " + old)
new = '    extra = set()  # b83 が壊した（未知の鍵を弾かない）'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/engine_tuner_gen.py" --selftest
finish
