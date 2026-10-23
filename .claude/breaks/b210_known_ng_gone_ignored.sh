#!/bin/bash
# EXPECT_RC: 1
# MEANS: 材料の検査の --known-ng の照らしが、一覧に在るのに出なかった行（直った行）を数えないと、--selftest-known-ng が落ちる
# EXPECT_MSG: known-ng の照らし: 直った行（一覧に在るが出なかった ❌）を止めない
# b210_known_ng_gone_ignored — 一覧に在る ❌ が出なくなったのを数えないと、--selftest-known-ng が落ちる（監査 CP87 の修正6）
#   守っているもの＝材料の検査の --known-ng の照らし（python3 scripts/priority_rebuild/observe_diag.py --selftest-known-ng）の②
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    gone = sorted(known - got)\n'
new = '    gone = []\n'
if s.count(old) != 1:
    raise SystemExit("[b210_known_ng_gone_ignored] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-known-ng
finish
