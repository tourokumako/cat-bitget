#!/bin/bash
# EXPECT_RC: 1
# MEANS: PSAR加速 を反転の列に差し替えると、下げ続ける足の既知答え（頭打ちの 0.2）で検査3 が落ちる（値段が一定の足では 0.02 の既知答えも落ちる）
# EXPECT_MSG: PSAR加速: 手計算の既知答えと不一致
# b177_psar_af_column — PSAR加速 を反転の列に差し替えると、下げ続ける足の既知答え（頭打ちの 0.2）で検査3 が落ちる（値段が一定の足では 0.02 の既知答えも落ちる）（工事 k4-reference-known-20261011・2026-10-11）
#   守っているもの＝完成の条件の軽い口（selftest_match＝検査3 と写しの印の番人）（observe_diag.py --selftest-match）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k4_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-match が「PSAR加速: 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '_reg("PSAR加速", "PSAR加速", False, lambda d, af0=None, af=None, max_af=None: _ps(d, af0=af0, af=af, max_af=max_af).iloc[:, 2])\n'
new = '_reg("PSAR加速", "PSAR加速", False, lambda d, af0=None, af=None, max_af=None: _ps(d, af0=af0, af=af, max_af=max_af).iloc[:, 3])\n'
if s.count(old) != 1:
    raise SystemExit("[b177_psar_af_column] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-match
finish
