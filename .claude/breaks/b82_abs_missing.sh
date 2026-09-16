#!/bin/bash
# EXPECT_RC: 1
# MEANS: 1本目が材料に abs を付ける行を消すと、T40④ が「向きを持つ指標に前処理が付いていない」で落ちた
# EXPECT_MSG: ❌ T40④
# b82 — 1本目が材料に符号を取り去る前処理を付けなくすると、検査が落ちるか
#   守っているもの＝完成の条件 AUDIT-6（実際の束の向きを持つ指標に abs が付いている）
#   なぜ要るか＝まこさん指示 2026-09-10「この件、毎回忘れて、設計に入れないし、やろうとしないから、
#     絶対入れろ」。符号を取り去らないと、強い下げまで「トレンドが弱い」と数える。
#   ★2026-09-16（監査 cp36 の M-6）＝壊し方を替えた。直す前＝実行器の前処理の一覧から `abs` の
#     登録を消していた。それでは元データの読み込みが止まり、T36①・T24②・T40・T39①③・T24⑥・
#     T38②・T26・T30 が一度に落ちた（監査 cp36 の §1-1 の3番）＝abs の守りだけを試す形ではなかった。
#     いまは、候補を作る所で前処理を付ける2行だけを消す。
#   壊し方＝`build_stage_candidates` の中で、元データの `pre` の欄から前処理を付ける2行を消す。
#   期待＝自己テスト T40④ が落ちる（終了コード 1）。元データの読み込みは最後まで進む。
#   ★壊す対象が1つに定まらなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

GEN="$PR/engine_tuner_gen.py"
guard "$GEN"

python3 - "$GEN" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '            if _op:\n                m = {**m, "pre": {"op": _op}}\n'
if s.count(old) != 1:
    raise SystemExit(f"[b82] 壊す対象の行が1つに定まらない（{s.count(old)} 件）")
new = '            pass  # b82 が壊した（前処理を付けない）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/engine_tuner_gen.py" --selftest
finish
