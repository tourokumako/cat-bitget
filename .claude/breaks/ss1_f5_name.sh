#!/bin/bash
# EXPECT_RC: 1
# MEANS: 計算の登録の名前の型を、どの種類にもつながらない名前にすると、写すプログラムが止まる
# EXPECT_MSG: INDICATOR_TABLE の名前1つにつながらない
# ss1_f5_name — 登録の名前をつながらない名前にすると、写すプログラムが止まる（工事 m2c15-single-source-fix-20261023・設計書1・F-5・2026-10-24）
#   守っているもの＝7-6 の F-5（名前の違う56種が表の名前にそろい、つながらない登録が0件）
#   壊し方＝scripts/priority_rebuild/observe_diag.py:1079 の RSI の登録の名前の型を、定義表に無い型に替える
#   期待＝--verify が「INDICATOR_TABLE の名前1つにつながらない」で落ちる（終了コード 1）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$PR/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
old = '_reg("RSI", "RSI{}", True, lambda d, n: _rsi(d.close, n))'
new = '_reg("RSI", "ZZZ試し{}", True, lambda d, n: _rsi(d.close, n))'
if s.count(old) != 1:
    raise SystemExit("[ss1_f5_name] 壊す対象の文字が1か所でない")
open(p, "w", encoding="utf-8").write(s.replace(old, new, 1))
PYEOF

measure python3 "$ROOT/.claude/state/indicator_review/gen_indicators_draft.py" --verify
finish
