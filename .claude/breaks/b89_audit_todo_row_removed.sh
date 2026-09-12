#!/bin/bash
# EXPECT_RC: 1
# MEANS: 設計書の監査の表から1行 消すと、検出が「手で書き換えられています」で止まった
# EXPECT_MSG: AUDITTODO
# b89 — 設計書の監査の指摘の表を手で書き換えると、検出が止まるか
#   守っているもの＝完成の条件 AUDIT-7（監査の指摘が設計書に機械で載っている）
#   なぜ要るか＝まこさん指示 2026-09-11「ヌケモレ発生しそうなので、自動生成で対応できない？」。
#     私（CC）が手で読んで報告したとき、別枠4件を1行も出さなかった。
#   壊し方＝設計書の監査の表の1行を書き換える。
#   期待＝`gen_acceptance.py --verify` が 0 以外で止まる。
#   ★壊す対象が見つからなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

DESIGN="$ROOT/.claude/state/acceptance.md"
guard "$DESIGN"

python3 - "$DESIGN" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '| 直すことの一覧（まこさんへ） | C-1 |'
if old not in s:
    raise SystemExit("[b89] 壊す対象の行が見つからない: " + old)
new = '| 直すことの一覧（まこさんへ） | C-1（b89 が書き換えた） |'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$ROOT/.claude/tools/gen_acceptance.py" --verify
finish
