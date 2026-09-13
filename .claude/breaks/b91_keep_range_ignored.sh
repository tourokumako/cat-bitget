#!/bin/bash
# EXPECT_RC: 1
# MEANS: 設定の欄 stage_keep_range を読まずに候補の本数を返す形に壊すと、T35② が「上端 1 なのに案2 が組めた」で落ちた
# EXPECT_MSG: ❌ T35
# b91 — 設定の欄 stage_keep_range を読まない形に壊すと、自己テストが落ちるか
#   守っているもの＝完成の条件 AUDIT-3（設定の欄 stage_keep_range が読まれている・監査 cp36 の C-2）
#   壊し方＝stage_keep_of の戻りを、設定を読まずに候補の本数にする（直す前の「keep=1 の直書き」と同じ型の壊れ方）。
#   期待＝自己テスト T35 が落ちる（終了コード 1）。
#   ★壊す対象が見つからなければ止まる（黙って壊さない）。
#   ★EXPECT_MSG は ❌ を含む文字＝正常な出力の進み具合の行には出ない（監査 cp36 の M-2 の直し方）。
source "$(dirname "$0")/lib.sh"

GEN="$PR/engine_tuner_gen.py"
guard "$GEN"

python3 - "$GEN" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = ('        raise SampleError(f"stage_keep_range が逆さま: lo={lo} > hi={hi}（fail-closed）")\n'
       '    return hi\n')
if old not in s:
    raise SystemExit("[b91] 壊す対象の行が見つからない: " + old)
new = ('        raise SampleError(f"stage_keep_range が逆さま: lo={lo} > hi={hi}（fail-closed）")\n'
       '    return int(n_cands)  # b91 が壊した（設定を読まない）\n')
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/engine_tuner_gen.py" --selftest
finish
