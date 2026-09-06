#!/bin/bash
# b30 — 節の実在を確かめる処理を空返しにすると、番人 Q11 が落ちるか（完成の条件 #4）
#   守っているもの＝監査 cp23 の X-9「依頼書が指した §38 が存在しなかった」
#   ★このプログラムの終了コードでは測れない（Q6 が別の理由で落ちているため）。
#   Q11 の行が出るかどうかで測る。
source "$(dirname "$0")/lib.sh"

T="$PR/gen_audit_request.py"
guard "$T"

# 壊す＝節の実在確認を、何も返さない形にする
python3 - "$T" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
s = s.replace('    out: list[str] = []\n    for ln in body.splitlines():',
              '    out: list[str] = []\n    return out\n    for ln in body.splitlines():')
open(p, 'w', encoding='utf-8').write(s)
PYEOF

# 測る＝Q11 の ❌ が出たら 1（壊れたことを検出できた）
if python3 "$PR/gen_audit_request.py" --selftest 2>&1 | grep -q "Q11:"; then
    MEASURED=1
else
    MEASURED=0
fi
finish
