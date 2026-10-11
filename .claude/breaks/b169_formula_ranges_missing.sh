#!/bin/bash
# EXPECT_RC: 1
# MEANS: 探す範囲から、1つ目の工事で「使う」に入った種類の行を外すと、資料と設定ファイルの照らし（②）が落ちる
# EXPECT_MSG: ❌ ②search_limits.json
# b169_formula_ranges_missing — 探す範囲から、1つ目の工事で「使う」に入った種類の行を外すと、資料と設定ファイルの照らし（②）が落ちる（工事 m2c15-formula-settings-20261011・2026-10-11）
#   守っているもの＝完成の条件の照らしのプログラム（python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources）
#   壊し方＝scripts/priority_rebuild/recipes/search_limits.json の中の、下の old を new に置き換える（k3cs_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources が「❌ ②search_limits.json」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/recipes/search_limits.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    "S-Rタッチ確定1時間ATR": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.5, "hi": 1.5, "dec": 1}, {"kind": "int", "lo": 7, "hi": 21}],\n    "DPO教科書%": [{"kind": "int", "lo": 14, "hi": 40}],\n    "StochRSI素%K": [{"kind": "int", "lo": 7, "hi": 21}],\n    "TRIX_EMAシグナル": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}],\n    "TRIX_EMAヒスト": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}],\n    "realized_vol_rv": [{"kind": "int", "lo": 10, "hi": 50}],\n    "close vs SSF平均%": [{"kind": "int", "lo": 10, "hi": 200}],\n    "close vs TRIMA_TA%": [{"kind": "int", "lo": 1, "hi": 200}],\n    "close vs VIDYA_CMO%": [{"kind": "int", "lo": 20, "hi": 200}]\n'
new = '    "S-Rタッチ確定1時間ATR": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.5, "hi": 1.5, "dec": 1}, {"kind": "int", "lo": 7, "hi": 21}]\n'
if s.count(old) != 1:
    raise SystemExit("[b169_formula_ranges_missing] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py" --check-indicator-sources
finish
