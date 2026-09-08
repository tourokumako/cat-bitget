#!/bin/bash
# EXPECT_RC: 1
# MEANS: その検査が落ちた（守りが働いた）
# b62 — 指紋の照合を先頭8文字だけに緩めると、番人が落ちるか
#
#   守っているもの＝設計書 iter="insp5-path-and-tidy-head-20260908" の完成の条件 #5。
#   何を守るか＝印と いまのコードの指紋を、丸ごと照らすこと。
#     監査 cp31 が check_fingerprint を5通りに壊したところ、2通りが生き残った（別枠 A）。
#     ①ハッシュ値を先頭8文字だけで比べる ②中の「印の対象一覧を狭めない」検査を外す。
#     ＝それまでの番人2件が守っていたのは「一致で 0」「食い違いで 1」の2つだけだった。
#   壊し方＝照合を `now[:8] != fp[:8]` に緩める。
#   測るもの＝enforce_h2_pass.py --selftest（足した番人「先頭8文字だけが同じ印は通さない」が見る）。
#   期待＝緩めると落ちて 1 になる。
#
# 限界（正直に書く）
#   ①監査が挙げたもう1つの壊し方（必須ファイルの検査を外す）は、別の番人が見る
#     （この壊すプログラムでは測らない）
#   ②印そのものを手で偽造されたら見抜けない（H2・G2 と同じ限界）
#   ③このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）

source "$(dirname "$0")/lib.sh"

HOOKP="$ROOT/.claude/hooks/enforce_h2_pass.py"
guard "$HOOKP"

python3 - "$HOOKP" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
new = '''    now = fingerprint(files)
    if now != fp:
'''
old = '''    now = fingerprint(files)
    if now[:8] != fp[:8]:
'''
if new not in s:
    raise SystemExit("壊す対象の行が見つからない（b62 の前提が変わった）")
open(p, 'w', encoding='utf-8').write(s.replace(new, old, 1))
PYEOF

measure python3 "$HOOKP" --selftest
finish
