#!/bin/bash
# EXPECT_RC: 1
# MEANS: 方向から性質への対応の元から1組を消すと、その方向の種類の性質を決められず、写すプログラムが止まる
# EXPECT_MSG: 方向から性質への対応の表に無い
# ss1_f7_prop — 対応の元から1組を消すと、写すプログラムが止まる（工事 m2c15-single-source-fix-20261023・設計書1・F-7・2026-10-24）
#   守っているもの＝7-6 の F-7（札と性質が表から決まり、決められない種類が0件）
#   壊し方＝scripts/priority_rebuild/gen_indicator_table.py:51 の HOUKOU2PROP から、ボラ量の1組を消す
#   期待＝--verify が「方向から性質への対応の表に無い」で落ちる（終了コード 1）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$PR/gen_indicator_table.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
old = '"ボラ量": "vol", '
if s.count(old) != 1:
    raise SystemExit("[ss1_f7_prop] 壊す対象の文字が1か所でない")
open(p, "w", encoding="utf-8").write(s.replace(old, "", 1))
PYEOF

measure python3 "$ROOT/.claude/state/indicator_review/gen_indicators_draft.py" --verify
finish
