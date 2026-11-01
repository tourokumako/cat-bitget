#!/bin/bash
# EXPECT_RC: 1
# MEANS: H2 の印の対象（WATCHED）から、読む口と1つのデータの行を消す＝grep の数が 0 になり、完成の条件が落ちる
# EXPECT_MSG: leak_causality_diag.py:0
# b226_h2_watch_no_indicators — H2 の印が indicators.json を見張らなくなると、完成の条件が落ちる（工事 m2c15-catalog-redirect-20261101・やることの表 7-6 の F-5）
#   守っているもの＝7-6 の F-5（測るコマンドは、完成の条件と同じ＝grep -H -c で数え、0 なら終わりのコード 1）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/leak_causality_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    f"{_PR}/indicators/indicators.json", f"{_PR}/indicators/indicators.py",\n'
new = ''
if s.count(old) != 1:
    raise SystemExit("[b226_h2_watch_no_indicators] 壊す対象（WATCHED の読む口と1つのデータの行）が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure grep -H -c -F 'indicators/indicators.json' "$PR/leak_causality_diag.py"
finish
