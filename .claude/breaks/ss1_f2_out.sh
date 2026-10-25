#!/bin/bash
# EXPECT_RC: 1
# MEANS: 写すプログラムの書く先を作業場の下書きの置き場に戻すと、F-2 の grep が当たって落ちる
# EXPECT_MSG: indicators_draft
# ss1_f2_out — 書く先を作業場に戻すと、F-2 の照らしが落ちる（工事 m2c15-single-source-fix-20261023・設計書1・F-2・2026-10-24）
#   守っているもの＝7-6 の F-2（写すプログラムが作業場の下書きの置き場に書かない）
#   壊し方＝.claude/state/indicator_review/gen_indicators_draft.py の OUT の行を、作業場の下書きの置き場に替える
#   期待＝! grep -n '"indicators_draft' …（CP88 の修正13 で、閉じの引用符を外した）が、当たった行を出して落ちる（終了コード 1）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$ROOT/.claude/state/indicator_review/gen_indicators_draft.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
old = 'OUT = PR / "indicators" / "indicators.json"'
new = 'OUT = HERE / "indicators_draft" / "indicators.json"'
if s.count(old) != 1:
    raise SystemExit("[ss1_f2_out] 壊す対象の文字が1か所でない")
open(p, "w", encoding="utf-8").write(s.replace(old, new, 1))
PYEOF

measure bash -c "! grep -n '\"indicators_draft' \"$F\""
finish
