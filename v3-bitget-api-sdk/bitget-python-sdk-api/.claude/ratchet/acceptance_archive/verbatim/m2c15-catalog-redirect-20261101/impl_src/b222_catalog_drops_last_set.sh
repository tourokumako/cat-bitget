#!/bin/bash
# EXPECT_RC: 1
# MEANS: build_catalog が、読む口の列を作る組の最後の1組を作らない形にする＝名前の並びが写す元の関数と違い、カタログの自己テストが落ちる
# EXPECT_MSG: [材料カタログ] build_catalog の名前の並びが、写す元の関数と違う
# b222_catalog_drops_last_set — build_catalog が列を作る組を1組でも落とすと、カタログの自己テストが落ちる（工事 m2c15-catalog-redirect-20261101・やることの表 7-6 の F-1 の1行目）
#   守っているもの＝7-6 の F-1 の1行目（測るコマンドは、完成の条件と同じ＝observe_diag.py --selftest-catalog）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    for cs in _ind.load().column_sets():\n'
new = '    for cs in _ind.load().column_sets()[:-1]:\n'
if s.count(old) != 1:
    raise SystemExit("[b222_catalog_drops_last_set] 壊す対象（列を作る組を回す行）が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-catalog
finish
