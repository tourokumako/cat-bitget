#!/bin/bash
# enforce_purpose_gate.sh — PreToolUse on Write|Edit|MultiEdit|Bash（2026-08-06 まこさん指示・新設・safety hook）
#
# ★まこさんの逐語（2026-08-06）
#   「net利益を最大化させる条件（指標、閾値、時間、パラメータ）の組み合わせを、見つけることができる機械を
#     作ることが目的」
#   「上記目的に即していないもの以外は作らないこと」
#   「つまりは上記条件を一つでも達成できていないものは作成してはいけないということ。」
#   「そのために強制hookを作ることはOK」
#
# 背景（なぜ在るか）
#   CC が 2026-08-01 に作った engine_tuner_gen（売買ルールの形を組み立てる方）は、材料105種・時間足8つ・
#   しきい値9段・向きを全部 乱数で引き、常に「かつ」でつなぐだけの器だった＝目的を1つも満たさない。
#   まこさんの逐語＝「私はそんな無意味な組み合わせ器を作れとは一言も言ってないのに、なんでそんなクソみたいな
#   もの作ったんだよ」。詳細＝.claude/ratchet/engine_tuner_defects.md（欠陥 D1〜D9・不正6件）。
#   CC の自主運用のルールでは止まらなかった（何度も素通りした）ので、物理で止める。
#
# 何を強制するか
#   engine_tuner 系を「書く／直す／走らせる」前に、.claude/state/purpose_check.md に目的の照合を書かせる。
#   6つの条件を1つずつ ✅ か ❌ で書き、**1つでも ❌ があればブロック**（まこさんの「一つでも達成できて
#   いないものは作成してはいけない」を機械化）。
#   あわせて、要件定義書の「⛔⛔ 作ってはいけないもの」の一覧を Read tool で開いていることを read_log で照合する。
#
# 宣言の型（.claude/state/purpose_check.md・チャットにも同じものを貼る）
#   【目的の照合】
#   対象: <これから作る／直すもの>
#   ① net 利益を最大化する方向に働くか: ✅ or ❌ ＋ 根拠1行
#   ② 指標を組み合わせられるか: ✅ or ❌ ＋ 根拠1行
#   ③ 閾値を組み合わせられるか: ✅ or ❌ ＋ 根拠1行
#   ④ 時間（時間足）を組み合わせられるか: ✅ or ❌ ＋ 根拠1行
#   ⑤ パラメータを組み合わせられるか: ✅ or ❌ ＋ 根拠1行
#   ⑥ 見つけることができるか（探索できるか）: ✅ or ❌ ＋ 根拠1行
#   作ってはいけないものの一覧との照合: <一覧の1件ずつ・当たらないことを書く>
#   ★入っていないもの: <明示・無ければ「なし」>
#
# 対象（止めるもの）
#   ① Write/Edit/MultiEdit で scripts/priority_rebuild/engine_tuner*.py を書く／直す
#   ② Write/Edit/MultiEdit で .claude/state/acceptance.md ／ *_design.md を書く（engine_tuner の設計）
#   ③ Bash で engine_tuner*.py を python 実行する（--selftest・--verify・--identity・py_compile・--help は除く）
# 対象外（通す）: 上記以外。宣言ファイル自身。読む・調べる系の Bash。サブエージェント。
#
# safety hook: fast-mode 無効化行を入れない（勝手な作りは fast-mode 中にこそ起きうる）。
# 解除: 無し（2026-08-16 まこさん指示で廃止＝合言葉では通らない）。
# 限界: テキスト検査＝「✅」と嘘を書けば機械では見抜けない。最後の関所はまこさんの目。
#   ただし「何を ✅ と言い切ったか」が手を動かす前に6行で残る＝後から突き合わせられる。

INPUT=$(cat)
AGENT_TYPE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('agent_type',''))" 2>/dev/null)
[ -n "$AGENT_TYPE" ] && exit 0

# ★解除（合言葉）は 2026-08-16 に廃止＝まこさん指示「じゃあ強制解除できない状態にしろ」。通す道は無い。

TOOL=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null)
CMD=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print((json.load(sys.stdin).get('tool_input',{}) or {}).get('command',''))" 2>/dev/null)
FPATH=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print((json.load(sys.stdin).get('tool_input',{}) or {}).get('file_path',''))" 2>/dev/null)

ROOT="/Users/tachiharamasako/Documents/GitHub/cat-bitget"
DECL="$ROOT/.claude/state/purpose_check.md"
RLOG="$ROOT/.claude/state/read_log.txt"

# 宣言ファイル自身は通す（デッドロック回避）
[ "$FPATH" = "$DECL" ] && exit 0

TARGET=0
case "$TOOL" in
  Write|Edit|MultiEdit)
    case "$FPATH" in
      */scripts/priority_rebuild/engine_tuner*.py) TARGET=1 ;;
      */.claude/state/acceptance.md|*_design.md)   TARGET=1 ;;
    esac
    ;;
  Bash)
    # 引用符の中身を除去（文章での言及で誤発火させない・他 hook と同型）
    CMD_X=$(printf '%s' "$CMD" | python3 -c "
import sys, re
s = sys.stdin.read()
s = re.sub(r'<<\s*[\"\x27]?(\w+)[\"\x27]?.*?^\1', ' ', s, flags=re.S | re.M)
s = re.sub(r'\"[^\"]*\"', ' ', s); s = re.sub(r\"'[^']*'\", ' ', s)
print(s)" 2>/dev/null)
    [ -z "$CMD_X" ] && CMD_X="$CMD"
    printf '%s' "$CMD" | grep -qE 'purpose_check' && exit 0
    printf '%s' "$CMD_X" | grep -qE 'python[0-9.]*[[:space:]]' || exit 0
    # 検査だけの実行は通す（作っていない＝目的の照合を求める場面ではない）
    printf '%s' "$CMD_X" | grep -qE -- '--selftest|--verify|--identity|py_compile|--help|--dry-run' && exit 0
    printf '%s' "$CMD_X" | grep -qE 'engine_tuner[a-z_]*\.py' && TARGET=1
    ;;
esac
[ "$TARGET" = "0" ] && exit 0

fail() {
  echo "🔒 [目的ゲート・safety hook] engine_tuner に手を入れる前に、目的の照合をチャットに貼ってください。" >&2
  echo "" >&2
  echo "★まこさんの逐語（2026-08-06）" >&2
  echo "  「net利益を最大化させる条件（指標、閾値、時間、パラメータ）の組み合わせを、見つけることができる機械を作ることが目的」" >&2
  echo "  「上記目的に即していないもの以外は作らないこと」" >&2
  echo "  「つまりは上記条件を一つでも達成できていないものは作成してはいけないということ。」" >&2
  echo "" >&2
  echo "不足: $1" >&2
  echo "" >&2
  if [ -f "$DECL" ]; then
    echo "───────── いまの目的の照合（この全文をそのままチャットに貼る）─────────" >&2
    cat "$DECL" >&2
    echo "──────────────────────────────────────────────────" >&2
    echo "" >&2
  fi
  echo "対処: ①下の型で $DECL を書く ②同じ内容をチャットに貼る ③再実行する" >&2
  echo "  【目的の照合】" >&2
  echo "  対象: <これから作る／直すもの>" >&2
  echo "  ① net 利益を最大化する方向に働くか: ✅ or ❌ ＋ 根拠1行" >&2
  echo "  ② 指標を組み合わせられるか: ✅ or ❌ ＋ 根拠1行" >&2
  echo "  ③ 閾値を組み合わせられるか: ✅ or ❌ ＋ 根拠1行" >&2
  echo "  ④ 時間（時間足）を組み合わせられるか: ✅ or ❌ ＋ 根拠1行" >&2
  echo "  ⑤ パラメータを組み合わせられるか: ✅ or ❌ ＋ 根拠1行" >&2
  echo "  ⑥ 見つけることができるか（探索できるか）: ✅ or ❌ ＋ 根拠1行" >&2
  echo "  作ってはいけないものの一覧との照合: <一覧の1件ずつ>" >&2
  echo "  ★入っていないもの: <明示・無ければ「なし」>" >&2
  echo "" >&2
  echo "⛔ ①〜⑥ に1つでも ❌ があるものは、作ってはいけません（まこさん確定 2026-08-06）。" >&2
  echo "   ❌ になるものを作りたいときは、まこさんに理由を出して確認してください（CC が勝手に進めない）。" >&2
  echo "（解除は 2026-08-16 に廃止＝合言葉では通りません）" >&2
  exit 2
}

[ -f "$DECL" ] || fail "目的の照合のファイルが無い（$DECL）"
grep -q "【目的の照合】" "$DECL" || fail "「【目的の照合】」の行が無い"
grep -q "^対象:" "$DECL" || fail "「対象:」の行が無い（これから作る／直すものを書く）"

# 6条件が1つずつ書かれているか
for n in ① ② ③ ④ ⑤ ⑥; do
  grep -q "^${n}" "$DECL" || fail "「${n}」で始まる行が無い（6つの条件を1つずつ書く）"
done

# ★1つでも ❌ があればブロック（まこさん確定＝一つでも達成できていないものは作成してはいけない）
NG=$(grep -E "^[①②③④⑤⑥]" "$DECL" | grep -c "❌")
if [ "$NG" -gt 0 ]; then
  echo "🔒 [目的ゲート] 目的の条件に ❌ が ${NG} 件あります。**これは作ってはいけないものです。**" >&2
  echo "" >&2
  grep -E "^[①②③④⑤⑥]" "$DECL" | grep "❌" >&2
  echo "" >&2
  echo "★まこさん確定 2026-08-06（逐語）＝「つまりは上記条件を一つでも達成できていないものは作成してはいけないということ。」" >&2
  echo "対処: 設計を直して6つとも ✅ にするか、まこさんに理由を出して確認してください。CC が勝手に進めません。" >&2
  exit 2
fi

grep -q "^作ってはいけないものの一覧との照合:" "$DECL" \
  || fail "「作ってはいけないものの一覧との照合:」の行が無い（要件定義書の一覧と1件ずつ突き合わせる）"
grep -q "入っていないもの:" "$DECL" \
  || fail "「★入っていないもの:」の行が無い（承認のときに都合の悪い事実を落とした 2026-08-01 の再発防止）"

# 要件定義書（作ってはいけないものの一覧の正本）を Read tool で開いたか
grep -qF "engine_tuner_requirements.md" "$RLOG" 2>/dev/null \
  || fail "作ってはいけないものの一覧の正本 engine_tuner_requirements.md を Read tool で開いていない"

exit 0
