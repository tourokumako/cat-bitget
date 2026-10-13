#!/bin/bash
# EXPECT_RC: 1
# MEANS: 宣言に要件定義の文書が無ければ止まる検査を壊すと、読むもの宣言の hook の自己テストが落ちる
# EXPECT_MSG: ❌ T9
# b185 — 要件定義の文書の検査を、いつも通す形にすると、読むもの宣言の hook（require_read_plan_before_design.py）の自己テストが落ちるか
#   守っているもの＝宣言に要件定義の文書が無ければ止まる検査（設計書 design-origin-form-20261013）
#   壊し方＝要件定義の文書の検査を、いつも通す形にする。
#   期待＝自己テスト（`--selftest`）が落ちる（終了コード 1・出力に「❌ T9」）。
#   ★壊す対象が見つからなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

T="$ROOT/.claude/hooks/require_read_plan_before_design.py"
guard "$T"

python3 - "$T" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    if rows and not any(r.endswith(os.path.basename(CORE_PATH[0])) for r in rows):\n'
if s.count(old) != 1:
    raise SystemExit("[b185] 壊す対象の行が、ちょうど1か所ではない")
new = '    if False and rows and not any(r.endswith(os.path.basename(CORE_PATH[0])) for r in rows):  # b185 が壊した\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$T" --selftest
finish
