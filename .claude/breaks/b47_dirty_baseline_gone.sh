#!/bin/bash
# EXPECT_RC: 1
# MEANS: その検査が落ちた（守りが働いた）
# b47 — 「承認の時点で汚れていた .py」を数えない処理を消すと、番人が落ちるか
#
#   守っているもの＝next_step §6 の138番（設計書 iter="approval-audit-plumbing-20260907" の
#     完成の条件 #8）。
#   何を守るか＝照合A(双方向) は git status の .py を全部 見て、設計書の impl_functions に
#     無ければ落とす。その .py が中で何を呼ぶかは見ない。だから並走している別のセッションが
#     .py を編集中なら、どの設計書でも落ちた（2026-09-06 の実測＝FAIL の10本は、
#     その時点で未コミットだった10本と1本も違わなかった）。
#     承認の瞬間に凍結した基準（<iter>.dirty.json）に在るものは数えない形にした。
#   壊し方＝counts_as_touched から、基準を見る2行を消す。
#   測るもの＝`verify_design_contract.py --self-test`（番人 N18 が この判定を試す）。
#   期待＝壊すと N18 が落ちて終了コードが 1 になる（N19 は通ったまま＝緩めていない）。
#
# ★時間について（b35 の事故の教訓）＝承認のときの打ち切りは 120秒。実測（2026-09-07）＝数秒。
#
# 限界（正直に書く）
#   ①壊すのは判定の2行だけ（基準を作る側＝approve_impl.sh を消す壊し方は、この1本では測れない）
#   ②基準の中身が正しいかは見ない（承認のときに git status から書かれる）
#   ③このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）

source "$(dirname "$0")/lib.sh"

guard "$VERIFY"

python3 - "$VERIFY" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
before = s
s = s.replace(
    '    if rel in baseline:\n'
    '        return False\n'
    '    return not any(rel.endswith(_k) or _k.endswith(rel) for _k in spec)\n',
    '    return not any(rel.endswith(_k) or _k.endswith(rel) for _k in spec)\n')
if s == before:
    raise SystemExit("壊す対象の行が見つからない（b47 の前提が変わった）")
open(p, 'w', encoding='utf-8').write(s)
PYEOF

measure python3 "$VERIFY" --self-test
finish
