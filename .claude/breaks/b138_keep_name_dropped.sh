#!/bin/bash
# EXPECT_RC: 1
# MEANS: 指標ごとの一覧から、採用中の戦略が使う ROC24 を外すと、残す名前の番人（⑫）が落ちる
# EXPECT_MSG: ❌ P-1: 残す名前
# b138_keep_name_dropped — 指標ごとの一覧から、採用中の戦略が使う ROC24 を外すと、残す名前の番人（⑫）が落ちる（工事 m2c15-param-values-20261006・2026-10-06）
#   守っているもの＝完成の条件の軽い口（observe_diag.py --selftest-catalog）
#   壊し方＝scripts/priority_rebuild/observe_config.json の中の、下の old を new に置き換える（r3_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-catalog が「❌ P-1: 残す名前」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_config.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '  "ROC": [[9], [12], [24]],\n'
new = '  "ROC": [[9], [12]],\n'
if s.count(old) != 1:
    raise SystemExit("[b138_keep_name_dropped] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-catalog
finish
