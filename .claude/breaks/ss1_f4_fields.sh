#!/bin/bash
# EXPECT_RC: 1
# MEANS: indicators.json の記録から欄を1つ消すと、照らす口が「23の欄と違う」で落ちる
# EXPECT_MSG: 欄が 4-8 の23の欄と違う
# ss1_f4_fields — 欄を1つ消すと、照らす口が落ちる（工事 m2c15-single-source-fix-20261023・設計書1・F-4・2026-10-24）
#   守っているもの＝7-6 の F-4（記録が 4-8 の23の欄を全部持つ）
#   壊し方＝scripts/priority_rebuild/indicators/indicators.json の RSI の記録から、欄「mako」を消す
#   期待＝--verify が「欄が 4-8 の23の欄と違う」で落ちる（終了コード 1）
source "$(dirname "$0")/lib.sh"

F="$PR/indicators/indicators.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import json, sys
p = sys.argv[1]
d = json.load(open(p, encoding="utf-8"))
r = d["記録"].get("RSI")
if not r or "mako" not in r:
    raise SystemExit("[ss1_f4_fields] 壊す対象の欄 RSI の mako が無い")
del r["mako"]
open(p, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=1))
PYEOF

measure python3 "$ROOT/.claude/state/indicator_review/gen_indicators_draft.py" --verify
finish
