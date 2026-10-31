#!/bin/bash
# EXPECT_RC: 1
# MEANS: 記録 RSI の名前の行だけを（ファイルの書き方を変えずに）書き替えると、git diff が「要素の定義表」の1行のほかの違いを出し、完成の条件4が落ちる
# EXPECT_MSG: RSI_壊した
# b212_records_changed — 要素の定義表のほかの所（記録と一番外の4つの鍵）が1文字でも変わると、完成の条件4が落ちる（工事 m2c15-indicator-structure-20261031・2026-10-31）
#   守っているもの＝7-6 の F-1 の条件4（測るコマンドは、条件4のコマンドと同じ）
#   ★json を読み直して書くと書き方（字下げ）が変わり、git diff が別の理由で落ちるので、文字の置き換えで1行だけ壊す。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$PR/indicators/indicators.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '\n   "名前": "RSI",\n'
if s.count(old) != 1:
    raise SystemExit("[b212_records_changed] 壊す対象（記録 RSI の名前の行）が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, '\n   "名前": "RSI_壊した",\n'))
PYEOF

measure git -C "$SDK" diff --exit-code -I '^ "要素の定義表": ' 40a456ac -- scripts/priority_rebuild/indicators/indicators.json
finish
