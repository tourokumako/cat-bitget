#!/bin/bash
# EXPECT_RC: 1
# MEANS: 写すプログラムの、範囲を②のパラメータの軸へ写す所を外す＝見本の RSI の軸に範囲が写らず、写すプログラムの自己テストが落ちる
# EXPECT_MSG: ❌ 写す: 名前に出る軸に範囲（2〜21）と代表の値（7／14）が写る
# b217_draft_range_not_copied — 範囲が軸へ写らないと、自己テストが落ちる（工事 m2c15-indicator-redirect-20261031・やることの表 7-6 の F-2）
#   守っているもの＝7-6 の F-2（測るコマンドは、完成の条件と同じ＝写すプログラムの --selftest）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$ROOT/.claude/state/indicator_review/gen_indicators_draft.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '            rg0 = old_ranges[ai] if ai < len(old_ranges) else None                     # ★範囲を軸へ写す（search_limits.json）'
new = '            rg0 = None                                                                 # ★範囲を軸へ写す（search_limits.json）'
if s.count(old) != 1:
    raise SystemExit("[b217_draft_range_not_copied] 壊す対象（範囲を軸へ写す行）が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$F" --selftest
finish
