#!/bin/bash
# b40 — 「足す」処理が指標の列を1つ書き換える形になったら、観察の道具の自己検査（T-f）が落ちるか
#
#   守っているもの＝設計書 iter="demand-in-ranking-20260907" の完成の条件 #2（AUDIT-1）
#     （足す前後で指標の列の分離力が1つも変わらない）。
#   壊し方＝observe_diag.merge_demand_into_ranking の中で、足した後の並び（merged）の先頭が指標の行なら
#          その分離力を 0.999 に書き換える1行を注入する。
#   測るもの＝`observe_diag.py --selftest-rank-demand`（数秒）。
#   期待＝壊すと、B の中の「指標の列が変わった＝fail-closed」（SystemExit）か T-f の③が ❌ を出し、
#         終了コードが 1 になる。
#
# ★時間について（b35 の事故の教訓・2026-09-07）
#   承認のときの打ち切りは 120秒。測る相手は数秒の口だけにする（T-f の実測＝3秒・2026-09-07）。
#
# 限界（正直に書く）
#   ①注入するのは1か所（先頭の行だけ）。別の形で指標の列を書き換える直しが入っても、この1本では測れない
#   ②自己検査のほかの枝は見ない（終了コードだけを見る）
#   ③このプログラム自身を書き換えれば無効にできる（承認のときに凍結される）

source "$(dirname "$0")/lib.sh"

T="$PR/observe_diag.py"
guard "$T"

# 壊す＝並べ直した直後に、先頭が指標の行なら分離力を書き換える1行を注入する
python3 - "$T" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
anchor = '                order[role].setdefault(lab, {})[key] = merged\n'
if anchor not in s:
    raise SystemExit("壊す対象の行が見つからない（b40 の前提が変わった）")
inject = ('                if merged and not _demand_rank_name(str(merged[0][0])): merged[0][1] = 0.999  # b40\n')
s = s.replace(anchor, anchor + inject, 1)
open(p, 'w', encoding='utf-8').write(s)
PYEOF

# 測る＝T-f だけを走らせる口。指標の列が変わると B が止まる（または③が ❌）＝1 になる
measure python3 "$PR/observe_diag.py" --selftest-rank-demand
finish
