#!/bin/bash
# show_design_check_after_write.sh — 設計書が書き換わった直後に、承認のプログラムの止まり所を先に全部 調べて出す（PostToolUse Bash）
#
# まこさん指示（2026-09-19・逐語）＝「これは何回も確認を走らせないように以下の方法で、
#   回数を1回で直せるように強制してほしい」。
#
# なぜ要るか＝2026-09-19（114回目）に、承認が3回 続けて止まり、まこさんに無駄に打たせた。
#   ★書いた直後に全部 出せば、CC は1回で直せる。それがこの hook。
#
# 何をするか（★2026-10-15・181回目に作り直した＝まこさん「応急処置ではなく根本解決」）＝
#   標準入力（hook の json）を、そのまま検査の本体 require_design_check_before_approval.py --post-tool に渡す。
#   本体は、このコマンドで設計書（acceptance.md と、コマンドの --out の後ろの置き場）が本当に書き換わったときだけ調べ、
#   不足が在っても0件でも 2 で終わる。書き換わっていなければ 0（何も出さない）。
#   この .sh は、本体の終了コードで出し方を分けるだけ（判定は全部 本体に在る）。
#   直す前＝コマンドの文字に「gen_acceptance.py」と「--write」が在るかだけで動き（作っていないのに64回）、
#     --out の設計書を調べず、不足0件と検査が落ちたときは何も出さなかった（worklog 20261015 §9）。
#
# 終了コード＝0 何も出さない ／ 2 私の画面に出す（PostToolUse の 2 は、走り終わった道具を取り消さない）。
#   本体が 0 と 2 以外で終わった（落ちた）ときと、本体が無いときも 2 で、そう出す＝黙って終わらない。
#   HOOK_CHECK_PY＝試すときだけ、本体の置き場を差し替える口（本体が無いときの試しに使う）。
#
# 限界（正直に）:
#   ・設計書の中身が正しいかは見ない（承認のプログラムが止まる所だけ）。中身は まこさんの目と監査。
#   ・上限 120秒（settings.json）で打ち切られたときは何も出ない（これまでの最長は 37.4秒）。
#   ・この hook 自身を書き換えれば無効にできる（差分は git に出る）。

set -u
ROOT="/Users/tachiharamasako/Documents/GitHub/cat-bitget"
PY="${HOOK_CHECK_PY:-${ROOT}/.claude/hooks/require_design_check_before_approval.py}"
TAG="[設計書を書いた直後の検査・show_design_check_after_write.sh]"

if [ ! -f "${PY}" ]; then
  echo "🔴 ${TAG} 検査の本体が見つかりません: ${PY}" >&2
  echo "   ＝設計書が書き換わったかも、不足も調べられていません。" >&2
  exit 2
fi

ERR="$(mktemp)"
python3 "${PY}" --post-tool 2>"${ERR}"
RC=$?
case "${RC}" in
  0) rm -f "${ERR}"; exit 0 ;;
  2) cat "${ERR}" >&2; rm -f "${ERR}"; exit 2 ;;
  *) echo "🔴 ${TAG} 検査の本体が落ちました（終了コード ${RC}）。不足は調べられていません:" >&2
     tail -n 15 "${ERR}" >&2
     rm -f "${ERR}"
     exit 2 ;;
esac
