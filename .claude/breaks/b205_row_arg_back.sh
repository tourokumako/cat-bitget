#!/bin/bash
# EXPECT_RC: 1
# MEANS: 定義表の行に方向と性質の引数を戻すと、表の照らしが落ちる
# EXPECT_MSG: ①定義表の行が方向か性質を引数で受け取っている
# b205_row_arg_back — 定義表の行に方向と性質の引数を戻すと、表の照らしが落ちる（工事 m2c15-single-source-20261022・2026-10-22）
#   守っているもの＝完成の条件の表の照らし（①〜⑥）（python3 scripts/priority_rebuild/gen_indicator_table.py --verify）
#   壊し方＝scripts/priority_rebuild/indicator_reference_diag.py の中の、下の old を new に置き換える（ss_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝python3 scripts/priority_rebuild/gen_indicator_table.py --verify が「①定義表の行が方向か性質を引数で受け取っている」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/indicator_reference_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '_r(r"ADX(\\d+)", "ADX",\n'
new = '_r(r"ADX(\\d+)", "ADX", "状態量", "none",\n'
if s.count(old) != 1:
    raise SystemExit("[b205_row_arg_back] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/gen_indicator_table.py" --verify
finish
