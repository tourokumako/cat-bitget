#!/bin/bash
# EXPECT_RC: 1
# MEANS: その検査が落ちた（守りが働いた）
# b53 — 検査5 の「枠づくり」と「使い回しの鍵の時刻」を同時に直す前へ戻すと、番人が落ちるか
#
#   守っているもの＝設計書 iter="insp5-frame-and-table-tidy-20260908" の完成の条件 #1
#     （next_step.md §6 の134番＝観察の検査5 が途中で例外を出して落ちる）。
#   何を守るか＝①1m・3m の枠を、1分足の元データから作る（直す前は5分足を入れ直していた）
#     ②重い計算の使い回しの鍵に、並んでいる時刻の指紋を入れる（直す前は本数と終値だけ）。
#   ★なぜ2つを同時に戻すか（Web Claude の3回目の指摘・重い1）＝片方だけ戻しても落ちないため。
#     枠だけ戻す → 鍵に時刻が入っているので、1分の枠と3分の枠は鍵が変わって計算し直す＝落ちない。
#     鍵だけ外す → 枠が直っているので、1分は本物の1分足・3分はそれを作り直したもの＝
#                  本数も終値も違うので鍵が変わる＝落ちない。
#     2つ同時に戻したときだけ、落ちた噛み合わせ（本数 317,376 の枠に 528,960 の列を当てる）が再現する。
#   壊し方＝insp5_frame の枝分かれを1行に戻し、_cyc の鍵から時刻の指紋を外す。
#   測るもの＝`observe_diag.py --selftest-insp5`（番人 T-g と T-j が この2つを試す）。
#   期待＝壊すと T-g（1m の枠の本数が5分足以下）と T-j（列の長さと枠の長さが違う）が落ちて 1 になる。
#
# ★時間について＝承認のときの打ち切りは 120秒。軽い口だけを走らせる（全部の番人は 1分48秒 かかるので使わない）。
#
# 限界（正直に書く）
#   ①T-h も道連れで落ちる（鍵を外すため）＝どの番人が落ちたかまでは終了コードから分からない
#   ②壊すのは2か所だけ（検査5 の呼び出し側を書き替える壊し方は、この1本では測れない）
#   ③このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）

source "$(dirname "$0")/lib.sh"

OBS="$PR/observe_diag.py"
guard "$OBS"

python3 - "$OBS" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()

frame_new = (
    '    if tf == "5m":\n'
    '        src = span\n'
    '    elif tf in SUB_5M_TF:                                # 5分足より短い足＝1分足の元データから作る\n'
    '        if one is None:\n'
    '            one = load_1m(span.index[0], span.index[-1])\n'
    '        src = one if tf == "1m" else _resample(one, TF_RULE[tf])\n'
    '    else:\n'
    '        src = _resample(span, TF_RULE[tf])\n')
frame_old = '    src = span if tf == "5m" else _resample(span, TF_RULE[tf])\n'

key_new = (
    '    sig = (len(d), hashlib.md5(d.close.to_numpy(dtype=float).tobytes()).hexdigest(),\n'
    '           hashlib.md5(np.ascontiguousarray(d.index.values).tobytes()).hexdigest())\n')
key_old = '    sig = (len(d), hashlib.md5(d.close.to_numpy(dtype=float).tobytes()).hexdigest())\n'

for name, new, old in (("枠づくり", frame_new, frame_old), ("使い回しの鍵", key_new, key_old)):
    if new not in s:
        raise SystemExit(f"壊す対象の行が見つからない（b53 の前提が変わった）: {name}")
    s = s.replace(new, old)
open(p, 'w', encoding='utf-8').write(s)
PYEOF

# ★2026-09-08（監査 cp31 の Critical 1）＝5分足のパスを書かない。
#   番人は observe_diag.py の定数 BARS_CSV（5分足の正本）を自分で読む。
#   直す前＝ここに同じファイル名が書き写してあり、取り足して名前が変わると古いものを指したままになった。
measure python3 "$OBS" --selftest-insp5
finish
