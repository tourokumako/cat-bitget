#!/bin/bash
# EXPECT_RC: 1
# MEANS: 外す時間足の一覧を空にすると、T40③-3 が「引いてはいけない時間足が出た」で落ちた
# EXPECT_MSG: ❌ T40③-3
# b81 — 外す時間足を取り除く処理を消すと、引いてはいけない時間足が候補に出るか
#   守っているもの＝完成の条件 条件8（絞り込みの段で 1分足・3分足・10分足を1件も引かない）
#   壊し方＝候補を作る所で「外す時間足を取り除く」1行を消す。
#     ★まこさん決定 2026-09-10（重い3本を絞り込みの段では外す）が効いているかを測る。
#   期待＝自己テスト T40③-3 が落ちる（終了コード 1）。
#   ★壊す対象が見つからなければ止まる（黙って壊さない）。
#
# ★2026-09-12（まこさん承認）＝壊す相手を「設定ファイル」から「実装の行」に変えた。
#   直す前＝設定の `drop_tfs` を空の配列にしていた。**これでは壊れない**（走らせて確認＝rc=0）。
#   理由2つ
#     ①実装が `limits.get("drop_tfs") or ["1m","3m","10m"]` と書いてあり、
#       空の配列は Python では偽なので、右の既定値に戻る
#       （Python 公式の逐語＝"if x is true, then x, else y"／空の配列は false）。
#     ②検査の側（engine_tuner_gen.py の 6033行）も**同じ設定を読む**。
#       ＝設定を変えると、組む側と検査の基準が同時に動き、いつも辻褄が合ってしまう。
#   ★実装の行を消せば、検査の側は既定値（1分足・3分足・10分足）のままなので、
#     10分足が候補に出た瞬間に落ちる。
#   ★10分足で壊せる根拠＝1分足・3分足は「執行足より上」の条件で既に外れる。
#     10分足だけが、この設定でしか外れない（時間足の並び＝1m・3m・5m・10m・15m…）。
#     成績表に10分足の列も実在する（S-Rタッチ数×10m が 36件 ほか）。
source "$(dirname "$0")/lib.sh"

GEN="$PR/engine_tuner_gen.py"
guard "$GEN"

python3 - "$GEN" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = "    upper = [t for t in upper if t not in set(_drop_tfs)]\n"
if s.count(old) != 1:
    raise SystemExit(f"[b81] 壊す対象の行が1つに定まらない（{s.count(old)} 件）: {old.strip()}")
new = "    # b81 が壊した（外す時間足を取り除かない）\n"
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/engine_tuner_gen.py" --selftest
finish
