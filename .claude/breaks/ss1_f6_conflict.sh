#!/bin/bash
# EXPECT_RC: 1
# MEANS: indicators.json の食い違いの記録を1つ消すと、照らす口が落ちる
# EXPECT_MSG: 欄「食い違いの記録」が写す元と違う
# ss1_f6_conflict — 食い違いの記録を1つ消すと、照らす口が落ちる（工事 m2c15-single-source-fix-20261023・設計書1・F-6・2026-10-24）
#   守っているもの＝7-6 の F-6（置き場どうしで違う値が1つの値になり、選ばなかった側が食い違いの記録に在る）
#   壊し方＝scripts/priority_rebuild/indicators/indicators.json の、食い違いの記録が在る最初の種類の記録を空にする
#   期待＝--verify が「欄「食い違いの記録」が写す元と違う」で落ちる（終了コード 1）
source "$(dirname "$0")/lib.sh"

F="$PR/indicators/indicators.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import json, sys
p = sys.argv[1]
d = json.load(open(p, encoding="utf-8"))
hit = next((f for f, r in sorted(d["記録"].items()) if r.get("食い違いの記録")), None)
if hit is None:
    raise SystemExit("[ss1_f6_conflict] 食い違いの記録が在る種類が無い")
d["記録"][hit]["食い違いの記録"] = []
open(p, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=1))
PYEOF

measure python3 "$ROOT/.claude/state/indicator_review/gen_indicators_draft.py" --verify
finish
