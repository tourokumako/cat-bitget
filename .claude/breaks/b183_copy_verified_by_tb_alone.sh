#!/bin/bash
# EXPECT_RC: 1
# MEANS: 検査3 の「写しの独立実装が合っただけでは検証済みに数えない」を外すと、自己テストの番人②が落ちる
# EXPECT_MSG: 写しの独立実装だけで一致検証済みになっている
# b183_copy_verified_by_tb_alone — 検査3 の「写しの独立実装が合っただけでは検証済みに数えない」を外すと、自己テストの番人②が落ちる（工事 k4-reference-known-20261011・2026-10-11）
#   守っているもの＝完成の条件の軽い口（selftest_match＝検査3 と写しの印の番人）（observe_diag.py --selftest-match）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k4_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-match が「写しの独立実装だけで一致検証済みになっている」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '            elif dmax <= ref["tol"]:\n                if ref.get("tb_kind") == "写し":\n                    # ★K-4（2026-10-11・監査 CP60 の修正59）＝写しの独立実装（カタログかライブラリと同じ変形を別の書き方で写した物）は\n                    #   「自分と同じか」しか確かめていない＝一致しても検証済みに数えない。検証済みにするのは手計算の既知答え（③）。\n                    marks.append(f"独立(写し)✓({dmax:.0e})")\n                else:\n                    marks.append(f"独立✓({dmax:.0e})")\n                    verified.add(name)\n'
new = '            elif dmax <= ref["tol"]:\n                marks.append(f"独立✓({dmax:.0e})")\n                verified.add(name)\n'
if s.count(old) != 1:
    raise SystemExit("[b183_copy_verified_by_tb_alone] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-match
finish
