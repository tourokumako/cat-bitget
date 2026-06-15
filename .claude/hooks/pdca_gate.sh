#!/bin/bash
# Stop: PDCA 未閉じならターン終了をブロック（analysis_playbook §4 物理強制・2026-06-05 まこさん矯正指示）
# score.py/precheck.py（審判の門）の後に report(--vs)・analyze・ledger 記録・5つの問い が無ければ
# exit 2 で終了を拒否し、CC に未済項目を返す（2026-06-12 まこさん合意で --vs / 5q を追加）。
STATE="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
MISS=""
# バックグラウンド実験が実行中（出力前）は審判催促を抑制（2026-06-13・長時間 replay 待ちで連発する事案の防止）。
# pdca_score_bg_pending は score.py/precheck.py 実行 or next_step 上書きでクリアされる＝完了後は通常通り催促。
[ -f "$STATE/pdca_need_score" ] && [ ! -f "$STATE/pdca_score_bg_pending" ] && MISS="${MISS}・審判（score.py または precheck.py）が未実行（実験スクリプトを回したのに審判を通っていない）\n"
[ -f "$STATE/pdca_need_report" ] && MISS="${MISS}・report.py 分析(結果一覧 A〜L)が未実行\n"
# need_vs: report を --vs なしで回すと立つ。no_baseline_approved（まこさん GO 済）があれば
# その場で消費して即 OK にする＝「ファイル作成→report 再実行」の二度手間を廃止（2026-06-15 まこさん指示）。
if [ -f "$STATE/pdca_need_vs" ]; then
  if [ -f "$STATE/no_baseline_approved" ]; then
    rm -f "$STATE/pdca_need_vs" "$STATE/no_baseline_approved"
  else
    MISS="${MISS}・report.py が --vs（前回ベースライン比較・KB §0 前後比較）なしで実行された。--vs <前回CSV> 付きで再実行せよ。真にベースラインが無い初回のみ、まこさん GO を得て state/no_baseline_approved を作成（GO なしの作成は類型G）\n"
  fi
fi
[ -f "$STATE/pdca_need_analyze" ] && MISS="${MISS}・analyze.py 深掘り(N1〜N9: 時間構造/交差/系列/ドリフト/bootstrap/個別読み/必要勝率/負け解剖/出口効率)が未実行\n"
[ -f "$STATE/pdca_need_ledger" ] && MISS="${MISS}・ledger.md への記録(結果+原因3分類+改善)が未実行\n"
[ -f "$STATE/pdca_need_5q" ] && MISS="${MISS}・ledger に 5つの問いが未記入: 【問1 レバー】(期待値4要素のどれが何pt動いたか)【問2 不足量】(あと何がいくら足りないか・数値)【問3 負け集中】(特徴・期間・出口)【問4 過去接続】(どの E と同じ/違う構造か)【問5 次仮説】(学習期間で検証可能な形で1つ)。5見出し全部を含む編集で旗が下りる\n"
[ -f "$STATE/pdca_need_claim" ] && MISS="${MISS}・ledger に【主張】1行が未記入（多角チェックリスト #19・analysis_playbook §2.0）。analyze.py N0 の件数妥当性(件数/日)を踏まえ、この実験の結論を【主張】<件数/日 と net を含む根拠つき1行> として ledger E エントリに書け（多角チェックを1発見で止めず量→質→...を通した結論）\n"
[ -f "$STATE/pdca_need_next_step" ] && MISS="${MISS}・next_step.md（次セッションの起点・SessionStart 表示）が未更新。ledger に実験を記録したら .claude/state/next_step.md を上書き更新せよ（毎回上書き=最新の起点1枚。必須記載=①次セッションの本筋 ②今セッションの確定(ledger E番号を参照) ③やってはいけないこと ④数字の出典）。「本筋」「やってはいけない」「出典」の見出しを含む上書きで旗が下りる\n"
if [ -n "$MISS" ]; then
  printf "⛔ PDCA未閉じ(analysis_playbook §4)。審判を通したら必ず以下を済ませてから終了せよ:\n%b最低ライン分析(N1〜N9)は数字の抽出にすぎない。5つの問いに答えるまでが分析(まこさん 2026-06-12)。\n" "$MISS" >&2
  exit 2
fi
exit 0
