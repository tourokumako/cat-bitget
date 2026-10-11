#!/bin/bash
# EXPECT_RC: 1
# MEANS: 指標ごとの一覧から、1つ目の工事で「使う」に入った種類の行を外すと、資料と設定ファイルの照らし（②）が落ちる
# EXPECT_MSG: ❌ ②observe_config.json
# b167_formula_params_missing — 指標ごとの一覧から、1つ目の工事で「使う」に入った種類の行を外すと、資料と設定ファイルの照らし（②）が落ちる（工事 m2c15-formula-settings-20261011・2026-10-11）
#   守っているもの＝完成の条件の照らしのプログラム（python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources）
#   壊し方＝scripts/priority_rebuild/observe_config.json の中の、下の old を new に置き換える（k3cs_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources が「❌ ②observe_config.json」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_config.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '  "RCI": [[5], [7], [9], [26], [52]],\n  "DPO教科書%": [[20]],\n  "StochRSI素%K": [[14]],\n  "TRIX_EMAシグナル": [[15, 9]],\n  "TRIX_EMAヒスト": [[15, 9]],\n  "close vs SSF平均%": [[10]],\n  "close vs TRIMA_TA%": [[10]]\n'
new = '  "RCI": [[5], [7], [9], [26], [52]]\n'
if s.count(old) != 1:
    raise SystemExit("[b167_formula_params_missing] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py" --check-indicator-sources
finish
