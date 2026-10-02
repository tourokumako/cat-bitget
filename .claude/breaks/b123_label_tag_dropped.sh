#!/bin/bash
# EXPECT_RC: 1
# MEANS: 順位表の各行に札の版を書かなくすると、自己検査⑬が「順位表か落ちた候補に、札の版が書かれていない」で落ちた
# EXPECT_MSG: ❌ ⑬
# b123 — regime_r9_diag.write_outputs が順位表の行に札の版を書かないと、⑬が落ちるか（M2-F-6d・2026-09-29）
#   守っているもの＝完成の条件 #3（どの版の札で作った順位表かを、順位表の側に残す＝まこさん決定 2026-09-28 の構造の文の3つ目）
#   壊し方＝`    rows = [dict(r, 札の版=tag_l) for r in rows]` を `    pass` にする。
#   期待＝regime_r9_diag.py --selftest の⑬が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

DIAG="$PR/regime_r9_diag.py"
guard "$DIAG"

python3 - "$DIAG" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    rows = [dict(r, 札の版=tag_l) for r in rows]\n'
if s.count(old) != 1:
    raise SystemExit("[b123] 壊す対象の行が1か所でない: " + old.strip())
new = '    pass  # b123 が壊した（順位表に札の版を書かない）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$DIAG" --selftest
finish
