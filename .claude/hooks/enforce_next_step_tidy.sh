#!/bin/bash
# enforce_next_step_tidy.sh — Stop: next_step.md の §0 の形を検査し、❌ が1つでも在ればターンを終われない
#   （2026-08-28・まこさん承認・設計書 iter=tidy-next-step-20260828・safety hook＝fast-mode でも動く）
#
# なぜ＝next_step.md は毎セッション汚れて、まこさんが指示しないと整理されなかった（69回目の末に実測）。
#   「消す」を CC の判断に任せると消されない。だから機械（tidy_next_step.py）が整えて検査し、
#   検査 ❌ のままではセッションを閉じられない形にする。
# 判定の本体は .py（pdca_gate.sh L13-19 の決まり＝hook の python は別ファイル化）。
# 直し方＝python3 .claude/tools/tidy_next_step.py --write（「消す」印の節を archive へ移し (0-b-2) を json から書く）
#         ＋ 0-1 を今日の状態に書き直す（文章は CC が書く・機械は日付だけ見る）。
# ★fast-mode の判定は入れない（(0-b-2) の腐りと「消す」印の溜まりは fast-mode の間にも起きる）。
# ★止める回数に上限は付けない（直し方が1つで、機械で直せるため）。
# テスト用＝第1引数に next_step.md の代わりのファイルを渡せる（--selftest の T8 が使う）。
ROOT="/Users/tachiharamasako/Documents/GitHub/cat-bitget"
TOOL="$ROOT/.claude/tools/tidy_next_step.py"
if [ -n "$1" ]; then
  OUT=$(python3 "$TOOL" --verify --file "$1" 2>&1); RC=$?
else
  OUT=$(python3 "$TOOL" --verify 2>&1); RC=$?
fi
if [ "$RC" -ne 0 ]; then
  printf "⛔ [next_step の形・Stop hook] next_step.md の §0 が整っていないのでターンを終われません（まこさん 2026-08-28「毎回、next_stepが汚くなり、私が指示しないと整理されない状況なんだけど、改善できないのか？」）。\n%s\n直し方＝python3 .claude/tools/tidy_next_step.py --write ＋ 0-1 を今日の状態に書き直す。\n（解除の合言葉はありません＝2026-08-16 に全部 廃止）\n" "$OUT" >&2
  exit 2
fi
# ★2026-09-09（まこさん指示・逐語「session_worklogへの記録は日付で区切ってほしい」「今後、このようなこと
#   （日付をまたいで記録し続ける）が無いようにしてほしい」）＝worklog を日付をまたいで書き続けていないかを見る。
#   判定の本体＝check_worklog_date.py（番人4件・--selftest）。テスト用の第1引数のときは見ない（next_step の検査だけ）。
if [ -z "$1" ]; then
  # ★2026-09-17（まこさん指示「手書きせざるをえないもの以外は自動生成にしてほしい」・設計書 docs-autogen-next-step-pdca-20260917）
  #   ＝pdca_flow.md の §1 の hook の一覧が、settings.json の登録と元データ hook_roles.json から作ったままかを見る。
  #   Bash で囲みの中を書き替えた・hook を登録したのに一覧を作り直していない、のどちらでもターンを終われない。
  #   テスト用の第1引数のときは見ない（tidy_next_step.py --selftest の T8 は next_step の検査だけを試す）。
  HL=$(python3 "$ROOT/.claude/tools/gen_hook_list.py" --verify 2>&1); HRC=$?
  if [ "$HRC" -ne 0 ]; then
    printf "⛔ [hook の一覧・Stop hook] pdca_flow.md の §1 の hook の一覧が、settings.json と元データから作ったままではありません（まこさん 2026-09-17「手書きせざるをえないもの以外は自動生成にしてほしい」）。\n%s\n直し方＝役割の文は .claude/state/hook_roles.json に書く → python3 .claude/tools/gen_hook_list.py --write\n（解除の合言葉はありません）\n" "$HL" >&2
    exit 2
  fi
  WL=$(python3 "$ROOT/.claude/hooks/check_worklog_date.py" 2>&1); WRC=$?
  if [ "$WRC" -ne 0 ]; then
    printf "⛔ [worklog の日付・Stop hook] worklog を日付をまたいで書き続けています（まこさん 2026-09-09「session_worklogへの記録は日付で区切ってほしい」）。\n%s\n直し方＝今日の日付の session_worklog_YYYYMMDD.md を作り、今日の節はそこへ書く。古いファイルは触らない（触ったら、そのあとで今日の worklog を書き足す）。\n（解除の合言葉はありません）\n" "$WL" >&2
    exit 2
  fi
fi
exit 0
