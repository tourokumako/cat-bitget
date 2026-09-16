#!/bin/bash
# EXPECT_RC: 1
# MEANS: 出力に出ない文字を EXPECT_MSG に書くと、走らせる道具の番人 T13 が落ちた
# EXPECT_MSG: ❌ T13
# b90 — 出力に在るべき文字の照合を外すと、走らせる道具の番人が落ちるか
#   守っているもの＝完成の条件 AUDIT-8（期待と違う結果を「期待どおり」と数えない）
#   なぜ要るか＝終了コードの数字だけを照らすと、**守りと関係ない所でエラーが起きて落ちた場合も
#     「期待どおり」になる**（監査 cp29 が指摘・既に在る b51 は判定が裏返っている）。
#   壊し方＝走らせる道具の「出力に EXPECT_MSG が在るか」を見る判定を、常に真にする。
#   期待＝走らせる道具の番人（`--selftest`）の T13 が落ちる（終了コード 1）。
#   ★壊す対象が見つからなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

RB="$ROOT/.claude/tools/run_breaks.py"
guard "$RB"

python3 - "$RB" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    if msg:                                     # 宣言が在れば、出力にその文字を求める\n        return msg in (out or "")'
if old not in s:
    raise SystemExit("[b90] 壊す対象の行が見つからない（出力の照合）")
new = '    if msg:  # b90 が壊した（出力を見ない）\n        return True'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$ROOT/.claude/tools/run_breaks.py" --selftest
finish
