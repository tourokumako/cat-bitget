#!/bin/bash
# b08 — Bash から土台6ファイルを書く6通りが、全部 止まるか（完成の条件 #7・E-1）
#   ★本物のファイルは1つも書き換えません。「その入力で hook を呼んだらどうなるか」だけを測ります。
source "$(dirname "$0")/lib.sh"

H="$ROOT/.claude/hooks/require_acceptance_before_impl.sh"
F="$SDK/.claude/ratchet/spec_lists.json"

# 6通り＝echo リダイレクト／cp／sed -i／tee／変数に入れる／ヒアドキュメント
CMDS=(
  "echo x > $F"
  "cp /tmp/x.json $F"
  "sed -i '' 's/a/b/' $F"
  "cat /tmp/x.json | tee $F"
  "T=$F; echo x > \$T"
  "python3 - <<'EOF'\nopen('$F','w').write('x')\nEOF"
)

NG=0
for c in "${CMDS[@]}"; do
    IN=$(python3 - "$c" <<'PYEOF'
import json, sys
print(json.dumps({"tool_input": {"command": sys.argv[1].replace("\\n", "\n")}}))
PYEOF
)
    printf '%s' "$IN" | bash "$H" >/dev/null 2>&1
    [ "$?" -ne 2 ] && NG=1
done

# 6通り全部 止まったら「壊し方が効いた」＝終了コード 1 を返す（0 以外が「止まった」の印）
if [ "$NG" -eq 0 ]; then MEASURED=1; else MEASURED=0; fi
finish
