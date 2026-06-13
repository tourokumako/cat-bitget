#!/bin/bash
# reset_read_log.sh — SessionStart
# 新セッション開始時に read_log をリセット（前セッションの読了を引き継がない）。
# これで毎セッション、必読を Read tool で読み直すまで作業ツールが block される。

STATE_DIR="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
mkdir -p "$STATE_DIR"
: > "$STATE_DIR/read_log.txt"
# 目標逆算ゲート（ゲート2）リセット: 前セッションの逆算ブロックは引き継がないが、
# 引き継ぎ前提（本筋・やってはいけないこと）は残す。必須見出しの語は入れないので
# ゲートは維持され、新セッションは前提を見てから自分で目標逆算を Write し直す（2026-06-12 まこさん指示）。
cat > "$STATE_DIR/goal_block.md" <<'EOF'
# 目標逆算（新セッションが本欄を Write し直す）

> ⚠️ 下は前セッションの引き継ぎ前提。新セッションはこれを踏まえ、本欄に目標逆算ブロックを Write し直すこと
> （必須見出しが揃うまで Bash/Edit/Write はブロックされる＝前提を読んでから自分で逆算する）。

## 引き継ぎ前提（2026-06-12・次セッションの本筋）
- 本筋＝**下げ相場の LONG でも稼げる状態にする**（打ち切り禁止）。「P4 打ち止め・P21 へ」は今セッション CC の逃げ・誤り。
- まこさん確定方針＝**下げ相場の反発（オーバーソールド・急落後の戻り）を add で伸ばさず短く取る LONG を、V9 P4 の枠を超えて設計**する。
- E26（P4 Exit policy ML）/ E27（P4 メタラベリング Entry 選別）は破棄＝V9 P4 の中身いじりでは下げ相場で稼げない
  （V9 P4＝上昇トレンドの押し目買いで下げ相場に不適・E27 で判別力 AUC 0.653 は立った）。
- 起点＝**P4 の改善案から話し合う**（実験前に議論）。詳細は next_step.md（SessionStart 表示）と ledger E26・E27。
EOF

echo "=== [読了強制ゲート 有効] ==="
echo "必読3本を Read tool で実際に開くまで、Bash/Edit/Write は block されます（読んだふり防止・2026-06-12 §8.1 で 7→3 にスリム化・require_read_before_work と一致）:"
echo "  1. cat_requirements.md（要件・H制約・PDCA）"
echo "  2. WORKFLOW.md（現在地・次タスク）"
echo "  3. ledger.md（PDCA 実験記録の正本・直近の数字/原因/採否）"
echo "→ grep や表示だけでは解除されません。Read tool で開いてください。"
echo "（補助＝必要時のみ: 設計=strat_v9ml_design / 分析手順=analysis_playbook / 教訓=lessons_active を grep 参照）"
echo ""
echo "=== [目標逆算ゲート 有効・WORKFLOW Step 0 ④] ==="
echo "必読後、目標逆算ブロック（5行+3行ゲート）を .claude/state/goal_block.md に Write し、"
echo "同内容をチャットに出してまこさんの GO を得るまで、Bash/Edit/Write は block されます。"
echo "（届かない候補を単体ミッションにしない・導出の向き＝届く構成から逆算・2026-06-12）"
exit 0
