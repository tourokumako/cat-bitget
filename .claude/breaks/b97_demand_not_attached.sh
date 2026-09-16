#!/bin/bash
# EXPECT_RC: 1
# MEANS: 需給の列を足す行を消すと、固定のレシピの束が「測れない」になり R9 の診断が rc=1 を返した
# EXPECT_MSG: 時間足が無い: taker_ls
# b97 — R9 の診断が需給の列を足さない形にすると、測れなくなるか
#   守っているもの＝完成の条件 AUDIT-5（R9 の診断が、入口に需給の材料を持つ固定のレシピでも束を測る）
#   なぜ要るか（監査 cp36 の M-4）＝直す前は、解決表を作る前に需給の列を足していなかった
#     （本走は足している）。入口に需給が入る束では全部「測れない」になり、しかも終了コードは
#     0 のままだった＝機械には成功に見えた。
#   壊し方＝`measure` の中の「需給の列を足す」行を消す。
#   期待＝固定のレシピの束が「測れない: [実行器] 材料の名前に時間足が無い: taker_ls」になり、
#     R9 の診断が終了コード 1 を返す。
#   ★測る相手は 種と乱数に依らない固定のレシピ（recipes/r9_demand_fixture.json）。
#   ★壊す対象が1つに定まらなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

DIAG="$PR/regime_r9_diag.py"
guard "$DIAG"

python3 - "$DIAG" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '            df = ex.attach_demand_columns(df, sorted(_dem))\n'
if s.count(old) != 1:
    raise SystemExit(f"[b97] 壊す対象の行が1つに定まらない（{s.count(old)} 件）")
new = '            pass  # b97 が壊した（需給の列を足さない）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/regime_r9_diag.py" --recipe "$PR/recipes/r9_demand_fixture.json" --no-trades
finish
