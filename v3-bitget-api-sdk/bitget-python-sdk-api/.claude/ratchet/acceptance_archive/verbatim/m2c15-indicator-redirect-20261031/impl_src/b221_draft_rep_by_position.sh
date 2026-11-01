#!/bin/bash
# EXPECT_RC: 1
# MEANS: 写すプログラムの、代表の値を資料の表の名前で軸に合わせる所を、並びの番号で割り当てる形に戻す＝見本の KSTシグナル の g_ に roc1 の値が入り、写すプログラムの自己テストが落ちる
# EXPECT_MSG: ❌ 写す: KSTシグナルの形＝名前に出る軸 g_ に資料の表の signal の値（9）が写り、roc1 に roc1 の値（10）が写る（並びの番号で割り当てない）
# b221_draft_rep_by_position — 代表の値を並びの番号で軸に割り当てると、自己テストが落ちる（工事 m2c15-indicator-redirect-20261031・やることの表 7-6 の F-3・監査 CP94 の修正1・修正2）
#   守っているもの＝7-6 の F-3 の2行目（測るコマンドは、完成の条件と同じ＝写すプログラムの --selftest）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$ROOT/.claude/state/indicator_review/gen_indicators_draft.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    got, left = match_params(rec, names, cur, pnames, firsts, src)\n'
new = '    got, left = {i: (i, "並び") for i in range(min(len(names), len(pnames)))}, list(range(len(names), len(pnames)))\n'
if s.count(old) != 1:
    raise SystemExit("[b221_draft_rep_by_position] 壊す対象（代表の値を名前で軸に合わせる行）が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$F" --selftest
finish
