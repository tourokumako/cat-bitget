#!/bin/bash
# EXPECT_RC: 1
# MEANS: その検査が落ちた（守りが働いた）
# b59 — 控えの見出しの取り方を直す前へ戻すと、番人が落ちるか
#
#   守っているもの＝設計書 iter="insp5-path-and-tidy-head-20260908" の完成の条件 #2。
#   何を守るか＝控えに入る見出しが「見出しの行1本＋区切りの行1本」になること。
#     直す前（監査 cp30 の別枠7 の直し）＝区切りの行を外してから先頭2本を取っていたので、
#     表に生きている行が1本でも在ると、2本目がその行になり、控えに複製された。
#     しかも区切りが入らないので、控えの表が表として描画されなかった（監査 cp31 の Major 1）。
#   壊し方＝見出しの取り方を、直す前の形（区切りを外して先頭2本）へ戻す。
#   測るもの＝tidy_next_step.py --selftest（番人 T10d・T10e が見る）。
#   期待＝戻すと落ちて 1 になる。
#
# 限界（正直に書く）
#   ①T10d と T10e は同じ壊し方で両方 落ちる（どちらが落ちたかは終了コードから分からない）
#   ②このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）

source "$(dirname "$0")/lib.sh"

TIDY="$ROOT/.claude/tools/tidy_next_step.py"
guard "$TIDY"

python3 - "$TIDY" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
new = '''    _rows = [ln for ln in lines[s2:end] if ln.lstrip().startswith("|")]
    _head_ln = None
    if (_rows and "---" not in _rows[0] and DONE_MARK not in _rows[0]
            and not STRIKE_RE.search(_rows[0])):
        _head_ln = _rows[0]
    if _head_ln is None:
        head_rows = "| 番号 | やること | 状態 |\\n|---|---|---|\\n"
    else:
        _sep_ln = (_rows[1] if len(_rows) >= 2 and "---" in _rows[1]
                   else "|" + "---|" * max(1, _head_ln.count("|") - 1) + "\\n")
        head_rows = _head_ln + _sep_ln
'''
old = '''    _hdr = [ln for ln in lines[s2:end]
            if ln.lstrip().startswith("|") and "---" not in ln and DONE_MARK not in ln
            and not STRIKE_RE.search(ln)]
    head_rows = "".join(_hdr[:2]) if len(_hdr) >= 1 else "| 番号 | やること | 状態 |\\n|---|---|---|\\n"
    if len(_hdr) == 1:
        head_rows = _hdr[0] + "|" + "---|" * max(1, _hdr[0].count("|") - 1) + "\\n"
'''
if new not in s:
    raise SystemExit("壊す対象の行が見つからない（b59 の前提が変わった）")
open(p, 'w', encoding='utf-8').write(s.replace(new, old, 1))
PYEOF

measure python3 "$TIDY" --selftest
finish
