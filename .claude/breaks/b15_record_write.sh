#!/bin/bash
# b15 — 壊し方の記録（証拠ファイル）へ書く6通りが、全部 止まるか（完成の条件 #13・G-1）
#   相手＝acceptance_archive/<iter>.breaks.json と <iter>.frozen.json
#
# なぜ要るか（監査 cp17 の実測）
#   `<iter>.breaks.json` へ Write rc=0・Bash のリダイレクト rc=0。
#   ＝run_breaks.py を1回も走らせずに、終了コードを好きな値で書けた。
#   ＝E-12（壊し方を機械が走らせて記録に残す）の根拠が、根拠にならない。
#
# ★本物のファイルは1つも書き換えません。「その入力で hook を呼んだらどうなるか」だけを測ります。
# ★1通りでも抜けたら 0 を返し、抜けた道の名前を最後の行に出す。
source "$(dirname "$0")/lib.sh"

H="$ROOT/.claude/hooks/require_acceptance_before_impl.sh"
AR="$SDK/.claude/ratchet/acceptance_archive"
B="$AR/impl-lock-fix-cp17-20260903.breaks.json"
Z="$AR/impl-lock-fix-cp17-20260903.frozen.json"

NAMES=("Write（記録）" "Bash のリダイレクト" "cp" "tee" "python3 別の.py" "サブエージェントの Write")

NG=0
LEAK=""

# ①Write ②サブエージェントの Write ＝ file_path で入る形
for pair in "1:$B:" "6:$B:general-purpose"; do
    idx="${pair%%:*}"; rest="${pair#*:}"; path="${rest%%:*}"; agent="${rest#*:}"
    IN=$(python3 - "$path" "$agent" <<'PYEOF'
import json, sys
d = {"tool_input": {"file_path": sys.argv[1], "content": "x"}}
if sys.argv[2]:
    d["agent_type"] = sys.argv[2]
print(json.dumps(d))
PYEOF
)
    printf '%s' "$IN" | bash "$H" >/dev/null 2>&1
    if [ "$?" -ne 2 ]; then
        NG=1
        [ "$idx" = "1" ] && LEAK="$LEAK ${NAMES[0]}" || LEAK="$LEAK ${NAMES[5]}"
    fi
done

# ③〜⑤ ＝ Bash のコマンドで入る形（凍結の控えも1つ 混ぜる）
CMDS=("echo x > $B" "cp /tmp/x.json $B" "cat /tmp/x.json | tee $Z" "python3 /tmp/writer.py $B")
CN=("Bash のリダイレクト" "cp" "tee" "python3 別の.py")
i=0
for c in "${CMDS[@]}"; do
    IN=$(python3 - "$c" <<'PYEOF'
import json, sys
print(json.dumps({"tool_input": {"command": sys.argv[1]}}))
PYEOF
)
    printf '%s' "$IN" | bash "$H" >/dev/null 2>&1
    if [ "$?" -ne 2 ]; then
        NG=1
        LEAK="$LEAK ${CN[$i]}"
    fi
    i=$((i + 1))
done

if [ "$NG" -eq 0 ]; then
    MEASURED=1
else
    MEASURED=0
    echo "抜けた道:$LEAK"
fi
finish
