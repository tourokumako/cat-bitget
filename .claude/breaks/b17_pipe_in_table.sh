#!/bin/bash
# b17 — 表に打ち消した縦棒を書いても、実在しない壊すプログラムの行が記録に混ざらないか
#        （完成の条件 #22・設計書 §3.8・まこさん指示 2026-09-03）
#
# なぜ要るか（実測）
#   承認②の画面に `# 19  bash` ほかを、上流ゲートに掛ける  rc=None` が出た。
#   表の欄の中に書いた縦棒（前に \ を付けたもの）を、列の区切りとして読んでいたため。
#   ＝記録に実在しない行が1つ 増え、画面の分母も 14 → 15 に膨らんだ。
#   まこさんの逐語＝「これは『表の書き方の問題』ではありません。…記録の信頼性の問題です。」
#
# ★呼び合いは起きません＝走らせるプログラムを「読むだけの口」（--parse-only）で呼びます。
#   壊すプログラムを1本も走らせないので、深さに関わらず動きます。
source "$(dirname "$0")/lib.sh"

RUNB="$ROOT/.claude/tools/run_breaks.py"
TMPD="$(mktemp -d)"
MD="$TMPD/pipe_table.md"

# 打ち消した縦棒を含む行だけの表を作る（壊すプログラムの欄は「—」＝走らせる相手は無い）
{
  printf '<!-- ACCEPT_TABLE_START -->\n'
  printf '| # | 完成の条件 | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |\n'
  printf '|---|---|---|---|---|---|---|\n'
  printf '| 19 | 迂回をどこまで塞げているか | 実経路 | `base64 -d \\| bash` ほかを、上流ゲートに掛ける | `—`（%s2） | 対象 | 未着手 |\n' '※'
  printf '| 20 | もう1つ 縦棒を入れた行 | 実経路 | `a \\| b \\| c` を通す | `—` | — | 未着手 |\n'
  printf '<!-- ACCEPT_TABLE_END -->\n'
} > "$MD"

OUT=$(python3 "$RUNB" --parse-only --design "$MD" 2>&1)
RC=$?
rm -rf "$TMPD"

# 期待＝拾った名前が0本（両方の行とも「—」なので、走らせる相手は無い）。
#   幽霊を拾うと、その行が `<番号>\t<名前>\tMISSING` として出る。
GHOST=$(printf '%s' "$OUT" | grep -c 'MISSING')

if [ "$RC" -eq 0 ] && [ "$GHOST" -eq 0 ]; then
    MEASURED=1        # 幽霊なし＝この壊し方が効いた（0 以外が「止まった」の印）
else
    MEASURED=0
    echo "GHOST=$GHOST rc=$RC :: $(printf '%s' "$OUT" | tr '\n' ' ' | cut -c1-160)"
fi
finish
