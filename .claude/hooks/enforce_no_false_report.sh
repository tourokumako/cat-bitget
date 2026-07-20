#!/bin/bash
# enforce_no_false_report.sh — PostToolUse on Write|Edit（2026-07-20 まこさん指示・fast-mode 限定）
# 目的: 「役に立つアピールのために虚偽報告をするな」を物理化。
# 事案（2026-07-20）: CC が report のどこにも無い数字「+$19」を2ファイルの手計算で作り、
#   災害SLが無効化されて損失計上が消えただけの変化に「改善している」と評価語を付けて報告した。
#   まこさんが3回問い直してようやく判明＝類型G（虚偽報告）。
# 判定は enforce_no_false_report.py（別ファイル＝pdca_mark の無言死の教訓）:
#   exit 5 = 機械の出力（report_*/analysis_*）に無い金額を書いた（＝CC の手計算・捏造）
#   exit 6 = 自分の作業結果に肯定的評価語を付けた（評価は score.py とまこさんがする）
# ★正直な限界: 文字列検査。数字を書かず言葉だけで良く見せる報告は検出できない＝最終判断はまこさんの目。
MARK="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/pdca_fast_mode"
[ ! -f "$MARK" ] && exit 0   # fast-mode 限定

INPUT=$(cat)
AGENT_TYPE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('agent_type',''))" 2>/dev/null)
[ -n "$AGENT_TYPE" ] && exit 0

printf '%s' "$INPUT" | grep -qE 'FALSE_REPORT_OK=1' && exit 0

FP=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print((json.load(sys.stdin).get('tool_input',{}) or {}).get('file_path',''))" 2>/dev/null)
# 対象＝CC が書く記録文書（結果と評価を書く場所）
printf '%s' "$FP" | grep -qE '(session_worklog_[0-9]+\.md|next_step\.md|ledger\.md)$' || exit 0

HOOKS="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks"
RATCHET="/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/results/priority_rebuild/ratchet"

# 検査対象＝この編集で「新しく書いた文」だけ（Edit の new_string / Write の content）。
# ⚠️ ファイル全体を検査すると、前セッションが書いた過去の記録が延々と引っかかり CC が記録を一切追記できなくなる
#    （2026-07-20 実測＝過去4箇所が毎回検出）。過去の記録は書き換えられない＝検査しても是正のしようがない。
#    これは検査範囲の誤りの修正であって、判定の緩和ではない（CC が今書く文には従来どおり全部かかる）。
TMPDOC=$(mktemp)
printf '%s' "$INPUT" | python3 -c "
import sys, json
ti = (json.load(sys.stdin).get('tool_input', {}) or {})
sys.stdout.write(ti.get('new_string') or ti.get('content') or '')
" > "$TMPDOC" 2>/dev/null
[ ! -s "$TMPDOC" ] && { rm -f "$TMPDOC"; exit 0; }

READLOG="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/read_log.txt"
ERR=$(python3 "$HOOKS/enforce_no_false_report.py" "$TMPDOC" "$RATCHET" "$READLOG" 2>&1 >/dev/null)
rc=$?
rm -f "$TMPDOC"
[ "$rc" -eq 0 ] && exit 0

if [ "$rc" -eq 8 ]; then
  echo "🔒 [虚偽報告ゲート・fast-mode] 金額を書くなら、根拠となる機械の出力を同じ編集の中に貼ってください。" >&2
  echo "" >&2
  echo "検出: $ERR" >&2
  echo "対処: report.py / analyze.py / score.py の出力から、その数字が出ている箇所を**逐語でコピー**して" >&2
  echo "      コードブロック（\`\`\`）で貼る。または『出典: <ファイル名の該当節>』を明記する。" >&2
  echo "      ★貼れない数字は書かない。手計算・引き算・要約した数字は貼る証拠が無い＝それが捏造の正体。" >&2
  echo "      前後の差が要るときは report が出す前後比較を使う＝F節(月別)・K節(期待値4要素)・L節(限界分解)・" >&2
  echo "      C2『型別の前後比較』『出口理由 × 型 の差』（機械が差まで出す）。" >&2
  echo "      背景＝機械のどこにも無い「+\$19」を CC が2ファイルの手計算で作り虚偽報告した（2026-07-20）。" >&2
  echo "      設計の出典＝SmartSnap 型 proactive evidence seeking（照合でなく証拠提出・中身の当否はまこさんが判断）。" >&2
  echo "" >&2
  echo "（正当に不要な時のみ FALSE_REPORT_OK=1）" >&2
  exit 2
fi
if [ "$rc" -eq 7 ]; then
  echo "🔒 [虚偽報告ゲート・fast-mode] 読んでいないファイルについて「確認した」と書いています。" >&2
  echo "" >&2
  echo "検出: $ERR" >&2
  echo "対処: そのファイルを Read tool で実際に開いてから書く。開かずに中身を断定しない（未確認なら『未確認』と書く）。" >&2
  echo "      判定は read_log（Read tool の履歴・セッション開始でリセット）との照合＝grep や tail の断片では『読んだ』にならない。" >&2
  echo "      背景＝CC が hook のコードを1行も読まずに『デバッグ表示です・実行時エラーではありません』と断定し、" >&2
  echo "      まこさんに判断を求めた（2026-07-20）。まこさんの「意味がわからない」で読み直して誤りと判明。" >&2
  echo "" >&2
  echo "（正当に不要な時のみ FALSE_REPORT_OK=1）" >&2
  exit 2
fi

echo "🔒 [虚偽報告ゲート・fast-mode] $(basename "$FP") の記述を差し戻します。" >&2
echo "" >&2
if [ "$rc" -eq 5 ]; then
  echo "検出: 機械の出力に無い金額を書いています → $ERR" >&2
  echo "対処: 金額は report_*.txt / analysis_*.txt に**実在する数字**だけを書く。CC の手計算・引き算をしない。" >&2
  echo "      前後の差が要るときは report が出す前後比較を使う＝F節(月別)・K節(期待値4要素)・L節(限界分解)・" >&2
  echo "      C2『型別の前後比較』『出口理由 × 型 の差』（2026-07-20 新設・型別の差も機械が出す）。" >&2
  echo "      背景＝CC が2ファイルを手で引き算して作った「+\$19 改善」が虚偽報告になった（実体は災害SLの無効化）。" >&2
else
  echo "検出: 自分の作業結果への肯定的評価語 → $ERR" >&2
  echo "対処: 評価するのは score.py とまこさん。CC は事実と数字だけ書く。" >&2
  echo "      ×「改善した」「効いた」「有効」 → ○「月平均 net が −\$8.79 から −\$41.30 へ変化」「SL の発火 0件」" >&2
  echo "      背景＝安全装置が外れて損失計上が消えただけの変化に『改善』と付け、まこさんの採用判断を汚した。" >&2
fi
echo "" >&2
echo "（正当に不要な時のみ FALSE_REPORT_OK=1）" >&2
exit 2
