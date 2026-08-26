#!/bin/bash
# ★2026-08-26（63回目・まこさん指示・逐語「強制に戻せよ。修正したのに強制してなかったら意味がないよね？」）
#   ＝fast-mode で自分を無効にする行を外した＝safety hook へ格上げ。
#   直す前の2行目: [ -f ".../pdca_fast_mode" ] && exit 0
#   なぜ外したか（同日の実測）＝この hook が止まっていたので、私は見出しの一覧を見ずに設計書を書き、
#     必須の見出しを2回 落として実装で止まり、まこさんに2回 再承認をお願いした
#     （1回目＝真因・期待値・symptom・ベースアップ／2回目＝★疑似シミュ由来の固定値ゼロ宣言）。
#   ★fast-mode 自体は ON のまま（まこさん指示 2026-08-23「全部起動しないでほしい」）＝外したのはこの1行だけ。
#   前例＝55回目に、まこさん指示で require_design_contract_before_run と require_acceptance_before_impl の
#     2本だけ同じ行を外した（next_step.md §6 の80番）。
# require_banned_words_check.sh — PreToolUse(Write|Edit) 禁止語チェックの事前実行を物理強制
#   （2026-07-11 まこさん指示「acceptance 等を書く前に list_banned_words.py を通すことを強制化しておいて」）
# 対象: list_banned_words.py が扱う5文書＝ledger.md / next_step.md / acceptance.md / improvement_plan.md / analysis_block.md
# 解除: 同一セッション内に list_banned_words.py を1回実行
#   （track_banned_words_check.sh[PostToolUse Bash] がマーカー touch・reset_read_log.sh がセッション開始で削除＝show_budget と同型の1セッション1回方式）
# 背景: 書いてから禁止語/必須見出し hook にブロックされ直す手戻り（2026-07-05 20回手戻り・2026-07-11 も enforce_combo_matrix 等で複数回）。
#   書く前に要件（必須見出しのコピペ用トークン＋禁止語と正しい言い換え）を1回見れば手戻りが消える＝その1回を物理強制する。

INPUT=$(cat)
FILE_PATH=$(printf '%s' "$INPUT" | python3 -c "import sys,json
try: print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))
except Exception: print('')" 2>/dev/null)
BASE=$(basename "$FILE_PATH")
case "$BASE" in
  ledger.md|next_step.md|acceptance.md|improvement_plan.md|analysis_block.md) ;;
  *) exit 0 ;;
esac

MARKER="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/banned_words_checked"
[ -f "$MARKER" ] && exit 0

echo "🔒 [禁止語チェック 事前実行ゲート] ${BASE} を書く前に、その文書のゲート要件（必須見出し＋禁止語）を確認してください（まこさん指示 2026-07-11）。" >&2
echo "→ 実行: python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/list_banned_words.py（引数なし=全文書 ／ または ledger|next_step|acceptance|improvement_plan|analysis_block）" >&2
echo "→ 1セッション1回で解除（実行が track_banned_words_check.sh に記録される）。書いてからブロックされる手戻り（2026-07-05 20回）を書く前の1回で防ぐ。" >&2
exit 2
