#!/bin/bash
# pdca_fast.sh — PDCA 強制フローの一時オンオフトグル（まこさん承認 2026-07-16・高速ループ用）
#   ON  = process/doc hook（分析→acceptance→網羅→係留→ベースアップ 等）を一時無効化して
#         「チャット決定→スクリプト修正→テスト→結果表示→チャット」の高速ループを回す。
#   常時オンで残る safety = require_period_source（期間 leak）／require_leak_annotation（H2 leak）／
#         require_tag_for_experiment（上書き防止）＋ コード内自動（e37 の leak self-grep・score.py の cap/窓）。
#   ★fast モード中の規律（hook でなく人）: 采否は score.py 両窓の数字だけ（crude/楽観値で採否しない）／
#         入口の新特徴は「建てる時点で取得可能か」を1行宣言して因果性確認（H2）／記録はセッション末に一括。
MARK="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/pdca_fast_mode"
STATE="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
case "$1" in
  on)
    touch "$MARK"
    echo "✅ PDCA fast-mode ON"
    echo "   process/doc hook 無効・safety(period/leak/tag)＋score.py cap/窓 は継続。"
    echo "   ⚠️ 采否は score.py 両窓の数字だけ／入口の新特徴は因果性(H2)を宣言／記録はセッション末に一括。"
    ;;
  off)
    rm -f "$MARK"
    rm -f "$STATE"/pdca_need_* "$STATE"/pdca_exp_started 2>/dev/null
    echo "✅ PDCA fast-mode OFF — full PDCA 復帰＋stale 旗クリア。"
    ;;
  status|"")
    if [ -f "$MARK" ]; then echo "PDCA fast-mode: ON"; else echo "PDCA fast-mode: OFF"; fi
    ;;
  *)
    echo "usage: pdca_fast.sh on|off|status"
    ;;
esac
