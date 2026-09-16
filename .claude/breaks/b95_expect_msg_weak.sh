#!/bin/bash
# EXPECT_RC: 1
# MEANS: 宣言を弱い文字に戻すと、走らせる道具の番人 T15 が「❌ で始まらない宣言を名指しできない」で落ちた
# EXPECT_MSG: ❌ T15
# b95 — 宣言を数える口を壊すと、走らせる道具の番人が落ちるか
#   守っているもの＝完成の条件 AUDIT-3（自己テストを測る壊すプログラムの EXPECT_MSG が、全部 ❌ で始まる）
#   なぜ要るか（監査 cp36 の M-2）＝直す前の宣言は「T24」のように、壊していない正常な出力にも
#     出る文字だった。だから別の理由で落ちても「期待どおり」に数えられた。
#   壊し方＝数える口（`lint_expect`）が、いつも空の並びを返す形にする＝1本も名指ししない。
#   期待＝走らせる道具の番人（`--selftest`）の T15 が落ちる（終了コード 1）。
#   ★壊す対象が1つに定まらなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

RB="$ROOT/.claude/tools/run_breaks.py"
guard "$RB"

python3 - "$RB" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '        if not msg.startswith("❌"):\n            bad.append(name)\n'
if s.count(old) != 1:
    raise SystemExit(f"[b95] 壊す対象の行が1つに定まらない（{s.count(old)} 件）")
new = '        pass  # b95 が壊した（❌ で始まらない宣言を名指ししない）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$ROOT/.claude/tools/run_breaks.py" --selftest
finish
