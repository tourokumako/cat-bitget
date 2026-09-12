#!/bin/bash
# EXPECT_RC: 1
# MEANS: 帯の引き方を役割の直書きに戻すと、T39③ が「系統を書き替えても帯が変わらない」で落ちた
# EXPECT_MSG: T39
# b85 — 帯の引き方を役割の直書きに戻すと、法則を読まなくなるか
#   守っているもの＝完成の条件 AUDIT-1（法則 R1・R3 を書き替えると帯の材料が変わる）
#   出どころ＝監査 cp35 の Critical C-1（5枠のうち帯だけが法則を読んでいなかった）
#   壊し方＝帯を引く行を、法則の系統を渡さない形（役割の名前だけ）に戻す。
#   期待＝自己テスト T39 が落ちる（終了コード 1）。
#   ★壊す対象が見つからなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

GEN="$PR/engine_tuner_gen.py"
guard "$GEN"

python3 - "$GEN" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    m_b, draw["B"] = _material_for_lineage("location", lins_b, r_b, tfs, table, tf_ok=upper)'
if old not in s:
    raise SystemExit("[b85] 壊す対象の行が見つからない: " + old)
new = ('    m_b, draw["B"] = _ranked_material_at("location", r_b, tfs, table, tf_ok=upper)'
       '  # b85 が壊した（法則を読まない）')
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/engine_tuner_gen.py" --selftest
finish
