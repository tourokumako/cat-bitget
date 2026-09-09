#!/bin/bash
# EXPECT_RC: 1
# MEANS: その検査が落ちた（守りが働いた）
# b74 — 設計書の骨組みを古い節の名前に戻すと、7つの節が出なくなるか
#   守っているもの＝設計書 gen-acceptance-tool-20260909 の完成の条件 #3
#     （骨組みが7つの節を出す＝恒久の決まり70番）
#   ★終了コードでは測れない（節の名前を変えても --skeleton は動く）ので、
#     「7つの節の見出しが全部 出るか」を機械で数える。
#   壊し方＝skeleton が出す7つ目の節の見出しを、古い名前（## 9｜限界）に戻す。
#   期待＝壊すと7つ目の節が出なくなるので 1（壊れたことを検出できた）。
#         壊さなければ7つの節が全部 出るので 0。
source "$(dirname "$0")/lib.sh"

LBW="$ROOT/.claude/tools/list_banned_words.py"
guard "$LBW"

# 壊す＝7つ目の節の見出しを、古い形に戻す
python3 - "$LBW" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
before = 'L.append("## 7｜付録（hook が求める項目）")'
after = 'L.append("## 9｜限界（隠さない）")'
if before not in s:
    sys.exit("壊す相手の行が見つからない: " + before)
open(p, 'w', encoding='utf-8').write(s.replace(before, after, 1))
PYEOF

# 測る＝7つの節の見出しが全部 出るか
OUT="$(python3 "$LBW" --skeleton 2>/dev/null)"
MISS=0
for h in "## 1｜概要" "## 2｜背景と範囲" "## 3｜目標と、やらないこと" "## 4｜設計の中身" \
         "## 5｜決めたことと理由・捨てた案" "## 6｜テストとリスクと見積もり" \
         "## 7｜付録（hook が求める項目）"; do
    case "$OUT" in
        *"$h"*) ;;
        *) MISS=$((MISS + 1)) ;;
    esac
done
if [ "$MISS" -gt 0 ]; then
    MEASURED=1      # 節が欠けた＝壊れたことを検出できた
else
    MEASURED=0      # 壊しても7つ全部 出る＝この検査は守れていない
fi
finish
