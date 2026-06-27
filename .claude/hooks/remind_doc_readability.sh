#!/usr/bin/env bash
# remind_doc_readability.sh — 資料文書を Write/Edit する瞬間に「文書はCCの足場が第一目的・
#   だがまこさんが原因究明できる可読性を保つ」原則を表示する（非ブロック・exit 0）。
# 対象: .claude/rules/ ・ .claude/ratchet/ ・ .claude/state/ 配下の .md / memory ディレクトリ配下の .md
# それ以外（.py 等のコード）では何も出さない。
# 登録: PreToolUse matcher "Write|Edit"（settings.local.json）。
# 背景: memory feedback_docs_are_cc_scaffold_keep_human_auditable（2026-06-27 まこさん指示）。
#   強制リマインダは作成の瞬間に出す（SessionStart/recall は background で錨が下りない・feedback_enforcement_at_proposal_time）。

input=$(cat)
fp=$(printf '%s' "$input" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)

case "$fp" in
  *.md)
    case "$fp" in
      */.claude/rules/*|*/.claude/ratchet/*|*/.claude/state/*|*/memory/*)
        cat >&2 <<'EOF'
📄 [文書作成リマインダ] この資料は「記憶ゼロの新セッションCCが cold start で誤解なく理解・改善するための足場」が第一目的（まこさんのためでない）。唯一の基準＝次のCCがこれだけで誤解せず動けるか。
 ・1情報1箇所／階層明示／局面等のブロックで文脈を閉じる／重複・散在・暗黙の前提・詰め込み・記号圧縮・暗号化を排除。
 ・ただし まこさんはCCのミスを原因究明する監督者＝暗号化せず まこさんも追える可読性を保つ（CCが誤解しない構造＝人間も追える・両立する）。
 ・動く数字（採用状態/net）は台帳1箇所・不変文書に焼かない。
EOF
        ;;
    esac
    ;;
esac
exit 0
