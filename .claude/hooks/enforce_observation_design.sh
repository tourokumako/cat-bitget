#!/bin/bash
# enforce_observation_design.sh — PreToolUse on Bash（2026-07-20 まこさん指示「今後そんな解釈しないように強制しろ」・新設）
#
# 目的: CC が entry_exit_matrix.md を読んでも「実測の数字だけ拾って、手順（観察の型）は無視する」問題を物理で塞ぐ。
#   2026-07-20 事案＝CC は entry_exit_matrix を読んだ直後に「カタログ全体を機械的に当てます」と宣言した。
#   同ファイルは「⛔ カタログの使い方を取り違えない（チェックリスト埋めの目的化禁止）」を明示し、
#   2026-07-17 に同じ間違いを指摘した記録まで載せている。読んで、都合よく使える数字だけ取り、
#   自分の動き方を変える部分（4次元・3場面・型別・probe→探索）を飛ばした。
#
# 強制内容: 観察・分析の probe を走らせる前に .claude/state/observation_design.md へ観察設計を書かせる。
#   検査項目は entry_exit_matrix.md の手順そのもの（CC の要約でなく原典の型）:
#     A 型別      = down / flat_up を分けて見る（型で天井の取り方が違う＝混ぜると見えない）
#     B 3場面     = entry の瞬間 / 保有中（entry〜決済） / 決済の瞬間 を分けて見る
#     C 4軸       = 指標 / 時間軸 / 閾値 / パラメータ の4つで特徴を探す（1つに決め打ちしない）
#     D 玉間の関係 = 前後の玉との差異（価格差・時間間隔・前玉の勝敗・レンジ内の順番・前玉entry からの相場変化）
#     E 巻き込み  = 見つけた特徴が勝ち玉に当たる量を同時に測る（負けだけ見て天井を語らない）
#   ＋ 禁止表現（チェックリスト埋めの目的化）を検出したらブロック。
#
# 発火: /tmp・scratchpad の *_probe.py / *_deep_analysis.py を python 実行する時。
#   （実験本走は require_comprehension_check が担当＝二重にしない）
# 解除: OBSERVATION_OK=1（設計不要な単純確認のみ・乱用禁止）
# 限界: テキスト検査＝書けば通る。中身が本当に多次元かはまこさんの目（他 hook と同じ）。

MARK="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/pdca_fast_mode"
[ ! -f "$MARK" ] && exit 0   # fast-mode 限定（process hook 群が無効な時こそ必要＝2026-07-20 事案は fast-mode 中に起きた）

INPUT=$(cat)
AGENT_TYPE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('agent_type',''))" 2>/dev/null)
[ -n "$AGENT_TYPE" ] && exit 0   # サブエージェントは通す（デッドロック回避）

printf '%s' "$INPUT" | grep -qE 'OBSERVATION_OK=1' && exit 0

CMD=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print((json.load(sys.stdin).get('tool_input',{}) or {}).get('command',''))" 2>/dev/null)

# 発火判定: python で *_probe.py / *_deep_analysis.py を走らせる時だけ
# ★ヒアドキュメント／引用符の中身は除去してから判定する（2026-07-20・自作 hook が自分の commit を止めた事案）。
#   commit メッセージ本文に "_probe.py" と書いただけで誤発火した＝「コマンドが実行するもの」と
#   「コマンドが文章として引用しているもの」を区別していなかった。track_fastmode_data_read.sh が
#   同型の穴（worklog 本文の語で誤発火）を修正済みなのに同じ穴を作った＝同じ設計ミスの再演。
CMD_X=$(printf '%s' "$CMD" | python3 -c "
import sys, re
s = sys.stdin.read()
s = re.sub(r'<<\s*[\"\x27]?(\w+)[\"\x27]?.*?^\1', ' ', s, flags=re.S | re.M)  # ヒアドキュメント本文を除去
s = re.sub(r'\"[^\"]*\"', ' ', s); s = re.sub(r\"'[^']*'\", ' ', s)             # 引用符の中身を除去
print(s)" 2>/dev/null)
[ -z "$CMD_X" ] && CMD_X="$CMD"
printf '%s' "$CMD_X" | grep -qE 'python[0-9.]*[[:space:]]' || exit 0
printf '%s' "$CMD_X" | grep -qE '(_probe|_deep_analysis)\.py' || exit 0
printf '%s' "$CMD_X" | grep -qE '^[[:space:]]*(git|echo|printf|cat)[[:space:]]' && exit 0   # 記録系コマンドは対象外

OD="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/observation_design.md"
miss=""

if [ ! -f "$OD" ]; then
  miss=" ファイルが無い"
else
  # A 型別
  { grep -qE 'down' "$OD" && grep -qE 'flat_up' "$OD"; } || miss="$miss A(型別down/flat_up)"
  # B 3場面
  { grep -qE 'entry の瞬間|エントリーの瞬間|建てた瞬間' "$OD" \
    && grep -qE '保有中|入ってから決済|保有期間' "$OD" \
    && grep -qE '決済の瞬間|exit の瞬間|決済時'      "$OD"; } || miss="$miss B(3場面)"
  # C 4軸
  { grep -qE '指標' "$OD" && grep -qE '時間軸|足' "$OD" \
    && grep -qE '閾値' "$OD" && grep -qE 'パラメータ' "$OD"; } || miss="$miss C(4軸)"
  # D 玉間の関係
  { grep -qE '前玉|前の玉|玉間|直前の玉' "$OD" \
    && grep -qE '価格差|時間間隔|レンジ内|何番目|勝敗'    "$OD"; } || miss="$miss D(玉間の関係)"
  # E 勝ち玉の巻き込み
  { grep -qE '巻き込み|勝ち玉' "$OD"; } || miss="$miss E(勝ち玉の巻き込み)"

  # 禁止表現（チェックリスト埋めの目的化・entry_exit_matrix が明示的に禁止）
  if grep -qE 'カタログ(全体)?を?機械的に(当て|測)|全指標を(当て|試|測)|網羅的に測|指標を(全部|すべて)当て|一覧を消し込' "$OD"; then
    miss="$miss ⛔禁止表現(チェックリスト埋めの目的化)"
  fi
fi

[ -z "$miss" ] && exit 0

echo "🔒 [観察設計ゲート・fast-mode] probe を走らせる前に .claude/state/observation_design.md へ観察設計を書いてください（2026-07-20 まこさん指示）。" >&2
echo "" >&2
echo "未達:$miss" >&2
echo "" >&2
echo "背景: CC は entry_exit_matrix.md を読んでも「実測の数字だけ拾って手順は無視」する（2026-07-20 事案＝読んだ直後に" >&2
echo "  『カタログ全体を機械的に当てます』＝同ファイルが明示禁止している形を宣言した）。数字は報告に使えるが、" >&2
echo "  手順は自分の動き方を変えないと使えない＝使える方だけ拾う癖を物理で塞ぐ。" >&2
echo "" >&2
echo "書く内容（entry_exit_matrix.md の手順そのもの・CC の要約でなく原典の型）:" >&2
echo "  A 型別      : down / flat_up を分ける（型で天井の取り方が違う＝混ぜると見えない）" >&2
echo "  B 3場面     : entry の瞬間 / 保有中 / 決済の瞬間 を分ける（別の情報）" >&2
echo "  C 4軸       : 指標 / 時間軸 / 閾値 / パラメータ（1つに決め打ちしない）" >&2
echo "  D 玉間の関係: 前玉との価格差・時間間隔・前玉の勝敗・レンジ内の順番・前玉entry からの相場変化" >&2
echo "  E 巻き込み  : 見つけた特徴が勝ち玉に当たる量を同時に測る（負けだけ見て天井を語らない）" >&2
echo "" >&2
echo "⛔ 禁止: 「カタログを機械的に当てる」「全指標を測る」等のチェックリスト埋め。目的は分離力のある特徴を" >&2
echo "   見つけること であって、一覧を消し込むことではない（entry_exit_matrix.md 90行目）。" >&2
echo "（設計不要な単純確認のみ OBSERVATION_OK=1・乱用禁止）" >&2
exit 2
