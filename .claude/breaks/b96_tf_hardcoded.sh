#!/bin/bash
# EXPECT_RC: 1
# MEANS: 時間足の絞りを直書きに戻すと、T40③-6 が「段2c の候補に執行足が無い」で落ちた
# EXPECT_MSG: ❌ T40③-6
# b96 — 時間足の条件を法則から読まない形に戻すと、検査が落ちるか
#   守っているもの＝完成の条件 AUDIT-4（時間足の条件と R3 を法則ファイルから読む）
#   なぜ要るか（監査 cp36 の M-3）＝直す前は「執行足より上」がコードに直書きしてあり、
#     法則 C4 を書き替えても組まれる束が1文字も変わらなかった。
#   壊し方＝`stage_tfs_of` が、法則を読まずに いつも「5分足より後ろ」に絞る形に戻す。
#   ★2026-09-16＝測る相手を T24⑤ から T40③-6 に替えた。走らせたら rc=0（壊れていなかった）。
#     理由＝T24⑤ は「法則を書き替えると束が変わるか」を見る。R3 は `stage_lineages_of`、
#     C4 は `_check_bundle_counts` が読むので、`stage_tfs_of` を壊しても束は変わり続けた。
#     ＝この壊し方が測っていたのは T24⑤ ではなかった。
#   期待＝自己テスト T40③-6 が落ちる（終了コード 1）。段2c は law_tf を持たない段なので、
#     いつも上位足に絞ると 執行足（5分足）が候補から消える。
#   ★壊す対象が1つに定まらなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

GEN="$PR/engine_tuner_gen.py"
guard "$GEN"

python3 - "$GEN" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    if _law_tf_upper(laws, spec_c.get("law_tf")):\n'
if s.count(old) != 1:
    raise SystemExit(f"[b96] 壊す対象の行が1つに定まらない（{s.count(old)} 件）")
new = '    if True:  # b96 が壊した（法則を読まず、いつも「5分足より後ろ」に絞る）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/engine_tuner_gen.py" --selftest
finish
