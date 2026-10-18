#!/bin/bash
# enforce_flow_declaration.sh — PreToolUse on Bash（2026-07-25 まこさん指示・新設・safety hook＝両モードで有効）
#
# 目的: 実行系コマンド（エンジン・探索・観察・採点）を打つ前に、「フローのどの工程をやっているのか」の
#   宣言を物理強制する。CC が工程を宣言せずに実行を重ね、まこさんが「今何をやっているのか」を
#   見失う事態（2026-07-25「毎回意味不明なことをしだすので私が混乱する」）を塞ぐ。
#
# 強制: 対象スクリプトを python 実行する前に、.claude/state/flow_declaration.md に
#   ①「段」の行 ②「工程」の行 ③実行するスクリプト名 が書かれていて、④宣言が24時間以内に
#   更新されていることを要求。満たさなければブロック（exit 2）。同じ工程で同じスクリプトを
#   回し直す間は宣言は1回でよい（工程が変わったら書き直す）。チャットにも同内容を出す（運用）。
#
# 宣言の型（5行・チャットと flow_declaration.md の両方）:
#   【フロー宣言】
#   段: E38 段3 Entry 策定
#   工程: 3️⃣層3 候補選定
#   実行: engine_tuner.py --logic S2
#   目的: 時間系候補の是正後の再探索
#   数え方: 値を選ぶ（search・累積に数える） ← --purpose を使う走行では必須（2026-08-19 まこさん決定「2」）
#          ／ プログラムの確認なら「確認する（check・累積に数えない）」と書く
#
# 対象（実行系のみ）: e38_priority_stack / engine_tuner / engine_search_e37 / observe_diag /
#   slot_opportunity_diag / e37_scalp / e35_* / e36_* / score.py / precheck.py / report.py / analyze.py / plot_trades
# 対象外（通す）: --selftest・py_compile・--help・読み取り系（grep/ls/cat 等）・引用符/ヒアドキュメント内の言及・
#   サブエージェント（デッドロック回避・他 hook と同型）。
# safety hook: fast-mode 無効化行を入れない（宣言なし実行は fast-mode 中に起きた＝fast-mode でこそ要る）。
# 解除: 無し（2026-08-16 まこさん指示「じゃあ強制解除できない状態にしろ」で廃止）。
# 限界: 宣言の中身が工程と一致しているかの意味判定はできない（まこさんの目と併用）。

INPUT=$(cat)
AGENT_TYPE=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('agent_type',''))" 2>/dev/null)
[ -n "$AGENT_TYPE" ] && exit 0   # サブエージェントは通す（デッドロック回避）

# ★解除（合言葉）は 2026-08-16 に廃止＝まこさん指示「じゃあ強制解除できない状態にしろ」。通す道は無い。

CMD=$(printf '%s' "$INPUT" | python3 -c "import sys,json;print((json.load(sys.stdin).get('tool_input',{}) or {}).get('command',''))" 2>/dev/null)

# 引用符・ヒアドキュメントの中身を除去（文章での言及では誤発火させない・enforce_observe_diag_only と同型）
CMD_X=$(printf '%s' "$CMD" | python3 -c "
import sys, re
s = sys.stdin.read()
for _m in re.finditer(chr(92) + chr(36) + r'\(([^()]*)\)|' + chr(96) + r'([^' + chr(96) + r']*)' + chr(96), s):
    s = s + chr(10) + (_m.group(1) or _m.group(2) or '')   # ★2026-10-18（監査 CP81）＝$( ) と逆引用符の中は引用符の中でも走る＝別の区切りとして足す
s = re.sub(r'(<<-?\s*[\"\x27]?(\w+)[\"\x27]?[^\n]*)\n.*?^\2', r'\1', s, flags=re.S | re.M)  # ヒアドキュメント本文を除去（<< の行は残す・監査 CP81）
s = re.sub(r'\"[^\"]*\"', ' ', s); s = re.sub(r\"'[^']*'\", ' ', s)             # 引用符の中身を除去
print(s)" 2>/dev/null)
[ -z "$CMD_X" ] && CMD_X="$CMD"

# 実行系スクリプトの抽出（読み取り系・文書生成は対象外）
# ★2026-08-19（まこさん決定「直す」）＝コマンド全体でなく、区切り（; & | 改行）で分けた断片ごとに見る。
#   直す前＝「コマンドのどこかに python が在り、どこかに対象の名前が在る」で止めていた。
#   ＝grep でファイルの名前を数えるだけでも止まった（2026-08-18 に2回・worklog §11.6）。
#   直したあと＝「python が、その対象のファイルを実行しようとしている断片」からだけ名前を拾う。
#   番人＝.claude/hooks/selftest_flow_declaration.sh（わざと壊して止まるかを実測する）
#   ★末尾は printf '%s\n'（改行なしだと while read が最後の断片を読み落とす）
# ★2026-10-17（186回目・まこさん「要。CCの案で修正する」）＝区切りの中に名前がどこかに在れば対象にする形をやめた。
#   対象にするのは、区切りの頭の python が、旗を飛ばした最初の語として走らせる .py で、ファイル名が対象の名前と全部 一致する物だけ。
#   直す前の誤報＝試しの道具の引数に observe_diag.py が在るだけで4回 止めた（2026-10-06）・enforce_no_false_report.py を report.py と読んだ。
#   自己テスト＝.claude/hooks/enforce_flow_declaration_selftest.py（--print-targets で読んだ名前を出させて照らす）
TARGETS=$(printf '%s\n' "$CMD_X" | python3 -c "
import sys, re
s = sys.stdin.read()
NAME = re.compile(r'(e38_priority_stack|engine_tuner|engine_search_e37|observe_diag|slot_opportunity_diag|e37_scalp|e3[56]_[a-z_]+|score|precheck|report|analyze|plot_trades)\.py', re.I)   # ★2026-10-18（監査 CP81）＝APFS は大文字と小文字を区別しない
ASSIGN = re.compile(r'^[A-Za-z_][A-Za-z_0-9]*=')
WRAP = set(['time', 'nice', 'nohup', 'timeout', 'exec', 'command', 'env', 'xargs', 'caffeinate'])
out = set()
for seg in re.split(r'[;|&\n]+', s):
    toks = seg.split()
    if '#' in toks:
        toks = toks[:toks.index('#')]   # ★2026-10-18（監査 CP81）＝区切りの後ろの注記（# --help）は旗でない
    if any(re.fullmatch(r'--selftest\S*|--verify\S*|--help|py_compile', t) for t in toks):   # 旗は語として見る（直す前は部分文字列＝--log /tmp/x--help.log で通った）
        continue
    i = 0
    while i < len(toks) and (ASSIGN.match(toks[i]) or toks[i] in WRAP or re.fullmatch(r'[0-9.]+[smhd]?', toks[i]) or (i > 0 and toks[i].startswith('-') and toks[i - 1] in WRAP)):
        i += 1
    if i >= len(toks) or not re.fullmatch(r'python[0-9.]*', toks[i].rsplit('/', 1)[-1]):
        continue
    j = i + 1
    while j < len(toks) and toks[j].startswith('-'):
        if toks[j] == '-m' and j + 1 < len(toks):   # ★2026-10-18（監査 CP81）＝-m <モジュール> は最後の名前に .py を付けて見る
            toks[j + 1] = toks[j + 1].rsplit('.', 1)[-1] + '.py'
            j += 1
            break
        j += 2 if toks[j] in ('-X', '-W') else 1   # 値を1つ取る旗は値ごと飛ばす（CP80 の enforce_purpose_gate._run_target と同じ）
    if j < len(toks) and NAME.fullmatch(toks[j].rsplit('/', 1)[-1]):
        out.add(toks[j].rsplit('/', 1)[-1])
print(chr(10).join(sorted(out)))
" 2>/dev/null)
[ "$1" = "--print-targets" ] && { printf '%s\n' "$TARGETS"; exit 0; }   # 自己テスト用（Claude Code は引数なしで呼ぶ）
[ -z "$TARGETS" ] && exit 0

DECL="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/flow_declaration.md"

fail() {
  echo "🔒 [フロー宣言ゲート・safety hook] 実行の前にフロー宣言を書いてください（まこさん指示 2026-07-25「毎回なにか実行するまえに、フローのなにをやってるのか宣言するように強制」）。" >&2
  echo "" >&2
  echo "不足: $1" >&2
  echo "対象: $(printf '%s' "$TARGETS" | tr '\n' ' ')" >&2
  echo "" >&2
  echo "対処: .claude/state/flow_declaration.md に次の4行の型で書き、同内容をチャットにも出してから実行する。" >&2
  echo "  【フロー宣言】" >&2
  echo "  段: <e38_flow.md の段（例 E38 段3 Entry 策定）>" >&2
  echo "  工程: <策定4段のどれ（例 3️⃣層3 候補選定）>" >&2
  echo "  実行: <スクリプト名と主な引数>" >&2
  echo "  目的: <1行>" >&2
  echo "  数え方: 値を選ぶ（search・累積に数える） ／ 確認する（check・累積に数えない）  ← --purpose を使う走行では必須" >&2
  echo "  時間の見込み: 15分未満 ／ 15分以上（見込み◯時間・根拠の実測・途中経過が見えるか・裏で走らせるか）  ← 必須（2026-08-23 まこさん指示）" >&2
  echo "  過去の実測: <記録のファイル名と引用（hook が記録から探して画面に出す）／無ければ『なし』>  ← 必須（2026-08-23 まこさん指示）" >&2
  echo "（同じ工程で同じスクリプトを回し直す間は宣言1回でよい・工程が変わったら書き直す・解除は 2026-08-16 に廃止）" >&2
  exit 2
}

[ -f "$DECL" ] || fail "宣言ファイルが無い（${DECL}）"

# 鮮度: 24時間以内の更新（古い宣言の使い回し＝工程が変わっても素通り、を防ぐ下限）
NOW=$(date +%s)
MT=$(stat -f %m "$DECL" 2>/dev/null || stat -c %Y "$DECL" 2>/dev/null)
[ -n "$MT" ] && [ $((NOW - MT)) -gt 86400 ] && fail "宣言が24時間より古い（工程を確認して書き直す）"

grep -q "段" "$DECL" || fail "「段:」の行が無い"
grep -q "工程" "$DECL" || fail "「工程:」の行が無い"

# ★時間の見込み（2026-08-23 まこさん指示・逐語「これは15分以上かかる場合は必ずその旨を宣言することを強制化してほしい」）
#   経緯: 54回目に CC が検査4（全列）を「1〜2時間の見込み」で裏で走らせたが、根拠の実測が重い列を含んでおらず
#   3時間28分 経っても終わらず、まこさんに「あとどのくらいで終わる？」「なんの計算をしてるの？」と聞かれた。
#   宣言に時間の見込みが無かったので、まこさんは待つか止めるかを判断できなかった（恒久の決まり60番）。
#   方式: 「時間の見込み:」の行を必須にし、「15分未満」か「15分以上」のどちらかを明示させる。
#   15分以上のときは、見込みの時間・根拠の実測・途中経過が見えるか・裏で走らせるか を同じ行に書く（中身の真偽は まこさんの目）。
grep -q "時間の見込み" "$DECL" || fail "「時間の見込み:」の行が無い（15分未満 ／ 15分以上 のどちらかを必ず書く・2026-08-23 まこさん指示）"
T_LT=0; T_GE=0
grep -qE '時間の見込み:.*15分未満' "$DECL" && T_LT=1
grep -qE '時間の見込み:.*15分以上' "$DECL" && T_GE=1
[ "$T_LT" = "1" ] && [ "$T_GE" = "1" ] && fail "「時間の見込み:」に『15分未満』と『15分以上』が両方 書いてある（どちらか1つにする）"
[ "$T_LT" = "0" ] && [ "$T_GE" = "0" ] && fail "「時間の見込み:」が読み取れない（『15分未満』か『15分以上』のどちらかを書く。15分以上なら 見込みの時間・根拠の実測・途中経過が見えるか・裏で走らせるか も書く）"
if [ "$T_GE" = "1" ]; then
  # ★61番（2026-08-23 まこさん指示「時間の予測ができない状態でテストを走らせることは禁止」）＝『分からない』は通さない
  grep -qE '時間の見込み:.*根拠' "$DECL" || fail "15分以上の走行なのに、見込みの根拠（実測）が書いていない（恒久の決まり61番＝予測できない走行は禁止。先に小さく測って根拠を作る）"
  grep -qE '時間の見込み:.*分からない' "$DECL" && fail "時間の見込みが『分からない』＝走らせない（恒久の決まり61番。先に列や期間を絞って1回あたりの時間を実測する）"
fi

for t in $TARGETS; do
  grep -q "$t" "$DECL" || fail "宣言に $t が書かれていない（このスクリプトの実行を宣言していない）"
done

# ★数え方の一致（2026-08-19 まこさん決定「2」・新設）
#   経緯: 2026-08-19 に CC が、プログラムの確認の走行を --purpose search で走らせ、
#   この窓の累積の試行数を 0本 → 16本 に増やした（決まり24番「プログラムの確認は必ず check」に違反）。
#   ★宣言の中で食い違っていた＝目的の欄には「実測する」（＝確認）、補足には「値を選ぶ走行」（＝search）。
#   どのプログラムもその食い違いを見ていなかった。まこさん決定「2」＝宣言と --purpose の一致を見る。
#   検査するのは --purpose を持つ走行だけ（いまは engine_tuner）。
PURPOSE=$(printf '%s\n' "$CMD_X" | grep -oE -- '--purpose[= ]+(search|check)' | grep -oE '(search|check)' | head -1)
if [ -n "$PURPOSE" ]; then
  grep -q "数え方" "$DECL" || fail "宣言に「数え方:」の行が無い（--purpose を使う走行では必須。値を選ぶ＝search ／ 確認する＝check）"
  D_SEARCH=0; D_CHECK=0
  grep -qE '数え方:.*値を選ぶ' "$DECL" && D_SEARCH=1
  grep -qE '数え方:.*確認する' "$DECL" && D_CHECK=1
  [ "$D_SEARCH" = "1" ] && [ "$D_CHECK" = "1" ] && fail "宣言の「数え方:」に『値を選ぶ』と『確認する』が両方 書いてある（どちらか1つにする）"
  [ "$D_SEARCH" = "0" ] && [ "$D_CHECK" = "0" ] && fail "宣言の「数え方:」が読み取れない（『値を選ぶ』か『確認する』のどちらかを書く）"
  DECL_KIND="check"; [ "$D_SEARCH" = "1" ] && DECL_KIND="search"
  [ "$DECL_KIND" = "$PURPOSE" ] || fail "宣言の数え方（${DECL_KIND}）と、コマンドの --purpose（${PURPOSE}）が食い違っている。★プログラムの確認は必ず check（恒久の決まり24番）。累積の試行数に足してよいのは、値を選ぶ走行だけ"
fi

# ★過去の実測の引用ゲート（2026-08-23 まこさん指示・逐語「手元の記録に在ったのに、走らせる前に探さなかった。
#   これは許されない。今後わかっていて報告しないようなことのないように強制しろ」）
#   経緯: 54回目に CC が検査4（全列）を「1〜2時間」の見込みで走らせたが、同じ全列の走行の実測（56分19秒）が
#   decisions.md に在った。CC は走らせる前に記録を探さず、4時間近く待たせた。
#   方式: hook 自身が記録（worklog・decisions・next_step）から「そのスクリプトの名前 ＋ 時間の語（分・秒・時間）」の
#   行を探す。見つかったら、その行を画面に出し、宣言の「過去の実測:」の行に見つかったファイル名が無ければ止める。
#   ＝CC が「探さなかった」と言える状態を無くす（記録の中身は hook が出す）。見つからなければ「過去の実測: なし」を要求。
#   限界: 引用した数字の解釈（期間の違い等）は見ない＝まこさんの目。
REC_DIR="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
# ★2026-10-12（172回目）＝next_step を2本に分けた（毎回読む next_step.md と、控えの next_step_reference.md）。
#   あとで直すことの一覧（§6）は控えのファイルに移ったので、探す相手に控えのファイルも入れる。
REC_FILES=$(ls "$REC_DIR"/session_worklog_*.md "$REC_DIR"/next_step.md "$REC_DIR"/next_step_reference.md \
  "/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/decisions.md" 2>/dev/null)
HIT_FILES=""; HIT_LINES=""
for t in $TARGETS; do
  stem=$(basename "$t" .py)
  for f in $REC_FILES; do
    ln=$(grep -nE "$stem" "$f" 2>/dev/null | grep -E '[0-9]+ ?(分|秒|時間)' | head -3)
    if [ -n "$ln" ]; then
      HIT_FILES="$HIT_FILES $(basename "$f")"
      HIT_LINES="$HIT_LINES
  [$(basename "$f")] $(printf '%s' "$ln" | cut -c1-160 | tr '\n' ' ')"
    fi
  done
done
if [ -n "$HIT_FILES" ]; then
  grep -q "過去の実測" "$DECL" || fail "「過去の実測:」の行が無い。★記録に、このスクリプトの時間の実測が在る（hook が探した）。どれかを引用して書く:$HIT_LINES"
  # 引用の実在＝「過去の実測:」の行の『』の中の文が、記録のどれかに実際に在るか（無い引用は通さない）
  QUOTE=$(grep '過去の実測' "$DECL" | python3 -c "import sys,re; m=re.search(r'「([^」]+)」', sys.stdin.read()); print(m.group(1) if m else '')" 2>/dev/null)
  [ -n "$QUOTE" ] || fail "「過去の実測:」に『「…」』で囲んだ引用が無い（記録の行を逐語で引用する）。見つかった記録:$HIT_LINES"
  CITED=0
  for f in $REC_FILES; do grep -qF -- "$QUOTE" "$f" 2>/dev/null && CITED=1 && break; done
  [ "$CITED" = "1" ] || fail "「過去の実測:」の引用「${QUOTE}」が、記録（worklog・decisions・next_step）のどこにも無い＝実在しない引用は通さない。見つかった記録:$HIT_LINES"
else
  grep -qE '過去の実測:.*なし' "$DECL" || fail "「過去の実測: なし」の行が無い（hook が記録を探したが、このスクリプトの時間の実測は見つからなかった＝その旨を書く）"
fi

# ★チャット表示ゲート（2026-07-26 まこさん指示）
#   経緯: CC は宣言を flow_declaration.md に書いて済ませ、チャットに出していなかった。
#   まこさん「そんな私がみないファイルにかかれても意味ないじゃん。私が見て確認するためなんだけど」。
#   ＝宣言の目的は「まこさんが実行前に現在地を確認すること」。ファイル検査だけでは目的を果たさない。
#   方式: 宣言の内容ハッシュを確認マーカーに持たせ、一致しなければ必ず1回ブロックして
#   宣言の全文をこの場に出す＝まこさんの画面に必ず出る。CC は同じ宣言をチャットに貼り、
#   マーカーを作ってから再実行する。宣言を書き換えるとハッシュが変わり、また最初のブロックに戻る。
#   同型＝show_budget_before_design（1回ブロック→再実行で通す）。
#   マーカーは reset_read_log がセッション開始で消す＝新しいセッションでは必ずもう一度まこさんの目に入る。
MARK="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/flow_declaration_posted"
DHASH=$(shasum -a 256 "$DECL" 2>/dev/null | awk '{print $1}')
POSTED=$(cat "$MARK" 2>/dev/null)
if [ -z "$DHASH" ] || [ "$POSTED" != "$DHASH" ]; then
  echo "🔒 [フロー宣言ゲート・safety hook] 実行の前に、この宣言をチャットに貼ってください。" >&2
  echo "   宣言はまこさんが実行前に現在地を確認するためのものです（2026-07-26 まこさん指示）。" >&2
  echo "   ファイルに書くだけでは目的を果たしません。" >&2
  echo "" >&2
  echo "───────── いまのフロー宣言（この全文をそのままチャットに貼る）─────────" >&2
  cat "$DECL" >&2
  echo "──────────────────────────────────────────────────" >&2
  echo "" >&2
  echo "対象: $(printf '%s' "$TARGETS" | tr '\n' ' ')" >&2
  echo "対処: ①上の宣言をチャットに貼る ②下のコマンドで確認マーカーを作る ③同じコマンドを再実行する" >&2
  echo "  shasum -a 256 \"$DECL\" | awk '{print \$1}' > \"$MARK\"" >&2
  echo "（宣言を書き換えるとハッシュが変わり、またここで止まる＝実行のたびにまこさんの目に入る）" >&2
  exit 2
fi

exit 0
