#!/bin/bash
# EXPECT_RC: 1
# MEANS: やることの番号と結ぶ要件を、やることリストから写す所（行に結ぶ要件が無ければ止まる）を壊すと、読むもの宣言の hook の自己テストが落ちる
# EXPECT_MSG: ❌ T13
# b184 — todo_link を、何も見ずに通す形にすると、読むもの宣言の hook（require_read_plan_before_design.py）の自己テストが落ちるか
#   守っているもの＝やることの番号と結ぶ要件を、やることリストから写す所（行に結ぶ要件が無ければ止まる）（設計書 design-origin-form-20261013）
#   壊し方＝todo_link を、何も見ずに通す形にする。
#   期待＝自己テスト（`--selftest`）が落ちる（終了コード 1・出力に「❌ T13」）。
#   ★壊す対象が見つからなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

T="$ROOT/.claude/hooks/require_read_plan_before_design.py"
guard "$T"

python3 - "$T" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = 'def todo_link(src):\n'
if s.count(old) != 1:
    raise SystemExit("[b184] 壊す対象の行が、ちょうど1か所ではない")
new = 'def todo_link(src):\n    return "なし", "見ない", []  # b184 が壊した（やることリストを見ない）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$T" --selftest
finish
