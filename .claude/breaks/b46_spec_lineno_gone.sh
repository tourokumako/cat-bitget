#!/bin/bash
# EXPECT_RC: 1
# MEANS: その検査が落ちた（守りが働いた）
# b46 — 関数の定義の行を集める処理を消すと、番人が落ちるか
#
#   守っているもの＝next_step §6 の93番（設計書 iter="approval-audit-plumbing-20260907" の
#     完成の条件 #7）。監査 cp6 の P-2。
#   何を守るか＝設計書に書く行番号を、人が手で写さない形にした。
#     直す前＝`--write` は公開する関数・定数・コマンドの旗だけを書き出し、定義の行番号を
#     出さなかった。だから CC が grep の出力を手で写し、実装のたびにずれた
#     （同じずれは相場の法則 R7 の引用でも2回 起きている＝§6 の155番）。
#   壊し方＝spec_from_impl の戻り値から def_lines を外す。
#   測るもの＝`verify_design_contract.py --self-test`（番人 N20 が この表を試す）。
#   期待＝壊すと N20 が落ちて終了コードが 1 になる。
#
# ★時間について（b35 の事故の教訓）＝承認のときの打ち切りは 120秒。実測（2026-09-07）＝数秒。
#
# 限界（正直に書く）
#   ①壊すのは戻り値の1か所だけ（書き出す側を消す壊し方は、この1本では測れない）
#   ②行番号が正しいかは見ない（番人が見本の .py で照らす）
#   ③このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）

source "$(dirname "$0")/lib.sh"

guard "$VERIFY"

python3 - "$VERIFY" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
before = s
s = s.replace(
    '            # ★2026-09-07（93番）＝関数の名前 → 定義の行。設計書はここを引く（手で写さない）。\n'
    '            "def_lines": dict(sorted(def_lines.items()))}\n',
    '            }\n')
if s == before:
    raise SystemExit("壊す対象の行が見つからない（b46 の前提が変わった）")
open(p, 'w', encoding='utf-8').write(s)
PYEOF

measure python3 "$VERIFY" --self-test
finish
