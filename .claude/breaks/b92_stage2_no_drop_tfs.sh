#!/bin/bash
# EXPECT_RC: 1
# MEANS: 2本目に渡す設定の drop_tfs から10分足を外す（10分足を含む一覧）と、T42 が「記録の上位が本物の一覧の本数と違う」で落ちた
# EXPECT_MSG: ❌ T42
# b92 — 2本目が、外す時間足を含めた一覧から材料を取る形に壊すと、自己テストが落ちるか
#   守っているもの＝完成の条件 AUDIT-2（実際に組まれる束が、1本目の一覧の上位から来ていて、外す時間足を含まない・監査 cp36 の C-1）
#   壊し方＝2本目が段1・段2a の一覧を作るときに渡す設定の drop_tfs を ["1m", "3m"] にする（10分足だけ外さない
#     ＝直す前の「10分足が残る」型の壊れ方）。
#   ★2026-09-14＝直す前は空の配列にしていたが、1本目の読み方（`limits.get("drop_tfs") or 既定`）が空を「無い」と
#     同じに扱って既定の3本に戻すため、壊しても何も変わらなかった（承認②・③で rc=0＝完成の条件 #9 の履歴と同じ罠）。
#   期待＝自己テスト T42 が落ちる（終了コード 1）＝記録の「上位」（一覧の本数）が本物と食い違う（案0 で決定的）。
#   ★壊す対象が見つからなければ止まる（黙って壊さない）。
#   ★EXPECT_MSG は ❌ を含む文字＝正常な出力の進み具合の行には出ない（監査 cp36 の M-2 の直し方）。
source "$(dirname "$0")/lib.sh"

GEN="$PR/engine_tuner_gen.py"
guard "$GEN"

python3 - "$GEN" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = ('    c1 = build_stage_candidates("stage1", laws, table, tfs, limits)\n'
       '    c2a = build_stage_candidates("stage2a", laws, table, tfs, limits)\n')
if old not in s:
    raise SystemExit("[b92] 壊す対象の行が見つからない: " + old)
new = ('    c1 = build_stage_candidates("stage1", laws, table, tfs, {**limits, "drop_tfs": ["1m", "3m"]})  # b92 が壊した\n'
       '    c2a = build_stage_candidates("stage2a", laws, table, tfs, {**limits, "drop_tfs": ["1m", "3m"]})  # b92 が壊した\n')
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/engine_tuner_gen.py" --selftest
finish
