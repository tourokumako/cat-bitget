#!/bin/bash
# show_decisions.sh — セッション開始時に「まこさんが決めたこと」の一覧を作り直して表示する
#   （まこさん OK 2026-07-26・表示専用＝exit 0 で止めない）
#
# 経緯: 2026-07-26、CC が「保有の上限4時間」を判断材料として持ち出した。まこさんが以前に
#   決着させ設定からも撤去済みの決定だった。記録は在ったが、始めるときに目に入る1枚が無かった。
#   同じ日、質問形式の hook（理解確認テスト）はこの失敗を防げないと実測で分かり無効化した。
#   代わりに本 hook で「決定の一覧」を毎セッション頭に出す。
#
# 限界（正直に）: これは表示だけ。チャットでの発言は hook では止められない。
#   できるのは、始めるときに CC とまこさんの両方の目に入れるところまで。
set -u
GEN="/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_decisions.py"
DOC="/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/decisions.md"
SHOW=25   # 全部出すと毎セッション長すぎる＝直近25件だけ出して、残りはファイルを開く

[ -f "$GEN" ] || exit 0
# ★2026-10-15（まこさん「良い」）＝作り直しの失敗を表示する（直す前は出力を捨て、失敗しても古い一覧を黙って出していた）
GEN_OUT=$(python3 "$GEN" --write 2>&1)
if [ $? -ne 0 ]; then
  echo "⚠️ 決定の一覧を作り直せなかった（古いままです）: $GEN"
  printf '%s\n' "$GEN_OUT" | tail -5
fi
[ -f "$DOC" ] || exit 0

echo "=============================================================="
echo "★ まこさんが決めたこと（提案を出す前にここと突き合わせる）"
echo "   正本 $DOC （機械生成・全件はこのファイル）"
echo "=============================================================="
awk '/^\| 日付 \|/{f=1} f' "$DOC" | head -n $((SHOW + 2))
TOTAL=$(awk '/^\| 20[0-9][0-9]-|^\| 日付なし/{n++} END{print n+0}' "$DOC")
echo "--- 直近 ${SHOW} 件を表示（全 ${TOTAL} 件）。過去の決定を蒸し返さない。印の無い決定は載らない ---"
exit 0
