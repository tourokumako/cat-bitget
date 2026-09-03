#!/bin/bash
# b09 — py_compile の語を引数の後ろに足しても、上流ゲートが外れないか（完成の条件 #8・E-5）
source "$(dirname "$0")/lib.sh"

H="$ROOT/.claude/hooks/require_design_contract_before_run.sh"
IN='{"tool_input":{"command":"python3 '"$PR"'/engine_tuner.py --purpose py_compile"}}'

printf '%s' "$IN" | bash "$H" >/dev/null 2>&1
RC=$?
# 止まった（rc=2）なら「壊し方が効いた」＝0 以外を返す
if [ "$RC" -eq 2 ]; then MEASURED=1; else MEASURED=0; fi
finish
