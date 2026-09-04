#!/bin/bash
# b20 — パスの書き方を変える8通りが、全部 止まるか（完成の条件 #2・J-2）
#
# ★道は私が考えたものではありません。
#   監査レポート 2026-09-04_impl_lock_fix_cp18_audit_report.md の §3 Q3 の表の
#   型②（3通り）・型③（2通り）・型⑤（3通り）を、そのまま写しています。
#   監査の実測では 8通りとも rc=0（素通り）でした。
#
# なぜ要るか（監査 cp18 の逐語）
#   「GATE_RE は .claude/hooks/ で始まって .sh で終わる形を探すので、
#     書き込み先が同じファイルでも、書き方を変えると当たりません。
#     cd した後の相対名にはこの文字列が現れません。スラッシュを2つにしても、
#     引用符を挟んでも同じです（bash は同じファイルに解決します）。」
#
# ★本物のファイルは1つも書き換えません。「その入力で hook を呼んだらどうなるか」だけを測ります。
# ★1通りでも抜けたら 0 を返し、抜けた道の名前を最後の行に出します。
source "$(dirname "$0")/lib.sh"

H="$ROOT/.claude/hooks/require_acceptance_before_impl.sh"

NG=0
LEAK=""

# ── 型②＝cd してから相対名で書く（3通り） ──
# ── 型③＝パスの書き換え（2通り） ──
CMDS=(
    "cd $ROOT/.claude/hooks && echo x > require_acceptance_before_impl.sh"
    "cd $ROOT/.claude/tools && echo x > run_breaks.py"
    "cd $ROOT/.claude/breaks && echo x > b01_missing_func.sh"
    "echo x > $ROOT/.claude//hooks/require_acceptance_before_impl.sh"
    "echo x > $ROOT/.claude/hooks/require_acceptance''_before_impl.sh"
)
CN=(
    "cd してから hook へ"
    "cd してから道具へ"
    "cd してから壊すプログラムへ"
    "スラッシュを2つにする"
    "空の引用符を挟む"
)

i=0
for c in "${CMDS[@]}"; do
    IN=$(python3 - "$c" <<'PYEOF'
import json, sys
print(json.dumps({"tool_input": {"command": sys.argv[1]}}))
PYEOF
)
    printf '%s' "$IN" | bash "$H" >/dev/null 2>&1
    [ "$?" -ne 2 ] && { NG=1; LEAK="$LEAK ${CN[$i]}"; }
    i=$((i + 1))
done

# ── 型⑤＝相対パスの Write（3通り・先頭に / を付けない） ──
PATHS=(
    ".claude/hooks/require_acceptance_before_impl.sh"
    ".claude/tools/run_breaks.py"
    ".claude/breaks/b01_missing_func.sh"
)
PN=(
    "相対パスの Write（hook）"
    "相対パスの Write（道具）"
    "相対パスの Write（壊すプログラム）"
)

i=0
for p in "${PATHS[@]}"; do
    IN=$(python3 - "$p" <<'PYEOF'
import json, sys
print(json.dumps({"tool_input": {"file_path": sys.argv[1], "content": "x"}}))
PYEOF
)
    printf '%s' "$IN" | bash "$H" >/dev/null 2>&1
    [ "$?" -ne 2 ] && { NG=1; LEAK="$LEAK ${PN[$i]}"; }
    i=$((i + 1))
done

if [ "$NG" -eq 0 ]; then
    MEASURED=1
else
    MEASURED=0
    echo "抜けた道:$LEAK"
fi
finish
