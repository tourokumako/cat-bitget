#!/bin/bash
# EXPECT_RC: 1
# MEANS: その検査が落ちた（守りが働いた）
# b75 — 目次の行番号を実物と違う数字に書き換えると、--verify が見つけるか
#   守っているもの＝設計書 gen-acceptance-tool-20260909 の完成の条件 #4
#     （目次が実物のコードから作られている＝手で書き換えたら分かる）
#   壊し方＝目次の中の行の範囲を、実物と違う数字に書き換える。
#   期待＝壊すと --verify が食い違いを見つけて 1 を返す。
#         壊さなければ 0。
source "$(dirname "$0")/lib.sh"

IDX="$SDK/.claude/ratchet/code_index.md"
guard "$IDX"

# 壊す＝最初の「行」の欄の数字を、実物と違うものに書き換える
python3 - "$IDX" <<'PYEOF'
import re
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
m = re.search(r'\| (\d+)〜(\d+) \|', s)
if not m:
    sys.exit("壊す相手の行の欄が見つからない")
bad = "| %d〜%d |" % (int(m.group(1)) + 777, int(m.group(2)) + 777)
open(p, 'w', encoding='utf-8').write(s[:m.start()] + bad + s[m.end():])
PYEOF

# 測る＝目次がコードと合っているかを見る（食い違えば 1）
measure python3 "$ROOT/.claude/tools/gen_code_index.py" --verify
finish
