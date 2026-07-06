#!/bin/bash
# hook_health_check.sh — SessionStart（2026-07-04 まこさん承認で新設）
# hook 無言死の検出（pdca_mark 2026-06-29〜07-03 無言死事案＝python SyntaxError を exit 0 が握りつぶし
# 旗管理が全停止していた、の横展開対策）。表示専用＝常に exit 0（ブロックしない）。
#  ① settings.json（共有・git 管理＝hook 登録の正本）＋ settings.local.json（ローカル上書き）両方に登録された全 hook .sh の実在・実行権限
#  ② hooks/*.py 全部の py_compile（構文死の検出）
#  ③ state/*_error.log の非空（fail-open で握りつぶされた実行時エラーの可視化）
#  ★2026-07-06: hook 登録を git 管理するため hooks ブロックを settings.local.json → settings.json へ移動（まこさん指示）。両方を走査。
HOOKS_DIR="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks"
STATE_DIR="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
SETTINGS_MAIN="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/settings.json"
SETTINGS_LOCAL="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/settings.local.json"
NG=0

# ① 登録 hook の実在・実行権限（settings.json＋settings.local.json 両方＝マージ後に効く全 hook）
for f in $(grep -hoE '"/[^"]*/\.claude/hooks/[^"]*\.sh"' "$SETTINGS_MAIN" "$SETTINGS_LOCAL" 2>/dev/null | tr -d '"' | sort -u); do
  if [ ! -f "$f" ]; then echo "❌ hook 不在: $f"; NG=$((NG+1));
  elif [ ! -x "$f" ]; then echo "⚠️ 実行権限なし: $f"; NG=$((NG+1)); fi
done

# ② hooks/*.py の構文チェック（無言死の主因＝SyntaxError）
for p in "$HOOKS_DIR"/*.py; do
  [ -f "$p" ] || continue
  if ! python3 -m py_compile "$p" 2>/dev/null; then
    echo "❌ hook python 構文死（無言死の温床）: $p"; NG=$((NG+1))
  fi
done

# ③ 実行時エラーログの可視化（fail-open で通した例外）
for lg in "$STATE_DIR"/*_error.log; do
  [ -s "$lg" ] || continue
  echo "⚠️ hook 実行時エラーあり（fail-open で素通りした可能性）: $lg（$(wc -l < "$lg" | tr -d ' ')行・要確認後クリア）"
  NG=$((NG+1))
done

if [ "$NG" -eq 0 ]; then
  echo "✅ hook 健全性: 登録 .sh 実在/実行権限・hooks/*.py 構文・エラーログ ぜんぶ異常なし"
else
  echo "🔴 hook 健全性: 異常 ${NG} 件（上記）＝強制が効いていない可能性＝作業前にまこさんへ報告"
fi
exit 0
