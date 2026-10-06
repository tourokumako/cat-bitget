#!/bin/bash
# EXPECT_RC: 1
# MEANS: 参照表の RCI の行から mako の欄を外すと（表を作り直すと「使わない」へ戻る）、RCI の番人が落ちる
# EXPECT_MSG: ❌ RCI:
# b135_rci_mako_gone — 参照表の RCI の行から mako の欄を外すと（表を作り直すと「使わない」へ戻る）、RCI の番人が落ちる（工事 m2c15-hidden-params-20261004・2026-10-04）
#   守っているもの＝完成の条件の軽い口（observe_diag.py --selftest-catalog）の番人
#   壊し方＝scripts/priority_rebuild/indicator_reference_diag.py の中の、下の old を new に置き換える（r2_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-catalog が「❌ RCI:」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/indicator_reference_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '   known=lambda p: [(_up(p[0] + 5), [(-1, 100.0, 1e-9)]), (_dn(p[0] + 5), [(-1, -100.0, 1e-9)])],\n   mako="2026-10-04 まこさん指示「V9で使ってる指標は入れるようにしてほしい」（V9 の P22 が RCI7 と RCI9 のクロスを使う）")\n'
new = '   known=lambda p: [(_up(p[0] + 5), [(-1, 100.0, 1e-9)]), (_dn(p[0] + 5), [(-1, -100.0, 1e-9)])])\n'
if s.count(old) != 1:
    raise SystemExit("[b135_rci_mako_gone] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-catalog
finish
