#!/bin/bash
# EXPECT_RC: 1
# MEANS: 1本目の法則の絞り（family と系統）を外すと、R1・R5・R6 を書き替えても束が変わらず、T24⑤ が「期待と違う」で落ちた
# EXPECT_MSG: ❌ T24⑤
# b93 — 候補の一覧が法則を読まない形に壊すと、自己テストが落ちるか
#   守っているもの＝完成の条件 AUDIT-1（法則を1件 書き替えると、実際に組まれる束が変わる・監査 cp36 の C-3）
#   壊し方＝1本目（build_stage_candidates）の「法則が名指しした family／系統だけを通す」2つの判定を if False にする。
#   期待＝自己テスト T24⑤ が落ちる（終了コード 1）。監査 cp36 §1-3 (ii) の実測では T24② も一緒に落ちる。
#   ★壊す対象が見つからなければ止まる（黙って壊さない）。
#   ★EXPECT_MSG は ❌ を含む文字＝正常な出力の進み具合の行には出ない（監査 cp36 の M-2 の直し方）。
source "$(dirname "$0")/lib.sh"

GEN="$PR/engine_tuner_gen.py"
guard "$GEN"

python3 - "$GEN" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old1 = '            if fams_law and fam not in fams_law:\n                continue\n'
old2 = '            if lins_law and iref.FAMILY_LINEAGE[fam]["k"] not in lins_law:\n                continue\n'
for old in (old1, old2):
    if old not in s:
        raise SystemExit("[b93] 壊す対象の行が見つからない: " + old)
s = s.replace(old1, '            if False:  # b93 が壊した（法則の family を読まない）\n                continue\n', 1)
s = s.replace(old2, '            if False:  # b93 が壊した（法則の系統を読まない）\n                continue\n', 1)
open(p, 'w', encoding='utf-8').write(s)
PYEOF

measure python3 "$PR/engine_tuner_gen.py" --selftest
finish
