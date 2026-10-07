# 監査結果 cp63 — CP63 — 指標の修正の全体の表の2回目＝パラメータ。M2-C-15（実装の監査）

## 1. 監査の相手と版

- 依頼書: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-06_m2c15_param_values_20261006_impl_cp63_audit_request.md`
- 依頼書のハッシュ値: ea2846580b075b1467c923a519e6e7f0cc6777c9a78fedce4ce7f6adeb01717b
- 監査の相手と版（依頼書に書いてあるもの）: `.claude/state/acceptance.md` ／ ハッシュ値 1249fa04e4ea67ae812f007e62740ea71064e03ee7b2e5b455365afc50393307
- 監査が照らしたハッシュ値: `shasum -a 256 .claude/state/acceptance.md` ＝ 1249fa04e4ea67ae812f007e62740ea71064e03ee7b2e5b455365afc50393307（依頼書と一致・1558行）。承認の控え `SDK/.claude/ratchet/acceptance_archive/m2c15-param-values-20261006.md` も同じ値。もう1つの控え `….01.md` は 2fb46ecf…（`.01.sha.txt` と同じ）。
- 実施日: 2026-10-06〜2026-10-07
- ★依頼書の事実と git が食い違っていた: 依頼書は「実装の前＝HEAD の 0cb31ab」「実装の後＝まだ commit していない作業中の変更」と書く。実際は、実装は commit 65e3f0c に入っていて、0cb31ab はその親。監査の途中で HEAD は 6f30563（hook と worklog）・593ae4b（docs）に進んだ。対象の9ファイルは 65e3f0c から HEAD まで変わっていない（`git diff --stat 65e3f0c HEAD -- <対象>` が空）。そのため Q1・Q2 は「0cb31ab → 65e3f0c」で比べた（Process-2）。


## 2. 監査対象の型宣言

- コード型＝observe_diag.py（build_catalog・selftest_catalog）・engine_tuner_gen.py（説明の文）・engine_tuner_exec.py（説明の文）・gen_materials.py（説明の文）・壊すプログラム b137〜b139・承認の仕組み（require_design_check_before_approval.py の A12・gen_acceptance.py の build_spec）。
- 数値型＝observe_config.json の material_params（80種）・material_keep（V9 19本・採用中の戦略と確認のレシピ 9本）・search_limits.json の material_param_ranges（104種）・型の表の数（部品 476種・禁止3 366組）。
- 文書型＝設計書 acceptance.md（4-0・4-13・4-20・3-1・3-2）・やることの表.md・承認の控え2版・見直し表。


## 3. 監査対象の事実データの確認

### 設計書の実装の指示の一覧（4-20・当てる道具が当てる相手）

依頼書の表17件は、acceptance.md:499〜1136 の `#### 実装 1〜17` と、ファイル・直す箇所・種類が全部合った。直す前の文字は、実装の前の版（`git show 0cb31ab:<パス>`）で数えて、どれもちょうど1か所（observe_diag.py の 1328・1331・1669・1676・7074、observe_config.json:164〜166 の3行の組、search_limits.json:44、engine_tuner_gen.py の 242・244・248・254・293、engine_tuner_exec.py:736、gen_materials.py:1583）。15〜17件目（b137〜b139）は 0cb31ab に無い新しいファイルで、直す前の文字は「なし」。

### 当てた記録（applied_fixes.json の名前 design:m2c15-param-values-20261006）

SDK/.claude/audits/applied_fixes.json:2567〜2683 に、名前 design:m2c15-param-values-20261006 の行が17件在る。番号1〜17・ファイルは依頼書の表のとおり、時刻は全部 2026-10-06T21:49:17、当て方は全部「当てた」（「もう当て終わっていた」は0件）。0cb31ab→65e3f0c でこのファイルに足された119行は 17件×7行 で数が合う。

### 必読に要るファイル（道具が設計書と実装から拾った）

表の13件は全部実在し、着手前必読に入っている。直す相手の9ファイルは、4-20 の対象のファイルと同じ。


## 4. 所見

### 一般の観点

該当なし（依頼書のとおり）

### Q1 — 実装の指示を当てた結果が、実装の後と1文字も同じか（優先度 A）

YES・問題なし。17件それぞれで、設計書の直した後の文字と 65e3f0c の実物の行を `diff <(sed -n 'a,bp' .claude/state/acceptance.md) <(git show 65e3f0c:<パス> | sed -n 'x,yp')` で比べ、差は17件とも0だった（例＝1件目 acceptance:510〜517 と observe_diag.py:1328〜1335、5件目 592〜624 と 7091〜7123、6件目 642〜771 と observe_config.json:164〜293、7件目 788〜894 と search_limits.json:44〜150、15〜17件目はファイル全文）。囲みの前後の行も同じ。作業ツリーと 65e3f0c の対象9ファイルも同じ（`git diff --stat 65e3f0c HEAD -- <対象>` が空）。

修正の番号＝なし

### Q2 — 実装の指示のどれにも当たらない行（設計書に無い変更）が無いか（優先度 A）

YES・問題なし。`git diff --numstat 0cb31ab 65e3f0c -- <対象9ファイル>` の行数が、指示の行数の合計とちょうど合った（observe_diag.py +51/−2・engine_tuner_gen.py +7/−6・engine_tuner_exec.py +1/−1・gen_materials.py +1/−1・observe_config.json +127・search_limits.json +107/−2・b137〜b139 各 +27）。差分の塊は全部が指示の場所で、指示に当たらない行は0行。

修正の番号＝なし

### Q3 — 当てた記録が、実装の指示の全部と1件ずつ合うか（優先度 A）

YES・問題なし。3節の確認のとおり、番号と対象のファイルが1対1で、抜けは0件。「もう当て終わっていた」は0件なので、どの実行で当たったかを別に確かめる件は無い。

修正の番号＝なし

### Q8 — 指標ごとの一覧（P-1）は、修正対応表の最初の値と残す名前を、漏れなく・余計なく写しているか（優先度 A）

一覧は問題なし。残す名前の読み方に取りこぼし1件（Minor-2）。

- 一覧＝`jq` で indicator_params_by_strategy.json の141行を出し、observe_config.json の material_params 80種と1行ずつ照らした。80種とも「スキャル∪デイトレ（AXIS_MAP で名前の軸を取ったもの）＋残す名前」とちょうど同じ（例＝ADX は [7,10,14]、RSI は [5,7,9,14,21]、ROC は [9,12,24]）。一覧に入らない種類は、最初の値が無いか名前に軸が無い種類で、理由どおり。
- 残す名前＝V9 の19本は v9_logic.md §1.2 と gen_signal_families.py:1233〜1253 の V9_FAMILY_MAP から確かめた。1つ目の数字だけで照らす読み方でも、取りこぼしは0件（BB%b(20,3.0) は drop_columns で省かれた後の名前で照らしている。MACD は macd_params が [[12,26,9]] だけ）。採用中の戦略（engine_tuner_exec.py:289〜297 の RUNTIME_ALIAS）も確かめた。
- 【Minor-2】r3_draft_build.py:130 の正規表現 `\{[^{}]*"family"…[^{}]*\}` は、入れ子の `"pre": { "op": "abs" }` が在る recipes/r9_demand_fixture.json:29〜30 の MACDヒスト%(12,26,9) を拾わない。observe_config.json の material_keep「採用中の戦略と確認のレシピ」は9本で、この1本が入っていない。名前は V9 の組と material_params の両方に在るので、カタログへの影響は0本。
- 両方に在る423本の列の値＝データ不足（理由＝写しで列を計算していない）。読んだ範囲では、make_material（observe_diag.py:764〜778）は種類とパラメータだけで決まる関数で、一覧の種類も前と同じ make_material(family, *p) で作る。JSON の数の型（2.0 は小数・ほかは整数）も前の設定と同じ。

修正の番号＝9

### Q9 — 範囲（P-2）は、修正対応表の範囲を名前の軸に正しく当てているか。CC が決めた対応 18種は正しいか（優先度 A）

大筋は問題なし。TSI の軸の当て違いと、VIDYA・T3 の範囲がカタログの列を含まない件が見つかった（Major 2件）。

- 104種の値は資料の範囲と1行ずつ同じ。ROC だけ 9〜14 を 9〜24 に広げている（search_limits.json:71・設計書 3-2 の2行目のとおり）。
- AXIS_MAP の18種は、計算式の引数で全部正しい（転換線・基準線＝observe_diag.py:808〜811、KSTシグナル＝:992 の signal=g_、StochRSI＝:1072〜1075、Keltner＝:893〜896、ALMA・JMA・KAMA・MCGD・SSF・T3・VIDYA＝:1110 付近の length=n、EMA傾き＝:813 の span=n、Stoch%K/D＝:794〜797）。
- MACD の3種の軸の重なり（3〜12 と 10〜26）は、設計書 3-2 の3行目のとおり範囲をそのまま書き、決まりは工事2 に回している。
- 【Major-2】TSI・TSIシグナル・TSIヒスト は、資料の軸の順（1つ目＝長い方・先にならす、2つ目＝短い方）と、名前の軸の順（observe_diag.py:1085「_pta6.tsi(close=d.close, fast=f_, slow=s_, signal=g_)」＝1つ目が短い方）が逆。資料の見つかった値は [7,4,2]・[13,7,4]・[13,8,5]・[25,13,7]（1つ目が長い）。今の値 [12,26,9] は1つ目が短い。両方を混ぜて軸の順のまま写したので、search_limits.json:60〜62 は1つ目 7〜25・2つ目 4〜26 になり、7〜25 で重なる。r3_draft_build.py:224 の重なりの検出は `fo in per`（一覧の在る種類）しか見ないので TSI を数えず、設計書の 4-0 の⑦にも 3-2 にも出ていない。
- 【Major-3】一覧に入らない close vs VIDYA% と close vs T3% は、カタログの数字が sma_periods の 20・50・200 で、設定の範囲は VIDYA 14〜14（search_limits.json:145）・T3 8〜34（:141）。VIDYA%20・50・200 と T3%50・200 の5列が範囲の外になる。範囲を広げる決まりは一覧の値にしか効かず、番人⑬もこの2種を見ない。設計書にも出ていない。

修正の番号＝4・5・6・7

### Q10 — 完成の条件3行は、設計書の直し（P-1・P-2）を全部 覆っているか。壊すプログラム3本は、直しを外したときだけ落ちるか（優先度 A）

壊すプログラム3本は宣言どおりに落ちる作り。番人⑬の飛ばしに守りの隙間がある（Minor-1）。

- 壊すプログラムは本物を一時的に書き替える作り（.claude/breaks/lib.sh:61〜66・:85〜86）なので、走らせていない。中身を読んで確かめた。壊す対象は `grep -c -x` で3本ともちょうど1か所。
- b137＝`if False and family in _per` にすると _per_done が空のままになり、build_catalog（observe_diag.py:1682〜1684）が EXPECT_MSG と同じ文で止まる。selftest_catalog（:7024）がそれを呼ぶので落ちる。
- b138＝ROC24 を一覧から外すと、⑪は {ROC9,ROC12} どうしで一致し、⑫だけが「残す名前（採用中の戦略と確認のレシピ）がカタログに無い: ['ROC24']」（:7108）で落ちる。
- b139＝ROC の範囲の上限を 14 に戻すと、⑬が「ROC24 の 1 番目の数字 24 が、設定の範囲 9〜14 の外」で落ちる。
- 【Minor-1】⑬は observe_diag.py:7119〜7120「if not _ax13: continue」で、設定の範囲が無い種類を飛ばす。いまの実物で飛ばすのは RCI（資料に行が無い）だけで、範囲を書くべきなのに書いていない種類の見逃しは、いまは0件。ただし、範囲の欄から1種類（例＝RSI）を消しても⑬は落ちず、範囲全体が空のときだけ落ちる。
- ⑪は一覧に無い種類を見ないが、その経路のコード（addf の `_per` に無い種類は元の1行に落ちる）は変わっていない。
- 4件目の指示（_gone）は専用の壊すプログラムが無いが、戻すと残す側が外れた13組で build_catalog が止まり、軽い口が落ちるので覆われている。_gone で止めなくなるのは「残す側の名前が一覧の種類として読める」ときだけで、いま当たる13組は当てる前もカタログに無かったので、列の増減は無い。

修正の番号＝8

### Q4 — 承認した版の設計書どうしで、実装の指示が同じか（優先度 B）

YES・問題なし。`diff …/m2c15-param-values-20261006.01.md …/m2c15-param-values-20261006.md` の違いは 1314〜1316 の3行だけで、完成の条件の表の状態が「未着手」から「✅済」になったもの。この3行は `<!-- ACCEPT_TABLE_START -->`（:1310）と END（:1318）の囲みの中。ACC_IMPL の囲みを抜き出して比べた差は0。今の設計書は .md の控えと同じハッシュ値。

修正の番号＝なし

### Q5 — 実装の指示が、やることの表の要件を全部 満たすか（優先度 B）

要件の抜けは無い。P-2 の「同じ事実を書く説明をそろえる」に揃え漏れがある（Minor-3）。

- P-1・P-2・P-4 は指示1〜14 が満たす。P-3 は測った結果だけの項目。P-5 の残り3種は 3-1 で理由つきで外している。G-1・G-2 は当てた後の手順で、worklog 20261006:205〜223 と commit 65e3f0c の表の作り直しで行われている。
- 【Minor-3】同じ事実の揃え漏れ＝gen_materials.py:1581「（例＝RSI は 7〜21 の整数 全部。設定ファイルに並んでいるのは 7・9・14・21 の4つだけ）。」（CC の自己申告どおり。materials.md:100 にも写っている）と、engine_tuner_gen.py:240「＝RSI なら 7〜21 の整数が全部 試せる（12 も 13 も 20 も出る）。カタログの4つは全部この中に入る。」。どちらもこの工事の後は事実と違う（RSI の一覧は 5・7・9・14・21、設定の範囲は 2〜21）。engine_tuner_gen.py:430「★範囲を狭めていない＝成績表は材料カタログの数字で作られており、範囲の中に在る。」も Q11 の Critical-1 で事実でないと分かったが、直し方が Critical-1 の決め方に従うので、ここでは修正の指示を書かない。

修正の番号＝10・11・12

### Q6 — 完成の条件が、実装の後に本当に成り立つか（優先度 B）

YES・成り立つ。監査が `cd v3-bitget-api-sdk/bitget-python-sdk-api && python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog` を走らせ、出力は「K-1・K-8・G-2 の番人（--selftest-catalog）: ❌ 0 件」（ng が空なので SystemExit(0)＝observe_diag.py:7128）。秒数は測っていない（数秒で終わった）。走らせる前に試しの道具（try_hooks.py）で止める hook 0本を確かめた。設計書 acceptance.md:1314〜1316 の3行が ✅済 なのと合う。

修正の番号＝なし

### Q11 — 名前が入れ替わったことで、ほかの仕組みが黙って変わった所は無いか（優先度 B）

問題あり。設計書 4-13 の3が書いた仕組みが実物に無い（Critical-1）。

- 【Critical-1】設計書 acceptance.md:477「段の候補は、成績表の順位から作り、その列の数字が範囲の中かで絞ります（engine_tuner_gen.py の _group_usable_col）。…範囲の外に出る数字の列（例＝ROC3・ROC6・96本高値・安値）は、候補から外れます」。実物の _group_usable_col は engine_tuner_gen.py:465「return not _banned_pair(m, table)」で、禁止3（標本不足）しか見ない。_banned_pair（:1435〜1443）は名前と時間足で禁止3 を引くだけ、_mat_from_col（:433〜447）は範囲の照らしをせず列の数字をそのまま材料にする。範囲の照らしは、案を作った後の assert_provenance（:767「param_in_range」）と engine_tuner_exec.py の G6（:742〜744）にしか無い。成績表 material_ranking.json（2026-10-03 から変わっていない）で、sufficiency と trigger の ROC の組84のうち36組は代表の列が ROC3 か ROC6 で、窓が短いので禁止3 に当たらず候補に残る。その順位で案を作ると、外れるのではなく出どころの検査で止まる。CHOP7 については設計書のとおり（範囲 7〜21 の中）。
- 禁止3 が 514組 → 366組 に減ったのは、名前の入れ替わりだけで説明できる。前後の signal_families.md の禁止3 の表を比べると、消えた行162は全部「消える名前」、足された行14は全部「増える名前」（AROON*25・CCI20・WMA30傾き%・DEMA30 ほか）。514 − 162 + 14 ＝ 366。式（gen_signal_families.py:93〜100・662〜666）は変わっていない。
- exit_families_rules.json の古い数（641〜698行）は、gen_exit_families.py:262〜270 が「空でないか」だけを見て、:530〜532 で表に写すだけで、数として読んでいない。【Minor-5】ただしこの工事で ADX は 7・10・14、Donchian幅% は 20 だけになったので、666行「ADX7/14/21」と 679行「Donchian幅%20/48」はさらに事実とずれた（表示だけ・修正の指示は書かない）。
- m2_stage_candidates.json は種類の名前で FAMILY_LINEAGE から引くので、名前の入れ替わりの影響は無い。

修正の番号＝1・2

### Q12 — このセッションで直した承認の仕組み2つと、仮当てが打ち切られた件の影響（優先度 B）

問題あり（Major-1・Minor-4）。

- 【Major-1】① A12 の T6 判定（require_design_check_before_approval.py:684〜686・HEAD 6f30563 の版。65e3f0c では 622〜624）は、`l.strip().startswith("❌ T")` の行だけを集め、それが全部 T6 なら止めない。gen_materials.py の自己テストの落ちの行は、全部 `print("  ❌ " + x)`（gen_materials.py:2984）で出るが、自己テストの中の ng.append のうち43件は「T数字」で始まらない（F1〜F6・R1〜R10・S1〜S8 ほか）。たとえば「❌ F4: …」と「❌ T6: …」が一緒に出ると、_t6 は T6 の1行だけになり、止めずに continue する＝T6 以外の落ちを見逃す。
- 【Minor-4】② gen_acceptance.py:697「if it.get("中身") and src_text.count(it["中身"]) == 1:」は、直した後の文字が1か所在るだけで「当て終わり」とみなす。直した後の文字が直す前の文字の中に含まれる指示（消すだけの指示）は、当てる前から直した後の文字が在るので、当てずに飛ばす。apply_audit_fix.py の _done_in（:505・510）はこの形を外しているが、ここには無い。この工事の指示は全部、直す前の文字を含まない形なので、この工事への影響は無い。
- 仮当ての打ち切り＝当てる前の本物はコミットの中身に戻っていた。根拠は Q1・Q2＝65e3f0c は「0cb31ab に17件を当てたもの」と1文字も違わず、余計な行も無い。記録が17件とも「当てた」なので、当てた時点で b137〜b139 は無く、直した後の文字も無かった。--dry の「17件当たる」は各件の直す前の文字が1か所在ることの証拠にしかならず、ファイル全体が戻っていた証拠には足りない（ファイル全体の証拠は Q1・Q2 の照合）。
- --verify の食い違い2つ＝データ不足（理由＝監査は --verify を走らせていない）。読んだ範囲では、当てた後に起きて当然の2つだけ（MATERIALS の「material_param_ranges ＝（空…）」と、CODEREF の selftest_catalog の定義の行 6994→7011）。ほかの囲み（SOURCE・RANKING・RANDOM・IMPL・SPEC）は、元の逐語・material_ranking.json・ACC_IMPL が変わっていないので、食い違う理由が無い。

修正の番号＝3・13


## 5. 外部検索

該当なし（依頼書のとおり）


## 6. 依頼を出した CC の自己申告への答え

### 自己申告 1

「囲みの外で 6 行」は事実と違う。違いは3行（diff の − 3行と + 3行を足して6と数えた形）で、場所は囲みの外ではなく ACCEPT_TABLE の目印の囲み（acceptance_archive の .md:1310〜1318）の中の、完成の条件の状態の欄だけ。ACC_IMPL の囲みは同じなので、実装への影響は無い。書き方の誤りなので Minor-6 にした（修正の指示は書かない）。

### 自己申告 2

今は事実と違う。require_design_check_before_approval.py・gen_acceptance.py・gen_audit_docs.py は commit 65e3f0c に入っていて、hook はさらに 6f30563 で直されている。require_chat_draft_before_long_reply.sh・require_request_understood.sh・e38_logics.backup_20260802_005140.json は未追跡（??）のまま。作業ツリーには一覧に無い decisions.md の変更（M）が在る。Q1・Q2 は対象の9ファイルだけで取ったので、結論への影響は無い。


## 7. 総合判定

### 結論を決める問いへの答え

- 問い1 ＝ NO（根拠＝実装の指示17件の当て方は Q1〜Q4 とも YES で、1文字の違いも、設計書に無い変更も、抜けも0件。しかし工事ごとの問い Q11 で、設計書 acceptance.md:477（4-13 の3）が書いた「範囲の外の列は _group_usable_col で段の候補から外れる」仕組みが、実物 engine_tuner_gen.py:450〜465 に無い。依頼書の「工事ごとの問いで設計書と違う所が見つかれば NO」に当たる）

### 結論と件数

- 結論＝NO-GO
- Critical＝1
- Major＝3
- Minor＝6
- Process＝3


## 8. 修正の指示

### Critical

#### 修正 1
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-param-values-20261006/やることの表.md
直す箇所: 110行
直す前の文字:
~~~
| このまま進める（成績表の作り直しは M2-D-8） | r3_names.json |
~~~
足す文字:
~~~

| 監査 CP63 の Q11＝設計書 4-13 の3は「段の候補は…その列の数字が範囲の中かで絞ります（engine_tuner_gen.py の _group_usable_col）」「範囲の外に出る数字の列（例＝ROC3・ROC6・96本高値・安値）は、候補から外れます」と書くが、実物の _group_usable_col（engine_tuner_gen.py:450〜465）は禁止3（標本不足）だけを見て範囲を見ない。成績表の sufficiency・trigger の ROC の組 84 のうち 36 は代表の列が ROC3 か ROC6 で、候補に残り、案を作るときに assert_provenance（engine_tuner_gen.py:767）か G6（engine_tuner_exec.py:742〜744）で止まる | 未決（A＝_group_usable_col に範囲の照らし（param_in_range）を足す実装の指示を 4-20 に足す／B＝4-13 の3の文を実物の動きに合わせ、成績表を作り直す M2-D-8 まで、その順位の案が作れないことを受け入れる） | 監査 CP63 の Q11 |
~~~
根拠の抜き書き: engine_tuner_gen.py:465「return not _banned_pair(m, table)」
状態: 未決

#### 修正 2
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --work m2c15-param-values-20261006 --write
~~~
根拠の抜き書き: acceptance.md:13「作り直し＝`python3 .claude/tools/gen_acceptance.py --work m2c15-param-values-20261006 --write`。」（監査は走らせていない＝本物を書き替えるため・秒数なし）
状態: 未決

### Major

#### 修正 3
対象のファイル: .claude/hooks/require_design_check_before_approval.py
直す箇所: 684行（HEAD 6f30563 の版）
直す前の文字:
~~~
if l.strip().startswith("❌ T")]
~~~
直した後の文字:
~~~
if l.strip().startswith("❌ ") and not re.match(r"❌ \d+ 件", l.strip())]
~~~
根拠の抜き書き: require_design_check_before_approval.py:684「_t6 = [l.strip() for l in ((r6.stdout or "") + (r6.stderr or "")).splitlines() if l.strip().startswith("❌ T")]」
状態: 確定

#### 修正 4
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-param-values-20261006/やることの表.md
直す箇所: 110行
直す前の文字:
~~~
| このまま進める（成績表の作り直しは M2-D-8） | r3_names.json |
~~~
足す文字:
~~~

| 監査 CP63 の Q9＝TSI・TSIシグナル・TSIヒスト は、資料の軸の順が「1つ目＝長い方（先にならす）・2つ目＝短い方（後にならす）・シグナル」（見つかった値 [7,4,2]・[13,7,4]・[13,8,5]・[25,13,7]）なのに、計算式の名前の軸は tsi(fast=f_, slow=s_, signal=g_)（observe_diag.py:1085＝1つ目が短い方）。資料の値と今の値 [12,26,9] を軸の順のまま混ぜて写したので、1つ目に 7〜25、2つ目に 4〜26 が入り、2つの範囲が 7〜25 で重なる（4-0 の⑦と 3-2 の3行目に無い） | 未決（A＝TSI の3種を名前の軸と資料の軸の対応に足し、1つ目と2つ目を入れ替えて写す／B＝MACD と同じく「短い方 < 長い方」の決まりを工事2 に入れ、3-2 の3行目に TSI の3種を足す） | 監査 CP63 の Q9・indicator_params_by_strategy.json の TSI の行 |
~~~
根拠の抜き書き: observe_diag.py:1085「_reg("TSI", "TSI({},{},{})", True, lambda d, f_, s_, g_:」
状態: 未決

#### 修正 5
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --work m2c15-param-values-20261006 --write
~~~
根拠の抜き書き: acceptance.md:13「作り直し＝`python3 .claude/tools/gen_acceptance.py --work m2c15-param-values-20261006 --write`。」（監査は走らせていない＝本物を書き替えるため・秒数なし）
状態: 未決

#### 修正 6
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-param-values-20261006/やることの表.md
直す箇所: 110行
直す前の文字:
~~~
| このまま進める（成績表の作り直しは M2-D-8） | r3_names.json |
~~~
足す文字:
~~~

| 監査 CP63 の Q9＝指標ごとの一覧に入らない close vs VIDYA%（カタログ 20・50・200）と close vs T3%（カタログ 20・50・200）は、設定の範囲（VIDYA 14〜14・T3 8〜34）がカタログの列 5本（VIDYA%20・50・200・T3%50・200）を含まない。範囲を広げる決まりは一覧の値にしか効かず、番人⑬も見ない | 未決（A＝範囲を広げてカタログの数字を含める／B＝一覧に入れて名前を範囲の中の値だけにする／C＝このままとし、4-0 の⑦に並べる） | 監査 CP63 の Q9・Q11 |
~~~
根拠の抜き書き: search_limits.json:145「"close vs VIDYA%": [{"kind": "int", "lo": 14, "hi": 14}],」
状態: 未決

#### 修正 7
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --work m2c15-param-values-20261006 --write
~~~
根拠の抜き書き: acceptance.md:13「作り直し＝`python3 .claude/tools/gen_acceptance.py --work m2c15-param-values-20261006 --write`。」（監査は走らせていない＝本物を書き替えるため・秒数なし）
状態: 未決

### Minor

#### 修正 8
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 7119〜7120行
直す前の文字:
~~~
        if not _ax13:
            continue
~~~
直した後の文字:
~~~
        if not _ax13:
            if _e13 and find_material(_x13)[0] in _per11:
                ng.append(f"P-2: {_x13} の種類 {_e13['family']} に、設定の範囲 material_param_ranges が無い（指標ごとの一覧の種類）")
            continue
~~~
根拠の抜き書き: observe_diag.py:7119「if not _ax13:」
状態: 未決

#### 修正 9
対象のファイル: .claude/state/indicator_review/r3_draft_build.py
直す箇所: 130行
直す前の文字:
~~~
(\[[^\]]*\]|[-\d.]+)[^{}]*\}', t):
~~~
直した後の文字:
~~~
(\[[^\]]*\]|[-\d.]+)(?:[^{}]|\{[^{}]*\})*\}', t):
~~~
根拠の抜き書き: r3_draft_build.py:130「for m in re.finditer(r'\{[^{}]*"family":\s*"([^"]+)"[^{}]*"param":\s*(\[[^\]]*\]|[-\d.]+)[^{}]*\}', t):」
状態: 未決

#### 修正 10
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_materials.py
直す箇所: 1581行
直す前の文字:
~~~
"（例＝RSI は 7〜21 の整数 全部。設定ファイルに並んでいるのは 7・9・14・21 の4つだけ）。"
~~~
直した後の文字:
~~~
"（例＝RSI は、設定の範囲 material_param_ranges が在るので 2〜21 の整数 全部。材料の一覧に並んでいるのは 5・7・9・14・21 の5つだけ）。"
~~~
根拠の抜き書き: gen_materials.py:1581「"（例＝RSI は 7〜21 の整数 全部。設定ファイルに並んでいるのは 7・9・14・21 の4つだけ）。"」
状態: 確定

#### 修正 11
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/materials.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
cd v3-bitget-api-sdk/bitget-python-sdk-api && python3 scripts/priority_rebuild/gen_materials.py --write
~~~
根拠の抜き書き: gen_materials.py:3011「if "--write" in argv:」（監査は走らせていない＝本物を書き替えるため・秒数なし）
状態: 確定

#### 修正 12
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 240行
直す前の文字:
~~~
＝RSI なら 7〜21 の整数が全部 試せる（12 も 13 も 20 も出る）。カタログの4つは全部この中に入る。
~~~
直した後の文字:
~~~
＝RSI なら、カタログの数字（5・7・9・14・21）から 5〜21 の整数が全部 試せる（ただし RSI は下の設定の範囲 2〜21 が優先される）。
~~~
根拠の抜き書き: engine_tuner_gen.py:240「＝RSI なら 7〜21 の整数が全部 試せる（12 も 13 も 20 も出る）。カタログの4つは全部この中に入る。」
状態: 確定

#### 修正 13
対象のファイル: .claude/tools/gen_acceptance.py
直す箇所: 697行
直す前の文字:
~~~
if it.get("中身") and src_text.count(it["中身"]) == 1:
~~~
直した後の文字:
~~~
if it.get("中身") and src_text.count(it["中身"]) == 1 and (not old or old not in src_text or old in it["中身"]):
~~~
根拠の抜き書き: gen_acceptance.py:697「if it.get("中身") and src_text.count(it["中身"]) == 1:」
状態: 確定


## 9. CC プロセス欠陥対策

### Process

修正の指示は書かない（3件とも CC の進め方の欠陥で、直す相手の1ファイルと文字に落とせないため。直す範囲は まこさんが決める）。

- Process-1＝設計書 4-13 の3の「_group_usable_col で範囲を絞る」という主張に、関数を開いた根拠が無い。見直し表 .claude/state/reviews/acceptance.review.md:40 の根拠にも engine_tuner_gen.py:450〜465 が無く、「走らせて確かめてはいません」のまま言い切っている（Critical-1 の元）。
- Process-2＝依頼書の事実が commit と食い違っていた（「未 commit」と書いたが 65e3f0c に commit 済み・自己申告2の一覧も古い）。依頼書を作った後に commit したため。
- Process-3＝承認の後に、承認の控えの置き場の元データ やることの表.md を書き替えている（worklog 20261006:230 の②・:236＝「## 手書きと自動の割り当て」の節・「M2-C-15」の1行・Y-5）。照らしたのは --verify の「囲みの外は同じ」だけ。


## 10. 開いたファイルと行・走らせたコマンドと結果と秒数・走らせられなかったものと理由

**監査の進め方**＝この session の CC は依頼書の全文（466行）を読み、Plan エージェントを cold start で起動して監査させた。Plan エージェントは読み取り専用で、ファイルを作らず状態を変えないコマンドだけで照合した。CC は所見の結論を決める行（Critical・Major の根拠）を実物で開き直し、完成の条件のコマンド（Q6）を走らせた。

**開いたもの**（SDK＝v3-bitget-api-sdk/bitget-python-sdk-api）
- 依頼書（全466行）・acceptance.md（1〜1138・1183〜1350・477）・承認の控え .01.md と .md（diff 全体）
- SDK/.claude/audits/applied_fixes.json:2567〜2683・やることの表.md（全114行・95〜114 は監査の CC も開いた）
- SDK/.claude/ratchet/engine_tuner_requirements.md:28〜103・cat_requirements.md:529〜752（H2・H6）・engine_tuner_milestones2.md:995〜1040・v9_logic.md §1.2
- .claude/state/indicator_params_by_strategy.json（jq で141行）・indicator_params_by_strategy.md:1〜60
- SDK/scripts/priority_rebuild/observe_diag.py:616〜640・741〜811・893〜897・992・1072〜1091・1100〜1150・1319〜1345・1520〜1600・1675〜1700・7011〜7130
- SDK/scripts/priority_rebuild/observe_config.json:160〜300・SDK/scripts/priority_rebuild/recipes/search_limits.json:44〜150
- SDK/scripts/priority_rebuild/engine_tuner_gen.py:228〜330・393〜500・728〜775・1359〜1455・2291〜2355・2720〜2755・2870〜2905・3080〜3140
- SDK/scripts/priority_rebuild/engine_tuner_exec.py:289〜297・668〜745・gen_materials.py:1570〜1591・2343〜3012
- gen_signal_families.py:60〜140・654〜667・1233〜1253・indicator_reference_diag.py:961〜985・gen_exit_families.py（grep）・exit_families_rules.json:641〜698
- signal_families.md（新旧の禁止3）・m2_stage_candidates.json（先頭）・material_ranking.json（jq）・recipes/*.json（grep）・r9_demand_fixture.json:25〜32
- .claude/breaks/b137〜b139・lib.sh（grep）・.claude/state/reviews/acceptance.review.md:40
- .claude/state/indicator_review/r3_draft_build.py:1〜330・session_worklog_20261006.md:160〜249
- .claude/hooks/require_design_check_before_approval.py:560〜690・.claude/tools/gen_acceptance.py:676〜707・1738〜1847・.claude/tools/apply_audit_fix.py:1〜315・413〜712・.claude/tools/try_hooks.py:1〜106
- 開いていないもの＝engine_tuner_milestones.md:95〜146・milestones2 の :3〜46・:1173〜1183（結論に関わらないため）

**走らせたコマンド**（どれも数秒以内。1本ずつの秒数は測っていない）
- `shasum -a 256`・`git log`・`git show`・`git diff --stat` と `--numstat`（0cb31ab・65e3f0c・HEAD）
- `diff <(sed …) <(git show …)`（17件・差0）・`grep -c -F` と `-x`（直す前の文字・壊す対象）・`awk`（禁止3 の再計算・ROC の代表の列）・`jq`（資料141行・drop_columns・成績表・material_params と material_param_ranges の種類）
- `python3 .claude/tools/try_hooks.py --session … --bash "…observe_diag.py --selftest-catalog"`＝止める hook 0本／試した17本
- `cd SDK && python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog`＝「❌ 0 件」

**hook に止められて走らなかったもの**（止まったので何も走っていない）
- Plan エージェントの `git diff`（変数と echo を含む形）＝require_acceptance_before_impl
- Plan エージェントの `python3 -c`・監査の CC の `python3 -`（標準入力から読む形）＝require_design_contract_before_run（走らせる .py を1つに決められない形）。jq に替えて同じことを数えた。
- Plan エージェントの `observe_diag.py --selftest-catalog`＝require_try_before_act（監査の CC が試しの道具を通してから走らせた）

**走らせなかったもの**
- 壊すプログラム b137〜b139＝本物を一時的に書き替える作り（lib.sh:61〜66）で、依頼書が本物の書き替えを禁じているため。中身を読んで落ち方を確かめた（Q10）。
- `gen_acceptance.py --work m2c15-param-values-20261006 --verify`＝監査の範囲で要らない読み方で足りたため（Q12 はデータ不足と書いた）。
- 写しでの423本の列の比べ（Q8）＝列の計算に5分足のデータ全部が要り、時間の見込みの根拠が無いため（恒久61番）。


## 11. 本物のファイルを書き替えていないこと

`cd /Users/tachiharamasako/Documents/GitHub/cat-bitget && git status --short | grep -v '^??'` の出力:

```
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/decisions.md
```

この M は監査を始めた時点（最初の git status）から在ったもので、監査は書いていない。監査が作ったファイルは、作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp63_work/` の cp63_result.md と見直し表、`.claude/state/try_ok.json` の試しの記録（試しの道具が書く）、このセッションの ToDo の置き場だけ。

<!-- gen_audit_docs: result request=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-06_m2c15_param_values_20261006_impl_cp63_audit_request.md request_sha256=ea2846580b075b1467c923a519e6e7f0cc6777c9a78fedce4ce7f6adeb01717b -->
