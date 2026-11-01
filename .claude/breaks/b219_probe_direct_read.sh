#!/bin/bash
# EXPECT_RC: 1
# MEANS: 数える道具 ss_outside_probe.py に、indicators.json を直に読む行を戻す＝grep が当たり、完成の条件（当たれば終わりのコード 1）が落ちる
# EXPECT_MSG: / "indicators.json"
# b219_probe_direct_read — 読む口を通さずに indicators.json を直に開く行が戻ると、完成の条件が落ちる（工事 m2c15-indicator-redirect-20261031・やることの表 7-6 の F-4・F-5）
#   守っているもの＝7-6 の F-4・F-5（測るコマンドは、完成の条件と同じ＝2本を grep して当たれば 1）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$ROOT/.claude/state/indicator_review/ss_outside_probe.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = 'FAMS = set(_ind.load().names("指標の記録")) | set(_ind.load().names("部品の記録"))\n'
new = old + '_IJ = PR / "indicators" / "indicators.json"\nFAMS = set(json.loads(_IJ.read_text(encoding="utf-8")).get("指標の記録", {}))\n'
if s.count(old) != 1:
    raise SystemExit("[b219_probe_direct_read] 壊す対象（読む口から名前を読む行）が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure bash -c "! grep -n -E '/ .indicators\.json.' \"$ROOT/.claude/state/indicator_review/gen_fix_inventory.py\" \"$ROOT/.claude/state/indicator_review/ss_outside_probe.py\""
finish
