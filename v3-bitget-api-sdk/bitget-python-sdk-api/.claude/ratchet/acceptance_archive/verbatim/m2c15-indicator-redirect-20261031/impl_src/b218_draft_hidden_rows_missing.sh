#!/bin/bash
# EXPECT_RC: 1
# MEANS: 写すプログラムの、隠れた数字を軸へ写す所から rows を外す＝見本の帯VA の軸に rows が写らず、写すプログラムの自己テストが落ちる
# EXPECT_MSG: ❌ 写す: 帯VA の va_pct と rows が部品の軸に写る（CP91 の修正1〜3）
# b218_draft_hidden_rows_missing — 隠れた数字が軸へ写らないと、自己テストが落ちる（工事 m2c15-indicator-redirect-20261031・やることの表 7-6 の F-3）
#   守っているもの＝7-6 の F-3（測るコマンドは、完成の条件と同じ＝写すプログラムの --selftest）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$ROOT/.claude/state/indicator_review/gen_indicators_draft.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    hidden = list(hidden)                                                         # ★隠れた数字を軸へ（F-3）'
new = '    hidden = [h for h in hidden if h["引数"] != "rows"]                             # ★隠れた数字を軸へ（F-3）'
if s.count(old) != 1:
    raise SystemExit("[b218_draft_hidden_rows_missing] 壊す対象（隠れた数字を軸へ写す行）が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$F" --selftest
finish
