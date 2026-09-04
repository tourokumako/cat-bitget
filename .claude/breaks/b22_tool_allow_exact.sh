#!/bin/bash
# b22 — 道具の例外が、名前を完全一致させた2本だけかを測る（完成の条件 #5・#6）
#
# ★道は私が考えたものではありません。まこさんの決定の文（2026-09-04・逐語）を、そのまま写しています。
#   「list_banned_words.py と gen_impl_functions.py の2本を名前で完全一致させたときだけ通す。」
#   「run_breaks.py は入れない。記録を直接 書ける道具だから。」
#   「リダイレクトの判定は、この例外でも外さない。」
#   「完成条件を1行 足す——『python3 .claude/tools/run_breaks.py --out <記録> が rc=2 で止まる』。」
#
# なぜ要るか
#   この例外は、監査が求めたものではなく、G-4（既定 deny）が作った行き止まりの後始末で、
#   ★穴を1つ開ける向きの変更（設計書 §9.1）。だから「2本だけ」を機械で見張る。
#
# ★本物のファイルは1つも書き換えません。「その入力で hook を呼んだらどうなるか」だけを測ります。
# ★1通りでも抜けたら 0 を返し、抜けた道の名前を最後の行に出します。
source "$(dirname "$0")/lib.sh"

H="$ROOT/.claude/hooks/require_acceptance_before_impl.sh"
B="$SDK/.claude/ratchet/acceptance_archive/impl-lock-fix-cp19-20260904.breaks.json"

NG=0
LEAK=""

_ask () {
    IN=$(python3 - "$1" <<'PYEOF'
import json, sys
print(json.dumps({"tool_input": {"command": sys.argv[1]}}))
PYEOF
)
    printf '%s' "$IN" | bash "$H" >/dev/null 2>&1
    return $?
}

# ── 完成の条件 #5＝記録を直接 書ける道具は、例外に入っていない（止まるはず） ──
_ask "python3 $ROOT/.claude/tools/run_breaks.py --out $B"
[ "$?" -ne 2 ] && { NG=1; LEAK="$LEAK 記録を書ける道具が通った"; }

# ── 完成の条件 #6 の前半＝通す2本は、いままでどおり通るはず ──
_ask "python3 $ROOT/.claude/tools/list_banned_words.py acceptance"
[ "$?" -ne 0 ] && { NG=1; LEAK="$LEAK 例外の1本目が通らない"; }

_ask "python3 $ROOT/.claude/tools/gen_impl_functions.py $ROOT/.claude/tools/run_breaks.py"
[ "$?" -ne 0 ] && { NG=1; LEAK="$LEAK 例外の2本目が通らない"; }

# ── 完成の条件 #6 の後半＝リダイレクトを付ければ、例外でも止まるはず ──
_ask "python3 $ROOT/.claude/tools/list_banned_words.py acceptance > $B"
[ "$?" -ne 2 ] && { NG=1; LEAK="$LEAK リダイレクトが通った"; }

if [ "$NG" -eq 0 ]; then
    MEASURED=1
else
    MEASURED=0
    echo "抜けた道:$LEAK"
fi
finish
