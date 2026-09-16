#!/bin/bash
# EXPECT_RC: 1
# MEANS: 窓を持たない前処理の枝を消すと、T44 が KeyError 'n' で「鍵を作れない」になり落ちた
# EXPECT_MSG: ❌ T44
# b98 — 分位の解決表の鍵から abs の枝を消すと、検査が落ちるか
#   守っているもの＝完成の条件 AUDIT-1（束に abs が付いていても、分位の解決表の鍵が作れる）
#   なぜ要るか（99回目に見つけた不具合）＝98回目の直しで、実際の束の強さの否定に符号を取り去る
#     前処理（abs）が付くようになった。abs は本数 n を持たない前処理なのに、鍵を作る関数は
#     前処理が在れば必ず n を読んでいた＝束に abs が入った瞬間に KeyError で落ちた。
#     自己テストは束を審査に掛けるまでしか見ていなかったので、気づけなかった。
#   壊し方＝実行器の `_mat_key` から、窓を持たない前処理（NO_ARG_OPS）の枝を消す。
#   期待＝自己テスト T44 が落ちる（終了コード 1）。
#   ★壊す対象が1つに定まらなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

EXE="$PR/engine_tuner_exec.py"
guard "$EXE"

python3 - "$EXE" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = ('    if pre["op"] in NO_ARG_OPS:                    '
       '# ★2026-09-16（M2-E-2 の不具合）＝窓を持たない前処理（abs）は n を持たない\n'
       '        return f"{pre[\'op\']}:{name}"\n')
if s.count(old) != 1:
    raise SystemExit(f"[b98] 壊す対象の行が1つに定まらない（{s.count(old)} 件）")
open(p, 'w', encoding='utf-8').write(s.replace(old, "", 1))
PYEOF

measure python3 "$PR/engine_tuner_gen.py" --selftest
finish
