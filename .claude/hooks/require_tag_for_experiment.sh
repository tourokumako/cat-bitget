#!/bin/bash
# require_tag_for_experiment.sh — PreToolUse on Bash（2026-06-29 まこさん承認で新設）
# 目的: 戦略実験を --tag 無しで「出力モード」実行して【番号なし出力】を作るのを物理ブロック。
#   背景: 2026-06-29 新戦略 E37 をタグ無しで走らせ trades_..._5m_base（番号なし・"base" 入り）を出した命名規則違反。
#   §3.1（analysis_playbook）= 実験は必ず --tag で _<tag>_<NNN> 連番。タグ無しの安定名は【採用済み base】専用
#   （採用は結果＝score.py 両窓を見てから決まる＝採用前の新戦略に番号なし/"base" 名を pre-declare しない）。
#   採用 base の再走（稀・通常しない＝memory feedback_no_manual_results_ops_use_common_io）も、解除は 2026-08-16 に廃止＝タグを付けて走らせる。
# 判別: python で戦略 .py（e3N_ / strat_ / measure_）を出力モードで実行＝--tag が要る。
#   テスト/非出力モード（--smoke/--diagnostic/--selftest/--no-score/py_compile/--help）は通す。
#   probe/deep_analysis・判定器（score/precheck/report/analyze/plot）は戦略でない＝対象外（regex 非該当）。

INPUT=$(cat)
# サブエージェント（Workflow/Agent 内）は通す（デッドロック回避・他 hook と同型）
AGENT_TYPE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('agent_type',''))" 2>/dev/null)
[ -n "$AGENT_TYPE" ] && exit 0

CMD=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print((json.load(sys.stdin).get('tool_input',{}) or {}).get('command',''))" 2>/dev/null)

# 明示オーバーライドは 2026-08-16 に廃止（まこさん指示）。
# ★解除（合言葉）は 2026-08-16 に廃止＝まこさん指示「じゃあ強制解除できない状態にしろ」。通す道は無い。

# python 実行コマンドの時だけ判定
has_python=$(printf '%s' "$CMD" | grep -cE 'python[0-9.]*[[:space:]]')
[ "$has_python" -eq 0 ] && exit 0

# 実行する戦略 .py（e3N_ / strat_ / measure_）を抽出（probe/deep_analysis は分析＝除外）
strat=$(printf '%s' "$CMD" | grep -oE '(e3[0-9][a-z0-9_]*|strat_[a-z0-9_]*|measure_[a-z0-9_]*)\.py' | grep -vE '(_probe|_deep_analysis)\.py$' | head -1)
[ -z "$strat" ] && exit 0

# テスト/非出力モード（出力を書かない or 動作確認）は通す
# ⚠️2026-07-21 修正（まこさん GO）: 旧版は '--selftest'（ダッシュ2つ完全一致）だけを除外しており、
#   '--param-schema-selftest' / '--v11-selftest-zones' のように接頭辞が付く self-test フラグを
#   捕まえられず、売買記録を1行も出さない検査を「実験」と誤検知してブロックしていた。
#   pdca_mark.py が 2026-07-12 に塞いだのと同型の穴（あちらは "selftest" 部分一致で是正済み）。
#   → '--<任意の接頭辞>selftest' を除外に含める。
printf '%s' "$CMD" | grep -qE '(--smoke|--diagnostic|--[a-z0-9-]*selftest|--no-score|py_compile|--help)' && exit 0

# --tag があれば OK（出力が _<tag>_<NNN> 連番になる）
printf '%s' "$CMD" | grep -qE '(^|[[:space:]])--tag([[:space:]]|=)' && exit 0

# ここまで＝戦略を出力モードで --tag 無し実行＝番号なし出力＝ブロック
echo "🔒 [実験 --tag ゲート] 戦略を出力モードで走らせる時は必ず --tag <名前> を付けてください（出力が _<tag>_<NNN> 連番になる・§3.1・2026-06-29 まこさん承認）。" >&2
echo "" >&2
echo "対象戦略: $strat（--tag 無し＝番号なし出力＝命名規則違反）" >&2
echo "" >&2
echo "理由: タグ無しの安定名は【採用済み base】専用（採用は結果＝score.py 両窓を見てから決まる）。採用前の新戦略に番号なし/\"base\" 名を pre-declare しない（2026-06-29 E37 を _5m_base で出した事案）。" >&2
echo "対処: --tag <実験名> を付けて再実行（例 --tag v1）。解除は 2026-08-16 に廃止＝タグ無しでは走らせられない。" >&2
exit 2
