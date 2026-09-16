#!/bin/bash
# EXPECT_RC: 1
# MEANS: 設定の欄を読まない形にすると、T43 が「時間足を1本に絞っても候補が絞られない」で落ちた
# EXPECT_MSG: ❌ T43
# b94 — 設定の欄 `stage_limits` を読まない形にすると、検査が落ちるか
#   守っているもの＝完成の条件 AUDIT-2（設定の欄 stage_limits が読まれている）
#   なぜ要るか（監査 cp36 の M-1）＝この欄は 2026-09-11 に作ったのに、読むコードが1行も
#     無かった。書いても黙って無視される状態だった。
#   壊し方＝`stage_limits_of` が、設定を読まずに「何も絞らない」を返す形にする。
#   期待＝自己テスト T43 が落ちる（終了コード 1）。
#   ★壊す対象が1つに定まらなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

GEN="$PR/engine_tuner_gen.py"
guard "$GEN"

python3 - "$GEN" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    all_ = limits.get("stage_limits") or {}\n'
if s.count(old) != 1:
    raise SystemExit(f"[b94] 壊す対象の行が1つに定まらない（{s.count(old)} 件）")
new = '    all_ = {}  # b94 が壊した（設定の欄を読まない）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/engine_tuner_gen.py" --selftest
finish
