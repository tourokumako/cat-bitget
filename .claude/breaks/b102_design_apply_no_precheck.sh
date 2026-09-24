#!/bin/bash
# EXPECT_RC: 1
# MEANS: 当てる直前の確かめを外して確かめながら当てる形にすると、当てる道具の自己テスト T7（半分だけ当てない）が落ちた
# EXPECT_MSG: ❌ 実物と合わない件
# b102 — 全件を先に確かめる処理（当てた後の中身での確かめ）を外すと、当てる道具の自己テストが落ちるか
#   守っているもの＝完成の条件 #4（設計書 impl-instruction-apply-20260924・まこさん承認 2026-09-24）
#     ＝実物と合わない件が1件でも在れば、1件も当てない（半分だけ当たった状態を作らない）
#   壊し方＝main の `if not _recheck(f, cur):` を常に偽にする（確かめずに当てる）。
#   期待＝自己テスト（`--selftest`）の T7 が落ちる（終了コード 1・出力に「❌ 実物と合わない件」）。
#   ★壊す対象が見つからなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

T="$ROOT/.claude/tools/apply_audit_fix.py"
guard "$T"

python3 - "$T" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '        if not _recheck(f, cur):\n'
if old not in s:
    raise SystemExit("[b102] 壊す対象の行が見つからない（当てる直前の確かめ）")
new = '        if False:  # b102 が壊した（確かめずに当てる）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$T" --selftest
finish
