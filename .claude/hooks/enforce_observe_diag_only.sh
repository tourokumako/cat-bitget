#!/bin/bash
# enforce_observe_diag_only.sh — PreToolUse on Bash（2026-07-24 まこさん指示・新設・safety hook＝両モードで有効）
#
# 目的: 検証・観察は observe_diag.py など scripts/priority_rebuild/ 配下の正本道具だけを使う。
#   CC が自作の観察/探索スクリプトを scratchpad・/tmp に書いて走らせる「道具の再発明」を物理で封じる。
#
# 背景（2026-07-24 事案）: CC が observe_diag を使わず、自作 probe（stage2_amplitude_probe.py /
#   s2_entry_separation_probe.py）を量産して走らせ、まこさんが確立した検証道具とフローを勝手に置き換えた。
#   理由=「合わないと判断した」意図=「自分のやり方で早く進めたかった」＝勝手に動く癖。gen_flow で固定した
#   フローの意味を道具レベルで壊した。cc_role §1.4.6.2＝CC 自主運用では止まらない→物理強制で塞ぐ。
#
# 強制: python で /private/tmp・/tmp・scratchpad 配下の .py を実行しようとしたらブロック（exit 2）。
#   正本道具（observe_diag / engine_tuner / score / report / analyze / precheck 等）は
#   scripts/priority_rebuild/ 配下にあるので一切影響しない（置き場所で判別）。
#   観察に足りない機能があれば自作せず observe_diag に節を足す（まこさん承認）。
#
# safety hook: fast-mode 無効化行を入れない（自作 probe の暴走は fast-mode 中に起きた＝fast-mode でこそ要る）。
# 対象外（通す）: 引用符・ヒアドキュメントの中身（git commit メッセージ・echo 等での言及は除去して判定）。
#   サブエージェント（Workflow/Agent 内）も通す（デッドロック回避・他 hook と同型）。
# 解除: 無し（2026-08-16 まこさん指示「じゃあ強制解除できない状態にしろ」で廃止）。
# 限界: 置き場所（scratchpad/tmp）で判別＝正本ディレクトリに自作を書けば素通り（他の命名/acceptance ゲートが担保）。
#   引用符を除去するので実行パスを引用符で囲めば素通りしうる（＝意図的 bypass は cc_role §1.4.6.2 で禁止）。テキスト検査＝まこさんの目と併用。

INPUT=$(cat)
AGENT_TYPE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('agent_type',''))" 2>/dev/null)
[ -n "$AGENT_TYPE" ] && exit 0   # サブエージェントは通す（デッドロック回避）

# ★解除（合言葉）は 2026-08-16 に廃止＝まこさん指示「じゃあ強制解除できない状態にしろ」。通す道は無い。

CMD=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print((json.load(sys.stdin).get('tool_input',{}) or {}).get('command',''))" 2>/dev/null)

# 引用符・ヒアドキュメントの中身を除去（文章での言及では誤発火させない・enforce_observation_design と同型）
CMD_X=$(printf '%s' "$CMD" | python3 -c "
import sys, re
s = sys.stdin.read()
s = re.sub(r'<<\s*[\"\x27]?(\w+)[\"\x27]?.*?^\1', ' ', s, flags=re.S | re.M)  # ヒアドキュメント本文を除去
s = re.sub(r'\"[^\"]*\"', ' ', s); s = re.sub(r\"'[^']*'\", ' ', s)             # 引用符の中身を除去
print(s)" 2>/dev/null)
[ -z "$CMD_X" ] && CMD_X="$CMD"

# python 実行の時だけ判定
printf '%s' "$CMD_X" | grep -qE 'python[0-9.]*[[:space:]]' || exit 0

# /private/tmp・/tmp・scratchpad 配下の .py を実行対象にしているか（＝自作の検証/観察スクリプト）
bad=$(printf '%s' "$CMD_X" | grep -oE '(/private/tmp|/tmp)/[^ "'"'"';|&]*\.py|[^ "'"'"';|&]*scratchpad/[^ "'"'"';|&]*\.py')
[ -z "$bad" ] && exit 0

echo "🔒 [検証は observe_diag だけ・safety hook] scratchpad・/tmp の自作スクリプトの実行はブロックします（まこさん指示 2026-07-24）。" >&2
echo "" >&2
echo "止めた対象:" >&2
printf '%s\n' "$bad" | sed 's/^/  - /' >&2
echo "" >&2
echo "背景: 2026-07-24 CC が observe_diag を使わず自作 probe を量産し、確立した検証道具・フローを勝手に置き換えた。" >&2
echo "検証・観察の正本道具（scripts/priority_rebuild/ 配下）だけを使う:" >&2
echo "  ・観察/分析 = observe_diag.py（--plan 提出→まこさん OK→本走）" >&2
echo "  ・層3 探索  = engine_tuner.py" >&2
echo "  ・採否/分析 = score.py / report.py / analyze.py / precheck.py" >&2
echo "" >&2
echo "observe_diag に足りない観察があれば、自作せず observe_diag に節を足す（まこさん承認）＝道具を再発明しない。" >&2
echo "（解除は 2026-08-16 に廃止。足りない観察は observe_diag に節を足す）" >&2
exit 2
