#!/bin/bash
# EXPECT_RC: 1
# MEANS: 写す元の1つ（observe_config.json の material_first_hidden）を読まないようにすると、照らす口が落ちる
# EXPECT_MSG: 欄「名前に出ない軸の最初の値」が写す元と違う
# ss1_f3_source — 写す元の1つを読まないと、照らす口が落ちる（工事 m2c15-single-source-fix-20261023・設計書1・F-3・2026-10-24）
#   守っているもの＝7-6 の F-3（4-4 の1〜9の写す元を全部読み、記録に入らない写す元の値が0件）
#   壊し方＝.claude/state/indicator_review/gen_indicators_draft.py が material_first_hidden を読む所を、空の辞書に替える
#   期待＝--verify が「欄「名前に出ない軸の最初の値」が写す元と違う」で落ちる（終了コード 1）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$ROOT/.claude/state/indicator_review/gen_indicators_draft.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
old = 'cfg.get("material_first_hidden", {})'
new = '{}'
if s.count(old) != 1:
    raise SystemExit("[ss1_f3_source] 壊す対象の文字が1か所でない")
open(p, "w", encoding="utf-8").write(s.replace(old, new, 1))
PYEOF

measure python3 "$F" --verify
finish
