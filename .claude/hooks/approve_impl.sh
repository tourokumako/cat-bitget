#!/bin/bash
# approve_impl.sh — まこさんが受け入れ条件リスト(.claude/state/acceptance.md)を承認する。
#
# 目的（まこさん命令 2026-06-15「指示→受け入れ条件リスト→合意→実装→照合 を標準にし、
#   リスト＋OK が無いと実装に入れない物理強制」）:
#   会話の指示も含め、実装の前に「やること(受け入れ条件)」を文字に起こしてまこさんが承認する。
#   承認＝その時点のリストの内容指紋(sha256)を記録。以後リストを1文字でも変えると指紋が変わり
#   再承認が必要になる（CC がリストをこっそり書き換えて別物を実装する、を防ぐ）。
#
# 使い方: まこさんが内容を確認して納得したら
#   bash /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/approve_impl.sh

STATE="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
LIST="$STATE/acceptance.md"

if [ ! -f "$LIST" ]; then
  echo "❌ 受け入れ条件リストがありません: $LIST" >&2
  echo "   先に CC がリストを書き、チャットで内容を提示するのを待ってください。" >&2
  exit 1
fi

SHA=$(shasum -a 256 "$LIST" | awk '{print $1}')
echo "$SHA" > "$STATE/acceptance.approved"
echo "✅ 承認しました（内容指紋を記録）。"
echo "   指紋: $SHA"
grep -E '^(TARGET|STATUS):' "$LIST" 2>/dev/null

# 承認した acceptance を git 管理 archive へ凍結保存（2026-06-27 まこさん指示・改善アーク自動生成の源）。
#   acceptance.md は state/ で gitignore＋上書き＝永続しない。承認の瞬間に .claude/ratchet/（git 追跡）へコピー＝
#   各 iter の承認版が git に永続（指紋＋git の二重で改ざん検出）。gen_improvement_arc.py が今後 iter の
#   狙い/内容/方法 を ここの ARC マーカーから読む（acceptance archive 優先・無ければ ledger）。
ARC_DIR="/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive"
mkdir -p "$ARC_DIR"
ITER=$(grep -oE 'iter="[^"]*"' "$LIST" | head -1 | sed 's/iter="//;s/"$//')
if [ -n "$ITER" ]; then
  SAFE=$(printf '%s' "$ITER" | tr ' /' '__')
  cp "$LIST" "$ARC_DIR/${SAFE}.md"
  echo "   📦 archive: acceptance_archive/${SAFE}.md（承認版を git 管理へ凍結＝改善アーク自動生成の源）"
else
  cp "$LIST" "$ARC_DIR/${SHA:0:12}.md"
  echo "   ⚠️ acceptance に ARC マーカー(<!-- ARC iter=\"...\" ... -->)が無いため指紋名で保存: ${SHA:0:12}.md"
  echo "      （次回からは acceptance に ARC マーカーを入れると改善アークが自動生成される＝acceptance_checklist 参照）"
fi
echo "   以後このリストを変更したら再承認が必要です。"
