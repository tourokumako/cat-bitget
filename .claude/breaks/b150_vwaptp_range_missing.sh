#!/bin/bash
# EXPECT_RC: 1
# MEANS: 探す範囲から close vs VWAP典型 の行を外すと、資料と設定ファイルの照らし（②）が落ちる
# EXPECT_MSG: ❌ ②search_limits.json
# b150_vwaptp_range_missing — 探す範囲から close vs VWAP典型 の行を外すと、資料と設定ファイルの照らし（②）が落ちる（工事 m2c15-period-settings-20261008・2026-10-08）
#   守っているもの＝完成の条件の照らしの道具（python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources）
#   壊し方＝scripts/priority_rebuild/recipes/search_limits.json の中の、下の old を new に置き換える（k3s_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources が「❌ ②search_limits.json」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/recipes/search_limits.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    "RCI": [{"kind": "int", "lo": 5, "hi": 52}],\n    "close vs VWAP典型": [{"kind": "int", "lo": 288, "hi": 288}],\n'
new = '    "RCI": [{"kind": "int", "lo": 5, "hi": 52}],\n'
if s.count(old) != 1:
    raise SystemExit("[b150_vwaptp_range_missing] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py" --check-indicator-sources
finish
