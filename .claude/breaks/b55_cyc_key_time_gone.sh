#!/bin/bash
# EXPECT_RC: 1
# MEANS: その検査が落ちた（守りが働いた）
# b55 — 重い計算の使い回しの鍵から「時刻の指紋」だけを外すと、番人が落ちるか
#
#   守っているもの＝設計書 iter="insp5-frame-and-table-tidy-20260908" の完成の条件 #2
#     （next_step.md §6 の134番の②）。
#   何を守るか＝_cyc の鍵に、並んでいる時刻の指紋を入れる。直す前の鍵は「本数」と「終値」の2つだけで、
#     終値が同じで時刻だけ違う枠を続けて渡すと、前の結果がそのまま返っていた。
#   壊し方＝_cyc の鍵を、直す前の2つ組に戻す。
#   測るもの＝`observe_diag.py --selftest-insp5`（番人 T-h が この鍵を直に試す）。
#   期待＝壊すと T-h（終値が同じで時刻だけ違う2つに、同じ値を返した）が落ちて 1 になる。
#
# ★時間について＝承認のときの打ち切りは 120秒。軽い口だけを走らせる。
#
# 限界（正直に書く）
#   ①鍵を外しても、枠が直っていれば T-g と T-j は落ちない（1分足と3分足で本数も終値も違うため）
#     ＝この1本が測るのは T-h だけ
#   ②このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）

source "$(dirname "$0")/lib.sh"

OBS="$PR/observe_diag.py"
guard "$OBS"

python3 - "$OBS" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
new = ('    sig = (len(d), hashlib.md5(d.close.to_numpy(dtype=float).tobytes()).hexdigest(),\n'
       '           hashlib.md5(np.ascontiguousarray(d.index.values).tobytes()).hexdigest())\n')
old = '    sig = (len(d), hashlib.md5(d.close.to_numpy(dtype=float).tobytes()).hexdigest())\n'
if new not in s:
    raise SystemExit("壊す対象の行が見つからない（b55 の前提が変わった）")
open(p, 'w', encoding='utf-8').write(s.replace(new, old))
PYEOF

measure python3 "$OBS" --selftest-insp5
finish
