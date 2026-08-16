#!/bin/bash
# enforce_e37_split_ceiling.sh — PreToolUse on Bash（2026-07-16 まこさん指示）
# 目的: E37 の入口から 2型切り分け（--v26-split-ceiling＝下落系レンジは天井=直近高値／平坦・上昇系は天井=res_hi
#   に売り指値を置く＝レンジの適切な上端で売る＝レンジ下端でショートを建てない）を外して本走するのを物理ブロック。
# 背景（「レンジ下端でショート」は E37 が何度も再発させてきた病）:
#   v19（ledger ARC34）到達を帯下端 res_lo→上端 res_hi へ＝一律 res_hi で件数−84%崩壊
#   v25 RG-v6（ARC40）束ね幅ボラ連動で res_lo を真の抵抗へ寄せ下弦是正
#   v26-split-ceiling（worklog §3/§9/§10）＝2型切り分け＝「価格が現実的に届く適切な天井」に売る＝下端で建てない対策の到達点
#   2026-07-16 CC が頻度を上げるため v26-split-ceiling を外し 12h上端の現値売り（--v26-touch-frac）にして
#   下端エントリーを再発（入口の97%が帯の下半分より下・損失そこに集中）＝改悪。まこさん「外せないように強制しろ」。
# ルール: e37_range_scalp.py を出力モードで走らせる時は --v26-split-ceiling を必須にする。
#   頻度は2型の適切な天井に錨を打ったまま上げる（現値売りで下端に散らさない）。
# 対象外（通す）: 非出力/テスト/診断/自己検査（--smoke/--diagnostic/--selftest 系/--param-schema-selftest/
#   guard-check/py_compile/--help）／判定器（score/precheck/report/analyze/plot）・probe/deep_analysis（e37 本体の python 実行でない）。
# override: 無し（2026-08-16 まこさん指示で廃止）。置き換えるときは、この hook 自体をまこさんが直す。

INPUT=$(cat)

# サブエージェント（Workflow/Agent 内）は通す（デッドロック回避・他 hook と同型）
AGENT_TYPE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('agent_type',''))" 2>/dev/null)
[ -n "$AGENT_TYPE" ] && exit 0

CMD=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print((json.load(sys.stdin).get('tool_input',{}) or {}).get('command',''))" 2>/dev/null)

# 明示オーバーライド（正当時のみ・うっかり外し防止が主目的）
# ★解除（合言葉）は 2026-08-16 に廃止＝まこさん指示「じゃあ強制解除できない状態にしろ」。通す道は無い。

# python 実行コマンドの時だけ判定
has_python=$(printf '%s' "$CMD" | grep -cE 'python[0-9.]*[[:space:]]')
[ "$has_python" -eq 0 ] && exit 0

# 実行する e37 戦略本体（e37_range_scalp.py）を抽出（probe/deep_analysis は分析＝除外）
strat=$(printf '%s' "$CMD" | grep -oE 'e37_range_scalp\.py' | grep -vE '(_probe|_deep_analysis)\.py$' | head -1)
[ -z "$strat" ] && exit 0

# 非出力/テスト/診断/自己検査モード（売買記録 CSV を出さない）は通す
printf '%s' "$CMD" | grep -qE '(--smoke|--diagnostic|--selftest|-selftest|--param-schema-selftest|guard-check|py_compile|--help)' && exit 0

# --v26-split-ceiling があれば OK（2型切り分けで適切な天井に売る＝下端で建てない）
printf '%s' "$CMD" | grep -qE '(^|[[:space:]])--v26-split-ceiling([[:space:]]|$)' && exit 0

# ここまで＝e37 を出力モードで 2型切り分け（--v26-split-ceiling）なしで本走＝レンジ下端エントリー再発の恐れ＝ブロック
echo "🔒 [E37 2型切り分けゲート・下端エントリー再発防止] e37_range_scalp.py を出力モードで走らせる時は --v26-split-ceiling を必ず付けてください（2026-07-16 まこさん指示）。" >&2
echo "" >&2
echo "外した理由の禁止: 「頻度を上げるため天井到達待ちをやめる」→ --v26-touch-frac 等の現値売りは【レンジ下端でショート】を再発させます（v26tf07 で入口の97%が帯の下半分より下・損失そこに集中）。" >&2
echo "" >&2
echo "2型切り分け（--v26-split-ceiling）＝下落系レンジは天井=直近高値／平坦・上昇系は天井=res_hi に売る＝価格が現実的に届く適切な上端で売る＝下端で建てない対策の到達点（v19 一律res_hi 崩壊／v25 下弦是正 の系譜・worklog §3/§9/§10・ledger ARC34/ARC40）。" >&2
echo "" >&2
echo "対処: 実行コマンドに --v26-split-ceiling（＋その付随フラグ --v26-gap/--v26-down-hours）を付ける。頻度は【2型の適切な天井に錨を打ったまま】上げる（現値売りで下端に散らさない）。" >&2
echo "  例（v27lock 恒等ベース）: --v20-rg5 ... --v26-split-ceiling --v26-gap 0.5 --v26-down-hours 1.0 --tag <名前>" >&2
echo "解除は 2026-08-16 に廃止。置き換えるときは、この hook 自体をまこさんが直す。" >&2
exit 2
