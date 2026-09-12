#!/bin/bash
# EXPECT_RC: 1
# MEANS: §2.2 の囲みを作る道具が「語が正本に1件も当たらない」で止まった（守りが働いた）
# EXPECT_MSG: 正本と合いません
# b88 — §2.2 の候補の元データに、正本に無い指標の名前を1件 書くと止まるか
#   守っているもの＝完成の条件 AUDIT-6（§2.2 の候補の一覧が、正本の指標の名前だけで書かれている）
#   なぜ要るか＝まこさん指示 2026-09-11「手書きで書き換えられないようにプログラムが読める
#     対応付けをすればいいのでは？」。正本に無い名前を私（CC）が書けない形にした。
#   壊し方＝元データの段1 の語に、正本に無い文字（帯内位置）を1件 足す。
#     ★`帯内位置` は正本に無い（正本は `レンジ幾何` の列 `帯内位置%`）。
#   期待＝`gen_regime_kb.py --write stage` が 0 以外で止まる（語が正本に1件も当たらない）。
#         壊さなければ 0 で通る。
source "$(dirname "$0")/lib.sh"

CANDS="$SDK/.claude/ratchet/m2_stage_candidates.json"
MILE="$SDK/.claude/ratchet/engine_tuner_milestones2.md"
guard "$CANDS" "$MILE"

# 壊す＝正本に無い語を1件 足す
python3 - "$CANDS" <<'PYEOF'
import json
import sys
p = sys.argv[1]
d = json.loads(open(p, encoding='utf-8').read())
d["段"][0]["語"].append({"§2.2": "（b88 が足した・正本に無い語）",
                         "探す": "帯内位置", "当て方": "完全"})
open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
PYEOF

# 測る＝止まれば 0 以外（壊れたことを検出できた）
measure python3 "$ROOT/.claude/tools/gen_regime_kb.py" --write stage
finish
