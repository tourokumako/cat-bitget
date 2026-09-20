#!/bin/bash
# EXPECT_RC: 1
# MEANS: 法則 R2 の「除く部品」を読まなくすると、帯の幅に指標を選んだ束が審査 G7 で拒否され、自己テストが落ちた
# EXPECT_MSG: [レシピ拒否 G7] 場面ごとの相場の法則（range）に反する: R2: 同じ系統が重なっている＝ボラ 2本
# b88 — 法則 R2 が帯の幅の枠を系統の数から外す処理が消えると、検査が落ちるか
#   守っているもの＝完成の条件 #4（帯の幅に指標を選んだ束が、法則 R2 でも R6 でも審査 G7 を通る）
#   期待＝自己テストが落ちる（終了コード 1）。
#   ★出る文が「❌ T45」ではない理由（2026-09-19 に実物で確かめた）＝審査が投げる RecipeError は
#     SystemExit を継承している（engine_tuner_exec.py の class RecipeError(SystemExit)）。
#     T45 の except Exception は SystemExit を捕まえないので、自己テストは T45 の ❌ を出す前に
#     その場で落ち、拒否の文だけが出力の最後に残る。
#   ★壊す対象が見つからなければ止まる（黙って壊さない）。
#
# ★2026-09-19 新設（設計書 m2c-width-and-stage-candidates-20260918・まこさん決定「案BでOK」）。
#   なぜ＝帯の幅の指標は3件とも系統が ボラ。ボラの1本は法則 R6（低ボラ）が使っているので、
#     R2（構造・位置 を除く系統は1本まで）が帯の幅を数から外さないと、束は必ず落ちる
#     （2026-09-19 に実物の審査を読んで確かめた）。この道が消えたら落ちる形にする。
source "$(dirname "$0")/lib.sh"

EXE="$PR/engine_tuner_exec.py"
guard "$EXE"

python3 - "$EXE" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = "            _exp = j.get(\"除く部品\") or {}\n"
if s.count(old) != 1:
    raise SystemExit(f"[b88] 壊す対象の行が1つに定まらない（{s.count(old)} 件）")
new = "            _exp = {}                                  # b88 が壊した（除く部品を読まない）\n"
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/engine_tuner_gen.py" --selftest
finish
