#!/bin/bash
# EXPECT_RC: 1
# MEANS: indicators.json の記録の値を1つ変えると、照らす口が落ちる
# EXPECT_MSG: 欄「範囲」が写す元と違う
# ss1_f8_verify — 記録の値を1つ変えると、照らす口が落ちる（工事 m2c15-single-source-fix-20261023・設計書1・F-8・2026-10-24）
#   守っているもの＝7-6 の F-8（--verify が違い0件で終わりのコード 0。記録の値を1つ変えると0以外）
#   壊し方＝scripts/priority_rebuild/indicators/indicators.json の RSI の範囲の上限を 99 に替える
#   期待＝--verify が「欄「範囲」が写す元と違う」で落ちる（終了コード 1）
source "$(dirname "$0")/lib.sh"

F="$PR/indicators/indicators.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import json, sys
p = sys.argv[1]
d = json.load(open(p, encoding="utf-8"))
r = d["記録"].get("RSI")
if not r or not r.get("範囲"):
    raise SystemExit("[ss1_f8_verify] 壊す対象の RSI の範囲が無い")
r["範囲"][0]["hi"] = 99
open(p, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=1))
PYEOF

measure python3 "$ROOT/.claude/state/indicator_review/gen_indicators_draft.py" --verify
finish
