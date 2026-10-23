#!/bin/bash
# EXPECT_RC: 1
# MEANS: 写しの印の登録から既知答えを外すと、自己テストの番人①（写しの印の登録は既知答えを必ず持つ）が落ちる
# EXPECT_MSG: 写しの印の登録に手計算の既知答えが無い: close vs HILO%
# b182_copy_mark_without_known — 写しの印の登録から既知答えを外すと、自己テストの番人①（写しの印の登録は既知答えを必ず持つ）が落ちる（工事 k4-reference-known-20261011・2026-10-11）
#   守っているもの＝完成の条件の軽い口（selftest_match＝検査3 と写しの印の番人）（observe_diag.py --selftest-match）
#   壊し方＝scripts/priority_rebuild/indicator_reference_diag.py の中の、下の old を new に置き換える（k4_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-match が「写しの印の登録に手計算の既知答えが無い: close vs HILO%」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
#   ★2026-10-22（工事 m2c15-single-source-20261022）＝定義表の行から方向・性質の引数が消えたので、壊す文字から「"反転サイン", "none",」を外した（壊し方と測る物は同じ）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/indicator_reference_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = ', tb=_tb_pos_hilo,\n   # ★K-4（監査 CP60 の修正59）＝定義（Krausz＝前の13本の高値の平均を終値が上抜けたら、21本の安値の平均の線）から導いた既知答え\n   #   ＝1本ごとに 1 上げる足（高値＝終値・安値＝前の終値）では、終値は常に高値の平均の上＝線は安値の平均＝終値 − 11。\n   known=lambda p: [(_up(80), [(-1, (179.0 / 168.0 - 1.0) * 100.0, 1e-9)])], tb_kind="写し")\n'
new = ', tb=_tb_pos_hilo,\n   # ★K-4（監査 CP60 の修正59）＝定義（Krausz＝前の13本の高値の平均を終値が上抜けたら、21本の安値の平均の線）から導いた既知答え\n   #   ＝1本ごとに 1 上げる足（高値＝終値・安値＝前の終値）では、終値は常に高値の平均の上＝線は安値の平均＝終値 − 11。\n   tb_kind="写し")\n'
if s.count(old) != 1:
    raise SystemExit("[b182_copy_mark_without_known] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-match
finish
