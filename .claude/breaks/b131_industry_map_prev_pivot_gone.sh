#!/bin/bash
# EXPECT_RC: 1
# MEANS: 業界のライブラリとの対応表から前期間pivot の3行を外す（151回目の直し忘れと同じ）と、検査10 の番人が落ちる
# EXPECT_MSG: ❌ 検査10 が現状の対応表で不一致を出す
# b131_industry_map_prev_pivot_gone — 業界のライブラリとの対応表から前期間pivot の3行を外す（151回目の直し忘れと同じ）と、検査10 の番人が落ちる（工事 m2c15-indicator-six-items-20261004・2026-10-04）
#   守っているもの＝完成の条件の軽い口（observe_diag.py --selftest-catalog）の番人
#   壊し方＝scripts/priority_rebuild/indicator_reference_diag.py の中の、下の old を new に置き換える（r1_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-catalog が「❌ 検査10 が現状の対応表で不一致を出す」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/indicator_reference_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    # ★G-2（2026-10-04・工事 m2c15-indicator-six-items-20261004）＝監査 CP60 の修正18〜21 で足した教科書の前期間 pivot。151回目に当てたとき、\n    #   この対応表に足し忘れ、観察の道具の自己テスト（検査10）が止まっていた。ライブラリの cpr と同じ作りかは照らしていない（定義表の既知答え＝修正20 で確かめる）。\n    "前期間pivotPP": ((), "前の UTC の日で固定する教科書の PP。ライブラリの cpr と同じ作りかは照らしていない（定義表の既知答えで確かめる）"),\n    "前期間pivotR1": ((), "同上（教科書の R1＝2×PP − 前の期間の安値）"),\n    "前期間pivotS1": ((), "同上（教科書の S1＝2×PP − 前の期間の高値）"),\n'
new = ''
if s.count(old) != 1:
    raise SystemExit("[b131_industry_map_prev_pivot_gone] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-catalog
finish
