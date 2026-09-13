#!/bin/bash
# EXPECT_RC: 1
# MEANS: 組む関数に乱数を1行 書いても、法則番号の文字を1つ書いても、数える道具が 0件でないと数えた（AUDIT-3 が効いている）
# EXPECT_MSG: b78: 2回とも見つけた
# b78 — 組む関数に「乱数」と「法則番号の文字」を1つずつ書き込むと、数える道具が見つけるか
#   守っているもの＝完成の条件 #4（AUDIT-3＝組む関数に法則番号の直書きが0件・乱数が0件）
#   測る道具＝.claude/tools/count_builder_literals.py（完成の条件 #4 の条件のコマンドそのもの）
#   壊し方（順に2回）
#     ①候補を作る関数に `_b78 = rng` を1行 足す → 道具が 0 以外を返すか
#     ②元に戻してから、同じ所に `_b78 = "R1"`（法則番号だけの文字）を1行 足す → 道具が 0 以外を返すか
#   期待＝①②の両方で見つけたときだけ rc=1。
#   ★壊す前に道具が 0 を返すことを確かめる（返さなければ測れない＝rc=0 で「期待と違う」になる）。
#     ★2026-09-13（97回目）に書き直した理由＝直す前のこのプログラムは、awk で説明の文を外して数えていたが、
#       1行で閉じる説明の文で内と外の判定が逆になり、**壊す前のコードでも2件**出ていた
#       ＝壊さなくても「見つかった」を出していた（worklog 20260913 §3）。
#   ★壊す対象の行が1つに定まらなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

GEN="$PR/engine_tuner_gen.py"
TOOL="$ROOT/.claude/tools/count_builder_literals.py"
guard "$GEN"

# 0) 壊す前＝道具が 0 を返すこと
python3 "$TOOL" >/dev/null 2>&1
RC0=$?
if [ "$RC0" != "0" ]; then
    # ★変数は ${…} で囲む（2026-09-13＝`$RC2）` の全角の「）」の一部が変数の名前として読まれ、
    #   まこさんの端末で「RC2?: unbound variable」で止まった）
    MEASURED_OUT="b78: 壊す前から数える道具が 0 を返さない（rc=${RC0}）＝測れない"
    MEASURED=0
    finish
fi

_inject () {
    python3 - "$GEN" "$1" <<'PYEOF'
import sys
p, line = sys.argv[1], sys.argv[2]
s = open(p, encoding='utf-8').read()
old = '    spec_c = stage_candidates(stage)\n'
if s.count(old) != 1:
    raise SystemExit(f"[b78] 壊す対象の行が1つに定まらない（{s.count(old)} 件）: {old.strip()}")
open(p, 'w', encoding='utf-8').write(s.replace(old, old + '    ' + line + '  # b78 が壊した\n', 1))
PYEOF
}

# 1) 乱数を1行 書く
_inject '_b78 = rng' || { MEASURED_OUT="b78: 1回目を壊せなかった"; MEASURED=0; finish; }
python3 "$TOOL" >/dev/null 2>&1
RC1=$?
cp -p "$BK_TMP/0.bak" "$GEN"

# 2) 法則番号だけの文字を1つ書く
_inject '_b78 = "R1"' || { MEASURED_OUT="b78: 2回目を壊せなかった"; MEASURED=0; finish; }
python3 "$TOOL" >/dev/null 2>&1
RC2=$?

if [ "$RC1" = "1" ] && [ "$RC2" = "1" ]; then
    MEASURED_OUT="b78: 2回とも見つけた（乱数 rc=${RC1} ／ 法則番号 rc=${RC2}）"
    MEASURED=1
else
    MEASURED_OUT="b78: 見つけられなかった回がある（乱数 rc=${RC1} ／ 法則番号 rc=${RC2}）"
    MEASURED=0
fi
finish
