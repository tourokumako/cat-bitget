#!/bin/bash
# b21 — サブエージェントの3通りが、全部 止まるか（完成の条件 #3・J-3）
#
# ★道は私が考えたものではありません。
#   監査レポート 2026-09-04_impl_lock_fix_cp18_audit_report.md の §3 Q3 の表の
#   型④（3通り）と §3 Q6 の表を、そのまま写しています。
#   監査の実測では 3通りとも rc=0（素通り）でした。
#
# なぜ要るか（監査 cp18 の逐語）
#   「.claude/hooks/*.sh が素通りするということは、
#     require_acceptance_before_impl.sh そのものを1回の Write で空にできるということです。
#     そうすれば、G-1〜G-4 も、承認ゲートも、土台ゲートも、同時に消えます。」
#
# ★本物のファイルは1つも書き換えません。「その入力で hook を呼んだらどうなるか」だけを測ります。
# ★1通りでも抜けたら 0 を返し、抜けた道の名前を最後の行に出します。
source "$(dirname "$0")/lib.sh"

H="$ROOT/.claude/hooks/require_acceptance_before_impl.sh"

NG=0
LEAK=""

# ★2026-09-04（まこさんの決定 10）＝相手を2つにする。
#   require_acceptance_before_impl.sh は、いまの設計書の TARGET に在る
#   ＝承認済みで書いてよいファイルなので、0 が返るのが正しい動き（穴ではない）。
#   approve_impl.sh は TARGET に無いので、2 が返るはず。
#   ★両方の終了コードを 実測: の行に出す。
_sub () {
    IN=$(python3 - "$1" <<'PYEOF'
import json, sys
print(json.dumps({"tool_input": {"file_path": sys.argv[1], "content": "x"},
                  "agent_type": "general-purpose"}))
PYEOF
)
    printf '%s' "$IN" | bash "$H" >/dev/null 2>&1
    return $?
}

_sub "$ROOT/.claude/hooks/require_acceptance_before_impl.sh"
RC_TGT=$?
_sub "$ROOT/.claude/hooks/approve_impl.sh"
RC_OUT=$?
[ "$RC_OUT" -ne 2 ] && { NG=1; LEAK="$LEAK サブエージェントの Write（TARGET に無い hook）"; }

PATHS=(
    "$ROOT/.claude/tools/run_breaks.py"
    "$SDK/scripts/priority_rebuild/e38_priority_stack.py"
)
PN=(
    "サブエージェントの Write（道具）"
    "サブエージェントの Write（戦略の .py）"
)

i=0
for p in "${PATHS[@]}"; do
    _sub "$p"
    [ "$?" -ne 2 ] && { NG=1; LEAK="$LEAK ${PN[$i]}"; }
    i=$((i + 1))
done

echo "実測: サブエージェントのWrite TARGETに在るhook=$RC_TGT ／ TARGETに無いhook=$RC_OUT"

if [ "$NG" -eq 0 ]; then
    MEASURED=1
else
    MEASURED=0
    echo "抜けた道:$LEAK"
fi
finish
