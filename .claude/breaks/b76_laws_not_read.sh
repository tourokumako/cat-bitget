#!/bin/bash
# EXPECT_RC: 1
# MEANS: 法則ファイルから系統を消すと、帯の枠が引けず T39① が落ちた（組む側が法則を読んでいる証拠）
# EXPECT_MSG: T39①
# b76 — 法則ファイルを読まずに組む形へ壊すと、帯の枠が引けなくなるか
#   守っているもの＝完成の条件 AUDIT-1（法則を1件 変えると、組まれる束が変わる）
#   壊し方＝法則 R1・R3 の「機械が読む判定」から系統（構造・位置）を消す。
#     ★組む側は `_law_lineages(laws, "R1")` で系統を読む。空になれば帯の材料を引けない。
#   期待＝自己テスト T39① が『いまの法則で帯の材料が引けない』で落ちる（終了コード 1）。
source "$(dirname "$0")/lib.sh"

LAWS="$SDK/.claude/ratchet/regime_laws.json"
guard "$LAWS"

# 壊す＝R1・R3 の系統の名指しを空にする
python3 - "$LAWS" <<'PYEOF'
import json
import sys
p = sys.argv[1]
d = json.loads(open(p, encoding='utf-8').read())
n = 0
for law in (d.get("法則") or []):
    if not isinstance(law, dict) or law.get("番号") not in ("R1", "R3"):
        continue
    jd = law.get("機械が読む判定") or {}
    sel = jd.get("数える部品") or {}
    if "系統" in sel:
        sel["系統"] = []
        n += 1
if n == 0:
    raise SystemExit("[b76] R1・R3 の系統の欄が見つからない（壊せていない）")
open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=1) + "\n")
PYEOF

# 測る＝自己テストが落ちれば 0 以外
measure python3 "$PR/engine_tuner_gen.py" --selftest
finish
