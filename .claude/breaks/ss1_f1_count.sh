#!/bin/bash
# EXPECT_RC: 1
# MEANS: indicators.json から記録を1つ消すと、照らす口が「記録が無い」で落ちる
# EXPECT_MSG: 記録が無い
# ss1_f1_count — 記録を1つ消すと、照らす口が落ちる（工事 m2c15-single-source-fix-20261023・設計書1・F-1・2026-10-24）
#   守っているもの＝7-6 の F-1（indicators.json が在り、記録が314種＝INDICATOR_TABLE の301種と別枠の材料13種、1種につき1つ）
#   壊し方＝scripts/priority_rebuild/indicators/indicators.json の記録から RSI を消す
#   期待＝python3 .claude/state/indicator_review/gen_indicators_draft.py --verify が「記録が無い」で落ちる（終了コード 1）
source "$(dirname "$0")/lib.sh"

F="$PR/indicators/indicators.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import json, sys
p = sys.argv[1]
d = json.load(open(p, encoding="utf-8"))
if "RSI" not in d["記録"]:
    raise SystemExit("[ss1_f1_count] 壊す対象の記録 RSI が無い")
del d["記録"]["RSI"]
open(p, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=1))
PYEOF

measure python3 "$ROOT/.claude/state/indicator_review/gen_indicators_draft.py" --verify
finish
