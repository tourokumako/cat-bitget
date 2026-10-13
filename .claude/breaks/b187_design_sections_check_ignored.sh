#!/bin/bash
# EXPECT_RC: 1
# MEANS: 設計書を作るたびに、項目の抜けを見張る検算を走らせ、通らなければ書かない所を壊すと、設計書を作るプログラムの自己テストが落ちる
# EXPECT_MSG: 項目の抜けを見張る検算が落ちても、設計書を書いた
# b187 — 検算の結果を、見ない形にすると、設計書を作るプログラム（gen_acceptance.py）の自己テストが落ちるか
#   守っているもの＝設計書を作るたびに、項目の抜けを見張る検算を走らせ、通らなければ書かない所（設計書 design-doc-gen-form-20261013）
#   壊し方＝検算の結果を、見ない形にする。
#   期待＝自己テスト（`--selftest`）が落ちる（終了コード 1・出力に「項目の抜けを見張る検算が落ちても、設計書を書いた」）。
#   ★壊す対象が見つからなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

T="$ROOT/.claude/tools/gen_acceptance.py"
guard "$T"

python3 - "$T" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    _rc, _out = _sections_rc()\n    if _rc:\n'
if s.count(old) != 1:
    raise SystemExit("[b187] 壊す対象の行が、ちょうど1か所ではない")
new = '    _rc, _out = _sections_rc()\n    if False and _rc:  # b187 が壊した\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$T" --selftest
finish
