#!/bin/bash
# b12 — 承認の記録が無いときに止まるか（完成の条件 #10・E-9）
#   2つ測る＝①design_approved.json を消す ②控えの凍結を消す
source "$(dirname "$0")/lib.sh"

DA="$ROOT/.claude/state/design_approved.json"
MD="$ROOT/.claude/state/acceptance.md"
guard "$DA"
rm -f "$DA"

python3 "$VERIFY" --check-approval "$MD" >/dev/null 2>&1
RC1=$?

# ②控えの凍結が無い控えを、一時の場所に作って照らす
TMPD="$(mktemp -d)"
cp "$MD" "$TMPD/dummy_iter.md"
python3 "$VERIFY" --diff "$TMPD/dummy_iter.md" >/dev/null 2>&1
RC2=$?
rm -rf "$TMPD"

# 両方 止まったときだけ「効いた」
if [ "$RC1" -ne 0 ] && [ "$RC2" -ne 0 ]; then MEASURED=1; else MEASURED=0; fi
finish
