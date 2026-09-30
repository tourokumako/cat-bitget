#!/bin/bash
# EXPECT_RC: 1
# MEANS: 走らせるコマンドの形の照らしを常に通すと、当てる道具の自己テスト T20（決まった形だけ通す）が落ちた
# EXPECT_MSG: ❌ コマンドの形
# b119 — 走らせるコマンドの形の照らしを外すと、当てる道具の自己テストが落ちるか
#   守っているもの＝完成の条件 #2（設計書 audit-fix-tools-target-20260930・まこさん承認 2026-09-30）
#     ＝一覧に無い形のコマンドは走らせない
#   壊し方＝command_argv の最初で、どのコマンドにも (置き場, 引数の並び) を返す。
#   期待＝自己テスト（`--selftest`）の T20 が落ちる（終了コード 1・出力に「❌ コマンドの形」）。
#   ★壊す対象が見つからなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

T="$ROOT/.claude/tools/apply_audit_fix.py"
guard "$T"

python3 - "$T" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = 'def command_argv(cmd: str):\n'
if old not in s:
    raise SystemExit("[b119] 壊す対象の行が見つからない（走らせるコマンドの形の照らし）")
new = old + '    return ROOT, ["python3", "x"]  # b119 が壊した（形を見ない）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$T" --selftest
finish
