#!/bin/bash
# EXPECT_RC: 1
# MEANS: 材料の検査の --known-ng の照らしが一覧に無い ❌ を数えないと、--selftest-known-ng が落ちる
# EXPECT_MSG: known-ng の照らし: 一覧に無い ❌ を止めない
# b208_known_ng_new_ignored — 材料の検査の --known-ng の照らしが一覧に無い ❌ を数えないと、--selftest-known-ng が落ちる（工事 m2c15-single-source-20261022・2026-10-22）
#   守っているもの＝完成の条件の材料の検査の --known-ng の照らし（--selftest-known-ng）（python3 scripts/priority_rebuild/observe_diag.py --selftest-known-ng）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（ss_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝python3 scripts/priority_rebuild/observe_diag.py --selftest-known-ng が「known-ng の照らし: 一覧に無い ❌ を止めない」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    new = sorted(got - known)\n'
new = '    new = []\n'
if s.count(old) != 1:
    raise SystemExit("[b208_known_ng_new_ignored] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-known-ng
finish
