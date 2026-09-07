#!/bin/bash
# b50 — 見本の関数を呼ぶ所の名前を戻すと、静的検査が赤に戻るか
#
#   守っているもの＝next_step §6 の149番（設計書 iter="approval-audit-plumbing-20260907" の
#     完成の条件 #11）。
#   何を守るか＝静的検査（lint_provenance の⑤）は「見本の関数（_thr_fixture ほか）は、
#     名前に selftest が入った関数の中でだけ呼んでよい」という決まりを見る。
#     直す前＝自己テストの本体の名前が `_check_extra_gate` で selftest が入っておらず、
#     その中の `_thr_fixture("q70")` が「自己テストの外で使った」と数えられ、
#     静的検査が 1件 の赤のままだった（実測＝m2d_lint_check.py の逐語「見本の関数: 1 件 行=[3815]」）。
#   壊し方＝判定を「名前がちょうど selftest のときだけ許す」に戻す。
#   測るもの＝`engine_tuner_gen.py --lint-provenance`。
#   期待＝壊すと 1件 に戻って終了コードが 0 以外になる。
#
# ★時間について（b35 の事故の教訓）＝承認のときの打ち切りは 120秒。実測（2026-09-07）＝数秒。
#
# 限界（正直に書く）
#   ①壊すのは判定の1行だけ（関数の名前を戻す壊し方は、この1本では測れない）
#   ②静的検査のほかの枠は見ない（終了コードだけを見る）
#   ③このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）

source "$(dirname "$0")/lib.sh"

T="$PR/engine_tuner_gen.py"
guard "$T"

python3 - "$T" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
before = s
s = s.replace(
    'if ch.func.id in _FIXTURE_CTORS and not any("selftest" in _s for _s in st):',
    'if ch.func.id in _FIXTURE_CTORS and "selftest" not in st:', 1)
if s == before:
    raise SystemExit("壊す対象の行が見つからない（b50 の前提が変わった）")
open(p, 'w', encoding='utf-8').write(s)
PYEOF

measure python3 "$T" --lint-provenance
finish
