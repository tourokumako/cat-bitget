#!/bin/bash
# b25 — 書き込みの門が、囲みを extract_block（目印の行）で選ぶか（完成の条件 #3・監査 cp20 の C2）
#   設計書（控えを取って必ず戻す）を「impl_file だけの囲みが先・目印の行の DESIGN_CONTRACT が無い」中身に替え、
#   書き込みの門を Write の入力で呼ぶ。門の出力に「DESIGN_CONTRACT（目印の行の後ろの json）が読めません」が在れば 1。
#   ★直す前＝最初の impl_file の囲み（この場合 SPEC の形）を契約と見て、別の文（impl_functions がありません）を出した。
#   ★Write の相手は照合の道具の .py にする（設計書そのものへの Write は、門が契約の検査まで進まずに通すため
#     ＝require_acceptance_before_impl.sh 554-560行の case）。門は契約の検査で設計書（$LIST）を読む。
#   ★2026-09-05 の5回目の承認で、この壊すプログラムの出力に UTF-8 として読めないバイトが混じり、
#     記録の道具（run_breaks.py）が UnicodeDecodeError で落ちた。直し＝①門の出力を1バイトも自分の出力に流さない
#     ②LC_ALL=C で bash 自身の言葉を ASCII にする ③自分が出す行は ASCII だけにする。
export LC_ALL=C
source "$(dirname "$0")/lib.sh"

H="$ROOT/.claude/hooks/require_acceptance_before_impl.sh"
MD="$ROOT/.claude/state/acceptance.md"
TGT="$SDK/scripts/priority_rebuild/verify_design_contract.py"
guard "$MD"

F3='```'
{
  printf '# b25 temporary design (restored by guard)\n\n'
  printf 'TARGET: scripts/priority_rebuild/verify_design_contract.py\n\n'
  printf '## spec\n\nSPEC\n\n%sjson\n{"impl_file": "scripts/priority_rebuild/verify_design_contract.py", "public_functions": {}}\n%s\n\n' "$F3" "$F3"
  printf '## contract (no marker line)\n\n%sjson\n{"impl_file": "scripts/priority_rebuild/verify_design_contract.py", "impl_functions": {"scripts/priority_rebuild/verify_design_contract.py": ["check"]}}\n%s\n' "$F3" "$F3"
} > "$MD"

IN=$(python3 - "$TGT" <<'PYEOF'
import json, sys
print(json.dumps({"tool_input": {"file_path": sys.argv[1], "content": "x"}}))
PYEOF
)
TMPO="$(mktemp)"
printf '%s' "$IN" | bash "$H" >"$TMPO" 2>&1
RC=$?
grep -q "目印の行の後ろの json）が読めません" "$TMPO"
HIT=$?
BYTES=$(wc -c < "$TMPO" | tr -d ' ')
rm -f "$TMPO"
echo "gate rc=$RC hit=$HIT (0=found) bytes=$BYTES"

if [ "$HIT" -eq 0 ] && [ "$RC" -ne 0 ]; then MEASURED=1; else MEASURED=0; fi
finish
