#!/bin/bash
# EXPECT_RC: 1
# MEANS: 段ごとの記録を書く行を消すと、T41① が「鍵6つが揃っていない」で落ちた
# EXPECT_MSG: ❌ T41①
# b87 — 段ごとの記録を書く行を消すと、検査が落ちるか
#   守っているもの＝完成の条件 条件13（段ごとの記録の鍵6つが全部 揃っている）
#   出どころ＝監査 cp35 の Critical C-3（作る順の手順6 に当たる条件が1つも無かった）
#   壊し方＝引いた記録に段ごとの記録を足す行を、空の一覧を入れる形に変える。
#   期待＝自己テスト T41 が落ちる（終了コード 1）。
#   ★壊す対象が見つからなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

GEN="$PR/engine_tuner_gen.py"
guard "$GEN"

python3 - "$GEN" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '        out.append(row)\n    _STAGE_COUNT_MEMO[_key] = copy.deepcopy(out)'
if old not in s:
    raise SystemExit("[b87] 壊す対象の行が見つからない（段ごとの記録の組み立て）")
new = ('        out.append({"stage": sk})  # b87 が壊した（鍵を1つだけにした）\n'
       '    _STAGE_COUNT_MEMO[_key] = copy.deepcopy(out)')
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/engine_tuner_gen.py" --selftest
finish
