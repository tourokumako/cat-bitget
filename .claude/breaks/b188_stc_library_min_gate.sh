#!/bin/bash
# EXPECT_RC: 1
# MEANS: STC を「窓の最小値 > 0 のときだけ計算する」形（ライブラリ pandas_ta_classic momentum/stc.py:180 の1段目の誤り。壊す行は2段とも通る関数 stage の中なので、2段目にも掛かる）に変えると、±1 を交互に繰り返す足の既知答え（STC は 0 より大きい）で検査3 が落ちる＝監査 CP60 が見つけた STC の式の誤りを捕まえる
# EXPECT_MSG: STC: 手計算の既知答えと不一致
# b188_stc_library_min_gate — STC をライブラリの誤り（最小値 > 0 のときだけ計算）に戻すと、交互の足の既知答えで検査3 が落ちる（監査 CP82 の修正3・2026-10-20）
#   守っているもの＝軽い口（selftest_match＝検査3 と写しの印の番人）（observe_diag.py --selftest-match）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える。
#   期待＝observe_diag.py --selftest-match が「STC: 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '            st[i] = 100.0 * (x[i] - lo[i]) / rng[i] if rng[i] > 0 else st[i - 1]\n'
new = '            st[i] = 100.0 * (x[i] - lo[i]) / rng[i] if lo[i] > 0 else st[i - 1]\n'
if s.count(old) != 1:
    raise SystemExit("[b188_stc_library_min_gate] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-match
finish
