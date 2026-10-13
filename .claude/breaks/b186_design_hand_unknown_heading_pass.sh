#!/bin/bash
# EXPECT_RC: 1
# MEANS: やることの表の手書きの項目に、知らない見出しが在れば止める検査を壊すと、設計書を作るプログラムの自己テストが落ちる
# EXPECT_MSG: 知らない見出しが在ると止まるはずが、通った
# b186 — 知らない見出しの検査を、いつも通す形にすると、設計書を作るプログラム（gen_acceptance.py）の自己テストが落ちるか
#   守っているもの＝やることの表の手書きの項目に、知らない見出しが在れば止める検査（設計書 design-doc-gen-form-20261013）
#   壊し方＝知らない見出しの検査を、いつも通す形にする。
#   期待＝自己テスト（`--selftest`）が落ちる（終了コード 1・出力に「知らない見出しが在ると止まるはずが、通った」）。
#   ★壊す対象が見つからなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

T="$ROOT/.claude/tools/gen_acceptance.py"
guard "$T"

python3 - "$T" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    for k in hand:\n        if k not in hand_keys:\n'
if s.count(old) != 1:
    raise SystemExit("[b186] 壊す対象の行が、ちょうど1か所ではない")
new = '    for k in hand:\n        if False and k not in hand_keys:  # b186 が壊した\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$T" --selftest
finish
