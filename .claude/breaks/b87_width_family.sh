#!/bin/bash
# EXPECT_RC: 1
# MEANS: 帯の幅の枠が法則 R7 の指標を読む処理を壊すと、T45 が「帯の幅の候補に指標が出ない」で落ちた
# EXPECT_MSG: ❌ T45
# b87 — 帯の幅の候補が、法則が名指しした指標（family）を読まなくなると、検査が落ちるか
#   守っているもの＝完成の条件 #3（帯の幅の候補に BB幅・Donchian幅・HWC幅% が出る）
#   期待＝自己テスト T45 が落ちる（終了コード 1）。
#   ★壊す対象が見つからなければ止まる（黙って壊さない）。
#
# ★2026-09-19 新設（設計書 m2c-width-and-stage-candidates-20260918・まこさん承認）。
#   なぜ＝2026-09-09 に私（CC）が法則 R7 から帯の幅の指標3件を外し、2026-09-18 に まこさんの指摘で
#     戻した（「以前もこの指摘があり修正しているはずだが、また先祖返りしている」）。
#     法則に戻しても、束を組む側が読まなければ届かない＝その道が消えたら落ちる形にする。
source "$(dirname "$0")/lib.sh"

GEN="$PR/engine_tuner_gen.py"
guard "$GEN"

python3 - "$GEN" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = "    for fam in fams_law:                           # ② 法則が名指しした指標（系統から役割を引く）\n"
if s.count(old) != 1:
    raise SystemExit(f"[b87] 壊す対象の行が1つに定まらない（{s.count(old)} 件）")
new = "    for fam in []:                                 # b87 が壊した（法則の指標を読まない）\n"
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/engine_tuner_gen.py" --selftest
finish
