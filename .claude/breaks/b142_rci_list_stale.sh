#!/bin/bash
# EXPECT_RC: 1
# MEANS: 指標ごとの一覧の RCI を、今の rci_periods の組（[[7], [9], [26], [52]]）に戻すと、資料と設定ファイルの照らし（②）が落ちる
# EXPECT_MSG: ❌ ②observe_config.json
# b142_rci_list_stale — 指標ごとの一覧の RCI を、今の rci_periods の組（[[7], [9], [26], [52]]）に戻すと、資料と設定ファイルの照らし（②）が落ちる（工事 m2c15-rci-pivot-sources-20261007・2026-10-07）
#   守っているもの＝完成の条件の照らしの道具（python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources）
#   壊し方＝scripts/priority_rebuild/observe_config.json の中の、下の old を new に置き換える（r5_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources が「❌ ②observe_config.json」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_config.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '  "RCI": [[5], [7], [9], [26], [52]],\n'
new = '  "RCI": [[7], [9], [26], [52]],\n'
if s.count(old) != 1:
    raise SystemExit("[b142_rci_list_stale] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py" --check-indicator-sources
finish
