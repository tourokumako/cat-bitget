#!/bin/bash
# enforce_scoring_window_only.sh — PreToolUse on Bash（2026-07-16 まこさん指示で新設・fast-mode 専用ガード）
# 目的: fast-mode(非ML固定ルール改善)で probe/分析/検証/テスト/採点を「採点窓(score CSV=直近6ヶ月)」だけで回す。
#   学習窓(train CSV=2021〜2025＝今の値動きと乖離)を分析/採点に使うのをブロック。
#   背景(2026-07-16 事案): CC が非ML固定ルール(flat_up 建値保護)を e37 標準パイプラインに乗せ、学習窓の
#   precheck FAIL・「学習窓↔採点窓 符号逆転(L-320)」で結果を誤って殺した。fast-mode は ML を使わないので学習窓は無関係。
#   正本: cat_requirements §8.5 / memory feedback_fastmode_scoring_window_only。
# 判別: fast-mode ON の時だけ発火。python 実行で _train.csv を score/precheck/report/analyze/probe に渡す→ブロック。
#   戦略の本走(e37 …)は _train.csv を「入力に取らない」(出力で生成する)ので誤発火しない。
#   ML に戻る(fast-mode OFF)時は普段の PDCA が学習窓を正当に使う＝この hook は黙る。明示解除 SCOREWIN_OK=1。
MARK="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/pdca_fast_mode"
[ ! -f "$MARK" ] && exit 0   # fast-mode OFF(=ML mode) では学習窓は正当 → 通す（safety hook と逆＝fast-mode 限定）

INPUT=$(cat)
AGENT_TYPE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('agent_type',''))" 2>/dev/null)
[ -n "$AGENT_TYPE" ] && exit 0   # サブエージェントは通す（他 hook と同型・デッドロック回避）

CMD=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print((json.load(sys.stdin).get('tool_input',{}) or {}).get('command',''))" 2>/dev/null)

printf '%s' "$CMD" | grep -qE 'SCOREWIN_OK=1' && exit 0   # 明示オーバーライド（ML 復帰時・稀）

printf '%s' "$CMD" | grep -qE 'python[0-9.]*[[:space:]]' || exit 0   # python 実行時のみ判定
printf '%s' "$CMD" | grep -qE '_train\.csv' || exit 0               # 学習窓 CSV に触れていなければ通す
# score/precheck/report/analyze/probe/deep_analysis のいずれかに train を渡している＝分析/採点に学習窓を使用
printf '%s' "$CMD" | grep -qE 'score\.py|precheck\.py|report\.py|analyze\.py|_probe\.py|_deep_analysis\.py' || exit 0

echo "🔒 [採点窓のみゲート・fast-mode] 学習窓(train CSV)を probe/分析/検証/採点に使っています。" >&2
echo "" >&2
echo "fast-mode(非ML固定ルール改善)は 採点窓(score CSV＝直近6ヶ月・本番に近い期間)だけで判定します（cat_requirements §8.5 / memory feedback_fastmode_scoring_window_only）。" >&2
echo "学習窓(2021〜2025)は今の値動きと価格帯が乖離＝固定ルールの采否に持ち込まない（2026-07-16 事案の再発防止）。" >&2
echo "対処: 対象を *_score.csv に差し替えて再実行。ML に戻す(まこさん明示解禁)時だけ SCOREWIN_OK=1 を付けて通す。" >&2
exit 2
