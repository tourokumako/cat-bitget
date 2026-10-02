#!/bin/bash
# EXPECT_RC: 1
# MEANS: 成績表の全走で、時間足を1本 計算し終えたら結果を書く所（_rank_resume_save）を外すと、自己テスト T-r が「落ちた後に書き終わった時間足のファイルが残らない」で落ちた
# EXPECT_MSG: ❌ T-r②
# b126 — observe_diag.rank_materials_for_regime の、時間足の結果を書く行を外すと、T-r が落ちるか（工事 E・2026-10-03）
#   守っているもの＝完成の条件 #1（観察の道具の自己テスト T-r が、途中で落ちても続きから計算できるかを見ている）
#   壊し方＝時間足の結果を書く行（_rank_resume_save の呼び出し）を消す（直す前と同じ＝最後にまとめて書くだけになる）。
#   期待＝observe_diag.py --selftest-rank-resume の T-r② が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

OD="$PR/observe_diag.py"
guard "$OD"

python3 - "$OD" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '        _rank_resume_save(_ck, tf, auc, nsample)              # ★工事 E＝この時間足の結果を書く\n'
if s.count(old) != 1:
    raise SystemExit("[b126] 壊す対象の行が1か所でない: " + old.strip())
new = '        pass  # b126 が壊した（時間足の結果を書かない）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$OD" --selftest-rank-resume
finish
