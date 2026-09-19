#!/bin/bash
# require_design_check_before_approval.sh — 承認をお願いする前に、設計書の門の検査を通す（Stop hook）
#
# まこさん指摘（2026-09-19・逐語）＝「毎回承認のたびにランダムでやられると迷惑なんだけど。」
#   「確認が面倒で思いつきランダムで進めようとしてる？」「すべて確認するのは面倒だから、
#    ランダム当てずっぽうで当たるまで続けるの？」
#
# なぜ要るか＝2026-09-19（114回目）に、承認が3回 続けて止まり、まこさんに無駄に打たせた。
#   止まった理由5つ（目的の照合が無い／「読んだ」と書いたファイルを開いていない／設計書の中の
#   食い違い3件／禁止語チェック未実行／「実測＝」の行に実行コマンドが無い）は、
#   どれも pre_audit_check.py --check-design を先に走らせれば全部 出た。
#   ＝承認のプログラム（approve_impl.sh）が呼ぶ検査と同じもの。
#   恒久の決まり §0-4 の3番（設計書を書く前に、門が求める形を実物で読む）を CC が飛ばした。
#
# 何をするか＝CC の返信に「approve_impl.sh」（＝承認のお願い）が在るターンを終える瞬間に、
#   その場で pre_audit_check.py --check-design を走らせる。不足が在ればターンを終われない。
#   ★記録（marker）に頼らない＝その場で走らせるので、走らせたフリができない。
#
# 限界（正直に）:
#   ・承認のお願いを「approve_impl.sh」の文字を出さずに書けば、この hook は当たらない。
#   ・設計書の中身が正しいかは見ない（門の形だけ）。中身は まこさんの目と監査。
#   ・この hook 自身を書き換えれば無効にできる（差分は git に出る）。

set -u
ROOT="/Users/tachiharamasako/Documents/GitHub/cat-bitget"
ACC="$ROOT/.claude/state/acceptance.md"
CHK="$ROOT/.claude/tools/pre_audit_check.py"

RAW="$(cat)"                                   # Stop hook の入力（json）

# 返信の中に承認のコマンドが在るか（無ければ何もしない）
if ! printf '%s' "$RAW" | grep -q "approve_impl.sh"; then
  exit 0
fi
# 承認のプログラムの説明そのもの（hook の一覧など）で誤発火しないよう、お願いの形だけを見る
if [ ! -f "$ACC" ] || [ ! -f "$CHK" ]; then
  exit 0
fi

OUT="$(python3 "$CHK" --check-design "$ACC" 2>&1)"
if printf '%s' "$OUT" | grep -q "設計書の中身は通ります（不足0件）"; then
  exit 0
fi

{
  echo "🔒 [承認の前の門の検査] 設計書に不足が在るまま、承認をお願いしようとしています。"
  echo "   まこさん指摘 2026-09-19「毎回承認のたびにランダムでやられると迷惑なんだけど。」"
  echo ""
  echo "   承認のプログラムが呼ぶ検査と同じものを、いま走らせた結果です:"
  printf '%s\n' "$OUT" | sed 's/^/   /'
  echo ""
  echo "   対処＝上の不足を全部 直し、次が「不足0件」になってから、承認をお願いしてください:"
  echo "     python3 .claude/tools/pre_audit_check.py --check-design .claude/state/acceptance.md"
} >&2
exit 2
