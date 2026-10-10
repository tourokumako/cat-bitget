#!/bin/bash
# EXPECT_RC: 1
# MEANS: 本走を呼ぶ口（_selftest_run）を、本走が止まるとプログラムごと終わる形に戻すと、短い口の T50① が落ちる
# EXPECT_MSG: ❌ T50: ①
# b159_selftest_run_passthrough — 本走を呼ぶ口（_selftest_run）を、本走が止まるとプログラムごと終わる形に戻すと、短い口の T50① が落ちる（工事 g2-table-range-source-20261010・2026-10-10）
#   守っているもの＝完成の条件 #1（短い口 --selftest-stop-note の T50①＝本走が途中で止まったら、理由の行つきで知らせる）
#   壊し方＝engine_tuner_gen.py の _selftest_run の中の、下の old を new に置き換える（SystemExit をそのまま通す＝直す前と同じ動き）。
#   期待＝engine_tuner_gen.py --selftest-stop-note が「❌ T50: ①」を出して落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

G="$PR/engine_tuner_gen.py"
guard "$G"

python3 - "$G" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    except SystemExit:\n        raise _RunStopped(_stop_note("".join(b.getvalue() for b in bufs))) from None\n'
new = '    except SystemExit:\n        raise\n'
if s.count(old) != 1:
    raise SystemExit("[b159_selftest_run_passthrough] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$G" --selftest-stop-note
finish
