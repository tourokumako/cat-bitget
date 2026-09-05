#!/bin/bash
# b26 — impl_functions の「触る関数4件」から1件を抜くと、照合A が NG を出すか（完成の条件 #8・まこさんの決定10）
#   いまの設計書の写しを一時の場所に作り、契約の impl_functions から contract_for_freeze を抜く。
#   同じ1件を抜いた凍結（<名前>.frozen.json）を並べて照合する。
#   照合の出力に「設計書に書いていない関数を触った → contract_for_freeze」（照合A）が在れば 1。
#   ★限界（設計書 §9 の O）＝照合A は git の差分で触った関数を集めるので、実装の差分が commit された後は
#     走らない＝そのときは 0 を返す。承認（commit の前）で走らせて記録する。
#   ★b24 と同じ直し（2026-09-05）＝LC_ALL=C・自分の stderr をファイルに落として ASCII で出す・
#     照合の出力を流さない・自分が出す行は ASCII だけ。本物のファイルは1つも触らない。
export LC_ALL=C
TMPD="$(mktemp -d)"
ERRF="$TMPD/stderr.txt"
exec 2>"$ERRF"
source "$(dirname "$0")/lib.sh"

MD="$ROOT/.claude/state/acceptance.md"
python3 - "$MD" "$TMPD/x.md" "$TMPD/x.frozen.json" <<'PYEOF'
import json, re, sys
src = open(sys.argv[1], encoding="utf-8").read()
m = re.search(r"(## 10｜DESIGN_CONTRACT.*?```json\n)(\{.*?\n\})(\n```)", src, re.S)
if m is None:
    sys.exit(9)
d = json.loads(m.group(2))
fz = d["impl_functions"]
for k in fz:
    fz[k] = [x for x in fz[k] if x != "contract_for_freeze"]
new = src[:m.start()] + m.group(1) + json.dumps(d, ensure_ascii=False, indent=2) + m.group(3) + src[m.end():]
open(sys.argv[2], "w", encoding="utf-8").write(new)
open(sys.argv[3], "w", encoding="utf-8").write(json.dumps(fz, ensure_ascii=False, indent=1))
PYEOF
RCP=$?
if [ "$RCP" -ne 0 ]; then echo "copy_failed rc=$RCP"; rm -rf "$TMPD"; MEASURED=0; finish; fi

python3 "$VERIFY" "$TMPD/x.md" > "$TMPD/out.txt" 2>&1
RC=$?
grep -q "contract_for_freeze" "$TMPD/out.txt"
HIT1=$?
grep -q "設計書に書いていない関数を触った" "$TMPD/out.txt"
HIT2=$?
OUTB=$(wc -c < "$TMPD/out.txt" | tr -d ' ')
ERRB=$(wc -c < "$ERRF" | tr -d ' ')
ERRHEAD=$(od -An -c "$ERRF" | head -2 | tr -s ' ' | tr '\n' ' ')
echo "verify rc=$RC hitA=$HIT2 hitName=$HIT1 (0=found) out_bytes=$OUTB stderr_bytes=$ERRB stderr_head=[$ERRHEAD]"
rm -rf "$TMPD"

if [ "$HIT1" -eq 0 ] && [ "$HIT2" -eq 0 ] && [ "$RC" -ne 0 ]; then MEASURED=1; else MEASURED=0; fi
finish
