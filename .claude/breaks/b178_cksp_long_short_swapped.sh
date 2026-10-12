#!/bin/bash
# EXPECT_RC: 1
# MEANS: CKSP の買い側を売り側の列に差し替えると、下げ続ける足の既知答え（終値＋17 の線）で検査3 が落ちる（値段が一定の足では見分けられない）
# EXPECT_MSG: close vs CKSPl%: 手計算の既知答えと不一致
# b178_cksp_long_short_swapped — CKSP の買い側を売り側の列に差し替えると、下げ続ける足の既知答え（終値＋17 の線）で検査3 が落ちる（値段が一定の足では見分けられない）（工事 k4-reference-known-20261011・2026-10-11）
#   守っているもの＝完成の条件の軽い口（selftest_match＝検査3 と写しの印の番人）（observe_diag.py --selftest-match）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k4_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-match が「close vs CKSPl%: 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '_reg("close vs CKSPl%", "close vs CKSPl%", True, lambda d, p=None, x=None, q=None: (d.close / _ck(d, p=p, x=x, q=q).iloc[:, 0] - 1) * 100)\n'
new = '_reg("close vs CKSPl%", "close vs CKSPl%", True, lambda d, p=None, x=None, q=None: (d.close / _ck(d, p=p, x=x, q=q).iloc[:, 1] - 1) * 100)\n'
if s.count(old) != 1:
    raise SystemExit("[b178_cksp_long_short_swapped] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-match
finish
