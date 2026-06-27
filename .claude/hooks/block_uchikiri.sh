#!/bin/bash
# block_uchikiri.sh — PreToolUse on Write|Edit
# 「打ち切り思考」のワードを 意思決定アーティファクト(ledger.md / next_step.md / acceptance.md)の
# 新規内容で物理禁止（まこさん命令 2026-06-15「破棄ワード自体禁止／打ち切り思考も防ぐ」）。
#
# 目的:
#   CC は1回の悪化で「破棄/全敗/打ち止め/再挑戦しない/不成立」と方向を勝手に閉じる（思考停止の却下）を
#   何度も再演した。アジャイル＝地面を超えなくても継続（ratchet=地面は維持）。個別ツマミが数字を上げない時は
#   「採用せず（地面維持）＋次の作り込み案（同方向の別の作り方）」と書く。＝打ち切り判断を物理的に書けなくする。
#
# 衝突回避（まこさん指示）:
#   - 対象は ledger.md / next_step.md / acceptance.md のみ。他ファイルは即 exit 0（script編集系hook に干渉しない）。
#   - doc_map_guard(ledger の経緯混入を防ぐ)とは別チェック＝共存。require_spec_read は *_design.md 対象で acceptance とは別。
#   - サブエージェントは通す（デッドロック回避・他hookと同型）。
#   - 禁止語は「早期撤退(feature名)」「打ち切りでない」を誤爆しない語だけ選定（撤退/打ち切り の部分一致は使わない）。
#
# 正直な限界: 言葉を塞ぐだけ＝中身の打ち切り思考は完全には防げない。深い分析ゲート(require_acceptance)＋まこさんの目 併用。

INPUT=$(cat)

AGENT_TYPE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('agent_type',''))" 2>/dev/null)
[ -n "$AGENT_TYPE" ] && exit 0

FILE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print((json.load(sys.stdin).get('tool_input',{}) or {}).get('file_path',''))" 2>/dev/null)
case "$FILE" in
  *ledger.md|*next_step.md|*acceptance.md) ;;
  *) exit 0 ;;
esac

# 新規に書き込む内容（Write content / Edit new_string / MultiEdit edits[].new_string）だけを集める
NEW=$(printf '%s' "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin); ti = d.get('tool_input', {}) or {}
s = (ti.get('content', '') or '') + (ti.get('new_string', '') or '')
for e in (ti.get('edits', []) or []):
    s += e.get('new_string', '') or ''
print(s)" 2>/dev/null)

HIT=$(printf '%s' "$NEW" | grep -oE "破棄|全敗|打ち止め|再挑戦しない|不成立|別途|行き止まり|改善余地なし|手詰まり|これ以上ない" | sort -u | tr '\n' ' ')
if [ -n "$HIT" ]; then
  echo "🔒 [打ち切り・逃げ禁止ゲート] 禁止ワード検出: $HIT（まこさん 2026-06-15）。" >&2
  echo "  ・破棄/全敗/打ち止め/再挑戦しない/不成立＝打ち切り思考。1回の悪化で方向を閉じない＝アジャイル。" >&2
  echo "    代わりに『採用せず（地面は ratchet で維持）＋次の作り込み案（同方向の別の作り方）』を書く。" >&2
  echo "  ・別途＝分析/作業の punt（先送り）。逃げずにこのセッションで完走させる（ツールが壊れているなら直す）。" >&2
  echo "  真の即不採用(leak/cap/degenerate/配管の捨て駒=§8.4 例外)は『即不採用（§8.4 理由=…）』と書く（禁止語は使わない）。" >&2
  exit 2
fi
exit 0
