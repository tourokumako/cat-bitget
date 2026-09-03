#!/bin/bash
# b16 — 壊すプログラムへ書く6通りが、全部 止まるか（完成の条件 #14・G-2）
#   相手＝.claude/breaks/*.sh
#
# なぜ要るか（監査 cp17 の実測）
#   `.claude/breaks/b09_run_bypass.sh` へ Write rc=0・Bash のリダイレクト rc=0。
#   凍結（breaks_frozen.json）は承認の**後**にしか効かないので、
#   承認の**前**に骨抜きにできた。
#
# ★本物のファイルは1つも書き換えません。「その入力で hook を呼んだらどうなるか」だけを測ります。
# ★1通りでも抜けたら 0 を返し、抜けた道の名前を最後の行に出す。
source "$(dirname "$0")/lib.sh"

H="$ROOT/.claude/hooks/require_acceptance_before_impl.sh"
V="$ROOT/.claude/breaks/b09_run_bypass.sh"
L="$ROOT/.claude/breaks/lib.sh"

NG=0
LEAK=""

# ①Write ⑥サブエージェントの Write
for pair in "Write:$V:" "サブエージェントのWrite:$V:general-purpose"; do
    nm="${pair%%:*}"; rest="${pair#*:}"; path="${rest%%:*}"; agent="${rest#*:}"
    IN=$(python3 - "$path" "$agent" <<'PYEOF'
import json, sys
d = {"tool_input": {"file_path": sys.argv[1], "content": "x"}}
if sys.argv[2]:
    d["agent_type"] = sys.argv[2]
print(json.dumps(d))
PYEOF
)
    printf '%s' "$IN" | bash "$H" >/dev/null 2>&1
    [ "$?" -ne 2 ] && { NG=1; LEAK="$LEAK $nm"; }
done

# ②〜⑤ ＝ Bash のコマンドで入る形（共通の部品 lib.sh も1つ 混ぜる）
CMDS=("echo x > $V" "cp /tmp/x.sh $V" "sed -i '' 's/a/b/' $L" "chmod 777 $V; echo x > $V")
CN=("Bash のリダイレクト" "cp" "sed -i" "chmod＋書き込み")
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

if [ "$NG" -eq 0 ]; then
    MEASURED=1
else
    MEASURED=0
    echo "抜けた道:$LEAK"
fi
finish
