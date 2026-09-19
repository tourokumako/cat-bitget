#!/bin/bash
# EXPECT_RC: 1
# MEANS: 候補の絞りに名前の一覧を戻すと、T40③-1 が「許される指標が候補に出ていない」で落ちた
# EXPECT_MSG: ❌ T40③-1
# b86 — 印より狭い名前の絞りを戻すと、候補の出どころの検査が落ちるか
#   守っているもの＝完成の条件 #1（候補が印と法則と役割と時間足と標本だけで決まる）
#   期待＝自己テスト T40③-1 が落ちる（終了コード 1）。
#   ★壊す対象が見つからなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

# ★2026-09-19（設計書 m2c-width-and-stage-candidates-20260918・まこさん承認）に書き直した。
#   直す前＝「元データで絞る2行を消す」形だった（絞りが在ることを前提にした壊し方）。
#   その2行は、この工事で **本体から消した**（印より狭い絞りだったため）。
#   ＝壊し方を逆にする。**絞りを戻す**（元データの語に無い指標を `continue` で落とす行を差し込む）。
#   すると T40③-1「印と法則と役割と時間足で許される指標が、全部 候補に出ているか」が落ちる。
#   ★経緯（残す）＝2026-09-12 に壊し方を5回 作り直した（法則の側を壊すと手前で止まる・
#     候補が0件になると例外で判定に届かない、など）。その記録は git の履歴に在る。
GEN="$PR/engine_tuner_gen.py"
guard "$GEN"

python3 - "$GEN" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
anchor = "        # ★2026-09-16（監査 cp36 の M-1）＝設定の欄 `stage_limits.<段>.families` で さらに絞る。\n"
if s.count(anchor) != 1:
    raise SystemExit(f"[b86] 壊す対象の行が1つに定まらない（{s.count(anchor)} 件）")
inject = (
    "        if spec_c[\"families\"] or spec_c[\"lineages\"]:   # b86 が戻した（印より狭い名前の絞り）\n"
    "            if not (fam in spec_c[\"families\"]\n"
    "                    or iref.FAMILY_LINEAGE[fam][\"k\"] in spec_c[\"lineages\"]):\n"
    "                continue\n"
)
open(p, 'w', encoding='utf-8').write(s.replace(anchor, inject + anchor, 1))
PYEOF

measure python3 "$PR/engine_tuner_gen.py" --selftest
finish
