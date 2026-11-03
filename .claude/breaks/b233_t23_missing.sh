#!/bin/bash
# EXPECT_RC: 1
# MEANS: 確認の道具の CHECKS から T23 を外すと、T23 が未作と出て、終わりのコードが 1 になる
# EXPECT_MSG: 未作
# b233_t23_missing — T23 の測る処理が無いと、確認の道具が通さない（工事 m2c15-outside-record-20261102）
#   守っているもの＝7-6 の F-6 と F-7（測るコマンドは --test T23）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$ROOT/.claude/tools/check_one_path.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '"T23": t23, "T24": t24, '
new = '"T24": t24, '
if s.count(old) != 1:
    raise SystemExit("[b233_t23_missing] 壊す対象（CHECKS の T23）が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$F" --test T23
finish
