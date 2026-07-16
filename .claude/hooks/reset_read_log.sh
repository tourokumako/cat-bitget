#!/bin/bash
# reset_read_log.sh — SessionStart
# 新セッション開始時に read_log をリセット（前セッションの読了を引き継がない）。
# これで毎セッション、必読を Read tool で読み直すまで作業ツールが block される。

STATE_DIR="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
mkdir -p "$STATE_DIR"
: > "$STATE_DIR/read_log.txt"
rm -f "$STATE_DIR/budget_rule_shown"   # 予算バナーを新セッションで1回出すため（show_budget_before_design.sh・2026-06-20）
rm -f "$STATE_DIR/banned_words_checked" # 禁止語チェックの事前実行を新セッションで1回強制（require_banned_words_check.sh・2026-07-11 まこさん指示）
rm -f "$STATE_DIR/analysis_block.md"   # 分析ブロックを新セッションでリセット（前セッションの分析を持ち越さない＝require_analysis_before_proposal.sh・2026-06-24）
rm -f "$STATE_DIR/improvement_plan.md" # 改善案生成(STEP1〜5)を新セッションでリセット（probe前ゲートA＋提案ゲートB＝require_probe_naming/require_analysis_before_proposal・2026-06-28）
rm -f "$STATE_DIR/fastmode_trades_seen" "$STATE_DIR/fastmode_e37_seen" "$STATE_DIR/fastmode_ledger_seen" "$STATE_DIR/worklog_ok" "$STATE_DIR/fastmode_record_pending"  # fast-mode ガード(改善前データ必読[trades/e37/ledger ARC]/引き継ぎ記録/分析後記録)のマーカーを新セッションでリセット（2026-07-16）
rm -f "$STATE_DIR/comprehension_check.md"   # 理解確認テストの回答を新セッションでリセット＝毎セッション再回答を強制（require_comprehension_check.sh・2026-07-16 まこさん指示）
# 目標逆算ゲート（ゲート2）リセット: 前セッションの逆算ブロックは引き継がないが、
# 引き継ぎ前提（本筋・やってはいけないこと）は残す。必須見出しの語は入れないので
# ゲートは維持され、新セッションは前提を見てから自分で目標逆算を Write し直す（2026-06-12 まこさん指示）。
cat > "$STATE_DIR/goal_block.md" <<'EOF'
# 目標逆算（新セッションが本欄を Write し直す）

> ⚠️ 下は前セッションの引き継ぎ前提。新セッションはこれを踏まえ、本欄に目標逆算ブロックを Write し直すこと
> （必須見出しが揃うまで Bash/Edit/Write はブロックされる＝前提を読んでから自分で逆算する）。

## 引き継ぎ前提
- 本筋・今セッションの確定・やってはいけないこと・数字の出典は **next_step.md（SessionStart で全文表示）が正本**。
  そちらを起点に、本欄へ目標逆算ブロック（大目標/器の現在値/ギャップ/候補/天井/選定/3行ゲート/届く構成/戦略照合）を Write し直す。
- ⚠️ ここに前セッション固有の handoff を焼き込まない（hook に焼くと古くなって誤誘導する＝2026-06-13 P4 stale 事案）。最新は常に next_step.md。
EOF

echo "=== [読了強制ゲート 有効] ==="
echo "必読3本を Read tool で実際に開くまで、Bash/Edit/Write は block されます（読んだふり防止・require_read_before_work と一致）:"
echo "  1. WORKFLOW.md（現在地・次タスク）"
echo "  2. next_step.md（改善アーク＝前提/狙い/内容/方法/結果/採否・次セッション起点・2026-07-05 ledger.md 全文読了強制から差替）"
echo "  3. adopted_strategies.md（採用ポートフォリオ台帳）"
echo "→ grep や表示だけでは解除されません。Read tool で開いてください。"
echo "（ledger.md 本体＝特定の過去実験を深掘りする時に読む参照資料。毎回の必読からは外した）"
echo "★ cat_requirements.md / exchange_spec.md（決済方法）は『設計書を書く瞬間』に強制 read（just-in-time・require_spec_read_before_design.sh）。"
echo "   理由: セッション開始時に読んでもインプットされない実証（まこさん 2026-06-13・add/決済を毎回誤解）。"
echo "（補助＝必要時のみ: 設計=strat_v9ml_design / 分析手順=analysis_playbook / 教訓=lessons_active を grep 参照）"
echo ""
echo "=== [目標逆算ゲート 有効・WORKFLOW Step 0 ④] ==="
echo "必読後、目標逆算ブロック（5行+3行ゲート）を .claude/state/goal_block.md に Write し、"
echo "同内容をチャットに出してまこさんの GO を得るまで、Bash/Edit/Write は block されます。"
echo "（届かない候補を単体ミッションにしない・導出の向き＝届く構成から逆算・2026-06-12）"
exit 0
