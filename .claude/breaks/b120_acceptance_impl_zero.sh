#!/bin/bash
# EXPECT_RC: 1
# MEANS: 直すファイルが在るのに 4-20 が0件の設計書を止める検査を外すと、設計書の道具の自己テストが落ちた
# EXPECT_MSG: 4-20 が0件でも書ける
# b120 — gen_acceptance.py の page の「4-20 が0件なら止める」を外すと、自己テストが落ちるか
#   守っているもの＝設計書 point2-design-to-impl-20260930 の W-5（実装 17）
#   なぜ要るか＝完成の条件4行目の b72 は verify を壊すだけで、この検査を壊していなかった（監査 cp53 の Q6）
#   期待＝壊すと「直すファイルが在るのに 4-20 が0件だと止まる」の場面が fail になり、終了コードが 1 になる
source "$(dirname "$0")/lib.sh"

GEN="$ROOT/.claude/tools/gen_acceptance.py"
guard "$GEN"

python3 - "$GEN" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
before = '    if (d.get("TARGET") or d.get("NEW_FILE")) and not (d.get("実装の指示") or []):'
if s.count(before) != 1:
    sys.exit("壊す相手の行がちょうど1か所ではない: " + before)
after = '    if False:  # わざと外した（壊すプログラム b120）'
open(p, 'w', encoding='utf-8').write(s.replace(before, after, 1))
PYEOF

measure python3 "$GEN" --selftest
finish
