#!/bin/bash
# EXPECT_RC: 1
# MEANS: 観察の道具の _regime_labels に札の式を書き写すと、自己検査 T6 が「札を作る場所を呼んでいない・式が書き写されている」で落ちた
# EXPECT_MSG: ❌ T6
# b122 — observe_diag._regime_labels が regime_label を呼ばずに式（中央値で切る）を持つと、T6 が落ちるか（M2-F-6d・2026-09-29）
#   守っているもの＝完成の条件 #1（札を作る場所が1つ＝まこさん決定 2026-09-28「札を作る場所を1つにすること」）
#   壊し方＝`    return rl.labels_at_bars(win, n)` を、中央値で切る式の写しに置き替える。
#   期待＝regime_label.py --selftest の T6 が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

OBS="$PR/observe_diag.py"
guard "$OBS"

python3 - "$OBS" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    return rl.labels_at_bars(win, n)\n'
if s.count(old) != 1:
    raise SystemExit("[b122] 壊す対象の行が1か所でない: " + old.strip())
new = ('    c = win["close"].astype(float).diff().abs()  # b122 が壊した（札の式を写した）\n'
       '    return {"強さ": (c >= c.median(), c.notna()), "向き": (c > 0, c.notna()), "大きさ": (c >= c.median(), c.notna())}\n')
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/regime_label.py" --selftest
finish
