#!/bin/bash
# EXPECT_RC: 1
# MEANS: 承認の印を照らす処理を常に真にすると、当てる道具の自己テスト T4（印が違えば当てない）が落ちた
# EXPECT_MSG: ❌ 承認の印
# b101 — 承認の印と設計書のハッシュ値の照らしを外すと、当てる道具の自己テストが落ちるか
#   守っているもの＝完成の条件 #3（設計書 impl-instruction-apply-20260924・まこさん承認 2026-09-24）
#     ＝承認の印と設計書のハッシュ値が合わないときは、1件も当てない
#   壊し方＝main の `ok, why = approved_ok(a.design, approved_path)` を常に真にする。
#   期待＝自己テスト（`--selftest`）の T4 が落ちる（終了コード 1・出力に「❌ 承認の印」）。
#   ★壊す対象が見つからなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

T="$ROOT/.claude/tools/apply_audit_fix.py"
guard "$T"

python3 - "$T" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '        ok, why = approved_ok(a.design, approved_path)\n'
if old not in s:
    raise SystemExit("[b101] 壊す対象の行が見つからない（承認の印の照らし）")
new = '        ok, why = True, ""  # b101 が壊した（印を見ない）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$T" --selftest
finish
