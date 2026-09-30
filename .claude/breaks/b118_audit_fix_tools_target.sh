#!/bin/bash
# EXPECT_RC: 1
# MEANS: 道具のファイルに当ててよいかの照らし（承認の印と TARGET）を常に真にすると、当てる道具の自己テスト T18・T19（印が違う・TARGET の外なら当てない）が落ちた
# EXPECT_MSG: ❌ 道具のファイル
# b118 — 道具のファイルに当てる前の照らしを外すと、当てる道具の自己テストが落ちるか
#   守っているもの＝完成の条件 #1（設計書 audit-fix-tools-target-20260930・まこさん承認 2026-09-30）
#     ＝承認の印と設計書のハッシュ値が合い、TARGET か NEW_FILE に在る道具のファイルにだけ当てる
#   壊し方＝tool_target_ok の最初で、いつも真を返す。
#   期待＝自己テスト（`--selftest`）の T18・T19 が落ちる（終了コード 1・出力に「❌ 道具のファイル」）。
#   ★壊す対象が見つからなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

T="$ROOT/.claude/tools/apply_audit_fix.py"
guard "$T"

python3 - "$T" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = 'def tool_target_ok(rel: str, design_path: str = None, mark_path: str = None) -> bool:\n'
if old not in s:
    raise SystemExit("[b118] 壊す対象の行が見つからない（道具のファイルに当ててよいかの照らし）")
new = old + '    return True  # b118 が壊した（印と TARGET を見ない）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$T" --selftest
finish
