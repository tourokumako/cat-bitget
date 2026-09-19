#!/bin/bash
# show_design_check_after_write.sh — 設計書を作り直した直後に、承認の門の検査を走らせて不足を出す（PostToolUse Bash）
#
# まこさん指示（2026-09-19・逐語）＝「これは何回も確認を走らせないように以下の方法で、
#   回数を1回で直せるように強制してほしい」。
#
# なぜ要るか＝2026-09-19（114回目）に、承認が3回 続けて止まり、まこさんに無駄に打たせた。
#   止まった理由は5つとも pre_audit_check.py --check-design で先に出たもの。
#   ★承認の直前に止める形（require_design_check_before_approval.sh）だけでは、
#     CC が「止められて直す」を繰り返す＝回数は減らない（まこさんの指摘）。
#   ★書いた直後に全部 出せば、CC は1回で直せる。それがこの hook。
#
# 何をするか＝Bash で `gen_acceptance.py` を `--write` で走らせた直後に、
#   その場で pre_audit_check.py --check-design を走らせ、結果を画面に出す。
#   ★止めない（exit 0）＝書く作業は続けられる。出すだけ。
#
# 限界（正直に）:
#   ・設計書の中身が正しいかは見ない（門の形だけ）。中身は まこさんの目と監査。
#   ・別の道（道具を直接 import する等）で設計書を作れば当たらない。
#   ・この hook 自身を書き換えれば無効にできる（差分は git に出る）。

set -u
ROOT="/Users/tachiharamasako/Documents/GitHub/cat-bitget"
ACC="$ROOT/.claude/state/acceptance.md"
CHK="$ROOT/.claude/tools/pre_audit_check.py"

RAW="$(cat)"
CMD="$(printf '%s' "$RAW" | python3 -c 'import json,sys
try:
    d = json.load(sys.stdin)
except Exception:
    print(""); raise SystemExit
print(((d.get("tool_input") or {}).get("command") or ""))' 2>/dev/null)"

case "$CMD" in
  *gen_acceptance.py*--write*) : ;;
  *) exit 0 ;;
esac
[ -f "$ACC" ] && [ -f "$CHK" ] || exit 0

OUT="$(python3 "$CHK" --check-design "$ACC" 2>&1)"
if printf '%s' "$OUT" | grep -q "設計書の中身は通ります（不足0件）"; then
  echo "✅ [承認の門の検査] 設計書の中身は通ります（不足0件）＝このまま承認をお願いできます。"
  exit 0
fi
{
  echo "📋 [承認の門の検査] 設計書を作り直したので、承認のプログラムと同じ検査を走らせました。"
  echo "   ★不足が在ります。**1回で全部 直してください**（止められてから1件ずつ直すのをやめる・まこさん 2026-09-19）:"
  printf '%s\n' "$OUT" | sed 's/^/   /'
} >&2
exit 0
