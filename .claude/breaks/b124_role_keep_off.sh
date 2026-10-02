#!/bin/bash
# EXPECT_RC: 1
# MEANS: 役割ごとに上位を残す判定を外すと、自己検査⑫が「役割ごとに keep 本ずつ残っていない」で落ちた
# EXPECT_MSG: ❌ ⑫
# b124 — regime_r9_diag.rank_rows が役割ごとに keep 本を残さないと、⑫が落ちるか（M2-F-6d・2026-09-29）
#   守っているもの＝完成の条件 #2（役割ごとに10本ずつ残す＝worklog 20260928 §51 の1・まこさん OK）
#   壊し方＝`            if keep is None or k <= keep:` を `            if False:` にする（どの行も残す側に入らない）。
#   期待＝regime_r9_diag.py --selftest の⑫が落ちる（終了コード 1）。⑩も一緒に落ちる。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

DIAG="$PR/regime_r9_diag.py"
guard "$DIAG"

python3 - "$DIAG" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '            if keep is None or k <= keep:\n'
if s.count(old) != 1:
    raise SystemExit("[b124] 壊す対象の行が1か所でない: " + old.strip())
new = '            if False:  # b124 が壊した（役割ごとに残さない）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$DIAG" --selftest
finish
