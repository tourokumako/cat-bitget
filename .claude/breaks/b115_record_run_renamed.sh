#!/bin/bash
# EXPECT_RC: 1
# MEANS: 試行を数える口の呼び出しを別の名前に替えると、番人⑧が「record_run が1回も呼ばれていない」で落ちた
# EXPECT_MSG: ❌ ⑧
# b115 — ts.record_run( の呼び出しを ts.record_run_off( に替えると、⑧が落ちるか（M2-F-2・§2.2・恒久24番・2026-09-27）
#   守っているもの＝完成の条件 #3（測る走行が試行を累積に数える）
#   壊し方＝`ts.record_run(` を全部（1か所の見込み） `ts.record_run_off(` に替える。
#   期待＝regime_r9_diag.py --selftest の⑧（構文木の見張り）が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

DIAG="$PR/regime_r9_diag.py"
guard "$DIAG"

python3 - "$DIAG" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = 'ts.record_run('
if s.count(old) != 1:
    raise SystemExit("[b115] 壊す対象が1か所でない: " + old)
new = 'ts.record_run_off('
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$DIAG" --selftest
finish
