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
if [ -f "$STATE/pdca_need_analyze" ]; then
  _why=""; [ -f "$STATE/pdca_analyze_incomplete" ] && _why="（不足: $(cat "$STATE/pdca_analyze_incomplete")）"
  MISS="${MISS}・analyze.py 深掘り(N0〜N12)が未実行 or 不完全${_why}。汎用 analyze は §0前後比較[前回≠今回]＋N4分布ドリフトが揃うまで旗が残る＝必ず --vs <直前の実験(report持ち)> --train <train.csv> を付けて再実行（2026-06-25 付け忘れ防止）\n"
fi
# 分析レポートを出して読む強制（「別途」で逃げる・省略・読み飛ばし 禁止・まこさん 2026-06-15）。
#   analyze を完走させ analysis_*.txt を生成 → Read tool で読む（read_log に /analysis_ が載る）まで終了不可。
#   analyze がスキーマ非対応等でクラッシュ→レポート未生成なら read_log に載らない＝ここで止まる（"別途"の逃げ道を塞ぐ）。
if [ -f "$STATE/pdca_need_analyze_report" ]; then
  if grep -q "/analysis_" "$STATE/read_log.txt" 2>/dev/null; then
    rm -f "$STATE/pdca_need_analyze_report"
  else
    MISS="${MISS}・分析レポートを出して読め（「別途」で逃げる・省略・読み飛ばし 禁止・まこさん 2026-06-15）。analyze を完走させ analysis_*.txt を生成→Read tool で読み、5問に N10〜N12 の構造解釈を引用して書け。analyze がクラッシュするならツールを直して完走させる（"別途"は不可）。\n"
  fi
fi
[ -f "$STATE/pdca_need_viz" ] && MISS="${MISS}・週次チャートPNG(トレード最多/最少・NET最大/最小 の4週)が未生成。report.py を --vs 付きで実行すれば M節が自動出力する（results/priority_rebuild/viz/）。M節が「スキップ」表示なら matplotlib/plot_trades を直して PNG を出すまで終了不可（まこさん 2026-06-21 強制化）\n"
[ -f "$STATE/pdca_need_ledger" ] && MISS="${MISS}・ledger.md への記録(結果+原因3分類+改善)が未実行\n"
[ -f "$STATE/pdca_need_5q" ] && MISS="${MISS}・ledger に 6つの問い＋方針が未記入: 【問0 前後比較】(前回ベースライン vs 今回の 件数/net/avg/勝率を並べ、激減や急増がないか=KB §0 大原則・degenerate 見落とし防止)【問1 レバー】(期待値4要素のどれが何pt動いたか)【問2 不足量】(あと何がいくら足りないか・数値)【問3 負け集中】(どのスライス=月/出口/指標帯 に負けが集中か)【問4 過去実験との接続】(過去のどの実験番号 E○○ と構造が同じ/違うか)【問5 次仮説】(学習期間で検証可能な形で1つ)＋【方針/狙い/目的】(前の iter の何を受けて何を狙ってこの変更をしたか=改善の意図・next_step の改善アークが引用する正本・2026-06-26)。6見出し＋方針/狙い/目的のいずれかを含む編集で旗が下りる\n"
[ -f "$STATE/pdca_need_claim" ] && MISS="${MISS}・ledger に【主張】1行が未記入（多角チェックリスト #19・analysis_playbook §2.0）。analyze.py N0 の件数妥当性(件数/日)を踏まえ、この実験の結論を【主張】<件数/日 と net を含む根拠つき1行> として ledger E エントリに書け（多角チェックを1発見で止めず量→質→...を通した結論）\n"
[ -f "$STATE/pdca_need_next_step" ] && MISS="${MISS}・next_step.md（次セッションの起点・SessionStart 表示）が未更新。ledger に実験を記録したら .claude/state/next_step.md を上書き更新せよ（毎回上書き=最新の起点1枚。必須記載=①次セッションの本筋 ②今セッションの確定(ledger E番号を参照) ③やってはいけないこと ④数字の出典 ⑤改善アーク=gen_improvement_arc.py が自動生成（CC 手書き禁止・改ざん不可）。狙い/内容/方法/前提=ARC マーカー（ledger/acceptance・git tamper-evident）・結果/採点窓数字=score.py（改造禁止 H13）・採否=記録ラベル＋score.py 数字併記）。**改善アーク表は手書きせず \`python3 .claude/ratchet/gen_improvement_arc.py --write\` で生成すること＝next_step の ARC_TABLE_START hash=H が表本文の sha256 と一致しないと（CC 手書き）旗が下りない（2026-06-27 まこさん指示「全列を改ざんできないように・自動生成」）**。「本筋」「やってはいけない」「出典」「改善アーク」見出し＋ARC_TABLE ハッシュ一致 で旗が下りる（2026-06-26/27 取り違え・妄想・改ざん 防止）\n"
if [ -n "$MISS" ]; then
  printf "⛔ PDCA未閉じ(analysis_playbook §4)。審判を通したら必ず以下を済ませてから終了せよ:\n%b最低ライン分析(N1〜N9)は数字の抽出にすぎない。5つの問いに答えるまでが分析(まこさん 2026-06-12)。\n" "$MISS" >&2
  exit 2
fi
exit 0
