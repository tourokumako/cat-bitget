#!/bin/bash
# b29 — 材料の文書を1行 書き換えると、番人が落ちるか（完成の条件 #3・#5）
#   守っているもの＝①改変の検出が生きていること ②素の状態で鳴っていたら番人を実行せず
#   不合格に数えること（監査 cp23 の X-4）
source "$(dirname "$0")/lib.sh"

T="$SDK/.claude/ratchet/materials.md"
guard "$T"

# 壊す＝材料の文書に1行 足す
printf 'この行は壊すプログラム b29 が足しました\n' >> "$T"

measure python3 "$PR/gen_materials.py" --selftest
finish
