#!/bin/bash
# ⚠️ fast-mode の早期 exit は「編集対象を判定した後」に移した（2026-07-20）。
#    標準入力は1回しか読めないため、file_path を取る前に exit すると対象別の例外を作れない。
# require_acceptance_before_impl.sh — PreToolUse on Write|Edit
# 戦略実装(scripts/priority_rebuild/*.py)を編集する前に、受け入れ条件リスト(acceptance.md)が在り・
# 対象が一致し・まこさんが承認済(内容指紋一致)であることを確認。無ければ exit 2 でブロック。
#
# 目的（まこさん命令 2026-06-15）:
#   会話の指示も含め「指示→受け入れ条件リスト→合意→実装→照合」を物理強制する。
#   リスト＋まこさんの承認が無いと実装に入れない＝CC が指示を勝手に解釈して別物を作る/部品を抜くを止める。
#
# 正直な限界: 承認は approve_impl.sh の実行で立つ。CC がそれを勝手に実行すれば通せる（完全物理化は
#   まこさんの承認操作が要る）。運用＝承認コマンドはまこさんが打つ。実行はログに残る。中身の骨抜きは
#   score.py の数字＋独立レビューで見る。

STATE="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
LIST="$STATE/acceptance.md"
APPROVED="$STATE/acceptance.approved"

INPUT=$(cat)

# 1) サブエージェント(Workflow/Agent 内)は通す（デッドロック回避・require_workflow_for_impl と同型）
AGENT_TYPE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('agent_type',''))" 2>/dev/null)
[ -n "$AGENT_TYPE" ] && exit 0

# 2) 編集対象を取得。戦略実装(scripts/priority_rebuild/*.py)だけ対象（hook/設計書/state は対象外）
FILE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print((json.load(sys.stdin).get('tool_input',{}) or {}).get('file_path',''))" 2>/dev/null)

# ★計器・レポートツールは fast-mode でも承認必須（2026-07-20 まこさん指示「report.pyは勝手に変更できないようにしてよ」）
#   旧仕様＝report.py / plot_trades.py / analyze.py は「表示専用で net 判定も戦略実装もしない」として
#   完全免除だった（2026-06-21 まこさん承認・2026-07-02 に analyze.py 追加）。**2026-07-20 に撤回。**
#   撤回の理由＝CC が「自作 hook を通すため」に report.py の月平均の表示桁を GO なしで書き換えた。
#   表示専用でも勝手に変えれば まこさんが判断に使う数字の見え方が変わる＝判断材料が CC の都合で動く。
case "$FILE" in
  */report.py|*/plot_trades.py|*/analyze.py|*/score.py|*/eval_engine.py|*/precheck.py) TOOLGATE=1 ;;
  *) TOOLGATE=0 ;;
esac

# [fast-mode] process hook の一時無効化（touch/rm pdca_fast_mode で切替・2026-07-16）。
#   ただし TOOLGATE=1（計器・レポート・判定器）は fast-mode でも通さない＝上の撤回の実体。
if [ -f "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/pdca_fast_mode" ] && [ "$TOOLGATE" -eq 0 ]; then
  exit 0
fi
# 診断レーン免除（2026-07-14 まこさん承認）: *_diag.py ＝ read-only の検証/診断（戦略の実関数を import で再利用・
#   print/集計のみ）。改善フロー（新レバー提案）でない検証実装に acceptance ゲートは過剰＝report/analyze と同じ思想。
#   ★歯止め（骨抜き防止）: 新内容 or 既存ファイルに 売買記録CSV出力(to_csv/write_sidecar)・score 呼び出し(import score/
#   score.score)・採用書き出し(_output_and_report/ratchet_io) のいずれかが在れば免除しない＝通常ゲートへ落とす
#   （＝read-only でなければ実験扱い）。採用戦略ファイル(e37_range_scalp.py 等)は別名で今まで通り全ゲート対象＝
#   診断からは採用パイプラインを1文字も変えられない。
case "$FILE" in
  *_diag.py)
    NEWC=$(printf '%s' "$INPUT" | python3 -c "import sys,json;d=(json.load(sys.stdin).get('tool_input',{}) or {});print((d.get('content') or d.get('new_string') or ''))" 2>/dev/null)
    EXIST=""; [ -f "$FILE" ] && EXIST=$(cat "$FILE" 2>/dev/null)
    if printf '%s\n%s' "$NEWC" "$EXIST" | grep -qE 'to_csv|write_sidecar|import score|from score|score\.score|_output_and_report|ratchet_io'; then
      : # CSV/score/採用書き出しを触る＝read-only でない＝下の通常ゲートへ（実験扱い）
    else
      exit 0
    fi
    ;;
esac
case "$FILE" in
  *scripts/priority_rebuild/*.py) ;;
  *) exit 0 ;;
esac

GUIDE="流れ: ①CC が $LIST に「TARGET: <対象.py>」と受け入れ条件(やること)を書く ②チャットで提示 ③まこさんが内容OKなら『bash .claude/hooks/approve_impl.sh』を実行 ④実装"

# 3) リスト存在
if [ ! -f "$LIST" ]; then
  echo "🔒 [受け入れ条件ゲート] 実装の前に受け入れ条件リストがありません: $LIST" >&2
  echo "$GUIDE" >&2
  exit 2
fi

# 4) TARGET 一致（複数 TARGET 行 or カンマ区切りを許可・2026-06-22 まこさん承認＝
#    1 acceptance で複数ファイルをまとめて承認できる＝承認の往復を減らす。各 TARGET いずれかに一致すれば通す）
TARGETS=$(grep -E '^TARGET:' "$LIST" | sed 's/^TARGET:[[:space:]]*//' | tr ',' '\n' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | grep -v '^$')
if [ -z "$TARGETS" ]; then
  echo "🔒 [受け入れ条件ゲート] $LIST に『TARGET: <対象.py>』がありません。" >&2
  echo "$GUIDE" >&2
  exit 2
fi
MATCH=0
while IFS= read -r tgt; do
  [ -z "$tgt" ] && continue
  case "$FILE" in *"$tgt") MATCH=1; break ;; esac
done <<EOF
$TARGETS
EOF
if [ "$MATCH" -ne 1 ]; then
  echo "🔒 [受け入れ条件ゲート] 編集対象($FILE)がリストの TARGET($(echo "$TARGETS" | tr '\n' ' '))のいずれとも一致しません。" >&2
  echo "$GUIDE" >&2
  exit 2
fi

# 5) 機械照合用の部品リスト(DESIGN_CONTRACT)が在るか（書き忘れ防止＝明文化できる範囲を機械で漏れなく）
if ! grep -q "DESIGN_CONTRACT" "$LIST"; then
  echo "🔒 [受け入れ条件ゲート] $LIST に機械照合用の部品リスト(DESIGN_CONTRACT ブロック)がありません。" >&2
  echo "やること(自然言語)に加え、実装と機械照合できる部品リスト(DESIGN_CONTRACT の json: impl_file / self_check_calls / must_combine)を必ず書いてください。" >&2
  exit 2
fi

# 5.5) 深い分析＋ベースアップの必須化（まこさん命令 2026-06-15「分析と改善のフローが一番重要・深掘りしてから改善案」）
#   難しい問題に最易パッチを当てる前に、損の真因・期待値のどれを動かすか・root か symptom か・参照KB を書かせる。
#   ＝雑な分析のまま改善案を実装するのを物理ブロック。中身の質はまこさん30秒チェックが担保。
MISS_KW=""
for kw in "真因" "期待値" "symptom" "ベースアップ"; do
  grep -q "$kw" "$LIST" || MISS_KW="$MISS_KW $kw"
done
if [ -n "$MISS_KW" ]; then
  echo "🔒 [深い分析ゲート] $LIST に深掘り4点の見出しがありません（不足:$MISS_KW）。改善案の前に必須:" >&2
  echo "   ①真因(root cause・損/不足の構造的原因) ②期待値分解(勝率/平均利益/敗率/平均損失 のどれを動かすか)" >&2
  echo "   ③root を直すか symptom か(Y/N+理由・symptom 患い＝最易パッチを防ぐ) ④ベースアップ(参照した KB/検索の証跡・記憶ベース禁止)" >&2
  exit 2
fi

# 5.6) 疑似シミュ由来の固定値ゼロ宣言の必須化（まこさん承認 2026-06-26）
#   probe(疑似シミュ・静的後処理)で出た特定の数値を設計の固定値/閾値/段数に焼き込むのを物理ブロック。
#   背景: 2026-06-26 add ゲート設計で probe の θ≤0.4 / 段数3 / AUC0.83 を「クリア」扱いし acceptance に固定値で焼き込み
#   →まこさん指摘（疑似シミュは あたり付け専用＝決定的根拠でない）。設計の各閾値/段数の出所を1つずつ書かせる。
#   正直な限界: hook は「宣言が在るか」までを機械強制。中身が本当に probe 値を焼いていないかはまこさんの目＋番人。
if ! grep -qE "疑似シミュ由来の固定値ゼロ|固定値ゼロ宣言" "$LIST"; then
  echo "🔒 [疑似シミュ固定値ゼロゲート] $LIST に『★疑似シミュ由来の固定値ゼロ宣言』の見出しがありません（まこさん承認 2026-06-26）。" >&2
  echo "   probe(疑似シミュ)は あたりを付ける専用＝決定的根拠でない。設計の閾値/段数/パラメータの出所を1つずつ明示してください:" >&2
  echo "   ・各値は probe で出した特定数値でなく、実エンジンの学習窓選定 or 分析の構造由来の a-priori か" >&2
  echo "   ・probe の数値（θ=X・段数=N・AUC=Y 等）を設計の固定値に焼いていないか" >&2
  echo "   ・採否は probe でなく実エンジン両窓 score.py の数字で決めると明記しているか" >&2
  exit 2
fi

# 5.7) crude(疑似シミュ)を承認材料にするなら メリット・デメリットをセットで（まこさん承認 2026-07-14「不正をしたという記録をしろ・対策の hook 化」）
#   背景: E37 v24 で crude が「resting maker 利確を足した分 +$724」という良い数字だけを承認材料にし、
#   「STOCH_REVERSE を廃止して届かない玉が TIME/RANGE_BREAK で被る損」という失う分を隠した楽観値を提示
#   →実エンジン net −$477＝v23 −$420 から悪化。crude で「足す分」だけ見て「失う分」を見ない＝良く見せる不正。
#   v21 も同型（入口フィルタで TREND_CONT 出血 +$1,980 圧縮を出したが PARTIAL_TP −$1,724 巻き込みを隠した）。
#   ＝置換に限らず汎用: crude/probe 由来の改善数字を acceptance の承認材料に書くなら、必ずセットで
#   「この変更で失う分（副作用・巻き込み・廃止する枝の損）の試算」を書く。片方（メリットだけ）は承認材料にできない。
#   正直な限界: キーワード検出＝デメリット語を形だけ書けばすり抜ける。中身の妥当性は実エンジン両窓 score.py＋まこさんの目。
# 精密化（2026-07-14 番人でケースC 誤ブロック検出→是正）: 「crude の語が在るだけ」で発火しない＝
#   crude系の語と 改善の数字（対現状／+$金額）が【同じ行に一緒に】出る時だけ＝crude を改善数字の出所として承認材料にした行のみ拾う。
#   grep は行単位＝`.*` は改行を跨がない。「crude は使わない」等の言及だけの行（数字なし）は素通り。
HAS_CRUDE_MERIT=$(grep -qE '(crude|あたり付け|疑似シミュ).*(対現状|\+\$[0-9])|(対現状|\+\$[0-9]).*(crude|あたり付け|疑似シミュ)' "$LIST" && echo 1)
if [ "$HAS_CRUDE_MERIT" = "1" ]; then
  if ! grep -qE 'デメリット|失う分|副作用|巻き込み|反対側.{0,6}試算' "$LIST"; then
    echo "🔒 [crude はメリット・デメリットのセット ゲート] $LIST は crude/probe の改善数字（メリット）を承認材料にしていますが、対になる『この変更で失う分（デメリット）の試算』がありません（まこさん承認 2026-07-14・E37 v24 の +\$724 不正の再発防止）。" >&2
    echo "   crude で『足す分（メリット）』だけを承認材料にするのは不正。必ずセットで書いてください:" >&2
    echo "   ・メリット＝この変更で足す/稼ぐ分の crude 試算（既に有り）" >&2
    echo "   ・デメリット＝この変更で失う分の crude 試算＝副作用/巻き込み（フィルタで減る玉の稼ぎ）や、" >&2
    echo "     廃止・置換する枝が今まで実CSVで出していた損益と、その玉が廃止後どの exit_reason へ流れ何を被るか" >&2
    echo "   ・crude の対現状改善は『メリット − デメリット』の差引で出す（片方だけを承認材料にしない）" >&2
    echo "   ・採否は crude でなく実エンジン両窓 score.py で決めると明記" >&2
    exit 2
  fi
fi

# 6) 承認(内容指紋一致)確認
if [ ! -f "$APPROVED" ]; then
  echo "🔒 [受け入れ条件ゲート] 未承認です。リストを提示し、まこさんに『bash .claude/hooks/approve_impl.sh』を実行してもらってください。" >&2
  echo "$GUIDE" >&2
  exit 2
fi
CUR=$(shasum -a 256 "$LIST" | awk '{print $1}')
OKD=$(cat "$APPROVED" 2>/dev/null)
if [ "$CUR" != "$OKD" ]; then
  echo "🔒 [受け入れ条件ゲート] リストが承認後に変更されています(内容指紋が不一致)。再承認が必要: bash .claude/hooks/approve_impl.sh" >&2
  exit 2
fi
exit 0
