#!/bin/bash
# EXPECT_RC: 1
# MEANS: その検査が落ちた（守りが働いた）
# b72 — 囲みを手で書き換えても通る形に戻すと、自己テストが落ちるか
#   守っているもの＝設計書 gen-acceptance-tool-20260909 の完成の条件 #1
#     （自己テストが8件とも pass）
#   ★#3（骨組みが7つの節を出す）は、このプログラムでは守れない。
#     このプログラムが壊すのは gen_acceptance.py で、骨組みを出すのは list_banned_words.py。
#     #3 を守るのは b74_skeleton_old_sections.sh。
#   壊し方＝gen_acceptance.py の verify を、中身を1つも見ずに 0 を返す形にする
#           （手で書き換えた囲みでも「機械が書いたまま」と言う状態にする）。
#   ★2026-09-09 の直し＝はじめはハッシュ値の照合だけを消したが、その後ろに
#     「正本と食い違うか」の照合が残っていたので、壊しても検出できた（終了コード 0）。
#     ＝守りが二重なので、片方だけ消しても検査は落ちない。だから verify を丸ごと骨抜きにする。
#   期待＝壊すと T2（囲みに1行 足すと ❌）が pass しなくなるので、終了コードが 1 になる。
#         壊さなければ 8/8 pass で 0。
source "$(dirname "$0")/lib.sh"

GEN="$ROOT/.claude/tools/gen_acceptance.py"
guard "$GEN"

# 壊す＝verify が中身を1つも見ずに 0 を返す形にする
python3 - "$GEN" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
before = 'def verify(dest: Path = None) -> int:'
if before not in s:
    sys.exit("壊す相手の行が見つからない: " + before)
after = before + '\n    return 0  # わざと骨抜きにした（壊すプログラム b72）'
open(p, 'w', encoding='utf-8').write(s.replace(before, after, 1))
PYEOF

# 測る＝自己テストの終了コード（8件そろわなければ 1）
measure python3 "$GEN" --selftest
finish
