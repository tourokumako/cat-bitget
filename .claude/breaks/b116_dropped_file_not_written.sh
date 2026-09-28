#!/bin/bash
# EXPECT_RC: 1
# MEANS: 落ちた候補のファイルを書かない形にすると、番人⑨が「5つの場面が全部 ファイルに出ない」で落ちた
# EXPECT_MSG: ❌ ⑨
# b116 — write_outputs が落ちた候補（dropped_*.json）を書かない形にすると、⑨が落ちるか（M2-F-2 の (l)・2026-09-27）
#   守っているもの＝完成の条件 #4（落ちた候補の5つの場面が全部 ファイルに出る）
#   壊し方＝dropped を書く write_text の行を、書かない行に替える。
#   期待＝regime_r9_diag.py --selftest の⑨が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

DIAG="$PR/regime_r9_diag.py"
guard "$DIAG"

python3 - "$DIAG" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    dp.write_text(json.dumps(dropped, ensure_ascii=False, indent=1, default=float) + "\\n", encoding="utf-8")\n'
if s.count(old) != 1:
    raise SystemExit("[b116] 壊す対象の行が1か所でない: " + old.strip())
new = '    pass  # b116 が壊した（落ちた候補を書かない）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$DIAG" --selftest
finish
