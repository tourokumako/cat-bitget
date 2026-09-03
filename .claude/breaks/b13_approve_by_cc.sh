#!/bin/bash
# b13 — CC の Bash から承認スクリプトを打てないか（完成の条件 #11・E-3）
source "$(dirname "$0")/lib.sh"

H="$ROOT/.claude/hooks/require_acceptance_before_impl.sh"

NG=0
for c in "bash $ROOT/.claude/hooks/approve_impl.sh" \
         "bash $ROOT/.claude/hooks/approve_design.sh $ROOT/.claude/state/acceptance.md" \
         "cd $ROOT && bash .claude/hooks/approve_impl.sh"; do
    IN=$(python3 - "$c" <<'PYEOF'
import json, sys
print(json.dumps({"tool_input": {"command": sys.argv[1]}}))
PYEOF
)
    printf '%s' "$IN" | bash "$H" >/dev/null 2>&1
    [ "$?" -ne 2 ] && NG=1
done

if [ "$NG" -eq 0 ]; then MEASURED=1; else MEASURED=0; fi
finish
