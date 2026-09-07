#!/bin/bash
# b34 — 定義表に無い材料の名前が源3（恒等レシピ）に混じると、自己検査が落ちるか
#   守っているもの＝監査 cp24 の §6-6「材料名の実在テスト」（完成の条件 #5・#6）
#   壊し方＝源3 を拾う処理から「昔からの列を外す」判定を消す
#          ＝BB・レンジ幾何（定義表に無い名前）がまた混じる。
#   期待＝壊すと gen_indicator_switch.py --selftest が T10 で落ちる（終了コード 1）。
source "$(dirname "$0")/lib.sh"

T="$PR/gen_indicator_switch.py"
guard "$T"

# 壊す＝昔からの列を外す判定を消す（直す前の形に戻す）
python3 - "$T" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
before = s
s = s.replace('if isinstance(f, str) and "legacy_col" not in o:',
              'if isinstance(f, str):')
if s == before:
    raise SystemExit("壊す対象の行が見つからない（b34 の前提が変わった）")
open(p, 'w', encoding='utf-8').write(s)
PYEOF

# 測る＝自己検査が落ちたら 1（壊れたことを検出できた）
measure python3 "$PR/gen_indicator_switch.py" --selftest
finish
