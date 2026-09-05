#!/bin/bash
# b24 — design も frozen も {} で理由なしなら、照合が比較の前に NG を出すか（完成の条件 #4・監査 cp20 の C3）
#   一時の場所に、impl_functions が {} で理由なしの控えと、{} の凍結（<名前>.frozen.json）を並べて照合する。
#   照合の出力に「凍結された impl_functions が空です」が在れば 1（止まった）。本物のファイルは1つも触らない。
#   ★直す前＝両方が {} なら文字列が一致して通った（1関数も照合せずに「設計通り」）。
#   ★2026-09-05 の6回目の承認で、この壊すプログラムの stderr に UTF-8 として読めないバイト（0xEF）が混じり、
#     記録の道具（run_breaks.py）が UnicodeDecodeError で落ちた（出どころは未特定）。
#     直し＝①LC_ALL=C ②自分の stderr を全部ファイルに落とし、バイト数と先頭を ASCII（od -c）で stdout に出す
#          ③照合の出力を1バイトも流さない（grep -q だけ）④自分が出す行は ASCII だけ。
export LC_ALL=C
TMPD="$(mktemp -d)"
ERRF="$TMPD/stderr.txt"
exec 2>"$ERRF"
source "$(dirname "$0")/lib.sh"

F3='```'
printf 'DESIGN_CONTRACT\n\n%sjson\n{"impl_file": "scripts/priority_rebuild/verify_design_contract.py", "impl_functions": {}}\n%s\n' "$F3" "$F3" > "$TMPD/x.md"
printf '{}\n' > "$TMPD/x.frozen.json"

python3 "$VERIFY" "$TMPD/x.md" > "$TMPD/out.txt" 2>&1
RC=$?
grep -q "凍結された impl_functions が空です" "$TMPD/out.txt"
HIT=$?
OUTB=$(wc -c < "$TMPD/out.txt" | tr -d ' ')
ERRB=$(wc -c < "$ERRF" | tr -d ' ')
ERRHEAD=$(od -An -c "$ERRF" | head -2 | tr -s ' ' | tr '\n' ' ')
echo "verify rc=$RC hit=$HIT (0=found) out_bytes=$OUTB stderr_bytes=$ERRB stderr_head=[$ERRHEAD]"
rm -rf "$TMPD"

if [ "$HIT" -eq 0 ] && [ "$RC" -ne 0 ]; then MEASURED=1; else MEASURED=0; fi
finish
