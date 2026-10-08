#!/bin/bash
# EXPECT_RC: 1
# MEANS: BB%b の範囲を直す前（本数 20〜50・倍率 2.0〜2.0）に戻すと、資料と設定ファイルの照らし（②）が落ちる
# EXPECT_MSG: ❌ ②search_limits.json
# b148_bb_range_not_widened — BB%b の範囲を直す前（本数 20〜50・倍率 2.0〜2.0）に戻すと、資料と設定ファイルの照らし（②）が落ちる（工事 m2c15-period-textbook-20261007・2026-10-07）
#   守っているもの＝完成の条件の照らしの道具（python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources）
#   壊し方＝scripts/priority_rebuild/recipes/search_limits.json の中の、下の old を new に置き換える（k3a_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources が「❌ ②search_limits.json」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/recipes/search_limits.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    "BB%b": [{"kind": "int", "lo": 10, "hi": 50}, {"kind": "float", "lo": 1.9, "hi": 2.1, "dec": 1}],\n'
new = '    "BB%b": [{"kind": "int", "lo": 20, "hi": 50}, {"kind": "float", "lo": 2.0, "hi": 2.0, "dec": 1}],\n'
if s.count(old) != 1:
    raise SystemExit("[b148_bb_range_not_widened] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py" --check-indicator-sources
finish
