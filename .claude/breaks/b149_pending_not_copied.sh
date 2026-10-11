#!/bin/bash
# EXPECT_RC: 1
# MEANS: 値を埋めない種類の並びを、資料から写し直す前（11種が載らない形）に戻すと、資料と設定ファイルの照らし（②）が落ちる
# EXPECT_MSG: ❌ ②observe_config.json
# b149_pending_not_copied — 値を埋めない種類の並びを、資料から写し直す前（11種が載らない形）に戻すと、資料と設定ファイルの照らし（②）が落ちる（工事 m2c15-period-settings-20261008・2026-10-08）
#   守っているもの＝完成の条件の照らしの道具（python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources）
#   壊し方＝scripts/priority_rebuild/observe_config.json の中の、下の old を new に置き換える（k3s_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources が「❌ ②observe_config.json」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_config.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = ' "_material_params_pending": ["KST＝範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9", "KSTシグナル＝範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9", "PPO＝範囲が1点のまま（全部の軸）：12・26・9", "PPOシグナル＝範囲が1点のまま（全部の軸）：12・26・9", "PPOヒスト＝範囲が1点のまま（全部の軸）：12・26・9", "STCstoch＝範囲が1点のまま（全部の軸）：23・50・10", "HWC幅%＝範囲が1点のまま（全部の軸）：0.2・0.1・0.1・0.1・1", "MASSI＝範囲が1点のまま（全部の軸）：9・25", "close vs VWAP＝範囲が1点のまま（全部の軸）：288", "pivotPP＝範囲が1点のまま（全部の軸）：288", "pivotR1＝範囲が1点のまま（全部の軸）：288", "pivotS1＝範囲が1点のまま（全部の軸）：288", "POC＝最初の値も範囲も決まらない", "VAH＝最初の値も範囲も決まらない", "VAL＝最初の値も範囲も決まらない", "SMC_SWEEP＝範囲が1点のまま（全部の軸）：15・1.5", "close vs MAMA%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs FAMA%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs ZLMA%＝最初の値も範囲も決まらない", "close vs PMAX%＝最初の値も範囲も決まらない", "close vs SAREXT%＝最初の値も範囲も決まらない", "close vs ABER_ZG%＝範囲が1点のまま（全部の軸）：5・15", "ABER位置＝範囲が1点のまま（全部の軸）：5・15", "HWC位置＝範囲が1点のまま（全部の軸）：0.2・0.1・0.1・0.1・1.0", "close vs VWAP典型＝範囲が1点のまま（全部の軸）：288", "当日VWAP＝最初の値も範囲も決まらない", "前日POC＝最初の値も範囲も決まらない", "前日VAH＝最初の値も範囲も決まらない", "前日VAL＝最初の値も範囲も決まらない", "当日POC＝最初の値も範囲も決まらない", "当日VAH＝最初の値も範囲も決まらない", "当日VAL＝最初の値も範囲も決まらない", "close vs MAMA_HL%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs FAMA_HL%＝範囲が1点のまま（全部の軸）：0.5・0.05"],\n'
new = ' "_material_params_pending": ["KST＝範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9", "KSTシグナル＝範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9", "PPO＝範囲が1点のまま（全部の軸）：12・26・9", "PPOシグナル＝範囲が1点のまま（全部の軸）：12・26・9", "PPOヒスト＝範囲が1点のまま（全部の軸）：12・26・9", "STCstoch＝範囲が1点のまま（全部の軸）：23・50・10", "HWC幅%＝範囲が1点のまま（全部の軸）：0.2・0.1・0.1・0.1・1", "MASSI＝範囲が1点のまま（全部の軸）：9・25", "close vs VWAP＝範囲が1点のまま（全部の軸）：288", "pivotPP＝範囲が1点のまま（全部の軸）：288", "pivotR1＝範囲が1点のまま（全部の軸）：288", "pivotS1＝範囲が1点のまま（全部の軸）：288", "POC＝最初の値も範囲も決まらない", "VAH＝最初の値も範囲も決まらない", "VAL＝最初の値も範囲も決まらない", "SMC_SWEEP＝範囲が1点のまま（全部の軸）：15・1.5", "close vs MAMA%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs FAMA%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs ZLMA%＝最初の値も範囲も決まらない", "close vs PMAX%＝最初の値も範囲も決まらない", "close vs SAREXT%＝最初の値も範囲も決まらない", "close vs ABER_ZG%＝範囲が1点のまま（全部の軸）：5・15", "ABER位置＝範囲が1点のまま（全部の軸）：5・15", "HWC位置＝範囲が1点のまま（全部の軸）：0.2・0.1・0.1・0.1・1.0"],\n'
if s.count(old) != 1:
    raise SystemExit("[b149_pending_not_copied] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py" --check-indicator-sources
finish
