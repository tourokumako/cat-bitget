#!/bin/bash
# EXPECT_RC: 1
# MEANS: 組む関数に乱数を1行 書き込むと、数え上げの結果が 0 でなくなった（AUDIT-3 が効いている）
# EXPECT_MSG: b78: 数え上げの結果
# b78 — 組む関数に乱数を1行 書き込むと、数え上げが 0 でなくなるか
#   守っているもの＝完成の条件 AUDIT-3（組む関数に法則番号の直書きが0件・乱数が0件）
#   壊し方＝`sample_regime_build` の中に `rng` を使う行を1行 足す。
#   期待＝数え上げのコマンドが 0 以外を出す（＝乱数が見つかった）。
#     ★このプログラムだけは「自己テスト」ではなく、設計書の AUDIT-3 のコマンドそのものを測る。
#   ★壊す対象が見つからなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

GEN="$PR/engine_tuner_gen.py"
guard "$GEN"

python3 - "$GEN" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    spec_c = stage_candidates(stage)'
if old not in s:
    raise SystemExit("[b78] 壊す対象の行が見つからない: " + old)
new = old + '\n    _b78 = rng  # b78 が壊した（乱数を1つ 書き込んだ）'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

# 測る＝AUDIT-3 の数え上げ（説明文を外して数える）。0 以外なら壊れたことを検出できた。
N=$(awk '/^def _ranked_material_at/,/^def default_regime/' "$GEN" \
     | awk '/"""/{n++} n%2==0' | sed 's/#.*$//' | grep -cE 'rng|draw_param')
if [ "$N" = "0" ]; then
    MEASURED=0      # 壊したのに見つからない＝守りが効いていない
else
    MEASURED=1      # 見つかった＝守りが効いている
    echo "b78: 数え上げの結果 $N 件（0 でない＝乱数が見つかった）"
fi
finish
