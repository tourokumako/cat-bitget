#!/bin/bash
# EXPECT_RC: 1
# MEANS: 名前に出ない軸の最初の値から、1つ目の工事で「使う」に入った種類の行を外すと、資料と設定ファイルの照らし（②）が落ちる
# EXPECT_MSG: ❌ ②observe_config.json
# b168_formula_hidden_missing — 名前に出ない軸の最初の値から、1つ目の工事で「使う」に入った種類の行を外すと、資料と設定ファイルの照らし（②）が落ちる（工事 m2c15-formula-settings-20261011・2026-10-11）
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
old = '  "HWC位置": {"スキャル": [[0.2, 0.1, 0.1, 0.1, 1.0]], "デイトレ": [[0.2, 0.1, 0.1, 0.1, 1.0]]},\n  "SQZ_ON_Carter": {"スキャル": [[20, 2, 20, 1.5]], "デイトレ": [[20, 2, 20, 1.5]]},\n  "StochRSI素%K": {"スキャル": [], "デイトレ": [[14, 3, 3]]},\n  "close vs SSF平均%": {"スキャル": [[10, 2]], "デイトレ": [[10, 2]]},\n  "close vs MAMA_HL%": {"スキャル": [[0.5, 0.05]], "デイトレ": [[0.5, 0.05]]},\n  "close vs FAMA_HL%": {"スキャル": [[0.5, 0.05]], "デイトレ": [[0.5, 0.05]]}\n'
new = '  "HWC位置": {"スキャル": [[0.2, 0.1, 0.1, 0.1, 1.0]], "デイトレ": [[0.2, 0.1, 0.1, 0.1, 1.0]]}\n'
if s.count(old) != 1:
    raise SystemExit("[b168_formula_hidden_missing] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py" --check-indicator-sources
finish
