#!/bin/bash
# b23 — 空の凍結（理由なし）で、承認の瞬間の契約の取り出しが止まるか（完成の条件 #1・#2・監査 cp20 の C1）
#   ①impl_functions が {} で理由なしの設計書 → --freeze-contract が 3 で止まる
#   ②同じ設計書に no_impl_functions_reason を足す → 0 で通る（cp19 の形）
#   両方 成り立つときだけ 1（止まった）。本物のファイルは1つも触らない（一時の場所に作る）。
#   ★測るのは「承認スクリプトと同じ関数（contract_for_freeze）を同じ口で呼んだときの終了コード」
#     ＝承認スクリプトそのものは CC の Bash から打てない（b13）。設計書 §9 の L。
source "$(dirname "$0")/lib.sh"

TMPD="$(mktemp -d)"
F3='```'
printf 'DESIGN_CONTRACT\n\n%sjson\n{"impl_file": "a.py", "impl_functions": {}}\n%s\n' "$F3" "$F3" > "$TMPD/x1.md"
printf 'DESIGN_CONTRACT\n\n%sjson\n{"impl_file": "a.py", "impl_functions": {}, "no_impl_functions_reason": "設計の段階では書けない"}\n%s\n' "$F3" "$F3" > "$TMPD/x2.md"

python3 "$VERIFY" --freeze-contract "$TMPD/x1.md" >/dev/null 2>"$TMPD/e1.txt"
RC1=$?
python3 "$VERIFY" --freeze-contract "$TMPD/x2.md" >/dev/null 2>&1
RC2=$?
echo "①空で理由なし rc=$RC1 $(tail -1 "$TMPD/e1.txt")"
echo "②理由あり rc=$RC2"
rm -rf "$TMPD"

if [ "$RC1" -eq 3 ] && [ "$RC2" -eq 0 ]; then MEASURED=1; else MEASURED=0; fi
finish
