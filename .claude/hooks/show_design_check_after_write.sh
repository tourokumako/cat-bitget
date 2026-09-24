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
#   ★書いた設計書は取り消さない＝書く作業は続けられる。出すだけ。
#     （2026-09-21＝不足が在るときは終了コード 2 にした。0 だと不足の一覧が CC の画面に出ないため。
#       PostToolUse の 2 は、走り終わった道具を取り消さない）
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

# ★2026-09-21（まこさん指示「一回で改善できる状態にしろ」）＝承認のプログラムの止まり所を
#   全部 確かめる本体（require_design_check_before_approval.py）を呼ぶ形にした。
#   直す前は --check-design（止まり所の1つ目）だけを出していた。止めない（出すだけ）のは変えない。
TR="$(printf '%s' "$RAW" | python3 -c 'import json,sys
try:
    print((json.load(sys.stdin).get("transcript_path") or ""))
except Exception:
    print("")' 2>/dev/null)"
if [ -n "$TR" ]; then
  python3 "$ROOT/.claude/hooks/require_design_check_before_approval.py" --after-write --transcript "$TR" >&2
else
  python3 "$ROOT/.claude/hooks/require_design_check_before_approval.py" --after-write >&2
fi
# ★不足が在るときは 2 で終わる＝設計書は もう書き終わっているので取り消されない。
#   2 にするのは、不足の一覧を CC の画面に出すため（0 だと CC には見えない）。
exit $?
