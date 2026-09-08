#!/bin/bash
# EXPECT_RC: 1
# MEANS: その検査が落ちた（守りが働いた）
# b66 — G2 の指紋の照合を先頭8文字だけに緩めると、足した番人が落ちるか
#
#   守っているもの＝設計書 iter="tm-scope-and-g2-fingerprint-20260908" の完成の条件 #4。
#   何を守るか＝G2 の印と いまのコードの指紋を、丸ごと照らすこと。
#     直す前＝G2 には「印を照らす口」そのものが在りませんでした（H2 には在る）。
#     ＝「G2 の印を取り直したか」を確かめる口が、どこにも無い状態でした
#     （監査 cp32 の別枠 D＝監査は fingerprint を直に呼んで照らすしかなかった）。
#   壊し方＝照合を `now[:8] != fp[:8]` に緩める。
#   測るもの＝enforce_g2_pass.py --selftest（足した番人「先頭8文字だけが同じ印は通さない」）。
#   期待＝緩めると落ちて 1 になる。
#
# 限界（正直に書く）
#   ①印そのものを手で偽造されたら見抜けない（H2 と同じ限界）
#   ②このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）

source "$(dirname "$0")/lib.sh"

HOOKP="$ROOT/.claude/hooks/enforce_g2_pass.py"
guard "$HOOKP"

python3 - "$HOOKP" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
new = '''    now = fingerprint(files)
    if now != fp:
        print(f"❌ 印と、いまのコードが違う（印 {fp[:16]}… ／ いま {now[:16]}…）"
'''
old = '''    now = fingerprint(files)
    if now[:8] != fp[:8]:
        print(f"❌ 印と、いまのコードが違う（印 {fp[:16]}… ／ いま {now[:16]}…）"
'''
if new not in s:
    raise SystemExit("壊す対象の行が見つからない（b66 の前提が変わった）")
open(p, 'w', encoding='utf-8').write(s.replace(new, old, 1))
PYEOF

measure python3 "$HOOKP" --selftest
finish
