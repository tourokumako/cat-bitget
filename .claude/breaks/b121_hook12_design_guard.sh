#!/bin/bash
# EXPECT_RC: 1
# MEANS: hook 12 が承認済みの設計書の TARGET を守る処理を外すと、当てる道具の自己テスト T31 が落ちた
# EXPECT_MSG: hook 12 T31
# b121 — enforce_audit_fix.py の pending の「承認済みの設計書に実装の指示が在れば TARGET を守る」を外すと、自己テストが落ちるか
#   守っているもの＝設計書 point2-design-to-impl-20260930 の W-4（実装 15）
#   なぜ要るか＝W-4 には完成の条件の行も壊すプログラムも無かった（監査 cp53 の Q6）
source "$(dirname "$0")/lib.sh"

HOOK="$ROOT/.claude/hooks/enforce_audit_fix.py"
guard "$HOOK"

python3 - "$HOOK" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
before = '        if a.approved_ok(a.DESIGN)[0] and a.read_design_fixes(dtext):'
if s.count(before) != 1:
    sys.exit("壊す相手の行がちょうど1か所ではない: " + before)
after = '        if False:  # わざと外した（壊すプログラム b121）'
open(p, 'w', encoding='utf-8').write(s.replace(before, after, 1))
PYEOF

measure python3 "$ROOT/.claude/tools/apply_audit_fix.py" --selftest
finish
