#!/bin/bash
# EXPECT_RC: 1
# MEANS: 守りを消したら、1分足を渡しても通ってしまった（＝その判定が守っている）
# b61 — 「渡されたのが5分足か」の判定を消すと、1分足を渡しても通ってしまうか
#
#   守っているもの＝設計書 iter="insp5-path-and-tidy-head-20260908" の完成の条件 #4。
#   何を守るか＝番人 T-i に渡すのが5分足であること。
#     直す前＝渡されたのが5分足かを見ていなかったので、1分足のファイルを渡しても
#     ❌ 0件 で通った（監査 cp31 の別枠 F が実測）。
#   壊し方＝バーの間隔を見る判定を消す。
#   測るもの＝observe_diag.py --selftest-insp5 に **1分足のファイル** を渡す。
#
#   ★向きが裏返っています（b51 と同じ形）。
#     守りが在るとき＝1分足を渡すと落ちる（終了コード 1）。
#     守りを消すと＝1分足を渡しても通る（終了コード 0）。
#     ＝「壊せた」ことを示す値は 0 です。承認のプログラムは 0 以外を見るので、
#       ここで向きを入れ替えて 1 を返します（下の if）。
#
# ★時間について＝承認のときの打ち切りは 120秒。軽い口だけを走らせる。
#
# 限界（正直に書く）
#   ①1分足のパスは実物の定数（ONE_MIN_CSV）から読む＝ここには書き写さない
#     （書き写すと、監査 cp31 の Critical 1 と同じ型をまた作ることになる）
#   ②向きを入れ替えているので、中で異常が起きた終了コード（lib.sh の 99）とは見分けが付く
#     （99 は 0 でないので、この判定では 0 側＝「壊せていない」に落ちる）
#   ③このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）

source "$(dirname "$0")/lib.sh"

OBS="$PR/observe_diag.py"
ONE_MIN_REL="$(python3 -c "import re,sys;print(re.search(r'ONE_MIN_CSV = \"([^\"]+)\"', open(sys.argv[1],encoding='utf-8').read()).group(1))" "$OBS")"
ONE_MIN="$SDK/$ONE_MIN_REL"
if [ ! -f "$ONE_MIN" ]; then
    echo "❌ 1分足の元データが無い: $ONE_MIN（b61 の前提が変わった）" >&2
    exit 98
fi
guard "$OBS"

python3 - "$OBS" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
new = '''            _step5 = _bars_step_minutes(bars_csv)
            if _step5 is None or abs(_step5 - 5.0) > 1e-9:
                ng.append(f"T-l: 渡されたファイルが5分足ではない（バーの間隔 {_step5} 分）: {bars_csv}")
'''
old = '''            pass  # ★b61 が、5分足かどうかの判定を消した
'''
if new not in s:
    raise SystemExit("壊す対象の行が見つからない（b61 の前提が変わった）")
open(p, 'w', encoding='utf-8').write(s.replace(new, old, 1))
PYEOF

python3 "$OBS" --selftest-insp5 "$ONE_MIN" >/dev/null 2>&1
rc=$?
if [ "$rc" -eq 0 ]; then MEASURED=1; else MEASURED=0; fi
finish
