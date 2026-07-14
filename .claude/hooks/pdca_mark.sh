#!/bin/bash
[ -f "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/pdca_fast_mode" ] && exit 0  # [fast-mode] process hook を一時無効化（touch/rm pdca_fast_mode で切替・safety hook には入れない・2026-07-16）
# PostToolUse: PDCA マーカー管理（analysis_playbook §4 物理強制・2026-06-05 まこさん矯正指示）
# score.py 採点 → 「report未済」「ledger未済」の旗を立てる。
# report.py 実行で report 旗 / ledger.md 編集で ledger 旗 を下ろす。
# Stop hook(pdca_gate.sh) が旗の残存でターン終了をブロックする。
#
# ★2026-07-03 修正（まこさん指示「pdca_mark の穴の調査・修正」）:
#   旧版は python コードを bash の python3 -c '...'（シングルクォート）に埋め込んでいた。
#   2026-06-29 改善で足した行（引用符除去 re.sub）が自身のシングルクォートでシェル引用を破壊し、
#   python が毎回 SyntaxError → 末尾 exit 0 が握りつぶし＝2026-06-29 以降 旗管理が全停止していた（無言死）。
#   対策: ① python 本体を pdca_mark.py に分離（-c クォート問題の構造的根絶）
#         ② stderr を state/pdca_mark_error.log へ記録（無言死の可視化＝エラーが出たらログに残る）
#   ロジックは pdca_mark.py 内に旧版と同一のまま移設（変更なし）。
export PDCA_STATE="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
mkdir -p "$PDCA_STATE"
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cat | python3 "$HOOK_DIR/pdca_mark.py" 2>> "$PDCA_STATE/pdca_mark_error.log"
exit 0
